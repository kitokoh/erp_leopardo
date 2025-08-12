import sqlite3
import uuid
from datetime import datetime
import logging
from ..generic_crud import _manage_conn

logger = logging.getLogger(__name__)

@_manage_conn
def add_transporter(data: dict, conn: sqlite3.Connection = None) -> str | None:
    cursor = conn.cursor()
    new_transporter_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    sql = """
        INSERT INTO Transporters (transporter_id, name, contact_person, phone, email, address, service_area, notes, latitude, longitude, current_cargo, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        new_transporter_id,
        data.get('name'),
        data.get('contact_person'),
        data.get('phone'),
        data.get('email'),
        data.get('address'),
        data.get('service_area'),
        data.get('notes'),
        data.get('latitude'),
        data.get('longitude'),
        data.get('current_cargo'),
        now,
        now
    )
    try:
        cursor.execute(sql, params)
        return new_transporter_id
    except sqlite3.Error as e:
        logger.error(f"Database error in add_transporter: {e}")
        return None

@_manage_conn
def get_transporter_by_id(transporter_id: str, conn: sqlite3.Connection = None) -> dict | None:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Transporters WHERE transporter_id = ?", (transporter_id,))
    row = cursor.fetchone()
    return dict(row) if row else None

@_manage_conn
def get_all_transporters(conn: sqlite3.Connection = None) -> list[dict]:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Transporters ORDER BY name")
    return [dict(row) for row in cursor.fetchall()]

@_manage_conn
def update_transporter(transporter_id: str, data: dict, conn: sqlite3.Connection = None) -> bool:
    if not data: return False
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    data['updated_at'] = now

    valid_columns = ['name', 'contact_person', 'phone', 'email', 'address', 'service_area', 'notes', 'latitude', 'longitude', 'current_cargo', 'updated_at']
    to_set = {k: v for k, v in data.items() if k in valid_columns}
    if not to_set: return False

    set_clauses = [f"{k} = ?" for k in to_set.keys()]
    params_list = list(to_set.values())
    params_list.append(transporter_id)
    sql = f"UPDATE Transporters SET {', '.join(set_clauses)} WHERE transporter_id = ?"
    try:
        cursor.execute(sql, tuple(params_list))
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Database error in update_transporter for {transporter_id}: {e}")
        return False

@_manage_conn
def delete_transporter(transporter_id: str, conn: sqlite3.Connection = None) -> bool:
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Transporters WHERE transporter_id = ?", (transporter_id,))
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Database error deleting transporter {transporter_id}: {e}")
        return False
