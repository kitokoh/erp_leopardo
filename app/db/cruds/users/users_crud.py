# db/cruds/users_crud.py
import sqlite3
import uuid
from datetime import datetime
import logging
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.engine import Engine, Connection as SQLAlchemyConnection
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError

from app.utils.auth import hash_password as util_hash_password, verify_password as util_verify_password
from app.db.generic_crud import _manage_conn
from app.models.db.users.user import User
from app.models.db.users.role import Role

module_logger = logging.getLogger(__name__)

def _get_cursor_and_dialect(db_session_or_conn):
    if isinstance(db_session_or_conn, (Session, Engine, SQLAlchemyConnection)):
        return db_session_or_conn, "sqlalchemy"
    elif hasattr(db_session_or_conn, 'cursor'):
        return db_session_or_conn.cursor(), "sqlite"
    return None, None

def _execute_query(conn_or_cursor, sql_text, params, dialect):
    if dialect == "sqlalchemy":
        return conn_or_cursor.execute(sql_text, params)
    elif dialect == "sqlite":
        return conn_or_cursor.execute(sql_text, params)
    return None

def _fetch_one_as_dict(conn_or_cursor, sql_query_sa, sql_query_sqlite, params_sa, params_sqlite, dialect, logger_to_use):
    try:
        row_data = None
        if dialect == "sqlalchemy":
            result = conn_or_cursor.execute(sql_query_sa, params_sa)
            row = result.fetchone()
            if row: row_data = dict(row._mapping)
        elif dialect == "sqlite":
            conn_or_cursor.execute(sql_query_sqlite, params_sqlite)
            row = conn_or_cursor.fetchone()
            if row:
                column_names = [desc[0] for desc in conn_or_cursor.description]
                row_data = dict(zip(column_names, row))
        return row_data
    except (sqlite3.Error, SQLAlchemyError) as e:
        logger_to_use.error(f"Database error during fetch one: {e}", exc_info=True)
        return None

def _fetch_all_as_dict_list(conn_or_cursor, sql_query_sa, sql_query_sqlite, params_sa, params_sqlite, dialect, logger_to_use):
    try:
        rows_data = []
        if dialect == "sqlalchemy":
            result = conn_or_cursor.execute(sql_query_sa, params_sa)
            for row in result.fetchall():
                rows_data.append(dict(row._mapping))
        elif dialect == "sqlite":
            conn_or_cursor.execute(sql_query_sqlite, params_sqlite)
            rows = conn_or_cursor.fetchall()
            if rows:
                column_names = [desc[0] for desc in conn_or_cursor.description]
                for row in rows:
                    rows_data.append(dict(zip(column_names, row)))
        return rows_data
    except (sqlite3.Error, SQLAlchemyError) as e:
        logger_to_use.error(f"Database error during fetch all: {e}", exc_info=True)
        return []

def add_user(db: Session, username: str, password: str, role_id: int, full_name: str = None, email: str = None, logger_passed: logging.Logger | None = None) -> str | None:
    current_logger = logger_passed if logger_passed else module_logger
    if not username or not password or role_id is None:
        current_logger.error("Username, password, and role_id are required.")
        return None

    final_hashed_password = util_hash_password(password, logger_passed=current_logger)
    user_id_generated = str(uuid.uuid4())
    now_iso = datetime.utcnow().isoformat() + "Z"

    db_obj, dialect = _get_cursor_and_dialect(db)
    if not db_obj or not dialect:
        current_logger.error(f"Unsupported connection type: {type(db)}")
        return None

    try:
        if dialect == "sqlalchemy":
            new_user = User(
                user_id=user_id_generated, username=username, hashed_password=final_hashed_password,
                full_name=full_name, email=email, role_id=role_id, is_active=True,
                created_at=datetime.utcnow(), updated_at=datetime.utcnow()
            )
            db_obj.add(new_user)
            db_obj.commit()
        else: # sqlite dialect
            sql_sqlite = """
                INSERT INTO Users (user_id, username, hashed_password, full_name, email, role_id, is_active, created_at, updated_at, is_deleted)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, 0)
            """
            params_sqlite = (user_id_generated, username, final_hashed_password, full_name, email, role_id, now_iso, now_iso)
            db_obj.execute(sql_sqlite, params_sqlite)
            # The raw connection is expected to be committed by the caller in the seeder.

        current_logger.info(f"User '{username}' added successfully with ID {user_id_generated}.")
        return user_id_generated
    except (sqlite3.Error, SQLAlchemyError) as e:
        current_logger.error(f"Error adding user '{username}': {e}", exc_info=True)
        if isinstance(db, Session):
            db.rollback()
        return None

