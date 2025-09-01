import os
import sys # Keep sys for sys.platform if needed elsewhere, but app_setup import logic removed
import sqlite3
import logging
from typing import Union

# Attempt to define project_root. This might need adjustment based on actual project structure.
# Assuming 'db' is a subdirectory of 'app', and 'app' is in the project root.
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# --- SQLAlchemy Setup ---
# Moved SQLAlchemy imports to the top as they are needed by get_db_connection's type hint and logic
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session # Added Session for type hinting

engine = None
SessionLocal = None # This will be populated by initialize_engine_and_session
Base = declarative_base()


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

def get_db_path() -> str:
    """
    Retrieves the database path from the centrally managed configuration.
    """
    if _db_config and 'database_path' in _db_config:
        return _db_config['database_path']

    # This is a critical failure. The config should always be set before this is called.
    logging.error("CRITICAL: get_db_path() was called before the database configuration was set via set_db_config().")
    # To prevent a crash in legacy code that might not initialize properly,
    # we can return a default, but this indicates a code flow problem.
    default_path = os.path.join(project_root, 'user_profile_data.db')
    logging.warning(f"Falling back to a default database path: {default_path}")
    return default_path

def get_raw_sqlite_connection(db_path_override=None) -> sqlite3.Connection:
    """
    Explicitly returns a raw sqlite3.Connection.
    Uses _db_config if set, otherwise relies on db_path_override.
    """
    global _db_config
    path_to_connect = db_path_override

    if not path_to_connect:
        if _db_config is None or _db_config.get('database_type') != 'sqlite':
            logging.critical(
                "CRITICAL: get_raw_sqlite_connection requires a db_path_override or a valid SQLite configuration via set_db_config()."
            )
            raise ValueError("Cannot establish raw SQLite connection without path or valid config.")
        path_to_connect = _db_config.get('database_path')
        if not path_to_connect:
            raise ValueError("SQLite database path not found in application configuration for raw connection.")

    logging.info(f"db.connection (get_raw_sqlite_connection): Attempting raw SQLite connection to absolute path: {os.path.abspath(path_to_connect)}")
    conn = sqlite3.connect(path_to_connect, timeout=10) # Added timeout
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def get_db_connection() -> Session:
    """
    Returns a new SQLAlchemy Session from the initialized SessionLocal.
    This is the single, centralized way to get a database session.
    It will raise an exception if the engine is not initialized.
    """
    if SessionLocal is None:
        logging.critical(
            "CRITICAL: get_db_connection() was called before the database engine was initialized. "
            "Please call initialize_engine_and_session() at application startup."
        )
        raise RuntimeError("Database session factory is not initialized.")

    db_session = SessionLocal()
    logging.info(f"db.connection: Providing new SQLAlchemy session from factory. Engine: {db_session.bind.url}")
    return db_session


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
            # Use the module-level project_root defined earlier
            if not os.path.isabs(database_path_for_engine) and project_root:
                 database_path_for_engine = os.path.join(project_root, database_path_for_engine)
            elif not os.path.isabs(database_path_for_engine):
                 # Fallback if project_root is None or path is relative and project_root couldn't be determined
                 logging.warning(f"db.connection: project_root not determined or path '{database_path_for_engine}' is relative. Assuming it's relative to CWD or needs to be absolute.")


            absolute_db_path = os.path.abspath(database_path_for_engine)

            if sys.platform == "win32" and absolute_db_path[1:3] == ":\\":
                engine_url = f"sqlite:///{absolute_db_path}"
            else:
                engine_url = f"sqlite:///{absolute_db_path}"

            logging.info(f"db.connection: SQLAlchemy engine connecting to absolute path: {absolute_db_path}")
            logging.info(f"db.connection: SQLAlchemy engine connecting to URL: {engine_url}")
            try:
                engine = create_engine(engine_url, connect_args={"check_same_thread": False, "timeout": 30}) # Increased timeout
                SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
                logging.info("db.connection: SQLAlchemy engine and SessionLocal created successfully for SQLite.")
            except Exception as e:
                logging.error(f"db.connection: Failed to create SQLAlchemy engine or SessionLocal: {e}", exc_info=True)
                # Removed resetting engine and SessionLocal to None on failure to allow retry or inspection.
                # engine = None
                # SessionLocal = None
                # Consider whether this is the desired behavior. If initialization fails, these will remain as they were or None.

    elif database_type_for_engine == 'postgresql':
        pg_host = app_config_param.get('postgresql_host', 'localhost')
        pg_port = app_config_param.get('postgresql_port', 5432)
        pg_user = app_config_param.get('postgresql_user')
        pg_password = app_config_param.get('postgresql_password')
        pg_dbname = app_config_param.get('postgresql_dbname')
        pg_ssl_mode = app_config_param.get('postgresql_ssl_mode', 'prefer')
        pg_ssl_rootcert = app_config_param.get('postgresql_ssl_rootcert')
        pg_ssl_clientcert = app_config_param.get('postgresql_ssl_clientcert')
        pg_ssl_clientkey = app_config_param.get('postgresql_ssl_clientkey')


        if not all([pg_user, pg_dbname]): # Password can be optional for some auth methods
            logging.error("db.connection: Missing PostgreSQL user or database name for SQLAlchemy engine setup.")
            return

        engine_url = f"postgresql+psycopg2://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_dbname}"

        connect_args = {}
        if pg_ssl_mode and pg_ssl_mode != 'disable':
            connect_args['sslmode'] = pg_ssl_mode
            if pg_ssl_rootcert:
                connect_args['sslrootcert'] = pg_ssl_rootcert
            if pg_ssl_clientcert:
                connect_args['sslcert'] = pg_ssl_clientcert
            if pg_ssl_clientkey:
                connect_args['sslkey'] = pg_ssl_clientkey

        logging.info(f"db.connection: SQLAlchemy engine connecting to PostgreSQL: {pg_user}@{pg_host}:{pg_port}/{pg_dbname} (SSL: {pg_ssl_mode})")
        try:
            engine = create_engine(engine_url, connect_args=connect_args)

            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            logging.info("db.connection: SQLAlchemy engine and SessionLocal created successfully for PostgreSQL.")
        except Exception as e:
            logging.error(f"db.connection: Failed to create SQLAlchemy engine or SessionLocal for PostgreSQL: {e}", exc_info=True)
            engine = None
            SessionLocal = None
    elif database_type_for_engine == 'sqlite' and not database_path_for_engine: # Ensure this else is for the sqlite condition
        logging.error("db.connection: 'database_path' not found in config for SQLAlchemy SQLite engine setup. ORM features unavailable.")
    else:
        # This 'else' now correctly pairs with the initial 'if/elif' for database_type_for_engine
        if database_type_for_engine not in ['sqlite', 'postgresql']:
            logging.warning(f"db.connection: SQLAlchemy engine setup not configured for database_type '{database_type_for_engine}'. ORM features might be limited.")

__all__ = ["get_db_connection", "engine", "SessionLocal", "Base", "initialize_engine_and_session"]
