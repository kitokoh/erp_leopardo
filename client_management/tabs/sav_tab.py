# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QMessageBox, QApplication
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QLocale, QDate # Added QLocale, QDate

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
        self.main_sav_layout = QVBoxLayout(self)
        self.main_sav_layout.setSpacing(10)
        self.main_sav_layout.setContentsMargins(5, 5, 5, 5)

        self.placeholder_label = QLabel(self.tr("La section SAV n'est pas applicable pour le statut actuel de ce client (doit être 'Vendu')."))
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet("font-style: italic; color: #718096; font-size: 10pt; padding: 20px;")
        self.main_sav_layout.addWidget(self.placeholder_label)

        self.sav_content_widget = QWidget()
        sav_content_layout = QVBoxLayout(self.sav_content_widget)
        sav_content_layout.setContentsMargins(0,0,0,0)
        sav_content_layout.setSpacing(10)

        header_style = """
            QHeaderView::section {
                background-color: #4a5568; color: white; padding: 6px;
                border: 1px solid #ddd; font-weight: bold; font-size: 9pt;
            }
        """

        # Purchase History Section
        purchase_group = QGroupBox(self.tr("Historique des Achats et Numéros de Série"))
        purchase_group_layout = QVBoxLayout(purchase_group)

        self.purchase_history_table = QTableWidget()
        self.purchase_history_table.setObjectName("purchaseHistoryTable")
        self.purchase_history_table.setColumnCount(6)
        self.purchase_history_table.setHorizontalHeaderLabels([
            self.tr("ID CPP (Hidden)"), self.tr("Produit Acheté"), self.tr("Quantité"),
            self.tr("Numéro de Série"), self.tr("Date d'Achat"), self.tr("Ouvrir Ticket")
        ])
        self.purchase_history_table.setColumnHidden(0, True)
        self.purchase_history_table.horizontalHeader().setStyleSheet(header_style)
        self.purchase_history_table.verticalHeader().setVisible(False)
        self.purchase_history_table.setAlternatingRowColors(True)
        self.purchase_history_table.setSortingEnabled(True)
        self.purchase_history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.purchase_history_table.itemChanged.connect(self.handle_purchase_history_item_changed) # For serial number edit

        self.purchase_history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch) # Produit
        self.purchase_history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents) # Quantité
        self.purchase_history_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Interactive) # Numéro de Série (Editable)
        self.purchase_history_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents) # Date d'Achat
        self.purchase_history_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents) # Actions (Ouvrir Ticket)
        self.purchase_history_table.setColumnWidth(3, 150) # Initial width for Serial Number

        purchase_group_layout.addWidget(self.purchase_history_table)

        self.refresh_purchase_history_btn = QPushButton(QIcon(":/icons/refresh-cw.svg"), self.tr("Actualiser Historique"))
        self.refresh_purchase_history_btn.setObjectName("secondaryButton")
        self.refresh_purchase_history_btn.clicked.connect(self.load_purchase_history_table)
        purchase_group_layout.addWidget(self.refresh_purchase_history_btn, 0, Qt.AlignRight)
        sav_content_layout.addWidget(purchase_group)


        # SAV Tickets Section
        tickets_group = QGroupBox(self.tr("Tickets SAV Associés au Client"))
        tickets_group_layout = QVBoxLayout(tickets_group)

        self.sav_tickets_table = QTableWidget()
        self.sav_tickets_table.setObjectName("savTicketsTable")
        self.sav_tickets_table.setColumnCount(7)
        self.sav_tickets_table.setHorizontalHeaderLabels([
            self.tr("ID Ticket (Hidden)"), self.tr("Produit Concerné"), self.tr("Description Problème"),
            self.tr("Statut"), self.tr("Date Ouverture"), self.tr("Technicien"), self.tr("Actions")
        ])
        self.sav_tickets_table.setColumnHidden(0, True)
        self.sav_tickets_table.horizontalHeader().setStyleSheet(header_style)
        self.sav_tickets_table.verticalHeader().setVisible(False)
        self.sav_tickets_table.setAlternatingRowColors(True)
        self.sav_tickets_table.setSortingEnabled(True)
        self.sav_tickets_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sav_tickets_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.sav_tickets_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents) # Produit
        self.sav_tickets_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch) # Description
        self.sav_tickets_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents) # Statut
        self.sav_tickets_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents) # Date Ouverture
        self.sav_tickets_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents) # Technicien
        self.sav_tickets_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents) # Actions
        tickets_group_layout.addWidget(self.sav_tickets_table)

        sav_tickets_buttons_layout = QHBoxLayout()
        self.add_sav_ticket_btn = QPushButton(QIcon(":/icons/plus-circle.svg"), self.tr("Nouveau Ticket SAV (Général)"))
        self.add_sav_ticket_btn.setObjectName("primaryButton")
        self.add_sav_ticket_btn.setToolTip(self.tr("Ouvrir un nouveau ticket SAV non lié à un achat spécifique de l'historique"))
        self.add_sav_ticket_btn.clicked.connect(lambda: self.open_new_sav_ticket_dialog(client_project_product_id=None)) # General ticket
        sav_tickets_buttons_layout.addStretch()
        sav_tickets_buttons_layout.addWidget(self.add_sav_ticket_btn)
        tickets_group_layout.addLayout(sav_tickets_buttons_layout)
        sav_content_layout.addWidget(tickets_group)

        sav_content_layout.addStretch()
        self.main_sav_layout.addWidget(self.sav_content_widget)
        self.sav_content_widget.hide()

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
            purchased_products = db_manager.get_client_purchase_history(client_id) or []

            if not purchased_products:
                self.purchase_history_table.hide() # Keep hidden if no data
                # Optionally, show a specific label for no purchase history if different from general SAV placeholder
            else:
                self.purchase_history_table.show()
                self.purchase_history_table.setRowCount(len(purchased_products))
                for row, item in enumerate(purchased_products):
                    cpp_id = item.get('client_project_product_id')
                    cpp_id_item = QTableWidgetItem(str(cpp_id))
                    cpp_id_item.setData(Qt.UserRole, cpp_id)
                    self.purchase_history_table.setItem(row, 0, cpp_id_item) # Hidden

                    self.purchase_history_table.setItem(row, 1, QTableWidgetItem(item.get('product_name', self.tr('N/A'))))
                    self.purchase_history_table.setItem(row, 2, QTableWidgetItem(str(item.get('quantity', '0'))))

                    sn_item = QTableWidgetItem(item.get('serial_number', ''))
                    sn_item.setFlags(sn_item.flags() | Qt.ItemIsEditable) # Serial number is editable
                    self.purchase_history_table.setItem(row, 3, sn_item)

                    purchase_date_str = item.get('purchase_date', '')
                    date_display = self.tr("N/A")
                    if purchase_date_str:
                        locale = QLocale()
                        # Attempt to parse as ISO date (common from DB) then format
                        q_date = QDate.fromString(str(purchase_date_str).split('T')[0], Qt.ISODate)
                        if q_date.isValid():
                            date_display = locale.toString(q_date, QLocale.ShortFormat)
                        else: # Fallback if not ISO or parsing fails
                            try: # Try parsing with datetime for more complex ISO (with Z)
                                dt_obj = datetime.fromisoformat(str(purchase_date_str).replace('Z', '+00:00'))
                                q_date_from_dt = QDate(dt_obj.year, dt_obj.month, dt_obj.day)
                                date_display = locale.toString(q_date_from_dt, QLocale.ShortFormat)
                            except ValueError:
                                date_display = str(purchase_date_str).split('T')[0] # Last resort: show date part as is
                    self.purchase_history_table.setItem(row, 4, QTableWidgetItem(date_display))

                    # Actions: Button to open new SAV ticket for this specific item
                    actions_widget = QWidget()
                    actions_layout = QHBoxLayout(actions_widget)
                    actions_layout.setContentsMargins(0,0,0,0)
                    actions_layout.setSpacing(5)

                    open_ticket_btn = QPushButton(QIcon(":/icons/file-plus.svg"), "") # Using file-plus for "new ticket"
                    open_ticket_btn.setToolTip(self.tr("Ouvrir un ticket SAV pour ce produit/achat"))
                    open_ticket_btn.setProperty("class", "tableActionButton")
                    open_ticket_btn.clicked.connect(lambda checked, c=cpp_id: self.open_new_sav_ticket_dialog(client_project_product_id=c))
                    actions_layout.addWidget(open_ticket_btn)
                    actions_layout.addStretch()
                    self.purchase_history_table.setCellWidget(row, 5, actions_widget)
                self.purchase_history_table.resizeRowsToContents()

        except Exception as e:
            logging.error(f"Error loading purchase history for client {client_id}: {e}", exc_info=True)
            if self.notification_manager:
                self.notification_manager.show_notification(
                    self.tr("Erreur Historique Achats"),
                    self.tr("Impossible de charger l'historique des achats. Détails: {0}").format(str(e)),
                    'ERROR'
                )
            else:
                QMessageBox.critical(self, self.tr("Erreur"), self.tr("Impossible de charger l'historique des achats."))
            # Optionally, display an error message in the table area or a label

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
        self.sav_tickets_table.setRowCount(0)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        client_id = self.client_info.get('client_id')
        if not client_id:
            QApplication.restoreOverrideCursor()
            return
        try:
            tickets = db_manager.get_sav_tickets_for_client(client_id)
            if tickets is None: tickets = [] # Ensure tickets is an iterable

            self.sav_tickets_table.setRowCount(len(tickets))
            for row_idx, ticket in enumerate(tickets):
                ticket_id = ticket.get('ticket_id')

                id_item = QTableWidgetItem(str(ticket_id)) # For internal use if needed, though column is hidden
                id_item.setData(Qt.UserRole, ticket_id)
                self.sav_tickets_table.setItem(row_idx, 0, id_item) # Hidden column

                # Use pre-joined data from get_sav_tickets_for_client
                product_name_display = ticket.get('linked_product_name', self.tr("N/A (Ticket Général)"))
                self.sav_tickets_table.setItem(row_idx, 1, QTableWidgetItem(product_name_display))

                issue_desc = ticket.get('issue_description', '')
                self.sav_tickets_table.setItem(row_idx, 2, QTableWidgetItem(issue_desc[:100] + ('...' if len(issue_desc) > 100 else '')))

                status_name = ticket.get('status_name', self.tr("Statut Inconnu"))
                self.sav_tickets_table.setItem(row_idx, 3, QTableWidgetItem(status_name))

                opened_at_str = ticket.get('opened_at', '')
                opened_at_display = self.tr('N/A')
                if opened_at_str:
                    locale = QLocale()
                    try:
                        # QDateTime can parse ISO strings directly
                        q_datetime = QDateTime.fromString(opened_at_str, Qt.ISODate)
                        if not q_datetime.isValid(): # Try with explicit timezone
                             q_datetime = QDateTime.fromString(opened_at_str.replace('Z', '+00:00'), Qt.ISODate)

                        if q_datetime.isValid():
                            opened_at_display = locale.toString(q_datetime, QLocale.ShortFormat)
                        else: # Fallback for Python's datetime if QDateTime fails
                            dt_obj = datetime.fromisoformat(opened_at_str.replace('Z', '+00:00'))
                            q_dt_from_py = QDateTime(dt_obj.year, dt_obj.month, dt_obj.day, dt_obj.hour, dt_obj.minute, dt_obj.second, Qt.UTC)
                            opened_at_display = locale.toString(q_dt_from_py.toLocalTime(), QLocale.ShortFormat)
                    except ValueError:
                        opened_at_display = opened_at_str # Show raw if all parsing fails
                self.sav_tickets_table.setItem(row_idx, 4, QTableWidgetItem(opened_at_display))

                tech_name = ticket.get('technician_name', self.tr("Non assigné"))
                self.sav_tickets_table.setItem(row_idx, 5, QTableWidgetItem(tech_name))

                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0,0,0,0); actions_layout.setSpacing(5)

                view_edit_button = QPushButton(QIcon(":/icons/edit-2.svg"), "") # Or eye.svg
                view_edit_button.setToolTip(self.tr("Voir/Modifier Ticket SAV"))
                view_edit_button.setProperty("class", "tableActionButton")
                view_edit_button.clicked.connect(lambda checked, t_id=ticket_id: self.view_edit_sav_ticket_dialog(t_id))
                actions_layout.addWidget(view_edit_button)
                actions_layout.addStretch()
                self.sav_tickets_table.setCellWidget(row_idx, 6, actions_widget)

            self.sav_tickets_table.resizeRowsToContents()

        except Exception as e:
            logging.error(f"Error loading SAV tickets for client {client_id}: {e}", exc_info=True)
            if self.notification_manager:
                self.notification_manager.show_notification(
                    self.tr("Erreur Chargement Tickets"),
                    self.tr("Impossible de charger la liste des tickets SAV. Détails: {0}").format(str(e)),
                    'ERROR'
                )
            else:
                QMessageBox.critical(self, self.tr("Erreur"), self.tr("Impossible de charger les tickets SAV: {0}").format(str(e)))
            # Optionally, display an error message in the SAV tickets table area
        finally:
            QApplication.restoreOverrideCursor()


    def open_new_sav_ticket_dialog(self, client_project_product_id=None): # Added param
        if not self.SAVTicketDialog:
            QMessageBox.critical(self, self.tr("Erreur Composant"), self.tr("Le dialogue de ticket SAV n'est pas correctement chargé."))
            return

        client_id = self.client_info.get('client_id')
        if not client_id:
            QMessageBox.warning(self, self.tr("Erreur Client"), self.tr("ID Client non disponible pour créer un ticket SAV."))
            return

        # Fetch purchased items for the dialog's dropdown, regardless of whether this ticket is for a specific one
        # This list is used by SAVTicketDialog to populate its "Product" dropdown.
        try:
            # Assuming get_client_purchase_history returns items suitable for the dropdown
            # Each item should ideally have 'client_project_product_id' and a display 'name'
            purchased_items_for_dialog = db_manager.get_client_purchase_history(client_id) or []
            # Reformat if necessary for SAVTicketDialog's expected 'purchased_products' structure
            # SAVTicketDialog expects list of dicts with 'name' and 'client_project_product_id'
            formatted_purchased_items = [
                {'name': item.get('product_name', 'N/A'), 'client_project_product_id': item.get('client_project_product_id')}
                for item in purchased_items_for_dialog
            ]

        except Exception as e:
            logging.error(f"Error fetching purchased items for SAV dialog: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur Données"), self.tr("Impossible de charger l'historique des achats pour le dialogue SAV."))
            formatted_purchased_items = [] # Proceed with empty list if fetch fails

        dialog = self.SAVTicketDialog(
            client_id=client_id,
            purchased_products=formatted_purchased_items,
            ticket_data=None, # New ticket
            # If client_project_product_id is provided, SAVTicketDialog should pre-select it
            selected_client_project_product_id=client_project_product_id,
            parent=self
        )
        if dialog.exec_() == QDialog.Accepted:
            self.load_sav_tickets_table() # Refresh the list of tickets
            if self.notification_manager:
                self.notification_manager.show(self.tr("Succès"), self.tr("Nouveau ticket SAV créé."), type='SUCCESS')


    def view_edit_sav_ticket_dialog(self, ticket_id):
        if not self.SAVTicketDialog:
            QMessageBox.critical(self, self.tr("Erreur Composant"), self.tr("Le dialogue de ticket SAV n'est pas correctement chargé."))
            return

        client_id = self.client_info.get('client_id') # Needed for context, e.g. fetching purchased items for dialog
        if not client_id:
             QMessageBox.warning(self, self.tr("Erreur Client"), self.tr("ID Client non disponible."))
             return

        ticket_data = db_manager.get_sav_ticket_by_id(ticket_id) # This DB function needs to exist
        if not ticket_data:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Ticket SAV (ID: {0}) non trouvé.").format(ticket_id))
            return

        try:
            purchased_items_for_dialog = db_manager.get_client_purchase_history(client_id) or []
            formatted_purchased_items = [
                {'name': item.get('product_name', 'N/A'), 'client_project_product_id': item.get('client_project_product_id')}
                for item in purchased_items_for_dialog
            ]
        except Exception as e:
            logging.error(f"Error fetching purchased items for SAV dialog (edit mode): {e}", exc_info=True)
            formatted_purchased_items = []


        dialog = self.SAVTicketDialog(
            client_id=client_id,
            purchased_products=formatted_purchased_items, # For the dropdown
            ticket_data=ticket_data, # Existing ticket data to populate fields
            selected_client_project_product_id=ticket_data.get('client_project_product_id'), # Pre-select linked product
            parent=self
        )
        if dialog.exec_() == QDialog.Accepted:
            self.load_sav_tickets_table()
            if self.notification_manager:
                 self.notification_manager.show(self.tr("Succès"), self.tr("Ticket SAV mis à jour."), type='SUCCESS')


    def apply_permissions_to_tab(self):
        # Example: if adding SAV tickets has a specific permission
        # from auth.permissions import P_MANAGE_SAV_TICKETS # Define this permission constant
        can_manage_sav = False
        if hasattr(self.parent_widget, 'current_user_info'):
            role_name = self.parent_widget.current_user_info.get('role_name')
            if role_name:
                # Use a placeholder permission for now, replace with actual P_MANAGE_SAV_TICKETS
                can_manage_sav = has_permission(role_name, P_MANAGE_CLIENT_DOCUMENTS)

        self.add_sav_ticket_btn.setEnabled(can_manage_sav)
        self.refresh_purchase_history_btn.setEnabled(can_manage_sav) # Or a view permission
        # Permissions for inline actions in tables are handled during table population
        # based on 'can_manage_sav' or similar logic.
        # We might need to re-populate tables if permissions change dynamically,
        # but for now, this is set on tab load.
        self.load_purchase_history_table() # Reload to apply action button visibility if needed
        self.load_sav_tickets_table()      # Reload to apply action button visibility if needed
        # role_name = self.current_user_info.get('role_name')
        # can_add_sav_ticket = has_permission(role_name, P_ADD_SAV_TICKET) # Define this permission
        # self.add_sav_ticket_btn.setEnabled(can_add_sav_ticket)
        pass # For now, visibility is controlled by client status 'Vendu'

    def refresh_tab_data(self):
        self.update_sav_tab_visibility_and_load_data()