def get_user_by_username(db: Session, username: str, logger_passed: logging.Logger | None = None) -> User | None:
    current_logger = logger_passed if logger_passed else module_logger
    current_logger.debug(f"Searching for active user: {username}")
    try:
        # Use joinedload to eagerly fetch the Role relationship, preventing subsequent queries
        user = db.query(User).options(joinedload(User.role)).filter(User.username == username, User.is_active == True, User.is_deleted == False).first()
        if user:
            current_logger.debug(f"User '{username}' found.")
        else:
            current_logger.debug(f"User '{username}' not found.")
        return user
    except SQLAlchemyError as e:
        current_logger.error(f"Database error getting user by username '{username}': {e}", exc_info=True)
        return None

def get_any_user_by_username(db: Session, username: str, logger_passed: logging.Logger | None = None) -> dict | None:
    """Fetches a user by username, regardless of their is_active or is_deleted status."""
    current_logger = logger_passed if logger_passed else module_logger
    sql_select_part = "SELECT u.*, r.role_name FROM Users u LEFT JOIN Roles r ON u.role_id = r.role_id"


    sql_sqlite = f"{sql_select_part} WHERE u.username = ?"
    sql_sa = text(f"{sql_select_part} WHERE u.username = :username")

    params_sa = {"username": username}
    params_sqlite = (username,)

    db_obj, dialect = _get_cursor_and_dialect(db)
    if not db_obj or not dialect:
        current_logger.error(f"Unsupported connection type: {type(db)}")
        return None

    user_data = _fetch_one_as_dict(db_obj, sql_sa, sql_sqlite, params_sa, params_sqlite, dialect, current_logger)

    if user_data:
        current_logger.debug(f"Any user (active or not) '{username}' found. Hash: {user_data.get('hashed_password')}")
    else:
        current_logger.debug(f"Any user (active or not) '{username}' not found.")
    return user_data

def get_user_by_id(db: Session, user_id: str, logger_passed: logging.Logger | None = None) -> User | None:
    """
    Retrieves a user by their ID from the database using the ORM.
    """
    current_logger = logger_passed if logger_passed else module_logger
    try:
        # Use joinedload to eagerly fetch the Role relationship
        user = db.query(User).options(joinedload(User.role)).filter(User.user_id == user_id).first()
        if user:
            current_logger.debug(f"User with ID '{user_id}' found.")
        else:
            current_logger.debug(f"User with ID '{user_id}' not found.")
        return user
    except SQLAlchemyError as e:
        current_logger.error(f"Database error getting user by ID '{user_id}': {e}", exc_info=True)
        return None

def update_user_role(db: Session, user_id: str, new_role_id: int, logger_passed: logging.Logger | None = None) -> bool:
    current_logger = logger_passed if logger_passed else module_logger
    now_iso = datetime.utcnow().isoformat() + "Z"

    sql_sqlite = "UPDATE Users SET role_id = ?, updated_at = ? WHERE user_id = ?"
    sql_sa = text("UPDATE Users SET role_id = :new_role_id, updated_at = :updated_at WHERE user_id = :user_id")

    params_sa = {"new_role_id": new_role_id, "updated_at": now_iso, "user_id": user_id}
    params_sqlite = (new_role_id, now_iso, user_id)

    db_obj, dialect = _get_cursor_and_dialect(db)
    if not db_obj or not dialect: return False

    try:
        result = _execute_query(db_obj, sql_sa if dialect == "sqlalchemy" else sql_sqlite, params_sa if dialect == "sqlalchemy" else params_sqlite, dialect)
        return result.rowcount > 0 if result else False
    except (sqlite3.Error, SQLAlchemyError) as e:
        current_logger.error(f"DB error updating role for user ID '{user_id}': {e}", exc_info=True)
        return False

