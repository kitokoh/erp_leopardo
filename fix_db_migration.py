import os
from alembic.config import Config
from alembic import command
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def main():
    """
    Stamps the database to the latest revision and autogenerates a new migration
    to resolve inconsistencies between the database schema and the models.
    """
    try:
        # Get the absolute path to the alembic.ini file
        # This script assumes it is run from the root of the project
        ini_path = os.path.join(os.path.dirname(__file__), 'alembic.ini')
        log.info(f"Using alembic.ini from: {ini_path}")

        if not os.path.exists(ini_path):
            log.error("alembic.ini not found. Please run this script from the project root.")
            return

        # Create an Alembic configuration object
        alembic_cfg = Config(ini_path)

        # 1. Stamp the database to the 'head' revision
        log.info("Stamping the database to the 'head' revision...")
        command.stamp(alembic_cfg, "head")
        log.info("Database successfully stamped.")

        # 2. Autogenerate a new migration
        log.info("Autogenerating a new migration file...")
        command.revision(alembic_cfg, autogenerate=True, message="Autogenerate new migration after stamping")
        log.info("New migration file generated successfully.")

        log.info("\nMigration fix applied. You can now try running the application again.")
        log.info("If the new migration file was created, you may want to review it and commit it to your version control.")

    except Exception as e:
        log.error(f"An error occurred: {e}")
        log.error("Please ensure that your database is running and accessible.")

if __name__ == "__main__":
    main()
