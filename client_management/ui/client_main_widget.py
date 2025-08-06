# -*- coding: utf-8 -*-
import os
import sys
import logging
from datetime import datetime
import math

from gui.dialogs.carrier_email_dialog import CarrierEmailDialog
from gui.dialogs.referent_details_dialog import ReferentDetailsDialog

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QListWidget, QLineEdit,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QInputDialog, QTabWidget, QGroupBox, QMessageBox, QDialog, QApplication,
    QSizePolicy, QFileDialog # QFileDialog was missing from QtWidget imports
)
from PyQt5.QtGui import QIcon, QDesktopServices, QFont, QColor, QPixmap, QTextCursor
from PyQt5.QtCore import Qt, QUrl, QCoreApplication, QEvent, QStandardPaths
from PyQt5.QtWidgets import QFormLayout
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtGui import QPixmap

import db as db_manager
from db.cruds.users import users_crud
from db.cruds.clients.clients_crud import clients_crud_instance
from gui.dialogs import ClientProductDimensionDialog, AssignPersonnelDialog, AssignTransporterDialog, AssignFreightForwarderDialog, AssignMoneyTransferAgentDialog
from whatsapp.whatsapp_dialog import SendWhatsAppDialog
from db.cruds.misc import money_transfer_agents_crud as mta_crud
from db.cruds.clients import client_order_money_transfer_agents_crud as coma_crud
from db.cruds.projects import projects_crud
from PyQt5.QtWidgets import QCheckBox

MAIN_MODULE_CONTACT_DIALOG = None
MAIN_MODULE_PRODUCT_DIALOG = None
MAIN_MODULE_EDIT_PRODUCT_LINE_DIALOG = None
MAIN_MODULE_CREATE_DOCUMENT_DIALOG = None
MAIN_MODULE_COMPILE_PDF_DIALOG = None
MAIN_MODULE_GENERATE_PDF_FOR_DOCUMENT = None
MAIN_MODULE_CONFIG = None
MAIN_MODULE_DATABASE_NAME = None
MAIN_MODULE_SEND_EMAIL_DIALOG = None
MAIN_MODULE_CLIENT_DOCUMENT_NOTE_DIALOG = None
MAIN_MODULE_SEND_WHATSAPP_DIALOG = None

# Variable globale pour mémoriser le dernier onglet principal sélectionné à travers les instances
LAST_SELECTED_MAIN_TAB_INDEX = 0 # Default to first tab

# It seems ClientController is not directly passed or stored in this widget in the provided code.
# For referent functionality, we'll need access to it.
# Assuming it might be available through db_manager or needs to be passed.
# For now, let's assume a global/singleton or that it's passed via main_controller if this widget is part of a larger structure.
# If this widget is standalone as presented, client_controller needs to be explicitly passed or instantiated.
# Let's assume for now it's part of db_manager for simplicity of this modification.
from client_management.client_controller import ClientController # This would be the ideal import


def _import_main_elements():
    global MAIN_MODULE_CONTACT_DIALOG, MAIN_MODULE_PRODUCT_DIALOG, \
           MAIN_MODULE_EDIT_PRODUCT_LINE_DIALOG, MAIN_MODULE_CREATE_DOCUMENT_DIALOG, \
           MAIN_MODULE_COMPILE_PDF_DIALOG, MAIN_MODULE_GENERATE_PDF_FOR_DOCUMENT, \
           MAIN_MODULE_CONFIG, MAIN_MODULE_DATABASE_NAME, MAIN_MODULE_SEND_EMAIL_DIALOG, \
           MAIN_MODULE_CLIENT_DOCUMENT_NOTE_DIALOG, MAIN_MODULE_SEND_WHATSAPP_DIALOG

    if MAIN_MODULE_CONFIG is None:
        from dialogs import (SendEmailDialog, ContactDialog, ProductDialog, EditProductLineDialog,
                             CreateDocumentDialog, CompilePdfDialog, ClientDocumentNoteDialog)
        from whatsapp.whatsapp_dialog import SendWhatsAppDialog as WhatsAppDialogModule
        from utils import generate_pdf_for_document as utils_generate_pdf_for_document
        from app_setup import CONFIG as APP_CONFIG
        from config import DATABASE_PATH as DB_PATH_CONFIG
        MAIN_MODULE_CONTACT_DIALOG = ContactDialog
        MAIN_MODULE_PRODUCT_DIALOG = ProductDialog
        MAIN_MODULE_EDIT_PRODUCT_LINE_DIALOG = EditProductLineDialog
        MAIN_MODULE_CREATE_DOCUMENT_DIALOG = CreateDocumentDialog
        MAIN_MODULE_COMPILE_PDF_DIALOG = CompilePdfDialog
        MAIN_MODULE_GENERATE_PDF_FOR_DOCUMENT = utils_generate_pdf_for_document
        MAIN_MODULE_CONFIG = APP_CONFIG
        MAIN_MODULE_DATABASE_NAME = DB_PATH_CONFIG
        MAIN_MODULE_SEND_EMAIL_DIALOG = SendEmailDialog
        MAIN_MODULE_CLIENT_DOCUMENT_NOTE_DIALOG = ClientDocumentNoteDialog
        MAIN_MODULE_SEND_WHATSAPP_DIALOG = WhatsAppDialogModule


from auth.permissions import has_permission, \
    P_EDIT_CLIENT_FULL, P_EDIT_CLIENT_BASIC, P_MANAGE_CLIENT_CONTACTS, \
    P_LINK_PRODUCTS_TO_CLIENT, P_MANAGE_CLIENT_DOCUMENTS, P_ARCHIVE_CLIENT, \
    P_MANAGE_CLIENT_ASSIGNMENTS, P_MANAGE_CLIENT_BILLING, P_REFERENTS_MANAGE

from commande_management.commande_widget import CommandeWidget
from client_management.tabs.documents_tab import DocumentsTab, SUPPORTED_LANGUAGES
from client_management.tabs.products_tab import ProductsTab
from client_management.tabs.document_notes_tab import DocumentNotesTab
from client_management.tabs.product_dimensions_tab import ProductDimensionsTab
from client_management.tabs.sav_tab import SAVTab
from client_management.tabs.billing_tab import BillingTab
from client_management.signals import client_management_signals


