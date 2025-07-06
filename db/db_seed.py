import os
import sys
import sqlite3

# Adjust sys.path to allow finding 'config' module from project root
# This needs to be at the very top before any project-level imports like 'config'
PROJECT_ROOT_FOR_SEED = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT_FOR_SEED not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_FOR_SEED)

import uuid
import hashlib
from datetime import datetime
import json
import logging
import importlib

# Assuming config.py is in the parent directory (root)
from config import DATABASE_PATH, DEFAULT_ADMIN_USERNAME
from app_setup import CONFIG


# Import necessary functions directly from their new CRUD module locations
from db.connection import get_db_connection # Corrected import
from db.cruds.generic_crud import GenericCRUD

# Import CRUD instances for refactored modules
# from db.cruds.users_crud import users_crud_instance # Replaced with direct module import
from db.cruds import users_crud # Import the module itself
from db.cruds.clients_crud import clients_crud_instance
from db.cruds.products_crud import products_crud_instance

# Imports for non-refactored or utility functions used in seeding
from db.cruds.template_categories_crud import add_template_category, get_template_category_by_name
from db.cruds.cover_page_templates_crud import get_cover_page_template_by_name, add_cover_page_template
# get_user_by_username will be called via users_crud_instance if needed for seeding logic outside Users table itself
from db.cruds.locations_crud import get_or_add_country, get_or_add_city, get_country_by_name, get_city_by_name_and_country_id
from db.cruds.status_settings_crud import get_status_setting_by_name
from db.cruds import partners_crud
# Assuming company and company personnel functions will be imported if they were used via db_main_manager
# For now, let's assume they are not, or will be handled if errors arise.
from db.cruds import regions_crud, referents_crud # Added for Referents seeding

LOGO_SUBDIR_CONTEXT = "company_logos" # This should match the setup

# Redundant local helper functions and data are removed.
# _get_or_create_category_id, set_setting, add_default_template_if_not_exists,
# DEFAULT_COVER_PAGE_TEMPLATES, and _populate_default_cover_page_templates
# are now expected to be handled by init_schema.py or imported CRUD modules.

# Ensure add_default_template_if_not_exists is imported if used by seed_initial_data directly
# (It is used, so ensure it's available from db.cruds.templates_crud)
from db.cruds.templates_crud import add_template, get_filtered_templates, add_default_template_if_not_exists
# Ensure set_setting is imported if used by seed_initial_data directly
# (It is used, so ensure it's available from db.cruds.application_settings_crud)
from db.cruds.application_settings_crud import get_setting, set_setting
from db.connection import engine as main_sqlalchemy_engine # Import the main engine


def _seed_default_partner_categories(cursor: sqlite3.Cursor, conn: sqlite3.Connection, logger_passed: logging.Logger):
    """Seeds default partner categories into the database."""
    logger = logger_passed
    logger.info("Attempting to seed default partner categories...")
    default_categories = [
        {'category_name': 'Supplier', 'description': 'Providers of goods and materials.'},
        {'category_name': 'Service Provider', 'description': 'Companies offering services.'},
        {'category_name': 'Technology Partner', 'description': 'Partners providing technology solutions.'},
        {'category_name': 'Consultant', 'description': 'External consultants and advisors.'},
        {'category_name': 'Distributor', 'description': 'Entities distributing products.'}
    ]

    for category_def in default_categories:
        existing_category_row = partners_crud.get_partner_category_by_name(category_def['category_name'], conn=conn)

        if existing_category_row: 
            logger.info(f"Partner Category '{category_def['category_name']}' already exists with ID: {existing_category_row['partner_category_id']}. Skipping.")
        else:
            category_id = partners_crud.add_partner_category(category_def, conn=conn)
            if category_id:
                logger.info(f"Partner Category '{category_def['category_name']}' added with ID: {category_id}")
            else:
                logger.warning(f"Could not add partner category '{category_def['category_name']}'. Check logs from partners_crud.")
    logger.info("Default partner categories seeding attempt finished.")

