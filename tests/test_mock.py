# Tests for user mocking for simulating more users with only a few real users
import yaml, unittest, time
from datetime import datetime, timezone

from scripts.google_api_util import UserSubject, MIMETYPE_FILE, MIMETYPE_FOLDER, Resource
from scripts.mock import MockUser, MockDrive

def initialize():
    '''Create 2 real users (Alice, Bob) with 2 mock users (Name.{0,1}) each'''
    sim = {}
    with open('scripts/.user_info', 'r') as file:
        user_info = yaml.safe_load(file)
    sim['real'] = list(map(lambda u: UserSubject(u['name'], u['email'], u['token'],), user_info['users'][0:2]))
    for u in sim['real']:
        u.delete_all_resources()
    sim['mock_drive'] = MockDrive(set(sim['real']))
    sim['mock'] = []
    for user in sim['real']:
        user.delete_all_resources()
        for i in range(2):
            name = user.name + '.' + str(i)
            sim['mock'].append(MockUser(name, str(i), user, sim['mock_drive']))
    sim['next_file'] = 0 # used for filenames
    return sim

def create_folder_with_file(sim, mock_user):
        '''Helper function to create a folder with a child file for mock_user'''
        name = "folder" + str(sim['next_file'])
        sim['next_file'] += 1
        res = mock_user.create_resource(MIMETYPE_FOLDER, name)
        mock_user.user.set_drive(res["parents"][0])
        resources = mock_user.list_resources()
        name = "file" + str(sim['next_file'])
        sim['next_file'] += 1
        potential_parents = mock_user.list_potential_parents(None, resources)
        res = mock_user.create_resource(MIMETYPE_FILE, name, potential_parents[0])

def assert_record_exists(tc: unittest.TestCase, resid: str, mock_user):
    tc.assertIn(resid, tc.sim['mock_drive'].resource_records)
    tc.assertIn(mock_user.user.id, tc.sim['mock_drive'].resource_records[resid])
    records = tc.sim['mock_drive'].resource_records[resid][mock_user.user.id]
    tc.assertEqual(len(records), 1)
    tc.assertEqual(records[0].mock_user, mock_user)
    tc.assertGreaterEqual(datetime.now(timezone.utc), records[0].start_time)

class TestA_Initialization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sim = initialize()

    def testA0__mock_drive_initialized(self):
        self.assertIn("0", self.sim['mock_drive'].mocks_by_id)
        self.assertDictEqual({ m.id: m for m in self.sim['mock']}, self.sim['mock_drive'].mocks_by_id)
        self.assertDictEqual({ self.sim['real'][0]: [self.sim['mock'][0], self.sim['mock'][1]],
                               self.sim['real'][1]: [self.sim['mock'][2], self.sim['mock'][3]] },
                             self.sim['mock_drive'].mocks_by_user)

class TestB_Create(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sim = initialize()

    def testB0_create_file(self):
        mock_user = self.sim['mock'][0]
        name = "file" + str(self.sim['next_file'])
        self.sim['next_file'] += 1
        res = mock_user.create_resource(MIMETYPE_FILE, name)
        self.assertEqual(len(mock_user.list_resources()), 1)
        self.assertIn(res['id'], self.sim['mock_drive'].resource_records)
        self.assertIn(mock_user.user.id, self.sim['mock_drive'].resource_records[res['id']])
        records = self.sim['mock_drive'].resource_records[res['id']][mock_user.user.id]
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].mock_user, mock_user)
        self.assertGreaterEqual(datetime.now(timezone.utc), records[0].start_time)
        self.assertIsNone(records[0].end_time)

    def testB1_create_folder(self):
        mock_user = self.sim['mock'][0]
        name = "folder" + str(self.sim['next_file'])
        self.sim['next_file'] += 1
        res = mock_user.create_resource(MIMETYPE_FOLDER, name)
        mock_user.user.set_drive(res["parents"][0])
        resources = mock_user.list_resources()
        self.assertEqual(len(resources), 2)

    def testB2_potential_parents(self):
        mock_user = self.sim['mock'][0]
        resources = mock_user.list_resources()
        potential_parents = mock_user.list_potential_parents(None, resources)
        self.assertEqual(len(potential_parents), 2)

    def testB3_create_file_in_folder(self):
        mock_user = self.sim['mock'][0]
        name = "file" + str(self.sim['next_file'])
        self.sim['next_file'] += 1
        resources = mock_user.list_resources()
        potential_parents = mock_user.list_potential_parents(None, resources)
        self.assertEqual(len(potential_parents), 2)
        res = mock_user.create_resource(MIMETYPE_FILE, name, potential_parents[0])
        self.assertEqual(res["parents"][0], potential_parents[0].id)

    def testB4_create_folder_in_folder(self):
        mock_user = self.sim['mock'][0]
        name = "folder" + str(self.sim['next_file'])
        self.sim['next_file'] += 1
        resources = mock_user.list_resources()
        self.assertEqual(len(resources), 3)
        potential_parents = mock_user.list_potential_parents(None, resources)
        self.assertEqual(len(potential_parents), 2)
        res = mock_user.create_resource(MIMETYPE_FOLDER, name, potential_parents[0])
        self.assertEqual(res["parents"][0], potential_parents[0].id)
        resources = mock_user.list_resources()
        self.assertEqual(len(resources), 4)
        self.assertEqual(len(mock_user.list_potential_parents(None, resources)), 3)

    def testB5_diff_mocks_same_user(self):
        mock_user = self.sim['mock'][1]
        self.assertEqual(len(mock_user.list_resources()), 0)
        name = "file" + str(self.sim['next_file'])
        self.sim['next_file'] += 1
        res = mock_user.create_resource(MIMETYPE_FILE, name)
        self.assertEqual(len(mock_user.list_resources()), 1)

    def testB6_diff_mocks_diff_users(self):
        mock_user = self.sim['mock'][2]
        self.assertEqual(len(mock_user.list_resources()), 0)
        name = "file" + str(self.sim['next_file'])
        self.sim['next_file'] += 1
        res = mock_user.create_resource(MIMETYPE_FILE, name)
        mock_user.user.set_drive(res["parents"][0])
        self.assertEqual(len(mock_user.list_resources()), 1)


