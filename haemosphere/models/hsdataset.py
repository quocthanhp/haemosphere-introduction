from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import chardet
import pandas
import genedataset.dataset
import haemosphere.views.mutex as mtex
import six
from .cache import LRUCache

def createDatasetFile(destDir, **kwargs):
	"""
	Based on genedataset.dataset.createDatasetFile() function, this function creates an 
	instance of HSDataset.
	
	Parameters
	----------
	The same parameters as genedataset.dataset.createDatasetFile() are needed. In addition we need:
	sampleDistances: pandas DataFrame of all pairwise sample distances (symmetric matrix)
	sampleGroupColours: dictionary of colour values keyed on sample group and item, 
		eg: {'cell_lineage': {'Stem Cell':'#cccccc', ...}, ... }
	sampleGroupOrdering: dictionary of list keyed on sample group, for ordering of items within
		the sample group, eg: {'celltype':['T1','T2',...],...}
	sampleGroupsDisplayed: a subset list of sample groups used by Haemosphere for display, eg ['celltype', 'tissue']
		Any sample group not in this list will be used for descriptive purposes only and not used
		for selection in data aggregation or diff exp analysis.
	parent: (string) name of the parent dataset if applicable. Defaults to None
	
	Only sampleDistances is a required parameter. The others are optional.
	Note that first element of sampleGroupsDisplayed is assumed to be the replicate sample group
	- eg. 3 biological replicates may have been made for each celltype.
	"""
	
	sampleDistances = kwargs['sampleDistances']
	sampleGroupColours = kwargs.get('sampleGroupColours', {})
	sampleGroupOrdering = kwargs.get('sampleGroupOrdering', {})
	sampleGroupsDisplayed = kwargs.get('sampleGroupsDisplayed', [])
	parent = kwargs.get('parent')
	ds = genedataset.dataset.createDatasetFile(destDir, **kwargs)
			
	instantiateDatasetFile(ds, sampleDistances, sampleGroupColours, sampleGroupOrdering, sampleGroupsDisplayed, parent)		
	
	return HSDataset(ds.filepath)
	
	
@mtex.mutual_exclusion
def instantiateDatasetFile(ds, sampleDistances, sampleGroupColours, sampleGroupOrdering, sampleGroupsDisplayed, parent):
	store = ds.hdfStore()
	store['/dataframe/sampleDistances'] = sampleDistances
	store['/series/sampleGroupColours'] = pandas.Series(sampleGroupColours)
	store['/series/sampleGroupOrdering'] = pandas.Series(sampleGroupOrdering)
	store['/series/sampleGroupsDisplayed'] = pandas.Series(sampleGroupsDisplayed)
	store['/series/attributes']['parent'] = parent
	store.close()


	
def datasetAttributes(filepath, includeFilepath=False):
	"""
	Return a dictionary of dataset attributes from hdf5 file:
		(name, fullname, species, platform_type, version, description, platform_details, pubmed_id, parent)
	This is the same as attributes() method on the HSDataset instant, but should be
	faster since it only extracts the attributes rather than all other values.
	
	If includeFilepath is true, filepath is included in the dictionary, which is useful when trying
	to recover this info from afterwards
	"""

	import os
	if os.path.exists(filepath):
		
		d = mtex.hdf_attr_to_dict(filepath, '/series/attributes')
			
		# Some of the older files don't have 'name' key in attributes but we need this; similarly for parent
		if 'name' not in d:
			d['name'] = os.path.splitext(os.path.basename(filepath))[0]
		if 'parent' not in d:
			d['parent'] = None
		if includeFilepath:
			d['filepath'] = filepath
		
		return d
	else:
		return {}
	


	
