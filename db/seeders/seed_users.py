import sqlite3
import logging
import uuid
from sqlalchemy.orm import Session
from auth.roles import SUPER_ADMIN
from db.cruds.users import users_crud
from config import DEFAULT_ADMIN_USERNAME

def seed_users(db: Session, logger_passed: logging.Logger, role_ids: dict):
    """Seeds the admin user and other default users."""
    logger = logger_passed

    # Seed Admin User
    logger.info("Seeding admin user...")
    super_admin_role_id = role_ids.get(SUPER_ADMIN)
    if super_admin_role_id:
        admin_user = users_crud.get_user_by_username(db=db, username=DEFAULT_ADMIN_USERNAME)
        if not admin_user:
            users_crud.add_user(
                db=db,
                username=DEFAULT_ADMIN_USERNAME,
                password="admin",
                role_id=super_admin_role_id,
                full_name="Administrator",
                email="admin@example.com"
            )
            logger.info(f"Admin user '{DEFAULT_ADMIN_USERNAME}' created.")
        else:
            logger.info(f"Admin user '{DEFAULT_ADMIN_USERNAME}' already exists.")
    else:
        logger.error(f"Could not find role '{SUPER_ADMIN}'. Cannot create admin user.")