def _original_seed_initial_data_func_placeholder(cursor: sqlite3.Cursor, conn: sqlite3.Connection, logger_passed: logging.Logger):
    logger = logger_passed

    # Import here to avoid circular dependencies if roles_crud uses get_db_connection
    # Alias imports to avoid conflict with the 'logger' variable in this function's scope.
    from db.cruds.roles_crud import add_role as crud_add_role, get_role_by_name as crud_get_role_by_name
    # users_crud functions now accept logger_passed
    from db.cruds import users_crud # Keep direct import for users_crud
    from auth.permissions import ADMINISTRATOR, TEAM_LEAD, OPERATOR # Role names

    try:
        # Seed Roles
        logger.info("Seeding default roles...")
        roles_to_seed = {
            ADMINISTRATOR: "Full application access and user management.",
            TEAM_LEAD: "Manages projects and teams, advanced client/product operations.",
            OPERATOR: "Standard user for daily operations, data entry, document generation."
        }
        role_ids = {}
        for role_name, desc in roles_to_seed.items():
            existing_role = crud_get_role_by_name(role_name, conn=conn)
            if existing_role:
                role_ids[role_name] = existing_role['role_id']
                logger.info(f"Role '{role_name}' already exists with ID {role_ids[role_name]}.")
            else:
                new_role_id = crud_add_role(role_name, desc, conn=conn)
                if new_role_id:
                    role_ids[role_name] = new_role_id
                    logger.info(f"Role '{role_name}' added with ID {new_role_id}.")
                else:
                    logger.error(f"Failed to add role '{role_name}'.")

        # Ensure Administrator role ID was obtained
        admin_role_id = role_ids.get(ADMINISTRATOR)
        if not admin_role_id:
            logger.critical(f"Administrator role ('{ADMINISTRATOR}') could not be seeded or found. Cannot create default admin user.")
            # Depending on policy, might raise an error or try to proceed if other roles are vital.
            # For now, log critical and proceed, other parts of seeding might still be useful.

        # 1. Users - Seed initial Admin User
        admin_user_id = None # Initialize
        if admin_role_id: # Only proceed if Admin role exists
            logger.info(f"Checking for default admin user '{DEFAULT_ADMIN_USERNAME}'...")
            admin_user_dict = users_crud.get_user_by_username(DEFAULT_ADMIN_USERNAME, conn=conn, logger_passed=logger)
            temp_admin_password = "admin" # Known default password

            if admin_user_dict:
                admin_user_id = admin_user_dict['user_id']
                logger.info(f"Default admin user '{DEFAULT_ADMIN_USERNAME}' (ID: {admin_user_id}) exists. Forcing password update to default to ensure bcrypt hash.")
                update_success = users_crud.update_user_password(admin_user_id, temp_admin_password, conn=conn, logger_passed=logger)
                if update_success:
                    logger.info(f"Password for default admin user '{DEFAULT_ADMIN_USERNAME}' (ID: {admin_user_id}) reset/updated successfully.")
                    # Re-fetch to log the hash that's now in DB
                    updated_admin_info = users_crud.get_user_by_username(DEFAULT_ADMIN_USERNAME, conn=conn, logger_passed=logger)
                    if updated_admin_info:
                        logger.info(f"Hash for '{DEFAULT_ADMIN_USERNAME}' in DB after update: {updated_admin_info.get('hashed_password')}")
                    else:
                        logger.error(f"Could not re-fetch admin user '{DEFAULT_ADMIN_USERNAME}' after password update.")
                else:
                    logger.error(f"Failed to update password for default admin user '{DEFAULT_ADMIN_USERNAME}' (ID: {admin_user_id}). This is critical for login.")
            else:
                logger.info(f"Default admin user '{DEFAULT_ADMIN_USERNAME}' not found. Creating with password '{temp_admin_password}'...")

                new_admin_id = users_crud.add_user(
                    username=DEFAULT_ADMIN_USERNAME,
                    password=temp_admin_password, # crud_add_user logs the hash used
                    role_id=admin_role_id,
                    full_name="Default Administrator",
                    email="admin@example.local",
                    conn=conn,
                    logger_passed=logger
                )
                if new_admin_id:
                    admin_user_id = new_admin_id
                    logger.info(f"Default admin user '{DEFAULT_ADMIN_USERNAME}' created with ID {admin_user_id}. PLEASE CHANGE THE DEFAULT PASSWORD IMMEDIATELY.")
                    # Re-fetch to log the hash that's now in DB
                    created_admin_info = users_crud.get_user_by_username(DEFAULT_ADMIN_USERNAME, conn=conn, logger_passed=logger)
                    if created_admin_info:
                        logger.info(f"Hash for new admin '{DEFAULT_ADMIN_USERNAME}' in DB: {created_admin_info.get('hashed_password')}")
                    else:
                        logger.error(f"Could not re-fetch admin user '{DEFAULT_ADMIN_USERNAME}' after creation.")
                else:
                    logger.error(f"Failed to create default admin user '{DEFAULT_ADMIN_USERNAME}'.")
        else: # admin_role_id was not found/created
            logger.warning(f"Cannot seed default admin user because Administrator role ID is missing.")


        # 2. Companies (uses admin_user_id if available for created_by or similar in future)
        default_company_id = None
        cursor.execute("SELECT COUNT(*) FROM Companies")
        if cursor.fetchone()[0] == 0:
            default_company_id = str(uuid.uuid4())
            cursor.execute("INSERT OR IGNORE INTO Companies (company_id, company_name, address, is_default) VALUES (?, ?, ?, ?)",
                           (default_company_id, "Default Company Inc.", "123 Default Street", True))
            logger.info("Seeded default company.")
        else:
            cursor.execute("SELECT company_id FROM Companies WHERE is_default = TRUE")
            row = cursor.fetchone()
            if row: default_company_id = row[0]

        # 3. CompanyPersonnel
        if default_company_id:
            cursor.execute("SELECT COUNT(*) FROM CompanyPersonnel WHERE company_id = ?", (default_company_id,))
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT OR IGNORE INTO CompanyPersonnel (company_id, name, role, email, phone) VALUES (?, ?, ?, ?, ?)",
                               (default_company_id, "Admin Contact", "Administrator", "contact@defaultcomp.com", "123-456-7890"))
                logger.info("Seeded default company personnel.")

        # 4. TeamMembers
        if admin_user_id:
            admin_user_for_tm_dict = users_crud.get_user_by_id(admin_user_id, conn=conn, logger_passed=logger)
            if admin_user_for_tm_dict:
                cursor.execute("SELECT COUNT(*) FROM TeamMembers WHERE user_id = ?", (admin_user_id,))
                if cursor.fetchone()[0] == 0:
                    # Use 'role_name' as fetched from get_user_by_id, and map to 'role_or_title' column in TeamMembers
                    cursor.execute("INSERT OR IGNORE INTO TeamMembers (user_id, full_name, email, role_or_title) VALUES (?, ?, ?, ?)",
                                   (admin_user_id, admin_user_for_tm_dict['full_name'], admin_user_for_tm_dict['email'], admin_user_for_tm_dict.get('role_name')))
                    logger.info("Seeded admin team member.")
            else:
                logger.warning(f"Could not retrieve admin user details for ID {admin_user_id} to seed into TeamMembers.")
        else:
            logger.warning("Admin user ID not available for TeamMember seeding.")

        # Default Operational User
        DEFAULT_OPERATIONAL_USERNAME = "default_operational_user"
        DEFAULT_OPERATIONAL_USER_ROLE = "User" # This should be a role_id or fetched dynamically
        logger.info(f"Checking for default operational user '{DEFAULT_OPERATIONAL_USERNAME}'...")
        existing_operational_user = users_crud.get_user_by_username(DEFAULT_OPERATIONAL_USERNAME, conn=conn, logger_passed=logger)
        if existing_operational_user is None:
            logger.info(f"Creating default operational user '{DEFAULT_OPERATIONAL_USERNAME}'...")
            # Fetch OPERATOR role_id
            operator_role_id = role_ids.get(OPERATOR) # Get OPERATOR role_id from seeded roles
            if operator_role_id:
                op_user_data = {
                    'username': DEFAULT_OPERATIONAL_USERNAME,
                    'password': uuid.uuid4().hex, # Generate a random password
                    'role_id': operator_role_id,
                    'full_name': "Default Operational User",
                    'email': f"{DEFAULT_OPERATIONAL_USERNAME}@example.local",
                    'is_active': True # This is not directly passed to users_crud.add_user; it's defaulted there
                }
                # users_crud.add_user expects: username, password, role_id, full_name=None, email=None, conn=None
                # It returns user_id (str) or None
                op_user_id = users_crud.add_user(
                    username=op_user_data['username'],
                    password=op_user_data['password'],
                    role_id=op_user_data['role_id'],
                    full_name=op_user_data['full_name'],
                    email=op_user_data['email'],
                    conn=conn,
                    logger_passed=logger
                )
                if op_user_id:
                    logger.info(f"Created default operational user ID: {op_user_id}.")
                else:
                    logger.error(f"Failed to create default operational user: {DEFAULT_OPERATIONAL_USERNAME}")
            else:
                logger.error(f"Could not find role_id for '{OPERATOR}'. Cannot create default operational user.")
        else:
            logger.info(f"Default operational user '{DEFAULT_OPERATIONAL_USERNAME}' already exists.")

        # 5. Countries & 6. Cities
        logger.info("Seeding default countries and cities...")
        countries_cities = {'France': 'Paris', 'USA': 'New York', 'Algeria': 'Algiers'}
        for country_name, city_name in countries_cities.items():
            country_dict = get_or_add_country(country_name, conn=conn)
            if country_dict and 'country_id' in country_dict:
                get_or_add_city(city_name, country_dict['country_id'], conn=conn)
            elif country_dict:
                logger.error(f"Country '{country_name}' processed by get_or_add_country but 'country_id' key is missing in returned dict: {country_dict}")
            else:
                 logger.error(f"Failed to get or add country '{country_name}', cannot add city '{city_name}'.")
        logger.info(f"Seeded {len(countries_cities)} countries/cities.")
        
        # 7. Clients & 8. Projects (Simplified)
        logger.info("Seeding sample client and project...")
        cursor.execute("SELECT COUNT(*) FROM Clients")
        if cursor.fetchone()[0] == 0:
            # Fetch IDs specifically for client seeding
            france_country_dict = get_country_by_name("France", conn=conn)
            actual_france_country_id = france_country_dict['country_id'] if france_country_dict else None

            paris_city_dict = None
            if actual_france_country_id:
                paris_city_dict = get_city_by_name_and_country_id("Paris", actual_france_country_id, conn=conn)
            actual_paris_city_id = paris_city_dict['city_id'] if paris_city_dict else None

            actif_status_dict = get_status_setting_by_name("Actif", "Client", conn=conn)
            actual_actif_status_id = actif_status_dict['status_id'] if actif_status_dict else None

            if admin_user_id and actual_france_country_id and actual_paris_city_id and actual_actif_status_id:
                client_data = {
                    'client_name': "Sample Client SARL",
                    'country_id': actual_france_country_id,
                    'city_id': actual_paris_city_id,
                    'status_id': actual_actif_status_id,
                    'created_by_user_id': admin_user_id,
                    'default_base_folder_path': f"clients/{uuid.uuid4()}",
                    'project_identifier': "SC-PROJ-001"
                }
                add_client_res = clients_crud_instance.add_client(client_data, conn=conn)
                if add_client_res['success']:
                    logger.info(f"Seeded sample client ID: {add_client_res['client_id']}")
                    planning_status_dict = get_status_setting_by_name("Planning", "Project", conn=conn)
                    planning_status_id = planning_status_dict['status_id'] if planning_status_dict else None
                    if planning_status_id:
                        project_data = {'project_id': str(uuid.uuid4()), 'client_id': add_client_res['client_id'], 'project_name': "Initial Project", 'status_id': planning_status_id, 'manager_team_member_id': admin_user_id}
                        cursor.execute("INSERT INTO Projects (project_id, client_id, project_name, status_id, manager_team_member_id) VALUES (?,?,?,?,?)",
                                       (project_data['project_id'], project_data['client_id'], project_data['project_name'], project_data['status_id'], project_data['manager_team_member_id']))
                        logger.info("Seeded sample project.")
                else:
                    logger.error(f"Failed to seed sample client. Add client response: {add_client_res}")
            else:
                logger.warning(f"One or more required IDs for sample client not found or invalid. Admin: {admin_user_id}, France: {actual_france_country_id}, Paris: {actual_paris_city_id}, ActifStatus: {actual_actif_status_id}. Skipping sample client seeding.")
        else:
            logger.info("Clients table not empty, skipping sample client/project seeding.")

        # 9. Contacts
        logger.info("Seeding generic contact...")
        cursor.execute("SELECT COUNT(*) FROM Contacts WHERE email = 'contact@example.com'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT OR IGNORE INTO Contacts (name, email) VALUES (?,?)", ("Placeholder Contact", "contact@example.com"))
            logger.info("Seeded generic contact.")

        # 10. Products
        logger.info("Seeding default and sample products...")
        sample_prods_data = [
            {'product_name': "Default Product", 'language_code': "en", 'base_unit_price': 10.0, 'product_code': "PROD001"},
            {'product_name': "Industrial Widget", 'language_code': "en", 'base_unit_price': 100.0, 'product_code': "PROD002"},
            {'product_name': "Gadget Standard", 'language_code': "fr", 'base_unit_price': 50.0, 'product_code': "PROD003"},
            {'product_name': "Advanced Gizmo", 'language_code': "en", 'base_unit_price': 250.0, 'product_code': "PROD004"}
        ]
        for prod_data in sample_prods_data:
            cursor.execute("SELECT COUNT(*) FROM Products WHERE product_name = ? AND language_code = ?", (prod_data["product_name"], prod_data["language_code"]))
            if cursor.fetchone()[0] == 0:
                products_crud_instance.add_product(prod_data, conn=conn)
        logger.info("Finished seeding products.")

        # Seed default hydraulic presses
        # _seed_default_hydraulic_presses(cursor, conn, logger_passed=logger) # Function definition not found
        try:
            # Changed to absolute import based on PROJECT_ROOT being in sys.path
            from db.hidroguc_product_seeder import seed_hidroguc_products
            logger.info("Attempting to seed HİDROGÜÇ PRES products...")
            seed_hidroguc_products(conn, cursor, logger_passed=logger)
            logger.info("HİDROGÜÇ PRES products seeding attempt finished.")
        except ImportError as e_import_hp:
            logger.error(f"Could not import seed_hidroguc_products. Error: {e_import_hp}. Skipping HİDROGÜÇ PRES products seeding.", exc_info=True)
        except Exception as e_hp_seed:
            logger.error(f"An error occurred during HİDROGÜÇ PRES products seeding: {e_hp_seed}", exc_info=True)
            # Ne pas laisser une erreur ici arrêter le reste du seeding, sauf si critique.
            # conn.rollback() # Peut-être pas souhaitable de rollback tout le seeding pour ça.

        # 11. SmtpConfigs
        logger.info("Seeding placeholder SMTP config...")
        cursor.execute("SELECT COUNT(*) FROM SmtpConfigs")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT OR IGNORE INTO SmtpConfigs (config_name, smtp_server, smtp_port, username, password_encrypted, use_tls, is_default, sender_email_address, sender_display_name) VALUES (?,?,?,?,?,?,?,?,?)",
                           ("Placeholder - Configure Me", "smtp.example.com", 587, "user", "placeholder_password", True, True, "noreply@example.com", "Placeholder Email"))
            logger.info("Seeded placeholder SMTP config.")

        # 12. ApplicationSettings
        logger.info("Seeding additional application settings...")
        set_setting('google_maps_review_url', 'https://maps.google.com/?cid=YOUR_CID_HERE', conn=conn) 
        logger.info("Seeded additional application settings.")

        # 13. Email Templates
        logger.info("Seeding email templates...")
        email_templates_defs = [
            {'template_name': 'SAV Ticket Ouvert (FR)', 'template_type': 'email_sav_ticket_opened', 'language_code': 'fr', 'base_file_name': 'sav_ticket_opened_fr.html', 'category_name': 'Modèles Email SAV', 'category_purpose': 'email', 'email_subject_template': 'Ticket SAV #{{ticket.id}} Ouvert - {{project.name | default: "Référence Client"}}', 'is_default_for_type_lang': True},
            {'template_name': 'SAV Ticket Résolu (FR)', 'template_type': 'email_sav_ticket_resolved', 'language_code': 'fr', 'base_file_name': 'sav_ticket_resolved_fr.html', 'category_name': 'Modèles Email SAV', 'category_purpose': 'email', 'email_subject_template': 'Ticket SAV #{{ticket.id}} Résolu - {{project.name | default: "Référence Client"}}', 'is_default_for_type_lang': True},
            {'template_name': 'Suivi Prospect Proforma (FR)', 'template_type': 'email_follow_up_prospect', 'language_code': 'fr', 'base_file_name': 'follow_up_prospect_fr.html', 'category_name': 'Modèles Email Marketing/Suivi', 'category_purpose': 'email', 'email_subject_template': 'Suite à votre demande de proforma : {{project.name | default: client.primary_need}}', 'is_default_for_type_lang': True},
            {'template_name': 'Vœux Noël (FR)', 'template_type': 'email_greeting_christmas', 'language_code': 'fr', 'base_file_name': 'greeting_holiday_christmas_fr.html', 'category_name': 'Modèles Email Vœux', 'category_purpose': 'email', 'email_subject_template': 'Joyeux Noël de la part de {{seller.company_name}}!', 'is_default_for_type_lang': True},
            {'template_name': 'Vœux Nouvelle Année (FR)', 'template_type': 'email_greeting_newyear', 'language_code': 'fr', 'base_file_name': 'greeting_holiday_newyear_fr.html', 'category_name': 'Modèles Email Vœux', 'category_purpose': 'email', 'email_subject_template': 'Bonne Année {{doc.current_year}} ! - {{seller.company_name}}', 'is_default_for_type_lang': True},
            {'template_name': 'Message Générique (FR)', 'template_type': 'email_generic_message', 'language_code': 'fr', 'base_file_name': 'generic_message_fr.html', 'category_name': 'Modèles Email Généraux', 'category_purpose': 'email', 'email_subject_template': 'Un message de {{seller.company_name}}', 'is_default_for_type_lang': True},
        ]
        for et_data in email_templates_defs:
            add_default_template_if_not_exists(et_data, conn=conn) 
        logger.info("Seeded email templates.")

        # 14. CoverPageTemplates (handled by init_schema.py)
        logger.info("Cover page templates are expected to be populated by initialize_database from init_schema.py.")

        # 15. Partner Categories
        _seed_default_partner_categories(cursor, conn, logger_passed=logger) 
        logger.info("Data seeding operations completed within _original_seed_initial_data_func_placeholder.")

    except sqlite3.Error as e:
        logger.error(f"An SQLite error occurred during data seeding (original part): {e}", exc_info=True)
        raise 
    except Exception as e_gen:
        logger.error(f"A general error occurred during data seeding (original part): {e_gen}", exc_info=True)
        raise

