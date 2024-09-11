# Tests for user mocking for simulating more users with only a few real users
import yaml, unittest, time
from datetime import datetime, timezone
from csv import DictReader

from scripts.google_api_util import UserSubject, MIMETYPE_FILE, MIMETYPE_FOLDER
from scripts.mock import MockUser, MockDrive
from src.serviceAPI import create_reportsAPI_service

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
    for j, user in enumerate(sim['real']):
        user.delete_all_resources()
        for i in range(2):
            name = user.name + '.' + str(i)
            sim['mock'].append(MockUser(name, str(i + j * 2), user, sim['mock_drive']))
    sim['next_file'] = 0 # used for filenames
    return sim

def initialize_larger():
    '''Create 3 read users (Alice, Bob, Carol), with 2 mock users (Name.{0,1}) each'''
    sim = {}
    with open('scripts/.user_info', 'r') as file:
        user_info = yaml.safe_load(file)
    sim['real'] = list(map(lambda u: UserSubject(u['name'], u['email'], u['token'],), user_info['users'][0:3]))
    for u in sim['real']:
        u.delete_all_resources()
    sim['mock_drive'] = MockDrive(set(sim['real']))
    sim['mock'] = []
    for j, user in enumerate(sim['real']):
        user.delete_all_resources()
        for i in range(2):
            name = user.name + '.' + str(i)
            sim['mock'].append(MockUser(name, str(i + j * 2), user, sim['mock_drive']))
    sim['next_file'] = 0 # used for filenames
    return sim

def initialize_reports(sim):
    '''Initialize Reports API'''
    with open('scripts/.user_info', 'r') as file:
        user_info = yaml.safe_load(file)
    sim['reports'] = create_reportsAPI_service(user_info['admin']['token'])

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

def assert_record_open(tc: unittest.TestCase, resid: str, mock_user: MockUser):
    '''Assert that there is an open access record for a mock user'''
    tc.assertIn(resid, tc.sim['mock_drive'].resource_records)
    tc.assertIn(mock_user.user.id, tc.sim['mock_drive'].resource_records[resid])
    records = tc.sim['mock_drive'].resource_records[resid][mock_user.user.id]
    t = datetime.now(timezone.utc)
    record_found = False
    for rec in records:
        if rec.mock_user is mock_user:
            if rec.start_time <= t and not rec.end_time:
                record_found = True
    tc.assertTrue(record_found)

