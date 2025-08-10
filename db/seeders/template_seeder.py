import json
import os
import logging
import sqlite3

from db.cruds.misc.template_categories_crud import add_template_category, get_template_category_by_name
from db.cruds.misc.templates_crud import add_default_template_if_not_exists
from db.cruds.misc.application_settings_crud import get_setting, set_setting

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def seed_all_templates(conn: sqlite3.Connection, logger: logging.Logger):
    """
    Seeds all templates (email, utility, main) from the default_templates.json file.
    """
    logger.info("Seeding all templates from default_templates.json...")
    json_path = os.path.join(PROJECT_ROOT, "db", "seed_data", "default_templates.json")

    if not os.path.exists(json_path):
        logger.error(f"JSON file not found at: {json_path}. Skipping template seeding.")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Seed Email Templates
    _seed_email_templates(conn, logger, data.get("email_templates", []))

    # Seed Utility Templates
    _seed_utility_templates(conn, logger, data.get("utility_templates", []))

    # Seed Main Document Templates
    _seed_main_document_templates(conn, logger, data.get("main_document_templates", []))

    logger.info("Finished seeding all templates.")


def _get_or_create_category(name, description, purpose, conn, logger):
    """Helper to get or create a template category."""
    category_obj = get_template_category_by_name(name, conn=conn)
    if category_obj:
        return category_obj['category_id']
    else:
        logger.info(f"Category '{name}' not found, creating it with purpose '{purpose}'.")
        category_id = add_template_category(
            category_name=name, description=description, purpose=purpose, conn=conn
        )
        if not category_id:
            logger.error(f"Failed to create category '{name}'.")
            return None
        return category_id

def _seed_email_templates(conn: sqlite3.Connection, logger: logging.Logger, templates_data: list):
    logger.info("Seeding email templates...")
    for template_def in templates_data:
        add_default_template_if_not_exists(template_def, conn=conn)
    logger.info("Finished seeding email templates.")


def _seed_utility_templates(conn: sqlite3.Connection, logger: logging.Logger, templates_data: list):
    logger.info("Seeding utility templates...")
    category_name = "Document Utilitaires"
    category_desc = "Modèles de documents utilitaires généraux"
    category_purpose = 'utility'
    category_id = _get_or_create_category(category_name, category_desc, category_purpose, conn, logger)

    if not category_id:
        logger.error("Could not get or create utility category. Aborting utility template seeding.")
        return

    for doc_def in templates_data:
        ext = os.path.splitext(doc_def['base_file_name'])[1].lower()
        template_type_map = {'.pdf': 'document_pdf', '.html': 'document_html', '.docx': 'document_word', '.xlsx': 'document_excel'}
        template_type = template_type_map.get(ext, 'document_other')

        template_data_for_db = {
            'template_name': doc_def['template_name'], 'template_type': template_type,
            'language_code': doc_def['language_code'], 'base_file_name': doc_def['base_file_name'],
            'description': doc_def['description'], 'category_id': category_id,
            'category_purpose': category_purpose,
            'client_id': None, 'is_default_for_type_lang': False,
        }
        template_id = add_default_template_if_not_exists(template_data_for_db, conn=conn)
        if template_id:
            visibility_key = f"template_visibility_{template_id}_enabled"
            if get_setting(visibility_key, conn=conn) is None:
                set_setting(visibility_key, 'True', conn=conn)
    logger.info("Finished seeding utility templates.")


def _seed_main_document_templates(conn: sqlite3.Connection, logger: logging.Logger, templates_data: list):
    logger.info("Seeding main document templates...")
    category_name = "Documents Client"
    category_desc = "Templates de documents principaux pour les clients (contrats, proformas, etc.)"
    category_purpose = 'client_document'
    category_id = _get_or_create_category(category_name, category_desc, category_purpose, conn, logger)

    if not category_id:
        logger.error("Could not get or create main document category. Aborting main document template seeding.")
        return

    all_supported_template_langs = ["fr", "en", "ar", "tr", "pt"]

    for lang_code in all_supported_template_langs:
        for doc_def in templates_data:
            full_template_name = f"{doc_def['template_name']} ({lang_code.upper()})"

            is_default = False
            if doc_def['template_type'] == 'HTML_PROFORMA' and lang_code == 'fr':
                is_default = True

            template_data_for_db = {
                'template_name': full_template_name, 'template_type': doc_def['template_type'],
                'language_code': lang_code, 'base_file_name': doc_def['base_file_name'],
                'description': doc_def['description'], 'category_id': category_id,
                'category_purpose': category_purpose,
                'client_id': None, 'is_default_for_type_lang': is_default,
            }
            template_id = add_default_template_if_not_exists(template_data_for_db, conn=conn)
            if template_id:
                visibility_key = f"template_visibility_{template_id}_enabled"
                if get_setting(visibility_key, conn=conn) is None:
                    set_setting(visibility_key, 'True', conn=conn)
    logger.info("Finished seeding main document templates.")