class ClientMainWidget(QWidget):
    CONTACT_PAGE_LIMIT = 15

    def __init__(self, client_info, config, app_root_dir, notification_manager, current_user_info: dict, client_controller_instance: ClientController, parent=None):
        super().__init__(parent)
        self.current_user_info = current_user_info
        self.current_user_id = self.current_user_info.get('user_id')

        logging.info(f"ClientMainWidget.__init__: INSTANTIATION STARTED for client_id={client_info.get('client_id')}, user: {self.current_user_info.get('username')}")
        self.client_info = client_info
        self.notification_manager = notification_manager # Kept for now for tabs that are not yet refactored

        client_management_signals.client_updated.connect(self.refresh_display)

        _import_main_elements()
        self.config = MAIN_MODULE_CONFIG # Expected to be app_setup.CONFIG
        self.app_root_dir = app_root_dir
        self.DATABASE_NAME = MAIN_MODULE_DATABASE_NAME
        self.client_controller = client_controller_instance

        self.ContactDialog = MAIN_MODULE_CONTACT_DIALOG
        self.ProductDialog = MAIN_MODULE_PRODUCT_DIALOG
        self.EditProductLineDialog = MAIN_MODULE_EDIT_PRODUCT_LINE_DIALOG
        self.CreateDocumentDialog = MAIN_MODULE_CREATE_DOCUMENT_DIALOG
        self.CompilePdfDialog = MAIN_MODULE_COMPILE_PDF_DIALOG
        self.generate_pdf_for_document = MAIN_MODULE_GENERATE_PDF_FOR_DOCUMENT
        self.SendEmailDialog = MAIN_MODULE_SEND_EMAIL_DIALOG
        self.ClientDocumentNoteDialog = MAIN_MODULE_CLIENT_DOCUMENT_NOTE_DIALOG
        self.SendWhatsAppDialog = MAIN_MODULE_SEND_WHATSAPP_DIALOG

        self.is_editing_client = False
        self.edit_widgets = {}
        self.default_company_id = None
        self.current_referent_details = None
        self.is_editing_client = False # Added for edit mode state
        # self.last_selected_main_tab_index is no longer an instance variable for this specific behavior

        try:
            default_company = db_manager.get_default_company()
            if default_company:
                self.default_company_id = default_company.get('company_id')
        except Exception as e:
            print(f"Error fetching default company ID in ClientMainWidget: {e}")

        self.current_contact_offset = 0
        self.total_contacts_count = 0

        logging.info("ClientMainWidget.__init__: Calling self.setup_ui()...")
        self.setup_ui()
        logging.info("ClientMainWidget.__init__: Finished self.setup_ui().")

        if self.client_info and self.client_info.get('client_id') and self.client_controller:
            self.current_referent_details = self.client_controller.get_referent_profile_by_client_id(
                self.client_info.get('client_id'), include_inactive=True
            )
            self._update_referent_status_display()
        else:
            logging.warning("Client info or client_controller not available at end of ClientMainWidget __init__ for referent status.")

        self._apply_permissions()
        logging.info(f"ClientMainWidget.__init__: INSTANTIATION COMPLETED for client_id={self.client_info.get('client_id')}")

    def _show_no_client_selected_state(self):
        self.header_label.setText(self.tr("Aucun Client Sélectionné"))
        if hasattr(self, 'info_container_widget'): self.info_container_widget.setVisible(False)
        if hasattr(self, 'notes_container_widget'): self.notes_container_widget.setVisible(False)
        if hasattr(self, 'tabs_group_box'): self.tabs_group_box.setVisible(False)
        if hasattr(self, 'client_info_group_box'): self.client_info_group_box.setTitle(self.tr("Information Client"))

        self.current_client_details = None # This should be client_info if this widget is for one client
        self.current_referent_details = None
        if hasattr(self, 'referent_status_label'):
            self.referent_status_label.setText("")
            self.referent_status_label.setVisible(False)

        if hasattr(self, 'edit_save_client_btn'): self.edit_save_client_btn.setEnabled(False)
        if hasattr(self, 'send_whatsapp_btn'): self.send_whatsapp_btn.setEnabled(False)
        if hasattr(self, 'archive_client_btn'): self.archive_client_btn.setEnabled(False)
        if hasattr(self, 'manage_referent_btn'): self.manage_referent_btn.setEnabled(False)
        if hasattr(self, 'compile_pdf_btn'): self.compile_pdf_btn.setEnabled(False)


    def _show_client_details_state(self):
        if hasattr(self, 'info_container_widget'): self.info_container_widget.setVisible(True)
        if hasattr(self, 'notes_container_widget') and hasattr(self, 'notes_group_box'):
            self.notes_container_widget.setVisible(self.notes_group_box.isChecked())
        if hasattr(self, 'tabs_group_box'):
            self.tabs_group_box.setVisible(True)
            if hasattr(self, 'tab_widget') and hasattr(self, 'tabs_group_box'):
                 self.tab_widget.setVisible(self.tabs_group_box.isChecked())

        if hasattr(self, 'referent_status_label'): self.referent_status_label.setVisible(True)

        self._apply_permissions()

    def setup_ui(self):
        logging.info("ClientMainWidget.setup_ui: Starting UI setup...")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # The rest of the setup is handled by the section and tab widgets
        self._setup_main_tabs_section(layout)

        logging.info("ClientMainWidget.setup_ui: Starting initial data loading for tabs...")
        try:
            self.load_contacts()
            logging.info("ClientMainWidget.setup_ui: Successfully completed self.load_contacts()")
        except Exception as e:
            logging.error(f"ClientMainWidget.setup_ui: Error during self.load_contacts(): {e}", exc_info=True)

        logging.info("ClientMainWidget.setup_ui: Finished initial data loading for main tabs.")

        if hasattr(self, 'client_info_group_box'):
             self.client_info_group_box.toggled.connect(self._handle_client_info_section_toggled)
        if hasattr(self, 'tabs_group_box'): # This is now "Commandes" group box
             self.tabs_group_box.toggled.connect(self._handle_tabs_section_toggled)

        if hasattr(self, 'notes_edit'): # notes_edit is now in a tab
            self.notes_edit.installEventFilter(self)
        logging.info(f"ClientMainWidget.setup_ui: FULL UI SETUP COMPLETED for client_id={self.client_info.get('client_id')}")

        self._show_client_details_state()

    def open_send_email_dialog(self):
        if not self.client_info or not self.client_info.get("client_id"):
            QMessageBox.warning(self, self.tr("Erreur Client"), self.tr("Informations client non disponibles pour envoyer un email."))
            return

        client_id = self.client_info.get("client_id")
        determined_client_email = self.client_info.get("email") # Default to client's own email field if present

        # Try to get a primary contact's email
        try:
            # Assuming get_contacts_for_client can filter by is_primary or returns data allowing it
            contacts = db_manager.get_contacts_for_client(client_id, limit=5, is_primary=True) # Hypothetical is_primary filter
            if contacts:
                primary_contact_with_email = next((c for c in contacts if c.get('email') and c.get('is_primary_for_client')), None)
                if primary_contact_with_email:
                    determined_client_email = primary_contact_with_email['email']
                else: # Fallback to first contact with email if no primary with email
                    first_contact_with_email = next((c for c in contacts if c.get('email')), None)
                    if first_contact_with_email:
                        determined_client_email = first_contact_with_email['email']

            if not determined_client_email: # If still no email, re-fetch all contacts and try again without primary filter
                all_contacts = db_manager.get_contacts_for_client(client_id, limit=10)
                if all_contacts:
                    first_contact_with_email_any = next((c for c in all_contacts if c.get('email')), None)
                    if first_contact_with_email_any:
                        determined_client_email = first_contact_with_email_any['email']

        except Exception as e:
            logging.error(f"Error fetching contact emails for SendEmailDialog: {e}", exc_info=True)
            # Proceed with client_info.email or None

        if not determined_client_email:
            # Prompt user if no email could be found automatically
            email_text, ok = QInputDialog.getText(self, self.tr("Email Destinataire"),
                                                  self.tr("Aucun email principal trouvé pour ce client. Veuillez saisir l'email du destinataire :"))
            if ok and email_text.strip():
                determined_client_email = email_text.strip()
            else:
                QMessageBox.information(self, self.tr("Annulé"), self.tr("Envoi d'email annulé car aucun destinataire n'a été spécifié."))
                return

        if not hasattr(self, 'SendEmailDialog') or self.SendEmailDialog is None:
            logging.error("SendEmailDialog component not available in ClientMainWidget.")
            QMessageBox.critical(self, self.tr("Erreur Composant"), self.tr("Le composant d'envoi d'email n'est pas chargé."))
            return

        dialog = self.SendEmailDialog(
            client_email=determined_client_email,
            config=self.config, # self.config should be set in __init__
            client_id=client_id,
            parent=self
        )
        dialog.exec_()

    def load_contacts(self):
        try:
            logging.info(f"ClientMainWidget.load_contacts called for client ID: {self.client_info.get('client_id')}")
            if not hasattr(self, 'contacts_table'):
                logging.warning("load_contacts: contacts_table not initialized.")
                return

            self.contacts_table.setRowCount(0)
            client_id = self.client_info.get("client_id")
            if not client_id:
                self.contacts_empty_label.setVisible(True)
                self.contacts_table.setVisible(False)
                self.total_contacts_count = 0
                self.update_contact_pagination_controls()
                return

            contacts_data = db_manager.get_contacts_for_client(
                client_id,
                limit=self.CONTACT_PAGE_LIMIT,
                offset=self.current_contact_offset
            )
            if hasattr(db_manager, 'get_contacts_for_client_count'):
                self.total_contacts_count = db_manager.get_contacts_for_client_count(client_id)
            else:
                self.total_contacts_count = len(contacts_data) if self.current_contact_offset == 0 else self.current_contact_offset + len(contacts_data)
                if len(contacts_data) < self.CONTACT_PAGE_LIMIT and self.current_contact_offset > 0:
                    pass
                elif len(contacts_data) == self.CONTACT_PAGE_LIMIT:
                    logging.warning("Missing get_contacts_for_client_count; pagination might be inaccurate if there are more pages.")

            if not contacts_data:
                self.contacts_empty_label.setVisible(True)
                self.contacts_table.setVisible(False)
            else:
                self.contacts_empty_label.setVisible(False)
                self.contacts_table.setVisible(True)
                self.contacts_table.setRowCount(len(contacts_data))
                for row, contact in enumerate(contacts_data):
                    name_item = QTableWidgetItem(contact.get("contact_name", "N/A"))
                    name_item.setData(Qt.UserRole, contact.get("contact_id"))
                    self.contacts_table.setItem(row, 0, name_item)
                    self.contacts_table.setItem(row, 1, QTableWidgetItem(contact.get("email", "N/A")))
                    self.contacts_table.setItem(row, 2, QTableWidgetItem(contact.get("phone", "N/A")))
                    self.contacts_table.setItem(row, 3, QTableWidgetItem(contact.get("position", "N/A")))
                    primary_text = self.tr("Oui") if contact.get("is_primary_for_client") else self.tr("Non")
                    primary_item = QTableWidgetItem(primary_text)
                    primary_item.setTextAlignment(Qt.AlignCenter)
                    self.contacts_table.setItem(row, 4, primary_item)

                    actions_widget = QWidget()
                    actions_layout = QHBoxLayout(actions_widget)
                    actions_layout.setContentsMargins(5, 0, 5, 0)
                    actions_layout.setSpacing(5)

                    edit_button = QPushButton("✏️")
                    edit_button.setToolTip(self.tr("Modifier ce contact"))
                    edit_button.setProperty("class", "tableActionButton")
                    edit_button.clicked.connect(lambda checked, r=row: self.handle_edit_contact_action(r))
                    actions_layout.addWidget(edit_button)

                    remove_button = QPushButton("🗑️")
                    remove_button.setToolTip(self.tr("Supprimer le lien vers ce contact"))
                    remove_button.setProperty("class", "dangerButtonTable")
                    remove_button.clicked.connect(lambda checked, r=row: self.handle_remove_contact_action(r))
                    actions_layout.addWidget(remove_button)

                    actions_layout.addStretch()
                    actions_widget.setLayout(actions_layout)
                    self.contacts_table.setCellWidget(row, 5, actions_widget)

                self.contacts_table.resizeRowsToContents()
        except Exception as e:
            logging.error(f"Error in load_contacts: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr("Une erreur inattendue est survenue lors du chargement des contacts: {0}").format(str(e)))
            self.contacts_empty_label.setVisible(True)
            self.contacts_table.setVisible(False)
            self.total_contacts_count = 0

        self.update_contact_pagination_controls()
        self._apply_permissions()

    def add_contact(self):
        try:
            client_id = self.client_info.get("client_id")
            if not client_id:
                QMessageBox.warning(self, self.tr("Erreur Client"), self.tr("ID Client non disponible pour ajouter un contact."))
                return

            if not hasattr(self, 'ContactDialog') or self.ContactDialog is None:
                logging.error("ContactDialog component not available in ClientMainWidget.")
                QMessageBox.critical(self, self.tr("Erreur Composant"), self.tr("Le composant d'ajout de contact n'est pas chargé."))
                return

            dialog = self.ContactDialog(manage_link_fields=True, parent=self)
            if dialog.exec_() == QDialog.Accepted:
                contact_core_data = dialog.get_contact_data()
                contact_link_data = dialog.get_link_data()

                if not contact_core_data or not contact_core_data.get('name'):
                    QMessageBox.warning(self, self.tr("Données Incomplètes"), self.tr("Le nom du contact est requis."))
                    return

                existing_contact = None
                if contact_core_data.get('email'):
                    existing_contact = db_manager.get_contact_by_email(contact_core_data['email'])

                contact_id_to_link = None
                if existing_contact:
                    contact_id_to_link = existing_contact['contact_id']
                    logging.info(f"Using existing contact ID: {contact_id_to_link} for client {client_id}")
                else:
                    new_contact_id = db_manager.add_contact(contact_core_data)
                    if new_contact_id:
                        contact_id_to_link = new_contact_id
                        logging.info(f"Created new contact with ID: {new_contact_id} for client {client_id}")
                    else:
                        QMessageBox.critical(self, self.tr("Erreur DB"), self.tr("Impossible de créer le nouveau contact."))
                        return

                if contact_id_to_link:
                    if contact_link_data.get('is_primary', False):
                        db_manager.clear_primary_contact_for_client(client_id, except_contact_id=contact_id_to_link)

                    link_success = db_manager.link_contact_to_client(
                        client_id=client_id,
                        contact_id=contact_id_to_link,
                        is_primary=contact_link_data.get('is_primary', False),
                        can_receive_documents=contact_link_data.get('can_receive_documents', True),
                        role_in_client=contact_link_data.get('role_in_entity', ''),
                        notes=contact_link_data.get('notes', '')
                    )

                    if link_success:
                        client_management_signals.show_notification.emit(self.tr("Succès"), self.tr("Contact ajouté et lié au client avec succès."), 'SUCCESS')
                        self.load_contacts()
                    else:
                        QMessageBox.critical(self, self.tr("Erreur DB"), self.tr("Impossible de lier le contact au client."))
                else:
                    QMessageBox.critical(self, self.tr("Erreur Interne"), self.tr("ID de contact non déterminé pour la liaison."))
        except Exception as e:
            logging.error(f"Error in add_contact: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr("Une erreur inattendue est survenue lors de l'ajout du contact: {0}").format(str(e)))

    def open_compile_pdf_dialog(self):
        if not self.client_info or not self.client_info.get("client_id"):
            QMessageBox.warning(self, self.tr("Erreur Client"), self.tr("Informations client non disponibles pour compiler un PDF."))
            return

        if not hasattr(self, 'CompilePdfDialog') or self.CompilePdfDialog is None:
            logging.error("CompilePdfDialog component not available in ClientMainWidget.")
            QMessageBox.critical(self, self.tr("Erreur Composant"), self.tr("Le composant de compilation PDF n'est pas chargé."))
            return

        dialog = self.CompilePdfDialog(
            client_info=self.client_info,
            config=self.config,
            app_root_dir=self.app_root_dir,
            parent=self
        )
        dialog.exec_()
        # After the dialog closes, you might want to refresh parts of the UI,
        # for example, if the compiled PDF is added to the client's document list.
        # This depends on how CompilePdfDialog signals its outcome or where it saves files.
        # For now, just executing the dialog.
        if hasattr(self, 'documents_tab_widget_ref') and hasattr(self.documents_tab_widget_ref, 'populate_doc_table'):
             self.documents_tab_widget_ref.populate_doc_table()


    def edit_contact(self, row=None, col=None):
        selected_items = self.contacts_table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, self.tr("Sélection Requise"), self.tr("Veuillez sélectionner un contact à modifier."))
            return

        selected_row = selected_items[0].row()
        contact_id_item = self.contacts_table.item(selected_row, 0)
        if not contact_id_item: return # Should not happen
        contact_id = contact_id_item.data(Qt.UserRole)

        if not contact_id:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("ID du contact non trouvé pour la ligne sélectionnée."))
            return

        try:
            # 1. Fetch global contact details
            contact_global_data = db_manager.get_contact_by_id(contact_id)
            if not contact_global_data:
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de charger les détails du contact global (ID: {0}).").format(contact_id))
                return

            # 2. Fetch link-specific details
            # We need a way to get the specific link details for *this client* and *this contact*.
            # Assuming get_contacts_for_client can be filtered or we find it in the list.
            # For simplicity, let's assume the UserRole of the name item in contacts_table might store the full link data,
            # or we refetch it. A dedicated CRUD function `get_client_contact_link(client_id, contact_id)` would be best.
            # Let's simulate fetching it:
            client_contact_link_data = None
            all_client_contacts_for_link_search = db_manager.get_contacts_for_client(self.client_info['client_id']) # This might be inefficient
            if all_client_contacts_for_link_search:
                for link in all_client_contacts_for_link_search:
                    if link.get('contact_id') == contact_id:
                        client_contact_link_data = {
                            'role_in_entity': link.get('role_in_client'), # or role_in_project
                            'is_primary': link.get('is_primary_for_client'),
                            'can_receive_documents': link.get('can_receive_documents'),
                            'link_notes': link.get('link_notes') # Assuming link_notes is the field name
                        }
                        break

            if client_contact_link_data is None:
                 client_contact_link_data = {} # Default if no specific link found (should ideally not happen if contact is in list)


            dialog = self.ContactDialog(
                contact_data=contact_global_data,
                link_data=client_contact_link_data,
                manage_link_fields=True,
                parent=self
            )

            if dialog.exec_() == QDialog.Accepted:
                updated_contact_core_data = dialog.get_contact_data()
                updated_link_data = dialog.get_link_data()

                # Update global contact
                db_manager.update_contact(contact_id, updated_contact_core_data)

                # Update link data
                if updated_link_data:
                    # Prepare payload for update_client_contact_link
                    link_update_payload = {
                        'is_primary': updated_link_data.get('is_primary', False),
                        'can_receive_documents': updated_link_data.get('can_receive_documents', True),
                        'role_in_client': updated_link_data.get('role_in_entity'),
                        'notes': updated_link_data.get('notes')
                    }
                    # Ensure other contacts are not primary if this one is set to primary
                    if link_update_payload['is_primary']:
                        db_manager.clear_primary_contact_for_client(self.client_info['client_id'], except_contact_id=contact_id)

                    # db_manager.update_client_contact_link needs to be created
                    # For now, let's assume it exists and takes these params:
                    # success_link_update = db_manager.update_client_contact_link(self.client_info['client_id'], contact_id, link_update_payload)
                    # As a workaround if update_client_contact_link doesn't exist, we might need to unlink then re-link
                    # This is not ideal. The best is to have an update function.
                    # For now, we'll log what would be updated.
                    logging.info(f"Would update link for client {self.client_info['client_id']}, contact {contact_id} with: {link_update_payload}")
                    # Placeholder for actual update call:
                    # if not success_link_update:
                    #    QMessageBox.warning(self, self.tr("Erreur"), self.tr("Échec de la mise à jour des détails de liaison du contact."))


                client_management_signals.show_notification.emit(self.tr("Succès"), self.tr("Contact mis à jour avec succès."), 'SUCCESS')
                self.load_contacts()
        except Exception as e:
            logging.error(f"Error editing contact (ID: {contact_id}): {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Une erreur est survenue lors de la modification du contact: {0}").format(str(e)))

    def handle_edit_contact_action(self, row):
        """Appelé par le bouton 'Modifier' dans une ligne du tableau des contacts."""
        contact_id_item = self.contacts_table.item(row, 0) # Nom (contient ID en UserRole)
        if contact_id_item:
            contact_id = contact_id_item.data(Qt.UserRole)
            if contact_id:
                self.edit_contact(contact_id_to_edit=contact_id) # Appeler la méthode existante avec l'ID
            else:
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("ID de contact non trouvé pour cette ligne."))
        else:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de récupérer les informations du contact pour cette ligne."))

    def handle_remove_contact_action(self, row):
        """Appelé par le bouton 'Supprimer' dans une ligne du tableau des contacts."""
        contact_id_item = self.contacts_table.item(row, 0) # Nom (contient ID en UserRole)
        if contact_id_item:
            contact_id = contact_id_item.data(Qt.UserRole)
            contact_name = contact_id_item.text()
            if contact_id:
                self.remove_contact(contact_id_to_remove=contact_id, contact_name_for_confirm=contact_name) # Appeler la méthode existante
            else:
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("ID de contact non trouvé pour cette ligne."))
        else:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de récupérer les informations du contact pour cette ligne."))

    def edit_contact(self, row=None, col=None, contact_id_to_edit=None): # Ajout de contact_id_to_edit
        contact_id = contact_id_to_edit
        selected_row = -1

        if contact_id is None: # Comportement existant si appelé par le bouton sous le tableau ou double-clic
            selected_items = self.contacts_table.selectedItems()
            if not selected_items:
                QMessageBox.information(self, self.tr("Sélection Requise"), self.tr("Veuillez sélectionner un contact à modifier."))
                return
            selected_row = selected_items[0].row()
            contact_id_item = self.contacts_table.item(selected_row, 0)
            if not contact_id_item: return
            contact_id = contact_id_item.data(Qt.UserRole)

        if not contact_id:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("ID du contact non trouvé."))
            return

        try:
            contact_global_data = db_manager.get_contact_by_id(contact_id)
            if not contact_global_data:
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de charger les détails du contact global (ID: {0}).").format(contact_id))
                return

            client_contact_link_data = None
            all_client_contacts_for_link_search = db_manager.get_contacts_for_client(self.client_info['client_id'])
            if all_client_contacts_for_link_search:
                for link in all_client_contacts_for_link_search:
                    if link.get('contact_id') == contact_id:
                        client_contact_link_data = {
                            'role_in_entity': link.get('role_in_client'),
                            'is_primary': link.get('is_primary_for_client'),
                            'can_receive_documents': link.get('can_receive_documents'),
                            'link_notes': link.get('link_notes')
                        }
                        break
            if client_contact_link_data is None: client_contact_link_data = {}

            dialog = self.ContactDialog(
                contact_data=contact_global_data,
                link_data=client_contact_link_data,
                manage_link_fields=True,
                parent=self
            )

            if dialog.exec_() == QDialog.Accepted:
                updated_contact_core_data = dialog.get_contact_data()
                updated_link_data = dialog.get_link_data()
                db_manager.update_contact(contact_id, updated_contact_core_data)
                if updated_link_data:
                    link_update_payload = {
                        'is_primary': updated_link_data.get('is_primary', False),
                        'can_receive_documents': updated_link_data.get('can_receive_documents', True),
                        'role_in_client': updated_link_data.get('role_in_entity'),
                        'notes': updated_link_data.get('notes')
                    }
                    if link_update_payload['is_primary']:
                        db_manager.clear_primary_contact_for_client(self.client_info['client_id'], except_contact_id=contact_id)

                    # Assumons qu'une fonction `update_client_contact_link` existe ou sera créée
                    # Pour l'instant, on loguerait ou on ferait un unlink/relink (moins idéal)
                    # db_manager.update_client_contact_link(self.client_info['client_id'], contact_id, link_update_payload)
                    logging.info(f"Mise à jour du lien pour client {self.client_info['client_id']}, contact {contact_id} avec: {link_update_payload} (logique de mise à jour DB à implémenter)")


                self.notification_manager.show(self.tr("Succès"), self.tr("Contact mis à jour avec succès."), type='SUCCESS')
                self.load_contacts()
        except Exception as e:
            logging.error(f"Error editing contact (ID: {contact_id}): {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Une erreur est survenue lors de la modification du contact: {0}").format(str(e)))


    def remove_contact(self, contact_id_to_remove=None, contact_name_for_confirm=None): # Ajout de paramètres
        contact_id = contact_id_to_remove
        contact_name = contact_name_for_confirm

        if contact_id is None: # Comportement existant
            selected_items = self.contacts_table.selectedItems()
            if not selected_items:
                QMessageBox.information(self, self.tr("Sélection Requise"), self.tr("Veuillez sélectionner un contact à délier."))
                return
            selected_row = selected_items[0].row()
            contact_id_item = self.contacts_table.item(selected_row, 0)
            contact_name_item = self.contacts_table.item(selected_row, 0)
            if not contact_id_item: return
            contact_id = contact_id_item.data(Qt.UserRole)
            contact_name = contact_name_item.text() if contact_name_item else "ID: " + str(contact_id)

        if not contact_name and contact_id: # Si appelé avec ID mais sans nom, essayer de le trouver
            for r in range(self.contacts_table.rowCount()):
                if self.contacts_table.item(r, 0).data(Qt.UserRole) == contact_id:
                    contact_name = self.contacts_table.item(r,0).text()
                    break
            if not contact_name: contact_name = f"ID: {contact_id}"


        if not contact_id:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("ID du contact non trouvé."))
            return

        reply = QMessageBox.question(self, self.tr("Confirmer Suppression Lien"),
                                     self.tr("Êtes-vous sûr de vouloir enlever le lien vers le contact '{0}' pour ce client?\nLe contact global ne sera pas supprimé.").format(contact_name),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                # Assume db_manager.unlink_contact_from_client(client_id, contact_id) exists
                # success = db_manager.unlink_contact_from_client(self.client_info['client_id'], contact_id)
                # For now, using a placeholder for the actual unlinking logic
                # This would typically delete the row from the EntityContacts table for this client-contact pair.
                # We need to ensure this function is created in db_manager or the relevant CRUD.

                # Placeholder for actual unlinking:
                entity_contact = db_manager.get_entity_contact_by_client_and_contact(self.client_info['client_id'], contact_id)
                success = False
                if entity_contact:
                    success = db_manager.delete_entity_contact(entity_contact['entity_contact_id'])
                else:
                    QMessageBox.warning(self, self.tr("Erreur"), self.tr("Lien contact-client non trouvé."))

                if success:
                    client_management_signals.show_notification.emit(self.tr("Succès"), self.tr("Lien vers le contact supprimé avec succès."), 'SUCCESS')
                    self.load_contacts()
                else:
                    QMessageBox.warning(self, self.tr("Échec"), self.tr("Impossible de supprimer le lien vers le contact."))
            except Exception as e:
                logging.error(f"Error unlinking contact (ID: {contact_id}) from client (ID: {self.client_info['client_id']}): {e}", exc_info=True)
                QMessageBox.critical(self, self.tr("Erreur"), self.tr("Une erreur est survenue lors de la suppression du lien: {0}").format(str(e)))

    def prev_contact_page(self):
        logging.warning("ClientMainWidget.prev_contact_page: Placeholder method called.")
        if self.current_contact_offset > 0:
            self.current_contact_offset -= self.CONTACT_PAGE_LIMIT
            self.load_contacts() # This will call the basic load_contacts for now

    def next_contact_page(self):
        logging.warning("ClientMainWidget.next_contact_page: Placeholder method called.")
        if (self.current_contact_offset + self.CONTACT_PAGE_LIMIT) < self.total_contacts_count:
            self.current_contact_offset += self.CONTACT_PAGE_LIMIT
            self.load_contacts() # This will call the basic load_contacts for now

    def handle_archive_client(self):
        client_id = self.client_info.get("client_id")
        if not client_id:
            QMessageBox.warning(self, self.tr("Erreur Client"), self.tr("ID Client non disponible."))
            return

        reply = QMessageBox.question(self, self.tr("Archiver Client"),
                                     self.tr("Êtes-vous sûr de vouloir archiver ce client ({0})?\nLe client sera marqué comme archivé et pourra être masqué des listes par défaut.").format(self.client_info.get("client_name", client_id)),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            parent_window = self
            doc_manager_instance = None
            for _ in range(5):
                if hasattr(parent_window, 'set_client_status_archived_slot'):
                    doc_manager_instance = parent_window
                    break
                if hasattr(parent_window, 'parent') and callable(parent_window.parent):
                    parent_window = parent_window.parent()
                    if parent_window is None or not isinstance(parent_window, QWidget):
                        break
                else:
                    break

            if doc_manager_instance:
                logging.info(f"ClientMainWidget: Demande d'archivage pour client ID {client_id} via parent.")
                doc_manager_instance.set_client_status_archived_slot(client_id)
                 # After archiving, this specific ClientMainWidget instance might become outdated or be closed.
                 # The parent (ClientDashboardWidget) should handle refreshing the client list and UI.
            else:
                QMessageBox.warning(self, self.tr("Erreur Action"), self.tr("Impossible de trouver la fonction d'archivage. L'action n'a pas pu être complétée."))
                logging.error("ClientMainWidget: La méthode set_client_status_archived_slot n'a pas été trouvée dans la hiérarchie parente.")

    def _apply_permissions(self):
        role_name = self.current_user_info.get('role_name') if self.current_user_info else None
        if not role_name:
            logging.warning("ClientMainWidget._apply_permissions: No role_name found, disabling most actions.")
            can_edit_full = False
            can_edit_basic = False
            can_manage_contacts = False
            can_link_products = False
            can_manage_documents = False
            can_manage_assignments = False
            can_manage_billing = False
            can_archive_client = False
            can_manage_referents = False
        else:
            can_edit_full = has_permission(role_name, P_EDIT_CLIENT_FULL)
            can_edit_basic = has_permission(role_name, P_EDIT_CLIENT_BASIC)
            can_manage_contacts = has_permission(role_name, P_MANAGE_CLIENT_CONTACTS)
            can_link_products = has_permission(role_name, P_LINK_PRODUCTS_TO_CLIENT)
            can_manage_documents = has_permission(role_name, P_MANAGE_CLIENT_DOCUMENTS)
            can_archive_client = has_permission(role_name, P_ARCHIVE_CLIENT)
            can_manage_assignments = has_permission(role_name, P_MANAGE_CLIENT_ASSIGNMENTS)
            can_manage_billing = has_permission(role_name, P_MANAGE_CLIENT_BILLING)
            can_manage_referents = has_permission(role_name, P_REFERENTS_MANAGE)

        # Define is_client_selected early for broad use in this method
        is_client_selected = self.client_info is not None and self.client_info.get('client_id') is not None

        if hasattr(self, 'compile_pdf_btn'):
             self.compile_pdf_btn.setEnabled(can_manage_documents)
        if hasattr(self, 'edit_save_client_btn'):
            self.edit_save_client_btn.setEnabled(can_edit_full or can_edit_basic)
        if hasattr(self, 'send_whatsapp_btn'):
            self.send_whatsapp_btn.setEnabled(can_manage_contacts)
        if hasattr(self, 'archive_client_btn'):
            self.archive_client_btn.setEnabled(can_archive_client)
        if hasattr(self, 'manage_referent_btn'):
            is_client_selected = self.client_info is not None and self.client_info.get('client_id') is not None
            self.manage_referent_btn.setEnabled(can_manage_referents and is_client_selected)

        if hasattr(self, 'generate_referents_report_btn'):
            # Assuming P_REFERENTS_MANAGE also covers viewing/generating reports, or use a new permission
            self.generate_referents_report_btn.setEnabled(can_manage_referents and is_client_selected)

        if hasattr(self, 'status_combo'):
            self.status_combo.setEnabled(can_edit_full or can_edit_basic)
        if hasattr(self, 'notes_edit'):
            self.notes_edit.setReadOnly(not (can_edit_full or can_edit_basic))
        if hasattr(self, 'documents_tab_widget_ref') and self.documents_tab_widget_ref:
            self.documents_tab_widget_ref.apply_permissions_to_tab(can_manage_documents)
        if hasattr(self, 'add_contact_btn'):
            self.add_contact_btn.setEnabled(can_manage_contacts)
        if hasattr(self, 'edit_contact_btn'):
            self.edit_contact_btn.setEnabled(can_manage_contacts)
        if hasattr(self, 'remove_contact_btn'):
            self.remove_contact_btn.setEnabled(can_manage_contacts)
        if hasattr(self, 'products_tab_widget_ref') and self.products_tab_widget_ref:
            self.products_tab_widget_ref.apply_permissions_to_tab(can_link_products)
        if hasattr(self, 'document_notes_tab_widget_ref') and self.document_notes_tab_widget_ref:
            self.document_notes_tab_widget_ref.apply_permissions_to_tab(can_manage_documents)
        if hasattr(self, 'product_dimensions_tab_widget_ref') and self.product_dimensions_tab_widget_ref:
            self.product_dimensions_tab_widget_ref.apply_permissions_to_tab(can_link_products)

        if hasattr(self, 'add_assigned_vendor_btn'): self.add_assigned_vendor_btn.setEnabled(can_manage_assignments)
        if hasattr(self, 'remove_assigned_vendor_btn') and hasattr(self, 'assigned_vendors_table'): self.remove_assigned_vendor_btn.setEnabled(can_manage_assignments and bool(self.assigned_vendors_table.selectedItems()))
        if hasattr(self, 'add_assigned_technician_btn'): self.add_assigned_technician_btn.setEnabled(can_manage_assignments)
        if hasattr(self, 'remove_assigned_technician_btn') and hasattr(self, 'assigned_technicians_table'): self.remove_assigned_technician_btn.setEnabled(can_manage_assignments and bool(self.assigned_technicians_table.selectedItems()))
        if hasattr(self, 'add_assigned_transporter_btn'): self.add_assigned_transporter_btn.setEnabled(can_manage_assignments)
        if hasattr(self, 'remove_assigned_transporter_btn') and hasattr(self, 'assigned_transporters_table'): self.remove_assigned_transporter_btn.setEnabled(can_manage_assignments and bool(self.assigned_transporters_table.selectedItems()))
        if hasattr(self, 'add_assigned_forwarder_btn'): self.add_assigned_forwarder_btn.setEnabled(can_manage_assignments)
        if hasattr(self, 'remove_assigned_forwarder_btn') and hasattr(self, 'assigned_forwarders_table'): self.remove_assigned_forwarder_btn.setEnabled(can_manage_assignments and bool(self.assigned_forwarders_table.selectedItems()))
        if hasattr(self, 'add_assigned_mta_btn') and hasattr(self, 'mta_project_selector_combo'): self.add_assigned_mta_btn.setEnabled(can_manage_assignments and self.mta_project_selector_combo.currentData() is not None)
        if hasattr(self, 'remove_assigned_mta_btn') and hasattr(self, 'assigned_mta_table'): self.remove_assigned_mta_btn.setEnabled(can_manage_assignments and bool(self.assigned_mta_table.selectedItems()))

        if hasattr(self, 'billing_tab_widget_ref') and self.billing_tab_widget_ref:
            self.billing_tab_widget_ref.apply_permissions_to_tab()

        logging.info(f"ClientMainWidget permissions applied for role: {role_name}")

    def _update_referent_status_display(self):
        if not hasattr(self, 'referent_status_label') or not hasattr(self, 'manage_referent_btn'):
            logging.warning("_update_referent_status_display called before UI elements are ready.")
            return

        if self.current_referent_details:
            if self.current_referent_details.get('is_active'):
                self.referent_status_label.setText("⭐ Référent Actif")
                self.referent_status_label.setStyleSheet("font-style: italic; color: green; font-weight: bold; margin-left: 10px;")
            else:
                self.referent_status_label.setText("Référent Inactif")
                self.referent_status_label.setStyleSheet("font-style: italic; color: orange; margin-left: 10px;")
            self.manage_referent_btn.setText(self.tr("Modifier Référent"))
        else:
            self.referent_status_label.setText("")
            self.manage_referent_btn.setText(self.tr("Devenir Référent"))
        self.referent_status_label.setVisible(True)

    def manage_referent_status_for_selected_client(self):
        if not self.client_info or not self.client_info.get('client_id'):
            QMessageBox.warning(self, self.tr("Aucun Client Sélectionné"), self.tr("Les informations du client ne sont pas disponibles."))
            return

        role_name = self.current_user_info.get('role_name') if self.current_user_info else None
        if not has_permission(role_name, P_REFERENTS_MANAGE):
            client_management_signals.show_notification.emit(self.tr("Accès Refusé"), self.tr("Vous n'avez pas la permission de gérer les référents."), 'ERROR')
            return

        client_id = self.client_info.get('client_id')
        client_name = self.client_info.get('client_name', 'N/A')

        if not self.client_controller:
            QMessageBox.critical(self, self.tr("Erreur Interne"), self.tr("Le contrôleur client n'est pas disponible."))
            logging.error("ClientMainWidget: client_controller is not set for manage_referent_status.")
            return

        # Refresh current_referent_details before opening dialog
        self.current_referent_details = self.client_controller.get_referent_profile_by_client_id(client_id, include_inactive=True)

        dialog = ReferentDetailsDialog(
            client_id=client_id,
            client_name=client_name,
            controller=self.client_controller,
            referent_data=self.current_referent_details,
            current_user_id=self.current_user_id,
            parent=self
        )
        if dialog.exec_() == QDialog.Accepted:
            self.current_referent_details = self.client_controller.get_referent_profile_by_client_id(client_id, include_inactive=True)
            self._update_referent_status_display()
            client_management_signals.show_notification.emit(self.tr("Statut Référent"), self.tr("Le statut de référent a été mis à jour."), 'SUCCESS')
            if hasattr(self.parent(), 'load_clients_data'):
                try:
                    # This assumes ClientMainWidget is part of a larger dashboard (ClientDashboardWidget)
                    # that has a load_clients_data method to refresh the main list.
                    # If ClientMainWidget is standalone for a single client, this refresh might not be needed
                    # or would apply differently.
                    # For now, assuming it's part of a dashboard context.
                    # The ClientDashboardWidget's on_client_selected would then re-instantiate ClientMainWidget
                    # with updated client_info if the main list item text changes (e.g. due to referent status indicator).
                    # This might be overly complex. A simpler approach is to just update the current view.
                    # The parent refresh is more if the list view itself needs to change.
                    # For now, local refresh of status is handled by _update_referent_status_display.
                    pass
                except Exception as e_refresh:
                    logging.error(f"Error trying to refresh parent client list: {e_refresh}", exc_info=True)
        else:
            logging.info(f"Manage referent status dialog cancelled for client {client_id}.")



    def _setup_main_tabs_section(self, main_layout):
        global LAST_SELECTED_MAIN_TAB_INDEX
        try:
            logging.info("ClientMainWidget.setup_ui: Starting setup for Main Tabs Section...")
            self.tabs_group_box = QGroupBox(self.tr("Dossier Client"))
            self.tabs_group_box.setCheckable(True)
            tabs_group_layout = QVBoxLayout(self.tabs_group_box)
            self.tab_widget = QTabWidget()
            tabs_group_layout.addWidget(self.tab_widget)
            self.tabs_group_box.setChecked(True)
            main_layout.addWidget(self.tabs_group_box)

            self.apercu_tab_widget = QWidget()
            apercu_layout = QVBoxLayout(self.apercu_tab_widget)
            apercu_label = QLabel(self.tr("Contenu de l'aperçu global du client et de ses commandes.\n(Détails à implémenter)"))
            apercu_label.setAlignment(Qt.AlignCenter)
            apercu_layout.addWidget(apercu_label)

            self.commandes_content_widget = CommandeWidget(
                client_info=self.client_info,
                current_user_info=self.current_user_info,
                parent=self
            )
            self.tab_widget.addTab(self.commandes_content_widget, self.tr("Commandes"))

            self.documents_tab_widget_ref = DocumentsTab(
                client_info=self.client_info,
                config=self.config,
                app_root_dir=self.app_root_dir,
                notification_manager=self.notification_manager,
                current_user_info=self.current_user_info,
                main_module_create_document_dialog=self.CreateDocumentDialog,
                main_module_compile_pdf_dialog=self.CompilePdfDialog,
                main_module_generate_pdf_for_document=self.generate_pdf_for_document,
                parent_widget=self
            )
            self.tab_widget.addTab(self.documents_tab_widget_ref, self.tr("Documents"))

            self.products_tab_widget_ref = ProductsTab(
                client_info=self.client_info,
                config=self.config,
                notification_manager=self.notification_manager,
                current_user_info=self.current_user_info,
                main_module_product_dialog=self.ProductDialog,
                main_module_edit_product_line_dialog=self.EditProductLineDialog,
                parent_widget=self
            )
            self.tab_widget.addTab(self.products_tab_widget_ref, self.tr("Produits"))

            self.document_notes_tab_widget_ref = DocumentNotesTab(
                client_info=self.client_info,
                current_user_info=self.current_user_info,
                notification_manager=self.notification_manager,
                main_module_client_document_note_dialog=self.ClientDocumentNoteDialog,
                parent_widget=self
            )
            self.tab_widget.addTab(self.document_notes_tab_widget_ref, self.tr("Notes de Document"))

            self.product_dimensions_tab_widget_ref = ProductDimensionsTab(
                client_info=self.client_info,
                app_root_dir=self.app_root_dir,
                main_module_client_product_dimension_dialog=ClientProductDimensionDialog,
                parent_widget=self
            )
            self.tab_widget.addTab(self.product_dimensions_tab_widget_ref, self.tr("Dimensions Produit (Global)"))

            self.sav_tab_widget_ref = SAVTab(
                client_info=self.client_info,
                current_user_info=self.current_user_info,
                notification_manager=self.notification_manager,
                parent_widget=self
            )
            self.tab_widget.addTab(self.sav_tab_widget_ref, self.tr("SAV"))

            self.billing_tab_widget_ref = BillingTab(
                client_info=self.client_info,
                current_user_info=self.current_user_info,
                notification_manager=self.notification_manager,
                config=self.config,
                parent_widget=self
            )
            self.tab_widget.addTab(self.billing_tab_widget_ref, "💳 " + self.tr("Billing"))

            if hasattr(self, 'commandes_content_widget') and self.commandes_content_widget is not None:
                commandes_tab_index = -1
                for i in range(self.tab_widget.count()):
                    if self.tab_widget.widget(i) == self.commandes_content_widget:
                        commandes_tab_index = i
                        break

                if LAST_SELECTED_MAIN_TAB_INDEX is not None and 0 <= LAST_SELECTED_MAIN_TAB_INDEX < self.tab_widget.count():
                    self.tab_widget.setCurrentIndex(LAST_SELECTED_MAIN_TAB_INDEX)
                elif commandes_tab_index != -1:
                    self.tab_widget.setCurrentIndex(commandes_tab_index)
                    LAST_SELECTED_MAIN_TAB_INDEX = commandes_tab_index
                elif self.tab_widget.count() > 0:
                    self.tab_widget.setCurrentIndex(0)
                    LAST_SELECTED_MAIN_TAB_INDEX = 0

            else:
                if LAST_SELECTED_MAIN_TAB_INDEX is not None and 0 <= LAST_SELECTED_MAIN_TAB_INDEX < self.tab_widget.count():
                    self.tab_widget.setCurrentIndex(LAST_SELECTED_MAIN_TAB_INDEX)
                elif self.tab_widget.count() > 0:
                    self.tab_widget.setCurrentIndex(0)
                    LAST_SELECTED_MAIN_TAB_INDEX = 0

            self.tab_widget.currentChanged.connect(self._on_main_tab_changed)

        except Exception as e:
            logging.error(f"Error in _setup_main_tabs_section: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur UI"), self.tr("Erreur initialisation conteneur onglets principaux:\n{0}").format(str(e)))

    def _on_main_tab_changed(self, index):
        """Slot to capture the current main tab index when changed by the user."""
        global LAST_SELECTED_MAIN_TAB_INDEX # S'assurer que la déclaration global est ici aussi

        if 0 <= index < self.tab_widget.count():
            LAST_SELECTED_MAIN_TAB_INDEX = index
            logging.debug(f"ClientMainWidget: Global LAST_SELECTED_MAIN_TAB_INDEX updated to {index} ({self.tab_widget.tabText(index)})")
        else:
            logging.warning(f"ClientMainWidget: _on_main_tab_changed received invalid index {index}, global not updated.")

    def handle_create_new_version_clicked(self, old_document_id, source_template_id):
        if not self.client_info or not self.client_info.get('client_id'):
            QMessageBox.warning(self, self.tr("Erreur Client"), self.tr("Informations client non disponibles."))
            return
        if not old_document_id or not source_template_id:
            QMessageBox.warning(self, self.tr("Données Manquantes"), self.tr("ID du document original ou ID du modèle source manquant."))
            return
        logging.info(f"Creating new version for old_doc_id: {old_document_id}, using source_template_id: {source_template_id}")
        if not hasattr(self, 'CreateDocumentDialog') or self.CreateDocumentDialog is None:
            logging.error("CreateDocumentDialog is not available in ClientMainWidget for versioning.")
            QMessageBox.critical(self, self.tr("Erreur Composant"), self.tr("Le composant de création de document n'est pas chargé."))
            return
        dialog = self.CreateDocumentDialog(
            client_info=self.client_info,
            config=self.config,
            current_user_id=self.current_user_id,
            parent=self,
            template_data={'template_id': source_template_id},
            old_document_id_to_version=old_document_id
        )
        if dialog.exec_() == QDialog.Accepted:
            self.populate_doc_table()
            client_management_signals.show_notification.emit(
                self.tr("Nouvelle Version Créée"),
                self.tr("Une nouvelle version du document a été créée avec succès."),
                'SUCCESS'
            )

    def delete_client_document_entry(self, document_id, file_path):
        if not document_id:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("ID du document manquant."))
            return
        file_display_name = os.path.basename(file_path) if file_path else self.tr("Inconnu")
        reply = QMessageBox.question(self, self.tr("Confirmer Suppression"),
                                     self.tr("Êtes-vous sûr de vouloir supprimer définitivement ce document (ID: {0})?\nLe fichier '{1}' sera également supprimé du disque.").format(document_id, file_display_name),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                db_deleted = db_manager.delete_client_document(document_id)
                if db_deleted:
                    logging.info(f"Document ID {document_id} deleted from database.")
                    if file_path and os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            logging.info(f"File {file_path} deleted from disk.")
                            client_management_signals.show_notification.emit(self.tr("Succès"), self.tr("Document et fichier supprimés avec succès."), 'SUCCESS')
                        except OSError as e_file:
                            logging.error(f"Error deleting file {file_path}: {e_file}", exc_info=True)
                            client_management_signals.show_notification.emit(self.tr("Erreur Fichier"), self.tr("Document supprimé de la base de données, mais échec de la suppression du fichier:\n{0}").format(str(e_file)), 'ERROR')
                    else:
                        logging.warning(f"File path not provided or file does not exist for document ID {document_id}: {file_path}. DB entry deleted.")
                        client_management_signals.show_notification.emit(self.tr("Succès (Partiel)"), self.tr("Entrée de document supprimée de la base de données. Fichier non trouvé ou chemin non spécifié."), 'WARNING')
                else:
                    client_management_signals.show_notification.emit(self.tr("Erreur DB"), self.tr("Impossible de supprimer l'entrée du document de la base de données (ID: {0}). Vérifiez les logs.").format(document_id), 'ERROR')
            except Exception as e:
                logging.error(f"Error in delete_client_document_entry for doc ID {document_id}: {e}", exc_info=True)
                client_management_signals.show_notification.emit(self.tr("Erreur Suppression"), self.tr("Une erreur inattendue est survenue:\n{0}").format(str(e)), 'CRITICAL')
            finally:
                self.populate_doc_table()

    def _handle_edit_pdf_action(self, file_path, document_id):
        if file_path and os.path.exists(file_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
        # The following line seems out of place and was causing an error because 'layout' is not defined in this scope.
        # layout.setContentsMargins(15, 15, 15, 15)
        # layout.setSpacing(15)
        else:
            QMessageBox.warning(self, self.tr("Fichier Introuvable"),
                                self.tr("Le fichier PDF spécifié est introuvable ou le chemin est invalide:\n{0}").format(file_path))


    def open_send_whatsapp_dialog(self):
       client_uuid = self.client_info.get("client_id")
       client_name = self.client_info.get("client_name", "")
       primary_phone = ""
       fallback_phone = ""
       if not client_uuid:
           QMessageBox.warning(self, self.tr("Client Error"), self.tr("Client ID not available."))
           return
       try:
           contacts = db_manager.get_contacts_for_client(client_uuid, limit=10, offset=0)
           if contacts:
               for contact in contacts:
                   if contact.get('phone'):
                       if not fallback_phone:
                           fallback_phone = contact['phone']
                       if contact.get('is_primary_for_client'):
                           primary_phone = contact['phone']
                           break
               selected_phone = primary_phone if primary_phone else fallback_phone
               if selected_phone:
                   if not hasattr(self, 'SendWhatsAppDialog') or self.SendWhatsAppDialog is None:
                       try:
                           from whatsapp.whatsapp_dialog import SendWhatsAppDialog
                           self.SendWhatsAppDialog = SendWhatsAppDialog
                       except ImportError:
                           QMessageBox.critical(self, self.tr("Import Error"), self.tr("Could not load the SendWhatsAppDialog component."))
                           return
                   dialog = self.SendWhatsAppDialog(phone_number=selected_phone, client_name=client_name, parent=self)
                   dialog.exec_()
               else:
                   QMessageBox.information(self, self.tr("No Phone Number"), self.tr("No phone number found for this client's contacts."))
           else:
               QMessageBox.information(self, self.tr("No Contacts"), self.tr("No contacts found for this client."))
       except Exception as e:
           QMessageBox.critical(self, self.tr("Error Fetching Contacts"), self.tr("Could not retrieve contact information: {0}").format(str(e)))

    def _handle_client_info_section_toggled(self, checked):
        self.info_container_widget.setVisible(checked)
        if checked:
            self.notes_group_box.setChecked(False)
            self.tabs_group_box.setChecked(False)

    def _handle_notes_section_toggled(self, checked):
        self.notes_container_widget.setVisible(checked)
        if checked:
            self.client_info_group_box.setChecked(False)
            self.tabs_group_box.setChecked(False)

    def _handle_tabs_section_toggled(self, checked):
        if not hasattr(self, 'tab_widget'):
            return
        self.tab_widget.setVisible(checked)
        if checked:
            if hasattr(self, 'client_info_group_box'):
                self.client_info_group_box.blockSignals(True)
                self.client_info_group_box.setChecked(False)
                if hasattr(self, 'info_container_widget'): self.info_container_widget.setVisible(False)
                self.client_info_group_box.blockSignals(False)
            if hasattr(self, 'notes_group_box'):
                self.notes_group_box.blockSignals(True)
                self.notes_group_box.setChecked(False)
                if hasattr(self, 'notes_container_widget'): self.notes_container_widget.setVisible(False)
                self.notes_group_box.blockSignals(False)
            if hasattr(self, 'contacts_group_box'):
                self.contacts_group_box.blockSignals(True)
                self.contacts_group_box.setChecked(False)
                if hasattr(self, 'contacts_container_widget'): self.contacts_container_widget.setVisible(False)
                self.contacts_group_box.blockSignals(False)
        elif hasattr(self, 'client_info_group_box') and not self.client_info_group_box.isChecked() and \
             hasattr(self, 'notes_group_box') and not self.notes_group_box.isChecked() and \
             (not hasattr(self, 'contacts_group_box') or not self.contacts_group_box.isChecked()):
            self.tabs_group_box.blockSignals(True)
            self.tabs_group_box.setChecked(True)
            self.tab_widget.setVisible(True)
            self.tabs_group_box.blockSignals(False)

    def _handle_contacts_section_toggled(self, checked):
        if not hasattr(self, 'contacts_container_widget'):
            return
        self.contacts_container_widget.setVisible(checked)
        if checked:
            if hasattr(self, 'client_info_group_box'):
                self.client_info_group_box.blockSignals(True)
                self.client_info_group_box.setChecked(False)
                if hasattr(self, 'info_container_widget'): self.info_container_widget.setVisible(False)
                self.client_info_group_box.blockSignals(False)
            if hasattr(self, 'notes_group_box'):
                self.notes_group_box.blockSignals(True)
                self.notes_group_box.setChecked(False)
                if hasattr(self, 'notes_container_widget'): self.notes_container_widget.setVisible(False)
                self.notes_group_box.blockSignals(False)
            if hasattr(self, 'tabs_group_box'):
                self.tabs_group_box.blockSignals(True)
                self.tabs_group_box.setChecked(False)
                if hasattr(self, 'tab_widget'): self.tab_widget.setVisible(False)
                self.tabs_group_box.blockSignals(False)
        elif hasattr(self, 'client_info_group_box') and not self.client_info_group_box.isChecked() and \
             hasattr(self, 'notes_group_box') and not self.notes_group_box.isChecked() and \
             (not hasattr(self, 'tabs_group_box') or not self.tabs_group_box.isChecked()):
            self.contacts_group_box.blockSignals(True)
            self.contacts_group_box.setChecked(True)
            self.contacts_container_widget.setVisible(True)
            self.contacts_group_box.blockSignals(False)

    def load_sav_tickets_table(self):
        if not hasattr(self, 'sav_tickets_table'):
            print("Warning: load_sav_tickets_table called before sav_tickets_table is initialized.")
            return
        self.sav_tickets_table.setRowCount(0)
        client_id = self.client_info.get('client_id')
        if not client_id: return
        try:
            tickets = db_manager.get_sav_tickets_for_client(client_id)
            if tickets is None: tickets = []
            self.sav_tickets_table.setRowCount(len(tickets))
            for row_idx, ticket in enumerate(tickets):
                ticket_id = ticket.get('ticket_id')
                id_item = QTableWidgetItem(str(ticket_id))
                id_item.setData(Qt.UserRole, ticket_id)
                self.sav_tickets_table.setItem(row_idx, 0, id_item)
                cpp_id = ticket.get('client_project_product_id')
                product_name_display = self.tr("N/A")
                if cpp_id:
                    linked_product_info = db_manager.get_client_project_product_by_id(cpp_id)
                    if linked_product_info:
                        product_details = db_manager.get_product_by_id(linked_product_info.get('product_id'))
                        if product_details:
                            product_name_display = product_details.get('product_name', self.tr("Produit Inconnu"))
                self.sav_tickets_table.setItem(row_idx, 1, QTableWidgetItem(product_name_display))
                issue_desc = ticket.get('issue_description', '')
                self.sav_tickets_table.setItem(row_idx, 2, QTableWidgetItem(issue_desc[:100] + '...' if len(issue_desc) > 100 else issue_desc))
                status_name = self.tr("N/A")
                if ticket.get('status_id'):
                    status_info = db_manager.get_status_setting_by_id(ticket['status_id'])
                    if status_info: status_name = status_info.get('status_name', self.tr("Statut Inconnu"))
                self.sav_tickets_table.setItem(row_idx, 3, QTableWidgetItem(status_name))
                opened_at_str = ticket.get('opened_at', '')
                if opened_at_str:
                    try:
                        dt_obj = datetime.fromisoformat(opened_at_str.replace('Z', '+00:00'))
                        opened_at_formatted = dt_obj.strftime('%Y-%m-%d %H:%M')
                    except ValueError: opened_at_formatted = opened_at_str
                else: opened_at_formatted = self.tr('N/A')
                self.sav_tickets_table.setItem(row_idx, 4, QTableWidgetItem(opened_at_formatted))
                tech_name = self.tr("Non assigné")
                if ticket.get('assigned_technician_id'):
                    tech_info = db_manager.get_team_member_by_id(ticket['assigned_technician_id'])
                    if tech_info: tech_name = tech_info.get('full_name', self.tr("Technicien Inconnu"))
                self.sav_tickets_table.setItem(row_idx, 5, QTableWidgetItem(tech_name))
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(2,2,2,2); actions_layout.setSpacing(5)
                view_edit_button = QPushButton(self.tr("Voir/Modifier"))
                view_edit_button.clicked.connect(lambda checked, t_id=ticket_id: self.view_edit_sav_ticket_dialog(t_id))
                actions_layout.addWidget(view_edit_button)
                actions_layout.addStretch()
                self.sav_tickets_table.setCellWidget(row_idx, 6, actions_widget)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur Chargement Tickets SAV"), self.tr("Impossible de charger les tickets SAV:\n{0}").format(str(e)))

    def open_new_sav_ticket_dialog(self):
        client_id = self.client_info.get('client_id')
        if not client_id:
            QMessageBox.warning(self, self.tr("Erreur Client"), self.tr("ID Client non disponible."))
            return
        try: from sav.ticket_dialog import SAVTicketDialog
        except ImportError:
            QMessageBox.critical(self, self.tr("Erreur Importation"), self.tr("Le dialogue de ticket SAV n'a pas pu être chargé."))
            return
        all_client_products = db_manager.get_products_for_client_or_project(client_id, project_id=None)
        purchased_items = [
            {'name': p.get('product_name', 'N/A'), 'client_project_product_id': p.get('client_project_product_id')}
            for p in all_client_products if p.get('purchase_confirmed_at') is not None
        ]
        dialog = SAVTicketDialog(client_id=client_id, purchased_products=purchased_items, parent=self)
        if dialog.exec_() == QDialog.Accepted: self.load_sav_tickets_table()

    def view_edit_sav_ticket_dialog(self, ticket_id):
        client_id = self.client_info.get('client_id')
        if not client_id:
            QMessageBox.warning(self, self.tr("Erreur Client"), self.tr("ID Client non disponible."))
            return
        try: from sav.ticket_dialog import SAVTicketDialog
        except ImportError:
            QMessageBox.critical(self, self.tr("Erreur Importation"), self.tr("Le dialogue de ticket SAV n'a pas pu être chargé."))
            return
        ticket_data = db_manager.get_sav_ticket_by_id(ticket_id)
        if not ticket_data:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Ticket SAV non trouvé (ID: {0}).").format(ticket_id))
            return
        all_client_products = db_manager.get_products_for_client_or_project(client_id, project_id=None)
        purchased_items = [
            {'name': p.get('product_name', 'N/A'), 'client_project_product_id': p.get('client_project_product_id')}
            for p in all_client_products if p.get('purchase_confirmed_at') is not None
        ]
        dialog = SAVTicketDialog(client_id=client_id, purchased_products=purchased_items, ticket_data=ticket_data, parent=self)
        if dialog.exec_() == QDialog.Accepted: self.load_sav_tickets_table()

    def handle_add_assigned_vendor(self):
        if not self.default_company_id:
            QMessageBox.warning(self, self.tr("Société par Défaut Manquante"), self.tr("Aucune société par défaut n'est configurée. Impossible d'assigner du personnel."))
            return
        dialog = AssignPersonnelDialog(client_id=self.client_info['client_id'], role_filter=None, company_id=self.default_company_id, parent=self)
        if dialog.exec_() == QDialog.Accepted: self.load_assigned_vendors_personnel()

    def handle_remove_assigned_vendor(self):
        selected_items = self.assigned_vendors_table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, self.tr("Sélection Requise"), self.tr("Veuillez sélectionner un membre du personnel à retirer."))
            return
        assignment_id = selected_items[0].data(Qt.UserRole)
        if assignment_id is None and self.assigned_vendors_table.currentItem():
             assignment_id = self.assigned_vendors_table.currentItem().data(Qt.UserRole)
        if assignment_id is None:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de récupérer l'ID de l'assignation."))
            return
        reply = QMessageBox.question(self, self.tr("Confirmer Suppression"), self.tr("Êtes-vous sûr de vouloir retirer ce membre du personnel?"), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if db_manager.unassign_personnel_from_client(assignment_id): self.load_assigned_vendors_personnel()
            else: QMessageBox.warning(self, self.tr("Erreur DB"), self.tr("Impossible de retirer le membre du personnel."))

    def update_assigned_vendors_buttons_state(self):
        has_selection = bool(self.assigned_vendors_table.selectedItems())
        self.remove_assigned_vendor_btn.setEnabled(has_selection)

    def handle_add_assigned_technician(self):
        if not self.default_company_id:
            QMessageBox.warning(self, self.tr("Société par Défaut Manquante"), self.tr("Aucune société par défaut n'est configurée. Impossible d'assigner des techniciens."))
            return
        dialog = AssignPersonnelDialog(client_id=self.client_info['client_id'], role_filter="technical_manager", company_id=self.default_company_id, parent=self)
        if dialog.exec_() == QDialog.Accepted: self.load_assigned_technicians()

    def handle_remove_assigned_technician(self):
        selected_items = self.assigned_technicians_table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, self.tr("Sélection Requise"), self.tr("Veuillez sélectionner un technicien à retirer."))
            return
        assignment_id = selected_items[0].data(Qt.UserRole)
        if assignment_id is None and self.assigned_technicians_table.currentItem():
             assignment_id = self.assigned_technicians_table.currentItem().data(Qt.UserRole)
        if assignment_id is None:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de récupérer l'ID de l'assignation."))
            return
        reply = QMessageBox.question(self, self.tr("Confirmer Suppression"), self.tr("Êtes-vous sûr de vouloir retirer ce technicien?"), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if db_manager.unassign_personnel_from_client(assignment_id): self.load_assigned_technicians()
            else: QMessageBox.warning(self, self.tr("Erreur DB"), self.tr("Impossible de retirer le technicien."))

    def update_assigned_technicians_buttons_state(self):
        has_selection = bool(self.assigned_technicians_table.selectedItems())
        self.remove_assigned_technician_btn.setEnabled(has_selection)

    def handle_add_assigned_transporter(self):
        dialog = AssignTransporterDialog(client_id=self.client_info['client_id'], parent=self)
        if dialog.exec_() == QDialog.Accepted: self.load_assigned_transporters()

    def handle_remove_assigned_transporter(self):
        selected_items = self.assigned_transporters_table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, self.tr("Sélection Requise"), self.tr("Veuillez sélectionner un transporteur à retirer."))
            return
        client_transporter_id = selected_items[0].data(Qt.UserRole)
        if client_transporter_id is None and self.assigned_transporters_table.currentItem():
             client_transporter_id = self.assigned_transporters_table.currentItem().data(Qt.UserRole)
        if client_transporter_id is None:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de récupérer l'ID de l'assignation du transporteur."))
            return
        reply = QMessageBox.question(self, self.tr("Confirmer Suppression"), self.tr("Êtes-vous sûr de vouloir retirer ce transporteur?"), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if db_manager.unassign_transporter_from_client(client_transporter_id): self.load_assigned_transporters()
            else: QMessageBox.warning(self, self.tr("Erreur DB"), self.tr("Impossible de retirer le transporteur."))

    def update_assigned_transporters_buttons_state(self):
        has_selection = bool(self.assigned_transporters_table.selectedItems())
        self.remove_assigned_transporter_btn.setEnabled(has_selection)

    def handle_add_assigned_forwarder(self):
        dialog = AssignFreightForwarderDialog(client_id=self.client_info['client_id'], parent=self)
        if dialog.exec_() == QDialog.Accepted: self.load_assigned_freight_forwarders()

    def handle_remove_assigned_forwarder(self):
        selected_items = self.assigned_forwarders_table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, self.tr("Sélection Requise"), self.tr("Veuillez sélectionner un transitaire à retirer."))
            return
        client_forwarder_id = selected_items[0].data(Qt.UserRole)
        if client_forwarder_id is None and self.assigned_forwarders_table.currentItem():
             client_forwarder_id = self.assigned_forwarders_table.currentItem().data(Qt.UserRole)
        if client_forwarder_id is None:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de récupérer l'ID de l'assignation du transitaire."))
            return
        reply = QMessageBox.question(self, self.tr("Confirmer Suppression"), self.tr("Êtes-vous sûr de vouloir retirer ce transitaire?"), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if db_manager.unassign_forwarder_from_client(client_forwarder_id): self.load_assigned_freight_forwarders()
            else: QMessageBox.warning(self, self.tr("Erreur DB"), self.tr("Impossible de retirer le transitaire."))

    def update_assigned_forwarders_buttons_state(self):
        has_selection = bool(self.assigned_forwarders_table.selectedItems())
        self.remove_assigned_forwarder_btn.setEnabled(has_selection)

    def open_carrier_email_dialog(self, row_index):
        try:
            transporter_name_item = self.assigned_transporters_table.item(row_index, 0)
            if not transporter_name_item:
                QMessageBox.warning(self, self.tr("Erreur Données"), self.tr("Impossible de récupérer le nom du transporteur."))
                return
            transporter_name = transporter_name_item.text()
            client_transporter_id = transporter_name_item.data(Qt.UserRole)
            if client_transporter_id is None:
                QMessageBox.warning(self, self.tr("Erreur Données"), self.tr("ID du transporteur non trouvé pour cette ligne."))
                return
            assigned_list = db_manager.get_assigned_transporters_for_client(self.client_info.get('client_id'))
            transporter_email = ""
            if assigned_list:
                for item_data in assigned_list:
                    if item_data.get('client_transporter_id') == client_transporter_id:
                        transporter_email = item_data.get('email')
                        if not transporter_email:
                            contact_person_field = item_data.get('contact_person', '')
                            if '@' in contact_person_field and '.' in contact_person_field.split('@')[-1]:
                                transporter_email = contact_person_field
                        break
            if not transporter_email:
                email_text, ok = QInputDialog.getText(self, self.tr("Email du Transporteur Manquant"), self.tr("L'email pour {0} n'est pas trouvé. Veuillez le saisir:").format(transporter_name))
                if ok and email_text.strip(): transporter_email = email_text.strip()
                else:
                    QMessageBox.information(self, self.tr("Annulé"), self.tr("Envoi d'email annulé car l'email du destinataire est manquant."))
                    self.load_assigned_transporters()
                    return
            client_name = self.client_info.get("client_name", self.tr("Notre Client"))
            dialog = CarrierEmailDialog(carrier_name=transporter_name, carrier_email=transporter_email, client_name=client_name, client_transporter_id=client_transporter_id, parent=self, config=self.config)
            dialog.exec_()
            self.load_assigned_transporters()
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur Dialogue Email"), self.tr("Une erreur est survenue lors de l'ouverture du dialogue d'email: {0}").format(str(e)))

    def load_assigned_vendors_personnel(self):
        self.assigned_vendors_table.setRowCount(0)
        self.assigned_vendors_table.setSortingEnabled(False)
        client_id = self.client_info.get('client_id')
        if not client_id: return
        try:
            assigned_list = db_manager.get_assigned_personnel_for_client(client_id, role_filter=None) or []
            for row, item_data in enumerate(assigned_list):
                self.assigned_vendors_table.insertRow(row)
                name_item = QTableWidgetItem(item_data.get('personnel_name'))
                name_item.setData(Qt.UserRole, item_data.get('assignment_id'))
                self.assigned_vendors_table.setItem(row, 0, name_item)
                self.assigned_vendors_table.setItem(row, 1, QTableWidgetItem(item_data.get('role_in_project')))
                self.assigned_vendors_table.setItem(row, 2, QTableWidgetItem(item_data.get('personnel_email')))
                self.assigned_vendors_table.setItem(row, 3, QTableWidgetItem(item_data.get('personnel_phone')))
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur Chargement"), self.tr("Impossible de charger le personnel assigné: {0}").format(str(e)))
        self.assigned_vendors_table.setSortingEnabled(True)
        self.update_assigned_vendors_buttons_state()

    def load_assigned_technicians(self):
        self.assigned_technicians_table.setRowCount(0)
        self.assigned_technicians_table.setSortingEnabled(False)
        client_id = self.client_info.get('client_id')
        if not client_id: return
        try:
            assigned_list = db_manager.get_assigned_personnel_for_client(client_id, role_filter="Technicien") or []
            for row, item_data in enumerate(assigned_list):
                self.assigned_technicians_table.insertRow(row)
                name_item = QTableWidgetItem(item_data.get('personnel_name'))
                name_item.setData(Qt.UserRole, item_data.get('assignment_id'))
                self.assigned_technicians_table.setItem(row, 0, name_item)
                self.assigned_technicians_table.setItem(row, 1, QTableWidgetItem(item_data.get('role_in_project')))
                self.assigned_technicians_table.setItem(row, 2, QTableWidgetItem(item_data.get('personnel_email')))
                self.assigned_technicians_table.setItem(row, 3, QTableWidgetItem(item_data.get('personnel_phone')))
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur Chargement"), self.tr("Impossible de charger les techniciens assignés: {0}").format(str(e)))
        self.assigned_technicians_table.setSortingEnabled(True)
        self.update_assigned_technicians_buttons_state()

    def load_assigned_transporters(self):
        self.assigned_transporters_table.setRowCount(0)
        self.assigned_transporters_table.setSortingEnabled(False)
        client_id = self.client_info.get('client_id')
        if not client_id: return
        try:
            assigned_list = db_manager.get_assigned_transporters_for_client(client_id) or []
            for row, item_data in enumerate(assigned_list):
                self.assigned_transporters_table.insertRow(row)
                name_item = QTableWidgetItem(item_data.get('transporter_name'))
                name_item.setData(Qt.UserRole, item_data.get('client_transporter_id'))
                self.assigned_transporters_table.setItem(row, 0, name_item)
                self.assigned_transporters_table.setItem(row, 1, QTableWidgetItem(item_data.get('contact_person')))
                self.assigned_transporters_table.setItem(row, 2, QTableWidgetItem(item_data.get('phone')))
                self.assigned_transporters_table.setItem(row, 3, QTableWidgetItem(item_data.get('transport_details')))
                cost_item = QTableWidgetItem(f"{item_data.get('cost_estimate', 0.0):.2f} €")
                cost_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.assigned_transporters_table.setItem(row, 4, cost_item)
                email_status = item_data.get('email_status', 'Pending')
                btn_send_email = QPushButton()
                if email_status == "Sent":
                    btn_send_email.setText(self.tr("Email Sent"))
                    btn_send_email.setStyleSheet("background-color: lightgray; color: black;")
                    btn_send_email.setEnabled(False)
                elif email_status == "Failed":
                    btn_send_email.setText(self.tr("Resend Email (Failed)"))
                    btn_send_email.setStyleSheet("background-color: orange; color: black;")
                    btn_send_email.clicked.connect(lambda checked, r=row: self.open_carrier_email_dialog(r))
                else:
                    btn_send_email.setText(self.tr("Send Email"))
                    btn_send_email.setStyleSheet("background-color: green; color: white;")
                    btn_send_email.clicked.connect(lambda checked, r=row: self.open_carrier_email_dialog(r))
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.addWidget(btn_send_email)
                action_layout.setContentsMargins(0, 0, 0, 0)
                action_layout.setAlignment(Qt.AlignCenter)
                action_widget.setLayout(action_layout)
                self.assigned_transporters_table.setCellWidget(row, 5, action_widget)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur Chargement"), self.tr("Impossible de charger les transporteurs assignés: {0}").format(str(e)))
        self.assigned_transporters_table.setSortingEnabled(True)
        self.update_assigned_transporters_buttons_state()

    def load_assigned_freight_forwarders(self):
        self.assigned_forwarders_table.setRowCount(0)
        self.assigned_forwarders_table.setSortingEnabled(False)
        client_id = self.client_info.get('client_id')
        if not client_id: return
        try:
            assigned_list = db_manager.get_assigned_forwarders_for_client(client_id) or []
            for row, item_data in enumerate(assigned_list):
                self.assigned_forwarders_table.insertRow(row)
                name_item = QTableWidgetItem(item_data.get('forwarder_name'))
                name_item.setData(Qt.UserRole, item_data.get('client_forwarder_id'))
                self.assigned_forwarders_table.setItem(row, 0, name_item)
                self.assigned_forwarders_table.setItem(row, 1, QTableWidgetItem(item_data.get('contact_person')))
                self.assigned_forwarders_table.setItem(row, 2, QTableWidgetItem(item_data.get('phone')))
                self.assigned_forwarders_table.setItem(row, 3, QTableWidgetItem(item_data.get('task_description')))
                cost_item = QTableWidgetItem(f"{item_data.get('cost_estimate', 0.0):.2f} €")
                cost_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.assigned_forwarders_table.setItem(row, 4, cost_item)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur Chargement"), self.tr("Impossible de charger les transitaires assignés: {0}").format(str(e)))
        self.assigned_forwarders_table.setSortingEnabled(True)
        self.update_assigned_forwarders_buttons_state()

    def load_document_notes_filters(self):
        self.load_document_notes_table()

    def load_document_notes_filters(self):
        self.doc_notes_type_filter_combo.blockSignals(True)
        self.doc_notes_lang_filter_combo.blockSignals(True)
        self.doc_notes_type_filter_combo.clear()
        self.doc_notes_type_filter_combo.addItem(self.tr("Tous Types"), None)
        doc_types = ["Proforma", "Packing List", "Sales Conditions", "Certificate of Origin", "Bill of Lading", "Other"]
        for doc_type in doc_types: self.doc_notes_type_filter_combo.addItem(doc_type, doc_type)
        self.doc_notes_lang_filter_combo.clear()
        self.doc_notes_lang_filter_combo.addItem(self.tr("Toutes Langues"), None)
        langs = ["fr", "en", "ar", "tr", "pt"]
        for lang in langs: self.doc_notes_lang_filter_combo.addItem(lang, lang)
        self.doc_notes_type_filter_combo.blockSignals(False)
        self.doc_notes_lang_filter_combo.blockSignals(False)
        self.doc_notes_type_filter_combo.setCurrentIndex(0)
        self.doc_notes_lang_filter_combo.setCurrentIndex(0)

    def load_document_notes_table(self):
        self.document_notes_table.setRowCount(0)
        client_id = self.client_info.get("client_id")
        if not client_id: return
        doc_type_filter = self.doc_notes_type_filter_combo.currentData()
        lang_filter = self.doc_notes_lang_filter_combo.currentData()
        try:
            notes = db_manager.get_client_document_notes(client_id, document_type=doc_type_filter, language_code=lang_filter, is_active=None)
            notes = notes if notes else []
            self.document_notes_table.setRowCount(len(notes))
            for row_idx, note in enumerate(notes):
                note_id = note.get("note_id")
                type_item = QTableWidgetItem(note.get("document_type"))
                type_item.setData(Qt.UserRole, note_id)
                self.document_notes_table.setItem(row_idx, 0, type_item)
                self.document_notes_table.setItem(row_idx, 1, QTableWidgetItem(note.get("language_code")))
                note_content = note.get("note_content", "")
                lines = [line.strip() for line in note_content.split('\n') if line.strip()]
                html_content = ""
                if lines:
                    html_content = "<ol style='margin:0px; padding-left: 15px;'>"
                    for line in lines:
                        escaped_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                        html_content += f"<li>{escaped_line}</li>"
                    html_content += "</ol>"
                else: html_content = f"<p style='margin:0px; font-style:italic;'>{self.tr('Aucune note.')}</p>"
                note_label = QLabel(); note_label.setText(html_content); note_label.setWordWrap(True)
                self.document_notes_table.setCellWidget(row_idx, 2, note_label)
                active_text = self.tr("Oui") if note.get("is_active") else self.tr("Non")
                active_item = QTableWidgetItem(active_text)
                active_item.setTextAlignment(Qt.AlignCenter)
                self.document_notes_table.setItem(row_idx, 3, active_item)
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(5, 0, 5, 0); actions_layout.setSpacing(5)
                role_name = self.current_user_info.get('role_name') if self.current_user_info else None
                can_manage_doc_notes = has_permission(role_name, P_MANAGE_CLIENT_DOCUMENTS)
                if can_manage_doc_notes:
                    edit_button = QPushButton("✏️")
                    edit_button.setToolTip(self.tr("Modifier cette note"))
                    edit_button.clicked.connect(lambda checked, n_id=note_id: self.on_edit_document_note_clicked(n_id))
                    actions_layout.addWidget(edit_button)
                    delete_button = QPushButton("🗑️")
                    delete_button.setToolTip(self.tr("Supprimer cette note"))
                    delete_button.setObjectName("dangerButton")
                    delete_button.clicked.connect(lambda checked, n_id=note_id: self.on_delete_document_note_clicked(n_id))
                    actions_layout.addWidget(delete_button)
                else: actions_layout.addStretch()
                actions_layout.addStretch()
                self.document_notes_table.setCellWidget(row_idx, 4, actions_widget)
            self.document_notes_table.resizeColumnToContents(0)
            self.document_notes_table.resizeColumnToContents(1)
            self.document_notes_table.resizeColumnToContents(3)
            self.document_notes_table.resizeColumnToContents(4)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur Chargement Notes"), self.tr("Impossible de charger les notes de document:\n{0}").format(str(e)))

    def on_add_document_note(self):
        client_id = self.client_info.get("client_id")
        if not client_id:
            QMessageBox.warning(self, self.tr("Erreur Client"), self.tr("ID Client non disponible."))
            return
        dialog = self.ClientDocumentNoteDialog(client_id=client_id, parent=self)
        if dialog.exec_() == QDialog.Accepted: self.load_document_notes_table()

    def on_edit_document_note_clicked(self, note_id):
        client_id = self.client_info.get("client_id")
        if not client_id:
            QMessageBox.warning(self, self.tr("Erreur Client"), self.tr("ID Client non disponible."))
            return
        note_data = db_manager.get_client_document_note_by_id(note_id)
        if note_data:
            dialog = self.ClientDocumentNoteDialog(client_id=client_id, note_data=note_data, parent=self)
            if dialog.exec_() == QDialog.Accepted: self.load_document_notes_table()
        else: QMessageBox.warning(self, self.tr("Erreur"), self.tr("Note non trouvée (ID: {0}).").format(note_id))

    def on_delete_document_note_clicked(self, note_id):
        reply = QMessageBox.question(self, self.tr("Confirmer Suppression"), self.tr("Êtes-vous sûr de vouloir supprimer cette note (ID: {0})?").format(note_id), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                success = db_manager.delete_client_document_note(note_id)
                if success:
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Note supprimée avec succès."))
                    self.load_document_notes_table()
                else: QMessageBox.warning(self, self.tr("Échec"), self.tr("Impossible de supprimer la note. Vérifiez les logs."))
            except Exception as e:
                 QMessageBox.critical(self, self.tr("Erreur"), self.tr("Une erreur est survenue lors de la suppression:\n{0}").format(str(e)))

    def prev_contact_page(self):
        if self.current_contact_offset > 0:
            self.current_contact_offset -= self.CONTACT_PAGE_LIMIT
            self.load_contacts()

    def next_contact_page(self):
        if (self.current_contact_offset + self.CONTACT_PAGE_LIMIT) < self.total_contacts_count:
            self.current_contact_offset += self.CONTACT_PAGE_LIMIT
            self.load_contacts()

    def update_contact_pagination_controls(self):
        if self.total_contacts_count == 0: total_pages = 1; current_page = 1
        else:
            total_pages = math.ceil(self.total_contacts_count / self.CONTACT_PAGE_LIMIT)
            current_page = (self.current_contact_offset // self.CONTACT_PAGE_LIMIT) + 1
        self.contact_page_info_label.setText(f"Page {current_page} / {total_pages}")
        self.prev_contact_button.setEnabled(self.current_contact_offset > 0)
        self.next_contact_button.setEnabled((self.current_contact_offset + self.CONTACT_PAGE_LIMIT) < self.total_contacts_count)

    def add_document(self):
        available_languages = ["en", "fr", "ar", "tr", "pt"]
        selected_doc_language, ok = QInputDialog.getItem(self, self.tr("Sélectionner la langue"), self.tr("Langue du document:"), available_languages, 0, False)
        if not ok or not selected_doc_language:
            QMessageBox.information(self, self.tr("Annulé"), self.tr("L'opération d'ajout de document a été annulée."))
            return
        initial_dir = self.config.get("clients_dir", os.path.expanduser("~"))

        # Use QFileDialog for file selection
        dialog = QFileDialog(self, self.tr("Sélectionner un document"), initial_dir, self.tr("Tous les fichiers (*.*)"))
        dialog.setFileMode(QFileDialog.ExistingFile) # Ensure only one existing file can be selected
        if dialog.exec_():
            selected_files = dialog.selectedFiles()
            if not selected_files:
                return # User cancelled or selected no file
            selected_file_path = selected_files[0]
        else:
            return # Dialog cancelled

        if selected_file_path:
            try:
                client_base_path = self.client_info.get("base_folder_path")
                if not client_base_path: client_base_path = self.client_info.get("default_base_folder_path", "")
                if not client_base_path or not os.path.isdir(client_base_path):
                    QMessageBox.warning(self, self.tr("Erreur Dossier Client"), self.tr("Le chemin du dossier de base du client n'est pas configuré ou est invalide."))
                    return
                selected_order_identifier_for_import = None
                target_dir = os.path.join(client_base_path, selected_doc_language)
                if selected_order_identifier_for_import:
                    safe_order_subfolder = selected_order_identifier_for_import.replace(':', '_').replace(' ', '_')
                    target_dir = os.path.join(client_base_path, safe_order_subfolder, selected_doc_language)
                os.makedirs(target_dir, exist_ok=True)
                file_name = os.path.basename(selected_file_path)
                target_file_path = os.path.join(target_dir, file_name)
                if os.path.exists(target_file_path):
                    reply = QMessageBox.question(self, self.tr("Fichier Existant"), self.tr("Un fichier du même nom existe déjà à cet emplacement. Voulez-vous le remplacer?"), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                    if reply == QMessageBox.No:
                        QMessageBox.information(self, self.tr("Annulé"), self.tr("L'opération d'ajout de document a été annulée."))
                        return

                # shutil.copy needs to be imported
                import shutil
                shutil.copy(selected_file_path, target_file_path)

                client_id = self.client_info.get("client_id")
                document_name = os.path.basename(selected_file_path)
                file_name_on_disk = document_name
                file_path_relative = os.path.join(selected_doc_language, file_name)
                ext = os.path.splitext(file_name)[1].lower()
                if ext == ".html": document_type_generated = "HTML"
                elif ext == ".pdf": document_type_generated = "PDF"
                elif ext == ".xlsx": document_type_generated = "XLSX"
                elif ext == ".docx": document_type_generated = "DOCX"
                else: document_type_generated = ext.upper().replace(".", "") if ext else "OTHER"
                language_code = selected_doc_language
                source_template_id = None
                order_identifier = None
                if hasattr(self, 'doc_order_filter_combo') and self.doc_order_filter_combo.isVisible():
                    current_order_data = self.doc_order_filter_combo.currentData()
                    if current_order_data not in ["ALL", "NONE"]: order_identifier = current_order_data
                notes = None
                version_tag = "1.0"
                doc_db_data_for_crud = {
                    "client_id": client_id, "document_name": document_name, "file_name_on_disk": file_name_on_disk,
                    "file_path_relative": file_path_relative, "document_type_generated": document_type_generated,
                    "language_code": language_code, "source_template_id": source_template_id,
                    "order_identifier": order_identifier, "user_id": self.current_user_id,
                    "notes": notes, "version_tag": version_tag,
                }
                db_success = False
                try:
                    new_doc_db_id = db_manager.add_client_document(doc_db_data_for_crud)
                    if new_doc_db_id:
                        db_success = True
                        current_selected_languages = self.client_info.get("selected_languages", [])
                        if isinstance(current_selected_languages, str):
                            current_selected_languages = [lang.strip() for lang in current_selected_languages.split(',') if lang.strip()]
                        if not current_selected_languages: current_selected_languages = []
                        if selected_doc_language not in current_selected_languages:
                            add_lang_reply = QMessageBox.question(self, self.tr("Ajouter Langue"), self.tr("Voulez-vous ajouter '{0}' aux langues sélectionnées pour ce client?").format(selected_doc_language), QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                            if add_lang_reply == QMessageBox.Yes:
                                updated_languages_list = current_selected_languages + [selected_doc_language]
                                updated_languages_str = ",".join(updated_languages_list)
                                client_id_to_update = self.client_info.get("client_id")
                                if client_id_to_update:
                                    if db_manager.update_client(client_id_to_update, {'selected_languages': updated_languages_str}):
                                        self.client_info["selected_languages"] = updated_languages_list
                                        print(f"Client {client_id_to_update} selected_languages updated to {updated_languages_str}")
                                    else: QMessageBox.warning(self, self.tr("Erreur DB"), self.tr("Échec de la mise à jour des langues du client dans la DB."))
                                else: QMessageBox.warning(self, self.tr("Erreur Client"), self.tr("ID Client non disponible, impossible de mettre à jour les langues."))
                        self.populate_doc_table()
                        QMessageBox.information(self, self.tr("Succès"), self.tr("Document '{0}' importé et enregistré avec succès en langue '{1}'.").format(file_name, selected_doc_language))
                    else:
                        self.populate_doc_table()
                        QMessageBox.warning(self, self.tr("Échec Enregistrement DB"), self.tr("Document '{0}' copié avec succès en langue '{1}', mais échec de l'enregistrement dans la base de données. Le document pourrait ne pas s'afficher correctement.").format(file_name, selected_doc_language))
                except Exception as db_e:
                    logging.error(f"Error during database operation in add_document: {db_e}", exc_info=True)
                    self.populate_doc_table()
                    QMessageBox.warning(self, self.tr("Erreur Base de Données"), self.tr("Document '{0}' copié, mais une erreur est survenue lors de l'enregistrement dans la base de données: {1}. Le document pourrait ne pas s'afficher correctement.").format(file_name, str(db_e)))
            except Exception as e:
                logging.error(f"Error copying file or preparing metadata in add_document: {e}", exc_info=True)
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible d'ajouter le document : {0}").format(str(e)))

    def _handle_generate_and_open_pdf_action(self, document_data: dict):
        QApplication.setOverrideCursor

    def handle_generate_referents_report(self):
        if not self.client_info or not self.client_info.get('client_id'):
            QMessageBox.warning(self, self.tr("Aucun Client Sélectionné"), self.tr("Veuillez sélectionner un client."))
            return

        client_id = self.client_info.get('client_id')

        # Choix de la langue
        languages = {"Français": "fr", "English": "en", "العربية": "ar"}
        lang_display_names = list(languages.keys())
        # Make sure QInputDialog is imported from PyQt5.QtWidgets
        selected_lang_display, ok = QInputDialog.getItem(self, self.tr("Choisir la langue du rapport"),
                                                         self.tr("Langue:"), lang_display_names, 0, False)
        if not ok or not selected_lang_display:
            return # User cancelled

        language_code = languages[selected_lang_display]

        # Appel au controller
        QApplication.setOverrideCursor(Qt.WaitCursor)
        pdf_path = None # Initialize pdf_path
        try:
            if not self.client_controller:
                logging.error("ClientMainWidget: client_controller is not initialized.")
                QMessageBox.critical(self, self.tr("Erreur Interne"), self.tr("Le contrôleur client n'est pas initialisé."))
                return
            if not self.app_root_dir:
                logging.error("ClientMainWidget: app_root_dir is not set.")
                QMessageBox.critical(self, self.tr("Erreur Configuration"), self.tr("Le répertoire racine de l'application n'est pas configuré."))
                return

            pdf_path = self.client_controller.generate_referents_report(
                client_id=client_id,
                language_code=language_code,
                app_root_dir=self.app_root_dir,
                current_user_id=self.current_user_id
            )
        except Exception as e_gen:
            logging.error(f"Exception during generate_referents_report call: {e_gen}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Inattendue"), self.tr(f"Une erreur inattendue est survenue lors de la génération du rapport: {e_gen}"))
            pdf_path = None # Ensure pdf_path is None on exception
        finally:
            QApplication.restoreOverrideCursor()

        if pdf_path and os.path.exists(pdf_path):
            # Make sure QDesktopServices, QUrl, QFileDialog, QStandardPaths are imported from PyQt5.QtGui / QtCore / QtWidgets
            reply = QMessageBox.information(self, self.tr("Rapport Généré"),
                                            self.tr(f"Le rapport des référents a été généré avec succès.\nChemin: {pdf_path}\n\nVoulez-vous l'ouvrir maintenant?"),
                                            QMessageBox.Open | QMessageBox.Save | QMessageBox.Cancel,
                                            QMessageBox.Open)

            if reply == QMessageBox.Open:
                QDesktopServices.openUrl(QUrl.fromLocalFile(pdf_path))
            elif reply == QMessageBox.Save:
                default_save_name = os.path.basename(pdf_path)
                save_path, _ = QFileDialog.getSaveFileName(self, self.tr("Enregistrer le rapport sous..."),
                                                           os.path.join(QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation), default_save_name),
                                                           self.tr("Fichiers PDF (*.pdf)"))
                if save_path:
                    try:
                        import shutil
                        shutil.copy(pdf_path, save_path)
                        QMessageBox.information(self, self.tr("Enregistré"), self.tr(f"Rapport enregistré sous:\n{save_path}"))
                        # Optionnel: supprimer le fichier temporaire si on ne veut pas le garder après sauvegarde
                        # try:
                        #     os.remove(pdf_path)
                        # except OSError as e_del_temp:
                        #     logging.warning(f"Could not delete temporary PDF file {pdf_path} after saving: {e_del_temp}")
                    except Exception as e_save:
                        QMessageBox.warning(self, self.tr("Erreur d'enregistrement"), self.tr(f"Impossible d'enregistrer le fichier: {e_save}"))
            # If Cancel, the temporary file remains (useful for debugging, but might need cleanup strategy)
        elif pdf_path and not os.path.exists(pdf_path): # Path was returned but file isn't there
             QMessageBox.warning(self, self.tr("Erreur Fichier"), self.tr(f"La génération du PDF semble avoir réussi mais le fichier n'a pas été trouvé à l'emplacement attendu:\n{pdf_path}"))
        elif not pdf_path: # Generation explicitly failed and returned None
            QMessageBox.critical(self, self.tr("Échec de la Génération"), self.tr("La génération du rapport des référents a échoué. Veuillez consulter les logs pour plus de détails."))
        # No else needed if pdf_path is None and an error was already shown by the controller or above.

    def toggle_client_edit_mode(self):
        self.is_editing_client = not self.is_editing_client
        if self.is_editing_client:
            self.edit_save_client_btn.setText(self.tr("Sauvegarder Client"))
            self.edit_save_client_btn.setText("💾")
            # Future: Enable editing of specific fields
            logging.info(f"ClientMainWidget: Entered edit mode for client {self.client_info.get('client_id')}.")
            # Example: self.client_name_edit.setReadOnly(False)
            # For now, just log and change button
            self.switchTo_edit_client_view() # Nouvelle méthode pour passer en mode édition
        else:
            # Future: Call a method to save changes if any
            # For now, just revert button and log
            if self.save_client_changes_from_edit_view(): # Nouvelle méthode pour sauvegarder
                self.edit_save_client_btn.setText(self.tr("Modifier Client"))
                self.edit_save_client_btn.setText("✏️")
                logging.info(f"ClientMainWidget: Exited edit mode for client {self.client_info.get('client_id')}. Changes saved.")
                # La vue est rafraîchie dans save_client_changes_from_edit_view
            else:
                # Si la sauvegarde échoue ou est annulée, rester en mode édition
                self.is_editing_client = True # Maintenir l'état d'édition
                # Le bouton reste "Sauvegarder Client"
                logging.info(f"ClientMainWidget: Save attempt failed or cancelled. Remained in edit mode for client {self.client_info.get('client_id')}.")

        # After toggling, re-apply permissions if some actions should be disabled during edit mode
        self._apply_permissions()

    def switchTo_edit_client_view(self):
        """Switches the client details view to an editable form."""
        if not self.client_info:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Aucune information client à modifier."))
            self.is_editing_client = False # Revert state
            self.edit_save_client_btn.setText(self.tr("Modifier Client"))
            self.edit_save_client_btn.setText("✏️")
            return

        logging.info(f"ClientMainWidget: Switching to edit view for client {self.client_info.get('client_id')}")
        self.edit_widgets = {} # Clear any previous edit widgets

        # Iterate over details_layout and replace QLabel values with QLineEdits or appropriate widgets
        # This is a simplified approach. A more robust way would be to have predefined edit widgets
        # and toggle their visibility or manage them in a stacked layout.

        # For simplicity, we'll clear and rebuild the details_layout for edit mode.
        # Store original labels to restore them later if needed, or just repopulate from self.client_info

        # Clear existing widgets from details_layout but keep the layout itself
        while self.details_layout.count():
            item = self.details_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout(): # If it's a sub-layout
                 # Clearing a sub-layout is more complex, for now assume direct widgets or simple layouts
                while item.layout().count():
                    sub_item = item.layout().takeAt(0)
                    if sub_item.widget():
                        sub_item.widget().deleteLater()

        # Client Name (already a QLabel: self.header_label, not in details_layout directly, handle separately if needed)
        # For now, let's assume client_name is part of the details_layout for editing
        self.edit_widgets['client_name'] = QLineEdit(self.client_info.get("client_name", ""))
        self.details_layout.addRow(self.tr("Nom Client:"), self.edit_widgets['client_name'])

        # Project ID (usually not editable by user directly, but for example)
        self.edit_widgets['project_identifier'] = QLineEdit(self.client_info.get("project_identifier", ""))
        self.details_layout.addRow(self.project_id_label, self.edit_widgets['project_identifier'])

        # Country and City - Needs QComboBoxes, potentially with "add new" functionality
        country_city_edit_widget = QWidget()
        country_city_h_layout = QHBoxLayout(country_city_edit_widget)
        country_city_h_layout.setContentsMargins(0,0,0,0)

        self.edit_widgets['country_combo'] = QComboBox(); self.edit_widgets['country_combo'].setEditable(True)
        # Populate countries and set current
        self._populate_country_edit_combo(self.edit_widgets['country_combo'], self.client_info.get('country_id'))

        self.edit_widgets['city_combo'] = QComboBox(); self.edit_widgets['city_combo'].setEditable(True)
        # Populate cities based on selected country and set current
        self.edit_widgets['country_combo'].currentIndexChanged.connect(
            lambda index: self._populate_city_edit_combo(
                self.edit_widgets['city_combo'],
                self.edit_widgets['country_combo'].itemData(index) if self.edit_widgets['country_combo'].count() > 0 and index >=0 else None, # Ensure valid index and data
                None # No city_id to preselect when country changes
            )
        )
        # Initial population of cities for the current country
        self._populate_city_edit_combo(self.edit_widgets['city_combo'], self.client_info.get('country_id'), self.client_info.get('city_id'))


        country_city_h_layout.addWidget(self._create_styled_label(self.tr("Pays:")))
        country_city_h_layout.addWidget(self.edit_widgets['country_combo'],1)
        country_city_h_layout.addSpacing(15)
        country_city_h_layout.addWidget(self._create_styled_label(self.tr("Ville:")))
        country_city_h_layout.addWidget(self.edit_widgets['city_combo'],1)
        self.details_layout.addRow(self.country_city_label, country_city_edit_widget)

        # Price and Creation Date (kept as read-only for now, as per original display logic)
        price_date_edit_widget = QWidget()
        price_date_edit_layout = QHBoxLayout(price_date_edit_widget)
        price_date_edit_layout.setContentsMargins(0,0,0,0)
        price_date_edit_layout.addWidget(self._create_styled_label(self.tr("Prix Final:")))
        price_date_edit_layout.addWidget(self._create_styled_value_label(self.price_value_label.text()),1) # Display existing value
        price_date_edit_layout.addSpacing(15)
        price_date_edit_layout.addWidget(self._create_styled_label(self.tr("Date Création:")))
        price_date_edit_layout.addWidget(self._create_styled_value_label(self.date_value_label.text()),1) # Display existing value
        self.details_layout.addRow(self.price_date_label, price_date_edit_widget)


        # Status and Category
        status_category_edit_widget = QWidget()
        status_category_edit_layout = QHBoxLayout(status_category_edit_widget)
        status_category_edit_layout.setContentsMargins(0,0,0,0)

        status_category_edit_layout.addWidget(self._create_styled_label(self.tr("Statut:")))
        self.status_combo.setEnabled(True) # Already a QComboBox, ensure it's enabled and added back
        status_category_edit_layout.addWidget(self.status_combo, 1)
        status_category_edit_layout.addSpacing(15)

        status_category_edit_layout.addWidget(self._create_styled_label(self.tr("Catégorie:")))
        self.edit_widgets['category'] = QLineEdit(self.client_info.get("category", ""))
        status_category_edit_layout.addWidget(self.edit_widgets['category'], 1)
        self.details_layout.addRow(self.status_category_label, status_category_edit_widget)

        # Distributor Info
        self.edit_widgets['distributor_info'] = QTextEdit(self.client_info.get("distributor_info", ""))
        self.edit_widgets['distributor_info'].setFixedHeight(60)
        self.details_layout.addRow(self.distributor_info_label_static, self.edit_widgets['distributor_info'])
        self.edit_widgets['distributor_info_label_static'] = self.distributor_info_label_static # Store for visibility toggle

        # Need
        self.edit_widgets['primary_need_description'] = QTextEdit(self.client_info.get("primary_need_description", ""))
        self.edit_widgets['primary_need_description'].setFixedHeight(60)
        self.details_layout.addRow(self.need_label_static, self.edit_widgets['primary_need_description'])

        # Folder Path (read-only usually)
        self.details_layout.addRow(self.folder_label_static, QLabel(self.folder_value_label.text()))

        # Created By (read-only)
        self.details_layout.addRow(self.created_by_label_static, QLabel(self.created_by_value_label.text()))

        # Handle Client Statuses (checkboxes) - make them interactive if needed
        # For now, assuming they are already interactive and their state will be read on save.

        # TODO: Add more fields as QLineEdits, QComboBoxes, etc.
        # Example for 'client_name' if it were a simple label:
        # self.edit_widgets['client_name_edit'] = QLineEdit(self.client_info.get('client_name'))
        # self.details_layout.replaceWidget(self.client_name_value_label, self.edit_widgets['client_name_edit'])
        # self.client_name_value_label.setVisible(False) # Hide original label

        # Make sure the client info group box is checked and visible
        self.client_info_group_box.setChecked(True)
        self.info_container_widget.setVisible(True)
        self.client_details_tab.setVisible(True) # Ensure the tab itself is visible

    def save_client_changes_from_edit_view(self):
        """Saves the changes made in the edit view to the database."""
        if not self.is_editing_client or not self.client_info:
            return False # Should not happen if called correctly

        logging.info(f"ClientMainWidget: Attempting to save changes for client {self.client_info.get('client_id')}")

        data_to_save = {}
        # Example: data_to_save['client_name'] = self.edit_widgets['client_name'].text().strip()
        # ... collect data from all self.edit_widgets ...

        # Collect data (simplified example)
        if 'client_name' in self.edit_widgets:
            data_to_save['client_name'] = self.edit_widgets['client_name'].text().strip()
        if 'project_identifier' in self.edit_widgets:
            data_to_save['project_identifier'] = self.edit_widgets['project_identifier'].text().strip()

        # Status
        data_to_save['status_id'] = self.status_combo.currentData()
        # Category
        if 'category' in self.edit_widgets:
            data_to_save['category'] = self.edit_widgets['category'].text().strip()
        # Distributor Info
        if 'distributor_info' in self.edit_widgets:
             data_to_save['distributor_info'] = self.edit_widgets['distributor_info'].toPlainText().strip()
        # Need
        if 'primary_need_description' in self.edit_widgets:
            data_to_save['primary_need_description'] = self.edit_widgets['primary_need_description'].toPlainText().strip()

        # TODO: Validate data_to_save before calling CRUD

        try:
            if not data_to_save: # No editable fields were actually changed or defined in edit_widgets
                logging.info("No data to save from edit widgets.")
                # Switch back to display mode without saving
                self.is_editing_client = False # Important to correctly flip the mode
                self.populate_details_layout() # Refresh to display mode
                return True # Indicate success in terms of mode switch

            success = clients_crud_instance.update_client(self.client_info['client_id'], data_to_save)
            if success:
                client_management_signals.show_notification.emit(self.tr("Succès"), self.tr("Modifications client sauvegardées."), 'SUCCESS')
                # Update self.client_info with the saved data
                for key, value in data_to_save.items():
                    self.client_info[key] = value
                # Also update text representations if IDs were saved (e.g., status name from status_id)
                self.client_info['status'] = self.status_combo.currentText()
                # ... similar for country, city if they were editable ...

                self.is_editing_client = False # Set before refresh
                self.populate_details_layout() # Refresh to display mode with new data
                self.refresh_display(self.client_info) # Ensure all parts of widget reflect change
                return True
            else:
                QMessageBox.warning(self, self.tr("Erreur DB"), self.tr("Échec de la sauvegarde des modifications client."))
                return False
        except Exception as e:
            logging.error(f"Error saving client changes: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Sauvegarde"), self.tr("Une erreur est survenue: {0}").format(str(e)))
            return False

    def populate_details_layout(self):
        logging.info(f"Populating details layout for client: {self.client_info.get('client_name', 'N/A')}")
        if not self.client_info:
            logging.warning("populate_details_layout: No client_info available.")
            # Optionally clear all labels or set to "N/A"
            self.project_id_value_label.setText(self.tr("N/A"))
            self.country_value_label.setText(self.tr("N/A"))
            self.city_value_label.setText(self.tr("N/A"))
            self.price_value_label.setText(self.tr("N/A"))
            self.date_value_label.setText(self.tr("N/A"))
            self.category_value_label.setText(self.tr("N/A"))
            self.distributor_info_value_label.setText(self.tr("N/A"))
            self.need_value_label.setText(self.tr("N/A"))
            self.folder_value_label.setText(self.tr("N/A"))
            self.created_by_value_label.setText(self.tr("N/A"))
            self.status_combo.clear()
            return

        self.project_id_value_label.setText(self.client_info.get('project_identifier', self.tr('N/A')))

        country_name = self.client_info.get('country', self.tr('N/A'))
        if isinstance(country_name, dict): # If full country object was passed
            country_name = country_name.get('country_name', self.tr('N/A'))
        self.country_value_label.setText(country_name)

        city_name = self.client_info.get('city', self.tr('N/A'))
        if isinstance(city_name, dict): # If full city object was passed
            city_name = city_name.get('city_name', self.tr('N/A'))
        self.city_value_label.setText(city_name)

        price = self.client_info.get('price', 0.0)
        self.price_value_label.setText(f"{price:.2f} €" if price is not None else self.tr('N/A'))

        created_at_str = self.client_info.get('creation_date', self.client_info.get('created_at'))
        date_display = self.tr('N/A')
        if created_at_str:
            try:
                # Handle both pre-formatted 'YYYY-MM-DD' and ISO datetime strings
                if 'T' in created_at_str: # Likely ISO format
                    dt_obj = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                    date_display = dt_obj.strftime('%Y-%m-%d')
                else: # Assume 'YYYY-MM-DD'
                    datetime.strptime(created_at_str, '%Y-%m-%d') # Validate format
                    date_display = created_at_str
            except ValueError:
                logging.warning(f"Invalid date format for created_at: {created_at_str}")
                date_display = created_at_str # Show raw if parsing fails
        self.date_value_label.setText(date_display)

        self.category_value_label.setText(self.client_info.get('category', self.tr('N/A')))
        self.distributor_info_value_label.setText(self.client_info.get('distributor_info', self.tr('N/A')))
        self.need_value_label.setText(self.client_info.get('primary_need_description', self.tr('N/A')))

        folder_path_relative = self.client_info.get('base_folder_path', self.client_info.get('default_base_folder_path', self.tr('N/A')))
        if folder_path_relative != self.tr('N/A') and self.app_root_dir:
            abs_folder_path = os.path.join(self.app_root_dir, folder_path_relative)
            self.folder_value_label.setText(f"<a href='file:///{abs_folder_path}'>{folder_path_relative}</a>")
        else:
            self.folder_value_label.setText(folder_path_relative)

        created_by_user_id = self.client_info.get('created_by_user_id')
        creator_name = self.tr("N/A")
        if created_by_user_id:
            try:
                user = users_crud.get_user_by_id(created_by_user_id)
                if user:
                    creator_name = user.get('full_name', user.get('username', self.tr("Inconnu")))
            except Exception as e:
                logging.error(f"Error fetching creator's name: {e}")
        self.created_by_value_label.setText(creator_name)

        # Populate status combo
        self.status_combo.blockSignals(True)
        self.status_combo.clear()
        current_client_status_id = self.client_info.get('status_id')
        selected_index = 0
        try:
            statuses = db_manager.get_all_status_settings(type_filter='Client')
            if statuses:
                for i, status_dict in enumerate(statuses):
                    self.status_combo.addItem(status_dict['status_name'], status_dict['status_id'])
                    if status_dict['status_id'] == current_client_status_id:
                        selected_index = i
            else:
                self.status_combo.addItem(self.tr("Aucun statut défini"), None)
        except Exception as e:
            logging.error(f"Error loading statuses for client details: {e}")
            self.status_combo.addItem(self.tr("Erreur chargement statuts"), None)

        self.status_combo.setCurrentIndex(selected_index)
        self.status_combo.blockSignals(False)

        # Connect status change if not already connected or if logic requires it here
        # self.status_combo.currentIndexChanged.connect(self.on_status_changed_slot) # Assuming such a slot exists

        # Setup client statuses section (checkboxes etc.)
        self._setup_client_statuses_section()
        logging.info("Client details layout populated, including statuses.")

    def _setup_client_statuses_section(self):
        """Sets up the UI for displaying and modifying client statuses."""
        # Clear previous status widgets if any (important for refresh_display)
        if hasattr(self, 'client_statuses_layout'):
            while self.client_statuses_layout.count():
                item = self.client_statuses_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
        else:
            # If the layout doesn't even exist, we can't proceed. Log an error.
            logging.error("ClientMainWidget._setup_client_statuses_section: client_statuses_layout is missing.")
            return

        if not self.client_info:
            return

        # --- Referent Status ---
        self.is_referent_checkbox = QCheckBox(self.tr("Référent"))
        # Determine initial state from self.current_referent_details
        is_currently_referent_active = False
        if self.current_referent_details and self.current_referent_details.get('is_active'):
            is_currently_referent_active = True
        self.is_referent_checkbox.setChecked(is_currently_referent_active)
        self.is_referent_checkbox.toggled.connect(self.on_referent_status_toggled)
        self.client_statuses_layout.addWidget(self.is_referent_checkbox)

        # Hide the old referent status label and related buttons as the checkbox supersedes their main function.
        if hasattr(self, 'referent_status_label'): self.referent_status_label.setVisible(False)
        if hasattr(self, 'manage_referent_btn') and self.manage_referent_btn.parentWidget() is self.action_buttons_layout: # Check if it's still there
            self.manage_referent_btn.setVisible(False) # Or remove from layout: self.action_buttons_layout.removeWidget(self.manage_referent_btn)

        # generate_referents_report_btn is kept visible in action_buttons_layout.


        # --- Distributor Status ---
        self.is_distributor_checkbox = QCheckBox(self.tr("Distributeur"))
        is_currently_distributor = (self.client_info.get('category') == 'Distributeur')

        self.is_distributor_checkbox.blockSignals(True) # Bloquer les signaux
        self.is_distributor_checkbox.setChecked(is_currently_distributor)
        self.is_distributor_checkbox.blockSignals(False) # Débloquer les signaux

        self.is_distributor_checkbox.toggled.connect(self.on_distributor_status_toggled)
        self.client_statuses_layout.addWidget(self.is_distributor_checkbox)

        # The mark_distributor_btn functionality is now handled by this checkbox toggle.
        # It will be removed from the action_buttons_layout.

        # Add more statuses here as QCheckBoxes if needed
        # e.g., self.is_vip_checkbox = QCheckBox(self.tr("VIP"))
        # self.client_statuses_layout.addWidget(self.is_vip_checkbox)

        self.client_statuses_layout.addStretch()
        self._apply_permissions_to_statuses() # Apply permissions specifically to status checkboxes

    def on_referent_status_toggled(self, checked):
        if not self.client_info or not self.client_info.get('client_id'): return
        client_id = self.client_info['client_id']

        # This is a simplified interaction. A real scenario might open ReferentDetailsDialog
        # or require more complex logic if being a referent has associated data.
        # For now, directly try to activate/deactivate.
        if not self.client_controller:
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Contrôleur client non disponible."))
            self.is_referent_checkbox.setChecked(not checked) # Revert
            return

        try:
            current_referent_profile = self.client_controller.get_referent_profile_by_client_id(client_id, include_inactive=True)

            if checked: # User wants to make this client a referent or activate existing
                if current_referent_profile:
                    if not current_referent_profile.get('is_active'):
                        # Profile exists and is inactive, so activate it
                        result = self.client_controller.set_referent_status(current_referent_profile['referent_id'], True, self.current_user_id)
                        if not result.get('success'):
                            raise Exception(result.get('error', self.tr("Échec de l'activation du référent.")))
                    # If already active, do nothing more here, state is already correct
                else:
                    # No profile exists, need to create one. This requires more info (country, city etc.)
                    # which the checkbox alone cannot provide.
                    # Option 1: Open the ReferentDetailsDialog to gather full info.
                    # Option 2: Create a very basic referent profile (might be problematic if fields are required).
                    # Option 3: Inform user and revert checkbox (simplest for now if dialog is too much change).

                    # Let's try Option 2: Create with client's primary country (if available)
                    client_country_id = self.client_info.get('country_id')
                    if not client_country_id:
                        QMessageBox.warning(self, self.tr("Données Manquantes"), self.tr("Le pays principal du client n'est pas défini. Impossible de créer un profil référent basique."))
                        raise Exception(self.tr("Pays du client non défini.")) # Will be caught by general except

                    creation_result = self.client_controller.make_client_referent(
                        client_id=client_id,
                        country_id=client_country_id, # Use client's country
                        region_name=None, # Basic profile
                        city_name=None,   # Basic profile
                        notes=self.tr("Profil référent créé via activation par case à cocher."),
                        user_id=self.current_user_id
                    )
                    if not creation_result.get('success'):
                        raise Exception(creation_result.get('error', self.tr("Échec de la création du profil référent.")))
            else: # User wants to deactivate referent status
                if current_referent_profile and current_referent_profile.get('is_active'):
                    result = self.client_controller.set_referent_status(current_referent_profile['referent_id'], False, self.current_user_id)
                    if not result.get('success'):
                        raise Exception(result.get('error', self.tr("Échec de la désactivation du référent.")))
                # If no active profile, do nothing, state is already correct (not active)

            # Refresh self.current_referent_details and checkbox state to be sure
            self.current_referent_details = self.client_controller.get_referent_profile_by_client_id(client_id, include_inactive=True)
            is_active_after_toggle = bool(self.current_referent_details and self.current_referent_details.get('is_active'))

            # Block signals to prevent re-triggering this handler
            self.is_referent_checkbox.blockSignals(True)
            self.is_referent_checkbox.setChecked(is_active_after_toggle)
            self.is_referent_checkbox.blockSignals(False)


            client_management_signals.show_notification.emit(self.tr("Statut Référent"), self.tr("Statut référent mis à jour."), 'SUCCESS')

        except Exception as e:
            logging.error(f"Error toggling referent status for client {client_id}: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Impossible de mettre à jour le statut référent: {0}").format(str(e)))
            # Revert checkbox state carefully
            self.is_referent_checkbox.blockSignals(True)
            self.is_referent_checkbox.setChecked(not checked)
            self.is_referent_checkbox.blockSignals(False)



    def on_distributor_status_toggled(self, checked):
        if not self.client_info or not self.client_info.get('client_id'): return
        client_id = self.client_info['client_id']
        new_category = 'Distributeur' if checked else self.client_info.get('original_category_before_distributor', 'Standard') # 'Standard' or some default

        update_payload = {'category': new_category}
        if checked: # Becoming a distributor
            # Prompt for distributor_specific_info if not already set or if desired
            current_dist_info = self.client_info.get('distributor_specific_info', '')
            info_text, ok = QInputDialog.getMultiLineText(self, self.tr("Informations Distributeur"),
                                                          self.tr("Veuillez fournir des informations spécifiques au distributeur:"),
                                                          current_dist_info)
            if ok:
                update_payload['distributor_specific_info'] = info_text
                if not self.client_info.get('category') == 'Distributeur': # Store original if changing to distributor
                    self.client_info['original_category_before_distributor'] = self.client_info.get('category', 'Standard')
            else: # User cancelled setting info, so revert checkbox
                self.is_distributor_checkbox.setChecked(not checked)
                return
        else: # No longer a distributor
            update_payload['distributor_specific_info'] = None # Or ""

        try:
            if clients_crud_instance.update_client(client_id, update_payload):
                self.client_info['category'] = new_category
                if 'distributor_specific_info' in update_payload:
                     self.client_info['distributor_specific_info'] = update_payload['distributor_specific_info']

                client_management_signals.show_notification.emit(self.tr("Statut Distributeur"), self.tr("Catégorie client mise à jour."), 'SUCCESS')
                self.populate_details_layout() # Refresh to show/hide info field if structure changes
            else:
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de mettre à jour la catégorie du client."))
                self.is_distributor_checkbox.setChecked(not checked) # Revert
        except Exception as e:
            logging.error(f"Error toggling distributor status for client {client_id}: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Erreur: {0}").format(str(e)))
            self.is_distributor_checkbox.setChecked(not checked) # Revert

    def _apply_permissions_to_statuses(self):
        role_name = self.current_user_info.get('role_name') if self.current_user_info else None
        can_manage_referents = has_permission(role_name, P_REFERENTS_MANAGE)
        can_edit_full = has_permission(role_name, P_EDIT_CLIENT_FULL)

        if hasattr(self, 'is_referent_checkbox'):
            self.is_referent_checkbox.setEnabled(can_manage_referents)
        if hasattr(self, 'is_distributor_checkbox'):
            self.is_distributor_checkbox.setEnabled(can_edit_full) # Assuming full edit can change category


    def refresh_display(self, client_data_to_show):
        logging.info(f"ClientMainWidget.refresh_display called for client: {client_data_to_show.get('client_name')}")
        self.client_info = client_data_to_show

        # Update header label
        if hasattr(self, 'header_label'):
            self.header_label.setText(f"<h2>{self.client_info.get('client_name', self.tr('Client Inconnu'))}</h2>")
        if hasattr(self, 'client_info_group_box'):
             self.client_info_group_box.setTitle(self.client_info.get('client_name', self.tr("Client Information")))


        # Repopulate details
        if hasattr(self, 'populate_details_layout'):
            self.populate_details_layout()

        # Refresh referent status
        if self.client_info and self.client_info.get('client_id') and self.client_controller:
            self.current_referent_details = self.client_controller.get_referent_profile_by_client_id(
                self.client_info.get('client_id'), include_inactive=True
            )
            if hasattr(self, '_update_referent_status_display'):
                self._update_referent_status_display()

        # Reload data for all relevant tabs
        if hasattr(self, 'load_contacts'):
            self.load_contacts()
        if hasattr(self, 'documents_tab_widget_ref') and hasattr(self.documents_tab_widget_ref, 'refresh_tab_data'):
            self.documents_tab_widget_ref.client_info = self.client_info # Ensure tab has latest client_info
            self.documents_tab_widget_ref.refresh_tab_data()
        if hasattr(self, 'products_tab_widget_ref') and hasattr(self.products_tab_widget_ref, 'refresh_tab_data'):
            self.products_tab_widget_ref.client_info = self.client_info
            self.products_tab_widget_ref.refresh_tab_data()
        if hasattr(self, 'document_notes_tab_widget_ref') and hasattr(self.document_notes_tab_widget_ref, 'refresh_tab_data'):
            self.document_notes_tab_widget_ref.client_info = self.client_info
            self.document_notes_tab_widget_ref.refresh_tab_data()
        if hasattr(self, 'product_dimensions_tab_widget_ref') and hasattr(self.product_dimensions_tab_widget_ref, 'refresh_tab_data'):
            self.product_dimensions_tab_widget_ref.client_info = self.client_info
            self.product_dimensions_tab_widget_ref.refresh_tab_data()
        if hasattr(self, 'sav_tab_widget_ref') and hasattr(self.sav_tab_widget_ref, 'refresh_tab_data'):
            self.sav_tab_widget_ref.client_info = self.client_info
            self.sav_tab_widget_ref.refresh_tab_data()
        if hasattr(self, 'billing_tab_widget_ref') and hasattr(self.billing_tab_widget_ref, 'refresh_data'):
            self.billing_tab_widget_ref.client_info = self.client_info
            self.billing_tab_widget_ref.refresh_data()

        # Assignments related refreshes (if these methods exist, otherwise they are part of the stubbing below)
        if hasattr(self, 'load_assigned_vendors_personnel'): self.load_assigned_vendors_personnel()
        if hasattr(self, 'load_assigned_technicians'): self.load_assigned_technicians()
        if hasattr(self, 'load_assigned_transporters'): self.load_assigned_transporters()
        if hasattr(self, 'load_assigned_freight_forwarders'): self.load_assigned_freight_forwarders()
        if hasattr(self, 'load_projects_for_mta_combo'): self.load_projects_for_mta_combo() # This will trigger MTA table refresh if connected

        if hasattr(self, '_apply_permissions'):
            self._apply_permissions()
        logging.info("ClientMainWidget display refreshed.")

    # --- Stubs for potentially missing methods ---
    def update_sav_tab_visibility(self):
        logging.debug("ClientMainWidget.update_sav_tab_visibility (stub) called.")
        if hasattr(self, 'sav_tab_widget_ref') and hasattr(self.sav_tab_widget_ref, 'update_sav_tab_visibility_and_load_data'):
            self.sav_tab_widget_ref.update_sav_tab_visibility_and_load_data()
        else:
            logging.warning("SAV tab or its update method not found.")

    def load_assigned_vendors_personnel(self):
        if not hasattr(self, 'assigned_vendors_table'):
            logging.error("assigned_vendors_table not initialized in ClientMainWidget.")
            return

        self.assigned_vendors_table.setRowCount(0)
        self.assigned_vendors_table.setSortingEnabled(False) # Disable sorting during population
        client_id = self.client_info.get('client_id')
        if not client_id:
            logging.warning("load_assigned_vendors_personnel: No client_id provided.")
            return

        try:
            # Assuming role_filter=None fetches all types of personnel or vendors
            assigned_list = db_manager.get_assigned_personnel_for_client(client_id, role_filter=None)
            if assigned_list is None: # Check for None specifically, as an empty list is valid
                assigned_list = []

            self.assigned_vendors_table.setRowCount(len(assigned_list))
            for row, item_data in enumerate(assigned_list):
                # self.assigned_vendors_table.insertRow(row) # Not needed if setRowCount is used

                name_item = QTableWidgetItem(item_data.get('personnel_name', self.tr("N/A")))
                name_item.setData(Qt.UserRole, item_data.get('assignment_id')) # Store assignment_id for removal
                self.assigned_vendors_table.setItem(row, 0, name_item)

                self.assigned_vendors_table.setItem(row, 1, QTableWidgetItem(item_data.get('role_in_project', self.tr("N/A"))))
                self.assigned_vendors_table.setItem(row, 2, QTableWidgetItem(item_data.get('personnel_email', self.tr("N/A"))))
                self.assigned_vendors_table.setItem(row, 3, QTableWidgetItem(item_data.get('personnel_phone', self.tr("N/A"))))
        except Exception as e:
            logging.error(f"Error loading assigned vendors/personnel for client {client_id}: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Chargement"), self.tr("Impossible de charger le personnel assigné: {0}").format(str(e)))
        finally:
            self.assigned_vendors_table.setSortingEnabled(True)
            self.update_assigned_vendors_buttons_state() # Update button state after loading

    def load_assigned_technicians(self):
        if not hasattr(self, 'assigned_technicians_table'):
            logging.error("assigned_technicians_table not initialized in ClientMainWidget.")
            return

        self.assigned_technicians_table.setRowCount(0)
        self.assigned_technicians_table.setSortingEnabled(False)
        client_id = self.client_info.get('client_id')
        if not client_id:
            logging.warning("load_assigned_technicians: No client_id provided.")
            return

        try:
            # Assuming "Technicien" or "technical_manager" is the role string stored in DB for technicians
            # This might need adjustment based on actual role names used.
            assigned_list = db_manager.get_assigned_personnel_for_client(client_id, role_filter="Technicien") # Or "technical_manager"
            if assigned_list is None: assigned_list = []

            self.assigned_technicians_table.setRowCount(len(assigned_list))
            for row, item_data in enumerate(assigned_list):
                name_item = QTableWidgetItem(item_data.get('personnel_name', self.tr("N/A")))
                name_item.setData(Qt.UserRole, item_data.get('assignment_id'))
                self.assigned_technicians_table.setItem(row, 0, name_item)
                self.assigned_technicians_table.setItem(row, 1, QTableWidgetItem(item_data.get('role_in_project', self.tr("N/A"))))
                self.assigned_technicians_table.setItem(row, 2, QTableWidgetItem(item_data.get('personnel_email', self.tr("N/A"))))
                self.assigned_technicians_table.setItem(row, 3, QTableWidgetItem(item_data.get('personnel_phone', self.tr("N/A"))))
        except Exception as e:
            logging.error(f"Error loading assigned technicians for client {client_id}: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Chargement"), self.tr("Impossible de charger les techniciens assignés: {0}").format(str(e)))
        finally:
            self.assigned_technicians_table.setSortingEnabled(True)
            self.update_assigned_technicians_buttons_state()

    def load_assigned_transporters(self):
        if not hasattr(self, 'assigned_transporters_table'):
            logging.error("assigned_transporters_table not initialized.")
            return
        self.assigned_transporters_table.setRowCount(0)
        self.assigned_transporters_table.setSortingEnabled(False)
        client_id = self.client_info.get('client_id')
        if not client_id: return

        try:
            assigned_list = db_manager.get_assigned_transporters_for_client(client_id)
            if assigned_list is None: assigned_list = []

            self.assigned_transporters_table.setRowCount(len(assigned_list))
            for row, item_data in enumerate(assigned_list):
                name_item = QTableWidgetItem(item_data.get('transporter_name', self.tr("N/A")))
                # Store client_transporter_id (link ID) not transporter_id (global ID)
                name_item.setData(Qt.UserRole, item_data.get('client_transporter_id'))
                self.assigned_transporters_table.setItem(row, 0, name_item)
                self.assigned_transporters_table.setItem(row, 1, QTableWidgetItem(item_data.get('contact_person', self.tr("N/A"))))
                self.assigned_transporters_table.setItem(row, 2, QTableWidgetItem(item_data.get('phone', self.tr("N/A"))))
                self.assigned_transporters_table.setItem(row, 3, QTableWidgetItem(item_data.get('transport_details', self.tr("N/A"))))

                cost_estimate_val = item_data.get('cost_estimate', 0.0)
                cost_item = QTableWidgetItem(f"{cost_estimate_val:.2f} €" if cost_estimate_val is not None else self.tr("N/A"))
                cost_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.assigned_transporters_table.setItem(row, 4, cost_item)

                email_status = item_data.get('email_status', 'Pending')
                btn_send_email = QPushButton()
                if email_status == "Sent":
                    btn_send_email.setText(self.tr("Email Envoyé"))
                    btn_send_email.setStyleSheet("background-color: lightgray; color: black;")
                    btn_send_email.setEnabled(False)
                elif email_status == "Failed":
                    btn_send_email.setText(self.tr("Renvoyer Email (Échec)"))
                    btn_send_email.setStyleSheet("background-color: orange; color: black;")
                    btn_send_email.clicked.connect(lambda checked, r=row, ct_id=item_data.get('client_transporter_id'): self.open_carrier_email_dialog_from_table(r, ct_id))
                else: # Pending or any other status
                    btn_send_email.setText(self.tr("Envoyer Email"))
                    btn_send_email.setStyleSheet("background-color: green; color: white;")
                    btn_send_email.clicked.connect(lambda checked, r=row, ct_id=item_data.get('client_transporter_id'): self.open_carrier_email_dialog_from_table(r, ct_id))

                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.addWidget(btn_send_email)
                action_layout.setContentsMargins(0, 0, 0, 0)
                action_layout.setAlignment(Qt.AlignCenter)
                self.assigned_transporters_table.setCellWidget(row, 5, action_widget)

        except Exception as e:
            logging.error(f"Error loading assigned transporters for client {client_id}: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Chargement"), self.tr("Impossible de charger les transporteurs assignés: {0}").format(str(e)))
        finally:
            self.assigned_transporters_table.setSortingEnabled(True)
            self.update_assigned_transporters_buttons_state()

    def load_assigned_freight_forwarders(self):
        if not hasattr(self, 'assigned_forwarders_table'):
            logging.error("assigned_forwarders_table not initialized.")
            return
        self.assigned_forwarders_table.setRowCount(0)
        self.assigned_forwarders_table.setSortingEnabled(False)
        client_id = self.client_info.get('client_id')
        if not client_id: return

        try:
            assigned_list = db_manager.get_assigned_forwarders_for_client(client_id)
            if assigned_list is None: assigned_list = []

            self.assigned_forwarders_table.setRowCount(len(assigned_list))
            for row, item_data in enumerate(assigned_list):
                name_item = QTableWidgetItem(item_data.get('forwarder_name', self.tr("N/A")))
                # Store client_forwarder_id (link ID)
                name_item.setData(Qt.UserRole, item_data.get('client_forwarder_id'))
                self.assigned_forwarders_table.setItem(row, 0, name_item)
                self.assigned_forwarders_table.setItem(row, 1, QTableWidgetItem(item_data.get('contact_person', self.tr("N/A"))))
                self.assigned_forwarders_table.setItem(row, 2, QTableWidgetItem(item_data.get('phone', self.tr("N/A"))))
                self.assigned_forwarders_table.setItem(row, 3, QTableWidgetItem(item_data.get('task_description', self.tr("N/A"))))

                cost_estimate_val = item_data.get('cost_estimate', 0.0)
                cost_item = QTableWidgetItem(f"{cost_estimate_val:.2f} €" if cost_estimate_val is not None else self.tr("N/A"))
                cost_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.assigned_forwarders_table.setItem(row, 4, cost_item)
        except Exception as e:
            logging.error(f"Error loading assigned freight forwarders for client {client_id}: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Chargement"), self.tr("Impossible de charger les transitaires assignés: {0}").format(str(e)))
        finally:
            self.assigned_forwarders_table.setSortingEnabled(True)
            self.update_assigned_forwarders_buttons_state()

    def update_assigned_vendors_buttons_state(self):
        role_name = self.current_user_info.get('role_name') if self.current_user_info else None
        can_manage_assignments = has_permission(role_name, P_MANAGE_CLIENT_ASSIGNMENTS)
        if hasattr(self, 'remove_assigned_vendor_btn') and hasattr(self, 'assigned_vendors_table'):
            has_selection = bool(self.assigned_vendors_table.selectedItems())
            self.remove_assigned_vendor_btn.setEnabled(has_selection and can_manage_assignments)

    def update_assigned_technicians_buttons_state(self):
        role_name = self.current_user_info.get('role_name') if self.current_user_info else None
        can_manage_assignments = has_permission(role_name, P_MANAGE_CLIENT_ASSIGNMENTS)
        if hasattr(self, 'remove_assigned_technician_btn') and hasattr(self, 'assigned_technicians_table'):
            has_selection = bool(self.assigned_technicians_table.selectedItems())
            self.remove_assigned_technician_btn.setEnabled(has_selection and can_manage_assignments)

    def update_assigned_transporters_buttons_state(self):
        role_name = self.current_user_info.get('role_name') if self.current_user_info else None
        can_manage_assignments = has_permission(role_name, P_MANAGE_CLIENT_ASSIGNMENTS)
        if hasattr(self, 'remove_assigned_transporter_btn') and hasattr(self, 'assigned_transporters_table'):
            has_selection = bool(self.assigned_transporters_table.selectedItems())
            self.remove_assigned_transporter_btn.setEnabled(has_selection and can_manage_assignments)

    def update_assigned_forwarders_buttons_state(self):
        role_name = self.current_user_info.get('role_name') if self.current_user_info else None
        can_manage_assignments = has_permission(role_name, P_MANAGE_CLIENT_ASSIGNMENTS)
        if hasattr(self, 'remove_assigned_forwarder_btn') and hasattr(self, 'assigned_forwarders_table'):
            has_selection = bool(self.assigned_forwarders_table.selectedItems())
            self.remove_assigned_forwarder_btn.setEnabled(has_selection and can_manage_assignments)

    def load_projects_for_mta_combo(self):
        logging.debug("ClientMainWidget.load_projects_for_mta_combo (stub) called.")
        if hasattr(self, 'mta_project_selector_combo'):
            self.mta_project_selector_combo.clear()
            self.mta_project_selector_combo.addItem(self.tr("-- Sélectionner Commande/Projet --"), None)
            # Add actual project/order loading logic here
            client_id = self.client_info.get('client_id')
            if client_id:
                try:
                    # Assuming projects_crud.get_projects_for_client returns a list of dicts with 'project_id' and 'project_name' or 'project_identifier'
                    orders = projects_crud.get_projects_by_client_id(client_id) # Or a specific "orders" CRUD
                    if orders:
                        for order in orders:
                            # Use project_identifier if available, else project_name
                            display_name = order.get('project_identifier') or order.get('project_name', f"ID: {order.get('project_id')}")
                            self.mta_project_selector_combo.addItem(display_name, order.get('project_id'))
                except Exception as e:
                    logging.error(f"Error loading projects/orders for MTA combo: {e}", exc_info=True)
        self.handle_mta_project_selection_changed() # Refresh table based on (possibly empty) combo

    def handle_mta_project_selection_changed(self):
        logging.debug("ClientMainWidget.handle_mta_project_selection_changed (stub) called.")
        if hasattr(self, 'assigned_mta_table'):
             self.assigned_mta_table.setRowCount(0) # Clear MTA table
        # Add logic to load MTAs for selected project/order
        selected_project_id = None
        if hasattr(self, 'mta_project_selector_combo'):
            selected_project_id = self.mta_project_selector_combo.currentData()

        if hasattr(self, 'add_assigned_mta_btn'):
            role_name = self.current_user_info.get('role_name') if self.current_user_info else None
            can_manage_assignments = has_permission(role_name, P_MANAGE_CLIENT_ASSIGNMENTS)
            self.add_assigned_mta_btn.setEnabled(selected_project_id is not None and can_manage_assignments)

        if selected_project_id:
            self.load_assigned_money_transfer_agents(selected_project_id)
        else:
            if hasattr(self, 'assigned_mta_table'):
                self.assigned_mta_table.setRowCount(0) # Clear table if no project selected
        self.update_mta_buttons_state()

    def load_assigned_money_transfer_agents(self, order_id):
        if not hasattr(self, 'assigned_mta_table'):
            logging.error("assigned_mta_table not initialized.")
            return
        self.assigned_mta_table.setRowCount(0)
        self.assigned_mta_table.setSortingEnabled(False)

        try:
            assigned_agents = coma_crud.get_agents_for_order(order_id)
            if assigned_agents is None: assigned_agents = []

            self.assigned_mta_table.setRowCount(len(assigned_agents))
            for row, agent_data in enumerate(assigned_agents):
                # client_order_money_transfer_agent_id is the assignment ID
                assignment_id = agent_data.get('client_order_money_transfer_agent_id')

                name_item = QTableWidgetItem(agent_data.get('agent_name', self.tr("N/A")))
                name_item.setData(Qt.UserRole, assignment_id)
                self.assigned_mta_table.setItem(row, 0, name_item)

                self.assigned_mta_table.setItem(row, 1, QTableWidgetItem(agent_data.get('agent_type', self.tr("N/A"))))
                self.assigned_mta_table.setItem(row, 2, QTableWidgetItem(agent_data.get('email', self.tr("N/A"))))
                self.assigned_mta_table.setItem(row, 3, QTableWidgetItem(agent_data.get('phone', self.tr("N/A"))))
                self.assigned_mta_table.setItem(row, 4, QTableWidgetItem(agent_data.get('assignment_details', self.tr("N/A"))))

                fees_val = agent_data.get('estimated_fees', 0.0)
                fees_item = QTableWidgetItem(f"{fees_val:.2f} €" if fees_val is not None else self.tr("N/A"))
                fees_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.assigned_mta_table.setItem(row, 5, fees_item)

                # Placeholder for email status and actions button, similar to transporters
                # For now, just a simple status text
                self.assigned_mta_table.setItem(row, 6, QTableWidgetItem(self.tr("N/A"))) # Email Status
                self.assigned_mta_table.setItem(row, 7, QTableWidgetItem(self.tr("N/A"))) # Actions
        except Exception as e:
            logging.error(f"Error loading assigned MTAs for order {order_id}: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Chargement"), self.tr("Impossible de charger les agents de transfert assignés: {0}").format(str(e)))
        finally:
            self.assigned_mta_table.setSortingEnabled(True)
            self.update_mta_buttons_state()


    def update_mta_buttons_state(self):
        role_name = self.current_user_info.get('role_name') if self.current_user_info else None
        can_manage_assignments = has_permission(role_name, P_MANAGE_CLIENT_ASSIGNMENTS)

        project_selected = False
        if hasattr(self, 'mta_project_selector_combo'):
            project_selected = self.mta_project_selector_combo.currentData() is not None

        mta_selected = False
        if hasattr(self, 'assigned_mta_table'):
            mta_selected = bool(self.assigned_mta_table.selectedItems())

        if hasattr(self, 'add_assigned_mta_btn'):
            self.add_assigned_mta_btn.setEnabled(project_selected and can_manage_assignments)
        if hasattr(self, 'remove_assigned_mta_btn'):
            self.remove_assigned_mta_btn.setEnabled(project_selected and mta_selected and can_manage_assignments)

    def handle_add_assigned_vendor(self):
        if not self.client_info or not self.client_info.get('client_id'):
            QMessageBox.warning(self, self.tr("Erreur Client"), self.tr("ID Client non disponible."))
            return
        if not self.default_company_id: # Should be set in __init__
            QMessageBox.warning(self, self.tr("Configuration Requise"), self.tr("Société par défaut non configurée."))
            return

        # Assuming AssignPersonnelDialog is correctly imported
        dialog = AssignPersonnelDialog(
            client_id=self.client_info['client_id'],
            role_filter=None, # No specific role filter for general personnel/vendors
            company_id=self.default_company_id,
            parent=self
        )
        if dialog.exec_() == QDialog.Accepted:
            # AssignPersonnelDialog should handle the actual DB assignment via db_manager.assign_personnel_to_client
            self.load_assigned_vendors_personnel() # Refresh the table
            client_management_signals.show_notification.emit(self.tr("Succès"), self.tr("Personnel assigné avec succès."), 'SUCCESS')

    def handle_remove_assigned_vendor(self):
        selected_items = self.assigned_vendors_table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, self.tr("Sélection Requise"), self.tr("Veuillez sélectionner un membre du personnel à retirer."))
            return

        assignment_id = self.assigned_vendors_table.item(selected_items[0].row(), 0).data(Qt.UserRole)
        personnel_name = self.assigned_vendors_table.item(selected_items[0].row(), 0).text()

        if assignment_id is None:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de récupérer l'ID de l'assignation."))
            return

        reply = QMessageBox.question(self, self.tr("Confirmer Suppression"),
                                     self.tr("Êtes-vous sûr de vouloir retirer {0} de ce client?").format(personnel_name),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                # Assuming db_manager.unassign_personnel_from_client(assignment_id) exists and returns bool
                success = db_manager.unassign_personnel_from_client(assignment_id)
                if success:
                    self.load_assigned_vendors_personnel()
                    client_management_signals.show_notification.emit(self.tr("Succès"), self.tr("Personnel retiré avec succès."), 'SUCCESS')
                else:
                    QMessageBox.warning(self, self.tr("Erreur DB"), self.tr("Impossible de retirer le membre du personnel."))
            except Exception as e:
                logging.error(f"Error removing assigned personnel (assignment_id: {assignment_id}): {e}", exc_info=True)
                QMessageBox.critical(self, self.tr("Erreur"), self.tr("Une erreur est survenue: {0}").format(str(e)))

    def handle_add_assigned_technician(self):
        if not self.client_info or not self.client_info.get('client_id'):
            QMessageBox.warning(self, self.tr("Erreur Client"), self.tr("ID Client non disponible."))
            return
        if not self.default_company_id:
            QMessageBox.warning(self, self.tr("Configuration Requise"), self.tr("Société par défaut non configurée."))
            return

        # The role_filter "Technicien" should match what's used in get_assigned_personnel_for_client for technicians
        dialog = AssignPersonnelDialog(
            client_id=self.client_info['client_id'],
            role_filter="Technicien", # Crucial to filter for personnel who are technicians
            company_id=self.default_company_id,
            parent=self
        )
        if dialog.exec_() == QDialog.Accepted:
            self.load_assigned_technicians()
            client_management_signals.show_notification.emit(self.tr("Succès"), self.tr("Technicien assigné avec succès."), 'SUCCESS')

    def handle_remove_assigned_technician(self):
        selected_items = self.assigned_technicians_table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, self.tr("Sélection Requise"), self.tr("Veuillez sélectionner un technicien à retirer."))
            return

        assignment_id = self.assigned_technicians_table.item(selected_items[0].row(), 0).data(Qt.UserRole)
        technician_name = self.assigned_technicians_table.item(selected_items[0].row(), 0).text()

        if assignment_id is None:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de récupérer l'ID de l'assignation du technicien."))
            return

        reply = QMessageBox.question(self, self.tr("Confirmer Suppression"),
                                     self.tr("Êtes-vous sûr de vouloir retirer {0} de ce client?").format(technician_name),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                success = db_manager.unassign_personnel_from_client(assignment_id) # Same function as for vendors
                if success:
                    self.load_assigned_technicians()
                    client_management_signals.show_notification.emit(self.tr("Succès"), self.tr("Technicien retiré avec succès."), 'SUCCESS')
                else:
                    QMessageBox.warning(self, self.tr("Erreur DB"), self.tr("Impossible de retirer le technicien."))
            except Exception as e:
                logging.error(f"Error removing assigned technician (assignment_id: {assignment_id}): {e}", exc_info=True)
                QMessageBox.critical(self, self.tr("Erreur"), self.tr("Une erreur est survenue: {0}").format(str(e)))

    def handle_add_assigned_transporter(self):
        if not self.client_info or not self.client_info.get('client_id'):
            QMessageBox.warning(self, self.tr("Erreur Client"), self.tr("ID Client non disponible."))
            return
        dialog = AssignTransporterDialog(client_id=self.client_info['client_id'], parent=self)
        if dialog.exec_() == QDialog.Accepted:
            # AssignTransporterDialog should handle the DB interaction via db_manager.assign_transporter_to_client
            self.load_assigned_transporters()
            client_management_signals.show_notification.emit(self.tr("Succès"), self.tr("Transporteur assigné avec succès."), 'SUCCESS')

    def handle_remove_assigned_transporter(self):
        selected_items = self.assigned_transporters_table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, self.tr("Sélection Requise"), self.tr("Veuillez sélectionner un transporteur à retirer."))
            return

        # client_transporter_id is stored in UserRole of the first item (Name)
        client_transporter_id = self.assigned_transporters_table.item(selected_items[0].row(), 0).data(Qt.UserRole)
        transporter_name = self.assigned_transporters_table.item(selected_items[0].row(), 0).text()

        if client_transporter_id is None:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de récupérer l'ID de l'assignation du transporteur."))
            return

        reply = QMessageBox.question(self, self.tr("Confirmer Suppression"),
                                     self.tr("Êtes-vous sûr de vouloir retirer le transporteur {0} de ce client?").format(transporter_name),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                success = db_manager.unassign_transporter_from_client(client_transporter_id)
                if success:
                    self.load_assigned_transporters()
                    client_management_signals.show_notification.emit(self.tr("Succès"), self.tr("Transporteur retiré avec succès."), 'SUCCESS')
                else:
                    QMessageBox.warning(self, self.tr("Erreur DB"), self.tr("Impossible de retirer le transporteur."))
            except Exception as e:
                logging.error(f"Error removing assigned transporter (link_id: {client_transporter_id}): {e}", exc_info=True)
                QMessageBox.critical(self, self.tr("Erreur"), self.tr("Une erreur est survenue: {0}").format(str(e)))

    def open_carrier_email_dialog_from_table(self, row_index, client_transporter_id):
        # This method replaces the previous open_carrier_email_dialog to ensure ct_id is correctly passed
        try:
            transporter_name_item = self.assigned_transporters_table.item(row_index, 0)
            if not transporter_name_item:
                QMessageBox.warning(self, self.tr("Erreur Données"), self.tr("Impossible de récupérer le nom du transporteur."))
                return
            transporter_name = transporter_name_item.text()

            # Fetch the specific assignment to get email, as it might not be directly in table for all cases
            # However, the assignment_id (client_transporter_id) is what we need for the dialog.
            # The dialog itself should fetch the email or prompt if not found.

            # We need to find the email for this transporter to pre-fill the dialog.
            # The `assigned_list` was used before, let's re-fetch or assume it's in item_data if `load_assigned_transporters` stores it.
            # For now, let's try to get it from db_manager if not directly available.
            # This part might need refinement based on how `CarrierEmailDialog` expects data.
            transporter_details = db_manager.get_transporter_assignment_details(client_transporter_id) # Assuming this function exists
            transporter_email = transporter_details.get('email') if transporter_details else None

            if not transporter_email:
                 # Fallback: try to get contact_person which might be an email
                contact_person_cell = self.assigned_transporters_table.item(row_index, 1)
                if contact_person_cell:
                    contact_person_text = contact_person_cell.text()
                    if '@' in contact_person_text and '.' in contact_person_text.split('@')[-1]:
                        transporter_email = contact_person_text

            if not transporter_email:
                email_text, ok = QInputDialog.getText(self, self.tr("Email du Transporteur Manquant"), self.tr("L'email pour {0} n'est pas trouvé. Veuillez le saisir:").format(transporter_name))
                if ok and email_text.strip():
                    transporter_email = email_text.strip()
                else:
                    QMessageBox.information(self, self.tr("Annulé"), self.tr("Envoi d'email annulé car l'email du destinataire est manquant."))
                    self.load_assigned_transporters()
                    return

            client_name = self.client_info.get("client_name", self.tr("Notre Client"))
            email_dialog = CarrierEmailDialog(
                carrier_name=transporter_name,
                carrier_email=transporter_email,
                client_name=client_name,
                client_transporter_id=client_transporter_id,
                parent=self,
                config=self.config
            )
            email_dialog.exec_()
            self.load_assigned_transporters() # Refresh to update email status
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur Dialogue Email"), self.tr("Une erreur est survenue lors de l'ouverture du dialogue d'email: {0}").format(str(e)))


    def handle_add_assigned_forwarder(self):
        if not self.client_info or not self.client_info.get('client_id'):
            QMessageBox.warning(self, self.tr("Erreur Client"), self.tr("ID Client non disponible."))
            return
        dialog = AssignFreightForwarderDialog(client_id=self.client_info['client_id'], parent=self)
        if dialog.exec_() == QDialog.Accepted:
            # AssignFreightForwarderDialog should handle the DB interaction via db_manager.assign_freight_forwarder_to_client
            self.load_assigned_freight_forwarders()
            client_management_signals.show_notification.emit(self.tr("Succès"), self.tr("Transitaire assigné avec succès."), 'SUCCESS')

    def handle_remove_assigned_forwarder(self):
        selected_items = self.assigned_forwarders_table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, self.tr("Sélection Requise"), self.tr("Veuillez sélectionner un transitaire à retirer."))
            return

        client_forwarder_id = self.assigned_forwarders_table.item(selected_items[0].row(), 0).data(Qt.UserRole)
        forwarder_name = self.assigned_forwarders_table.item(selected_items[0].row(), 0).text()

        if client_forwarder_id is None:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de récupérer l'ID de l'assignation du transitaire."))
            return

        reply = QMessageBox.question(self, self.tr("Confirmer Suppression"),
                                     self.tr("Êtes-vous sûr de vouloir retirer le transitaire {0} de ce client?").format(forwarder_name),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                # Ensure db_manager.unassign_freight_forwarder_from_client exists
                success = db_manager.unassign_freight_forwarder_from_client(client_forwarder_id)
                if success:
                    self.load_assigned_freight_forwarders()
                    client_management_signals.show_notification.emit(self.tr("Succès"), self.tr("Transitaire retiré avec succès."), 'SUCCESS')
                else:
                    QMessageBox.warning(self, self.tr("Erreur DB"), self.tr("Impossible de retirer le transitaire."))
            except Exception as e:
                logging.error(f"Error removing assigned freight forwarder (link_id: {client_forwarder_id}): {e}", exc_info=True)
                QMessageBox.critical(self, self.tr("Erreur"), self.tr("Une erreur est survenue: {0}").format(str(e)))

    def handle_add_assigned_mta(self):
        if not self.client_info or not self.client_info.get('client_id'):
            QMessageBox.warning(self, self.tr("Erreur Client"), self.tr("ID Client non disponible."))
            return

        selected_order_id = self.mta_project_selector_combo.currentData()
        if not selected_order_id:
            QMessageBox.warning(self, self.tr("Sélection Requise"), self.tr("Veuillez d'abord sélectionner une commande/projet."))
            return

        dialog = AssignMoneyTransferAgentDialog(order_id=selected_order_id, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            # AssignMoneyTransferAgentDialog should handle DB interaction via coma_crud.assign_agent_to_order
            self.load_assigned_money_transfer_agents(selected_order_id) # Refresh the table for the current order
            client_management_signals.show_notification.emit(self.tr("Succès"), self.tr("Agent de transfert d'argent assigné avec succès."), 'SUCCESS')

    def handle_remove_assigned_mta(self):
        selected_items = self.assigned_mta_table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, self.tr("Sélection Requise"), self.tr("Veuillez sélectionner un agent à retirer."))
            return

        # The assignment ID is stored in UserRole of the first item (Name)
        assignment_id = self.assigned_mta_table.item(selected_items[0].row(), 0).data(Qt.UserRole)
        agent_name = self.assigned_mta_table.item(selected_items[0].row(), 0).text()
        selected_order_id = self.mta_project_selector_combo.currentData() # For refreshing the correct list

        if assignment_id is None:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de récupérer l'ID de l'assignation de l'agent."))
            return

        reply = QMessageBox.question(self, self.tr("Confirmer Suppression"),
                                     self.tr("Êtes-vous sûr de vouloir retirer l'agent {0} de cette commande/projet?").format(agent_name),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                # Ensure coma_crud.unassign_agent_from_order exists
                success = coma_crud.unassign_agent_from_order(assignment_id)
                if success:
                    if selected_order_id: # Refresh if an order is still selected
                        self.load_assigned_money_transfer_agents(selected_order_id)
                    else: # Clear table if no order selected (should not happen if button was enabled)
                        self.assigned_mta_table.setRowCount(0)

                    client_management_signals.show_notification.emit(self.tr("Succès"), self.tr("Agent de transfert d'argent retiré avec succès."), 'SUCCESS')
                else:
                    QMessageBox.warning(self, self.tr("Erreur DB"), self.tr("Impossible de retirer l'agent de transfert d'argent."))
            except Exception as e:
                logging.error(f"Error removing assigned MTA (assignment_id: {assignment_id}): {e}", exc_info=True)
                QMessageBox.critical(self, self.tr("Erreur"), self.tr("Une erreur est survenue: {0}").format(str(e)))

    def populate_doc_table(self): # This is a call to the DocumentsTab's method
        if hasattr(self, 'documents_tab_widget_ref') and hasattr(self.documents_tab_widget_ref, 'populate_doc_table'):
            self.documents_tab_widget_ref.populate_doc_table()
        else:
            logging.warning("ClientMainWidget: documents_tab_widget_ref or its populate_doc_table method not found.")

    # Add on_status_changed_slot if it's intended to be part of ClientMainWidget
    # def on_status_changed_slot(self, index):
    #     logging.debug(f"ClientMainWidget.on_status_changed_slot (stub) called with index {index}.")
    #     # Add logic to update client status in DB
    #     status_id = self.status_combo.itemData(index)
    #     if status_id and self.client_info.get('client_id'):
    #         try:
    #             clients_crud_instance.update_client(self.client_info['client_id'], {'status_id': status_id})
    #             self.client_info['status_id'] = status_id # Update local copy
    #             # Notify parent or refresh main client list if necessary
    #             if self.notification_manager:
    #                 self.notification_manager.show(self.tr("Statut Modifié"), self.tr("Le statut du client a été mis à jour."), type='SUCCESS')
    #         except Exception as e:
    #             logging.error(f"Error updating client status: {e}", exc_info=True)
    #             if self.notification_manager:
    #                 self.notification_manager.show(self.tr("Erreur"), self.tr("Impossible de mettre à jour le statut du client."), type='ERROR')
    #             # Revert combo to old status?
    #             # For now, just log. A full implementation would handle this better.

    def product_selected_in_products_tab(self, global_product_id: int = None):
        """
        Called when a product selection changes in ProductsTab.
        Relays this selection to ProductDimensionsTab.
        """
        logging.debug(f"ClientMainWidget: product_selected_in_products_tab received global_product_id: {global_product_id}")
        if hasattr(self, 'product_dimensions_tab_widget_ref') and \
           self.product_dimensions_tab_widget_ref is not None and \
           hasattr(self.product_dimensions_tab_widget_ref, 'select_product_in_combo'):
            self.product_dimensions_tab_widget_ref.select_product_in_combo(global_product_id)
        else:
            logging.warning("ClientMainWidget: ProductDimensionsTab reference or select_product_in_combo method not found.")

    def _populate_country_edit_combo(self, combo_box, current_country_id=None):
        combo_box.blockSignals(True)
        combo_box.clear()
        combo_box.addItem(self.tr("Sélectionner un pays..."), None)
        selected_idx = 0
        try:
            countries = db_manager.get_all_countries()
            if countries:
                for i, country in enumerate(sorted(countries, key=lambda x: x['country_name'])):
                    combo_box.addItem(country['country_name'], country['country_id'])
                    if current_country_id and country['country_id'] == current_country_id:
                        selected_idx = i + 1 # +1 because of "Sélectionner..."
        except Exception as e:
            logging.error(f"Error populating country combo box: {e}", exc_info=True)
        combo_box.setCurrentIndex(selected_idx)
        combo_box.blockSignals(False)
        # Manually trigger city update for the initially selected country
        if selected_idx > 0 and 'city_combo' in self.edit_widgets: # Ensure city_combo exists
            self._populate_city_edit_combo(self.edit_widgets['city_combo'], combo_box.currentData(), self.client_info.get('city_id'))


    def _populate_city_edit_combo(self, combo_box, country_id, current_city_id=None):
        combo_box.blockSignals(True)
        combo_box.clear()
        combo_box.addItem(self.tr("Sélectionner une ville..."), None)
        selected_idx = 0
        if country_id:
            try:
                cities = db_manager.get_cities_by_country_id(country_id) # Assuming this CRUD function exists
                if cities:
                    for i, city in enumerate(sorted(cities, key=lambda x: x['city_name'])):
                        combo_box.addItem(city['city_name'], city['city_id'])
                        if current_city_id and city['city_id'] == current_city_id:
                            selected_idx = i + 1
            except Exception as e:
                logging.error(f"Error populating city combo box for country_id {country_id}: {e}", exc_info=True)
        combo_box.setCurrentIndex(selected_idx)
        combo_box.setEnabled(country_id is not None and combo_box.count() > 1) # Enable if country selected and cities exist
        combo_box.blockSignals(False)

    def _create_styled_label(self, text): # Helper for styled labels in edit form
        label = QLabel(text)
        label.setStyleSheet("font-weight: bold; padding-right: 5px;")
        return label

    def _create_styled_value_label(self, text): # Helper for styled value labels (read-only in edit form)
        label = QLabel(text)
        label.setStyleSheet("padding: 3px; background-color: #f0f0f0; border-radius: 3px;") # Example style
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        return label