DEFAULT_UTILITY_TEMPLATES_CATEGORY_NAME = "Document Utilitaires"
DEFAULT_UTILITY_TEMPLATES_CATEGORY_DESC = "Modèles de documents utilitaires généraux"
DEFAULT_UTILITY_TEMPLATES_PURPOSE = 'utility'

DEFAULT_UTILITY_DOCUMENTS = [
    {'template_name': 'Contact Page EN', 'base_file_name': 'contact_page_template.html', 'language_code': 'en', 'description': 'Standard contact page template in English.'},
    {'template_name': 'Contact Page FR', 'base_file_name': 'contact_page_template.html', 'language_code': 'fr', 'description': 'Modèle de page de contact standard en français.'},
    {'template_name': 'Cover Page EN', 'base_file_name': 'cover_page_template.html', 'language_code': 'en', 'description': 'Standard cover page template in English.'},
    {'template_name': 'Cover Page FR', 'base_file_name': 'cover_page_template.html', 'language_code': 'fr', 'description': 'Modèle de page de garde standard en français.'},
    {'template_name': 'Technical Specifications EN', 'base_file_name': 'technical_specifications_template.html', 'language_code': 'en', 'description': 'Template for technical specifications in English.'},
    {'template_name': 'Technical Specifications FR', 'base_file_name': 'technical_specifications_template.html', 'language_code': 'fr', 'description': 'Modèle de spécifications techniques en français.'},
    {'template_name': 'Warranty Document EN', 'base_file_name': 'warranty_document_template.html', 'language_code': 'en', 'description': 'Standard warranty document in English.'},
    {
        'template_name': 'Affichage Images Produit FR',
        'base_file_name': 'product_images_template.html',
        'language_code': 'fr',
        'description': 'Affiche les images des produits, leur nom et leur code.'
    }
]

