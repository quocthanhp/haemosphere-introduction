from __future__ import absolute_import
import os

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

from haemosphere.models import hsgeneset

from .user_views import currentUser
from .utility import forest, params, addGenesetToSession
from .hsdataset_views import datasetAttributes, datasetFromName
from .views import setSelectedDataset, setSelectedGene
import six
from six.moves import range

# ---------------------------------------------------------
# geneset related
# ---------------------------------------------------------
@view_config(route_name="/geneset/current", renderer="haemosphere:templates/geneset.mako")
def showCurrentGeneset(request):
	"""
	Show the geneset page, using the list of genesets saved in sessions.
	"""
	# Parse input
	index = request.params.get('index','-1')
	index = int(index)	if index.isdigit() else -1 # select specific geneset from history - can be left out
	savedGenesetName = request.params.get('savedGeneset')	# select specific geneset from saved genesets - can be left out
	downloadfile = params(request, 'downloadRObjects', False)
	
	# fetch user's list of saved genesets and locations
	user = currentUser(request)
	savedGenesets = [item[0] for item in forest(request).inventory(user.username, user.groupnames(), clean=True, sieve='p')] if user else []
		
	# if a specific index of genesets in history is requested, place this as the first element
	if index!=-1 and index<len(request.session['genesets']):	
		# specified an index of geneset to show, so shuffle genesets around
		request.session['genesets'].insert(0, request.session['genesets'].pop(index))
	
	# if a specific saved geneset is requested, place this in the session
	if savedGenesetName and user:
		gs = forest(request).loadfile(user.username, savedGenesetName + '.p')
		request.session['genesets'].insert(0, gs)

	return {'historyGenesets':request.session['genesets'], 
			'savedGenesets':savedGenesets, 
			'datasets':[{'name':ds['name'], 'species':ds['species']} for ds in datasetAttributes(request)],
			'guestUser':user is None,
			'downloadfile':downloadfile}

@view_config(route_name="/geneset/save", permission="view", renderer="json")
def saveCurrentGeneset(request):
	"""
	Save current geneset on the server. Only available to registered users, hence permission='view'

	Request parameters
	----------
	name: string, name of the geneset
	description: string, description of the geneset
	geneIds: a list of gene ids to create a subset of current geneset; can be left out to avoid subsetting

	"""
	if not request.session['genesets']: return {}
	gs = request.session['genesets'][0]
	
	# Input params
	gs.name = params(request, 'name')
	gs.description = params(request, 'description')
	geneIds = params(request, 'geneIds')
	
	if geneIds and len(geneIds)>0: 
		gs = gs.subset(queryStrings=geneIds, searchColumns=['GeneId'])
	forest(request).picklefile(request.authenticated_userid, gs, gs.name + '.p')
	return {'success':gs.size()}

@view_config(route_name="/geneset/rename", renderer="json")
def renameGeneset(request):
	"""
	Rename specified saved or history geneset.

    Request parameters
    ----------
    type: one of ['saved','history']
    id: geneset name if type=='saved', index of history geneset if type=='history'
    newName: string representing the new name of the geneset.

	"""
	# Parse input
	type = request.params.get('type')
	id = request.params.get('id')
	newName = request.params.get('newName')
	if id is None: return {'error':'No id specified'}
	
	if type=='saved':	# rename a saved geneset
		user = currentUser(request)
		if not user: return {'error':'No user associated with this saved gene set.'}
		savedGenesetInventory = forest(request).inventory(user.username, user.groupnames(), clean=True, sieve='p')
		
		import os
		for i in range(len(savedGenesetInventory)):
			if id==savedGenesetInventory[i][0]:
				filepath = savedGenesetInventory[i][1]
				os.rename(filepath,'%s/%s%s' % (os.path.dirname(filepath), newName, os.path.splitext(filepath)[1]))
				return {'success': i}

	elif type=='history':
		if int(id)<len(request.session['genesets']):	# rename matching geneset
			request.session['genesets'][int(id)].name = newName
			return {'success':id}
			
	return {'error':'unexpected error with /geneset/rename'}
	
