# db/cruds/roles_crud.py
import sqlite3
import logging
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine, Connection as SQLAlchemyConnection
from sqlalchemy.sql import text as sqlalchemy_text
from sqlalchemy.exc import SQLAlchemyError

from .generic_crud import _manage_conn # Assuming generic_crud provides this decorator

logger = logging.getLogger(__name__)

# Helper functions (similar to users_crud.py, consider moving to a shared util if widely used)
def _get_cursor_and_dialect(conn):
    """Determines if conn is SQLAlchemy or raw sqlite3 and returns appropriate object/dialect string."""
    if isinstance(conn, (Session, Engine, SQLAlchemyConnection)):
        return conn, "sqlalchemy"
    elif hasattr(conn, 'cursor'): # Check for raw DBAPI connection (like sqlite3.Connection)
        return conn.cursor(), "sqlite" # Return the cursor for sqlite
    logger.warning(f"Unsupported connection type: {type(conn)} in _get_cursor_and_dialect.")
    return None, None

def _execute_query(db_obj, sql_query, params, dialect, logger_to_use=None):
    """Executes a query using the appropriate method based on dialect."""
    current_logger = logger_to_use if logger_to_use else logger
    try:
        if dialect == "sqlalchemy":
            # db_obj is SA Session/Engine/Connection
            return db_obj.execute(sql_query, params)
        elif dialect == "sqlite":
            # db_obj is sqlite3.Cursor
            return db_obj.execute(sql_query, params)
        else:
            current_logger.error(f"Unsupported dialect '{dialect}' in _execute_query.")
            return None
    except (sqlite3.Error, SQLAlchemyError) as e:
        current_logger.error(f"Database error in _execute_query (dialect: {dialect}): {e}", exc_info=True)
        raise # Re-raise to be caught by calling function or @_manage_conn

def _fetch_one_as_dict(db_obj, sql_query, params, dialect, logger_to_use=None):
    """Fetches a single row as a dictionary based on dialect."""
    current_logger = logger_to_use if logger_to_use else logger
    try:
        row_data = None
        if dialect == "sqlalchemy":
            result = db_obj.execute(sql_query, params)
            row = result.fetchone()
            if row: row_data = dict(row._mapping)
        elif dialect == "sqlite":
            db_obj.execute(sql_query, params) # db_obj is a cursor here
            row = db_obj.fetchone()
            if row:
                column_names = [desc[0] for desc in db_obj.description]
                row_data = dict(zip(column_names, row))
        return row_data
    except (sqlite3.Error, SQLAlchemyError) as e:
        current_logger.error(f"Database error in _fetch_one_as_dict (dialect: {dialect}): {e}", exc_info=True)
        return None # Or re-raise, depending on desired error handling

def _fetch_all_as_dict_list(db_obj, sql_query, params, dialect, logger_to_use=None):
    """Fetches all rows as a list of dictionaries based on dialect."""
    current_logger = logger_to_use if logger_to_use else logger
    try:
        rows_data = []
        if dialect == "sqlalchemy":
            result = db_obj.execute(sql_query, params)
            for row in result.fetchall():
                rows_data.append(dict(row._mapping))
        elif dialect == "sqlite":
            db_obj.execute(sql_query, params) # db_obj is a cursor here
            rows = db_obj.fetchall()
            if rows:
                column_names = [desc[0] for desc in db_obj.description]
                for row_item in rows: # Renamed row to row_item to avoid conflict
                    rows_data.append(dict(zip(column_names, row_item)))
        return rows_data
    except (sqlite3.Error, SQLAlchemyError) as e:
        current_logger.error(f"Database error in _fetch_all_as_dict_list (dialect: {dialect}): {e}", exc_info=True)
        return [] # Or re-raise


