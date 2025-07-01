# -*- coding: utf-8 -*-
import os
import json
import sys
import logging # Added logging
from datetime import datetime

from PyQt5.QtCore import QStandardPaths, QCoreApplication, QUrl
from PyQt5.QtGui import QDesktopServices # Added for generate_pdf_for_document
from PyQt5.QtWidgets import QMessageBox

# Document import removed, as populate_docx_template was moved to utils/docx.py
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
# This function has been moved to utils/docx.py

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

    file_name, file_ext = os.path.splitext(os.path.basename(source_file_path))
    current_timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S") # Changed to include time
    output_pdf_filename = f"{file_name}_{current_timestamp_str}.pdf" # Changed to use timestamp
    output_pdf_path = os.path.join(os.path.dirname(source_file_path), output_pdf_filename)
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
# These functions have been moved to utils/auth.py

