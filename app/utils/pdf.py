# utils/pdf.py
import os
import logging
from datetime import datetime

from PyQt5.QtCore import QUrl, QCoreApplication
from PyQt5.QtWidgets import QMessageBox

# Assuming db_manager, html_to_pdf_util, and html_editor are accessible from this new path.
# If they are at the root, direct imports like these should work if PYTHONPATH is set up.
# Otherwise, they might need to be relative or adjusted based on project structure.
from app import db as db_manager
from .html_to_pdf_util import convert_html_to_pdf
# HtmlEditor is imported deferred inside the function.

def generate_pdf_for_document(
    source_file_path: str,
    client_info: dict,
    app_root_dir:str, # app_root_dir is passed for resolving paths
    parent_widget=None,
    target_language_code: str = "fr",
    project_id: int = None,
    additional_context: dict = None,
    document_type_for_context: str = None,
    allow_empty_products: bool = False
) -> str | None:
    """
    Generates a PDF for a given source document (HTML, XLSX, DOCX).
    Uses app_root_dir for resolving paths to resources like default logos if needed.
    Accepts project_id and additional_context to enrich the document context.
    Includes logic to check for product language match for proforma invoices.
    """
    from gui.widgets.html_editor import HtmlEditor # Deferred import

    if not os.path.exists(source_file_path):
        logging.error(f"Source HTML file not found for PDF generation: {source_file_path}")
        QMessageBox.critical(parent_widget, "File Error", f"Source HTML file not found for PDF generation: {source_file_path}")
        return None

    if not client_info or 'client_id' not in client_info:
        QMessageBox.warning(parent_widget, QCoreApplication.translate("utils.generate_pdf", "Erreur Client"),
                            QCoreApplication.translate("utils.generate_pdf", "ID Client manquant. Impossible de générer le PDF."))
        return None

    file_name, file_ext = os.path.splitext(os.path.basename(source_file_path))
    # current_timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S") # Original line for basic output name
    # output_pdf_filename = f"{file_name}_{current_timestamp_str}.pdf" # Original line for basic output name
    # output_pdf_path = os.path.join(os.path.dirname(source_file_path), output_pdf_filename) # Original line for basic output name

    file_name_base_template, _ = os.path.splitext(os.path.basename(source_file_path))

    client_name_for_file = client_info.get('client_name', 'Client').replace(' ', '_').replace('/', '_')
    doc_type_for_file = document_type_for_context if document_type_for_context else file_name_base_template
    doc_type_for_file = doc_type_for_file.replace('_HTML', '').replace('_TEMPLATE', '').replace(' ', '_') # Basic cleanup
    timestamp_for_file = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_pdf_filename = f"{doc_type_for_file}_{client_name_for_file}_{target_language_code}_{timestamp_for_file}.pdf"

    client_base_folder = client_info.get('base_folder_path')
    if not client_base_folder:
        logging.error("Client base_folder_path missing in client_info. Cannot determine PDF save location.")
        QMessageBox.critical(parent_widget, "Erreur Configuration Client", "Dossier de base du client non trouvé.")
        return None

    doc_type_folder_name = doc_type_for_file
    if not doc_type_folder_name or doc_type_folder_name == "template":
        doc_type_folder_name = "DocumentsGeneres"

    target_save_directory = os.path.join(client_base_folder, target_language_code, doc_type_folder_name)
    try:
        os.makedirs(target_save_directory, exist_ok=True)
    except OSError as e:
        logging.error(f"Failed to create target directory {target_save_directory}: {e}")
        QMessageBox.critical(parent_widget, "Erreur Dossier", f"Impossible de créer le dossier de sauvegarde : {target_save_directory}")
        return None

    output_pdf_path = os.path.join(target_save_directory, output_pdf_filename)

    default_company_obj = db_manager.get_default_company()
    default_company_id = default_company_obj['company_id'] if default_company_obj else None
    if not default_company_id and file_ext.lower() == '.html':
         QMessageBox.information(parent_widget, QCoreApplication.translate("utils.generate_pdf", "Avertissement"),
                                QCoreApplication.translate("utils.generate_pdf", "Aucune société par défaut n'est définie. Les détails du vendeur peuvent être manquants."))

    document_context = db_manager.get_document_context_data(
        client_id=client_info['client_id'],
        company_id=default_company_id,
        target_language_code=target_language_code,
        project_id=project_id,
        document_type=document_type_for_context,
        additional_context=additional_context if additional_context else {'document_title': file_name},
        app_root_dir=app_root_dir
    )

    if file_ext.lower() == '.html':
        logging.debug(f"PDF Generation for {file_name}: allow_empty_products = {allow_empty_products}")
        if not allow_empty_products and ("proforma" in file_name.lower() or "invoice" in file_name.lower()):
            logging.debug(f"PDF Generation for {file_name}: Running product check because allow_empty_products is False.")
            if not document_context.get('products'):
                 logging.info(f"PDF Generation for {file_name}: No products in context. Cancelling.")
                 QMessageBox.information(parent_widget, QCoreApplication.translate("utils.generate_pdf", "Information"),
                                        QCoreApplication.translate("utils.generate_pdf", f"Aucun produit n'est lié à ce client/projet (ou aucun ne correspond à la langue '{target_language_code}'). La génération du PDF pour '{file_name}' est annulée."))
                 return None
        try:
            with open(source_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            processed_html = HtmlEditor.populate_html_content(html_content, document_context)
            base_url_path = os.path.dirname(source_file_path)
            # Ensure the base_url is correctly formatted for local file access
            base_url = QUrl.fromLocalFile(base_url_path).toString()
            if not base_url.endswith('/'): # Ensure base_url ends with a slash if it's a directory
                base_url += '/'

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
            logging.error(f"Error during PDF generation from HTML for {source_file_path}: {e}", exc_info=True)
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
