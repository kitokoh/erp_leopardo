import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.db.generic_crud import _manage_conn, _convert_to_dict

logger = logging.getLogger(__name__)

@_manage_conn
def assign_forwarder_to_client(client_id: str, forwarder_id: str, task_description: str = None, cost_estimate: float = None, conn: Session = None) -> int | None:
    """Assigns a freight forwarder to a client. Returns client_forwarder_id or None."""
    try:
        now = datetime.utcnow()
        sql = text("""
            INSERT INTO Client_FreightForwarders (client_id, forwarder_id, task_description, cost_estimate, assigned_at)
            VALUES (:client_id, :forwarder_id, :task, :cost, :now)
        """)
        params = {
            "client_id": client_id, "forwarder_id": forwarder_id, "task": task_description,
            "cost": cost_estimate, "now": now
        }
        result = conn.execute(sql, params)
        conn.commit()
        return result.lastrowid
    except IntegrityError:
        logger.warning(f"Freight forwarder {forwarder_id} already assigned to client {client_id}.")
        conn.rollback()
        return None
    except SQLAlchemyError as e:
        logger.error(f"Database error in assign_forwarder_to_client: {e}", exc_info=True)
        conn.rollback()
        return None

@_manage_conn
def get_assigned_forwarders_for_client(client_id: str, conn: Session = None) -> list[dict]:
    """Retrieves assigned freight forwarders for a client."""
    try:
        sql = text("""
            SELECT cff.*, ff.name as forwarder_name, ff.contact_person, ff.phone, ff.email
            FROM Client_FreightForwarders cff
            JOIN FreightForwarders ff ON cff.forwarder_id = ff.forwarder_id
            WHERE cff.client_id = :client_id
            ORDER BY ff.name
        """)
        result = conn.execute(sql, {"client_id": client_id})
        return [_convert_to_dict(row) for row in result.fetchall()]
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_assigned_forwarders_for_client: {e}", exc_info=True)
        return []

@_manage_conn
def unassign_forwarder_from_client(client_forwarder_id: int, conn: Session = None) -> bool:
    """Unassigns a freight forwarder from a client by client_forwarder_id. Returns True on success."""
    try:
        sql = text("DELETE FROM Client_FreightForwarders WHERE client_forwarder_id = :id")
        result = conn.execute(sql, {"id": client_forwarder_id})
        conn.commit()
        return result.rowcount > 0
    except SQLAlchemyError as e:
        logger.error(f"Database error in unassign_forwarder_from_client: {e}", exc_info=True)
        conn.rollback()
        return False
