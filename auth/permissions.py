# auth/permissions.py
import logging

logger = logging.getLogger(__name__)

# Define Role Names (consistent with what's stored in DB or used by auth_service)
ADMINISTRATOR = "Administrator"
TEAM_LEAD = "Team Lead"
OPERATOR = "Operator"

# Define Permission Keys (based on Step 7)
# System & User Management
P_MANAGE_USERS = "manage_users"  # CRUD users, change roles, active status
P_MANAGE_ROLES = "manage_roles"  # CRUD roles (if dynamic)
P_MANAGE_SYSTEM_SETTINGS = "manage_system_settings" # General, SMTP, Logistics, Company Profiles, Modules

# Client Management
P_VIEW_ALL_CLIENTS = "view_all_clients"
P_CREATE_CLIENT = "create_client"
P_EDIT_CLIENT_FULL = "edit_client_full" # All client fields
P_EDIT_CLIENT_BASIC = "edit_client_basic" # Potentially restricted fields for operator
P_ARCHIVE_CLIENT = "archive_client"
P_DELETE_CLIENT_PERMANENT = "delete_client_permanent"
P_MANAGE_CLIENT_CONTACTS = "manage_client_contacts" # Add, edit, link, unlink contacts for a client

# Product Management (Global)
P_VIEW_GLOBAL_PRODUCTS = "view_global_products"
P_MANAGE_GLOBAL_PRODUCTS = "manage_global_products" # Create, edit, delete global products, dimensions, equivalencies

# Product Linking (Client Specific)
P_LINK_PRODUCTS_TO_CLIENT = "link_products_to_client" # Add/remove/set qty/price for client

# Document Management (Client Specific)
P_MANAGE_CLIENT_DOCUMENTS = "manage_client_documents" # Create, view, edit, delete client docs, compile, email

# Client Assignments & Billing
P_MANAGE_CLIENT_ASSIGNMENTS = "manage_client_assignments" # Manage assignments of personnel, transporters, etc. to a client/project
P_MANAGE_CLIENT_BILLING = "manage_client_billing" # Manage billing aspects, generate invoices for a client

# Modules & Specific Features
P_ACCESS_PROJECT_MODULE = "access_project_module"
P_MANAGE_ALL_PROJECTS = "manage_all_projects" # Create, edit, task management for all projects
P_MANAGE_ASSIGNED_PROJECTS = "manage_assigned_projects" # For Team Leads/Operators on specific projects

P_ACCESS_STATISTICS_MODULE = "access_statistics_module"
P_ACCESS_PARTNER_MODULE = "access_partner_module"
P_MANAGE_PARTNERS = "manage_partners"

P_ACCESS_INVENTORY_MODULE = "access_inventory_module"
P_MANAGE_INVENTORY = "manage_inventory" # Manage items & stock levels

P_ACCESS_RECRUITMENT_MODULE = "access_recruitment_module"
P_MANAGE_RECRUITMENT = "manage_recruitment"

P_ACCESS_EXPERIENCE_MODULE = "access_experience_module" # Knowledge base
P_MANAGE_EXPERIENCE_ARTICLES = "manage_experience_articles"

P_ACCESS_CALENDAR_MODULE = "access_calendar_module"
P_MANAGE_COMPANY_CALENDAR_EVENTS = "manage_company_calendar_events"
P_MANAGE_OWN_CALENDAR_EVENTS = "manage_own_calendar_events" # All users can manage their own

P_ACCESS_BOTPRESS_MODULE = "access_botpress_module"
P_ACCESS_CARRIER_MAP_MODULE = "access_carrier_map_module"
P_ACCESS_CAMERA_MODULE = "access_camera_module"
P_ACCESS_CALCULATOR_MODULE = "access_calculator_module" # Added
P_MANAGE_STATUSES = "manage_statuses"

