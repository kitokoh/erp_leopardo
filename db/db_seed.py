import os
import sys
import sqlite3
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
from db.cruds.users_crud import users_crud_instance
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
    try:
        # 1. Users
        logger.info(f"Attempting to retrieve admin user ID for '{DEFAULT_ADMIN_USERNAME}' for seeding purposes.")
        admin_user_dict = users_crud_instance.get_user_by_username(DEFAULT_ADMIN_USERNAME, conn=conn)
        admin_user_id = admin_user_dict['user_id'] if admin_user_dict else None

        if admin_user_id:
            logger.info(f"Found admin user '{DEFAULT_ADMIN_USERNAME}' with ID: {admin_user_id}.")
        else:
            logger.warning(f"Admin user '{DEFAULT_ADMIN_USERNAME}' not found.")

        # 2. Companies
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
            admin_user_for_tm_dict = users_crud_instance.get_user_by_id(admin_user_id, conn=conn)
            if admin_user_for_tm_dict:
                cursor.execute("SELECT COUNT(*) FROM TeamMembers WHERE user_id = ?", (admin_user_id,))
                if cursor.fetchone()[0] == 0:
                    cursor.execute("INSERT OR IGNORE INTO TeamMembers (user_id, full_name, email, role_or_title) VALUES (?, ?, ?, ?)",
                                   (admin_user_id, admin_user_for_tm_dict['full_name'], admin_user_for_tm_dict['email'], admin_user_for_tm_dict['role']))
                    logger.info("Seeded admin team member.")
            else:
                logger.warning(f"Could not retrieve admin user details for ID {admin_user_id}.")
        else:
            logger.warning("Admin user ID not available for TeamMember seeding.")

        # Default Operational User
        DEFAULT_OPERATIONAL_USERNAME = "default_operational_user"
        DEFAULT_OPERATIONAL_USER_ROLE = "User"
        logger.info(f"Checking for default operational user '{DEFAULT_OPERATIONAL_USERNAME}'...")
        existing_operational_user = users_crud_instance.get_user_by_username(DEFAULT_OPERATIONAL_USERNAME, conn=conn)
        if existing_operational_user is None:
            logger.info(f"Creating default operational user '{DEFAULT_OPERATIONAL_USERNAME}'...")
            op_user_data = {'username': DEFAULT_OPERATIONAL_USERNAME, 'password': uuid.uuid4().hex, 
                            'email': f"{DEFAULT_OPERATIONAL_USERNAME}@example.local", 'role': DEFAULT_OPERATIONAL_USER_ROLE,
                            'full_name': "Default Operational User", 'is_active': True}
            op_user_result = users_crud_instance.add_user(op_user_data, conn=conn)
            if op_user_result['success']: logger.info(f"Created default operational user ID: {op_user_result['id']}.")
            else: logger.error(f"Failed to create default operational user: {op_user_result.get('error')}")
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
        {'template_name': 'Facture Proforma (HTML)', 'base_file_name': 'proforma_invoice_template.html', 'template_type': 'PROFORMA_INVOICE_HTML', 'description': 'Modèle HTML pour les factures proforma.'},
        {'template_name': 'Liste de Colisage (HTML)', 'base_file_name': 'packing_list_template.html', 'template_type': 'PACKING_LIST_HTML', 'description': 'Modèle HTML pour les listes de colisage.'},
        {'template_name': 'Contrat de Vente (HTML)', 'base_file_name': 'sales_contract_template.html', 'template_type': 'SALES_CONTRACT_HTML', 'description': 'Modèle HTML pour les contrats de vente.'},
    ]
    all_supported_template_langs = ["fr", "en", "ar", "tr", "pt"]

    for lang_code in all_supported_template_langs:
        for doc_def in main_document_templates_definitions:
            full_template_name = f"{doc_def['template_name']} ({lang_code.upper()})"
            template_data_for_db = {
                'template_name': full_template_name, 'template_type': doc_def['template_type'],
                'language_code': lang_code, 'base_file_name': doc_def['base_file_name'],
                'description': doc_def['description'], 'category_id': category_id,
                'client_id': None, 'is_default_for_type_lang': False,
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


def _seed_motivational_messages(cursor: sqlite3.Cursor, conn: sqlite3.Connection, logger_passed: logging.Logger):
    logger = logger_passed
    logger.info("Attempting to seed motivational messages...")

    messages_crud = GenericCRUD(table_name='motivational_messages', primary_key='id')

    default_messages = [
        # French
        {"language_code": "fr", "message": "Chaque jour est une nouvelle opportunité.", "day_of_year": None},
        {"language_code": "fr", "message": "Croyez en vous et tout deviendra possible.", "day_of_year": None},
        {"language_code": "fr", "message": "Le succès commence par un état d'esprit.", "day_of_year": None},
        {"language_code": "fr", "message": "Soyez le changement que vous voulez voir dans le monde.", "day_of_year": None},
        {"language_code": "fr", "message": "La persévérance est la clé de la réussite.", "day_of_year": None},
        # English
        {"language_code": "en", "message": "Every day is a new opportunity.", "day_of_year": None},
        {"language_code": "en", "message": "Believe in yourself and anything is possible.", "day_of_year": None},
        {"language_code": "en", "message": "Success begins with a state of mind.", "day_of_year": None},
        {"language_code": "en", "message": "Be the change you wish to see in the world.", "day_of_year": None},
        {"language_code": "en", "message": "Perseverance is the key to success.", "day_of_year": None},
        # Arabic (Example - ensure your DB/system handles UTF-8 correctly)
        {"language_code": "ar", "message": "كل يوم هو فرصة جديدة.", "day_of_year": None},
        {"language_code": "ar", "message": "آمن بنفسك وكل شيء سيصبح ممكنًا.", "day_of_year": None},
    ]

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
            if msg_data["day_of_year"] is None:
                # Query for existing message with same language and text where day_of_year IS NULL
                query = "SELECT id FROM motivational_messages WHERE language_code = ? AND message = ? AND day_of_year IS NULL"
                cursor.execute(query, (msg_data["language_code"], msg_data["message"]))
                existing = cursor.fetchone()

            if existing:
                logger.debug(f"Motivational message '{msg_data['message'][:30]}...' for lang '{msg_data['language_code']}' already exists. Skipping.")
                skipped_count += 1
                continue

            # Prepare data for insertion (GenericCRUD expects a dict)
            # We don't need to specify 'id', 'created_at', 'updated_at', 'is_active' as they have defaults or are auto.
            data_to_insert = {
                "language_code": msg_data["language_code"],
                "message": msg_data["message"],
                "day_of_year": msg_data["day_of_year"] # Can be None
            }
            messages_crud.create(data_to_insert)
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
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    main_logger = logging.getLogger(__name__)
    main_logger.info("Ensuring database schema is initialized before seeding...")
    from db.init_schema import initialize_database
    try:
        initialize_database()
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