def _seed_default_utility_templates(cursor: sqlite3.Cursor, conn: sqlite3.Connection, logger_passed: logging.Logger):
    logger = logger_passed
    logger.info("Attempting to seed default utility document templates...")

    category_obj = get_template_category_by_name(DEFAULT_UTILITY_TEMPLATES_CATEGORY_NAME, conn=conn)
    utility_category_id = None
    if not category_obj:
        logger.info(f"Utility category '{DEFAULT_UTILITY_TEMPLATES_CATEGORY_NAME}' not found, creating it.")
        utility_category_id = add_template_category(
            category_name=DEFAULT_UTILITY_TEMPLATES_CATEGORY_NAME,
            description=DEFAULT_UTILITY_TEMPLATES_CATEGORY_DESC,
            purpose=DEFAULT_UTILITY_TEMPLATES_PURPOSE,
            conn=conn
        )
        if not utility_category_id:
            logger.error(f"Failed to create utility category '{DEFAULT_UTILITY_TEMPLATES_CATEGORY_NAME}'. Aborting utility template seeding.")
            return
        logger.info(f"Utility category '{DEFAULT_UTILITY_TEMPLATES_CATEGORY_NAME}' created with ID: {utility_category_id}.")
    else:
        utility_category_id = category_obj['category_id']
        logger.info(f"Found utility category '{DEFAULT_UTILITY_TEMPLATES_CATEGORY_NAME}' with ID: {utility_category_id}.")

    for doc_def in DEFAULT_UTILITY_DOCUMENTS:
        ext = os.path.splitext(doc_def['base_file_name'])[1].lower()
        template_type_map = {'.pdf': 'document_pdf', '.html': 'document_html', '.docx': 'document_word', '.xlsx': 'document_excel'}
        template_type = template_type_map.get(ext, 'document_other')

        template_data_for_db = {
            'template_name': doc_def['template_name'], 'template_type': template_type,
            'language_code': doc_def['language_code'], 'base_file_name': doc_def['base_file_name'],
            'description': doc_def['description'], 'category_id': utility_category_id,
            'client_id': None, 'is_default_for_type_lang': False,
        }
        template_id = add_default_template_if_not_exists(template_data_for_db, conn=conn) 
        if template_id:
            logger.info(f"Ensured utility template '{doc_def['template_name']}' exists with ID: {template_id}")
            visibility_key = f"template_visibility_{template_id}_enabled"
            if get_setting(visibility_key, conn=conn) is None:
                set_setting(visibility_key, 'True', conn=conn) 
                logger.info(f"Visibility for utility template ID {template_id} set to True.")
        else:
            logger.error(f"Failed to ensure utility template '{doc_def['template_name']}'.")
    logger.info("Default utility document templates seeding attempt finished.")

