from __future__ import absolute_import
import pandas

import haemosphere.views.mutex as mtex
from haemosphere.views.utility import replaceItemInList, moveItemInList
from sqlalchemy.ext.declarative import declarative_base
from six.moves import range

Base = declarative_base()

from sqlalchemy import (
    Table,
    Column, Integer, Text, Sequence, Float,
    ForeignKey
)

from sqlalchemy.orm import relationship
from sqlalchemy.orm.session import Session
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.hybrid import hybrid_property

def createDatafile(**kwargs):
    """Create the .h5 associated with LabSamples class.
    """
    infile = kwargs.get('infile')
    outfile = kwargs.get('outfile')

    df = pandas.read_csv(infile, sep='\t')

    # construct sample table
    samples = df[['sampleId','batchId','shortName','description','notes','Cell No.','Date of','Elution',\
                       'RIN','RNA','RNA Prep','Sort Date','Total RNA','amplified RNA-Bio']]
    samples.columns = ['sampleId','batchId','celltype','description','notes','cell_number','collection_date','elution',\
                       'RIN','RNA','RNA Prep','sort_date','Total RNA','amplified RNA-Bio']
    samples = samples.fillna('').sort('sampleId').set_index('sampleId')

    # construct celltypes table with these columns
    celltypes = df[['shortName','celltype','cell_lineage','tissue','surface_markers','description','Species','Strain']].drop_duplicates()
    celltypes.columns = ['celltype','synonyms','cell_lineage','tissue','surface_markers','description','species','strain']
    celltypes['synonyms'] = [row['synonyms'] if row['synonyms']!=row['celltype'] else '' for index,row in celltypes.iterrows()]
    celltypes['species'] = ['MusMusculus' for i in range(len(celltypes))]
    celltypes['strain'] = ['C57BL/6' for i in range(len(celltypes))]
    celltypes = celltypes.drop_duplicates().fillna('').sort('celltype').set_index('celltype')
    #celltypes.to_csv('/Users/jchoi/projects/Hematlas/haemosphere.org/data/celltypes.txt', sep='\t', index=False)

    # construct batch table
    batches = df[['batchId','description','Date of']].drop_duplicates()
    batches.columns = ['batchId','description','date_data_received']
    batches = batches.fillna('').sort('batchId').set_index('batchId')

    # write to outfile
    initialiseDateFile(samples, celltypes, batches)


@mtex.mutual_exclusion
def initialiseDataFile(samples, celltypes, batches):
    samples.to_hdf(outfile, '/dataframe/samples')
    celltypes.to_hdf(outfile, '/dataframe/celltypes')
    batches.to_hdf(outfile, '/dataframe/batches')



# ----------------------------------------------------------
# LabSamples class
# ----------------------------------------------------------

