# -*- coding: utf-8 -*-
import os
import sys
# import logging # logging is already imported
import logging
# import shutil # No longer used directly
from datetime import datetime
# import sqlite3 # No longer needed as methods are refactored to use db_manager
import math # Added for pagination

from carrier_email_dialog import CarrierEmailDialog # Added import

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QListWidget, QLineEdit,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QInputDialog, QTabWidget, QGroupBox, QMessageBox, QDialog, QApplication, # QFileDialog removed
    QSizePolicy
)
from PyQt5.QtGui import QIcon, QDesktopServices, QFont, QColor, QPixmap, QTextCursor # QFileDialog is part of QtWidgets
from PyQt5.QtCore import Qt, QUrl, QCoreApplication, QEvent, QStandardPaths
from PyQt5.QtWidgets import QFormLayout
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtGui import QPixmap

import db as db_manager
# client_documents_crud, activity_logs_crud removed, users_crud is kept
from db.cruds import users_crud

from db.cruds.clients_crud import clients_crud_instance
# from excel_editor import ExcelEditor # No longer used directly
# from html_editor import HtmlEditor # No longer used directly
from dialogs import ClientProductDimensionDialog, AssignPersonnelDialog, AssignTransporterDialog, AssignFreightForwarderDialog, AssignMoneyTransferAgentDialog # Added import
from whatsapp.whatsapp_dialog import SendWhatsAppDialog # Added import
# Removed: from main import get_notification_manager
# CRUD imports for Money Transfer Agents
import db.cruds.money_transfer_agents_crud as mta_crud
import db.cruds.client_order_money_transfer_agents_crud as coma_crud
import db.cruds.projects_crud as projects_crud

# from invoicing.final_invoice_data_dialog import FinalInvoiceDataDialog # No longer used directly
# from document_manager_logic import create_final_invoice_and_update_db # No longer used directly


# Globals imported from main (temporary, to be refactored)
# SUPPORTED_LANGUAGES definition removed, will be imported

MAIN_MODULE_CONTACT_DIALOG = None
MAIN_MODULE_PRODUCT_DIALOG = None
MAIN_MODULE_EDIT_PRODUCT_LINE_DIALOG = None
MAIN_MODULE_CREATE_DOCUMENT_DIALOG = None
MAIN_MODULE_COMPILE_PDF_DIALOG = None
MAIN_MODULE_GENERATE_PDF_FOR_DOCUMENT = None
MAIN_MODULE_CONFIG = None
MAIN_MODULE_DATABASE_NAME = None
MAIN_MODULE_SEND_EMAIL_DIALOG = None
MAIN_MODULE_CLIENT_DOCUMENT_NOTE_DIALOG = None # Added for ClientDocumentNoteDialog
MAIN_MODULE_SEND_WHATSAPP_DIALOG = None

def _import_main_elements():
    global MAIN_MODULE_CONTACT_DIALOG, MAIN_MODULE_PRODUCT_DIALOG, \
           MAIN_MODULE_EDIT_PRODUCT_LINE_DIALOG, MAIN_MODULE_CREATE_DOCUMENT_DIALOG, \
           MAIN_MODULE_COMPILE_PDF_DIALOG, MAIN_MODULE_GENERATE_PDF_FOR_DOCUMENT, \
           MAIN_MODULE_CONFIG, MAIN_MODULE_DATABASE_NAME, MAIN_MODULE_SEND_EMAIL_DIALOG, \
           MAIN_MODULE_CLIENT_DOCUMENT_NOTE_DIALOG, MAIN_MODULE_SEND_WHATSAPP_DIALOG

    if MAIN_MODULE_CONFIG is None: # Check one, load all if not loaded
        # import main as main_module # No longer needed
        from dialogs import (SendEmailDialog, ContactDialog, ProductDialog, EditProductLineDialog,
                             CreateDocumentDialog, CompilePdfDialog, ClientDocumentNoteDialog)
        from whatsapp.whatsapp_dialog import SendWhatsAppDialog as WhatsAppDialogModule
        from utils import generate_pdf_for_document as utils_generate_pdf_for_document
        from app_setup import CONFIG as APP_CONFIG
        from config import DATABASE_PATH as DB_PATH_CONFIG # Added line
        MAIN_MODULE_CONTACT_DIALOG = ContactDialog
        MAIN_MODULE_PRODUCT_DIALOG = ProductDialog
        MAIN_MODULE_EDIT_PRODUCT_LINE_DIALOG = EditProductLineDialog
        MAIN_MODULE_CREATE_DOCUMENT_DIALOG = CreateDocumentDialog
        MAIN_MODULE_COMPILE_PDF_DIALOG = CompilePdfDialog
        MAIN_MODULE_GENERATE_PDF_FOR_DOCUMENT = utils_generate_pdf_for_document
        MAIN_MODULE_CONFIG = APP_CONFIG
        MAIN_MODULE_DATABASE_NAME = DB_PATH_CONFIG # Changed DB_NAME to DB_PATH_CONFIG
        MAIN_MODULE_SEND_EMAIL_DIALOG = SendEmailDialog
        MAIN_MODULE_CLIENT_DOCUMENT_NOTE_DIALOG = ClientDocumentNoteDialog
        MAIN_MODULE_SEND_WHATSAPP_DIALOG = WhatsAppDialogModule


from auth.permissions import has_permission, \
    P_EDIT_CLIENT_FULL, P_EDIT_CLIENT_BASIC, P_MANAGE_CLIENT_CONTACTS, \
    P_LINK_PRODUCTS_TO_CLIENT, P_MANAGE_CLIENT_DOCUMENTS, P_ARCHIVE_CLIENT, \
    P_MANAGE_CLIENT_ASSIGNMENTS, P_MANAGE_CLIENT_BILLING # Define more as needed

# Import CommandeWidget
from commande_management.commande_widget import CommandeWidget

# Import the new Documentstab and its SUPPORTED_LANGUAGES
from client_management.tabs.documents_tab import DocumentsTab, SUPPORTED_LANGUAGES
# Import the new ProductsTab
from client_management.tabs.products_tab import ProductsTab
# Import the new DocumentNotesTab
from client_management.tabs.document_notes_tab import DocumentNotesTab
# Import the new ProductDimensionsTab
from client_management.tabs.product_dimensions_tab import ProductDimensionsTab
# Import the new SAVTab
from client_management.tabs.sav_tab import SAVTab
# Import the new BillingTab
from client_management.tabs.billing_tab import BillingTab


