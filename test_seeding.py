import os
import sys
import logging

# Ensure the app module is in the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.core.config import CONFIG
from app.db.connection import initialize_engine_and_session, get_db_connection
from app.db.db_seed import seed_all_data

def run_seeding_test():
    """
    Tests only the database seeding step, assuming migration has already run.
    """
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

    # 1. Configure for the test database
    CONFIG['database_path'] = os.path.join(project_root, 'test.db')
    CONFIG['database_url'] = f"sqlite:///{CONFIG['database_path']}"

    db_path = CONFIG['database_path']

    if not os.path.exists(db_path):
        logging.error(">>> Seeding Test FAILED: Database file does not exist. Run migration test first. <<<")
        return False

    # 2. Initialize the engine and run the seeder
    logging.info("--- Running Database Seeding ---")
    db_session = None
    try:
        initialize_engine_and_session(CONFIG)
        db_session = get_db_connection()
        seed_all_data(db_session)
        logging.info("--- Database Seeding Complete ---")
        logging.info(">>> Seeding Test PASSED <<<")
        return True
    except Exception as e:
        logging.error(">>> Seeding Test FAILED: An error occurred during seeding.", exc_info=True)
        return False
    finally:
        if db_session:
            db_session.close()

if __name__ == "__main__":
    if run_seeding_test():
        sys.exit(0)
    else:
        sys.exit(1)
