import os
import sys
import sqlite3
import logging

# Add the project root to sys.path to allow importing app_setup
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import app_setup # Import app_setup directly

# The following block attempting to import app_setup seems to be an older version or a mismerge.
# The current sys.path manipulation and import is handled above and then checked below.
# _APP_SETUP_IMPORTED = False
# try:
#     import app_setup # Initial import attempt
#     _APP_SETUP_IMPORTED = True
# except ImportError as e_initial:
#     logging.warning(f"db.connection: Initial import of 'app_setup' failed: {e_initial}. Attempting path adjustment.")
#     _project_root_db_conn = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')) # Adjusted to be project root from db/
#     original_sys_path = list(sys.path) # Keep a copy for reference if needed

#     path_manipulation_done = False
#     if _project_root_db_conn not in sys.path:
#         sys.path.insert(0, _project_root_db_conn)
#         logging.warning(
#             f"db.connection: Added '{_project_root_db_conn}' to sys.path to find 'app_setup'."
#         )
#         path_manipulation_done = True
#     elif sys.path[0] != _project_root_db_conn:
#         # It's in sys.path, but not at the front. This is a less common case to handle defensively.
#         try:
#             sys.path.remove(_project_root_db_conn)
#         except ValueError:
#             pass # Should not happen if 'in' check passed, but defensive
#         sys.path.insert(0, _project_root_db_conn)
#         logging.warning(
#             f"db.connection: Moved '{_project_root_db_conn}' to sys.path[0] to find 'app_setup'."
#         )
#         path_manipulation_done = True

#     if path_manipulation_done or (sys.path[0] == _project_root_db_conn) : # Try importing if path was changed or if it was already correct
#         try:
#             import app_setup # Retry import
#             _APP_SETUP_IMPORTED = True
#         except ModuleNotFoundError as e_retry:
#             logging.critical(
#                 "db.connection: CRITICAL - Failed to import 'app_setup' after sys.path adjustment. "
#                 f"Path: '{_project_root_db_conn}', Error: {e_retry}. Sys.path was: {original_sys_path}, now: {sys.path}"
#             )
#             # Restore sys.path if we changed it and failed, to minimize side effects, though system is likely unstable.
#             if path_manipulation_done:
#                  sys.path = original_sys_path
#             raise ImportError(
#                 "Essential module 'app_setup' could not be imported by db.connection. "
#                 "Please check Python path and project structure."
#             ) from e_retry
#     else: # Should not be reached if logic is correct, means path was not manipulated and not already correct.
#         logging.critical(
#             "db.connection: CRITICAL - Project root '{_project_root_db_conn}' was not added to sys.path and app_setup initially failed. This indicates a logic error in db.connection's path setup."
#         )
#         raise ImportError("Essential module 'app_setup' could not be imported due to path setup logic error in db.connection.")

# This check ensures app_setup was imported, relying on the sys.path modification at the top of the file.
if 'app_setup' not in sys.modules:
    logging.critical("db.connection: 'app_setup' module was not successfully imported. This is a fatal error for database configuration.")
    raise ImportError("db.connection: Failed to make 'app_setup' available.")

# Module-level variable for test database path override
_TEST_DB_PATH_OVERRIDE = None

def set_test_db_path_override(path: str):
    """Sets the database path override for testing purposes."""
    global _TEST_DB_PATH_OVERRIDE
    _TEST_DB_PATH_OVERRIDE = path
    logging.info(f"Test DB path override set to: {path}")

def clear_test_db_path_override():
    """Clears the database path override for testing."""
    global _TEST_DB_PATH_OVERRIDE
    _TEST_DB_PATH_OVERRIDE = None
    logging.info("Test DB path override cleared.")

def get_db_connection(db_path_override=None):
    """
    Returns a new database connection object.
    Priority for path:
    1. Explicit db_path_override argument.
    2. Module-level _TEST_DB_PATH_OVERRIDE (if set).
    3. 'database_path' from the centralized app_setup.CONFIG.
    """
    global _TEST_DB_PATH_OVERRIDE
    path_to_connect = None
    database_type = 'sqlite' # Default, will be updated from config if possible

    if db_path_override:
        path_to_connect = db_path_override
        # If path is overridden, we assume it's SQLite for testing unless specified otherwise
        # Or, we could try to infer type from app_config if override is just for path
        if app_setup:
            app_config_temp = app_setup.get_app_config()
            database_type = app_config_temp.get('database_type', 'sqlite')

    elif _TEST_DB_PATH_OVERRIDE:
        path_to_connect = _TEST_DB_PATH_OVERRIDE
        # Same assumption as above for database_type
        if app_setup:
            app_config_temp = app_setup.get_app_config()
            database_type = app_config_temp.get('database_type', 'sqlite')
    else:
        if app_setup:
            app_config = app_setup.get_app_config()
            path_to_connect = app_config.get('database_path')
            database_type = app_config.get('database_type', 'sqlite')
        else:
            logging.warning("db.connection: app_setup not available. Using default 'sqlite' type. Path must be determined by override or test override.")
            # path_to_connect remains None, database_type is 'sqlite'
            # This state should be problematic if not using an override, caught below.

    if not path_to_connect and database_type == 'sqlite': # Path is critical for SQLite
        logging.critical(
            "CRITICAL: SQLite database path could not be determined. "
            "Checked explicit override, test override, and application configuration. "
            "Please ensure one of these provides a valid path for SQLite."
        )
        raise ValueError("SQLite database path not found. Cannot establish connection.")

    if database_type == 'sqlite':
        # path_to_connect should be valid here due to the check above for sqlite
        conn = sqlite3.connect(path_to_connect, timeout=10) # Increased timeout for busy DB
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;") # Enforce foreign key constraints
        conn.execute("PRAGMA busy_timeout = 5000;") # Wait 5 seconds if DB is locked
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