class ClientMainWidget(QWidget): # Renamed from ClientWidget
    CONTACT_PAGE_LIMIT = 15 # Class attribute for page limit

    def __init__(self, client_info, config, app_root_dir, notification_manager, current_user_info: dict, parent=None): # Changed to current_user_info
        super().__init__(parent)
        self.current_user_info = current_user_info # Store full user info
        self.current_user_id = self.current_user_info.get('user_id') # Extract for existing code
        # self._is_populating_docs = False # This line removed

        logging.info(f"ClientMainWidget.__init__: INSTANTIATION STARTED for client_id={client_info.get('client_id')}, user: {self.current_user_info.get('username')}")
        logging.info(f"ClientMainWidget.__init__: Received client_info: {client_info}")
        logging.info(f"ClientMainWidget __init__: client_id={client_info.get('client_id')}, client_name={client_info.get('client_name')}")
        self.client_info = client_info
        self.notification_manager = notification_manager
        # self.config = config # Will be set by _import_main_elements

        # Dynamically import main elements
        logging.info("ClientMainWidget.__init__: Calling _import_main_elements()...")
        _import_main_elements()
        logging.info("ClientMainWidget.__init__: Finished _import_main_elements().")
        self.config = MAIN_MODULE_CONFIG
        self.app_root_dir = app_root_dir
        self.DATABASE_NAME = MAIN_MODULE_DATABASE_NAME

        self.ContactDialog = MAIN_MODULE_CONTACT_DIALOG
        self.ProductDialog = MAIN_MODULE_PRODUCT_DIALOG
        self.EditProductLineDialog = MAIN_MODULE_EDIT_PRODUCT_LINE_DIALOG
        self.CreateDocumentDialog = MAIN_MODULE_CREATE_DOCUMENT_DIALOG
        self.CompilePdfDialog = MAIN_MODULE_COMPILE_PDF_DIALOG
        self.generate_pdf_for_document = MAIN_MODULE_GENERATE_PDF_FOR_DOCUMENT
        self.SendEmailDialog = MAIN_MODULE_SEND_EMAIL_DIALOG
        self.ClientDocumentNoteDialog = MAIN_MODULE_CLIENT_DOCUMENT_NOTE_DIALOG # Added
        self.SendWhatsAppDialog = MAIN_MODULE_SEND_WHATSAPP_DIALOG

        self.is_editing_client = False
        self.edit_widgets = {}
        self.default_company_id = None
        try:
            default_company = db_manager.get_default_company()
            if default_company:
                self.default_company_id = default_company.get('company_id')
        except Exception as e:
            print(f"Error fetching default company ID in ClientMainWidget: {e}")
            # Log this, user might not be able to assign personnel if no default company found

        # Pagination for Contacts
        self.current_contact_offset = 0
        self.total_contacts_count = 0
        # self.CONTACT_PAGE_LIMIT is a class attribute

        logging.info("ClientMainWidget.__init__: Calling self.setup_ui()...")
        self.setup_ui()
        logging.info("ClientMainWidget.__init__: Finished self.setup_ui().")
        logging.info(f"ClientMainWidget.__init__: INSTANTIATION COMPLETED for client_id={self.client_info.get('client_id')}")

    def setup_ui(self):
        logging.info("ClientMainWidget.setup_ui: Starting UI setup...")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        try:
            logging.info("ClientMainWidget.setup_ui: Starting setup for Collapsible Client Info Section...")
            # --- Collapsible Client Info Section ---

            self.client_info_group_box = QGroupBox(self.client_info.get('client_name', self.tr("Client Information")))
            self.client_info_group_box.setCheckable(True)
            client_info_group_layout = QVBoxLayout(self.client_info_group_box)

            self.info_container_widget = QWidget()
            info_container_layout = QVBoxLayout(self.info_container_widget)
            info_container_layout.setContentsMargins(0, 5, 0, 0)
            info_container_layout.setSpacing(10)

            self.header_label = QLabel(f"<h2>{self.client_info.get('client_name', self.tr('Client Inconnu'))}</h2>")
            self.header_label.setObjectName("clientHeaderLabel")
            info_container_layout.addWidget(self.header_label)

            action_layout = QHBoxLayout()
            self.create_docs_btn = QPushButton(self.tr("Envoyer Mail"))
            self.create_docs_btn.setIcon(QIcon.fromTheme("mail-send", QIcon(":/icons/bell.svg")))
            self.create_docs_btn.setToolTip(self.tr("Envoyer un email au client"))
            self.create_docs_btn.setObjectName("primaryButton")
            try:
                self.create_docs_btn.clicked.disconnect(self.open_create_docs_dialog)
            except TypeError:
                pass # Not connected or already disconnected
            self.create_docs_btn.clicked.connect(self.open_send_email_dialog)
            action_layout.addWidget(self.create_docs_btn)

            self.compile_pdf_btn = QPushButton(self.tr("Compiler PDF"))
            self.compile_pdf_btn.setIcon(QIcon.fromTheme("document-export"))
            self.compile_pdf_btn.setProperty("primary", True)
            self.compile_pdf_btn.clicked.connect(self.open_compile_pdf_dialog)
            # action_layout.addWidget(self.compile_pdf_btn) # Moved to documents tab filters

            self.edit_save_client_btn = QPushButton(self.tr("Modifier Client"))
            self.edit_save_client_btn.setIcon(QIcon.fromTheme("document-edit", QIcon(":/icons/pencil.svg")))
            self.edit_save_client_btn.setToolTip(self.tr("Modifier les informations du client"))
            self.edit_save_client_btn.clicked.connect(self.toggle_client_edit_mode)
            action_layout.addWidget(self.edit_save_client_btn)

            self.send_whatsapp_btn = QPushButton(self.tr("Send WhatsApp"))
            self.send_whatsapp_btn.setIcon(QIcon.fromTheme("contact-new", QIcon(":/icons/user.svg")))
            self.send_whatsapp_btn.setToolTip(self.tr("Send a WhatsApp message to the client"))
            self.send_whatsapp_btn.clicked.connect(self.open_send_whatsapp_dialog)
            # action_layout.addWidget(self.send_whatsapp_btn) # Moved to an internal tab

            self.archive_client_btn = QPushButton(self.tr("Archiver Client"))
            self.archive_client_btn.setIcon(QIcon(":/icons/folder.svg")) # Replaced archive.svg with folder.svg
            self.archive_client_btn.setToolTip(self.tr("Archiver ce client (soft delete)"))
            self.archive_client_btn.clicked.connect(self.handle_archive_client) # Connect to the new handler
            action_layout.addWidget(self.archive_client_btn)

            info_container_layout.addLayout(action_layout)

            # Create the internal QTabWidget
            self.internal_client_info_tabs = QTabWidget()
            info_container_layout.addWidget(self.internal_client_info_tabs)

            # --- Tab 1: Client Details (populated by populate_details_layout) ---
            self.client_details_tab = QWidget()
            details_tab_layout = QVBoxLayout(self.client_details_tab)

            self.status_combo = QComboBox() # Status combo will be part of the details tab
            # self.load_statuses() # load_statuses will be called by populate_details_layout or refresh_display
            # self.status_combo.setCurrentText(self.client_info.get("status", self.tr("En cours")))
            # self.status_combo.currentTextChanged.connect(self.update_client_status)

            self.details_layout = QFormLayout() # This is the layout for client fields
            self.details_layout.setLabelAlignment(Qt.AlignLeft)
            self.details_layout.setSpacing(10)

            # --- Persistent UI Elements for Client Details Tab ---
            # These are created once here and updated by populate_details_layout

            # Project ID
            self.project_id_label = QLabel(self.tr("ID Projet:"))
            self.project_id_value_label = QLabel(self.tr("N/A"))
            self.details_layout.addRow(self.project_id_label, self.project_id_value_label)

            # Country and City
            self.country_city_label = QLabel(self.tr("Localisation:"))
            self.country_city_widget = QWidget()
            country_city_h_layout = QHBoxLayout(self.country_city_widget)
            country_city_h_layout.setContentsMargins(0,0,0,0)
            self.country_label_static = QLabel(self.tr("Pays:")) # Static label
            self.country_value_label = QLabel(self.tr("N/A"))
            self.city_label_static = QLabel(self.tr("Ville:")) # Static label
            self.city_value_label = QLabel(self.tr("N/A"))
            country_city_h_layout.addWidget(self.country_label_static)
            country_city_h_layout.addWidget(self.country_value_label)
            country_city_h_layout.addSpacing(20)
            country_city_h_layout.addWidget(self.city_label_static)
            country_city_h_layout.addWidget(self.city_value_label)
            country_city_h_layout.addStretch()
            self.details_layout.addRow(self.country_city_label, self.country_city_widget)

            # Price and Creation Date
            self.price_date_label = QLabel(self.tr("Finances & Date:"))
            self.price_date_widget = QWidget()
            price_date_h_layout = QHBoxLayout(self.price_date_widget)
            price_date_h_layout.setContentsMargins(0,0,0,0)
            self.price_label_static = QLabel(self.tr("Prix Final:")) # Static label
            self.price_value_label = QLabel(self.tr("0 €"))
            self.date_label_static = QLabel(self.tr("Date Création:")) # Static label
            self.date_value_label = QLabel(self.tr("N/A"))
            price_date_h_layout.addWidget(self.price_label_static)
            price_date_h_layout.addWidget(self.price_value_label)
            price_date_h_layout.addSpacing(20)
            price_date_h_layout.addWidget(self.date_label_static)
            price_date_h_layout.addWidget(self.date_value_label)
            price_date_h_layout.addStretch()
            self.details_layout.addRow(self.price_date_label, self.price_date_widget)

            # Status and Category
            self.status_category_label = QLabel(self.tr("Classification:"))
            self.status_category_widget = QWidget() # Persistent container for this row
            status_category_h_layout = QHBoxLayout(self.status_category_widget)
            status_category_h_layout.setContentsMargins(0,0,0,0)
            self.status_label_static = QLabel(self.tr("Statut:")) # Static label for "Statut:"
            self.status_combo = QComboBox() # Created once
            self.category_label_static = QLabel(self.tr("Catégorie:")) # Static label for "Catégorie:"
            self.category_value_label = QLabel(self.tr("N/A")) # Value label for category
            status_category_h_layout.addWidget(self.status_label_static)
            status_category_h_layout.addWidget(self.status_combo)
            status_category_h_layout.addSpacing(20)
            status_category_h_layout.addWidget(self.category_label_static)
            status_category_h_layout.addWidget(self.category_value_label)
            status_category_h_layout.addStretch()
            self.details_layout.addRow(self.status_category_label, self.status_category_widget)

            # Distributor Specific Info (conditionally visible)
            self.distributor_info_label_static = QLabel(self.tr("Info Distributeur:")) # Static label
            self.distributor_info_value_label = QLabel(self.tr("N/A")) # Value label
            self.distributor_info_value_label.setWordWrap(True)
            self.distributor_info_value_label.setObjectName("distributorInfoValueLabel")
            self.distributor_info_label_static.setObjectName("distributorInfoLabel") # Label for the row
            self.details_layout.addRow(self.distributor_info_label_static, self.distributor_info_value_label)


            # Need (Besoin Principal)
            self.need_label_static = QLabel(self.tr("Besoin Principal:")) # Static label
            self.need_value_label = QLabel(self.tr("N/A")) # Value label
            self.details_layout.addRow(self.need_label_static, self.need_value_label)

            # Base Folder Path
            self.folder_label_static = QLabel(self.tr("Chemin Dossier:")) # Static label
            self.folder_value_label = QLabel(self.tr("N/A")) # Value label, will contain link
            self.folder_value_label.setOpenExternalLinks(True)
            self.folder_value_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
            self.details_layout.addRow(self.folder_label_static, self.folder_value_label)

            # Created By
            self.created_by_label_static = QLabel(self.tr("Créé par:"))
            self.created_by_value_label = QLabel(self.tr("N/A"))
            self.details_layout.addRow(self.created_by_label_static, self.created_by_value_label)
            # --- End of Persistent UI Elements for Client Details Tab ---

            details_tab_layout.addLayout(self.details_layout)
            self.internal_client_info_tabs.addTab(self.client_details_tab, self.client_info.get('client_name', self.tr("Détails Client")))

            # Initial population of the now persistent elements
            self.populate_details_layout()


            # --- Tab 2: Contacts ---
            contacts_tab_widget = QWidget()
            contacts_tab_layout = QVBoxLayout(contacts_tab_widget)

            # Re-create contacts UI (table, buttons, pagination)
            self.contacts_table = QTableWidget()
            self.contacts_table.setColumnCount(5)
            self.contacts_table.setHorizontalHeaderLabels([
                self.tr("Nom"), self.tr("Email"), self.tr("Téléphone"),
                self.tr("Position"), self.tr("Principal")
            ])
            self.contacts_table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.contacts_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.contacts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.contacts_table.setAlternatingRowColors(True)
            self.contacts_table.cellDoubleClicked.connect(self.edit_contact)

            self.contacts_empty_label = QLabel(self.tr("Aucun contact ajouté pour ce client.\nCliquez sur '➕ Ajouter' pour commencer."))
            self.contacts_empty_label.setAlignment(Qt.AlignCenter)
            font_contacts_empty = self.contacts_empty_label.font(); font_contacts_empty.setPointSize(10)
            self.contacts_empty_label.setFont(font_contacts_empty)
            contacts_tab_layout.addWidget(self.contacts_empty_label)
            contacts_tab_layout.addWidget(self.contacts_table)

            contacts_pagination_layout = QHBoxLayout()
            self.prev_contact_button = QPushButton("<< Précédent")
            self.prev_contact_button.setObjectName("paginationButton")
            self.prev_contact_button.clicked.connect(self.prev_contact_page)
            self.contact_page_info_label = QLabel("Page 1 / 1")
            self.contact_page_info_label.setObjectName("paginationLabel")
            self.next_contact_button = QPushButton("Suivant >>")
            self.next_contact_button.setObjectName("paginationButton")
            self.next_contact_button.clicked.connect(self.next_contact_page)
            contacts_pagination_layout.addStretch()
            contacts_pagination_layout.addWidget(self.prev_contact_button)
            contacts_pagination_layout.addWidget(self.contact_page_info_label)
            contacts_pagination_layout.addWidget(self.next_contact_button)
            contacts_pagination_layout.addStretch()
            contacts_tab_layout.addLayout(contacts_pagination_layout)

            contacts_btn_layout = QHBoxLayout()
            self.add_contact_btn = QPushButton(self.tr("Ajouter")); self.add_contact_btn.setIcon(QIcon(":/icons/user-plus.svg"))
            self.add_contact_btn.setToolTip(self.tr("Ajouter un nouveau contact pour ce client")); self.add_contact_btn.clicked.connect(self.add_contact); contacts_btn_layout.addWidget(self.add_contact_btn)
            self.edit_contact_btn = QPushButton(self.tr("Modifier")); self.edit_contact_btn.setIcon(QIcon(":/icons/pencil.svg"))
            self.edit_contact_btn.setToolTip(self.tr("Modifier le contact sélectionné")); self.edit_contact_btn.clicked.connect(self.edit_contact); contacts_btn_layout.addWidget(self.edit_contact_btn)
            self.remove_contact_btn = QPushButton(self.tr("Supprimer")); self.remove_contact_btn.setIcon(QIcon(":/icons/trash.svg"))
            self.remove_contact_btn.setToolTip(self.tr("Supprimer le lien vers le contact sélectionné pour ce client")); self.remove_contact_btn.setObjectName("dangerButton"); self.remove_contact_btn.clicked.connect(self.remove_contact); contacts_btn_layout.addWidget(self.remove_contact_btn)
            contacts_tab_layout.addLayout(contacts_btn_layout)

            self.internal_client_info_tabs.addTab(contacts_tab_widget, self.tr("Contacts"))
            # self.load_contacts() # Will be called in the main setup_ui after all tabs are defined


            # --- Tab 3: Assignments (Affectations) ---
            self.assignments_internal_tab = QWidget() # Using a more specific name for the tab widget itself
            assignments_internal_tab_layout = QVBoxLayout(self.assignments_internal_tab)
            self.assignments_sub_tabs = QTabWidget() # This is the QTabWidget for sub-assignments
            assignments_internal_tab_layout.addWidget(self.assignments_sub_tabs)

            # Sub-Tab: Assigned Vendors/Sellers (CompanyPersonnel)
            assigned_vendors_widget = QWidget()
            assigned_vendors_layout = QVBoxLayout(assigned_vendors_widget)
            self.assigned_vendors_table = QTableWidget(); self.assigned_vendors_table.setColumnCount(4)
            self.assigned_vendors_table.setHorizontalHeaderLabels([self.tr("Nom"), self.tr("Rôle Projet"), self.tr("Email"), self.tr("Téléphone")])
            self.assigned_vendors_table.setSelectionBehavior(QAbstractItemView.SelectRows); self.assigned_vendors_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.assigned_vendors_table.horizontalHeader().setStretchLastSection(True)
            assigned_vendors_layout.addWidget(self.assigned_vendors_table)
            vendor_buttons_layout = QHBoxLayout()
            self.add_assigned_vendor_btn = QPushButton(self.tr("Ajouter Vendeur/Personnel")); self.add_assigned_vendor_btn.clicked.connect(self.handle_add_assigned_vendor)
            self.remove_assigned_vendor_btn = QPushButton(self.tr("Retirer Vendeur/Personnel")); self.remove_assigned_vendor_btn.clicked.connect(self.handle_remove_assigned_vendor)
            vendor_buttons_layout.addWidget(self.add_assigned_vendor_btn); vendor_buttons_layout.addWidget(self.remove_assigned_vendor_btn)
            assigned_vendors_layout.addLayout(vendor_buttons_layout)
            self.assignments_sub_tabs.addTab(assigned_vendors_widget, self.tr("Vendeurs & Personnel"))

            # Sub-Tab: Assigned Technicians
            assigned_technicians_widget = QWidget()
            assigned_technicians_layout = QVBoxLayout(assigned_technicians_widget)
            self.assigned_technicians_table = QTableWidget(); self.assigned_technicians_table.setColumnCount(4)
            self.assigned_technicians_table.setHorizontalHeaderLabels([self.tr("Nom"), self.tr("Rôle Projet"), self.tr("Email"), self.tr("Téléphone")])
            self.assigned_technicians_table.setSelectionBehavior(QAbstractItemView.SelectRows); self.assigned_technicians_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.assigned_technicians_table.horizontalHeader().setStretchLastSection(True)
            assigned_technicians_layout.addWidget(self.assigned_technicians_table)
            technician_buttons_layout = QHBoxLayout()
            self.add_assigned_technician_btn = QPushButton(self.tr("Ajouter Technicien")); self.add_assigned_technician_btn.clicked.connect(self.handle_add_assigned_technician)
            self.remove_assigned_technician_btn = QPushButton(self.tr("Retirer Technicien")); self.remove_assigned_technician_btn.clicked.connect(self.handle_remove_assigned_technician)
            technician_buttons_layout.addWidget(self.add_assigned_technician_btn); technician_buttons_layout.addWidget(self.remove_assigned_technician_btn)
            assigned_technicians_layout.addLayout(technician_buttons_layout)
            self.assignments_sub_tabs.addTab(assigned_technicians_widget, self.tr("Techniciens"))

            # Sub-Tab: Assigned Transporters
            assigned_transporters_widget = QWidget()
            assigned_transporters_layout = QVBoxLayout(assigned_transporters_widget)
            self.assigned_transporters_table = QTableWidget(); self.assigned_transporters_table.setColumnCount(6)
            self.assigned_transporters_table.setHorizontalHeaderLabels([self.tr("Nom Transporteur"), self.tr("Contact"), self.tr("Téléphone"), self.tr("Détails Transport"), self.tr("Coût Estimé"), self.tr("Actions")])
            self.assigned_transporters_table.setSelectionBehavior(QAbstractItemView.SelectRows); self.assigned_transporters_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.assigned_transporters_table.horizontalHeader().setStretchLastSection(True)
            assigned_transporters_layout.addWidget(self.assigned_transporters_table)
            transporter_buttons_layout = QHBoxLayout()
            self.add_assigned_transporter_btn = QPushButton(self.tr("Ajouter Transporteur")); self.add_assigned_transporter_btn.clicked.connect(self.handle_add_assigned_transporter)
            self.remove_assigned_transporter_btn = QPushButton(self.tr("Retirer Transporteur")); self.remove_assigned_transporter_btn.clicked.connect(self.handle_remove_assigned_transporter)
            transporter_buttons_layout.addWidget(self.add_assigned_transporter_btn); transporter_buttons_layout.addWidget(self.remove_assigned_transporter_btn)
            assigned_transporters_layout.addLayout(transporter_buttons_layout)
            self.assignments_sub_tabs.addTab(assigned_transporters_widget, self.tr("Transporteurs"))

            # Sub-Tab: Assigned Freight Forwarders
            assigned_forwarders_widget = QWidget()
            assigned_forwarders_layout = QVBoxLayout(assigned_forwarders_widget)
            self.assigned_forwarders_table = QTableWidget(); self.assigned_forwarders_table.setColumnCount(5)
            self.assigned_forwarders_table.setHorizontalHeaderLabels([self.tr("Nom Transitaire"), self.tr("Contact"), self.tr("Téléphone"), self.tr("Description Tâche"), self.tr("Coût Estimé")])
            self.assigned_forwarders_table.setSelectionBehavior(QAbstractItemView.SelectRows); self.assigned_forwarders_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.assigned_forwarders_table.horizontalHeader().setStretchLastSection(True)
            assigned_forwarders_layout.addWidget(self.assigned_forwarders_table)
            forwarder_buttons_layout = QHBoxLayout()
            self.add_assigned_forwarder_btn = QPushButton(self.tr("Ajouter Transitaire")); self.add_assigned_forwarder_btn.clicked.connect(self.handle_add_assigned_forwarder)
            self.remove_assigned_forwarder_btn = QPushButton(self.tr("Retirer Transitaire")); self.remove_assigned_forwarder_btn.clicked.connect(self.handle_remove_assigned_forwarder)
            forwarder_buttons_layout.addWidget(self.add_assigned_forwarder_btn); forwarder_buttons_layout.addWidget(self.remove_assigned_forwarder_btn)
            assigned_forwarders_layout.addLayout(forwarder_buttons_layout)
            self.assignments_sub_tabs.addTab(assigned_forwarders_widget, self.tr("Transitaires"))

            # Sub-Tab: Money Transfer Agents
            mta_widget = QWidget()
            mta_layout = QVBoxLayout(mta_widget)
            mta_project_selector_layout = QHBoxLayout()
            mta_project_selector_layout.addWidget(QLabel(self.tr("Sélectionner Commande/Projet:")))
            self.mta_project_selector_combo = QComboBox()
            mta_project_selector_layout.addWidget(self.mta_project_selector_combo)
            mta_layout.addLayout(mta_project_selector_layout)
            self.assigned_mta_table = QTableWidget()
            self.assigned_mta_table.setColumnCount(8)
            self.assigned_mta_table.setHorizontalHeaderLabels([
                self.tr("Nom Agent"), self.tr("Type"), self.tr("Email"), self.tr("Téléphone"),
                self.tr("Détails Affectation"), self.tr("Frais Estimés"), self.tr("Statut Email"), self.tr("Actions")])
            self.assigned_mta_table.setSelectionBehavior(QAbstractItemView.SelectRows); self.assigned_mta_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.assigned_mta_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.assigned_mta_table.setMinimumHeight(150)
            mta_layout.addWidget(self.assigned_mta_table)
            mta_buttons_layout = QHBoxLayout()
            self.add_assigned_mta_btn = QPushButton(self.tr("Assigner Agent de Transfert")); self.add_assigned_mta_btn.clicked.connect(self.handle_add_assigned_mta)
            self.remove_assigned_mta_btn = QPushButton(self.tr("Retirer Agent de Transfert")); self.remove_assigned_mta_btn.clicked.connect(self.handle_remove_assigned_mta)
            mta_buttons_layout.addWidget(self.add_assigned_mta_btn); mta_buttons_layout.addWidget(self.remove_assigned_mta_btn)
            mta_layout.addLayout(mta_buttons_layout)
            self.assignments_sub_tabs.addTab(mta_widget, self.tr("Agents de Transfert d'Argent"))

            self.internal_client_info_tabs.addTab(self.assignments_internal_tab, self.tr("Affectations"))
            # Connect signals for assignment tables (moved from old _setup_assignments_tab)
            self.assigned_vendors_table.itemSelectionChanged.connect(self.update_assigned_vendors_buttons_state)
            self.assigned_technicians_table.itemSelectionChanged.connect(self.update_assigned_technicians_buttons_state)
            self.assigned_transporters_table.itemSelectionChanged.connect(self.update_assigned_transporters_buttons_state)
            self.assigned_forwarders_table.itemSelectionChanged.connect(self.update_assigned_forwarders_buttons_state)
            self.mta_project_selector_combo.currentIndexChanged.connect(self.handle_mta_project_selection_changed)
            self.assigned_mta_table.itemSelectionChanged.connect(self.update_mta_buttons_state)
            # Initial load for MTA project selector and button states
            self.load_projects_for_mta_combo()
            self.add_assigned_mta_btn.setEnabled(False)
            self.remove_assigned_mta_btn.setEnabled(False)


            # --- Tab 4: Send Email ---
            send_email_tab_widget = QWidget()
            send_email_tab_layout = QVBoxLayout(send_email_tab_widget)
            self.open_email_dialog_btn = QPushButton(self.tr("Composer un Email..."))
            self.open_email_dialog_btn.setIcon(QIcon.fromTheme("mail-send", QIcon(":/icons/bell.svg")))
            self.open_email_dialog_btn.clicked.connect(self.open_send_email_dialog)
            send_email_tab_layout.addWidget(self.open_email_dialog_btn)
            send_email_tab_layout.addStretch()
            self.internal_client_info_tabs.addTab(send_email_tab_widget, self.tr("Envoyer Mail"))

            # --- Tab 5: Send WhatsApp ---
            send_whatsapp_tab_widget = QWidget()
            send_whatsapp_tab_layout = QVBoxLayout(send_whatsapp_tab_widget)
            self.open_whatsapp_dialog_btn = QPushButton(self.tr("Envoyer message WhatsApp..."))
            self.open_whatsapp_dialog_btn.setIcon(QIcon.fromTheme("contact-new", QIcon(":/icons/user.svg"))) # Placeholder
            self.open_whatsapp_dialog_btn.clicked.connect(self.open_send_whatsapp_dialog)
            send_whatsapp_tab_layout.addWidget(self.open_whatsapp_dialog_btn)
            send_whatsapp_tab_layout.addStretch()
            self.internal_client_info_tabs.addTab(send_whatsapp_tab_widget, self.tr("Send WhatsApp"))


            client_info_group_layout.addWidget(self.info_container_widget)
            self.client_info_group_box.setChecked(True) # Ensure the main group is expanded by default
            layout.addWidget(self.client_info_group_box)
        except Exception as e:
            logging.error(f"Error in _setup_client_info_section: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur UI"), self.tr("Erreur initialisation section infos client:\n{0}").format(str(e)))

        self._setup_notes_section(layout)
        self._setup_main_tabs_section(layout) # This will call sub-methods for each tab, including _setup_commandes_tab internally now.
        # self._setup_commandes_tab() # Call removed from here, as it's part of _setup_main_tabs_section

        # Initial data loading calls
        logging.info("ClientMainWidget.setup_ui: Starting initial data loading for tabs...")

        # logging.info("ClientMainWidget.setup_ui: Attempting self.populate_doc_table()") # Call removed
        # try:
            # self.populate_doc_table() # Call removed, DocumentsTab handles its own loading
            # logging.info("ClientMainWidget.setup_ui: Successfully completed self.populate_doc_table()")
        # except Exception as e:
            # logging.error(f"ClientMainWidget.setup_ui: Error during self.populate_doc_table(): {e}", exc_info=True)

        logging.info("ClientMainWidget.setup_ui: Attempting self.load_contacts()")
        try:
            self.load_contacts()
            logging.info("ClientMainWidget.setup_ui: Successfully completed self.load_contacts()")
        except Exception as e:
            logging.error(f"ClientMainWidget.setup_ui: Error during self.load_contacts(): {e}", exc_info=True)

        # logging.info("ClientMainWidget.setup_ui: Attempting self.load_products()") # Call removed
        # try:
            # self.load_products() # This also calls load_products_for_dimension_tab - Call removed, ProductsTab handles its own loading
            # logging.info("ClientMainWidget.setup_ui: Successfully completed self.load_products()")
        # except Exception as e:
            # logging.error(f"ClientMainWidget.setup_ui: Error during self.load_products(): {e}", exc_info=True)

        # logging.info("ClientMainWidget.setup_ui: Attempting self.load_document_notes_filters()") # Call removed
        # try:
            # self.load_document_notes_filters() # Call removed, DocumentNotesTab handles this
            # logging.info("ClientMainWidget.setup_ui: Successfully completed self.load_document_notes_filters()")
        # except Exception as e:
            # logging.error(f"ClientMainWidget.setup_ui: Error during self.load_document_notes_filters(): {e}", exc_info=True)

        # logging.info("ClientMainWidget.setup_ui: Attempting self.load_document_notes_table()") # Call removed
        # try:
            # self.load_document_notes_table() # Call removed, DocumentNotesTab handles this
            # logging.info("ClientMainWidget.setup_ui: Successfully completed self.load_document_notes_table()")
        # except Exception as e:
            # logging.error(f"ClientMainWidget.setup_ui: Error during self.load_document_notes_table(): {e}", exc_info=True)

        # logging.info("ClientMainWidget.setup_ui: Attempting self.update_sav_tab_visibility()") # Call removed
        # try:
            # self.update_sav_tab_visibility() # Call removed, SAVTab handles its own visibility and loading
            # logging.info("ClientMainWidget.setup_ui: Successfully completed self.update_sav_tab_visibility()")
        # except Exception as e:
            # logging.error(f"ClientMainWidget.setup_ui: Error during self.update_sav_tab_visibility(): {e}", exc_info=True)

        logging.info("ClientMainWidget.setup_ui: Attempting self.load_assigned_vendors_personnel()")
        try:
            self.load_assigned_vendors_personnel()
            logging.info("ClientMainWidget.setup_ui: Successfully completed self.load_assigned_vendors_personnel()")
        except Exception as e:
            logging.error(f"ClientMainWidget.setup_ui: Error during self.load_assigned_vendors_personnel(): {e}", exc_info=True)

        logging.info("ClientMainWidget.setup_ui: Attempting self.load_assigned_technicians()")
        try:
            self.load_assigned_technicians()
            logging.info("ClientMainWidget.setup_ui: Successfully completed self.load_assigned_technicians()")
        except Exception as e:
            logging.error(f"ClientMainWidget.setup_ui: Error during self.load_assigned_technicians(): {e}", exc_info=True)

        logging.info("ClientMainWidget.setup_ui: Attempting self.load_assigned_transporters()")
        try:
            self.load_assigned_transporters()
            logging.info("ClientMainWidget.setup_ui: Successfully completed self.load_assigned_transporters()")
        except Exception as e:
            logging.error(f"ClientMainWidget.setup_ui: Error during self.load_assigned_transporters(): {e}", exc_info=True)

        logging.info("ClientMainWidget.setup_ui: Attempting self.load_assigned_freight_forwarders()")
        try:
            self.load_assigned_freight_forwarders()
            logging.info("ClientMainWidget.setup_ui: Successfully completed self.load_assigned_freight_forwarders()")
        except Exception as e:
            logging.error(f"ClientMainWidget.setup_ui: Error during self.load_assigned_freight_forwarders(): {e}", exc_info=True)

        logging.info("ClientMainWidget.setup_ui: Finished initial data loading for tabs.")

        # Connect accordion group box toggled signals
        if hasattr(self, 'client_info_group_box'):
             self.client_info_group_box.toggled.connect(self._handle_client_info_section_toggled)
        if hasattr(self, 'notes_group_box'):
             self.notes_group_box.toggled.connect(self._handle_notes_section_toggled)
        if hasattr(self, 'tabs_group_box'):
             self.tabs_group_box.toggled.connect(self._handle_tabs_section_toggled)
        # if hasattr(self, 'contacts_group_box'): # Connection removed as the group box is being removed
            # self.contacts_group_box.toggled.connect(self._handle_contacts_section_toggled)



        # Apply permissions
        self._apply_permissions()

        # Event filter for notes auto-save
        if hasattr(self, 'notes_edit'):
            self.notes_edit.installEventFilter(self)
        logging.info(f"ClientMainWidget.setup_ui: FULL UI SETUP COMPLETED for client_id={self.client_info.get('client_id')}")

    def handle_archive_client(self):
        client_id = self.client_info.get("client_id")
        if not client_id:
            QMessageBox.warning(self, self.tr("Erreur Client"), self.tr("ID Client non disponible."))
            return

        reply = QMessageBox.question(self, self.tr("Archiver Client"),
                                     self.tr("Êtes-vous sûr de vouloir archiver ce client ({0})?\nLe client sera marqué comme archivé et pourra être masqué des listes par défaut.").format(self.client_info.get("client_name", client_id)),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            parent_window = self # Start with self, then try parent
            doc_manager_instance = None
            for _ in range(5): # Max 5 levels up
                if hasattr(parent_window, 'set_client_status_archived_slot'):
                    doc_manager_instance = parent_window
                    break
                if hasattr(parent_window, 'parent') and callable(parent_window.parent):
                    parent_window = parent_window.parent()
                    if parent_window is None or not isinstance(parent_window, QWidget): # Stop if no more QWidget parents
                        break
                else:
                    break

            if doc_manager_instance:
                logging.info(f"ClientMainWidget: Demande d'archivage pour client ID {client_id} via parent.")
                doc_manager_instance.set_client_status_archived_slot(client_id)
            else:
                QMessageBox.warning(self, self.tr("Erreur Action"), self.tr("Impossible de trouver la fonction d'archivage. L'action n'a pas pu être complétée."))
                logging.error("ClientMainWidget: La méthode set_client_status_archived_slot n'a pas été trouvée dans la hiérarchie parente.")


    # def _setup_contacts_section(self, main_layout): # Method removed as contacts are now an internal tab
    #     """Sets up the collapsible contacts section directly in the main layout."""
    #     pass # Content moved to an internal tab

    def _apply_permissions(self):
        """Applies role-based permissions to UI elements within ClientMainWidget."""
        role_name = self.current_user_info.get('role_name') if self.current_user_info else None
        if not role_name:
            # Default to least privilege if role_name is somehow not available
            # This state should ideally not be reached if login is enforced.
            logging.warning("ClientMainWidget._apply_permissions: No role_name found, disabling most actions.")
            can_edit_full = False
            can_edit_basic = False
            can_manage_contacts = False
            can_link_products = False
            can_manage_documents = False
            can_manage_assignments = False # New permission P_MANAGE_CLIENT_ASSIGNMENTS
            can_manage_billing = False     # New permission P_MANAGE_CLIENT_BILLING
            can_archive_client = False
        else:
            can_edit_full = has_permission(role_name, P_EDIT_CLIENT_FULL)
            can_edit_basic = has_permission(role_name, P_EDIT_CLIENT_BASIC) # For notes, status
            can_manage_contacts = has_permission(role_name, P_MANAGE_CLIENT_CONTACTS)
            can_link_products = has_permission(role_name, P_LINK_PRODUCTS_TO_CLIENT)
            can_manage_documents = has_permission(role_name, P_MANAGE_CLIENT_DOCUMENTS)
            can_archive_client = has_permission(role_name, P_ARCHIVE_CLIENT)
            # Assuming new permissions P_MANAGE_CLIENT_ASSIGNMENTS, P_MANAGE_CLIENT_BILLING exist in auth.permissions
            # If not, these will default to False. Add them to auth/permissions.py
            can_manage_assignments = has_permission(role_name, P_MANAGE_CLIENT_ASSIGNMENTS)
            can_manage_billing = has_permission(role_name, P_MANAGE_CLIENT_BILLING)


        # Client Info Header Buttons
        if hasattr(self, 'create_docs_btn'): # Send Email
            self.create_docs_btn.setEnabled(can_manage_documents) # Emailing often tied to doc management
        if hasattr(self, 'compile_pdf_btn'): # This button is part of client info actions
             self.compile_pdf_btn.setEnabled(can_manage_documents)
        if hasattr(self, 'edit_save_client_btn'):
            self.edit_save_client_btn.setEnabled(can_edit_full or can_edit_basic)
        if hasattr(self, 'send_whatsapp_btn'): # Assuming this is contact related
            self.send_whatsapp_btn.setEnabled(can_manage_contacts)
        if hasattr(self, 'archive_client_btn'):
            self.archive_client_btn.setEnabled(can_archive_client)


        # Status ComboBox
        if hasattr(self, 'status_combo'):
            self.status_combo.setEnabled(can_edit_full or can_edit_basic)

        # Notes Section
        if hasattr(self, 'notes_edit'):
            self.notes_edit.setReadOnly(not (can_edit_full or can_edit_basic))

        # Documents Tab Buttons (Now handled by DocumentsTab.apply_permissions_to_tab)
        if hasattr(self, 'documents_tab_widget_ref') and self.documents_tab_widget_ref: # documents_tab_widget_ref is the instance of DocumentsTab
            self.documents_tab_widget_ref.apply_permissions_to_tab(can_manage_documents)
        # if hasattr(self, 'add_doc_btn'): # Import Document # MOVED to DocumentsTab
        #     self.add_doc_btn.setEnabled(can_manage_documents)
        # if hasattr(self, 'add_template_btn'): # Generate via Template # MOVED to DocumentsTab
        #     self.add_template_btn.setEnabled(can_manage_documents)
        # Action buttons within doc_table are handled in DocumentsTab.populate_doc_table

        # Contacts Tab Buttons
        if hasattr(self, 'add_contact_btn'):
            self.add_contact_btn.setEnabled(can_manage_contacts)
        if hasattr(self, 'edit_contact_btn'):
            self.edit_contact_btn.setEnabled(can_manage_contacts)
        if hasattr(self, 'remove_contact_btn'):
            self.remove_contact_btn.setEnabled(can_manage_contacts)

        # Products Tab Buttons (Now handled by ProductsTab.apply_permissions_to_tab)
        if hasattr(self, 'products_tab_widget_ref') and self.products_tab_widget_ref:
            self.products_tab_widget_ref.apply_permissions_to_tab(can_link_products)
        # if hasattr(self, 'add_product_btn'): # MOVED
        #     self.add_product_btn.setEnabled(can_link_products)
        # if hasattr(self, 'edit_product_btn'): # MOVED
        #     # Editing a product line might require more specific permissions than just linking
        #     # For now, linking implies ability to edit the link details (qty, price_override)
        #     self.edit_product_btn.setEnabled(can_link_products)
        # if hasattr(self, 'remove_product_btn'): # MOVED
        #     self.remove_product_btn.setEnabled(can_link_products)

        # Document Notes Tab Buttons (Now handled by DocumentNotesTab.apply_permissions_to_tab)
        if hasattr(self, 'document_notes_tab_widget_ref') and self.document_notes_tab_widget_ref:
            self.document_notes_tab_widget_ref.apply_permissions_to_tab(can_manage_documents) # Assuming P_MANAGE_CLIENT_DOCUMENTS controls this
        # if hasattr(self, 'add_doc_note_button'): # MOVED
        #     self.add_doc_note_button.setEnabled(can_manage_documents) # Or a specific P_MANAGE_DOCUMENT_NOTES
        # Action buttons in document_notes_table handled in DocumentNotesTab.load_document_notes_table

        # Product Dimensions Tab (Now handled by ProductDimensionsTab.apply_permissions_to_tab)
        if hasattr(self, 'product_dimensions_tab_widget_ref') and self.product_dimensions_tab_widget_ref:
            self.product_dimensions_tab_widget_ref.apply_permissions_to_tab(can_link_products)
        # if hasattr(self, 'edit_client_product_dimensions_button'): # MOVED
        #     # This modifies client-specific product data, linked to product linking ability.
        #     self.edit_client_product_dimensions_button.setEnabled(can_link_products)
        #     # The button's enabled state also depends on a product being selected in dim_product_selector_combo,
        #     # which is handled by on_dim_product_selected. This RBAC check is an additional layer.
        #     if not can_link_products:
        #          self.dim_product_selector_combo.setEnabled(False) # Disable selector if no perm
        #     else:
        #          self.dim_product_selector_combo.setEnabled(True)


        # Assignments Tab Buttons (Vendors, Techs, Transporters, Forwarders, MTA)
        # Using P_MANAGE_CLIENT_ASSIGNMENTS as a general permission for all these
        if hasattr(self, 'add_assigned_vendor_btn'): self.add_assigned_vendor_btn.setEnabled(can_manage_assignments)
        if hasattr(self, 'remove_assigned_vendor_btn'): self.remove_assigned_vendor_btn.setEnabled(can_manage_assignments) # Initial state also depends on selection
        if hasattr(self, 'add_assigned_technician_btn'): self.add_assigned_technician_btn.setEnabled(can_manage_assignments)
        if hasattr(self, 'remove_assigned_technician_btn'): self.remove_assigned_technician_btn.setEnabled(can_manage_assignments)
        if hasattr(self, 'add_assigned_transporter_btn'): self.add_assigned_transporter_btn.setEnabled(can_manage_assignments)
        if hasattr(self, 'remove_assigned_transporter_btn'): self.remove_assigned_transporter_btn.setEnabled(can_manage_assignments)
        if hasattr(self, 'add_assigned_forwarder_btn'): self.add_assigned_forwarder_btn.setEnabled(can_manage_assignments)
        if hasattr(self, 'remove_assigned_forwarder_btn'): self.remove_assigned_forwarder_btn.setEnabled(can_manage_assignments)
        if hasattr(self, 'add_assigned_mta_btn'): self.add_assigned_mta_btn.setEnabled(can_manage_assignments) # Initial state also depends on project selection
        if hasattr(self, 'remove_assigned_mta_btn'): self.remove_assigned_mta_btn.setEnabled(can_manage_assignments)

        # Billing Tab (Now handled by BillingTab.apply_permissions_to_tab)
        if hasattr(self, 'billing_tab_widget_ref') and self.billing_tab_widget_ref:
            self.billing_tab_widget_ref.apply_permissions_to_tab() # BillingTab's method will use its own current_user_info
        # if hasattr(self, 'generate_invoice_button'): # MOVED
            # self.generate_invoice_button.setEnabled(can_manage_billing)

        logging.info(f"ClientMainWidget permissions applied for role: {role_name}")


    def _setup_notes_section(self, main_layout):
        try:
            logging.info("ClientMainWidget.setup_ui: Starting setup for Notes Section...")
            self.notes_edit = QTextEdit(self.client_info.get("notes", ""))
            self.notes_edit.setPlaceholderText(self.tr("Ajoutez des notes sur ce client..."))
            self.notes_group_box = QGroupBox(self.tr("Notes"))
            self.notes_group_box.setCheckable(True)
            notes_group_layout = QVBoxLayout(self.notes_group_box)
            self.notes_container_widget = QWidget()
            notes_container_layout = QVBoxLayout(self.notes_container_widget)
            notes_container_layout.setContentsMargins(0, 5, 0, 0)
            notes_container_layout.addWidget(self.notes_edit)
            notes_group_layout.addWidget(self.notes_container_widget)
            self.notes_group_box.setChecked(False)
            main_layout.addWidget(self.notes_group_box)
        except Exception as e:
            logging.error(f"Error in _setup_notes_section: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur UI"), self.tr("Erreur initialisation section notes:\n{0}").format(str(e)))

    def _setup_main_tabs_section(self, main_layout):
        try:
            logging.info("ClientMainWidget.setup_ui: Starting setup for Tabs Section...")
            # --- Collapsible Tabs Section ---

            self.tabs_group_box = QGroupBox(self.tr("Autres Informations"))
            self.tabs_group_box.setCheckable(True)
            tabs_group_layout = QVBoxLayout(self.tabs_group_box)
            self.tab_widget = QTabWidget()
            tabs_group_layout.addWidget(self.tab_widget)
            self.tabs_group_box.setChecked(False)
            main_layout.addWidget(self.tabs_group_box)

            # Instantiate and add DocumentsTab
            self.documents_tab_widget_ref = DocumentsTab(
                client_info=self.client_info,
                config=self.config,
                app_root_dir=self.app_root_dir,
                notification_manager=self.notification_manager,
                current_user_info=self.current_user_info,
                main_module_create_document_dialog=self.CreateDocumentDialog, # Pass reference
                main_module_compile_pdf_dialog=self.CompilePdfDialog,     # Pass reference
                main_module_generate_pdf_for_document=self.generate_pdf_for_document, # Pass reference
                parent_widget=self # Pass self as parent_widget for tr() and other potential calls
            )
            self.tab_widget.addTab(self.documents_tab_widget_ref, self.tr("Documents"))
            # self._setup_documents_tab() # This line is now replaced by the instantiation above

            # Instantiate and add ProductsTab
            self.products_tab_widget_ref = ProductsTab(
                client_info=self.client_info,
                config=self.config,
                notification_manager=self.notification_manager,
                current_user_info=self.current_user_info,
                main_module_product_dialog=self.ProductDialog, # Pass reference
                main_module_edit_product_line_dialog=self.EditProductLineDialog, # Pass reference
                parent_widget=self
            )
            self.tab_widget.addTab(self.products_tab_widget_ref, self.tr("Produits"))
            # self._setup_products_tab() # This line is now replaced

            # Instantiate and add DocumentNotesTab
            self.document_notes_tab_widget_ref = DocumentNotesTab(
                client_info=self.client_info,
                current_user_info=self.current_user_info,
                notification_manager=self.notification_manager,
                main_module_client_document_note_dialog=self.ClientDocumentNoteDialog, # Pass reference
                parent_widget=self
            )
            self.tab_widget.addTab(self.document_notes_tab_widget_ref, self.tr("Notes de Document"))
            # self._setup_document_notes_tab() # This line is now replaced

            # Instantiate and add ProductDimensionsTab
            self.product_dimensions_tab_widget_ref = ProductDimensionsTab(
                client_info=self.client_info,
                app_root_dir=self.app_root_dir,
                main_module_client_product_dimension_dialog=ClientProductDimensionDialog, # Pass class directly
                parent_widget=self
            )
            # Determine insertion index (e.g., after DocumentNotesTab or ProductsTab)
            # For simplicity, adding it after DocumentNotesTab if it exists.
            notes_tab_idx = -1
            for i in range(self.tab_widget.count()):
                if self.tab_widget.widget(i) == self.document_notes_tab_widget_ref:
                    notes_tab_idx = i
                    break
            if notes_tab_idx != -1:
                 self.tab_widget.insertTab(notes_tab_idx + 1, self.product_dimensions_tab_widget_ref, self.tr("Dimensions Produit (Global)"))
            else: # Fallback
                 self.tab_widget.addTab(self.product_dimensions_tab_widget_ref, self.tr("Dimensions Produit (Global)"))
            # self._setup_product_dimensions_tab() # This line is now replaced

            # self._setup_available_templates_tab() # Call removed

            # Instantiate and add SAVTab
            self.sav_tab_widget_ref = SAVTab(
                client_info=self.client_info,
                current_user_info=self.current_user_info,
                notification_manager=self.notification_manager,
                parent_widget=self
                # SAVTicketDialog is attempted to be imported by SAVTab itself or passed if already loaded in ClientMainWidget
            )
            self.tab_widget.addTab(self.sav_tab_widget_ref, self.tr("SAV"))
            # The SAVTab's __init__ calls update_sav_tab_visibility_and_load_data which handles enabling/disabling and loading.
            # logging.info("ClientMainWidget._setup_main_tabs_section: PRE-CALL self._setup_sav_tab()") # Old call replaced
            # try:
            #     logging.debug("ClientMainWidget._setup_main_tabs_section: ATTEMPTING CALL self._setup_sav_tab()")
            #     self._setup_sav_tab() # Old call replaced
            #     logging.info("ClientMainWidget._setup_main_tabs_section: POST-CALL self._setup_sav_tab() - SUCCESS")
            # except Exception as e:
            #     logging.error("ClientMainWidget._setup_main_tabs_section: CRITICAL ERROR DURING OR IMMEDIATELY AFTER CALL TO self._setup_sav_tab()", exc_info=True)
            #     QMessageBox.critical(self, self.tr("Erreur Critique"), self.tr("Une erreur critique est survenue lors de l'initialisation de l'onglet SAV."))

            # logging.info("ClientMainWidget._setup_main_tabs_section: PRE-CALL self._setup_assignments_tab()") # Call removed, assignments are now an internal tab
            # self._setup_assignments_tab() # Logic will be moved

            # Instantiate and add BillingTab
            self.billing_tab_widget_ref = BillingTab(
                client_info=self.client_info,
                current_user_info=self.current_user_info,
                notification_manager=self.notification_manager,
                config=self.config, # Pass main config
                parent_widget=self
            )
            self.tab_widget.addTab(self.billing_tab_widget_ref, QIcon(":/icons/credit-card.svg"), self.tr("Billing"))
            # self._setup_billing_tab() # This line is now replaced

        except Exception as e:
            logging.error(f"Error in _setup_main_tabs_section: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur UI"), self.tr("Erreur initialisation conteneur onglets principaux:\n{0}").format(str(e)))

    # _setup_available_templates_tab and load_available_templates removed.
    # handle_generate_template_button_clicked was only called by load_available_templates, so it can also be removed.

    # def _setup_documents_tab(self): # ENTIRE METHOD MOVED TO DocumentsTab
    #     pass

    def _setup_contacts_tab(self): # This method seems to have been removed in a previous step or intended for removal.
        # If it's truly gone, this section can be deleted. If it was for an *internal* contacts tab,
        # its logic would be part of the Client Info Section setup.
        # For now, assuming it's obsolete as contacts are an internal tab.
        pass # logging.info("ClientMainWidget.setup_ui: Starting setup for Contacts Tab Structure...")

    # def _setup_products_tab(self): # ENTIRE METHOD MOVED TO ProductsTab
    #     pass

    # def _setup_document_notes_tab(self): # ENTIRE METHOD MOVED TO DocumentNotesTab
    #     pass

    # def _setup_product_dimensions_tab(self): # ENTIRE METHOD MOVED TO ProductDimensionsTab
    #     pass

    # def _setup_sav_tab(self): # ENTIRE METHOD MOVED TO SAVTab
    #     pass

    def _setup_assignments_tab(self):
        try:
            logging.info("ClientMainWidget.setup_ui: Starting setup for Assignments Tab...")
            # --- Assignments Tab ---

            self.assignments_tab = QWidget()
            assignments_main_layout = QVBoxLayout(self.assignments_tab)
            self.assignments_sub_tabs = QTabWidget()
            assignments_main_layout.addWidget(self.assignments_sub_tabs)
            self.tab_widget.addTab(self.assignments_tab, self.tr("Affectations"))
            # Vendors/Sellers (CompanyPersonnel)
            assigned_vendors_widget = QWidget()
            assigned_vendors_layout = QVBoxLayout(assigned_vendors_widget)
            self.assigned_vendors_table = QTableWidget(); self.assigned_vendors_table.setColumnCount(4)
            self.assigned_vendors_table.setHorizontalHeaderLabels([self.tr("Nom"), self.tr("Rôle Projet"), self.tr("Email"), self.tr("Téléphone")])
            self.assigned_vendors_table.setSelectionBehavior(QAbstractItemView.SelectRows); self.assigned_vendors_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.assigned_vendors_table.horizontalHeader().setStretchLastSection(True)
            assigned_vendors_layout.addWidget(self.assigned_vendors_table)
            vendor_buttons_layout = QHBoxLayout()
            self.add_assigned_vendor_btn = QPushButton(self.tr("Ajouter Vendeur/Personnel")); self.add_assigned_vendor_btn.clicked.connect(self.handle_add_assigned_vendor)
            self.remove_assigned_vendor_btn = QPushButton(self.tr("Retirer Vendeur/Personnel")); self.remove_assigned_vendor_btn.clicked.connect(self.handle_remove_assigned_vendor)
            vendor_buttons_layout.addWidget(self.add_assigned_vendor_btn); vendor_buttons_layout.addWidget(self.remove_assigned_vendor_btn)
            assigned_vendors_layout.addLayout(vendor_buttons_layout)
            self.assignments_sub_tabs.addTab(assigned_vendors_widget, self.tr("Vendeurs & Personnel"))
            # Technicians
            assigned_technicians_widget = QWidget()
            assigned_technicians_layout = QVBoxLayout(assigned_technicians_widget)
            self.assigned_technicians_table = QTableWidget(); self.assigned_technicians_table.setColumnCount(4)
            self.assigned_technicians_table.setHorizontalHeaderLabels([self.tr("Nom"), self.tr("Rôle Projet"), self.tr("Email"), self.tr("Téléphone")])
            self.assigned_technicians_table.setSelectionBehavior(QAbstractItemView.SelectRows); self.assigned_technicians_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.assigned_technicians_table.horizontalHeader().setStretchLastSection(True)
            assigned_technicians_layout.addWidget(self.assigned_technicians_table)
            technician_buttons_layout = QHBoxLayout()
            self.add_assigned_technician_btn = QPushButton(self.tr("Ajouter Technicien")); self.add_assigned_technician_btn.clicked.connect(self.handle_add_assigned_technician)
            self.remove_assigned_technician_btn = QPushButton(self.tr("Retirer Technicien")); self.remove_assigned_technician_btn.clicked.connect(self.handle_remove_assigned_technician)
            technician_buttons_layout.addWidget(self.add_assigned_technician_btn); technician_buttons_layout.addWidget(self.remove_assigned_technician_btn)
            assigned_technicians_layout.addLayout(technician_buttons_layout)
            self.assignments_sub_tabs.addTab(assigned_technicians_widget, self.tr("Techniciens"))
            # Transporters
            assigned_transporters_widget = QWidget()
            assigned_transporters_layout = QVBoxLayout(assigned_transporters_widget)
            self.assigned_transporters_table = QTableWidget(); self.assigned_transporters_table.setColumnCount(6)
            self.assigned_transporters_table.setHorizontalHeaderLabels([self.tr("Nom Transporteur"), self.tr("Contact"), self.tr("Téléphone"), self.tr("Détails Transport"), self.tr("Coût Estimé"), self.tr("Actions")])
            self.assigned_transporters_table.setSelectionBehavior(QAbstractItemView.SelectRows); self.assigned_transporters_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.assigned_transporters_table.horizontalHeader().setStretchLastSection(True)
            assigned_transporters_layout.addWidget(self.assigned_transporters_table)
            transporter_buttons_layout = QHBoxLayout()
            self.add_assigned_transporter_btn = QPushButton(self.tr("Ajouter Transporteur")); self.add_assigned_transporter_btn.clicked.connect(self.handle_add_assigned_transporter)
            self.remove_assigned_transporter_btn = QPushButton(self.tr("Retirer Transporteur")); self.remove_assigned_transporter_btn.clicked.connect(self.handle_remove_assigned_transporter)
            transporter_buttons_layout.addWidget(self.add_assigned_transporter_btn); transporter_buttons_layout.addWidget(self.remove_assigned_transporter_btn)
            assigned_transporters_layout.addLayout(transporter_buttons_layout)
            self.assignments_sub_tabs.addTab(assigned_transporters_widget, self.tr("Transporteurs"))
            # Freight Forwarders
            assigned_forwarders_widget = QWidget()
            assigned_forwarders_layout = QVBoxLayout(assigned_forwarders_widget)
            self.assigned_forwarders_table = QTableWidget(); self.assigned_forwarders_table.setColumnCount(5)
            self.assigned_forwarders_table.setHorizontalHeaderLabels([self.tr("Nom Transitaire"), self.tr("Contact"), self.tr("Téléphone"), self.tr("Description Tâche"), self.tr("Coût Estimé")])
            self.assigned_forwarders_table.setSelectionBehavior(QAbstractItemView.SelectRows); self.assigned_forwarders_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.assigned_forwarders_table.horizontalHeader().setStretchLastSection(True)
            assigned_forwarders_layout.addWidget(self.assigned_forwarders_table)
            forwarder_buttons_layout = QHBoxLayout()
            self.add_assigned_forwarder_btn = QPushButton(self.tr("Ajouter Transitaire")); self.add_assigned_forwarder_btn.clicked.connect(self.handle_add_assigned_forwarder)
            self.remove_assigned_forwarder_btn = QPushButton(self.tr("Retirer Transitaire")); self.remove_assigned_forwarder_btn.clicked.connect(self.handle_remove_assigned_forwarder)
            forwarder_buttons_layout.addWidget(self.add_assigned_forwarder_btn); forwarder_buttons_layout.addWidget(self.remove_assigned_forwarder_btn)
            assigned_forwarders_layout.addLayout(forwarder_buttons_layout)
            self.assignments_sub_tabs.addTab(assigned_forwarders_widget, self.tr("Transitaires"))

            # Sub-Tab: Money Transfer Agents
            mta_widget = QWidget()
            mta_layout = QVBoxLayout(mta_widget)

            # Project/Order Selector for MTA
            mta_project_selector_layout = QHBoxLayout()
            mta_project_selector_layout.addWidget(QLabel(self.tr("Sélectionner Commande/Projet:")))
            self.mta_project_selector_combo = QComboBox()
            mta_project_selector_layout.addWidget(self.mta_project_selector_combo)
            mta_layout.addLayout(mta_project_selector_layout)

            # Table for Assigned Money Transfer Agents
            self.assigned_mta_table = QTableWidget()
            self.assigned_mta_table.setColumnCount(8) # Agent Name, Type, Email, Phone, Details, Fee, Email Status, Actions
            self.assigned_mta_table.setHorizontalHeaderLabels([
                self.tr("Nom Agent"), self.tr("Type"), self.tr("Email"), self.tr("Téléphone"),
                self.tr("Détails Affectation"), self.tr("Frais Estimés"), self.tr("Statut Email"), self.tr("Actions")
            ])
            self.assigned_mta_table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.assigned_mta_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.assigned_mta_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) # Stretch to fill
            self.assigned_mta_table.setMinimumHeight(150) # Example height
            mta_layout.addWidget(self.assigned_mta_table)

            # Buttons for MTA
            mta_buttons_layout = QHBoxLayout()
            self.add_assigned_mta_btn = QPushButton(self.tr("Assigner Agent de Transfert"))
            self.remove_assigned_mta_btn = QPushButton(self.tr("Retirer Agent de Transfert"))
            mta_buttons_layout.addWidget(self.add_assigned_mta_btn)
            mta_buttons_layout.addWidget(self.remove_assigned_mta_btn)
            mta_layout.addLayout(mta_buttons_layout)

            self.assignments_sub_tabs.addTab(mta_widget, self.tr("Agents de Transfert d'Argent"))

        except Exception as e:
            logging.error(f"Error during UI setup of Assignments Tab Structure: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur UI"), self.tr("Erreur initialisation structure onglet Affectations:\n{0}").format(str(e)))

        # Call to load SAV tickets table initially if tab is visible
        try:
            logging.info("ClientMainWidget.setup_ui: Updating SAV tab visibility and loading initial data...")
            self.update_sav_tab_visibility() # This calls load_purchase_history_table and load_sav_tickets_table
        except Exception as e:
            logging.error(f"Error during initial visibility update/load of SAV tab: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Chargement Partiel"), self.tr("Une erreur est survenue lors de la mise à jour/chargement initial de l'onglet SAV:\n{0}").format(str(e)))

        # Initial load for assignment tabs
        try:
            self.load_assigned_vendors_personnel()
        except Exception as e:
            logging.error(f"Error during initial load of Assigned Vendors/Personnel: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Chargement Partiel"), self.tr("Une erreur est survenue lors du chargement des vendeurs/personnel assignés:\n{0}").format(str(e)))
        try:
            self.load_assigned_technicians()
        except Exception as e:
            logging.error(f"Error during initial load of Assigned Technicians: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Chargement Partiel"), self.tr("Une erreur est survenue lors du chargement des techniciens assignés:\n{0}").format(str(e)))
        try:
            self.load_assigned_transporters()
        except Exception as e:
            logging.error(f"Error during initial load of Assigned Transporters: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Chargement Partiel"), self.tr("Une erreur est survenue lors du chargement des transporteurs assignés:\n{0}").format(str(e)))
        try:
            self.load_assigned_freight_forwarders()
        except Exception as e:
            logging.error(f"Error during initial load of Assigned Freight Forwarders: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Chargement Partiel"), self.tr("Une erreur est survenue lors du chargement des transitaires assignés:\n{0}").format(str(e)))

        # Connect selection changed signals for assignment tables
        self.assigned_vendors_table.itemSelectionChanged.connect(self.update_assigned_vendors_buttons_state)
        self.assigned_technicians_table.itemSelectionChanged.connect(self.update_assigned_technicians_buttons_state)
        self.assigned_transporters_table.itemSelectionChanged.connect(self.update_assigned_transporters_buttons_state)
        self.assigned_forwarders_table.itemSelectionChanged.connect(self.update_assigned_forwarders_buttons_state)
        # Connections for MTA tab
        self.mta_project_selector_combo.currentIndexChanged.connect(self.handle_mta_project_selection_changed)
        self.add_assigned_mta_btn.clicked.connect(self.handle_add_assigned_mta)
        self.remove_assigned_mta_btn.clicked.connect(self.handle_remove_assigned_mta)
        self.assigned_mta_table.itemSelectionChanged.connect(self.update_mta_buttons_state)

        # Initial load for MTA project selector
        # self.load_projects_for_mta_combo() # This will be called when the assignments tab is created
        # Initial state for MTA buttons
        # self.add_assigned_mta_btn.setEnabled(False) # These buttons will be part of the new internal assignments tab
        # self.remove_assigned_mta_btn.setEnabled(False)

    # def _setup_assignments_tab(self): # Method completely removed
    #     pass


    def _setup_commandes_tab(self):
        """Sets up the Commandes tab."""
        try:
            logging.info("ClientMainWidget.setup_ui: Starting setup for Commandes Tab...")
            self.commandes_tab_widget = CommandeWidget(
                client_info=self.client_info,
                current_user_info=self.current_user_info,
                parent=self
            )
            # Add this as a top-level tab in self.tab_widget (main tab container)
            # Or, if Commandes should be part of the "Autres Informations" group box, then add to self.tab_widget
            # For now, let's add it to the main self.tab_widget
            if hasattr(self, 'tab_widget'):
                 # Insert it before "Available Templates" or as the second tab for prominence
                docs_tab_index = -1
                for i in range(self.tab_widget.count()):
                    if self.tab_widget.tabText(i) == self.tr("Documents"):
                        docs_tab_index = i
                        break

                if docs_tab_index != -1:
                    self.tab_widget.insertTab(docs_tab_index + 1, self.commandes_tab_widget, self.tr("Commandes"))
                else: # Fallback if Documents tab isn't found by that exact name
                    self.tab_widget.addTab(self.commandes_tab_widget, self.tr("Commandes"))

                logging.info("ClientMainWidget._setup_commandes_tab: Commandes tab added.")
            else:
                logging.error("ClientMainWidget._setup_commandes_tab: self.tab_widget not found. Cannot add Commandes tab.")

        except Exception as e:
            logging.error(f"Error in _setup_commandes_tab: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur UI"), self.tr("Erreur initialisation onglet Commandes:\n{0}").format(str(e)))

    def _setup_commandes_tab(self):
        """Sets up the Commandes tab."""
        try:
            logging.info("ClientMainWidget.setup_ui: Starting setup for Commandes Tab...")
            self.commandes_tab_widget = CommandeWidget(
                client_info=self.client_info,
                current_user_info=self.current_user_info,
                parent=self
            )
            # Add this as a top-level tab in self.tab_widget (main tab container)
            # Or, if Commandes should be part of the "Autres Informations" group box, then add to self.tab_widget
            # For now, let's add it to the main self.tab_widget
            if hasattr(self, 'tab_widget'):
                 # Insert it before "Available Templates" or as the second tab for prominence
                docs_tab_index = -1
                for i in range(self.tab_widget.count()):
                    if self.tab_widget.tabText(i) == self.tr("Documents"):
                        docs_tab_index = i
                        break

                if docs_tab_index != -1:
                    self.tab_widget.insertTab(docs_tab_index + 1, self.commandes_tab_widget, self.tr("Commandes"))
                else: # Fallback if Documents tab isn't found by that exact name
                    self.tab_widget.addTab(self.commandes_tab_widget, self.tr("Commandes"))

                logging.info("ClientMainWidget._setup_commandes_tab: Commandes tab added.")
            else:
                logging.error("ClientMainWidget._setup_commandes_tab: self.tab_widget not found. Cannot add Commandes tab.")

        except Exception as e:
            logging.error(f"Error in _setup_commandes_tab: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur UI"), self.tr("Erreur initialisation onglet Commandes:\n{0}").format(str(e)))

    def _setup_commandes_tab(self):
        """Sets up the Commandes tab."""
        try:
            logging.info("ClientMainWidget.setup_ui: Starting setup for Commandes Tab...")
            self.commandes_tab_widget = CommandeWidget(
                client_info=self.client_info,
                current_user_info=self.current_user_info,
                parent=self
            )
            # Add this as a top-level tab in self.tab_widget (main tab container)
            # Or, if Commandes should be part of the "Autres Informations" group box, then add to self.tab_widget
            # For now, let's add it to the main self.tab_widget
            if hasattr(self, 'tab_widget'):
                 # Insert it before "Available Templates" or as the second tab for prominence
                docs_tab_index = -1
                for i in range(self.tab_widget.count()):
                    if self.tab_widget.tabText(i) == self.tr("Documents"):
                        docs_tab_index = i
                        break

                if docs_tab_index != -1:
                    self.tab_widget.insertTab(docs_tab_index + 1, self.commandes_tab_widget, self.tr("Commandes"))
                else: # Fallback if Documents tab isn't found by that exact name
                    self.tab_widget.addTab(self.commandes_tab_widget, self.tr("Commandes"))

                logging.info("ClientMainWidget._setup_commandes_tab: Commandes tab added.")
            else:
                logging.error("ClientMainWidget._setup_commandes_tab: self.tab_widget not found. Cannot add Commandes tab.")

        except Exception as e:
            logging.error(f"Error in _setup_commandes_tab: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur UI"), self.tr("Erreur initialisation onglet Commandes:\n{0}").format(str(e)))

    # def _setup_billing_tab(self): # ENTIRE METHOD MOVED TO BillingTab
    #     pass

    # def handle_generate_final_invoice(self): # MOVED to BillingTab
    #     pass

    # def setup_ui(self):
    #     main_layout = QVBoxLayout(self)
    #     main_layout.setContentsMargins(15, 15, 15, 15)
    #     main_layout.setSpacing(15)

    #     self._setup_main_tabs_section(main_layout)
    #     self._setup_notes_section(main_layout)
    #     self._setup_main_tabs_section(main_layout) # This will call sub-methods for each tab

    #     # Initial data loading calls
    #     try: self.populate_doc_table()
    #     except Exception as e: logging.error(f"Error initial load Documents tab: {e}", exc_info=True)
    #     try: self.load_contacts()
    #     except Exception as e: logging.error(f"Error initial load Contacts tab: {e}", exc_info=True)
    #     try: self.load_products()
    #     except Exception as e: logging.error(f"Error initial load Products tab: {e}", exc_info=True)
    #     try: self.load_document_notes_filters()
    #     except Exception as e: logging.error(f"Error initial load Doc Notes Filters: {e}", exc_info=True)
    #     try: self.load_document_notes_table()
    #     except Exception as e: logging.error(f"Error initial load Doc Notes tab: {e}", exc_info=True)
    #     try: self.update_sav_tab_visibility()
    #     except Exception as e: logging.error(f"Error initial SAV tab visibility/load: {e}", exc_info=True)
    #     try: self.load_assigned_vendors_personnel()
    #     except Exception as e: logging.error(f"Error initial load Assigned Vendors: {e}", exc_info=True)
    #     try: self.load_assigned_technicians()
    #     except Exception as e: logging.error(f"Error initial load Assigned Technicians: {e}", exc_info=True)
    #     try: self.load_assigned_transporters()
    #     except Exception as e: logging.error(f"Error initial load Assigned Transporters: {e}", exc_info=True)
    #     try: self.load_assigned_freight_forwarders()
    #     except Exception as e: logging.error(f"Error initial load Assigned Forwarders: {e}", exc_info=True)

    #     # Connect accordion group box toggled signals
    #     if hasattr(self, 'client_info_group_box'):
    #          self.client_info_group_box.toggled.connect(self._handle_client_info_section_toggled)
    #     if hasattr(self, 'notes_group_box'):
    #          self.notes_group_box.toggled.connect(self._handle_notes_section_toggled)
    #     if hasattr(self, 'tabs_group_box'):
    #          self.tabs_group_box.toggled.connect(self._handle_tabs_section_toggled)
    #     # Event filter for notes auto-save
    #     if hasattr(self, 'notes_edit'):
    #         self.notes_edit.installEventFilter(self)


    def _handle_edit_pdf_action(self, file_path, document_id):
        if file_path and os.path.exists(file_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
        # layout = QVBoxLayout(self) # This line seems out of place, QVBoxLayout is already set for the widget
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        try:
            self._setup_main_tabs_section(layout) #FIXED
            # --- Collapsible Client Info Section ---
            self.client_info_group_box = QGroupBox(self.client_info.get('client_name', self.tr("Client Information")))
            self.client_info_group_box.setCheckable(True)
            client_info_group_layout = QVBoxLayout(self.client_info_group_box) # Layout for the GroupBox itself

            self.info_container_widget = QWidget() # Container for all info elements
            info_container_layout = QVBoxLayout(self.info_container_widget)
            info_container_layout.setContentsMargins(0, 5, 0, 0) # Adjust margins as needed
            info_container_layout.setSpacing(10) # Adjust spacing as needed

            self.header_label = QLabel(f"<h2>{self.client_info.get('client_name', self.tr('Client Inconnu'))}</h2>")
            self.header_label.setObjectName("clientHeaderLabel")
            info_container_layout.addWidget(self.header_label)

            action_layout = QHBoxLayout()
            self.create_docs_btn = QPushButton(self.tr("Envoyer Mail"))
            self.create_docs_btn.setIcon(QIcon.fromTheme("mail-send", QIcon(":/icons/bell.svg"))) # Using bell.svg as fallback
            self.create_docs_btn.setToolTip(self.tr("Envoyer un email au client"))
            self.create_docs_btn.setObjectName("primaryButton") # Keep primary styling for now
            try:
                # Disconnect previous connection if it exists
                self.create_docs_btn.clicked.disconnect(self.open_create_docs_dialog)
            except TypeError:
                print("Note: self.create_docs_btn.clicked was not connected to self.open_create_docs_dialog or already disconnected.")
            self.create_docs_btn.clicked.connect(self.open_send_email_dialog) # Connect to new method
            action_layout.addWidget(self.create_docs_btn)

            self.compile_pdf_btn = QPushButton(self.tr("Compiler PDF"))
            self.compile_pdf_btn.setIcon(QIcon.fromTheme("document-export"))
            self.compile_pdf_btn.setProperty("primary", True)
            self.compile_pdf_btn.clicked.connect(self.open_compile_pdf_dialog)
            action_layout.addWidget(self.compile_pdf_btn)

            self.edit_save_client_btn = QPushButton(self.tr("Modifier Client"))
            self.edit_save_client_btn.setIcon(QIcon.fromTheme("document-edit", QIcon(":/icons/pencil.svg")))
            self.edit_save_client_btn.setToolTip(self.tr("Modifier les informations du client"))
            self.edit_save_client_btn.clicked.connect(self.toggle_client_edit_mode)
            action_layout.addWidget(self.edit_save_client_btn)

            self.send_whatsapp_btn = QPushButton(self.tr("Send WhatsApp"))
            self.send_whatsapp_btn.setIcon(QIcon.fromTheme("contact-new", QIcon(":/icons/user.svg"))) # Changed placeholder
            self.send_whatsapp_btn.setToolTip(self.tr("Send a WhatsApp message to the client"))
            self.send_whatsapp_btn.clicked.connect(self.open_send_whatsapp_dialog)
            action_layout.addWidget(self.send_whatsapp_btn)
            info_container_layout.addLayout(action_layout)

            # Status combo (part of details, but initialized here due to load_statuses)
            self.status_combo = QComboBox()
            self.load_statuses()
            self.status_combo.setCurrentText(self.client_info.get("status", self.tr("En cours")))
            self.status_combo.currentTextChanged.connect(self.update_client_status)

            # Details layout (QFormLayout)
            self.details_layout = QFormLayout()
            self.details_layout.setLabelAlignment(Qt.AlignLeft)
            self.details_layout.setSpacing(10)

            # Initialize category labels (used in populate_details_layout)
            self.category_label = QLabel(self.tr("Catégorie:"))
            self.category_value_label = QLabel()

            self.populate_details_layout() # Builds the details_layout
            info_container_layout.addLayout(self.details_layout)

            client_info_group_layout.addWidget(self.info_container_widget)
            self.client_info_group_box.setChecked(True)
            layout.addWidget(self.client_info_group_box)
        except Exception as e:
            logging.error(f"Error during UI setup of Client Info Section: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur UI"), self.tr("Erreur initialisation section infos client:\n{0}").format(str(e)))

        try:
            self.notes_edit = QTextEdit(self.client_info.get("notes", ""))
            self.notes_edit.setPlaceholderText(self.tr("Ajoutez des notes sur ce client..."))
            # --- Collapsible Notes Section ---
            self.notes_group_box = QGroupBox(self.tr("Notes"))
            self.notes_group_box.setCheckable(True)
            notes_group_layout = QVBoxLayout(self.notes_group_box)
            self.notes_container_widget = QWidget()
            notes_container_layout = QVBoxLayout(self.notes_container_widget)
            notes_container_layout.setContentsMargins(0, 5, 0, 0)
            notes_container_layout.addWidget(self.notes_edit)
            notes_group_layout.addWidget(self.notes_container_widget)
            self.notes_group_box.setChecked(False)
            layout.addWidget(self.notes_group_box)
        except Exception as e:
            logging.error(f"Error during UI setup of Notes Section: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur UI"), self.tr("Erreur initialisation section notes:\n{0}").format(str(e)))

        try:
            # --- Collapsible Tabs Section ---
            self.tabs_group_box = QGroupBox(self.tr("Autres Informations"))
            self.tabs_group_box.setCheckable(True)
            tabs_group_layout = QVBoxLayout(self.tabs_group_box)
            self.tab_widget = QTabWidget()
            tabs_group_layout.addWidget(self.tab_widget)
            self.tabs_group_box.setChecked(False)
            layout.addWidget(self.tabs_group_box)
        except Exception as e:
            logging.error(f"Error during UI setup of Main Tabs Container: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur UI"), self.tr("Erreur initialisation conteneur onglets:\n{0}").format(str(e)))

        try:
            # --- Documents Tab Structure ---
            docs_tab = QWidget(); docs_layout = QVBoxLayout(docs_tab)
            self.doc_filter_layout_widget = QWidget()
            doc_filter_layout = QHBoxLayout(self.doc_filter_layout_widget)
            doc_filter_layout.setContentsMargins(0,0,0,0)
            doc_filter_label = QLabel(self.tr("Filtrer par Commande:"))
            doc_filter_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            doc_filter_layout.addWidget(doc_filter_label)
            self.doc_order_filter_combo = QComboBox()
            self.doc_order_filter_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.doc_order_filter_combo.currentIndexChanged.connect(self.populate_doc_table)
            doc_filter_layout.addWidget(self.doc_order_filter_combo)
            doc_filter_layout.addSpacing(10)
            doc_lang_filter_label = QLabel(self.tr("Filtrer par Langue:"))
            doc_lang_filter_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            doc_filter_layout.addWidget(doc_lang_filter_label)
            self.doc_language_filter_combo = QComboBox()
            self.doc_language_filter_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.doc_language_filter_combo.addItem(self.tr("Toutes"), "ALL")
            for lang_code in SUPPORTED_LANGUAGES:
                self.doc_language_filter_combo.addItem(lang_code, lang_code)
            self.doc_language_filter_combo.currentIndexChanged.connect(self.populate_doc_table)
            doc_filter_layout.addWidget(self.doc_language_filter_combo)
            doc_filter_layout.addSpacing(10)
            doc_type_filter_label = QLabel(self.tr("Filtrer par Type:"))
            doc_type_filter_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            doc_filter_layout.addWidget(doc_type_filter_label)
            self.doc_type_filter_combo = QComboBox()
            self.doc_type_filter_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.doc_type_filter_combo.addItem(self.tr("Tous"), "ALL")
            self.doc_type_filter_combo.addItem("HTML", "HTML")
            self.doc_type_filter_combo.addItem("PDF", "PDF")
            self.doc_type_filter_combo.addItem("XLSX", "XLSX")
            self.doc_type_filter_combo.addItem("DOCX", "DOCX")
            self.doc_type_filter_combo.addItem(self.tr("Autre"), "OTHER")
            self.doc_type_filter_combo.currentIndexChanged.connect(self.populate_doc_table)
            doc_filter_layout.addWidget(self.doc_type_filter_combo)

            doc_filter_layout.addStretch(1) # Add stretch before the button
            if hasattr(self, 'compile_pdf_btn'): # Ensure button was created
                doc_filter_layout.addWidget(self.compile_pdf_btn) # Add compile PDF button here

            docs_layout.addWidget(self.doc_filter_layout_widget)
            self.doc_filter_layout_widget.setVisible(True)
            self.documents_empty_label = QLabel(self.tr("Aucun document trouvé pour ce client.\nUtilisez les boutons ci-dessous pour ajouter ou générer des documents."))
            self.documents_empty_label.setAlignment(Qt.AlignCenter)
            font_docs_empty = self.documents_empty_label.font()
            font_docs_empty.setPointSize(10)
            self.documents_empty_label.setFont(font_docs_empty)
            docs_layout.addWidget(self.documents_empty_label)
            self.doc_table = QTableWidget()
            self.doc_table.setColumnCount(5)
            self.doc_table.setHorizontalHeaderLabels([self.tr("Nom"), self.tr("Type"), self.tr("Langue"), self.tr("Date"), self.tr("Actions")])
            self.doc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.doc_table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.doc_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            docs_layout.addWidget(self.doc_table)
            doc_btn_layout = QHBoxLayout()
            self.add_doc_btn = QPushButton(self.tr("Importer Document"))
            self.add_doc_btn.setIcon(QIcon(":/icons/file-plus.svg"))
            self.add_doc_btn.setToolTip(self.tr("Importer un fichier document existant pour ce client"))
            self.add_doc_btn.clicked.connect(self.add_document)
            doc_btn_layout.addWidget(self.add_doc_btn)
            self.refresh_docs_btn = QPushButton(self.tr("Actualiser"))
            self.refresh_docs_btn.setIcon(QIcon.fromTheme("view-refresh"))
            self.refresh_docs_btn.clicked.connect(self.populate_doc_table)
            doc_btn_layout.addWidget(self.refresh_docs_btn)
            self.add_template_btn = QPushButton(self.tr("Générer via Modèle"))
            self.add_template_btn.setIcon(QIcon.fromTheme("document-new", QIcon(":/icons/file-plus.svg")))
            self.add_template_btn.setToolTip(self.tr("Générer un nouveau document pour ce client à partir d'un modèle"))
            self.add_template_btn.clicked.connect(self.open_create_docs_dialog)
            doc_btn_layout.addWidget(self.add_template_btn)
            docs_layout.addLayout(doc_btn_layout)
            self.tab_widget.addTab(docs_tab, self.tr("Documents"))
        except Exception as e:
            logging.error(f"Error during UI setup of Documents Tab Structure: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur UI"), self.tr("Erreur initialisation structure onglet Documents:\n{0}").format(str(e)))

        try:
            # --- Contacts Tab Structure ---
            contacts_tab = QWidget()
            contacts_layout = QVBoxLayout(contacts_tab)
            self.contacts_table = QTableWidget()
            self.contacts_table.setColumnCount(5)
            self.contacts_table.setHorizontalHeaderLabels([
                self.tr("Nom"), self.tr("Email"), self.tr("Téléphone"),
                self.tr("Position"), self.tr("Principal")
            ])
            self.contacts_table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.contacts_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.contacts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.contacts_table.setAlternatingRowColors(True)
            self.contacts_table.cellDoubleClicked.connect(self.edit_contact)
            self.contacts_empty_label = QLabel(self.tr("Aucun contact ajouté pour ce client.\nCliquez sur '➕ Ajouter' pour commencer."))
            self.contacts_empty_label.setAlignment(Qt.AlignCenter)
            font = self.contacts_empty_label.font()
            font.setPointSize(10)
            self.contacts_empty_label.setFont(font)
            contacts_layout.addWidget(self.contacts_empty_label)
            contacts_layout.addWidget(self.contacts_table)
            contacts_pagination_layout = QHBoxLayout()
            self.prev_contact_button = QPushButton("<< Précédent")
            self.prev_contact_button.setObjectName("paginationButton")
            self.prev_contact_button.clicked.connect(self.prev_contact_page)
            self.contact_page_info_label = QLabel("Page 1 / 1")
            self.contact_page_info_label.setObjectName("paginationLabel")
            self.next_contact_button = QPushButton("Suivant >>")
            self.next_contact_button.setObjectName("paginationButton")
            self.next_contact_button.clicked.connect(self.next_contact_page)
            contacts_pagination_layout.addStretch()
            contacts_pagination_layout.addWidget(self.prev_contact_button)
            contacts_pagination_layout.addWidget(self.contact_page_info_label)
            contacts_pagination_layout.addWidget(self.next_contact_button)
            contacts_pagination_layout.addStretch()
            contacts_layout.addLayout(contacts_pagination_layout)
            contacts_btn_layout = QHBoxLayout()
            self.add_contact_btn = QPushButton(self.tr("Ajouter")); self.add_contact_btn.setIcon(QIcon(":/icons/user-plus.svg")); self.add_contact_btn.setToolTip(self.tr("Ajouter un nouveau contact pour ce client")); self.add_contact_btn.clicked.connect(self.add_contact); contacts_btn_layout.addWidget(self.add_contact_btn)
            self.edit_contact_btn = QPushButton(self.tr("Modifier")); self.edit_contact_btn.setIcon(QIcon(":/icons/pencil.svg")); self.edit_contact_btn.setToolTip(self.tr("Modifier le contact sélectionné")); self.edit_contact_btn.clicked.connect(self.edit_contact); contacts_btn_layout.addWidget(self.edit_contact_btn)
            self.remove_contact_btn = QPushButton(self.tr("Supprimer")); self.remove_contact_btn.setIcon(QIcon(":/icons/trash.svg")); self.remove_contact_btn.setToolTip(self.tr("Supprimer le lien vers le contact sélectionné pour ce client")); self.remove_contact_btn.setObjectName("dangerButton"); self.remove_contact_btn.clicked.connect(self.remove_contact); contacts_btn_layout.addWidget(self.remove_contact_btn)
            contacts_layout.addLayout(contacts_btn_layout)
            self.tab_widget.addTab(contacts_tab, self.tr("Contacts"))
        except Exception as e:
            logging.error(f"Error during UI setup of Contacts Tab Structure: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur UI"), self.tr("Erreur initialisation structure onglet Contacts:\n{0}").format(str(e)))

        try:
            # --- Products Tab Structure ---
            products_tab = QWidget()
            products_layout = QVBoxLayout(products_tab)
            product_filters_layout = QHBoxLayout()
            product_filters_layout.addWidget(QLabel(self.tr("Filtrer par langue:")))
            self.product_lang_filter_combo = QComboBox()
            self.product_lang_filter_combo.addItem(self.tr("All Languages"), None)
            self.product_lang_filter_combo.addItem(self.tr("English (en)"), "en")
            self.product_lang_filter_combo.addItem(self.tr("French (fr)"), "fr")
            self.product_lang_filter_combo.addItem(self.tr("Arabic (ar)"), "ar")
            self.product_lang_filter_combo.addItem(self.tr("Turkish (tr)"), "tr")
            self.product_lang_filter_combo.addItem(self.tr("Portuguese (pt)"), "pt")
            self.product_lang_filter_combo.currentTextChanged.connect(self.load_products)
            product_filters_layout.addWidget(self.product_lang_filter_combo)
            product_filters_layout.addStretch()
            products_layout.addLayout(product_filters_layout)
            self.products_empty_label = QLabel(self.tr("Aucun produit ajouté pour ce client.\nCliquez sur '➕ Ajouter' pour commencer."))
            self.products_empty_label.setAlignment(Qt.AlignCenter)
            font_products_empty = self.products_empty_label.font()
            font_products_empty.setPointSize(10)
            self.products_empty_label.setFont(font_products_empty)
            products_layout.addWidget(self.products_empty_label)
            self.products_table = QTableWidget()
            self.products_table.setColumnCount(8)
            self.products_table.setHorizontalHeaderLabels([
                self.tr("ID"), self.tr("Nom Produit"), self.tr("Description"),
                self.tr("Poids"), self.tr("Dimensions"),
                self.tr("Qté"), self.tr("Prix Unitaire"), self.tr("Prix Total")
            ])
            self.products_table.setEditTriggers(QAbstractItemView.DoubleClicked)
            self.products_table.itemChanged.connect(self.handle_product_item_changed)
            self.products_table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.products_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.products_table.hideColumn(0)
            products_layout.addWidget(self.products_table)
            products_btn_layout = QHBoxLayout()
            self.add_product_btn = QPushButton(self.tr("Ajouter")); self.add_product_btn.setIcon(QIcon(":/icons/plus-circle.svg")); self.add_product_btn.setToolTip(self.tr("Ajouter un produit pour ce client/projet")); self.add_product_btn.clicked.connect(self.add_product); products_btn_layout.addWidget(self.add_product_btn)
            self.edit_product_btn = QPushButton(self.tr("Modifier")); self.edit_product_btn.setIcon(QIcon(":/icons/pencil.svg")); self.edit_product_btn.setToolTip(self.tr("Modifier le produit sélectionné")); self.edit_product_btn.clicked.connect(self.edit_product); products_btn_layout.addWidget(self.edit_product_btn)
            self.remove_product_btn = QPushButton(self.tr("Supprimer")); self.remove_product_btn.setIcon(QIcon(":/icons/trash.svg")); self.remove_product_btn.setToolTip(self.tr("Supprimer le produit sélectionné de ce client/projet")); self.remove_product_btn.setObjectName("dangerButton"); self.remove_product_btn.clicked.connect(self.remove_product); products_btn_layout.addWidget(self.remove_product_btn)
            products_layout.addLayout(products_btn_layout)
            self.tab_widget.addTab(products_tab, self.tr("Produits"))
        except Exception as e:
            logging.error(f"Error during UI setup of Products Tab Structure: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur UI"), self.tr("Erreur initialisation structure onglet Produits:\n{0}").format(str(e)))

        try:
            # --- Document Notes Tab Structure ---
            self.document_notes_tab = QWidget()
            doc_notes_layout = QVBoxLayout(self.document_notes_tab)
            doc_notes_filters_layout = QHBoxLayout()
            doc_notes_filters_layout.addWidget(QLabel(self.tr("Type de Document:")))
            self.doc_notes_type_filter_combo = QComboBox()
            doc_notes_filters_layout.addWidget(self.doc_notes_type_filter_combo)
            doc_notes_filters_layout.addWidget(QLabel(self.tr("Langue:")))
            self.doc_notes_lang_filter_combo = QComboBox()
            doc_notes_filters_layout.addWidget(self.doc_notes_lang_filter_combo)
            doc_notes_filters_layout.addStretch()
            doc_notes_layout.addLayout(doc_notes_filters_layout)
            self.document_notes_table = QTableWidget()
            self.document_notes_table.setColumnCount(5)
            self.document_notes_table.setHorizontalHeaderLabels([
                self.tr("Type Document"), self.tr("Langue"),
                self.tr("Aperçu Note"), self.tr("Actif"), self.tr("Actions")
            ])
            self.document_notes_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
            self.document_notes_table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.document_notes_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            doc_notes_layout.addWidget(self.document_notes_table)
            doc_notes_buttons_layout = QHBoxLayout()
            self.add_doc_note_button = QPushButton(self.tr("Ajouter Note de Document"))
            self.add_doc_note_button.setIcon(QIcon.fromTheme("document-new"))
            doc_notes_buttons_layout.addWidget(self.add_doc_note_button)
            self.refresh_doc_notes_button = QPushButton(self.tr("Actualiser Liste"))
            self.refresh_doc_notes_button.setIcon(QIcon.fromTheme("view-refresh"))
            doc_notes_buttons_layout.addWidget(self.refresh_doc_notes_button)
            doc_notes_buttons_layout.addStretch()
            doc_notes_layout.addLayout(doc_notes_buttons_layout)
            self.document_notes_tab.setLayout(doc_notes_layout)
            self.tab_widget.addTab(self.document_notes_tab, self.tr("Notes de Document"))
        except Exception as e:
            logging.error(f"Error during UI setup of Document Notes Tab Structure: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur UI"), self.tr("Erreur initialisation structure onglet Notes de Document:\n{0}").format(str(e)))

        self.doc_notes_type_filter_combo.currentIndexChanged.connect(self.load_document_notes_table)
        self.doc_notes_lang_filter_combo.currentIndexChanged.connect(self.load_document_notes_table)
        self.add_doc_note_button.clicked.connect(self.on_add_document_note)
        self.refresh_doc_notes_button.clicked.connect(self.load_document_notes_table)

        try:
            # --- Product Dimensions Tab Structure ---
            self.product_dimensions_tab = QWidget()
            prod_dims_layout = QVBoxLayout(self.product_dimensions_tab)
            self.dim_product_selector_combo = QComboBox()
            self.dim_product_selector_combo.addItem(self.tr("Sélectionner un produit..."), None)
            prod_dims_layout.addWidget(self.dim_product_selector_combo)
            self.edit_client_product_dimensions_button = QPushButton(self.tr("Modifier Dimensions Produit"))
            self.edit_client_product_dimensions_button.setIcon(QIcon.fromTheme("document-edit", QIcon(":/icons/pencil.svg")))
            self.edit_client_product_dimensions_button.setEnabled(False)
            prod_dims_layout.addWidget(self.edit_client_product_dimensions_button)
            prod_dims_layout.addStretch()
            produits_tab_index = -1
            for i in range(self.tab_widget.count()):
                if self.tab_widget.tabText(i) == self.tr("Notes de Document"):
                    produits_tab_index = i
                    break
            if produits_tab_index != -1:
                self.tab_widget.insertTab(produits_tab_index + 1, self.product_dimensions_tab, self.tr("Dimensions Produit (Client)"))
            else:
                self.tab_widget.addTab(self.product_dimensions_tab, self.tr("Dimensions Produit (Client)"))
        except Exception as e:
            logging.error(f"Error during UI setup of Product Dimensions Tab Structure: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur UI"), self.tr("Erreur initialisation structure onglet Dimensions Produit:\n{0}").format(str(e)))

        try:
            self.load_products_for_dimension_tab()
        except Exception as e:
            logging.error(f"Error during initial load of Product Dimensions Tab (first call): {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Chargement Partiel"), self.tr("Une erreur est survenue lors du chargement initial des dimensions de produit:\n{0}").format(str(e)))

        self.dim_product_selector_combo.currentIndexChanged.connect(self.on_dim_product_selected)
        self.edit_client_product_dimensions_button.clicked.connect(self.on_edit_client_product_dimensions)

        try:
            self.load_products_for_dimension_tab() # Initial population of product selector
        except Exception as e:
            logging.error(f"Error during initial load of Product Dimensions Tab (second call): {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Chargement Partiel"), self.tr("Une erreur est survenue lors du chargement initial des dimensions de produit (2):\n{0}").format(str(e)))

        # Connect signals for the Product Dimensions Tab
        # self.dim_product_selector_combo.currentIndexChanged.connect(self.on_dim_product_selected) # Already connected
        # self.edit_client_product_dimensions_button.clicked.connect(self.on_edit_client_product_dimensions) # Already connected

        # Removed connections for old buttons (client_browse_tech_image_button, save_client_product_dimensions_button)
        try:
            self.populate_doc_table()
        except Exception as e:
            logging.error(f"Error during initial load of Documents tab: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Chargement Partiel"), self.tr("Une erreur est survenue lors du chargement initial des documents:\n{0}").format(str(e)))
        try:
            self.load_contacts()
        except Exception as e:
            logging.error(f"Error during initial load of Contacts tab: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Chargement Partiel"), self.tr("Une erreur est survenue lors du chargement initial des contacts:\n{0}").format(str(e)))
        try:
            self.load_products() # This now also calls load_products_for_dimension_tab which has its own try-except
        except Exception as e:
            logging.error(f"Error during initial load of Products tab: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Chargement Partiel"), self.tr("Une erreur est survenue lors du chargement initial des produits:\n{0}").format(str(e)))

        try:
            self.load_document_notes_filters()
        except Exception as e:
            logging.error(f"Error during initial load of Document Notes Filters: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Chargement Partiel"), self.tr("Une erreur est survenue lors du chargement des filtres de notes de document:\n{0}").format(str(e)))
        try:
            self.load_document_notes_table()
        except Exception as e:
            logging.error(f"Error during initial load of Document Notes tab: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Chargement Partiel"), self.tr("Une erreur est survenue lors du chargement des notes de document:\n{0}").format(str(e)))

        # SAV Tab
        self.sav_tab = QWidget()
        sav_layout = QVBoxLayout(self.sav_tab)

        # Purchase History Section
        sav_layout.addWidget(QLabel("<h3>Historique des Achats</h3>"))
        self.purchase_history_table = QTableWidget()
        self.purchase_history_table.setColumnCount(6) # ID, Produit, Qté, N/S, Date Achat, Actions (or 5 if N/S is directly editable)
        self.purchase_history_table.setHorizontalHeaderLabels([
            self.tr("ID CPP (Hidden)"), self.tr("Produit"), self.tr("Quantité"),
            self.tr("Numéro de Série"), self.tr("Date d'Achat"), self.tr("Actions")
        ])
        self.purchase_history_table.setColumnHidden(0, True) # Hide ID CPP
        self.purchase_history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.purchase_history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # self.purchase_history_table.setEditTriggers(QAbstractItemView.NoEditTriggers) # Will make N/S editable
        self.purchase_history_table.itemChanged.connect(self.handle_purchase_history_item_changed)
        sav_layout.addWidget(self.purchase_history_table)

        self.refresh_purchase_history_btn = QPushButton(self.tr("Rafraîchir l'historique"))
        self.refresh_purchase_history_btn.setIcon(QIcon.fromTheme("view-refresh"))
        self.refresh_purchase_history_btn.clicked.connect(self.load_purchase_history_table)
        sav_layout.addWidget(self.refresh_purchase_history_btn)

        # Placeholder for SAV Tickets section (to be added later)
        sav_layout.addWidget(QLabel("<h3>Tickets SAV (Prochainement)</h3>"))
        sav_layout.addStretch()


        self.tab_widget.addTab(self.sav_tab, self.tr("SAV"))
        self.sav_tab_index = self.tab_widget.indexOf(self.sav_tab)

        # --- Assignments Tab ---
        self.assignments_tab = QWidget()
        assignments_main_layout = QVBoxLayout(self.assignments_tab)
        self.assignments_sub_tabs = QTabWidget()
        assignments_main_layout.addWidget(self.assignments_sub_tabs)
        self.tab_widget.addTab(self.assignments_tab, self.tr("Affectations"))

        # Sub-Tab: Assigned Vendors/Sellers (CompanyPersonnel)
        assigned_vendors_widget = QWidget()
        assigned_vendors_layout = QVBoxLayout(assigned_vendors_widget)
        self.assigned_vendors_table = QTableWidget()
        self.assigned_vendors_table.setColumnCount(4)
        self.assigned_vendors_table.setHorizontalHeaderLabels([self.tr("Nom"), self.tr("Rôle Projet"), self.tr("Email"), self.tr("Téléphone")])
        self.assigned_vendors_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.assigned_vendors_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.assigned_vendors_table.horizontalHeader().setStretchLastSection(True)
        assigned_vendors_layout.addWidget(self.assigned_vendors_table)
        vendor_buttons_layout = QHBoxLayout()
        self.add_assigned_vendor_btn = QPushButton(self.tr("Ajouter Vendeur/Personnel"))
        self.add_assigned_vendor_btn.clicked.connect(self.handle_add_assigned_vendor)
        self.remove_assigned_vendor_btn = QPushButton(self.tr("Retirer Vendeur/Personnel"))
        self.remove_assigned_vendor_btn.clicked.connect(self.handle_remove_assigned_vendor)
        vendor_buttons_layout.addWidget(self.add_assigned_vendor_btn)
        vendor_buttons_layout.addWidget(self.remove_assigned_vendor_btn)
        assigned_vendors_layout.addLayout(vendor_buttons_layout)
        self.assignments_sub_tabs.addTab(assigned_vendors_widget, self.tr("Vendeurs & Personnel"))

        # Sub-Tab: Assigned Technicians (CompanyPersonnel with different role context or from TeamMembers)
        # For now, assuming Technicians are also CompanyPersonnel, filtered by a role like 'Technicien'
        assigned_technicians_widget = QWidget()
        assigned_technicians_layout = QVBoxLayout(assigned_technicians_widget)
        self.assigned_technicians_table = QTableWidget()
        self.assigned_technicians_table.setColumnCount(4)
        self.assigned_technicians_table.setHorizontalHeaderLabels([self.tr("Nom"), self.tr("Rôle Projet"), self.tr("Email"), self.tr("Téléphone")])
        self.assigned_technicians_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.assigned_technicians_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.assigned_technicians_table.horizontalHeader().setStretchLastSection(True)
        assigned_technicians_layout.addWidget(self.assigned_technicians_table)
        technician_buttons_layout = QHBoxLayout()
        self.add_assigned_technician_btn = QPushButton(self.tr("Ajouter Technicien"))
        self.add_assigned_technician_btn.clicked.connect(self.handle_add_assigned_technician)
        self.remove_assigned_technician_btn = QPushButton(self.tr("Retirer Technicien"))
        self.remove_assigned_technician_btn.clicked.connect(self.handle_remove_assigned_technician)
        technician_buttons_layout.addWidget(self.add_assigned_technician_btn)
        technician_buttons_layout.addWidget(self.remove_assigned_technician_btn)
        assigned_technicians_layout.addLayout(technician_buttons_layout)
        self.assignments_sub_tabs.addTab(assigned_technicians_widget, self.tr("Techniciens"))

        # Sub-Tab: Assigned Transporters
        assigned_transporters_widget = QWidget()
        assigned_transporters_layout = QVBoxLayout(assigned_transporters_widget)
        self.assigned_transporters_table = QTableWidget()
        self.assigned_transporters_table.setColumnCount(6) # Increased column count
        self.assigned_transporters_table.setHorizontalHeaderLabels([self.tr("Nom Transporteur"), self.tr("Contact"), self.tr("Téléphone"), self.tr("Détails Transport"), self.tr("Coût Estimé"), self.tr("Actions")])
        self.assigned_transporters_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.assigned_transporters_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.assigned_transporters_table.horizontalHeader().setStretchLastSection(True)
        assigned_transporters_layout.addWidget(self.assigned_transporters_table)
        transporter_buttons_layout = QHBoxLayout()
        self.add_assigned_transporter_btn = QPushButton(self.tr("Ajouter Transporteur"))
        self.add_assigned_transporter_btn.clicked.connect(self.handle_add_assigned_transporter)
        self.remove_assigned_transporter_btn = QPushButton(self.tr("Retirer Transporteur"))
        self.remove_assigned_transporter_btn.clicked.connect(self.handle_remove_assigned_transporter)
        transporter_buttons_layout.addWidget(self.add_assigned_transporter_btn)
        transporter_buttons_layout.addWidget(self.remove_assigned_transporter_btn)
        assigned_transporters_layout.addLayout(transporter_buttons_layout)
        self.assignments_sub_tabs.addTab(assigned_transporters_widget, self.tr("Transporteurs"))

        # Sub-Tab: Assigned Freight Forwarders
        assigned_forwarders_widget = QWidget()
        assigned_forwarders_layout = QVBoxLayout(assigned_forwarders_widget)
        self.assigned_forwarders_table = QTableWidget()
        self.assigned_forwarders_table.setColumnCount(5)
        self.assigned_forwarders_table.setHorizontalHeaderLabels([self.tr("Nom Transitaire"), self.tr("Contact"), self.tr("Téléphone"), self.tr("Description Tâche"), self.tr("Coût Estimé")])
        self.assigned_forwarders_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.assigned_forwarders_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.assigned_forwarders_table.horizontalHeader().setStretchLastSection(True)
        assigned_forwarders_layout.addWidget(self.assigned_forwarders_table)
        forwarder_buttons_layout = QHBoxLayout()
        self.add_assigned_forwarder_btn = QPushButton(self.tr("Ajouter Transitaire"))
        self.add_assigned_forwarder_btn.clicked.connect(self.handle_add_assigned_forwarder)
        self.remove_assigned_forwarder_btn = QPushButton(self.tr("Retirer Transitaire"))
        self.remove_assigned_forwarder_btn.clicked.connect(self.handle_remove_assigned_forwarder)
        forwarder_buttons_layout.addWidget(self.add_assigned_forwarder_btn)
        forwarder_buttons_layout.addWidget(self.remove_assigned_forwarder_btn)
        assigned_forwarders_layout.addLayout(forwarder_buttons_layout)
        self.assignments_sub_tabs.addTab(assigned_forwarders_widget, self.tr("Transitaires"))
        # --- End Assignments Tab ---

        # Call to load SAV tickets table initially if tab is visible
        try:
            self.update_sav_tab_visibility() # This calls load_purchase_history_table and load_sav_tickets_table
        except Exception as e:
            logging.error(f"Error during initial visibility update/load of SAV tab: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Chargement Partiel"), self.tr("Une erreur est survenue lors de la mise à jour/chargement initial de l'onglet SAV:\n{0}").format(str(e)))

        # Initial load for assignment tabs
        try:
            self.load_assigned_vendors_personnel()
        except Exception as e:
            logging.error(f"Error during initial load of Assigned Vendors/Personnel: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Chargement Partiel"), self.tr("Une erreur est survenue lors du chargement des vendeurs/personnel assignés:\n{0}").format(str(e)))
        try:
            self.load_assigned_technicians()
        except Exception as e:
            logging.error(f"Error during initial load of Assigned Technicians: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Chargement Partiel"), self.tr("Une erreur est survenue lors du chargement des techniciens assignés:\n{0}").format(str(e)))
        try:
            self.load_assigned_transporters()
        except Exception as e:
            logging.error(f"Error during initial load of Assigned Transporters: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Chargement Partiel"), self.tr("Une erreur est survenue lors du chargement des transporteurs assignés:\n{0}").format(str(e)))
        try:
            self.load_assigned_freight_forwarders()
        except Exception as e:
            logging.error(f"Error during initial load of Assigned Freight Forwarders: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Chargement Partiel"), self.tr("Une erreur est survenue lors du chargement des transitaires assignés:\n{0}").format(str(e)))

        # Connect selection changed signals for assignment tables
        self.assigned_vendors_table.itemSelectionChanged.connect(self.update_assigned_vendors_buttons_state)
        self.assigned_technicians_table.itemSelectionChanged.connect(self.update_assigned_technicians_buttons_state)
        self.assigned_transporters_table.itemSelectionChanged.connect(self.update_assigned_transporters_buttons_state)
        self.assigned_forwarders_table.itemSelectionChanged.connect(self.update_assigned_forwarders_buttons_state)

        # --- Billing Tab ---
        self.billing_tab = QWidget()
        self.billing_tab_layout = QVBoxLayout(self.billing_tab)

        self.generate_invoice_button = QPushButton(QIcon(":/icons/file-plus.svg"), self.tr("Generate Final Invoice"))
        self.generate_invoice_button.setToolTip(self.tr("Open dialog to prepare and generate a final invoice for this client."))
        self.generate_invoice_button.clicked.connect(self.handle_generate_final_invoice)
        self.billing_tab_layout.addWidget(self.generate_invoice_button)
        self.billing_tab_layout.addStretch()

        self.tab_widget.addTab(self.billing_tab, QIcon(":/icons/credit-card.svg"), self.tr("Billing"))
        # Connect new accordion handlers
        self.client_info_group_box.toggled.connect(self._handle_client_info_section_toggled)
        self.notes_group_box.toggled.connect(self._handle_notes_section_toggled)
        self.tabs_group_box.toggled.connect(self._handle_tabs_section_toggled)

    def handle_create_new_version_clicked(self, old_document_id, source_template_id):
        """
        Handles the click of the 'Create New Version' button for a document.
        Opens CreateDocumentDialog with parameters to indicate versioning.
        """
        if not self.client_info or not self.client_info.get('client_id'):
            QMessageBox.warning(self, self.tr("Erreur Client"), self.tr("Informations client non disponibles."))
            return

        if not old_document_id or not source_template_id:
            QMessageBox.warning(self, self.tr("Données Manquantes"), self.tr("ID du document original ou ID du modèle source manquant."))
            return

        logging.info(f"Creating new version for old_doc_id: {old_document_id}, using source_template_id: {source_template_id}")

        # Ensure CreateDocumentDialog is available
        if not hasattr(self, 'CreateDocumentDialog') or self.CreateDocumentDialog is None:
            logging.error("CreateDocumentDialog is not available in ClientMainWidget for versioning.")
            QMessageBox.critical(self, self.tr("Erreur Composant"), self.tr("Le composant de création de document n'est pas chargé."))
            return

        dialog = self.CreateDocumentDialog(
            client_info=self.client_info,
            config=self.config,
            current_user_id=self.current_user_id, # Pass current_user_id
            parent=self,
            template_data={'template_id': source_template_id}, # To pre-select the original template
            old_document_id_to_version=old_document_id      # Pass the ID of the document to version
        )

        if dialog.exec_() == QDialog.Accepted:
            self.populate_doc_table()  # Refresh documents tab to show the new version
            self.notification_manager.show(
                self.tr("Nouvelle Version Créée"),
                self.tr("Une nouvelle version du document a été créée avec succès."),
                type='SUCCESS'
            )

    def delete_client_document_entry(self, document_id, file_path):
        """
        Deletes a client document entry from the database and the corresponding file from disk.
        """
        if not document_id:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("ID du document manquant."))
            return

        reply = QMessageBox.question(self, self.tr("Confirmer Suppression"),
                                     self.tr("Êtes-vous sûr de vouloir supprimer définitivement ce document ({0})?\nLe fichier '{1}' sera également supprimé du disque.").format(document_id, os.path.basename(file_path or "N/A")),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                # Attempt to delete from DB
                # Assuming db_manager.delete_client_document is now implemented correctly
                db_deleted = db_manager.delete_client_document(document_id)

                if db_deleted:
                    logging.info(f"Document ID {document_id} deleted from database.")
                    # Attempt to delete file from disk
                    if file_path and os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            logging.info(f"File {file_path} deleted from disk.")
                            self.notification_manager.show(self.tr("Succès"), self.tr("Document et fichier supprimés avec succès."), type='SUCCESS')
                        except OSError as e_file:
                            logging.error(f"Error deleting file {file_path}: {e_file}", exc_info=True)
                            self.notification_manager.show(self.tr("Erreur Fichier"), self.tr("Document supprimé de la base de données, mais échec de la suppression du fichier:\n{0}").format(str(e_file)), type='ERROR')
                    else:
                        logging.warning(f"File path not provided or file does not exist for document ID {document_id}: {file_path}. DB entry deleted.")
                        self.notification_manager.show(self.tr("Succès (Partiel)"), self.tr("Entrée de document supprimée de la base de données. Fichier non trouvé ou chemin non spécifié."), type='WARNING')
                else:
                    self.notification_manager.show(self.tr("Erreur DB"), self.tr("Impossible de supprimer l'entrée du document de la base de données (ID: {0}). Vérifiez les logs.").format(document_id), type='ERROR')

            except Exception as e:
                logging.error(f"Error in delete_client_document_entry for doc ID {document_id}: {e}", exc_info=True)
                self.notification_manager.show(self.tr("Erreur Suppression"), self.tr("Une erreur inattendue est survenue:\n{0}").format(str(e)), type='CRITICAL')
            finally:
                self.populate_doc_table() # Refresh the document list

    def _handle_edit_pdf_action(self, file_path, document_id):
        if file_path and os.path.exists(file_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
        try:
            self._setup_main_tabs_section(layout) #FIXED
            self.notes_edit.textChanged.disconnect(self.save_client_notes)
        except TypeError:
            pass # Signal was not connected or already disconnected
        self.notes_edit.installEventFilter(self)


        # --- Collapsible Notes Section ---
        self.notes_group_box = QGroupBox(self.tr("Notes"))
        self.notes_group_box.setCheckable(True)
        notes_group_layout = QVBoxLayout(self.notes_group_box)

        # self.notes_edit is already initialized earlier
        # Move self.notes_edit into this new group box
        # notes_group_layout.addWidget(self.notes_edit) # Directly adding notes_edit

        self.notes_group_box.setChecked(False) # Expanded by default
        self.notes_container_widget = QWidget() # Create a container for the notes_edit
        notes_container_layout = QVBoxLayout(self.notes_container_widget)
        notes_container_layout.setContentsMargins(0, 5, 0, 0)
        notes_container_layout.addWidget(self.notes_edit) # Add notes_edit to the container
        notes_group_layout.addWidget(self.notes_container_widget) # Add container to group_layout
        # self.notes_group_box.toggled.connect(self.notes_container_widget.setVisible)

        # Add the new notes group box to the main layout
        layout.addWidget(self.notes_group_box)
        # --- End Collapsible Notes Section ---

        # --- Collapsible Tabs Section ---
        self.tabs_group_box = QGroupBox(self.tr("Autres Informations")) # Or "Details Supplementaires" / "Tabs"
        self.tabs_group_box.setCheckable(True)
        tabs_group_layout = QVBoxLayout(self.tabs_group_box)

        self.tab_widget = QTabWidget()
        # Move self.tab_widget into this new group box
        tabs_group_layout.addWidget(self.tab_widget)

        self.tabs_group_box.setChecked(False) # Collapsed by default
        # Add the new tabs_group_box to the main layout instead of tab_widget directly
        # layout.addWidget(self.tab_widget) # This line will be replaced by:
        layout.addWidget(self.tabs_group_box)
        # --- End Collapsible Tabs Section ---

        docs_tab = QWidget(); docs_layout = QVBoxLayout(docs_tab)

        # Filter layout for documents tab
        self.doc_filter_layout_widget = QWidget() # Container for the filter layout
        doc_filter_layout = QHBoxLayout(self.doc_filter_layout_widget)
        doc_filter_layout.setContentsMargins(0,0,0,0) # Keep tight margins for the filter bar itself

        doc_filter_label = QLabel(self.tr("Filtrer par Commande:"))
        doc_filter_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed) # Prevent label from expanding
        doc_filter_layout.addWidget(doc_filter_label)

        self.doc_order_filter_combo = QComboBox()
        self.doc_order_filter_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.doc_order_filter_combo.currentIndexChanged.connect(self.populate_doc_table)
        doc_filter_layout.addWidget(self.doc_order_filter_combo)
        doc_filter_layout.addSpacing(10)

        # Language Filter
        doc_lang_filter_label = QLabel(self.tr("Filtrer par Langue:"))
        doc_lang_filter_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        doc_filter_layout.addWidget(doc_lang_filter_label)

        self.doc_language_filter_combo = QComboBox()
        self.doc_language_filter_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.doc_language_filter_combo.addItem(self.tr("Toutes"), "ALL")
        for lang_code in SUPPORTED_LANGUAGES:
            self.doc_language_filter_combo.addItem(lang_code, lang_code)
        self.doc_language_filter_combo.currentIndexChanged.connect(self.populate_doc_table)
        doc_filter_layout.addWidget(self.doc_language_filter_combo)
        doc_filter_layout.addSpacing(10)

        # Type Filter
        doc_type_filter_label = QLabel(self.tr("Filtrer par Type:"))
        doc_type_filter_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        doc_filter_layout.addWidget(doc_type_filter_label)

        self.doc_type_filter_combo = QComboBox()
        self.doc_type_filter_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.doc_type_filter_combo.addItem(self.tr("Tous"), "ALL")
        self.doc_type_filter_combo.addItem("HTML", "HTML")
        self.doc_type_filter_combo.addItem("PDF", "PDF")
        self.doc_type_filter_combo.addItem("XLSX", "XLSX")
        self.doc_type_filter_combo.addItem("DOCX", "DOCX")
        self.doc_type_filter_combo.addItem(self.tr("Autre"), "OTHER")
        self.doc_type_filter_combo.currentIndexChanged.connect(self.populate_doc_table)
        doc_filter_layout.addWidget(self.doc_type_filter_combo)

        docs_layout.addWidget(self.doc_filter_layout_widget)
        self.doc_filter_layout_widget.setVisible(True) # Make filter bar always visible

        # Create and add the empty state label for documents
        self.documents_empty_label = QLabel(self.tr("Aucun document trouvé pour ce client.\nUtilisez les boutons ci-dessous pour ajouter ou générer des documents."))
        self.documents_empty_label.setAlignment(Qt.AlignCenter)
        font_docs_empty = self.documents_empty_label.font() # Use a different variable name for font
        font_docs_empty.setPointSize(10) # Adjust size as needed
        self.documents_empty_label.setFont(font_docs_empty)
        docs_layout.addWidget(self.documents_empty_label) # Add before the table

        self.doc_table = QTableWidget()
        self.doc_table.setColumnCount(5) # Name, Type, Language, Date, Actions
        self.doc_table.setHorizontalHeaderLabels([self.tr("Nom"), self.tr("Type"), self.tr("Langue"), self.tr("Date"), self.tr("Actions")])
        self.doc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.doc_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.doc_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        docs_layout.addWidget(self.doc_table)
        doc_btn_layout = QHBoxLayout()
        self.add_doc_btn = QPushButton(self.tr("Importer Document"))
        self.add_doc_btn.setIcon(QIcon(":/icons/file-plus.svg"))
        self.add_doc_btn.setToolTip(self.tr("Importer un fichier document existant pour ce client"))
        self.add_doc_btn.clicked.connect(self.add_document) # Connect the signal
        doc_btn_layout.addWidget(self.add_doc_btn)

        self.refresh_docs_btn = QPushButton(self.tr("Actualiser"))
        self.refresh_docs_btn.setIcon(QIcon.fromTheme("view-refresh"))
        self.refresh_docs_btn.clicked.connect(self.populate_doc_table)
        doc_btn_layout.addWidget(self.refresh_docs_btn)

        self.add_template_btn = QPushButton(self.tr("Générer via Modèle"))
        self.add_template_btn.setIcon(QIcon.fromTheme("document-new", QIcon(":/icons/file-plus.svg"))) # Reverted
        self.add_template_btn.setToolTip(self.tr("Générer un nouveau document pour ce client à partir d'un modèle"))
        self.add_template_btn.clicked.connect(self.open_create_docs_dialog)
        doc_btn_layout.addWidget(self.add_template_btn)
        docs_layout.addLayout(doc_btn_layout)
        self.tab_widget.addTab(docs_tab, self.tr("Documents"))

        contacts_tab = QWidget()
        contacts_layout = QVBoxLayout(contacts_tab)
        self.contacts_table = QTableWidget()
        self.contacts_table.setColumnCount(5) # Name, Email, Phone, Position, Primary
        self.contacts_table.setHorizontalHeaderLabels([
            self.tr("Nom"), self.tr("Email"), self.tr("Téléphone"),
            self.tr("Position"), self.tr("Principal")
        ])
        self.contacts_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.contacts_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.contacts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.contacts_table.setAlternatingRowColors(True)
        self.contacts_table.cellDoubleClicked.connect(self.edit_contact) # row, column are passed

        self.contacts_empty_label = QLabel(self.tr("Aucun contact ajouté pour ce client.\nCliquez sur '➕ Ajouter' pour commencer."))
        self.contacts_empty_label.setAlignment(Qt.AlignCenter)
        font = self.contacts_empty_label.font()
        font.setPointSize(10)
        self.contacts_empty_label.setFont(font)
        contacts_layout.addWidget(self.contacts_empty_label)

        contacts_layout.addWidget(self.contacts_table)

        contacts_pagination_layout = QHBoxLayout()
        self.prev_contact_button = QPushButton("<< Précédent")
        self.prev_contact_button.setObjectName("paginationButton")
        self.prev_contact_button.clicked.connect(self.prev_contact_page)
        self.contact_page_info_label = QLabel("Page 1 / 1")
        self.contact_page_info_label.setObjectName("paginationLabel")
        self.next_contact_button = QPushButton("Suivant >>")
        self.next_contact_button.setObjectName("paginationButton")
        self.next_contact_button.clicked.connect(self.next_contact_page)

        contacts_pagination_layout.addStretch()
        contacts_pagination_layout.addWidget(self.prev_contact_button)
        contacts_pagination_layout.addWidget(self.contact_page_info_label)
        contacts_pagination_layout.addWidget(self.next_contact_button)
        contacts_pagination_layout.addStretch()
        contacts_layout.addLayout(contacts_pagination_layout)

        contacts_btn_layout = QHBoxLayout()
        self.add_contact_btn = QPushButton(self.tr("Ajouter")); self.add_contact_btn.setIcon(QIcon(":/icons/user-plus.svg")); self.add_contact_btn.setToolTip(self.tr("Ajouter un nouveau contact pour ce client")); self.add_contact_btn.clicked.connect(self.add_contact); contacts_btn_layout.addWidget(self.add_contact_btn)
        self.edit_contact_btn = QPushButton(self.tr("Modifier")); self.edit_contact_btn.setIcon(QIcon(":/icons/pencil.svg")); self.edit_contact_btn.setToolTip(self.tr("Modifier le contact sélectionné")); self.edit_contact_btn.clicked.connect(self.edit_contact); contacts_btn_layout.addWidget(self.edit_contact_btn)
        self.remove_contact_btn = QPushButton(self.tr("Supprimer")); self.remove_contact_btn.setIcon(QIcon(":/icons/trash.svg")); self.remove_contact_btn.setToolTip(self.tr("Supprimer le lien vers le contact sélectionné pour ce client")); self.remove_contact_btn.setObjectName("dangerButton"); self.remove_contact_btn.clicked.connect(self.remove_contact); contacts_btn_layout.addWidget(self.remove_contact_btn)
        contacts_layout.addLayout(contacts_btn_layout)
        self.tab_widget.addTab(contacts_tab, self.tr("Contacts"))

        products_tab = QWidget()
        products_layout = QVBoxLayout(products_tab)

        product_filters_layout = QHBoxLayout()
        product_filters_layout.addWidget(QLabel(self.tr("Filtrer par langue:")))
        self.product_lang_filter_combo = QComboBox()
        self.product_lang_filter_combo.addItem(self.tr("All Languages"), None)
        self.product_lang_filter_combo.addItem(self.tr("English (en)"), "en")
        self.product_lang_filter_combo.addItem(self.tr("French (fr)"), "fr")
        self.product_lang_filter_combo.addItem(self.tr("Arabic (ar)"), "ar")
        self.product_lang_filter_combo.addItem(self.tr("Turkish (tr)"), "tr")
        self.product_lang_filter_combo.addItem(self.tr("Portuguese (pt)"), "pt")
        self.product_lang_filter_combo.currentTextChanged.connect(self.load_products)
        product_filters_layout.addWidget(self.product_lang_filter_combo)
        product_filters_layout.addStretch()
        products_layout.addLayout(product_filters_layout)

        self.products_empty_label = QLabel(self.tr("Aucun produit ajouté pour ce client.\nCliquez sur '➕ Ajouter' pour commencer."))
        self.products_empty_label.setAlignment(Qt.AlignCenter)
        font_products_empty = self.products_empty_label.font()
        font_products_empty.setPointSize(10)
        self.products_empty_label.setFont(font_products_empty)
        products_layout.addWidget(self.products_empty_label)

        self.products_table = QTableWidget()
        self.products_table.setColumnCount(8)
        self.products_table.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Nom Produit"), self.tr("Description"),
            self.tr("Poids"), self.tr("Dimensions"),
            self.tr("Qté"), self.tr("Prix Unitaire"), self.tr("Prix Total")
        ])
        self.products_table.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.products_table.itemChanged.connect(self.handle_product_item_changed)
        self.products_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.products_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.products_table.hideColumn(0)
        products_layout.addWidget(self.products_table)

        products_btn_layout = QHBoxLayout()
        self.add_product_btn = QPushButton(self.tr("Ajouter")); self.add_product_btn.setIcon(QIcon(":/icons/plus-circle.svg")); self.add_product_btn.setToolTip(self.tr("Ajouter un produit pour ce client/projet")); self.add_product_btn.clicked.connect(self.add_product); products_btn_layout.addWidget(self.add_product_btn)
        self.edit_product_btn = QPushButton(self.tr("Modifier")); self.edit_product_btn.setIcon(QIcon(":/icons/pencil.svg")); self.edit_product_btn.setToolTip(self.tr("Modifier le produit sélectionné")); self.edit_product_btn.clicked.connect(self.edit_product); products_btn_layout.addWidget(self.edit_product_btn)
        self.remove_product_btn = QPushButton(self.tr("Supprimer")); self.remove_product_btn.setIcon(QIcon(":/icons/trash.svg")); self.remove_product_btn.setToolTip(self.tr("Supprimer le produit sélectionné de ce client/projet")); self.remove_product_btn.setObjectName("dangerButton"); self.remove_product_btn.clicked.connect(self.remove_product); products_btn_layout.addWidget(self.remove_product_btn)
        products_layout.addLayout(products_btn_layout)
        self.tab_widget.addTab(products_tab, self.tr("Produits"))

        # layout.addWidget(self.tab_widget) # This was moved into tabs_group_box

        self.document_notes_tab = QWidget()
        doc_notes_layout = QVBoxLayout(self.document_notes_tab)

        doc_notes_filters_layout = QHBoxLayout()
        doc_notes_filters_layout.addWidget(QLabel(self.tr("Type de Document:")))
        self.doc_notes_type_filter_combo = QComboBox()
        doc_notes_filters_layout.addWidget(self.doc_notes_type_filter_combo)

        doc_notes_filters_layout.addWidget(QLabel(self.tr("Langue:")))
        self.doc_notes_lang_filter_combo = QComboBox()
        doc_notes_filters_layout.addWidget(self.doc_notes_lang_filter_combo)
        doc_notes_filters_layout.addStretch()
        doc_notes_layout.addLayout(doc_notes_filters_layout)

        self.document_notes_table = QTableWidget()
        self.document_notes_table.setColumnCount(5)
        self.document_notes_table.setHorizontalHeaderLabels([
            self.tr("Type Document"), self.tr("Langue"),
            self.tr("Aperçu Note"), self.tr("Actif"), self.tr("Actions")
        ])
        self.document_notes_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.document_notes_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.document_notes_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        doc_notes_layout.addWidget(self.document_notes_table)

        doc_notes_buttons_layout = QHBoxLayout()
        self.add_doc_note_button = QPushButton(self.tr("Ajouter Note de Document"))
        self.add_doc_note_button.setIcon(QIcon.fromTheme("document-new"))

        doc_notes_buttons_layout.addWidget(self.add_doc_note_button)

        self.refresh_doc_notes_button = QPushButton(self.tr("Actualiser Liste"))
        self.refresh_doc_notes_button.setIcon(QIcon.fromTheme("view-refresh"))
        doc_notes_buttons_layout.addWidget(self.refresh_doc_notes_button)
        doc_notes_buttons_layout.addStretch()
        doc_notes_layout.addLayout(doc_notes_buttons_layout)

        self.document_notes_tab.setLayout(doc_notes_layout)
        self.tab_widget.addTab(self.document_notes_tab, self.tr("Notes de Document"))

        self.doc_notes_type_filter_combo.currentIndexChanged.connect(self.load_document_notes_table)
        self.doc_notes_lang_filter_combo.currentIndexChanged.connect(self.load_document_notes_table)
        self.add_doc_note_button.clicked.connect(self.on_add_document_note)
        self.refresh_doc_notes_button.clicked.connect(self.load_document_notes_table)

        self.product_dimensions_tab = QWidget()
        prod_dims_layout = QVBoxLayout(self.product_dimensions_tab)

        self.dim_product_selector_combo = QComboBox()
        self.dim_product_selector_combo.addItem(self.tr("Sélectionner un produit..."), None)
        prod_dims_layout.addWidget(self.dim_product_selector_combo)

        self.edit_client_product_dimensions_button = QPushButton(self.tr("Modifier Dimensions Produit"))
        self.edit_client_product_dimensions_button.setIcon(QIcon.fromTheme("document-edit", QIcon(":/icons/pencil.svg")))
        self.edit_client_product_dimensions_button.setEnabled(False)
        prod_dims_layout.addWidget(self.edit_client_product_dimensions_button)

        prod_dims_layout.addStretch()


        produits_tab_index = -1
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == self.tr("Notes de Document"):
                produits_tab_index = i
                break

        if produits_tab_index != -1:
            self.tab_widget.insertTab(produits_tab_index + 1, self.product_dimensions_tab, self.tr("Dimensions Produit (Client)"))
        else:
            self.tab_widget.addTab(self.product_dimensions_tab, self.tr("Dimensions Produit (Client)"))

        try:
            self.load_products_for_dimension_tab()
        except Exception as e:
            logging.error(f"Error during initial load of Product Dimensions Tab (first call): {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Chargement Partiel"), self.tr("Une erreur est survenue lors du chargement initial des dimensions de produit:\n{0}").format(str(e)))

        self.dim_product_selector_combo.currentIndexChanged.connect(self.on_dim_product_selected)
        self.edit_client_product_dimensions_button.clicked.connect(self.on_edit_client_product_dimensions)

        try:
            self.load_products_for_dimension_tab() # Initial population of product selector
        except Exception as e:
            logging.error(f"Error during initial load of Product Dimensions Tab (second call): {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Chargement Partiel"), self.tr("Une erreur est survenue lors du chargement initial des dimensions de produit (2):\n{0}").format(str(e)))

        # Connect signals for the Product Dimensions Tab
        # self.dim_product_selector_combo.currentIndexChanged.connect(self.on_dim_product_selected) # Already connected
        # self.edit_client_product_dimensions_button.clicked.connect(self.on_edit_client_product_dimensions) # Already connected

        # Removed connections for old buttons (client_browse_tech_image_button, save_client_product_dimensions_button)
        try:
            self.populate_doc_table()
        except Exception as e:
            logging.error(f"Error during initial load of Documents tab: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Chargement Partiel"), self.tr("Une erreur est survenue lors du chargement initial des documents:\n{0}").format(str(e)))
        try:
            self.load_contacts()
        except Exception as e:
            logging.error(f"Error during initial load of Contacts tab: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Chargement Partiel"), self.tr("Une erreur est survenue lors du chargement initial des contacts:\n{0}").format(str(e)))
        try:
            self.load_products() # This now also calls load_products_for_dimension_tab which has its own try-except
        except Exception as e:
            logging.error(f"Error during initial load of Products tab: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Chargement Partiel"), self.tr("Une erreur est survenue lors du chargement initial des produits:\n{0}").format(str(e)))

        try:
            self.load_document_notes_filters()
        except Exception as e:
            logging.error(f"Error during initial load of Document Notes Filters: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Chargement Partiel"), self.tr("Une erreur est survenue lors du chargement des filtres de notes de document:\n{0}").format(str(e)))
        try:
            self.load_document_notes_table()
        except Exception as e:
            logging.error(f"Error during initial load of Document Notes tab: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Chargement Partiel"), self.tr("Une erreur est survenue lors du chargement des notes de document:\n{0}").format(str(e)))

        # SAV Tab
        self.sav_tab = QWidget()
        sav_layout = QVBoxLayout(self.sav_tab)

        # Purchase History Section
        sav_layout.addWidget(QLabel("<h3>Historique des Achats</h3>"))
        self.purchase_history_table = QTableWidget()
        self.purchase_history_table.setColumnCount(6) # ID, Produit, Qté, N/S, Date Achat, Actions (or 5 if N/S is directly editable)
        self.purchase_history_table.setHorizontalHeaderLabels([
            self.tr("ID CPP (Hidden)"), self.tr("Produit"), self.tr("Quantité"),
            self.tr("Numéro de Série"), self.tr("Date d'Achat"), self.tr("Actions")
        ])
        self.purchase_history_table.setColumnHidden(0, True) # Hide ID CPP
        self.purchase_history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.purchase_history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # self.purchase_history_table.setEditTriggers(QAbstractItemView.NoEditTriggers) # Will make N/S editable
        self.purchase_history_table.itemChanged.connect(self.handle_purchase_history_item_changed)
        sav_layout.addWidget(self.purchase_history_table)

        self.refresh_purchase_history_btn = QPushButton(self.tr("Rafraîchir l'historique"))
        self.refresh_purchase_history_btn.setIcon(QIcon.fromTheme("view-refresh"))
        self.refresh_purchase_history_btn.clicked.connect(self.load_purchase_history_table)
        sav_layout.addWidget(self.refresh_purchase_history_btn)

        # Placeholder for SAV Tickets section (to be added later)
        sav_layout.addWidget(QLabel("<h3>Tickets SAV (Prochainement)</h3>"))
        sav_layout.addStretch()


        self.tab_widget.addTab(self.sav_tab, self.tr("SAV"))
        self.sav_tab_index = self.tab_widget.indexOf(self.sav_tab)

        # --- Assignments Tab ---
        self.assignments_tab = QWidget()
        assignments_main_layout = QVBoxLayout(self.assignments_tab)
        self.assignments_sub_tabs = QTabWidget()
        assignments_main_layout.addWidget(self.assignments_sub_tabs)
        self.tab_widget.addTab(self.assignments_tab, self.tr("Affectations"))

        # Sub-Tab: Assigned Vendors/Sellers (CompanyPersonnel)
        assigned_vendors_widget = QWidget()
        assigned_vendors_layout = QVBoxLayout(assigned_vendors_widget)
        self.assigned_vendors_table = QTableWidget()
        self.assigned_vendors_table.setColumnCount(4)
        self.assigned_vendors_table.setHorizontalHeaderLabels([self.tr("Nom"), self.tr("Rôle Projet"), self.tr("Email"), self.tr("Téléphone")])
        self.assigned_vendors_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.assigned_vendors_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.assigned_vendors_table.horizontalHeader().setStretchLastSection(True)
        assigned_vendors_layout.addWidget(self.assigned_vendors_table)
        vendor_buttons_layout = QHBoxLayout()
        self.add_assigned_vendor_btn = QPushButton(self.tr("Ajouter Vendeur/Personnel"))
        self.add_assigned_vendor_btn.clicked.connect(self.handle_add_assigned_vendor)
        self.remove_assigned_vendor_btn = QPushButton(self.tr("Retirer Vendeur/Personnel"))
        self.remove_assigned_vendor_btn.clicked.connect(self.handle_remove_assigned_vendor)
        vendor_buttons_layout.addWidget(self.add_assigned_vendor_btn)
        vendor_buttons_layout.addWidget(self.remove_assigned_vendor_btn)
        assigned_vendors_layout.addLayout(vendor_buttons_layout)
        self.assignments_sub_tabs.addTab(assigned_vendors_widget, self.tr("Vendeurs & Personnel"))

        # Sub-Tab: Assigned Technicians (CompanyPersonnel with different role context or from TeamMembers)
        # For now, assuming Technicians are also CompanyPersonnel, filtered by a role like 'Technicien'
        assigned_technicians_widget = QWidget()
        assigned_technicians_layout = QVBoxLayout(assigned_technicians_widget)
        self.assigned_technicians_table = QTableWidget()
        self.assigned_technicians_table.setColumnCount(4)
        self.assigned_technicians_table.setHorizontalHeaderLabels([self.tr("Nom"), self.tr("Rôle Projet"), self.tr("Email"), self.tr("Téléphone")])
        self.assigned_technicians_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.assigned_technicians_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.assigned_technicians_table.horizontalHeader().setStretchLastSection(True)
        assigned_technicians_layout.addWidget(self.assigned_technicians_table)
        technician_buttons_layout = QHBoxLayout()
        self.add_assigned_technician_btn = QPushButton(self.tr("Ajouter Technicien"))
        self.add_assigned_technician_btn.clicked.connect(self.handle_add_assigned_technician)
        self.remove_assigned_technician_btn = QPushButton(self.tr("Retirer Technicien"))
        self.remove_assigned_technician_btn.clicked.connect(self.handle_remove_assigned_technician)
        technician_buttons_layout.addWidget(self.add_assigned_technician_btn)
        technician_buttons_layout.addWidget(self.remove_assigned_technician_btn)
        assigned_technicians_layout.addLayout(technician_buttons_layout)
        self.assignments_sub_tabs.addTab(assigned_technicians_widget, self.tr("Techniciens"))

        # Sub-Tab: Assigned Transporters
        assigned_transporters_widget = QWidget()
        assigned_transporters_layout = QVBoxLayout(assigned_transporters_widget)
        self.assigned_transporters_table = QTableWidget()
        self.assigned_transporters_table.setColumnCount(6) # Increased column count
        self.assigned_transporters_table.setHorizontalHeaderLabels([self.tr("Nom Transporteur"), self.tr("Contact"), self.tr("Téléphone"), self.tr("Détails Transport"), self.tr("Coût Estimé"), self.tr("Actions")])
        self.assigned_transporters_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.assigned_transporters_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.assigned_transporters_table.horizontalHeader().setStretchLastSection(True)
        assigned_transporters_layout.addWidget(self.assigned_transporters_table)
        transporter_buttons_layout = QHBoxLayout()
        self.add_assigned_transporter_btn = QPushButton(self.tr("Ajouter Transporteur"))
        self.add_assigned_transporter_btn.clicked.connect(self.handle_add_assigned_transporter)
        self.remove_assigned_transporter_btn = QPushButton(self.tr("Retirer Transporteur"))
        self.remove_assigned_transporter_btn.clicked.connect(self.handle_remove_assigned_transporter)
        transporter_buttons_layout.addWidget(self.add_assigned_transporter_btn)
        transporter_buttons_layout.addWidget(self.remove_assigned_transporter_btn)
        assigned_transporters_layout.addLayout(transporter_buttons_layout)
        self.assignments_sub_tabs.addTab(assigned_transporters_widget, self.tr("Transporteurs"))

        # Sub-Tab: Assigned Freight Forwarders
        assigned_forwarders_widget = QWidget()
        assigned_forwarders_layout = QVBoxLayout(assigned_forwarders_widget)
        self.assigned_forwarders_table = QTableWidget()
        self.assigned_forwarders_table.setColumnCount(5)
        self.assigned_forwarders_table.setHorizontalHeaderLabels([self.tr("Nom Transitaire"), self.tr("Contact"), self.tr("Téléphone"), self.tr("Description Tâche"), self.tr("Coût Estimé")])
        self.assigned_forwarders_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.assigned_forwarders_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.assigned_forwarders_table.horizontalHeader().setStretchLastSection(True)
        assigned_forwarders_layout.addWidget(self.assigned_forwarders_table)
        forwarder_buttons_layout = QHBoxLayout()
        self.add_assigned_forwarder_btn = QPushButton(self.tr("Ajouter Transitaire"))
        self.add_assigned_forwarder_btn.clicked.connect(self.handle_add_assigned_forwarder)
        self.remove_assigned_forwarder_btn = QPushButton(self.tr("Retirer Transitaire"))
        self.remove_assigned_forwarder_btn.clicked.connect(self.handle_remove_assigned_forwarder)
        forwarder_buttons_layout.addWidget(self.add_assigned_forwarder_btn)
        forwarder_buttons_layout.addWidget(self.remove_assigned_forwarder_btn)
        assigned_forwarders_layout.addLayout(forwarder_buttons_layout)
        self.assignments_sub_tabs.addTab(assigned_forwarders_widget, self.tr("Transitaires"))
        # --- End Assignments Tab ---

        # Call to load SAV tickets table initially if tab is visible
        try:
            self.update_sav_tab_visibility() # This calls load_purchase_history_table and load_sav_tickets_table
        except Exception as e:
            logging.error(f"Error during initial visibility update/load of SAV tab: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Chargement Partiel"), self.tr("Une erreur est survenue lors de la mise à jour/chargement initial de l'onglet SAV:\n{0}").format(str(e)))

        # Initial load for assignment tabs
        try:
            self.load_assigned_vendors_personnel()
        except Exception as e:
            logging.error(f"Error during initial load of Assigned Vendors/Personnel: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Chargement Partiel"), self.tr("Une erreur est survenue lors du chargement des vendeurs/personnel assignés:\n{0}").format(str(e)))
        try:
            self.load_assigned_technicians()
        except Exception as e:
            logging.error(f"Error during initial load of Assigned Technicians: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Chargement Partiel"), self.tr("Une erreur est survenue lors du chargement des techniciens assignés:\n{0}").format(str(e)))
        try:
            self.load_assigned_transporters()
        except Exception as e:
            logging.error(f"Error during initial load of Assigned Transporters: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Chargement Partiel"), self.tr("Une erreur est survenue lors du chargement des transporteurs assignés:\n{0}").format(str(e)))
        try:
            self.load_assigned_freight_forwarders()
        except Exception as e:
            logging.error(f"Error during initial load of Assigned Freight Forwarders: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Chargement Partiel"), self.tr("Une erreur est survenue lors du chargement des transitaires assignés:\n{0}").format(str(e)))

        # Connect selection changed signals for assignment tables
        self.assigned_vendors_table.itemSelectionChanged.connect(self.update_assigned_vendors_buttons_state)
        self.assigned_technicians_table.itemSelectionChanged.connect(self.update_assigned_technicians_buttons_state)
        self.assigned_transporters_table.itemSelectionChanged.connect(self.update_assigned_transporters_buttons_state)
        self.assigned_forwarders_table.itemSelectionChanged.connect(self.update_assigned_forwarders_buttons_state)

        # --- Billing Tab ---
        self.billing_tab = QWidget()
        self.billing_tab_layout = QVBoxLayout(self.billing_tab)

        self.generate_invoice_button = QPushButton(QIcon(":/icons/file-plus.svg"), self.tr("Generate Final Invoice"))
        self.generate_invoice_button.setToolTip(self.tr("Open dialog to prepare and generate a final invoice for this client."))
        self.generate_invoice_button.clicked.connect(self.handle_generate_final_invoice)
        self.billing_tab_layout.addWidget(self.generate_invoice_button)
        self.billing_tab_layout.addStretch()

        self.tab_widget.addTab(self.billing_tab, QIcon(":/icons/credit-card.svg"), self.tr("Billing"))
        # Connect new accordion handlers
        self.client_info_group_box.toggled.connect(self._handle_client_info_section_toggled)
        self.notes_group_box.toggled.connect(self._handle_notes_section_toggled)
        self.tabs_group_box.toggled.connect(self._handle_tabs_section_toggled)

    def delete_client_document_entry(self, document_id, file_path):
        """
        Deletes a client document entry from the database and the corresponding file from disk.
        """
        if not document_id:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("ID du document manquant."))
            return

        # Ensure file_path is a string for os.path.basename
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
                            self.notify(self.tr("Succès"), self.tr("Document et fichier supprimés avec succès."), type='SUCCESS')
                        except OSError as e_file:
                            logging.error(f"Error deleting file {file_path}: {e_file}", exc_info=True)
                            self.notify(self.tr("Erreur Fichier"), self.tr("Document supprimé de la base de données, mais échec de la suppression du fichier:\n{0}").format(str(e_file)), type='ERROR')
                    else:
                        logging.warning(f"File path not provided or file does not exist for document ID {document_id}: {file_path}. DB entry deleted.")
                        self.notify(self.tr("Succès (Partiel)"), self.tr("Entrée de document supprimée de la base de données. Fichier non trouvé ou chemin non spécifié."), type='WARNING')
                else:
                    self.notify(self.tr("Erreur DB"), self.tr("Impossible de supprimer l'entrée du document de la base de données (ID: {0}). Vérifiez les logs.").format(document_id), type='ERROR')

            except Exception as e:
                logging.error(f"Error in delete_client_document_entry for doc ID {document_id}: {e}", exc_info=True)
                self.notify(self.tr("Erreur Suppression"), self.tr("Une erreur inattendue est survenue:\n{0}").format(str(e)), type='CRITICAL')
            finally:
                self.populate_doc_table()

    def _handle_edit_pdf_action(self, file_path, document_id):
        if file_path and os.path.exists(file_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
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
           contacts = db_manager.get_contacts_for_client(client_uuid, limit=10, offset=0) # Fetch a few contacts
           if contacts:
               for contact in contacts:
                   if contact.get('phone'):
                       if not fallback_phone: # Store first available phone number
                           fallback_phone = contact['phone']
                       if contact.get('is_primary_for_client'):
                           primary_phone = contact['phone']
                           break # Found primary, use this

               selected_phone = primary_phone if primary_phone else fallback_phone

               if selected_phone:
                   # Ensure SendWhatsAppDialog is available
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

        # Accordion logic connections
       # if hasattr(self, 'notes_group_box') and hasattr(self, 'tabs_group_box'):
            # self.notes_group_box.toggled.connect(self._handle_notes_toggled)
            # self.tabs_group_box.toggled.connect(self._handle_tabs_toggled)

    def _handle_client_info_section_toggled(self, checked):
        # Ensure the container widget exists
        if not hasattr(self, 'info_container_widget'):
            return
        self.info_container_widget.setVisible(checked)

        if checked:
            # Block signals to prevent infinite loops or unintended recursive calls
            if hasattr(self, 'notes_group_box'):
                self.notes_group_box.blockSignals(True)
                self.notes_group_box.setChecked(False)
                if hasattr(self, 'notes_container_widget'): # Ensure notes_container_widget also exists
                    self.notes_container_widget.setVisible(False) # Explicitly hide content
                self.notes_group_box.blockSignals(False)

            if hasattr(self, 'tabs_group_box'):
                self.tabs_group_box.blockSignals(True)
                self.tabs_group_box.setChecked(False)
                if hasattr(self, 'tab_widget'): # Ensure tab_widget exists
                    self.tab_widget.setVisible(False) # Explicitly hide content
                self.tabs_group_box.blockSignals(False)
        elif not self.notes_group_box.isChecked() and not self.tabs_group_box.isChecked():
            # If this is the only one checked, and user tried to uncheck it, re-check it.
            self.client_info_group_box.blockSignals(True)
            self.client_info_group_box.setChecked(True)
            self.info_container_widget.setVisible(True) # Ensure content visibility matches state
            self.client_info_group_box.blockSignals(False)

    def _handle_notes_section_toggled(self, checked):
        # Ensure the container widget exists
        if not hasattr(self, 'notes_container_widget'):
            return
        self.notes_container_widget.setVisible(checked)

        if checked:
            if hasattr(self, 'client_info_group_box'):
                self.client_info_group_box.blockSignals(True)
                self.client_info_group_box.setChecked(False)
                if hasattr(self, 'info_container_widget'): # Ensure info_container_widget also exists
                    self.info_container_widget.setVisible(False) # Explicitly hide content
                self.client_info_group_box.blockSignals(False)

            if hasattr(self, 'tabs_group_box'):
                self.tabs_group_box.blockSignals(True)
                self.tabs_group_box.setChecked(False)
                if hasattr(self, 'tab_widget'): # Ensure tab_widget exists
                     self.tab_widget.setVisible(False) # Explicitly hide content
                self.tabs_group_box.blockSignals(False)
        elif not self.client_info_group_box.isChecked() and not self.tabs_group_box.isChecked():
            # If this is the only one checked, and user tried to uncheck it, re-check it.
            self.notes_group_box.blockSignals(True)
            self.notes_group_box.setChecked(True)
            self.notes_container_widget.setVisible(True) # Ensure content visibility matches state
            self.notes_group_box.blockSignals(False)

    def _handle_tabs_section_toggled(self, checked):
        # Ensure the tab_widget (content) exists
        if not hasattr(self, 'tab_widget'):
            return
        self.tab_widget.setVisible(checked)

        if checked:
            # Collapse Client Info
            if hasattr(self, 'client_info_group_box'):
                self.client_info_group_box.blockSignals(True)
                self.client_info_group_box.setChecked(False)
                if hasattr(self, 'info_container_widget'): self.info_container_widget.setVisible(False)
                self.client_info_group_box.blockSignals(False)
            # Collapse Notes
            if hasattr(self, 'notes_group_box'):
                self.notes_group_box.blockSignals(True)
                self.notes_group_box.setChecked(False)
                if hasattr(self, 'notes_container_widget'): self.notes_container_widget.setVisible(False)
                self.notes_group_box.blockSignals(False)
            # Collapse Contacts
            if hasattr(self, 'contacts_group_box'):
                self.contacts_group_box.blockSignals(True)
                self.contacts_group_box.setChecked(False)
                if hasattr(self, 'contacts_container_widget'): self.contacts_container_widget.setVisible(False)
                self.contacts_group_box.blockSignals(False)

        elif not self.client_info_group_box.isChecked() and \
             not self.notes_group_box.isChecked() and \
             (not hasattr(self, 'contacts_group_box') or not self.contacts_group_box.isChecked()): # Check if contacts_group_box exists
            # If this is the only one checked, and user tried to uncheck it, re-check it.
            self.tabs_group_box.blockSignals(True)
            self.tabs_group_box.setChecked(True)
            self.tab_widget.setVisible(True) # Ensure content visibility matches state
            self.tabs_group_box.blockSignals(False)

    def _handle_contacts_section_toggled(self, checked):
        if not hasattr(self, 'contacts_container_widget'):
            return
        self.contacts_container_widget.setVisible(checked)

        if checked:
            # Collapse Client Info
            if hasattr(self, 'client_info_group_box'):
                self.client_info_group_box.blockSignals(True)
                self.client_info_group_box.setChecked(False)
                if hasattr(self, 'info_container_widget'): self.info_container_widget.setVisible(False)
                self.client_info_group_box.blockSignals(False)
            # Collapse Notes
            if hasattr(self, 'notes_group_box'):
                self.notes_group_box.blockSignals(True)
                self.notes_group_box.setChecked(False)
                if hasattr(self, 'notes_container_widget'): self.notes_container_widget.setVisible(False)
                self.notes_group_box.blockSignals(False)
            # Collapse Tabs Group
            if hasattr(self, 'tabs_group_box'):
                self.tabs_group_box.blockSignals(True)
                self.tabs_group_box.setChecked(False)
                if hasattr(self, 'tab_widget'): self.tab_widget.setVisible(False)
                self.tabs_group_box.blockSignals(False)

        elif not self.client_info_group_box.isChecked() and \
             not self.notes_group_box.isChecked() and \
             (not hasattr(self, 'tabs_group_box') or not self.tabs_group_box.isChecked()):
            self.contacts_group_box.blockSignals(True)
            self.contacts_group_box.setChecked(True)
            self.contacts_container_widget.setVisible(True)
            self.contacts_group_box.blockSignals(False)


    def load_sav_tickets_table(self):
        # Ensure sav_tickets_table is initialized before use
        if not hasattr(self, 'sav_tickets_table'):
            # This might indicate an issue if SAV tab is created but table isn't part of its layout yet.
            # For now, just return to prevent error, but this should be reviewed if SAV tab is expected.
            # It's possible this method is called before SAV tab UI is fully set up during initial __init__.
            print("Warning: load_sav_tickets_table called before sav_tickets_table is initialized.")
            return

        self.sav_tickets_table.setRowCount(0)
        client_id = self.client_info.get('client_id')
        if not client_id:
            return

        try:
            tickets = db_manager.get_sav_tickets_for_client(client_id)
            if tickets is None: tickets = []

            self.sav_tickets_table.setRowCount(len(tickets))
            for row_idx, ticket in enumerate(tickets):
                ticket_id = ticket.get('ticket_id')

                id_item = QTableWidgetItem(str(ticket_id))
                id_item.setData(Qt.UserRole, ticket_id)
                self.sav_tickets_table.setItem(row_idx, 0, id_item) # Hidden

                # Product Name
                cpp_id = ticket.get('client_project_product_id')
                product_name_display = self.tr("N/A")
                if cpp_id:
                    # This could be optimized by batch fetching product names if performance is an issue
                    linked_product_info = db_manager.get_client_project_product_by_id(cpp_id) # Custom function needed
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
                    except ValueError:
                        opened_at_formatted = opened_at_str
                else:
                    opened_at_formatted = self.tr('N/A')
                self.sav_tickets_table.setItem(row_idx, 4, QTableWidgetItem(opened_at_formatted))

                tech_name = self.tr("Non assigné")
                if ticket.get('assigned_technician_id'):
                    tech_info = db_manager.get_team_member_by_id(ticket['assigned_technician_id'])
                    if tech_info: tech_name = tech_info.get('full_name', self.tr("Technicien Inconnu"))
                self.sav_tickets_table.setItem(row_idx, 5, QTableWidgetItem(tech_name))

                # Actions button
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(2,2,2,2); actions_layout.setSpacing(5)
                view_edit_button = QPushButton(self.tr("Voir/Modifier"))
                view_edit_button.clicked.connect(lambda checked, t_id=ticket_id: self.view_edit_sav_ticket_dialog(t_id))
                actions_layout.addWidget(view_edit_button)
                actions_layout.addStretch()
                self.sav_tickets_table.setCellWidget(row_idx, 6, actions_widget)

        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur Chargement Tickets SAV"),
                                 self.tr("Impossible de charger les tickets SAV:\n{0}").format(str(e)))

    def open_new_sav_ticket_dialog(self):
        client_id = self.client_info.get('client_id')
        if not client_id:
            QMessageBox.warning(self, self.tr("Erreur Client"), self.tr("ID Client non disponible."))
            return

        try:
            from sav.ticket_dialog import SAVTicketDialog # Import here to avoid circular if moved
        except ImportError:
            QMessageBox.critical(self, self.tr("Erreur Importation"), self.tr("Le dialogue de ticket SAV n'a pas pu être chargé."))
            return

        all_client_products = db_manager.get_products_for_client_or_project(client_id, project_id=None)
        purchased_items = [
            {'name': p.get('product_name', 'N/A'), 'client_project_product_id': p.get('client_project_product_id')}
            for p in all_client_products if p.get('purchase_confirmed_at') is not None
        ]

        dialog = SAVTicketDialog(client_id=client_id, purchased_products=purchased_items, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_sav_tickets_table()

    def view_edit_sav_ticket_dialog(self, ticket_id):
        client_id = self.client_info.get('client_id')
        if not client_id: # Should not happen if ticket_id is valid for this client context
            QMessageBox.warning(self, self.tr("Erreur Client"), self.tr("ID Client non disponible."))
            return

        try:
            from sav.ticket_dialog import SAVTicketDialog
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
        if dialog.exec_() == QDialog.Accepted:
            self.load_sav_tickets_table()

    # Placeholder handlers for new Assignment buttons
    def handle_add_assigned_vendor(self):
        if not self.default_company_id:
            QMessageBox.warning(self, self.tr("Société par Défaut Manquante"),
                                self.tr("Aucune société par défaut n'est configurée. Impossible d'assigner du personnel."))
            return
        # Assuming "seller" role for this button, adjust as needed or make role_filter dynamic
        dialog = AssignPersonnelDialog(client_id=self.client_info['client_id'],
                                       role_filter=None, # Or "seller", "sales", etc.
                                       company_id=self.default_company_id,
                                       parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_assigned_vendors_personnel()

    def handle_remove_assigned_vendor(self):
        selected_items = self.assigned_vendors_table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, self.tr("Sélection Requise"), self.tr("Veuillez sélectionner un membre du personnel à retirer."))
            return

        assignment_id = selected_items[0].data(Qt.UserRole) # Assuming ID is stored in the first item
        if assignment_id is None and self.assigned_vendors_table.currentItem(): # Fallback if UserRole was not on first item
             assignment_id = self.assigned_vendors_table.currentItem().data(Qt.UserRole)


        if assignment_id is None:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de récupérer l'ID de l'assignation."))
            return

        reply = QMessageBox.question(self, self.tr("Confirmer Suppression"),
                                     self.tr("Êtes-vous sûr de vouloir retirer ce membre du personnel?"),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if db_manager.unassign_personnel_from_client(assignment_id):
                self.load_assigned_vendors_personnel()
            else:
                QMessageBox.warning(self, self.tr("Erreur DB"), self.tr("Impossible de retirer le membre du personnel."))

    def update_assigned_vendors_buttons_state(self):
        has_selection = bool(self.assigned_vendors_table.selectedItems())
        self.remove_assigned_vendor_btn.setEnabled(has_selection)


    def handle_add_assigned_technician(self):
        if not self.default_company_id:
            QMessageBox.warning(self, self.tr("Société par Défaut Manquante"),
                                self.tr("Aucune société par défaut n'est configurée. Impossible d'assigner des techniciens."))
            return
        # Assuming "technical_manager" or similar role for technicians
        dialog = AssignPersonnelDialog(client_id=self.client_info['client_id'],
                                       role_filter="technical_manager", # Or more generic like "technician"
                                       company_id=self.default_company_id,
                                       parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_assigned_technicians()

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

        reply = QMessageBox.question(self, self.tr("Confirmer Suppression"),
                                     self.tr("Êtes-vous sûr de vouloir retirer ce technicien?"),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if db_manager.unassign_personnel_from_client(assignment_id):
                self.load_assigned_technicians()
            else:
                QMessageBox.warning(self, self.tr("Erreur DB"), self.tr("Impossible de retirer le technicien."))

    def update_assigned_technicians_buttons_state(self):
        has_selection = bool(self.assigned_technicians_table.selectedItems())
        self.remove_assigned_technician_btn.setEnabled(has_selection)

    def handle_add_assigned_transporter(self):
        dialog = AssignTransporterDialog(client_id=self.client_info['client_id'], parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_assigned_transporters()

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

        reply = QMessageBox.question(self, self.tr("Confirmer Suppression"),
                                     self.tr("Êtes-vous sûr de vouloir retirer ce transporteur?"),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if db_manager.unassign_transporter_from_client(client_transporter_id):
                self.load_assigned_transporters()
            else:
                QMessageBox.warning(self, self.tr("Erreur DB"), self.tr("Impossible de retirer le transporteur."))

    def update_assigned_transporters_buttons_state(self):
        has_selection = bool(self.assigned_transporters_table.selectedItems())
        self.remove_assigned_transporter_btn.setEnabled(has_selection)


    def handle_add_assigned_forwarder(self):
        dialog = AssignFreightForwarderDialog(client_id=self.client_info['client_id'], parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_assigned_freight_forwarders()

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

        reply = QMessageBox.question(self, self.tr("Confirmer Suppression"),
                                     self.tr("Êtes-vous sûr de vouloir retirer ce transitaire?"),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if db_manager.unassign_forwarder_from_client(client_forwarder_id):
                self.load_assigned_freight_forwarders()
            else:
                QMessageBox.warning(self, self.tr("Erreur DB"), self.tr("Impossible de retirer le transitaire."))

    def update_assigned_forwarders_buttons_state(self):
        has_selection = bool(self.assigned_forwarders_table.selectedItems())
        self.remove_assigned_forwarder_btn.setEnabled(has_selection)

    def open_carrier_email_dialog(self, row_index):
        try:
            transporter_name_item = self.assigned_transporters_table.item(row_index, 0) # Nom Transporteur

            if not transporter_name_item:
                QMessageBox.warning(self, self.tr("Erreur Données"), self.tr("Impossible de récupérer le nom du transporteur."))
                return

            transporter_name = transporter_name_item.text()
            client_transporter_id = transporter_name_item.data(Qt.UserRole)

            if client_transporter_id is None:
                QMessageBox.warning(self, self.tr("Erreur Données"), self.tr("ID du transporteur non trouvé pour cette ligne."))
                return

            # Fetch transporter details to get a reliable email.
            # This is a simplified way to get the email. Ideally, fetch directly or store more info in the table item's UserRole.
            assigned_list = db_manager.get_assigned_transporters_for_client(self.client_info.get('client_id'))
            transporter_email = ""
            if assigned_list: # Ensure assigned_list is not None
                for item_data in assigned_list:
                    if item_data.get('client_transporter_id') == client_transporter_id:
                        # Check for an 'email' field first
                        transporter_email = item_data.get('email')
                        if not transporter_email: # Fallback to 'contact_person' if it might be an email
                            contact_person_field = item_data.get('contact_person', '')
                            # Basic check if contact_person_field looks like an email
                            if '@' in contact_person_field and '.' in contact_person_field.split('@')[-1]:
                                transporter_email = contact_person_field
                        break

            if not transporter_email:
                email_text, ok = QInputDialog.getText(self, self.tr("Email du Transporteur Manquant"),
                                                      self.tr("L'email pour {0} n'est pas trouvé. Veuillez le saisir:").format(transporter_name))
                if ok and email_text.strip():
                    transporter_email = email_text.strip()
                else:
                    QMessageBox.information(self, self.tr("Annulé"), self.tr("Envoi d'email annulé car l'email du destinataire est manquant."))
                    self.load_assigned_transporters() # Refresh table even if cancelled here
                    return

            client_name = self.client_info.get("client_name", self.tr("Notre Client"))

            # Ensure self.config (application config) is passed to CarrierEmailDialog
            # self.config should be available from ClientMainWidget's __init__
            dialog = CarrierEmailDialog(
                carrier_name=transporter_name,
                carrier_email=transporter_email,
                client_name=client_name,
                client_transporter_id=client_transporter_id, # Pass the ID
                parent=self,
                config=self.config
            )
            dialog.exec_()
            self.load_assigned_transporters() # Refresh table after dialog closes

        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur Dialogue Email"),
                                 self.tr("Une erreur est survenue lors de l'ouverture du dialogue d'email: {0}").format(str(e)))
            # For debugging: logging.error(f"Error opening carrier email dialog: {e}", exc_info=True)

    # Data Loading methods for Assignment Tables
    def load_assigned_vendors_personnel(self):
        self.assigned_vendors_table.setRowCount(0)
        self.assigned_vendors_table.setSortingEnabled(False)
        client_id = self.client_info.get('client_id')
        if not client_id: return
        try:
            # Example: Load all assigned personnel, or filter by a general "vendor/sales" role_in_project
            # For now, role_filter=None fetches all personnel assigned to this client.
            assigned_list = db_manager.get_assigned_personnel_for_client(client_id, role_filter=None) or []
            for row, item_data in enumerate(assigned_list):
                self.assigned_vendors_table.insertRow(row)
                name_item = QTableWidgetItem(item_data.get('personnel_name'))
                name_item.setData(Qt.UserRole, item_data.get('assignment_id')) # Store assignment_id
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
            # Example: Filter for personnel assigned with a role_in_project like 'Technicien assigné'
            # Or, if AssignPersonnelDialog uses a role_filter for DB CompanyPersonnel.role, that's different.
            # Assuming here role_in_project is the primary filter criteria from Client_AssignedPersonnel table.
            assigned_list = db_manager.get_assigned_personnel_for_client(client_id, role_filter="Technicien") or [] # Or specific role
            for row, item_data in enumerate(assigned_list): # This list now comes from get_assigned_personnel_for_client
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

                email_status = item_data.get('email_status', 'Pending') # Get email_status

                btn_send_email = QPushButton()
                if email_status == "Sent":
                    btn_send_email.setText(self.tr("Email Sent"))
                    btn_send_email.setStyleSheet("background-color: lightgray; color: black;")
                    btn_send_email.setEnabled(False)
                elif email_status == "Failed":
                    btn_send_email.setText(self.tr("Resend Email (Failed)"))
                    btn_send_email.setStyleSheet("background-color: orange; color: black;")
                    btn_send_email.clicked.connect(lambda checked, r=row: self.open_carrier_email_dialog(r))
                else: # Pending or other
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


    def load_products_for_dimension_tab(self):
        """Populates the product selector combo box in the Product Dimensions tab."""
        self.dim_product_selector_combo.blockSignals(True)
        self.dim_product_selector_combo.clear()
        self.dim_product_selector_combo.addItem(self.tr("Sélectionner un produit..."), None)

        client_id = self.client_info.get('client_id')
        if not client_id:
            self.dim_product_selector_combo.blockSignals(False)
            return

        try:
            # Fetch all globally available products for selection.
            # Assuming db_manager.get_all_products() returns a list of product dictionaries
            # with at least 'product_id', 'product_name', 'language_code'.
            all_global_products = db_manager.get_all_products(filters=None)

            if all_global_products:
                # Global products should be unique by their definition (product_id).
                # Sorting can be done here if not handled by the DB query, or to ensure consistent order.
                # For example: all_global_products.sort(key=lambda x: (x.get('product_name', ''), x.get('language_code', '')))

                for prod_data in all_global_products: # Iterate directly if already sorted or uniqueness is guaranteed by source
                    product_name = prod_data.get('product_name', 'N/A')
                    global_product_id = prod_data.get('product_id')
                    lang_code = prod_data.get('language_code', '')

                    display_text = f"{product_name} ({lang_code}) - ID: {global_product_id}"
                    # Store the global_product_id as data for the combo box item
                    self.dim_product_selector_combo.addItem(display_text, global_product_id)
        except Exception as e:
            print(f"Error loading products for dimension tab: {e}")
            QMessageBox.warning(self, self.tr("Erreur Chargement"), self.tr("Impossible de charger les produits pour l'onglet dimensions."))

        self.dim_product_selector_combo.blockSignals(False)
        self.on_dim_product_selected()


    def on_dim_product_selected(self, index=None):
        """Handles selection change in the product selector for the dimensions tab."""
        selected_global_product_id = self.dim_product_selector_combo.currentData()

        if selected_global_product_id is None:
            self.edit_client_product_dimensions_button.setEnabled(False)
        else:
            self.edit_client_product_dimensions_button.setEnabled(True)


    def on_edit_client_product_dimensions(self):
        selected_global_product_id = self.dim_product_selector_combo.currentData()
        if selected_global_product_id is None:
            QMessageBox.warning(self, self.tr("Aucun Produit Sélectionné"),
                                self.tr("Veuillez sélectionner un produit dans la liste déroulante."))
            return


        client_id = self.client_info.get('client_id')
        if not client_id:
            QMessageBox.critical(self, self.tr("Erreur Client"),
                                 self.tr("L'ID du client n'est pas disponible."))
            return

        dialog = ClientProductDimensionDialog(
            client_id=client_id,
            product_id=selected_global_product_id,
            app_root_dir=self.app_root_dir,
            parent=self
        )
        dialog.exec_()

        self.load_document_notes_filters()
        self.load_document_notes_table()



    def load_document_notes_filters(self):
        """Populates filter combos for the document notes tab."""
        self.doc_notes_type_filter_combo.blockSignals(True)
        self.doc_notes_lang_filter_combo.blockSignals(True)

        self.doc_notes_type_filter_combo.clear()
        self.doc_notes_type_filter_combo.addItem(self.tr("Tous Types"), None)
        doc_types = ["Proforma", "Packing List", "Sales Conditions", "Certificate of Origin", "Bill of Lading", "Other"]
        for doc_type in doc_types:
            self.doc_notes_type_filter_combo.addItem(doc_type, doc_type)

        self.doc_notes_lang_filter_combo.clear()
        self.doc_notes_lang_filter_combo.addItem(self.tr("Toutes Langues"), None)
        langs = ["fr", "en", "ar", "tr", "pt"]
        for lang in langs:
            self.doc_notes_lang_filter_combo.addItem(lang, lang)

        self.doc_notes_type_filter_combo.blockSignals(False)
        self.doc_notes_lang_filter_combo.blockSignals(False)

        self.doc_notes_type_filter_combo.setCurrentIndex(0)
        self.doc_notes_lang_filter_combo.setCurrentIndex(0)


    def load_document_notes_table(self):
        """Fetches data from db_manager.get_client_document_notes() and populates table."""
        self.document_notes_table.setRowCount(0)
        client_id = self.client_info.get("client_id")
        if not client_id:
            return

        doc_type_filter = self.doc_notes_type_filter_combo.currentData()
        lang_filter = self.doc_notes_lang_filter_combo.currentData()

        try:
            notes = db_manager.get_client_document_notes(
                client_id,
                document_type=doc_type_filter,
                language_code=lang_filter,
                is_active=None
            )
            notes = notes if notes else []

            self.document_notes_table.setRowCount(len(notes))
            for row_idx, note in enumerate(notes):
                note_id = note.get("note_id")

                type_item = QTableWidgetItem(note.get("document_type"))
                type_item.setData(Qt.UserRole, note_id)
                self.document_notes_table.setItem(row_idx, 0, type_item)

                self.document_notes_table.setItem(row_idx, 1, QTableWidgetItem(note.get("language_code")))

                content_preview = note.get("note_content", "")
                if len(content_preview) > 70: content_preview = content_preview[:67] + "..."
                # self.document_notes_table.setItem(row_idx, 2, QTableWidgetItem(content_preview)) # Replaced by HTML label

                note_content = note.get("note_content", "")
                lines = [line.strip() for line in note_content.split('\n') if line.strip()]

                html_content = ""
                if lines:
                    html_content = "<ol style='margin:0px; padding-left: 15px;'>"
                    for line in lines:

                        escaped_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                        html_content += f"<li>{escaped_line}</li>"
                    html_content += "</ol>"
                else:
                    html_content = f"<p style='margin:0px; font-style:italic;'>{self.tr('Aucune note.')}</p>"

                note_label = QLabel()
                note_label.setText(html_content)
                note_label.setWordWrap(True)

                self.document_notes_table.setCellWidget(row_idx, 2, note_label)


                active_text = self.tr("Oui") if note.get("is_active") else self.tr("Non")
                active_item = QTableWidgetItem(active_text)
                active_item.setTextAlignment(Qt.AlignCenter)
                self.document_notes_table.setItem(row_idx, 3, active_item)


                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(5, 0, 5, 0)
                actions_layout.setSpacing(5)

                role_name = self.current_user_info.get('role_name') if self.current_user_info else None
                # Assuming P_MANAGE_CLIENT_DOCUMENTS or a new P_MANAGE_DOCUMENT_NOTES controls this
                can_manage_doc_notes = has_permission(role_name, P_MANAGE_CLIENT_DOCUMENTS)

                if can_manage_doc_notes:
                    edit_button = QPushButton(QIcon(":/icons/pencil.svg"), "")
                    edit_button.setToolTip(self.tr("Modifier cette note"))
                    edit_button.clicked.connect(lambda checked, n_id=note_id: self.on_edit_document_note_clicked(n_id))
                    actions_layout.addWidget(edit_button)

                    delete_button = QPushButton(QIcon(":/icons/trash.svg"), "")
                    delete_button.setToolTip(self.tr("Supprimer cette note"))
                    delete_button.setObjectName("dangerButton")
                    delete_button.clicked.connect(lambda checked, n_id=note_id: self.on_delete_document_note_clicked(n_id))
                    actions_layout.addWidget(delete_button)
                else:
                    # Add spacers or leave empty if no permissions
                    actions_layout.addStretch()

                actions_layout.addStretch() # Ensure this is outside the conditional if buttons were added
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
        if dialog.exec_() == QDialog.Accepted:
            self.load_document_notes_table()


    def on_edit_document_note_clicked(self, note_id):
        client_id = self.client_info.get("client_id")
        if not client_id:
            QMessageBox.warning(self, self.tr("Erreur Client"), self.tr("ID Client non disponible."))
            return

        note_data = db_manager.get_client_document_note_by_id(note_id)
        if note_data:
            dialog = self.ClientDocumentNoteDialog(client_id=client_id, note_data=note_data, parent=self)
            if dialog.exec_() == QDialog.Accepted:
                self.load_document_notes_table()
        else:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Note non trouvée (ID: {0}).").format(note_id))


    def on_delete_document_note_clicked(self, note_id):
        reply = QMessageBox.question(self, self.tr("Confirmer Suppression"),
                                     self.tr("Êtes-vous sûr de vouloir supprimer cette note (ID: {0})?").format(note_id),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                success = db_manager.delete_client_document_note(note_id)
                if success:
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Note supprimée avec succès."))
                    self.load_document_notes_table()
                else:
                    QMessageBox.warning(self, self.tr("Échec"), self.tr("Impossible de supprimer la note. Vérifiez les logs."))
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
        if self.total_contacts_count == 0:
            total_pages = 1
            current_page = 1
        else:
            total_pages = math.ceil(self.total_contacts_count / self.CONTACT_PAGE_LIMIT)
            current_page = (self.current_contact_offset // self.CONTACT_PAGE_LIMIT) + 1

        self.contact_page_info_label.setText(f"Page {current_page} / {total_pages}")
        self.prev_contact_button.setEnabled(self.current_contact_offset > 0)
        self.next_contact_button.setEnabled((self.current_contact_offset + self.CONTACT_PAGE_LIMIT) < self.total_contacts_count)

    def add_document(self):
        # Define available languages
        available_languages = ["en", "fr", "ar", "tr", "pt"]

        # Ask user to select language
        selected_doc_language, ok = QInputDialog.getItem(
            self,
            self.tr("Sélectionner la langue"),
            self.tr("Langue du document:"),
            available_languages,
            0,
            False
        )

        if not ok or not selected_doc_language:
            QMessageBox.information(self, self.tr("Annulé"), self.tr("L'opération d'ajout de document a été annulée."))
            return

        # Get the base path for the client's documents
        initial_dir = self.config.get("clients_dir", os.path.expanduser("~"))

        selected_file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Sélectionner un document"),
            initial_dir,
            self.tr("Tous les fichiers (*.*)")
        )

        if selected_file_path:
            try:
                # Determine the target directory using the selected language
                # AND POTENTIAL order_identifier (conceptual for now, as add_document doesn't create DB entry)
                client_base_path = self.client_info.get("base_folder_path")
                if not client_base_path:
                    client_base_path = self.client_info.get("default_base_folder_path", "")

                if not client_base_path or not os.path.isdir(client_base_path):
                    QMessageBox.warning(self, self.tr("Erreur Dossier Client"), self.tr("Le chemin du dossier de base du client n'est pas configuré ou est invalide."))
                    return

                # --- Conceptual: How order_identifier would be handled if add_document created DB entries ---
                # For now, this part is more about the file system structure if an order_id were available.
                # The actual capture of order_identifier for imported docs is deferred.
                # Let's assume `selected_order_identifier_for_import` is obtained similar to CreateDocumentDialog
                selected_order_identifier_for_import = None # Placeholder for this example
                # if self.client_info.get('category') == 'Distributeur' or db_manager.get_distinct_purchase_confirmed_at_for_client(self.client_info['client_id']):
                #     # ... QInputDialog logic to get order_identifier ...
                #     pass

                target_dir = os.path.join(client_base_path, selected_doc_language) # Default for general docs
                if selected_order_identifier_for_import:
                    safe_order_subfolder = selected_order_identifier_for_import.replace(':', '_').replace(' ', '_')
                    target_dir = os.path.join(client_base_path, safe_order_subfolder, selected_doc_language)
                # --- End conceptual part ---

                os.makedirs(target_dir, exist_ok=True)

                file_name = os.path.basename(selected_file_path)
                target_file_path = os.path.join(target_dir, file_name) # This is the actual save path

                if os.path.exists(target_file_path):
                    reply = QMessageBox.question(
                        self,
                        self.tr("Fichier Existant"),
                        self.tr("Un fichier du même nom existe déjà à cet emplacement. Voulez-vous le remplacer?"),
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        QMessageBox.information(self, self.tr("Annulé"), self.tr("L'opération d'ajout de document a été annulée."))
                        return

                shutil.copy(selected_file_path, target_file_path)

                # Metadata gathering
                client_id = self.client_info.get("client_id")
                document_name = os.path.basename(selected_file_path)
                file_name_on_disk = document_name
                file_path_relative = os.path.join(selected_doc_language, file_name) # Assuming target_dir structure

                # Infer document_type_generated from extension
                ext = os.path.splitext(file_name)[1].lower()
                if ext == ".html":
                    document_type_generated = "HTML"
                elif ext == ".pdf":
                    document_type_generated = "PDF"
                elif ext == ".xlsx":
                    document_type_generated = "XLSX"
                elif ext == ".docx":
                    document_type_generated = "DOCX"
                else:
                    document_type_generated = ext.upper().replace(".", "") if ext else "OTHER"

                language_code = selected_doc_language
                source_template_id = None # For imported documents

                order_identifier = None
                if hasattr(self, 'doc_order_filter_combo') and self.doc_order_filter_combo.isVisible():
                    current_order_data = self.doc_order_filter_combo.currentData()
                    if current_order_data not in ["ALL", "NONE"]:
                        order_identifier = current_order_data

                # created_by_user_id = None # ClientMainWidget does not have self.current_user_id - Now it does
                notes = None
                version_tag = "1.0"

                doc_db_data_for_crud = {
                    "client_id": client_id,
                    "document_name": document_name,
                    "file_name_on_disk": file_name_on_disk,
                    "file_path_relative": file_path_relative,
                    "document_type_generated": document_type_generated,
                    "language_code": language_code,
                    "source_template_id": source_template_id,
                    "order_identifier": order_identifier,
                    "user_id": self.current_user_id, # Use the stored current_user_id
                    "notes": notes,
                    "version_tag": version_tag,
                    # project_id is not explicitly gathered here, will be None if not in dict
                }
                # The key in add_client_document is 'user_id', not 'created_by_user_id'
                # Let's adjust doc_db_data to use 'user_id' for the CRUD function based on its definition.
                # doc_db_data_for_crud = doc_db_data.copy() # No longer needed, dict created directly
                # doc_db_data_for_crud['user_id'] = doc_db_data_for_crud.pop('created_by_user_id') # No longer needed


                db_success = False
                try:
                    new_doc_db_id = db_manager.add_client_document(doc_db_data_for_crud)
                    if new_doc_db_id:
                        db_success = True
                        # Update client's selected languages if necessary
                        current_selected_languages = self.client_info.get("selected_languages", [])
                        if isinstance(current_selected_languages, str):
                            current_selected_languages = [lang.strip() for lang in current_selected_languages.split(',') if lang.strip()]
                        if not current_selected_languages: current_selected_languages = []

                        if selected_doc_language not in current_selected_languages:
                            add_lang_reply = QMessageBox.question(
                                self, self.tr("Ajouter Langue"),
                                self.tr("Voulez-vous ajouter '{0}' aux langues sélectionnées pour ce client?").format(selected_doc_language),
                                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
                            )
                            if add_lang_reply == QMessageBox.Yes:
                                updated_languages_list = current_selected_languages + [selected_doc_language]
                                updated_languages_str = ",".join(updated_languages_list)
                                client_id_to_update = self.client_info.get("client_id")
                                if client_id_to_update:
                                    if db_manager.update_client(client_id_to_update, {'selected_languages': updated_languages_str}):
                                        self.client_info["selected_languages"] = updated_languages_list
                                        print(f"Client {client_id_to_update} selected_languages updated to {updated_languages_str}")
                                    else:
                                        QMessageBox.warning(self, self.tr("Erreur DB"), self.tr("Échec de la mise à jour des langues du client dans la DB."))
                                else:
                                    QMessageBox.warning(self, self.tr("Erreur Client"), self.tr("ID Client non disponible, impossible de mettre à jour les langues."))

                        self.populate_doc_table() # Call after successful DB operation
                        QMessageBox.information(
                            self, self.tr("Succès"),
                            self.tr("Document '{0}' importé et enregistré avec succès en langue '{1}'.").format(file_name, selected_doc_language)
                        )
                    else:
                        # db_success remains False
                        self.populate_doc_table() # Still populate to show the file if copied
                        QMessageBox.warning(
                            self, self.tr("Échec Enregistrement DB"),
                            self.tr("Document '{0}' copié avec succès en langue '{1}', mais échec de l'enregistrement dans la base de données. Le document pourrait ne pas s'afficher correctement.").format(file_name, selected_doc_language)
                        )
                except Exception as db_e:
                    # db_success remains False
                    logging.error(f"Error during database operation in add_document: {db_e}", exc_info=True)
                    self.populate_doc_table() # Still populate to show the file if copied
                    QMessageBox.warning(
                        self, self.tr("Erreur Base de Données"),
                        self.tr("Document '{0}' copié, mais une erreur est survenue lors de l'enregistrement dans la base de données: {1}. Le document pourrait ne pas s'afficher correctement.").format(file_name, str(db_e))
                    )

            except Exception as e:
                logging.error(f"Error copying file or preparing metadata in add_document: {e}", exc_info=True)
                QMessageBox.warning(
                    self, self.tr("Erreur"),
                    self.tr("Impossible d'ajouter le document : {0}").format(str(e))
                )

    def _handle_generate_and_open_pdf_action(self, document_data: dict):
        QApplication.setOverrideCursor
