from __future__ import absolute_import
from pyramid.view import view_config

from haemosphere.models import hsgeneset
from haemosphere.views.hsdataset_views import datasetFromName
from haemosphere.models import labsamples

from .user_views import currentUser
from .utility import currentEnv
import six

def currentLabSamples(request):
	"""
	Return the User instance attached to this request. Only works after a successful authentication.
	"""
	try:
# 		username = request.authenticated_userid
		return labsamples.getLabSamples(request.ls_dbsession) #, username)
	except:
		return None


# ---------------------------------------------------------
# Pages specific to particular user groups
# ---------------------------------------------------------
def groupPages(groups):
	"""Return a list of dict describing all pages specific to each group in groups.
	"""
	# metadata for each group page - not sure currently where to keep this
	groupInfo = {'HiltonLab':[('samples','View/edit all Hiltonlab sample data')],
				 'CSL':[('scoregenes','Score Genes')]}
	grouplist = []
	for group in groups:
		for item in groupInfo.get(group, []):
			grouplist.append({'url':'/grouppages/%s/%s' % (group,item[0]), 'display':item[1], 'group':group})
	return grouplist
	
def checkUserAccessToGroupPage(user, groupname, env, allowedEnv=['dev','private']):
	"""All the group pages should first check if user has permission to access the page, so call this function first.
	Parameters:
		user: User instance
		groupname: (str) group name
		env: (str) ['dev','private','public']
		allowedEnv: (list) subset of all possible env values
	Returns:
		(str) error message or empty string if no error.
	"""
	if not user or groupname not in user.groupnames():
		return 'User does not have access to this page.'
	elif env not in allowedEnv:
		return 'This function is not available in this server environment.'
	return ''
	
def labSamples(request):
	"""Return labsamples.LabSamples instance using the appropriate argument
	"""
	from haemosphere.models import labsamples
	groupDir = request.registry.settings['haemosphere.model.grouppages']
	return labsamples.LabSamples({'samples':'%s/HiltonLab/HematlasSamples_samples.txt' % groupDir,
								  'celltypes':'%s/HiltonLab/HematlasSamples_celltypes.txt' % groupDir,
								  'batches':'%s/HiltonLab/HematlasSamples_batches.txt' % groupDir})
								  
@view_config(route_name="/grouppages/HiltonLab/samples", permission="view", renderer="haemosphere:templates/hematlas_samples.mako")
def manageHematlasSamples(request):
	currentLabSamples(request)
	"""Manage all sample data produced by hiltonlab.
	"""
	error = checkUserAccessToGroupPage(currentUser(request), 'HiltonLab', currentEnv(request))
	if error: return {'error':error}
	
	# ls = { 'samples' : { 'columns' : [ ... ], 'data' : [ ... ] }, 'celltypes' : { 'columns' : [ ... ], 'data' : [ ... ] }, 'batches' : { 'columns' : [ ... ], 'data' : [ ... ] } }
	ls = labsamples.getAllLabSamples(request.ls_dbsession)

	return ls

			
@view_config(route_name="/grouppages/HiltonLab/samples_save", permission="view", renderer="json")
def saveHematlasSamples(request):
    """Manage all sample data produced by hiltonlab.
    """
    user = currentUser(request)
    error = checkUserAccessToGroupPage(user, 'HiltonLab', currentEnv(request))
    if error: return {'error':error}

    params = request.json_body	
    # {'update':{'batches': [], 'celltypes': [{'column':'celltype', 'currentValue':'EoBM', 'newValue':'Eo', 'rowId':'EoBM', 'id':12 i.e(db primary key)}], 'samples': []}, 'makeBackup':True}

    for tableType,items in six.iteritems(params['create']):
        for item in items:
            labsamples.saveNewData(request.ls_dbsession, tableType, item)	

    lsamples = labSamples(request)	
    for tableType,items in six.iteritems(params['update']):
        if params['makeBackup'] and len(items)>0:
            lsamples.makeBackup(tableType)
        for item in items:
            if not item['id']:
                # entry was created then updated
                item['id'] = labsamples.getEntryByName(request.ls_dbsession, tableType, item['rowId'])
            lsamples.update(request.ls_dbsession, tableType, item['id'], item['column'], item['newValue'])
			
    for tableType,items in six.iteritems(params['delete']):
        for item in items:
            if not item['id']:
                # entry was created then deleted
                item['id'] = labsamples.getEntryByName(request.ls_dbsession, tableType, item['rowId'])
            labsamples.deleteData(request.ls_dbsession, tableType, item['id'])	
	        		
    return {'message':'saved'}


