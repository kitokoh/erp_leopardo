import os
import sys
import logging
import sqlite3

# Adjust sys.path to ensure project root is included
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app_setup import CONFIG
from db import connection as db_connection_module

# Import the new seeder modules
from db.seeders.location_seeder import seed_all_locations
from db.seeders.role_permission_seeder import seed_roles_and_permissions
from db.seeders.user_seeder import seed_default_users
from db.seeders.template_seeder import seed_all_templates
from db.seeders.motivational_message_seeder import seed_motivational_messages
from db.seeders.initial_setup_seeder import seed_initial_setup
from db.seeders.hidroguc_product_seeder import seed_hidroguc_products


def run_seed():
    """
    Orchestrates the entire database seeding process by calling individual seeders in order.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"--- Starting Database Seeding Process for: {CONFIG.get('database_path')} ---")

    # Phase 1: Raw SQLite Connection for seeders that use it.
    raw_conn = None
    try:
        raw_conn = db_connection_module.get_raw_sqlite_connection()
        if not raw_conn:
            logger.critical("Failed to get a raw SQLite connection. Aborting seed.")
            return

        # Set row_factory for dictionary-like access
        raw_conn.row_factory = sqlite3.Row

        # Call seeders that depend on the raw connection
        seed_roles_and_permissions(raw_conn, logger)
        seed_default_users(raw_conn, logger)
        seed_all_locations(raw_conn, logger)
        seed_all_templates(raw_conn, logger)
        seed_motivational_messages(raw_conn, logger)
        seed_initial_setup(raw_conn, logger)

        raw_conn.commit()
        logger.info("Raw SQL seeding phase committed successfully.")

    except Exception as e:
        logger.error(f"Error during raw SQL seeding phase: {e}", exc_info=True)
        if raw_conn:
            raw_conn.rollback()
    finally:
        if raw_conn:
            raw_conn.close()
            logger.info("Raw SQLite connection for seeding closed.")

    # Phase 2: SQLAlchemy Session for seeders that use the ORM.
    try:
        logger.info("Attempting SQLAlchemy-based seeding...")
        if not db_connection_module.engine:
            from db.connection import initialize_engine_and_session
            initialize_engine_and_session(CONFIG)

        if db_connection_module.engine:
            from sqlalchemy.orm import Session
            with Session(db_connection_module.engine) as session:
                # Add any SQLAlchemy-based seeders here
                seed_hidroguc_products(session, logger)
                # _seed_accounting_data(session, logger) # Example if you create this seeder
                session.commit()
            logger.info("SQLAlchemy-based seeding phase completed and committed.")
        else:
            logger.error("SQLAlchemy engine (db.connection.engine) not initialized. Skipping SQLAlchemy seeding.")

    except Exception as e_sqla_seed:
        logger.error(f"Error during SQLAlchemy-based seeding phase: {e_sqla_seed}", exc_info=True)

    logger.info("--- Full Seeding Process Completed ---")


def seed_only_hidroguc_products():
    """
    Seeds only the HİDROGÜÇ PRES products without running the full initial data seeding.
    This is useful for development or specific data-loading tasks.
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting HİDROGÜÇ PRES products specific seeding.")

    try:
        if not db_connection_module.engine:
            from db.connection import initialize_engine_and_session
            initialize_engine_and_session(CONFIG)

        from sqlalchemy.orm import Session
        with Session(db_connection_module.engine) as session:
            seed_hidroguc_products(session, logger)
            session.commit()
        logger.info("HİDROGÜÇ PRES products specific seeding committed successfully.")
    except Exception as e:
        logger.error(f"Error during HİDROGÜÇ PRES products specific seeding: {e}", exc_info=True)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    main_logger = logging.getLogger(__name__)

    main_logger.info("Ensuring database schema is initialized before seeding...")
    from db.init_schema import initialize_database
    try:
        initialize_database(CONFIG)
        main_logger.info("Database schema initialization check complete.")
        run_seed()
    except Exception as e_main:
        main_logger.critical(f"Critical error during __main__ execution of db_seed: {e_main}", exc_info=True)
