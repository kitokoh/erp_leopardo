import unittest
import os
import sys

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from client_management.client_controller import ClientController
from db.cruds import clients_crud, users_crud
from db import init_schema, db_seed
from app_setup import CONFIG

class TestClientPersistence(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up the database once for all tests."""
    @classmethod
    def setUpClass(cls):
        """Set up the database once for all tests."""
        # Use an in-memory database for testing
        CONFIG['database_path'] = ":memory:"
        init_schema.initialize_database(CONFIG)
        db_seed.run_seed()
        cls.client_controller = ClientController()

        # We need a user to associate with the client
        cls.test_user = users_crud.get_user_by_username("admin")
        if not cls.test_user:
            # If admin user doesn't exist, try to get any user
            all_users = users_crud.list_users()
            if all_users:
                cls.test_user = all_users[0]
            else:
                raise Exception("No users found in the database for testing.")
        cls.user_id = cls.test_user['user_id']


    def test_1_create_country_and_city(self):
        """Test that a new country and city can be created and persisted."""
        print("\n--- Running test_1_create_country_and_city ---")
        new_country_name = "Testland"
        new_city_name = "Testville"

        # Add country
        country_obj = self.client_controller.add_country(new_country_name)
        self.assertIsNotNone(country_obj)
        self.assertEqual(country_obj['country_name'], new_country_name)
        print(f"Successfully created/retrieved country: {country_obj}")

        # Add city
        country_id = country_obj['country_id']
        city_obj = self.client_controller.add_city(new_city_name, country_id)
        self.assertIsNotNone(city_obj)
        self.assertEqual(city_obj['city_name'], new_city_name)
        self.assertEqual(city_obj['country_id'], country_id)
        print(f"Successfully created/retrieved city: {city_obj}")

    def test_2_create_client_and_verify_persistence(self):
        """Test that a client can be created and is persisted in the database."""
        print("\n--- Running test_2_create_client_and_verify_persistence ---")
        client_data = {
            "client_name": "Persistent Test Client",
            "company_name": "Test Corp",
            "primary_need_description": "Testing persistence",
            "country_name": "Testland",
            "city_name": "Testville",
            "project_identifier": "PROJ-PERSIST",
            "selected_languages": "en,fr",
            "created_by_user_id": self.user_id
        }

        # Create client
        created_client_info = self.client_controller.create_client(client_data)
        self.assertIsNotNone(created_client_info)
        self.assertTrue(created_client_info.get('success') or 'client_id' in created_client_info)

        new_client_id = created_client_info.get('client_id')
        self.assertIsNotNone(new_client_id)
        print(f"Client created with ID: {new_client_id}")

        # Verify persistence by reading from DB
        retrieved_client = clients_crud.get_client_by_id(new_client_id)
        self.assertIsNotNone(retrieved_client)
        self.assertEqual(retrieved_client['client_name'], client_data['client_name'])
        self.assertEqual(retrieved_client['project_identifier'], client_data['project_identifier'])
        print(f"Successfully retrieved client from DB: {retrieved_client['client_name']}")

        # Verify details display simulation
        client_details = clients_crud.get_all_clients_with_details(filters={'client_name': 'Persistent Test Client'})
        self.assertEqual(len(client_details), 1)
        client_detail = client_details[0]
        self.assertEqual(client_detail['client_name'], client_data['client_name'])
        self.assertEqual(client_detail['country'], client_data['country_name'])
        self.assertEqual(client_detail['city'], client_data['city_name'])
        print(f"Successfully verified client details for display: {client_detail}")

if __name__ == '__main__':
    unittest.main()
