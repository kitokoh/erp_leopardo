# -*- coding: utf-8 -*-
import os
import shutil
import logging # Added for logging
from datetime import datetime

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QDialogButtonBox, QMessageBox, QLabel,
    QListWidget, QListWidgetItem, QComboBox, QGroupBox, QWidget
)
from PyQt5.QtGui import QIcon, QColor # QColor was used for item background (optional)
from PyQt5.QtCore import Qt # Qt is used for e.g. Qt.UserRole

import db as db_manager
# get_template_category_by_name is not directly used anymore, get_all_template_categories is.
# from db.cruds.template_categories_crud import get_template_category_by_name
from db.cruds.template_categories_crud import get_all_template_categories # Import for fetching all categories
# get_setting is no longer used for this purpose.
# from db.cruds.application_settings_crud import get_setting
from html_editor import HtmlEditor
from utils import populate_docx_template
# clients_crud_instance is not used by CreateDocumentDialog
import icons_rc # Import for Qt resource file

class CreateDocumentDialog(QDialog):
    # Maps internal type keys to user-friendly names and template_type filters
    DOCUMENT_TYPE_MAPPING = {
        "DEVIS": {"name": "Devis", "template_type_filter": "DEVIS_HTML"}, # Example, adjust as needed
        "PROFORMA": {"name": "Facture Proforma", "template_type_filter": "PROFORMA_INVOICE_HTML"},
        "ORDER_FORM": {"name": "Bon de Commande", "template_type_filter": "ORDER_FORM_HTML"}, # Assuming such a type exists
        "DELIVERY_NOTE": {"name": "Note de Livraison", "template_type_filter": "PACKING_LIST_HTML"} # Using Packing List as example
    }

    def __init__(self, client_info, config, current_user_id, parent=None, template_data=None):
        super().__init__(parent)
        self.client_info = client_info
        self.config = config
        self.app_root_dir = config.get("app_root_dir", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.current_user_id = current_user_id
        # self.template_data is not used in the new design, but kept for compatibility if constructor is called with it.
        self.template_data = template_data

        self.setWindowTitle(self.tr("Générer Document Client"))
        self.setMinimumSize(500, 250) # Adjusted size
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.doc_type_combo = QComboBox()
        self.language_combo = QComboBox()

        form_layout.addRow(self.tr("Type de Document:"), self.doc_type_combo)
        form_layout.addRow(self.tr("Langue du Document:"), self.language_combo)

        self._load_document_types_and_languages()

        main_layout.addLayout(form_layout)
        main_layout.addStretch(1)

        button_layout = QHBoxLayout()
        self.view_folder_button = QPushButton(QIcon(":/icons/folder.svg"), self.tr("Voir Dossier Client"))
        self.view_folder_button.clicked.connect(self._handle_view_client_folder)
        button_layout.addWidget(self.view_folder_button)
        button_layout.addStretch(1)

        self.generate_open_button = QPushButton(QIcon(":/icons/file-plus.svg"), self.tr("Générer et Ouvrir"))
        self.generate_open_button.setObjectName("primaryButton")
        self.generate_open_button.clicked.connect(self._handle_generate_and_open)
        button_layout.addWidget(self.generate_open_button)

        self.generate_copy_path_button = QPushButton(QIcon(":/icons/copy.svg"), self.tr("Générer et Copier Chemin"))
        self.generate_copy_path_button.clicked.connect(self._handle_generate_and_copy_path)
        button_layout.addWidget(self.generate_copy_path_button)

        main_layout.addLayout(button_layout)

        dialog_button_box = QDialogButtonBox(QDialogButtonBox.Cancel)
        dialog_button_box.rejected.connect(self.reject)
        main_layout.addWidget(dialog_button_box)

    def _load_document_types_and_languages(self):
        # Populate Document Types
        self.doc_type_combo.clear()
        for key, info in self.DOCUMENT_TYPE_MAPPING.items():
            self.doc_type_combo.addItem(self.tr(info["name"]), key) # Store key as data

        # Populate Languages
        self.language_combo.clear()
        client_languages = self.client_info.get('selected_languages', [])
        if isinstance(client_languages, str): # If it's a comma-separated string
            client_languages = [lang.strip() for lang in client_languages.split(',') if lang.strip()]

        available_langs = client_languages if client_languages else ["fr", "en"] # Fallback
        for lang_code in available_langs:
            self.language_combo.addItem(lang_code.upper(), lang_code)

        if not available_langs and self.language_combo.count() == 0: # Ensure at least one language if client has none
            self.language_combo.addItem("FR", "fr")


    def _get_selected_generation_params(self):
        doc_type_key = self.doc_type_combo.currentData()
        language_code = self.language_combo.currentData()

        if not doc_type_key:
            QMessageBox.warning(self, self.tr("Sélection Requise"), self.tr("Veuillez sélectionner un type de document."))
            return None, None
        if not language_code:
            QMessageBox.warning(self, self.tr("Sélection Requise"), self.tr("Veuillez sélectionner une langue."))
            return None, None

        return doc_type_key, language_code

    def _handle_generate_and_open(self):
        doc_type_key, language_code = self._get_selected_generation_params()
        if not doc_type_key or not language_code:
            return

        generated_file_path = self._generate_document(doc_type_key, language_code)
        if generated_file_path and os.path.exists(generated_file_path):
            try:
                QDesktopServices.openUrl(QUrl.fromLocalFile(generated_file_path))
                self.accept() # Close dialog on success
            except Exception as e:
                logging.error(f"Error opening file {generated_file_path}: {e}", exc_info=True)
                QMessageBox.warning(self, self.tr("Erreur Ouverture"), self.tr("Impossible d'ouvrir le document généré : {0}").format(str(e)))
        elif generated_file_path: # Path returned but file doesn't exist (should not happen if _generate_document is robust)
             QMessageBox.warning(self, self.tr("Erreur Fichier"), self.tr("Le fichier document semble avoir été généré mais est introuvable : {0}").format(generated_file_path))


    def _handle_generate_and_copy_path(self):
        doc_type_key, language_code = self._get_selected_generation_params()
        if not doc_type_key or not language_code:
            return

        generated_file_path = self._generate_document(doc_type_key, language_code)
        if generated_file_path and os.path.exists(generated_file_path):
            try:
                QApplication.clipboard().setText(generated_file_path)
                QMessageBox.information(self, self.tr("Chemin Copié"),
                                        self.tr("Le chemin du document généré a été copié dans le presse-papiers:\n{0}").format(generated_file_path))
                # Optionally open the containing folder
                # QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(generated_file_path)))
                self.accept() # Close dialog on success
            except Exception as e:
                logging.error(f"Error copying path for file {generated_file_path}: {e}", exc_info=True)
                QMessageBox.warning(self, self.tr("Erreur Copie"), self.tr("Impossible de copier le chemin du document : {0}").format(str(e)))
        elif generated_file_path:
             QMessageBox.warning(self, self.tr("Erreur Fichier"), self.tr("Le fichier document semble avoir été généré mais est introuvable : {0}").format(generated_file_path))


    def _handle_view_client_folder(self):
        client_base_folder = self.client_info.get("base_folder_path")
        if not client_base_folder:
             client_base_folder = self.client_info.get("default_base_folder_path") # Fallback

        if client_base_folder and os.path.isdir(client_base_folder):
            try:
                QDesktopServices.openUrl(QUrl.fromLocalFile(client_base_folder))
            except Exception as e:
                logging.error(f"Error opening client folder {client_base_folder}: {e}", exc_info=True)
                QMessageBox.warning(self, self.tr("Erreur Ouverture Dossier"), self.tr("Impossible d'ouvrir le dossier client : {0}").format(str(e)))
        else:
            QMessageBox.warning(self, self.tr("Dossier Introuvable"), self.tr("Le dossier de base du client n'est pas configuré ou est invalide."))

    def _generate_document(self, doc_type_key, language_code):
        """
        Handles the logic for generating a document based on type and language.
        This is a placeholder and needs full implementation.
        """
        logging.info(f"Attempting to generate document: type_key='{doc_type_key}', lang='{language_code}' for client_id='{self.client_info.get('client_id')}'")

        doc_type_info = self.DOCUMENT_TYPE_MAPPING.get(doc_type_key)
        if not doc_type_info:
            QMessageBox.critical(self, self.tr("Erreur Type Document"), self.tr("Type de document interne non reconnu : {0}").format(doc_type_key))
            return None

        template_type_filter = doc_type_info["template_type_filter"] # e.g., "DEVIS_HTML"

        # 1. Find the appropriate template_id or template file
        # This requires querying the database for a template matching template_type_filter and language_code,
        # and preferably one that is marked as 'is_default_for_type_lang'.
        # Example placeholder for fetching template:
        try:
            # We need to find a specific template. This implies get_all_templates and then filtering.
            # Or a new DB function like get_default_template_for_type_lang(template_type, lang_code, client_id=None)
            # For now, let's assume we find one:
            templates = db_manager.get_all_templates(
                template_type_filter_list=[template_type_filter],
                language_code_filter=language_code,
                client_id_filter=self.client_info.get('client_id'), # Prioritize client-specific
                apply_visibility_filter=True
            )

            chosen_template = None
            if templates:
                # Prioritize client-specific default, then global default, then any client-specific, then any global
                client_default = next((t for t in templates if t.get('client_id') and t.get('is_default_for_type_lang')), None)
                global_default = next((t for t in templates if not t.get('client_id') and t.get('is_default_for_type_lang')), None)
                any_client_specific = next((t for t in templates if t.get('client_id')), None)
                any_global = next((t for t in templates if not t.get('client_id')), None)

                chosen_template = client_default or global_default or any_client_specific or any_global

            if not chosen_template:
                QMessageBox.warning(self, self.tr("Modèle Introuvable"), self.tr("Aucun modèle par défaut trouvé pour le type '{0}' en langue '{1}'.\n Veuillez vérifier la configuration des modèles.").format(doc_type_info['name'], language_code))
                return None

            template_id = chosen_template.get('template_id')
            template_base_filename = chosen_template.get('base_file_name')
            template_actual_type = chosen_template.get('template_type') # e.g., 'document_html', 'document_excel'

            template_file_on_disk_abs = os.path.join(self.config["templates_dir"], language_code, template_base_filename)
            if not os.path.exists(template_file_on_disk_abs):
                 QMessageBox.warning(self, self.tr("Fichier Modèle Introuvable"), self.tr("Le fichier modèle '{0}' est introuvable.").format(template_base_filename))
                 return None

        except Exception as e_tpl_fetch:
            logging.error(f"Error fetching template for {template_type_filter}/{language_code}: {e_tpl_fetch}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Modèle"), self.tr("Erreur lors de la recherche du modèle : {0}").format(str(e_tpl_fetch)))
            return None

        # 2. Prepare Context Data
        default_company_obj = db_manager.get_default_company()
        default_company_id = default_company_obj['company_id'] if default_company_obj else None
        if not default_company_id:
            QMessageBox.warning(self, self.tr("Config Erreur"), self.tr("Société par défaut non définie."))
            # Allow generation but with potentially missing seller info

        client_id_for_context = self.client_info.get('client_id')
        # project_id might be relevant for some documents. For this dialog, it's client-level generation.
        project_id_for_context_arg = self.client_info.get('project_id') # If client_info might have it

        additional_context_for_gen = {
            'document_type': template_type_filter, # E.g. DEVIS_HTML
            'current_document_type_for_notes': template_type_filter, # For notes fetching
            # Add any other specific context needed for this doc_type_key
        }
        if doc_type_key == "DELIVERY_NOTE": # Example for packing list context
            # Simplified packing list context for demonstration
            linked_products = db_manager.get_products_for_client_or_project(client_id_for_context, project_id=project_id_for_context_arg) or []
            packing_items = [{'product_name_override': p.get('product_name'), 'quantity_description': str(p.get('quantity'))} for p in linked_products]
            additional_context_for_gen['packing_details'] = {'items': packing_items, 'total_packages': len(packing_items)}
            additional_context_for_gen['packing_list_id'] = f"PL-{self.client_info.get('project_identifier', client_id_for_context)}-{datetime.now().strftime('%Y%m%d')}"


        document_context = db_manager.get_document_context_data(
            client_id=client_id_for_context,
            company_id=default_company_id,
            target_language_code=language_code,
            project_id=project_id_for_context_arg,
            additional_context=additional_context_for_gen
        )
        if not document_context:
            logging.warning(f"Failed to get full document context for {doc_type_key}. Document might be incomplete.")
            # Proceed with empty context if necessary, or partial.
            document_context = {}

        # 3. Determine Output Filename and Path
        client_base_folder = self.client_info.get("base_folder_path")
        if not client_base_folder: client_base_folder = self.client_info.get("default_base_folder_path")

        if not client_base_folder or not os.path.isdir(client_base_folder):
            QMessageBox.critical(self, self.tr("Erreur Dossier Client"), self.tr("Dossier client non configuré ou invalide."))
            return None

        # Use a subfolder based on document type for organization
        doc_type_name_for_folder = doc_type_info["name"].replace(" ", "_") # e.g. "Facture_Proforma"
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Extract original extension from template_base_filename
        original_ext = os.path.splitext(template_base_filename)[1] # .html, .xlsx, .docx

        # Output filename: ClientName_DocType_Lang_Timestamp.original_ext
        output_filename_base = f"{self.client_info.get('client_name', 'Client').replace(' ', '_')}_{doc_type_name_for_folder}_{language_code}_{timestamp_str}"
        output_filename = f"{output_filename_base}{original_ext}"

        target_doc_folder = os.path.join(client_base_folder, language_code, doc_type_name_for_folder)
        os.makedirs(target_doc_folder, exist_ok=True)
        output_file_path = os.path.join(target_doc_folder, output_filename)

        # 4. Call Generation Logic (Placeholder)
        generation_success = False
        try:
            shutil.copy(template_file_on_disk_abs, output_file_path) # Start by copying

            if template_actual_type == 'document_html': # Or check extension
                with open(output_file_path, 'r', encoding='utf-8') as f: html_content = f.read()
                populated_html = HtmlEditor.populate_html_content(html_content, document_context)
                with open(output_file_path, 'w', encoding='utf-8') as f: f.write(populated_html)
                generation_success = True
            elif template_actual_type == 'document_excel':
                # Placeholder: excel_processor = ExcelProcessor(output_file_path)
                # excel_processor.populate_template(document_context)
                # generation_success = excel_processor.save()
                QMessageBox.information(self, "Info", f"Excel generation for {doc_type_info['name']} not yet fully implemented. Copied template.")
                generation_success = True # Assume copy is success for now
            elif template_actual_type == 'document_word':
                populate_docx_template(output_file_path, document_context) # Assuming this works
                generation_success = True
            else:
                QMessageBox.warning(self, self.tr("Type Inconnu"), self.tr("Type de modèle '{0}' non géré pour la population automatique.").format(template_actual_type))
                generation_success = True # Copied, but not populated further

        except Exception as e_gen:
            logging.error(f"Error during document generation for {output_filename}: {e_gen}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Génération"), self.tr("Erreur lors de la génération de '{0}':\n{1}").format(output_filename, str(e_gen)))
            return None

        if not generation_success:
            return None

        # 5. Add to ClientDocuments Table
        relative_path_for_db = os.path.relpath(output_file_path, client_base_folder)
        doc_db_data = {
            'client_id': client_id_for_context,
            'project_id': project_id_for_context_arg,
            'order_identifier': document_context.get('order_identifier'), # If context provided it
            'document_name': output_filename,
            'file_name_on_disk': output_filename,
            'file_path_relative': relative_path_for_db,
            'document_type_generated': template_type_filter, # Store the internal filter type
            'source_template_id': template_id,
            'user_id': self.current_user_id,
            'language_code': language_code
        }
        try:
            new_doc_id = db_manager.add_client_document(doc_db_data)
            if new_doc_id:
                logging.info(f"Document '{output_filename}' (ID: {new_doc_id}) added to DB for client {client_id_for_context}")
                return output_file_path
            else:
                QMessageBox.warning(self, self.tr("Erreur DB"), self.tr("Document généré mais échec de l'enregistrement en base de données."))
                # Optionally delete output_file_path if DB record fails
                return None # Or output_file_path if user should still see it
        except Exception as e_db_add:
            logging.error(f"Error adding document to DB {output_filename}: {e_db_add}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur DB"), self.tr("Erreur lors de l'enregistrement du document en DB:\n{0}").format(str(e_db_add)))
            return None

    # Remove old methods related to template list display
    def has_multiple_purchase_events(self): return False # No longer relevant to this dialog's new UI
    def load_templates(self): pass # No longer relevant
    def create_documents(self): pass # Replaced by individual generate buttons