def _seed_main_document_templates(cursor: sqlite3.Cursor, conn: sqlite3.Connection, logger_passed: logging.Logger):
    logger = logger_passed
    logger.info("Attempting to seed main document templates (Excel, specific HTML)...")

    client_doc_category_name = "Documents Client"
    client_doc_category_desc = "Templates de documents principaux pour les clients (contrats, proformas, etc.)"
    client_doc_purpose = 'client_document'

    category_obj = get_template_category_by_name(client_doc_category_name, conn=conn)
    category_id = None
    if not category_obj:
        logger.info(f"Category '{client_doc_category_name}' not found, creating it with purpose '{client_doc_purpose}'.")
        category_id = add_template_category(
            category_name=client_doc_category_name, description=client_doc_category_desc,
            purpose=client_doc_purpose, conn=conn
        )
        if not category_id:
            logger.error(f"Failed to create category '{client_doc_category_name}'. Aborting.")
            return
        logger.info(f"Category '{client_doc_category_name}' created with ID: {category_id}.")
    else:
        category_id = category_obj['category_id']
        logger.info(f"Found category '{client_doc_category_name}' with ID: {category_id}.")

    main_document_templates_definitions = [
        {'template_name': 'Spécification Technique (Excel)', 'base_file_name': 'specification_technique_template.xlsx', 'template_type': 'EXCEL_TECHNICAL_SPECIFICATIONS', 'description': 'Modèle Excel pour les spécifications techniques.'},
        {'template_name': 'Facture Proforma (Excel)', 'base_file_name': 'proforma_template.xlsx', 'template_type': 'EXCEL_PROFORMA_INVOICE', 'description': 'Modèle Excel pour les factures proforma.'},
        {'template_name': 'Contrat de Vente (Excel)', 'base_file_name': 'contrat_vente_template.xlsx', 'template_type': 'EXCEL_SALES_CONTRACT', 'description': 'Modèle Excel pour les contrats de vente.'},
        {'template_name': 'Liste de Colisage (Excel)', 'base_file_name': 'packing_liste_template.xlsx', 'template_type': 'EXCEL_PACKING_LIST', 'description': 'Modèle Excel pour les listes de colisage.'},
        {'template_name': 'Facture Proforma (HTML)', 'base_file_name': 'proforma_invoice_template.html', 'template_type': 'HTML_PROFORMA', 'description': 'Modèle HTML pour les factures proforma.'}, # Corrected template_type
        {'template_name': 'Liste de Colisage (HTML)', 'base_file_name': 'packing_list_template.html', 'template_type': 'PACKING_LIST_HTML', 'description': 'Modèle HTML pour les listes de colisage.'},
        {'template_name': 'Contrat de Vente (HTML)', 'base_file_name': 'sales_contract_template.html', 'template_type': 'SALES_CONTRACT_HTML', 'description': 'Modèle HTML pour les contrats de vente.'},
    ]
    all_supported_template_langs = ["fr", "en", "ar", "tr", "pt"]

    for lang_code in all_supported_template_langs:
        for doc_def in main_document_templates_definitions:
            full_template_name = f"{doc_def['template_name']} ({lang_code.upper()})"

            # Determine if this template should be default
            is_default = False
            if doc_def['template_type'] == 'HTML_PROFORMA' and lang_code == 'fr':
                is_default = True
            # Add other conditions for other default templates if needed
            # Example:
            # elif doc_def['template_type'] == 'SOME_OTHER_TYPE' and lang_code == 'en':
            #     is_default = True

            template_data_for_db = {
                'template_name': full_template_name, 'template_type': doc_def['template_type'],
                'language_code': lang_code, 'base_file_name': doc_def['base_file_name'],
                'description': doc_def['description'], 'category_id': category_id,
                'client_id': None, 'is_default_for_type_lang': is_default, # Set dynamically
            }
            template_id = add_default_template_if_not_exists(template_data_for_db, conn=conn) 
            
            if template_id:
                logger.info(f"Ensured main document template '{full_template_name}' exists with ID: {template_id}")
                visibility_key = f"template_visibility_{template_id}_enabled"
                current_visibility = get_setting(visibility_key, conn=conn)
                if current_visibility is None: 
                    set_setting(visibility_key, 'True', conn=conn) 
                    logger.info(f"Visibility setting '{visibility_key}' created and set to True for template ID {template_id}.")
            else:
                logger.error(f"Failed to ensure main document template '{full_template_name}'.")
    logger.info("Main document templates seeding attempt finished.")

def seed_initial_data_master(cursor: sqlite3.Cursor):
    """Master seeding function that calls all individual seeding parts."""
    logger = logging.getLogger(__name__)
    conn = cursor.connection
    
    _original_seed_initial_data_func_placeholder(cursor, conn, logger_passed=logger) 
    _seed_main_document_templates(cursor, conn, logger_passed=logger)
    _seed_default_utility_templates(cursor, conn, logger_passed=logger)
    _seed_motivational_messages(cursor, conn, logger_passed=logger)
    _seed_user_motivational_messages(cursor, conn, logger_passed=logger)
    _seed_default_document_footers(cursor, conn, logger_passed=logger)
    _seed_new_default_document_notes(cursor, conn, logger_passed=logger)
    _seed_default_regions(cursor, conn, logger_passed=logger) # Added Region seeding
    _seed_sample_referents(cursor, conn, logger_passed=logger) # Added Referent seeding


