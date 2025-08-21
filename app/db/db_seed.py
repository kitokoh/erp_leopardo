import logging
import sys
import os

# Ensure the app's root directory is in the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.core.config import CONFIG
from app.db.connection import get_db_connection, set_db_config
from app.db.seeders.location_seeder import seed_all_locations
from app.db.seeders.role_permission_seeder import seed_roles_and_permissions
from app.db.seeders.user_seeder import seed_default_users
# Import other seeders as they are created
# from db.seeders.product_seeder import seed_products

def seed_all_data():
    """
    Master seeding function that calls all individual seeder modules.
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting master data seeding process...")

    # Set the database configuration before trying to connect
    set_db_config(CONFIG)

    db = None  # Initialize db to None
    try:
        db = get_db_connection()

        # Call seeders in a logical order
        seed_all_locations(db, logger)
        seed_roles_and_permissions(db, logger)
        seed_default_users(db, logger)
        # seed_products(db, logger)

        logger.info("Master data seeding process completed and committed successfully.")

    except Exception as e:
        logger.error(f"An error occurred during the master seeding process: {e}", exc_info=True)
        if db:
            db.rollback()
            logger.info("Transaction rolled back.")
    finally:
        if db:
            db.close()
            logger.info("Database connection closed.")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    print("Running database seeder script...")
    seed_all_data()
    print("Seeding process finished.")
