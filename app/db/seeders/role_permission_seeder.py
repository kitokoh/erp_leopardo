import json
import logging
import os
from db.cruds.users.roles_crud import add_role, get_role_by_name
from db.cruds.users.permissions_crud import add_permission, get_permission_by_codename
from db.cruds.role_permissions_crud import add_permission_to_role

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def seed_roles_and_permissions(conn, logger: logging.Logger):
    """
    Seeds roles, permissions, and their relationships from a JSON file.
    """
    logger.info("Seeding roles and permissions from JSON file...")
    json_path = os.path.join(PROJECT_ROOT, "db", "seed_data", "default_roles_permissions.json")

    if not os.path.exists(json_path):
        logger.error(f"JSON file not found at: {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. Seed Permissions
    all_permission_keys = []
    for perm_data in data.get("permissions", []):
        key = perm_data["key"]
        all_permission_keys.append(key)
        # In the new structure, we use codename which is the same as key
        existing_perm = get_permission_by_codename(key, conn=conn)
        if not existing_perm:
            # The new add_permission takes (name, codename, conn)
            # We will use the key for both name and codename for simplicity
            add_permission(key, key, conn=conn)
            logger.info(f"Added permission: {key}")

    # 2. Seed Roles and Assign Permissions
    for role_data in data.get("roles", []):
        role_name = role_data["name"]
        existing_role = get_role_by_name(role_name, conn=conn)

        if existing_role:
            role_id = existing_role['id']
            logger.info(f"Role '{role_name}' already exists with ID {role_id}.")
        else:
            role_id = add_role(role_name, role_data.get("description", ""), conn=conn)
            if role_id:
                logger.info(f"Added role '{role_name}' with ID {role_id}.")
            else:
                logger.error(f"Failed to add role '{role_name}'.")
                continue

        # 3. Assign Permissions to Role
        permissions_to_assign = role_data["permissions"]
        if "all" in permissions_to_assign:
            permissions_to_assign = all_permission_keys

        for perm_key in permissions_to_assign:
            # The function is add_permission_to_role(role_id, permission_key, conn)
            add_permission_to_role(role_id, perm_key, conn=conn)

        logger.info(f"Assigned {len(permissions_to_assign)} permissions to role '{role_name}'.")

    logger.info("Finished seeding roles and permissions.")
