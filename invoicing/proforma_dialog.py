# -*- coding: utf-8 -*-
import os
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit,
    QPushButton, QDialogButtonBox, QMessageBox, QLabel, QTableWidget,
    QTableWidgetItem, QComboBox, QGroupBox, QDoubleSpinBox,
    QAbstractItemView, QHeaderView, QApplication
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QDate

import db as db_manager
# Placeholder for API client functions - will be created in a later step
from api_client import post_proforma_invoice, download_file # Adjusted import
from PyQt5.QtCore import QStandardPaths # For download path
import os # For joining paths for download

class ProformaDialog(QDialog):
    def __init__(self, client_info: dict, current_user_info: dict, parent=None):
        super().__init__(parent)
        self.client_info = client_info
        self.current_user_info = current_user_info
        self.default_company_id = None
        self.products_cache = [] # To store fetched global products

        self.setWindowTitle(self.tr("Générer Facture Proforma"))
        self.setMinimumSize(800, 600)
        self.setWindowIcon(QIcon(":/icons/file-plus.svg")) # Placeholder icon

        self._fetch_default_company_id()
        self._fetch_products_cache()
        self._init_ui()
        self._load_client_data()

    def _fetch_default_company_id(self):
        try:
            default_company = db_manager.get_default_company()
            if default_company:
                self.default_company_id = default_company.get('company_id')
            else:
                QMessageBox.warning(self, self.tr("Configuration Error"),
                                    self.tr("No default selling company configured. Proforma cannot be generated."))
                # self.reject() # Or disable generate button
        except Exception as e:
            logging.error(f"Error fetching default company ID: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Database Error"),
                                 self.tr("Could not fetch default company information: {str(e)}"))
            # self.reject()

    def _fetch_products_cache(self):
        try:
            # Assuming get_all_products_for_selection returns a list of dicts with 'product_id', 'product_name', 'base_unit_price', 'description'
            self.products_cache = db_manager.get_all_products_for_selection() # You'll need to create this in db_manager
            if not self.products_cache:
                self.products_cache = [] # Ensure it's a list
                # QMessageBox.information(self, self.tr("Info Produits"), self.tr("Aucun produit global trouvé. Vous devrez entrer les descriptions manuellement."))
        except Exception as e:
            logging.error(f"Error fetching global products: {e}", exc_info=True)
            self.products_cache = []
            QMessageBox.warning(self, self.tr("Erreur Produits"), self.tr("Impossible de charger la liste des produits globaux: {str(e)}"))


    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        # Client Info Section
        client_group = QGroupBox(self.tr("Client"))
        client_layout = QVBoxLayout()
        self.client_name_label = QLabel(self.tr("Client: N/A"))
        client_layout.addWidget(self.client_name_label)
        client_group.setLayout(client_layout)
        main_layout.addWidget(client_group)

        # Proforma Details Section
        details_group = QGroupBox(self.tr("Détails de la Proforma"))
        details_form_layout = QVBoxLayout() # Using QVBoxLayout for more control over groups

        # Row 1: Currency, Payment Terms
        row1_layout = QHBoxLayout()
        currency_label = QLabel(self.tr("Devise:"))
        self.currency_edit = QLineEdit("EUR")
        row1_layout.addWidget(currency_label)
        row1_layout.addWidget(self.currency_edit)

        payment_terms_label = QLabel(self.tr("Conditions de Paiement:"))
        self.payment_terms_edit = QLineEdit(self.tr("Paiement anticipé"))
        row1_layout.addWidget(payment_terms_label)
        row1_layout.addWidget(self.payment_terms_edit)
        details_form_layout.addLayout(row1_layout)

        # Row 2: Delivery Terms, Incoterms
        row2_layout = QHBoxLayout()
        delivery_terms_label = QLabel(self.tr("Conditions de Livraison:"))
        self.delivery_terms_edit = QLineEdit(self.tr("Selon accord"))
        row2_layout.addWidget(delivery_terms_label)
        row2_layout.addWidget(self.delivery_terms_edit)

        incoterms_label = QLabel(self.tr("Incoterms:"))
        self.incoterms_combo = QComboBox()
        self.incoterms_combo.addItems(["EXW", "FOB", "CIF", "DDP", "CPT", "CIP", "DAP", "DPU"])
        self.incoterms_combo.setCurrentText("EXW")
        row2_layout.addWidget(incoterms_label)
        row2_layout.addWidget(self.incoterms_combo)
        details_form_layout.addLayout(row2_layout)

        # Row 3: Named Place of Delivery
        row3_layout = QHBoxLayout()
        named_place_label = QLabel(self.tr("Lieu de Livraison Convenu:"))
        self.named_place_edit = QLineEdit() # Default will be set from client/company city
        row3_layout.addWidget(named_place_label)
        row3_layout.addWidget(self.named_place_edit)
        details_form_layout.addLayout(row3_layout)

        # Row 4: VAT Rate, Discount Rate
        row4_layout = QHBoxLayout()
        vat_rate_label = QLabel(self.tr("Taux de TVA (%):"))
        self.vat_rate_spinbox = QDoubleSpinBox()
        self.vat_rate_spinbox.setRange(0, 100)
        self.vat_rate_spinbox.setValue(20.0)
        self.vat_rate_spinbox.setDecimals(2)
        row4_layout.addWidget(vat_rate_label)
        row4_layout.addWidget(self.vat_rate_spinbox)

        discount_rate_label = QLabel(self.tr("Taux de Remise (%):"))
        self.discount_rate_spinbox = QDoubleSpinBox()
        self.discount_rate_spinbox.setRange(0, 100)
        self.discount_rate_spinbox.setValue(0.0)
        self.discount_rate_spinbox.setDecimals(2)
        row4_layout.addWidget(discount_rate_label)
        row4_layout.addWidget(self.discount_rate_spinbox)
        details_form_layout.addLayout(row4_layout)

        details_group.setLayout(details_form_layout)
        main_layout.addWidget(details_group)

        # Line Items Section
        items_group = QGroupBox(self.tr("Lignes de Produits/Services"))
        items_layout = QVBoxLayout()
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels([
            self.tr("Produit/Service"), self.tr("Description"), self.tr("Quantité"),
            self.tr("Prix Unitaire"), self.tr("Prix Total")
        ])
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # Allow editing for Description, Quantity, Unit Price columns by connecting itemChanged or using delegates
        self.items_table.itemChanged.connect(self._on_item_changed)

        items_layout.addWidget(self.items_table)

        item_buttons_layout = QHBoxLayout()
        self.add_item_button = QPushButton(QIcon(":/icons/plus-circle.svg"), self.tr("Ajouter Ligne"))
        self.add_item_button.clicked.connect(self._add_item_row)
        item_buttons_layout.addWidget(self.add_item_button)

        self.remove_item_button = QPushButton(QIcon(":/icons/trash.svg"), self.tr("Supprimer Ligne"))
        self.remove_item_button.clicked.connect(self._remove_item_row)
        item_buttons_layout.addWidget(self.remove_item_button)
        item_buttons_layout.addStretch()
        items_layout.addLayout(item_buttons_layout)
        items_group.setLayout(items_layout)
        main_layout.addWidget(items_group)

        # Notes Section
        notes_group = QGroupBox(self.tr("Notes Additionnelles"))
        notes_layout = QVBoxLayout()
        self.notes_edit = QTextEdit()
        notes_layout.addWidget(self.notes_edit)
        notes_group.setLayout(notes_layout)
        main_layout.addWidget(notes_group)

        # Totals Display (Read-only)
        totals_group = QGroupBox(self.tr("Totaux Estimés"))
        totals_layout = QVBoxLayout()
        self.subtotal_label = QLabel(self.tr("Sous-total: 0.00 EUR"))
        self.discount_label = QLabel(self.tr("Remise: 0.00 EUR"))
        self.vat_label = QLabel(self.tr("TVA: 0.00 EUR"))
        self.grand_total_label = QLabel(self.tr("Total Général: 0.00 EUR"))
        totals_layout.addWidget(self.subtotal_label)
        totals_layout.addWidget(self.discount_label)
        totals_layout.addWidget(self.vat_label)
        totals_layout.addWidget(self.grand_total_label)
        totals_group.setLayout(totals_layout)
        main_layout.addWidget(totals_group)


        # Dialog Buttons
        self.button_box = QDialogButtonBox()
        self.generate_button = self.button_box.addButton(self.tr("Générer Proforma"), QDialogButtonBox.AcceptRole)
        self.generate_button.setIcon(QIcon(":/icons/file-plus.svg"))
        self.cancel_button = self.button_box.addButton(QDialogButtonBox.Cancel)

        self.generate_button.clicked.connect(self._on_generate_proforma)
        self.cancel_button.clicked.connect(self.reject)
        main_layout.addWidget(self.button_box)

        if not self.default_company_id:
            self.generate_button.setEnabled(False)
            self.generate_button.setToolTip(self.tr("La société vendeuse par défaut n'est pas configurée."))

        # Connect signals for dynamic total calculation
        self.vat_rate_spinbox.valueChanged.connect(self._calculate_totals)
        self.discount_rate_spinbox.valueChanged.connect(self._calculate_totals)


    def _load_client_data(self):
        if self.client_info:
            self.client_name_label.setText(self.tr("Client: {0} (ID: {1})").format(
                self.client_info.get('client_name', 'N/A'),
                self.client_info.get('client_id', 'N/A')
            ))
            # Set default for named place of delivery
            client_city = self.client_info.get('city', '')
            if client_city:
                self.named_place_edit.setText(client_city)
            elif self.default_company_id: # Fallback to seller city if client city not available
                try:
                    company_data = db_manager.get_company_by_id_from_db(self.default_company_id) # Assuming direct db access
                    if company_data and company_data.get('city'):
                        self.named_place_edit.setText(company_data.get('city'))
                    else: # Ultimate fallback
                        self.named_place_edit.setText(self.tr("Lieu du vendeur"))
                except Exception as e:
                    logging.warning(f"Could not fetch default company city for named place: {e}")
                    self.named_place_edit.setText(self.tr("Lieu du vendeur"))


    def _add_item_row(self):
        row_position = self.items_table.rowCount()
        self.items_table.insertRow(row_position)

        # Column 0: Product (ComboBox for selection)
        product_combo = QComboBox()
        product_combo.setEditable(False) # User selects from list
        product_combo.addItem(self.tr("-- Sélectionner Produit --"), None)
        for prod in self.products_cache:
            display_text = f"{prod.get('product_name', 'N/A')} (Code: {prod.get('product_code', 'N/A')})"
            product_combo.addItem(display_text, prod.get('product_id'))

        product_combo.currentIndexChanged.connect(lambda index, r=row_position: self._on_product_selected(index, r))
        self.items_table.setCellWidget(row_position, 0, product_combo)

        # Column 1: Description (QLineEdit, editable)
        desc_edit = QLineEdit()
        self.items_table.setCellWidget(row_position, 1, desc_edit) # Use setCellWidget for custom editors

        # Column 2: Quantity (QDoubleSpinBox)
        qty_spinbox = QDoubleSpinBox()
        qty_spinbox.setRange(0.01, 999999.99)
        qty_spinbox.setValue(1.0)
        qty_spinbox.setDecimals(2)
        qty_spinbox.valueChanged.connect(lambda val, r=row_position: self._update_row_total(r))
        self.items_table.setCellWidget(row_position, 2, qty_spinbox)

        # Column 3: Unit Price (QDoubleSpinBox)
        price_spinbox = QDoubleSpinBox()
        price_spinbox.setRange(0.00, 99999999.99)
        price_spinbox.setDecimals(2)
        price_spinbox.valueChanged.connect(lambda val, r=row_position: self._update_row_total(r))
        self.items_table.setCellWidget(row_position, 3, price_spinbox)

        # Column 4: Total Price (QLabel, read-only)
        total_label = QLabel("0.00")
        total_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.items_table.setCellWidget(row_position, 4, total_label)

        self._calculate_totals() # Recalculate grand totals

    def _on_product_selected(self, combo_box_index, table_row_index):
        product_combo_widget = self.items_table.cellWidget(table_row_index, 0)
        if not isinstance(product_combo_widget, QComboBox): return

        product_id = product_combo_widget.itemData(combo_box_index)

        desc_widget = self.items_table.cellWidget(table_row_index, 1) # QLineEdit
        price_widget = self.items_table.cellWidget(table_row_index, 3) # QDoubleSpinBox

        if product_id:
            selected_product_data = next((p for p in self.products_cache if p.get('product_id') == product_id), None)
            if selected_product_data:
                if isinstance(desc_widget, QLineEdit):
                    desc_text = selected_product_data.get('description') or selected_product_data.get('product_name', '')
                    desc_widget.setText(desc_text)
                if isinstance(price_widget, QDoubleSpinBox):
                    price_widget.setValue(float(selected_product_data.get('base_unit_price', 0.0)))
            else: # Product ID selected but not found in cache (should not happen if cache is up-to-date)
                if isinstance(desc_widget, QLineEdit): desc_widget.clear()
                if isinstance(price_widget, QDoubleSpinBox): price_widget.setValue(0.0)
        else: # "-- Select Product --" chosen
            if isinstance(desc_widget, QLineEdit): desc_widget.clear()
            if isinstance(price_widget, QDoubleSpinBox): price_widget.setValue(0.0)

        self._update_row_total(table_row_index)


    def _remove_item_row(self):
        current_row = self.items_table.currentRow()
        if current_row >= 0:
            self.items_table.removeRow(current_row)
            self._calculate_totals()

    def _update_row_total(self, row_index):
        qty_widget = self.items_table.cellWidget(row_index, 2) # QDoubleSpinBox
        price_widget = self.items_table.cellWidget(row_index, 3) # QDoubleSpinBox
        total_label_widget = self.items_table.cellWidget(row_index, 4) # QLabel

        if isinstance(qty_widget, QDoubleSpinBox) and \
           isinstance(price_widget, QDoubleSpinBox) and \
           isinstance(total_label_widget, QLabel):

            quantity = qty_widget.value()
            unit_price = price_widget.value()
            row_total = quantity * unit_price
            total_label_widget.setText(f"{row_total:.2f}")

        self._calculate_totals() # Update grand totals

    def _on_item_changed(self, item: QTableWidgetItem):
        # This is a simpler handler if we don't use custom cell widgets for Qty/Price
        # For now, _update_row_total is connected to spinbox valueChanged, so this might be redundant
        # or could be used if we switch QTableWidgetItems for Qty/Price later.
        # row = item.row()
        # col = item.column()
        # if col == 2 or col == 3: # Quantity or Unit Price column
        #     self._update_row_total(row)
        pass


    def _calculate_totals(self):
        subtotal = 0.0
        for row in range(self.items_table.rowCount()):
            total_label_widget = self.items_table.cellWidget(row, 4) # QLabel for row total
            if isinstance(total_label_widget, QLabel):
                try:
                    subtotal += float(total_label_widget.text())
                except ValueError:
                    pass # Ignore if text is not a valid float

        discount_rate = self.discount_rate_spinbox.value() / 100.0
        discount_amount = subtotal * discount_rate

        amount_after_discount = subtotal - discount_amount

        vat_rate = self.vat_rate_spinbox.value() / 100.0
        vat_amount = amount_after_discount * vat_rate

        grand_total = amount_after_discount + vat_amount

        currency_symbol = self.currency_edit.text().strip() or "EUR"

        self.subtotal_label.setText(self.tr("Sous-total: {0:.2f} {1}").format(subtotal, currency_symbol))
        self.discount_label.setText(self.tr("Remise ({0}%): {1:.2f} {2}").format(self.discount_rate_spinbox.value(), discount_amount, currency_symbol))
        self.vat_label.setText(self.tr("TVA ({0}%): {1:.2f} {2}").format(self.vat_rate_spinbox.value(), vat_amount, currency_symbol))
        self.grand_total_label.setText(self.tr("Total Général: {0:.2f} {1}").format(grand_total, currency_symbol))


    def _on_generate_proforma(self):
        if not self.client_info or not self.client_info.get('client_id'):
            QMessageBox.warning(self, self.tr("Erreur Client"), self.tr("Information client non disponible."))
            return

        if not self.default_company_id:
            QMessageBox.warning(self, self.tr("Erreur Configuration"), self.tr("Société vendeuse par défaut non configurée."))
            return

        line_items_payload = []
        for row in range(self.items_table.rowCount()):
            product_combo_widget = self.items_table.cellWidget(row, 0) # QComboBox
            desc_widget = self.items_table.cellWidget(row, 1)          # QLineEdit
            qty_widget = self.items_table.cellWidget(row, 2)           # QDoubleSpinBox
            price_widget = self.items_table.cellWidget(row, 3)         # QDoubleSpinBox
            total_widget = self.items_table.cellWidget(row, 4)         # QLabel

            product_id = None
            if isinstance(product_combo_widget, QComboBox):
                product_id = product_combo_widget.currentData() # This is the product_id (string or None)

            description = desc_widget.text().strip() if isinstance(desc_widget, QLineEdit) else ""
            quantity = qty_widget.value() if isinstance(qty_widget, QDoubleSpinBox) else 0.0
            unit_price = price_widget.value() if isinstance(price_widget, QDoubleSpinBox) else 0.0

            if not description and not product_id: # Skip rows where no product is selected and no custom description
                continue
            if quantity <= 0 or unit_price < 0: # Basic validation
                QMessageBox.warning(self, self.tr("Données Invalides"),
                                    self.tr("Ligne {0}: Quantité doit être positive et prix unitaire non-négatif.").format(row + 1))
                return

            line_items_payload.append({
                "product_id": product_id, # Can be None for custom items
                "description": description,
                "quantity": quantity,
                "unit_price": unit_price,
                "total_price": quantity * unit_price # Calculated server-side too, but good to send
            })

        if not line_items_payload:
            QMessageBox.warning(self, self.tr("Aucune Ligne"), self.tr("Veuillez ajouter au moins une ligne à la proforma."))
            return

        proforma_data = {
            "client_id": self.client_info.get('client_id'),
            "project_id": self.client_info.get('project_id'), # Optional, pass if available in client_info context
            "company_id": self.default_company_id,
            "currency": self.currency_edit.text().strip() or "EUR",
            "payment_terms": self.payment_terms_edit.text().strip(),
            "delivery_terms": self.delivery_terms_edit.text().strip(),
            "incoterms": self.incoterms_combo.currentText(),
            "named_place_of_delivery": self.named_place_edit.text().strip(),
            "notes": self.notes_edit.toPlainText().strip(),
            "vat_rate_percentage": self.vat_rate_spinbox.value(),
            "discount_rate_percentage": self.discount_rate_spinbox.value(),
            "target_language_code": "fr",
            "items": line_items_payload
        }

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            logging.info(f"Attempting to generate Proforma with data: {proforma_data}")
            success, response_data = post_proforma_invoice(proforma_data)

            if success:
                proforma_number = response_data.get("proforma_invoice_number", "N/A")
                pdf_url = response_data.get("proforma_pdf_url")

                QMessageBox.information(self, self.tr("Succès"),
                                        self.tr("Facture Proforma '{0}' générée avec succès.").format(proforma_number))

                if pdf_url:
                    reply = QMessageBox.question(self, self.tr("Télécharger PDF"),
                                                 self.tr("Voulez-vous télécharger et ouvrir le PDF de la proforma maintenant?"),
                                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                    if reply == QMessageBox.Yes:
                        downloads_path = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
                        if not downloads_path:
                            downloads_path = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation) # Fallback
                        if not downloads_path: # Ultimate fallback
                             downloads_path = os.path.expanduser("~")

                        # Sanitize proforma_number for use in filename
                        safe_proforma_number = "".join(c if c.isalnum() else "_" for c in proforma_number)
                        local_filename = f"Proforma_{safe_proforma_number}.pdf"
                        local_save_path = os.path.join(downloads_path, local_filename)

                        dl_success, dl_message = download_file(pdf_url, local_save_path)
                        if dl_success:
                            QMessageBox.information(self, self.tr("Téléchargement Réussi"),
                                                    self.tr("PDF sauvegardé sous: {0}").format(local_save_path))
                            from PyQt5.QtGui import QDesktopServices # Late import
                            QDesktopServices.openUrl(QUrl.fromLocalFile(local_save_path))
                        else:
                            QMessageBox.warning(self, self.tr("Échec du Téléchargement"),
                                                self.tr("Impossible de télécharger le PDF: {0}").format(dl_message))
                self.accept() # Close dialog on success
            else:
                # response_data here is an error message string
                QMessageBox.critical(self, self.tr("Erreur API"),
                                     self.tr("La génération de la proforma a échoué: {0}").format(response_data))

        except Exception as e:
            logging.error(f"Error generating proforma: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Inattendue"),
                                 self.tr("Une erreur est survenue: {str(e)}"))
        finally:
            QApplication.restoreOverrideCursor()