# Define a comprehensive list of all permissions
ALL_PERMISSIONS = [
    P_MANAGE_USERS, P_MANAGE_ROLES, P_MANAGE_SYSTEM_SETTINGS,
    P_VIEW_ALL_CLIENTS, P_CREATE_CLIENT, P_EDIT_CLIENT_FULL, P_EDIT_CLIENT_BASIC, P_ARCHIVE_CLIENT, P_DELETE_CLIENT_PERMANENT, P_MANAGE_CLIENT_CONTACTS,
    P_VIEW_GLOBAL_PRODUCTS, P_MANAGE_GLOBAL_PRODUCTS,
    P_LINK_PRODUCTS_TO_CLIENT,
    P_MANAGE_CLIENT_DOCUMENTS,
    P_MANAGE_CLIENT_ASSIGNMENTS, P_MANAGE_CLIENT_BILLING,
    P_ACCESS_PROJECT_MODULE, P_MANAGE_ALL_PROJECTS, P_MANAGE_ASSIGNED_PROJECTS,
    P_ACCESS_STATISTICS_MODULE,
    P_ACCESS_PARTNER_MODULE, P_MANAGE_PARTNERS,
    P_ACCESS_INVENTORY_MODULE, P_MANAGE_INVENTORY,
    P_ACCESS_RECRUITMENT_MODULE, P_MANAGE_RECRUITMENT,
    P_ACCESS_EXPERIENCE_MODULE, P_MANAGE_EXPERIENCE_ARTICLES,
    P_ACCESS_CALENDAR_MODULE, P_MANAGE_COMPANY_CALENDAR_EVENTS, P_MANAGE_OWN_CALENDAR_EVENTS,
    P_ACCESS_BOTPRESS_MODULE, P_ACCESS_CARRIER_MAP_MODULE, P_ACCESS_CAMERA_MODULE, P_ACCESS_CALCULATOR_MODULE,
    P_MANAGE_STATUSES
]

# Define permissions for Team Lead
TEAM_LEAD_PERMISSIONS = [
    P_VIEW_ALL_CLIENTS, P_CREATE_CLIENT, P_EDIT_CLIENT_FULL, P_ARCHIVE_CLIENT, P_MANAGE_CLIENT_CONTACTS,
    P_VIEW_GLOBAL_PRODUCTS, P_MANAGE_GLOBAL_PRODUCTS,
    P_LINK_PRODUCTS_TO_CLIENT,
    P_MANAGE_CLIENT_DOCUMENTS,
    P_MANAGE_CLIENT_ASSIGNMENTS, P_MANAGE_CLIENT_BILLING,
    P_ACCESS_PROJECT_MODULE, P_MANAGE_ALL_PROJECTS, P_MANAGE_ASSIGNED_PROJECTS,
    P_ACCESS_STATISTICS_MODULE,
    P_ACCESS_PARTNER_MODULE, P_MANAGE_PARTNERS,
    P_ACCESS_INVENTORY_MODULE, P_MANAGE_INVENTORY,
    P_ACCESS_RECRUITMENT_MODULE, # Access, not necessarily full management
    P_ACCESS_EXPERIENCE_MODULE, P_MANAGE_EXPERIENCE_ARTICLES,
    P_ACCESS_CALENDAR_MODULE, P_MANAGE_COMPANY_CALENDAR_EVENTS, P_MANAGE_OWN_CALENDAR_EVENTS,
    P_ACCESS_BOTPRESS_MODULE, P_ACCESS_CARRIER_MAP_MODULE, P_ACCESS_CAMERA_MODULE, P_ACCESS_CALCULATOR_MODULE,
    P_MANAGE_STATUSES
]

# Define permissions for Operator
OPERATOR_PERMISSIONS = [
    P_VIEW_ALL_CLIENTS, P_CREATE_CLIENT, P_EDIT_CLIENT_BASIC, P_MANAGE_CLIENT_CONTACTS,
    P_VIEW_GLOBAL_PRODUCTS,
    P_LINK_PRODUCTS_TO_CLIENT,
    P_MANAGE_CLIENT_DOCUMENTS,
    P_ACCESS_PROJECT_MODULE, P_MANAGE_ASSIGNED_PROJECTS,
    P_ACCESS_STATISTICS_MODULE,
    P_ACCESS_PARTNER_MODULE,
    P_ACCESS_INVENTORY_MODULE,
    P_ACCESS_RECRUITMENT_MODULE,
    P_ACCESS_EXPERIENCE_MODULE,
    P_ACCESS_CALENDAR_MODULE, P_MANAGE_OWN_CALENDAR_EVENTS,
    P_ACCESS_BOTPRESS_MODULE, P_ACCESS_CARRIER_MAP_MODULE, P_ACCESS_CAMERA_MODULE, P_ACCESS_CALCULATOR_MODULE
    # Operator typically does not manage statuses, roles, users, or system settings.
]

PERMISSION_MAP = {
    ADMINISTRATOR: ALL_PERMISSIONS,
    TEAM_LEAD: TEAM_LEAD_PERMISSIONS,
    OPERATOR: OPERATOR_PERMISSIONS,
}

