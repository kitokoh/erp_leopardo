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
        return dict(row) if row else None
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
        return dict(row) if row else None
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
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Database error listing roles: {e}", exc_info=True)
        return []