@view_config(route_name="/geneset/delete", renderer="json")
def deleteGeneset(request):
	"""
	Delete specified or all saved genesets.
	"""
	# Parse input. If id is None, all saved genesets will be deleted.
	type = request.params.get('type')
	id = request.params.get('id')
	
	if type=='saved':	# delete saved genesets
		user = currentUser(request)
		if not user: return {'error':'No user associated with this saved gene set.'}
		savedGenesetInventory = forest(request).inventory(user.username, user.groupnames(), clean=True, sieve='p')
		
		import os
		if id is None:	# remove all saved genesets
			for inv in savedGenesetInventory: os.remove(inv[1])
			return {'success': 'deleted all saved genesets'}
		else:	# remove matching saved geneset
			for item in savedGenesetInventory:
				if id==item[0]:
					os.remove(item[1])
					return {'success': id}

	elif type=='history':
		if id is None:	# remove all genesets in history, except the current one
			request.session['genesets'] = request.session['genesets'][:1]
			return {'success': 'deleted all history genesets'}
		elif int(id)<len(request.session['genesets']):	# remove matching genest
			request.session['genesets'].pop(int(id))
			return {'success':id}
			
	return {'error':'unexpected error with /geneset/delete'}

@view_config(route_name="/geneset/modify", renderer="json")
def modifyGeneset(request):
	"""
	Add or subtract genes from current geneset.
	"""
	if not request.session['genesets']: return {}
	gs = request.session['genesets'][0]
	
	# Input params
	geneIds = params(request, 'geneIds')
	action = params(request, 'action')
	
	if action=='remove':	# remove selected gene ids, so redefine geneIds
		geneIds = [geneId for geneId in gs.geneIds() if geneId not in geneIds]
		
	if len(geneIds)==0:
		return {'error':'no gene ids matched the request'}
		
	newGs = hsgeneset.HSGeneset(name=gs.name, description=gs.description).subset(queryStrings=geneIds, searchColumns=['GeneId'], matchSubstring=False, caseSensitive=True)
	if newGs.size()>0:
		addGenesetToSession(request,newGs)
		return {'success':newGs.size()}
	else:
		return {'error':'Could not create a new gene set based on gene ids provided.'}

@view_config(route_name="/geneset/orthologue", renderer="json")
def showOrthologues(request):
	'''Fetch all existing orthologues for the current geneset, or orthologues for specified
	geneIds. Creates a new HSGeneset instance based on the orthologues and makes it the current
	geneset. Returns 'success' or 'error' key depending on success.
	'''
	# Parse input
	geneIds = params(request, 'geneIds')
	
	if geneIds:
		gs = hsgeneset.HSGeneset().subset(queryStrings=geneIds, searchColumns=['GeneId'])
		if gs.size()>0: gs.name = gs.geneSymbols()[0]
	elif request.session['genesets']:
		gs = request.session['genesets'][0]
	else:
		return {'error':'No gene id specified or a current gene set to work with.'}

	newGs = hsgeneset.HSGeneset(name='%s orthologues' % gs.name, description='orthologues of genes in %s' % gs.name)
	newGs = newGs.subset(queryStrings=gs.orthologueGeneIds(), searchColumns=['GeneId'])
	if newGs.size()>0:
		addGenesetToSession(request,newGs)
		return {'success':newGs.size()}
	else:
		return {'error':'Could not create the orthologue geneset in /geneset/orthologue'}