def update_user_password(db: Session, user_id: str, new_password: str, logger_passed: logging.Logger | None = None) -> bool:
    current_logger = logger_passed if logger_passed else module_logger
    if not new_password:
        current_logger.error("New password cannot be empty.")
        return False

    hashed_pw = util_hash_password(new_password, logger_passed=current_logger)
    now_iso = datetime.utcnow().isoformat() + "Z"

    sql_sqlite = "UPDATE Users SET hashed_password = ?, updated_at = ? WHERE user_id = ?"
    sql_sa = text("UPDATE Users SET hashed_password = :hashed_password, updated_at = :updated_at WHERE user_id = :user_id")

    params_sa = {"hashed_password": hashed_pw, "updated_at": now_iso, "user_id": user_id}
    params_sqlite = (hashed_pw, now_iso, user_id)

    db_obj, dialect = _get_cursor_and_dialect(db)
    if not db_obj or not dialect: return False

    try:
        current_logger.debug(f"Updating password for user_id '{user_id}'. New hash: {hashed_pw}")
        result = _execute_query(db_obj, sql_sa if dialect == "sqlalchemy" else sql_sqlite, params_sa if dialect == "sqlalchemy" else params_sqlite, dialect)
        success = result.rowcount > 0 if result else False
        if success: current_logger.info(f"Password updated for user_id '{user_id}'.")
        else: current_logger.warning(f"Password update for user_id '{user_id}' affected 0 rows.")
        return success
    except (sqlite3.Error, SQLAlchemyError) as e:
        current_logger.error(f"DB error updating password for user ID '{user_id}': {e}", exc_info=True)
        return False

def set_user_active_status(db: Session, user_id: str, is_active: bool, logger_passed: logging.Logger | None = None) -> bool:
    current_logger = logger_passed if logger_passed else module_logger
    now_iso = datetime.utcnow().isoformat() + "Z"
    status_int = 1 if is_active else 0

    sql_sqlite = "UPDATE Users SET is_active = ?, updated_at = ? WHERE user_id = ?"
    sql_sa = text("UPDATE Users SET is_active = :is_active, updated_at = :updated_at WHERE user_id = :user_id")

    params_sa = {"is_active": status_int, "updated_at": now_iso, "user_id": user_id}
    params_sqlite = (status_int, now_iso, user_id)

    db_obj, dialect = _get_cursor_and_dialect(db)
    if not db_obj or not dialect: return False

    try:
        result = _execute_query(db_obj, sql_sa if dialect == "sqlalchemy" else sql_sqlite, params_sa if dialect == "sqlalchemy" else params_sqlite, dialect)
        return result.rowcount > 0 if result else False
    except (sqlite3.Error, SQLAlchemyError) as e:
        current_logger.error(f"DB error setting active status for user ID '{user_id}': {e}", exc_info=True)
        return False

def record_login_time(db: Session, user_id: str, logger_passed: logging.Logger | None = None) -> bool:
    current_logger = logger_passed if logger_passed else module_logger
    now_iso = datetime.utcnow().isoformat() + "Z"

    sql_sqlite = "UPDATE Users SET last_login_at = ? WHERE user_id = ?"
    sql_sa = text("UPDATE Users SET last_login_at = :last_login_at WHERE user_id = :user_id")

    params_sa = {"last_login_at": now_iso, "user_id": user_id}
    params_sqlite = (now_iso, user_id)

    db_obj, dialect = _get_cursor_and_dialect(db)
    if not db_obj or not dialect: return False

    try:
        result = _execute_query(db_obj, sql_sa if dialect == "sqlalchemy" else sql_sqlite, params_sa if dialect == "sqlalchemy" else params_sqlite, dialect)
        return result.rowcount > 0 if result else False
    except (sqlite3.Error, SQLAlchemyError) as e:
        current_logger.error(f"DB error recording login time for user ID '{user_id}': {e}", exc_info=True)
        return False

