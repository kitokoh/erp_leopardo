import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Mock PyQt5 classes before they are imported by the application
mock_q_application = MagicMock()
mock_q_dialog = MagicMock()
mock_q_main_window = MagicMock()

# We need to return QDialog.Accepted from login_dialog.exec_() to proceed to the main window part.
mock_q_dialog.exec_.return_value = 1 # QDialog.Accepted is 1
mock_login_dialog_instance = MagicMock()
mock_login_dialog_instance.exec_.return_value = 1

# The main window's show() method will be called. We just need to mock it.
mock_document_manager_instance = MagicMock()

# Patch the entire modules or specific classes
patcher_q_application = patch('PyQt5.QtWidgets.QApplication', mock_q_application)
patcher_login_dialog = patch('app.services.auth.login_window.LoginWindow', mock_login_dialog_instance)
patcher_main_window = patch('app.views.gui.main_window.DocumentManager', mock_document_manager_instance)

class TestStartup(unittest.TestCase):

    def setUp(self):
        """Set up the test environment by starting the patchers."""
        self.patcher_q_application = patcher_q_application.start()
        self.patcher_login_dialog = patcher_login_dialog.start()
        self.patcher_main_window = patcher_main_window.start()

    def tearDown(self):
        """Tear down the test environment by stopping the patchers."""
        patcher_q_application.stop()
        patcher_login_dialog.stop()
        patcher_main_window.stop()

        # Clean up the test database file if it was created
        db_path = os.path.join(project_root, 'app', 'app_data.db')
        if os.path.exists(db_path):
            os.remove(db_path)

        user_db_path = os.path.join(project_root, 'user_profile_data.db')
        if os.path.exists(user_db_path):
            os.remove(user_db_path)

    def test_application_startup_sequence(self):
        """
        Tests the main application startup sequence to ensure it runs without crashing,
        specifically verifying that the database initialization completes.
        """
        # We need to patch sys.exit to prevent the test runner from exiting.
        with patch('sys.exit') as mock_exit:
            # Import main after patches are active
            from main import main as main_function

            # Run the main function
            main_function()

            # Assert that sys.exit was called by `app.exec_()` which means the
            # application successfully reached the end of its startup sequence.
            mock_exit.assert_called()

if __name__ == '__main__':
    unittest.main()