def _seed_default_regions(cursor: sqlite3.Cursor, conn: sqlite3.Connection, logger_passed: logging.Logger):
    logger = logger_passed
    logger.info("Attempting to seed default regions...")

    default_regions_data = {
        "France": ["Île-de-France", "Occitanie", "Nouvelle-Aquitaine", "Auvergne-Rhône-Alpes"],
        "USA": ["California", "New York", "Texas", "Florida"],
        "Algeria": ["Alger", "Oran", "Constantine"]
        # Add more countries and their regions as needed
    }

    added_count = 0
    skipped_count = 0

    for country_name, region_names in default_regions_data.items():
        country = get_country_by_name(country_name, conn=conn) # Changed from locations_crud.get_country_by_name
        if not country or 'country_id' not in country:
            logger.warning(f"Country '{country_name}' not found for seeding regions. Skipping its regions.")
            skipped_count += len(region_names)
            continue

        country_id = country['country_id']
        for region_name in region_names:
            existing_region = regions_crud.get_region_by_name_and_country_id(region_name, country_id, conn=conn)
            if existing_region:
                logger.debug(f"Region '{region_name}' in '{country_name}' already exists. Skipping.")
                skipped_count += 1
                continue

            region_id = regions_crud.add_region(region_name, country_id, conn=conn)
            if region_id:
                added_count += 1
                logger.info(f"Added region '{region_name}' to '{country_name}' with ID {region_id}.")
            else:
                # This might happen if add_region itself fails for reasons other than duplicate
                logger.warning(f"Failed to add region '{region_name}' to '{country_name}'.")
                skipped_count +=1

    logger.info(f"Default regions seeding complete. Added: {added_count}, Skipped/Existing: {skipped_count}")


def _seed_sample_referents(cursor: sqlite3.Cursor, conn: sqlite3.Connection, logger_passed: logging.Logger):
    logger = logger_passed
    logger.info("Attempting to seed sample referents...")

    from db.cruds import commandes_crud # For checking if client has orders

    # Get a default user ID (e.g., admin) for created_by_user_id
    admin_user = users_crud.get_user_by_username(DEFAULT_ADMIN_USERNAME, conn=conn)
    if not admin_user or 'user_id' not in admin_user:
        logger.error(f"Default admin user '{DEFAULT_ADMIN_USERNAME}' not found. Cannot seed referents.")
        return
    creator_user_id = admin_user['user_id']

    # Get some sample clients (e.g., the first few active ones)
    # We need clients that already have country_id and ideally city_id
    sample_clients = clients_crud_instance.get_all_clients_with_details(filters={'status_name': 'Client Actif'}, limit=5, conn=conn) # Get some active clients
    if not sample_clients:
        logger.warning("No sample active clients found to make into referents.")
        return

    added_count = 0
    skipped_count = 0

    for client_data in sample_clients:
        client_id = client_data.get('client_id')
        client_name = client_data.get('client_name')
        client_country_id = client_data.get('country_id')
        client_city_id = client_data.get('city_id')

        if not all([client_id, client_country_id]):
            logger.warning(f"Client '{client_name}' (ID: {client_id}) is missing country_id. Skipping referent seeding for this client.")
            skipped_count +=1
            continue

        # Check if client already a referent
        existing_referent = referents_crud.get_referent_by_client_id(client_id, conn=conn, include_inactive=True)
        if existing_referent:
            logger.debug(f"Client '{client_name}' (ID: {client_id}) is already a referent. Skipping.")
            skipped_count +=1
            continue

        # Check if client has orders (simplified check)
        client_orders = commandes_crud.get_commandes_for_client(client_id, limit=1, conn=conn)
        if not client_orders:
            logger.info(f"Client '{client_name}' (ID: {client_id}) has no orders. Skipping referent seeding as per policy (requires purchase).")
            skipped_count += 1
            continue

        # Get a sample region for the client's country
        client_regions = regions_crud.get_regions_for_country(client_country_id, conn=conn)
        sample_region_id = None
        if client_regions:
            sample_region_id = client_regions[0]['region_id'] # Take the first available region for simplicity

        referent_notes = f"Référent exemplaire pour la région de {client_data.get('country', 'N/A')}."

        new_referent_id = referents_crud.add_referent(
            client_id=client_id,
            country_id=client_country_id,
            region_id=sample_region_id, # Can be None if no regions for country
            city_id=client_city_id,     # Can be None
            notes=referent_notes,
            created_by_user_id=creator_user_id,
            conn=conn
        )

        if new_referent_id:
            added_count += 1
            logger.info(f"Client '{client_name}' (ID: {client_id}) made a referent with ID {new_referent_id}.")
        else:
            skipped_count +=1
            logger.warning(f"Failed to make client '{client_name}' (ID: {client_id}) a referent.")

    logger.info(f"Sample referents seeding complete. Added: {added_count}, Skipped/Existing/NoOrders: {skipped_count}")


def _seed_new_default_document_notes(cursor: sqlite3.Cursor, conn: sqlite3.Connection, logger_passed: logging.Logger):
    logger = logger_passed
    logger.info("Attempting to seed DefaultDocumentNotes...")

    # Import the CRUD function for adding notes
    # Placed here to avoid potential circular imports if notes_crud uses get_db_connection
    from db.cruds.notes_crud import add_default_document_note, get_default_document_note

    # Define document types based on template analysis (simplified names)
    # These should ideally match the 'document_type_generated' values or a defined enum/list
    document_types = [
        "contact_page", "sales_contract_excel", "cover_page", "packing_list_html",
        "packing_list_excel", "product_images", "proforma_invoice_html", "proforma_invoice_excel",
        "sales_contract_html", "technical_specs_excel", "technical_specs_html", "warranty_document"
    ]
    # It's better to have a canonical list of document_types used across the application.
    # For now, using derived names.

    supported_languages = ["en", "fr", "ar", "tr", "pt", "ru"] # From template folders

    default_notes_content = {
        "en": "Default note: Please review all details carefully.",
        "fr": "Note par défaut : Veuillez vérifier attentivement tous les détails.",
        "ar": "ملاحظة افتراضية: يرجى مراجعة جميع التفاصيل بعناية.",
        "tr": "Varsayılan not: Lütfen tüm ayrıntıları dikkatlice inceleyin.",
        "pt": "Nota padrão: Revise todos os detalhes com atenção.",
        "ru": "Примечание по умолчанию: Пожалуйста, внимательно проверьте все детали."
    }

    added_count = 0
    skipped_count = 0

    for doc_type in document_types:
        for lang_code in supported_languages:
            # Check if a note already exists for this combination
            existing_note = get_default_document_note(doc_type, lang_code, conn=conn)
            if existing_note:
                logger.debug(f"Default note for type '{doc_type}', lang '{lang_code}' already exists. Skipping.")
                skipped_count += 1
                continue

            note_content_for_lang = default_notes_content.get(lang_code, f"Default note for {doc_type} ({lang_code}).")

            new_note_id = add_default_document_note(doc_type, lang_code, note_content_for_lang, conn=conn)
            if new_note_id:
                added_count += 1
                logger.info(f"Added default note ID {new_note_id} for type '{doc_type}', lang '{lang_code}'.")
            else:
                # This might happen due to an unexpected error or if add_default_document_note returns None on IntegrityError
                # (though we check for existing_note before calling add)
                logger.warning(f"Failed to add default note for type '{doc_type}', lang '{lang_code}'.")
                skipped_count +=1


    logger.info(f"DefaultDocumentNotes seeding complete. Added: {added_count}, Skipped/Existing: {skipped_count}")


