import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.db.settings.status_setting import StatusSetting
from app.models.db.clients.client import Client

logger = logging.getLogger(__name__)

def get_status_setting_by_name(db: Session, name: str, status_type: str) -> Optional[StatusSetting]:
    """
    Retrieves a status setting by its name and type using the ORM.
    """
    try:
        return db.query(StatusSetting).filter(
            StatusSetting.status_name == name,
            StatusSetting.status_type == status_type
        ).first()
    except Exception as e:
        logger.error(f"Error getting status setting by name '{name}' and type '{status_type}': {e}", exc_info=True)
        return None

def get_status_setting_by_id(db: Session, status_id: int) -> Optional[StatusSetting]:
    """
    Retrieves a status setting by its ID using the ORM.
    """
    try:
        return db.query(StatusSetting).filter(StatusSetting.status_id == status_id).first()
    except Exception as e:
        logger.error(f"Error getting status setting by id {status_id}: {e}", exc_info=True)
        return None

def get_all_status_settings(db: Session, type_filter: str = None) -> List[StatusSetting]:
    """
    Retrieves all status settings, optionally filtered by type, using the ORM.
    """
    try:
        query = db.query(StatusSetting)
        if type_filter:
            query = query.filter(StatusSetting.status_type == type_filter)
        return query.order_by(StatusSetting.status_type, StatusSetting.sort_order, StatusSetting.status_name).all()
    except Exception as e:
        logger.error(f"Database error in get_all_status_settings (filter: {type_filter}): {e}", exc_info=True)
        return []

def add_status_setting(db: Session, status_name: str, status_type: str, color_hex: str = None, sort_order: int = 0) -> Optional[StatusSetting]:
    """
    Adds a new status setting to the StatusSettings table using the ORM.
    """
    try:
        new_status = StatusSetting(
            status_name=status_name,
            status_type=status_type,
            color_hex=color_hex,
            sort_order=sort_order
        )
        db.add(new_status)
        # The calling function is responsible for the commit
        return new_status
    except Exception as e:
        logger.error(f"Database error in add_status_setting for '{status_name}'/'{status_type}': {e}", exc_info=True)
        return None

def update_status_setting(db: Session, status_id: int, **kwargs) -> bool:
    """
    Updates an existing status setting in the StatusSettings table using the ORM.
    """
    try:
        status = db.query(StatusSetting).filter(StatusSetting.status_id == status_id).first()
        if not status:
            return False
        for key, value in kwargs.items():
            if hasattr(status, key):
                setattr(status, key, value)
        # The calling function is responsible for the commit
        return True
    except Exception as e:
        logger.error(f"Database error in update_status_setting for ID {status_id}: {e}", exc_info=True)
        return False

def is_status_in_use(db: Session, status_id: int) -> bool:
    """
    Checks if a status_id is currently in use in the Clients or other relevant tables.
    """
    try:
        in_use_in_clients = db.query(Client).filter(Client.status_id == status_id).first() is not None
        if in_use_in_clients:
            return True
        # TODO: Add checks for other tables like Projects, Commandes as needed
        return False
    except Exception as e:
        logger.error(f"Database error in is_status_in_use for status_id {status_id}: {e}", exc_info=True)
        return True # Safer to assume in use if check fails

def delete_status_setting(db: Session, status_id: int) -> bool:
    """
    Deletes a status setting from the StatusSettings table using the ORM.
    """
    try:
        status = db.query(StatusSetting).filter(StatusSetting.status_id == status_id).first()
        if status:
            db.delete(status)
            # The calling function is responsible for the commit
            return True
        return False
    except Exception as e:
        logger.error(f"Database error in delete_status_setting for ID {status_id}: {e}", exc_info=True)
        return False
