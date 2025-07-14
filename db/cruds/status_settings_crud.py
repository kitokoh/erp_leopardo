import sqlite3 # Keep for type hints if necessary, but conn will be Session
from sqlalchemy.sql import text
# from .generic_crud import _manage_conn # Decorator removed
from ..connection import get_db_connection # Direct import
import logging

# --- StatusSettings CRUD ---
def get_status_setting_by_name(name: str, type: str, conn = None) -> dict | None:
    conn_is_external = conn is not None
    if not conn_is_external:
        conn = get_db_connection() # This should provide an SA Session if configured

    original_name_param = name
    if isinstance(name, dict) and type == 'Client':
        logging.warning(
            f"WARNING: get_status_setting_by_name called with a dictionary for 'name' when type is 'Client'. "
            f"Attempting to recover using name.get('status'). problematic_dict: {name}"
        )
        status_from_dict = name.get('status')
        if isinstance(status_from_dict, str):
            name = status_from_dict
            logging.info(f"Recovered status_name '{name}' from dictionary for type 'Client'.")
        else:
            logging.error(
                f"Failed to recover a string status from dict['status'] for type 'Client'. "
                f"Dict['status'] was: {status_from_dict}. Proceeding with original dict, which will likely fail."
            )
            name = original_name_param

    try:
        sql_query = text("SELECT * FROM StatusSettings WHERE status_name = :name AND status_type = :type")
        # Check if the connection is a raw sqlite3 connection
        if hasattr(conn, 'execute') and not hasattr(conn, 'begin'):
            # It's a raw connection, so convert TextClause to string
            result = conn.execute(str(sql_query), {"name": name, "type": type})
        else:
            # It's a SQLAlchemy connection, which can handle TextClause directly
            result = conn.execute(sql_query, {"name": name, "type": type})
        row = result.fetchone()
        return dict(row._mapping) if row else None # Use row._mapping for RowProxy
    except Exception as e: # Changed to general Exception
        logging.error(f"Error getting status setting by name '{name}' (original_param_type: {type(original_name_param).__name__}) and type '{type}': {e}", exc_info=True)
        return None
    finally:
        if not conn_is_external and conn:
            conn.close()

def get_status_setting_by_id(id: int, conn = None) -> dict | None:
    conn_is_external = conn is not None
    if not conn_is_external:
        conn = get_db_connection()

    try:
        sql_query = text("SELECT * FROM StatusSettings WHERE status_id = :id")
        # Check if the connection is a raw sqlite3 connection
        if hasattr(conn, 'execute') and not hasattr(conn, 'begin'):
            # It's a raw connection, so convert TextClause to string
            result = conn.execute(str(sql_query), {"id": id})
        else:
            # It's a SQLAlchemy connection, which can handle TextClause directly
            result = conn.execute(sql_query, {"id": id})
        row = result.fetchone()
        return dict(row._mapping) if row else None
    except Exception as e: # Changed to general Exception
        logging.error(f"Error getting status setting by id {id}: {e}", exc_info=True)
        return None
    finally:
        if not conn_is_external and conn:
            conn.close()

def get_all_status_settings(type_filter: str = None, conn = None) -> list[dict]:
    conn_is_external = conn is not None
    if not conn_is_external:
        conn = get_db_connection()
    """
    Retrieves all status settings, optionally filtered by type.
    """
    sql_base = "SELECT * FROM StatusSettings"
    params = {}
    conditions = []

    if type_filter:
        conditions.append("status_type = :type_filter")
        params["type_filter"] = type_filter

    if conditions:
        sql_base += " WHERE " + " AND ".join(conditions)

    sql_base += " ORDER BY status_type, sort_order, status_name"

    sql_query = text(sql_base)

    try:
        # Check if the connection is a raw sqlite3 connection
        if hasattr(conn, 'execute') and not hasattr(conn, 'begin'):
             # It's a raw connection, so convert TextClause to string
             result = conn.execute(str(sql_query), params)
        else:
             # It's a SQLAlchemy connection, which can handle TextClause directly
             result = conn.execute(sql_query, params)
        return [dict(row._mapping) for row in result.fetchall()]
    except Exception as e: # Changed to general Exception
        logging.error(f"Database error in get_all_status_settings (filter: {type_filter}): {e}", exc_info=True)
        return []
    finally:
        if not conn_is_external and conn:
            conn.close()


def add_status_setting(status_name: str, status_type: str, color_hex: str = None, sort_order: int = 0, conn = None) -> int | bool:
    conn_is_external = conn is not None
    if not conn_is_external:
        conn = get_db_connection()
    """
    Adds a new status setting to the StatusSettings table.

    Args:
        status_name: The name of the status.
        status_type: The type of the status (e.g., 'Client', 'Project', 'Task').
        color_hex: The hex color code for the status (optional).
        sort_order: The sort order for the status (optional, default 0).
        conn: The database connection (managed by _manage_conn decorator if not provided).

    Returns:
        The ID of the newly inserted status if successful, False otherwise.
    """
    # The @_manage_conn decorator handles the connection, cursor creation,
    # commit/rollback, and closing the connection.
    # The `conn` parameter is provided by the decorator.

    try:
        sql_query = text("""INSERT INTO StatusSettings (status_name, status_type, color_hex, sort_order)
                         VALUES (:status_name, :status_type, :color_hex, :sort_order)""")
        params = {
            "status_name": status_name, "status_type": status_type,
            "color_hex": color_hex, "sort_order": sort_order
        }
        # Check if the connection is a raw sqlite3 connection
        if hasattr(conn, 'execute') and not hasattr(conn, 'begin'):
            # It's a raw connection, so convert TextClause to string
            result = conn.execute(str(sql_query), params)
        else:
            # It's a SQLAlchemy connection, which can handle TextClause directly
            result = conn.execute(sql_query, params)
        if not conn_is_external:
            conn.commit()

        last_id = result.lastrowid
        if last_id is None and hasattr(result, 'inserted_primary_key') and result.inserted_primary_key: # Fallback for some drivers
            last_id = result.inserted_primary_key[0]

        return last_id if last_id is not None else True
    except Exception as e: # Changed to general Exception
        logging.error(f"Database error in add_status_setting for '{status_name}'/'{status_type}': {e}", exc_info=True)
        if not conn_is_external and conn:
            conn.rollback()
        return False
    finally:
        if not conn_is_external and conn:
            conn.close()


