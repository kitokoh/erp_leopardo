# db/cruds/__init__.py
import logging

# Explicitly import functions to make them available directly under db.cruds namespace
from .activity_logs_crud import add_activity_log, get_activity_logs
from .application_settings_crud import get_setting, set_setting
from .client_assigned_personnel_crud import assign_personnel_to_client, get_assigned_personnel_for_client, unassign_personnel_from_client
from .client_documents_crud import add_client_document, get_document_by_id, get_documents_for_client, get_client_document_notes, add_client_document_note, update_client_document_note, delete_client_document_note, get_client_document_note_by_id, delete_client_document
from .client_freight_forwarders_crud import assign_forwarder_to_client, get_assigned_forwarders_for_client, unassign_forwarder_from_client
from .client_project_products_crud import get_products_for_client_or_project, add_product_to_client_or_project, update_client_project_product, remove_product_from_client_or_project, get_client_project_product_by_id, get_distinct_purchase_confirmed_at_for_client
from .client_order_money_transfer_agents_crud import assign_agent_to_client_order, get_assigned_agents_for_client_order, unassign_agent_from_client_order, update_assignment_details as update_mta_assignment_details
from .client_transporters_crud import assign_transporter_to_client, get_assigned_transporters_for_client, unassign_transporter_from_client, update_client_transporter_email_status
from .clients_crud import get_all_clients, get_client_by_id, get_active_clients_count, get_client_counts_by_country, get_client_segmentation_by_city, get_client_segmentation_by_status, get_client_segmentation_by_category, get_total_clients_count, update_client, add_client, delete_client as soft_delete_client, get_all_clients_with_details, get_clients_by_archival_status, get_active_clients_per_country, add_client_note as add_client_note_to_client, get_client_notes as get_client_notes_for_client, get_clients_count_created_between, get_total_clients_count_up_to_date, get_active_clients_count_up_to_date
from .companies_crud import add_company, get_company_by_id, get_all_companies, update_company, delete_company, set_default_company, get_default_company
from .company_personnel_crud import add_company_personnel, get_personnel_for_company, update_company_personnel, delete_company_personnel
from .contacts_crud import get_contacts_for_client, add_contact, get_contact_by_id as get_contact_details_by_id, get_contact_by_email, get_all_contacts, update_contact, delete_contact, link_contact_to_client, unlink_contact_from_client, get_contacts_for_client_count, get_clients_for_contact, get_specific_client_contact_link_details, update_client_contact_link, unlink_contact_from_client_by_link_id
from .employees_crud import add_employee, get_employee_by_id, get_all_employees, update_employee, delete_employee as soft_delete_employee
from .employee_documents_crud import add_employee_document, get_employee_documents, delete_employee_document
from .experience_crud import add_experience, get_experience_by_id, get_all_experiences, update_experience, delete_experience
from .cover_page_templates_crud import get_cover_page_template_by_id as get_cover_template_by_id # Alias to avoid conflict
from .cover_pages_crud import get_cover_pages_for_client, add_cover_page, update_cover_page, delete_cover_page, get_cover_page_by_id
from .freight_forwarders_crud import get_all_freight_forwarders, add_freight_forwarder, get_freight_forwarder_by_id, update_freight_forwarder, delete_freight_forwarder
from .google_sync_crud import get_user_google_account_by_google_account_id, update_user_google_account, add_user_google_account, get_user_google_account_by_user_id, get_user_google_account_by_id as get_google_account_by_id, delete_user_google_account, add_contact_sync_log, get_contact_sync_log_by_local_contact, get_contact_sync_log_by_google_contact_id, get_contact_sync_log_by_id, update_contact_sync_log, delete_contact_sync_log, get_contacts_pending_sync, get_all_sync_logs_for_account
from .hr_reports_crud import add_hr_report, get_hr_report_by_id, get_all_hr_reports, update_hr_report, delete_hr_report
from .internal_stock_items_crud import add_internal_stock_item, get_internal_stock_item_by_id, get_all_internal_stock_items, update_internal_stock_item, delete_internal_stock_item
from .kpis_crud import get_kpis_for_project, add_kpi, update_kpi, delete_kpi
from .leave_crud import add_leave_request, get_leave_request_by_id, get_leave_requests_for_employee, get_all_leave_requests, update_leave_request_status
from .item_locations_crud import add_item_location, get_item_location_by_id, get_all_item_locations, update_item_location, delete_item_location
from .locations_crud import get_all_countries, add_country, get_or_add_country, get_all_cities, add_city, get_or_add_city, get_country_by_id, get_city_by_id, get_country_by_name, get_city_by_name_and_country_id
from .milestones_crud import get_milestones_for_project, add_milestone, get_milestone_by_id, update_milestone, delete_milestone
from .performance_crud import add_performance_review, get_performance_review_by_id, get_performance_reviews_for_employee, update_performance_review, delete_performance_review
from .partners_crud import get_all_partner_categories, get_all_partners, get_partners_in_category, get_categories_for_partner, get_partner_by_id as get_partner_details_by_id, get_documents_for_partner, add_partner_document, update_partner_document, delete_partner_document, get_partner_document_by_id, get_contacts_for_partner, add_partner_contact, update_partner_contact, delete_partner_contact, add_partner, update_partner, delete_partner, link_partner_to_category, unlink_partner_from_category, get_or_add_partner_category, get_partner_category_by_name, add_partner_category, delete_partner_category, update_partner_category, get_partner_category_by_id, add_partner_interaction, get_interactions_for_partner, update_partner_interaction, delete_partner_interaction
from .product_media_links_crud import add_product_media_link, get_media_links_for_product, delete_product_media_link, get_product_media_link_by_id
from .products_crud import get_product_by_id, add_product as add_global_product, get_product_by_name, get_product_by_code, get_all_products as get_all_global_products, update_product as update_global_product, delete_product as soft_delete_global_product, get_products as get_active_products_by_lang, update_product_price, get_products_by_name_pattern, get_all_products_for_selection_filtered, get_total_products_count as get_global_total_products_count, add_or_update_product_dimension, get_product_dimension, delete_product_dimension, add_product_equivalence, get_equivalent_products, get_all_product_equivalencies, remove_product_equivalence # Using get_equivalent_products
from .projects_crud import get_all_projects, get_project_by_id, add_project, update_project, delete_project, get_total_projects_count as get_total_project_count_stat, get_active_projects_count as get_active_project_count_stat, get_projects_by_client_id
from .status_settings_crud import get_status_setting_by_id, get_all_status_settings, get_status_setting_by_name, add_status_setting, update_status_setting, delete_status_setting
from .tags_crud import add_tag, get_tag_by_id, get_all_tags, update_tag, delete_tag, get_tags_for_item, add_tag_to_item, remove_tag_from_item
from .tasks_crud import get_tasks_by_project_id, add_task, update_task, delete_task, get_task_by_id, get_tasks_by_assignee_id, get_tasks_by_project_id_ordered_by_sequence, add_task_dependency, get_predecessor_tasks, remove_task_dependency
from .team_members_crud import get_all_team_members, get_team_member_by_id, add_team_member, update_team_member, delete_team_member
from .template_categories_crud import get_all_template_categories, add_template_category, update_template_category, delete_template_category, get_template_category_by_id, get_template_category_by_name
from .templates_crud import get_all_templates, get_template_by_id, add_template, update_template, delete_template, get_all_file_based_templates, get_distinct_template_languages, get_distinct_template_types, get_filtered_templates, get_distinct_languages_for_template_type, add_utility_document_template, get_utility_documents
from .transporters_crud import get_all_transporters, add_transporter, get_transporter_by_id, update_transporter, delete_transporter
from .money_transfer_agents_crud import get_all_money_transfer_agents, add_money_transfer_agent, get_money_transfer_agent_by_id, update_money_transfer_agent, delete_money_transfer_agent
from .users_crud import get_user_by_id, list_users, update_user_password, verify_password, add_user as add_user_crud, verify_user_password, update_user_role, set_user_active_status, record_login_time, get_user_by_username
from .company_expenses_crud import add_company_expense, get_company_expense_by_id, get_all_company_expenses, update_company_expense, delete_company_expense