class TestC_Delete(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sim = initialize()

    def testC0_delete_file(self):
        mock_user = self.sim['mock'][2]
        name = "file" + str(self.sim['next_file'])
        self.sim['next_file'] += 1
        res0 = mock_user.create_resource(MIMETYPE_FILE, name)
        timestamp = datetime.now(timezone.utc)

        resources = mock_user.list_resources()
        mock_user.delete_resource(resources[0])
        resources = mock_user.list_resources()
        self.assertEqual(len(resources), 0)

        self.assertIn(res0['id'], self.sim['mock_drive'].resource_records)
        self.assertIn(mock_user.user.id, self.sim['mock_drive'].resource_records[res0['id']])
        records = self.sim['mock_drive'].resource_records[res0['id']][mock_user.user.id]
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].mock_user, mock_user)
        self.assertGreaterEqual(timestamp, records[0].start_time)
        self.assertGreaterEqual(records[0].end_time, timestamp)

    def testC1_delete_folder(self):
        mock_user = self.sim['mock'][2]
        name = "folder" + str(self.sim['next_file'])
        self.sim['next_file'] += 1
        res = mock_user.create_resource(MIMETYPE_FOLDER, name)
        resources = mock_user.list_resources()
        self.assertEqual(len(resources), 1)
        timestamp = datetime.now(timezone.utc)

        mock_user.delete_resource(resources[0])
        resources = mock_user.list_resources()
        self.assertEqual(len(resources), 0)

        self.assertIn(res['id'], self.sim['mock_drive'].resource_records)
        self.assertIn(mock_user.user.id, self.sim['mock_drive'].resource_records[res['id']])
        records = self.sim['mock_drive'].resource_records[res['id']][mock_user.user.id]
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].mock_user, mock_user)
        self.assertGreaterEqual(timestamp, records[0].start_time)
        self.assertGreaterEqual(records[0].end_time, timestamp)

    def testC2_delete_folder_with_contents(self):
        mock_user = self.sim['mock'][3]
        name = "folder" + str(self.sim['next_file'])
        self.sim['next_file'] += 1
        res = mock_user.create_resource(MIMETYPE_FOLDER, name)
        mock_user.user.set_drive(res["parents"][0])
        resources = mock_user.list_resources()
        potential_parents = mock_user.list_potential_parents(None, resources)
        res = mock_user.create_resource(MIMETYPE_FILE, name, potential_parents[0])
        resources = mock_user.list_resources()
        folder = None
        for r in resources:
            if r.mime_type == MIMETYPE_FOLDER:
                folder = r
                break
        mock_user.delete_resource(folder)
        time.sleep(1) # Takes some time for Google to resolve recursive deletion
        resources = mock_user.list_resources()
        self.assertEqual(len(resources), 0)

class TestD_Permission_Change(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sim = initialize()

    def testD0_addable_users_simple(self):
        mock_user = self.sim['mock'][0]
        name = "file" + str(self.sim['next_file'])
        self.sim['next_file'] += 1
        res = mock_user.create_resource(MIMETYPE_FILE, name)
        resources = mock_user.list_resources()
        children = mock_user.get_children(resources[0], resources)
        self.assertEqual(children, resources)
        addable_users = mock_user.get_addable_users(children)
        self.assertEqual(len(addable_users), len(self.sim['mock']) - 2)
        for mu in self.sim['mock'][2:]:
            self.assertIn(mu, addable_users)
        self.assertNotIn(mock_user, addable_users)
        self.assertNotIn(self.sim['mock'][1], addable_users)

    def testD1_add_permission(self):
        mock_user = self.sim['mock'][0]
        resources = mock_user.list_resources()
        children = mock_user.get_children(resources[0], resources)
        self.assertEqual(children, resources)
        addable_users = mock_user.get_addable_users(children)
        new_user = addable_users[0]
        mock_user.add_permission(resources[0], children, new_user, 'writer')
        assert_record_exists(self, resources[0].id, new_user)
        new_user_resources = new_user.list_resources()
        time.sleep(1)
        self.assertEqual(len(new_user_resources), 1)

    def testD2_addable_users_children(self):
        mock_user = self.sim['mock'][3]
        create_folder_with_file(self.sim, mock_user)
        resources = mock_user.list_resources()
        if resources[0].mime_type == MIMETYPE_FILE:
            file = resources[0]
            folder = resources[1]
        else:
            file = resources[1]
            folder = resources[0]
        file_children = mock_user.get_children(file, resources)
        mock_user.add_permission(file, file_children, self.sim['mock'][1], 'commenter')
        time.sleep(1)
        resources = mock_user.list_resources()
        folder_children = mock_user.get_children(folder, resources)
        self.assertEqual(len(folder_children), 2)
        folder_addable_users = mock_user.get_addable_users(folder_children)
        self.assertEqual(len(folder_addable_users), 1)
        self.assertIs(folder_addable_users[0], self.sim['mock'][1])


if __name__ == "__main__":
    unittest.main()