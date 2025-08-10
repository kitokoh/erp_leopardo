# db/cruds/client_visits_crud.py
import sqlite3
import uuid
from datetime import datetime, timezone
import logging
from ..generic_crud import _manage_conn

logger = logging.getLogger(__name__)

@_manage_conn
def add_client_visit(data: dict, conn: sqlite3.Connection = None) -> str | None:
    """
    Adds a new client visit.
    Expected data: client_id, visit_date (YYYY-MM-DD), visit_type, visit_purpose, notes_impressions, created_by_user_id.
    """
    cursor = conn.cursor()
    new_visit_id = str(uuid.uuid4())
    now_utc = datetime.now(timezone.utc).isoformat()

    required_fields = ['client_id', 'visit_date', 'created_by_user_id']
    for field in required_fields:
        if field not in data or data[field] is None:
            logger.error(f"Field '{field}' is required to add a client visit.")
            return None

    sql = """
        INSERT INTO ClientVisits (
            visit_id, client_id, visit_date, visit_type, visit_purpose,
            notes_impressions, created_by_user_id, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        new_visit_id,
        data['client_id'],
        data['visit_date'], # Should be 'YYYY-MM-DD' string
        data.get('visit_type'),
        data.get('visit_purpose'),
        data.get('notes_impressions'),
        data['created_by_user_id'],
        now_utc,
        now_utc
    )
    try:
        cursor.execute(sql, params)
        logger.info(f"ClientVisit added with ID: {new_visit_id} for client {data['client_id']}.")
        return new_visit_id
    except sqlite3.Error as e:
        logger.error(f"Failed to add client visit. Error: {e}", exc_info=True)
        return None

@_manage_conn
def get_visits_for_client(client_id: str, conn: sqlite3.Connection = None) -> list[dict]:
    """Retrieves all visits for a given client_id, ordered by visit_date descending."""
    cursor = conn.cursor()
    # Optionally join with Users table to get created_by_username
    sql = """
        SELECT cv.*, u.username AS created_by_username
        FROM ClientVisits cv
        LEFT JOIN Users u ON cv.created_by_user_id = u.user_id
        WHERE cv.client_id = ?
        ORDER BY cv.visit_date DESC, cv.created_at DESC
    """
    try:
        cursor.execute(sql, (client_id,))
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Failed to get visits for client {client_id}. Error: {e}", exc_info=True)
        return []

@_manage_conn
def get_client_visit_by_id(visit_id: str, conn: sqlite3.Connection = None) -> dict | None:
    """Retrieves a specific client visit by its ID."""
    cursor = conn.cursor()
    sql = """
        SELECT cv.*, u.username AS created_by_username
        FROM ClientVisits cv
        LEFT JOIN Users u ON cv.created_by_user_id = u.user_id
        WHERE cv.visit_id = ?
    """
    try:
        cursor.execute(sql, (visit_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        logger.error(f"Failed to get client visit by ID {visit_id}. Error: {e}", exc_info=True)
        return None

@_manage_conn
def update_client_visit(visit_id: str, data: dict, conn: sqlite3.Connection = None) -> bool:
    """Updates an existing client visit."""
    cursor = conn.cursor()
    now_utc = datetime.now(timezone.utc).isoformat()

    valid_fields = ['visit_date', 'visit_type', 'visit_purpose', 'notes_impressions']
    fields_to_update = {k: v for k, v in data.items() if k in valid_fields}

    if not fields_to_update:
        logger.info(f"No valid fields provided for updating client visit {visit_id}.")
        return False

    fields_to_update['updated_at'] = now_utc

    set_clauses = [f"{field} = ?" for field in fields_to_update.keys()]
    params = list(fields_to_update.values())
    params.append(visit_id)

    sql = f"UPDATE ClientVisits SET {', '.join(set_clauses)} WHERE visit_id = ?"
    try:
        cursor.execute(sql, tuple(params))
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Database error updating client visit {visit_id}: {e}", exc_info=True)
        return False

@_manage_conn
def delete_client_visit(visit_id: str, conn: sqlite3.Connection = None) -> bool:
    """Deletes a client visit by its ID."""
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM ClientVisits WHERE visit_id = ?", (visit_id,))
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Database error deleting client visit {visit_id}: {e}", exc_info=True)
        return False

__all__ = [
    "add_client_visit",
    "get_visits_for_client",
    "get_client_visit_by_id",
    "update_client_visit",
    "delete_client_visit"
]