@_manage_conn
def add_role(role_name: str, description: str = None, conn=None) -> int | None:
    """Adds a new role to the Roles table."""
    sql_sqlite = "INSERT INTO Roles (role_name, description) VALUES (?, ?)"
    sql_sa = sqlalchemy_text("INSERT INTO Roles (role_name, description) VALUES (:role_name, :description)")

    params_sqlite = (role_name, description)
    params_sa = {"role_name": role_name, "description": description}

    db_obj, dialect = _get_cursor_and_dialect(conn)
    if not db_obj or not dialect:
        logger.error(f"Unsupported connection type in add_role: {type(conn)}")
        return None

    try:
        result = _execute_query(db_obj, sql_sa if dialect == "sqlalchemy" else sql_sqlite,
                                params_sa if dialect == "sqlalchemy" else params_sqlite, dialect)

        last_id = None
        if dialect == "sqlalchemy":
            # For SQLAlchemy with SQLite, result.lastrowid should work.
            # For other DBs, this might need adjustment or might not be standard.
            if result and hasattr(result, 'lastrowid'):
                last_id = result.lastrowid
        elif dialect == "sqlite":
             # db_obj is a cursor here
            if result and hasattr(result, 'lastrowid'): # result is the cursor itself from _execute_query
                last_id = result.lastrowid


        if last_id is not None:
            logger.info(f"Role '{role_name}' added successfully with ID {last_id}.")
            return last_id
        else: # Should not happen if insert is successful and lastrowid is supported
            logger.warning(f"Role '{role_name}' added but could not retrieve lastrowid.")
            return None # Or some other indicator of partial success/failure

    except (sqlite3.IntegrityError, SQLAlchemyError) as e: # SQLAlchemyError might wrap IntegrityError
        if isinstance(e, SQLAlchemyError) and isinstance(e.orig, sqlite3.IntegrityError): # Unwrap for SA
             logger.error(f"Role '{role_name}' already exists (SA).")
        elif isinstance(e, sqlite3.IntegrityError):
             logger.error(f"Role '{role_name}' already exists (SQLite).")
        else: # Other SQLAlchemyError
            logger.error(f"Database error adding role '{role_name}': {e}", exc_info=True)
        return None
    except (sqlite3.Error, SQLAlchemyError) as e: # Catch broader errors
        logger.error(f"General database error adding role '{role_name}': {e}", exc_info=True)
        return None


@_manage_conn
def get_role_by_id(role_id: int, conn=None) -> dict | None:
    """Fetches a role by its ID."""
    sql_sqlite = "SELECT * FROM Roles WHERE role_id = ?"
    sql_sa = sqlalchemy_text("SELECT * FROM Roles WHERE role_id = :role_id")

    params_sqlite = (role_id,)
    params_sa = {"role_id": role_id}

    db_obj, dialect = _get_cursor_and_dialect(conn)
    if not db_obj or not dialect:
        logger.error(f"Unsupported connection type in get_role_by_id: {type(conn)}")
        return None

    return _fetch_one_as_dict(db_obj, sql_sa if dialect == "sqlalchemy" else sql_sqlite,
                              params_sa if dialect == "sqlalchemy" else params_sqlite, dialect, logger)


@_manage_conn
def get_role_by_name(role_name: str, conn=None) -> dict | None:
    """Fetches a role by its name."""
    sql_sqlite = "SELECT * FROM Roles WHERE role_name = ?"
    sql_sa = sqlalchemy_text("SELECT * FROM Roles WHERE role_name = :role_name")

    params_sqlite = (role_name,)
    params_sa = {"role_name": role_name}

    db_obj, dialect = _get_cursor_and_dialect(conn)
    if not db_obj or not dialect:
        logger.error(f"Unsupported connection type in get_role_by_name: {type(conn)}")
        return None

    return _fetch_one_as_dict(db_obj, sql_sa if dialect == "sqlalchemy" else sql_sqlite,
                              params_sa if dialect == "sqlalchemy" else params_sqlite, dialect, logger)


@_manage_conn
def list_roles(conn=None) -> list[dict]:
    """Lists all roles."""
    sql_common = "SELECT * FROM Roles ORDER BY role_name"
    sql_sqlite = sql_common
    sql_sa = sqlalchemy_text(sql_common)

    # No parameters for this query
    params_sqlite = ()
    params_sa = {}

    db_obj, dialect = _get_cursor_and_dialect(conn)
    if not db_obj or not dialect:
        logger.error(f"Unsupported connection type in list_roles: {type(conn)}")
        return []

    return _fetch_all_as_dict_list(db_obj, sql_sa if dialect == "sqlalchemy" else sql_sqlite,
                                   params_sa if dialect == "sqlalchemy" else params_sqlite, dialect, logger)