class LabSamples(object):
    """
    Example of creating a joined table with subset of sample ids and columns
        > df = labSamples.table('samples').join(labSamples.table('celltypes'), on='celltype').loc[sampleIds,columns]
    """
    def __repr__(self):
        return "<LabSamples: {0} tabletypes>".format(self.tabletypes)

    def __init__(self, filepaths):
        self.filepaths = filepaths
        self.tabletypes = list(filepaths.keys())
        self._table = dict([(tabletype, pandas.read_csv(filepaths[tabletype], sep='\t', index_col=0)) for tabletype in self.tabletypes])

    def table(self, tabletype):
        return self._table[tabletype]

    def makeBackup(self, tabletype=None, destdir=None):
        """Make a backup file of tabletype using the last modified date. So samples.txt will be copied to samples.2015-12-20_14:42.txt.
        If tabletype is None, all tabletypes will be backed up.
        If destdir is None use same directory as used in filepaths.
        """
        for tt in self.tabletypes:
            if tabletype and tabletype!=tt: continue

            filepath = self.filepaths[tt]
            import os, datetime, shutil

            # get timestamp to use on the filename based on last modified time
            timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y%m%d_%H%M')
            destfile = '%s/%s' % (destdir if destdir else os.path.dirname(filepath), os.path.basename(filepath))
            destfile = destfile.replace('.txt', '.%s.txt' % timestamp)

            # write file
            shutil.copyfile(filepath, destfile)

    def update(self, dbsess, tabletype, id, key, value):
        """
        Update column 'key' from table 'tabletype' for instance with primary key 'id'
        Value is updates to 'value'
        """
        if(tabletype == 'samples'):
            s = getSample(dbsess, 'id', id)
            if(key == 'batch'):
                # Updating relationship
                if not value:
                    s.batch = None
                    dbsess.flush()
                else:
                    bt = getBatch(dbsess, 'batch_id', value)
                    if bt:
                        s.batch = bt
                        dbsess.flush()
            elif(key == 'celltype'):
                # Updating relationship
                if not value:
                    s.celltype = None
                    dbsess.flush()
                else:
                    ct = getCelltype(dbsess, 'celltype', value)
                    if ct:
                        s.celltype = ct
                        dbsess.flush()
            else:
                # Updating attribute
                editSample(dbsess, id, key, value)
        if(tabletype == 'celltypes'):
            editCelltype(dbsess, id, key, value)
        if(tabletype == 'batches'):
            editBatch(dbsess, id, key, value)


def getAllLabSamples(dbsess):

    samples = getAllSampleData(dbsess)
    celltypes = getAllCelltypeData(dbsess)
    batches = getAllBatchData(dbsess)

    return { 'samples':  samples, 'celltypes': celltypes, 'batches': batches }


def saveNewData(dbsess, tableType, data):
    instance = None

    if(tableType == 'samples'):
        instance, message = newSample(dbsess, data)
        columns = list(Sample.__table__.columns.keys())
        replaceItemInList(columns, 'batch_id', 'batch')
        replaceItemInList(columns, 'celltype_id', 'celltype')
        moveItemInList(columns, 'celltype', 2)
        moveItemInList(columns, 'batch', 3)
    elif(tableType == 'celltypes'):
        instance, message = newCelltype(dbsess, data)
        columns = list(Celltype.__table__.columns.keys())
    elif(tableType == 'batches'):
        instance, message = newBatch(dbsess, data)
        columns = list(Batch.__table__.columns.keys())

    if instance:
        instance_data = instanceToList(instance, columns)
        return instance_data, message
    else:
        return None, 'Could not save data.'

def deleteData(dbsess, tableType, id):

    if(tableType == 'samples'):
        deleteSample(dbsess, id)
    elif(tableType == 'celltypes'):
        if not (checkSamplesRel(dbsess, 'celltype_id', id)):
            deleteCelltype(dbsess, id)
        else:
            return "Unable to delete until related Sample(s) are removed"
    elif(tableType == 'batches'):
        if not (checkSamplesRel(dbsess, 'batch_id', id)):
            deleteBatch(dbsess, id)
        else:
            return "Unable to delete until related Sample(s) are removed"

    return None

def getEntryByName(dbsess, table_type, entry_name):
    entry = None;
    if table_type == "samples":
        entry = getSample(dbsess, "sample_id", entry_name)
    elif table_type == "celltypes":
        entry = getCelltype(dbsess, "celltype", entry_name)
    elif table_type == "batches":
        entry = getBatch(dbsess, "batch_id", entry_name)
    return entry.id


def selectQuery(dbsess, data):
    return dbsess.query(Sample, Celltype, Batch).outerjoin(Celltype).outerjoin(Batch).filter(Sample.sample_id.in_(data)).all()

