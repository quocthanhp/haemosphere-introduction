'''
Unit tests for models.

These tests are adapted from the following examples:
http://docs.pylonsproject.org/projects/pyramid/en/latest/tutorials/wiki2/tests.html
https://github.com/Pylons/shootout/blob/master/shootout/tests/test_models.py

From the Haemosphere app directory,

    $ nosetests haemosphere/tests/test_models.py

runs these tests.
'''
import unittest
import transaction

from pyramid import testing

from haemosphere.tests.test_views import dummy_request

'''
Set up testing for users model and its sql database
'''
class ModelsTest(unittest.TestCase):
    def setUp(self):
        from haemosphere.models import get_tm_session
        self.config = testing.setUp(settings={
            'sqlalchemy.url': 'sqlite:///:memory:',
            'sqlalchemy2.url': 'sqlite:///:memory:'
        })
        self.config.include('haemosphere.models')

        session_factory = self.config.registry['dbsession_factory']
        self.session = get_tm_session(session_factory, transaction.manager)
    
        self.init_db()

    def init_db(self):
        from haemosphere.models.meta import Base
        session_factory = self.config.registry['dbsession_factory']
        engine = session_factory.kw['bind']
        Base.metadata.create_all(engine)

    def tearDown(self):
        testing.tearDown()
        transaction.abort()

'''
Set up testing for labsamples model and its sql database
'''     
class LabSamplesModelTest(unittest.TestCase):
    def setUp(self):
        from haemosphere.models import get_tm_session
        self.config = testing.setUp(settings={
            'sqlalchemy.url': 'sqlite:///:memory:',
            'sqlalchemy2.url': 'sqlite:///:memory:'
        })
        self.config.include('haemosphere.models')

        session_factory = self.config.registry['ls_dbs_factory']
        self.session = get_tm_session(session_factory, transaction.manager)
    
        self.init_db()

    def init_db(self):
        from haemosphere.models.labsamples import Base
        session_factory = self.config.registry['ls_dbs_factory']
        engine = session_factory.kw['bind']
        Base.metadata.create_all(engine)

    def tearDown(self):
        testing.tearDown()
        transaction.abort()


