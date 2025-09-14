import os
import sys
import logging

project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.core.config import CONFIG
from app.db.session_manager import session_manager
from app.services.auth.authentication import login

def run_login_only_test():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

    # The default config creates the DB inside the /app/app directory.
    db_path = os.path.join(project_root, 'app', 'app_data.db')
    db_url = f"sqlite:///{db_path}"

    if not os.path.exists(db_path):
        logging.error(f">>> Login Test FAILED: Database file '{db_path}' does not exist. Run migration and seeding first. <<<")
        return False

    logging.info("--- Running Admin Login Test ---")
    try:
        session_manager.initialize(db_url)

        # The login function will now be refactored to accept a session
        success, message, user_data, license_details = login(
            username=CONFIG['default_admin_username'],
            password=CONFIG['default_admin_password'],
            remember_me=False
        )

        if success and user_data and user_data.get('username') == CONFIG['default_admin_username']:
            print(">>> Admin Login Test PASSED <<<")
            return True
        else:
            print(f">>> Admin Login Test FAILED: {message} <<<")
            return False
    except Exception as e:
        logging.error(">>> Admin Login Test FAILED: An exception occurred.", exc_info=True)
        return False

if __name__ == "__main__":
    if run_login_only_test():
        sys.exit(0)
    else:
        sys.exit(1)