# Example Usage (for testing the dialog standalone)
if __name__ == '__main__':
    import sys
    # Basic logging setup for testing
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Mock db_manager functions for standalone testing
    # In a real app, db_manager would be properly initialized.

    def mock_get_default_company():
        return {"company_id": "comp-test-001", "company_name": "Test Seller Inc.", "city": "Seller City"}

    def mock_get_all_products_for_selection():
        return [
            {"product_id": "prod-aaa", "product_name": "Produit Alpha", "product_code": "P-ALPHA", "base_unit_price": 100.0, "description": "Description Alpha"},
            {"product_id": "prod-bbb", "product_name": "Service Beta", "product_code": "S-BETA", "base_unit_price": 50.0, "description": "Description Beta"},
            {"product_id": "prod-ccc", "product_name": "Article Gamma", "product_code": "A-GAMMA", "base_unit_price": 75.50, "description": "Description Gamma"},
        ]

    def mock_get_company_by_id_from_db(company_id): # Mock for _load_client_data fallback
        if company_id == "comp-test-001":
            return {"company_id": "comp-test-001", "company_name": "Test Seller Inc.", "city": "Seller City"}
        return None

    db_manager.get_default_company = mock_get_default_company
    db_manager.get_all_products_for_selection = mock_get_all_products_for_selection
    db_manager.get_company_by_id_from_db = mock_get_company_by_id_from_db


    app = QApplication(sys.argv)

    # Ensure icons are loaded if your main app does this via resources_rc
    # import icons_rc # Assuming icons_rc.py is in the path or generated

    mock_client_info = {
        "client_id": "client-test-123",
        "client_name": "Test Client SARL",
        "project_id": "proj-test-456", # Optional
        "city": "Clientville"
    }
    mock_user_info = {
        "user_id": "user-xyz",
        "username": "testuser"
    }

    dialog = ProformaDialog(client_info=mock_client_info, current_user_info=mock_user_info)
    if dialog.exec_() == QDialog.Accepted:
        print("Proforma Dialog accepted (simulated generation).")
    else:
        print("Proforma Dialog cancelled.")
    sys.exit(app.exec_())

# End of invoicing/proforma_dialog.py