# --- PERMISSION_MAP is now OBSOLETE ---
# The PERMISSION_MAP above is no longer directly used by the has_permission function.
# Its structure was used as the source for the initial seeding of the
# RolePermissions table in `db/init_schema.py`.
# For any future changes to default permissions for roles, modifications should
# either be done via the Role Management UI (once implemented) or by adjusting
# the seeding logic in `db/init_schema.py` if fundamental defaults need to change
# prior to application deployment or for new installations.
# It is kept here temporarily for historical reference during development of dynamic permissions.
# Consider removing it entirely once the dynamic permission management is fully stable.
# --- End of PERMISSION_MAP obsolescence notice ---

# Import necessary CRUDs for the new has_permission logic
from db.cruds import roles_crud, role_permissions_crud

def has_permission(user_role_name: str, required_permission_key: str) -> bool:
    """
    Checks if a user with a given role has the specified permission by querying the database.

    Args:
        user_role_name (str): The name of the user's role (e.g., "Administrator").
        required_permission_key (str): The permission key to check (e.g., P_MANAGE_USERS).

    Returns:
        bool: True if the user has the permission, False otherwise.
    """
    if not user_role_name:
        logger.warning("has_permission called with no user_role_name. Denying permission.")
        return False

    if not required_permission_key:
        logger.warning(f"has_permission called for role '{user_role_name}' with no required_permission_key. Denying permission.")
        return False

    try:
        role = roles_crud.get_role_by_name(user_role_name)
        if not role:
            logger.warning(f"Role '{user_role_name}' not found in database. Denying permission for '{required_permission_key}'.")
            return False

        role_id = role.get('role_id')
        if role_id is None: # Should not happen if role is fetched correctly
            logger.error(f"Role '{user_role_name}' fetched but has no role_id. Denying permission for '{required_permission_key}'.")
            return False

        # Check if the role has the permission
        has_perm = role_permissions_crud.check_role_has_permission(role_id, required_permission_key)

        if has_perm:
            logger.debug(f"Permission '{required_permission_key}' GRANTED for role '{user_role_name}' (ID: {role_id}) via database check.")
        else:
            logger.debug(f"Permission '{required_permission_key}' DENIED for role '{user_role_name}' (ID: {role_id}) via database check.")
        return has_perm

    except Exception as e:
        logger.error(f"Error checking permission for role '{user_role_name}', permission '{required_permission_key}': {e}", exc_info=True)
        return False # Fail safe: deny permission on error

# Example usage (for testing this module):
# Note: This test block will now rely on the database being initialized and seeded.
if __name__ == '__main__':
    # To run this test block standalone, you'd need to ensure db_init.py has run
    # and the project root is in sys.path for db.cruds imports to work.
    # Example:
    # import sys
    # import os
    # project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # sys.path.insert(0, project_root)
    # from db.init_schema import initialize_database
    # initialize_database() # This would initialize your actual DB or a test DB

    logging.basicConfig(level=logging.DEBUG)

    # Test cases (assuming 'Administrator', 'Team Lead', 'Operator' roles and permissions are seeded)
    print(f"Testing permissions (dynamic from DB):")
    print(f"  Admin has '{P_MANAGE_USERS}': {has_permission(ADMINISTRATOR, P_MANAGE_USERS)}")
    print(f"  Team Lead has '{P_MANAGE_USERS}': {has_permission(TEAM_LEAD, P_MANAGE_USERS)}") # Expected False based on old map

    # Find a permission Operator should have from the old map for a positive test
    # Example: P_CREATE_CLIENT was in Operator's list
    print(f"  Operator has '{P_CREATE_CLIENT}': {has_permission(OPERATOR, P_CREATE_CLIENT)}") # Expected True

    # Find a permission Operator should NOT have
    print(f"  Operator has '{P_MANAGE_SYSTEM_SETTINGS}': {has_permission(OPERATOR, P_MANAGE_SYSTEM_SETTINGS)}") # Expected False

    print(f"  Unknown Role ('Visitor') has '{P_CREATE_CLIENT}': {has_permission('Visitor', P_CREATE_CLIENT)}") # Expected False
    print(f"  Admin has 'unknown_permission': {has_permission(ADMINISTRATOR, 'unknown_permission_key_xyz')}") # Expected False
    print(f"  Admin has no permission key: {has_permission(ADMINISTRATOR, '')}") # Expected False
    print(f"  No role name has '{P_MANAGE_USERS}': {has_permission('', P_MANAGE_USERS)}") # Expected False
