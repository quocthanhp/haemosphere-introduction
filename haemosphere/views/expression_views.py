from __future__ import absolute_import
from pyramid.view import view_config
import numpy

from haemosphere.models import hsgeneset
from .hsdataset_views import datasetAttributes, datasetFromName
from .views import setSelectedDataset, setSelectedGene
from .utility import params
import six

import time
import logging
log = logging.getLogger(__name__)

def getSelectedDatasetExpressionPreference(request):
	return request.session['preferences'].get('expression/selectedDatasetName') if 'preferences' in request.session else None

def _allGenesInDataset(ds):
	"""
	Return all gene ids and corresponding symbols in this dataset instance ds.
	Example usage: 
		ds = hsdataset.datasetFromName("Haemopedia")
		allGeneIds, allGenes = _allGenesInDataset(ds):
	ds must be an instance of hsdataset.HSDataset.
	Returns a tuple, where the first element is a list of all geneIds found in the dataset 
	(basically the index of the expression matrix), and the second element looks like 
	[{"EnsemblId":"ENSGxxxx", "GeneSymbol":"Gene1"},...].
	"""
	allGeneIds = ds.expressionMatrix().index if ds.isRnaSeqData else ds.geneIdsFromProbeIds(ds.expressionMatrix().index)
	df = hsgeneset.HSGeneset().dataframe()
	df = df.loc[set(allGeneIds).intersection(df.index)]
	df.index.name = "EnsemblId"
	return allGeneIds, df.sort_values("GeneSymbol").reset_index()[["EnsemblId","GeneSymbol"]].dropna().drop_duplicates().to_dict(orient="records")