def _seed_default_document_footers(cursor: sqlite3.Cursor, conn: sqlite3.Connection, logger_passed: logging.Logger):
    logger = logger_passed
    logger.info("Attempting to seed default document footer notes...")

    default_footers = {
        "default_document_footer_notes_fr": "Merci de votre confiance. N'hésitez pas à nous contacter pour toute question.",
        "default_document_footer_notes_en": "Thank you for your business. Please contact us if you have any questions.",
        "default_document_footer_notes_ar": "شكراً لثقتكم بنا. لا تترددوا في الاتصال بنا لأية استفسارات."
        # Add other languages as needed
    }

    added_count = 0
    skipped_count = 0

    for key, value in default_footers.items():
        try:
            # Check if setting already exists (optional, set_setting is INSERT OR REPLACE)
            existing_value = get_setting(key, conn=conn)
            if existing_value is not None and existing_value == value:
                logger.debug(f"Default footer note for '{key}' already exists and matches. Skipping.")
                skipped_count += 1
                continue
            elif existing_value is not None:
                logger.info(f"Default footer note for '{key}' exists but differs. Updating.")

            set_setting(key, value, conn=conn)
            added_count += 1
            logger.debug(f"Seeded/Updated default footer note for: {key}")
        except Exception as e:
            logger.error(f"Error seeding default footer note for '{key}': {e}", exc_info=True)
            skipped_count +=1

    logger.info(f"Default document footer notes seeding complete. Added/Updated: {added_count}, Skipped/Existing: {skipped_count}")


def _seed_user_motivational_messages(cursor: sqlite3.Cursor, conn: sqlite3.Connection, logger_passed: logging.Logger):
    logger = logger_passed
    logger.info("Attempting to seed example user motivational messages...")

    user_messages_crud = GenericCRUD(table_name='user_motivational_messages', primary_key='id')

    example_user_messages = [
        {"message": "Keep pushing your limits!", "language_code": "en"},
        {"message": "Aujourd'hui est un cadeau.", "language_code": "fr"},
        {"message": "Make today amazing.", "language_code": None}, # Example of a language-neutral user message
    ]

    added_count = 0
    skipped_count = 0

    for msg_data in example_user_messages:
        try:
            # Check for existing message to avoid IntegrityError on UNIQUE constraint
            query = "SELECT id FROM user_motivational_messages WHERE message = ?"
            cursor.execute(query, (msg_data["message"],))
            existing = cursor.fetchone()

            if existing:
                logger.debug(f"User motivational message '{msg_data['message'][:30]}...' already exists. Skipping.")
                skipped_count += 1
                continue

            data_to_insert = {
                "message": msg_data["message"],
                "language_code": msg_data.get("language_code"), # Handles if language_code is not present
                "is_active": True
            }
            user_messages_crud.create(data_to_insert, conn=conn)
            added_count += 1
            logger.debug(f"Added user motivational message: {msg_data['message'][:30]}...")
        except sqlite3.IntegrityError as e:
            logger.warning(f"Skipping user motivational message due to integrity error: {msg_data['message'][:30]}.... Error: {e}")
            skipped_count += 1
        except Exception as e:
            logger.error(f"Error adding user motivational message '{msg_data['message'][:30]}...': {e}", exc_info=True)
            skipped_count += 1

    logger.info(f"User motivational messages seeding complete. Added: {added_count}, Skipped/Existing: {skipped_count}")



