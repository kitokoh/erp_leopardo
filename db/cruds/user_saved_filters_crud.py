# db/cruds/user_saved_filters_crud.py
import json
import logging
from db.connection import get_db_connection
from datetime import datetime

def add_saved_filter(user_id: str, filter_name: str, filter_parameters: dict) -> int | None:
    """
    Adds a new saved filter configuration for a user.

    Args:
        user_id: The ID of the user saving the filter.
        filter_name: The name given to the filter by the user.
        filter_parameters: A dictionary containing the filter criteria.

    Returns:
        The ID of the newly inserted filter, or None on failure.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Optional: Check for uniqueness if the unique index idx_user_saved_filters_user_filter_name is used
        # This check is better handled by the database constraint itself if defined.
        # cursor.execute("SELECT id FROM user_saved_filters WHERE user_id = ? AND filter_name = ?", (user_id, filter_name))
        # if cursor.fetchone():
        #     logging.warning(f"User {user_id} already has a filter named '{filter_name}'.")
        #     # Consider raising a custom exception for duplicate name if not handled by DB constraint message
        #     return None

        filter_parameters_json = json.dumps(filter_parameters)
        current_timestamp = datetime.utcnow().isoformat() + "Z" # Ensure ISO 8601 format with Z for UTC

        cursor.execute("""
            INSERT INTO user_saved_filters (user_id, filter_name, filter_parameters_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, filter_name, filter_parameters_json, current_timestamp, current_timestamp))

        conn.commit()
        new_filter_id = cursor.lastrowid
        logging.info(f"Saved filter '{filter_name}' for user {user_id} with ID {new_filter_id}.")
        return new_filter_id
    except Exception as e: # Consider catching specific sqlite3.IntegrityError for unique constraint
        if conn:
            conn.rollback()
        logging.error(f"Error adding saved filter for user {user_id}, name '{filter_name}': {e}", exc_info=True)
        # Re-raise or return a more specific error/value if needed by UI
        # For example, if it's a unique constraint violation for filter_name
        if "UNIQUE constraint failed: user_saved_filters.user_id, user_saved_filters.filter_name" in str(e):
             # This specific error message might vary slightly based on DB/driver
             logging.warning(f"Attempt to add duplicate filter name '{filter_name}' for user {user_id}.")
             # The UI should ideally handle this by informing the user.
             # Returning None here is one way; raising a custom exception is another.
        return None
    finally:
        if conn:
            conn.close()

