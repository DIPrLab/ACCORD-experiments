import unittest
from src.conflictDetctionAlgorithm import detectmain

class TestDetectMain(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(detectmain([], []), [])

if __name__ == "__main__":
    unittest.main()