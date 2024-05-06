from __future__ import absolute_import
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os, pandas
import sys, codecs

import chardet
from pyramid.view import view_config
from unidecode import unidecode

from haemosphere.models import hsdataset
from pyramid.httpexceptions import HTTPFound

from .user_views import currentUser
from .utility import forest, params
from six.moves import zip

# ---------------------------------------------------------
# Dataset related utility functions
# ---------------------------------------------------------
def _newDatasetNameFromOld(oldName):
    """Dataset names got changed at version 4.9. Users may have saved dataset subsets or orderings using the old names,
    so substitute these. Will just return oldName if there's no match.
    """
    return {"haemopedia":"Haemopedia",
            "haemopedia-plus":"Haemopedia-Plus",
            "gxcommons":"Gene-Expression-Commons",
            "immgen":"Immgen",
            "IL5T Eosinophils":"IL5T-Eo",
            "goodell":"Goodell",
            "rapin":"Rapin-BloodSpot",
            "dmap":"DMAP",
            "watkins":"Watkins",
            "schultze":"Shultze"}.get(oldName, oldName)

def _sortUserDatasets(datasets, datasetOrdering, groupby="species"):
    """
    Take a list of datasets (dictionaries) and return a sorted list. 
    datasetOrdering: a list of dataset names user may have specified for ordering
    groupby: ['species','platformType']
    """
    #print(datasets)

    # create a dictionary from list of datasets
    dictFromName = dict([(ds['name'], ds) for ds in datasets])
    # Some hard-coded dataset names in the order that we want
    orderedList = {"platformType":[["Haemopedia-Mouse-RNASeq","Immgen-ULI-RNASeq","Haemopedia-Human-RNASeq","Linsley"],
                                    ["Haemopedia","Haemopedia-Plus","IL5T-Eo","Gene-Expression-Commons","Immgen","Goodell","DMAP","Rapin-BloodSpot", "Schultze","Watkins"]],
                    "species":[["Haemopedia-Mouse-RNASeq","Haemopedia","Haemopedia-Plus","Immgen-ULI-RNASeq","IL5T-Eo","Gene-Expression-Commons","Immgen","Goodell"],
                                ["Haemopedia-Human-RNASeq","Linsley","DMAP","Rapin-BloodSpot", "Schultze","Watkins"]]}

    # There will be items in datasets which are not found in orderedList, such as private datasets. So add these
    # according to groupby
    itemsNotInOrderedList = [item['name'] for item in datasets if item['name'] not in sum(orderedList["platformType"],[])]

    if groupby=="platformType":  # platform first, then species within
        orderedList = orderedList[groupby][0] + sorted([item for item in itemsNotInOrderedList if dictFromName[item]['platform_type']=='rna-seq'])\
                        + orderedList[groupby][1] + sorted([item for item in itemsNotInOrderedList if dictFromName[item]['platform_type']=='microarray'])
    else:  # species first then platform within
        orderedList = orderedList[groupby][0] + sorted([item for item in itemsNotInOrderedList if dictFromName[item]['species']=='MusMusculus'])\
                        + orderedList[groupby][1] + sorted([item for item in itemsNotInOrderedList if dictFromName[item]['species']=='HomoSapiens'])

    # Read user preference
    if datasetOrdering:
        # substitute old names with new ones
        datasetOrdering =  [_newDatasetNameFromOld(item) for item in datasetOrdering]
        datasetOrdering = [item for item in datasetOrdering if item in orderedList]  # only keep those found in orderedList
        
        # create a dictionary of indices from orderedList
        indexFromOrderedList = dict([(item,i) for i,item in enumerate(orderedList)])
        
        # select items found in datasetOrdering, and reassign their indices based on datasetOrdering
        newIndexFromOrderedList = dict(zip([item for item in orderedList if item in datasetOrdering], [indexFromOrderedList[item] for item in datasetOrdering]))
        
        # create a newly sorted version of orderedList based on these new indices
        newOrderedList = [(newIndexFromOrderedList.get(item, indexFromOrderedList[item]), item) for item in orderedList]
        orderedList = [item[1] for item in sorted(newOrderedList)]

    return [dictFromName[name] for name in orderedList]