@view_config(route_name="/geneset/corr", renderer="json")
def showCorrelatedGenes(request):
	'''
	Create a new geneset with correlation scores for specified geneId and datasetName.
	The geneset will have 100 most positively correlated genes, and 100 most negatively correlated genes.
	'''
	# Input params
	featureId = request.params.get('featureId')
	datasetName = request.params.get('datasetName')
	cutoff = request.params.get('cutoff', 100)
	
	ds = datasetFromName(request, datasetName)
	if not ds: return {'error':"No matching dataset found - this is an unexpected error."}

	geneId = featureId if ds.isRnaSeqData else ds.geneIdsFromProbeIds(probeIds=[featureId])[0]
	geneSymbol = hsgeneset.HSGeneset().geneSymbols(returnType="dict")[geneId]
	
	score = ds.correlation(featureId)
	if len(score)==0:
		return {'error':'Unexpected error happened during correlation calculation'}
	
	# sort score
	scoreLow = sorted([[val,key] for key,val in six.iteritems(score)])[:cutoff]
	scoreHigh = sorted([[val,key] for key,val in six.iteritems(score)], reverse=True)[:cutoff]
	score = dict([(item[1],item[0]) for item in scoreLow+scoreHigh])
	
	#pandas.concat([df.sort(columns="correlation").iloc[:cutoff,:], df.sort(columns="correlation", ascending=False).iloc[:cutoff,:]]).to_dict()
	geneIds = list(score.keys())

	# Create a new geneset using geneIds. Use gene symbol and use it in geneset name and description
	# matching featureId from gs, since it is always contained in gs.
	gs = hsgeneset.HSGeneset().subset(queryStrings=list(geneIds), searchColumns=['geneId'])
	if gs.size()==0:
		return {'error':'Unexpected error in creating a geneset after successful correlation calculation'}
	
	# set score values to geneset and add to session
	gs.name = 'Find similar: %s (%s)' % (geneSymbol, datasetName) if ds.isRnaSeqData else 'Find similar: %s (%s in %s)' % (geneSymbol, featureId, datasetName)
	gs.description = 'Geneset from find similar search, gene: %s (%s), dataset %s.' % (geneSymbol, featureId, datasetName)
	gs.setScore({"correlation":score})
	gs.sort("correlation", ascending=False)
	addGenesetToSession(request, gs)

	# set dataset and gene as selected defaults
	setSelectedDataset(request, ds.name)
	setSelectedGene(request, geneId)
	return {'genesetSize':gs.size()}

