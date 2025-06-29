# -*- coding: utf-8 -*-
import os
import json
import sys
import logging # Added logging
from datetime import datetime

from PyQt5.QtCore import QStandardPaths, QCoreApplication, QUrl
from PyQt5.QtGui import QDesktopServices # Added for generate_pdf_for_document
from PyQt5.QtWidgets import QMessageBox

from docx import Document
import db as db_manager # For generate_pdf_for_document

from html_to_pdf_util import convert_html_to_pdf # For generate_pdf_for_document

# MAIN_APP_ROOT_DIR import removed as app_root_dir is now passed to generate_pdf_for_document

# --- Configuration Constants ---
CONFIG_DIR_NAME = "ClientDocumentManager"
CONFIG_FILE_NAME = "config.json"
# TEMPLATES_SUBDIR = "templates" # Removed as no longer used in utils.py
# CLIENTS_SUBDIR = "clients"   # Removed as no longer used in utils.py

# --- Configuration Functions ---
def get_config_dir():
    config_dir_path = os.path.join(
        QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation),
        CONFIG_DIR_NAME
    )
    os.makedirs(config_dir_path, exist_ok=True)
    return config_dir_path

def get_config_file_path():
    return os.path.join(get_config_dir(), CONFIG_FILE_NAME)

def load_config(app_root_dir, default_templates_dir, default_clients_dir):
    """
    Loads configuration from JSON file.
    Requires app_root_dir to construct default paths if config file doesn't exist.
    """
    config_path = get_config_file_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)
                # Ensure 'database_type' defaults to 'sqlite' if not present
                user_config.setdefault('database_type', 'sqlite')
                return user_config
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading config: {e}. Using defaults.")

    # If config file doesn't exist or is invalid, return defaults
    default_config = {
        "templates_dir": default_templates_dir, # Use passed default
        "clients_dir": default_clients_dir,     # Use passed default
        "database_path": os.path.join(app_root_dir, "app_data.db"),
        "database_type": "sqlite", # Ensure default is sqlite
        "language": "fr",
        "smtp_server": "",
        "smtp_port": 587,
        "smtp_user": "",
        "smtp_password": "",
        "default_reminder_days": 30,
        "download_monitor_enabled": False,
        "download_monitor_path": os.path.join(os.path.expanduser('~'), 'Downloads')
    }
    return default_config

def save_config(config_data):
    try:
        config_path = get_config_file_path()
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
    except IOError as e:
        QMessageBox.warning(None, QCoreApplication.translate("utils.save_config", "Erreur de Configuration"),
                            QCoreApplication.translate("utils.save_config", "Impossible d'enregistrer la configuration: {0}").format(e))

def is_first_launch(app_root_dir, default_templates_dir, default_clients_dir):
    """Checks if this is the first launch of the application."""
    config = load_config(app_root_dir, default_templates_dir, default_clients_dir)
    return not config.get("initial_setup_complete", False)

def mark_initial_setup_complete(app_root_dir, default_templates_dir, default_clients_dir):
    """Marks that the initial setup has been completed."""
    config = load_config(app_root_dir, default_templates_dir, default_clients_dir)
    config["initial_setup_complete"] = True
    save_config(config)

