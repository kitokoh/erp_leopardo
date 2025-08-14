# db/cruds/role_permissions_crud.py
import sqlite3
import logging
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine, Connection as SQLAlchemyConnection
from sqlalchemy.sql import text as sqlalchemy_text
from sqlalchemy.exc import SQLAlchemyError

from app.db.cruds.generic_crud import _manage_conn

logger = logging.getLogger(__name__)

# Helper functions (copied from other CRUD modules)
# Ideally, these should be in a shared db.crud_utils module
def _get_cursor_and_dialect(conn):
    if isinstance(conn, (Session, Engine, SQLAlchemyConnection)):
        return conn, "sqlalchemy"
    elif hasattr(conn, 'cursor'):
        return conn.cursor(), "sqlite"
    logger.warning(f"Unsupported connection type: {type(conn)} in _get_cursor_and_dialect (role_permissions_crud).")
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
    except (sqlite3.Error, SQLAlchemyError) as e: # Catch both types of errors
        current_logger.error(f"Database error in _execute_query (dialect: {dialect}): {e}", exc_info=True)
        raise # Re-raise for @_manage_conn to handle rollback/close

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


@_manage_conn
def add_permission_to_role(role_id: int, permission_key: str, conn=None) -> bool:
    """
    Assigns a permission to a role.
    Returns True if successful or if the assignment already exists.
    Returns False on database error.
    """
    # SQLite's "INSERT OR IGNORE" is specific.
    # For SQLAlchemy, a more generic approach for "upsert" or "insert if not exists"
    # might involve a preliminary check or using database-specific dialect features.
    # For simplicity here, we'll try the insert and catch integrity errors,
    # or rely on the "OR IGNORE" for SQLite and a plain INSERT for SA (expecting potential error).
    # A better SA way for "if not exists" often involves checking first.

    sql_sqlite = "INSERT OR IGNORE INTO RolePermissions (role_id, permission_key) VALUES (?, ?)"
    # For SA, a plain insert. If it fails due to PK violation, it means it exists.
    # The `OR IGNORE` is not standard SQL for all DBs SA might support.
    # We'll assume the calling logic or DB schema handles uniqueness for SA.
    sql_sa = sqlalchemy_text("INSERT INTO RolePermissions (role_id, permission_key) VALUES (:role_id, :permission_key)")

    params_sqlite = (role_id, permission_key)
    params_sa = {"role_id": role_id, "permission_key": permission_key}

    db_obj, dialect = _get_cursor_and_dialect(conn)
    if not db_obj or not dialect:
        logger.error(f"Unsupported connection type in add_permission_to_role: {type(conn)}")
        return False

    try:
        if dialect == "sqlalchemy":
            # For SA, we might need to check existence first if "OR IGNORE" is not used/portable
            # Or, attempt insert and catch specific integrity error for "already exists"
            try:
                result = _execute_query(db_obj, sql_sa, params_sa, dialect)
                if result.rowcount > 0:
                     logger.info(f"Permission '{permission_key}' added to role ID {role_id} (SA).")
                # If rowcount is 0 but no error, it might mean some DBs don't report rowcount for INSERT like SQLite.
                # Or, if the DB has an "ON CONFLICT DO NOTHING" type clause used with SA, rowcount might be 0.
                # For this simple case, we assume success if no error.
                return True
            except SQLAlchemyError as e_sa:
                # Check if it's a unique constraint violation (specific error codes/classes vary by DB)
                # This is a simplification. Real check is more complex.
                if "UNIQUE constraint failed" in str(e_sa) or "IntegrityError" in str(type(e_sa.orig)): # Check for SQLite through SA
                    logger.info(f"Permission '{permission_key}' likely already assigned to role ID {role_id} (SA - Integrity).")
                    return True # Treat as success if already exists
                raise # Re-raise other SQLAlchemy errors
        else: # sqlite
            result = _execute_query(db_obj, sql_sqlite, params_sqlite, dialect) # db_obj is cursor
            if result.rowcount > 0:
                logger.info(f"Permission '{permission_key}' added to role ID {role_id} (SQLite).")
            else:
                logger.info(f"Permission '{permission_key}' likely already assigned to role ID {role_id} (SQLite - OR IGNORE).")
            return True

    except (sqlite3.IntegrityError) as e_sqlite_integrity: # Explicitly for SQLite if not caught by OR IGNORE logic (e.g. FK fail)
        logger.error(f"Integrity error (SQLite) adding permission '{permission_key}' to role {role_id}: {e_sqlite_integrity}. Check if role and permission exist.", exc_info=True)
        return False
    except (sqlite3.Error, SQLAlchemyError) as e: # Catch broader errors
        logger.error(f"Database error adding permission '{permission_key}' to role {role_id}: {e}", exc_info=True)
        return False


