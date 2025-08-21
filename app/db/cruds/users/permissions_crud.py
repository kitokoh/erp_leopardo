# db/cruds/permissions_crud.py
import sqlite3
import logging
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine, Connection as SQLAlchemyConnection
from sqlalchemy.sql import text as sqlalchemy_text
from sqlalchemy.exc import SQLAlchemyError

from ..generic_crud import _manage_conn

logger = logging.getLogger(__name__)

# Helper functions (copied from roles_crud.py / users_crud.py)
# Ideally, these should be in a shared db.crud_utils module
def _get_cursor_and_dialect(conn):
    if isinstance(conn, (Session, Engine, SQLAlchemyConnection)):
        return conn, "sqlalchemy"
    elif hasattr(conn, 'cursor'):
        return conn.cursor(), "sqlite"
    logger.warning(f"Unsupported connection type: {type(conn)} in _get_cursor_and_dialect (permissions_crud).")
    return None, None

def _execute_query(db_obj, sql_query, params, dialect, logger_to_use=None):
    current_logger = logger_to_use if logger_to_use else logger
    try:
        if dialect == "sqlalchemy":
            return db_obj.execute(sql_query, params)
        elif dialect == "sqlite":
            return db_obj.execute(sql_query, params)
        else:
            current_logger.error(f"Unsupported dialect '{dialect}' in _execute_query.")
            return None
    except (sqlite3.Error, SQLAlchemyError) as e:
        current_logger.error(f"Database error in _execute_query (dialect: {dialect}): {e}", exc_info=True)
        raise

def _fetch_one_as_dict(db_obj, sql_query, params, dialect, logger_to_use=None):
    current_logger = logger_to_use if logger_to_use else logger
    try:
        row_data = None
        if dialect == "sqlalchemy":
            result = db_obj.execute(sql_query, params)
            row = result.fetchone()
            if row: row_data = dict(row._mapping)
        elif dialect == "sqlite":
            db_obj.execute(sql_query, params)
            row = db_obj.fetchone()
            if row:
                column_names = [desc[0] for desc in db_obj.description]
                row_data = dict(zip(column_names, row))
        return row_data
    except (sqlite3.Error, SQLAlchemyError) as e:
        current_logger.error(f"Database error in _fetch_one_as_dict (dialect: {dialect}): {e}", exc_info=True)
        return None

def _fetch_all_as_dict_list(db_obj, sql_query, params, dialect, logger_to_use=None):
    current_logger = logger_to_use if logger_to_use else logger
    try:
        rows_data = []
        if dialect == "sqlalchemy":
            result = db_obj.execute(sql_query, params)
            for row in result.fetchall():
                rows_data.append(dict(row._mapping))
        elif dialect == "sqlite":
            db_obj.execute(sql_query, params)
            rows = db_obj.fetchall()
            if rows:
                column_names = [desc[0] for desc in db_obj.description]
                for row_item in rows:
                    rows_data.append(dict(zip(column_names, row_item)))
        return rows_data
    except (sqlite3.Error, SQLAlchemyError) as e:
        current_logger.error(f"Database error in _fetch_all_as_dict_list (dialect: {dialect}): {e}", exc_info=True)
        return []


from app.models.db.misc.permissions import Permission

def add_permission(db: Session, permission_key: str, description: str) -> Permission | None:
    """
    Adds a new permission to the Permissions table.
    Mainly intended for initial seeding or administrative setup.
    """
    try:
        new_permission = Permission(permission_key=permission_key, description=description)
        db.add(new_permission)
        db.commit()
        db.refresh(new_permission)
        logger.info(f"Permission '{permission_key}' added successfully.")
        return new_permission
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error adding permission '{permission_key}': {e}", exc_info=True)
        return None


def get_permission_by_key(db: Session, permission_key: str) -> Permission | None:
    """Fetches a permission by its key."""
    try:
        return db.query(Permission).filter(Permission.permission_key == permission_key).first()
    except SQLAlchemyError as e:
        logger.error(f"Database error getting permission by key '{permission_key}': {e}", exc_info=True)
        return None


@_manage_conn
def list_all_permissions(conn=None) -> list[dict]:
    """Lists all available permissions."""
    sql_common = "SELECT * FROM Permissions ORDER BY permission_key"
    sql_sqlite = sql_common
    sql_sa = sqlalchemy_text(sql_common)

    params_sqlite = ()
    params_sa = {}

    db_obj, dialect = _get_cursor_and_dialect(conn)
    if not db_obj or not dialect:
        logger.error(f"Unsupported connection type in list_all_permissions: {type(conn)}")
        return []

    return _fetch_all_as_dict_list(db_obj, sql_sa if dialect == "sqlalchemy" else sql_sqlite,
                                   params_sa if dialect == "sqlalchemy" else params_sqlite, dialect, logger)

# Potential future functions:
# - update_permission_description(permission_key: str, new_description: str) -> bool
# - delete_permission(permission_key: str) -> bool (use with extreme caution, might break RolePermissions)

if __name__ == '__main__':
    # Example Usage (requires database to be initialized with Permissions table)
    # For direct execution, you might need to adjust sys.path or run from project root
    # Ensure your DB connection is set up (e.g., via config and _manage_conn)

    # This example assumes a temporary in-memory DB for testing if run standalone
    # In a real scenario, this would connect to your application's DB.
    # To test, you'd need to initialize the schema first.

    # Example:
    # from db.init_schema import initialize_database
    # initialize_database() # Create schema in memory or test DB

    # print("Listing all permissions:")
    # permissions = list_all_permissions()
    # if permissions:
    #     for p in permissions:
    #         print(f"- {p['permission_key']}: {p['description']}")
    # else:
    #     print("No permissions found or error listing them.")

    # print("\nGetting P_MANAGE_USERS:")
    # p_manage_users = get_permission_by_key("P_MANAGE_USERS")
    # if p_manage_users:
    #     print(p_manage_users)
    # else:
    #     print("P_MANAGE_USERS not found.")
    pass # Keep __main__ block minimal or for dedicated tests
