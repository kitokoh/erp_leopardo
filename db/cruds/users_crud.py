# db/cruds/users_crud.py
import sqlite3
import uuid
from datetime import datetime
import logging
from werkzeug.security import generate_password_hash, check_password_hash # For password hashing
from .generic_crud import _manage_conn

logger = logging.getLogger(__name__)

@_manage_conn
def add_user(username: str, password: str, role_id: int, full_name: str = None, email: str = None, conn: sqlite3.Connection = None) -> str | None:
    """Adds a new user with a hashed password. Returns the new user_id (UUID string)."""
    if not username or not password or role_id is None:
        logger.error("Username, password, and role_id are required to add a user.")
        return None

    hashed_pw = generate_password_hash(password)
    user_id = str(uuid.uuid4()) # Generate UUID for user_id
    now = datetime.utcnow().isoformat() + "Z"

    sql = """INSERT INTO Users (user_id, username, hashed_password, full_name, email, role_id, is_active, created_at, updated_at, last_login_at)
             VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, NULL)"""
    params = (user_id, username, hashed_pw, full_name, email, role_id, now, now)

    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        # conn.commit() # Handled by _manage_conn
        logger.info(f"User '{username}' added successfully with ID {user_id}.")
        return user_id
    except sqlite3.IntegrityError as e:
        logger.error(f"Error adding user '{username}'. Username or email might already exist: {e}", exc_info=True)
        return None
    except sqlite3.Error as e:
        logger.error(f"Database error adding user '{username}': {e}", exc_info=True)
        return None

@_manage_conn
def get_user_by_username(username: str, conn: sqlite3.Connection = None) -> dict | None:
    """Fetches a user by username, including their role information."""
    sql = """SELECT u.*, r.role_name
             FROM Users u
             JOIN Roles r ON u.role_id = r.role_id
             WHERE u.username = ?"""
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (username,))
        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        logger.error(f"Database error fetching user by username '{username}': {e}", exc_info=True)
        return None

@_manage_conn
def get_user_by_id(user_id: str, conn: sqlite3.Connection = None) -> dict | None:
    """Fetches a user by user_id, including their role information."""
    sql = """SELECT u.*, r.role_name
             FROM Users u
             JOIN Roles r ON u.role_id = r.role_id
             WHERE u.user_id = ?"""
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        logger.error(f"Database error fetching user by ID '{user_id}': {e}", exc_info=True)
        return None

@_manage_conn
def update_user_role(user_id: str, new_role_id: int, conn: sqlite3.Connection = None) -> bool:
    """Updates the role of a user."""
    now = datetime.utcnow().isoformat() + "Z"
    sql = "UPDATE Users SET role_id = ?, updated_at = ? WHERE user_id = ?"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (new_role_id, now, user_id))
        # conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Database error updating role for user ID '{user_id}': {e}", exc_info=True)
        return False

@_manage_conn
def update_user_password(user_id: str, new_password: str, conn: sqlite3.Connection = None) -> bool:
    """Updates the password for a user. The new password will be hashed."""
    if not new_password:
        logger.error("New password cannot be empty.")
        return False
    hashed_pw = generate_password_hash(new_password)
    now = datetime.utcnow().isoformat() + "Z"
    sql = "UPDATE Users SET hashed_password = ?, updated_at = ? WHERE user_id = ?"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (hashed_pw, now, user_id))
        # conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Database error updating password for user ID '{user_id}': {e}", exc_info=True)
        return False

@_manage_conn
def set_user_active_status(user_id: str, is_active: bool, conn: sqlite3.Connection = None) -> bool:
    """Sets the is_active status for a user."""
    now = datetime.utcnow().isoformat() + "Z"
    status_int = 1 if is_active else 0
    sql = "UPDATE Users SET is_active = ?, updated_at = ? WHERE user_id = ?"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (status_int, now, user_id))
        # conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Database error setting active status for user ID '{user_id}': {e}", exc_info=True)
        return False

@_manage_conn
def record_login_time(user_id: str, conn: sqlite3.Connection = None) -> bool:
    """Updates the last_login_at timestamp for a user."""
    now = datetime.utcnow().isoformat() + "Z"
    sql = "UPDATE Users SET last_login_at = ? WHERE user_id = ?"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (now, user_id))
        # conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Database error recording login time for user ID '{user_id}': {e}", exc_info=True)
        return False

@_manage_conn
def list_users(conn: sqlite3.Connection = None) -> list[dict]:
    """Lists all users with their role names."""
    sql = """SELECT u.user_id, u.username, u.full_name, u.email, r.role_name, u.is_active, u.created_at, u.last_login_at
             FROM Users u
             JOIN Roles r ON u.role_id = r.role_id
             ORDER BY u.username"""
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Database error listing users: {e}", exc_info=True)
        return []

def verify_password(hashed_password: str, provided_password: str) -> bool:
    """Verifies a provided password against a stored hash."""
    return check_password_hash(hashed_password, provided_password)

# For consistency, if there's an existing users_crud_instance, re-declare it or ensure it's updated.
# If the previous users_crud.py was very different, this overwrite is fine.
# users_crud_instance = UsersCRUD() # If it were a class-based CRUD
# For now, these are module-level functions.
