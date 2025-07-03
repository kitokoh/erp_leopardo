# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QMessageBox, QApplication # QDialog removed
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

import db as db_manager
# SAVTicketDialog will be imported locally or passed if it's a shared component.
# For now, assume it might be imported locally if specific to SAV.
# from sav.ticket_dialog import SAVTicketDialog # Placeholder

class SAVTab(QWidget):
    def __init__(self, client_info: dict, current_user_info: dict,
                 notification_manager: object,
                 parent_widget: QWidget, # To access tr() and potentially main module dialogs
                 parent=None):
        super().__init__(parent)
        self.client_info = client_info
        self.current_user_info = current_user_info
        self.notification_manager = notification_manager
        self.parent_widget = parent_widget # For tr() and accessing shared dialogs

        # Attempt to import SAVTicketDialog dynamically or ensure it's passed
        self.SAVTicketDialog = None
        if hasattr(self.parent_widget, 'SAVTicketDialog'): # Check if parent (ClientMainWidget) has it
            self.SAVTicketDialog = self.parent_widget.SAVTicketDialog
        else:
            try:
                from sav.ticket_dialog import SAVTicketDialog as SAVTicketDialogModule
                self.SAVTicketDialog = SAVTicketDialogModule
                logging.info("SAVTab: SAVTicketDialog imported locally.")
            except ImportError:
                logging.error("SAVTab: Failed to import SAVTicketDialog locally and not found in parent.")
                # This state should be handled, perhaps by disabling features or showing an error.

        self.sav_tab_index = -1 # To store its own index if needed, though less relevant as a separate class

        self._setup_ui()
        self.update_sav_tab_visibility_and_load_data() # Initial setup and data load

    def tr(self, text, disambiguation=None, n=-1):
        if self.parent_widget:
            return self.parent_widget.tr(text, disambiguation, n)
        return QApplication.translate("SAVTab", text, disambiguation, n)

    def _setup_ui(self):
        logging.info("SAVTab._setup_ui: Starting setup...")
        self.main_sav_layout = QVBoxLayout(self) # Main layout for the tab

        # Placeholder for when SAV is not applicable
        self.placeholder_label = QLabel(self.tr("La section SAV n'est pas applicable pour le statut actuel de ce client."))
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.main_sav_layout.addWidget(self.placeholder_label)

        # Container for actual SAV content (initially hidden)
        self.sav_content_widget = QWidget()
        sav_content_layout = QVBoxLayout(self.sav_content_widget)
        sav_content_layout.setContentsMargins(0,0,0,0)

        sav_content_layout.addWidget(QLabel("<h3>" + self.tr("Historique des Achats") + "</h3>"))
        self.purchase_history_table = QTableWidget()
        self.purchase_history_table.setColumnCount(6) # ID CPP (Hidden), Produit, Quantité, Numéro de Série, Date d'Achat, Actions
        self.purchase_history_table.setHorizontalHeaderLabels([
            self.tr("ID CPP (Hidden)"), self.tr("Produit"), self.tr("Quantité"),
            self.tr("Numéro de Série"), self.tr("Date d'Achat"), self.tr("Actions")
        ])
        self.purchase_history_table.setColumnHidden(0, True)
        self.purchase_history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.purchase_history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.purchase_history_table.itemChanged.connect(self.handle_purchase_history_item_changed)
        sav_content_layout.addWidget(self.purchase_history_table)

        self.refresh_purchase_history_btn = QPushButton(self.tr("Rafraîchir l'historique"))
        self.refresh_purchase_history_btn.setIcon(QIcon.fromTheme("view-refresh"))
        self.refresh_purchase_history_btn.clicked.connect(self.load_purchase_history_table)
        sav_content_layout.addWidget(self.refresh_purchase_history_btn)

        # SAV Tickets Section
        sav_content_layout.addWidget(QLabel("<h3>" + self.tr("Tickets SAV") + "</h3>"))
        self.sav_tickets_table = QTableWidget()
        self.sav_tickets_table.setColumnCount(7) # ID (Hidden), Produit, Description, Statut, Ouvert le, Technicien, Actions
        self.sav_tickets_table.setHorizontalHeaderLabels([
            self.tr("ID Ticket (Hidden)"), self.tr("Produit Concerné"), self.tr("Description Problème"),
            self.tr("Statut"), self.tr("Date Ouverture"), self.tr("Technicien Assigné"), self.tr("Actions")
        ])
        self.sav_tickets_table.setColumnHidden(0, True)
        self.sav_tickets_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.sav_tickets_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.sav_tickets_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sav_tickets_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        sav_content_layout.addWidget(self.sav_tickets_table)

        sav_tickets_buttons_layout = QHBoxLayout()
        self.add_sav_ticket_btn = QPushButton(self.tr("Nouveau Ticket SAV"))
        self.add_sav_ticket_btn.setIcon(QIcon.fromTheme("document-new"))
        self.add_sav_ticket_btn.clicked.connect(self.open_new_sav_ticket_dialog)
        sav_tickets_buttons_layout.addWidget(self.add_sav_ticket_btn)
        sav_tickets_buttons_layout.addStretch()
        sav_content_layout.addLayout(sav_tickets_buttons_layout)

        sav_content_layout.addStretch()
        self.main_sav_layout.addWidget(self.sav_content_widget)
        self.sav_content_widget.hide() # Initially hidden

    def update_sav_tab_visibility_and_load_data(self):
        client_status_id = self.client_info.get('status_id')
        vendu_status_info = None
        try:
            vendu_status_info = db_manager.get_status_setting_by_name('Vendu', 'Client')
        except Exception as e_db_status:
            logging.error(f"SAVTab: Error fetching 'Vendu' status: {e_db_status}", exc_info=True)

        is_client_vendu = False
        if vendu_status_info and client_status_id == vendu_status_info.get('status_id'):
            is_client_vendu = True

        if is_client_vendu:
            self.placeholder_label.hide()
            self.sav_content_widget.show()
            self.load_purchase_history_table()
            self.load_sav_tickets_table()
            # Enable the tab in the parent QTabWidget if reference is available
            if self.parent_widget and hasattr(self.parent_widget, 'tab_widget'):
                idx = self.parent_widget.tab_widget.indexOf(self)
                if idx != -1: self.parent_widget.tab_widget.setTabEnabled(idx, True)
        else:
            self.placeholder_label.show()
            self.sav_content_widget.hide()
            # Disable the tab in the parent QTabWidget
            if self.parent_widget and hasattr(self.parent_widget, 'tab_widget'):
                idx = self.parent_widget.tab_widget.indexOf(self)
                if idx != -1: self.parent_widget.tab_widget.setTabEnabled(idx, False)

        # Apply specific permissions if any (e.g. for add_sav_ticket_btn)
        self.apply_permissions_to_tab()


    def load_purchase_history_table(self):
        self.purchase_history_table.setRowCount(0)
        client_id = self.client_info.get('client_id')
        if not client_id: return
        try:
            # This needs a new DB function: get_client_purchase_history(client_id)
            # It should return products linked to this client that are considered "purchased"
            # (e.g., linked via a confirmed order or have a purchase_confirmed_at date).
            # For now, using get_products_for_client_or_project as a placeholder,
            # but this will need refinement based on actual DB schema for purchases.
            # It should include client_project_product_id, product_name, quantity, serial_number, purchase_date

            # Placeholder - replace with actual DB call
            # purchased_products = db_manager.get_client_purchase_history(client_id) or []
            purchased_products = [] # Actual DB call needed
            # Example structure: [{'client_project_product_id': 1, 'product_name': 'Prod A', 'quantity': 2, 'serial_number': 'SN123', 'purchase_date': '2023-01-01'}]


            # Temporarily using get_products_for_client_or_project for structure, but this is not correct for purchase history
            temp_products = db_manager.get_products_for_client_or_project(client_id, project_id=None) or []
            for prod in temp_products:
                # This is a HACK - needs proper purchase data
                if prod.get('purchase_confirmed_at'): # Or some other indicator of purchase
                     purchased_products.append({
                         'client_project_product_id': prod.get('client_project_product_id'),
                         'product_name': prod.get('product_name'),
                         'quantity': prod.get('quantity'),
                         'serial_number': prod.get('serial_number', ''), # Assuming serial_number is on client_project_products
                         'purchase_date': prod.get('purchase_confirmed_at') # Or a specific purchase_date
                     })


            self.purchase_history_table.setRowCount(len(purchased_products))
            for row, item in enumerate(purchased_products):
                cpp_id_item = QTableWidgetItem(str(item.get('client_project_product_id')))
                cpp_id_item.setData(Qt.UserRole, item.get('client_project_product_id'))
                self.purchase_history_table.setItem(row, 0, cpp_id_item) # Hidden
                self.purchase_history_table.setItem(row, 1, QTableWidgetItem(item.get('product_name')))
                self.purchase_history_table.setItem(row, 2, QTableWidgetItem(str(item.get('quantity'))))

                sn_item = QTableWidgetItem(item.get('serial_number', ''))
                # Make serial number editable
                sn_item.setFlags(sn_item.flags() | Qt.ItemIsEditable)
                self.purchase_history_table.setItem(row, 3, sn_item)

                purchase_date_str = item.get('purchase_date', '')
                date_display = ""
                if purchase_date_str:
                    try:
                        dt_obj = datetime.fromisoformat(str(purchase_date_str).replace('Z', '+00:00'))
                        date_display = dt_obj.strftime('%Y-%m-%d')
                    except ValueError: date_display = str(purchase_date_str)
                self.purchase_history_table.setItem(row, 4, QTableWidgetItem(date_display))
                # Actions (e.g., link to SAV ticket for this item) - Placeholder
                # actions_widget = QWidget(); QHBoxLayout(actions_widget) # ...
                # self.purchase_history_table.setCellWidget(row, 5, actions_widget)

        except Exception as e:
            logging.error(f"Error loading purchase history: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Impossible de charger l'historique des achats."))

    def handle_purchase_history_item_changed(self, item: QTableWidgetItem):
        if item.column() == 3: # Serial Number column
            cpp_id = self.purchase_history_table.item(item.row(), 0).data(Qt.UserRole)
            new_serial_number = item.text().strip()
            try:
                # This DB function needs to be created:
                # db_manager.update_client_project_product_serial_number(cpp_id, new_serial_number)
                logging.info(f"SAVTab: Serial number for CPP ID {cpp_id} changed to '{new_serial_number}' (DB update pending implementation).")
                # For now, just log. Actual DB update required.
                # Example:
                # if db_manager.update_client_project_product_serial_number(cpp_id, new_serial_number):
                #     if self.notification_manager: self.notification_manager.show("Succès", "Numéro de série mis à jour.", type="SUCCESS")
                # else:
                #     QMessageBox.warning(self, "Erreur DB", "Échec de la mise à jour du numéro de série.")
                #     self.load_purchase_history_table() # Revert
            except Exception as e:
                logging.error(f"Error updating serial number for CPP ID {cpp_id}: {e}", exc_info=True)
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("Échec de la mise à jour."))
                self.load_purchase_history_table() # Revert on error

    def load_sav_tickets_table(self):
        # (Implementation is similar to ClientMainWidget's version, adapted for SAVTab class)
        # ... (Ensure self.sav_tickets_table exists)
        # ... (Fetch tickets using db_manager.get_sav_tickets_for_client(client_id))
        # ... (Populate self.sav_tickets_table)
        # ... (Connect view/edit buttons to self.view_edit_sav_ticket_dialog)
        pass # Placeholder - full implementation to be added

    def open_new_sav_ticket_dialog(self):
        if not self.SAVTicketDialog:
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Dialogue de ticket SAV non chargé."))
            return
        # ... (rest of the logic from ClientMainWidget.open_new_sav_ticket_dialog, adapted)
        pass # Placeholder

    def view_edit_sav_ticket_dialog(self, ticket_id):
        if not self.SAVTicketDialog:
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Dialogue de ticket SAV non chargé."))
            return
        # ... (rest of the logic from ClientMainWidget.view_edit_sav_ticket_dialog, adapted)
        pass # Placeholder

    def apply_permissions_to_tab(self):
        # Example: if adding SAV tickets has a specific permission
        # role_name = self.current_user_info.get('role_name')
        # can_add_sav_ticket = has_permission(role_name, P_ADD_SAV_TICKET) # Define this permission
        # self.add_sav_ticket_btn.setEnabled(can_add_sav_ticket)
        pass # For now, visibility is controlled by client status 'Vendu'

    def refresh_tab_data(self):
        self.update_sav_tab_visibility_and_load_data()

# ```