# ---------------------------------------------------------
# Expression related
# ---------------------------------------------------------
@view_config(route_name="/expression/show", renderer="haemosphere:templates/expression.mako")
def showExpression(request):
	"""
	Given gene id and dataset name, return the expression plot template.
	The template requires a lot of variables to work, so list all of them up front.
	Currently only works with one gene, but only small mods will be necessary to include more genes
	in future, hence the use of Geneset instance rather than a single gene.
	"""
	# variables to return - must provide defaults here because many of these may be empty when there is an error
	error = ''	# template will just show the error message if this is not blank
	ePref = {}

	gs = ''	# json form of genes to show [{'EnsemblId':'ENSG0000034343', ... }, ... ]
	matchingDatasets = []	# list of dictionary containing datasets to show [{'name':'haemopedia', 'species':'MusMusculus', ... }, ...]
	selectedDatasetName = ''	# template will select first dataset if this is not supplied

	expressionValues = {}	# same format as required by expbarplot.ExpressionBarplot.
	cpmValues = {}	# same format as expressionValues but using cpm, empty for microarray dataset
	valueRange = []  # min,max values for the whole dataset rather than genes shown on the template, used for scaling
	featureGroups = []	# same format as required by 

	groupByItems = []	# ['celltype','cell_lineage',...]
	sampleGroupItems = {}	# {'cell_lineage': {}, 'celltype': {'cell_lineage': {'Cell Line':['FD',...], ... }, ... }, ... }
	selectedGroupByItem = ''
	selectedColourByItem = ''
	sampleIdsFromSampleGroups = {}	# {'celltype':{'HSC':['HSC(1)','HSC(2)'], ...}, ... }
	sampleGroupColours = {}	# {'cell_lineage': {'B Cell Lineage':'#cccccc', ... }, ... }
	sampleGroupOrderedItems = {}	# {'cell_lineage': ['Multi Potential Progenitor', ... ], ... }

	valueAxisLabel = ''
	groupAxisLabel = ''
	allGenes = []

	# Input params:
	geneIds = request.params.getall("geneId")	# multiples OK
	if not geneIds: # if there's no selectedGeneId, we just provide one (Gata1)
		geneIds = [request.session.get("selectedGeneId", "ENSMUSG00000031162")]
	selectedDatasetName = request.params.get("datasetName", request.session.get('selectedDatasetName'))	# can be left out
	selectedGroupByItem = request.params.get("groupByItem") # can be left out

	# Geneset instance for all requested gene ids - will assume all genes in the geneset are same species
	gs = hsgeneset.HSGeneset().subset(queryStrings=geneIds, searchColumns=["EnsemblId"])

	# subset of the datasets user has access to, where species matches geneset species
	matchingDatasets = [ds for ds in datasetAttributes(request) if ds['species']==gs.species()]

	# If no dataset has been selected through the request, try to get it from session preferences, 
	# but only if it's a member of matchingDatasets.
	sde_preference = getSelectedDatasetExpressionPreference(request)
	if not selectedDatasetName and sde_preference:	
		if sde_preference in [ds['name'] for ds in matchingDatasets]:
			selectedDatasetName = sde_preference

	# It is also possible that selectedDatasetName matches a different species to matchingDatasets
	# in which case select first dataset from matchingDatasets
	datasetWithMatchingName = [ds for ds in datasetAttributes(request) if ds['name']==selectedDatasetName]
	if len(datasetWithMatchingName)>0 and matchingDatasets and datasetWithMatchingName[0]['species']!=matchingDatasets[0]['species']:
		selectedDatasetName = matchingDatasets[0]['name']

	# Now there are several possibilities for datasets
	if not matchingDatasets:
		error = "There is no expression data for this gene in any of the datasets."    	
	elif selectedDatasetName and selectedDatasetName not in [ds['name'] for ds in matchingDatasets]:
		error = "There is no expression data for this gene in any of the datasets."
	else:	# selectedDatasetName may or may not have been specified
		eValues = {}
		ds = None
		
		if selectedDatasetName:	# this has been specified, so find expression values for matching dataset
			ds = datasetFromName(request, [dset['name'] for dset in matchingDatasets if dset['name']==selectedDatasetName][0])
			eValues = ds.expressionValues(geneIds=geneIds)
			if not eValues['values']:
				error = "No expression value for the gene for requested dataset"
		else:	# find the first dataset where expression values can be found, and use this for selectedDatasetName		
			for item in matchingDatasets:
				dset = datasetFromName(request, item['name'])
				eValues = dset.expressionValues(geneIds)
				if len(eValues['values'])>0:
					selectedDatasetName = dset.name
					ds = dset
					break
			if not eValues['values']:
				error = "No expression values found in any of the datasets for the gene"

		if not error:	# looks OK to plot, so supply all necessary variables
			expressionValues = eValues['values']
			if ds.isRnaSeqData:  # take log of values
				logValues = {}
				for geneId,vals in six.iteritems(expressionValues):
					logValues[geneId] = dict([(sampleId, numpy.log2(val+1)) for sampleId,val in six.iteritems(vals)])
				expressionValues = logValues
			else:
				valueRange = ds.valueRange()

			featureGroups = eValues['featureGroups']
			groupByItems = ds.sampleGroups(returnType="display")	# only need sample groups for display

			if not selectedGroupByItem: # try celltype, if not pick the first sample group item
				if "celltype" in groupByItems:
					selectedGroupByItem = "celltype"
				elif len(groupByItems)>0:
					selectedGroupByItem = groupByItems[0];
			
			if not selectedColourByItem: # try cell_lineage, if not pick the second sample group item
				if "cell_lineage" in groupByItems:
					selectedColourByItem = "cell_lineage"
				elif len(groupByItems)>1:
					selectedColourByItem = groupByItems[1];
			
			# Work out sampleGroupItems, which gives ordered list of sample group items for 
			# sample group combinations. eg: sampleGroupItems['celltype']['cell_lineage'] may be
			# {'B Cell Lineage':['ProB','PreB'], ... }. This is used by the template to work out colourBy
			# which groups bars into same colours. If the combination of sample groups don't occur in this
			# dictionary, it implies that colourBy can't be done.
			for sg in groupByItems:
				sampleGroupItems[sg] = {}
				for sampleGroup in groupByItems:
					if sampleGroup==sg: continue
					sgi = ds.sampleGroupItems(sampleGroup=sg, groupBy=sampleGroup)
					values = sum(list(sgi.values()), [])
					if len(values)==len(set(values)):
						sampleGroupItems[sg][sampleGroup] = sgi
			
			# dictionary of sample ids keyed on sample group and sample group items {'celltype':{'HSC':['HSC(1)','HSC(2)'], ...}, ... }
			sampleIds = ds.sampleIdsFromSampleGroups()
			# we only need sample groups in groupByItems
			sampleIdsFromSampleGroups = dict([(key,sampleIds[key]) for key in sampleIds.keys() if key in groupByItems])

			# colours for sample groups
			sampleGroupColours = ds.sampleGroupColours()
			
			# specify ordering of sample group items within a sample group
			sampleGroupOrderedItems = dict([(sampleGroup, ds.sampleGroupItems(sampleGroup=sampleGroup)) for sampleGroup in groupByItems])
			
			# label to use for the value axis of the plot 
			valueAxisLabel = 'log2(tpm+1)' if ds and ds.isRnaSeqData else 'log2'

			allGeneIds,allGenes = _allGenesInDataset(ds)

		# set selectedDatasetName and selectedGeneId
		setSelectedDataset(request, datasetName=selectedDatasetName)
		setSelectedGene(request, geneId=geneIds[0])

	return {"error": error,
			"ePref": ePref,
			"geneset": gs.to_json(), 
			"datasets": [{'name':ds['name'], 'species':ds['species'], 'platform_type':ds['platform_type'], 'rnaseq':ds['platform_type']=="rna-seq"} for ds in matchingDatasets],
			"selectedDatasetName": selectedDatasetName,
			"expressionValues": expressionValues,
			"valueRange": valueRange,
			"featureGroups": featureGroups,
			"groupByItems": groupByItems,
			"sampleGroupItems": sampleGroupItems,
			"selectedGroupByItem": selectedGroupByItem,
			"selectedColourByItem": selectedColourByItem,
			"sampleIdsFromSampleGroups": sampleIdsFromSampleGroups,
			"sampleGroupColours": sampleGroupColours,
			"sampleGroupOrderedItems": sampleGroupOrderedItems,
			"valueAxisLabel": valueAxisLabel, 
			"groupAxisLabel": '',
			"allGenes": allGenes
			}
	'''			
			# fetch preferences 
			ePref = getExpressionPreferences(request, selectedDatasetName)


	if ePref and (not selectedGroupByItem or selectedGroupByItem not in map(lambda x: x['name'], groupByItems)):  # try to get it from ePref
		selectedGroupByItem = ePref.get('selectedGroupByItem')

	return { "sampleDataDict":sdd, "sampleGroupData":sgd, "sampleColourDict":scd, 
				"selectedColourByItem":ePref.get('selectedColourByItem') if ePref else None,
			}
	'''

