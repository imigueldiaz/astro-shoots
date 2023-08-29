import unittest

from pyongc.ongc import Dso

from src.app.search.dsosearcher import DsoSearcher


class TestSearch(unittest.TestCase):
    def test_search_partial_name(self):
        # Test searching for a partial name that matches multiple Dso objects
        partial_name = "orion"
        expected_results = [Dso(name="IC0434").to_json(), Dso(name="NGC1976").to_json()]
        self.assertEqual(DsoSearcher.search(partial_name), expected_results)

    def test_search_no_match(self):
        # Test searching for a partial name that does not match any Dso objects
        partial_name = "tururu"
        expected_results = []
        self.assertEqual(DsoSearcher.search(partial_name), expected_results)

    def test_search_exact_match(self):
        # Test searching for a partial name that matches an exact Dso object
        partial_name = "NGC1976"
        expected_results = [Dso(name="NGC1976").to_json()]
        self.assertEqual(DsoSearcher.search(partial_name), expected_results)

    def test_count_objects_any(self):
        # Test counting the number of objects in the 'objects' table
        self.assertGreater(DsoSearcher.count_objects(), 0)

    def test_count_objects_no_dups_exact(self):
        # Test counting the number of objects in the 'objects' table excluding duplicates
        self.assertEqual(DsoSearcher.count_objects(), 13340)

    def test_count_objects_with_dups(self):
        # Test counting the number of objects in the 'objects' table including duplicates
        self.assertEqual(DsoSearcher.count_objects(omit_dupes=False), 13992)


if __name__ == "__main__":
    unittest.main()
