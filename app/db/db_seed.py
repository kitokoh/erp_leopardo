import logging
from db.connection import get_db_connection
from db.seeders.location_seeder import seed_all_locations
from db.seeders.role_permission_seeder import seed_roles_and_permissions
# Import other seeders as they are created
# from db.seeders.product_seeder import seed_products

def seed_all_data():
    """
    Master seeding function that calls all individual seeder modules.
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting master data seeding process...")

    try:
        conn = get_db_connection()

        # Call seeders in a logical order
        seed_all_locations(conn, logger)
        seed_roles_and_permissions(conn, logger)
        # seed_products(conn, logger)

        conn.commit()
        logger.info("Master data seeding process completed and committed successfully.")

    except Exception as e:
        logger.error(f"An error occurred during the master seeding process: {e}", exc_info=True)
        if 'conn' in locals() and conn:
            conn.rollback()
            logger.info("Transaction rolled back.")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            logger.info("Database connection closed.")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    seed_all_data()
