# Tests for user mocking for simulating more users with only a few real users
import yaml
import unittest
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
        cls.resources = []

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
        self.resources = mock_user.list_resources()
        self.assertEqual(len(self.resources), 2)

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


if __name__ == "__main__":
    unittest.main()