@_manage_conn
def remove_permission_from_role(role_id: int, permission_key: str, conn=None) -> bool:
    """
    Removes a permission from a role.
    Returns True if successful or if the assignment didn't exist (rowcount >= 0).
    Returns False on database error.
    """
    sql_sqlite = "DELETE FROM RolePermissions WHERE role_id = ? AND permission_key = ?"
    sql_sa = sqlalchemy_text("DELETE FROM RolePermissions WHERE role_id = :role_id AND permission_key = :permission_key")

    params_sqlite = (role_id, permission_key)
    params_sa = {"role_id": role_id, "permission_key": permission_key}

    db_obj, dialect = _get_cursor_and_dialect(conn)
    if not db_obj or not dialect:
        logger.error(f"Unsupported connection type in remove_permission_from_role: {type(conn)}")
        return False

    try:
        result = _execute_query(db_obj, sql_sa if dialect == "sqlalchemy" else sql_sqlite,
                                params_sa if dialect == "sqlalchemy" else params_sqlite, dialect)
        if result.rowcount > 0:
            logger.info(f"Permission '{permission_key}' removed from role ID {role_id}.")
        else:
            logger.info(f"Permission '{permission_key}' was not assigned to role ID {role_id}, or role/permission does not exist (no rows deleted).")
        return True # Success if operation completed, even if no rows affected
    except (sqlite3.Error, SQLAlchemyError) as e:
        logger.error(f"Database error removing permission '{permission_key}' from role {role_id}: {e}", exc_info=True)
        return False


@_manage_conn
def get_permissions_for_role(role_id: int, conn=None) -> list[str]:
    """
    Lists all permission keys assigned to a specific role.
    Returns a list of permission_key strings.
    """
    sql_common = "SELECT permission_key FROM RolePermissions WHERE role_id = :role_id ORDER BY permission_key"
    # For SQLite, ? placeholder
    sql_sqlite_variant = "SELECT permission_key FROM RolePermissions WHERE role_id = ? ORDER BY permission_key"

    sql_sa_variant = sqlalchemy_text(sql_common)

    params_sqlite = (role_id,)
    params_sa = {"role_id": role_id}

    db_obj, dialect = _get_cursor_and_dialect(conn)
    if not db_obj or not dialect:
        logger.error(f"Unsupported connection type in get_permissions_for_role: {type(conn)}")
        return []

    permission_rows = _fetch_all_as_dict_list(db_obj,
                                              sql_sa_variant if dialect == "sqlalchemy" else sql_sqlite_variant,
                                              params_sa if dialect == "sqlalchemy" else params_sqlite,
                                              dialect, logger)
    return [row['permission_key'] for row in permission_rows]


@_manage_conn
def check_role_has_permission(role_id: int, permission_key: str, conn=None) -> bool:
    """
    Checks if a specific role has a specific permission.
    Returns True if the role has the permission, False otherwise.
    """
    sql_common = "SELECT 1 FROM RolePermissions WHERE role_id = :role_id AND permission_key = :permission_key"
    sql_sqlite_variant = "SELECT 1 FROM RolePermissions WHERE role_id = ? AND permission_key = ?"
    sql_sa_variant = sqlalchemy_text(sql_common)

    params_sqlite = (role_id, permission_key)
    params_sa = {"role_id": role_id, "permission_key": permission_key}

    db_obj, dialect = _get_cursor_and_dialect(conn)
    if not db_obj or not dialect:
        logger.error(f"Unsupported connection type in check_role_has_permission: {type(conn)}")
        return False # Fail safe

    row = _fetch_one_as_dict(db_obj,
                             sql_sa_variant if dialect == "sqlalchemy" else sql_sqlite_variant,
                             params_sa if dialect == "sqlalchemy" else params_sqlite,
                             dialect, logger)
    return row is not None