class HSDataset(genedataset.dataset.Dataset):

	"""
	Class to handle a dataset object in haemosphere. Inherits from genedataset.dataset.Dataset but has extra attributes
	more specific to haemosphere such as sample group colours.
	
	Full list of keys and objects stored in the hdf file:
	
		/series/attributes: (name, fullname, species, platform_type, version, description, platform_details, pubmed_id, parent)
		/series/sampleGroupColours: 
		/series/sampleGroupOrdering
		/series/sampleGroupsDisplayed
		/dataframe/sampleDistances
		/dataframe/samples
		
		For rna-seq data:
			/dataframe/counts
			/dataframe/cpm
			/dataframe/tpm
		
		For microarray:
			/dataframe/expression
			/series/probeIdsFromGeneId
			/series/geneIdsFromProbeId			
	"""
	_cache = LRUCache()# This is a class-level attribute

	def __new__(cls, pathToHDF):
        # Check if the object is already cached
		cached_instance = cls._cache.get(pathToHDF)
		if cached_instance:
			return cached_instance
        
		instance = super(HSDataset, cls).__new__(cls)
		cls._cache.set(pathToHDF, instance)
		return instance
	
	@mtex.mutual_exclusion
	def __init__(self, pathToHDF):
		if hasattr(self, 'initialised') and self.initialised:
			return

		super(HSDataset, self).__init__(pathToHDF)

		#print("path", pathToHDF)
		# '/dataframe/sampleDistances': calculated pairwise pearson correlation distance matrix
		self._sampleDistances = pandas.read_hdf(self.filepath,'/dataframe/sampleDistances')
		self._sampleGroupColours = pandas.read_hdf(self.filepath, '/series/sampleGroupColours')
		self._sampleGroupOrdering = pandas.read_hdf(self.filepath, '/series/sampleGroupOrdering')
		self._sampleGroupsDisplayed = pandas.read_hdf(self.filepath, '/series/sampleGroupsDisplayed')
		# #print("SampelDistnce", self._sampleDistances)
		# ##print("samplegroupordering",self._sampleGroupOrdering)
		# #print("samplegropus",self._sampleGroupsDisplayed)

		# #print(pandas.read_hdf(self.filepath, '/dataframe/sampleDistances'))
		# # Added a new attribute key 'parent', to deal with dataset subsets. Use this code to be backwards compatible with
		# # datasets created before this key was introduced.
		
		self.parent = self._attributes.get('parent')
		# #print(self.parent)
		self.initialised = True

	def sampleGroups(self, returnType=None):
		"""
		Return a list of sample group names eg: ["celltype","tissue"]. Override base class method
		in order to ensure correct ordering and filtering.

		Parameters
		----------
		returnType: {None, "display"}. If display, it returns only sample groups defined as for display.
		This is useful when not all sample groups are important for data aggregation or differential expression.
		
		Returns
		----------
		a list
		"""
		if returnType=="display":
			return self._sampleGroupsDisplayed.tolist()
		else:
			return super(HSDataset, self).sampleGroups()
				
	def sampleGroupItems(self, sampleGroup=None, groupBy=None, duplicates=False):
		"""
		Return sample group items belonging to sampleGroup, eg: ["B1","B2"]. Override base class method
		to enforce correct ordering.
		
		Parameters
		----------
		sampleGroup: name of sample group, eg: 'celltype'
		groupBy: name of another sample group for grouping, eg: 'cell_lineage'
		duplicates: boolean to return a list of unique values in the list avoiding duplicates if False; 
			if True, it specifies a list of sample group items in the same order/position as columns of 
			expression matrix; ignored if groupBy is specified.
		
		Returns
		----------
		list if groupBy is None, eg: ['B1','B2',...]. If duplicates is True, the list
			returned is the same length as dataset's columns in its expression matrix, and in the same
			corresponding position.
		dictionary of list if groupBy is specified, eg: {'Stem Cell':['LSK','STHSC',...], ...}
			groupBy sorts the flat list which would have been returned without groupBy into
			appropriate groups.
			
		Note that this method does not make assumptions about the integrity of the data returned for 
		groupBy specification. So it's possible to return {'Stem Cell':['LSK','STHSC'], 'B Cells':['LSK','B1']},
		if there is a sample id which has been assigned to ('LSK','Stem Cell') and another to ('LSK','B Cells') by mistake.
		"""
		df = self._samples
		sgo = self._sampleGroupOrdering
		
		if sampleGroup in df.columns and groupBy in df.columns: # group each item by sample ids, then substitute items from sampleGroup
			sampleIdsFromGroupBy = dict([(item, df[df[groupBy]==item].index.tolist()) for item in set(df[groupBy])])
			# {'Stem Cell':['sample1','sample2',...], ... }
		
			# substitute items from sampleGroup for each sample id
			dictToReturn = {}
			for sampleGroupItem in sampleIdsFromGroupBy.keys():
				# this is the set of matching sample group items with duplicates removed, eg: set(['LSK','CMP',...])
				groupItems = set([df.at[sampleId,sampleGroup] for sampleId in sampleIdsFromGroupBy[sampleGroupItem]])
				# order by sgo
				if sampleGroup in sgo:
					indexedItems = [(sgo[sampleGroup].index(item) if item in sgo[sampleGroup] else None, item) for item in groupItems]
					dictToReturn[sampleGroupItem] = [value[1] for value in sorted([item for item in indexedItems if item[0] is not None])] + [item[1] for item in indexedItems if item[0] is None]
				else:
					dictToReturn[sampleGroupItem] = sorted(groupItems)
			return dictToReturn
		
		elif sampleGroup in df.columns:
			if duplicates:
				return super(HSDataset, self).sampleGroupItems(sampleGroup=sampleGroup, duplicates=True)
				
			groupItems = set(df[sampleGroup])
			# order them if possible
			if sampleGroup in sgo:
				indexedItems = [(sgo[sampleGroup].index(item) \
								 if item in sgo[sampleGroup] else None, item) for item in groupItems if pandas.notnull(item)]
				return [value[1] for value in sorted([item for item in indexedItems if item[0] is not None])] + \
						[item[1] for item in indexedItems if item[0] is None]
			else:
				return sorted([item for item in groupItems if pandas.notnull(item)])

		else:
			return []
			
	def sampleGroupColours(self, sampleGroup=None):
		"""Return colour dictionary given sampleGroup, eg: {'Stem Cell':'#cccccc', ...}
		If sampleGroup==None, returns the dictionary with enclosing sample groups as keys, 
		eg: {'cell_lineage': {'Stem Cell':'#cccccc', ...}, ...}
		
		Parameters:
			sampleGroup: string, a member of self.sampleGroups()
			
		"""
		series = self._sampleGroupColours
		if sampleGroup:
			return series[sampleGroup] if sampleGroup in series else {}  # series[sampleGroup] is already a dict
		else:
			return series.to_dict()
		
	def sampleGroupOrdering(self, sampleGroup=None):
		"""Return list of ordered sample group items given sampleGroup, eg: ['LSK','MPP', ...]
		If sampleGroup==None, returns the dictionary with enclosing sample groups as keys, 
		eg: {'celltype': ['LSK','MPP', ...], ...}
		
		Parameters:
			sampleGroup: string, a member of self.sampleGroups()
			
		"""
		series = self._sampleGroupOrdering
		if sampleGroup:
			return series[sampleGroup] if sampleGroup in series else {}  # series[sampleGroup] is already a dict
		else:
			return series.to_dict()
	
	def sampleDistances(self):
		return self._sampleDistances
		
	def replicateSampleGroup(self):
		return self.sampleGroups(returnType='display')[0]

	def sampleTable(self):
		"""Ensure that 'sampleId' is always the name of the index, just in case it was left out.
		"""
		df = self._samples
		df.index.name = 'sampleId'
		return df
	
