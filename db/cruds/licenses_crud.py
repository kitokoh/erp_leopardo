# db/cruds/licenses_crud.py
import sqlite3
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def add_license(conn: sqlite3.Connection, license_data: dict) -> str | None:
    """
    Adds a new license to the database.

    Args:
        conn: Database connection object.
        license_data: A dictionary containing license details:
            - license_id (str)
            - user_id (str)
            - license_type (str)
            - license_key (str, can be None)
            - activation_date (datetime)
            - expiration_date (datetime, can be None)
            - machine_info (str, can be None)
            - is_active (bool)
    Returns:
        The license_id if successful, None otherwise.
    """
    sql = """
        INSERT INTO Licenses (
            license_id, user_id, license_type, license_key,
            activation_date, expiration_date, machine_info,
            is_active, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    now_utc_iso = datetime.now(timezone.utc).isoformat()
    # Ensure datetime objects are converted to ISO format strings for SQLite
    activation_date_iso = license_data.get('activation_date').isoformat() if isinstance(license_data.get('activation_date'), datetime) else license_data.get('activation_date')
    expiration_date_iso = license_data.get('expiration_date').isoformat() if isinstance(license_data.get('expiration_date'), datetime) else license_data.get('expiration_date')

    params = (
        license_data.get('license_id'),
        license_data.get('user_id'),
        license_data.get('license_type'),
        license_data.get('license_key'),
        activation_date_iso,
        expiration_date_iso,
        license_data.get('machine_info'),
        1 if license_data.get('is_active', True) else 0,
        now_utc_iso,
        now_utc_iso
    )
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        logger.info(f"License {license_data.get('license_id')} added for user {license_data.get('user_id')}.")
        return license_data.get('license_id')
    except sqlite3.Error as e:
        logger.error(f"Error adding license for user {license_data.get('user_id')}: {e}", exc_info=True)
        conn.rollback()
        return None

def get_active_license_for_user(conn: sqlite3.Connection, user_id: str) -> dict | None:
    """
    Retrieves the currently active license for a given user.
    An active license is one where is_active is TRUE and expiration_date is in the future.
    If multiple such licenses exist, it might return the one with the furthest expiration date or the most recently activated.
    For simplicity, this version returns the first one found that matches.
    """
    sql = """
        SELECT * FROM Licenses
        WHERE user_id = ? AND is_active = 1
        ORDER BY expiration_date DESC, activation_date DESC
        LIMIT 1
    """
    # No, the above query is not quite right for "active and not expired".
    # SQLite doesn't have a native boolean TRUE, it uses 1.
    # Dates are stored as TEXT, so comparison needs care. ISO format strings compare correctly.

    sql_corrected = """
        SELECT * FROM Licenses
        WHERE user_id = ?
          AND is_active = 1
          AND (expiration_date IS NULL OR expiration_date > ?)
        ORDER BY expiration_date DESC, activation_date DESC
        LIMIT 1
    """
    now_utc_iso = datetime.now(timezone.utc).isoformat()

    try:
        cursor = conn.cursor()
        cursor.execute(sql_corrected, (user_id, now_utc_iso))
        row = cursor.fetchone()
        if row:
            license_details = dict(row)
            # Convert date strings back to datetime objects if needed by caller,
            # but for now, returning as stored.
            logger.debug(f"Active license found for user {user_id}: {license_details.get('license_id')}")
            return license_details
        else:
            logger.debug(f"No active license found for user {user_id}.")
            return None
    except sqlite3.Error as e:
        logger.error(f"Error retrieving active license for user {user_id}: {e}", exc_info=True)
        return None

def deactivate_license(conn: sqlite3.Connection, license_id: str) -> bool:
    """
    Deactivates a license by setting is_active to 0.
    """
    sql = "UPDATE Licenses SET is_active = 0, updated_at = ? WHERE license_id = ?"
    now_utc_iso = datetime.now(timezone.utc).isoformat()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (now_utc_iso, license_id))
        conn.commit()
        if cursor.rowcount > 0:
            logger.info(f"License {license_id} deactivated.")
            return True
        else:
            logger.warning(f"Attempted to deactivate license {license_id}, but license not found or no change made.")
            return False
    except sqlite3.Error as e:
        logger.error(f"Error deactivating license {license_id}: {e}", exc_info=True)
        conn.rollback()
        return False

def get_license_by_key(conn: sqlite3.Connection, license_key: str) -> dict | None:
    """
    Retrieves a license by its license_key.
    """
    sql = "SELECT * FROM Licenses WHERE license_key = ?"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (license_key,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    except sqlite3.Error as e:
        logger.error(f"Error retrieving license by key {license_key}: {e}", exc_info=True)
        return None

def update_license(conn: sqlite3.Connection, license_id: str, license_data: dict) -> bool:
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
    params = []
    for key, value in license_data.items():
        # Ensure datetime objects are converted
        if isinstance(value, datetime):
            current_val = value.isoformat()
        else:
            current_val = value

        if key in ['user_id', 'license_type', 'license_key', 'activation_date', 'expiration_date', 'machine_info', 'is_active']:
            fields.append(f"{key} = ?")
            params.append(current_val)

    if not fields:
        logger.warning(f"No valid fields provided for updating license {license_id}.")
        return False

    params.append(datetime.now(timezone.utc).isoformat()) # for updated_at
    params.append(license_id) # for WHERE clause

    sql = f"UPDATE Licenses SET {', '.join(fields)}, updated_at = ? WHERE license_id = ?"

    try:
        cursor = conn.cursor()
        cursor.execute(sql, tuple(params))
        conn.commit()
        logger.info(f"License {license_id} updated successfully.")
        return True
    except sqlite3.Error as e:
        logger.error(f"Error updating license {license_id}: {e}", exc_info=True)
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

def get_license_by_key_and_machine(conn: sqlite3.Connection, license_key: str, machine_info: str) -> dict | None:
    """
    Retrieves a license by its license_key and machine_info.
    This is used to check if a specific signed key has already been activated on a particular machine.
    """
    sql = "SELECT * FROM Licenses WHERE license_key = ? AND machine_info = ?"
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (license_key, machine_info))
        row = cursor.fetchone()
        if row:
            logger.debug(f"License found for key '{license_key}' and machine '{machine_info}'.")
            return dict(row)
        logger.debug(f"No license found for key '{license_key}' and machine '{machine_info}'.")
        return None
    except sqlite3.Error as e:
        logger.error(f"Error retrieving license by key '{license_key}' and machine '{machine_info}': {e}", exc_info=True)
        return None
