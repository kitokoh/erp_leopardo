import logging
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.generic_crud import _manage_conn, _convert_to_dict
from app.models.db.misc.permissions import Permission

logger = logging.getLogger(__name__)

def add_permission(db: Session, permission_key: str, description: str) -> Permission | None:
    """
    Adds a new permission to the Permissions table.
    This function expects the caller to manage the session.
    """
    try:
        new_permission = Permission(permission_key=permission_key, description=description)
        db.add(new_permission)
        db.flush()
        logger.info(f"Permission '{permission_key}' staged for addition.")
        return new_permission
    except SQLAlchemyError as e:
        logger.error(f"Database error staging permission '{permission_key}': {e}", exc_info=True)
        return None

def get_permission_by_key(db: Session, permission_key: str) -> Permission | None:
    """Fetches a permission by its key."""
    try:
        return db.query(Permission).filter(Permission.permission_key == permission_key).first()
    except SQLAlchemyError as e:
        logger.error(f"Database error getting permission by key '{permission_key}': {e}", exc_info=True)
        return None

@_manage_conn
def list_all_permissions(conn: Session = None) -> list[dict]:
    """Lists all available permissions."""
    try:
        sql = text("SELECT * FROM Permissions ORDER BY permission_key")
        result = conn.execute(sql)
        return [_convert_to_dict(row) for row in result.fetchall()]
    except SQLAlchemyError as e:
        logger.error(f"Database error listing all permissions: {e}", exc_info=True)
        return []
