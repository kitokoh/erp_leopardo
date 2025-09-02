import logging
import uuid
from sqlalchemy.orm import Session

# Import all necessary CRUDs and Models
from app.db.cruds.users import users_crud
from app.db.cruds.clients.clients_crud import clients_crud_instance
from app.db.cruds.products.products_crud import products_crud
from app.db.cruds.misc.status_settings_crud import get_status_setting_by_name
from app.db.cruds.misc.locations_crud import get_country_by_name, get_city_by_name_and_country_id
from app.db.cruds.misc.partners_crud import partner_categories_crud
from app.db.cruds.misc.referents_crud import get_referent_by_client_id, add_referent
from app.db.cruds.misc.application_settings_crud import settings_crud
from app.db.cruds.invoices import commandes_crud
from app.services.auth.roles import SUPER_ADMIN
from app.services.api.models import ProductCreate

from app.models.db.misc.companies import Company
from app.models.db.misc.companypersonnel import CompanyPersonnel
from app.models.db.misc.teammembers import TeamMember
from app.models.db.clients.client import Client
from app.models.db.projects.project import Project
from app.models.db.misc.contacts import Contact
from app.models.db.products.product import Product
from app.models.db.misc.smtpconfigs import SmtpConfig
from app.models.db.misc.partnercategories import PartnerCategory
from app.models.db.documents.defaultdocumentnotes import Defaultdocumentnotes as DefaultDocumentNote


def seed_initial_setup(db: Session, logger: logging.Logger):
    """
    Runs all the miscellaneous initial setup seeding functions using SQLAlchemy ORM.
    """
    logger.info("--- Starting initial setup seeding ---")

    admin_user = users_crud.get_user_by_username(db, "admin")
    if not admin_user:
        logger.error("Admin user not found. Many initial setup seeds will be skipped.")
        return

    admin_user_id = admin_user.user_id

    _seed_default_company(db, logger)
    _seed_admin_team_member(db, logger, admin_user_id)
    _seed_sample_client_and_project(db, logger, admin_user_id)
    _seed_generic_contact(db, logger)
    _seed_sample_products(db, logger)
    _seed_smtp_config(db, logger)
    _seed_app_settings(db, logger)
    _seed_partner_categories(db, logger)
    _seed_document_footers(db, logger)
    _seed_default_document_notes(db, logger)
    _seed_sample_referents(db, logger, admin_user_id)

    logger.info("--- Finished initial setup seeding ---")


def _seed_default_company(db: Session, logger: logging.Logger):
    if db.query(Company).count() == 0:
        default_company = Company(
            company_id=str(uuid.uuid4()),
            company_name="Default Company Inc.",
            address="123 Default Street",
            is_default=True
        )
        db.add(default_company)
        logger.info("Seeded default company.")

        personnel = CompanyPersonnel(
            company_id=default_company.company_id,
            name="Admin Contact",
            role="Administrator",
            email="contact@defaultcomp.com",
            phone="123-456-7890"
        )
        db.add(personnel)
        logger.info("Seeded default company personnel.")

def _seed_admin_team_member(db: Session, logger: logging.Logger, admin_user_id: str):
    admin_details = users_crud.get_user_by_id(db, admin_user_id)
    if admin_details:
        member_exists = db.query(TeamMember).filter(TeamMember.user_id == admin_user_id).first()
        if not member_exists:
            new_member = TeamMember(
                user_id=admin_user_id,
                full_name=admin_details.full_name,
                email=admin_details.email,
                role_or_title=admin_details.role.role_name if admin_details.role else 'Administrator'
            )
            db.add(new_member)
            logger.info(f"Seeded TeamMember for admin user ID: {admin_user_id}.")

def _seed_sample_client_and_project(db: Session, logger: logging.Logger, admin_user_id: str):
    if db.query(Client).count() == 0:
        france = get_country_by_name(db, "France")
        paris = get_city_by_name_and_country_id(db, "Paris", france.country_id) if france else None
        active_status = get_status_setting_by_name(db, "Client Actif", "Client")

        if france and paris and active_status:
            client_data = {
                'client_name': "Sample Client", 'company_name': "Sample Corp",
                'country_id': france.country_id, 'city_id': paris.city_id,
                'status_id': active_status.status_id, 'created_by_user_id': admin_user_id,
                'project_identifier': "SC-PROJ-001"
            }
            res = clients_crud_instance.add_client(db, client_data)
            if res.get('success'):
                logger.info(f"Seeded sample client with ID: {res.get('client_id')}")
            else:
                logger.error(f"Failed to seed sample client: {res.get('error')}")
        else:
            logger.warning("Could not find required data (France, Paris, or Active Status) for sample client seeding.")

