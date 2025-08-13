import unittest
import sqlite3
import os
from app.db.cruds.misc import regions_crud
from app.db.cruds.misc import locations_crud as countries_crud
from app.db.init_schema import initialize_database # To set up in-memory DB

# Use a consistent in-memory database for tests
TEST_DB_PATH = ":memory:"

# Mock app_config for initialize_database
mock_app_config = {
    "database_path": TEST_DB_PATH,
    # Add other necessary config keys if initialize_database expects them
}

class TestRegionsCRUD(unittest.TestCase):
    conn = None

    @classmethod
    def setUpClass(cls):
        """Set up an in-memory SQLite database for all tests in this class."""
        # Initialize the schema
        initialize_database(mock_app_config)
        # Note: initialize_database now handles its own connection for schema setup.
        # We'll establish a new connection for test operations.
        cls.conn = sqlite3.connect(TEST_DB_PATH)
        cls.conn.row_factory = sqlite3.Row # Important for dict-like row access

        # Seed a country for testing regions
        # Assuming countries_crud.add_country returns the ID or a dict with 'country_id'
        country_data = countries_crud.add_country("Testlandia", conn=cls.conn)
        if isinstance(country_data, dict) and 'country_id' in country_data:
            cls.test_country_id = country_data['country_id']
        elif isinstance(country_data, int): # If add_country returns just the ID
             cls.test_country_id = country_data
        else:
            raise Exception("Failed to seed test country for regions CRUD tests.")

        # Ensure commit if add_country doesn't auto-commit (it should via _manage_conn)
        # cls.conn.commit() # Not needed if CRUD methods commit via decorator


    @classmethod
    def tearDownClass(cls):
        """Close the database connection after all tests."""
        if cls.conn:
            cls.conn.close()

    def setUp(self):
        """Ensure each test starts with a clean slate if necessary, or use setUpClass."""
        # For in-memory, schema is set up once. Data added per test might need cleanup
        # or be designed to be independent. For now, we rely on setUpClass for schema
        # and data added there.
        pass

    def tearDown(self):
        """Clean up after each test if data was added that needs removal."""
        # Example: If tests add regions that conflict, delete them here.
        # For now, assuming tests are either independent or cleanup is handled by recreating DB.
        # Since it's :memory:, it's fresh per setUpClass connection usually.
        # However, if using the same cls.conn, manual cleanup might be needed.
        # Let's assume _manage_conn handles commits/rollbacks properly within CRUD methods.
        pass

    def test_01_add_region(self):
        """Test adding a new region."""
        region_id = regions_crud.add_region("Central TestRegion", self.test_country_id, conn=self.conn)
        self.assertIsNotNone(region_id, "Should return an ID for the new region.")
        self.assertIsInstance(region_id, int)

        # Verify by fetching
        region = regions_crud.get_region_by_id(region_id, conn=self.conn)
        self.assertIsNotNone(region)
        self.assertEqual(region['region_name'], "Central TestRegion")
        self.assertEqual(region['country_id'], self.test_country_id)

    def test_02_get_region_by_id(self):
        """Test fetching a region by its ID."""
        # Add a region first to ensure it exists
        region_id = regions_crud.add_region("IDTest Region", self.test_country_id, conn=self.conn)
        self.assertIsNotNone(region_id)

        fetched_region = regions_crud.get_region_by_id(region_id, conn=self.conn)
        self.assertIsNotNone(fetched_region)
        self.assertEqual(fetched_region['region_id'], region_id)
        self.assertEqual(fetched_region['region_name'], "IDTest Region")

    def test_03_get_region_by_name_and_country_id(self):
        """Test fetching a region by name and country ID."""
        regions_crud.add_region("NameCountryTest Region", self.test_country_id, conn=self.conn)

        fetched_region = regions_crud.get_region_by_name_and_country_id("NameCountryTest Region", self.test_country_id, conn=self.conn)
        self.assertIsNotNone(fetched_region)
        self.assertEqual(fetched_region['region_name'], "NameCountryTest Region")

    def test_04_get_regions_for_country(self):
        """Test fetching all regions for a specific country."""
        # Add a couple of regions to the test country
        regions_crud.add_region("Region Alpha", self.test_country_id, conn=self.conn)
        regions_crud.add_region("Region Beta", self.test_country_id, conn=self.conn)

        regions = regions_crud.get_regions_for_country(self.test_country_id, conn=self.conn)
        self.assertIsInstance(regions, list)
        # Check if names are present, count might be higher due to other tests
        region_names = [r['region_name'] for r in regions]
        self.assertIn("Region Alpha", region_names)
        self.assertIn("Region Beta", region_names)
        self.assertTrue(len(regions) >= 2)


    def test_05_get_all_regions(self):
        """Test fetching all regions."""
        # Ensure at least a few regions exist from previous tests or add one more
        regions_crud.add_region("GlobalTest Region", self.test_country_id, conn=self.conn)
        all_regions = regions_crud.get_all_regions(conn=self.conn)
        self.assertIsInstance(all_regions, list)
        self.assertTrue(len(all_regions) > 0)

    def test_06_update_region(self):
        """Test updating a region's information."""
        region_id = regions_crud.add_region("UpdatableRegion", self.test_country_id, conn=self.conn)
        self.assertIsNotNone(region_id)

        update_data = {"region_name": "Updated RegionName"}
        updated = regions_crud.update_region(region_id, update_data, conn=self.conn)
        self.assertTrue(updated)

        fetched_region = regions_crud.get_region_by_id(region_id, conn=self.conn)
        self.assertEqual(fetched_region['region_name'], "Updated RegionName")

    def test_07_delete_region(self):
        """Test deleting a region."""
        region_id = regions_crud.add_region("DeletableRegion", self.test_country_id, conn=self.conn)
        self.assertIsNotNone(region_id)

        deleted = regions_crud.delete_region(region_id, conn=self.conn)
        self.assertTrue(deleted)

        fetched_region = regions_crud.get_region_by_id(region_id, conn=self.conn)
        self.assertIsNone(fetched_region)

    def test_08_get_or_add_region_existing(self):
        """Test get_or_add_region for an existing region."""
        regions_crud.add_region("ExistingRegionForGetOrAdd", self.test_country_id, conn=self.conn)

        region = regions_crud.get_or_add_region("ExistingRegionForGetOrAdd", self.test_country_id, conn=self.conn)
        self.assertIsNotNone(region)
        self.assertEqual(region['region_name'], "ExistingRegionForGetOrAdd")

    def test_09_get_or_add_region_new(self):
        """Test get_or_add_region for a new region."""
        region = regions_crud.get_or_add_region("NewRegionForGetOrAdd", self.test_country_id, conn=self.conn)
        self.assertIsNotNone(region)
        self.assertEqual(region['region_name'], "NewRegionForGetOrAdd")
        self.assertIn('region_id', region)

        # Verify it was actually added
        fetched_region = regions_crud.get_region_by_id(region['region_id'], conn=self.conn)
        self.assertIsNotNone(fetched_region)
        self.assertEqual(fetched_region['region_name'], "NewRegionForGetOrAdd")

    def test_10_add_duplicate_region_returns_existing_id(self):
        """Test that adding a duplicate region (name + country_id) returns the existing ID."""
        region_name = "DuplicateTestRegion"
        initial_id = regions_crud.add_region(region_name, self.test_country_id, conn=self.conn)
        self.assertIsNotNone(initial_id)

        # Try adding the same region again
        duplicate_add_id = regions_crud.add_region(region_name, self.test_country_id, conn=self.conn)
        self.assertIsNotNone(duplicate_add_id, "Adding a duplicate should not return None if it finds the existing.")
        self.assertEqual(initial_id, duplicate_add_id, "Adding a duplicate region should return the ID of the existing region.")


if __name__ == '__main__':
    unittest.main()