@view_config(route_name="/expression/multispecies", renderer="haemosphere:templates/expression_multispecies.mako")
def showExpressionMultiSpecies(request):
	"""
	Given geneId, show expression of this gene and its orthologue, summarised at cell_lineage level across all datasets.
	The page should also work for a gene without an orthologue. selectedDataset is the parameter which controls
	which datasets to show. By default, if this parameter is not specified, there will be at least 
	defaultNumberOfDatasets shown. To explicitly not return any datasets use "MusMusculus_none" or "HomoSapiens_none".
	Note: there are hard-coded lineage names in this function.
	"""
	# Input params.
	geneId = params(request, "geneId", request.session.get("selectedGeneId"))
	selectedDatasets = request.params.getall("selectedDataset")
		
	# Define the variables which will get passed onto the template
	error = ''	# template will just show the error message if this is not blank
	gene = {}
	orthGene = {}
	lineageGroups = ["Progenitor","Meg/Ery","Granulocytes","Mac/DC","B Cells","T Cells","Innate Lymphocytes"]
	expressionValues = []
	valueRanges = []
	columnNames = []
	colours = []
	datasetNames = []
	defaultNumberOfDatasets = 2
	
	# get all dataset attributes the user has access to, and filter the list on a number of factors
	datasetsToUse = {'MusMusculus':[], 'HomoSapiens':[]}
	for item in [item for item in datasetAttributes(request) if item['name']!='Haemopedia-Plus' and \
		"celltype" in item['sampleGroups'] and "cell_lineage" in item['sampleGroups']]:
		datasetsToUse[item['species']].append(item)

	# Fetch geneset matching the gene id, so we can get some info about the gene.
	df = hsgeneset.HSGeneset().dataframe()
	if geneId not in df.index:
		error = "Matching gene not found in the system."
	else:
		gene = df.loc[geneId].to_dict()  # assumes only one geneId hence .loc returning a Series
		gene["EnsemblId"] = geneId

		# Check orthologue: gene['Orthologue'] looks like 'ENSG00003435:Gene1,ENSG00002525:Gene2' (multiple orthologues possible)
		orthGeneIds = set([item.split(':')[0] for item in gene['Orthologue'].split(',') if item.split(':')[0]])
		orthGeneIds = list(orthGeneIds.intersection(set(df.index)))
		if len(orthGeneIds)>0: 
			# what to do with multiple matches? Using the first match for now
			orthGene = df.loc[orthGeneIds[0]].to_dict()
			orthGene["EnsemblId"] = orthGeneIds[0]
			
		lineages = [["Multi Potential Progenitor", "Restricted Potential Progenitor"],
					["Erythrocyte Lineage", "Megakaryocyte Lineage"],
					["Mast Cell Lineage", "Basophil Lineage", "Eosinophil Lineage", "Neutrophil Lineage"], 
					["Macrophage Lineage", "Dendritic Cell Lineage"], 
					["B Cell Lineage"], 
					["T Cell Lineage"], 
					# have this in here as we have two different lineage names for NK cells, but both will eventually be called Innate Lymphocyte to match immgen 
					["NK Cell Lineage","Innate Lymphocyte Lineage"]]
				
		# get lineage colours from haemopedia dataset, for datasets where this isn't specified
		coloursFromLineage = datasetFromName(request, "Haemopedia").sampleGroupColours(sampleGroup="cell_lineage")
				
		# filter these based on selectedDatasets
		filteredDatasetsToUse = {}
		for species,items in six.iteritems(datasetsToUse):
			filteredDatasetsToUse[species] = [item for item in items if item['name'] in selectedDatasets]
		
		# Now what if there aren't enough datasets in filteredDatasetsToUse after this? We add some more, unless
		# user has specified less than defaultNumberOfDatasets.
		# Note that we can still end up with less datasets than assigned here, if there are no expression values
		# found for a dataset below.
		for species,items in six.iteritems(datasetsToUse):
			for item in items:
				# First test is to see if we have less than defaultNumberOfDatasets in this species but this
				# was deliberately chosen by the user, because at least one of the selectedDatasets is in
				# filteredDatasetsToUse. Second test is to see if we have the default number when nothing was specified.
				if len(filteredDatasetsToUse[species])<defaultNumberOfDatasets and \
					len(set(selectedDatasets).intersection(set([ds['name'] for ds in filteredDatasetsToUse[species]])))>0 \
					or len(filteredDatasetsToUse[species]) >= defaultNumberOfDatasets:
					continue
				elif item['name'] not in selectedDatasets:
					filteredDatasetsToUse[species].append(item)

		# If no dataset has been requested for a species specifically, we remove all datasets for that species
		for species in datasetsToUse.keys():
			if "%s_none" % species in selectedDatasets:
				filteredDatasetsToUse[species] = []

		if len(orthGeneIds)==0:  # no orthologue, so don't need any datasets of the orthologue species
			filteredDatasetsToUse['MusMusculus' if gene['Species']=='HomoSapiens' else 'HomoSapiens'] = []

		# populate the variables - most will be a list of same length as the number of datasets to show
		for species,items in six.iteritems(filteredDatasetsToUse):
			for item in items:
				# fetch matching row from expression data - take max value for each sample for multiple probes
				ds = datasetFromName(request, item['name'])
				if item['species']==gene['Species']:
					values = ds.expressionMatrix(geneIds=geneId, sampleGroupForMean="celltype").max()
				else:
					values = ds.expressionMatrix(geneIds=orthGeneIds[0], sampleGroupForMean="celltype").max()
				
				if len(values)==0:
					continue
				elif ds.isRnaSeqData:
					values = numpy.log2(values+1)
			
				celltypesFromLineage = ds.sampleGroupItems(sampleGroup="celltype", groupBy="cell_lineage")
						
				expressionValueRow = []
				columnNameRow = []
				colourRow = []
				for i,group in enumerate(lineageGroups):
					# data exists at the lineage level and not at lineageGroups, so collect data at that level
					# and flatten out to lieageGroup level.
					celltypes = []  # should end up with ['LTHSC', 'STHSC',...]
					colourItems = []
					for lineage in lineages[i]:
						for celltype in celltypesFromLineage.get(lineage, []):
							celltypes.append(celltype)
							colourItems.append(coloursFromLineage.get(lineage,"grey"))
					expressionValueRow.append(values[celltypes].tolist())
					columnNameRow.append(celltypes)
					colourRow.append(colourItems)
				
				if len(sum(expressionValueRow, []))==0:  # no matching celltypes found for this dataset
					continue
				
				expressionValues.append(expressionValueRow)
				valueRange = ds.valueRange()
				if ds.isRnaSeqData:
					valueRange = [numpy.log2(item+1) for item in valueRange]
				valueRanges.append(valueRange)
				columnNames.append(columnNameRow)
				colours.append(colourRow)
				datasetNames.append("%s, %s, %s, %s" % (gene["GeneSymbol"] if ds.species==gene['Species'] else orthGene["GeneSymbol"], 
														ds.name, 
														"mouse" if ds.species=="MusMusculus" else "human",
														ds.platform_type))

	return {"gene": gene,
			"orthGene": orthGene,
			"lineageGroups": lineageGroups,
			"expressionValues": expressionValues,
			"valueRanges": valueRanges,
			"columnNames": columnNames,
			"colours": colours,
			"datasetNames": datasetNames,
			"datasetsToUse": datasetsToUse,
			"error": error
			}