def _seed_generic_contact(db: Session, logger: logging.Logger):
    if db.query(Contact).filter(Contact.email == 'contact@example.com').count() == 0:
        new_contact = Contact(name="Placeholder Contact", email="contact@example.com")
        db.add(new_contact)
        logger.info("Seeded generic contact.")

def _seed_sample_products(db: Session, logger: logging.Logger):
    sample_prods = [
        {'product_name': "Default Product", "product_code": "DEFAULT-001", 'language_code': "en", 'base_unit_price': 10.0},
        {'product_name': "Industrial Widget", "product_code": "IND-WID-001", 'language_code': "en", 'base_unit_price': 100.0},
    ]
    for prod_data in sample_prods:
        exists = products_crud.get_product_by_name(db, prod_data['product_name'])
        if not exists:
            product_to_create = ProductCreate(**prod_data)
            products_crud.create_product(db, product_to_create)
    logger.info("Finished seeding sample products.")

def _seed_smtp_config(db: Session, logger: logging.Logger):
    if db.query(SmtpConfig).count() == 0:
        new_config = SmtpConfig(
            config_name="Placeholder - Configure Me", smtp_server="smtp.example.com", smtp_port=587,
            username="user", password_encrypted="placeholder_password", use_tls=True, is_default=True,
            sender_email_address="noreply@example.com", sender_display_name="Placeholder Email"
        )
        db.add(new_config)
        logger.info("Seeded placeholder SMTP config.")

def _seed_app_settings(db: Session, logger: logging.Logger):
    settings_crud.set_setting(db, 'google_maps_review_url', 'https://maps.google.com/?cid=YOUR_CID_HERE')
    logger.info("Seeded additional application settings.")

def _seed_partner_categories(db: Session, logger: logging.Logger):
    categories = [
        {'category_name': 'Supplier', 'description': 'Providers of goods and materials.'},
        {'category_name': 'Service Provider', 'description': 'Companies offering services.'},
    ]
    for cat_data in categories:
        if not partner_categories_crud.get_partner_category_by_name(db, cat_data['category_name']):
            partner_categories_crud.add_partner_category(db, cat_data)
    logger.info("Default partner categories seeding attempt finished.")

def _seed_document_footers(db: Session, logger: logging.Logger):
    footers = {
        "default_document_footer_notes_fr": "Merci de votre confiance.",
        "default_document_footer_notes_en": "Thank you for your business.",
    }
    for key, value in footers.items():
        settings_crud.set_setting(db, key, value)
    logger.info("Default document footer notes seeding complete.")

def _seed_default_document_notes(db: Session, logger: logging.Logger):
    from app.db.cruds.misc.notes_crud import default_document_notes_crud
    doc_types = ["contact_page", "proforma_invoice_html"]
    langs = ["en", "fr"]
    notes = {"en": "Default note.", "fr": "Note par défaut."}
    for doc_type in doc_types:
        for lang in langs:
            if not default_document_notes_crud.get_default_document_note(db, doc_type, lang):
                default_document_notes_crud.add_default_document_note(db, doc_type, lang, notes.get(lang))
    logger.info("DefaultDocumentNotes seeding complete.")

def _seed_sample_referents(db: Session, logger: logging.Logger, admin_user_id: str):
    sample_clients = clients_crud_instance.get_all_clients_with_details(db, filters={'status_name': 'Client Actif'}, limit=1)
    if not sample_clients:
        logger.warning("No sample active clients found to make into referents.")
        return

    for client in sample_clients:
        client_id = client.get('client_id')
        if not client_id or not client.get('country_id'):
            continue
        if get_referent_by_client_id(db, client_id, include_inactive=True):
            continue
        if not commandes_crud.get_commandes_for_client(db, client_id, limit=1):
            continue
        add_referent(
            db=db, client_id=client_id, country_id=client.get('country_id'),
            notes=f"Exemplary referent from {client.get('country', 'N/A')}.",
            created_by_user_id=admin_user_id
        )
    logger.info("Sample referents seeding complete.")