def _seed_motivational_messages(cursor: sqlite3.Cursor, conn: sqlite3.Connection, logger_passed: logging.Logger):
    logger = logger_passed
    logger.info("Attempting to seed motivational messages...")

    messages_crud = GenericCRUD(table_name='motivational_messages', primary_key='id')

    default_messages = [
        # French - Generic
        {"language_code": "fr", "message": "Chaque effort compte, continuez d'avancer !", "day_of_year": None},
        {"language_code": "fr", "message": "Votre potentiel est illimité, explorez-le.", "day_of_year": None},
        {"language_code": "fr", "message": "Les défis sont des opportunités déguisées.", "day_of_year": None},
        # French - Daily Specific (examples)
        {"language_code": "fr", "message": "Bonne année ! Que cette nouvelle année vous apporte succès et bonheur.", "day_of_year": 1}, # Jan 1st
        {"language_code": "fr", "message": "Joyeux Noël ! Paix et joie à vous et vos proches.", "day_of_year": 359}, # Dec 25th (approx for non-leap)
        {"language_code": "fr", "message": "C'est le printemps, un temps de renouveau et de croissance !", "day_of_year": 80}, # Approx March 21st

        # English - Generic
        {"language_code": "en", "message": "Every effort counts, keep moving forward!", "day_of_year": None},
        {"language_code": "en", "message": "Your potential is limitless, explore it.", "day_of_year": None},
        {"language_code": "en", "message": "Challenges are disguised opportunities.", "day_of_year": None},
        # English - Daily Specific (examples)
        {"language_code": "en", "message": "Happy New Year! May this year bring you success and happiness.", "day_of_year": 1},
        {"language_code": "en", "message": "Merry Christmas! Peace and joy to you and yours.", "day_of_year": 359},
        {"language_code": "en", "message": "It's springtime, a time for renewal and growth!", "day_of_year": 80},

        # Arabic - Generic
        {"language_code": "ar", "message": "كل مجهود مهم، استمر في التقدم!", "day_of_year": None},
        {"language_code": "ar", "message": "إمكانياتك لا حدود لها، استكشفها.", "day_of_year": None},
        # Arabic - Daily Specific (example)
        {"language_code": "ar", "message": "سنة جديدة سعيدة! أتمنى لك التوفيق والسعادة.", "day_of_year": 1},
    ]
    # Keep some of the original messages as generic fallbacks
    original_generic_messages = [
        {"language_code": "fr", "message": "Chaque jour est une nouvelle opportunité.", "day_of_year": None},
        {"language_code": "fr", "message": "Croyez en vous et tout deviendra possible.", "day_of_year": None},
        {"language_code": "en", "message": "Every day is a new opportunity.", "day_of_year": None},
        {"language_code": "en", "message": "Believe in yourself and anything is possible.", "day_of_year": None},
        {"language_code": "ar", "message": "كل يوم هو فرصة جديدة.", "day_of_year": None},
    ]
    default_messages.extend(original_generic_messages)


    added_count = 0
    skipped_count = 0

    for msg_data in default_messages:
        try:
            # Check if a similar message (ignoring day_of_year for general messages) already exists
            # The UNIQUE constraint on (language_code, message) should handle this,
            # but a more explicit check might be useful if we want to avoid trying to insert.
            # For now, rely on the UNIQUE constraint and catch the IntegrityError.

            # Create a dictionary for insertion, ensuring all necessary fields are present
            # even if some are defaulted by the DB (like is_active, created_at, updated_at)
            # For GenericCRUD, we only need to provide non-defaulted fields.
            # The schema has UNIQUE(language_code, message) and UNIQUE(language_code, day_of_year)
            # If day_of_year is None, the second constraint won't prevent multiple generic messages per language.

            # Let's ensure we don't insert duplicates for generic messages (day_of_year is None)
            existing = None
            # Check for existing message based on UNIQUE constraints
            if msg_data["day_of_year"] is None:
                # Generic message: check language_code and message content (as per existing schema's UNIQUE(language_code, message))
                # This also implicitly handles the case where multiple generic messages might exist for the same language
                # if the schema didn't have UNIQUE(language_code, message) but relied on day_of_year IS NULL.
                # Given UNIQUE(language_code, message), this check is somewhat redundant if we let IntegrityError handle it,
                # but explicit check can be clearer.
                query = "SELECT id FROM motivational_messages WHERE language_code = ? AND message = ? AND day_of_year IS NULL"
                cursor.execute(query, (msg_data["language_code"], msg_data["message"]))
                existing = cursor.fetchone()
            else:
                # Day-specific message: check language_code and day_of_year (as per UNIQUE(language_code, day_of_year))
                query = "SELECT id FROM motivational_messages WHERE language_code = ? AND day_of_year = ?"
                cursor.execute(query, (msg_data["language_code"], msg_data["day_of_year"]))
                existing = cursor.fetchone()

            if existing:
                logger.debug(f"Motivational message (lang: {msg_data['language_code']}, day: {msg_data['day_of_year']}, text: '{msg_data['message'][:30]}...') already exists. Skipping.")
                skipped_count += 1
                continue

            # Prepare data for insertion (GenericCRUD expects a dict)
            # We don't need to specify 'id', 'created_at', 'updated_at', 'is_active' as they have defaults or are auto.
            data_to_insert = {
                "language_code": msg_data["language_code"],
                "message": msg_data["message"],
                "day_of_year": msg_data["day_of_year"], # Can be None
                "is_active": True
            }
            messages_crud.create(data_to_insert, conn=conn)
            added_count += 1
            logger.debug(f"Added motivational message: {msg_data['message'][:30]}... for lang {msg_data['language_code']}")
        except sqlite3.IntegrityError as e: # Handles UNIQUE constraint violations
            logger.warning(f"Skipping motivational message due to integrity error (likely duplicate): {msg_data['message'][:30]}... for lang {msg_data['language_code']}. Error: {e}")
            skipped_count += 1
        except Exception as e:
            logger.error(f"Error adding motivational message '{msg_data['message'][:30]}...': {e}", exc_info=True)
            skipped_count +=1 # Count as skipped if error

    logger.info(f"Motivational messages seeding complete. Added: {added_count}, Skipped/Existing: {skipped_count}")


def run_seed():
    logger = logging.getLogger(__name__)
    logger.info(f"Attempting to seed database: {DATABASE_PATH}")
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        seed_initial_data_master(cursor) 
        conn.commit()
        logger.info("Seeding process completed and committed.")
    except Exception as e:
        if conn: conn.rollback()
        logger.error(f"Error during seeding process: {e}", exc_info=True)
    finally:
        if conn: conn.close()
        logger.info("Database connection closed after seeding attempt.")

if __name__ == '__main__':
    # Adjust sys.path to allow finding 'config' module from project root
    import sys
    import os
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # This gets the project root from db/
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    main_logger = logging.getLogger(__name__)

    # Now that sys.path is adjusted, config should be importable.
    # Load APP_CONFIG and then set it for db.connection
    # We need to load config here and pass it.
    try:
        from config import load_config # Assuming config.py has a load_config() or similar
        APP_CONFIG = load_config() # Or however your config is loaded
        # If config is just a dict defined in config.py, then:
        # import config as app_config_module
        # APP_CONFIG = {key: getattr(app_config_module, key) for key in dir(app_config_module) if not key.startswith('_')}
        # For simplicity, let's assume APP_CONFIG can be derived or config.py makes it available directly
        # Fallback: if load_config() doesn't exist, try importing the dict.
    except ImportError: # No load_config, try direct import of a dict or module attributes
        try:
            import config as app_config_module
            # Construct a dictionary from the config module's attributes
            # This is a common pattern if config.py defines variables directly.
            APP_CONFIG = {
                "database_path": app_config_module.DATABASE_PATH,
                "default_admin_username": app_config_module.DEFAULT_ADMIN_USERNAME,
                # Add any other necessary config variables that init_schema might use
                # or that are part of the CONFIG dict used in the app.
                # For init_schema, 'database_path' is critical.
            }
            # If your config.py actually defines a dictionary named CONFIG:
            # from config import CONFIG as APP_CONFIG
        except ImportError as e_cfg_import:
            main_logger.critical(f"Failed to import or load configuration: {e_cfg_import}. Seeding cannot proceed without DB path.")
            sys.exit(1)
        except AttributeError as e_cfg_attr:
             main_logger.critical(f"Config module is missing expected attributes (e.g., DATABASE_PATH): {e_cfg_attr}. Seeding cannot proceed.")
             sys.exit(1)

    # Set the DB_CONFIG in db.connection module
    # This must be done BEFORE initialize_database is called if get_db_connection is used within it,
    # or before run_seed() which definitely uses get_db_connection.
    try:
        from db import connection as db_connection_module
        db_connection_module.set_db_config(APP_CONFIG)
        main_logger.info("db.connection.DB_CONFIG has been set.")
    except Exception as e_set_conf:
        main_logger.critical(f"Failed to set DB_CONFIG in db.connection: {e_set_conf}. Seeding may fail.", exc_info=True)
        # Depending on how critical this is, you might sys.exit(1)

    main_logger.info("Ensuring database schema is initialized before seeding...")
    from db.init_schema import initialize_database
    try:
        # initialize_database now expects app_config
        initialize_database(APP_CONFIG) # Pass the loaded config
        main_logger.info("Database schema initialization check complete.")
        run_seed()
    except Exception as e_main:
        main_logger.critical(f"Critical error during __main__ execution of db_seed: {e_main}", exc_info=True)

_global_seed_initial_data_function_ref = seed_initial_data_master

def seed_initial_data(cursor: sqlite3.Cursor): # type: ignore
    """
    Primary entry point for seeding data, typically called by init_schema.
    This function now calls the master seeding logic.
    """
    _global_seed_initial_data_function_ref(cursor)