class UserTests(ModelsTest):
    def _createTestUser(self, username='username', fullname='User', email=None, password='password'):
        from haemosphere.models.users import createUser
        if email is None:
            email = username + "@foo.com"
        return createUser(self.session, username, fullname, email, password)

    def _createTestGroup(self, groupname='TestGroup'):
        from haemosphere.models.users import createGroup
        return createGroup(self.session, groupname)

    def test_create_group(self):
        from haemosphere.models.users import Group
        self._createTestGroup()
        groups = self.session.query(Group).all()
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].name, 'TestGroup')

    def test_create_group_groupname_exists(self):
        from haemosphere.models.users import Group
        self._createTestGroup()
        # need to commit transaction to avoid this INSERT getting rolled
        # back along with the uniqueness-violating INSERT
        transaction.commit()
        self.assertRaises(ValueError, self._createTestGroup)
        num_groups = self.session.query(Group).count()
        self.assertEqual(num_groups, 1)

    def test_change_groupname(self):
        from haemosphere.models.users import Group
        self._createTestGroup()
        group = self.session.query(Group).filter_by(name='TestGroup').first()
        group.name = 'CoolGroupName'
        self.session.flush()
        num_cool_groups = self.session.query(Group).filter_by(name='CoolGroupName').count()
        num_uncool_groups = self.session.query(Group).filter_by(name='TestGroup').count()
        self.assertEqual(num_cool_groups, 1)
        self.assertEqual(num_uncool_groups, 0)

    def test_delete_group_exists(self):
        from haemosphere.models.users import Group, deleteGroup
        self._createTestGroup()
        deleteGroup(self.session, 'TestGroup')
        count = self.session.query(Group).filter_by(name='TestGroup').count()
        self.assertEqual(count, 0)

    def test_delete_group_doesnt_exist(self):
        """
        deleteGroup handles the NoResultFound exception,
        so we don't get any warning about this.
        """
        from haemosphere.models.users import Group, deleteGroup
        num_groups = self.session.query(Group).count()
        self.assertEqual(num_groups, 0)
        self.assertRaises(ValueError, deleteGroup, self.session, 'TestGroup')

    def test_all_groups(self):
        from haemosphere.models.users import Group, allGroups
        self.assertEqual(allGroups(self.session), [])
        expected_names = ['TestierGroup', 'TestiestGroup', 'TestyGroup']
        for name in expected_names:
            self._createTestGroup(name)
        actual_names = [group.name for group in allGroups(self.session)]
        self.assertEqual(sorted(actual_names), expected_names)

    def test_create_user(self):
        from haemosphere.models.users import User
        self._createTestUser()
        user = self.session.query(User).filter_by(username='username').first()
        self.assertEqual(user.username, 'username')
        self.assertEqual(user.fullname, 'User')
        self.assertEqual(user.email, 'username@foo.com')

    def test_create_user_username_exists(self):
        from haemosphere.models.users import User
        self._createTestUser()
        # need to commit transaction to avoid this INSERT getting rolled
        # back along with the uniqueness-violating INSERT
        transaction.commit()
        u = self._createTestUser()
        self.assertIsNone(u)
        num_users = self.session.query(User).count()
        self.assertEqual(num_users, 1)

    def test_get_user_exists(self):
        from haemosphere.models.users import getUser
        self._createTestUser()
        u = getUser(self.session, 'username')
        self.assertEqual(u.username, 'username')
        u = getUser(self.session, 'username@foo.com', tryEmail=False)
        self.assertIsNone(u)
        u = getUser(self.session, 'username@foo.com')
        self.assertEqual(u.username, 'username')

    def test_get_user_doesnt_exist(self):
        from haemosphere.models.users import getUser
        u = getUser(self.session, 'username')
        self.assertIsNone(u)

    def test_delete_user_exists(self):
        from haemosphere.models.users import User, deleteUser
        self._createTestUser()
        num_users = self.session.query(User).count()
        self.assertEqual(num_users, 1)
        deleteUser(self.session, 'username')
        num_users = self.session.query(User).count()
        self.assertEqual(num_users, 0)

    def test_delete_user_doesnt_exist(self):
        """
        deleteUser handles the NoResultFound exception,
        so we don't get any warning about this.
        """
        from haemosphere.models.users import User, deleteUser
        num_users = self.session.query(User).count()
        self.assertEqual(num_users, 0)
        deleteUser(self.session, 'username')
        num_users = self.session.query(User).count()
        self.assertEqual(num_users, 0)

    def test_change_username(self):
        from haemosphere.models.users import User, editUser, getUser
        u = self._createTestUser()
        editUser(self.session, u.username, 'betterusername', u.fullname, u.email)
        self.assertEqual(u.username, 'betterusername')
        u = getUser(self.session, 'username')
        self.assertIsNone(u)
        u = getUser(self.session, 'betterusername')
        self.assertIsNotNone(u)
        # editUser also needs to validate uniqueness of username
        self._createTestUser(fullname='User2', email='foo2@foo.com')
        transaction.commit()
        u = getUser(self.session, 'username')
        self.assertRaises(ValueError, editUser, self.session, 'username', 'betterusername', u.fullname, u.email)
        # betterusername already exists, so edit gets rolled back
        # and User2 keeps 'username' as username
        u = getUser(self.session, 'username')
        self.assertIsNotNone(u)
        self.assertEqual(u.fullname, 'User2')

    def test_change_user_details(self):
        from haemosphere.models.users import User, editUser, getUser
        u = self._createTestUser()
        editUser(self.session, u.username, u.username, 'User von User', u.email)
        u = getUser(self.session, 'username')
        self.assertEqual(u.fullname, 'User von User')
        editUser(self.session, u.username, u.username, u.fullname, 'foo2@foo.com')
        u = getUser(self.session, 'username')
        self.assertEqual(u.email, 'foo2@foo.com')
        editUser(self.session, u.username, u.username, 'User', 'foo@foo.com')
        u = getUser(self.session, 'username')
        self.assertEqual(u.fullname, 'User')
        self.assertEqual(u.email, 'foo@foo.com')
        # if username update fails, entire edit is aborted
        self._createTestUser(username='username2', fullname='User2')
        transaction.commit()
        u = getUser(self.session, 'username2')
        self.assertRaises(ValueError, editUser, self.session, u.username, 'username', 'User2 deUser', u.email)
        u = getUser(self.session, 'username2')
        self.assertEqual(u.fullname, 'User2')

    def test_set_password(self):
        from haemosphere.models.users import User
        u = self._createTestUser(password='pw')
        self.assertEqual(u.password, User.hash('pw'))

    def test_check_password(self):
        u = self._createTestUser(password='pw')
        self.assertTrue(u.check_password('pw'))
        self.assertFalse(u.check_password('pww'))
        self.assertFalse(u.check_password(''))

    def test_reset_password(self):
        from haemosphere.models.users import resetUserPassword, getUser
        self._createTestUser()

        u = getUser(self.session, 'username')
        self.assertTrue(u.check_password('password'))

        resetUserPassword(self.session, 'username', 'abcd1234')
        u = getUser(self.session, 'username')
        self.assertTrue(u.check_password('abcd1234'))

        resetUserPassword(self.session, 'username')
        u = getUser(self.session, 'username')
        self.assertTrue(u.check_password('username@foo.com'))

    def test_add_group(self):
        from haemosphere.models.users import getUser
        self._createTestUser()
        u = getUser(self.session, 'username')
        self.assertEqual(len(u.groups), 0)
        self.assertRaises(ValueError, u.addGroup, 'TestGroup')
        self._createTestGroup()
        u.addGroup('TestGroup')
        self.assertEqual(len(u.groups), 1)

    def test_remove_group(self):
        from haemosphere.models.users import getUser
        self._createTestUser()
        self._createTestGroup()
        u = getUser(self.session, 'username')
        u.addGroup('TestGroup')
        self.assertEqual(len(u.groups), 1)
        self.assertRaises(ValueError, u.removeGroup, 'SomeOtherGroup')
        self.assertEqual(len(u.groups), 1)
        u.removeGroup('TestGroup')
        self.assertEqual(len(u.groups), 0)

    def test_groupnames(self):
        from haemosphere.models.users import getUser
        u = self._createTestUser()
        expected = ['TestyGroup', 'TestierGroup', 'TestiestGroup']
        for name in expected:
            self._createTestGroup(name)
            u.addGroup(name)
        actual = u.groupnames()
        self.assertEqual(sorted(actual), sorted(expected))

    def test_isAdmin(self):
        from haemosphere.models.users import getUser
        u = self._createTestUser()
        self.assertFalse(u.isAdmin())
        self._createTestGroup('Admin')
        u.addGroup('Admin')
        self.assertTrue(u.isAdmin())

    def test_to_json(self):
        from haemosphere.models.users import User, getUser
        u = self._createTestUser()
        self._createTestGroup()
        u.addGroup('TestGroup')
        expected = {'username': 'username',
                    'fullname': 'User',
                    'email': 'username@foo.com',
                    'password': User.hash('password'),
                    'groups': ['TestGroup']
                    }
        self.assertEqual(u.to_json(), expected)

    def test_group_finder(self):
        from haemosphere.models.users import User, getUser
        u = self._createTestUser()
        self._createTestGroup()
        self._createTestGroup('Admin')
        u.addGroup('TestGroup')
        u.addGroup('Admin')
        request = dummy_request(self.session)
        expected = ['group:Admin', 'group:TestGroup']
        actual = User.group_finder('username', request)
        self.assertEqual(sorted(actual), expected)

    def test_all_users(self):
        from haemosphere.models.users import User, allUsers
        self.assertEqual(allUsers(self.session), [])
        expected_names = ['username', '2sername', '3sername']
        for name in expected_names:
            u = self._createTestUser(username=name)
            self.assertIsNotNone(u)
        actual_names = [u.username for u in allUsers(self.session)]
        self.assertEqual(sorted(actual_names), sorted(expected_names))
        