def datasetAttributes(request, sortDatasets=True, selectedDatasetsOnly=True):
    """
    Return a list of dictionaries, where each dictionary contains the attributes of the dataset.
    The list is automatically restricted to the datasets that current user has access to.

    parameters
    ----------
    sortDatasets (bool): If true, a sorted list of datasets will be returned.
    selectedDatasetsOnly (bool): If true, only the datasets user has selected will be returned if user has made such selections.
        Otherwise all datasets current user has access to will be returned.
    
    To speed up access of these attributes which are used widely across the app, cache the list of all dataset attributes in 
    request.session. Note that request.session saves data per session, which is linked to a client, and does not know about 
    application specific info such as users. This means that data saved under request.session will be shared among all users 
    on the same browser on the same machine, regardless of who may be logged in. So we keep the username of last user and if 
    there's no match, re-fetch the dataset attributes. Also if a dataset changes (eg. upgraded to next version), this caching 
    mechanism won't pick up the changes automatically. We can just delete the cache but that will also delete all other cached 
    data including selectedGeneId, geneset history, etc. So we read a flag from the config file to see if this cache needs 
    rebuilding for this specific session.
    """    
    user = currentUser(request)
    username = user.username if user else None
    rebuildVersion = request.registry.settings.get("haemosphere.datasetAttributesRebuildVersion")
        # Get list of datasets and filepaths for this user (inventory looks like: [('abraham', '/path/to/abraham.h5'), ...])
    #if not request.session.get("datasetAttributes") or request.session.get("lastUsername")!=username or \
    #request.session.get("datasetAttributesRebuildVersion",0) < rebuildVersion:
    #print("datasetAttributes information", request.session.get("datasetAttributes"))
    #print("lastUsername information", request.session.get("lastUsername"))
#    print("datasetAttributesRebuildVersion information",request.session.get("datasetAttributesRebuildVersion",0)<rebuildVersion)
    inventory = forest(request).inventory(user.username, user.groupnames(), clean=True) if user else forest(request).inventory(None)
    dsattrs = []

        #print(chardet.detect(bytes('/Users/ndhanawada/haemosphere/data/datasets/F0r3sT/PUBLIC/dmap.1.4.h5',encoding="utf-8")))
    #try:
    #print("PO90",hsdataset.HSDataset(inventory[0][1]))
    for ds in [hsdataset.HSDataset(item[1]) for item in inventory]:
            #print("DS",ds)
            att = ds.attributes()
            att['name'] = ds.name
            att['sampleNumber'] = len(ds.sampleIds())
            att['isRnaSeqData'] = ds.isRnaSeqData
            att['pubmed_id'] = att['pubmed_id'] if att['pubmed_id'] and pandas.notnull(att['pubmed_id']) else ''
            att['parent'] = ds.parent
            att['sampleGroups'] = ds.sampleGroups(returnType="display")
            att['filepath'] = ds.filepath
            att['sampleGroupItems'] = dict([(group, ds.sampleGroupItems(sampleGroup=group)) for group in ds.sampleGroups(returnType='display')])
            dsattrs.append(att)
    request.session['datasetAttributes'] = dsattrs
    request.session['lastUsername'] = username
    request.session['datasetAttributesRebuildVersion'] = rebuildVersion
    #except Exception as e:
        #print('error2:', e)
    dsattrs = request.session.get("datasetAttributes")

    if sortDatasets:
        datasetOrdering = forest(request).loadfile(user.username, 'DatasetOrdering.ds') if user else None
        dsattrs = _sortUserDatasets(dsattrs, datasetOrdering)

    # Now filter these if the user has a list of selected datasets
    if selectedDatasetsOnly:
        selectedDatasetNames = forest(request).loadfile(user.username, 'SelectedDatasets.ds') if user else None
        if selectedDatasetNames:
            selectedDatasetNames = [_newDatasetNameFromOld(name) for name in selectedDatasetNames]
            dsattrs = [ds for ds in dsattrs if ds.get('name','') in selectedDatasetNames]

    return dsattrs
        
