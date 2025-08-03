import unittest
import sqlite3
import os
import uuid
from db.cruds import users_crud, roles_crud
from db.init_schema import initialize_database # To setup schema in memory
from utils import hash_password # For creating users

# Define a global path for a temporary test database file
TEST_DB_PATH = "test_app_data_users_crud.db"

from db.models import Base, User, Role

class TestUsersCrud(unittest.TestCase):

    def setUp(self):
        """Set up a temporary in-memory database for testing."""
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

        # Ensure at least one role exists for creating users
        self.test_role = Role(role_name="TestRole", description="A role for testing users_crud")
        self.session.add(self.test_role)
        self.session.commit()
        self.test_role_id = self.test_role.role_id

    def tearDown(self):
        """Close the session and drop all tables."""
        self.session.close()
        Base.metadata.drop_all(self.engine)

    def _add_test_user(self, username_suffix="test"):
        """Helper to add a user for testing."""
        username = f"user_{username_suffix}_{uuid.uuid4().hex[:6]}"
        email = f"{username}@example.com"
        user_id = users_crud.add_user(
            username, "password123", self.test_role_id,
            full_name=f"User {username_suffix.capitalize()}", email=email,
            conn=self.session
        )
        self.assertIsNotNone(user_id)
        return user_id, username

    def test_01_add_user_initializes_biometric_fields(self):
        """Test that new users have biometric fields initialized to False/Null."""
        user_id, _ = self._add_test_user("bio_init")

        user = users_crud.get_user_by_id(user_id, conn=self.session)
        self.assertIsNotNone(user)
        self.assertEqual(user['is_fingerprint_auth_enabled'], False)
        self.assertIsNone(user['fingerprint_template_id'])
        self.assertEqual(user['is_face_auth_enabled'], False)
        self.assertIsNone(user['face_template_id'])
        self.assertEqual(user['is_voice_auth_enabled'], False)
        self.assertIsNone(user['voice_profile_id'])

    def test_02_set_and_get_biometric_auth_status_fingerprint(self):
        """Test setting and getting fingerprint auth status."""
        user_id, _ = self._add_test_user("fingerprint")

        # Enable fingerprint
        result = users_crud.set_biometric_auth_status(user_id, "fingerprint", True, template_id="fp_template_123", conn=self.session)
        self.session.commit()
        self.assertTrue(result)

        status = users_crud.get_biometric_auth_status(user_id, conn=self.session)
        self.assertIsNotNone(status)
        self.assertTrue(status['is_fingerprint_auth_enabled'])
        self.assertEqual(status['fingerprint_template_id'], "fp_template_123")
        # Check other methods remain unchanged
        self.assertFalse(status['is_face_auth_enabled'])
        self.assertFalse(status['is_voice_auth_enabled'])

        # Disable fingerprint
        result = users_crud.set_biometric_auth_status(user_id, "fingerprint", False, conn=self.session)
        self.session.commit()
        self.assertTrue(result)

        status_after_disable = users_crud.get_biometric_auth_status(user_id, conn=self.session)
        self.assertIsNotNone(status_after_disable)
        self.assertFalse(status_after_disable['is_fingerprint_auth_enabled'])
        self.assertIsNone(status_after_disable['fingerprint_template_id']) # Template ID should be cleared

    def test_03_set_and_get_biometric_auth_status_face(self):
        """Test setting and getting face auth status."""
        user_id, _ = self._add_test_user("face")

        result = users_crud.set_biometric_auth_status(user_id, "face", True, template_id="face_id_abc", conn=self.session)
        self.session.commit()
        self.assertTrue(result)

        status = users_crud.get_biometric_auth_status(user_id, conn=self.session)
        self.assertTrue(status['is_face_auth_enabled'])
        self.assertEqual(status['face_template_id'], "face_id_abc")

        result = users_crud.set_biometric_auth_status(user_id, "face", False, conn=self.session)
        self.session.commit()
        status_after_disable = users_crud.get_biometric_auth_status(user_id, conn=self.session)
        self.assertFalse(status_after_disable['is_face_auth_enabled'])
        self.assertIsNone(status_after_disable['face_template_id'])

    def test_04_set_and_get_biometric_auth_status_voice(self):
        """Test setting and getting voice auth status."""
        user_id, _ = self._add_test_user("voice")

        result = users_crud.set_biometric_auth_status(user_id, "voice", True, template_id="voice_prof_xyz", conn=self.session)
        self.session.commit()
        self.assertTrue(result)

        status = users_crud.get_biometric_auth_status(user_id, conn=self.session)
        self.assertTrue(status['is_voice_auth_enabled'])
        self.assertEqual(status['voice_profile_id'], "voice_prof_xyz") # Note: DB field is voice_profile_id

        result = users_crud.set_biometric_auth_status(user_id, "voice", False, conn=self.session)
        self.session.commit()
        status_after_disable = users_crud.get_biometric_auth_status(user_id, conn=self.session)
        self.assertFalse(status_after_disable['is_voice_auth_enabled'])
        self.assertIsNone(status_after_disable['voice_profile_id'])

    def test_05_set_biometric_auth_invalid_method(self):
        """Test setting status for an invalid biometric method."""
        user_id, _ = self._add_test_user("invalid_method")
        result = users_crud.set_biometric_auth_status(user_id, "retina_scan", True, conn=self.session)
        # No commit needed as it should fail and not change DB
        self.assertFalse(result) # Should fail for an unknown method

    def test_06_get_user_by_id_returns_biometric_fields(self):
        """Test that get_user_by_id returns new biometric fields."""
        user_id, _ = self._add_test_user("get_id_bio")
        users_crud.set_biometric_auth_status(user_id, "fingerprint", True, "fp1", conn=self.session)
        self.session.commit()

        user = users_crud.get_user_by_id(user_id, conn=self.session)
        self.assertIsNotNone(user)
        self.assertIn('is_fingerprint_auth_enabled', user)
        self.assertEqual(user['is_fingerprint_auth_enabled'], True)
        self.assertEqual(user['fingerprint_template_id'], "fp1")
        self.assertEqual(user['is_face_auth_enabled'], False)

    def test_07_get_user_by_username_returns_biometric_fields(self):
        """Test that get_user_by_username returns new biometric fields."""
        _, username = self._add_test_user("get_uname_bio")
        user_for_id = users_crud.get_user_by_username(username, conn=self.session) # Get user to obtain ID
        self.assertIsNotNone(user_for_id)
        user_id = user_for_id['user_id']

        users_crud.set_biometric_auth_status(user_id, "face", True, "face1", conn=self.session)
        self.session.commit()

        user = users_crud.get_user_by_username(username, conn=self.session) # Fetch again
        self.assertIsNotNone(user)
        self.assertIn('is_face_auth_enabled', user)
        self.assertEqual(user['is_face_auth_enabled'], True)
        self.assertEqual(user['face_template_id'], "face1")
        self.assertEqual(user['is_fingerprint_auth_enabled'], False)

if __name__ == '__main__':
    unittest.main()