def list_users(db: Session, role_id_filter: int = None, status_filter: str = None, include_deleted: bool = False, logger_passed: logging.Logger | None = None) -> list[dict]:
    current_logger = logger_passed if logger_passed else module_logger

    base_sql = "SELECT u.user_id, u.username, u.full_name, u.email, r.role_name, u.is_active, u.created_at, u.last_login_at, u.is_deleted, u.deleted_at FROM Users u JOIN Roles r ON u.role_id = r.role_id"
    conditions_sqlite = []
    conditions_sa_str = []
    params_sqlite = []
    params_sa = {}

    if not include_deleted:
        conditions_sqlite.append("(u.is_deleted = 0 OR u.is_deleted IS NULL)")
        conditions_sa_str.append("(u.is_deleted = 0 OR u.is_deleted IS NULL)")

    if role_id_filter is not None:
        conditions_sqlite.append("u.role_id = ?")
        params_sqlite.append(role_id_filter)
        conditions_sa_str.append("u.role_id = :role_id_filter")
        params_sa["role_id_filter"] = role_id_filter

    if status_filter == "active":
        conditions_sqlite.append("u.is_active = 1")
        conditions_sa_str.append("u.is_active = 1")
    elif status_filter == "inactive":
        conditions_sqlite.append("u.is_active = 0")
        conditions_sa_str.append("u.is_active = 0")

    where_clause_sqlite = (" WHERE " + " AND ".join(conditions_sqlite)) if conditions_sqlite else ""
    where_clause_sa = (" WHERE " + " AND ".join(conditions_sa_str)) if conditions_sa_str else ""

    final_sql_sqlite = f"{base_sql}{where_clause_sqlite} ORDER BY u.username"
    final_sql_sa = text(f"{base_sql}{where_clause_sa} ORDER BY u.username")

    db_obj, dialect = _get_cursor_and_dialect(db)
    if not db_obj or not dialect: return []

    return _fetch_all_as_dict_list(db_obj, final_sql_sa, final_sql_sqlite, params_sa, params_sqlite, dialect, current_logger)


def _update_user_password_hash_only(db: Session, user_id: str, new_hashed_password: str, logger_passed: logging.Logger | None = None) -> bool:
    current_logger = logger_passed if logger_passed else module_logger
    now_iso = datetime.utcnow().isoformat() + "Z"

    sql_sqlite = "UPDATE Users SET hashed_password = ?, updated_at = ? WHERE user_id = ?"
    sql_sa = text("UPDATE Users SET hashed_password = :new_hashed_password, updated_at = :updated_at WHERE user_id = :user_id")

    params_sa = {"new_hashed_password": new_hashed_password, "updated_at": now_iso, "user_id": user_id}
    params_sqlite = (new_hashed_password, now_iso, user_id)

    db_obj, dialect = _get_cursor_and_dialect(db)
    if not db_obj or not dialect: return False

    try:
        result = _execute_query(db_obj, sql_sa if dialect == "sqlalchemy" else sql_sqlite, params_sa if dialect == "sqlalchemy" else params_sqlite, dialect)
        if result and result.rowcount > 0:
            current_logger.info(f"Password hash upgraded for user ID '{user_id}'.")
            return True
        return False
    except (sqlite3.Error, SQLAlchemyError) as e:
        current_logger.error(f"DB error updating password hash for user ID '{user_id}': {e}", exc_info=True)
        return False


def verify_user_password(db: Session, username: str, password: str, logger_passed: logging.Logger | None = None) -> dict | None:
    current_logger = logger_passed if logger_passed else module_logger
    if not username or not password:
        current_logger.warning("Username and password are required for verification.")
        return None

    user = get_user_by_username(username, db=db, logger_passed=current_logger)

    if user:
        if not user.get('is_active'):
            current_logger.warning(f"Login attempt for inactive user: {username}")
            return None
        if 'hashed_password' not in user:
            current_logger.error(f"User record for {username} missing 'hashed_password'.")
            return None

        verified, new_hash = util_verify_password(password, user['hashed_password'], logger_passed=current_logger)

        if verified:
            current_logger.info(f"Password verification successful for user: {username}")
            record_login_time(user['user_id'], db=db, logger_passed=current_logger)
            if new_hash:
                current_logger.info(f"Password hash for user '{username}' needs upgrade.")
                if _update_user_password_hash_only(user['user_id'], new_hash, db=db, logger_passed=current_logger):
                    current_logger.info(f"Upgraded password hash for user '{username}'.")
                else:
                    current_logger.error(f"Failed to upgrade password hash for user '{username}'.")
            return user
        else:
            current_logger.warning(f"Password verification failed for user: {username}")
            return None
    else:
        current_logger.warning(f"Login attempt for non-existent user: {username}")
        return None

