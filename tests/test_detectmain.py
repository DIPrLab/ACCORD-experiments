import unittest
import json
from src.conflictDetctionAlgorithm import detectmain

class TestDetectMain(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(detectmain([], []), [])

    def test_many_logs_one_conflict(self):
        logs = [['2024-04-22T15:58:34.153Z', 'Delete', '1pKjYSud0_oqWIcU30a_9LftSJ-4abJ2T5YJKvAtSzUs', 'Testing', '100482560272922900872', 'admin@accord.foundation'], ['2024-04-22T15:57:13.599Z', 'Permission Change-to:can_edit-from:none-for:drew@accord.foundation', '1pKjYSud0_oqWIcU30a_9LftSJ-4abJ2T5YJKvAtSzUs', 'Testing', '100482560272922900872', 'admin@accord.foundation'], ['2024-04-22T15:57:06.275Z', 'Edit', '1pKjYSud0_oqWIcU30a_9LftSJ-4abJ2T5YJKvAtSzUs', 'Testing', '112627686161565491345', 'drew@accord.foundation'], ['2024-04-22T15:56:16.221Z', 'Permission Change-to:none-from:can_edit-for:drew@accord.foundation', '1pKjYSud0_oqWIcU30a_9LftSJ-4abJ2T5YJKvAtSzUs', 'Testing', '105806898968975168992', 'bob@accord.foundation'], ['2024-04-22T15:55:27.265Z', 'Permission Change-to:can_edit-from:none-for:bob@accord.foundation', '1pKjYSud0_oqWIcU30a_9LftSJ-4abJ2T5YJKvAtSzUs', 'Testing', '100482560272922900872', 'admin@accord.foundation'], ['2024-04-22T15:54:50.902Z', 'Edit', '1pKjYSud0_oqWIcU30a_9LftSJ-4abJ2T5YJKvAtSzUs', 'Testing', '112627686161565491345', 'drew@accord.foundation'], ['2024-04-22T15:54:04.778Z', 'Edit', '1pKjYSud0_oqWIcU30a_9LftSJ-4abJ2T5YJKvAtSzUs', 'Testing', '112627686161565491345', 'drew@accord.foundation'], ['2024-04-22T15:53:21.519Z', 'Permission Change-to:can_edit-from:none-for:drew@accord.foundation', '1pKjYSud0_oqWIcU30a_9LftSJ-4abJ2T5YJKvAtSzUs', 'Testing', '100482560272922900872', 'admin@accord.foundation'], ['2024-04-22T15:51:03.734Z', 'Rename', '1pKjYSud0_oqWIcU30a_9LftSJ-4abJ2T5YJKvAtSzUs', 'Testing', '100482560272922900872', 'admin@accord.foundation']]
        constraints = {'1pKjYSud0_oqWIcU30a_9LftSJ-4abJ2T5YJKvAtSzUs': [['Testing', '1pKjYSud0_oqWIcU30a_9LftSJ-4abJ2T5YJKvAtSzUs', 'Edit', 'Can Edit', 'drew@accord.foundation', 'FALSE', '', 'admin@accord.foundation', ''], ['Testing', '1pKjYSud0_oqWIcU30a_9LftSJ-4abJ2T5YJKvAtSzUs', 'Permission Change', 'Remove Permission', 'bob@accord.foundation', 'FALSE', 'not in', 'admin@accord.foundation', '']],}
        self.assertEqual(detectmain(logs, constraints), [False, False, False, True, False, False, False, False, False])

    def test_one_log_no_conflict(self):
        constraints = {'Doc_ID': [['Doc_Name', 'Doc_ID', 'Action', 'Action Type', 'Constraint Target', 'Action Value', 'Comparator', 'Constraint Owner', 'Allowed Values']], '1MSzbQFwHdC6vZdV5jyeHIfqJZZLIghFhCwHSj87w9jc': [['Revisions', '1MSzbQFwHdC6vZdV5jyeHIfqJZZLIghFhCwHSj87w9jc', 'Permission Change', 'Add Permission', 'abt@abhiroop.shop', 'FALSE', 'not in', 'abhi09@abhiroop.shop', '']]}
        logs = [['2024-07-24T17:38:17.755Z', 'Permission Change-to:can_viewcan_comment-from:can_edit-for:bob@accord.foundation', '1qiUmGMg5ueyv_MnfcacVktQdx_6xjCeD8b0dH1OAydo', 'doc1', '114128337804353370964', 'alice@accord.foundation']]
        self.assertEqual(detectmain(logs, constraints), [False])

    def test_comparators(self):
        # not in
        constraints = {'Doc_ID': [['Doc_Name', 'Doc_ID', 'Action', 'Action Type', 'Constraint Target', 'Action Value', 'Comparator', 'Constraint Owner', 'Allowed Values']], '1qiUmGMg5ueyv_MnfcacVktQdx_6xjCeD8b0dH1OAydo': [['doc1', '1qiUmGMg5ueyv_MnfcacVktQdx_6xjCeD8b0dH1OAydo', 'Permission Change', 'Update Permission', 'alice@accord.foundation', '', 'not in', 'abhi09@abhiroop.shop', '']]}
        logs = [['2024-07-24T17:38:17.755Z', 'Permission Change-to:can_viewcan_comment-from:can_edit-for:bob@accord.foundation', '1qiUmGMg5ueyv_MnfcacVktQdx_6xjCeD8b0dH1OAydo', 'doc1', '114128337804353370964', 'alice@accord.foundation']]
        self.assertEqual(detectmain(logs, constraints), [True])
        # in
        constraints = {'Doc_ID': [['Doc_Name', 'Doc_ID', 'Action', 'Action Type', 'Constraint Target', 'Action Value', 'Comparator', 'Constraint Owner', 'Allowed Values']], '1qiUmGMg5ueyv_MnfcacVktQdx_6xjCeD8b0dH1OAydo': [['doc1', '1qiUmGMg5ueyv_MnfcacVktQdx_6xjCeD8b0dH1OAydo', 'Permission Change', 'Update Permission', 'alice@accord.foundation', '', 'in', 'abhi09@abhiroop.shop', 'bob@accord.foundation,carol@accord.foundation']]}
        logs = [['2024-07-24T17:38:17.755Z', 'Permission Change-to:can_viewcan_comment-from:can_edit-for:bob@accord.foundation', '1qiUmGMg5ueyv_MnfcacVktQdx_6xjCeD8b0dH1OAydo', 'doc1', '114128337804353370964', 'alice@accord.foundation']]
        self.assertEqual(detectmain(logs, constraints), [True])
        # no comparator
        logs = [['2024-04-22T15:58:34.153Z', 'Delete', '1pKjYSud0_oqWIcU30a_9LftSJ-4abJ2T5YJKvAtSzUs', 'Testing', '100482560272922900872', 'admin@accord.foundation']]
        constraints = {'1pKjYSud0_oqWIcU30a_9LftSJ-4abJ2T5YJKvAtSzUs': [['Testing', '1pKjYSud0_oqWIcU30a_9LftSJ-4abJ2T5YJKvAtSzUs', 'Delete', 'Can Delete', 'admin@accord.foundation', 'FALSE', '', 'drew@accord.foundation', '']]}
        self.assertEqual(detectmain(logs, constraints), [True])
        # gt
        logs = [['2024-04-22T15:57:06.275Z', 'Edit', '1pKjYSud0_oqWIcU30a_9LftSJ-4abJ2T5YJKvAtSzUs', 'Testing', '112627686161565491345', 'drew@accord.foundation']]
        constraints = {'1pKjYSud0_oqWIcU30a_9LftSJ-4abJ2T5YJKvAtSzUs': [['Testing', '1pKjYSud0_oqWIcU30a_9LftSJ-4abJ2T5YJKvAtSzUs', 'Edit', 'Time Limit Edit', 'drew@accord.foundation', 'FALSE', 'gt', 'admin@accord.foundation', '2024-04-22T15:57:06.000Z']]}
        self.assertEqual(detectmain(logs, constraints), [True])
        # lt
        logs = [['2024-04-22T15:57:06.275Z', 'Edit', '1pKjYSud0_oqWIcU30a_9LftSJ-4abJ2T5YJKvAtSzUs', 'Testing', '112627686161565491345', 'drew@accord.foundation']]
        constraints = {'1pKjYSud0_oqWIcU30a_9LftSJ-4abJ2T5YJKvAtSzUs': [['Testing', '1pKjYSud0_oqWIcU30a_9LftSJ-4abJ2T5YJKvAtSzUs', 'Edit', 'Time Limit Edit', 'drew@accord.foundation', 'FALSE', 'lt', 'admin@accord.foundation', '2024-04-22T15:57:06.000Z']]}
        self.assertEqual(detectmain(logs, constraints), [False])

    def test_many_logs_many_conflicts(self):
        with open("tests/sample_constraints.txt") as file:
            constraints = json.load(file)
        with open("tests/sample_logs.txt") as file:
            logs = json.load(file)
        self.assertEqual(sum(detectmain(logs, constraints)), 33)

if __name__ == "__main__":
    unittest.main()