@_manage_conn
def set_permissions_for_role(role_id: int, permission_keys: list[str], conn=None) -> bool:
    """
    Sets all permissions for a role.
    This will remove all existing permissions for the role and add the new ones.
    This is a transactional operation (managed by @_manage_conn).
    """
    db_obj, dialect = _get_cursor_and_dialect(conn)
    if not db_obj or not dialect:
        logger.error(f"Unsupported connection type in set_permissions_for_role: {type(conn)}")
        return False

    try:
        # 1. Delete all existing permissions for the role
        sql_delete_sqlite = "DELETE FROM RolePermissions WHERE role_id = ?"
        sql_delete_sa = sqlalchemy_text("DELETE FROM RolePermissions WHERE role_id = :role_id")
        params_delete_sqlite = (role_id,)
        params_delete_sa = {"role_id": role_id}

        del_result = _execute_query(db_obj,
                                    sql_delete_sa if dialect == "sqlalchemy" else sql_delete_sqlite,
                                    params_delete_sa if dialect == "sqlalchemy" else params_delete_sqlite,
                                    dialect)
        # logger.info(f"Cleared existing permissions for role ID {role_id}. Rows affected: {getattr(del_result, 'rowcount', 'N/A')}")
        if del_result: # Check if execution was successful
             logger.info(f"Cleared existing permissions for role ID {role_id}. Rows affected: {del_result.rowcount if hasattr(del_result, 'rowcount') else 'N/A'}")


        # 2. Add new permissions
        if permission_keys:
            sql_insert_sqlite = "INSERT INTO RolePermissions (role_id, permission_key) VALUES (?, ?)"
            sql_insert_sa = sqlalchemy_text("INSERT INTO RolePermissions (role_id, permission_key) VALUES (:role_id, :permission_key)")

            inserted_count = 0
            for p_key in permission_keys:
                params_insert_sqlite = (role_id, p_key)
                params_insert_sa = {"role_id": role_id, "permission_key": p_key}
                # Note: executemany is often more efficient but _execute_query is one-by-one here.
                # For batch insert with _execute_query, it would need modification or a new helper.
                # For simplicity, doing one by one, which is less efficient but works with current helpers.
                # A better approach for multiple inserts would be a batch operation.
                insert_result = _execute_query(db_obj,
                                               sql_insert_sa if dialect == "sqlalchemy" else sql_insert_sqlite,
                                               params_insert_sa if dialect == "sqlalchemy" else params_insert_sqlite,
                                               dialect)
                if insert_result and getattr(insert_result, 'rowcount', 0) > 0 : # Check rowcount if available
                    inserted_count +=1
                elif dialect == "sqlalchemy" and insert_result : # For SA, if no error, assume insert worked if rowcount not reliable
                    inserted_count +=1


            logger.info(f"Attempted to add {len(permission_keys)} permissions to role ID {role_id}. Successfully inserted: {inserted_count}.")

        # @_manage_conn handles commit/rollback
        return True

    except (sqlite3.Error, SQLAlchemyError) as e:
        logger.error(f"Database error setting permissions for role {role_id}: {e}", exc_info=True)
        return False


if __name__ == '__main__':
    # Example Usage (requires database to be initialized with relevant tables and some data)
    # from db.init_schema import initialize_database
    # from db.cruds import roles_crud # For getting role_id
    # from db.cruds import permissions_crud # For ensuring permissions exist

    # initialize_database() # Ensure schema

    # Example:
    # admin_role = roles_crud.get_role_by_name("Administrator")
    # if admin_role:
    #     admin_role_id = admin_role['role_id']

    #     print(f"Permissions for Administrator (ID: {admin_role_id}) before changes:")
    #     print(get_permissions_for_role(admin_role_id))

    #     # Add a permission (ensure 'P_TEST_PERMISSION' exists in Permissions table first)
    #     # permissions_crud.add_permission("P_TEST_PERMISSION", "A test permission")
    #     # add_permission_to_role(admin_role_id, "P_TEST_PERMISSION")

    #     # print(f"Permissions for Administrator after adding P_TEST_PERMISSION:")
    #     # print(get_permissions_for_role(admin_role_id))

    #     # print(f"Does Admin have P_TEST_PERMISSION? {check_role_has_permission(admin_role_id, 'P_TEST_PERMISSION')}")
    #     # print(f"Does Admin have P_NON_EXISTENT? {check_role_has_permission(admin_role_id, 'P_NON_EXISTENT')}")

    #     # remove_permission_from_role(admin_role_id, "P_TEST_PERMISSION")
    #     # print(f"Permissions for Administrator after removing P_TEST_PERMISSION:")
    #     # print(get_permissions_for_role(admin_role_id))

    #     # Set all permissions (example)
    #     # current_admin_perms = permissions_crud.list_all_permissions()
    #     # keys_to_set = [p['permission_key'] for p in current_admin_perms if p['permission_key'].startswith("P_MANAGE")]
    #     # print(f"Setting Admin permissions to: {keys_to_set}")
    #     # set_permissions_for_role(admin_role_id, keys_to_set)
    #     # print(f"Permissions for Administrator after set_permissions_for_role:")
    #     # print(get_permissions_for_role(admin_role_id))

    pass
