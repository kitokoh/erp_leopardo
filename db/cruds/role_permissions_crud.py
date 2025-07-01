# db/cruds/role_permissions_crud.py
import sqlite3
import logging
from .generic_crud import _manage_conn

logger = logging.getLogger(__name__)

@_manage_conn
def add_permission_to_role(role_id: int, permission_key: str, conn: sqlite3.Connection = None) -> bool:
    """
    Assigns a permission to a role.
    Returns True if successful or if the assignment already exists.
    Returns False on database error.
    """
    sql = "INSERT OR IGNORE INTO RolePermissions (role_id, permission_key) VALUES (?, ?)"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (role_id, permission_key))
        # conn.commit() # Handled by _manage_conn
        if cursor.rowcount > 0:
            logger.info(f"Permission '{permission_key}' added to role ID {role_id}.")
        else:
            logger.info(f"Permission '{permission_key}' likely already assigned to role ID {role_id}.")
        return True
    except sqlite3.IntegrityError as e: # Should be caught by OR IGNORE, but as safeguard
        # This might happen if permission_key doesn't exist in Permissions table, or role_id in Roles.
        logger.error(f"Integrity error adding permission '{permission_key}' to role {role_id}: {e}. Check if role and permission exist.", exc_info=True)
        return False
    except sqlite3.Error as e:
        logger.error(f"Database error adding permission '{permission_key}' to role {role_id}: {e}", exc_info=True)
        return False

@_manage_conn
def remove_permission_from_role(role_id: int, permission_key: str, conn: sqlite3.Connection = None) -> bool:
    """
    Removes a permission from a role.
    Returns True if successful or if the assignment didn't exist.
    Returns False on database error.
    """
    sql = "DELETE FROM RolePermissions WHERE role_id = ? AND permission_key = ?"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (role_id, permission_key))
        # conn.commit() # Handled by _manage_conn
        if cursor.rowcount > 0:
            logger.info(f"Permission '{permission_key}' removed from role ID {role_id}.")
        else:
            logger.info(f"Permission '{permission_key}' was not assigned to role ID {role_id}, or role/permission does not exist.")
        return True
    except sqlite3.Error as e:
        logger.error(f"Database error removing permission '{permission_key}' from role {role_id}: {e}", exc_info=True)
        return False

@_manage_conn
def get_permissions_for_role(role_id: int, conn: sqlite3.Connection = None) -> list[str]:
    """
    Lists all permission keys assigned to a specific role.
    Returns a list of permission_key strings.
    """
    # Fetches from RolePermissions and joins with Permissions to ensure key validity (optional, but good practice)
    # sql = """SELECT rp.permission_key
    #          FROM RolePermissions rp
    #          JOIN Permissions p ON rp.permission_key = p.permission_key
    #          WHERE rp.role_id = ?
    #          ORDER BY rp.permission_key"""
    # Simpler version if we trust RolePermissions integrity:
    sql = "SELECT permission_key FROM RolePermissions WHERE role_id = ? ORDER BY permission_key"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (role_id,))
        return [row['permission_key'] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Database error listing permissions for role ID {role_id}: {e}", exc_info=True)
        return []

@_manage_conn
def check_role_has_permission(role_id: int, permission_key: str, conn: sqlite3.Connection = None) -> bool:
    """
    Checks if a specific role has a specific permission.
    Returns True if the role has the permission, False otherwise.
    """
    sql = "SELECT 1 FROM RolePermissions WHERE role_id = ? AND permission_key = ?"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (role_id, permission_key))
        return cursor.fetchone() is not None
    except sqlite3.Error as e:
        logger.error(f"Database error checking permission '{permission_key}' for role {role_id}: {e}", exc_info=True)
        return False # Fail safe: assume no permission on error

@_manage_conn
def set_permissions_for_role(role_id: int, permission_keys: list[str], conn: sqlite3.Connection = None) -> bool:
    """
    Sets all permissions for a role.
    This will remove all existing permissions for the role and add the new ones.
    This is a transactional operation.
    """
    # Start transaction (handled by _manage_conn if it supports nested transactions or single op mode)
    # For explicit transaction control if _manage_conn doesn't handle it perfectly for multiple steps:
    # try:
    #     if conn.in_transaction: # If _manage_conn already started one
    #         pass
    #     else:
    #         conn.execute("BEGIN") # Start one if not already in one.
    # except AttributeError: # conn might not have in_transaction if it's not a standard Connection obj
    #     pass


    # 1. Delete all existing permissions for the role
    sql_delete = "DELETE FROM RolePermissions WHERE role_id = ?"
    cursor = conn.cursor()
    cursor.execute(sql_delete, (role_id,))
    logger.info(f"Cleared existing permissions for role ID {role_id}. Rows affected: {cursor.rowcount}")

    # 2. Add new permissions
    if permission_keys: # Only proceed if there are permissions to add
        sql_insert = "INSERT INTO RolePermissions (role_id, permission_key) VALUES (?, ?)"
        # Prepare data for executemany: list of tuples
        data_to_insert = [(role_id, p_key) for p_key in permission_keys]
        cursor.executemany(sql_insert, data_to_insert)
        logger.info(f"Added {len(data_to_insert)} permissions to role ID {role_id}.")

    # Commit transaction (handled by _manage_conn)
    return True # Assuming success if no exceptions were raised by _manage_conn

    # except sqlite3.Error as e:
    #     logger.error(f"Database error setting permissions for role {role_id}: {e}", exc_info=True)
    #     # conn.rollback() # Handled by _manage_conn on exception
    #     return False
    # finally:
    #     # If we explicitly started a transaction, we might need to handle its end state here,
    #     # but _manage_conn should ideally manage the commit/rollback.
    #     pass


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
