import sqlite3
import logging
from ..generic_crud import _manage_conn

logger = logging.getLogger(__name__)

@_manage_conn
def add_tag(data: dict, conn: sqlite3.Connection = None) -> int | None:
    """Adds a new tag. Expects data['tag_name']."""
    cursor = conn.cursor()
    sql = "INSERT INTO Tags (tag_name) VALUES (?)"
    try:
        cursor.execute(sql, (data['tag_name'],))
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        logger.warning(f"Tag '{data['tag_name']}' already exists.")
        existing = get_tag_by_name(data['tag_name'], conn=conn)
        return existing['tag_id'] if existing else None
    except sqlite3.Error as e:
        logger.error(f"Database error in add_tag: {e}")
        return None

@_manage_conn
def get_tag_by_id(tag_id: int, conn: sqlite3.Connection = None) -> dict | None:
    """Retrieves a tag by its ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Tags WHERE tag_id = ?", (tag_id,))
    row = cursor.fetchone()
    return dict(row) if row else None

@_manage_conn
def get_tag_by_name(tag_name: str, conn: sqlite3.Connection = None) -> dict | None:
    """Retrieves a tag by its name."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Tags WHERE tag_name = ?", (tag_name,))
    row = cursor.fetchone()
    return dict(row) if row else None

@_manage_conn
def get_tags(conn: sqlite3.Connection = None) -> list[dict]:
    """Retrieves all tags."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Tags ORDER BY tag_name")
    return [dict(row) for row in cursor.fetchall()]

@_manage_conn
def update_tag(tag_id: int, data: dict, conn: sqlite3.Connection = None) -> bool:
    """Updates a tag's name."""
    if 'tag_name' not in data:
        return False
    cursor = conn.cursor()
    sql = "UPDATE Tags SET tag_name = ? WHERE tag_id = ?"
    try:
        cursor.execute(sql, (data['tag_name'], tag_id))
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Database error in update_tag for {tag_id}: {e}")
        return False

@_manage_conn
def delete_tag(tag_id: int, conn: sqlite3.Connection = None) -> bool:
    """Deletes a tag."""
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Tags WHERE tag_id = ?", (tag_id,))
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Database error deleting tag {tag_id}: {e}")
        return False
