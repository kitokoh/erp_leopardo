# auth/permissions.py
import logging
from sqlalchemy.orm import Session

from app.db.cruds.users import roles_crud, permissions_crud
from app.db.cruds.users import role_permissions_crud
from app.services.auth.roles import SUPER_ADMIN as SUPER_ADMIN_ROLE_CONSTANT

logger = logging.getLogger(__name__)

# Define Role Names
ADMINISTRATOR = "Administrator"
TEAM_LEAD = "Team Lead"
OPERATOR = "Operator"

# Define Permission Keys
P_MANAGE_USERS = "manage_users"
P_MANAGE_ROLES = "manage_roles"
P_MANAGE_SYSTEM_SETTINGS = "manage_system_settings"
P_VIEW_ALL_CLIENTS = "view_all_clients"
P_CREATE_CLIENT = "create_client"
P_EDIT_CLIENT_FULL = "edit_client_full"
P_EDIT_CLIENT_BASIC = "edit_client_basic"
P_ARCHIVE_CLIENT = "archive_client"
P_DELETE_CLIENT_PERMANENT = "delete_client_permanent"
P_MANAGE_CLIENT_CONTACTS = "manage_client_contacts"
P_REFERENTS_MANAGE = "manage_referents"
P_MANAGE_CLIENT_VISITS = "manage_client_visits"
P_VIEW_CLIENT_VISITS = "view_client_visits"
P_VIEW_GLOBAL_PRODUCTS = "view_global_products"
P_MANAGE_GLOBAL_PRODUCTS = "manage_global_products"
P_LINK_PRODUCTS_TO_CLIENT = "link_products_to_client"
P_MANAGE_CLIENT_DOCUMENTS = "manage_client_documents"
P_MANAGE_CLIENT_ASSIGNMENTS = "manage_client_assignments"
P_MANAGE_CLIENT_BILLING = "manage_client_billing"
P_VIEW_CLIENT_BILLING = "view_client_billing"
P_ACCESS_PROJECT_MODULE = "access_project_module"
P_MANAGE_ALL_PROJECTS = "manage_all_projects"
P_MANAGE_ASSIGNED_PROJECTS = "manage_assigned_projects"
P_ACCESS_STATISTICS_MODULE = "access_statistics_module"
P_ACCESS_PARTNER_MODULE = "access_partner_module"
P_MANAGE_PARTNERS = "manage_partners"
P_ACCESS_INVENTORY_MODULE = "access_inventory_module"
P_MANAGE_INVENTORY = "manage_inventory"
P_ACCESS_RECRUITMENT_MODULE = "access_recruitment_module"
P_MANAGE_RECRUITMENT = "manage_recruitment"
P_ACCESS_EXPERIENCE_MODULE = "access_experience_module"
P_MANAGE_EXPERIENCE_ARTICLES = "manage_experience_articles"
P_ACCESS_CALENDAR_MODULE = "access_calendar_module"
P_MANAGE_COMPANY_CALENDAR_EVENTS = "manage_company_calendar_events"
P_MANAGE_OWN_CALENDAR_EVENTS = "manage_own_calendar_events"
P_ACCESS_BOTPRESS_MODULE = "access_botpress_module"
P_ACCESS_CARRIER_MAP_MODULE = "access_carrier_map_module"
P_ACCESS_CAMERA_MODULE = "access_camera_module"
P_ACCESS_CALCULATOR_MODULE = "access_calculator_module"
P_MANAGE_STATUSES = "manage_statuses"
ALL_PERMISSIONS = [
    P_MANAGE_USERS, P_MANAGE_ROLES, P_MANAGE_SYSTEM_SETTINGS,
    P_VIEW_ALL_CLIENTS, P_CREATE_CLIENT, P_EDIT_CLIENT_FULL, P_EDIT_CLIENT_BASIC, P_ARCHIVE_CLIENT, P_DELETE_CLIENT_PERMANENT, P_MANAGE_CLIENT_CONTACTS, P_REFERENTS_MANAGE,
    P_MANAGE_CLIENT_VISITS, P_VIEW_CLIENT_VISITS,
    P_VIEW_GLOBAL_PRODUCTS, P_MANAGE_GLOBAL_PRODUCTS,
    P_LINK_PRODUCTS_TO_CLIENT,
    P_MANAGE_CLIENT_DOCUMENTS,
    P_MANAGE_CLIENT_ASSIGNMENTS, P_MANAGE_CLIENT_BILLING, P_VIEW_CLIENT_BILLING,
    P_VIEW_CLIENT_VISITS, P_MANAGE_CLIENT_VISITS,
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

def has_permission(conn: Session, user_role_name: str, required_permission_key: str) -> bool:
    if not user_role_name:
        logger.warning("has_permission called with no user_role_name. Denying permission.")
        return False

    if user_role_name == SUPER_ADMIN_ROLE_CONSTANT:
        logger.debug(f"Permission check for role '{user_role_name}' (SUPER_ADMIN) for key '{required_permission_key}': GRANTED (superuser).")
        return True

    if not required_permission_key:
        logger.warning(f"has_permission called for role '{user_role_name}' with no required_permission_key. Denying permission.")
        return False

    try:
        role = roles_crud.get_role_by_name(conn, user_role_name)
        if not role:
            logger.warning(f"Role '{user_role_name}' not found in database. Denying permission for '{required_permission_key}'.")
            return False

        role_id = role.role_id
        if role_id is None:
            logger.error(f"Role '{user_role_name}' fetched but has no role_id. Denying permission for '{required_permission_key}'.")
            return False

        has_perm = role_permissions_crud.check_role_has_permission(conn=conn, role_id=role_id, permission_key=required_permission_key)

        if has_perm:
            logger.debug(f"Permission '{required_permission_key}' GRANTED for role '{user_role_name}' (ID: {role_id}) via database check.")
        else:
            logger.debug(f"Permission '{required_permission_key}' DENIED for role '{user_role_name}' (ID: {role_id}) via database check.")
        return has_perm

    except Exception as e:
        logger.error(f"Error checking permission for role '{user_role_name}', permission '{required_permission_key}': {e}", exc_info=True)
        return False
