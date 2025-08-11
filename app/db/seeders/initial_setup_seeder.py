import logging
import sqlite3
import uuid
from datetime import datetime

from app.db.cruds.users import users_crud
from app.db.cruds.clients.clients_crud import clients_crud_instance
from app.db.cruds.products.products_crud import products_crud_instance as products_crud
from app.db.cruds.misc.status_settings_crud import get_status_setting_by_name
from app.db.cruds.misc.locations_crud import get_country_by_name, get_city_by_name_and_country_id
from app.db.cruds.misc.partners_crud import get_partner_category_by_name, add_partner_category
from app.db.cruds.misc.referents_crud import get_referent_by_client_id, add_referent
from app.db.cruds.misc.application_settings_crud import set_setting
from app.db.cruds import commandes_crud
from app.auth.roles import SUPER_ADMIN

def seed_initial_setup(conn: sqlite3.Connection, logger: logging.Logger):
    """
    Runs all the miscellaneous initial setup seeding functions.
    """
    logger.info("--- Starting initial setup seeding ---")

    admin_user = users_crud.get_user_by_username(conn, "admin")
    if not admin_user:
        logger.error("Admin user not found. Many initial setup seeds will be skipped.")
        return

    admin_user_id = admin_user['user_id']

    _seed_default_company(conn, logger)
    _seed_admin_team_member(conn, logger, admin_user_id)
    _seed_sample_client_and_project(conn, logger, admin_user_id)
    _seed_generic_contact(conn, logger)
    _seed_sample_products(conn, logger)
    _seed_smtp_config(conn, logger)
    _seed_app_settings(conn, logger)
    _seed_partner_categories(conn, logger)
    _seed_document_footers(conn, logger)
    _seed_default_document_notes(conn, logger)
    _seed_sample_referents(conn, logger, admin_user_id)

    logger.info("--- Finished initial setup seeding ---")


def _seed_default_company(conn: sqlite3.Connection, logger: logging.Logger):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM companies")
    if cursor.fetchone()[0] == 0:
        default_company_id = str(uuid.uuid4())
        cursor.execute("INSERT OR IGNORE INTO companies (company_id, company_name, address, is_default) VALUES (?, ?, ?, ?)",
                       (default_company_id, "Default Company Inc.", "123 Default Street", True))
        logger.info("Seeded default company.")

        cursor.execute("INSERT OR IGNORE INTO CompanyPersonnel (company_id, name, role, email, phone) VALUES (?, ?, ?, ?, ?)",
                       (default_company_id, "Admin Contact", "Administrator", "contact@defaultcomp.com", "123-456-7890"))
        logger.info("Seeded default company personnel.")

def _seed_admin_team_member(conn: sqlite3.Connection, logger: logging.Logger, admin_user_id: str):
    cursor = conn.cursor()
    admin_details = users_crud.get_user_by_id(conn, admin_user_id)
    if admin_details:
        cursor.execute("SELECT COUNT(*) FROM TeamMembers WHERE user_id = ?", (admin_user_id,))
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT OR IGNORE INTO TeamMembers (user_id, full_name, email, role_or_title) VALUES (?, ?, ?, ?)",
                           (admin_user_id, admin_details.get('full_name'), admin_details.get('email'), admin_details.get('role_name')))
            logger.info(f"Seeded TeamMember for admin user ID: {admin_user_id}.")

def _seed_sample_client_and_project(conn: sqlite3.Connection, logger: logging.Logger, admin_user_id: str):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Clients")
    if cursor.fetchone()[0] == 0:
        france = get_country_by_name("France", conn=conn)
        paris = get_city_by_name_and_country_id("Paris", france['country_id'], conn=conn) if france else None
        active_status = get_status_setting_by_name("Client Actif", "Client", conn=conn)

        if france and paris and active_status:
            client_data = {
                'client_name': "Sample Client", 'country_id': france['country_id'], 'city_id': paris['city_id'],
                'status_id': active_status['status_id'], 'created_by_user_id': admin_user_id,
                'default_base_folder_path': f"clients/{uuid.uuid4()}", 'project_identifier': "SC-PROJ-001"
            }
            res = clients_crud_instance.add_client(client_data, conn=conn)
            if res['success']:
                client_id = res['client_id']
                logger.info(f"Seeded sample client ID: {client_id}")
                planning_status = get_status_setting_by_name("Planning", "Project", conn=conn)
                if planning_status:
                    proj_data = {'project_id': str(uuid.uuid4()), 'client_id': client_id, 'project_name': "Initial Project", 'status_id': planning_status['status_id'], 'manager_team_member_id': admin_user_id}
                    cursor.execute("INSERT INTO Projects (project_id, client_id, project_name, status_id, manager_team_member_id) VALUES (?,?,?,?,?)",
                                   (proj_data['project_id'], proj_data['client_id'], proj_data['project_name'], proj_data['status_id'], proj_data['manager_team_member_id']))
                    logger.info("Seeded sample project.")
        else:
            logger.warning("Could not find required data (France, Paris, or Active Status) for sample client seeding.")

def _seed_generic_contact(conn: sqlite3.Connection, logger: logging.Logger):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Contacts WHERE email = 'contact@example.com'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT OR IGNORE INTO Contacts (name, email) VALUES (?,?)", ("Placeholder Contact", "contact@example.com"))
        logger.info("Seeded generic contact.")