def findDatasetInList(datasets, name):
    """
    Find HSDataset instance from set based on name. Returns None if there is no matching dataset within dataset.
    """
    for ds in datasets:
        if ds.get('name','')==name:
            return hsdataset.HSDataset(ds['filepath'])
    return None

def datasetFromName(request, name):
    """
    Return HSDataset instance based on name. Returns None if there is no matching dataset within user access.
    """
    for ds in datasetAttributes(request, sortDatasets=False, selectedDatasetsOnly=False):
        if ds.get('name')==name:
            return hsdataset.HSDataset(ds.get('filepath'))
    return None


# ---------------------------------------------------------
# Dataset and sample related views
# ---------------------------------------------------------
@view_config(route_name="/datasets/show", renderer="haemosphere:templates/datasets.mako")
def showDatasets(request):
    """
    Create a list of dictionaries for information about all the datasets user has access to. No input params required.
    Template needs a few extra keys in each dictionary, other than the keys from attributes() method of the dataset.
    """
    user = currentUser(request)
    filteredDatasets = datasetAttributes(request)
    allDatasets = datasetAttributes(request, selectedDatasetsOnly=False)

    # provide the template with the attributes of all datasets user has access to also
    return {"datasets":filteredDatasets, "guestUser":user is None, "allDatasets":allDatasets}


@view_config(route_name="/datasets/analyse", renderer="haemosphere:templates/dataset.mako")
def analyseDataset(request):
    """
    Show MDS plot for a dataset.
    """
    datasets = datasetAttributes(request)

    # Get datasetName from request parameters. If not present, use first available dataset
    datasetName = params(request, 'datasetName', datasets[0]['name'])	

    # Check selected dataset exists. If not return to datasets/show and display error message.
    try:
        selectedDatasetIndex = [ds['name'] for ds in datasets].index(datasetName)		
    except:
        request.session.flash('Unable to access requested dataset', 'accesserror')
        url = request.route_url('/datasets/show')
        return HTTPFound(location=url)

    ds = findDatasetInList(datasets, datasetName)

    distances = ds.sampleDistances()
    sampleGroups = ['sampleId'] + ds.sampleGroups(returnType='display')
    sampleTable = ds.sampleTable()
    samples = []
    for sampleId in distances.columns:
        row = {'sampleId':sampleId}
        for sampleGroup in sampleGroups[1:]:
            row[sampleGroup] = sampleTable.at[sampleId,sampleGroup]# if pandas.notnull(sampleTable.at[sampleId,sampleGroup]) else ''
        samples.append(row)

    return {"datasets": [{'name':d['name'], 'species':d['species'], 'platform':d['platform_type'], 'version':d['version']} for d in datasets],
            "selectedDatasetIndex": selectedDatasetIndex,
            "distances": distances.to_json(orient='values'),  # [[0,0.8145728942,...], ...] note: this is a string!
            "sampleGroups": sampleGroups,
            "samples": samples,
            "sampleGroupColours": ds.sampleGroupColours(),
            "sampleGroupOrdering": ds.sampleGroupOrdering()
            }		