def update_status_setting(status_id: int, status_name: str, status_type: str, color_hex: str = None, sort_order: int = None, conn = None) -> bool:
    conn_is_external = conn is not None
    if not conn_is_external:
        conn = get_db_connection()
    """
    Updates an existing status setting in the StatusSettings table.

    Args:
        status_id: The ID of the status to update.
        status_name: The new name of the status.
        status_type: The new type of the status.
        color_hex: The new hex color code (optional, None to leave unchanged if not provided, or pass existing value).
                   Consider how to handle clearing a value if that's a use case (e.g. pass empty string or specific sentinel).
                   For now, if None, it implies no change to color_hex in the SET clause.
        sort_order: The new sort order (optional, None to leave unchanged).
        conn: The database connection (managed by _manage_conn decorator).

    Returns:
        True if successful, False otherwise.
    """
    sql_base = "UPDATE StatusSettings SET status_name = :status_name, status_type = :status_type"
    params_dict = {"status_name": status_name, "status_type": status_type, "status_id": status_id}

    if color_hex is not None:
        sql_base += ", color_hex = :color_hex"
        params_dict["color_hex"] = color_hex

    if sort_order is not None:
        sql_base += ", sort_order = :sort_order"
        params_dict["sort_order"] = sort_order

    sql_base += " WHERE status_id = :status_id"

    sql_query = text(sql_base)

    try:
        # Check if the connection is a raw sqlite3 connection
        if hasattr(conn, 'execute') and not hasattr(conn, 'begin'):
            # It's a raw connection, so convert TextClause to string
            result = conn.execute(str(sql_query), params_dict)
        else:
            # It's a SQLAlchemy connection, which can handle TextClause directly
            result = conn.execute(sql_query, params_dict)
        if not conn_is_external:
            conn.commit()
        return result.rowcount > 0
    except Exception as e: # Changed to general Exception
        logging.error(f"Database error in update_status_setting for ID {status_id}: {e}", exc_info=True)
        if not conn_is_external and conn:
            conn.rollback()
        return False
    finally:
        if not conn_is_external and conn:
            conn.close()


def is_status_in_use(status_id: int, conn = None) -> bool:
    conn_is_external = conn is not None
    if not conn_is_external:
        conn = get_db_connection()
    """
    Checks if a status_id is currently in use in the Clients table.

    Args:
        status_id: The ID of the status to check.
        conn: The database connection (managed by _manage_conn decorator).

    Returns:
        True if the status_id is found in Clients, False otherwise.
    """
    sql_query = text("SELECT 1 FROM Clients WHERE status_id = :status_id LIMIT 1")
    try:
        # Check if the connection is a raw sqlite3 connection
        if hasattr(conn, 'execute') and not hasattr(conn, 'begin'):
            # It's a raw connection, so convert TextClause to string
            result = conn.execute(str(sql_query), {"status_id": status_id})
        else:
            # It's a SQLAlchemy connection, which can handle TextClause directly
            result = conn.execute(sql_query, {"status_id": status_id})
        return result.fetchone() is not None
    except Exception as e: # Changed to general Exception
        logging.error(f"Database error in is_status_in_use for status_id {status_id}: {e}", exc_info=True)
        # Returning True on error prevents deletion if the check fails, which is safer.
        return True # Safer: assume in use if check fails
    finally:
        if not conn_is_external and conn:
            conn.close()


def delete_status_setting(status_id: int, conn = None) -> bool:
    conn_is_external = conn is not None
    if not conn_is_external:
        conn = get_db_connection()
    """
    Deletes a status setting from the StatusSettings table.

    Args:
        status_id: The ID of the status to delete.
        conn: The database connection (managed by _manage_conn decorator).

    Returns:
        True if successful (row was deleted), False otherwise.
    """
    sql_query = text("DELETE FROM StatusSettings WHERE status_id = :status_id")
    try:
        # Check if the connection is a raw sqlite3 connection
        if hasattr(conn, 'execute') and not hasattr(conn, 'begin'):
            # It's a raw connection, so convert TextClause to string
            result = conn.execute(str(sql_query), {"status_id": status_id})
        else:
            # It's a SQLAlchemy connection, which can handle TextClause directly
            result = conn.execute(sql_query, {"status_id": status_id})
        if not conn_is_external:
            conn.commit()
        return result.rowcount > 0
    except Exception as e: # Changed to general Exception
        logging.error(f"Database error in delete_status_setting for ID {status_id}: {e}", exc_info=True)
        if not conn_is_external and conn:
            conn.rollback()
        return False
    finally:
        if not conn_is_external and conn:
            conn.close()
