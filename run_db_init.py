import sys
import os
import logging
from alembic.config import Config
from alembic import command

# Add project root to Python path
sys.path.insert(0, os.getcwd())

from app.core.config import CONFIG
from app.db.connection import initialize_engine_and_session, get_db_connection
from app.db.db_seed import seed_all_data

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def initialize_database():
    """
    Initializes the database by running Alembic migrations to the latest version
    and then seeding it with initial data.
    """
    log.info("--- Database Initialization Started ---")

    # 1. Load configuration and initialize the engine
    if not CONFIG:
        log.error("Failed to load configuration. Aborting initialization.")
        return False

    # This sets up the engine that Alembic will use
    initialize_engine_and_session(CONFIG)

    # 2. Run Alembic migrations
    try:
        log.info("Running Alembic migrations to head...")
        # Path to alembic.ini
        alembic_cfg_path = os.path.join(os.getcwd(), 'alembic.ini')
        alembic_cfg = Config(alembic_cfg_path)

        # Tell Alembic to use our database connection URL from the config
        alembic_cfg.set_main_option('sqlalchemy.url', CONFIG['database_url'])

        command.upgrade(alembic_cfg, "head")
        log.info("Alembic migrations completed successfully.")
    except Exception as e:
        log.error(f"An error occurred during Alembic migrations: {e}", exc_info=True)
        return False

    # 3. Seed the database
    try:
        log.info("Seeding database with initial data...")
        db_session = get_db_connection()
        seed_all_data(db_session)
        db_session.close()
        log.info("Database seeding completed successfully.")
    except Exception as e:
        log.error(f"An error occurred during database seeding: {e}", exc_info=True)
        # We might have a partially seeded DB here, which could be problematic.
        # For a fresh setup, this might be okay. For rerunning, needs caution.
        return False

    log.info("--- Database Initialization Finished Successfully ---")
    return True

if __name__ == "__main__":
    if not initialize_database():
        sys.exit(1) # Exit with an error code if initialization fails
    sys.exit(0)
