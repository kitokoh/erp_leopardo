# db/cruds/__init__.py
import logging

# Import instances or specific functions from the new sub-modules
from .misc import activity_logs_crud
from .misc import application_settings_crud
from .clients import client_assigned_personnel_crud
from .clients import client_contacts_crud
from .clients import client_documents_crud
from .clients import client_freight_forwarders_crud
from .clients import client_project_products_crud
from .clients import client_order_money_transfer_agents_crud
from .clients import client_transporters_crud
from .clients import clients_crud
from .misc import companies_crud
from .misc import company_personnel_crud
from .misc import contacts_crud
from .users import employees_crud
from .users import employee_documents_crud
from .misc import experience_crud
from .misc import cover_page_templates_crud
from .misc import cover_pages_crud
from .misc import freight_forwarders_crud
from .misc import google_sync_crud
from .misc import hr_reports_crud
from .products import internal_stock_items_crud
from .projects import kpis_crud
from .leave import leave_crud
from .products import item_locations_crud
from .misc import locations_crud
from .projects import milestones_crud
from .performance import performance_crud
from .misc import partners_crud
from .products import product_media_links_crud
from .products import products_crud_instance
from .projects import projects_crud_instance
from .misc import status_settings_crud
from .misc import tags_crud
from .projects import tasks_crud
from .users import team_members_crud
from .misc import template_categories_crud
from .misc import templates_crud
from .misc import transporters_crud
from .misc import money_transfer_agents_crud
from .invoices import commandes_crud
from .users import users_crud
from .users import roles_crud
from .users import password_reset_tokens_crud
from . import user_session_tokens_crud

# This is a simplified __all__ for clarity.
# The goal is to allow access like `db.cruds.clients_crud.add_client(...)`
__all__ = [
    "activity_logs_crud",
    "application_settings_crud",
    "client_assigned_personnel_crud",
    "client_contacts_crud",
    "client_documents_crud",
    "client_freight_forwarders_crud",
    "client_project_products_crud",
    "client_order_money_transfer_agents_crud",
    "client_transporters_crud",
    "clients_crud",
    "companies_crud",
    "company_personnel_crud",
    "contacts_crud",
    "employees_crud",
    "employee_documents_crud",
    "experience_crud",
    "cover_page_templates_crud",
    "cover_pages_crud",
    "freight_forwarders_crud",
    "google_sync_crud",
    "hr_reports_crud",
    "internal_stock_items_crud",
    "item_locations_crud",
    "kpis_crud",
    "leave_crud",
    "locations_crud",
    "milestones_crud",
    "performance_crud",
    "partners_crud",
    "product_media_links_crud",
    "products_crud_instance",
    "projects_crud_instance",
    "status_settings_crud",
    "tags_crud",
    "tasks_crud",
    "team_members_crud",
    "template_categories_crud",
    "templates_crud",
    "transporters_crud",
    "money_transfer_agents_crud",
    "commandes_crud",
    "users_crud",
    "roles_crud",
    "password_reset_tokens_crud",
    "user_session_tokens_crud",
]
