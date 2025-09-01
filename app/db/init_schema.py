import logging
import os

def initialize_database(app_config):
    """
    Ensures the directory for the database file exists.
    Table creation and data seeding are now handled by Alembic and db_seed.py respectively.
    """
    if not app_config or 'database_path' not in app_config:
        logging.critical("initialize_database called without valid app_config or database_path. Aborting.")
        raise ValueError("app_config with database_path is required for initialize_database.")

    database_path = app_config['database_path']
    db_dir = os.path.dirname(database_path)

    if db_dir and not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir, exist_ok=True)
            logging.info(f"Created directory for database: {db_dir}")
        except OSError as e:
            logging.error(f"Failed to create database directory {db_dir}: {e}")
            raise
    else:
        logging.info(f"Database directory {db_dir} already exists or is not specified.")

if __name__ == '__main__':
    # This block is for standalone testing of this script, if needed.
    # It's not used by the main application flow.
    print("Running init_schema.py directly for testing purposes.")
    mock_config = {
        "database_path": "test_init_schema.db"
    }
    if os.path.exists(mock_config["database_path"]):
        os.remove(mock_config["database_path"])
        print(f"Removed old test database: {mock_config['database_path']}")

    initialize_database(mock_config)
    print("initialize_database function executed successfully.")
    # Verify directory creation if db path was nested, e.g., "db/test.db"
    # For now, it just ensures no crash.