# ----------------------------------------------------------------
# Sample Table and methods for interacting with Sample data
# ----------------------------------------------------------------
class Sample(Base):
    __tablename__ = 'sample'

    id = Column(Integer, Sequence('sample_id_seq'), primary_key=True)
    sample_id = Column(Text, nullable=False, unique=True)
    cell_num = Column(Text)
    elution_date = Column(Text)
    elution_volume = Column(Text)
    rin = Column(Text)
    rna = Column(Text)
    rna_prep = Column(Text)
    sort_date = Column(Text)
    total_rna = Column(Text)
    amplified_rna_bio = Column(Text)

    batch_id = Column(Integer, ForeignKey('batch.id'))
    batch = relationship("Batch")

    celltype_id = Column(Integer, ForeignKey('celltype.id'))
    celltype = relationship("Celltype")

    description = Column(Text)
    notes = Column(Text)
    original_sample_id = Column(Text)
    previous_sample_id = Column(Text)
    genotype = Column(Text)
    treatment = Column(Text)
    group = Column(Text)


    def __init__(self, sample_id, cell_num, elution_date, elution_volume, rin, rna,	rna_prep,
                sort_date, total_rna, amplified_rna_bio,
                description, notes, original_sample_id,
                previous_sample_id, genotype, treatment, group):
        self.sample_id = sample_id
        self.cell_num = cell_num
        self.elution_date = elution_date
        self.elution_volume = elution_volume
        self.rin = rin
        self.rna = rna
        self.rna_prep = rna_prep
        self.sort_date = sort_date
        self.total_rna = total_rna
        self.amplified_rna_bio = amplified_rna_bio
        self.description = description
        self.notes = notes
        self.original_sample_id = original_sample_id
        self.previous_sample_id = previous_sample_id
        self.genotype = genotype
        self.treatment = treatment
        self.group = group

    def __repr__(self):
        return "<Sample sample_id='{0.sample_id}' description='{0.description}'>".format(self)



def getAllSampleData(dbsess):
    columns = list(Sample.__table__.columns.keys())
    replaceItemInList(columns, 'batch_id', 'batch')
    replaceItemInList(columns, 'celltype_id', 'celltype')

    moveItemInList(columns, 'celltype', 2)
    moveItemInList(columns, 'batch', 3)

    data = dataToLists(dbsess.query(Sample).all(), columns)

    return { 'data' : data, 'columns' : columns }


def newSample(dbsess, data):
    """Create a new sample, unless sampleId is already taken in which case return None
    """
    ## Assign values entered by user
    new_sample = Sample(sample_id = data['sample_id'],
                        cell_num = data['cell_num'] 				if 'cell_num' in data else None,
                        elution_date = data['elution_date']			if 'elution_date' in data else None,
                        elution_volume = data['elution_volume'] 	if 'elution_volume' in data else None,
                        rin = data['rin'] 							if 'rin' in data else None,
                        rna = data['rna'] 							if 'rna' in data else None,
                        rna_prep = data['rna_prep']					if 'rna_prep' in data else None,
                        sort_date = data['sort_date']				if 'sort_date' in data else None,
                        total_rna = data['total_rna']				if 'total_rna' in data else None,
                        amplified_rna_bio = data['amplified_rna_bio']	if 'amplified_rna_bio' in data else None,
                        description = data['description']			if 'description' in data else None,
                        notes = data['notes']						if 'notes' in data else None,
                        original_sample_id = data['original_sample_id']	if 'original_sample_id' in data else None,
                        previous_sample_id = data['previous_sample_id']	if 'previous_sample_id' in data else None,
                        genotype = data['genotype']					if 'genotype' in data else None,
                        treatment = data['treatment']				if 'treatment' in data else None,
                        group = data['group'] 						if 'group' in data else None)

    ## Set up relationships
    try:
        b = dbsess.query(Batch).filter_by(batch_id=data['batch']).one()
        new_sample.batch = b
    except Exception:
        pass

    try:
        c = dbsess.query(Celltype).filter_by(celltype=data['celltype']).one()
        new_sample.celltype = c
    except Exception:
        pass

    try:
        dbsess.add(new_sample)
        dbsess.flush()
        return new_sample, "Saved Successfully"
    except IntegrityError as exc:
        if 'UNIQUE constraint failed' in exc.__class__.__name__:
            # sample with that sampleId already exists
            dbsess.rollback()
            return None, "%s already exists" %data['sample_id']
        else:
            raise



