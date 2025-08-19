# -*- coding: utf-8 -*-
import logging
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QMessageBox, QApplication,
    QGroupBox, QDialog
)
from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5.QtCore import Qt, QUrl, QLocale, QDate

from app import db as db_manager
from app.db.cruds.invoices import invoices_crud
from app.invoicing.record_payment_dialog import RecordPaymentDialog
from app.utils.document_manager_logic import create_final_invoice_and_update_db
from app.services.auth.permissions import has_permission, P_MANAGE_CLIENT_BILLING, P_VIEW_CLIENT_BILLING
from app.utils.file_utils import get_document_full_path

class BillingTab(QWidget):
    def __init__(self, client_info: dict, current_user_info: dict,
                 notification_manager: object, config: object,
                 parent_widget: QWidget,
                 parent=None):
        super().__init__(parent)
        self.client_info = client_info
        self.current_user_info = current_user_info
        self.notification_manager = notification_manager
        self.config = config
        self.parent_widget = parent_widget # Used for tr method

        self._setup_ui()
        self.load_invoices_table() # Load data on init
        self.apply_permissions_to_tab()

    def tr(self, text, disambiguation=None, n=-1):
        if self.parent_widget: # Prefer parent's tr if available (likely ClientMainWidget)
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

        self.generate_invoice_button = QPushButton("📄 " + self.tr("Préparer et Générer une Facture Finale"))
        self.generate_invoice_button.setObjectName("primaryButton")
        self.generate_invoice_button.setToolTip(self.tr("Ouvre un dialogue pour saisir les informations finales et générer la facture PDF pour ce client."))
        self.generate_invoice_button.clicked.connect(self.handle_generate_final_invoice)
        actions_group_layout.addWidget(self.generate_invoice_button)

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
        self.invoices_table.setColumnCount(6)

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
        self.invoices_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        invoices_group_layout.addWidget(self.invoices_table)
        self.invoices_table.hide()


        self.refresh_invoices_btn = QPushButton("🔄 " + self.tr("Actualiser Factures"))
        self.refresh_invoices_btn.setObjectName("secondaryButton")
        self.refresh_invoices_btn.clicked.connect(self.load_invoices_table)
        invoices_group_layout.addWidget(self.refresh_invoices_btn, 0, Qt.AlignRight)

        billing_layout.addWidget(invoices_group)
        billing_layout.addStretch(1)

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
            invoices_list = invoices_crud.get_invoices_by_client_id(client_id)


            if not invoices_list:
                self.invoices_empty_label.show()
                self.invoices_table.hide()
            else:
                self.invoices_empty_label.hide()
                self.invoices_table.show()
                self.invoices_table.setRowCount(len(invoices_list))
                for row, invoice_data_dict in enumerate(invoices_list):
                    # invoice_data is a dict from sqlite3.Row
                    invoice_id = invoice_data_dict.get("invoice_id")

                    num_item = QTableWidgetItem(invoice_data_dict.get("invoice_number", self.tr("N/A")))
                    num_item.setData(Qt.UserRole, invoice_id) # Store invoice_id for actions
                    num_item.setData(Qt.UserRole + 1, invoice_data_dict.get("document_id")) # Store document_id
                    self.invoices_table.setItem(row, 0, num_item)

                    locale = QLocale()
                    issue_date_str = invoice_data_dict.get("issue_date", "")
                    q_issue_date = QDate.fromString(issue_date_str, Qt.ISODate)
                    date_display = locale.toString(q_issue_date, QLocale.ShortFormat) if q_issue_date.isValid() else self.tr("N/A")
                    date_item = QTableWidgetItem(date_display)
                    self.invoices_table.setItem(row, 1, date_item)

                    total_amount = invoice_data_dict.get('total_amount', 0.0)
                    currency_symbol = invoice_data_dict.get('currency', 'EUR') # Assuming EUR if not specified
                    # For robust currency display, QLocale().toCurrencyString is better if full ICU data is available.
                    # Otherwise, format number and append symbol.
                    amount_str = locale.toString(float(total_amount), 'f', 2)
                    amount_item = QTableWidgetItem(f"{amount_str} {currency_symbol}")
                    amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.invoices_table.setItem(row, 2, amount_item)

                    status_item = QTableWidgetItem(self.tr(invoice_data_dict.get("payment_status", "Unknown").capitalize()))
                    self.invoices_table.setItem(row, 3, status_item)

                    payment_date_str = invoice_data_dict.get("payment_date")
                    payment_date_display = self.tr("N/P")
                    if payment_date_str:
                        q_payment_date = QDate.fromString(payment_date_str, Qt.ISODate)
                        payment_date_display = locale.toString(q_payment_date, QLocale.ShortFormat) if q_payment_date.isValid() else payment_date_str
                    payment_date_item = QTableWidgetItem(payment_date_display)
                    self.invoices_table.setItem(row, 4, payment_date_item)

                    actions_widget = QWidget()
                    actions_layout = QHBoxLayout(actions_widget)
                    actions_layout.setContentsMargins(2, 2, 2, 2)
                    actions_layout.setSpacing(5)

                    view_pdf_btn = QPushButton("📄") # No text, icon only
                    view_pdf_btn.setToolTip(self.tr("Ouvrir le fichier PDF de la facture"))
                    view_pdf_btn.setObjectName("iconButton")
                    view_pdf_btn.clicked.connect(lambda ch, inv_id=invoice_id, doc_id=invoice_data_dict.get("document_id"): self.handle_view_invoice_pdf(inv_id, doc_id))
                    actions_layout.addWidget(view_pdf_btn)

                    record_payment_btn = QPushButton("💵") # No text, icon only
                    record_payment_btn.setToolTip(self.tr("Enregistrer ou mettre à jour le statut du paiement pour cette facture"))
                    record_payment_btn.setObjectName("iconButton")
                    record_payment_btn.clicked.connect(lambda ch, inv_id=invoice_id: self.handle_record_payment(inv_id))
                    actions_layout.addWidget(record_payment_btn)

                    # Disable record payment if already paid
                    if invoice_data_dict.get("payment_status", "").lower() == "paid":
                        record_payment_btn.setEnabled(False)
                        record_payment_btn.setToolTip(self.tr("Facture déjà payée"))

                    actions_layout.addStretch()
                    self.invoices_table.setCellWidget(row, 5, actions_widget)
                self.invoices_table.resizeColumnsToContents()
                self.invoices_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)


        except Exception as e:
            logging.error(f"Error loading invoices for client {client_id}: {e}", exc_info=True)
            if self.notification_manager:
                self.notification_manager.show_notification(
                    self.tr("Erreur Chargement Factures"),
                    self.tr("Impossible de charger la liste des factures pour ce client. Détails: {0}").format(str(e)),
                    'ERROR'
                )
            else: # Fallback if notification_manager is somehow None
                QMessageBox.critical(self, self.tr("Erreur Chargement Factures"), str(e))
            self.invoices_empty_label.setText(self.tr("Erreur lors du chargement des factures."))

            self.invoices_empty_label.show()
            self.invoices_table.hide()
        finally:
            QApplication.restoreOverrideCursor()

    def handle_view_invoice_pdf(self, invoice_id: str, document_id: str):
        logging.info(f"Attempting to view PDF for invoice_id: {invoice_id}, document_id: {document_id}")
        if not document_id:
            QMessageBox.information(self, self.tr("Document Manquant"), self.tr("Aucun document PDF n'est associé à cette facture dans la base de données."))
            return

        try:
            doc_details = db_manager.cruds.client_documents_crud.get_document_by_id(document_id) # Use the main db_manager
            if not doc_details:
                QMessageBox.warning(self, self.tr("Document Introuvable"), self.tr("Le document associé à cette facture n'a pas pu être trouvé."))
                return

            # Use app_utils.get_document_full_path to construct the path
            # This requires client_id and project_identifier from self.client_info
            # and relative_file_path from doc_details
            client_id = self.client_info.get("client_id")
            project_identifier = self.client_info.get("project_identifier") # Or however it's stored
            relative_path = doc_details.get("file_path_relative")
            file_name_on_disk = doc_details.get("file_name_on_disk")

            if not all([client_id, project_identifier, relative_path, file_name_on_disk]):
                 QMessageBox.warning(self, self.tr("Informations Manquantes"), self.tr("Informations client ou document incomplètes pour localiser le fichier."))
                 logging.error(f"Missing info for PDF path: client_id={client_id}, project_id={project_identifier}, rel_path={relative_path}, disk_name={file_name_on_disk}")
                 return

            # Construct the base path using client_id and project_identifier
            # This logic might need adjustment based on how `default_base_folder_path` is structured in `Clients` table
            # and how `get_document_full_path` expects its arguments.
            # Assuming `config.CLIENTS_DOCUMENTS_BASE_DIR` is the root for all client documents.

            # Simpler approach if file_path_relative already contains the necessary subfolders from client's base
            # and file_name_on_disk is just the filename.
            # The function get_document_full_path should handle the logic of joining these.

            # We need the base path for the client. This might be stored in client_info or fetched.
            # For now, let's assume `ClientDocuments.file_path_relative` is relative to a base client documents directory.
            # And `file_name_on_disk` is the actual file name.
            # So, full_path = os.path.join(self.config.CLIENTS_DOCUMENTS_BASE_DIR, relative_path, file_name_on_disk)
            # But it's better to use a utility function if available.

            # The `get_document_full_path` in `app_utils.py` is:
            # get_document_full_path(app_config, client_default_base_folder, relative_file_path, file_name_on_disk)
            # client_default_base_folder is from Clients table.

            client_default_base_folder = self.client_info.get("default_base_folder_path")
            if not client_default_base_folder:
                QMessageBox.warning(self, self.tr("Configuration Client Manquante"), self.tr("Le dossier de base du client n'est pas configuré."))
                return

            full_pdf_path = get_document_full_path(
                app_config=self.config, # Assuming self.config is the app_config object
                client_default_base_folder=client_default_base_folder, # From client_info
                relative_file_path=doc_details.get("file_path_relative"), # From document_details
                file_name_on_disk=doc_details.get("file_name_on_disk") # From document_details
            )

            if os.path.exists(full_pdf_path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(full_pdf_path))
            else:
                QMessageBox.warning(self, self.tr("Fichier Introuvable"), self.tr("Le fichier PDF de la facture n'a pas été trouvé à l'emplacement attendu:\n{0}").format(full_pdf_path))
        except Exception as e:
            logging.error(f"Error opening PDF for invoice {invoice_id}, doc {document_id}: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur PDF"), self.tr("Impossible d'ouvrir le document PDF de la facture."))

    def handle_record_payment(self, invoice_id: str):
        logging.info(f"Recording payment for invoice_id: {invoice_id}")

        invoice_details = invoices_crud.get_invoice_by_id(invoice_id)
        if not invoice_details:
            QMessageBox.warning(self, self.tr("Facture Introuvable"), self.tr("Les détails de la facture n'ont pas pu être chargés."))
            return

        dialog = RecordPaymentDialog(invoice_details, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            payment_data = dialog.get_payment_data()
            try:
                QApplication.setOverrideCursor(Qt.WaitCursor)
                success = invoices_crud.update_invoice(invoice_id, payment_data)
                QApplication.restoreOverrideCursor()
                if success:
                    self.notification_manager.show_notification(self.tr("Paiement Enregistré"), self.tr("Le paiement pour la facture a été enregistré avec succès."), 'success')
                    self.load_invoices_table() # Refresh
                else:
                    QMessageBox.critical(self, self.tr("Erreur Enregistrement"), self.tr("Échec de l'enregistrement du paiement."))
            except Exception as e:
                QApplication.restoreOverrideCursor()
                logging.error(f"Error recording payment for invoice {invoice_id}: {e}", exc_info=True)
                QMessageBox.critical(self, self.tr("Erreur Critique"), str(e))


    def handle_generate_final_invoice(self):
        # This method seems to be mostly fine but ensure QDialog is imported if FinalInvoiceDataDialog needs it.
        # FinalInvoiceDataDialog is already imported.
        client_id = self.client_info.get("client_id")
        if not client_id:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("ID Client non disponible."))
            return

        # Need to import FinalInvoiceDataDialog if not already. It is.
        from app.invoicing.final_invoice_data_dialog import FinalInvoiceDataDialog
        dialog = FinalInvoiceDataDialog(client_id=client_id, current_user_id=self.current_user_info.get('user_id'), config=self.config, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            invoice_data_from_dialog = dialog.get_invoice_data() # Renamed to avoid conflict
            if not invoice_data_from_dialog:

                QMessageBox.warning(self, self.tr("Données Manquantes"), self.tr("Aucune donnée de facture à traiter."))
                return

            try:
                QApplication.setOverrideCursor(Qt.WaitCursor)
                # create_final_invoice_and_update_db is expected to handle PDF generation and DB entries for Invoice and ClientDocument
                document_id, invoice_id = create_final_invoice_and_update_db(

                    client_info=self.client_info,
                    current_user_id=self.current_user_info.get('user_id'),
                    invoice_data=invoice_data_from_dialog, # Use the new variable name
                    config=self.config,
                    notification_manager=self.notification_manager,
                    parent_for_dialogs=self # Pass self (BillingTab) for any dialogs it might need to parent
                )
                QApplication.restoreOverrideCursor()
                if document_id and invoice_id:
                    self.notification_manager.show_notification(
                        self.tr("Facture Générée"),
                        self.tr("La facture {0} a été générée et enregistrée.").format(invoice_data_from_dialog.get('invoice_number', 'N/A')),
                        'success'
                    )
                    self.load_invoices_table()
                    # Refresh documents tab if it exists on the parent
                    if hasattr(self.parent_widget, 'documents_tab_widget_ref') and \
                       hasattr(self.parent_widget.documents_tab_widget_ref, 'refresh_tab_data'):

                        self.parent_widget.documents_tab_widget_ref.refresh_tab_data()
                else:
                    QMessageBox.warning(self, self.tr("Échec de Génération"), self.tr("La facture n'a pas pu être générée ou enregistrée."))

            except Exception as e:
                QApplication.restoreOverrideCursor()
                logging.error(f"Error generating final invoice: {e}", exc_info=True)
                QMessageBox.critical(self, self.tr("Erreur Critique"), self.tr("Une erreur est survenue lors de la génération de la facture: {0}").format(str(e)))
            # finally: QApplication.restoreOverrideCursor() # Already handled inside try and except
        else:
            logging.info("Final invoice generation cancelled by user.")


    def apply_permissions_to_tab(self):
        role_name = self.current_user_info.get('role_name')
        can_manage_billing = has_permission(role_name, P_MANAGE_CLIENT_BILLING)
        can_view_billing = has_permission(role_name, P_VIEW_CLIENT_BILLING) or can_manage_billing # Manage implies view


        self.generate_invoice_button.setEnabled(can_manage_billing)
        if hasattr(self, 'invoices_table'): # Check if table exists
            # The table's general enabled state is less critical than its visibility and action controls.
            # Visibility is handled by can_view_billing. Actions within are (or should be) by can_manage_billing.
            self.refresh_invoices_btn.setEnabled(can_view_billing) # Refresh should be available if user can view

        if hasattr(self, 'invoices_table'):
            self.invoices_table.setVisible(can_view_billing) # Show/hide based on view permission
            # self.refresh_invoices_btn.setEnabled(can_view_billing) # Already set above

            if not can_view_billing:
                 self.invoices_empty_label.setText(self.tr("Vous n'avez pas la permission de voir l'historique des factures."))
                 self.invoices_empty_label.show()
            elif self.invoices_table.rowCount() == 0 : # if can view but table is empty
                 self.invoices_empty_label.setText(self.tr("Aucune facture trouvée pour ce client."))
                 self.invoices_empty_label.show()
            else: # Can view and table has data
                self.invoices_empty_label.hide()

            # Further granular control for action buttons in table can be done during load_invoices_table
            # For now, the "Enregistrer Paiement" button is already managed by can_manage_billing in handle_record_payment dialog
            # and view PDF could be P_VIEW_CLIENT_BILLING.


    def refresh_tab_data(self):
        """Called by parent to refresh data in this tab."""
        self.load_invoices_table()
        self.apply_permissions_to_tab() # Re-apply permissions which might affect visibility
        logging.info("BillingTab refreshed.")
