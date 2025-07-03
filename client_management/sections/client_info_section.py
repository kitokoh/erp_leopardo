# -*- coding: utf-8 -*-
import logging
import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QComboBox, QTabWidget, QGroupBox, QMessageBox, QDialog, QFormLayout,
    QTableWidget, QAbstractItemView, QHeaderView, QSizePolicy
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

import db as db_manager
from db.cruds import users_crud # For fetching user names

# Import other necessary dialogs and classes that will be used by internal tabs
# from ..dialogs import AssignPersonnelDialog, AssignTransporterDialog, AssignFreightForwarderDialog, AssignMoneyTransferAgentDialog
# from ..whatsapp.whatsapp_dialog import SendWhatsAppDialog
# from carrier_email_dialog import CarrierEmailDialog

# These will be moved into their own files later
# from .client_details_tab import ClientDetailsTab
# from .client_contacts_internal_tab import ClientContactsInternalTab
# from .client_assignments_internal_tab import ClientAssignmentsInternalTab
# from .client_email_internal_tab import ClientEmailInternalTab
# from .client_whatsapp_internal_tab import ClientWhatsAppInternalTab


class ClientInfoSection(QWidget):
    def __init__(self, client_info, config, app_root_dir, notification_manager, current_user_info, main_widget, parent=None):
        super().__init__(parent)
        self.client_info = client_info
        self.config = config
        self.app_root_dir = app_root_dir
        self.notification_manager = notification_manager
        self.current_user_info = current_user_info
        self.current_user_id = current_user_info.get('user_id')
        self.main_widget = main_widget # Reference to ClientMainWidget for callbacks if needed

        self.edit_widgets = {} # For edit mode

        # References to dialogs will be passed from ClientMainWidget or imported directly if static
        self.AssignPersonnelDialog = getattr(main_widget, 'AssignPersonnelDialog', None)
        self.AssignTransporterDialog = getattr(main_widget, 'AssignTransporterDialog', None)
        self.AssignFreightForwarderDialog = getattr(main_widget, 'AssignFreightForwarderDialog', None)
        self.AssignMoneyTransferAgentDialog = getattr(main_widget, 'AssignMoneyTransferAgentDialog', None)
        self.SendWhatsAppDialog = getattr(main_widget, 'SendWhatsAppDialog', None)
        self.SendEmailDialog = getattr(main_widget, 'SendEmailDialog', None) # For the internal email tab
        self.CarrierEmailDialog = getattr(main_widget, 'CarrierEmailDialog', None) # If used by assignments

        # CRUDs (can be accessed via db_manager or passed if preferred)
        self.users_crud = users_crud
        self.clients_crud_instance = getattr(db_manager, 'clients_crud_instance', None) # Example

        # CONTACT_PAGE_LIMIT will be defined in ClientContactsInternalTab
        # self.CONTACT_PAGE_LIMIT = 15
        self.current_contact_offset = 0
        self.total_contacts_count = 0

        # Default company ID needed for assignments
        self.default_company_id = getattr(main_widget, 'default_company_id', None)


        self._setup_section_ui()

    def _setup_section_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0) # This section is part of a groupbox, so no outer margins

        # The QGroupBox and its title are managed by ClientMainWidget.
        # This widget just provides the content for the group box's container.

        # Header Label (Client Name) - This might be better managed by ClientMainWidget's group box title
        # self.header_label = QLabel(f"<h2>{self.client_info.get('client_name', self.tr('Client Inconnu'))}</h2>")
        # self.header_label.setObjectName("clientHeaderLabel")
        # layout.addWidget(self.header_label)

        # Action buttons (Envoyer Mail, Modifier Client etc.) are also in ClientMainWidget for now.

        # Internal QTabWidget for Details, Contacts, Assignments, Email, WhatsApp
        self.internal_tabs = QTabWidget()
        layout.addWidget(self.internal_tabs)

        self._setup_details_tab()
        self._setup_contacts_internal_tab()
        self._setup_assignments_internal_tab()
        self._setup_email_internal_tab()
        self._setup_whatsapp_internal_tab()

        # Initial data loads for internal tabs
        self.load_contacts() # For the internal contacts tab
        # Assignment data loads will be called from _setup_assignments_internal_tab

    def _setup_details_tab(self):
        # This will be the content of the "Détails Client" tab within internal_tabs
        self.details_tab_content = QWidget() # Placeholder, will be replaced by ClientDetailsTab instance
        # For now, inline the basic structure to allow ClientMainWidget to call populate_details_layout on this instance

        details_tab_layout = QVBoxLayout(self.details_tab_content)
        self.details_layout = QFormLayout() # QFormLayout for client fields
        self.details_layout.setLabelAlignment(Qt.AlignLeft)
        self.details_layout.setSpacing(10)

        # Persistent UI Elements (Labels and value holders)
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
        self.status_combo = QComboBox() # This is THE status_combo
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
        self.internal_tabs.addTab(self.details_tab_content, self.client_info.get('client_name', self.tr("Détails Client")))

        # Initial population
        self.populate_details_layout()


    def _setup_contacts_internal_tab(self):
        # This will be the content of the "Contacts" tab within internal_tabs
        # Eventually, this will instantiate ClientContactsInternalTab
        self.contacts_internal_tab_content = QWidget() # Placeholder
        contacts_tab_layout = QVBoxLayout(self.contacts_internal_tab_content)

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
        self.contacts_table.cellDoubleClicked.connect(self.edit_contact) # Method to be moved here

        self.contacts_empty_label = QLabel(self.tr("Aucun contact ajouté pour ce client.\nCliquez sur '➕ Ajouter' pour commencer."))
        self.contacts_empty_label.setAlignment(Qt.AlignCenter)
        font_contacts_empty = self.contacts_empty_label.font(); font_contacts_empty.setPointSize(10)
        self.contacts_empty_label.setFont(font_contacts_empty)
        contacts_tab_layout.addWidget(self.contacts_empty_label)
        contacts_tab_layout.addWidget(self.contacts_table)

        contacts_pagination_layout = QHBoxLayout()
        self.prev_contact_button = QPushButton("<< Précédent")
        self.prev_contact_button.setObjectName("paginationButton")
        self.prev_contact_button.clicked.connect(self.prev_contact_page) # Method to be moved
        self.contact_page_info_label = QLabel("Page 1 / 1")
        self.contact_page_info_label.setObjectName("paginationLabel")
        self.next_contact_button = QPushButton("Suivant >>")
        self.next_contact_button.setObjectName("paginationButton")
        self.next_contact_button.clicked.connect(self.next_contact_page) # Method to be moved
        contacts_pagination_layout.addStretch()
        contacts_pagination_layout.addWidget(self.prev_contact_button)
        contacts_pagination_layout.addWidget(self.contact_page_info_label)
        contacts_pagination_layout.addWidget(self.next_contact_button)
        contacts_pagination_layout.addStretch()
        contacts_tab_layout.addLayout(contacts_pagination_layout)

        contacts_btn_layout = QHBoxLayout()
        self.add_contact_btn = QPushButton(self.tr("Ajouter")); self.add_contact_btn.setIcon(QIcon(":/icons/user-plus.svg"))
        self.add_contact_btn.setToolTip(self.tr("Ajouter un nouveau contact pour ce client")); self.add_contact_btn.clicked.connect(self.add_contact); contacts_btn_layout.addWidget(self.add_contact_btn) # Method to be moved
        self.edit_contact_btn = QPushButton(self.tr("Modifier")); self.edit_contact_btn.setIcon(QIcon(":/icons/pencil.svg"))
        self.edit_contact_btn.setToolTip(self.tr("Modifier le contact sélectionné")); self.edit_contact_btn.clicked.connect(self.edit_contact); contacts_btn_layout.addWidget(self.edit_contact_btn) # Method to be moved
        self.remove_contact_btn = QPushButton(self.tr("Supprimer")); self.remove_contact_btn.setIcon(QIcon(":/icons/trash.svg"))
        self.remove_contact_btn.setToolTip(self.tr("Supprimer le lien vers le contact sélectionné pour ce client")); self.remove_contact_btn.setObjectName("dangerButton"); self.remove_contact_btn.clicked.connect(self.remove_contact); contacts_btn_layout.addWidget(self.remove_contact_btn) # Method to be moved
        contacts_tab_layout.addLayout(contacts_btn_layout)

        self.internal_tabs.addTab(self.contacts_internal_tab_content, self.tr("Contacts"))

    def _setup_assignments_internal_tab(self):
        # This will be the content of the "Assignments" tab within internal_tabs
        # Eventually, this will instantiate ClientAssignmentsInternalTab
        self.assignments_internal_tab_content = QWidget() # Placeholder
        assignments_layout = QVBoxLayout(self.assignments_internal_tab_content)

        self.assignments_sub_tabs = QTabWidget()
        assignments_layout.addWidget(self.assignments_sub_tabs)

        # Sub-Tab: Assigned Vendors/Sellers
        # ... (Code for vendors sub-tab UI and logic - to be moved from ClientMainWidget)
        # Sub-Tab: Assigned Technicians
        # ... (Code for technicians sub-tab UI and logic)
        # Sub-Tab: Assigned Transporters
        # ... (Code for transporters sub-tab UI and logic)
        # Sub-Tab: Assigned Freight Forwarders
        # ... (Code for forwarders sub-tab UI and logic)
        # Sub-Tab: Money Transfer Agents
        # ... (Code for MTA sub-tab UI and logic)

        self.internal_tabs.addTab(self.assignments_internal_tab_content, self.tr("Affectations"))

    def _setup_email_internal_tab(self):
        # This will be the content of the "Envoyer Mail" tab within internal_tabs
        self.email_internal_tab_content = QWidget() # Placeholder
        email_layout = QVBoxLayout(self.email_internal_tab_content)
        self.open_email_dialog_btn_internal = QPushButton(self.tr("Composer un Email..."))
        self.open_email_dialog_btn_internal.setIcon(QIcon.fromTheme("mail-send", QIcon(":/icons/bell.svg")))
        self.open_email_dialog_btn_internal.clicked.connect(self.open_send_email_dialog) # Method to be potentially moved or adapted
        email_layout.addWidget(self.open_email_dialog_btn_internal)
        email_layout.addStretch()
        self.internal_tabs.addTab(self.email_internal_tab_content, self.tr("Envoyer Mail"))

    def _setup_whatsapp_internal_tab(self):
        # This will be the content of the "Send WhatsApp" tab within internal_tabs
        self.whatsapp_internal_tab_content = QWidget() # Placeholder
        whatsapp_layout = QVBoxLayout(self.whatsapp_internal_tab_content)
        self.open_whatsapp_dialog_btn_internal = QPushButton(self.tr("Envoyer message WhatsApp..."))
        # self.open_whatsapp_dialog_btn_internal.setIcon(QIcon.fromTheme("contact-new", QIcon(":/icons/user.svg"))) # Assuming user.svg is a placeholder
        self.open_whatsapp_dialog_btn_internal.setIcon(QIcon(":/icons/phone.svg")) # Example different icon
        self.open_whatsapp_dialog_btn_internal.clicked.connect(self.open_send_whatsapp_dialog) # Method to be potentially moved or adapted
        whatsapp_layout.addWidget(self.open_whatsapp_dialog_btn_internal)
        whatsapp_layout.addStretch()
        self.internal_tabs.addTab(self.whatsapp_internal_tab_content, self.tr("Send WhatsApp"))

    # --- Methods to be moved from ClientMainWidget (or their logic adapted) ---
    # populate_details_layout, switchTo_edit_client_view (partial), save_client_changes_from_edit_view (partial)
    # _populate_country_edit_combo, _populate_city_edit_combo
    # toggle_distributor_info_visibility, toggle_edit_distributor_info_visibility
    # load_contacts, add_contact, edit_contact, remove_contact, prev_contact_page, next_contact_page, update_contact_pagination_controls
    # All handle_add_assigned_*, handle_remove_assigned_*, update_assigned_*_buttons_state, load_assigned_* methods
    # open_send_email_dialog (for internal tab), open_send_whatsapp_dialog (for internal tab)
    # load_statuses, update_client_status (related to the status_combo in details tab)

    def populate_details_layout(self):
        # This method will now operate on self.project_id_value_label, self.country_value_label etc.
        # which are part of self.details_tab_content
        logging.info(f"ClientInfoSection: Populating details for {self.client_info.get('client_name')}")

        self.project_id_value_label.setText(self.client_info.get("project_identifier", self.tr("N/A")))
        self.country_value_label.setText(self.client_info.get("country", self.tr("N/A")))
        self.city_value_label.setText(self.client_info.get("city", self.tr("N/A")))
        self.price_value_label.setText(f"{self.client_info.get('price', 0)} €")
        self.date_value_label.setText(self.client_info.get("creation_date", self.tr("N/A")))

        # Status ComboBox
        current_status_text = self.client_info.get("status", self.tr("En cours"))
        # self.load_statuses() should be called here or before to populate self.status_combo
        if not self.main_widget.is_editing_client: # Only manage status_combo if not in edit mode here
            self.load_statuses() # Ensure combo is populated
            self.status_combo.setEnabled(False)
            status_idx = self.status_combo.findText(current_status_text)
            if status_idx != -1: self.status_combo.setCurrentIndex(status_idx)
            elif self.status_combo.count() > 0: self.status_combo.setCurrentIndex(0)
            # Connect signal if not already connected by main_widget's edit mode logic
            try: self.status_combo.currentTextChanged.disconnect(self.update_client_status)
            except TypeError: pass
            self.status_combo.currentTextChanged.connect(self.update_client_status)


        self.category_value_label.setText(self.client_info.get("category", self.tr("N/A")))
        self.toggle_distributor_info_visibility() # Updates visibility based on category

        self.need_value_label.setText(self.client_info.get("need", self.client_info.get("primary_need_description", self.tr("N/A"))))

        folder_path_value = self.client_info.get('base_folder_path') or self.client_info.get('default_base_folder_path', '')
        if folder_path_value and os.path.isdir(folder_path_value):
            self.folder_value_label.setText(f"<a href='file:///{folder_path_value}'>{folder_path_value}</a>")
        else:
            self.folder_value_label.setText(self.tr("N/A - Chemin non configuré"))

        created_by_user_id = self.client_info.get("created_by_user_id")
        created_by_user_name = self.tr("N/A")
        if created_by_user_id:
            user = self.users_crud.get_user_by_id(created_by_user_id)
            if user: created_by_user_name = user.get("full_name") or user.get("username", self.tr("Inconnu"))
            else: created_by_user_name = self.tr("Utilisateur Inconnu (ID: {0})").format(created_by_user_id)
        self.created_by_value_label.setText(created_by_user_name)

    def load_statuses(self):
        # This method is now part of ClientInfoSection and operates on self.status_combo
        # It's called by populate_details_layout (if not in edit mode) or by main_widget during edit mode setup.
        current_client_status_id = self.client_info.get("status_id")
        current_client_status_text = self.client_info.get("status")

        self.status_combo.blockSignals(True)
        self.status_combo.clear()
        try:
            client_statuses = db_manager.get_all_status_settings(type_filter='Client') or []
            for status_dict in client_statuses:
                status_name = status_dict.get('status_name', self.tr("Unnamed Status ({0})").format(status_dict.get('status_id')))
                self.status_combo.addItem(str(status_name), status_dict.get('status_id'))

            idx_to_set = -1
            if current_client_status_id is not None:
                idx_by_id = self.status_combo.findData(current_client_status_id)
                if idx_by_id != -1: idx_to_set = idx_by_id

            if idx_to_set == -1 and current_client_status_text:
                idx_by_text = self.status_combo.findText(current_client_status_text, Qt.MatchFixedString)
                if idx_by_text != -1: idx_to_set = idx_by_text

            if idx_to_set != -1: self.status_combo.setCurrentIndex(idx_to_set)
            elif self.status_combo.count() > 0: self.status_combo.setCurrentIndex(0)

        except Exception as e:
            logging.error(f"Error loading statuses in ClientInfoSection: {e}", exc_info=True)
        finally:
            self.status_combo.blockSignals(False)

    def update_client_status(self, status_text):
        # This method now belongs to ClientInfoSection
        # It needs to inform ClientMainWidget or directly call db_manager
        # For now, assume it calls db_manager and updates self.client_info
        # It will also need to handle the "Vendu" status logic
        # This is a simplified version, the full logic from ClientMainWidget needs to be adapted here.
        logging.info(f"ClientInfoSection: Attempting to update status to '{status_text}'")
        status_setting = db_manager.get_status_setting_by_name(status_text, 'Client')
        if status_setting and status_setting.get('status_id') is not None:
            status_id_to_set = status_setting['status_id']
            client_id_to_update = self.client_info.get("client_id")
            if client_id_to_update:
                 # Add "Vendu" logic here if necessary, or ensure main_widget handles it
                if db_manager.update_client(client_id_to_update, {'status_id': status_id_to_set}):
                    self.client_info["status"] = status_text
                    self.client_info["status_id"] = status_id_to_set
                    if self.notification_manager:
                        self.notification_manager.show(title=self.tr("Statut Mis à Jour"),
                                                       message=self.tr("Statut du client '{0}' mis à jour à '{1}'.").format(self.client_info.get("client_name", ""), status_text),
                                                       type='SUCCESS')
                    # Inform main_widget to update SAV tab visibility
                    if hasattr(self.main_widget, 'update_sav_tab_visibility'):
                        self.main_widget.update_sav_tab_visibility()
                else:
                    if self.notification_manager:
                        self.notification_manager.show(title=self.tr("Erreur Statut"), message=self.tr("Échec de la mise à jour du statut."), type='ERROR')

    def toggle_distributor_info_visibility(self):
        is_distributor = self.client_info.get('category') == 'Distributeur'
        self.distributor_info_label_static.setVisible(is_distributor)
        self.distributor_info_value_label.setVisible(is_distributor)
        if is_distributor:
            self.distributor_info_value_label.setText(self.client_info.get('distributor_specific_info', ''))

    # Placeholder for methods to be moved from ClientMainWidget related to internal tabs
    def load_contacts(self): pass # Will be in ClientContactsInternalTab
    def add_contact(self): pass
    def edit_contact(self, r=None, c=None): pass
    def remove_contact(self): pass
    def prev_contact_page(self): pass
    def next_contact_page(self): pass
    def update_contact_pagination_controls(self): pass

    def open_send_email_dialog(self): # For the internal email tab
        # Simplified, actual logic will be in ClientEmailInternalTab or here
        if self.SendEmailDialog:
            # Logic to get primary email of client
            primary_email = "" # Fetch appropriately
            dialog = self.SendEmailDialog(client_email=primary_email, config=self.config, client_id=self.client_info.get('client_id'), parent=self)
            dialog.exec_()

    def open_send_whatsapp_dialog(self): # For the internal WhatsApp tab
        if self.SendWhatsAppDialog:
            # Logic to get primary phone of client
            primary_phone = "" # Fetch appropriately
            dialog = self.SendWhatsAppDialog(phone_number=primary_phone, client_name=self.client_info.get('client_name',""), parent=self)
            dialog.exec_()

    def refresh_section_display(self, new_client_info):
        """Refreshes the display of this section with new client_info."""
        self.client_info = new_client_info
        # self.header_label.setText(f"<h2>{self.client_info.get('client_name', '')}</h2>") # If header is here
        self.populate_details_layout() # Repopulates the details tab

        # Refresh other internal tabs if they hold client-specific data that might change
        if hasattr(self, 'contacts_internal_tab_content') and hasattr(self.contacts_internal_tab_content, 'load_contacts'):
            self.contacts_internal_tab_content.load_contacts() # Assuming ClientContactsInternalTab has load_contacts

        if hasattr(self, 'assignments_internal_tab_content') and hasattr(self.assignments_internal_tab_content, 'refresh_assignments'):
            self.assignments_internal_tab_content.refresh_assignments() # Assuming ClientAssignmentsInternalTab has this

    # Edit mode related methods will also largely move here for the details part
    # switchTo_edit_client_view (partial), save_client_changes_from_edit_view (partial)
    # _populate_country_edit_combo, _populate_city_edit_combo
    # toggle_edit_distributor_info_visibility
    # (These will be added in subsequent steps)

    def tr(self, text, disambiguation=None, n=-1):
        if hasattr(self.main_widget, 'tr'):
            return self.main_widget.tr(text, disambiguation, n)
        return QApplication.translate("ClientInfoSection", text, disambiguation, n)

# Future: Define ClientDetailsTab, ClientContactsInternalTab, ClientAssignmentsInternalTab, etc.
# and instantiate them in _setup_details_tab, _setup_contacts_internal_tab, etc.
