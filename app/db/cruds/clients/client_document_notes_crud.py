import sqlite3
from datetime import datetime
from ...connection import get_db_connection

def get_client_document_notes(client_id: str, document_type: str = None, language_code: str = None, is_active: bool = None) -> list[dict]:
    """Retrieves document notes for a client, with optional filters."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "SELECT * FROM ClientDocumentNotes WHERE client_id = ?"
        params = (client_id,)

        if document_type:
            sql += " AND document_type = ?"
            params += (document_type,)
        if language_code:
            sql += " AND language_code = ?"
            params += (language_code,)
        if is_active is not None:
            sql += " AND is_active = ?"
            params += (1 if is_active else 0,)

        sql += " ORDER BY document_type, language_code"
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"Database error in get_client_document_notes: {e}")
        return []
    finally:
        if conn: conn.close()

def get_client_document_note_by_id(note_id: int) -> dict | None:
    """Retrieves a specific document note by its ID."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ClientDocumentNotes WHERE note_id = ?", (note_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        print(f"Database error in get_client_document_note_by_id: {e}")
        return None
    finally:
        if conn: conn.close()

def add_client_document_note(data: dict) -> int | None:
    """Adds a new document note for a client."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat() + "Z"
        sql = """
            INSERT INTO ClientDocumentNotes (client_id, document_type, language_code, note_content, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            data['client_id'], data['document_type'], data['language_code'],
            data['note_content'], 1 if data.get('is_active', True) else 0,
            now, now
        )
        cursor.execute(sql, params)
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Database error in add_client_document_note: {e}")
        return None
    finally:
        if conn: conn.close()

def update_client_document_note(note_id: int, data: dict) -> bool:
    """Updates a client document note."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat() + "Z"
        data['updated_at'] = now

        fields_to_update = []
        params = []
        for key, value in data.items():
            if key in ['document_type', 'language_code', 'note_content', 'is_active', 'updated_at']:
                fields_to_update.append(f"{key} = ?")
                params.append(value)

        if not fields_to_update:
            return False

        sql = f"UPDATE ClientDocumentNotes SET {', '.join(fields_to_update)} WHERE note_id = ?"
        params.append(note_id)
        cursor.execute(sql, tuple(params))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Database error in update_client_document_note: {e}")
        return False
    finally:
        if conn: conn.close()

def delete_client_document_note(note_id: int) -> bool:
    """Deletes a document note. Returns True on success."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ClientDocumentNotes WHERE note_id = ?", (note_id,))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Database error in delete_client_document_note: {e}")
        return False
    finally:
        if conn: conn.close()
