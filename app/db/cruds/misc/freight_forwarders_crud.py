import sqlite3
import uuid
from datetime import datetime
import logging
from ..generic_crud import _manage_conn

logger = logging.getLogger(__name__)

@_manage_conn
def add_freight_forwarder(data: dict, conn: sqlite3.Connection = None) -> str | None:
    """Adds a new freight forwarder. Returns forwarder_id (UUID) or None."""
    cursor = conn.cursor()
    new_forwarder_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat() + "Z"
    sql = """
        INSERT INTO FreightForwarders (
            forwarder_id, name, contact_person, phone, email, address,
            services_offered, notes, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        new_forwarder_id, data.get('name'), data.get('contact_person'),
        data.get('phone'), data.get('email'), data.get('address'),
        data.get('services_offered'), data.get('notes'), now, now
    )
    try:
        cursor.execute(sql, params)
        return new_forwarder_id
    except sqlite3.Error as e:
        logger.error(f"Database error in add_freight_forwarder: {e}")
        return None

@_manage_conn
def get_freight_forwarder_by_id(forwarder_id: str, conn: sqlite3.Connection = None) -> dict | None:
    """Retrieves a freight forwarder by its ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM FreightForwarders WHERE forwarder_id = ?", (forwarder_id,))
    row = cursor.fetchone()
    return dict(row) if row else None

@_manage_conn
def get_all_freight_forwarders(conn: sqlite3.Connection = None) -> list[dict]:
    """Retrieves all freight forwarders."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM FreightForwarders ORDER BY name")
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

@_manage_conn
def update_freight_forwarder(forwarder_id: str, data: dict, conn: sqlite3.Connection = None) -> bool:
    """Updates a freight forwarder. Returns True on success."""
    if not data: return False
    cursor = conn.cursor()
    data['updated_at'] = datetime.utcnow().isoformat() + "Z"
    set_clauses = [f"{key} = ?" for key in data.keys() if key != 'forwarder_id']
    params = [value for key, value in data.items() if key != 'forwarder_id']
    if not set_clauses: return False
    params.append(forwarder_id)
    sql = f"UPDATE FreightForwarders SET {', '.join(set_clauses)} WHERE forwarder_id = ?"
    try:
        cursor.execute(sql, tuple(params))
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Database error in update_freight_forwarder: {e}")
        return False

@_manage_conn
def delete_freight_forwarder(forwarder_id: str, conn: sqlite3.Connection = None) -> bool:
    """Deletes a freight forwarder. Returns True on success."""
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM FreightForwarders WHERE forwarder_id = ?", (forwarder_id,))
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Database error in delete_freight_forwarder: {e}")
        return False
