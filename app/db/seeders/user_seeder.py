import logging
import sqlite3
import uuid

from db.cruds.users import users_crud
from db.cruds.users.roles_crud import get_role_by_name
from auth.roles import SUPER_ADMIN, OPERATOR

def seed_default_users(conn: sqlite3.Connection, logger: logging.Logger):
    """
    Seeds the default super_admin and operational users if they don't exist.
    """
    logger.info("Seeding default users...")

    # 1. Seed Super Admin User
    super_admin_role = get_role_by_name(SUPER_ADMIN, conn=conn)
    if not super_admin_role:
        logger.critical(f"Role '{SUPER_ADMIN}' not found. Cannot seed super admin user.")
        return

    existing_admin = users_crud.get_user_by_username(conn, "admin")
    if not existing_admin:
        admin_data = {
            "username": "admin",
            "password": "admin",
            "role_id": super_admin_role['role_id'],
            "full_name": "Super Administrator",
            "email": "superadmin@example.local"
        }
        admin_id = users_crud.add_user(db=conn, **admin_data)
        if admin_id:
            logger.info(f"Created super admin user 'admin' with ID: {admin_id}")
        else:
            logger.error("Failed to create super admin user 'admin'.")
    else:
        logger.info("Super admin user 'admin' already exists.")

    # 2. Seed Default Operational User
    operator_role = get_role_by_name(OPERATOR, conn=conn)
    if not operator_role:
        logger.error(f"Role '{OPERATOR}' not found. Cannot seed default operational user.")
        return

    op_username = "default_operational_user"
    existing_op_user = users_crud.get_user_by_username(conn, op_username)
    if not existing_op_user:
        op_user_data = {
            "username": op_username,
            "password": uuid.uuid4().hex,  # Secure random password
            "role_id": operator_role['role_id'],
            "full_name": "Default Operational User",
            "email": f"{op_username}@example.local"
        }
        op_user_id = users_crud.add_user(db=conn, **op_user_data)
        if op_user_id:
            logger.info(f"Created default operational user with ID: {op_user_id}")
        else:
            logger.error("Failed to create default operational user.")
    else:
        logger.info("Default operational user already exists.")

    logger.info("Finished seeding default users.")
