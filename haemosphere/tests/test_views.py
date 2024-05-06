from __future__ import absolute_import
import unittest
import transaction

from pyramid import testing
import six

'''
From the Haemosphere app directory,

    $ nosetests haemosphere/tests/test_views.py

runs these tests.
'''


def multiDictParams(params):
    """
	Construct and return params portion of webob.request.Request object, given params for request
	as key values pairs.
	Example:
	----------
	>> request = testing.DummyRequest()
	>> request.params = multiDictParams({'geneId':['ENSMUSG00000019982','ENSMUSG00000047591']})
	
	Note that after doing this, you can no longer assign single values to request.params, so 
	>> request.params['datasetName'] = 'Haemopedia'
	won't work anymore. So use multiDictParams({'geneId':['ENSMUSG00000019982','ENSMUSG00000047591'], 'datasetName':'Haemopedia'})
	 
	Details
	----------
	For requests where NestedMultiDict is needed for request.params.getall(),
	it seems I can't assign webob.multidict.NestedMultiDict() directly to params of DummyRequest().
	Instead, create a proper request object using webob.request.Request, set multi dict
	to its params, then we can pass on the same params to the dummy request.
	(Worked this out after looking at https://github.com/Pylons/webob/blob/master/tests/test_request.py)
	"""
    from webob.request import Request
    paramPairs = []
    for key, value in six.iteritems(params):
        if isinstance(value, str) or isinstance(value, six.text_type):
            value = [value]
        paramPairs.append('&'.join(['%s=%s' % (key, val) for val in value]))
    req = Request.blank('/test?%s' % '&'.join(paramPairs))  # proper request object
    return req.params  # pass the params


def dummy_request(dbsession):
    return testing.DummyRequest(dbsession=dbsession)


from haemosphere.models import sharewould


class ViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.request = testing.DummyRequest()

        # need to tell where to look for datasets - match this path to whatever is in config file
        sharewould.init_model('data/datasets')
        self.request.registry.settings['haemosphere.model.datasets.root'] = "data/datasets"

    def tearDown(self):
        testing.tearDown()

    def test_datasetAttributes(self):
        from haemosphere.views.hsdataset_views import datasetAttributes
        request = self.request

        result = datasetAttributes(request)
        self.assertTrue('Goodell' in [ds['name'] for ds in result])

    def test_datasetFromName(self):
        from haemosphere.views.hsdataset_views import datasetFromName
        request = self.request

        ds = datasetFromName(request, 'Goodell')
        self.assertTrue('HSC(1)' in ds.sampleTable().index.tolist())

    def test_geneset(self):
        """Perform search, and check geneset that comes back, then check it has been added
		to current list of genesets. Then rename a geneset, and delete another.
		"""
        import json
        from haemosphere.views.views import searchKeyword
        from haemosphere.views.hsgeneset_views import showCurrentGeneset, renameGeneset, deleteGeneset
        request = self.request

        # searchKeyword uses json_body attribute on request object to access the data
        request.json_body = {'searchString': 'p53'}
        result = searchKeyword(request)
        self.assertTrue(result['genesetSize'] > 90)

        # showCurrentGeneset returns latest searched geneset as the first element of 'historyGenesets'
        result = showCurrentGeneset(request)
        gs = result['historyGenesets'][0]
        self.assertEqual(gs.name, 'Search: p53')
        self.assertTrue(result['guestUser'])

        # renameGeneset
        request.params['type'] = 'history'
        request.params['id'] = 0
        request.params['newName'] = 'p53 search'
        result = renameGeneset(request)
        self.assertEqual(request.session['genesets'][0].name, request.params['newName'])
        self.assertEqual(result['success'], request.params['id'])

        # deleteGeneset
        request.session['genesets'].append(gs)
        self.assertEqual(len(request.session['genesets']), 2)
        request.params['id'] = 1
        result = deleteGeneset(request)
        self.assertEqual(len(request.session['genesets']), 1)

    def test_heatmap(self):
        from haemosphere.views.hsgeneset_views import showHeatmap
        from haemosphere.models import hsgeneset
        request = self.request

        request.params = multiDictParams({'datasetName': 'Haemopedia', 'sampleGroup': 'celltype'})
        gs = hsgeneset.HSGeneset().subset(queryStrings=['p53'], species='MusMusculus')
        request.session['genesets'] = [gs]
        result = showHeatmap(request)
        self.assertEqual(result['datasets'][0]['name'], 'Haemopedia-Mouse-RNASeq')
        self.assertEqual(result['sampleGroups']['Haemopedia'],
                         ['celltype', 'cell_lineage', 'tissue', 'surface_markers'])
        self.assertTrue('Trp53inp1' in [item['displayString'] for item in result['data']['rowLabels']])

    def test_showCorrelatedGenes(self):
        from haemosphere.views.hsgeneset_views import showCorrelatedGenes
        request = self.request
        request.params['featureId'] = "ILMN_2990014"
        request.params['datasetName'] = "Haemopedia"
        result = showCorrelatedGenes(request)
        self.assertTrue(result['genesetSize'] > 0)

    def test_searchKeyword(self):
        from haemosphere.views.views import searchKeyword
        request = self.request
        request.params['searchString'] = 'myb,suz12'
        result = searchKeyword(request)
        self.assertTrue('Myb' in request.session['genesets'][0].geneSymbols())

        request.params['searchScope'] = 'entrez'
        result = searchKeyword(request)
        self.assertEqual(result['genesetSize'], 0)

        request.params['searchString'] = '216810'
        result = searchKeyword(request)
        self.assertEqual(result['genesetSize'], 1)

        request.params['species'] = 'HomoSapiens'
        result = searchKeyword(request)
        self.assertEqual(result['genesetSize'], 0)

        request.params['searchString'] = 'ENSMUSG00000005672\nENSMUSG00000042821'
        request.params['searchScope'] = 'ensembl'
        request.params['species'] = None
        result = searchKeyword(request)
        self.assertEqual(result['genesetSize'], 2)

    def test_searchExpression(self):
        # This test can take a bit of time
        return
        from haemosphere.views.views import searchExpression
        request = self.request
        request.params['dataset'] = 'Haemopedia'
        request.params['sampleGroup'] = 'celltype'
        request.params['sampleGroupItem1'] = 'PreCFUE'
        request.params['sampleGroupItem2'] = 'MEP'
        result = searchExpression(request)
        self.assertEqual(request.session['genesets'][0].size(), 74)

    def test_searchHighExpression(self):
        from haemosphere.views.views import searchHighExpression
        request = self.request
        request.params['dataset'] = 'Haemopedia'
        request.params['sampleGroup'] = 'celltype'
        request.params['sampleGroupItem'] = 'PreCFUE'
        result = searchHighExpression(request)
        self.assertTrue(request.session['genesets'][0].size() > 0)

    def test_showExpression(self):
        from haemosphere.views.expression_views import showExpression
        request = self.request

        request.params = multiDictParams({'geneId': ['ENSMUSG00000019982', 'ENSMUSG00000047591']})
        result = showExpression(request)
        # import json
        # print json.dumps(result['sampleIdsFromSampleGroups'], indent=2)
        self.assertTrue(result['geneset'].startswith('[{"EnsemblId":'))
        self.assertEqual(result['datasets'][0]['name'], 'Haemopedia-Mouse-RNASeq')
        self.assertEqual(result['groupByItems'], ['celltype', 'cell_lineage', 'tissue', 'surface_markers'])
        self.assertEqual(set(result['sampleIdsFromSampleGroups']['celltype']['RegT']),
                         set(['iltp1786a-03', 'iltp1786a-04', 'iltp1786a-05']))
        self.assertEqual(result['sampleGroupItems']['celltype']['cell_lineage']['Eosinophil Lineage'], ['EoP', 'Eo'])
        self.assertEqual(result['sampleGroupColours']['cell_lineage']['B Cell Lineage'], 'rgb(0,0,255)')

    def test_datasetAnalysis(self):
        from haemosphere.views.hsdataset_views import analyseDataset
        request = self.request
        request.params['datasetName'] = 'Haemopedia'
        result = analyseDataset(request)
        self.assertTrue(result['distances'].startswith('[[0.0,'))  # result['distances'] is a string
        self.assertEqual(result['sampleGroups'], ['sampleId', 'celltype', 'cell_lineage', 'tissue', 'surface_markers'])
        self.assertEqual(result['samples'][0]['sampleId'], 'iltp1786a-11')
        self.assertEqual(result['samples'][0]['celltype'], 'B2')

    def test_showSamples(self):
        from haemosphere.views.hsdataset_views import showSamples
        request = self.request
        request.params['selectedDatasetName'] = 'Haemopedia'
        result = showSamples(request)
        assert 'iltp1786a-00' in [item['sampleId'] for item in result['sampleTable']]

    def test_manageHematlasSamples(self):
        from haemosphere.views.group_views import manageHematlasSamples
        from haemosphere.models import users
        from pyramid.security import remember

        request = self.request
        request.registry.settings['haemosphere.env'] = "dev"

        # first try without user
        result = manageHematlasSamples(request)
        self.assertTrue('error' in result)

        # user in wrong group
        request.authenticated_user_id = 'wilson'
        result = manageHematlasSamples(request)
        self.assertTrue('error' in result)

        # this won't work; see https://groups.google.com/forum/#!msg/pylons-discuss/Hm2Dyd5Rwr8/2fI7MhHqLQoJ
        headers = remember(request, 'userid')
        request.authenticated_user_id = 'jarny'
        result = manageHematlasSamples(request)

    # print headers
    # print result

    def test_downloadFile(self):
        from haemosphere.views.downloads import downloadFile
        request = self.request

        # Test AllGenes download
        request.params['filetype'] = 'AllGenes'
        result = downloadFile(request)
        self.assertEqual(result.headers['Content-Disposition'], "attachment; filename=AllGenes.txt")

        # Test AllMouseGeneSymbols
        request.params['filetype'] = 'AllMouseGeneSymbols'
        result = downloadFile(request)
        self.assertEqual(result.headers['Content-Disposition'], "attachment; filename=AllMouseGeneSymbols.txt")
        # Test AllHumanGeneSymbols
        request.params['filetype'] = 'AllHumanGeneSymbols'
        result = downloadFile(request)
        self.assertEqual(result.headers['Content-Disposition'], "attachment; filename=AllHumanGeneSymbols.txt")

        # Test dataset
        request.params['filetype'] = 'dataset'
        request.params['datasetName'] = 'Haemopedia'
        request.params['datasetFile'] = 'expression'
        result = downloadFile(request)
        self.assertEqual(result.headers['Content-Disposition'], "attachment; filename=Haemopedia_expression.txt")

    def test_searchPage(self):
        from haemosphere.views.views import searchPage
        request = self.request
        result = searchPage(request)
        dsnames = [ds['name'] for ds in result['datasets']]
        self.assertTrue('Haemopedia' in dsnames)

    def test_dataset(self):
        from haemosphere.views.hsdataset_views import showDatasets, selectDatasets, orderDatasets
        request = self.request
        result = showDatasets(request)
        datasetNames = [ds['name'] for ds in result['datasets']]
        allDatasetNames = [ds['name'] for ds in result['allDatasets']]
        self.assertTrue('Haemopedia' in datasetNames)
        self.assertTrue('Haemopedia' in allDatasetNames)

    '''	
	def test_datasetRetrieval(self):
		from .views import datasets
		from models import hsdataset
		import time
		
		request = self.request
		
		t0 = time.time()
		result = datasets(request)
		print time.time() - t0, len(result)
		t1 = time.time()
		print len([hsdataset.datasetAttributes(ds.filepath) for ds in result])
		print time.time() - t1
		
	def test_user(self):
		from .views import currentUser
		request = testing.DummyRequest()
		request.registry.settings['haemosphere.model.datasets.root'] = '/Users/jchoi/projects/Hematlas/haemosphere.org/data/datasets'
		user = currentUser(request)
		self.assertEqual(True, True)
	'''