@view_config(route_name="/datasets/samples", renderer="haemosphere:templates/samples.mako")
def showSamples(request):
    """
    Get the sample data from hdf file
    """
    user = currentUser(request)
    dslist = datasetAttributes(request)

    # Input params
    selectedDatasetName = params(request, 'datasetName', dslist[0]['name']) # Get first available if no datasetName is given
    if selectedDatasetName not in [item['name'] for item in dslist]:
        selectedDatasetName = dslist[0]['name']

    ds = findDatasetInList(dslist, selectedDatasetName)
    df = ds.sampleTable().reset_index().fillna('')

    sampleTable = df.to_dict(orient="records")
    columns = df.columns.tolist()
            
    return {"datasets":dslist, "selectedDatasetName":selectedDatasetName, "sampleTable":sampleTable, "columns":columns, 
            "userIsAdmin":user.isAdmin() if user else False, "guestUser":user is None, 
            "sampleGroupsDisplayed":ds.sampleGroups(returnType="display")}


@view_config(route_name="/datasets/createsubset", permission="view", renderer="json")
def createDatasetSubset(request):
    """
    Create a subset of a dataset. Only available to registered users, hence permission='view'.

    Request parameters
    ----------
    datasetName: string, name of the parent dataset
    subsetName: string, name of subset
    subsetDescription: string, description of the subset
    sampleIds: a list of sample ids to create a subset of parent dataset
    sampleGroupsDisplayed: a list of sample groups to be used for display - may be different to parent
    """
    # Input params
    datasetName = params(request, 'datasetName')
    subsetName = params(request, 'subsetName')
    subsetDescription = params(request, 'subsetDescription')
    sampleIds = params(request, 'sampleIds')
    sampleGroupsDisplayed = params(request, 'sampleGroupsDisplayed')

    user = currentUser(request)

    # save new dataset file under user's directory with .h5 suffix
    ds = datasetFromName(request, datasetName)
    filepath = os.path.join(forest(request).directory(user.username), "%s.h5" % subsetName)
    # Remove current file of same name if exists - otherwise .h5 file may get too big
    if os.path.exists(filepath): os.remove(filepath)
    hsdataset.saveDatasetSubset(ds, filepath, subsetName, subsetDescription, sampleIds, sampleGroupsDisplayed)
    # If user has a list of selectedDatasets, add this to it, otherwise it'll be hidden initially
    selectedDatasetNames = forest(request).loadfile(user.username, 'SelectedDatasets.ds') if user else None
    if selectedDatasetNames:
        selectedDatasetNames.append(subsetName)
        forest(request).picklefile(user.username, selectedDatasetNames, 'SelectedDatasets.ds')

    # Clear datasetAttributes cache, since it relies on parent field
    request.session['datasetAttributes'] = []

    return {'success':1}

@view_config(route_name="/datasets/select", permission="view", renderer="json")
def selectDatasets(request):
    """
    Select a subset of datasets to view. Only available to registered users, hence permission='view'

    Request parameters
    ----------
    datasetNames: (list of strings) names of the datasets selected; if empty, remove prevous selections
    """
    datasetNames = params(request, 'datasetNames')
    user = currentUser(request)

    if datasetNames is None or len(datasetNames)==0:   # remove any previous selections
        filepath = os.path.join(forest(request).directory(user.username), 'SelectedDatasets.ds')
        if os.path.exists(filepath): os.remove(filepath)
    else:	# store these into the user directory 
        forest(request).picklefile(user.username, datasetNames, 'SelectedDatasets.ds')
        
    return {'success':1}

@view_config(route_name="/datasets/order", permission="view", renderer="json")
def orderDatasets(request):
    """
    Order the datasets - this means saving the ordering for this user. Only available to registered users, hence permission='view'

    Request parameters
    ----------
    datasetOrdering: (list of strings) names of the datasets ordered; if empty, remove prevous ordering
    """
    datasetOrdering = params(request, 'datasetOrdering')
    user = currentUser(request)

    if datasetOrdering is None or len(datasetOrdering)==0:   # remove any previous selections
        filepath = os.path.join(forest(request).directory(user.username), 'DatasetOrdering.ds')
        if os.path.exists(filepath): os.remove(filepath)
    else:	# store these into the user directory 
        forest(request).picklefile(user.username, datasetOrdering, 'DatasetOrdering.ds')
        
    return {'success':1}



