import unittest
import sys
import os

# Set the TESTING environment variable BEFORE importing any application modules
os.environ["TESTING"] = "1"

# Add project root to sys.path to allow importing 'app'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.core.initializer import initialize_database
from app.db.connection import get_db_connection
from app.db.cruds.users import users_crud
from app.core.config import CONFIG

class TestAuth(unittest.TestCase):

    def setUp(self):
        """
        Initialize the database and seed it with default data before each test.
        """
        # Delete the database file to ensure a clean slate
        db_path = CONFIG.get("database_path")
        if os.path.exists(db_path):
            os.remove(db_path)

        print("Initializing database for test...")
        # This function now handles migrations and seeding if the DB is new
        initialize_database(CONFIG, project_root)
        print("Database initialized.")

    def test_admin_login(self):
        """Test that the default admin user can log in with correct credentials."""
        print("Testing admin login...")
        username = CONFIG.get("default_admin_username", "admin")
        password = CONFIG.get("default_admin_password", "admin")

        db_session = get_db_connection()
        try:
            # First, check if the user exists
            user = users_crud.get_user_by_username(db_session, username)
            self.assertIsNotNone(user, f"Admin user '{username}' should exist after seeding.")

            # Now, authenticate the user
            password_verified, _ = users_crud.util_verify_password(password, user.hashed_password)
            self.assertTrue(password_verified, "Authentication should succeed with correct admin credentials.")
            print("Admin login successful.")
        finally:
            db_session.close()


if __name__ == '__main__':
    unittest.main()