def getSample(dbsess, key, value):
    '''Fetch the Sample instance with attribute given by key matching value provided.
    '''
    try:
        return dbsess.query(Sample).filter(getattr(Sample, key) == value).one()
    except NoResultFound:
        return None

def getAllSamples(dbsess, key, value):
    '''Fetch all Sample instances with attribute given by key matching value provided.
    '''
    try:
        return dbsess.query(Sample).filter(getattr(Sample, key) == value).all()
    except NoResultFound:
        return None


def editSample(dbsess, id, key, value):
    '''Edit sample matching given id.
    '''

    sample = getSample(dbsess, 'id', id)
    if not sample:
        return

    try:
        sample.__setattr__(key, value)
        dbsess.flush()
    except IntegrityError as exc:
        if 'UNIQUE constraint failed' in exc.__class__.__name__:
            dbsess.rollback()
            raise ValueError("sample '{}' is already taken".format(value))
        else:
            raise


def deleteSample(dbsess, id):
    '''Delete Sample with primary key given by id.
    '''
    sample = getSample(dbsess, 'id', id)
    if not sample:
        return

    dbsess.delete(sample)
    dbsess.flush()

def getSampleColumnNames():
    return list(Sample.__table__.columns.keys())


# ----------------------------------------------------------------
# Celltype Table and methods for interacting with Celltype data
# ----------------------------------------------------------------	
class Celltype(Base):
    __tablename__ = 'celltype'

    id = Column(Integer, Sequence('celltype_id_seq'), primary_key=True)
    celltype = Column(Text, nullable=False, unique=True)
    cell_lineage = Column(Text)
    colour = Column(Text)
    description = Column(Text)
    include_haemopedia = Column(Text)
    maturity = Column(Text)
    notes = Column(Text)
    order = Column(Text)
    species = Column(Text)
    strain = Column(Text)
    surface_markers = Column(Text)
    previous_names = Column(Text)
    tissue = Column(Text)

    def __init__(self, celltype, cell_lineage, colour, description, include_haemopedia, maturity,
                    notes, order, species, strain, surface_markers, previous_names, tissue):
        self.celltype = celltype
        self.cell_lineage = cell_lineage
        self.colour = colour
        self.description = description
        self.include_haemopedia = include_haemopedia
        self.maturity = maturity
        self.notes = notes
        self.order = order
        self.species = species
        self.strain = strain
        self.surface_markers = surface_markers
        self.previous_names = previous_names
        self.tissue = tissue

    def __repr__(self):
        return "<Celltype celltype='{0.celltype}' description='{0.description}'>".format(self)

    def __str__(self):
        return "{0.celltype}".format(self)


def getAllCelltypeData(dbsess):
    columns = list(Celltype.__table__.columns.keys())

    data = dataToLists(dbsess.query(Celltype).all(), columns)

    return { 'data' : data, 'columns' : columns }


def newCelltype(dbsess, data):
    """Create a new celltype, unless attribute 'celltype' is already taken in which case return None
    """
    ## Assign values entered by user
    new_celltype = Celltype(celltype = data['celltype'],
                        cell_lineage = data['cell_lineage'] 				if 'cell_lineage' in data else None,
                        colour = data['colour']								if 'colour' in data else None,
                        description = data['description'] 					if 'description' in data else None,
                        include_haemopedia = data['include_haemopedia'] 	if 'include_haemopedia' in data else None,
                        maturity = data['maturity'] 						if 'maturity' in data else None,
                        notes = data['notes']								if 'notes' in data else None,
                        order = data['order']								if 'order' in data else None,
                        species = data['species']							if 'species' in data else None,
                        strain = data['strain']								if 'strain' in data else None,
                        surface_markers = data['surface_markers']			if 'surface_markers' in data else None,
                        previous_names = data['previous_names']				if 'previous_names' in data else None,
                        tissue = data['tissue']								if 'tissue' in data else None)

    try:
        dbsess.add(new_celltype)
        dbsess.flush()
        return new_celltype, "Saved Successfully"
    except IntegrityError as exc:
        if 'UNIQUE constraint failed' in exc.__class__.__name__:
            # celltype with that 'celltype' attribute already exists
            dbsess.rollback()
            return None, "%s already exists" %data['celltype']
        else:
            raise