# --- DOCX Population Logic ---
def populate_docx_template(docx_path, document_context):
    """
    Populates a .docx template with data from the document_context.
    Placeholders should be in the format {{CLIENT_NAME}}, {{SELLER_NAME}}, etc.
    """
    if not os.path.exists(docx_path):
        logging.error(f"DOCX template file not found: {docx_path}")
        QMessageBox.critical(None, "Template Error", f"DOCX template file not found: {docx_path}")
        return

    try:
        document = Document(docx_path)

        # Extract data from document_context
        client = document_context.get("client", {})
        seller = document_context.get("seller", {})
        doc_info = document_context.get("doc", {})
        project_info = document_context.get("project", {})
        # products_info = document_context.get("products", []) # Products might be complex for simple placeholders

        placeholders = {
            "{{CLIENT_NAME}}": client.get("individual_name", ""),
            "{{CLIENT_COMPANY_NAME}}": client.get("company_name", ""),
            "{{CLIENT_DISPLAY_NAME}}": client.get("display_name", ""),
            "{{CLIENT_ADDRESS_FULL}}": client.get("address_full", ""),
            "{{CLIENT_ADDRESS_LINE1}}": client.get("address_line1", ""),
            "{{CLIENT_CITY}}": client.get("city", ""),
            "{{CLIENT_COUNTRY}}": client.get("country", ""),
            "{{CLIENT_POSTAL_CODE}}": client.get("postal_code", ""),
            "{{CLIENT_CONTACT_NAME}}": client.get("contact_name", ""),
            "{{CLIENT_CONTACT_EMAIL}}": client.get("contact_email", ""),
            "{{CLIENT_CONTACT_PHONE}}": client.get("contact_phone", ""),
            "{{CLIENT_VAT_ID}}": client.get("vat_id", ""),
            "{{CLIENT_REGISTRATION_NUMBER}}": client.get("registration_number", ""),

            "{{SELLER_NAME}}": seller.get("name", ""),
            "{{SELLER_ADDRESS_FULL}}": seller.get("address_full", ""),
            "{{SELLER_ADDRESS_LINE1}}": seller.get("address_line1", ""),
            "{{SELLER_CITY}}": seller.get("city", ""),
            "{{SELLER_COUNTRY}}": seller.get("country", ""),
            "{{SELLER_POSTAL_CODE}}": seller.get("postal_code", ""),
            "{{SELLER_PHONE}}": seller.get("phone", ""),
            "{{SELLER_EMAIL}}": seller.get("email", ""),
            "{{SELLER_WEBSITE}}": seller.get("website", ""),
            "{{SELLER_VAT_ID}}": seller.get("vat_id", ""),
            "{{SELLER_REGISTRATION_NUMBER}}": seller.get("registration_number", ""),
            "{{SELLER_BANK_NAME}}": seller.get("bank_name", ""),
            "{{SELLER_BANK_ACCOUNT_HOLDER_NAME}}": seller.get("bank_account_holder_name", ""),
            "{{SELLER_BANK_IBAN}}": seller.get("bank_iban", ""),
            "{{SELLER_BANK_SWIFT_BIC}}": seller.get("bank_swift_bic", ""),
            "{{SELLER_BANK_ADDRESS}}": seller.get("bank_address", ""),
            "{{SELLER_REPRESENTATIVE_NAME}}": seller.get("representative_name", ""),
            "{{SELLER_LOGO_URL}}": seller.get("logo_url", ""), # Note: DOCX might not directly embed web URLs for images easily. Path might be better.

            "{{PROJECT_NAME}}": project_info.get("name", ""),
            "{{PROJECT_IDENTIFIER}}": project_info.get("identifier", ""),

            "{{DOC_CURRENT_DATE}}": doc_info.get("current_date_formatted", doc_info.get("current_date", "")),
            "{{DOC_REFERENCE}}": doc_info.get("document_reference", ""),
            "{{DOC_PROFORMA_ID}}": doc_info.get("proforma_id", ""), # Alias for proforma
            "{{DOC_CURRENCY_SYMBOL}}": doc_info.get("currency_symbol", ""),
            "{{DOC_SUBTOTAL_AMOUNT}}": doc_info.get("subtotal_amount", ""),
            "{{DOC_DISCOUNT_AMOUNT}}": doc_info.get("discount_amount", ""),
            "{{DOC_VAT_AMOUNT}}": doc_info.get("vat_amount", ""),
            "{{DOC_GRAND_TOTAL_AMOUNT}}": doc_info.get("grand_total_amount", ""),
            # Add more from doc_info.get("client_specific_notes") if it's a simple string, or handle list
        }

        # Add labels from context if they exist
        labels = document_context.get("labels", {})
        for label_key, label_value in labels.items():
            placeholders[f"{{{{LABEL_{label_key.upper()}}}}}"] = label_value # e.g. {{LABEL_PROFORMA_NO}}

        # Simple replacement for paragraphs and tables
        # For more complex scenarios (like repeating product rows), python-docx-template might be better.
        for para in document.paragraphs:
            for key, value in placeholders.items():
                if key in para.text:
                    # Replacing in runs to preserve formatting as much as possible
                    for run in para.runs:
                        if key in run.text:
                            run.text = run.text.replace(key, str(value))

        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        for key, value in placeholders.items():
                            if key in para.text:
                                for run in para.runs:
                                    if key in run.text:
                                        run.text = run.text.replace(key, str(value))

        document.save(docx_path)
        logging.info(f"DOCX template populated using document_context: {docx_path}")
    except Exception as e:
        logging.error(f"Error populating DOCX template {docx_path} with document_context: {e}", exc_info=True)
        QMessageBox.critical(None, "Population Error", f"Error populating DOCX template {docx_path}: {e}")
        return

