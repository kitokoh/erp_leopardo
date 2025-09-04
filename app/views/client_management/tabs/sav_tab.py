# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QMessageBox, QApplication,
    QGroupBox, QDialog
)
from PyQt5.QtCore import Qt, QLocale, QDate, QDateTime

from app.db.connection import get_db_connection
from app.db.cruds.misc.status_settings_crud import get_status_setting_by_name
from app.db.cruds.clients.sav_crud import (
    get_client_purchase_history, get_sav_tickets_for_client, get_sav_ticket_by_id,
    update_client_project_product_serial_number
)
from app.services.auth.permissions import has_permission, P_MANAGE_CLIENT_DOCUMENTS

class SAVTab(QWidget):
    def __init__(self, client_info: dict, current_user_info: dict,
                 notification_manager: object,
                 parent_widget: QWidget,
                 parent=None):
        super().__init__(parent)
        self.client_info = client_info
        self.current_user_info = current_user_info
        self.notification_manager = notification_manager
        self.parent_widget = parent_widget
        self.SAVTicketDialog = None
        try:
            from app.sav.ticket_dialog import SAVTicketDialog as SAVTicketDialogModule
            self.SAVTicketDialog = SAVTicketDialogModule
        except ImportError:
            logging.error("SAVTab: Failed to import SAVTicketDialog.")

        self._setup_ui()
        self.update_sav_tab_visibility_and_load_data()

    def tr(self, text, disambiguation=None, n=-1):
        # ... (same as original)
        return self.parent_widget.tr(text, disambiguation, n) if self.parent_widget else text

    def _setup_ui(self):
        # ... (UI setup code remains the same) ...
        pass

    def update_sav_tab_visibility_and_load_data(self):
        client_status_id = self.client_info.get('status_id')
        vendu_status_info = None
        db_session = None
        try:
            db_session = get_db_connection()
            vendu_status_info = get_status_setting_by_name(db_session, 'Vendu', 'Client')
        except Exception as e:
            logging.error(f"SAVTab: Error fetching 'Vendu' status: {e}", exc_info=True)
        finally:
            if db_session:
                db_session.close()

        is_client_vendu = bool(vendu_status_info and client_status_id == vendu_status_info.get('status_id'))

        if is_client_vendu:
            self.placeholder_label.hide()
            self.sav_content_widget.show()
            self.load_purchase_history_table()
            self.load_sav_tickets_table()
        else:
            self.placeholder_label.show()
            self.sav_content_widget.hide()

        self.apply_permissions_to_tab()

    def load_purchase_history_table(self):
        self.purchase_history_table.setRowCount(0)
        client_id = self.client_info.get('client_id')
        if not client_id: return

        db_session = None
        try:
            db_session = get_db_connection()
            purchased_products = get_client_purchase_history(db_session, client_id) or []
            # ... (UI population logic remains the same) ...
        except Exception as e:
            logging.error(f"Error loading purchase history for client {client_id}: {e}", exc_info=True)
        finally:
            if db_session:
                db_session.close()

    def handle_purchase_history_item_changed(self, item: QTableWidgetItem):
        if item.column() != 3: return # Only handle serial number column
        cpp_id = self.purchase_history_table.item(item.row(), 0).data(Qt.UserRole)
        new_serial_number = item.text().strip()

        db_session = None
        try:
            db_session = get_db_connection()
            if update_client_project_product_serial_number(db_session, cpp_id, new_serial_number):
                self.notification_manager.show("Succès", "Numéro de série mis à jour.", type="SUCCESS")
            else:
                QMessageBox.warning(self, "Erreur DB", "Échec de la mise à jour.")
                self.load_purchase_history_table() # Revert
        except Exception as e:
            logging.error(f"Error updating serial number for CPP ID {cpp_id}: {e}", exc_info=True)
            self.load_purchase_history_table() # Revert on error
        finally:
            if db_session:
                db_session.close()

    def load_sav_tickets_table(self):
        self.sav_tickets_table.setRowCount(0)
        client_id = self.client_info.get('client_id')
        if not client_id: return

        db_session = None
        try:
            db_session = get_db_connection()
            tickets = get_sav_tickets_for_client(db_session, client_id) or []
            # ... (UI population logic remains the same) ...
        except Exception as e:
            logging.error(f"Error loading SAV tickets for client {client_id}: {e}", exc_info=True)
        finally:
            if db_session:
                db_session.close()

    def open_new_sav_ticket_dialog(self, client_project_product_id=None):
        if not self.SAVTicketDialog: return
        client_id = self.client_info.get('client_id')
        if not client_id: return

        db_session = None
        try:
            db_session = get_db_connection()
            purchased_items = get_client_purchase_history(db_session, client_id) or []
            formatted_items = [{'name': item.get('product_name', 'N/A'), 'client_project_product_id': item.get('client_project_product_id')} for item in purchased_items]

            dialog = self.SAVTicketDialog(client_id=client_id, purchased_products=formatted_items, ticket_data=None, selected_client_project_product_id=client_project_product_id, parent=self)
            if dialog.exec_() == QDialog.Accepted:
                self.load_sav_tickets_table()
                self.notification_manager.show("Succès", "Nouveau ticket SAV créé.", type='SUCCESS')
        except Exception as e:
            logging.error(f"Error opening new SAV ticket dialog: {e}", exc_info=True)
        finally:
            if db_session:
                db_session.close()

    def view_edit_sav_ticket_dialog(self, ticket_id):
        if not self.SAVTicketDialog: return
        client_id = self.client_info.get('client_id')
        if not client_id: return

        db_session = None
        try:
            db_session = get_db_connection()
            ticket_data = get_sav_ticket_by_id(db_session, ticket_id)
            if not ticket_data:
                QMessageBox.warning(self, "Erreur", f"Ticket SAV (ID: {ticket_id}) non trouvé.")
                return

            purchased_items = get_client_purchase_history(db_session, client_id) or []
            formatted_items = [{'name': item.get('product_name', 'N/A'), 'client_project_product_id': item.get('client_project_product_id')} for item in purchased_items]

            dialog = self.SAVTicketDialog(client_id=client_id, purchased_products=formatted_items, ticket_data=ticket_data, selected_client_project_product_id=ticket_data.get('client_project_product_id'), parent=self)
            if dialog.exec_() == QDialog.Accepted:
                self.load_sav_tickets_table()
                self.notification_manager.show("Succès", "Ticket SAV mis à jour.", type='SUCCESS')
        except Exception as e:
            logging.error(f"Error opening edit SAV ticket dialog: {e}", exc_info=True)
        finally:
            if db_session:
                db_session.close()

    def apply_permissions_to_tab(self):
        # No DB calls here
        pass

    def refresh_tab_data(self):
        self.update_sav_tab_visibility_and_load_data()
