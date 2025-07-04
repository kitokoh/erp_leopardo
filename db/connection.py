import os
import sys # Keep sys for sys.platform if needed elsewhere, but app_setup import logic removed
import sqlite3
import logging

# Module-level configuration placeholder
_db_config = None

def set_db_config(config):
    """
    Sets the database configuration for this module.
    This function should be called once at application startup.
    """
    global _db_config
    if _db_config is not None:
        logging.warning("db.connection.set_db_config called multiple times.")
    _db_config = config
    logging.info("db.connection: Database configuration has been set.")

def get_db_connection(db_path_override=None):
    """
    Returns a new database connection object.
    Uses 'database_path' from the centrally set configuration.
    An optional db_path_override can be provided (e.g., for tests).
    """
    global _db_config
    current_app_config_to_use = {}

    if db_path_override:
        path_to_connect = db_path_override
        database_type = 'sqlite' # Assuming override is for SQLite for now
        # No app_config needed if path is overridden directly
    else:
        if _db_config is None:
            logging.critical(
                "CRITICAL: Database configuration not set in db.connection. Call set_db_config() first."
            )
            raise ValueError("Database configuration not set. Cannot establish connection.")

        current_app_config_to_use = _db_config
        path_to_connect = current_app_config_to_use.get('database_path')
        database_type = current_app_config_to_use.get('database_type', 'sqlite')

        if not path_to_connect and database_type == 'sqlite':
            logging.critical(
                "CRITICAL: 'database_path' is missing or empty in the application configuration for SQLite, and no override was provided."
            )
            raise ValueError("SQLite database path not found in application configuration. Cannot establish connection.")

    if database_type == 'sqlite':
        if not path_to_connect: # Should be caught above if not overridden, but double check
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