@view_config(route_name="/expression/genevsgene", renderer="haemosphere:templates/gene_vs_gene.mako")
def showExpressionGeneVsGene(request):
	"""
	Plot gene vs gene expression, given dataset name, and two genes. If both genes can't be found, error variable
	is filled out.
	"""
	import pandas
	from scipy.stats import pearsonr


	ofetch_time = time.time()
	log.debug("\n====================\nshowExpressionGeneVsGene started\n====================\n")

	# Parse parameters
	selectedDatasetName = params(request, "datasetName", request.session.get('selectedDatasetName'))	# can be left out
	gene1 = params(request, "gene1")  # should be Ensembl ids
	gene2 = params(request, "gene2")

	error = ""
	geneIds = [gene1, gene2]

	# Matching dataset from name
	datasets = datasetAttributes(request)
	if not selectedDatasetName:  # just use the first one
		selectedDatasetName = datasets[0]["name"]


	log.debug(request)
	log.debug(selectedDatasetName)

	ds = datasetFromName(request, selectedDatasetName)

	nfetch_time = time.time()
	log.debug(f"datasetFromName completed in {nfetch_time - ofetch_time:.2f} seconds.")
	ofetch_time = nfetch_time

	

	# Fetch all gene ids and corresponding symbols in this dataset
	allGeneIds,allGenes = _allGenesInDataset(ds)

	nfetch_time = time.time()
	log.debug(f"_allGenesInDataset completed in {nfetch_time - ofetch_time:.2f} seconds.")
	ofetch_time = nfetch_time

	
	# Check if geneIds are valid or found in the dataset, otherwise try selectedGeneId, then first genes in the dataset
	for i,geneId in enumerate(geneIds):
		if geneId is None or geneId not in allGeneIds:
			if request.session.get("selectedGeneId") and request.session.get("selectedGeneId") in allGeneIds:
				geneIds[i] = request.session.get("selectedGeneId")
			else:
				geneIds[i] = allGeneIds[i]

	nfetch_time = time.time()
	log.debug(f"enumerate(geneIds) completed in {nfetch_time - ofetch_time:.2f} seconds.")
	ofetch_time = nfetch_time

	# Get info on each gene
	genes = hsgeneset.hsgenesetFromGeneIds(geneIds).dataframe().reset_index().to_dict(orient="records")

	nfetch_time = time.time()
	log.debug(f"hsgenesetFromGeneIds completed in {nfetch_time - ofetch_time:.2f} seconds.")
	ofetch_time = nfetch_time

	# List of cell lineage values
	lineages = ds.sampleGroupItems(sampleGroup="cell_lineage")
	lineageColours = {}

	# Expression values for both genes (note that eValues["values"] holds tpm values)
	eValues = ds.expressionValues(geneIds=geneIds)

	# Calculated values of expression for each gene
	celltypesFromLineage = {}
	valuesFromLineage = {geneIds[0]:{}, geneIds[1]:{}}
	correlationsFromLineage = {}  # pearson correlation at each lineage level; add "all" lineage for all lineages
	sampleIdsFromGroupItems = ds.sampleIdsFromSampleGroups()  # {'celltype':{'HSC':['HSC(1)','HSC(2)'], ...}, ... }
	if "celltype" not in ds.sampleGroups(returnType="display") or "cell_lineage" not in ds.sampleGroups(returnType="display"):
		error = "celltype or cell_lineage not found in this dataset. Currently this function is only available to datasets with these sample groups defined."
	else:
		for lineage,celltypes in six.iteritems(ds.sampleGroupItems(sampleGroup="celltype", groupBy="cell_lineage")):
			celltypesFromLineage[lineage] = celltypes
			for gene in geneIds:
				valuesFromLineage[gene][lineage] = []
				# the value for each celltype is the mean of all values at sample ids of this celltype 
				for celltype in celltypes:
					if ds.isRnaSeqData:  # expect keys of eValues["values"] to be the same as gene1,gene2
						values = [eValues["values"][gene][sampleId] for sampleId in sampleIdsFromGroupItems["celltype"][celltype]]
						valuesFromLineage[gene][lineage].append(numpy.mean([numpy.log2(item+1) for item in values]))
					else:  # multiple probes may exist for this gene - take highest value for each sample id
						data = []
						for probeId in eValues["featureGroups"][gene]:
							data.append([eValues["values"][probeId][sampleId] for sampleId in sampleIdsFromGroupItems["celltype"][celltype]])
						values = pandas.DataFrame(data).max()
						valuesFromLineage[gene][lineage].append(numpy.mean(values))
			values = [valuesFromLineage[geneIds[0]][lineage], valuesFromLineage[geneIds[1]][lineage]]
			valid = all(len(item)>2 and numpy.var(item)>0 for item in values)
			correlationsFromLineage[lineage] = pearsonr(values[0],values[1])[0] if valid else None

		# now calculate pearson correlation for all points
		values = [sum([valuesFromLineage[geneIds[0]][lineage] for lineage in lineages],[]), sum([valuesFromLineage[geneIds[1]][lineage] for lineage in lineages],[])]
		valid = all(len(item)>2 and numpy.var(item)>0 for item in values)
		correlationsFromLineage["all"] = pearsonr(values[0],values[1])[0] if valid else None

		lineageColours = ds.sampleGroupColours(sampleGroup="cell_lineage")


	nfetch_time = time.time()
	log.debug(f"total time in {nfetch_time - ofetch_time:.2f} seconds.")
	ofetch_time = nfetch_time

	log.debug("\n====================\nshowExpressionGeneVsGene return\n====================\n")

	return {"error": error,
			"datasets": datasets,
			"selectedDatasetName": selectedDatasetName,
			"geneIds": geneIds,
			"genes": genes,
			"allGenes": allGenes,
			"lineages": lineages,
			"lineageColours": lineageColours,
			"celltypesFromLineage": celltypesFromLineage,
			"valuesFromLineage": valuesFromLineage,
			"correlationsFromLineage": correlationsFromLineage
			}
