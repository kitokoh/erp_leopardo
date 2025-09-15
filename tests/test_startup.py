import sys
import os
from unittest.mock import patch, MagicMock

import pytest
from PyQt5.QtWidgets import QApplication

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now we can import the main function
from main import main as main_function

@pytest.fixture(scope="session")
def qapp():
    """Session-wide QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app

@patch('main.LoginDialog')
@patch('main.DocumentManager')
@patch('main.QApplication.exec_')
@patch('main.sys.exit')
def test_application_startup(mock_sys_exit, mock_app_exec, mock_doc_manager, mock_login_dialog, qapp):
    """
    Tests the application startup sequence to ensure it completes without crashing.
    Mocks out the UI components to prevent the application from blocking the test.
    """
    # Arrange: Configure mocks
    # Simulate a successful login
    mock_login_instance = mock_login_dialog.return_value
    mock_login_instance.exec_.return_value = MagicMock().Accepted

    # Act
    try:
        main_function()
    except Exception as e:
        pytest.fail(f"Application startup failed with an exception: {e}")

    # Assert
    # Check that the main window was called
    mock_doc_manager.assert_called_once()
    # Check that the app event loop was started
    mock_app_exec.assert_called_once()
