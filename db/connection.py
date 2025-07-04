import os
import sys
import sqlite3
import logging

# Add the project root to sys.path to allow importing app_setup
# This should be the primary sys.path modification for this file's needs.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
elif sys.path[0] != project_root: # If already in path, ensure it's at the front
    try:
        sys.path.remove(project_root)
    except ValueError:
        pass # Should not happen if 'in' check would have been true
    sys.path.insert(0, project_root)

# Diagnostic print: Check if app_setup is already in sys.modules and what it is
if 'app_setup' in sys.modules:
    print(f"DEBUG db.connection: 'app_setup' already in sys.modules BEFORE local import. __file__ = {getattr(sys.modules['app_setup'], '__file__', 'N/A')}")
else:
    print("DEBUG db.connection: 'app_setup' NOT in sys.modules before local import.")

import app_setup # Import app_setup directly

# Diagnostic print: After import, what is app_setup?
print(f"DEBUG db.connection: After local import, app_setup.__file__ = {getattr(app_setup, '__file__', 'N/A')}")
print(f"DEBUG db.connection: After local import, attributes in app_setup: {dir(app_setup)}")

# This check ensures the correct app_setup was imported
if not hasattr(app_setup, 'get_app_config'): # Check for a known essential attribute
    logging.critical(f"db.connection: Imported 'app_setup' from {getattr(app_setup, '__file__', 'Unknown location')} does not have 'get_app_config'. This is a fatal error.")
    raise ImportError("db.connection: Failed to import the correct 'app_setup' module with expected attributes.")

def get_db_connection(db_path_override=None):
    """
    Returns a new database connection object.
    Uses 'database_path' from the centralized app_setup.CONFIG by default.
    An optional db_path_override can be provided (e.g., for tests).
    """
    if db_path_override:
        path_to_connect = db_path_override
        # database_type is not determined here, assuming SQLite for override if not specified
        # This could be enhanced if overrides need to specify type
        database_type = 'sqlite'
        current_app_config = {} # Default to empty dict if using override without full config
    else:
        # Access app_setup here, assuming it's fully loaded by runtime.
        current_app_config = app_setup.get_app_config() # Call when needed
        path_to_connect = current_app_config.get('database_path')
        database_type = current_app_config.get('database_type', 'sqlite')

        if not path_to_connect and database_type == 'sqlite': # Path is critical for SQLite
            logging.critical(
                "CRITICAL: 'database_path' is missing or empty in the application configuration for SQLite, and no override was provided."
            )
            raise ValueError("SQLite database path not found in application configuration. Cannot establish connection.")

    if database_type == 'sqlite':
        if not path_to_connect:
            raise ValueError("SQLite connection requires a valid database path.")
        conn = sqlite3.connect(path_to_connect)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    elif database_type == 'postgresql':
        raise NotImplementedError("PostgreSQL connection not yet implemented.")
    elif database_type == 'mysql':
        raise NotImplementedError("MySQL connection not yet implemented.")
    else:
        raise ValueError(f"Unsupported database_type: '{database_type}'. Please check configuration.")

# --- SQLAlchemy Setup ---
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = None
SessionLocal = None
Base = declarative_base()

# This function will be called from main.py after config is loaded and app_setup is fully initialized
def initialize_engine_and_session(app_config_param):
    global engine, SessionLocal, project_root # Allow modification of module-level globals

    if not app_config_param:
        logging.error("db.connection.initialize_engine_and_session: app_config_param is missing. Cannot initialize SQLAlchemy engine.")
        return

    database_path_for_engine = app_config_param.get('database_path')
    database_type_for_engine = app_config_param.get('database_type', 'sqlite')

    if database_type_for_engine == 'sqlite':
        if database_path_for_engine:
            # 'project_root' is defined at the top of this file
            if not os.path.isabs(database_path_for_engine) and project_root:
                 database_path_for_engine = os.path.join(project_root, database_path_for_engine)

            absolute_db_path = os.path.abspath(database_path_for_engine)

            if sys.platform == "win32" and absolute_db_path[1:3] == ":\\":
                engine_url = f"sqlite:///{absolute_db_path}"
            else:
                engine_url = f"sqlite:///{absolute_db_path}"

            logging.info(f"db.connection: SQLAlchemy engine connecting to: {engine_url}")
            try:
                engine = create_engine(engine_url, connect_args={"check_same_thread": False})
                SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
                logging.info("db.connection: SQLAlchemy engine and SessionLocal created successfully for SQLite.")
            except Exception as e:
                logging.error(f"db.connection: Failed to create SQLAlchemy engine or SessionLocal: {e}", exc_info=True)
                engine = None
                SessionLocal = None
        else:
            logging.error("db.connection: 'database_path' not found in config for SQLAlchemy SQLite engine setup. ORM features unavailable.")
    else:
        logging.warning(f"db.connection: SQLAlchemy engine setup not configured for database_type '{database_type_for_engine}'. ORM features might be limited.")

__all__ = ["get_db_connection", "engine", "SessionLocal", "Base", "initialize_engine_and_session"]
