import logging
import sys
import os
from sqlalchemy.orm import Session

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.core.config import CONFIG
from app.db.session_manager import session_manager
from app.db.seeders.location_seeder import seed_all_locations
from app.db.seeders.role_permission_seeder import seed_roles_and_permissions
from app.db.seeders.user_seeder import seed_default_users

def seed_all_data(db: Session):
    logger = logging.getLogger(__name__)
    logger.info("Starting master data seeding process...")

    try:
        seed_all_locations(db, logger)
        seed_roles_and_permissions(db, logger)
        seed_default_users(db, logger)
        logger.info("Master data seeding process completed.")
    except Exception as e:
        logger.error(f"An error occurred during the master seeding process: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    main_logger = logging.getLogger(__name__)
    print("Running database seeder script...")

    session_manager.initialize(CONFIG['database_url'])

    print("Seeding all data...")
    try:
        with session_manager.get_session() as db_session:
            seed_all_data(db_session)
        print("Seeding process finished successfully.")
    except Exception as e:
        print(f"Seeding process failed: {e}")
