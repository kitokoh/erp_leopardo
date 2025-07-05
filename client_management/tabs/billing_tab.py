# -*- coding: utf-8 -*-
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QMessageBox, QApplication # QDialog removed
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

import db as db_manager
from invoicing.final_invoice_data_dialog import FinalInvoiceDataDialog
from utils.document_manager_logic import create_final_invoice_and_update_db # Assuming this handles PDF generation & DB update
from auth.permissions import has_permission, P_MANAGE_CLIENT_BILLING

class BillingTab(QWidget):
    def __init__(self, client_info: dict, current_user_info: dict,
                 notification_manager: object, config: object,
                 parent_widget: QWidget,
                 parent=None):
        super().__init__(parent)
        self.client_info = client_info
        self.current_user_info = current_user_info
        self.notification_manager = notification_manager
        self.config = config # For paths or other settings if needed by dialogs/logic
        self.parent_widget = parent_widget

        self._setup_ui()
        self.apply_permissions_to_tab()

    def tr(self, text, disambiguation=None, n=-1):
        if self.parent_widget:
            return self.parent_widget.tr(text, disambiguation, n)
        return QApplication.translate("BillingTab", text, disambiguation, n)

    def _setup_ui(self):
        logging.info("BillingTab._setup_ui: Starting setup...")
        billing_layout = QVBoxLayout(self)

        self.generate_invoice_button = QPushButton(QIcon(":/icons/file-plus.svg"), self.tr("Generate Final Invoice"))
        self.generate_invoice_button.setToolTip(self.tr("Open dialog to prepare and generate a final invoice for this client."))
        self.generate_invoice_button.clicked.connect(self.handle_generate_final_invoice)
        billing_layout.addWidget(self.generate_invoice_button)

        billing_layout.addStretch()
        self.setLayout(billing_layout)

    def handle_generate_final_invoice(self):
        client_id = self.client_info.get("client_id")
        if not client_id:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("ID Client non disponible."))
            return

        # Ensure the dialog can be created.
        # FinalInvoiceDataDialog and create_final_invoice_and_update_db are imported.

        dialog = FinalInvoiceDataDialog(client_id=client_id, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            invoice_data = dialog.get_invoice_data()
            if not invoice_data:
                QMessageBox.warning(self, self.tr("Données Manquantes"), self.tr("Aucune donnée de facture à traiter."))
                return

            try:
                QApplication.setOverrideCursor(Qt.WaitCursor)
                # Call the logic function to create invoice and update DB
                # This function needs client_info, current_user_id, invoice_data, config, notification_manager
                # It's imported from document_manager_logic

                # Ensure all required parameters for create_final_invoice_and_update_db are available
                # For example, it might need the main window or specific parts of config.
                # We assume self.config and self.notification_manager are sufficient for its needs,
                # or that it can access them if it's a global/singleton.

                # The original call in ClientMainWidget was:
                # create_final_invoice_and_update_db(
                #     client_info=self.client_info,
                #     current_user_id=self.current_user_id,
                #     invoice_data=invoice_data,
                #     config=self.config, # ClientMainWidget's config
                #     notification_manager=self.notification_manager,
                #     parent_for_dialogs=self # ClientMainWidget instance
                # )
                # We need to adapt this call. parent_for_dialogs would be self (BillingTab instance)

                create_final_invoice_and_update_db(
                    client_info=self.client_info,
                    current_user_id=self.current_user_info.get('user_id'),
                    invoice_data=invoice_data,
                    config=self.config,
                    notification_manager=self.notification_manager,
                    parent_for_dialogs=self
                )
                # No direct feedback here as create_final_invoice_and_update_db handles notifications.
                # If DocumentsTab exists and needs refresh, parent needs to handle that.
                if hasattr(self.parent_widget, 'documents_tab_widget_ref'):
                    if hasattr(self.parent_widget.documents_tab_widget_ref, 'refresh_tab_data'):
                        self.parent_widget.documents_tab_widget_ref.refresh_tab_data()

            except Exception as e:
                logging.error(f"Error generating final invoice: {e}", exc_info=True)
                QMessageBox.critical(self, self.tr("Erreur Critique"), self.tr("Une erreur est survenue lors de la génération de la facture: {0}").format(str(e)))
            finally:
                QApplication.restoreOverrideCursor()
        else:
            logging.info("Final invoice generation cancelled by user.")


    def apply_permissions_to_tab(self):
        role_name = self.current_user_info.get('role_name')
        can_manage_billing = has_permission(role_name, P_MANAGE_CLIENT_BILLING)
        self.generate_invoice_button.setEnabled(can_manage_billing)

    def refresh_tab_data(self):
        # Currently, no data to refresh on this tab itself, but method is good practice.
        self.apply_permissions_to_tab() # Re-apply permissions in case user role changed
        logging.info("BillingTab refreshed (permissions re-applied).")