def assert_record_closed(tc: unittest.TestCase, resid: str, mock_user: MockUser):
    '''Assert that all access records for a mock user are closed'''
    tc.assertIn(resid, tc.sim['mock_drive'].resource_records)
    tc.assertIn(mock_user.user.id, tc.sim['mock_drive'].resource_records[resid])
    records = tc.sim['mock_drive'].resource_records[resid][mock_user.user.id]
    record_open = False
    for rec in records:
        if rec.mock_user is mock_user:
            record_open |= rec.end_time is not None
    tc.assertFalse(record_open)


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
    '''Test Add, Update, Remove Permission, as well as get_addable_users()

    Must run entire suite, as cases build on one anther
    '''
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
        assert_record_open(self, resources[0].id, new_user)
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
        mock_user.add_permission(folder, folder_children, folder_addable_users[0], 'reader')
        self.assertEqual(len(self.sim['mock_drive'].resource_records[file.id]), 2)
        records = self.sim['mock_drive'].resource_records[file.id][folder_addable_users[0].user.id]
        self.assertEqual(len(records), 2)

    def testD3_update_permission_indirect(self):
        mock_user = self.sim['mock'][3]
        target = self.sim['mock'][1]
        resources = mock_user.list_resources()
        if resources[0].mime_type == MIMETYPE_FILE:
            folder = resources[1]
        else:
            folder = resources[0]
        folder_children = mock_user.get_children(folder, resources)
        mock_user.update_permission(folder, folder_children, target, 'writer')
        time.sleep(1)

        resources = mock_user.list_resources()
        if resources[0].mime_type == MIMETYPE_FILE:
            folder = resources[1]
            file = resources[0]
        else:
            folder = resources[0]
            file = resources[1]

        permission_found = False
        for userid, role in folder.permissions.items():
            if userid == target.user.id:
                self.assertEqual(role, 'writer')
                permission_found = True
        self.assertTrue(permission_found)
        permission_found = False
        for userid, role in file.permissions.items():
            if userid == target.user.id:
                self.assertEqual(role, 'writer')

    def testD4_update_permission_direct(self):
        mock_user = self.sim['mock'][3]
        target = self.sim['mock'][1]
        resources = mock_user.list_resources()
        if resources[0].mime_type == MIMETYPE_FILE:
            file = resources[0]
        else:
            file = resources[1]
        file_children = mock_user.get_children(file, resources)
        mock_user.update_permission(file, file_children, target, 'reader')

        resources = mock_user.list_resources()
        if resources[0].mime_type == MIMETYPE_FILE:
            folder = resources[1]
            file = resources[0]
        else:
            folder = resources[0]
            file = resources[1]

        permission_found = False
        for userid, role in folder.permissions.items():
            if userid == target.user.id:
                self.assertEqual(role, 'writer')
                permission_found = True
        self.assertTrue(permission_found)
        permission_found = False
        for userid, role in file.permissions.items():
            if userid == target.user.id:
                self.assertEqual(role, 'reader')
                permission_found = True
        self.assertTrue(permission_found)

    def testD5_remove_permission_direct(self):
        mock_user = self.sim['mock'][3]
        target = self.sim['mock'][1]
        resources = mock_user.list_resources()
        if resources[0].mime_type == MIMETYPE_FILE:
            file = resources[0]
        else:
            file = resources[1]
        time = datetime.now(timezone.utc)
        file_children = mock_user.get_children(file, resources)
        mock_user.remove_permission(file, file_children, target)

        # Assert all records closed, regardless of whether indirect or direct
        records = self.sim['mock_drive'].resource_records[file.id][target.user.id]
        for rec in records:
            self.assertEqual(rec.mock_user, target)
            self.assertGreaterEqual(time, rec.start_time)
            self.assertGreaterEqual(rec.end_time, time)

    def testD6_remove_permission_indirect(self):
        mock_user = self.sim['mock'][3]
        target = self.sim['mock'][0]
        resources = mock_user.list_resources()
        if resources[0].mime_type == MIMETYPE_FILE:
            file = resources[0]
            folder = resources[1]
        else:
            file = resources[1]
            folder = resources[0]
        mock_user.add_permission(file, [file], target, 'writer')
        folder_children = mock_user.get_children(folder, resources)
        mock_user.remove_permission(folder, folder_children, self.sim['mock'][1])
        mock_user.add_permission(folder, folder_children, target, 'reader')
        time.sleep(1)
        resources = mock_user.list_resources()
        folder_children = mock_user.get_children(folder, resources)
        timestamp = datetime.now(timezone.utc)
        mock_user.remove_permission(folder, folder_children, target)

        # Assert that there is still an open record on file
        open_found = False
        records = self.sim['mock_drive'].resource_records[file.id][target.user.id]
        for rec in records:
            if not open_found and not rec.end_time:
                open_found = True
            elif open_found and not rec.end_time:
                self.assertFalse(open_found) # Basically, fail the test
        self.assertTrue(open_found)

        # Assert that there is still a direct permission on file
        resources = mock_user.list_resources()
        if resources[0].mime_type == MIMETYPE_FILE:
            file = resources[0]
        else:
            file = resources[1]
        for userid, role in file.permissions.items():
            if userid == target.user.id:
                self.assertEqual(role, 'writer')

        # Assert that all direct permissions on folder were removed
        records = self.sim['mock_drive'].resource_records[folder.id][target.user.id]
        for rec in records:
            if rec.mock_user is target:
                self.assertGreaterEqual(timestamp, rec.start_time)
                self.assertGreaterEqual(rec.end_time, timestamp)

    def testD7_update_permission_after_remove(self):
        mock_user = self.sim['mock'][3]
        target = self.sim['mock'][0]
        resources = mock_user.list_resources()
        if resources[0].mime_type == MIMETYPE_FILE:
            file = resources[0]
            folder = resources[1]
        else:
            file = resources[1]
            folder = resources[0]

        file_children = mock_user.get_children(file, resources)
        folder_children = mock_user.get_children(folder, resources)
        mock_user.remove_permission(file, file_children, target)
        mock_user.add_permission(folder, folder_children, target, 'writer')
        time.sleep(1)
        mock_user.remove_permission(file, file_children, target)
        mock_user.update_permission(folder, folder_children, target, 'reader')
        time.sleep(1)

        assert_record_open(self, file.id, target)

