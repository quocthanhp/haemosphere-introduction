from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import re, os
import logging
import six
import time

log = logging.getLogger(__name__)

from pyramid.view import (view_config, forbidden_view_config)
from pyramid.security import (Allow, Deny, Everyone, Authenticated)
from pyramid.security import (remember, forget)
from pyramid.httpexceptions import (HTTPException, HTTPFound, HTTPNotFound, HTTPBadRequest, HTTPConflict,
                                    HTTPInternalServerError)
from pyramid.response import Response, FileResponse
from pyramid.events import NewRequest, subscriber

from sqlalchemy.orm.exc import NoResultFound

from haemosphere.models import sharewould, hsdataset, hsgeneset, users, rfunctions
from haemosphere.models.users import User, Group

from .user_views import currentUser
from .hsdataset_views import datasetAttributes, datasetFromName
from .utility import params, addGenesetToSession, currentEnv


# Note that any global variables set here are accessible throughout application across all requests.

# RootFactory is called on every request.
class RootFactory(object):
    __acl__ = [(Allow, Authenticated, 'view'), (Allow, 'group:Admin', ('view', 'edit'))]

    def __init__(self, request):
        # Define some request.session variables here. These are saved per client session.
        if 'genesets' not in request.session: request.session['genesets'] = []


# This method is called whenever a new request is made. So it's a way to record every user request if log level is INFO and above.
@subscriber(NewRequest)
def logUsage(event):
    requestString = event.request.path  # eg: /geneset/current
    ignoreList = ['/css', '/js', '/images', '/media',
                  '/favicon']  # ignore if requestString starts with any of these strings
    for item in ignoreList:
        if requestString.startswith(item): return
    # record user or ip address - event.request.remote_addr doesn't work with apache working as proxy.
    user = currentUser(event.request)
    userinfo = user.username if user else os.environ.get('HTTP_X_FORWARDED_FOR', os.environ.get('REMOTE_ADDR'))
    log.info('usage: {0} {1}'.format(userinfo, requestString))


@view_config(context=HTTPInternalServerError)
def exception_view(context, request):
    print("### The error was: %s" % context)
    return Response(status_int=500, body=str(context))


# ---------------------------------------------------------
# generic functions any pages can use
# ---------------------------------------------------------
@view_config(route_name='/session/selecteddataset', renderer="json")
def setSelectedDataset(request, datasetName=None):
    """
	Use request.session to store datasetName as currently selected dataset, which is useful as default in many pages.
	"""
    request.session['selectedDatasetName'] = datasetName if datasetName else params(request, 'datasetName')
    return {}


@view_config(route_name='/session/selectedGene', renderer="json")
def setSelectedGene(request, geneId=None):
    """
	Use request.session to store geneId as currently selected gene, which is useful as default in many pages.
	"""
    request.session['selectedGeneId'] = geneId if geneId else params(request, 'geneId')
    return {}


# ---------------------------------------------------------
# home page and searches
# ---------------------------------------------------------
@view_config(route_name='/home', renderer="haemosphere:templates/about.mako")
def homePage(request):
    return {}


@view_config(route_name='/about', renderer="haemosphere:templates/about.mako")
def aboutPage(request):
    return {}


@view_config(route_name="/searches", renderer="haemosphere:templates/search.mako")
def searchPage(request):
    # Input params
    selectedSearch = request.params.get('selectedSearch')  # integer value, which can be left out
    allDatasets = datasetAttributes(request)

    sampleGroups = {}
    for ds in allDatasets:
        sampleGroups[ds['name']] = [{'name': group, 'items': ds['sampleGroupItems'][group]} for group in
                                    ds['sampleGroups']]

    return {"datasets": allDatasets, "sampleGroups": sampleGroups, "selectedSearch": selectedSearch,
            'topTableString': rfunctions.topTableString}


