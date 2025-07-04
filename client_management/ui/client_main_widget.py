# -*- coding: utf-8 -*-
import os
import sys
import logging
from datetime import datetime
import math

from carrier_email_dialog import CarrierEmailDialog
from client_management.dialogs.referent_details_dialog import ReferentDetailsDialog

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
from db.cruds import users_crud
from db.cruds.clients_crud import clients_crud_instance
from dialogs import ClientProductDimensionDialog, AssignPersonnelDialog, AssignTransporterDialog, AssignFreightForwarderDialog, AssignMoneyTransferAgentDialog
from whatsapp.whatsapp_dialog import SendWhatsAppDialog
import db.cruds.money_transfer_agents_crud as mta_crud
import db.cruds.client_order_money_transfer_agents_crud as coma_crud
import db.cruds.projects_crud as projects_crud

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


class ClientMainWidget(QWidget):
    CONTACT_PAGE_LIMIT = 15

    def __init__(self, client_info, config, app_root_dir, notification_manager, current_user_info: dict, client_controller_instance: ClientController, parent=None):
        super().__init__(parent)
        self.current_user_info = current_user_info
        self.current_user_id = self.current_user_info.get('user_id')

        logging.info(f"ClientMainWidget.__init__: INSTANTIATION STARTED for client_id={client_info.get('client_id')}, user: {self.current_user_info.get('username')}")
        self.client_info = client_info
        self.notification_manager = notification_manager

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
        if hasattr(self, 'create_docs_btn'): self.create_docs_btn.setEnabled(False)
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

        try:
            logging.info("ClientMainWidget.setup_ui: Starting setup for Collapsible Client Info Section...")
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

            self.referent_status_label = QLabel("")
            self.referent_status_label.setObjectName("referentStatusLabel")
            self.referent_status_label.setVisible(False)
            info_container_layout.addWidget(self.referent_status_label)

            action_layout = QHBoxLayout()

            self.manage_referent_btn = QPushButton(QIcon.fromTheme("star", QIcon(":/icons/emblem-favorite.svg")), self.tr("Gérer Référent"))
            self.manage_referent_btn.setToolTip(self.tr("Gérer le statut de référent pour ce client"))
            self.manage_referent_btn.clicked.connect(self.manage_referent_status_for_selected_client)
            action_layout.addWidget(self.manage_referent_btn)
            action_layout.addStretch(1)

            self.create_docs_btn = QPushButton(self.tr("Envoyer Mail"))
            self.create_docs_btn.setIcon(QIcon.fromTheme("mail-send", QIcon(":/icons/bell.svg")))
            self.create_docs_btn.setToolTip(self.tr("Envoyer un email au client"))
            self.create_docs_btn.setObjectName("primaryButton")
            self.create_docs_btn.clicked.connect(self.open_send_email_dialog)
            action_layout.addWidget(self.create_docs_btn)

            self.compile_pdf_btn = QPushButton(self.tr("Compiler PDF"))
            self.compile_pdf_btn.setIcon(QIcon.fromTheme("document-export"))
            self.compile_pdf_btn.setProperty("primary", True)
            self.compile_pdf_btn.clicked.connect(self.open_compile_pdf_dialog)
            # action_layout.addWidget(self.compile_pdf_btn)

            self.edit_save_client_btn = QPushButton(self.tr("Modifier Client"))
            self.edit_save_client_btn.setIcon(QIcon.fromTheme("document-edit", QIcon(":/icons/pencil.svg")))
            self.edit_save_client_btn.setToolTip(self.tr("Modifier les informations du client"))
            self.edit_save_client_btn.clicked.connect(self.toggle_client_edit_mode)
            action_layout.addWidget(self.edit_save_client_btn)

            self.send_whatsapp_btn = QPushButton(self.tr("Send WhatsApp"))
            self.send_whatsapp_btn.setIcon(QIcon.fromTheme("contact-new", QIcon(":/icons/user.svg")))
            self.send_whatsapp_btn.setToolTip(self.tr("Send a WhatsApp message to the client"))
            self.send_whatsapp_btn.clicked.connect(self.open_send_whatsapp_dialog)
            # action_layout.addWidget(self.send_whatsapp_btn)

            self.archive_client_btn = QPushButton(self.tr("Archiver Client"))
            self.archive_client_btn.setIcon(QIcon(":/icons/folder.svg"))
            self.archive_client_btn.setToolTip(self.tr("Archiver ce client (soft delete)"))
            self.archive_client_btn.clicked.connect(self.handle_archive_client)
            action_layout.addWidget(self.archive_client_btn)

            info_container_layout.addLayout(action_layout)

            self.internal_client_info_tabs = QTabWidget()
            info_container_layout.addWidget(self.internal_client_info_tabs)

            self.client_details_tab = QWidget()
            details_tab_layout = QVBoxLayout(self.client_details_tab)
            self.status_combo = QComboBox()
            self.details_layout = QFormLayout()
            self.details_layout.setLabelAlignment(Qt.AlignLeft)
            self.details_layout.setSpacing(10)

            self.project_id_label = QLabel(self.tr("ID Projet:"))
            self.project_id_value_label = QLabel(self.tr("N/A"))
            self.details_layout.addRow(self.project_id_label, self.project_id_value_label)
            self.country_city_label = QLabel(self.tr("Localisation:"))
            self.country_city_widget = QWidget()
            country_city_h_layout = QHBoxLayout(self.country_city_widget)
            country_city_h_layout.setContentsMargins(0,0,0,0)
            self.country_label_static = QLabel(self.tr("Pays:"))
            self.country_value_label = QLabel(self.tr("N/A"))
            self.city_label_static = QLabel(self.tr("Ville:"))
            self.city_value_label = QLabel(self.tr("N/A"))
            country_city_h_layout.addWidget(self.country_label_static)
            country_city_h_layout.addWidget(self.country_value_label)
            country_city_h_layout.addSpacing(20)
            country_city_h_layout.addWidget(self.city_label_static)
            country_city_h_layout.addWidget(self.city_value_label)
            country_city_h_layout.addStretch()
            self.details_layout.addRow(self.country_city_label, self.country_city_widget)
            self.price_date_label = QLabel(self.tr("Finances & Date:"))
            self.price_date_widget = QWidget()
            price_date_h_layout = QHBoxLayout(self.price_date_widget)
            price_date_h_layout.setContentsMargins(0,0,0,0)
            self.price_label_static = QLabel(self.tr("Prix Final:"))
            self.price_value_label = QLabel(self.tr("0 €"))
            self.date_label_static = QLabel(self.tr("Date Création:"))
            self.date_value_label = QLabel(self.tr("N/A"))
            price_date_h_layout.addWidget(self.price_label_static)
            price_date_h_layout.addWidget(self.price_value_label)
            price_date_h_layout.addSpacing(20)
            price_date_h_layout.addWidget(self.date_label_static)
            price_date_h_layout.addWidget(self.date_value_label)
            price_date_h_layout.addStretch()
            self.details_layout.addRow(self.price_date_label, self.price_date_widget)
            self.status_category_label = QLabel(self.tr("Classification:"))
            self.status_category_widget = QWidget()
            status_category_h_layout = QHBoxLayout(self.status_category_widget)
            status_category_h_layout.setContentsMargins(0,0,0,0)
            self.status_label_static = QLabel(self.tr("Statut:"))
            self.status_combo = QComboBox()
            self.category_label_static = QLabel(self.tr("Catégorie:"))
            self.category_value_label = QLabel(self.tr("N/A"))
            status_category_h_layout.addWidget(self.status_label_static)
            status_category_h_layout.addWidget(self.status_combo)
            status_category_h_layout.addSpacing(20)
            status_category_h_layout.addWidget(self.category_label_static)
            status_category_h_layout.addWidget(self.category_value_label)
            status_category_h_layout.addStretch()
            self.details_layout.addRow(self.status_category_label, self.status_category_widget)
            self.distributor_info_label_static = QLabel(self.tr("Info Distributeur:"))
            self.distributor_info_value_label = QLabel(self.tr("N/A"))
            self.distributor_info_value_label.setWordWrap(True)
            self.distributor_info_value_label.setObjectName("distributorInfoValueLabel")
            self.distributor_info_label_static.setObjectName("distributorInfoLabel")
            self.details_layout.addRow(self.distributor_info_label_static, self.distributor_info_value_label)
            self.need_label_static = QLabel(self.tr("Besoin Principal:"))
            self.need_value_label = QLabel(self.tr("N/A"))
            self.details_layout.addRow(self.need_label_static, self.need_value_label)
            self.folder_label_static = QLabel(self.tr("Chemin Dossier:"))
            self.folder_value_label = QLabel(self.tr("N/A"))
            self.folder_value_label.setOpenExternalLinks(True)
            self.folder_value_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
            self.details_layout.addRow(self.folder_label_static, self.folder_value_label)
            self.created_by_label_static = QLabel(self.tr("Créé par:"))
            self.created_by_value_label = QLabel(self.tr("N/A"))
            self.details_layout.addRow(self.created_by_label_static, self.created_by_value_label)
            details_tab_layout.addLayout(self.details_layout)
            self.internal_client_info_tabs.addTab(self.client_details_tab, self.client_info.get('client_name', self.tr("Détails Client")))
            self.populate_details_layout()

            contacts_tab_widget = QWidget()
            contacts_tab_layout = QVBoxLayout(contacts_tab_widget)
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
            self.add_contact_btn = QPushButton(self.tr("Ajouter")); self.add_contact_btn.setIcon(QIcon(":/icons/user-plus.svg")); self.add_contact_btn.setToolTip(self.tr("Ajouter un nouveau contact pour ce client")); self.add_contact_btn.clicked.connect(self.add_contact); contacts_btn_layout.addWidget(self.add_contact_btn)
            self.edit_contact_btn = QPushButton(self.tr("Modifier")); self.edit_contact_btn.setIcon(QIcon(":/icons/pencil.svg")); self.edit_contact_btn.setToolTip(self.tr("Modifier le contact sélectionné")); self.edit_contact_btn.clicked.connect(self.edit_contact); contacts_btn_layout.addWidget(self.edit_contact_btn)
            self.remove_contact_btn = QPushButton(self.tr("Supprimer")); self.remove_contact_btn.setIcon(QIcon(":/icons/trash.svg")); self.remove_contact_btn.setToolTip(self.tr("Supprimer le lien vers le contact sélectionné pour ce client")); self.remove_contact_btn.setObjectName("dangerButton"); self.remove_contact_btn.clicked.connect(self.remove_contact); contacts_btn_layout.addWidget(self.remove_contact_btn)
            contacts_tab_layout.addLayout(contacts_btn_layout)
            self.internal_client_info_tabs.addTab(contacts_tab_widget, self.tr("Contacts"))

            self.assignments_internal_tab = QWidget()
            assignments_internal_tab_layout = QVBoxLayout(self.assignments_internal_tab)
            self.assignments_sub_tabs = QTabWidget()
            assignments_internal_tab_layout.addWidget(self.assignments_sub_tabs)
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
            self.assigned_vendors_table.itemSelectionChanged.connect(self.update_assigned_vendors_buttons_state)
            self.assigned_technicians_table.itemSelectionChanged.connect(self.update_assigned_technicians_buttons_state)
            self.assigned_transporters_table.itemSelectionChanged.connect(self.update_assigned_transporters_buttons_state)
            self.assigned_forwarders_table.itemSelectionChanged.connect(self.update_assigned_forwarders_buttons_state)
            self.mta_project_selector_combo.currentIndexChanged.connect(self.handle_mta_project_selection_changed)
            self.assigned_mta_table.itemSelectionChanged.connect(self.update_mta_buttons_state)
            self.load_projects_for_mta_combo()
            self.add_assigned_mta_btn.setEnabled(False)
            self.remove_assigned_mta_btn.setEnabled(False)

            send_email_tab_widget = QWidget()
            send_email_tab_layout = QVBoxLayout(send_email_tab_widget)
            self.open_email_dialog_btn = QPushButton(self.tr("Composer un Email..."))
            self.open_email_dialog_btn.setIcon(QIcon.fromTheme("mail-send", QIcon(":/icons/bell.svg")))
            self.open_email_dialog_btn.clicked.connect(self.open_send_email_dialog)
            send_email_tab_layout.addWidget(self.open_email_dialog_btn)
            send_email_tab_layout.addStretch()
            self.internal_client_info_tabs.addTab(send_email_tab_widget, self.tr("Envoyer Mail"))

            send_whatsapp_tab_widget = QWidget()
            send_whatsapp_tab_layout = QVBoxLayout(send_whatsapp_tab_widget)
            self.open_whatsapp_dialog_btn = QPushButton(self.tr("Envoyer message WhatsApp..."))
            self.open_whatsapp_dialog_btn.setIcon(QIcon.fromTheme("contact-new", QIcon(":/icons/user.svg")))
            self.open_whatsapp_dialog_btn.clicked.connect(self.open_send_whatsapp_dialog)
            send_whatsapp_tab_layout.addWidget(self.open_whatsapp_dialog_btn)
            send_whatsapp_tab_layout.addStretch()
            self.internal_client_info_tabs.addTab(send_whatsapp_tab_widget, self.tr("Send WhatsApp"))

            client_info_group_layout.addWidget(self.info_container_widget)
            self.client_info_group_box.setChecked(True)
            layout.addWidget(self.client_info_group_box)
        except Exception as e:
            logging.error(f"Error in _setup_client_info_section: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur UI"), self.tr("Erreur initialisation section infos client:\n{0}").format(str(e)))

        self._setup_notes_section(layout)
        self._setup_main_tabs_section(layout)

        logging.info("ClientMainWidget.setup_ui: Starting initial data loading for tabs...")
        try:
            self.load_contacts()
            logging.info("ClientMainWidget.setup_ui: Successfully completed self.load_contacts()")
        except Exception as e:
            logging.error(f"ClientMainWidget.setup_ui: Error during self.load_contacts(): {e}", exc_info=True)

        logging.info("ClientMainWidget.setup_ui: Finished initial data loading for tabs (calls moved to individual tab/section initializers).")

        if hasattr(self, 'client_info_group_box'):
             self.client_info_group_box.toggled.connect(self._handle_client_info_section_toggled)
        if hasattr(self, 'notes_group_box'):
             self.notes_group_box.toggled.connect(self._handle_notes_section_toggled)
        if hasattr(self, 'tabs_group_box'):
             self.tabs_group_box.toggled.connect(self._handle_tabs_section_toggled)

        if hasattr(self, 'notes_edit'):
            self.notes_edit.installEventFilter(self)
        logging.info(f"ClientMainWidget.setup_ui: FULL UI SETUP COMPLETED for client_id={self.client_info.get('client_id')}")

        self._show_client_details_state() # Ensure initial state is correct if client_info is valid

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

        if hasattr(self, 'create_docs_btn'):
            self.create_docs_btn.setEnabled(can_manage_documents)
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
            self.notification_manager.show(self.tr("Accès Refusé"), self.tr("Vous n'avez pas la permission de gérer les référents."), type='ERROR')
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
            self.notification_manager.show(self.tr("Statut Référent"), self.tr("Le statut de référent a été mis à jour."), type='SUCCESS')
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
            self.tabs_group_box = QGroupBox(self.tr("Autres Informations"))
            self.tabs_group_box.setCheckable(True)
            tabs_group_layout = QVBoxLayout(self.tabs_group_box)
            self.tab_widget = QTabWidget()
            tabs_group_layout.addWidget(self.tab_widget)
            self.tabs_group_box.setChecked(False)
            main_layout.addWidget(self.tabs_group_box)

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
            notes_tab_idx = -1
            for i in range(self.tab_widget.count()):
                if self.tab_widget.widget(i) == self.document_notes_tab_widget_ref:
                    notes_tab_idx = i
                    break
            if notes_tab_idx != -1:
                 self.tab_widget.insertTab(notes_tab_idx + 1, self.product_dimensions_tab_widget_ref, self.tr("Dimensions Produit (Global)"))
            else:
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
            self.tab_widget.addTab(self.billing_tab_widget_ref, QIcon(":/icons/credit-card.svg"), self.tr("Billing"))

        except Exception as e:
            logging.error(f"Error in _setup_main_tabs_section: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur UI"), self.tr("Erreur initialisation conteneur onglets principaux:\n{0}").format(str(e)))

    def _setup_contacts_tab(self):
        pass

    def _setup_assignments_tab(self):
        try:
            logging.info("ClientMainWidget.setup_ui: Starting setup for Assignments Tab...")
            self.assignments_tab = QWidget()
            assignments_main_layout = QVBoxLayout(self.assignments_tab)
            self.assignments_sub_tabs = QTabWidget()
            assignments_main_layout.addWidget(self.assignments_sub_tabs)
            self.tab_widget.addTab(self.assignments_tab, self.tr("Affectations"))

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
            self.add_assigned_mta_btn = QPushButton(self.tr("Assigner Agent de Transfert"))
            self.remove_assigned_mta_btn = QPushButton(self.tr("Retirer Agent de Transfert"))
            mta_buttons_layout.addWidget(self.add_assigned_mta_btn)
            mta_buttons_layout.addWidget(self.remove_assigned_mta_btn)
            mta_layout.addLayout(mta_buttons_layout)
            self.assignments_sub_tabs.addTab(mta_widget, self.tr("Agents de Transfert d'Argent"))

        except Exception as e:
            logging.error(f"Error during UI setup of Assignments Tab Structure: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur UI"), self.tr("Erreur initialisation structure onglet Affectations:\n{0}").format(str(e)))

        try:
            logging.info("ClientMainWidget.setup_ui: Updating SAV tab visibility and loading initial data...")
            self.update_sav_tab_visibility()
        except Exception as e:
            logging.error(f"Error during initial visibility update/load of SAV tab: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Chargement Partiel"), self.tr("Une erreur est survenue lors de la mise à jour/chargement initial de l'onglet SAV:\n{0}").format(str(e)))

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

        self.assigned_vendors_table.itemSelectionChanged.connect(self.update_assigned_vendors_buttons_state)
        self.assigned_technicians_table.itemSelectionChanged.connect(self.update_assigned_technicians_buttons_state)
        self.assigned_transporters_table.itemSelectionChanged.connect(self.update_assigned_transporters_buttons_state)
        self.assigned_forwarders_table.itemSelectionChanged.connect(self.update_assigned_forwarders_buttons_state)

        self.mta_project_selector_combo.currentIndexChanged.connect(self.handle_mta_project_selection_changed)
        self.add_assigned_mta_btn.clicked.connect(self.handle_add_assigned_mta)
        self.remove_assigned_mta_btn.clicked.connect(self.handle_remove_assigned_mta)
        self.assigned_mta_table.itemSelectionChanged.connect(self.update_mta_buttons_state)

    def _setup_commandes_tab(self):
        try:
            logging.info("ClientMainWidget.setup_ui: Starting setup for Commandes Tab...")
            self.commandes_tab_widget = CommandeWidget(
                client_info=self.client_info,
                current_user_info=self.current_user_info,
                parent=self
            )
            if hasattr(self, 'tab_widget'):
                docs_tab_index = -1
                for i in range(self.tab_widget.count()):
                    if self.tab_widget.tabText(i) == self.tr("Documents"):
                        docs_tab_index = i
                        break
                if docs_tab_index != -1:
                    self.tab_widget.insertTab(docs_tab_index + 1, self.commandes_tab_widget, self.tr("Commandes"))
                else:
                    self.tab_widget.addTab(self.commandes_tab_widget, self.tr("Commandes"))
                logging.info("ClientMainWidget._setup_commandes_tab: Commandes tab added.")
            else:
                logging.error("ClientMainWidget._setup_commandes_tab: self.tab_widget not found. Cannot add Commandes tab.")
        except Exception as e:
            logging.error(f"Error in _setup_commandes_tab: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur UI"), self.tr("Erreur initialisation onglet Commandes:\n{0}").format(str(e)))

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
            self.notification_manager.show(
                self.tr("Nouvelle Version Créée"),
                self.tr("Une nouvelle version du document a été créée avec succès."),
                type='SUCCESS'
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
        if not hasattr(self, 'info_container_widget'):
            return
        self.info_container_widget.setVisible(checked)
        if checked:
            if hasattr(self, 'notes_group_box'):
                self.notes_group_box.blockSignals(True)
                self.notes_group_box.setChecked(False)
                if hasattr(self, 'notes_container_widget'):
                    self.notes_container_widget.setVisible(False)
                self.notes_group_box.blockSignals(False)
            if hasattr(self, 'tabs_group_box'):
                self.tabs_group_box.blockSignals(True)
                self.tabs_group_box.setChecked(False)
                if hasattr(self, 'tab_widget'):
                    self.tab_widget.setVisible(False)
                self.tabs_group_box.blockSignals(False)
        elif hasattr(self, 'notes_group_box') and not self.notes_group_box.isChecked() and \
             hasattr(self, 'tabs_group_box') and not self.tabs_group_box.isChecked():
            self.client_info_group_box.blockSignals(True)
            self.client_info_group_box.setChecked(True)
            self.info_container_widget.setVisible(True)
            self.client_info_group_box.blockSignals(False)

    def _handle_notes_section_toggled(self, checked):
        if not hasattr(self, 'notes_container_widget'):
            return
        self.notes_container_widget.setVisible(checked)
        if checked:
            if hasattr(self, 'client_info_group_box'):
                self.client_info_group_box.blockSignals(True)
                self.client_info_group_box.setChecked(False)
                if hasattr(self, 'info_container_widget'):
                    self.info_container_widget.setVisible(False)
                self.client_info_group_box.blockSignals(False)
            if hasattr(self, 'tabs_group_box'):
                self.tabs_group_box.blockSignals(True)
                self.tabs_group_box.setChecked(False)
                if hasattr(self, 'tab_widget'):
                     self.tab_widget.setVisible(False)
                self.tabs_group_box.blockSignals(False)
        elif hasattr(self, 'client_info_group_box') and not self.client_info_group_box.isChecked() and \
             hasattr(self, 'tabs_group_box') and not self.tabs_group_box.isChecked():
            self.notes_group_box.blockSignals(True)
            self.notes_group_box.setChecked(True)
            self.notes_container_widget.setVisible(True)
            self.notes_group_box.blockSignals(False)

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
                    edit_button = QPushButton(QIcon(":/icons/pencil.svg"), "")
                    edit_button.setToolTip(self.tr("Modifier cette note"))
                    edit_button.clicked.connect(lambda checked, n_id=note_id: self.on_edit_document_note_clicked(n_id))
                    actions_layout.addWidget(edit_button)
                    delete_button = QPushButton(QIcon(":/icons/trash.svg"), "")
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