class TestE_Move(unittest.TestCase):
    '''Test cases for move & resulting permission changes.

    Must run whole test suite together.
    '''
    @classmethod
    def setUpClass(cls):
        cls.sim = initialize_larger()

    def testE0_move_to_root(self):
        mock_user = self.sim['mock'][0]
        create_folder_with_file(self.sim, mock_user)
        resources = mock_user.list_resources()
        if resources[0].mime_type == MIMETYPE_FILE:
            file = resources[0]
            folder = resources[1]
        else:
            file = resources[1]
            folder = resources[0]
        file_children = [file]
        potential_parents = mock_user.list_potential_parents(file, resources)
        self.assertEqual(len(potential_parents), 1)
        mock_user.move(file, file_children, folder, potential_parents[0])
        time.sleep(1)

        resources = mock_user.list_resources()
        if resources[0].mime_type == MIMETYPE_FILE:
            file = resources[0]
        else:
            file = resources[1]
        self.assertEqual(file.parents, potential_parents[0].id)
        potential_parents = mock_user.list_potential_parents(file, resources)
        self.assertEqual(len(potential_parents), 1)
        self.assertEqual(potential_parents[0].id, folder.id)

    def testE1_move_to_folder(self):
        mock_user = self.sim['mock'][0]
        resources = mock_user.list_resources()
        if resources[0].mime_type == MIMETYPE_FILE:
            file = resources[0]
            folder = resources[1]
        else:
            file = resources[1]
            folder = resources[0]
        file_children = [file]
        potential_parents = mock_user.list_potential_parents(file, resources)
        self.assertEqual(len(potential_parents), 1)
        mock_user.move(file, file_children, folder, potential_parents[0])
        time.sleep(1)

        resources = mock_user.list_resources()
        if resources[0].mime_type == MIMETYPE_FILE:
            file = resources[0]
        else:
            file = resources[1]
        self.assertEqual(file.parents, potential_parents[0].id)
        potential_parents = mock_user.list_potential_parents(file, resources)
        self.assertEqual(len(potential_parents), 1)
        self.assertEqual(potential_parents[0].id, mock_user.user.driveid)

    def testE2_between_folders_permission_change(self):
        mock_user = self.sim['mock'][0]
        target1 = self.sim['mock'][2]
        target2 = self.sim['mock'][4]
        folder1 = None
        folder2 = None
        file = None
        resources = mock_user.list_resources()
        for res in resources:
            if res.mime_type == MIMETYPE_FOLDER:
                folder1 = res
            else:
                file = res
        name = "folder" + str(self.sim['next_file'])
        self.sim['next_file'] += 1
        res = mock_user.create_resource(MIMETYPE_FOLDER, name)
        resources = mock_user.list_resources()
        for res in resources:
            if res.mime_type == MIMETYPE_FOLDER and res.id != folder1.id:
                folder2 = res

        folder1_children = mock_user.get_children(folder1, resources)
        folder2_children = mock_user.get_children(folder2, resources)
        mock_user.add_permission(folder1, folder1_children, target1, 'writer')
        mock_user.add_permission(folder2, folder2_children, target2, 'writer')
        time.sleep(1)
        assert_record_open(self, folder1.id, target1)
        assert_record_open(self, folder2.id, target2)
        assert_record_open(self, file.id, target1)

        resources = mock_user.list_resources()
        for res in resources:
            if res.mime_type == MIMETYPE_FOLDER:
                if res.id == folder1.id:
                    folder1 = res
                else:
                    folder2 = res
            else:
                file = res
        file_children = [file]
        potential_parents = mock_user.list_potential_parents(file, resources)
        self.assertEqual(len(potential_parents), 2)
        mock_user.move(file, file_children, folder1, folder2)
        time.sleep(1)
        assert_record_closed(self, file.id, target1)
        assert_record_open(self, file.id, target2)
        assert_record_open(self, folder1.id, target1)
        assert_record_open(self, folder2.id, target2)

        resources = mock_user.list_resources()
        for res in resources:
            if res.mime_type == MIMETYPE_FILE:
                self.assertEqual(res.parents, folder2.id)

