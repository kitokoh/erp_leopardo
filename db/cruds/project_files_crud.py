import sqlite3
import logging
from .generic_crud import _manage_conn

logger = logging.getLogger(__name__)

@_manage_conn
def add_project_file(project_id: str, file_name: str, file_path: str, uploaded_by_user_id: str, conn: sqlite3.Connection = None) -> int | None:
    """(Placeholder) Adds a file record associated with a project."""
    logger.warning("Placeholder function `add_project_file` called. Not yet implemented.")
    # Example INSERT:
    # from datetime import datetime
    # now = datetime.utcnow().isoformat() + "Z"
    # sql = "INSERT INTO ProjectFiles (project_id, file_name, file_path, uploaded_by_user_id, upload_timestamp) VALUES (?, ?, ?, ?, ?)"
    # try:
    #     cursor = conn.cursor()
    #     cursor.execute(sql, (project_id, file_name, file_path, uploaded_by_user_id, now))
    #     return cursor.lastrowid
    # except sqlite3.Error as e:
    #     logger.error(f"Error adding project file: {e}")
    #     return None
    return None

@_manage_conn
def get_project_files(project_id: str, conn: sqlite3.Connection = None) -> list[dict]:
    """(Placeholder) Retrieves file records for a specific project."""
    logger.warning("Placeholder function `get_project_files` called. Not yet implemented.")
    # Example SELECT:
    # sql = "SELECT * FROM ProjectFiles WHERE project_id = ? ORDER BY upload_timestamp DESC"
    # try:
    #     cursor = conn.cursor()
    #     cursor.execute(sql, (project_id,))
    #     return [dict(row) for row in cursor.fetchall()]
    # except sqlite3.Error as e:
    #     logger.error(f"Error fetching project files: {e}")
    #     return []
    return []

@_manage_conn
def delete_project_file(file_id: int, conn: sqlite3.Connection = None) -> bool:
    """(Placeholder) Deletes a project file record (and potentially the file from disk)."""
    logger.warning("Placeholder function `delete_project_file` called. Not yet implemented.")
    # Example DELETE:
    # try:
    #     cursor = conn.cursor()
    #     # Optionally, fetch file_path here to delete from disk before DB record
    #     cursor.execute("DELETE FROM ProjectFiles WHERE file_id = ?", (file_id,))
    #     return cursor.rowcount > 0
    # except sqlite3.Error as e:
    #     logger.error(f"Error deleting project file: {e}")
    #     return False
    return False

__all__ = [
    "add_project_file",
    "get_project_files",
    "delete_project_file",
]
