import logging
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.generic_crud import _manage_conn, _convert_to_dict
from app.models.db.users.rolepermissions import RolePermissions as RolePermission

logger = logging.getLogger(__name__)

def add_permission_to_role(db: Session, role_id: int, permission_key: str) -> RolePermission | None:
    """
    Assigns a permission to a role.
    This function expects the caller to manage the session and commit.
    """
    try:
        existing_assignment = db.query(RolePermission).filter_by(role_id=role_id, permission_key=permission_key).first()
        if existing_assignment:
            logger.info(f"Permission '{permission_key}' is already assigned to role ID {role_id}.")
            return existing_assignment

        new_assignment = RolePermission(role_id=role_id, permission_key=permission_key)
        db.add(new_assignment)
        logger.info(f"Permission '{permission_key}' staged for addition to role ID {role_id}.")
        return new_assignment
    except SQLAlchemyError as e:
        logger.error(f"Database error staging permission '{permission_key}' for role {role_id}: {e}", exc_info=True)
        return None

@_manage_conn
def remove_permission_from_role(role_id: int, permission_key: str, conn: Session = None) -> bool:
    """Removes a permission from a role."""
    try:
        sql = text("DELETE FROM RolePermissions WHERE role_id = :role_id AND permission_key = :permission_key")
        params = {"role_id": role_id, "permission_key": permission_key}
        result = conn.execute(sql, params)
        conn.commit()
        if result.rowcount > 0:
            logger.info(f"Permission '{permission_key}' removed from role ID {role_id}.")
        else:
            logger.info(f"Permission '{permission_key}' was not assigned to role ID {role_id}.")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database error removing permission '{permission_key}' from role {role_id}: {e}", exc_info=True)
        conn.rollback()
        return False

@_manage_conn
def get_permissions_for_role(role_id: int, conn: Session = None) -> list[str]:
    """Lists all permission keys assigned to a specific role."""
    try:
        sql = text("SELECT permission_key FROM RolePermissions WHERE role_id = :role_id ORDER BY permission_key")
        result = conn.execute(sql, {"role_id": role_id})
        return [row[0] for row in result.fetchall()]
    except SQLAlchemyError as e:
        logger.error(f"Database error getting permissions for role {role_id}: {e}", exc_info=True)
        return []

@_manage_conn
def check_role_has_permission(role_id: int, permission_key: str, conn: Session = None) -> bool:
    """Checks if a specific role has a specific permission."""
    try:
        sql = text("SELECT 1 FROM RolePermissions WHERE role_id = :role_id AND permission_key = :permission_key")
        result = conn.execute(sql, {"role_id": role_id, "permission_key": permission_key})
        return result.fetchone() is not None
    except SQLAlchemyError as e:
        logger.error(f"Database error checking permission for role {role_id}: {e}", exc_info=True)
        return False

@_manage_conn
def set_permissions_for_role(role_id: int, permission_keys: list[str], conn: Session = None) -> bool:
    """Sets all permissions for a role by deleting existing and adding new ones."""
    try:
        # 1. Delete all existing permissions for the role
        sql_delete = text("DELETE FROM RolePermissions WHERE role_id = :role_id")
        conn.execute(sql_delete, {"role_id": role_id})
        logger.info(f"Cleared existing permissions for role ID {role_id}.")

        # 2. Add new permissions
        if permission_keys:
            # Use add_permission_to_role which is not decorated and expects a session
            for p_key in permission_keys:
                add_permission_to_role(conn, role_id, p_key)

        conn.commit()
        logger.info(f"Successfully set {len(permission_keys)} permissions for role ID {role_id}.")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database error setting permissions for role {role_id}: {e}", exc_info=True)
        conn.rollback()
        return False
