# User Roles
SUPER_ADMIN = "super_admin"
ADMINISTRATOR = "administrator"
STANDARD_USER = "standard_user"
READ_ONLY_USER = "read_only_user"

ALL_ROLES = {SUPER_ADMIN, ADMINISTRATOR, STANDARD_USER, READ_ONLY_USER}

# The ROLE_PERMISSIONS dictionary and the old has_permission function
# that were previously here have been removed as they were deprecated.
# All permission checking should now use the dynamic, database-backed system
# available via `auth.permissions.has_permission(user_role_name, permission_key)`.

# --- Permission Checking Functions ---

# The deprecated has_permission function has been removed.

def check_user_role(user_role: str, allowed_roles: set[str]) -> bool:
    """
    Checks if the user's role is one of the allowed roles.
    """
    if not user_role: # Handle cases where user_role might be None or empty
        return False
    return user_role in allowed_roles

# Example usage (for demonstration, not for direct use in FastAPI deps yet):
# def require_role(user_role: str, target_roles: set[str]):
#     if not check_user_role(user_role, target_roles):
#         raise Exception(f"User role '{user_role}' not authorized. Requires one of: {target_roles}")

# def require_permission_explicit(user_role: str, permission_needed: str):
#     if not has_permission(user_role, permission_needed):
#         raise Exception(f"User role '{user_role}' lacks permission: '{permission_needed}'")