from nose.tools import set_trace as nose_trace


class UserViewTests(unittest.TestCase):
    def setUp(self):
        from haemosphere.models import get_tm_session
        self.config = testing.setUp(settings={
            'sqlalchemy.url': 'sqlite:///:memory:',
            'sqlalchemy2.url': 'sqlite:///:memory:',
            'haemosphere.model.datasets.root': 'data/test-datasets',
            'mail.host': 'unix01.wehi.edu.au',
            'mail.port': '25',
            'mail.sender': 'admin@haemosphere.org',
            'haemosphere.hosturl': '127.0.0.1:6544',
        })
        self.config.include('haemosphere.models')
        self.config.include('haemosphere.routes')
        self.config.include('pyramid_mailer.testing')

        session_factory = self.config.registry['dbsession_factory']
        self.session = get_tm_session(session_factory, transaction.manager)
        self.init_db()
        self.init_forest()
        self.init_security_policy()

    def init_security_policy(self, userid=None):
        self.security_policy = self.config.testing_securitypolicy(userid=userid)
        self.config.set_authorization_policy(self.security_policy)
        self.config.set_authentication_policy(self.security_policy)

    def init_forest(self):
        # initialise new test dataset repository
        dataset_root = self.config.registry.settings['haemosphere.model.datasets.root']
        import shutil, os
        if os.path.exists(dataset_root):
            shutil.rmtree(dataset_root)
        sharewould.init_model(dataset_root)
        sharewould.ShareWould(dataset_root, create_it=True)

    def init_db(self):
        from haemosphere.models.meta import Base
        session_factory = self.config.registry['dbsession_factory']
        engine = session_factory.kw['bind']
        Base.metadata.create_all(engine)

    def tearDown(self):
        testing.tearDown()
        transaction.abort()

    def _createTestUser(self, username='username', fullname='User', email=None, password='password'):
        from haemosphere.models.users import createUser
        if email is None:
            email = username + "@foo.com"
        return createUser(self.session, username, fullname, email, password)

    def _createTestGroup(self, groupname='TestGroup'):
        from haemosphere.models.users import createGroup
        return createGroup(self.session, groupname)

    def _createTestUserAndLogin(self, username='username', admin=False):
        from haemosphere.views.user_views import login
        self.init_security_policy(userid=username)
        u = self._createTestUser(username)
        if admin:
            self._createTestGroup('Admin')
            u.addGroup('Admin')
        request = dummy_request(self.session)
        request.params['form.submitted'] = True
        request.params['username'] = username
        request.params['password'] = 'password'
        login(request)
        return request

    def test_login_invalid(self):
        from haemosphere.views.user_views import login
        self._createTestUser()
        request = dummy_request(self.session)
        request.params['form.submitted'] = True
        request.params['username'] = 'username'
        request.params['password'] = 'badpassword'
        response = login(request)
        self.assertEqual(response['message'], 'Failed login')

    def test_login_valid(self):
        from pyramid.httpexceptions import HTTPFound
        from haemosphere.views.user_views import login
        self._createTestUser('testlogin')
        request = dummy_request(self.session)
        request.params['form.submitted'] = True
        request.params['username'] = 'testlogin'
        request.params['password'] = 'password'
        request.session['last_path'] = '/'
        response = login(request)
        self.assertEqual(type(response), HTTPFound)
        self.assertEqual(response.location, '/')
        self.assertEqual(self.security_policy.remembered, 'testlogin')

    def test_logout(self):
        from haemosphere.views.user_views import logout
        request = self._createTestUserAndLogin('testlogin')
        self.assertEqual(self.security_policy.remembered, 'testlogin')
        logout(request)
        self.assertTrue(self.security_policy.forgotten)

    def test_current_user(self):
        from haemosphere.views.user_views import currentUser
        request = dummy_request(self.session)
        self.assertIsNone(currentUser(request))
        request = self._createTestUserAndLogin('testlogin')
        u = currentUser(request)
        self.assertIsNotNone(u)
        self.assertEqual(u.username, 'testlogin')

    def test_check_username_availability(self):
        from haemosphere.views.user_views import checkUsernameAvailability
        self._createTestUser()
        request = dummy_request(self.session)
        request.params['username'] = 'username'
        self.assertEqual(checkUsernameAvailability(request), {'usernameAvailable': False})
        request.params['username'] = 'anotherusername'
        self.assertEqual(checkUsernameAvailability(request), {'usernameAvailable': True})

    def test_send_confirmation_email(self):
        from haemosphere.views.utility import sendEmail
        from pyramid_mailer import get_mailer
        request = dummy_request(self.session)
        sendEmail(request, 'foo', 'bar', 'barbar')
        mailer = get_mailer(request)
        self.assertEqual(len(mailer.outbox), 1)
        self.assertEqual(mailer.outbox[0].subject, 'foo')
        self.assertEqual(mailer.outbox[0].recipients, 'bar')
        self.assertEqual(mailer.outbox[0].body, 'barbar')

    def test_register_user_valid(self):
        from pyramid.httpexceptions import HTTPFound
        from haemosphere.views.utility import confirmationToken, forest
        from haemosphere.views.user_views import registerUser
        from haemosphere.models.users import getUser
        request = dummy_request(self.session)
        f = forest(request)
        self.assertRaises(OSError, f.inventory, 'username')
        user_properties = {'username': 'username', 'fullname': 'User',
                           'email': 'user@foo.com', 'password': 'password'}
        request.params['token'] = confirmationToken(user_properties, 'register')
        response = registerUser(request)
        self.assertIsNotNone(getUser(request.dbsession, 'username'))
        self.assertEqual(type(response), HTTPFound)
        self.assertEqual(response.location, '/')
        self.assertEqual(self.security_policy.remembered, 'username')
        f = forest(request)
        self.assertEqual(type(f.inventory('username')), list)

    def test_register_user_invalid(self):
        from pyramid.httpexceptions import HTTPFound
        from haemosphere.views.user_views import registerUser
        request = dummy_request(self.session)
        request.params['token'] = "foobar"
        response = registerUser(request)
        self.assertEqual(type(response), HTTPFound)
        self.assertEqual(response.location, "/login?message=Error with registration.")

    def test_retrieve_user_details(self):
        from haemosphere.views.user_views import retrieveUserDetails
        from haemosphere.models import users
        from pyramid_mailer import get_mailer
        request = dummy_request(self.session)

        request.params['email'] = 'no match'
        result = retrieveUserDetails(request)
        self.assertTrue(result['message'].startswith('No user'))

        self._createTestUser()
        request.params['email'] = 'username@foo.com'
        result = retrieveUserDetails(request)
        self.assertEqual(result['message'], 'Email has been sent.')
        mailer = get_mailer(request)
        self.assertEqual(len(mailer.outbox), 1)
        email = mailer.outbox[0]
        self.assertEqual(email.subject, 'User detail retrieval for Haemosphere')
        self.assertEqual(email.recipients, [u'username@foo.com'])
        self.assertIn(u"Hi User,\n\nYour username in Haemosphere "
                      "is username.\nClick on this link if you "
                      "wish to reset your password:", email.body)

    def test_user_account(self):
        from haemosphere.views.user_views import userAccount
        from haemosphere.models.users import getUser
        request = self._createTestUserAndLogin()
        response = userAccount(request)
        self.assertEqual(len(response), 2)
        self.assertEqual(response['user'], getUser(self.session, 'username'))
        self.assertEqual(response['groupPages'], [])

    def test_update_user_account(self):
        from haemosphere.views.user_views import updateUserAccount
        from haemosphere.models.users import User
        request = dummy_request(self.session)
        resp = updateUserAccount(request)
        self.assertEqual(resp, {'error': 'No user "None" found.'})
        request = self._createTestUserAndLogin()
        resp = updateUserAccount(request)
        self.assertEqual(resp, {'error': 'No matching attribute to update'})

        request.params.update({'attr': 'fullname', 'value': 'User Q. User'})
        resp = updateUserAccount(request)
        self.assertEqual(resp['fullname'], 'User Q. User')

        request.params.update({'attr': 'email', 'value': 'uquser@foo.com'})
        resp = updateUserAccount(request)
        self.assertEqual(resp['email'], 'uquser@foo.com')

        request.params.update({'attr': 'password', 'value': 'iheartuser'})
        resp = updateUserAccount(request)
        self.assertEqual(resp['password'], User.hash('iheartuser'))

    def test_show_reset_user_password(self):
        from haemosphere.views.utility import confirmationToken
        from haemosphere.views.user_views import showResetUserPassword
        request = self._createTestUserAndLogin()
        resp = showResetUserPassword(request)
        self.assertEqual(resp, {'error': "The link for resetting password "
                                         "expired. Please go through the "
                                         "process again."})
        url = confirmationToken('username', 'password')
        request.params['url'] = url
        resp = showResetUserPassword(request)
        self.assertEqual(resp, {'token': url})

    def test_reset_user_password(self):
        from haemosphere.views.utility import confirmationToken
        from haemosphere.views.user_views import resetUserPassword
        request = self._createTestUserAndLogin()
        resp = resetUserPassword(request)
        self.assertEqual(resp, {'passwordChanged': False})

        token = confirmationToken('username', 'password')
        new_password = 'foo'
        request.params.update({'token': token, 'password': new_password})
        resp = resetUserPassword(request)
        self.assertEqual(resp, {'passwordChanged': True})

    def test_show_users(self):
        from haemosphere.views.user_views import showUsers, currentUser
        from pyramid.httpexceptions import HTTPFound
        self._createTestGroup('Admin')
        self._createTestGroup('HaemoPoets')
        self._createTestUser('jaime')
        self._createTestUser('cersei')
        self._createTestUser('tyrion')

        request = self._createTestUserAndLogin()
        resp = showUsers(request)
        self.assertEqual(type(resp), HTTPFound)
        self.assertEqual(resp.location, request.route_path('/user/account'))

        currentUser(request).addGroup('Admin')
        resp = showUsers(request)
        self.assertEqual(len(resp), 2)
        self.assertEqual(len(resp['users']), 4)
        self.assertEqual(sorted(resp['groups']), ['Admin', 'HaemoPoets'])

    def test_manage_user_account(self):
        from haemosphere.views.user_views import manageUserAccount, currentUser
        from haemosphere.views.utility import forest
        from haemosphere.models.users import allGroups, getUser
        self._createTestGroup('Admin')
        self._createTestGroup('Boltons')
        self._createTestUser('sansa')
        self._createTestUser('ramsay')
        request = self._createTestUserAndLogin()

        resp = manageUserAccount(request)
        self.assertEqual(resp, {'error': 'only users in Admin group are '
                                         'allowed to manage users.'})

        currentUser(request).addGroup('Admin')
        request.params['action'] = 'create_group'
        request.POST['name'] = 'Starks'
        resp = manageUserAccount(request)
        self.assertIn('Starks', [g.name for g in allGroups(self.session)])

        request.params['action'] = 'delete_group'
        request.POST['name'] = 'Boltons'
        resp = manageUserAccount(request)
        self.assertNotIn('Boltons', [g.name for g in allGroups(self.session)])

        request.params['action'] = 'add_group_to_user'
        request.params['username'] = 'sansa'
        request.params['groupname'] = 'Starks'
        resp = manageUserAccount(request)
        self.assertIn('Starks', getUser(self.session, 'sansa').groupnames())

        request.params['action'] = 'remove_group_from_user'
        resp = manageUserAccount(request)
        self.assertNotIn('Starks', getUser(self.session, 'sansa').groupnames())

        request.params['action'] = 'create_user'
        request.params.update({'username': 'jon', 'fullname': 'Jon Snow',
                               'email': 'jon@housestark.com', 'password': 'unonothing'})
        resp = manageUserAccount(request)
        self.assertIsNotNone(getUser(self.session, 'jon'))
        f = forest(request)
        self.assertEqual(type(f.inventory('jon')), list)

        request.params['action'] = 'delete_user'
        request.params['username'] = 'ramsay'
        resp = manageUserAccount(request)
        self.assertIsNone(getUser(self.session, 'ramsay'))

        request.params['action'] = 'edit_user'
        request.POST.update({'currentUsername': 'sansa', 'newUsername': 'sansa',
                             'fullname': 'Sansa Stark', 'email': 'sansa@housestark.com'})
        resp = manageUserAccount(request)
        sansa = getUser(self.session, 'sansa')
        self.assertEqual(sansa.fullname, 'Sansa Stark')
        self.assertEqual(sansa.email, 'sansa@housestark.com')

        request.POST.update({'currentUsername': 'jon', 'newUsername': 'jonsnow',
                             'fullname': 'Jon Snow', 'email': 'jon@housestark.com'})
        resp = manageUserAccount(request)
        self.assertIsNotNone(getUser(self.session, 'jonsnow'))

        f = forest(request)
        self.assertRaises(OSError, f.inventory, 'jon')
        self.assertEqual(type(f.inventory('jonsnow')), list)

    def test_send_email_to_users(self):
        from haemosphere.views.user_views import sendEmailToUsers
        from pyramid_mailer import get_mailer
        request = dummy_request(self.session)
        mailer = get_mailer(request)

        response = sendEmailToUsers(request)
        self.assertEqual(response['message'], "Only Admin users are allowed to email other users.")
        self.assertEqual(len(mailer.outbox), 0)

        self._createTestUserAndLogin("farnsworth", admin=True)
        response = sendEmailToUsers(request)
        self.assertEqual(response['message'], "Email not sent: no form data supplied.")
        self.assertEqual(len(mailer.outbox), 0)

        request.params['data'] = {'foo': 'bar'}
        response = sendEmailToUsers(request)
        self.assertEqual(response['message'], "Email not sent: no recipients specified.")
        self.assertEqual(len(mailer.outbox), 0)

        request.params['data']['recipients'] = ''
        response = sendEmailToUsers(request)
        self.assertEqual(response['message'], "Email not sent: no subject line specified.")
        self.assertEqual(len(mailer.outbox), 0)

        request.params['data']['subject'] = 'Good News'
        response = sendEmailToUsers(request)
        self.assertEqual(response['message'], "Email not sent: no email content specified.")
        self.assertEqual(len(mailer.outbox), 0)

        request.params['data']['body'] = 'Good news, everyone!'
        response = sendEmailToUsers(request)
        self.assertEqual(response['message'], "Email not sent: no recipients specified.")
        self.assertEqual(len(mailer.outbox), 0)

        request.params['data']['recipients'] = 'fry,leela,bender'
        response = sendEmailToUsers(request)
        self.assertEqual(response['message'], "Email not sent: username 'fry' is invalid")
        self.assertEqual(len(mailer.outbox), 0)

        self._createTestUser('fry', fullname='Philip J. Fry')
        response = sendEmailToUsers(request)
        self.assertEqual(response['message'], "Email not sent: username 'leela' is invalid")
        self.assertEqual(len(mailer.outbox), 0)

        self._createTestUser('leela', fullname='Leela')
        self._createTestUser('bender', fullname='Bender')
        response = sendEmailToUsers(request)
        self.assertEqual(response['message'], "Email sent to users: fry, leela, bender")
        self.assertEqual(len(mailer.outbox), 3)
        self.assertEqual(mailer.outbox[0].subject, "Good News")
        self.assertEqual(mailer.outbox[0].body, "Dear Philip J. Fry,"
                                                "\n\nGood news, everyone!"
                                                "\n\nRegards,\nHaemosphere Team\nhaemosphere.org")

    def test_group_pages(self):
        from haemosphere.views.group_views import groupPages
        self._createTestGroup()
        self._createTestGroup('HiltonLab')
        self._createTestGroup('CSL')

        pages = groupPages(['TestGroup'])
        self.assertEqual(pages, [])

        hiltonpage = {'url': '/grouppages/HiltonLab/samples', 'group': 'HiltonLab',
                      'display': 'View/edit all Hiltonlab sample data'}
        cslpage = {'url': '/grouppages/CSL/scoregenes', 'group': 'CSL', 'display': 'Score Genes'}

        self.assertEqual(groupPages(['HiltonLab']), [hiltonpage])
        self.assertEqual(groupPages(['CSL']), [cslpage])
        pages = groupPages(['HiltonLab', 'CSL'])
        self.assertEqual(len(pages), 2)
        self.assertIn(hiltonpage, pages)
        self.assertIn(cslpage, pages)

    def test_check_user_access_to_group_page(self):
        from haemosphere.views.group_views import checkUserAccessToGroupPage as checkAccess
        from haemosphere.models.users import getUser
        allgood = ''
        baduser = 'User does not have access to this page.'
        badenv = 'This function is not available in this server environment.'

        self._createTestGroup()
        self._createTestUser()

        u = getUser(self.session, 'username')
        resp = checkAccess(u, 'TestGroup', 'dev', ['dev'])
        self.assertEqual(resp, baduser)
        resp = checkAccess(u, 'TestGroup', 'private', ['dev'])
        self.assertEqual(resp, baduser)

        u.addGroup('TestGroup')
        resp = checkAccess(u, 'TestGroup', 'dev', ['dev'])
        self.assertEqual(resp, allgood)
        resp = checkAccess(u, 'TestGroup', 'public', ['dev'])
        self.assertEqual(resp, badenv)