######################################################################
#   Labsample Tests
######################################################################
class SampleTests(LabSamplesModelTest):
    def _createTestSample(self, sample_id="test sample", cell_num="100", elution_date="12.01.15", 
                elution_volume="10", rin="20", rna="30", rna_prep="prep", sort_date="13.01.15", 
                total_rna="100", amplified_rna_bio="sample_bio", description="test description", 
                notes="test notes", original_sample_id=None, previous_sample_id=None, 
                genotype="test geno", treatment="test treatment", group="test group", batch=None, celltype=None):
        from haemosphere.models.labsamples import newSample
        data = {"sample_id":sample_id, "cell_num":cell_num, "elution_date":elution_date, "elution_volume":elution_volume,
                "elution_date":elution_date, "rin":rin, "rna":rna, "rna_prep":rna_prep, "sort_date":sort_date, 
                "total_rna":total_rna, "amplified_rna_bio":amplified_rna_bio, "description":description, 
                "notes":notes, "original_sample_id":original_sample_id, "previous_sample_id":previous_sample_id, 
                "genotype":genotype, "treatment":treatment, "group":group, "batch":batch, "celltype":celltype}
        return newSample(self.session, data)
        
    def _newSampleData(self, sample_id="test sample", cell_num="100", elution_date="12.01.15", 
                elution_volume="10", rin="20", rna="30", rna_prep="prep", sort_date="13.01.15", 
                total_rna="100", amplified_rna_bio="sample_bio", description="test description", 
                notes="test notes", original_sample_id=None, previous_sample_id=None, 
                genotype="test geno", treatment="test treatment", group="test group", batch=None, celltype=None):                
        return {"sample_id":sample_id, "cell_num":cell_num, "elution_date":elution_date, "elution_volume":elution_volume,
                "elution_date":elution_date, "rin":rin, "rna":rna, "rna_prep":rna_prep, "sort_date":sort_date, 
                "total_rna":total_rna, "amplified_rna_bio":amplified_rna_bio, "description":description, 
                "notes":notes, "original_sample_id":original_sample_id, "previous_sample_id":previous_sample_id, 
                "genotype":genotype, "treatment":treatment, "group":group, "batch":batch, "celltype":celltype}

    def _createTestCelltype(self, celltype="test celltype", cell_lineage="test_cell_lineage", 
                colour="test colour", description="test description", include_haemopedia="no", 
                maturity="test maturity", notes="test notes", order="test order", 
                species="test species", strain="test strain", surface_markers="test surface markers", 
                previous_names=None, tissue="test tissue"):
        from haemosphere.models.labsamples import newCelltype
        data = {"celltype":celltype, "cell_lineage":cell_lineage, "colour":colour, 
                "description":description, "include_haemopedia":include_haemopedia, 
                "maturity":maturity, "notes":notes, "order":order, 
                "species":species, "strain":strain, "surface_markers":surface_markers, 
                "previous_names":previous_names, "tissue":tissue}        
        return newCelltype(self.session, data)   
        
    def _newCelltypeData(self, celltype="test celltype", cell_lineage="test_cell_lineage", 
                colour="test colour", description="test description", include_haemopedia="no", 
                maturity="test maturity", notes="test notes", order="test order", 
                species="test species", strain="test strain", surface_markers="test surface markers", 
                previous_names=None, tissue="test tissue"):
        return {"celltype":celltype, "cell_lineage":cell_lineage, "colour":colour, 
                "description":description, "include_haemopedia":include_haemopedia, 
                "maturity":maturity, "notes":notes, "order":order, 
                "species":species, "strain":strain, "surface_markers":surface_markers, 
                "previous_names":previous_names, "tissue":tissue}  
    
    def _createTestBatch(self, batch_id="test batch", description="test description", 
                date_data_received="12.01.15"):
        from haemosphere.models.labsamples import newBatch
        data = {"batch_id":batch_id, "description":description, "date_data_received":date_data_received}
        return newBatch(self.session, data)
        
    def _newBatchData(self, batch_id="test batch", description="test description", 
                date_data_received="12.01.15"):
        return {"batch_id":batch_id, "description":description, "date_data_received":date_data_received}    
        
    '''
    Insert batch and celltype into db, followed by a sample with a relationship to the celltype
    '''
    def _createTestRelationships(self):
        celltype = self._createTestCelltype()
        batch = self._createTestBatch()
        sample = self._createTestSample(celltype=celltype[0].celltype)        
            
    ######################################################################
    #   Sample Tests
    ######################################################################       
    def test_newSample(self):
        from haemosphere.models.labsamples import Sample
        self._createTestSample()
        sample = self.session.query(Sample).filter_by(sample_id='test sample').first()
        self.assertEqual(sample.sample_id, "test sample")
        self.assertEqual(sample.cell_num, "100")
        self.assertEqual(sample.elution_date, "12.01.15")
        self.assertEqual(sample.elution_volume, "10")
        self.assertEqual(sample.rin, '20')
        self.assertEqual(sample.rna, '30')        
        self.assertEqual(sample.rna_prep, 'prep')
        self.assertEqual(sample.sort_date, '13.01.15')
        self.assertEqual(sample.total_rna, '100')
        self.assertEqual(sample.amplified_rna_bio, 'sample_bio')
        self.assertEqual(sample.description, 'test description')
        self.assertEqual(sample.notes, 'test notes')
        self.assertEqual(sample.original_sample_id, None)
        self.assertEqual(sample.previous_sample_id, None)
        self.assertEqual(sample.genotype, 'test geno')
        self.assertEqual(sample.treatment, 'test treatment')
        self.assertEqual(sample.group, 'test group')
    
    def test_sample_repr(self):
        sample = self._createTestSample()
        expected = "<Sample sample_id='test sample' description='test description'>"    
        self.assertEqual(sample[0].__repr__(), expected)
    

    def test_getSample(self):
        sample = self._createTestSample()
        from haemosphere.models.labsamples import getSample
        result = getSample(self.session, 'id', 1)
        self.assertEqual(result, sample[0])
        
        result = getSample(self.session, 'id', 0)
        self.assertEqual(result, None)
        
    def test_editSample(self):    
        sample = self._createTestSample()
        from haemosphere.models.labsamples import editSample
        editSample(self.session, 1, "cell_num", "300")
        self.assertEqual(sample[0].cell_num, "300")
        self.assertNotEqual(sample[0].cell_num, "100")
        
        sample2 = self._createTestSample(sample_id="test sample2")        
        self.assertRaises(ValueError, editSample, self.session, 2, "sample_id", "test sample")

    def test_deleteSample(self):
        sample = self._createTestSample()
        from haemosphere.models.labsamples import deleteSample
        from haemosphere.models.labsamples import Sample

        count = self.session.query(Sample).filter_by(sample_id=sample[0].sample_id).count()
        self.assertEqual(count, 1)

        deleteSample(self.session, sample[0].id)
        count = self.session.query(Sample).filter_by(sample_id=sample[0].sample_id).count()
        self.assertEqual(count, 0)


    def test_getAllSamples(self):
        sample = self._createTestSample()
        sample2 = self._createTestSample(sample_id="test sample2", cell_num="200")        
        from haemosphere.models.labsamples import getAllSamples
        results = getAllSamples(self.session, "cell_num", "200")
        self.assertEqual(len(results), 1)
        
        results = getAllSamples(self.session, "cell_num", "300")
        self.assertEqual(len(results), 0)
        
        results = getAllSamples(self.session, "rin", "20")
        self.assertEqual(len(results), 2)

    def test_getAllSampleData(self):
        sample = self._createTestSample()
        sample2 = self._createTestSample(sample_id="test sample2")
        from haemosphere.models.labsamples import getAllSampleData
        columns = ["id", "sample_id", "celltype", "batch", "cell_num", "elution_date", "elution_volume", "rin", "rna", "rna_prep", "sort_date", 
                "total_rna", "amplified_rna_bio", "description",
                "notes", "original_sample_id", "previous_sample_id", "genotype",
                "treatment", "group"]
        results = getAllSampleData(self.session)
        self.assertEqual(results['columns'], columns)
        self.assertEqual(results['data'][0][1], sample[0].sample_id)
        self.assertEqual(results['data'][1][1], sample2[0].sample_id)

    def test_getSampleColumnNames(self):
        from haemosphere.models.labsamples import getSampleColumnNames
        expected = ["id", "sample_id", "cell_num", "elution_date", "elution_volume", "rin", "rna", "rna_prep", "sort_date", 
                "total_rna", "amplified_rna_bio", "batch_id", "celltype_id", "description",
                "notes", "original_sample_id", "previous_sample_id", "genotype",
                "treatment", "group"]
        results = getSampleColumnNames()

        self.assertEqual(results, expected)


    ######################################################################
    #   Celltype Tests
    ######################################################################       
    def test_newCelltype(self):
        from haemosphere.models.labsamples import Celltype
        self._createTestCelltype()
        celltype = self.session.query(Celltype).filter_by(celltype='test celltype').first()
        self.assertEqual(celltype.celltype, "test celltype")
        self.assertEqual(celltype.cell_lineage, "test_cell_lineage")
        self.assertEqual(celltype.colour, "test colour")
        self.assertEqual(celltype.description, "test description")
        self.assertEqual(celltype.include_haemopedia, 'no')
        self.assertEqual(celltype.maturity, 'test maturity')        
        self.assertEqual(celltype.notes, 'test notes')
        self.assertEqual(celltype.order, 'test order')
        self.assertEqual(celltype.species, 'test species')
        self.assertEqual(celltype.strain, 'test strain')
        self.assertEqual(celltype.surface_markers, 'test surface markers')
        self.assertEqual(celltype.previous_names, None)
        self.assertEqual(celltype.tissue, "test tissue")
    
        celltype2 = self._createTestCelltype()
        self.assertEqual(celltype2[0], None)
    
    def test_celltype_repr(self):
        celltype = self._createTestCelltype()
        expected = "<Celltype celltype='test celltype' description='test description'>"    
        self.assertEqual(celltype[0].__repr__(), expected)
    
    def test_celltype_str(self):
        celltype = self._createTestCelltype()
        expected = "test celltype"    
        self.assertEqual(celltype[0].__str__(), expected)    
        
    def test_getCelltype(self):
        celltype = self._createTestCelltype()
        from haemosphere.models.labsamples import getCelltype
        result = getCelltype(self.session, 'id', 1)
        self.assertEqual(result, celltype[0])
        
        result = getCelltype(self.session, 'id', 0)
        self.assertEqual(result, None)
        
    def test_editCelltype(self):    
        celltype = self._createTestCelltype()
        from haemosphere.models.labsamples import editCelltype
        editCelltype(self.session, 1, "cell_lineage", "new test_cell_lineage")
        self.assertEqual(celltype[0].cell_lineage, "new test_cell_lineage")
        self.assertNotEqual(celltype[0].cell_lineage, "test_cell_lineage")
        
        celltype2 = self._createTestCelltype(celltype="test celltype2")        
        self.assertRaises(ValueError, editCelltype, self.session, 2, "celltype", "test celltype")

    def test_deleteCelltype(self):
        celltype = self._createTestCelltype()
        from haemosphere.models.labsamples import deleteCelltype
        from haemosphere.models.labsamples import Celltype

        count = self.session.query(Celltype).filter_by(celltype=celltype[0].celltype).count()
        self.assertEqual(count, 1)
        
        deleteCelltype(self.session, celltype[0].id)
        count = self.session.query(Celltype).filter_by(celltype=celltype[0].celltype).count()
        self.assertEqual(count, 0)

    def test_getAllCelltypes(self):
        celltype = self._createTestCelltype()
        celltype2 = self._createTestCelltype(celltype="test celltype2", cell_lineage="new test_cell_lineage")        
        from haemosphere.models.labsamples import getAllCelltypes
        results = getAllCelltypes(self.session, "cell_lineage", "new test_cell_lineage")
        self.assertEqual(len(results), 1)
        
        results = getAllCelltypes(self.session, "cell_lineage", "newer test_cell_lineage")
        self.assertEqual(len(results), 0)
        
        results = getAllCelltypes(self.session, "tissue", "test tissue")
        self.assertEqual(len(results), 2)

    def test_getAllCelltypeData(self):
        celltype = self._createTestCelltype()
        celltype2 = self._createTestCelltype(celltype="test celltype2")
        from haemosphere.models.labsamples import getAllCelltypeData
        columns = ["id", "celltype", "cell_lineage", "colour", "description", 
                "include_haemopedia", "maturity", "notes", "order", "species", 
                "strain", "surface_markers", "previous_names", "tissue"]                
                
        results = getAllCelltypeData(self.session)
        self.assertEqual(results['columns'], columns)
        self.assertEqual(results['data'][0][1], celltype[0].celltype)
        self.assertEqual(results['data'][1][1], celltype2[0].celltype)

    def test_getCelltypeColumnNames(self):
        from haemosphere.models.labsamples import getCelltypeColumnNames
        expected = ["id", "celltype", "cell_lineage", "colour", "description", 
                "include_haemopedia", "maturity", "notes", "order", "species", 
                "strain", "surface_markers", "previous_names", "tissue"] 
        results = getCelltypeColumnNames()
        self.assertEqual(results, expected)

    ######################################################################
    #   Batch Tests
    ######################################################################    
    def test_newBatch(self):
        from haemosphere.models.labsamples import Batch
        self._createTestBatch()
        batch = self.session.query(Batch).filter_by(batch_id='test batch').first()
        self.assertEqual(batch.batch_id, "test batch")
        self.assertEqual(batch.description, "test description")
        self.assertEqual(batch.date_data_received, "12.01.15")
    
        batch2 = self._createTestBatch()
        self.assertEqual(batch2[0], None)
   
    def test_batch_repr(self):
        batch = self._createTestBatch()
        expected = "<Batch batch_id='test batch' description='test description' date_data_received='12.01.15'>"    
        self.assertEqual(batch[0].__repr__(), expected)
    
    def test_batch_str(self):
        batch = self._createTestBatch()
        expected = "test batch"    
        self.assertEqual(batch[0].__str__(), expected)    
 
    def test_getBatch(self):
        batch = self._createTestBatch()
        from haemosphere.models.labsamples import getBatch
        result = getBatch(self.session, 'id', 1)
        self.assertEqual(result, batch[0])
        
        result = getBatch(self.session, 'id', 0)
        self.assertEqual(result, None)
        
    def test_editBatch(self):    
        batch = self._createTestBatch()
        from haemosphere.models.labsamples import editBatch
        editBatch(self.session, 1, "description", "new description2")
        self.assertEqual(batch[0].description, "new description2")
        self.assertNotEqual(batch[0].description, "new description")
        
        batch2 = self._createTestBatch(batch_id="test batch2")        
        self.assertRaises(ValueError, editBatch, self.session, 2, "batch_id", "test batch")

    def test_deleteBatch(self):
        batch = self._createTestBatch()
        from haemosphere.models.labsamples import deleteBatch
        from haemosphere.models.labsamples import Batch

        count = self.session.query(Batch).filter_by(batch_id=batch[0].batch_id).count()
        self.assertEqual(count, 1)
        
        deleteBatch(self.session, batch[0].id)
        count = self.session.query(Batch).filter_by(batch_id=batch[0].batch_id).count()
        self.assertEqual(count, 0)

    def test_getAllBatches(self):
        batch = self._createTestBatch()
        batch2 = self._createTestBatch(batch_id="test celltype2", description="new description2")        
        from haemosphere.models.labsamples import getAllBatches
        results = getAllBatches(self.session, "description", "new description2")
        self.assertEqual(len(results), 1)
        
        results = getAllBatches(self.session, "description", "newer description")
        self.assertEqual(len(results), 0)
        
        results = getAllBatches(self.session, "date_data_received", "12.01.15")
        self.assertEqual(len(results), 2)

    def test_getAllBatchData(self):
        batch = self._createTestBatch()
        batch2 = self._createTestBatch(batch_id="test batch2")
        from haemosphere.models.labsamples import getAllBatchData
        columns = ["id", "batch_id", "description", "date_data_received"]                
                
        results = getAllBatchData(self.session)
        self.assertEqual(results['columns'], columns)
        self.assertEqual(results['data'][0][1], batch[0].batch_id)
        self.assertEqual(results['data'][1][1], batch2[0].batch_id)

    def test_getBatchColumnNames(self):
        from haemosphere.models.labsamples import getBatchColumnNames
        expected = ["id", "batch_id", "description", "date_data_received"] 
        results = getBatchColumnNames()
        self.assertEqual(results, expected)

    ######################################################################
    #   Methods common to all db tables
    ######################################################################               
    def test_saveNewData(self):
        from haemosphere.models.labsamples import saveNewData
        from haemosphere.models.labsamples import Celltype, Batch, Sample
        
        celltypeData = self._newCelltypeData()
        batchData = self._newBatchData()
        sampleData = self._newSampleData()   

        # Normal data insert
        count = self.session.query(Celltype).count()
        self.assertEqual(count, 0)
        saveNewData(self.session, "celltypes", celltypeData)
        count = self.session.query(Celltype).count()
        self.assertEqual(count, 1)
        
        count = self.session.query(Batch).count()
        self.assertEqual(count, 0)
        saveNewData(self.session, "batches", batchData)
        count = self.session.query(Batch).count()
        self.assertEqual(count, 1)
        
        count = self.session.query(Sample).count()
        self.assertEqual(count, 0)
        saveNewData(self.session, "samples", sampleData)        
        count = self.session.query(Sample).count()
        self.assertEqual(count, 1)
        
        # Try to insert duplicate data
        result = saveNewData(self.session, "samples", sampleData)        
        self.assertEqual(result[0], None)
                    
        # Try to insert into non existant table            
        result = saveNewData(self.session, "sam", sampleData)        
        self.assertEqual(result[0], None)
        
    def test_deleteData(self):
        from haemosphere.models.labsamples import deleteData
        from haemosphere.models.labsamples import Celltype, Batch, Sample
        
        celltype = self._createTestCelltype()
        batch = self._createTestBatch()
        sample = self._createTestSample()

        deleteData(self.session, "celltypes", 1)
        count = self.session.query(Celltype).filter_by(celltype=celltype[0].celltype).count()
        self.assertEqual(count, 0)

        deleteData(self.session, "batches", 1)
        count = self.session.query(Batch).filter_by(batch_id=batch[0].batch_id).count()
        self.assertEqual(count, 0)

        deleteData(self.session, "samples", 1)
        count = self.session.query(Sample).filter_by(sample_id=sample[0].sample_id).count()
        self.assertEqual(count, 0)

    def test_instanceToList(self):
        from haemosphere.models.labsamples import instanceToList
        columns = ["id", "sample_id", "cell_num", "elution_date", "elution_volume", "rin", "rna", "rna_prep", "sort_date", 
                "total_rna", "amplified_rna_bio", "batch", "celltype", "description",
                "notes", "original_sample_id", "previous_sample_id", "genotype",
                "treatment", "group"]
        sample = self._createTestSample()
        expected = ["1", "test sample", "100", "12.01.15", "10", "20", "30", "prep", "13.01.15", 
                "100", "sample_bio", 'None', 'None', "test description", "test notes", 'None', 'None',
                "test geno", "test treatment", "test group"]      
        result = instanceToList(sample[0], columns)
        self.assertEqual(result, expected)
             
    def test_dataToLists(self):
        sample = self._createTestSample()
        from haemosphere.models.labsamples import dataToLists
        from haemosphere.models.labsamples import Sample
        data = self.session.query(Sample).all()
        columns = ["sample_id", "cell_num", "elution_date", "rin", "rna", "rna_prep", "sort_date", 
                "total_rna", "amplified_rna_bio", "batch", "celltype", "description",
                "notes", "original_sample_id", "previous_sample_id", "genotype",
                "treatment", "group"]
        results = dataToLists(data, columns)
        expected = [[sample[0].sample_id, sample[0].cell_num, sample[0].elution_date, sample[0].rin, 
                sample[0].rna, sample[0].rna_prep, sample[0].sort_date, 
                sample[0].total_rna, sample[0].amplified_rna_bio, '', '', 
                sample[0].description, sample[0].notes, '', '', 
                sample[0].genotype, sample[0].treatment, sample[0].group]]
        self.assertEqual(results, expected)
        
    def test_dfColToSqlCol(self):
        from haemosphere.models.labsamples import dfColToSqlCol
        columns = ['sampleId', 'Total RNA', 'originalSampleId', 'not a column']   
        newColumns = dfColToSqlCol(columns)
        self.assertEqual(newColumns, ['sample_id','total_rna','original_sample_id'])
        self.assertNotEqual(newColumns, columns)                    

    def test_checkSamplesRel(self):
        from haemosphere.models.labsamples import checkSamplesRel
        self._createTestRelationships()
        
        # There exists a relationship with sample
        result = checkSamplesRel(self.session, 'celltype_id', 1)
        self.assertTrue(result)
        
        # No relationship with sample
        result = checkSamplesRel(self.session, 'batch_id', 1)
        self.assertFalse(result)

      


