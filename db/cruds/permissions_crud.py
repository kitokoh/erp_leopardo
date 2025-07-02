# db/cruds/permissions_crud.py
import sqlite3
import logging
from .generic_crud import _manage_conn

logger = logging.getLogger(__name__)

@_manage_conn
def add_permission(permission_key: str, description: str, conn: sqlite3.Connection = None) -> bool:
    """
    Adds a new permission to the Permissions table.
    Mainly intended for initial seeding or administrative setup.
    Returns True if successful, False otherwise.
    """
    sql = "INSERT INTO Permissions (permission_key, description) VALUES (?, ?)"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (permission_key, description))
        # conn.commit() # Handled by _manage_conn
        logger.info(f"Permission '{permission_key}' added successfully.")
        return True
    except sqlite3.IntegrityError:
        logger.warning(f"Permission '{permission_key}' already exists. Skipping.")
        return False # Not necessarily an error if called during seeding
    except sqlite3.Error as e:
        logger.error(f"Database error adding permission '{permission_key}': {e}", exc_info=True)
        return False

@_manage_conn
def get_permission_by_key(permission_key: str, conn: sqlite3.Connection = None) -> dict | None:
    """Fetches a permission by its key."""
    sql = "SELECT * FROM Permissions WHERE permission_key = ?"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (permission_key,))
        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        logger.error(f"Database error fetching permission by key '{permission_key}': {e}", exc_info=True)
        return None

@_manage_conn
def list_all_permissions(conn: sqlite3.Connection = None) -> list[dict]:
    """Lists all available permissions."""
    sql = "SELECT * FROM Permissions ORDER BY permission_key"
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Database error listing all permissions: {e}", exc_info=True)
        return []

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
