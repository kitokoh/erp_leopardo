import os
import sys
import logging

# Ensure the app module is in the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.core.config import CONFIG
from app.db.connection import initialize_engine_and_session, set_db_config
from app.services.auth.authentication import login

def run_login_only_test():
    """
    Tests only the admin login, assuming a migrated and seeded database.
    """
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

    # 1. Configure for the application database
    db_path = os.path.join(project_root, 'app_data.db')
    CONFIG['database_path'] = db_path
    CONFIG['database_url'] = f"sqlite:///{db_path}"

    if not os.path.exists(db_path):
        logging.error(f">>> Login Test FAILED: Database file does not exist at {db_path}. Run migration and seeding first. <<<")
        return False

    # 2. Initialize the engine and attempt to log in
    logging.info("--- Running Admin Login Test ---")
    try:
        # Must initialize the engine for get_db_connection to work
        set_db_config(CONFIG)
        initialize_engine_and_session(CONFIG)

        success, message, user_data, license_details = login(
            username=CONFIG['default_admin_username'],
            password=CONFIG['default_admin_password'],
            remember_me=False
        )

        if success and user_data and user_data.get('username') == CONFIG['default_admin_username']:
            logging.info(">>> Admin Login Test PASSED <<<")
            return True
        else:
            logging.error(f">>> Admin Login Test FAILED: {message} <<<")
            return False

    except Exception as e:
        logging.error(">>> Admin Login Test FAILED: An exception occurred during login attempt.", exc_info=True)
        return False


if __name__ == "__main__":
    if run_login_only_test():
        sys.exit(0)
    else:
        sys.exit(1)
