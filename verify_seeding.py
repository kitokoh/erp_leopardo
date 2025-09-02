import os
import sys
import logging

# --- Setup Project Root ---
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Core Imports ---
from app.core.app_setup import CONFIG
from app.core.initializer import initialize_database
from app.services.auth import authentication

def run_seeding_verification():
    """
    Verifies that the database initialization and data seeding process works.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("--- Starting Seeding Verification Test ---")

    # 1. --- Clean up old database if it exists ---
    db_path = CONFIG.get('database_path')
    if os.path.exists(db_path):
        logging.info(f"Removing existing database at {db_path}")
        os.remove(db_path)
    else:
        logging.info("No existing database found. Starting fresh.")

    # 2. --- Initialize Database ---
    try:
        logging.info("Initializing database from scratch...")
        # The project root is now the current directory
        initialize_database(CONFIG, project_root)
        logging.info("Database initialization and seeding process completed.")
    except Exception as e:
        logging.critical(f"Database initialization failed: {e}", exc_info=True)
        return

    # 3. --- Attempt to log in as default admin ---
    logging.info("--- Verifying Admin User Seeding ---")
    admin_username = "admin"
    admin_password = "admin"
    success, message, user_data, license_details = authentication.login(admin_username, admin_password)

    if success:
        logging.info("SUCCESS: Default admin user login was successful.")
        logging.info(f"User data: {user_data}")
    else:
        logging.error(f"FAILURE: Default admin user login failed. Reason: {message}")

    logging.info("--- Seeding Verification Test Finished ---")


if __name__ == "__main__":
    run_seeding_verification()
