import os
import sys # Keep sys for sys.platform if needed elsewhere, but app_setup import logic removed
import sqlite3
import logging
from typing import Union

# Attempt to define project_root. This might need adjustment based on actual project structure.
# Assuming 'db' is a subdirectory of the project root.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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

    logging.info(f"db.connection (get_raw_sqlite_connection): Attempting raw SQLite connection to: {path_to_connect}")
    conn = sqlite3.connect(path_to_connect, timeout=10) # Added timeout
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def get_db_connection(db_path_override=None) -> Union[sqlite3.Connection, Session]: # Modified return type hint
    """
    Returns a database connection object.
    If SQLAlchemy SessionLocal is initialized, it returns a SQLAlchemy Session.
    Otherwise, it falls back to the previous behavior (e.g., sqlite3.Connection).
    """
    global _db_config, SessionLocal # Ensure SessionLocal is accessible
    current_app_config_to_use = {}

    # Prioritize SQLAlchemy session if SessionLocal is available
    if SessionLocal:
        db_session = SessionLocal()
        # Log the engine URL associated with this SessionLocal to know which DB it's for
        if db_session.bind:
            logging.info(f"db.connection (get_db_connection - SQLAlchemy Session): Providing SQLAlchemy session linked to engine: {db_session.bind.url}")
        else:
            logging.warning("db.connection (get_db_connection - SQLAlchemy Session): SessionLocal is available but not bound to an engine.")
        return db_session

    # Fallback to original logic if SessionLocal is not initialized
    logging.warning("db.connection (get_db_connection - Fallback): SessionLocal not initialized. Falling back to raw connection. Ensure initialize_engine_and_session is called for ORM features.")

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
        # Log specifically for raw SQLite connection path
        logging.info(f"db.connection (get_db_connection - raw sqlite): Attempting to connect to SQLite DB at: {path_to_connect}")
        conn = sqlite3.connect(path_to_connect)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    elif database_type == 'postgresql':
        try:
            import psycopg2
        except ImportError:
            logging.critical("The 'psycopg2' library is required for PostgreSQL connections. Please install it (e.g., pip install psycopg2-binary).")
            raise ImportError("psycopg2 library not found. Needed for PostgreSQL connection.")

        pg_host = current_app_config_to_use.get('postgresql_host', 'localhost')
        pg_port = current_app_config_to_use.get('postgresql_port', 5432)
        pg_user = current_app_config_to_use.get('postgresql_user')
        pg_password = current_app_config_to_use.get('postgresql_password')
        pg_dbname = current_app_config_to_use.get('postgresql_dbname')
        pg_ssl_mode = current_app_config_to_use.get('postgresql_ssl_mode', 'prefer')
        pg_ssl_rootcert = current_app_config_to_use.get('postgresql_ssl_rootcert')
        pg_ssl_clientcert = current_app_config_to_use.get('postgresql_ssl_clientcert')
        pg_ssl_clientkey = current_app_config_to_use.get('postgresql_ssl_clientkey')


        if not pg_user or not pg_dbname: # Check if pg_user is defined before using
            logging.critical("PostgreSQL connection requires at least 'postgresql_user' and 'postgresql_dbname' in configuration.")
            raise ValueError("Missing PostgreSQL user or database name in configuration.")

        try:
            conn_params = {
                "dbname": pg_dbname,
                "user": pg_user, # pg_user is now guaranteed to be checked
                "password": pg_password,
                "host": pg_host,
                "port": pg_port,
                "sslmode": pg_ssl_mode
            }
            if pg_ssl_mode not in ['disable', 'allow', 'prefer']: # Modes that might need certs
                if pg_ssl_rootcert:
                    conn_params["sslrootcert"] = pg_ssl_rootcert
                if pg_ssl_clientcert:
                    conn_params["sslcert"] = pg_ssl_clientcert
                if pg_ssl_clientkey:
                    conn_params["sslkey"] = pg_ssl_clientkey

            logging.info(f"Attempting PostgreSQL connection to {pg_host}:{pg_port}/{pg_dbname} with SSL mode: {pg_ssl_mode}")
            conn = psycopg2.connect(**conn_params)
            logging.info(f"Successfully connected to PostgreSQL database '{pg_dbname}' on {pg_host}:{pg_port} (SSL: {pg_ssl_mode})")
            return conn
        except psycopg2.OperationalError as op_err:
            logging.error(f"PostgreSQL OperationalError during connection: {op_err}")
            raise ConnectionError(f"Erreur opérationnelle PostgreSQL: {op_err}") from op_err
        except psycopg2.Error as e: # Catch other psycopg2 errors
            logging.error(f"Unable to connect to PostgreSQL database (psycopg2.Error): {e}")
            raise Exception(f"Erreur de connexion PostgreSQL générique: {e}") from e

    elif database_type == 'mysql':
        raise NotImplementedError("MySQL connection not yet implemented.")
    else:
        raise ValueError(f"Unsupported database_type: '{database_type}'. Please check configuration.")


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

            logging.info(f"db.connection: SQLAlchemy engine connecting to: {engine_url}")
            try:
                engine = create_engine(engine_url, connect_args={"check_same_thread": False, "timeout": 10}) # Increased timeout
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
