# -*- coding: utf-8 -*-
import os
import smtplib # Keep for type hinting if direct SMTP usage was intended, but EmailSenderService is preferred
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import logging # Added for logging

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QTextEdit,
    QPushButton, QDialogButtonBox, QMessageBox, QComboBox,
    QListWidget, QAbstractItemView, QFileDialog, QLabel
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

import db as db_manager # db_manager will provide access to new CRUDs
from db.cruds.clients.clients_crud import clients_crud_instance
# from db.cruds import templates_crud # templates_crud is not directly used, db_manager.get_template_details_by_id is used

# Import EmailSenderService
from services.email_service import EmailSenderService

from .select_contacts_dialog import SelectContactsDialog
from .select_client_attachment_dialog import SelectClientAttachmentDialog
from .select_utility_attachment_dialog import SelectUtilityAttachmentDialog
import icons_rc

logger = logging.getLogger(__name__)

class SendEmailDialog(QDialog):
    def __init__(self, client_email, config, current_user_id: str, client_id=None, parent=None):
        super().__init__(parent)
        self.client_email = client_email
        self.config = config # Main app config, not SMTP config object
        self.current_user_id = current_user_id
        self.client_id = client_id
        self.client_info = None
        if self.client_id:
            try:
                self.client_info = clients_crud_instance.get_client_by_id(self.client_id)
            except Exception as e:
                logger.error(f"Error fetching client_info in SendEmailDialog: {e}", exc_info=True)
        self.attachments = []
        self.active_template_type = None

        self.setWindowTitle(self.tr("Envoyer un Email"))
        self.setMinimumSize(600, 580) # Increased height slightly for the new combo box
        self.setup_ui()
        self._populate_send_from_combo() # Populate after UI is set up

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        to_layout = QHBoxLayout()
        self.to_edit = QLineEdit(self.client_email)
        to_layout.addWidget(self.to_edit)

        if self.client_id:
            self.select_contacts_btn = QPushButton("👥 " + self.tr("Sélectionner Contacts"))
            self.select_contacts_btn.clicked.connect(self.open_select_contacts_dialog)
            to_layout.addWidget(self.select_contacts_btn)
        form_layout.addRow(self.tr("À:"), to_layout)

        # "Send From" ComboBox
        self.send_from_combo = QComboBox()
        self.send_from_combo.setPlaceholderText(self.tr("Sélectionner le compte expéditeur..."))
        form_layout.addRow(self.tr("De (Compte Expéditeur):"), self.send_from_combo)

        template_selection_layout = QHBoxLayout()
        self.language_combo = QComboBox()
        self.language_combo.setPlaceholderText(self.tr("Langue..."))
        template_selection_layout.addWidget(self.language_combo)
        self.template_combo = QComboBox()
        self.template_combo.setPlaceholderText(self.tr("Sélectionner un modèle..."))
        template_selection_layout.addWidget(self.template_combo)
        form_layout.addRow(self.tr("Modèle d'Email:"), template_selection_layout)

        self.subject_edit = QLineEdit()
        form_layout.addRow(self.tr("Sujet:"), self.subject_edit)
        self.body_edit = QTextEdit()
        self.body_edit.setPlaceholderText(self.tr("Saisissez votre message ici ou sélectionnez un modèle..."))
        form_layout.addRow(self.tr("Corps:"), self.body_edit)
        layout.addLayout(form_layout)

        self.email_template_types = ['EMAIL_BODY_HTML', 'EMAIL_BODY_TXT']
        self.default_company_id = None
        try:
            default_company_obj = db_manager.get_default_company()
            if default_company_obj:
                self.default_company_id = default_company_obj.get('company_id')
        except Exception as e:
            logger.error(f"Error fetching default company ID: {e}", exc_info=True)

        self.language_combo.currentTextChanged.connect(self.load_email_templates)
        self.template_combo.currentIndexChanged.connect(self.on_template_selected)
        self.load_available_languages()
        if self.language_combo.count() > 0:
            self.load_email_templates(self.language_combo.currentText())

        attachment_buttons_layout = QHBoxLayout()
        self.add_attachment_btn = QPushButton("📎 " + self.tr("Ajouter Pièce Jointe (Fichier)"))
        self.add_attachment_btn.clicked.connect(self.add_attachment_from_file_system)
        attachment_buttons_layout.addWidget(self.add_attachment_btn)

        if self.client_info:
            self.add_client_document_btn = QPushButton("📄 " + self.tr("Ajouter Document Client"))
            self.add_client_document_btn.clicked.connect(self.add_attachment_from_client_docs)
            attachment_buttons_layout.addWidget(self.add_client_document_btn)

        self.add_utility_document_btn = QPushButton("📑 " + self.tr("Ajouter Document Utilitaire"))
        self.add_utility_document_btn.clicked.connect(self.add_attachment_from_utility_docs)
        attachment_buttons_layout.addWidget(self.add_utility_document_btn)

        self.remove_attachment_btn = QPushButton("🗑️ " + self.tr("Supprimer Pièce Jointe"))
        self.remove_attachment_btn.clicked.connect(self.remove_attachment)
        attachment_buttons_layout.addWidget(self.remove_attachment_btn)
        layout.addLayout(attachment_buttons_layout)

        self.attachments_list_widget = QListWidget()
        self.attachments_list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(QLabel(self.tr("Pièces jointes:")))
        layout.addWidget(self.attachments_list_widget)

        button_box = QDialogButtonBox()
        send_button = button_box.addButton("Envoyer", QDialogButtonBox.AcceptRole)
        send_button.setText("✉️ " + self.tr("Envoyer"))
        send_button.setObjectName("primaryButton")
        button_box.addButton(QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.send_email_action)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _populate_send_from_combo(self):
        self.send_from_combo.blockSignals(True)
        self.send_from_combo.clear()
        added_config_ids = set()
        selected_an_item = False

        if not db_manager:
            logger.error("db_manager not available in SendEmailDialog._populate_send_from_combo")
            self.send_from_combo.addItem(self.tr("Erreur: DB non accessible"), None)
            self.send_from_combo.setEnabled(False)
            self.send_from_combo.blockSignals(False)
            return

        # 1. User's default assigned SMTP
        if self.current_user_id:
            try:
                user_default_config = db_manager.get_default_smtp_for_user(self.current_user_id)
                if user_default_config and user_default_config.get('smtp_config_id') not in added_config_ids:
                    label = self.tr("Défaut Utilisateur: {0} ({1})").format(
                        user_default_config.get('config_name', 'N/A'),
                        user_default_config.get('sender_email_address', 'N/A')
                    )
                    self.send_from_combo.addItem(label, user_default_config.get('smtp_config_id'))
                    added_config_ids.add(user_default_config.get('smtp_config_id'))
                    self.send_from_combo.setCurrentIndex(self.send_from_combo.count() - 1)
                    selected_an_item = True
            except Exception as e:
                logger.error(f"Error fetching user's default SMTP: {e}", exc_info=True)

            # 2. Other user-assigned SMTP configs
            try:
                user_assignments = db_manager.get_user_smtp_assignments(self.current_user_id)
                for assignment in user_assignments:
                    if assignment.get('smtp_config_id') not in added_config_ids:
                        label = self.tr("Assigné: {0} ({1})").format(
                            assignment.get('config_name', 'N/A'),
                            assignment.get('sender_email_address', 'N/A')
                        )
                        self.send_from_combo.addItem(label, assignment.get('smtp_config_id'))
                        added_config_ids.add(assignment.get('smtp_config_id'))
                        if not selected_an_item:
                             self.send_from_combo.setCurrentIndex(self.send_from_combo.count() - 1)
                             selected_an_item = True
            except Exception as e:
                logger.error(f"Error fetching user's assigned SMTPs: {e}", exc_info=True)

        # 3. Global default SMTP config
        try:
            global_default_config = db_manager.get_default_smtp_config()
            if global_default_config and global_default_config.get('smtp_config_id') not in added_config_ids:
                label = self.tr("Défaut Global: {0} ({1})").format(
                    global_default_config.get('config_name', 'N/A'),
                    global_default_config.get('sender_email_address', 'N/A')
                )
                self.send_from_combo.addItem(label, global_default_config.get('smtp_config_id'))
                # added_config_ids.add(global_default_config.get('smtp_config_id')) # Not strictly needed here if it's the last one
                if not selected_an_item:
                     self.send_from_combo.setCurrentIndex(self.send_from_combo.count() - 1)
                     # selected_an_item = True # Not strictly needed here
        except Exception as e:
            logger.error(f"Error fetching global default SMTP: {e}", exc_info=True)

        if self.send_from_combo.count() == 0:
            self.send_from_combo.addItem(self.tr("Aucune configuration SMTP disponible"), None)
            self.send_from_combo.setEnabled(False)

        self.send_from_combo.blockSignals(False)

    def load_available_languages(self):
        self.language_combo.blockSignals(True)
        self.language_combo.clear()
        available_langs = set()
        try:
            for template_type in self.email_template_types:
                langs = db_manager.get_distinct_languages_for_template_type(template_type) # type: ignore
                if langs:
                    available_langs.update(lang_tuple[0] for lang_tuple in langs if lang_tuple and lang_tuple[0])
        except Exception as e:
            logger.error(f"Error loading available languages for email templates: {e}", exc_info=True)
            available_langs.update(["fr", "en"]) # Fallback

        sorted_langs = sorted(list(available_langs))
        if not sorted_langs: # Ensure there's at least one language if db query fails badly
            sorted_langs = ["fr", "en"]

        self.language_combo.addItems(sorted_langs)
        preferred_lang_set = False
        if self.client_info and self.client_info.get('selected_languages'):
            client_langs_list = self.client_info['selected_languages'] # Should be a list already
            if isinstance(client_langs_list, str): # Parse if it's a string
                client_langs_list = [lang.strip() for lang in client_langs_list.split(',') if lang.strip()]

            if client_langs_list and isinstance(client_langs_list, list):
                first_client_lang = client_langs_list[0]
                if first_client_lang in sorted_langs:
                    self.language_combo.setCurrentText(first_client_lang)
                    preferred_lang_set = True

        if not preferred_lang_set and sorted_langs: # Default to first in list if no client preference matched
            self.language_combo.setCurrentIndex(0)

        self.language_combo.blockSignals(False)
        if self.language_combo.currentText(): # Trigger template load if a language is selected
             self.load_email_templates(self.language_combo.currentText())

    def load_email_templates(self, language_code):
        self.template_combo.blockSignals(True)
        self.template_combo.clear()
        self.template_combo.addItem(self.tr("--- Aucun Modèle ---"), None)
        if not language_code:
            self.template_combo.blockSignals(False)
            self.on_template_selected(0) # Call with index 0 (no template)
            return
        try:
            EMAIL_CATEGORY_ID = 2 # Assuming '2' is for "Modèles Email"
            all_templates_for_lang = db_manager.get_all_templates( # type: ignore
                language_code_filter=language_code,
                category_id_filter=EMAIL_CATEGORY_ID,
                template_type_filter_list=self.email_template_types
            )

            if all_templates_for_lang is None: all_templates_for_lang = []
            all_templates_for_lang.sort(key=lambda x: x.get('template_name', ''))

            for template in all_templates_for_lang:
                self.template_combo.addItem(template['template_name'], template['template_id'])
        except Exception as e:
            logger.error(f"Error loading email templates for lang {language_code}: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur Modèles Email"), self.tr("Impossible de charger les modèles d'email."))
        finally:
            self.template_combo.blockSignals(False)
            self.on_template_selected(self.template_combo.currentIndex())


    def on_template_selected(self, index):
        template_id = self.template_combo.itemData(index)
        self.active_template_type = None # Reset active type
        if template_id is None: # "--- Aucun Modèle ---" selected
            self.body_edit.setPlainText("")
            self.body_edit.setReadOnly(False) # Allow manual editing
            self.subject_edit.setText("") # Clear subject
            return

        try:
            template_details = db_manager.get_template_details_by_id(template_id) # type: ignore
            if not template_details:
                QMessageBox.warning(self, self.tr("Erreur Modèle"), self.tr("Détails du modèle non trouvés."))
                self.body_edit.setPlainText(""); self.body_edit.setReadOnly(False); return

            template_lang = template_details.get('language_code')
            base_file_name = template_details.get('base_file_name') # This is the template content itself for DB stored templates
            template_type = template_details.get('template_type')
            self.active_template_type = template_type # Store the type (HTML/TXT)
            email_subject_template = template_details.get('email_subject_template')

            # For DB stored templates (raw_template_file_data)
            template_content = ""
            if template_details.get('raw_template_file_data'):
                raw_data = template_details['raw_template_file_data']
                if isinstance(raw_data, bytes):
                    template_content = raw_data.decode('utf-8')
                else: # Should be string
                    template_content = str(raw_data)
            elif base_file_name: # Fallback to file system if raw_template_file_data is empty but base_file_name exists
                if not self.config or "templates_dir" not in self.config:
                    QMessageBox.critical(self, self.tr("Erreur Configuration"), self.tr("Le dossier des modèles n'est pas configuré."))
                    return
                template_file_path = os.path.join(self.config["templates_dir"], template_lang, base_file_name)
                if not os.path.exists(template_file_path):
                    QMessageBox.warning(self, self.tr("Erreur Fichier Modèle"), self.tr("Fichier modèle introuvable:\n{0}").format(template_file_path))
                    self.body_edit.setPlainText(""); self.body_edit.setReadOnly(False); return
                with open(template_file_path, 'r', encoding='utf-8') as f: template_content = f.read()
            else:
                QMessageBox.warning(self, self.tr("Erreur Modèle"), self.tr("Contenu du modèle introuvable."))
                self.body_edit.setPlainText(""); self.body_edit.setReadOnly(False); return

            context_data = {}
            if self.client_info and self.client_info.get('client_id'):
                # Ensure get_document_context_data is called correctly
                context_data = db_manager.get_document_context_data( # type: ignore
                    client_id=self.client_info['client_id'],
                    company_id=self.default_company_id, # May be None
                    target_language_code=template_lang,
                    project_id=self.client_info.get('project_id') # May be None
                )
            elif self.default_company_id: # No client, but maybe a default company for seller info
                 company_details = db_manager.get_company_by_id(self.default_company_id) # type: ignore
                 if company_details : context_data['seller'] = company_details

            # Replace placeholders (simple replacement, consider Jinja2 for complex logic)
            populated_body = template_content
            for key, value in context_data.items():
                if isinstance(value, dict): # For nested contexts like client.name
                    for sub_key, sub_value in value.items():
                         placeholder = f"{{{{{key}.{sub_key}}}}}"
                         populated_body = populated_body.replace(placeholder, str(sub_value) if sub_value is not None else "")
                else: # For direct contexts like doc.date
                    placeholder = f"{{{{{key}}}}}"
                    populated_body = populated_body.replace(placeholder, str(value) if value is not None else "")

            if template_type == 'EMAIL_BODY_HTML': self.body_edit.setHtml(populated_body)
            elif template_type == 'EMAIL_BODY_TXT': self.body_edit.setPlainText(populated_body)
            else: self.body_edit.setPlainText(self.tr("Type de modèle non supporté pour l'aperçu."))
            self.body_edit.setReadOnly(True) # Template applied, make read-only

            if email_subject_template:
                populated_subject = email_subject_template
                # Simplified placeholder replacement for subject as well
                for key, value in context_data.items():
                     if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                             placeholder = f"{{{{{key}.{sub_key}}}}}"
                             populated_subject = populated_subject.replace(placeholder, str(sub_value) if sub_value is not None else "")
                     else:
                        placeholder = f"{{{{{key}}}}}"
                        populated_subject = populated_subject.replace(placeholder, str(value) if value is not None else "")
                self.subject_edit.setText(populated_subject)
            else: self.subject_edit.setText("") # Clear subject if template has none
        except Exception as e:
            logger.error(f"Error applying email template (ID: {template_id}): {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Application Modèle"), self.tr("Une erreur est survenue:\n{0}").format(str(e)))
            self.body_edit.setPlainText(""); self.body_edit.setReadOnly(False); self.active_template_type = None


    def open_select_contacts_dialog(self):
        if not self.client_id:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("ID Client non disponible."))
            return
        dialog = SelectContactsDialog(self.client_id, self)
        if dialog.exec_() == QDialog.Accepted:
            selected_emails = dialog.get_selected_emails()
            if selected_emails:
                current_text = self.to_edit.text().strip()
                current_emails = [email.strip() for email in current_text.split(',') if email.strip()]
                new_emails_to_add = [email for email in selected_emails if email not in current_emails]
                if new_emails_to_add:
                    prefix = ", " if current_emails and current_text and not current_text.endswith(',') else ""
                    if not current_text: prefix = ""
                    elif current_text.endswith(','): prefix = " " # Ensure space after comma
                    self.to_edit.setText(current_text + prefix + ", ".join(new_emails_to_add))

    def add_attachment_from_client_docs(self):
        if not self.client_info:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Informations client non disponibles."))
            return
        dialog = SelectClientAttachmentDialog(self.client_info, self)
        if dialog.exec_() == QDialog.Accepted:
            selected_files = dialog.get_selected_files() # List of full paths
            for file_path in selected_files:
                if file_path not in self.attachments:
                    self.attachments.append(file_path)
                    self.attachments_list_widget.addItem(os.path.basename(file_path))

    def add_attachment_from_utility_docs(self):
        dialog = SelectUtilityAttachmentDialog(self.config, self) # Pass main app config
        if dialog.exec_() == QDialog.Accepted:
            selected_files = dialog.get_selected_files() # List of full paths
            for file_path in selected_files:
                if file_path not in self.attachments:
                    self.attachments.append(file_path)
                    self.attachments_list_widget.addItem(os.path.basename(file_path))

    def add_attachment_from_file_system(self):
        files, _ = QFileDialog.getOpenFileNames(self, self.tr("Sélectionner des fichiers à joindre"), "", self.tr("Tous les fichiers (*.*)"))
        if files:
            for file_path in files:
                if file_path not in self.attachments:
                    self.attachments.append(file_path)
                    self.attachments_list_widget.addItem(os.path.basename(file_path))

    def remove_attachment(self):
        selected_items = self.attachments_list_widget.selectedItems()
        if not selected_items: return
        for item in selected_items:
            row = self.attachments_list_widget.row(item)
            self.attachments_list_widget.takeItem(row)
            # Remove from self.attachments by value (path) rather than index if list order changes
            # This assumes filenames are unique enough for this context, or store full paths if needed.
            # For simplicity, if we stored full paths in self.attachments:
            # self.attachments = [att for att in self.attachments if os.path.basename(att) != item.text()]
            # If self.attachments stores full paths and item.text() is just basename, this needs care.
            # Assuming self.attachments stores full paths and items are added with basename.
            # A safer way is to store full path in item's UserRole data if needed.
            # For now, let's assume the index based removal is okay if additions are always at end.
            try:
                # Find the full path based on basename. This is fragile if basenames are not unique.
                path_to_remove = next(p for p in self.attachments if os.path.basename(p) == item.text())
                self.attachments.remove(path_to_remove)
            except StopIteration:
                 logger.warning(f"Could not find attachment {item.text()} in internal list for removal.")
            except ValueError: # Should not happen if StopIteration is caught
                 pass


    def send_email_action(self):
        to_email_str = self.to_edit.text().strip()
        if not to_email_str:
            QMessageBox.warning(self, self.tr("Champ Requis"), self.tr("L'adresse email du destinataire est requise.")); return

        recipients = [email.strip() for email in to_email_str.split(',') if email.strip()]
        if not recipients:
            QMessageBox.warning(self, self.tr("Champ Requis"), self.tr("L'adresse email du destinataire est requise.")); return

        subject = self.subject_edit.text().strip()
        if not subject:
            QMessageBox.warning(self, self.tr("Champ Requis"), self.tr("Le sujet de l'email est requis.")); return

        body_content = self.body_edit.toHtml() if self.active_template_type == 'EMAIL_BODY_HTML' else self.body_edit.toPlainText()

        selected_smtp_config_id = self.send_from_combo.currentData()
        if selected_smtp_config_id is None:
            QMessageBox.warning(self, self.tr("Configuration SMTP Manquante"),
                                self.tr("Veuillez sélectionner un compte expéditeur valide."))
            return

        try:
            # Initialize EmailSenderService with the selected SMTP config ID
            email_service = EmailSenderService(smtp_config_id=selected_smtp_config_id)

            if not email_service.smtp_config: # Check if service initialized correctly
                QMessageBox.critical(self, self.tr("Erreur Configuration SMTP"),
                                     self.tr("Impossible de charger la configuration SMTP sélectionnée. Vérifiez les paramètres."))
                return

            # Prepare context data for placeholder replacement
            # This context can be enhanced with more details as needed
            context_data = {}
            if self.client_info:
                context_data['client'] = self.client_info
                # Add more specific client fields if your templates use them directly, e.g.
                # context_data['client_name'] = self.client_info.get('client_name')
            if self.default_company_id: # Assuming default_company_id is set
                company_details = db_manager.get_company_by_id(self.default_company_id) # type: ignore
                if company_details: context_data['seller'] = company_details

            # For generic placeholders like current date, add them here
            from datetime import datetime
            context_data['doc'] = {'current_date': datetime.now().strftime('%Y-%m-%d')}


            # The EmailSenderService's send_email method now handles placeholder replacement
            success, message = email_service.send_email(
                recipient_email=recipients, # Pass list of recipients
                subject_template=subject, # Subject might also have placeholders
                body_html_content_or_filename=body_content, # Pass the content directly
                context_data=context_data,
                # template_obj is None here as we are not using a full template object from DB in this simplified flow
                attachments=self.attachments
            )

            if success:
                QMessageBox.information(self, self.tr("Email Envoyé"), self.tr("L'email a été envoyé avec succès."))
                self.accept()
            else:
                QMessageBox.critical(self, self.tr("Erreur d'Envoi Email"),
                                     self.tr("Une erreur est survenue lors de l'envoi de l'email:\n{0}").format(message))
        except Exception as e:
            logger.error(f"Fatal error during email sending preparation or execution: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Critique Email"),
                                 self.tr("Une erreur critique est survenue: {0}").format(str(e)))

# Ensure `db_manager` provides the necessary functions like `get_default_smtp_for_user`,
# `get_user_smtp_assignments`, `get_default_smtp_config`, `get_template_details_by_id`, etc.
# These should be available via `import db as db_manager`.
# Also ensure `EmailSenderService` is correctly imported from `services.email_service`.
# Add `import logging` and `logger = logging.getLogger(__name__)` at the top if not present.
# Make sure `current_user_id` is passed to `SendEmailDialog` constructor.
# The `self.config` in `SendEmailDialog` is the main application config, not an SMTP config object.
# `EmailSenderService` is initialized with `smtp_config_id`.
# The `send_email_action` now correctly initializes `EmailSenderService` with the chosen `smtp_config_id`.
# The `recipient_email` parameter in `email_service.send_email` was changed to accept a list.
# `body_html_content_or_filename` in `email_service.send_email` now expects direct content.
# `template_obj` is passed as `None` to `email_service.send_email` since we handle template logic here.
# `subject_template` is passed as the (potentially already populated) subject string.