# Create a Geneset instance based on keywords
@view_config(route_name="/search/keyword", renderer="json")
def searchKeyword(request):
    """
	Return a json object, which is the result of search made for genes using key words.
	
    Request parameters
    ----------
    searchString: key words used for search string. comma, newline or spaces are interpreted as separate strings
    searchScope: one of ['ensembl','entrez','symbol',None], used to narrow the search scope.
    species: one of ['MusMusculus','HomoSapiens',None], used to narrow the search scope.
    exactMatch: boolean to use exact or fuzzy matching

	Returns
	----------
	a json object that looks like 
	{'search_terms': ['p53','IL5'], 'genesetSize': 122}
	
	Note that actual geneset matching the search is pushed into current session parameters using addGenesetToSession() function.
	"""
    # Parse input - expect json_body for request here (via $http.post in angular)
    searchString = params(request, 'searchString', '')
    searchScope = params(request, 'searchScope', '')
    species = params(request, 'species', '')
    exactMatch = params(request, 'exactMatch', False)

    searchTerms = [_f for _f in [t.strip() for t in re.split('[,\s\n\r]+', searchString)] if _f]
    if not searchTerms:
        return {'search_terms': '', 'genesetSize': 0}

    # Name of Geneset uses first 3 search terms or less
    genesetName = ','.join(searchTerms[:3]) + ('...' if len(searchTerms) > 3 else '')
    description = 'Geneset from keyword search: %s' % genesetName

    # Parse search scope which corresponds to searchColumns parameter
    searchColumns = None
    if 'entrez' in searchScope.lower():
        searchColumns = ['EntrezId']
    # elif 'probe' in searchScope.lower():	# not implemented yet
    #	searchColumns = 'probeId'
    elif 'ensembl' in searchScope.lower():
        searchColumns = ['EnsemblId']
    elif 'symbol' in searchScope.lower():
        searchColumns = ['GeneSymbol']

    gs = hsgeneset.HSGeneset(name='Search: %s' % genesetName, description=description) \
        .subset(queryStrings=searchTerms, searchColumns=searchColumns, species=species, caseSensitive=exactMatch,
                matchSubstring=not exactMatch)
    addGenesetToSession(request, gs)
    return {'search_terms': searchTerms, 'genesetSize': gs.size()}


# Create a Geneset instance based on diff expression
@view_config(route_name="/search/expression", renderer="json")
def searchExpression(request):
    '''Perform DE search for selected dataset and fetch the corresponding Geneset instance .
	The Geneset is added to the current session and its size is returned, unless the size is 0,
	in which case an error key is returned.
	'''
    # Input parameters
    selectedDatasetName = params(request, 'dataset')
    sampleGroup = params(request, 'sampleGroup')
    sampleGroupItem1 = params(request, 'sampleGroupItem1')
    sampleGroupItem2 = params(request, 'sampleGroupItem2')
    downloadRObjects = params(request, 'downloadRObjects', False)

    # These are only relevant for rna-seq data
    normalization = params(request, 'normalisation', 'TMM')
    filterMinCpm = float(params(request, 'filterCpm', 0.5))
    minFilterSample = int(params(request, 'minFilterSample', 2))

    # Get Dataset instance matching selected name
    ds = datasetFromName(request, selectedDatasetName)
    if not ds:  # should not happen unless manually changed url
        return {'error': "No matching dataset."}

    # Check that dataset contains duplicates at both the replicate sample group and at the selected sample group
    replicateSampleGroupItems = ds.sampleGroupItems(sampleGroup=ds.replicateSampleGroup(), duplicates=True)
    sampleTable = ds.sampleTable()
    sampleTable1 = sampleTable[sampleTable[sampleGroup] == sampleGroupItem1]
    sampleTable2 = sampleTable[sampleTable[sampleGroup] == sampleGroupItem2]
    if len(replicateSampleGroupItems) == len(set(replicateSampleGroupItems)) or len(sampleTable1) < 2 or len(
            sampleTable2) < 2:
        return {
            'error': "You have chosen a dataset and sample group where there is not enough replicates for a statistical analysis"}

    # print(ds, ds.replicateSampleGroup(), replicateSampleGroupItems, selectedSampleGroupItems)

    # use topTable function from R to fetch a pandas data frame version of limma's topTable
    if downloadRObjects:  # create a temporary file that can be used to dump the R object to
        import tempfile
        r_object_filepath = tempfile.NamedTemporaryFile(prefix="haemosphere", suffix='.r').name
    else:
        r_object_filepath = None

    df = ds.expressionMatrix(datatype="counts")
    log.debug("Start R func\n")
    start = time.time()
    topTable = rfunctions.topTable(selectedDatasetName, df, ds.sampleGroupItems(sampleGroup=ds.replicateSampleGroup(), duplicates=True),
                                   ds.sampleGroupItems(sampleGroup=sampleGroup, duplicates=True), \
                                   sampleGroupItem1, sampleGroupItem2, not ds.isRnaSeqData, filterMinCpm=filterMinCpm,
                                   filterMinExpressedSamples=minFilterSample, normalizationMethod=normalization,
                                   saveToFile=r_object_filepath)
    end = time.time()
    log.debug(f"R func ends in {end - start}\n")
    if topTable is None:
        log.debug(f"R func ends in {end - start}\n")
        return {'error': "topTable error"}

    # Create a geneset with gene ids coming from topTable - match gene ids to probes for microarray data.
    # Also set score dictionary
    if ds.isRnaSeqData:
        geneIds = topTable.index
        score = topTable.to_dict()
    else:  # fetch matching geneIds and assign topTable values to them
        import pandas
        gpid = ds.geneIdsFromProbeIds(probeIds=topTable.index, returnType='dict')
        scoreList, index = [], []
        for probeId, row in topTable.iterrows():
            if probeId not in gpid: continue
            matchingGeneIds = gpid[probeId]
            for geneId in matchingGeneIds:
                if geneId not in index:  # avoid duplicate rows
                    scoreList.append(row)
                    index.append(geneId)
        newTopTable = pandas.DataFrame(scoreList, index=index)
        geneIds = newTopTable.index
        score = newTopTable.to_dict()

    genesetName = '%s (%s vs %s)' % (ds.name, sampleGroupItem1, sampleGroupItem2)
    description = 'Geneset from expression search, with dataset %s, %s vs %s' % (
        ds.name, sampleGroupItem1, sampleGroupItem2)
    gs = hsgeneset.HSGeneset(name='Diff Exp: %s' % genesetName, description=description).subset(queryStrings=geneIds,
                                                                                                searchColumns=[
                                                                                                    'GeneId'])
    if gs.size() == 0:  # shouldn't happen, since topTable is already not None by this stage, but something could have gone wrong when fetching Geneset
        return {'error': 'Error creating a Geneset after successful topTable'}

    # set score values to geneset and add to session
    gs.setScore(score)
    gs.sort('absLogFC', ascending=False)
    addGenesetToSession(request, gs)

    # set selectedDatasetName
    setSelectedDataset(request, datasetName=ds.name)

    if downloadRObjects:  # it's difficult to pass filepaths around as url parameters, so just keep this in request.session
        request.session['r_object_filepath'] = r_object_filepath

    return {'genesetSize': gs.size(), 'downloadRObjects': downloadRObjects}