@mtex.mutual_exclusion
def saveDatasetSubset(ds, filepath, name, description, sampleIds, sampleGroupsDisplayed=[]):
	"""Work out a subset of ds which is an instance of HSDataset, using sampleIds, and save
	the resulting hdf5 file to filepath. Note that 'parent' key in '/series/attributes' dictionary
	will hold ds.name value so we know which dataset that it came from.
	"""
	store = ds.hdfStore()
	try:
		for key in store.keys():
			item = store[key]
			if key=='/series/attributes':
				item['name'] = name
				item['fullname'] = name
				item['description'] = description
				item['parent'] = ds.name
			elif key=='/series/sampleGroupsDisplayed' and len(sampleGroupsDisplayed)>0:
				item = pandas.Series(sampleGroupsDisplayed)
			elif key=='/dataframe/sampleDistances':
				item = item.loc[sampleIds,sampleIds]
			elif key=='/dataframe/samples':
				item = item.loc[sampleIds]
			elif key in ['/dataframe/counts', '/dataframe/cpm', '/dataframe/tpm', '/dataframe/expression']:
				item = item[sampleIds]
			item.to_hdf(filepath, key)
	except:
		store.close()
		raise
			
def convertSampleTable(df):
	"""Convert previous version of sample table with name and value columns to new format
	"""
	# First work out a list of columns to create
	columns = [(row['level'],row['name']) for index,row in df.iterrows()]
	# convert to a unique list, dropping unwanted columns
	seen = set()
	columns =[item for item in columns if not (item[1] in seen or seen.add(item[1])) and item[1]!='cmyk_colour']
	# +ve level columns first, then -ve
	columns = [item[1] for item in sorted(columns) if item[0]>=0] + [item[1] for item in sorted(columns) if item[0]<0]
	# some datasets have 'sample_id' and 'sampleId' entries in 'name' column - we can ignore one of these
	if 'sample_id' in columns and 'sampleId' in columns:
		columns = [item for item in columns if item!='sampleId']

	# row index will be sample ids
	sampleIds = sorted(set(df['sample_id']))

	# Gather data
	data = []
	for sampleId in sampleIds:
		subset = df[df['sample_id']==sampleId]
		data.append([sampleId] + [subset[subset['name']==column]['value'].tolist()[0] if column in subset['name'].tolist() else None for column in columns[1:]])
	
	return pandas.DataFrame(data, columns=['sampleId' if item=='sample_id' else item for item in columns]).set_index('sampleId')
    
