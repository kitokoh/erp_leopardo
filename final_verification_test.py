import os
import sys
import logging
import subprocess

# Ensure the app module is in the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.core.config import CONFIG
from app.db.connection import initialize_engine_and_session, set_db_config
from app.services.auth.authentication import login

def run_full_stack_test():
    """
    A comprehensive test that simulates the full application startup and login.
    1. Deletes the old test database.
    2. Runs the full initializer (migrations + seeding).
    3. Attempts to log in as the default admin.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    os.environ["TESTING"] = "1"

    # 1. Configure for a fresh test database
    db_filename = 'verification_test.db'
    CONFIG['database_path'] = os.path.join(project_root, db_filename)
    CONFIG['database_url'] = f"sqlite:///{CONFIG['database_path']}"
    db_path = CONFIG['database_path']

    logging.info("--- Starting Final Verification Test ---")
    print("--- Starting Final Verification Test ---")
    if os.path.exists(db_path):
        logging.info(f"Deleting existing test database: {db_path}")
        print(f"Deleting existing test database: {db_path}")
        os.remove(db_path)

    # 2. Run the full database initializer script
    logging.info("Running the main database initializer...")
    print("Running the main database initializer...")
    try:
        # We need to run main.py's initialization logic.
        # The easiest way is to call the same function that main() calls.
        from app.core.initializer import initialize_database
        initialize_database(CONFIG, project_root)
        logging.info("Initializer function completed.")
        print("Initializer function completed.")
    except SystemExit as e:
        logging.error(f">>> Verification FAILED: The database initializer exited prematurely. Check logs for critical errors. EXIT DETAILS: {e} <<<")
        print(f">>> Verification FAILED: The database initializer exited prematurely. Check logs for critical errors. EXIT DETAILS: {e} <<<")
        return False
    except Exception as e:
        logging.error(f">>> Verification FAILED: An unhandled exception occurred during database initialization: {e}", exc_info=True)
        print(f">>> Verification FAILED: An unhandled exception occurred during database initialization: {e}")
        return False

    # 3. Attempt login
    logging.info("--- Running Admin Login Check ---")
    print("--- Running Admin Login Check ---")
    try:
        logging.info(f"Attempting login with user: {CONFIG['default_admin_username']}")
        print(f"Attempting login with user: {CONFIG['default_admin_username']}")
        success, message, user_data, license_details = login(
            username=CONFIG['default_admin_username'],
            password=CONFIG['default_admin_password'],
            remember_me=False
        )

        if success and user_data and user_data.get('username') == CONFIG['default_admin_username']:
            logging.info(">>> Verification PASSED: Admin login successful. <<<")
            print(">>> Verification PASSED: Admin login successful. <<<")
            logging.info("The test database is available for inspection at: " + db_path)
            print("The test database is available for inspection at: " + db_path)
            return True
        else:
            logging.error(f">>> Verification FAILED: Login failed. Message: {message} <<<")
            print(f">>> Verification FAILED: Login failed. Message: {message} <<<")
            return False

    except Exception as e:
        logging.error(">>> Verification FAILED: An exception occurred during the login attempt.", exc_info=True)
        print(f">>> Verification FAILED: An exception occurred during the login attempt. Exception: {e}")
        return False

if __name__ == "__main__":
    if run_full_stack_test():
        sys.exit(0)
    else:
        sys.exit(1)
