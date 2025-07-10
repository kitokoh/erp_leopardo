# db/cruds/licenses_crud.py
import sqlite3
import logging
from datetime import datetime, timezone
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

def _is_sqlalchemy_conn(conn):
    """Checks if the connection is a SQLAlchemy Session or Connection."""
    return hasattr(conn, 'execute') and not hasattr(conn, 'cursor')

def _execute_commit(conn, sql_query, params=None):
    """Executes a query and commits. Handles both SQLAlchemy and sqlite3."""
    if _is_sqlalchemy_conn(conn):
        conn.execute(text(sql_query), params or {})
        conn.commit()
    else: # sqlite3 connection
        cursor = conn.cursor()
        cursor.execute(sql_query, params or ())
        conn.commit()

def _fetchone_as_dict(conn, sql_query, params=None):
    """Executes a query and returns one row as a dict. Handles both."""
    if _is_sqlalchemy_conn(conn):
        result = conn.execute(text(sql_query), params or {}).fetchone()
        return dict(result._mapping) if result else None
    else: # sqlite3 connection
        cursor = conn.cursor()
        cursor.execute(sql_query, params or ())
        row = cursor.fetchone()
        if row:
            return {desc[0]: value for desc, value in zip(cursor.description, row)}
        return None

def _fetchall_as_dict_list(conn, sql_query, params=None):
    """Executes a query and returns all rows as a list of dicts. Handles both."""
    if _is_sqlalchemy_conn(conn):
        results = conn.execute(text(sql_query), params or {}).fetchall()
        return [dict(row._mapping) for row in results]
    else: # sqlite3 connection
        cursor = conn.cursor()
        cursor.execute(sql_query, params or ())
        rows = cursor.fetchall()
        return [{desc[0]: value for desc, value in zip(cursor.description, row)} for row in rows]


