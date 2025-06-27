# db/cruds/users_crud.py
import sqlite3
import uuid
from datetime import datetime
import logging
# from werkzeug.security import generate_password_hash, check_password_hash # Replaced by passlib
from utils import hash_password, verify_password # Using passlib functions from utils
from .generic_crud import _manage_conn

logger = logging.getLogger(__name__)

@_manage_conn
def add_user(username: str, password: str, role_id: int, full_name: str = None, email: str = None, conn: sqlite3.Connection = None) -> str | None:
    """Adds a new user with a hashed password. Returns the new user_id (UUID string)."""
    if not username or not password or role_id is None:
        logger.error("Username, password, and role_id are required to add a user.")
        return None

    # hashed_pw = generate_password_hash(password) # Replaced by utils.hash_password
    hashed_pw = hash_password(password)
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
    # hashed_pw = generate_password_hash(new_password) # Replaced by utils.hash_password
    hashed_pw = hash_password(new_password)
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
    """
    Verifies a provided password against a stored hash.
    Internal helper, typically not called directly from outside for login.
    Uses the verify_password function imported from utils.py (which uses passlib).
    Now returns a tuple: (bool_verified, new_hash_if_updated_or_None)
    """
    # The function signature in utils.verify_password is (plain_password, hashed_password)
    # So, the call should be utils.verify_password(provided_password, hashed_password)
    return verify_password(provided_password, hashed_password) # Corrected argument order from previous step if it was wrong

@_manage_conn
def _update_user_password_hash_only(user_id: str, new_hashed_password: str, conn: sqlite3.Connection = None) -> bool:
    """Updates only the hashed_password and updated_at for a user. Internal use for hash upgrades."""
    now = datetime.utcnow().isoformat() + "Z"
    sql = "UPDATE Users SET hashed_password = ?, updated_at = ? WHERE user_id = ?"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (new_hashed_password, now, user_id))
        # conn.commit() # Handled by _manage_conn decorator
        if cursor.rowcount > 0:
            logger.info(f"Password hash upgraded and updated in DB for user ID '{user_id}'.")
            return True
        return False # Should not happen if user_id is valid
    except sqlite3.Error as e:
        logger.error(f"Database error updating password hash for user ID '{user_id}': {e}", exc_info=True)
        return False

@_manage_conn
def verify_user_password(username: str, password: str, conn: sqlite3.Connection = None) -> dict | None:
    """
    Verifies user credentials for login.
    Fetches user by username, checks if active, and verifies password.
    Returns user dictionary if valid and active, otherwise None.
    """
    if not username or not password:
        logger.warning("Username and password are required for verification.")
        return None

    user = get_user_by_username(username, conn=conn) # get_user_by_username is already decorated

    if user:
        if not user.get('is_active'):
            logger.warning(f"Login attempt for inactive user: {username}")
            return None

        # Ensure 'hashed_password' key exists, though it should if user record is proper
        if 'hashed_password' not in user:
            logger.error(f"User record for {username} is missing 'hashed_password'. Cannot verify.")
            return None

        # verify_password (the internal one) now calls utils.verify_password which returns a tuple
        verified, new_hash = verify_password(user['hashed_password'], password)

        if verified:
            logger.info(f"Password verification successful for user: {username}")
            # Update last login time
            record_login_time(user['user_id'], conn=conn)

            # If the hash was upgraded (old scheme), update it in the DB
            if new_hash:
                logger.info(f"Password hash for user '{username}' needs upgrade. New hash: {new_hash[:20]}...") # Log only part of hash
                if _update_user_password_hash_only(user['user_id'], new_hash, conn=conn):
                    logger.info(f"Successfully upgraded password hash for user '{username}'.")
                else:
                    logger.error(f"Failed to upgrade password hash for user '{username}' in database.")
                    # Depending on policy, this could be a critical error, but login can still proceed.

            return user  # Return the full user dictionary
        else:
            logger.warning(f"Password verification failed for user: {username}")
            return None
    else:
        logger.warning(f"Login attempt for non-existent user: {username}")
        return None

# For consistency, if there's an existing users_crud_instance, re-declare it or ensure it's updated.
# If the previous users_crud.py was very different, this overwrite is fine.
# users_crud_instance = UsersCRUD() # If it were a class-based CRUD
# For now, these are module-level functions.
