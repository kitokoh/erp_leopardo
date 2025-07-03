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

    # Added biometric fields to the INSERT statement, defaulting to disabled/NULL
    sql = """INSERT INTO Users (
                 user_id, username, hashed_password, full_name, email, role_id, is_active,
                 created_at, updated_at, last_login_at,
                 is_fingerprint_auth_enabled, fingerprint_template_id,
                 is_face_auth_enabled, face_template_id,
                 is_voice_auth_enabled, voice_profile_id
             ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, NULL, 0, NULL, 0, NULL, 0, NULL)"""
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
             WHERE u.username = ? AND u.is_active = 1 AND (u.is_deleted = 0 OR u.is_deleted IS NULL)"""
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
def list_users(role_id_filter: int = None, status_filter: str = None, include_deleted: bool = False, conn: sqlite3.Connection = None) -> list[dict]:
    """
    Lists all users with their role names, with optional filtering by role_id, active status, and deleted status.
    Args:
        role_id_filter (int, optional): Role ID to filter by. Defaults to None (no role filter).
        status_filter (str, optional): Status to filter by ('active', 'inactive'). Defaults to None (all statuses).
        include_deleted (bool, optional): Whether to include soft-deleted users. Defaults to False.
        conn (sqlite3.Connection, optional): Database connection.
    Returns:
        list[dict]: A list of user dictionaries.
    """
    params = []
    sql = """SELECT u.user_id, u.username, u.full_name, u.email, r.role_name, u.is_active, u.created_at, u.last_login_at, u.is_deleted, u.deleted_at
             FROM Users u
             JOIN Roles r ON u.role_id = r.role_id"""

    conditions = []
    if not include_deleted:
        conditions.append("(u.is_deleted = 0 OR u.is_deleted IS NULL)")

    if role_id_filter is not None:
        conditions.append("u.role_id = ?")
        params.append(role_id_filter)

    if status_filter == "active":
        conditions.append("u.is_active = 1")
    elif status_filter == "inactive":
        # When filtering for inactive, we should only show non-deleted inactive users
        # unless include_deleted is true.
        # If include_deleted is true, this filter might show users that are inactive AND deleted.
        conditions.append("u.is_active = 0")


    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += " ORDER BY u.username"

    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Database error listing users with filters (role_id: {role_id_filter}, status: {status_filter}): {e}", exc_info=True)
        return []

# Removed local verify_password function. Will use the one imported from utils directly.

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

        # Call the verify_password function imported from utils.
        # The expected signature is verify_password(plain_password, hashed_password)
        verified, new_hash = verify_password(password, user['hashed_password'])

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

@_manage_conn
def soft_delete_user(user_id_to_delete: str, current_user_id: str, conn: sqlite3.Connection = None) -> bool:
    """
    Soft deletes a user by setting is_deleted = 1, deleted_at = now(), and is_active = 0.
    Prevents self-deletion.
    """
    if user_id_to_delete == current_user_id:
        logger.error(f"User {current_user_id} cannot soft delete themselves.")
        # Consider raising a specific exception here if preferred for API/service layer handling
        return False

    now = datetime.utcnow().isoformat() + "Z"
    sql = """UPDATE Users
             SET is_deleted = 1,
                 deleted_at = ?,
                 is_active = 0,
                 updated_at = ?
             WHERE user_id = ?"""
    params = (now, now, user_id_to_delete)

    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        # conn.commit() # Handled by _manage_conn
        if cursor.rowcount > 0:
            logger.info(f"User {user_id_to_delete} soft deleted successfully by user {current_user_id}.")
            return True
        else:
            logger.warning(f"Soft delete failed for user {user_id_to_delete} (user not found or no change needed).")
            return False # User not found or already in desired state (though updated_at would change)
    except sqlite3.Error as e:
        logger.error(f"Database error soft deleting user {user_id_to_delete}: {e}", exc_info=True)
        return False

@_manage_conn
def set_biometric_auth_status(user_id: str, method: str, enabled: bool, template_id: str = None, conn: sqlite3.Connection = None) -> bool:
    """
    Sets the status (enabled/disabled) and template ID for a specific biometric authentication method for a user.

    Args:
        user_id (str): The ID of the user.
        method (str): The biometric method ('fingerprint', 'face', 'voice').
        enabled (bool): True to enable, False to disable.
        template_id (str, optional): The template ID provided by the OS/library. Defaults to None.
        conn (sqlite3.Connection, optional): Database connection.

    Returns:
        bool: True if the update was successful, False otherwise.
    """
    now = datetime.utcnow().isoformat() + "Z"
    enabled_int = 1 if enabled else 0

    field_enabled_map = {
        'fingerprint': 'is_fingerprint_auth_enabled',
        'face': 'is_face_auth_enabled',
        'voice': 'is_voice_auth_enabled'
    }
    field_template_id_map = {
        'fingerprint': 'fingerprint_template_id',
        'face': 'face_template_id',
        'voice': 'voice_profile_id'
    }

    if method not in field_enabled_map:
        logger.error(f"Invalid biometric method: {method}")
        return False

    sql = f"""UPDATE Users
              SET {field_enabled_map[method]} = ?,
                  {field_template_id_map[method]} = ?,
                  updated_at = ?
              WHERE user_id = ?"""

    # If disabling, template_id should usually be cleared.
    current_template_id = template_id if enabled else None
    params = (enabled_int, current_template_id, now, user_id)

    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        if cursor.rowcount > 0:
            logger.info(f"Biometric method '{method}' for user '{user_id}' set to {enabled} (Template ID: {current_template_id}).")
            return True
        else:
            logger.warning(f"No user found with ID '{user_id}' or no change made for biometric method '{method}'.")
            return False
    except sqlite3.Error as e:
        logger.error(f"Database error setting biometric auth status for user '{user_id}', method '{method}': {e}", exc_info=True)
        return False

@_manage_conn
def get_biometric_auth_status(user_id: str, conn: sqlite3.Connection = None) -> dict | None:
    """
    Retrieves the biometric authentication settings for a given user.

    Args:
        user_id (str): The ID of the user.
        conn (sqlite3.Connection, optional): Database connection.

    Returns:
        dict | None: A dictionary with biometric settings if user is found, otherwise None.
                     Example: {'is_fingerprint_auth_enabled': True, 'fingerprint_template_id': 'xyz', ...}
    """
    sql = """SELECT user_id, is_fingerprint_auth_enabled, fingerprint_template_id,
                    is_face_auth_enabled, face_template_id,
                    is_voice_auth_enabled, voice_profile_id
             FROM Users
             WHERE user_id = ?"""
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (user_id,))
        row = cursor.fetchone()
        if row:
            # Convert boolean fields from 0/1 to True/False if necessary, though dict(row) usually handles it.
            # Ensuring boolean conversion for clarity if values are consistently 0/1.
            user_settings = dict(row)
            for key in ['is_fingerprint_auth_enabled', 'is_face_auth_enabled', 'is_voice_auth_enabled']:
                if key in user_settings: # Check if key exists (it should from the SELECT)
                    user_settings[key] = bool(user_settings[key])
            return user_settings
        else:
            logger.warning(f"No biometric settings found for user ID '{user_id}' (user might not exist).")
            return None
    except sqlite3.Error as e:
        logger.error(f"Database error fetching biometric auth status for user '{user_id}': {e}", exc_info=True)
        return None
