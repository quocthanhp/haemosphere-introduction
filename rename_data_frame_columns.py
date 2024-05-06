"""
This script will rename the column names the samples dataframe of selected h5 files
to match the column names in the labsamples sql db

Adding a third command line argument, False, will write the changes to the h5 file.
Omitting this argument will only print the changes that would be made
"""
import pandas as pd
import sys
import os

from pyramid.paster import (
	get_appsettings,
	setup_logging,
	)
	
def usage(argv):
	cmd = os.path.basename(argv[0])
	print('usage: %s <config_uri> [var=value]\n'
			'(example: "%s development.ini")' % (cmd, cmd))
	sys.exit(1)


def main(argv=sys.argv):
	if len(argv) < 2:
		usage(argv)
	config_uri = argv[1]
	setup_logging(config_uri)
	settings = get_appsettings(config_uri)
	
	justChecking = True # Don't alter dataframe at all. Only print the changes to be made

	if(len(argv) == 3):
		if(argv[2] == "False"):
			justChecking = False



	directorypath = settings['haemosphere.model.datasets.root']


	stores = []

	###
	#	PUBLIC
	###
	stores.append(pd.HDFStore(directorypath + '/F0r3sT/PUBLIC/haemopedia-plus.2.6.h5'))
	stores.append(pd.HDFStore(directorypath + '/F0r3sT/PUBLIC/haemopedia.2.7.h5'))

	###
	#	PRIVATE/GROUPS/HILTONLAB
	###
	stores.append(pd.HDFStore(directorypath + '/F0r3sT/PRIVATE/GROUPS/CSL/hiltonlab-rnaseq-plus.1.3.h5'))
	stores.append(pd.HDFStore(directorypath + '/F0r3sT/PRIVATE/GROUPS/HiltonLab/hiltonlab-rnaseq.h5'))
	stores.append(pd.HDFStore(directorypath + '/F0r3sT/PRIVATE/GROUPS/HiltonLab/hiltonlab.h5'))
	stores.append(pd.HDFStore(directorypath + '/F0r3sT/PRIVATE/GROUPS/HiltonLab/megs.h5'))
	stores.append(pd.HDFStore(directorypath + '/F0r3sT/PRIVATE/GROUPS/HiltonLab/taoudi.h5'))

	###
	#	PRIVATE/GROUPS/NILSONLAB
	###
	stores.append(pd.HDFStore(directorypath + '/F0r3sT/PRIVATE/GROUPS/NilssonLab/nilsson-megs.h5'))


	for store in stores:

		df = store['/dataframe/samples']
		columns = df.columns.tolist()
		newColumns = dfColToSqlCol(columns)

		if justChecking:
			print('')
			print('=======NEW DATASET=======')
			compareNames(columns, newColumns)
		else:
			di, delDi = nameDict(columns, newColumns)
			for col in delDi:
				del df[col]	
			df.rename(columns=di, inplace=True)
			store['/dataframe/samples'] = df
			print(store['/dataframe/samples'])


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
        
    }.get(colName, ' ')


def compareNames(listA, listB):
	""" Print out each column name in a dataframe alongside the column name it has
		been mapped to
	"""
	numCols = len(listA) if len(listA) < len(listB) else len(listB)
	for i in range(0, numCols):
		print(listA[i] + ' --- ' + listB[i])


def nameDict(columns, newColumns):
	""" Split the new columns into two lists. One list of obsolete columns to be deleted
		from the datafram, and another list containing the names the columns in the dataframe
		will be renamed as
	"""
	di = {}
	delDi = []
	for i in range(len(newColumns)):
		if(newColumns[i] == ' '):
			delDi.append(columns[i])
		else:
			di[columns[i]] = newColumns[i]
	
	return di, delDi



if __name__ == '__main__':
    main()