def _seed_sample_products(conn: sqlite3.Connection, logger: logging.Logger):
    cursor = conn.cursor()
    sample_prods = [
        {'product_name': "Default Product", 'language_code': "en", 'base_unit_price': 10.0, 'product_code': "PROD001"},
        {'product_name': "Industrial Widget", 'language_code': "en", 'base_unit_price': 100.0, 'product_code': "PROD002"},
        {'product_name': "Gadget Standard", 'language_code': "fr", 'base_unit_price': 50.0, 'product_code': "PROD003"},
        {'product_name': "Advanced Gizmo", 'language_code': "en", 'base_unit_price': 250.0, 'product_code': "PROD004"}
    ]
    for prod in sample_prods:
        cursor.execute("SELECT COUNT(*) FROM Products WHERE product_name = ? AND language_code = ?", (prod["product_name"], prod["language_code"]))
        if cursor.fetchone()[0] == 0:
            products_crud.add_product(prod, conn=conn)
    logger.info("Finished seeding sample products.")

def _seed_smtp_config(conn: sqlite3.Connection, logger: logging.Logger):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM SmtpConfigs")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT OR IGNORE INTO SmtpConfigs (config_name, smtp_server, smtp_port, username, password_encrypted, use_tls, is_default, sender_email_address, sender_display_name) VALUES (?,?,?,?,?,?,?,?,?)",
                       ("Placeholder - Configure Me", "smtp.example.com", 587, "user", "placeholder_password", True, True, "noreply@example.com", "Placeholder Email"))
        logger.info("Seeded placeholder SMTP config.")

def _seed_app_settings(conn: sqlite3.Connection, logger: logging.Logger):
    set_setting('google_maps_review_url', 'https://maps.google.com/?cid=YOUR_CID_HERE', conn=conn)
    logger.info("Seeded additional application settings.")

def _seed_partner_categories(conn: sqlite3.Connection, logger: logging.Logger):
    categories = [
        {'category_name': 'Supplier', 'description': 'Providers of goods and materials.'},
        {'category_name': 'Service Provider', 'description': 'Companies offering services.'},
        {'category_name': 'Technology Partner', 'description': 'Partners providing technology solutions.'},
        {'category_name': 'Consultant', 'description': 'External consultants and advisors.'},
        {'category_name': 'Distributor', 'description': 'Entities distributing products.'}
    ]
    for cat in categories:
        if not get_partner_category_by_name(cat['category_name'], conn=conn):
            add_partner_category(cat, conn=conn)
    logger.info("Default partner categories seeding attempt finished.")

def _seed_document_footers(conn: sqlite3.Connection, logger: logging.Logger):
    footers = {
        "default_document_footer_notes_fr": "Merci de votre confiance. N'hésitez pas à nous contacter pour toute question.",
        "default_document_footer_notes_en": "Thank you for your business. Please contact us if you have any questions.",
        "default_document_footer_notes_ar": "شكراً لثقتكم بنا. لا تترددوا في الاتصال بنا لأية استفسارات."
    }
    for key, value in footers.items():
        set_setting(key, value, conn=conn)
    logger.info("Default document footer notes seeding complete.")

def _seed_default_document_notes(conn: sqlite3.Connection, logger: logging.Logger):
    from app.db.cruds.misc.notes_crud import add_default_document_note, get_default_document_note
    doc_types = [
        "contact_page", "sales_contract_excel", "cover_page", "packing_list_html",
        "packing_list_excel", "product_images", "proforma_invoice_html", "proforma_invoice_excel",
        "sales_contract_html", "technical_specs_excel", "technical_specs_html", "warranty_document"
    ]
    langs = ["en", "fr", "ar", "tr", "pt", "ru"]
    notes = {
        "en": "Default note: Please review all details carefully.",
        "fr": "Note par défaut : Veuillez vérifier attentivement tous les détails.",
        "ar": "ملاحظة افتراضية: يرجى مراجعة جميع التفاصيل بعناية.",
        "tr": "Varsayılan not: Lütfen tüm ayrıntıları dikkatlice inceleyin.",
        "pt": "Nota padrão: Revise todos os detalhes com atenção.",
        "ru": "Примечание по умолчанию: Пожалуйста, внимательно проверьте все детали."
    }
    for doc_type in doc_types:
        for lang in langs:
            if not get_default_document_note(doc_type, lang, conn=conn):
                add_default_document_note(doc_type, lang, notes.get(lang, f"Default note for {doc_type} ({lang})."), conn=conn)
    logger.info("DefaultDocumentNotes seeding complete.")

def _seed_sample_referents(conn: sqlite3.Connection, logger: logging.Logger, admin_user_id: str):
    sample_clients = clients_crud_instance.get_all_clients_with_details(filters={'status_name': 'Client Actif'}, limit=5, conn=conn)
    if not sample_clients:
        logger.warning("No sample active clients found to make into referents.")
        return

    for client in sample_clients:
        client_id = client.get('client_id')
        if not client_id or not client.get('country_id'):
            continue
        if get_referent_by_client_id(client_id, conn=conn, include_inactive=True):
            continue
        if not commandes_crud.get_commandes_for_client(client_id, limit=1, conn=conn):
            continue

        add_referent(
            client_id=client_id, country_id=client.get('country_id'), region_id=None,
            city_id=client.get('city_id'), notes=f"Exemplary referent from {client.get('country', 'N/A')}.",
            created_by_user_id=admin_user_id, conn=conn
        )
    logger.info("Sample referents seeding complete.")
