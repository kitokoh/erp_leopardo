import logging
import sys
import os
from sqlalchemy.orm import Session

# Ensure the app's root directory is in the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.core.config import CONFIG
from app.db.connection import get_db_connection, set_db_config
from app.db.seeders.location_seeder import seed_all_locations
from app.db.seeders.role_permission_seeder import seed_roles_and_permissions
from app.db.seeders.user_seeder import seed_default_users
from app.db.seeders.initial_setup_seeder import seed_initial_setup
# Import other seeders as they are created
# from db.seeders.product_seeder import seed_products

def seed_all_data(db: Session):
    """
    Master seeding function that calls all individual seeder modules.
    It expects an already-created db session to be passed to it.
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting master data seeding process...")

    try:
        # Call seeders in a logical order
        seed_all_locations(db, logger)
        seed_roles_and_permissions(db, logger)
        seed_default_users(db, logger)
        seed_initial_setup(db, logger) # Add the call to the initial setup seeder
        # seed_products(db, logger)

        logger.info("Master data seeding process completed and committed successfully.")

    except Exception as e:
        logger.error(f"An error occurred during the master seeding process: {e}", exc_info=True)
        db.rollback()
        logger.info("Transaction rolled back.")
        raise # Re-raise the exception to notify the caller

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    print("Running database seeder script...")
    from app.db.connection import initialize_engine_and_session, get_db_connection
    set_db_config(CONFIG)
    initialize_engine_and_session(CONFIG)
    db_session = get_db_connection()
    try:
        seed_all_data(db_session)
    finally:
        db_session.close()
    print("Seeding process finished.")
