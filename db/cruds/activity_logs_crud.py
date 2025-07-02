import sqlite3
from .generic_crud import _manage_conn # get_db_connection is not used directly
import logging
from datetime import datetime

@_manage_conn
def add_activity_log(data: dict, conn: sqlite3.Connection = None) -> int | None:
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat() + "Z"
    # Corrected table name to ActivityLog and added related_client_id
    sql = """INSERT INTO ActivityLog (user_id, action_type, details, related_entity_type, related_entity_id, related_client_id, created_at)
             VALUES (?, ?, ?, ?, ?, ?, ?)"""
    params = (
        data.get('user_id'),
        data.get('action_type'),
        data.get('details'),
        data.get('related_entity_type'),
        data.get('related_entity_id'),
        data.get('related_client_id'), # Added related_client_id
        now
    )
    try:
        cursor.execute(sql, params)
        return cursor.lastrowid
    except sqlite3.Error as e:
        logging.error(f"Failed to add activity log: {e} with params: {params}")
        return None

@_manage_conn
def get_activity_logs(limit: int = 100, offset: int = 0, user_id_filter: str = None, conn: sqlite3.Connection = None) -> list[dict]:
    cursor = conn.cursor()
    # Corrected table name to ActivityLog
    sql = "SELECT * FROM ActivityLog"
    filters_clauses = []
    params = []

    if user_id_filter:
        filters_clauses.append("user_id = ?")
        params.append(user_id_filter)

    # New filter for related_client_id
    related_client_id_filter = data.get('related_client_id_filter') if isinstance(data, dict) else None # Assuming data might be passed for other filters in future
    if not related_client_id_filter and 'related_client_id_filter' in locals() and locals()['related_client_id_filter']: # Check if passed directly as kwarg
        related_client_id_filter = locals()['related_client_id_filter']

    if related_client_id_filter:
        filters_clauses.append("related_client_id = ?")
        params.append(related_client_id_filter)

    # Add more filters here if needed, e.g., by date range, action_type, related_entity

    if filters_clauses:
        sql += " WHERE " + " AND ".join(filters_clauses)

    sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

# --- get_activity_logs function signature needs to be updated if related_client_id_filter is a direct param ---
# For now, keeping the original signature and assuming it might be passed via a 'data' dict
# or a more complex filter object in the future.
# If it's intended as a direct named argument, the signature should be:
# def get_activity_logs(limit: int = 100, offset: int = 0, user_id_filter: str = None, related_client_id_filter: str = None, conn: sqlite3.Connection = None) -> list[dict]:
# And the logic to get related_client_id_filter would be simpler.
# Let's adjust the signature for clarity and direct use.

@_manage_conn
def get_activity_logs(limit: int = 100, offset: int = 0, user_id_filter: str = None, related_client_id_filter: str = None, conn: sqlite3.Connection = None) -> list[dict]:
    cursor = conn.cursor()
    sql = "SELECT al.*, u.username FROM ActivityLog al LEFT JOIN Users u ON al.user_id = u.user_id" # Join with Users to get username
    filters_clauses = []
    params = []

    if user_id_filter:
        filters_clauses.append("al.user_id = ?")
        params.append(user_id_filter)

    if related_client_id_filter:
        filters_clauses.append("al.related_client_id = ?")
        params.append(related_client_id_filter)

    # Example: Add filter for related_entity_type if needed
    # related_entity_type_filter = data.get('related_entity_type_filter')
    # if related_entity_type_filter:
    #     filters_clauses.append("al.related_entity_type = ?")
    #     params.append(related_entity_type_filter)

    if filters_clauses:
        sql += " WHERE " + " AND ".join(filters_clauses)

    sql += " ORDER BY al.created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    try:
        cursor.execute(sql, tuple(params))
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logging.error(f"Failed to get activity logs: {e}")
        return []

@_manage_conn
def get_activity_log_by_id(log_id: int, conn: sqlite3.Connection = None) -> dict | None:
    cursor = conn.cursor()
    # Corrected table name to ActivityLog
    sql = "SELECT * FROM ActivityLog WHERE log_id = ?"
    try:
        cursor.execute(sql, (log_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        logging.error(f"Failed to get activity log by ID {log_id}: {e}")
        return None