class TestF_Fetch_Logs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sim = initialize_larger()
        initialize_reports(cls.sim)

    def testF0_all_actions(self):
        '''Can be flaky--last actions may not be in logs if extracted too soon'''
        alice0 = self.sim['mock'][0]
        alice1 = self.sim['mock'][1]
        bob0 = self.sim['mock'][2]
        carol0 = self.sim['mock'][4]
        t = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Create
        create_folder_with_file(self.sim, alice0)
        a0_resources = alice0.list_resources()
        a0_folder = None
        a0_file = None
        for r in a0_resources:
            if r.mime_type == MIMETYPE_FILE:
                a0_file = r
                print(a0_file.id)
            else:
                a0_folder = r
        create_folder_with_file(self.sim, alice1)
        a1_resources = alice1.list_resources()
        a1_folder = None
        a1_file = None
        for r in a1_resources:
            if r.mime_type == MIMETYPE_FILE:
                a1_file = r
            else:
                a1_folder = r

        # Edit
        alice0.edit(a0_file)

        # Permission
        alice1.add_permission(a1_folder, [a1_file, a1_folder], bob0, 'writer')
        alice1.update_permission(a1_folder, [a1_file, a1_folder], bob0, 'owner')
        time.sleep(1)
        bob0.add_permission(a1_file, [a1_file], carol0, 'reader')
        time.sleep(1)
        alice1.remove_permission(a1_file, [a1_file], carol0)
        bob0.update_permission(a1_folder, [a1_file, a1_folder], alice1, 'commenter')

        # Test potential_parents()
        alice0.add_permission(a0_folder, [a0_folder, a0_file], bob0, 'writer')
        time.sleep(2)
        b0_resources = bob0.list_resources()
        a0_file_b0 = None
        for res in b0_resources:
            if res.id == a0_file.id:
                a0_file_b0 = res
        potential_parents = bob0.list_potential_parents(a0_file_b0, b0_resources)
        self.assertEqual(len(potential_parents), 0)

        # Move
        name = "folder" + str(self.sim['next_file'])
        self.sim['next_file'] += 1
        res = bob0.create_resource(MIMETYPE_FOLDER, name)
        b0_resources = bob0.list_resources()
        b0_folder = None
        for res in b0_resources:
            if res.id == a1_file.id:
                a1_file = res
            elif res.id == a1_folder.id:
                a1_folder = res
            elif res.id != a0_file.id and res.id != a0_folder.id:
                b0_folder = res
        bob0.move(a1_file, [a1_file], a1_folder, b0_folder)

        # Delete
        bob0.delete_resource(b0_folder)
        print("\n")
        for i in range(12):
            time.sleep(5)
            print("Logs ready in...", 60 - i * 5)

        logs = self.sim['mock_drive'].fetch_logs(t, self.sim['reports'])
        print(logs) # Check manually
        print("\n*** Check logs above manually ***")


if __name__ == "__main__":
    unittest.main()
