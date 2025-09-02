import logging
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.generic_crud import _manage_conn, _convert_to_dict
from app.models.db.users.role import Role

logger = logging.getLogger(__name__)

def add_role(db: Session, role_name: str, description: str = None) -> Role | None:
    """Adds a new role to the Roles table."""
    try:
        new_role = Role(role_name=role_name, description=description)
        db.add(new_role)
        db.flush()
        logger.info(f"Role '{role_name}' staged for addition with ID {new_role.role_id}.")
        return new_role
    except SQLAlchemyError as e:
        logger.error(f"Database error staging role '{role_name}': {e}", exc_info=True)
        return None

def get_role_by_name(db: Session, role_name: str) -> Role | None:
    """Fetches a role by its name."""
    try:
        return db.query(Role).filter(Role.role_name == role_name).first()
    except SQLAlchemyError as e:
        logger.error(f"Database error getting role by name '{role_name}': {e}", exc_info=True)
        return None

@_manage_conn
def get_role_by_id(role_id: int, conn: Session = None) -> dict | None:
    """Fetches a role by its ID."""
    try:
        sql = text("SELECT * FROM Roles WHERE role_id = :role_id")
        result = conn.execute(sql, {"role_id": role_id})
        row = result.fetchone()
        return _convert_to_dict(row) if row else None
    except SQLAlchemyError as e:
        logger.error(f"Database error getting role by ID {role_id}: {e}", exc_info=True)
        return None

@_manage_conn
def list_roles(conn: Session = None) -> list[dict]:
    """Lists all roles."""
    try:
        sql = text("SELECT * FROM Roles ORDER BY role_name")
        result = conn.execute(sql)
        return [_convert_to_dict(row) for row in result.fetchall()]
    except SQLAlchemyError as e:
        logger.error(f"Database error listing roles: {e}", exc_info=True)
        return []

@_manage_conn
def update_role(role_id: int, role_name: str, description: str = None, conn: Session = None) -> bool:
    """Updates an existing role's name and description."""
    try:
        sql = text("UPDATE Roles SET role_name = :role_name, description = :description WHERE role_id = :role_id")
        params = {"role_name": role_name, "description": description, "role_id": role_id}
        result = conn.execute(sql, params)
        conn.commit()
        if result.rowcount > 0:
            logger.info(f"Role ID {role_id} updated to name '{role_name}'.")
            return True
        logger.warning(f"Role ID {role_id} not found for update or no change made.")
        return False
    except SQLAlchemyError as e:
        conn.rollback()
        logger.error(f"Database error updating role ID {role_id}: {e}", exc_info=True)
        return False

@_manage_conn
def delete_role(role_id: int, conn: Session = None) -> bool:
    """Deletes a role by its ID."""
    try:
        if is_role_used(role_id, conn=conn):
            logger.error(f"Cannot delete role ID {role_id} as it's currently in use.")
            return False

        sql = text("DELETE FROM Roles WHERE role_id = :role_id")
        result = conn.execute(sql, {"role_id": role_id})
        conn.commit()

        if result.rowcount > 0:
            logger.info(f"Role ID {role_id} deleted successfully.")
            return True
        logger.warning(f"Role ID {role_id} not found for deletion.")
        return False
    except SQLAlchemyError as e:
        conn.rollback()
        logger.error(f"Database error deleting role ID {role_id}: {e}", exc_info=True)
        return False

@_manage_conn
def is_role_used(role_id: int, conn: Session = None) -> bool:
    """Checks if a role is currently assigned to any user."""
    try:
        sql = text("SELECT 1 FROM Users WHERE role_id = :role_id LIMIT 1")
        result = conn.execute(sql, {"role_id": role_id})
        return result.fetchone() is not None
    except SQLAlchemyError as e:
        logger.error(f"Database error checking if role ID {role_id} is used: {e}", exc_info=True)
        return True # Fail safe: assume it's used if there's an error checking
