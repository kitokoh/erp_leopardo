import sys
import os
import logging

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app.core.app_setup import setup_logging, CONFIG
from app.db.connection import initialize_engine_and_session, set_db_config, get_db_connection
from app.services.auth import authentication
from app.db.seeders.user_seeder import seed_default_users
from app.db.seeders.role_permission_seeder import seed_roles_and_permissions

def test_login():
    """Tests the admin login functionality."""
    # 1. Setup Logging
    setup_logging()
    logging.info("Starting login test...")

    # 2. Load Configuration and Initialize DB
    if not CONFIG:
        logging.critical("Failed to load configuration. Exiting.")
        return

    # Clean slate
    db_path = CONFIG.get("database_path")
    if os.path.exists(db_path):
        os.remove(db_path)
        logging.info(f"Removed existing database file at {db_path}")

    try:
        set_db_config(CONFIG)
        initialize_engine_and_session(CONFIG)
        logging.info("Database engine and session initialized successfully.")
    except Exception as e:
        logging.critical(f"Failed to initialize database: {e}", exc_info=True)
        return

    # 3. Seed data directly
    db = None
    try:
        db = get_db_connection()
        logging.info("Seeding roles and permissions...")
        seed_roles_and_permissions(db, logging.getLogger())
        logging.info("Seeding default users...")
        seed_default_users(db, logging.getLogger())
    except Exception as e:
        logging.critical(f"Failed to seed data: {e}", exc_info=True)
        if db:
            db.rollback()
    finally:
        if db:
            db.close()

    # 4. Attempt Login
    username = CONFIG.get("default_admin_username", "admin")
    password = CONFIG.get("default_admin_password", "admin")
    logging.info(f"Attempting login for user: {username}")

    success, error_message, user_info, license_info = authentication.login(username, password)

    if success:
        logging.info("Login successful!")
        logging.info(f"User Info: {user_info}")
        logging.info(f"License Info: {license_info}")
        print("\n[SUCCESS] Admin login test passed!")
    else:
        logging.error(f"Login failed: {error_message}")
        print(f"\n[FAILURE] Admin login test failed: {error_message}")

if __name__ == "__main__":
    test_login()