@view_config(route_name="/geneset/heatmap", renderer="haemosphere:templates/heatmap.mako")
def showHeatmap(request):
	"""Show the heatmap page based on current geneset and selected dataset. Since gene ids can be specified to restrict the number of 
	genes in the current geneset, use post data rather than get to avoid URI too large errors.
	"""
	allDatasets = datasetAttributes(request)
	
	# Parse input
	geneIdString = params(request, 'geneId')  # "ENS0000034241&ENS000052324&..." gene ids joined up into one string; use all genes in current geneset if left out
	datasetName = params(request, 'datasetName', request.session.get('selectedDatasetName', (allDatasets[0]).get('name')))
	selectedSampleGroup = params(request, 'sampleGroup')  # "celltype"; selected sample group for aggregation - choose first available if left out
	maxFeatures = params(request, 'maxFeatures', 300)
	selectedGeneIds = geneIdString.split('&') if geneIdString else []
		
	if 'genesets' not in request.session or len(request.session['genesets'])==0:
		request.session.flash('No gene set available', 'dataerror')
		url = request.route_url('/geneset/current')
		return HTTPFound(location=url)
		
	gs = request.session['genesets'][0]
	
	# geneset may be filtered
	if selectedGeneIds: 
		gs = gs.subset(queryStrings=selectedGeneIds, searchColumns=['GeneId'])

	# need list of datasets and sample groups
	datasetProperties = []
	sampleGroups = {}
	for ds in allDatasets:
		if gs.species()==ds.get('species'):
			datasetProperties.append({'name':ds.get('name'), 'isRnaSeqData':ds.get('isRnaSeqData')})
		sampleGroups[ds['name']] = ds.get('sampleGroups')
		
	selectedDataset = next(datasetFromName(request,ds.get('name')) for ds in allDatasets if ds.get('name')==datasetName)
	
	if not selectedSampleGroup or selectedSampleGroup not in sampleGroups[selectedDataset.name]:
		selectedSampleGroup = sampleGroups[selectedDataset.name][0]

	# fetch expression matrix for selectedDataset with geneset
	import numpy, pandas
	from scipy import stats
	df = selectedDataset.expressionMatrix(geneIds=gs.geneIds(),sampleGroupForMean=selectedSampleGroup)
	if selectedDataset.isRnaSeqData:	
		# filter out genes with all zero values, and use log2 values (of tpm which come from expressionMatrix())
		max = df.max(axis=1)
		df = numpy.log2(df.loc[max[max>0].index] + 1)
	
	# columnLabels depend on sampleGroupItems
	sgi = selectedDataset.sampleGroupItems(sampleGroup=selectedSampleGroup)

	# Some datasets do not have sampleGroupOrdering defined for celltype, but may have it defined for cell_lineage.
	# In this case it would be better to use that to sort celltype.
	if selectedSampleGroup=="celltype" and 'cell_lineage' in selectedDataset.sampleGroups() \
		and selectedDataset.sampleGroupOrdering('cell_lineage') and len(selectedDataset.sampleGroupOrdering(selectedSampleGroup))==0:
			celltypesFromLineage = selectedDataset.sampleGroupItems(sampleGroup='celltype', groupBy='cell_lineage')
			sgi = sum([celltypesFromLineage[lineage] for lineage in selectedDataset.sampleGroupItems(sampleGroup='cell_lineage')],[])    			
	df = df[sgi]

	# Filter rows if too many
	if len(df)>maxFeatures:  # first filter low range rows
		df = df.loc[[rowId for rowId,row in df.iterrows() if row.max()-row.min()>1]]
		
	if len(df)>maxFeatures:  # still too many - filter by variance
		variances = [[numpy.var(row), rowId] for rowId,row in df.iterrows()]
		df = df.loc[[item[1] for item in sorted(variances, reverse=True)]].iloc[:maxFeatures,:]

	# Create a copy of df with zscores
	zscores = pandas.DataFrame([stats.zscore(row) for rowId,row in df.iterrows()], index=df.index, columns=df.columns)

	# Test enough data is given to plot on heatmap
	if(zscores.shape[0] < 2):
		# Not enough data. Redirect back to geneset page
		request.session.flash('Not enough data to plot', 'dataerror')
		url = request.route_url('/geneset/current')
		return HTTPFound(location=url)
	
	# cluster features based on zscore
	from scipy.spatial.distance import pdist, squareform
	import scipy.cluster.hierarchy as hc

	dist = squareform(pdist([row for rowId,row in zscores.iterrows()]))
	zscores.to_csv("zscores.txt", sep="\t")
	rowOrdering = hc.leaves_list(hc.linkage(dist, method='centroid'))
	zscores = zscores.iloc[rowOrdering]
	df = df.iloc[rowOrdering]
	
	# construct the labels used by each row of the heatmap
	# need gene symbols
	geneSymbolsFromGeneId = gs.geneSymbols(returnType='dict')

	# need gene ids from rowIds for microarray data	
	if not selectedDataset.isRnaSeqData:
		geneIdsFromProbeId = selectedDataset.geneIdsFromProbeIds(probeIds=df.index.tolist(), returnType='dict')
	
	rowLabels = []
	for rowId in df.index:
		if selectedDataset.isRnaSeqData:
			symbols = geneSymbolsFromGeneId[rowId] if rowId in geneSymbolsFromGeneId else rowId
			geneIds = [rowId]
		else:
			if rowId in geneIdsFromProbeId:
				symbols = ','.join([geneSymbolsFromGeneId[geneId] if geneId in geneSymbolsFromGeneId else geneId for geneId in geneIdsFromProbeId[rowId]])
			else:
				symbols = rowId
			geneIds = geneIdsFromProbeId.get(rowId, [rowId])
		rowLabels.append({'featureId':rowId, 'displayString':symbols, 'geneIds':geneIds})
	
	# construct the matrix object to pass
	matrix = []
	for i in range(len(df)):
		for j in range(len(sgi)):
			matrix.append({'x':j, 'y':i, 'value':zscores.iat[i,j], 'name':'(%s,%s): %s' % (rowLabels[i]['displayString'],sgi[j],df.iat[i,j])})

	error = 'No expression profile found for any of the genes for this dataset.' if len(df)==0 else ''
	valueRange = [zscores.min().min(), zscores.max().max()]
	
	# colours used for bar plot
	colours = selectedDataset.sampleGroupColours(sampleGroup=selectedSampleGroup)  # this is a dict
	
	# save dataset as defaults
	setSelectedDataset(request, selectedDataset.name)

	return {'genesetName':gs.name, 'genesetDescription':gs.description, 'datasets':datasetProperties,  'geneIds':selectedGeneIds,
			'selectedDatasetName':selectedDataset.name, 'sampleGroups':sampleGroups, 'selectedSampleGroup':selectedSampleGroup,
			'data':{'columnLabels':sgi, 'rowLabels':rowLabels, 'matrix':matrix, 'colours':[colours.get(item,'#ccc') for item in sgi]}, 
			'valueRange':valueRange, 'error':error}