# Also import modules themselves if direct access like db.cruds.clients_crud is used elsewhere
from . import activity_logs_crud
from . import application_settings_crud
from . import client_assigned_personnel_crud # Added
from . import client_documents_crud
from . import client_freight_forwarders_crud # Added
from . import client_project_products_crud
from . import client_order_money_transfer_agents_crud # Added
from . import client_transporters_crud # Added
from . import clients_crud
from . import companies_crud
from . import company_personnel_crud
from . import contacts_crud
from . import employees_crud
from . import employee_documents_crud
from . import experience_crud # Added
from . import cover_page_templates_crud
from . import cover_pages_crud
from . import freight_forwarders_crud # Added
from . import google_sync_crud
from . import hr_reports_crud
from . import internal_stock_items_crud # Added
from . import kpis_crud
from . import leave_crud
from . import item_locations_crud # Added
from . import locations_crud
from . import milestones_crud
from . import performance_crud
from . import partners_crud
from . import product_media_links_crud
from . import products_crud
from . import projects_crud
from . import status_settings_crud
from . import tags_crud
from . import tasks_crud
from . import team_members_crud
from . import template_categories_crud
from . import templates_crud
from . import transporters_crud # Added
from . import money_transfer_agents_crud # Added
from . import users_crud
from . import company_expenses_crud # Added for new expense module

try:
    from . import media_items_crud
except ImportError:
    media_items_crud = None
    logging.warning("db.cruds.media_items_crud module not found. Media item functionality will be limited.")

# Recruitment CRUDs
from . import recruitment_job_openings_crud
from . import recruitment_candidates_crud
from . import recruitment_interviews_crud
from . import recruitment_steps_crud
from . import recruitment_candidate_progress_crud

# generic_crud.py is typically not imported directly into __all__ or here
# unless it provides functions intended for direct use from db.cruds.generic_crud
# For now, assuming it's primarily for internal use by other CRUD modules.

# Ensure all .py files in db/cruds that define CRUD operations are imported here
# so they can be accessed like db.cruds.module_name.function_name