def soft_delete_user(db: Session, user_id_to_delete: str, current_user_id: str, logger_passed: logging.Logger | None = None) -> bool:
    current_logger = logger_passed if logger_passed else module_logger
    if user_id_to_delete == current_user_id:
        current_logger.error(f"User {current_user_id} cannot soft delete themselves.")
        return False

    now_iso = datetime.utcnow().isoformat() + "Z"
    sql_update = "UPDATE Users SET is_deleted = 1, deleted_at = :deleted_at, is_active = 0, updated_at = :updated_at WHERE user_id = :user_id"

    sql_sqlite = "UPDATE Users SET is_deleted = 1, deleted_at = ?, is_active = 0, updated_at = ? WHERE user_id = ?"
    sql_sa = text(sql_update)

    params_sa = {"deleted_at": now_iso, "updated_at": now_iso, "user_id": user_id_to_delete}
    params_sqlite = (now_iso, now_iso, user_id_to_delete)

    db_obj, dialect = _get_cursor_and_dialect(db)
    if not db_obj or not dialect: return False

    try:
        result = _execute_query(db_obj, sql_sa if dialect == "sqlalchemy" else sql_sqlite, params_sa if dialect == "sqlalchemy" else params_sqlite, dialect)
        if result and result.rowcount > 0:
            current_logger.info(f"User {user_id_to_delete} soft deleted by {current_user_id}.")
            return True
        else:
            current_logger.warning(f"Soft delete failed for user {user_id_to_delete} (not found or no change).")
            return False
    except (sqlite3.Error, SQLAlchemyError) as e:
        current_logger.error(f"DB error soft deleting user {user_id_to_delete}: {e}", exc_info=True)
        return False

def set_biometric_auth_status(db: Session, user_id: str, method: str, enabled: bool, template_id: str = None, logger_passed: logging.Logger | None = None) -> bool:
    current_logger = logger_passed if logger_passed else module_logger
    now_iso = datetime.utcnow().isoformat() + "Z"
    enabled_int = 1 if enabled else 0

    field_map = {
        'fingerprint': ('is_fingerprint_auth_enabled', 'fingerprint_template_id'),
        'face': ('is_face_auth_enabled', 'face_template_id'),
        'voice': ('is_voice_auth_enabled', 'voice_profile_id')
    }
    if method not in field_map:
        current_logger.error(f"Invalid biometric method: {method}")
        return False

    enabled_field, template_field = field_map[method]
    current_template_id = template_id if enabled else None

    sql_sqlite = f"UPDATE Users SET {enabled_field} = ?, {template_field} = ?, updated_at = ? WHERE user_id = ?"
    sql_sa = text(f"UPDATE Users SET {enabled_field} = :{enabled_field}, {template_field} = :{template_field}, updated_at = :updated_at WHERE user_id = :user_id")

    params_sa = {
        enabled_field: enabled_int, template_field: current_template_id,
        "updated_at": now_iso, "user_id": user_id
    }
    params_sqlite = (enabled_int, current_template_id, now_iso, user_id)

    db_obj, dialect = _get_cursor_and_dialect(db)
    if not db_obj or not dialect: return False

    try:
        result = _execute_query(db_obj, sql_sa if dialect == "sqlalchemy" else sql_sqlite, params_sa if dialect == "sqlalchemy" else params_sqlite, dialect)
        if result and result.rowcount > 0:
            current_logger.info(f"Biometric '{method}' for user '{user_id}' set to {enabled}.")
            return True
        else:
            current_logger.warning(f"No user '{user_id}' or no change for biometric '{method}'.")
            return False
    except (sqlite3.Error, SQLAlchemyError) as e:
        current_logger.error(f"DB error setting biometric for user '{user_id}', method '{method}': {e}", exc_info=True)
        return False

def get_biometric_auth_status(db: Session, user_id: str, logger_passed: logging.Logger | None = None) -> dict | None:
    current_logger = logger_passed if logger_passed else module_logger
    sql_select = """SELECT user_id, is_fingerprint_auth_enabled, fingerprint_template_id,
                           is_face_auth_enabled, face_template_id,
                           is_voice_auth_enabled, voice_profile_id
                    FROM Users"""

    sql_sqlite = f"{sql_select} WHERE user_id = ?"
    sql_sa = text(f"{sql_select} WHERE user_id = :user_id")

    params_sa = {"user_id": user_id}
    params_sqlite = (user_id,)

    db_obj, dialect = _get_cursor_and_dialect(db)
    if not db_obj or not dialect: return None

    user_settings = _fetch_one_as_dict(db_obj, sql_sa, sql_sqlite, params_sa, params_sqlite, dialect, current_logger)

    if user_settings:
        for key in ['is_fingerprint_auth_enabled', 'is_face_auth_enabled', 'is_voice_auth_enabled']:
            if key in user_settings: user_settings[key] = bool(user_settings[key])
        return user_settings
    else:
        current_logger.warning(f"No biometric settings for user ID '{user_id}'.")
        return None