def add_license(conn, license_data: dict) -> str | None:
    """
    Adds a new license to the database.
    Args:
        conn: Database connection object (sqlite3 or SQLAlchemy).
        license_data: A dictionary containing license details.
    Returns:
        The license_id if successful, None otherwise.
    """
    # SQL query remains the same, but placeholders differ for SQLAlchemy
    sql_insert = """
        INSERT INTO Licenses (
            license_id, user_id, license_type, license_key,
            activation_date, expiration_date, machine_info,
            is_active, created_at, updated_at
        ) VALUES (:license_id, :user_id, :license_type, :license_key,
                  :activation_date, :expiration_date, :machine_info,
                  :is_active, :created_at, :updated_at)
    """
    # For sqlite3, use ? placeholders
    sql_insert_sqlite = """
        INSERT INTO Licenses (
            license_id, user_id, license_type, license_key,
            activation_date, expiration_date, machine_info,
            is_active, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    now_utc_iso = datetime.now(timezone.utc).isoformat()
    activation_date_iso = license_data.get('activation_date').isoformat() if isinstance(license_data.get('activation_date'), datetime) else license_data.get('activation_date')
    expiration_date_iso = license_data.get('expiration_date').isoformat() if isinstance(license_data.get('expiration_date'), datetime) else license_data.get('expiration_date')

    params_dict = {
        'license_id': license_data.get('license_id'),
        'user_id': license_data.get('user_id'),
        'license_type': license_data.get('license_type'),
        'license_key': license_data.get('license_key'),
        'activation_date': activation_date_iso,
        'expiration_date': expiration_date_iso,
        'machine_info': license_data.get('machine_info'),
        'is_active': 1 if license_data.get('is_active', True) else 0,
        'created_at': now_utc_iso,
        'updated_at': now_utc_iso
    }
    params_tuple = tuple(params_dict.values()) # Order must match columns for sqlite

    logger.debug(f"Attempting to add license. Data: {params_dict}")
    try:
        sql_to_use = sql_insert if _is_sqlalchemy_conn(conn) else sql_insert_sqlite
        params_to_use = params_dict if _is_sqlalchemy_conn(conn) else params_tuple
        _execute_commit(conn, sql_to_use, params_to_use)
        logger.info(f"License {params_dict['license_id']} added for user {params_dict['user_id']}.")
        return params_dict['license_id']
    except (sqlite3.Error, SQLAlchemyError) as e:
        logger.error(f"Error adding license for user {params_dict['user_id']}. Error: {e}", exc_info=True)
        if not _is_sqlalchemy_conn(conn): # SQLAlchemy handles its own rollback usually with session context
            conn.rollback()
        return None

def get_active_license_for_user(conn, user_id: str) -> dict | None:
    """
    Retrieves the currently active license for a given user.
    An active license is one where is_active is TRUE and expiration_date is in the future.
    If multiple such licenses exist, it might return the one with the furthest expiration date or the most recently activated.
    For simplicity, this version returns the first one found that matches.
    """
    sql_query_sa = """
        SELECT * FROM Licenses
        WHERE user_id = :user_id
          AND is_active = 1
          AND (expiration_date IS NULL OR expiration_date > :now_utc_iso)
        ORDER BY expiration_date DESC, activation_date DESC
        LIMIT 1
    """
    sql_query_sqlite = """
        SELECT * FROM Licenses
        WHERE user_id = ?
          AND is_active = 1
          AND (expiration_date IS NULL OR expiration_date > ?)
        ORDER BY expiration_date DESC, activation_date DESC
        LIMIT 1
    """
    now_utc_iso = datetime.now(timezone.utc).isoformat()
    params_sa = {'user_id': user_id, 'now_utc_iso': now_utc_iso}
    params_sqlite = (user_id, now_utc_iso)

    try:
        sql_to_use = sql_query_sa if _is_sqlalchemy_conn(conn) else sql_query_sqlite
        params_to_use = params_sa if _is_sqlalchemy_conn(conn) else params_sqlite
        license_details = _fetchone_as_dict(conn, sql_to_use, params_to_use)

        if license_details:
            logger.debug(f"Active license found for user {user_id}: {license_details.get('license_id')}")
        else:
            logger.debug(f"No active license found for user {user_id}.")
        return license_details
    except (sqlite3.Error, SQLAlchemyError) as e:
        logger.error(f"Error retrieving active license for user {user_id}: {e}", exc_info=True)
        return None

def deactivate_license(conn, license_id: str) -> bool:
    """
    Deactivates a license by setting is_active to 0.
    """
    sql_sa = "UPDATE Licenses SET is_active = 0, updated_at = :now_utc_iso WHERE license_id = :license_id"
    sql_sqlite = "UPDATE Licenses SET is_active = 0, updated_at = ? WHERE license_id = ?"
    now_utc_iso = datetime.now(timezone.utc).isoformat()
    params_sa = {'now_utc_iso': now_utc_iso, 'license_id': license_id}
    params_sqlite = (now_utc_iso, license_id)

    try:
        sql_to_use = sql_sa if _is_sqlalchemy_conn(conn) else sql_sqlite
        params_to_use = params_sa if _is_sqlalchemy_conn(conn) else params_sqlite

        if _is_sqlalchemy_conn(conn):
            result = conn.execute(text(sql_to_use), params_to_use)
            conn.commit()
            rowcount = result.rowcount
        else:
            cursor = conn.cursor()
            cursor.execute(sql_to_use, params_to_use)
            conn.commit()
            rowcount = cursor.rowcount

        if rowcount > 0:
            logger.info(f"License {license_id} deactivated.")
            return True
        else:
            logger.warning(f"Attempted to deactivate license {license_id}, but license not found or no change made.")
            return False
    except (sqlite3.Error, SQLAlchemyError) as e:
        logger.error(f"Error deactivating license {license_id}: {e}", exc_info=True)
        if not _is_sqlalchemy_conn(conn):
            conn.rollback()
        return False

def get_license_by_key(conn, license_key: str) -> dict | None:
    """
    Retrieves a license by its license_key.
    """
    sql_sa = "SELECT * FROM Licenses WHERE license_key = :license_key"
    sql_sqlite = "SELECT * FROM Licenses WHERE license_key = ?"
    params_sa = {'license_key': license_key}
    params_sqlite = (license_key,)
    try:
        sql_to_use = sql_sa if _is_sqlalchemy_conn(conn) else sql_sqlite
        params_to_use = params_sa if _is_sqlalchemy_conn(conn) else params_sqlite
        return _fetchone_as_dict(conn, sql_to_use, params_to_use)
    except (sqlite3.Error, SQLAlchemyError) as e:
        logger.error(f"Error retrieving license by key {license_key}: {e}", exc_info=True)
        return None

def update_license(conn, license_id: str, license_data: dict) -> bool:
    """
    Updates an existing license with new data.
    Args:
        license_id (str): The ID of the license to update.
        license_data (dict): Dictionary containing fields to update, e.g.,
                             {'expiration_date': new_date, 'is_active': True/False, 'machine_info': new_machine_id}
    """
    if not license_data:
        logger.warning(f"No data provided for updating license {license_id}.")
        return False

    fields = []
    params_dict = {}
    params_sqlite_list = []

    for key, value in license_data.items():
        current_val = value.isoformat() if isinstance(value, datetime) else value
        if key in ['user_id', 'license_type', 'license_key', 'activation_date', 'expiration_date', 'machine_info', 'is_active']:
            if _is_sqlalchemy_conn(conn):
                fields.append(f"{key} = :{key}")
                params_dict[key] = current_val
            else:
                fields.append(f"{key} = ?")
                params_sqlite_list.append(current_val)

    if not fields:
        logger.warning(f"No valid fields provided for updating license {license_id}.")
        return False

    now_utc_iso = datetime.now(timezone.utc).isoformat()
    if _is_sqlalchemy_conn(conn):
        params_dict['updated_at'] = now_utc_iso
        params_dict['license_id_where'] = license_id # Use a different key for WHERE clause to avoid conflict if license_id is in update data
        sql_query = f"UPDATE Licenses SET {', '.join(fields)}, updated_at = :updated_at WHERE license_id = :license_id_where"
        params_to_use = params_dict
    else:
        params_sqlite_list.append(now_utc_iso) # updated_at
        params_sqlite_list.append(license_id)    # license_id for WHERE
        sql_query = f"UPDATE Licenses SET {', '.join(fields)}, updated_at = ? WHERE license_id = ?"
        params_to_use = tuple(params_sqlite_list)

    try:
        if _is_sqlalchemy_conn(conn):
            result = conn.execute(text(sql_query), params_to_use)
            conn.commit()
            rowcount = result.rowcount
        else:
            cursor = conn.cursor()
            cursor.execute(sql_query, params_to_use)
            conn.commit()
            rowcount = cursor.rowcount

        if rowcount > 0:
            logger.info(f"License {license_id} updated successfully.")
            return True
        else:
            logger.warning(f"License {license_id} not updated (not found or no change).")
            return False
    except (sqlite3.Error, SQLAlchemyError) as e:
        logger.error(f"Error updating license {license_id}: {e}", exc_info=True)
        if not _is_sqlalchemy_conn(conn):
            conn.rollback()
        return False

# Example of how to use:
# conn = get_db_connection() # Assuming get_db_connection is available
# if conn:
#     new_license_id = str(uuid.uuid4())
#     data = {
#         'license_id': new_license_id,
#         'user_id': 'some_user_id',
#         'license_type': 'complet',
#         'license_key': 'UNIQUE-KEY-123',
#         'activation_date': datetime.now(timezone.utc),
#         'expiration_date': datetime.now(timezone.utc) + timedelta(days=30),
#         'machine_info': 'machine_xyz',
#         'is_active': True
#     }
#     add_license(conn, data)
#     retrieved_license = get_active_license_for_user(conn, 'some_user_id')
#     if retrieved_license:
#         print(f"Active license: {retrieved_license}")
#     conn.close()

def get_license_by_key_and_machine(conn, license_key: str, machine_info: str) -> dict | None:
    """
    Retrieves a license by its license_key and machine_info.
    This is used to check if a specific signed key has already been activated on a particular machine.
    """
    sql_sa = "SELECT * FROM Licenses WHERE license_key = :license_key AND machine_info = :machine_info"
    sql_sqlite = "SELECT * FROM Licenses WHERE license_key = ? AND machine_info = ?"
    params_sa = {'license_key': license_key, 'machine_info': machine_info}
    params_sqlite = (license_key, machine_info)
    try:
        sql_to_use = sql_sa if _is_sqlalchemy_conn(conn) else sql_sqlite
        params_to_use = params_sa if _is_sqlalchemy_conn(conn) else params_sqlite
        result = _fetchone_as_dict(conn, sql_to_use, params_to_use)
        if result:
            logger.debug(f"License found for key '{license_key}' and machine '{machine_info}'.")
        else:
            logger.debug(f"No license found for key '{license_key}' and machine '{machine_info}'.")
        return result
    except (sqlite3.Error, SQLAlchemyError) as e:
        logger.error(f"Error retrieving license by key '{license_key}' and machine '{machine_info}': {e}", exc_info=True)
        return None

def has_any_active_complete_license(conn) -> bool:
    """
    Checks if there is any active 'complet' license in the system for any user.
    An active license is one where is_active is TRUE and expiration_date is in the future (or NULL).
    """
    sql_sa = """
        SELECT 1 FROM Licenses
        WHERE license_type = 'complet'
          AND is_active = 1
          AND (expiration_date IS NULL OR expiration_date > :now_utc_iso)
        LIMIT 1
    """
    sql_sqlite = """
        SELECT 1 FROM Licenses
        WHERE license_type = 'complet'
          AND is_active = 1
          AND (expiration_date IS NULL OR expiration_date > ?)
        LIMIT 1
    """
    now_utc_iso = datetime.now(timezone.utc).isoformat()
    params_sa = {'now_utc_iso': now_utc_iso}
    params_sqlite = (now_utc_iso,)

    try:
        sql_to_use = sql_sa if _is_sqlalchemy_conn(conn) else sql_sqlite
        params_to_use = params_sa if _is_sqlalchemy_conn(conn) else params_sqlite
        result = _fetchone_as_dict(conn, sql_to_use, params_to_use) # Using fetchone, expecting 0 or 1 row with a single col
        if result:
            logger.debug("Found at least one active 'complet' license in the system.")
            return True
        else:
            logger.debug("No active 'complet' licenses found in the system.")
            return False
    except (sqlite3.Error, SQLAlchemyError) as e:
        logger.error(f"Error checking for active 'complet' licenses: {e}", exc_info=True)
        return False # Fail safe: assume one might exist if check fails