def getCelltype(dbsess, key, value):
    '''Fetch the Celltype instance with attribute given by key matching value provided.
    '''
    try:
        return dbsess.query(Celltype).filter(getattr(Celltype, key) == value).one()
    except NoResultFound:
        return None

def getAllCelltypes(dbsess, key, value):
    '''Fetch all Celltype instances with attribute given by key matching value provided.
    '''
    try:
        return dbsess.query(Celltype).filter(getattr(Celltype, key) == value).all()
    except NoResultFound:
        return None

def editCelltype(dbsess, id, key, value):
    '''Edit celltype matching given id.
    '''
    if not value:
        return # Don't update value to NULL

    celltype = getCelltype(dbsess, 'id', id)
    if not celltype:
        return

    try:
        celltype.__setattr__(key, value)
        dbsess.flush()
    except IntegrityError as exc:
        if 'UNIQUE constraint failed' in exc.__class__.__name__:
            dbsess.rollback()
            raise ValueError("celltype '{}' is already taken".format(value))
        else:
            raise

def deleteCelltype(dbsess, id):
    '''Delete Celltype with primary key given by id.
    '''
    celltype = getCelltype(dbsess, 'id', id)
    if not celltype:
        return

    dbsess.delete(celltype)
    dbsess.flush()

def getCelltypeColumnNames():
    return list(Celltype.__table__.columns.keys())



# ----------------------------------------------------------------
# Batch Table and methods for interacting with Batch data
# ----------------------------------------------------------------
class Batch(Base):
    __tablename__ = 'batch'

    id = Column(Integer, Sequence('batch_id_seq'), primary_key=True)
    batch_id = Column(Text, nullable=False, unique=True)
    description = Column(Text)
    date_data_received = Column(Text)

    def __init__(self, batch_id, description, date_data_received):
        self.batch_id = batch_id
        self.description = description
        self.date_data_received = date_data_received

    def __repr__(self):
        return "<Batch batch_id='{0.batch_id}' description='{0.description}' date_data_received='{0.date_data_received}'>".format(self)

    def __str__(self):
        return "{0.batch_id}".format(self)


def getAllBatchData(dbsess):
    columns = list(Batch.__table__.columns.keys()) # ['id', 'batch_id', 'description', 'date_data_received']

    data = dataToLists(dbsess.query(Batch).all(), columns)

    return { 'data' : data, 'columns' : columns }

def newBatch(dbsess, data):
    """Create a new batch, unless attribute 'batch_id' is already taken in which case return None
    """
    ## Assign values entered by user
    new_batch = Batch(batch_id = data['batch_id'],
                        description = data['description'] 					if 'description' in data else None,
                        date_data_received = data['date_data_received']		if 'date_data_received' in data else None)

    try:
        dbsess.add(new_batch)
        dbsess.flush()
        return new_batch, "Saved Successfully"
    except IntegrityError as exc:
        if 'UNIQUE constraint failed' in exc.__class__.__name__:
            # batch with that 'batch_id' attribute already exists
            dbsess.rollback()
            return None, "%s already exists" %data['batch_id']
        else:
            raise


def getBatch(dbsess, key, value):
    '''Fetch the Batch instance with attribute given by key matching value provided.
    '''
    try:
        return dbsess.query(Batch).filter(getattr(Batch, key) == value).one()
    except NoResultFound:
        return None

def getAllBatches(dbsess, key, value):
    '''Fetch all Batch instances with attribute given by key matching value provided.
    '''
    try:
        return dbsess.query(Batch).filter(getattr(Batch, key) == value).all()
    except NoResultFound:
        return None

