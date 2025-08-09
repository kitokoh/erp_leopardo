import sqlite3
import logging
from auth.roles import SUPER_ADMIN as SUPER_ADMIN_ROLE_NAME
from auth import permissions as auth_perms_module
from db.cruds.users.roles_crud import add_role, get_role_by_name

def seed_roles_and_permissions(conn: sqlite3.Connection, logger_passed: logging.Logger):
    """Seeds roles, permissions, and role-permission links."""
    logger = logger_passed
    cursor = conn.cursor()

    # Seed Roles
    logger.info("Seeding default roles...")
    roles_to_seed_map = {
        auth_perms_module.ADMINISTRATOR: "Full application access and user management.",
        auth_perms_module.TEAM_LEAD: "Manages projects and teams, advanced client/product operations.",
        auth_perms_module.OPERATOR: "Standard user for daily operations, data entry, document generation."
    }
    if SUPER_ADMIN_ROLE_NAME not in roles_to_seed_map:
        roles_to_seed_map[SUPER_ADMIN_ROLE_NAME] = "Super administrator with all system privileges."

    current_role_ids = {}
    for role_name, desc in roles_to_seed_map.items():
        existing_role = get_role_by_name(role_name, conn=conn)
        if existing_role:
            current_role_ids[role_name] = existing_role['role_id']
            logger.info(f"Role '{role_name}' already exists with ID {existing_role['role_id']}.")
        else:
            new_role_id = add_role(role_name, desc, conn=conn)
            if new_role_id:
                current_role_ids[role_name] = new_role_id
                logger.info(f"Role '{role_name}' added with ID {new_role_id}.")
            else:
                logger.error(f"Failed to add role '{role_name}'.")

    # Seed Permissions
    logger.info("Seeding permissions...")
    all_permission_keys = [getattr(auth_perms_module, attr) for attr in dir(auth_perms_module) if attr.startswith("P_")]
    for p_key in all_permission_keys:
        if isinstance(p_key, str):
            desc = p_key.replace("P_", "").replace("_", " ").capitalize()
            cursor.execute("INSERT OR IGNORE INTO Permissions (permission_key, description) VALUES (?, ?)", (p_key, f"Permission to {desc}"))
    logger.info(f"{len(all_permission_keys)} permissions seeded.")

    # Seed RolePermissions
    logger.info("Seeding role-permission links...")
    admin_role_id = current_role_ids.get(auth_perms_module.ADMINISTRATOR)
    if admin_role_id:
        for p_key in all_permission_keys:
            if isinstance(p_key, str):
                cursor.execute("INSERT OR IGNORE INTO RolePermissions (role_id, permission_key) VALUES (?, ?)", (admin_role_id, p_key))

    super_admin_role_id = current_role_ids.get(SUPER_ADMIN_ROLE_NAME)
    if super_admin_role_id:
        for p_key in all_permission_keys:
            if isinstance(p_key, str):
                cursor.execute("INSERT OR IGNORE INTO RolePermissions (role_id, permission_key) VALUES (?, ?)", (super_admin_role_id, p_key))

    for role_name_const, perm_keys_list in auth_perms_module.PERMISSION_MAP.items():
        role_name = role_name_constant
        if role_name not in [auth_perms_module.ADMINISTRATOR, SUPER_ADMIN_ROLE_NAME]:
            role_id = current_role_ids.get(role_name)
            if role_id:
                for perm_key in perm_keys_list:
                    if perm_key in all_permission_keys:
                        cursor.execute("INSERT OR IGNORE INTO RolePermissions (role_id, permission_key) VALUES (?, ?)", (role_id, perm_key))

    logger.info("Finished seeding roles and permissions.")
    return current_role_ids
