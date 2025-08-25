import os
import sys
import logging
import subprocess

# Add project root to sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.core.config import CONFIG
from app.db.connection import set_db_config, initialize_engine_and_session, get_db_connection
from app.db.db_seed import seed_all_data
from app.db.cruds.users import users_crud
from app.utils.auth import verify_password

def setup_database_and_test_login():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    logger = logging.getLogger(__name__)
    logger.info("--- Starting Full Database Setup and Login Test ---")

    # 1. Delete old DB
    db_path = os.path.join(project_root, "app", "core", "app_data.db")
    if os.path.exists(db_path):
        os.remove(db_path)
        logger.info(f"Removed old database file: {db_path}")

    # 2. Run Alembic migrations using subprocess
    try:
        logger.info("Running Alembic migrations via subprocess...")
        # Using text=True to get stdout/stderr as strings
        result = subprocess.run(
            ["poetry", "run", "alembic", "upgrade", "head"],
            check=True, capture_output=True, text=True
        )
        logger.info("Alembic stdout:\n" + result.stdout)
        if result.stderr:
            logger.warning("Alembic stderr:\n" + result.stderr)
        logger.info("Alembic migrations completed.")
    except subprocess.CalledProcessError as e:
        logger.critical(f"Alembic migration failed!\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        logger.critical("'poetry' command not found. Is poetry installed and in the system's PATH?")
        sys.exit(1)


    # 3. Initialize DB session and run seeders
    db = None
    try:
        logger.info("Initializing DB session...")
        set_db_config(CONFIG)
        initialize_engine_and_session(CONFIG)
        db = get_db_connection()
        logger.info("DB session acquired. Running seeders...")
        seed_all_data(db) # Pass the session to the seeder
        logger.info("Data seeding completed.")
    except Exception as e:
        logger.critical(f"Data seeding failed: {e}", exc_info=True)
        if db:
            db.close()
        sys.exit(1)

    # 4. Test admin login
    try:
        logger.info("--- Starting Admin Login Test ---")
        admin_user = users_crud.get_user_by_username(db, "admin")

        if not admin_user:
            logger.critical("TEST FAILED: Admin user not found in the database.")
            sys.exit(1)

        logger.info(f"Admin user found: {admin_user.username}")

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
        if db:
            db.close()

if __name__ == "__main__":
    setup_database_and_test_login()