# ------------------------------------------------------------
# Tests - eg. nosetests hsdataset.py
# ------------------------------------------------------------
def test_samples():
	"""Testing of sample related functions.
	"""
	ds = HSDataset("data/datasets/F0r3sT/PUBLIC/goodell.h5")
	assert ds.sampleGroups()==['celltype', 'cell_lineage', 'surface_markers', 'tissue', 'description', 'notes']
	assert ds.sampleGroups(returnType="display")==['celltype', 'cell_lineage', 'surface_markers', 'tissue']
	assert ds.sampleGroupItems(sampleGroup='celltype', groupBy='cell_lineage')['T Cell Lineage']==['T-CD4-A', 'T-CD4-N', 'T-CD8-A', 'T-CD8-N']
	
	return
	sg='celltype'
	for sampleGroup in ds.sampleGroups(returnType='display'):
		if sampleGroup==sg: continue
		sgi = ds.sampleGroupItems(sampleGroup=sg, groupBy=sampleGroup)
		values = sum(list(sgi.values()), [])
		if len(values)==len(set(values)):
			print('\n',sampleGroup, ds.sampleGroupItems(sampleGroup=sampleGroup))
			for k,v in six.iteritems(sgi):
				print(k,v)


def test_sampleGroupItems():
	ds = HSDataset("data/datasets/F0r3sT/PUBLIC/goodell.h5")
	assert len(ds.sampleGroupItems(sampleGroup='celltype', duplicates=True))==len(ds.expressionMatrix().columns)
	
def test_saveDatasetSubset():
	ds = HSDataset("data/datasets/F0r3sT/PUBLIC/goodell.h5")
	saveDatasetSubset(ds, "/tmp/goodellSubset.h5", "goodellSubset", "testing dataset subset function", ['B-Cell(1)','B-Cell(2)','HSC(1)','HSC(2)'])
	store = mtex.read_hdf_mutex("/tmp/goodellSubset.h5", '/series/attributes')
	assert store.description=='testing dataset subset function'

def test_datasetAttributes():
	d = datasetAttributes("data/datasets/F0r3sT/PUBLIC/goodell.h5")
	assert d['fullname']=='Goodell' 	

def test_createDatasetFile():
	sampleDis = mtex.read_hdf_mutex("data/datasets/F0r3sT/PUBLIC/goodell.h5", 'dataframe/sampleDistances')
	samples = mtex.read_hdf_mutex("data/datasets/F0r3sT/PUBLIC/goodell.h5", 'dataframe/samples')
	exp = mtex.read_hdf_mutex("data/datasets/F0r3sT/PUBLIC/goodell.h5", 'dataframe/expression')
	attr = mtex.read_hdf_mutex("data/datasets/F0r3sT/PUBLIC/goodell.h5", '/series/attributes').to_dict()
	kwargs = { 'name' : 'testCreateFile', 'attributes': attr, 'samples' : samples, 'sampleDistances' : sampleDis, 'expression' : exp }
	ds = createDatasetFile("/tmp/", **kwargs)
	assert ds.sampleDistances().size==sampleDis.size	
