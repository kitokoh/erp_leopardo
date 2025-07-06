import os

# --- Application Root ---
APP_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Database Settings ---
DATABASE_NAME = "app_data.db"
DATABASE_PATH = os.path.join(APP_ROOT_DIR, DATABASE_NAME)

# --- Default Admin User Settings (for initial seeding) ---
DEFAULT_ADMIN_USERNAME = "admin"
# For production, ensure DEFAULT_ADMIN_PASSWORD environment variable is set to a strong, unique password.
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin")

# --- Path Settings ---
LOGO_SUBDIR = "company_logos"
LOGO_DIR_PATH = os.path.join(APP_ROOT_DIR, LOGO_SUBDIR)

PARTNERS_DOCUMENTS_SUBDIR = "partners_documents"
PARTNERS_DOCUMENTS_DIR = os.path.join(APP_ROOT_DIR, PARTNERS_DOCUMENTS_SUBDIR)

MEDIA_FILES_SUBDIR = "media_files" # Changed from MEDIA_FILES_DIR_NAME to match new var name
MEDIA_FILES_BASE_PATH = os.path.join(APP_ROOT_DIR, MEDIA_FILES_SUBDIR)

DEFAULT_DOWNLOAD_SUBDIR = "downloaded_media" # Changed from DEFAULT_DOWNLOAD_DIR_NAME
DEFAULT_DOWNLOAD_PATH = os.path.join(APP_ROOT_DIR, DEFAULT_DOWNLOAD_SUBDIR)

COMPANY_FACTURES_SUBDIR = "company_factures"
COMPANY_FACTURES_DIR_PATH = os.path.join(APP_ROOT_DIR, COMPANY_FACTURES_SUBDIR)

# Note: The os.makedirs(LOGO_DIR_PATH, exist_ok=True) line previously in db_config.py
# has been removed. This directory creation logic should be handled in app_setup.py
# or a similar application initialization script.

# --- API Specific Settings ---
# Example: API_SECRET_KEY = os.getenv("API_SECRET_KEY", "a_sEcReT_kEy_for_dev_only")
# (This is handled in api/auth.py, but could be centralized here if desired for other keys)

# --- License Management Settings ---
LICENSE_REQUEST_SERVER_URL = "http://127.0.0.1:5678/api/license/request"


# print(f"Config loaded. Database Path: {DATABASE_PATH}")
# print(f"Root app dir: {APP_ROOT_DIR}")

# Central CONFIG dictionary
CONFIG = {
    "app_root_dir": APP_ROOT_DIR,
    "database_name": DATABASE_NAME,
    "database_path": DATABASE_PATH,
    "default_admin_username": DEFAULT_ADMIN_USERNAME,
    "default_admin_password": DEFAULT_ADMIN_PASSWORD,
    "logo_dir": LOGO_DIR_PATH,
    "partners_documents_dir": PARTNERS_DOCUMENTS_DIR,
    "media_files_base_path": MEDIA_FILES_BASE_PATH,
    "default_download_path": DEFAULT_DOWNLOAD_PATH,
    "company_factures_dir": COMPANY_FACTURES_DIR_PATH,
    "license_request_server_url": LICENSE_REQUEST_SERVER_URL,
    # Add other relevant paths or settings that modules might expect from a CONFIG dict
    "clients_dir": os.path.join(APP_ROOT_DIR, "clients"), # As used in commande_widget.py
    "templates_dir": os.path.join(APP_ROOT_DIR, "resources", "templates"), # As used in create_document_dialog.py & commande_widget.py
    "default_document_language": "fr", # Example, used in document_manager_logic.py
    "default_reminder_days": 30, # Example, used in document_manager_logic.py

    # --- PostgreSQL Settings (add sensible defaults or placeholders) ---
    "postgresql_host": "localhost",
    "postgresql_port": 5432,
    "postgresql_user": "your_pg_user", # Placeholder - user should configure
    "postgresql_password": "your_pg_password", # Placeholder - user should configure
    "postgresql_dbname": "app_data_pg", # Placeholder - user should configure
    "postgresql_ssl_mode": "prefer", # Default SSL mode: prefer, allow, require, verify-ca, verify-full
    "postgresql_ssl_rootcert": "",   # Path to SSL root CA certificate
    "postgresql_ssl_clientcert": "", # Path to SSL client certificate
    "postgresql_ssl_clientkey": "",  # Path to SSL client key
}