def get_saved_filters_for_user(user_id: str) -> list[dict]:
    """
    Retrieves all saved filters for a specific user.

    Args:
        user_id: The ID of the user.

    Returns:
        A list of dictionaries, each representing a saved filter.
        Each dictionary includes 'id', 'filter_name', and 'filter_parameters' (parsed from JSON).
        Returns an empty list if no filters are found or an error occurs.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Ensure row_factory is set for dictionary-like access if get_db_connection doesn't set it globally
        # conn.row_factory = sqlite3.Row # Example for sqlite3

        cursor.execute("""
            SELECT id, user_id, filter_name, filter_parameters_json, created_at, updated_at
            FROM user_saved_filters
            WHERE user_id = ?
            ORDER BY filter_name ASC
        """, (user_id,))

        filters_list = []
        # Assuming cursor.fetchall() returns list of tuples or Row objects
        # Need to access by index or column name string if Row factory is used.
        # For simplicity, assuming get_db_connection sets up row_factory for dict-like access.
        raw_rows = cursor.fetchall()
        for row in raw_rows:
            # Convert row to dict if it's not already (e.g., if it's a tuple)
            # This depends on how get_db_connection configures cursors.
            # If it's a tuple: row_dict = dict(zip([col[0] for col in cursor.description], row))
            # If row_factory=sqlite3.Row is used, can access by key: row['id'], row['filter_name']
            row_dict = dict(row) # This works if conn.row_factory = sqlite3.Row was set

            try:
                filter_params_dict = json.loads(row_dict['filter_parameters_json'])
                filters_list.append({
                    'id': row_dict['id'],
                    'user_id': row_dict['user_id'],
                    'filter_name': row_dict['filter_name'],
                    'filter_parameters': filter_params_dict,
                    'created_at': row_dict['created_at'],
                    'updated_at': row_dict['updated_at']
                })
            except json.JSONDecodeError as je:
                logging.error(f"Error decoding JSON for filter ID {row_dict['id']}: {je}")
        return filters_list
    except Exception as e:
        logging.error(f"Error retrieving saved filters for user {user_id}: {e}", exc_info=True)
        return []
    finally:
        if conn:
            conn.close()

def get_saved_filter_by_id(saved_filter_id: int, user_id: str) -> dict | None:
    """
    Retrieves a specific saved filter by its ID, ensuring it belongs to the user.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, filter_name, filter_parameters_json, created_at, updated_at
            FROM user_saved_filters
            WHERE id = ? AND user_id = ?
        """, (saved_filter_id, user_id))

        row = cursor.fetchone()
        if row:
            row_dict = dict(row)
            try:
                filter_params_dict = json.loads(row_dict['filter_parameters_json'])
                return {
                    'id': row_dict['id'],
                    'user_id': row_dict['user_id'],
                    'filter_name': row_dict['filter_name'],
                    'filter_parameters': filter_params_dict,
                    'created_at': row_dict['created_at'],
                    'updated_at': row_dict['updated_at']
                }
            except json.JSONDecodeError as je:
                logging.error(f"Error decoding JSON for filter ID {row_dict['id']}: {je}")
                return None
        return None
    except Exception as e:
        logging.error(f"Error retrieving saved filter ID {saved_filter_id} for user {user_id}: {e}", exc_info=True)
        return None
    finally:
        if conn:
            conn.close()

def update_saved_filter(saved_filter_id: int, user_id: str,
                        new_name: str = None, new_filter_parameters: dict = None) -> bool:
    """
    Updates the name and/or parameters of an existing saved filter.
    """
    if new_name is None and new_filter_parameters is None:
        logging.info("No changes provided for update_saved_filter.")
        return False

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        fields_to_update = []
        params_for_sql = [] # Renamed to avoid conflict with function parameter

        if new_name is not None:
            fields_to_update.append("filter_name = ?")
            params_for_sql.append(new_name)

        if new_filter_parameters is not None:
            fields_to_update.append("filter_parameters_json = ?")
            params_for_sql.append(json.dumps(new_filter_parameters))

        if not fields_to_update:
            return True

        fields_to_update.append("updated_at = ?")
        params_for_sql.append(datetime.utcnow().isoformat() + "Z")

        params_for_sql.extend([saved_filter_id, user_id])

        sql = f"UPDATE user_saved_filters SET {', '.join(fields_to_update)} WHERE id = ? AND user_id = ?"

        cursor.execute(sql, tuple(params_for_sql))
        conn.commit()

        if cursor.rowcount == 0:
            logging.warning(f"No filter found with ID {saved_filter_id} for user {user_id}, or no update made (e.g. name collision if constraint exists).")
            return False # Or raise an error if name collision is an issue handled by DB

        logging.info(f"Updated filter ID {saved_filter_id} for user {user_id}.")
        return True
    except Exception as e: # Consider catching specific sqlite3.IntegrityError
        if conn:
            conn.rollback()
        logging.error(f"Error updating filter ID {saved_filter_id} for user {user_id}: {e}", exc_info=True)
        if "UNIQUE constraint failed: user_saved_filters.user_id, user_saved_filters.filter_name" in str(e):
            logging.warning(f"Attempt to update to a duplicate filter name for user {user_id}.")
        return False
    finally:
        if conn:
            conn.close()

def delete_saved_filter(saved_filter_id: int, user_id: str) -> bool:
    """
    Deletes a specific saved filter for a user.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM user_saved_filters
            WHERE id = ? AND user_id = ?
        """, (saved_filter_id, user_id))
        conn.commit()

        if cursor.rowcount > 0:
            logging.info(f"Deleted filter ID {saved_filter_id} for user {user_id}.")
            return True
        else:
            logging.warning(f"No filter found to delete with ID {saved_filter_id} for user {user_id}.")
            return False
    except Exception as e:
        if conn:
            conn.rollback()
        logging.error(f"Error deleting filter ID {saved_filter_id} for user {user_id}: {e}", exc_info=True)
        return False
    finally:
        if conn:
            conn.close()
