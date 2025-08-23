import os
import sys
import logging

# Add project root to sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.core.config import CONFIG
from app.db.connection import set_db_config, initialize_engine_and_session, get_db_connection
from app.db.cruds.users import users_crud
from app.utils.auth import verify_password

def test_admin_login():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    logger = logging.getLogger(__name__)
    logger.info("--- Starting Admin Login Test ---")

    try:
        # 1. Initialize DB Connection
        set_db_config(CONFIG)
        initialize_engine_and_session(CONFIG)
        logger.info("Database connection initialized.")

        # 2. Get a DB session
        db = get_db_connection()
        logger.info("Database session acquired.")

        # 3. Fetch the admin user
        admin_user = users_crud.get_user_by_username(db, "admin")

        if not admin_user:
            logger.critical("TEST FAILED: Admin user not found in the database.")
            sys.exit(1)

        logger.info(f"Admin user found: {admin_user.username} (ID: {admin_user.user_id})")

        # 4. Verify the password
        plain_password = "admin_password"
        if not verify_password(plain_password, admin_user.hashed_password):
            logger.critical("TEST FAILED: Admin password verification failed.")
            sys.exit(1)

        logger.info("Admin password verified successfully.")
        logger.info("--- Admin Login Test PASSED ---")
        sys.exit(0)

    except Exception as e:
        logger.critical(f"An unexpected error occurred during the login test: {e}", exc_info=True)
        sys.exit(1)
    finally:
        if 'db' in locals() and db:
            db.close()

if __name__ == "__main__":
    test_admin_login()