# --- PDF Generation Logic ---
def generate_pdf_for_document(
    source_file_path: str,
    client_info: dict,
    app_root_dir:str,
    parent_widget=None,
    target_language_code: str = "fr",
    project_id: int = None,
    additional_context: dict = None,
    document_type_for_context: str = None,
    allow_empty_products: bool = False # New flag
) -> str | None:
    """
    Generates a PDF for a given source document (HTML, XLSX, DOCX).
    Uses app_root_dir for resolving paths to resources like default logos if needed.
    Accepts project_id and additional_context to enrich the document context.
    Includes logic to check for product language match for proforma invoices.
    """
    from html_editor import HtmlEditor # Moved here to break circular import

    if not os.path.exists(source_file_path):
        logging.error(f"Source HTML file not found for PDF generation: {source_file_path}")
        QMessageBox.critical(parent_widget, "File Error", f"Source HTML file not found for PDF generation: {source_file_path}")
        return None

    from html_editor import HtmlEditor # DEFERRED IMPORT

    if not client_info or 'client_id' not in client_info:
        QMessageBox.warning(parent_widget, QCoreApplication.translate("utils.generate_pdf", "Erreur Client"),
                            QCoreApplication.translate("utils.generate_pdf", "ID Client manquant. Impossible de générer le PDF."))
        return None

    file_name_base_template, file_ext = os.path.splitext(os.path.basename(source_file_path)) # file_name_base_template is like 'proforma_invoice_template'

    # Determine a more descriptive PDF filename
    client_name_for_file = client_info.get('client_name', 'Client').replace(' ', '_').replace('/', '_')
    doc_type_for_file = document_type_for_context if document_type_for_context else file_name_base_template
    doc_type_for_file = doc_type_for_file.replace('_HTML', '').replace('_TEMPLATE', '').replace(' ', '_') # Basic cleanup
    timestamp_for_file = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_pdf_filename = f"{doc_type_for_file}_{client_name_for_file}_{target_language_code}_{timestamp_for_file}.pdf"

    # Determine correct output directory within client's folder structure
    client_base_folder = client_info.get('base_folder_path') # This should be an absolute path
    if not client_base_folder:
        logging.error("Client base_folder_path missing in client_info. Cannot determine PDF save location.")
        QMessageBox.critical(parent_widget, "Erreur Configuration Client", "Dossier de base du client non trouvé.")
        return None

    # Define a subfolder for the specific document type, e.g., "Proformas", "Devis"
    # We can use document_type_for_context (like HTML_PROFORMA) and clean it up for a folder name
    doc_type_folder_name = doc_type_for_file # Use the cleaned up doc_type_for_file
    if not doc_type_folder_name or doc_type_folder_name == "template": # Fallback if cleanup was too aggressive
        doc_type_folder_name = "DocumentsGeneres"

    # Path: ClientBaseFolder / LanguageCode / DocumentTypeFolder / filename.pdf
    target_save_directory = os.path.join(client_base_folder, target_language_code, doc_type_folder_name)
    try:
        os.makedirs(target_save_directory, exist_ok=True)
    except OSError as e:
        logging.error(f"Failed to create target directory {target_save_directory}: {e}")
        QMessageBox.critical(parent_widget, "Erreur Dossier", f"Impossible de créer le dossier de sauvegarde : {target_save_directory}")
        return None

    output_pdf_path = os.path.join(target_save_directory, output_pdf_filename)



    # Fetch default company ID for context data
    default_company_obj = db_manager.get_default_company()
    default_company_id = default_company_obj['company_id'] if default_company_obj else None
    if not default_company_id and file_ext.lower() == '.html': # Only warn if it's an HTML doc where seller info is crucial
         QMessageBox.information(parent_widget, QCoreApplication.translate("utils.generate_pdf", "Avertissement"),
                                QCoreApplication.translate("utils.generate_pdf", "Aucune société par défaut n'est définie. Les détails du vendeur peuvent être manquants."))

    # Get document context data, now including target_language_code
    # Assuming client_info contains 'client_id'
    # The 'company_id' for get_document_context_data is the seller/our company.
    document_context = db_manager.get_document_context_data(
        client_id=client_info['client_id'],
        company_id=default_company_id,
        target_language_code=target_language_code,
        project_id=project_id, # Use the passed project_id
        document_type=document_type_for_context, # Pass the specific document type for context
        additional_context=additional_context if additional_context else {'document_title': file_name}, # Pass additional_context
        app_root_dir=app_root_dir # Pass app_root_dir through
    )

    if file_ext.lower() == '.html':
        # "No Products" Check for proforma invoices, conditional on allow_empty_products
        logging.debug(f"PDF Generation for {file_name}: allow_empty_products = {allow_empty_products}") # NEW LOG
        if not allow_empty_products and ("proforma" in file_name.lower() or "invoice" in file_name.lower()):
            logging.debug(f"PDF Generation for {file_name}: Running product check because allow_empty_products is False.") # NEW LOG
            # The context_builder now only includes products that match the target language.
            # So, we only need to check if the 'products' list in the context is empty.

            if not document_context.get('products'):
                 logging.info(f"PDF Generation for {file_name}: No products in context. Cancelling.") # NEW LOG
                 QMessageBox.information(parent_widget, QCoreApplication.translate("utils.generate_pdf", "Information"),
                                        QCoreApplication.translate("utils.generate_pdf", f"Aucun produit n'est lié à ce client/projet (ou aucun ne correspond à la langue '{target_language_code}'). La génération du PDF pour '{file_name}' est annulée."))
                 return None

            # If document_context.get('products') is not empty here, it means there ARE products for the target language.

        try:
            with open(source_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # HtmlEditor.populate_html_content now uses the enhanced context
            processed_html = HtmlEditor.populate_html_content(html_content, document_context) # Pass the full context

            base_url = QUrl.fromLocalFile(os.path.dirname(source_file_path)).toString()
            pdf_bytes = convert_html_to_pdf(processed_html, base_url=base_url)

            if pdf_bytes:
                with open(output_pdf_path, 'wb') as f_pdf:
                    f_pdf.write(pdf_bytes)
                QMessageBox.information(parent_widget, QCoreApplication.translate("utils.generate_pdf", "Succès PDF"),
                                        QCoreApplication.translate("utils.generate_pdf", "PDF généré avec succès:\n{0}").format(output_pdf_path))
                return output_pdf_path
            else:
                QMessageBox.warning(parent_widget, QCoreApplication.translate("utils.generate_pdf", "Erreur PDF"),
                                    QCoreApplication.translate("utils.generate_pdf", "La conversion HTML en PDF a échoué. Le contenu PDF résultant était vide."))
                return None
        except Exception as e:
            QMessageBox.critical(parent_widget, QCoreApplication.translate("utils.generate_pdf", "Erreur HTML vers PDF"),
                                 QCoreApplication.translate("utils.generate_pdf", "Erreur lors de la génération du PDF à partir du HTML:\n{0}").format(str(e)))
            return None
    elif file_ext.lower() in ['.xlsx', '.docx']:
        QMessageBox.information(parent_widget, QCoreApplication.translate("utils.generate_pdf", "Fonctionnalité non disponible"),
                                QCoreApplication.translate("utils.generate_pdf", "La génération PDF directe pour les fichiers {0} n'est pas supportée.\nVeuillez utiliser la fonction 'Enregistrer sous PDF' ou 'Exporter vers PDF' de l'application correspondante.").format(file_ext.upper()))
        return None
    else:
        QMessageBox.warning(parent_widget, QCoreApplication.translate("utils.generate_pdf", "Type de fichier non supporté"),
                            QCoreApplication.translate("utils.generate_pdf", "La génération PDF n'est pas supportée pour les fichiers de type '{0}'.").format(file_ext))
        return None

# Note: APP_ROOT_DIR is problematic here.
# If utils.py is at the project root, os.path.dirname(os.path.abspath(__file__)) is fine for its own constants.
# But if functions here (like generate_pdf_for_document) need the *application's* root directory (where main.py is, or the sys._MEIPASS dir),
# it must be passed in or imported carefully to avoid circular dependencies if utils itself is imported by main.
# For generate_pdf_for_document, I've added MAIN_APP_ROOT_DIR import as a temporary measure.
# For load_config, it now explicitly takes app_root_dir.
# populate_docx_template does not seem to need APP_ROOT_DIR directly.
# save_config and get_config_file_path/get_config_dir are self-contained.

# --- Password Hashing Utilities ---
from passlib.context import CryptContext

# Setup CryptContext - this should ideally be done once per application
# Using bcrypt as it's specified in requirements.txt (passlib[bcrypt])
# Deprecated algorithms can be added if migrating from older hashes.
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def hash_password(password: str) -> str:
    """Hashes a password using the configured context."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> tuple[bool, str | None]:
    """
    Verifies a plain password against a hashed one and checks if the hash should be updated.

    Returns:
        tuple[bool, str | None]: (is_verified, new_hash_if_needed_or_None)
    """
    try:
        # verify_and_update returns (verified, new_hash_or_None)
        # new_hash_or_None is None if the hash is already in the default format.
        # It's a new hash string if the old hash was valid but used a deprecated scheme.
        verified, new_hash = pwd_context.verify_and_update(plain_password, hashed_password)
        return verified, new_hash
    except Exception as e:
        # Log unexpected errors during verification, e.g., malformed hash, unknown scheme
        logging.error(f"Error verifying password or during hash update check: {e}", exc_info=True)
        return False, None # Return False and no new hash on error

