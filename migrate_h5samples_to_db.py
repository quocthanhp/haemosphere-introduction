"""
This script migrates the labsample data from the samples, 
batches, and celltypes txt files to the SQL database 
(connection details are defined in haemosphere/models/__init__.py).
"""
import os
import sys
import transaction
import pandas as pd
from sqlalchemy.exc import IntegrityError

from haemosphere.models import hsdataset
from haemosphere.models import labsamples


from zope.sqlalchemy import mark_changed

from pyramid.paster import (
	get_appsettings,
	setup_logging,
	)

from pyramid.scripts.common import parse_vars

from haemosphere.models import (
	get_engine2,
	get_session_factory,
	get_tm_session,
	)

from haemosphere.models import labsamples
from haemosphere.models.labsamples import Sample, Batch, Celltype

def usage(argv):
	cmd = os.path.basename(argv[0])
	print('usage: %s <config_uri> [var=value]\n'
			'(example: "%s development.ini")' % (cmd, cmd))
	sys.exit(1)


def main(argv=sys.argv):
	if len(argv) < 2:
		usage(argv)
	config_uri = argv[1]
	options = parse_vars(argv[2:])
	setup_logging(config_uri)
	settings = get_appsettings(config_uri, options=options)

	# get data from txt files store
	directorypath = settings['haemosphere.model.datasets.root']
	
	paths = []

	paths.append(directorypath + '/F0r3sT/PRIVATE/GROUPS/CSL/hiltonlab-rnaseq-plus.1.4.h5')
	paths.append(directorypath + '/F0r3sT/PRIVATE/GROUPS/HiltonLab/hiltonlab.h5')
	paths.append(directorypath + '/F0r3sT/PRIVATE/GROUPS/HiltonLab/megs.h5')
	paths.append(directorypath + '/F0r3sT/PRIVATE/GROUPS/HiltonLab/taoudi.h5')

	paths.append(directorypath + '/F0r3sT/PRIVATE/GROUPS/NilssonLab/nilsson-megs.h5')

	paths.append(directorypath + '/F0r3sT/PUBLIC/haemopedia.2.7.h5')
	paths.append(directorypath + '/F0r3sT/PUBLIC/haemopedia-plus.2.6.h5')
	
	
	for path in paths:
		add_to_sql(path, settings)
		


def add_to_sql(path, settings):
	
	store = pd.HDFStore(path)
	columns = store['/dataframe/samples'].columns.tolist()
	df = hsdataset.HSDataset(path).sampleTable().reset_index().fillna('')

	di = df.set_index('sampleId').T.to_dict()

	samples = []	
	celltypes = []
	batches = []
	celltypeColumns = labsamples.getCelltypeColumnNames()
	batchColumns = labsamples.getBatchColumnNames()
	sampleColumns = labsamples.getSampleColumnNames()
	
	# organise data into relevant tables
	for key in di:
		data = di[key]
		
		celltype_dict = get_relevant_data(data, celltypeColumns)				
		batch_dict = { 'batch_id' : data['batchId'] } if 'batchId' in data else {}	
		
		sample_dict = get_relevant_data(data, sampleColumns)
		sample_dict['sample_id'] = key
		
		if batch_dict:
			sample_dict['batch'] = batch_dict['batch_id']
			batches.append(batch_dict)
		
		if celltype_dict:
			sample_dict['celltype'] = celltype_dict['celltype']
			celltypes.append(celltype_dict)	
		
		samples.append(sample_dict)
		 				
	# connect to DB
	engine = get_engine2(settings)
	session_factory = get_session_factory(engine)


	with transaction.manager:
		dbsession = get_tm_session(session_factory, transaction.manager)
		for ct in celltypes:
			if ct['celltype']:
				newCelltype(dbsession, ct)
		for b in batches:
			if b['batch_id']:
				newBatch(dbsession, b)
		for s in samples:
			newSample(dbsession, s)


def get_relevant_data(data, columns):
	""" Extract data with keys matching the column names of the relevant table in the db
	"""
	new_dict = {}
	for key in data:
		sqlKey = labsamples.convertColName(key)
		if sqlKey and "Description" in sqlKey:
			sqlKey = "description"
		if sqlKey in columns:
			new_dict[sqlKey] = data[key] 
		
	return new_dict


def newSample(dbsess, data):
	"""Create a new sample, unless sampleId is already taken in which case return None
	"""
	s = dbsess.query(Sample).filter_by(sample_id=data['sample_id']).first()
	if s:
		## update any any empty fields in sql database
		for key in data:
			if not s.__getattribute__(key):
				if key != "batch" and key != "celltype":
					s.__setattr__(key, data[key])

		try:
			b = dbsess.query(Batch).filter_by(batch_id=data['batch']).one()
			if not s.batch:
				s.batch = b
		except Exception:
			pass			

		try:
			c = dbsess.query(Celltype).filter_by(celltype=data['celltype']).one()
			if not s.celltype:
				s.celltype = c   
		except Exception:
			pass										
							
		try:
			dbsess.flush()
			transaction.commit()
		except:
			dbsess.rollback()
	else:
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

		dbsess.add(new_sample)
		transaction.commit()


		
def newCelltype(dbsess, data):
	"""Create a new celltype, unless attribute 'celltype' is already taken in which case return None
	"""
	c = dbsess.query(Celltype).filter_by(celltype=data['celltype']).first()
	if c:
		## update any any empty fields in sql database
		for key in data:
			if not c.__getattribute__(key):
				c.__setattr__(key, data[key])
							
		try:
			dbsess.flush()
			transaction.commit()
		except:
			dbsess.rollback()
	else:
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
			transaction.commit()
		except:
			dbsess.rollback()
					

def newBatch(dbsess, data):
	"""Create a new batch, unless attribute 'batch_id' is already taken in which case return None
	"""
	b = dbsess.query(Batch).filter_by(batch_id=data['batch_id']).first()
	if b:
		## update any any empty fields in sql database
		for key in data:
			if not b.__getattribute__(key):
				b.__setattr__(key, data[key])						
		try:
			dbsess.flush()	
			transaction.commit()
		except:
			dbsess.rollback()
	else:
	## Assign values entered by user
		new_batch = Batch(batch_id = data['batch_id'],
							description = data['description'] 					if 'description' in data else None,
							date_data_received = data['date_data_received']		if 'date_data_received' in data else None)
	
		dbsess.add(new_batch)
		transaction.commit()


if __name__ == '__main__':
    main()
