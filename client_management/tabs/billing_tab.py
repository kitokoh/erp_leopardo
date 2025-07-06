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
        billing_layout.setSpacing(10)
        billing_layout.setContentsMargins(5, 5, 5, 5)

        # --- Section Actions de Facturation ---
        actions_group = QGroupBox(self.tr("Actions de Facturation"))
        actions_group_layout = QVBoxLayout(actions_group)

        self.generate_invoice_button = QPushButton(QIcon(":/icons/file-text.svg"), self.tr("Préparer et Générer une Facture Finale"))
        self.generate_invoice_button.setObjectName("primaryButton")
        self.generate_invoice_button.setToolTip(self.tr("Ouvre un dialogue pour saisir les informations finales et générer la facture PDF pour ce client."))
        self.generate_invoice_button.clicked.connect(self.handle_generate_final_invoice)
        actions_group_layout.addWidget(self.generate_invoice_button)

        # Potentiellement d'autres boutons ici (ex: Voir Relevé de Compte)
        actions_group_layout.addStretch()
        billing_layout.addWidget(actions_group)

        # --- Section Liste des Factures ---
        invoices_group = QGroupBox(self.tr("Historique des Factures"))
        invoices_group_layout = QVBoxLayout(invoices_group)

        self.invoices_empty_label = QLabel(self.tr("Aucune facture trouvée pour ce client."))
        self.invoices_empty_label.setAlignment(Qt.AlignCenter)
        self.invoices_empty_label.setStyleSheet("font-style: italic; color: #718096; font-size: 10pt; padding: 15px;")
        invoices_group_layout.addWidget(self.invoices_empty_label)

        self.invoices_table = QTableWidget()
        self.invoices_table.setObjectName("invoicesTable")
        self.invoices_table.setColumnCount(6) # Num Facture, Date, Montant Total, Statut Paiement, Date Paiement, Actions
        self.invoices_table.setHorizontalHeaderLabels([
            self.tr("Numéro Facture"), self.tr("Date Facture"), self.tr("Montant Total"),
            self.tr("Statut Paiement"), self.tr("Date Paiement"), self.tr("Actions")
        ])
        header_style = """
            QHeaderView::section {
                background-color: #4a5568; color: white; padding: 6px;
                border: 1px solid #ddd; font-weight: bold; font-size: 9pt;
            }
        """
        self.invoices_table.horizontalHeader().setStyleSheet(header_style)
        self.invoices_table.verticalHeader().setVisible(False)
        self.invoices_table.setAlternatingRowColors(True)
        self.invoices_table.setSortingEnabled(True)
        self.invoices_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.invoices_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.invoices_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.invoices_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.invoices_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.invoices_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.invoices_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.invoices_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch) # Actions
        invoices_group_layout.addWidget(self.invoices_table)
        self.invoices_table.hide() # Cacher initialement si vide

        self.refresh_invoices_btn = QPushButton(QIcon(":/icons/refresh-cw.svg"), self.tr("Actualiser Factures"))
        self.refresh_invoices_btn.setObjectName("secondaryButton")
        self.refresh_invoices_btn.clicked.connect(self.load_invoices_table)
        invoices_group_layout.addWidget(self.refresh_invoices_btn, 0, Qt.AlignRight)

        billing_layout.addWidget(invoices_group)
        billing_layout.addStretch(1) # Pousse les groupes vers le haut
        self.setLayout(billing_layout)

    def load_invoices_table(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.invoices_table.setRowCount(0)
        client_id = self.client_info.get("client_id")
        if not client_id:
            QApplication.restoreOverrideCursor()
            self.invoices_empty_label.show()
            self.invoices_table.hide()
            return

        try:
            # TODO: Remplacer par un appel CRUD réel: db_manager.invoices_crud.get_invoices_for_client(client_id)
            invoices_list = [] # Placeholder
            # invoices_list = db_manager.invoices_crud.get_invoices_for_client(client_id)

            if not invoices_list:
                self.invoices_empty_label.show()
                self.invoices_table.hide()
            else:
                self.invoices_empty_label.hide()
                self.invoices_table.show()
                self.invoices_table.setRowCount(len(invoices_list))
                for row, invoice_data in enumerate(invoices_list):
                    invoice_id = invoice_data.get("invoice_id")

                    num_item = QTableWidgetItem(invoice_data.get("invoice_number", self.tr("N/A")))
                    num_item.setData(Qt.UserRole, invoice_id)
                    self.invoices_table.setItem(row, 0, num_item)

                    date_item = QTableWidgetItem(invoice_data.get("invoice_date", self.tr("N/A"))) # Formatter la date
                    self.invoices_table.setItem(row, 1, date_item)

                    amount_item = QTableWidgetItem(f"{invoice_data.get('total_amount', 0.0):.2f} {invoice_data.get('currency', 'EUR')}")
                    amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.invoices_table.setItem(row, 2, amount_item)

                    status_item = QTableWidgetItem(self.tr(invoice_data.get("payment_status", "Unknown"))) # Traduire le statut
                    self.invoices_table.setItem(row, 3, status_item)

                    payment_date_item = QTableWidgetItem(invoice_data.get("payment_date") or self.tr("N/P")) # Non Payé
                    self.invoices_table.setItem(row, 4, payment_date_item)

                    # Actions Cell
                    actions_widget = QWidget()
                    actions_layout = QHBoxLayout(actions_widget)
                    actions_layout.setContentsMargins(0,0,0,0)
                    actions_layout.setSpacing(5)

                    view_pdf_btn = QPushButton(QIcon(":/icons/file-text.svg"), self.tr("Voir PDF"))
                    view_pdf_btn.setToolTip(self.tr("Ouvrir le fichier PDF de la facture"))
                    # view_pdf_btn.clicked.connect(lambda ch, inv_id=invoice_id: self.handle_view_invoice_pdf(inv_id))
                    actions_layout.addWidget(view_pdf_btn)

                    # record_payment_btn = QPushButton(QIcon(":/icons/dollar-sign.svg"), self.tr("Enregistrer Paiement"))
                    # record_payment_btn.setToolTip(self.tr("Enregistrer ou mettre à jour le statut du paiement pour cette facture"))
                    # record_payment_btn.clicked.connect(lambda ch, inv_id=invoice_id: self.handle_record_payment(inv_id))
                    # actions_layout.addWidget(record_payment_btn)

                    actions_layout.addStretch()
                    self.invoices_table.setCellWidget(row, 5, actions_widget)
                self.invoices_table.resizeColumnsToContents()

        except Exception as e:
            logging.error(f"Error loading invoices for client {client_id}: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Chargement Factures"), str(e))
            self.invoices_empty_label.show()
            self.invoices_table.hide()
        finally:
            QApplication.restoreOverrideCursor()

    def handle_generate_final_invoice(self):
        client_id = self.client_info.get("client_id")
        if not client_id:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("ID Client non disponible."))
            return

        dialog = FinalInvoiceDataDialog(client_id=client_id, parent=self)
        if dialog.exec_() == QDialog.Accepted: # FinalInvoiceDataDialog uses QDialog.Accepted
            invoice_data = dialog.get_invoice_data()
            if not invoice_data:
                QMessageBox.warning(self, self.tr("Données Manquantes"), self.tr("Aucune donnée de facture à traiter."))
                return

            try:
                QApplication.setOverrideCursor(Qt.WaitCursor)
                create_final_invoice_and_update_db(
                    client_info=self.client_info,
                    current_user_id=self.current_user_info.get('user_id'),
                    invoice_data=invoice_data,
                    config=self.config,
                    notification_manager=self.notification_manager,
                    parent_for_dialogs=self
                )
                # Refresh invoice list and potentially documents tab
                self.load_invoices_table()
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
        if hasattr(self, 'invoices_table'): # Check if table exists
            self.invoices_table.setEnabled(can_manage_billing) # Or a more granular view permission
            self.refresh_invoices_btn.setEnabled(can_manage_billing) # If they can't see the table, no need to refresh

    def refresh_tab_data(self):
        self.load_invoices_table()
        self.apply_permissions_to_tab()
        logging.info("BillingTab refreshed.")


