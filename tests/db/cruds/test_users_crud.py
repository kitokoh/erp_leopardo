import unittest
import sqlite3
import os
import uuid
from db.cruds import users_crud, roles_crud
from db.init_schema import initialize_database # To setup schema in memory
from utils import hash_password # For creating users

# Define a global path for a temporary test database file
TEST_DB_PATH = "test_app_data_users_crud.db"

class TestUsersCrud(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Set up a temporary in-memory database or a file-based one for testing.
        This will initialize the schema.
        """
        # Override DATABASE_PATH for tests if init_schema uses it from config
        # For simplicity, directly use TEST_DB_PATH with sqlite3.connect
        # and ensure init_schema can be pointed to this DB.

        # If there's an existing test DB, remove it
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

        # Store original config path if needed and mock config.DATABASE_PATH
        # For now, assume initialize_database can be made to work with a passed connection
        # or we manage connection directly.
        # The simplest is to let initialize_database create the file defined by TEST_DB_PATH
        # by temporarily overriding config if needed, or by modifying init_schema to accept a path.

        # For this test, we will ensure initialize_database uses TEST_DB_PATH
        # This is tricky if config.py is imported directly by init_schema.
        # A robust way is to allow initialize_database to accept a db_path.
        # Assuming current initialize_database uses config.DATABASE_PATH:
        try:
            from config import DATABASE_PATH as ORIGINAL_DB_PATH
            import config
            config.DATABASE_PATH = TEST_DB_PATH
            cls.original_db_path = ORIGINAL_DB_PATH # store to restore
            cls.config_module = config
        except ImportError: # config.py might not exist or be in path
            cls.original_db_path = None
            cls.config_module = None
            # If config doesn't exist, init_schema might use a fallback.
            # This test will then rely on that fallback or fail if db path is not controllable.
            # For now, we proceed assuming init_schema will create TEST_DB_PATH due to override.

        initialize_database() # This should now use TEST_DB_PATH

    @classmethod
    def tearDownClass(cls):
        """Clean up the test database file."""
        if cls.original_db_path and cls.config_module: # Restore original config path
            cls.config_module.DATABASE_PATH = cls.original_db_path

        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

    def setUp(self):
        """Connect to the test database before each test."""
        self.conn = sqlite3.connect(TEST_DB_PATH)
        self.conn.row_factory = sqlite3.Row # Important for accessing columns by name

        # Ensure at least one role exists for creating users
        # Using roles_crud and passing the connection
        cursor = self.conn.cursor()
        cursor.execute("SELECT role_id FROM Roles WHERE role_name = 'TestRole'")
        role = cursor.fetchone()
        if not role:
            roles_crud.add_role("TestRole", "A role for testing users_crud", conn=self.conn)

        cursor.execute("SELECT role_id FROM Roles WHERE role_name = 'TestRole'")
        self.test_role_id = cursor.fetchone()['role_id']
        self.conn.commit() # Commit role creation


    def tearDown(self):
        """Close the connection after each test. Clean up tables if needed."""
        # Clean up users to avoid conflicts between tests
        # Or, each test could use unique usernames.
        # For simplicity, let's clear users table.
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM Users")
        self.conn.commit()
        self.conn.close()

    def _add_test_user(self, username_suffix="test"):
        """Helper to add a user for testing."""
        username = f"user_{username_suffix}_{uuid.uuid4().hex[:6]}"
        email = f"{username}@example.com"
        user_id = users_crud.add_user(
            username, "password123", self.test_role_id,
            full_name=f"User {username_suffix.capitalize()}", email=email,
            conn=self.conn
        )
        self.conn.commit() # add_user uses @_manage_conn which commits per call if conn is not passed
                           # but if conn is passed, commit is handled by caller of _manage_conn wrapper.
                           # Here, we pass self.conn, so commit is needed.
        self.assertIsNotNone(user_id)
        return user_id, username

    def test_01_add_user_initializes_biometric_fields(self):
        """Test that new users have biometric fields initialized to False/Null."""
        user_id, _ = self._add_test_user("bio_init")

        user = users_crud.get_user_by_id(user_id, conn=self.conn)
        self.assertIsNotNone(user)
        self.assertEqual(user['is_fingerprint_auth_enabled'], 0) # SQLite BOOLEAN is 0 or 1
        self.assertIsNone(user['fingerprint_template_id'])
        self.assertEqual(user['is_face_auth_enabled'], 0)
        self.assertIsNone(user['face_template_id'])
        self.assertEqual(user['is_voice_auth_enabled'], 0)
        self.assertIsNone(user['voice_profile_id'])

    def test_02_set_and_get_biometric_auth_status_fingerprint(self):
        """Test setting and getting fingerprint auth status."""
        user_id, _ = self._add_test_user("fingerprint")

        # Enable fingerprint
        result = users_crud.set_biometric_auth_status(user_id, "fingerprint", True, template_id="fp_template_123", conn=self.conn)
        self.conn.commit()
        self.assertTrue(result)

        status = users_crud.get_biometric_auth_status(user_id, conn=self.conn)
        self.assertIsNotNone(status)
        self.assertTrue(status['is_fingerprint_auth_enabled'])
        self.assertEqual(status['fingerprint_template_id'], "fp_template_123")
        # Check other methods remain unchanged
        self.assertFalse(status['is_face_auth_enabled'])
        self.assertFalse(status['is_voice_auth_enabled'])

        # Disable fingerprint
        result = users_crud.set_biometric_auth_status(user_id, "fingerprint", False, conn=self.conn)
        self.conn.commit()
        self.assertTrue(result)

        status_after_disable = users_crud.get_biometric_auth_status(user_id, conn=self.conn)
        self.assertIsNotNone(status_after_disable)
        self.assertFalse(status_after_disable['is_fingerprint_auth_enabled'])
        self.assertIsNone(status_after_disable['fingerprint_template_id']) # Template ID should be cleared

    def test_03_set_and_get_biometric_auth_status_face(self):
        """Test setting and getting face auth status."""
        user_id, _ = self._add_test_user("face")

        result = users_crud.set_biometric_auth_status(user_id, "face", True, template_id="face_id_abc", conn=self.conn)
        self.conn.commit()
        self.assertTrue(result)

        status = users_crud.get_biometric_auth_status(user_id, conn=self.conn)
        self.assertTrue(status['is_face_auth_enabled'])
        self.assertEqual(status['face_template_id'], "face_id_abc")

        result = users_crud.set_biometric_auth_status(user_id, "face", False, conn=self.conn)
        self.conn.commit()
        status_after_disable = users_crud.get_biometric_auth_status(user_id, conn=self.conn)
        self.assertFalse(status_after_disable['is_face_auth_enabled'])
        self.assertIsNone(status_after_disable['face_template_id'])

    def test_04_set_and_get_biometric_auth_status_voice(self):
        """Test setting and getting voice auth status."""
        user_id, _ = self._add_test_user("voice")

        result = users_crud.set_biometric_auth_status(user_id, "voice", True, template_id="voice_prof_xyz", conn=self.conn)
        self.conn.commit()
        self.assertTrue(result)

        status = users_crud.get_biometric_auth_status(user_id, conn=self.conn)
        self.assertTrue(status['is_voice_auth_enabled'])
        self.assertEqual(status['voice_profile_id'], "voice_prof_xyz") # Note: DB field is voice_profile_id

        result = users_crud.set_biometric_auth_status(user_id, "voice", False, conn=self.conn)
        self.conn.commit()
        status_after_disable = users_crud.get_biometric_auth_status(user_id, conn=self.conn)
        self.assertFalse(status_after_disable['is_voice_auth_enabled'])
        self.assertIsNone(status_after_disable['voice_profile_id'])

    def test_05_set_biometric_auth_invalid_method(self):
        """Test setting status for an invalid biometric method."""
        user_id, _ = self._add_test_user("invalid_method")
        result = users_crud.set_biometric_auth_status(user_id, "retina_scan", True, conn=self.conn)
        # No commit needed as it should fail and not change DB
        self.assertFalse(result) # Should fail for an unknown method

    def test_06_get_user_by_id_returns_biometric_fields(self):
        """Test that get_user_by_id returns new biometric fields."""
        user_id, _ = self._add_test_user("get_id_bio")
        users_crud.set_biometric_auth_status(user_id, "fingerprint", True, "fp1", conn=self.conn)
        self.conn.commit()

        user = users_crud.get_user_by_id(user_id, conn=self.conn)
        self.assertIsNotNone(user)
        self.assertIn('is_fingerprint_auth_enabled', user)
        self.assertEqual(user['is_fingerprint_auth_enabled'], 1) # 1 for True
        self.assertEqual(user['fingerprint_template_id'], "fp1")
        self.assertEqual(user['is_face_auth_enabled'], 0) # Should be default 0

    def test_07_get_user_by_username_returns_biometric_fields(self):
        """Test that get_user_by_username returns new biometric fields."""
        _, username = self._add_test_user("get_uname_bio")
        user_for_id = users_crud.get_user_by_username(username, conn=self.conn) # Get user to obtain ID
        self.assertIsNotNone(user_for_id)
        user_id = user_for_id['user_id']

        users_crud.set_biometric_auth_status(user_id, "face", True, "face1", conn=self.conn)
        self.conn.commit()

        user = users_crud.get_user_by_username(username, conn=self.conn) # Fetch again
        self.assertIsNotNone(user)
        self.assertIn('is_face_auth_enabled', user)
        self.assertEqual(user['is_face_auth_enabled'], 1)
        self.assertEqual(user['face_template_id'], "face1")
        self.assertEqual(user['is_fingerprint_auth_enabled'], 0)

if __name__ == '__main__':
    unittest.main()
