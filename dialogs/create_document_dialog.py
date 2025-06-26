# -*- coding: utf-8 -*-
import os
import shutil
import logging # Added for logging
from datetime import datetime

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QDialogButtonBox, QMessageBox, QLabel,
    QListWidget, QListWidgetItem, QComboBox, QGroupBox, QWidget, QApplication
)
from PyQt5.QtGui import QIcon, QColor, QDesktopServices # QColor was used for item background (optional)
from PyQt5.QtCore import Qt, QUrl # Qt is used for e.g. Qt.UserRole

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
from PyQt5.QtWidgets import QFormLayout

class CreateDocumentDialog(QDialog):
    # Maps internal type keys to user-friendly names and template_type filters
    DOCUMENT_TYPE_MAPPING = {
        "DEVIS": {"name": "Devis", "template_type_filter": "DEVIS_HTML"},
        "PROFORMA": {"name": "Facture Proforma", "template_type_filter": "PROFORMA_INVOICE_HTML"},
        "ORDER_FORM": {"name": "Bon de Commande", "template_type_filter": "ORDER_FORM_HTML"},
        "DELIVERY_NOTE": {"name": "Note de Livraison", "template_type_filter": "PACKING_LIST_HTML"},
        "SALES_CONTRACT": {"name": "Contrat de Vente", "template_type_filter": "SALES_CONTRACT_HTML"},
        "TECHNICAL_SPECIFICATIONS": {"name": "Spécifications Techniques", "template_type_filter": "TECHNICAL_SPECIFICATIONS_HTML"},
        "WARRANTY_DOCUMENT": {"name": "Document de Garantie", "template_type_filter": "WARRANTY_DOCUMENT_HTML"},
        "COVER_PAGE": {"name": "Page de Garde", "template_type_filter": "COVER_PAGE_HTML"},
        "PRODUCT_IMAGES": {"name": "Images Produits", "template_type_filter": "PRODUCT_IMAGES_HTML"},
        "CONTACT_PAGE": {"name": "Page Contact", "template_type_filter": "CONTACT_PAGE_HTML"},
        # Excel types
        "PROFORMA_EXCEL": {"name": "Facture Proforma (Excel)", "template_type_filter": "PROFORMA_EXCEL"},
        "PACKING_LIST_EXCEL": {"name": "Liste de Colisage (Excel)", "template_type_filter": "PACKING_LIST_EXCEL"},
        "SALES_CONTRACT_EXCEL": {"name": "Contrat de Vente (Excel)", "template_type_filter": "SALES_CONTRACT_EXCEL"},
        "TECHNICAL_SPECIFICATIONS_EXCEL": {"name": "Spécifications Techniques (Excel)", "template_type_filter": "TECHNICAL_SPECIFICATIONS_EXCEL"},
    }

    def __init__(self, client_info, config, current_user_id, parent=None, template_data=None):
        super().__init__(parent)
        self.client_info = client_info
        self.config = config
        self.app_root_dir = config.get("app_root_dir", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.current_user_id = current_user_id
        self.pre_selected_template_id = template_data.get('template_id') if template_data else None

        self.setWindowTitle(self.tr("Générer Document(s) Client via Modèle"))
        self.setMinimumSize(600, 400) # Adjusted size
        self._init_ui()
        if self.pre_selected_template_id:
            self._select_and_load_pre_selected_template()


    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.doc_type_combo = QComboBox()
        self.language_combo = QComboBox()
        self.template_list_widget = QListWidget()
        self.template_list_widget.setSelectionMode(QListWidget.ExtendedSelection) # Allow multiple selections

        form_layout.addRow(self.tr("Type de Document (Filtre):"), self.doc_type_combo)
        form_layout.addRow(self.tr("Langue du Document (Filtre):"), self.language_combo)

        main_layout.addLayout(form_layout)

        main_layout.addWidget(QLabel(self.tr("Modèles Disponibles (sélectionnez un ou plusieurs):")))
        main_layout.addWidget(self.template_list_widget)

        self._load_document_types_and_languages() # Populates combos

        # Connect signals for filtering the template list
        self.doc_type_combo.currentIndexChanged.connect(self._filter_and_load_templates_for_selection)
        self.language_combo.currentIndexChanged.connect(self._filter_and_load_templates_for_selection)

        self._filter_and_load_templates_for_selection() # Initial load

        # Buttons
        button_layout = QHBoxLayout()
        self.view_folder_button = QPushButton(QIcon(":/icons/folder.svg"), self.tr("Voir Dossier Client"))
        self.view_folder_button.clicked.connect(self._handle_view_client_folder)
        button_layout.addWidget(self.view_folder_button)
        button_layout.addStretch(1)

        self.generate_open_button = QPushButton(QIcon(":/icons/file-plus.svg"), self.tr("Générer Sélectionnés"))
        self.generate_open_button.setObjectName("primaryButton")
        self.generate_open_button.clicked.connect(self._handle_generate_selected_and_open)
        button_layout.addWidget(self.generate_open_button)

        main_layout.addLayout(button_layout)

        dialog_button_box = QDialogButtonBox(QDialogButtonBox.Cancel)
        dialog_button_box.rejected.connect(self.reject)
        main_layout.addWidget(dialog_button_box)

    def _load_document_types_and_languages(self):
        # Populate Document Types
        self.doc_type_combo.blockSignals(True)
        self.doc_type_combo.clear()
        self.doc_type_combo.addItem(self.tr("Tous Types"), "ALL") # Add an "All" option
        for key, info in self.DOCUMENT_TYPE_MAPPING.items():
            self.doc_type_combo.addItem(self.tr(info["name"]), info["template_type_filter"]) # Store template_type_filter as data
        self.doc_type_combo.blockSignals(False)

        # Populate Languages
        self.language_combo.blockSignals(True)
        self.language_combo.clear()
        self.language_combo.addItem(self.tr("Toutes Langues"), "ALL") # Add an "All" option

        client_languages = self.client_info.get('selected_languages', [])
        if isinstance(client_languages, str):
            client_languages = [lang.strip() for lang in client_languages.split(',') if lang.strip()]

        # Use all known system languages if client has none or for broader selection
        system_languages = ["fr", "en", "ar", "tr", "pt"] # Define or get from config

        effective_langs_for_combo = sorted(list(set(client_languages + system_languages)))

        for lang_code in effective_langs_for_combo:
            self.language_combo.addItem(lang_code.upper(), lang_code)

        if not effective_langs_for_combo and self.language_combo.count() <= 1: # Count <=1 due to "All"
            self.language_combo.addItem("FR", "fr") # Fallback
        self.language_combo.blockSignals(False)

    def _filter_and_load_templates_for_selection(self):
        self.template_list_widget.clear()

        selected_type_filter = self.doc_type_combo.currentData()
        selected_lang_filter = self.language_combo.currentData()

        filter_params = {'apply_visibility_filter': True}
        if selected_type_filter and selected_type_filter != "ALL":
            filter_params['template_type_filter_list'] = [selected_type_filter]
        if selected_lang_filter and selected_lang_filter != "ALL":
            filter_params['language_code_filter'] = selected_lang_filter

        # Prioritize client-specific templates then global ones
        client_id = self.client_info.get('client_id')

        # Fetch client-specific templates matching filters
        client_specific_templates = []
        if client_id:
            client_filter_params = filter_params.copy()
            client_filter_params['client_id_filter'] = client_id
            client_specific_templates = db_manager.get_all_templates(**client_filter_params) or []

        # Fetch global templates matching filters
        global_filter_params = filter_params.copy()
        global_filter_params['client_id_filter'] = None # Explicitly for global
        global_templates = db_manager.get_all_templates(**global_filter_params) or []

        # Combine and display, prioritizing client-specific and avoiding duplicates if a global was copied to client
        displayed_template_ids = set()

        for template in client_specific_templates:
            item_text = f"{template.get('template_name')} ({template.get('language_code')}) - Client"
            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.UserRole, template.get('template_id'))
            self.template_list_widget.addItem(list_item)
            displayed_template_ids.add(template.get('template_id'))
            if self.pre_selected_template_id and template.get('template_id') == self.pre_selected_template_id:
                list_item.setSelected(True)

        for template in global_templates:
            # Only add global if a client-specific version (by original_template_id or name+type+lang) isn't already there
            # This simple check by ID might not be enough if copies don't share ID.
            # A more robust check might involve name, type, and language.
            # For now, if ID is different, it's considered a different template entry.
            if template.get('template_id') not in displayed_template_ids:
                item_text = f"{template.get('template_name')} ({template.get('language_code')}) - Global"
                list_item = QListWidgetItem(item_text)
                list_item.setData(Qt.UserRole, template.get('template_id'))
                self.template_list_widget.addItem(list_item)
                if self.pre_selected_template_id and template.get('template_id') == self.pre_selected_template_id:
                    list_item.setSelected(True)

        if self.template_list_widget.count() == 0:
            self.template_list_widget.addItem(self.tr("Aucun modèle ne correspond aux filtres."))

    def _select_and_load_pre_selected_template(self):
        # This method tries to set filters to match the pre_selected_template_id
        # and then calls _filter_and_load_templates_for_selection to highlight it.
        if not self.pre_selected_template_id:
            return

        template_details = db_manager.get_template_by_id(self.pre_selected_template_id)
        if not template_details:
            return

        # Set language combo
        lang_code_to_select = template_details.get('language_code')
        if lang_code_to_select:
            for i in range(self.language_combo.count()):
                if self.language_combo.itemData(i) == lang_code_to_select:
                    self.language_combo.setCurrentIndex(i)
                    break

        # Set document type combo
        # This is trickier as DOCUMENT_TYPE_MAPPING maps display names to template_type_filters.
        # We need to find which DOCUMENT_TYPE_MAPPING entry's template_type_filter matches the template's type.
        template_actual_type = template_details.get('template_type') # e.g., PROFORMA_INVOICE_HTML
        if template_actual_type:
            for i in range(self.doc_type_combo.count()):
                combo_data_type_filter = self.doc_type_combo.itemData(i) # This is the template_type_filter
                if combo_data_type_filter == template_actual_type:
                    self.doc_type_combo.setCurrentIndex(i)
                    break

        # Filters are now set, reload the list which should select the item
        self._filter_and_load_templates_for_selection()


    def _get_selected_template_ids_and_lang(self):
        selected_items = self.template_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, self.tr("Sélection Requise"), self.tr("Veuillez sélectionner au moins un modèle à générer."))
            return None, None

        template_ids = [item.data(Qt.UserRole) for item in selected_items]

        # For language, we'll use the language_combo if a specific one is selected.
        # If "All Languages" is selected in combo, each template will use its own language.
        # This part of the logic might need refinement based on desired behavior when multiple templates are chosen.
        # For now, let's assume a single language context if specified, otherwise template's own.
        language_code_from_combo = self.language_combo.currentData()
        if language_code_from_combo == "ALL":
            language_code_from_combo = None # Indicates template should use its own language

        return template_ids, language_code_from_combo

    def _handle_generate_selected_and_open(self):
        selected_template_ids, language_context = self._get_selected_template_ids_and_lang()
        if not selected_template_ids:
            return

        generated_paths = []
        for template_id in selected_template_ids:
            # If language_context is None, _generate_document_from_template_id should use template's own lang.
            # If language_context is set, it overrides the template's language (e.g. for generating a French template in English).
            # This needs to be handled carefully in _generate_document_from_template_id.
            # For now, let's assume _generate_document_from_template_id will primarily use the template's own language
            # and language_context is more for filtering or a future "translate on the fly" feature.
            # So, we'll pass the template's own language for generation.

            template_details = db_manager.get_template_by_id(template_id)
            if not template_details:
                logging.warning(f"Template ID {template_id} not found when generating. Skipping.")
                continue

            actual_generation_language = language_context if language_context else template_details.get('language_code')
            if not actual_generation_language:
                logging.warning(f"Language code for template ID {template_id} could not be determined. Skipping.")
                QMessageBox.warning(self, self.tr("Erreur Langue"), self.tr(f"Impossible de déterminer la langue pour le modèle {template_details.get('template_name')}. Document ignoré."))
                continue

            generated_file_path = self._generate_document_from_template_id(template_id, actual_generation_language)
            if generated_file_path and os.path.exists(generated_file_path):
                generated_paths.append(generated_file_path)
            elif generated_file_path:
                 QMessageBox.warning(self, self.tr("Erreur Fichier Partiel"), self.tr("Le fichier pour le modèle '{0}' semble avoir été généré mais est introuvable : {1}").format(template_details.get('template_name'),generated_file_path))


        if generated_paths:
            if len(generated_paths) == 1:
                try:
                    QDesktopServices.openUrl(QUrl.fromLocalFile(generated_paths[0]))
                except Exception as e:
                    logging.error(f"Error opening file {generated_paths[0]}: {e}", exc_info=True)
                    QMessageBox.warning(self, self.tr("Erreur Ouverture"), self.tr("Impossible d'ouvrir le document généré : {0}").format(str(e)))
            else:
                QMessageBox.information(self, self.tr("Documents Générés"),
                                        self.tr("{0} documents ont été générés. Vous pouvez les trouver dans le dossier client.").format(len(generated_paths)))
                # Optionally open the client folder
                self._handle_view_client_folder()
            self.accept()
        elif selected_template_ids and not generated_paths: # Attempted but all failed
            QMessageBox.warning(self, self.tr("Échec Génération"), self.tr("Aucun document n'a pu être généré avec succès."))


    def _handle_view_client_folder(self):
        client_base_folder = self.client_info.get("base_folder_path")
        if not client_base_folder:
             client_base_folder = self.client_info.get("default_base_folder_path")

        if client_base_folder and os.path.isdir(client_base_folder):
            try:
                QDesktopServices.openUrl(QUrl.fromLocalFile(client_base_folder))
            except Exception as e:
                logging.error(f"Error opening client folder {client_base_folder}: {e}", exc_info=True)
                QMessageBox.warning(self, self.tr("Erreur Ouverture Dossier"), self.tr("Impossible d'ouvrir le dossier client : {0}").format(str(e)))
        else:
            QMessageBox.warning(self, self.tr("Dossier Introuvable"), self.tr("Le dossier de base du client n'est pas configuré ou est invalide."))

    def _generate_document_from_template_id(self, template_id, language_code_for_generation):
        """
        Generates a document using a specific template_id.
        language_code_for_generation specifies the language context for data fetching and notes.
        The template itself has an inherent language.
        """
        logging.info(f"Attempting to generate document from template_id='{template_id}', lang_context='{language_code_for_generation}' for client_id='{self.client_info.get('client_id')}'")

        chosen_template = db_manager.get_template_by_id(template_id)
        if not chosen_template:
            QMessageBox.critical(self, self.tr("Erreur Modèle"), self.tr("Modèle avec ID '{0}' introuvable.").format(template_id))
            return None

        template_base_filename = chosen_template.get('base_file_name')
        # The template's own language is important for finding its file.
        template_inherent_language = chosen_template.get('language_code')
        template_actual_type = chosen_template.get('template_type') # e.g., 'PROFORMA_INVOICE_HTML', 'document_excel'
        template_display_name_for_output = chosen_template.get('template_name', 'Document')


        template_file_on_disk_abs = os.path.join(self.config.get("templates_dir", "templates"), template_inherent_language, template_base_filename)
        if not os.path.exists(template_file_on_disk_abs):
             QMessageBox.warning(self, self.tr("Fichier Modèle Introuvable"), self.tr("Le fichier modèle '{0}' (lang: {1}) est introuvable.").format(template_base_filename, template_inherent_language))
             return None

        # Prepare Context Data
        default_company_obj = db_manager.get_default_company()
        default_company_id = default_company_obj['company_id'] if default_company_obj else None
        if not default_company_id:
            QMessageBox.warning(self, self.tr("Config Erreur"), self.tr("Société par défaut non définie. Certaines informations pourraient manquer."))

        client_id_for_context = self.client_info.get('client_id')
        project_id_for_context_arg = self.client_info.get('project_id')

        # Determine the document_type_for_notes (e.g., 'PROFORMA_INVOICE_HTML') from the template's type
        # This ensures correct notes are fetched based on the actual template type being generated.
        document_type_for_notes_fetch = template_actual_type

        additional_context_for_gen = {
            'document_type': template_actual_type,
            'current_document_type_for_notes': document_type_for_notes_fetch,
        }
        # Add specific context if needed, e.g., for DELIVERY_NOTE as before
        # This needs to map template_actual_type to specific context keys if they differ from the general mapping.
        # Example: if template_actual_type == "PACKING_LIST_HTML" or template_actual_type == "PACKING_LIST_EXCEL":
        #    ... add packing_details context ...

        document_context = db_manager.get_document_context_data(
            client_id=client_id_for_context,
            company_id=default_company_id,
            target_language_code=language_code_for_generation, # Use the context language here
            project_id=project_id_for_context_arg,
            additional_context=additional_context_for_gen
        )
        if not document_context:
            logging.warning(f"Failed to get full document context for template_id {template_id}. Document might be incomplete.")
            document_context = {}

        # Determine Output Filename and Path
        client_base_folder = self.client_info.get("base_folder_path") or self.client_info.get("default_base_folder_path")
        if not client_base_folder or not os.path.isdir(client_base_folder):
            QMessageBox.critical(self, self.tr("Erreur Dossier Client"), self.tr("Dossier client non configuré ou invalide."))
            return None

        # Use a subfolder based on template's display name for organization
        doc_type_name_for_folder = template_display_name_for_output.replace(" ", "_").replace("/", "_")
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_ext = os.path.splitext(template_base_filename)[1]

        output_filename_base = f"{self.client_info.get('client_name', 'Client').replace(' ', '_')}_{doc_type_name_for_folder}_{language_code_for_generation}_{timestamp_str}"
        output_filename = f"{output_filename_base}{original_ext}"

        # Output path uses the language_code_for_generation for the subfolder, not template_inherent_language
        target_doc_folder = os.path.join(client_base_folder, language_code_for_generation, doc_type_name_for_folder)
        os.makedirs(target_doc_folder, exist_ok=True)
        output_file_path = os.path.join(target_doc_folder, output_filename)

        # Generation Logic
        generation_success = False
        try:
            shutil.copy(template_file_on_disk_abs, output_file_path)

            if template_actual_type.endswith('_HTML'): # Assuming convention like PROFORMA_INVOICE_HTML
                with open(output_file_path, 'r', encoding='utf-8') as f: html_content = f.read()
                populated_html = HtmlEditor.populate_html_content(html_content, document_context)
                with open(output_file_path, 'w', encoding='utf-8') as f: f.write(populated_html)
                generation_success = True
            elif template_actual_type.endswith('_EXCEL'): # e.g., PROFORMA_EXCEL
                # Placeholder for Excel processing
                QMessageBox.information(self, "Info", f"La génération Excel pour '{template_display_name_for_output}' n'est pas encore entièrement implémentée. Le modèle a été copié.")
                generation_success = True
            elif template_actual_type.endswith('_WORD') or template_actual_type.endswith('_DOCX'): # e.g., SALES_CONTRACT_DOCX
                populate_docx_template(output_file_path, document_context)
                generation_success = True
            else: # Other types, or if type is just 'document_excel', 'document_word' without _HTML suffix
                if original_ext == '.html':
                     with open(output_file_path, 'r', encoding='utf-8') as f: html_content = f.read()
                     populated_html = HtmlEditor.populate_html_content(html_content, document_context)
                     with open(output_file_path, 'w', encoding='utf-8') as f: f.write(populated_html)
                     generation_success = True
                elif original_ext == '.docx':
                     populate_docx_template(output_file_path, document_context)
                     generation_success = True
                else:
                    logging.info(f"Template type '{template_actual_type}' or extension '{original_ext}' not specifically handled for population. File copied only.")
                    generation_success = True # Copied

        except Exception as e_gen:
            logging.error(f"Error during document generation for {output_filename} from template_id {template_id}: {e_gen}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Génération"), self.tr("Erreur lors de la génération de '{0}':\n{1}").format(output_filename, str(e_gen)))
            return None

        if not generation_success:
            return None

        # Add to ClientDocuments Table
        relative_path_for_db = os.path.relpath(output_file_path, client_base_folder)
        doc_db_data = {
            'client_id': client_id_for_context,
            'project_id': project_id_for_context_arg,
            'order_identifier': document_context.get('order_identifier'),
            'document_name': output_filename,
            'file_name_on_disk': output_filename,
            'file_path_relative': relative_path_for_db,
            'document_type_generated': template_actual_type, # Store the template's specific type
            'source_template_id': template_id,
            'user_id': self.current_user_id,
            'language_code': language_code_for_generation # Language of the generated document content
        }
        try:
            new_doc_id = db_manager.add_client_document(doc_db_data)
            if new_doc_id:
                logging.info(f"Document '{output_filename}' (ID: {new_doc_id}) added to DB for client {client_id_for_context}")
                return output_file_path
            else:
                QMessageBox.warning(self, self.tr("Erreur DB"), self.tr("Document généré mais échec de l'enregistrement en base de données."))
                return None
        except Exception as e_db_add:
            logging.error(f"Error adding document to DB {output_filename}: {e_db_add}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur DB"), self.tr("Erreur lors de l'enregistrement du document en DB:\n{0}").format(str(e_db_add)))
            return None

    # Remove old methods related to template list display
    def has_multiple_purchase_events(self): return False
    def load_templates(self): pass
    def create_documents(self): pass
    # _generate_document is removed as its logic is now in _generate_document_from_template_id
    # _get_selected_generation_params is removed as selection is now from list widget
    # _handle_generate_and_copy_path is removed as we only have one generate button now