@_manage_conn
def update_role(role_id: int, role_name: str, description: str = None, conn=None) -> bool:
    """Updates an existing role's name and description."""
    sql_sqlite = "UPDATE Roles SET role_name = ?, description = ? WHERE role_id = ?"
    sql_sa = sqlalchemy_text("UPDATE Roles SET role_name = :role_name, description = :description WHERE role_id = :role_id")

    params_sqlite = (role_name, description, role_id)
    params_sa = {"role_name": role_name, "description": description, "role_id": role_id}

    db_obj, dialect = _get_cursor_and_dialect(conn)
    if not db_obj or not dialect:
        logger.error(f"Unsupported connection type in update_role: {type(conn)}")
        return False

    try:
        result = _execute_query(db_obj, sql_sa if dialect == "sqlalchemy" else sql_sqlite,
                                params_sa if dialect == "sqlalchemy" else params_sqlite, dialect)
        if result and result.rowcount > 0:
            logger.info(f"Role ID {role_id} updated to name '{role_name}'.")
            return True
        logger.warning(f"Role ID {role_id} not found for update or no change made.")
        return False
    except (sqlite3.IntegrityError, SQLAlchemyError) as e:
        # Handle potential wrapped IntegrityError from SQLAlchemy
        original_error = getattr(e, 'orig', e)
        if isinstance(original_error, sqlite3.IntegrityError):
             logger.error(f"Update failed for role ID {role_id}: New role name '{role_name}' might already exist (IntegrityError).")
        else:
            logger.error(f"Database error updating role ID {role_id}: {e}", exc_info=True)
        return False
    except (sqlite3.Error, SQLAlchemyError) as e:
        logger.error(f"General database error updating role ID {role_id}: {e}", exc_info=True)
        return False


@_manage_conn
def delete_role(role_id: int, conn=None) -> bool:
    """Deletes a role by its ID."""
    sql_sqlite = "DELETE FROM Roles WHERE role_id = ?"
    sql_sa = sqlalchemy_text("DELETE FROM Roles WHERE role_id = :role_id")

    params_sqlite = (role_id,)
    params_sa = {"role_id": role_id}

    db_obj, dialect = _get_cursor_and_dialect(conn)
    if not db_obj or not dialect:
        logger.error(f"Unsupported connection type in delete_role: {type(conn)}")
        return False

    try:
        result = _execute_query(db_obj, sql_sa if dialect == "sqlalchemy" else sql_sqlite,
                                params_sa if dialect == "sqlalchemy" else params_sqlite, dialect)
        if result and result.rowcount > 0:
            logger.info(f"Role ID {role_id} deleted successfully.")
            return True
        logger.warning(f"Role ID {role_id} not found for deletion.")
        return False
    except (sqlite3.Error, SQLAlchemyError) as e:
        # Check for IntegrityError which might be wrapped by SQLAlchemyError
        original_error = getattr(e, 'orig', e)
        if isinstance(original_error, sqlite3.IntegrityError):
            logger.error(f"Cannot delete role ID {role_id} as it's likely in use (IntegrityError). Error: {original_error}", exc_info=False)
        else:
            logger.error(f"Database error deleting role ID {role_id}: {e}", exc_info=True)
        return False

@_manage_conn
def is_role_used(role_id: int, conn=None) -> bool:
    """Checks if a role is currently assigned to any user."""
    sql_sqlite = "SELECT 1 FROM Users WHERE role_id = ? LIMIT 1"
    sql_sa = sqlalchemy_text("SELECT 1 FROM Users WHERE role_id = :role_id LIMIT 1")

    params_sqlite = (role_id,)
    params_sa = {"role_id": role_id}

    db_obj, dialect = _get_cursor_and_dialect(conn)
    if not db_obj or not dialect:
        logger.error(f"Unsupported connection type in is_role_used: {type(conn)}")
        return True # Fail safe

    try:
        # _fetch_one_as_dict returns a dict or None. We just need to know if a row exists.
        row = _fetch_one_as_dict(db_obj, sql_sa if dialect == "sqlalchemy" else sql_sqlite,
                                 params_sa if dialect == "sqlalchemy" else params_sqlite, dialect, logger)
        return row is not None
    except (sqlite3.Error, SQLAlchemyError) as e: # Catching broader errors from helpers
        logger.error(f"Database error checking if role ID {role_id} is used: {e}", exc_info=True)
        return True # Fail safe: assume it's used if there's an error checking
