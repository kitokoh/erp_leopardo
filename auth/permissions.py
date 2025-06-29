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
P_ACCESS_PDF_EDITOR_MODULE = "access_pdf_editor_module" # Added PDF Editor Permission
P_MANAGE_STATUSES = "manage_statuses"


# PERMISSION_MAP: Defines which roles have which permissions.
PERMISSION_MAP = {
    ADMINISTRATOR: [
        P_MANAGE_USERS, P_MANAGE_ROLES, P_MANAGE_SYSTEM_SETTINGS, P_MANAGE_STATUSES,
        P_VIEW_ALL_CLIENTS, P_CREATE_CLIENT, P_EDIT_CLIENT_FULL, P_ARCHIVE_CLIENT, P_DELETE_CLIENT_PERMANENT,
        P_MANAGE_CLIENT_CONTACTS,
        P_VIEW_GLOBAL_PRODUCTS, P_MANAGE_GLOBAL_PRODUCTS,
        P_LINK_PRODUCTS_TO_CLIENT,
        P_MANAGE_CLIENT_DOCUMENTS,
        P_MANAGE_CLIENT_ASSIGNMENTS, P_MANAGE_CLIENT_BILLING, # Added
        P_ACCESS_PROJECT_MODULE, P_MANAGE_ALL_PROJECTS,
        P_ACCESS_STATISTICS_MODULE,
        P_ACCESS_PARTNER_MODULE, P_MANAGE_PARTNERS,
        P_ACCESS_INVENTORY_MODULE, P_MANAGE_INVENTORY,
        P_ACCESS_RECRUITMENT_MODULE, P_MANAGE_RECRUITMENT,
        P_ACCESS_EXPERIENCE_MODULE, P_MANAGE_EXPERIENCE_ARTICLES,
        P_ACCESS_CALENDAR_MODULE, P_MANAGE_COMPANY_CALENDAR_EVENTS, P_MANAGE_OWN_CALENDAR_EVENTS,
        P_ACCESS_BOTPRESS_MODULE, P_ACCESS_CARRIER_MAP_MODULE, P_ACCESS_CAMERA_MODULE, P_ACCESS_CALCULATOR_MODULE,
        P_ACCESS_PDF_EDITOR_MODULE, # Added PDF Editor Permission
    ],
    TEAM_LEAD: [
        P_VIEW_ALL_CLIENTS, P_CREATE_CLIENT, P_EDIT_CLIENT_FULL, P_ARCHIVE_CLIENT,
        P_MANAGE_CLIENT_CONTACTS,
        P_VIEW_GLOBAL_PRODUCTS, P_MANAGE_GLOBAL_PRODUCTS, # Might restrict delete from P_MANAGE_GLOBAL_PRODUCTS for TL
        P_LINK_PRODUCTS_TO_CLIENT,
        P_MANAGE_CLIENT_DOCUMENTS, # Might restrict delete for TL
        P_MANAGE_CLIENT_ASSIGNMENTS, P_MANAGE_CLIENT_BILLING, # Added
        P_ACCESS_PROJECT_MODULE, P_MANAGE_ALL_PROJECTS, # Or P_MANAGE_ASSIGNED_PROJECTS
        P_ACCESS_STATISTICS_MODULE,
        P_ACCESS_PARTNER_MODULE, P_MANAGE_PARTNERS,
        P_ACCESS_INVENTORY_MODULE, P_MANAGE_INVENTORY,
        P_ACCESS_RECRUITMENT_MODULE, P_MANAGE_RECRUITMENT,
        P_ACCESS_EXPERIENCE_MODULE, P_MANAGE_EXPERIENCE_ARTICLES,
        P_ACCESS_CALENDAR_MODULE, P_MANAGE_OWN_CALENDAR_EVENTS,
        P_ACCESS_BOTPRESS_MODULE, P_ACCESS_CARRIER_MAP_MODULE, P_ACCESS_CAMERA_MODULE, P_ACCESS_CALCULATOR_MODULE,
        P_ACCESS_PDF_EDITOR_MODULE, # Added PDF Editor Permission
    ],
    OPERATOR: [
        P_VIEW_ALL_CLIENTS, # Allowing view all for now for simplicity, can be changed to assigned_only
        P_CREATE_CLIENT, P_EDIT_CLIENT_BASIC, P_ARCHIVE_CLIENT,
        P_MANAGE_CLIENT_CONTACTS,
        P_VIEW_GLOBAL_PRODUCTS,
        P_LINK_PRODUCTS_TO_CLIENT,
        P_MANAGE_CLIENT_DOCUMENTS, # Create, View. Edit/Delete could be fine-tuned by UI action handlers.
        P_ACCESS_PROJECT_MODULE, # View assigned projects/tasks
        P_ACCESS_EXPERIENCE_MODULE,
        P_ACCESS_CALENDAR_MODULE, P_MANAGE_OWN_CALENDAR_EVENTS,
        P_ACCESS_BOTPRESS_MODULE, P_ACCESS_CARRIER_MAP_MODULE, P_ACCESS_CALCULATOR_MODULE,
        P_ACCESS_PDF_EDITOR_MODULE, # Added PDF Editor Permission
    ]
}

def has_permission(user_role_name: str, required_permission_key: str) -> bool:
    """
    Checks if a user with a given role has the specified permission.

    Args:
        user_role_name (str): The name of the user's role (e.g., "Administrator", "Team Lead").
        required_permission_key (str): The permission key to check (e.g., P_MANAGE_USERS).

    Returns:
        bool: True if the user has the permission, False otherwise.
    """
    if not user_role_name:
        logger.warning("has_permission called with no user_role_name. Denying permission.")
        return False

    role_permissions = PERMISSION_MAP.get(user_role_name)

    if role_permissions is None:
        logger.warning(f"Role '{user_role_name}' not found in PERMISSION_MAP. Denying permission for '{required_permission_key}'.")
        return False

    if required_permission_key in role_permissions:
        logger.debug(f"Permission '{required_permission_key}' GRANTED for role '{user_role_name}'.")
        return True
    else:
        logger.debug(f"Permission '{required_permission_key}' DENIED for role '{user_role_name}'.")
        return False

# Example usage (for testing this module):
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    print(f"Admin has '{P_MANAGE_USERS}': {has_permission(ADMINISTRATOR, P_MANAGE_USERS)}")
    print(f"Team Lead has '{P_MANAGE_USERS}': {has_permission(TEAM_LEAD, P_MANAGE_USERS)}")
    print(f"Operator has '{P_CREATE_CLIENT}': {has_permission(OPERATOR, P_CREATE_CLIENT)}")
    print(f"Operator has '{P_MANAGE_GLOBAL_PRODUCTS}': {has_permission(OPERATOR, P_MANAGE_GLOBAL_PRODUCTS)}")
    print(f"Operator has '{P_EDIT_CLIENT_FULL}': {has_permission(OPERATOR, P_EDIT_CLIENT_FULL)}")
    print(f"Operator has '{P_EDIT_CLIENT_BASIC}': {has_permission(OPERATOR, P_EDIT_CLIENT_BASIC)}")
    print(f"Unknown Role has '{P_CREATE_CLIENT}': {has_permission('Visitor', P_CREATE_CLIENT)}")
    print(f"Admin has 'unknown_permission': {has_permission(ADMINISTRATOR, 'unknown_permission')}")