def activate_and_update_user_details(
    db: Session,
    user_id: str,
    role_id: int,
    password: str, # Plain text password, will be hashed
    full_name: str,
    email: str,
    logger_passed: logging.Logger | None = None
) -> bool:
    current_logger = logger_passed if logger_passed else module_logger
    now_iso = datetime.utcnow().isoformat() + "Z"

    if not password:
        current_logger.error(f"Password cannot be empty for user update (ID: {user_id}).")
        return False

    hashed_new_password = util_hash_password(password, logger_passed=current_logger)

    sql_sqlite = """
        UPDATE Users
        SET role_id = ?,
            hashed_password = ?,
            full_name = ?,
            email = ?,
            is_active = 1,
            is_deleted = 0,
            deleted_at = NULL,
            updated_at = ?
        WHERE user_id = ?
    """
    sql_sa = text("""
        UPDATE Users
        SET role_id = :role_id,
            hashed_password = :hashed_password,
            full_name = :full_name,
            email = :email,
            is_active = 1,
            is_deleted = 0,
            deleted_at = NULL,
            updated_at = :updated_at
        WHERE user_id = :user_id
    """)

    params_sa = {
        "role_id": role_id,
        "hashed_password": hashed_new_password,
        "full_name": full_name,
        "email": email,
        "updated_at": now_iso,
        "user_id": user_id
    }
    params_sqlite = (role_id, hashed_new_password, full_name, email, now_iso, user_id)

    db_obj, dialect = _get_cursor_and_dialect(db)
    if not db_obj or not dialect:
        current_logger.error(f"Unsupported connection type for activate_and_update_user_details: {type(db)}")
        return False

    try:
        result = _execute_query(db_obj, sql_sa if dialect == "sqlalchemy" else sql_sqlite, params_sa if dialect == "sqlalchemy" else params_sqlite, dialect)
        if result and result.rowcount > 0:
            current_logger.info(f"User '{user_id}' activated and details updated successfully.")
            return True
        else:
            current_logger.warning(f"Failed to activate/update user '{user_id}' (user not found or no changes made).")
            return False
    except (sqlite3.Error, SQLAlchemyError) as e:
        current_logger.error(f"Database error activating/updating user '{user_id}': {e}", exc_info=True)
        # Rollback is assumed to be handled by @_manage_conn
        return False

def get_user_by_email(db: Session, email: str, logger_passed: logging.Logger | None = None) -> dict | None:
    current_logger = logger_passed if logger_passed else module_logger
    sql_select_part = "SELECT u.*, r.role_name FROM Users u JOIN Roles r ON u.role_id = r.role_id"

    sql_sqlite = f"{sql_select_part} WHERE u.email = ? AND (u.is_deleted = 0 OR u.is_deleted IS NULL)"
    sql_sa = text(f"{sql_select_part} WHERE u.email = :email AND (u.is_deleted = 0 OR u.is_deleted IS NULL)")

    params_sa = {"email": email}
    params_sqlite = (email,)

    db_obj, dialect = _get_cursor_and_dialect(db)
    if not db_obj or not dialect: return None

    user_data = _fetch_one_as_dict(db_obj, sql_sa, sql_sqlite, params_sa, params_sqlite, dialect, current_logger)

    if user_data: current_logger.debug(f"User with email '{email}' found.")
    else: current_logger.debug(f"User with email '{email}' not found.")
    return user_data
        # # return None


def is_users_table_empty(db: Session, logger_passed: logging.Logger | None = None) -> bool:
    """
    Checks if the Users table is empty.
    """
    current_logger = logger_passed if logger_passed else module_logger
    sql_sqlite = "SELECT 1 FROM Users LIMIT 1"
    sql_sa = text(sql_sqlite)

    db_obj, dialect = _get_cursor_and_dialect(db)
    if not db_obj or not dialect:
        current_logger.error(f"Unsupported connection type: {type(db)}")
        return True  # Assume empty on error to be safe

    try:
        result = _execute_query(db_obj, sql_sqlite if dialect == "sqlite" else sql_sa, {}, dialect)
        return result.fetchone() is None
    except (sqlite3.Error, SQLAlchemyError) as e:
        current_logger.error(f"Database error checking if users table is empty: {e}", exc_info=True)
        return True # Assume empty on error
