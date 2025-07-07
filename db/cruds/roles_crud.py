# db/cruds/roles_crud.py
import sqlite3
import logging
from .generic_crud import _manage_conn # Assuming generic_crud provides this decorator

logger = logging.getLogger(__name__)

@_manage_conn
def add_role(role_name: str, description: str = None, conn: sqlite3.Connection = None) -> int | None:
    """Adds a new role to the Roles table."""
    sql = "INSERT INTO Roles (role_name, description) VALUES (?, ?)"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (role_name, description))
        # conn.commit() # Handled by _manage_conn
        logger.info(f"Role '{role_name}' added successfully with ID {cursor.lastrowid}.")
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        logger.error(f"Role '{role_name}' already exists.")
        return None
    except sqlite3.Error as e:
        logger.error(f"Database error adding role '{role_name}': {e}", exc_info=True)
        return None

@_manage_conn
def get_role_by_id(role_id: int, conn: sqlite3.Connection = None) -> dict | None:
    """Fetches a role by its ID."""
    sql = "SELECT * FROM Roles WHERE role_id = ?"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (role_id,))
        row = cursor.fetchone()
        if row:
            column_names = [desc[0] for desc in cursor.description]
            return dict(zip(column_names, row))
        return None
    except sqlite3.Error as e:
        logger.error(f"Database error fetching role ID {role_id}: {e}", exc_info=True)
        return None

@_manage_conn
def get_role_by_name(role_name: str, conn: sqlite3.Connection = None) -> dict | None:
    """Fetches a role by its name."""
    sql = "SELECT * FROM Roles WHERE role_name = ?"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (role_name,))
        row = cursor.fetchone()
        if row:
            column_names = [desc[0] for desc in cursor.description]
            return dict(zip(column_names, row))
        return None
    except sqlite3.Error as e:
        logger.error(f"Database error fetching role by name '{role_name}': {e}", exc_info=True)
        return None

@_manage_conn
def list_roles(conn: sqlite3.Connection = None) -> list[dict]:
    """Lists all roles."""
    sql = "SELECT * FROM Roles ORDER BY role_name"
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        if not rows:
            return []
        column_names = [desc[0] for desc in cursor.description]
        return [dict(zip(column_names, row)) for row in rows]
    except sqlite3.Error as e:
        logger.error(f"Database error listing roles: {e}", exc_info=True)
        return []

@_manage_conn
def update_role(role_id: int, role_name: str, description: str = None, conn: sqlite3.Connection = None) -> bool:
    """Updates an existing role's name and description."""
    sql = "UPDATE Roles SET role_name = ?, description = ? WHERE role_id = ?"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (role_name, description, role_id))
        # conn.commit()
        if cursor.rowcount > 0:
            logger.info(f"Role ID {role_id} updated to name '{role_name}'.")
            return True
        logger.warning(f"Role ID {role_id} not found for update.")
        return False
    except sqlite3.IntegrityError:
        logger.error(f"Update failed for role ID {role_id}: New role name '{role_name}' might already exist.")
        return False
    except sqlite3.Error as e:
        logger.error(f"Database error updating role ID {role_id}: {e}", exc_info=True)
        return False

@_manage_conn
def delete_role(role_id: int, conn: sqlite3.Connection = None) -> bool:
    """Deletes a role by its ID."""
    # Note: This does not currently check for users assigned to this role.
    # That check should be done in the application logic before calling this.
    sql = "DELETE FROM Roles WHERE role_id = ?"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (role_id,))
        # conn.commit()
        if cursor.rowcount > 0:
            logger.info(f"Role ID {role_id} deleted successfully.")
            return True
        logger.warning(f"Role ID {role_id} not found for deletion.")
        return False
    except sqlite3.Error as e: # Could be IntegrityError if foreign key constraints are set up to prevent deletion of used roles at DB level
        logger.error(f"Database error deleting role ID {role_id}: {e}", exc_info=True)
        # If e is an IntegrityError specifically (e.g., foreign key violation),
        # it means the role is in use and the DB prevented deletion.
        # This function would return False, and the calling code should interpret this.
        # For robust handling, one might check `isinstance(e, sqlite3.IntegrityError)`.
        return False

@_manage_conn
def is_role_used(role_id: int, conn: sqlite3.Connection = None) -> bool:
    """Checks if a role is currently assigned to any user."""
    sql = "SELECT 1 FROM Users WHERE role_id = ? LIMIT 1"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (role_id,))
        return cursor.fetchone() is not None
    except sqlite3.Error as e:
        logger.error(f"Database error checking if role ID {role_id} is used: {e}", exc_info=True)
        return True # Fail safe: assume it's used if there's an error checking
