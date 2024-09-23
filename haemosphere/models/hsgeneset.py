import pandas

import genedataset.geneset
import haemosphere.views.mutex as mtex
	
class HSGeneset(genedataset.geneset.Geneset):
	# _cache = LRUCache()# This is a class-level attribute

	# def __new__(cls):
    #     # Check if the object is already cached
	# 	cached_instance = cls._cache.get(pathToHDF)
	# 	if cached_instance:
	# 		log.debug(f"******File name is {pathToHDF} from cache*******\n")
	# 		return cached_instance
        
	# 	instance = super(HSDataset, cls).__new__(cls)
	# 	cls._cache.set(pathToHDF, instance)
	# 	return instance

	@mtex.mutual_exclusion
	def __init__(self, name='unnamed', description=''):
		super(HSGeneset, self).__init__(name=name, description=description)
				
	def setScore(self, score):
		"""
		score is a nested dictionary: {'logFC':{'ENSG000043353':-7.89, 'ENSG00003533':4.32, ...}, 'adjPValue':{'ENSG000043353':-7.89, 'ENSG00003533':4.32, ...}, ...}
		Note: do not use dots in column names, to avoid possible problems with jsonified javascript objects.
		So use 'adjPValue' instead of 'adj.P.Val' for example.
		"""
		# adding such a dictionary to make up extra columns to existing dataframe is simple with pandas!
		self._dataframe = self._dataframe.join(pandas.DataFrame(score))
		
	def sort(self, column, ascending=True):
		"""
		Sort genes contained in this gene set based on column.
		Example: gs.sort('correlation').
		columns should be one of self._dataframe.columns, or 'absLogFC'. Since there is no absLogFC column,
		it will instead use absolute logFC to sort.
		reverse=True will make it descending.
		"""
		df = self.dataframe()
		if column in df.columns:
			self._dataframe = df.sort_values(column, ascending=ascending)
		elif column=="absLogFC" and 'logFC' in df.columns:
			df[column] = [abs(item) for item in df['logFC']]
			self._dataframe = df.sort_values(column, ascending=ascending).drop(column, axis=1)

def hsgenesetFromGeneIds(geneIds):
	"""Return a HSGeneset instance from Ensembl gene ids (list). 
	This is a wrapper for calling genedataset.Geneset with some default parameters.
	For large sized geneIds, consider just getting a dataframe using hsgeneset.HSGeneset().dataframe().loc[geneIds]
	which is much faster than using this method.
	"""
	return HSGeneset().subset(queryStrings=geneIds, searchColumns=["EnsemblId"], caseSensitive=True, matchSubstring=False)

# ------------------------------------------------------------
# Tests - eg. nosetests hsgeneset.py
# ------------------------------------------------------------
def test_setScore():
	gs = HSGeneset()
