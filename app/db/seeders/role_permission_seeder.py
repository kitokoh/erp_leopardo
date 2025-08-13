import json
import os
import logging
import sqlite3

from app.db.cruds.users.roles_crud import add_role, get_role_by_name
from app.db.cruds.users.permissions_crud import add_permission, get_permission_by_key
from app.db.cruds.role_permissions_crud import add_permission_to_role

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def seed_roles_and_permissions(conn: sqlite3.Connection, logger: logging.Logger):
    """
    Seeds roles, permissions, and their relationships from the default_roles_permissions.json file.
    """
    logger.info("Seeding roles and permissions from default_roles_permissions.json...")
    json_path = os.path.join(PROJECT_ROOT, "db", "seed_data", "default_roles_permissions.json")

    if not os.path.exists(json_path):
        logger.error(f"JSON file not found at: {json_path}. Skipping role and permission seeding.")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. Seed Permissions
    all_permission_keys = []
    for perm_data in data.get("permissions", []):
        key = perm_data["key"]
        all_permission_keys.append(key)
        existing_perm = get_permission_by_key(key, conn=conn)
        if not existing_perm:
            add_permission(key, perm_data["description"], conn=conn)
            logger.info(f"Added permission: {key}")
    logger.info("Finished seeding Permissions table.")

    # 2. Seed Roles and RolePermissions
    for role_data in data.get("roles", []):
        role_name = role_data["name"]
        existing_role = get_role_by_name(role_name, conn=conn)
        if existing_role:
            role_id = existing_role['role_id']
            logger.info(f"Role '{role_name}' already exists with ID {role_id}.")
        else:
            role_id = add_role(role_name, role_data["description"], conn=conn)
            if role_id:
                logger.info(f"Added role '{role_name}' with ID {role_id}.")
            else:
                logger.error(f"Failed to add role '{role_name}'. Skipping its permissions.")
                continue

        # 3. Assign Permissions to Role
        permissions_to_assign = role_data["permissions"]
        if "all" in permissions_to_assign:
            permissions_to_assign = all_permission_keys

        for perm_key in permissions_to_assign:
            # We don't need to check if perm_key exists in the permissions table
            # because add_permission_to_role should handle that (or fail gracefully).
            # The foreign key constraint will enforce integrity.
            add_permission_to_role(role_id, perm_key, conn=conn)

        logger.info(f"Assigned {len(permissions_to_assign)} permissions to role '{role_name}'.")

    logger.info("Finished seeding Roles and RolePermissions.")
