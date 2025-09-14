import os

# Get the project root assuming this mock_config.py is in app/tests/mocks
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATABASE_PATH = os.path.join(project_root, "test_app_data.db")
DATABASE_NAME = "test_app_data.db"
MEDIA_FILES_BASE_PATH = "/tmp/media_files"
COMPANY_LOGO_DIR = "company_logos_test"
TEMPLATES_DIR = "templates_test"
CLIENTS_DIR = "clients_test"
DEFAULT_ADMIN_USERNAME = "test_admin"
DEFAULT_ADMIN_PASSWORD = "test_password"
DEFAULT_DOWNLOAD_PATH = "/tmp/downloads"

# A dictionary that mimics the structure of the main CONFIG object
CONFIG = {
    "database_path": DATABASE_PATH,
    "database_name": DATABASE_NAME,
    "media_files_path": MEDIA_FILES_BASE_PATH,
    "company_logo_dir": COMPANY_LOGO_DIR,
    "templates_dir": TEMPLATES_DIR,
    "clients_dir": CLIENTS_DIR,
    "default_admin_username": DEFAULT_ADMIN_USERNAME,
    "default_admin_password": DEFAULT_ADMIN_PASSWORD,
    "default_download_path": DEFAULT_DOWNLOAD_PATH,
    # Add other key-value pairs as needed by tests
    "language": "en",
    "session_timeout_minutes": 30,
    "show_initial_setup_on_startup": False,
    "google_maps_review_url": "https://example.com/review",
    "smtp_server": "smtp.test.com",
    "smtp_port": 587,
    "smtp_user": "test@user.com",
    "smtp_password": "password"
}
