import os
import sys
import logging
import subprocess

# Ensure the app module is in the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now it's safe to import from the app
from app.core.config import CONFIG
from app.db.db_seed import seed_all_data
from app.db.connection import get_db_connection, set_db_config, initialize_engine_and_session
from login_test import run_login_only_test

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

def run_command(command):
    """Runs a command and raises an exception on failure."""
    logging.info(f"Running command: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        logging.error(f"Command failed with exit code {result.returncode}")
        logging.error(f"STDOUT: {result.stdout}")
        logging.error(f"STDERR: {result.stderr}")
        raise RuntimeError(f"Command failed: {' '.join(command)}")
    logging.info("Command completed successfully.")
    return result

def main():
    """
    Orchestrates the full setup and test process.
    1. Deletes old DB.
    2. Runs Alembic migrations.
    3. Seeds the database.
    4. Runs the login test.
    """
    logging.info("--- Starting Full Integration Test ---")

    # 1. Define DB path and ensure it's clean
    db_path = os.path.join(project_root, 'app_data.db')
    if os.path.exists(db_path):
        logging.info(f"Removing existing database file at {db_path}")
        os.remove(db_path)

    try:
        # 2. Run Alembic migrations using poetry
        alembic_command = ["poetry", "run", "alembic", "upgrade", "head"]
        run_command(alembic_command)

        # 3. Seed the database
        logging.info("--- Seeding Database ---")
        # The seeder needs its own db session
        set_db_config(CONFIG)
        initialize_engine_and_session(CONFIG)
        db_session_for_seeding = get_db_connection()
        try:
            seed_all_data(db_session_for_seeding)
        finally:
            db_session_for_seeding.close()
        logging.info("Database seeding completed.")

        # 4. Run the login test
        logging.info("--- Running Login Test ---")
        if run_login_only_test():
            logging.info(">>> Full Integration Test PASSED <<<")
            sys.exit(0)
        else:
            logging.error(">>> Full Integration Test FAILED <<<")
            sys.exit(1)

    except (RuntimeError, Exception) as e:
        logging.critical(f"An error occurred during the test execution: {e}", exc_info=True)
        logging.error(">>> Full Integration Test FAILED <<<")
        sys.exit(1)

if __name__ == "__main__":
    main()
