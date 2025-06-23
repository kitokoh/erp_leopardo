import os
import sys
import sqlite3
import logging # Added for error logging

# Attempt to import app_setup, with a fallback mechanism for sys.path
try:
    import app_setup # Import app_setup directly
except ModuleNotFoundError:
    # This block provides a fallback if app_setup is not found,
    # which can happen if sys.path is not correctly configured by the entry point.
    # Calculate the project root relative to this file's location:
    # __file__ is db/connection.py
    # os.path.dirname(__file__) is db/
    # os.path.dirname(os.path.dirname(__file__)) is the project root (e.g., testpy/)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root_calculated = os.path.dirname(current_dir)

    if project_root_calculated not in sys.path:
        sys.path.insert(0, project_root_calculated)
        logging.warning(
            f"db.connection: Added '{project_root_calculated}' to sys.path to find 'app_setup'."
        )

    try:
        import app_setup # Retry import
    except ModuleNotFoundError as e_retry:
        logging.critical(
            "db.connection: CRITICAL - Failed to import 'app_setup' even after "
            f"attempting to add '{project_root_calculated}' to sys.path. Error: {e_retry}"
        )
        # Re-raise the original error or a new one to halt execution,
        # as app_setup is essential.
        raise ImportError(
            "Essential module 'app_setup' could not be imported. "
            "Please check Python path and project structure."
        ) from e_retry

# Removed try-except block for config import (original comment)
# Removed config_fallback class (original comment)

def get_db_connection(db_path_override=None):
    """
    Returns a new database connection object.
    Uses 'database_path' from the centralized app_setup.CONFIG by default.
    An optional db_path_override can be provided (e.g., for tests).
    """
    if db_path_override:
        path_to_connect = db_path_override
    else:
        if app_setup:
            app_config = app_setup.get_app_config()
            path_to_connect = app_config.get('database_path') # Used by SQLite and potentially others
            database_type = app_config.get('database_type', 'sqlite') # Default to 'sqlite' if not set
        else: # app_setup is not available, fall back to defaults or raise error if path not overridden
            logging.warning("db.connection: app_setup not available. Using default 'sqlite' type. Path must be overridden for non-test scenarios.")
            path_to_connect = None # Must be overridden by db_path_override
            database_type = 'sqlite'


        if not path_to_connect and database_type == 'sqlite' and not db_path_override: # Path is critical for SQLite if no override
            logging.critical(
                "CRITICAL: 'database_path' is missing or empty in the application configuration for SQLite, and no override was provided. "
                "This path is essential for SQLite database connectivity. "
                "Please check the configuration setup."
            )
            raise ValueError("SQLite database path not found in application configuration. Cannot establish connection.")

    if database_type == 'sqlite':
        if not path_to_connect: # Should be caught above if db_path_override is also None, but as a safeguard.
            raise ValueError("SQLite connection requires a valid database path.")
        conn = sqlite3.connect(path_to_connect)
        conn.row_factory = sqlite3.Row
        return conn
    elif database_type == 'postgresql':
        # --- PostgreSQL Connection (Not Implemented) ---
        # This section is reserved for PostgreSQL database connection logic.
        #
        # To implement PostgreSQL support:
        # 1. Install the PostgreSQL database driver:
        #    pip install psycopg2-binary (or psycopg2)
        # 2. Import the driver at the top of this file:
        #    import psycopg2
        # 3. Replace the NotImplementedError below with connection code.
        #
        # Required connection parameters (typically sourced from app_config):
        #   - host:     Hostname or IP address of the PostgreSQL server (e.g., app_config.get('db_host', 'localhost'))
        #   - port:     Port number (e.g., app_config.get('db_port', 5432))
        #   - user:     Database username (e.g., app_config.get('db_user'))
        #   - password: User's password (e.g., app_config.get('db_password'))
        #   - dbname:   Name of the database (e.g., app_config.get('db_name'))
        #
        # Example connection:
        #   try:
        #       conn = psycopg2.connect(
        #           host=app_config.get('db_host', 'localhost'),
        #           dbname=app_config.get('db_name'),
        #           user=app_config.get('db_user'),
        #           password=app_config.get('db_password'),
        #           port=int(app_config.get('db_port', 5432)) # Ensure port is an integer
        #       )
        #       # Optionally, set conn.row_factory or other session parameters
        #       return conn
        #   except psycopg2.Error as e:
        #       logging.error(f"PostgreSQL connection error: {e}")
        #       raise ConnectionError(f"Failed to connect to PostgreSQL database: {e}") # Or handle more gracefully
        #
        # The 'path_to_connect' variable (derived from 'database_path' in config) is typically
        # not used directly by PostgreSQL, as connection is usually via network parameters.
        raise NotImplementedError(
            "PostgreSQL connection not yet implemented. "
            "Please configure in db/connection.py within the 'postgresql' block and install the 'psycopg2' driver."
        )
    elif database_type == 'mysql':
        # --- MySQL Connection (Not Implemented) ---
        # This section is reserved for MySQL database connection logic.
        #
        # To implement MySQL support:
        # 1. Install the MySQL database driver:
        #    pip install mysql-connector-python
        # 2. Import the driver at the top of this file:
        #    import mysql.connector
        # 3. Replace the NotImplementedError below with connection code.
        #
        # Required connection parameters (typically sourced from app_config):
        #   - host:     Hostname or IP address of the MySQL server (e.g., app_config.get('db_host', 'localhost'))
        #   - port:     Port number (e.g., app_config.get('db_port', 3306))
        #   - user:     Database username (e.g., app_config.get('db_user'))
        #   - password: User's password (e.g., app_config.get('db_password'))
        #   - database: Name of the database (e.g., app_config.get('db_name'))
        #
        # Example connection:
        #   try:
        #       conn = mysql.connector.connect(
        #           host=app_config.get('db_host', 'localhost'),
        #           database=app_config.get('db_name'),
        #           user=app_config.get('db_user'),
        #           password=app_config.get('db_password'),
        #           port=int(app_config.get('db_port', 3306)) # Ensure port is an integer
        #       )
        #       # For MySQL with mysql-connector-python, to get dict-like rows (similar to sqlite3.Row):
        #       # cursor = conn.cursor(dictionary=True)
        #       # However, the connection object itself is returned here. Row factory is usually set on cursor.
        #       # This function is expected to return a connection object.
        #       # Adapting to a common row_factory pattern might require changes to how cursors are handled.
        #       return conn
        #   except mysql.connector.Error as e:
        #       logging.error(f"MySQL connection error: {e}")
        #       raise ConnectionError(f"Failed to connect to MySQL database: {e}") # Or handle more gracefully
        #
        # The 'path_to_connect' variable is typically not used directly by MySQL.
        raise NotImplementedError(
            "MySQL connection not yet implemented. "
            "Please configure in db/connection.py within the 'mysql' block and install the 'mysql-connector-python' driver."
        )
    else:
        raise ValueError(f"Unsupported database_type: '{database_type}'. Please check configuration.")

__all__ = ["get_db_connection"]
