import sqlite3
from datetime import datetime
from ...connection import get_db_connection

def assign_personnel_to_client(client_id: str, personnel_id: str, role_in_project: str = None) -> int | None:
    """Assigns a personnel to a client. Returns assignment_id or None."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat() + "Z"
        sql = """
            INSERT INTO ClientPersonnelAssignments (client_id, personnel_id, role_in_project, assigned_at)
            VALUES (?, ?, ?, ?)
        """
        params = (client_id, personnel_id, role_in_project, now)
        cursor.execute(sql, params)
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        print(f"Personnel {personnel_id} already assigned to client {client_id}.")
        return None
    except sqlite3.Error as e:
        print(f"Database error in assign_personnel_to_client: {e}")
        return None
    finally:
        if conn: conn.close()

def get_assigned_personnel_for_client(client_id: str, role_filter: str = None) -> list[dict]:
    """Retrieves assigned personnel for a client."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            SELECT cpa.*, tm.full_name as personnel_name, tm.email as personnel_email, tm.phone as personnel_phone
            FROM ClientPersonnelAssignments cpa
            JOIN TeamMembers tm ON cpa.personnel_id = tm.user_id
            WHERE cpa.client_id = ?
        """
        params = (client_id,)
        if role_filter:
            sql += " AND cpa.role_in_project = ?"
            params = (client_id, role_filter)

        sql += " ORDER BY tm.full_name"
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"Database error in get_assigned_personnel_for_client: {e}")
        return []
    finally:
        if conn: conn.close()

def unassign_personnel_from_client(assignment_id: int) -> bool:
    """Unassigns a personnel from a client by assignment_id. Returns True on success."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ClientPersonnelAssignments WHERE assignment_id = ?", (assignment_id,))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Database error in unassign_personnel_from_client: {e}")
        return False
    finally:
        if conn: conn.close()