# Create a Geneset instance based on high expression on specified sample group item
@view_config(route_name="/search/highexp", renderer="json")
def searchHighExpression(request):
    '''Find genes with highest expression in specified sample group item relative to all others
	for selected dataset, and fetch the corresponding Geneset instance .
	The Geneset is added to the current session and its size is returned, unless the size is 0,
	in which case an error key is returned.
	'''
    import numpy

    # Input parameters
    selectedDatasetName = params(request, 'dataset')
    sampleGroup = params(request, 'sampleGroup')
    sampleGroupItem = params(request, 'sampleGroupItem')

    # Get Dataset instance matching selected name
    ds = datasetFromName(request, selectedDatasetName)
    if not ds:  # should not happen unless manually changed url
        return {'error': "No matching dataset."}

    # score each gene by difference between value at sampleGroupItem vs highest of the rest
    df = ds.expressionMatrix(datatype="tpm", sampleGroupForMean=sampleGroup)
    if ds.isRnaSeqData:  # use log2
        df = numpy.log2(df + 1)

    # Filter df based on some row properties. I think it's quicker to do this here than inside iterrows
    variance = df.var(axis=1)  # columnwise variance (so each index will be row id of df)
    maximum = df.max(axis=1)  # maximum value of each gene
    minOfDf = df.min().min()
    df = df.loc[variance[variance > 1].index]
    #df = df.loc[maximum[maximum > minOfDf + 1].index]
    df = df.reindex(maximum[maximum > minOfDf + 1].index)

    otherGroupItems = [item for item in df.columns if item != sampleGroupItem]
    scores = dict([(rowId, row[sampleGroupItem] - row[otherGroupItems].max()) for rowId, row in df.iterrows()])
    scores = dict([(rowId, value) for rowId, value in six.iteritems(scores) if value > 0])  # only keep positive scores

    # Create a geneset with gene ids coming from scores - match gene ids to probes for microarray data.
    # Also set score dictionary
    if not ds.isRnaSeqData:  # fetch matching geneIds and assign topTable values to them
        gpid = ds.geneIdsFromProbeIds(probeIds=list(scores.keys()), returnType='dict')
        newScores = {}
        for probeId, value in six.iteritems(scores):
            if probeId not in gpid: continue
            for geneId in gpid[probeId]:
                if geneId not in newScores:  # avoid duplicate entries
                    newScores[geneId] = value
        scores = newScores

    geneIds = list(scores.keys())
    genesetName = '%s (high in %s vs all others)' % (ds.name, sampleGroupItem)
    description = 'Geneset from high expression search, with dataset %s, %s vs all others' % (ds.name, sampleGroupItem)
    gs = hsgeneset.HSGeneset(name='High Exp: %s' % genesetName, description=description).subset(queryStrings=geneIds,
                                                                                                searchColumns=[
                                                                                                    'GeneId'])
    if gs.size() == 0:  # shouldn't happen, since scores is already not None by this stage, but something could have gone wrong when fetching Geneset
        return {'error': 'Error creating a Geneset after successful high expression'}

    # set score values to geneset and add to session
    gs.setScore({'score': scores})
    gs.sort('score', ascending=False)
    addGenesetToSession(request, gs)

    # set selectedDatasetName
    setSelectedDataset(request, datasetName=ds.name)

    return {'genesetSize': gs.size()}