@view_config(route_name="/grouppages/HiltonLab/new_samples_save", permission="view", renderer="json")
def saveNewHematlasSamples(request):
	"""Add new sample data produced by hiltonlab to database.
	"""
	user = currentUser(request)
	error = checkUserAccessToGroupPage(user, 'HiltonLab', currentEnv(request))
	if error: return {'error':error}

	params = request.json_body	
	# {'tableType': 'samples', 'data' : { 'sampleId': 'newsampleexample', ...all other sample attributes user can enter in labsample_modal  } }

	new_entry, message = labsamples.saveNewData(request.ls_dbsession, params['tableType'], params['data'])
	
	return {'message': message, 'new_entry': new_entry, 'table_type': params['tableType']}


@view_config(route_name="/grouppages/HiltonLab/delete_samples", permission="view", renderer="json")
def deleteHematlasSamples(request):
	"""Delete selected sample data from database.
	"""
	user = currentUser(request)
	error = checkUserAccessToGroupPage(user, 'HiltonLab', currentEnv(request))
	if error: return {'error':error}

	params = request.json_body	
	# {'tableType': 'samples', 'data' : { 'id': (primary key for given entry), 'rowId': exampleId (this is the instances celltype, sampleId, or BatchId)  } }

	message = labsamples.deleteData(request.ls_dbsession, params['tableType'], params['data']['id'])
	
	return {'message': message}


@view_config(route_name="/grouppages/CSL/scoregenes", permission="view", renderer="haemosphere:templates/hematlas_scoregenes.mako")
def manageHematlasScoregenes(request):
	"""Manage scoregenes.
	"""
	error = checkUserAccessToGroupPage(currentUser(request), 'CSL', currentEnv(request))
	if error: return {'error':error}
		
	from haemosphere.models import scoregenes
	sg = scoregenes.ScoreGenes('data/grouppages/CSL/scoregenes_scores.txt', 'data/grouppages/CSL/scoregenes_comments.txt')

	# main table of genes and scores to pass on
	df = sg.scoresTable()
	
	# add gene info columns using Geneset instance
	gsdf = hsgeneset.HSGeneset().dataframe()
	gsdf.index.name = 'geneId'
	df = df.join(gsdf)
		
	# add lineage score
	ds = datasetFromName(request, 'hiltonlab')
	exp = ds.expressionMatrix(geneIds=df.index, sampleGroupForMean='cell_lineage')
	
	# for each gene, just grab the max value for each lineage across probes
	pgid = ds.probeIdsFromGeneIds(geneIds=df.index, returnType='dict')
	lineageValues = []
	for geneId in df.index:
		if geneId in pgid:
			e = exp.loc[pgid[geneId]]
			if len(e)>0:
				lineageValues.append(e.max().to_dict())
				continue
		lineageValues.append(None)	
	df.insert(1,'lineageValues',lineageValues)

	# need lineages and colours
	lineages = ds.sampleGroupItems(sampleGroup='cell_lineage')
	lineageColours = ds.sampleGroupColours(sampleGroup='cell_lineage')
	
	return {'scoreTable':df.fillna('').reset_index().to_dict(orient='records'),
			'commentsTable':sg.commentsTable().fillna('').to_dict(orient='records'),
			'lineages':lineages, 'lineageColours':lineageColours}

@view_config(route_name="/grouppages/CSL/scoregenes_save", permission="view", renderer="json")
def saveHematlasScoregenes(request):
	"""Save changes to scoregenes.
	"""
	user = currentUser(request)
	error = checkUserAccessToGroupPage(user, 'CSL', currentEnv(request))
	if error: return {'error':error}
		
	# parse input eg: {"score":"more research required","short comment":"Insufficient expression","extended comment":"test","geneId":"ENSMUSG00000000627"}
	params = request.json_body
	params['user'] = user.fullname
	if 'short comment' in params: params['shortComment'] = params['short comment']
	if 'extended comment' in params: params['comment'] = params['extended comment']

	from haemosphere.models import scoregenes
	sg = scoregenes.ScoreGenes('data/grouppages/CSL/scoregenes_scores.txt', 'data/grouppages/CSL/scoregenes_comments.txt')
		
	return {'user':user.fullname, 'date':sg.saveChanges(**params)}