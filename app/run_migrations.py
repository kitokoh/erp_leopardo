import logging
import sys
import os
from pathlib import Path

# The script is now inside 'app', so we need to adjust paths accordingly.
# The project root is one level up.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

from app.core.config import CONFIG
from alembic.config import Config
from alembic import command

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def main():
    log.info("Creating Alembic config...")
    # alembic.ini is in the project root
    alembic_ini_path = os.path.join(PROJECT_ROOT, 'alembic.ini')
    alembic_cfg = Config(alembic_ini_path)

    alembic_cfg.set_main_option("script_location", "migrations")


    log.info(f"Setting database URL to: {CONFIG['database_url']}")
    alembic_cfg.set_main_option("sqlalchemy.url", CONFIG['database_url'])


    log.info("Running Alembic revision to generate new migration script...")
    try:
        command.revision(
            alembic_cfg, message="Add missing tables and columns", autogenerate=True
        )
        log.info("Revision script generated successfully (check the versions folder).")
    except Exception as e:
        log.warning(f"Could not create revision. This might be okay if no schema changes were detected. Error: {e}")


    log.info("Applying all migrations to upgrade the database to the latest version...")
    try:
        command.upgrade(alembic_cfg, "head")
        log.info("Database migration upgrade completed successfully.")
    except Exception as e:
        log.error(f"Failed to apply migrations: {e}", exc_info=True)


if __name__ == "__main__":
    main()
