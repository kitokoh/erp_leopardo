import unittest
import sqlite3
import os
import uuid
from db.cruds import referents_crud, clients_crud, countries_crud, regions_crud, users_crud, status_settings_crud
from db.init_schema import initialize_database

TEST_DB_PATH = ":memory:"

mock_app_config = {
    "database_path": TEST_DB_PATH,
}

class TestReferentsCRUD(unittest.TestCase):
    conn = None
    test_country_id = None
    test_region_id = None
    test_city_id = None # Assuming cities are also seeded or handled by client/country setup
    test_user_id = None
    sample_client_id1 = None
    sample_client_id2 = None

    @classmethod
    def setUpClass(cls):
        initialize_database(mock_app_config)
        cls.conn = sqlite3.connect(TEST_DB_PATH)
        cls.conn.row_factory = sqlite3.Row

        # Seed common data needed for referents
        country_data = countries_crud.add_country("Referentia", conn=cls.conn)
        cls.test_country_id = country_data['country_id'] if isinstance(country_data, dict) else country_data

        region_data = regions_crud.add_region("Central Referentia", cls.test_country_id, conn=cls.conn)
        cls.test_region_id = region_data # Assuming add_region returns ID directly

        # Seed a user (e.g., admin or a test user)
        # Assuming users_crud.add_user handles password hashing and returns user_id
        # We need role_id first.
        admin_role_id = users_crud.get_role_id_by_name("Administrator", conn=cls.conn) # Assuming "Administrator" role exists from init_schema
        if not admin_role_id: # Fallback if role not found or specific test role needed
            # This part depends on how roles are seeded by init_schema.
            # For robustness, could add a test role here if needed.
            # For now, assuming 'Administrator' is available.
            admin_role_id = users_crud.add_role("TestAdminRoleForReferents", "Test role for referents", conn=cls.conn)


        cls.test_user_id = users_crud.add_user(
            username=f"ref_test_user_{uuid.uuid4().hex[:6]}",
            password="password",
            role_id=admin_role_id, # Use fetched/created role_id
            full_name="Referent Test User",
            email=f"ref_user_{uuid.uuid4().hex[:6]}@example.com",
            conn=cls.conn
        )
        if not cls.test_user_id:
            raise Exception("Failed to seed test user for Referents CRUD tests.")

        # Seed clients
        # Need a status_id for client creation
        client_status_active = status_settings_crud.get_status_setting_by_name("Client Actif", "Client", conn=cls.conn)
        if not client_status_active:
            raise Exception("Default 'Client Actif' status not found for client seeding.")
        active_status_id = client_status_active['status_id']

        client_data1 = {
            'client_name': "Referent Client One", 'company_name': "RefOne Ltd.",
            'country_id': cls.test_country_id, 'status_id': active_status_id,
            'created_by_user_id': cls.test_user_id, 'project_identifier': 'REF001'
        }
        res1 = clients_crud.add_client(client_data1, conn=cls.conn)
        cls.sample_client_id1 = res1.get('client_id') if res1 and res1.get('success') else None
        if not cls.sample_client_id1: raise Exception("Failed to seed client 1")

        client_data2 = {
            'client_name': "Referent Client Two", 'company_name': "RefTwo Co.",
            'country_id': cls.test_country_id, 'status_id': active_status_id,
            'created_by_user_id': cls.test_user_id, 'project_identifier': 'REF002'
        }
        res2 = clients_crud.add_client(client_data2, conn=cls.conn)
        cls.sample_client_id2 = res2.get('client_id') if res2 and res2.get('success') else None
        if not cls.sample_client_id2: raise Exception("Failed to seed client 2")

        # cls.conn.commit() # Handled by _manage_conn in CRUDs

    @classmethod
    def tearDownClass(cls):
        if cls.conn:
            cls.conn.close()

    def test_01_add_referent(self):
        """Test adding a new referent."""
        referent_id = referents_crud.add_referent(
            client_id=self.sample_client_id1,
            country_id=self.test_country_id,
            region_id=self.test_region_id,
            city_id=None, # Assuming city is optional or not set up for this test client
            notes="Sample referent one",
            created_by_user_id=self.test_user_id,
            conn=self.conn
        )
        self.assertIsNotNone(referent_id)
        self.assertIsInstance(referent_id, str) # UUID

        # Verify
        ref = referents_crud.get_referent_by_id(referent_id, conn=self.conn)
        self.assertIsNotNone(ref)
        self.assertEqual(ref['client_id'], self.sample_client_id1)
        self.assertEqual(ref['notes'], "Sample referent one")

    def test_02_add_duplicate_referent_for_same_client(self):
        """Test that a client cannot be made a referent more than once."""
        # First one was added in test_01_add_referent
        referent_id_again = referents_crud.add_referent(
            client_id=self.sample_client_id1, # Same client
            country_id=self.test_country_id, region_id=None, city_id=None,
            notes="Attempt duplicate", created_by_user_id=self.test_user_id, conn=self.conn
        )
        self.assertIsNone(referent_id_again, "Should not allow adding a client as referent twice.")

    def test_03_get_referent_by_client_id(self):
        """Test fetching a referent by client_id."""
        # Assumes sample_client_id1 is already a referent from test_01
        ref = referents_crud.get_referent_by_client_id(self.sample_client_id1, conn=self.conn)
        self.assertIsNotNone(ref)
        self.assertEqual(ref['client_id'], self.sample_client_id1)

    def test_04_get_all_referents(self):
        """Test fetching all referents with details."""
        # Add another referent
        referents_crud.add_referent(
            client_id=self.sample_client_id2, country_id=self.test_country_id,
            region_id=self.test_region_id, city_id=None, notes="Client Two as Referent",
            created_by_user_id=self.test_user_id, conn=self.conn
        )
        all_refs = referents_crud.get_all_referents(conn=self.conn)
        self.assertIsInstance(all_refs, list)
        self.assertTrue(len(all_refs) >= 2) # At least the two we added/ensured

        # Check if joined names are present for one of them
        found_client_one = any(r['client_id'] == self.sample_client_id1 and 'client_name' in r for r in all_refs)
        self.assertTrue(found_client_one, "Joined client_name should be in get_all_referents output.")

    def test_05_update_referent(self):
        """Test updating a referent's details."""
        ref_profile = referents_crud.get_referent_by_client_id(self.sample_client_id1, conn=self.conn)
        self.assertIsNotNone(ref_profile, "Referent for client 1 should exist for update test.")
        referent_id_to_update = ref_profile['referent_id']

        update_data = {"notes": "Updated referent notes", "is_active": False}
        updated = referents_crud.update_referent(referent_id_to_update, update_data, conn=self.conn)
        self.assertTrue(updated)

        updated_ref = referents_crud.get_referent_by_id(referent_id_to_update, conn=self.conn)
        self.assertEqual(updated_ref['notes'], "Updated referent notes")
        self.assertEqual(updated_ref['is_active'], 0) # False is stored as 0 in SQLite for BOOLEAN

    def test_06_set_referent_active_status(self):
        """Test setting a referent's active status."""
        ref_profile = referents_crud.get_referent_by_client_id(self.sample_client_id1, conn=self.conn, include_inactive=True)
        referent_id_for_status_change = ref_profile['referent_id']

        # Reactivate
        activated = referents_crud.set_referent_active_status(referent_id_for_status_change, True, conn=self.conn)
        self.assertTrue(activated)
        active_ref = referents_crud.get_referent_by_id(referent_id_for_status_change, conn=self.conn)
        self.assertEqual(active_ref['is_active'], 1) # True is 1

    def test_07_get_all_referents_filters(self):
        """Test filtering in get_all_referents."""
        # Assuming client 1 (active) and client 2 (active) are referents in test_country_id
        # Deactivate client 1's referent status for this test
        ref_profile1 = referents_crud.get_referent_by_client_id(self.sample_client_id1, conn=self.conn, include_inactive=True)
        referents_crud.set_referent_active_status(ref_profile1['referent_id'], False, conn=self.conn)

        # Get only active
        active_refs = referents_crud.get_all_referents(filters={'country_id': self.test_country_id}, include_inactive=False, conn=self.conn)
        self.assertTrue(all(r['is_active'] == 1 for r in active_refs))
        client_ids_active = [r['client_id'] for r in active_refs]
        self.assertNotIn(self.sample_client_id1, client_ids_active)
        self.assertIn(self.sample_client_id2, client_ids_active) # Client 2 should still be active

        # Get all including inactive
        all_refs_in_country = referents_crud.get_all_referents(filters={'country_id': self.test_country_id}, include_inactive=True, conn=self.conn)
        client_ids_all = [r['client_id'] for r in all_refs_in_country]
        self.assertIn(self.sample_client_id1, client_ids_all)
        self.assertIn(self.sample_client_id2, client_ids_all)

        # Reactivate client 1 for subsequent tests if needed
        referents_crud.set_referent_active_status(ref_profile1['referent_id'], True, conn=self.conn)


    def test_08_delete_referent(self):
        """Test deleting a referent."""
        # Use client2 for this test to avoid impacting client1 used in other tests
        ref_profile2 = referents_crud.get_referent_by_client_id(self.sample_client_id2, conn=self.conn)
        self.assertIsNotNone(ref_profile2, "Referent for client 2 should exist for delete test.")
        referent_id_to_delete = ref_profile2['referent_id']

        deleted = referents_crud.delete_referent(referent_id_to_delete, conn=self.conn)
        self.assertTrue(deleted)

        fetched_ref = referents_crud.get_referent_by_id(referent_id_to_delete, conn=self.conn)
        self.assertIsNone(fetched_ref)

if __name__ == '__main__':
    unittest.main()