def editBatch(dbsess, id, key, value):
    '''Edit batch matching given id.
    '''
    batch = getBatch(dbsess, 'id', id)
    if not batch:
        return

    try:
        batch.__setattr__(key, value)
        dbsess.flush()
    except IntegrityError as exc:
        if 'UNIQUE constraint failed':
            dbsess.rollback()
            raise ValueError("batch '{}' is already taken".format(value))
        else:
            raise


def deleteBatch(dbsess, id):
    '''Delete Batch with primary key given by id.
    '''
    batch = getBatch(dbsess, 'id', id)
    if not batch:
        return

    dbsess.delete(batch)
    dbsess.flush()

def checkSampleBatchRel(dbsess, id):
    '''Check if batch is currently in a relationship with Sample(s)
    '''
    samples = getAllSamples(dbsess, 'batch_id', id)

    if not samples:
        return false # no samples related to given batch
    else:
        return true

def getBatchColumnNames():
    return list(Batch.__table__.columns.keys())



# ----------------------------------------------------------------
# Methods common to all db tables
# ----------------------------------------------------------------	
def dataToLists(rawData, columns):
    '''
    Store data in two separate lists. One to store primary keys of selected data,
    the other to store the data to be displayed as a table to the user
    '''
    data = []
    for i, row in enumerate(rawData):
        rowData = []
        for key in columns:
            value = row.__getattribute__(key)
            rowData.append(str(value) if value else '')

        data.append(rowData)

    return data

def instanceToList(instance, columns):
    '''
    Convert a single instance into a list containing all required data to display to a
    user on a table
    '''
    instance_data = [str(instance.__getattribute__(key)) for key in columns]

    return instance_data

def checkSamplesRel(dbsess, relKey, id):
    '''Check if celltype or batch is currently in a relationship with Sample(s)
    relKey = "celltype_id" or "batch_id"
    id = the primary key of the celltype or batch
    '''
    samples = getAllSamples(dbsess, relKey, id)

    if not samples:
        return False
    else:
        return True


# ----------------------------------------------------------------
# Methods to map dataset column names to sql column names
# ----------------------------------------------------------------	

def dfColToSqlCol(columns):
    """ Take the column names of a dataframe and map them onto a column name in
        the labsamples db
    """
    sqlCols = []
    for col in columns:
        newCol = convertColName(col)
        if(newCol):
            sqlCols.append(newCol)

    return sqlCols

def convertColName(colName):
    """ Take a column name from a datafram and map it to a column name in the labsamples db
    """
    return {
        'sampleId': 'sample_id',
        'celltype': 'celltype',
        'Celltype': 'celltype',
        'cell_lineage': 'cell_lineage',
        'tissue': 'tissue',
        'Tissue Type':'tissue',
        'description':'celltypeDescription',
        'comment':'sampleDescription',
        'Comment':'sampleDescription',
        'surface_markers':'surface_markers',
        'mAB':'surface_markers',
        'Cell No.':'cell_num',
        'RIN':'rin',
        'RNA':'rna',
        'Strain':'strain',
        'Total RNA':'total_rna',
        'notes':'notes',
        'amplified RNA-Bio':'amplified_rna_bio',
        'Sort Date':'sort_date',
        'RNA Prep':'rna_prep',
        'Date of':'elution_date',
        'Elution':'elution_volume',
        'Species':'species',
        'originalSampleId':'original_sample_id', 
        'previousSampleId':'previous_sample_id',
        'group':'group',
        'treatment':'treatment',
        'genotype':'genotype',
        'batchId':'batch_id',
        'maturity':'maturity',
        
    }.get(colName, None)		


# ------------------------------------------------------------
# Tests - eg. nosetests labsamples.py
# ------------------------------------------------------------
def test_samplesTable():
    ls = LabSamples({'samples':'data/grouppages/HiltonLab/HematlasSamples_samples.txt',
                     'celltypes':'data/grouppages/HiltonLab/HematlasSamples_celltypes.txt',
                     'batches':'data/grouppages/HiltonLab/HematlasSamples_batches.txt'})

