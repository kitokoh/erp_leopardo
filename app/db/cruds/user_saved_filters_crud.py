# db/cruds/user_saved_filters_crud.py
import json
import logging
from app.db.connection import get_db_connection
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

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
        filter_parameters_json = json.dumps(filter_parameters)
        current_timestamp = datetime.utcnow().isoformat() + "Z" # Ensure ISO 8601 format with Z for UTC
        new_filter_id = None

        if isinstance(conn, Session): # SQLAlchemy Session
            stmt = text("""
                INSERT INTO user_saved_filters (user_id, filter_name, filter_parameters_json, created_at, updated_at)
                VALUES (:user_id, :filter_name, :filter_parameters_json, :created_at, :updated_at)
            """)
            # For SQLite with SQLAlchemy, lastrowid is available on the result object
            result = conn.execute(stmt, {
                "user_id": user_id,
                "filter_name": filter_name,
                "filter_parameters_json": filter_parameters_json,
                "created_at": current_timestamp,
                "updated_at": current_timestamp
            })
            conn.commit()
            # Accessing lastrowid; for some DBs/drivers, this might require specific handling (e.g., RETURNING clause)
            # For SQLite, this should work.
            new_filter_id = result.lastrowid
        else: # DB-API connection
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_saved_filters (user_id, filter_name, filter_parameters_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, filter_name, filter_parameters_json, current_timestamp, current_timestamp))
            conn.commit()
            new_filter_id = cursor.lastrowid

        if new_filter_id is not None:
            logging.info(f"Saved filter '{filter_name}' for user {user_id} with ID {new_filter_id}.")
            return new_filter_id
        else: # Should not happen if insert was successful and lastrowid is supported
            logging.error(f"Failed to retrieve lastrowid for filter '{filter_name}', user {user_id}.")
            return None

    except Exception as e:
        if conn:
            try:
                if isinstance(conn, Session):
                    conn.rollback()
                else:
                    conn.rollback() # Standard DB-API rollback
            except Exception as rb_ex:
                logging.error(f"Error during rollback: {rb_ex}")

        logging.error(f"Error adding saved filter for user {user_id}, name '{filter_name}': {e}", exc_info=True)
        if "UNIQUE constraint failed" in str(e) or "IntegrityError" in str(type(e)): # More generic check
             logging.warning(f"Attempt to add duplicate filter name '{filter_name}' for user {user_id} or other integrity error.")
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
        filters_list = []

        if isinstance(conn, Session): # SQLAlchemy Session
            # For SQLAlchemy, use session.execute with text() for raw SQL
            # The result is a CursorResult (similar to a DBAPI cursor), which can be iterated.
            # Rows are often RowProxy objects which behave like dictionaries or tuples.
            stmt = text("""
                SELECT id, user_id, filter_name, filter_parameters_json, created_at, updated_at
                FROM user_saved_filters
                WHERE user_id = :user_id
                ORDER BY filter_name ASC
            """)
            result = conn.execute(stmt, {"user_id": user_id})
            for row in result:
                # Assuming row behaves like a mapping (e.g., result of .mappings().all())
                # or access by index/name: row[0] or row.id
                # To be safe and explicit, converting to dict if it's a RowProxy
                row_dict = dict(row._mapping) # Access the underlying mapping for RowProxy
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
                    logging.error(f"Error decoding JSON for filter ID {row_dict['id']} (SQLAlchemy path): {je}")
            # SQLAlchemy sessions are typically managed (committed/rolled back/closed) by the caller
            # or a higher-level construct (like a context manager or FastAPI dependency).
            # The existing finally block will call conn.close(), which is fine for sessions from SessionLocal().
        else: # DB-API connection (e.g., sqlite3.Connection)
            cursor = conn.cursor()
            # Ensure row_factory is set for dictionary-like access if get_db_connection doesn't set it globally
            # For sqlite3, conn.row_factory = sqlite3.Row is usually set in get_db_connection

            cursor.execute("""
                SELECT id, user_id, filter_name, filter_parameters_json, created_at, updated_at
                FROM user_saved_filters
                WHERE user_id = ?
                ORDER BY filter_name ASC
            """, (user_id,))

            raw_rows = cursor.fetchall()
            for row in raw_rows:
                row_dict = dict(row) # Works if conn.row_factory = sqlite3.Row was set
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
                    logging.error(f"Error decoding JSON for filter ID {row_dict['id']} (DBAPI path): {je}")
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
        row_data = None

        if isinstance(conn, Session): # SQLAlchemy Session
            stmt = text("""
                SELECT id, user_id, filter_name, filter_parameters_json, created_at, updated_at
                FROM user_saved_filters
                WHERE id = :saved_filter_id AND user_id = :user_id
            """)
            result = conn.execute(stmt, {"saved_filter_id": saved_filter_id, "user_id": user_id})
            # fetchone() returns a RowProxy or None
            row_proxy = result.fetchone()
            if row_proxy:
                row_data = dict(row_proxy._mapping) # Convert RowProxy to dict
        else: # DB-API connection
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, filter_name, filter_parameters_json, created_at, updated_at
                FROM user_saved_filters
                WHERE id = ? AND user_id = ?
            """, (saved_filter_id, user_id))
            raw_row = cursor.fetchone()
            if raw_row:
                row_data = dict(raw_row)

        if row_data:
            try:
                filter_params_dict = json.loads(row_data['filter_parameters_json'])
                return {
                    'id': row_data['id'],
                    'user_id': row_data['user_id'],
                    'filter_name': row_data['filter_name'],
                    'filter_parameters': filter_params_dict,
                    'created_at': row_data['created_at'],
                    'updated_at': row_data['updated_at']
                }
            except json.JSONDecodeError as je:
                logging.error(f"Error decoding JSON for filter ID {row_data['id']}: {je}")
                return None
        return None # If no row was found
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

        update_fields = []
        sql_params = {}

        if new_name is not None:
            update_fields.append("filter_name = :new_name")
            sql_params["new_name"] = new_name

        if new_filter_parameters is not None:
            update_fields.append("filter_parameters_json = :new_filter_parameters_json")
            sql_params["new_filter_parameters_json"] = json.dumps(new_filter_parameters)

        if not update_fields: # No actual change to make
            logging.info("No fields to update for filter ID {saved_filter_id}.")
            return True # Or False, depending on desired semantics for "no change"

        update_fields.append("updated_at = :updated_at")
        sql_params["updated_at"] = datetime.utcnow().isoformat() + "Z"

        sql_params["saved_filter_id"] = saved_filter_id
        sql_params["user_id"] = user_id

        set_clause = ", ".join(update_fields)

        rowcount = 0

        if isinstance(conn, Session): # SQLAlchemy Session
            stmt = text(f"UPDATE user_saved_filters SET {set_clause} WHERE id = :saved_filter_id AND user_id = :user_id")
            result = conn.execute(stmt, sql_params)
            conn.commit()
            rowcount = result.rowcount
        else: # DB-API connection
            # Need to adjust for '?' placeholders if using DB-API
            # This part becomes more complex as the SQL structure changes based on named vs positional params.
            # For simplicity, let's reconstruct for DB-API style if needed, assuming SQLite '?'
            dbapi_fields_to_update = []
            dbapi_params_for_sql = []
            if new_name is not None:
                dbapi_fields_to_update.append("filter_name = ?")
                dbapi_params_for_sql.append(new_name)
            if new_filter_parameters is not None:
                dbapi_fields_to_update.append("filter_parameters_json = ?")
                dbapi_params_for_sql.append(json.dumps(new_filter_parameters))

            dbapi_fields_to_update.append("updated_at = ?")
            dbapi_params_for_sql.append(sql_params["updated_at"]) # Re-use calculated timestamp

            dbapi_params_for_sql.extend([saved_filter_id, user_id])

            dbapi_set_clause = ", ".join(dbapi_fields_to_update)
            dbapi_sql = f"UPDATE user_saved_filters SET {dbapi_set_clause} WHERE id = ? AND user_id = ?"

            cursor = conn.cursor()
            cursor.execute(dbapi_sql, tuple(dbapi_params_for_sql))
            conn.commit()
            rowcount = cursor.rowcount

        if rowcount == 0:
            logging.warning(f"No filter found with ID {saved_filter_id} for user {user_id} to update, or no change made.")
            return False

        logging.info(f"Updated filter ID {saved_filter_id} for user {user_id}.")
        return True

    except Exception as e:
        if conn:
            try:
                if isinstance(conn, Session):
                    conn.rollback()
                else:
                    conn.rollback()
            except Exception as rb_ex:
                logging.error(f"Error during rollback: {rb_ex}")
        logging.error(f"Error updating filter ID {saved_filter_id} for user {user_id}: {e}", exc_info=True)
        if "UNIQUE constraint failed" in str(e) or "IntegrityError" in str(type(e)):
            logging.warning(f"Attempt to update to a duplicate filter name for user {user_id} or other integrity error.")
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
        rowcount = 0

        if isinstance(conn, Session): # SQLAlchemy Session
            stmt = text("""
                DELETE FROM user_saved_filters
                WHERE id = :saved_filter_id AND user_id = :user_id
            """)
            result = conn.execute(stmt, {"saved_filter_id": saved_filter_id, "user_id": user_id})
            conn.commit()
            rowcount = result.rowcount
        else: # DB-API connection
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM user_saved_filters
                WHERE id = ? AND user_id = ?
            """, (saved_filter_id, user_id))
            conn.commit()
            rowcount = cursor.rowcount

        if rowcount > 0:
            logging.info(f"Deleted filter ID {saved_filter_id} for user {user_id}.")
            return True
        else:
            logging.warning(f"No filter found to delete with ID {saved_filter_id} for user {user_id}.")
            return False
    except Exception as e:
        if conn:
            try:
                if isinstance(conn, Session):
                    conn.rollback()
                else:
                    conn.rollback()
            except Exception as rb_ex:
                logging.error(f"Error during rollback: {rb_ex}")
        logging.error(f"Error deleting filter ID {saved_filter_id} for user {user_id}: {e}", exc_info=True)
        return False
    finally:
        if conn:
            conn.close()
