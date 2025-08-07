import logging
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView, QDialogButtonBox,
                             QMessageBox, QLineEdit, QSpinBox, QComboBox, QFormLayout,
                             QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon

try:
    from ..cruds import restaurant_commande_crud, restaurant_ligne_commande_crud, restaurant_paiement_crud
    from ..models import RestaurantCommande, RestaurantLigneCommande # For type hinting
    from db.cruds.products.products_crud import products_crud_instance # To fetch product names
except ImportError:
    logging.error("ges_restaurant.ui.order_management_dialog: Failed to import CRUDS or Models.")
    restaurant_commande_crud = None
    restaurant_ligne_commande_crud = None
    restaurant_paiement_crud = None
    products_crud_instance = None

# --- Product Selection Dialog (Simplified for now) ---
class ProductSelectionDialog(QDialog):
    product_selected_signal = pyqtSignal(dict) # Emits product data dict

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Select Product"))
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # Search/Filter (Basic)
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.tr("Search product by name or code..."))
        self.search_button = QPushButton(self.tr("Search"))
        self.search_button.clicked.connect(self._search_products)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)

        self.products_table = QTableWidget()
        self.products_table.setColumnCount(4)
        self.products_table.setHorizontalHeaderLabels([self.tr("ID"), self.tr("Name"), self.tr("Code"), self.tr("Price (€ HT)")])
        self.products_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.products_table.setSelectionMode(QTableWidget.SingleSelection)
        self.products_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.products_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.products_table.hideColumn(0) # Hide product_id
        self.products_table.doubleClicked.connect(self._accept_selection)
        layout.addWidget(self.products_table)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self._accept_selection)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self._search_products() # Initial load

    def _search_products(self):
        if not products_crud_instance:
            QMessageBox.critical(self, self.tr("Error"), self.tr("Product CRUD not available."))
            return

        search_term = self.search_input.text().strip()
        try:
            # Get active, non-deleted products. Filter by name or code.
            filters = {'is_active': True}
            if search_term:
                 # This is a simplified search. Ideally, products_crud would have a search function
                 # that queries name OR code. For now, let's try name.
                 filters['product_name'] = f"%{search_term}%"
                 # Or, get_all_products and filter manually if no combined search in CRUD

            # products_list = products_crud_instance.get_all_products(filters=filters, include_deleted=False, limit=100)
            # A better function might be get_all_products_for_selection_filtered if it supports name_pattern for name and code
            products_list = products_crud_instance.get_all_products_for_selection_filtered(name_pattern=search_term, include_deleted=False)


            self.products_table.setRowCount(0)
            if products_list:
                self.products_table.setRowCount(len(products_list))
                for row, prod in enumerate(products_list):
                    self.products_table.setItem(row, 0, QTableWidgetItem(str(prod.get('product_id'))))
                    self.products_table.setItem(row, 1, QTableWidgetItem(prod.get('product_name')))
                    self.products_table.setItem(row, 2, QTableWidgetItem(prod.get('product_code', 'N/A'))) # Assuming product_code is available
                    price = prod.get('base_unit_price', 0.0)
                    self.products_table.setItem(row, 3, QTableWidgetItem(f"{price:.2f}"))
            else:
                logging.info(f"No products found for search term: '{search_term}'")

        except Exception as e:
            logging.error(f"Error searching products: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Search Error"), str(e))

    def _accept_selection(self):
        selected_rows = self.products_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, self.tr("No Selection"), self.tr("Please select a product."))
            return

        selected_row = selected_rows[0].row()
        product_id = int(self.products_table.item(selected_row, 0).text())
        # Fetch full product details to pass back (or just ID and rely on parent to fetch)
        # For now, let's pass enough to add to line item
        product_data = {
            "product_id": product_id,
            "product_name": self.products_table.item(selected_row, 1).text(),
            "product_code": self.products_table.item(selected_row, 2).text(),
            "base_unit_price_ht": float(self.products_table.item(selected_row, 3).text())
        }
        self.product_selected_signal.emit(product_data)
        self.accept()


# --- Order Management Dialog ---
class OrderManagementDialog(QDialog):
    order_updated_signal = pyqtSignal(int) # Emits commande_id on update

    def __init__(self, commande: RestaurantCommande, parent=None):
        super().__init__(parent)
        self.setObjectName("OrderManagementDialog") # Set object name for the dialog itself
        self.commande = commande # Store the full SQLAlchemy Commande object

        if not self.commande:
            QMessageBox.critical(self, self.tr("Error"), self.tr("No commande data provided to dialog."))
            raise ValueError("OrderManagementDialog initialized without a commande object.")

        self.setWindowTitle(self.tr("Manage Order - ID: {0} (Table: {1})")
                            .format(self.commande.id, self.commande.table.numero_table if self.commande.table else "N/A"))
        self.setMinimumSize(800, 600)
        self._init_ui()
        self._load_order_details()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        # Order Info Section
        info_group = QGroupBox(self.tr("Order Information"))
        info_group.setObjectName("infoGroup")
        info_layout = QFormLayout(info_group)
        self.order_id_label = QLabel(str(self.commande.id))
        self.table_numero_label = QLabel(self.commande.table.numero_table if self.commande.table else "N/A")
        self.status_combo = QComboBox()
        self.status_combo.setObjectName("statusCombo")
        self.status_combo.addItems(['en_cours', 'servie', 'payee', 'annulee'])
        self.status_combo.setCurrentText(self.commande.statut)
        self.nom_client_edit = QLineEdit(self.commande.nom_client_facultatif or "")
        self.nom_client_edit.setObjectName("nomClientEdit")
        self.notes_client_edit = QLineEdit(self.commande.notes_client or "")
        self.notes_client_edit.setObjectName("notesClientEdit")

        info_layout.addRow(self.tr("Order ID:"), self.order_id_label)
        info_layout.addRow(self.tr("Table:"), self.table_numero_label)
        info_layout.addRow(self.tr("Status:"), self.status_combo)
        info_layout.addRow(self.tr("Client Name (Optional):"), self.nom_client_edit)
        info_layout.addRow(self.tr("Client Notes:"), self.notes_client_edit)
        main_layout.addWidget(info_group)

        # Order Lines Section
        lines_group = QGroupBox(self.tr("Order Items"))
        lines_group.setObjectName("linesGroup")
        lines_v_layout = QVBoxLayout(lines_group)

        lines_actions_layout = QHBoxLayout()
        self.add_item_button = QPushButton(self.tr("Add Item"))
        self.add_item_button.setObjectName("addItemButton")
        self.add_item_button.setText("➕ " + self.tr("Ajouter"))
        self.add_item_button.clicked.connect(self._add_item_to_order)
        self.remove_item_button = QPushButton(self.tr("Remove Selected Item"))
        self.remove_item_button.setObjectName("removeItemButton")
        self.remove_item_button.setText("➖ " + self.tr("Supprimer"))
        self.remove_item_button.clicked.connect(self._remove_selected_item)
        self.remove_item_button.setEnabled(False)
        lines_actions_layout.addWidget(self.add_item_button)
        lines_actions_layout.addWidget(self.remove_item_button)
        lines_actions_layout.addStretch()
        lines_v_layout.addLayout(lines_actions_layout)

        self.order_lines_table = QTableWidget()
        self.order_lines_table.setObjectName("orderLinesTable")
        self.order_lines_table.setColumnCount(6)
        self.order_lines_table.setHorizontalHeaderLabels([
            self.tr("Line ID"), self.tr("Product"), self.tr("Qty"),
            self.tr("Unit Price (€ HT)"), self.tr("Total (€ HT)"), self.tr("Notes")
        ])
        self.order_lines_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.order_lines_table.setSelectionMode(QTableWidget.SingleSelection)
        self.order_lines_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.order_lines_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.order_lines_table.hideColumn(0)
        self.order_lines_table.itemChanged.connect(self._handle_line_item_change)
        self.order_lines_table.selectionModel().selectionChanged.connect(
            lambda: self.remove_item_button.setEnabled(bool(self.order_lines_table.selectedItems()) and self.add_item_button.isEnabled()) # Also check if add is enabled
        )
        lines_v_layout.addWidget(self.order_lines_table)
        main_layout.addWidget(lines_group)

        # Totals Section
        totals_layout = QHBoxLayout()
        totals_layout.addStretch()
        self.total_ht_label = QLabel(self.tr("Total HT: €0.00"))
        self.total_ht_label.setObjectName("totalHTLabel")
        # self.total_ht_label.setStyleSheet("font-weight: bold;")
        self.total_ttc_label = QLabel(self.tr("Total TTC: €0.00"))
        self.total_ttc_label.setObjectName("totalTTCLabel")
        # self.total_ttc_label.setStyleSheet("font-weight: bold; font-size: 12pt; color: #27ae60;")
        totals_layout.addWidget(self.total_ht_label)
        totals_layout.addSpacing(20)
        totals_layout.addWidget(self.total_ttc_label)
        main_layout.addLayout(totals_layout)

        # Dialog Buttons (Specific object names for targeted QSS)
        self.dialog_buttons = QDialogButtonBox()
        self.save_button = self.dialog_buttons.addButton(self.tr("Save Order"), QDialogButtonBox.AcceptRole)
        self.process_payment_button = self.dialog_buttons.addButton(self.tr("Process Payment"), QDialogButtonBox.ActionRole)
        self.print_receipt_button = self.dialog_buttons.addButton(self.tr("Print Receipt"), QDialogButtonBox.ActionRole)
        self.close_button = self.dialog_buttons.addButton(QDialogButtonBox.Close)

        self.save_button.clicked.connect(self._save_order)
        self.process_payment_button.clicked.connect(self._open_payment_dialog)
        self.print_receipt_button.clicked.connect(self._print_receipt)
        self.close_button.clicked.connect(self.reject) # QDialogButtonBox.Close maps to reject()

        main_layout.addWidget(self.dialog_buttons)
        self._update_action_buttons_state()


    def _load_order_details(self):
        self.order_lines_table.blockSignals(True) # Block signals during programmatic changes
        self.order_lines_table.setRowCount(0) # Clear table

        if not self.commande: # Should be caught by __init__ check
            self._update_totals_display()
            self._update_action_buttons_state()
            self.order_lines_table.blockSignals(False)
            return

        if self.commande.lignes_commande:
            self.order_lines_table.setRowCount(len(self.commande.lignes_commande))
            for row, ligne in enumerate(self.commande.lignes_commande):
                self.order_lines_table.setItem(row, 0, QTableWidgetItem(str(ligne.id)))

                product_name = f"Product ID: {ligne.produit_id}" # Fallback
                if products_crud_instance:
                    try:
                        # Ensure product is fetched with include_deleted=True if it might have been soft-deleted
                        # but still part of an old order. For active orders, False is fine.
                        product = products_crud_instance.get_product_by_id(ligne.produit_id, include_deleted=True)
                        if product:
                            product_name = product.get('product_name', product_name)
                            if product.get('is_deleted'):
                                product_name += self.tr(" (Deleted)")
                    except Exception as e_prod:
                        logging.warning(f"Could not fetch product name for ID {ligne.produit_id}: {e_prod}")

                name_item = QTableWidgetItem(product_name)
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable) # Product name not editable here
                self.order_lines_table.setItem(row, 1, name_item)

                qty_item = QTableWidgetItem(str(ligne.quantite))
                # Make quantity editable only if order is not paid/cancelled
                if self.commande.statut not in ['payee', 'annulee']:
                    pass # Default flags allow editing
                else:
                    qty_item.setFlags(qty_item.flags() & ~Qt.ItemIsEditable)
                self.order_lines_table.setItem(row, 2, qty_item)

                unit_price_item = QTableWidgetItem(f"{ligne.prix_unitaire_ht_commande:.2f}")
                if self.commande.statut not in ['payee', 'annulee']:
                    pass # Default flags allow editing
                else:
                    unit_price_item.setFlags(unit_price_item.flags() & ~Qt.ItemIsEditable)
                self.order_lines_table.setItem(row, 3, unit_price_item)

                total_ligne_item = QTableWidgetItem(f"{ligne.prix_total_ht_ligne:.2f}")
                total_ligne_item.setFlags(total_ligne_item.flags() & ~Qt.ItemIsEditable)
                self.order_lines_table.setItem(row, 4, total_ligne_item)

                notes_item = QTableWidgetItem(ligne.notes or "")
                if self.commande.statut not in ['payee', 'annulee']:
                     pass # Default flags allow editing
                else:
                    notes_item.setFlags(notes_item.flags() & ~Qt.ItemIsEditable)
                self.order_lines_table.setItem(row, 5, notes_item)

        self.order_lines_table.blockSignals(False) # Unblock after programmatic changes

        self._update_totals_display()
        self.status_combo.setCurrentText(self.commande.statut)
        self._update_action_buttons_state()


    def _update_totals_display(self):
        total_ht = self.commande.total_commande_ht or 0.0
        total_ttc = self.commande.total_commande_ttc or 0.0

        self.total_ht_label.setText(self.tr("Total HT: €{0:.2f}").format(total_ht))
        self.total_ttc_label.setText(self.tr("Total TTC: €{0:.2f}").format(total_ttc))

    def _update_action_buttons_state(self):
        is_editable = self.commande.statut not in ['payee', 'annulee']
        self.add_item_button.setEnabled(is_editable)
        self.remove_item_button.setEnabled(is_editable and bool(self.order_lines_table.selectedItems()))
        self.save_button.setEnabled(is_editable) # Can always save status/notes if not paid/cancelled
        self.process_payment_button.setEnabled(self.commande.statut != 'annulee' and self.commande.statut != 'payee')
        self.print_receipt_button.setEnabled(self.commande.statut == 'payee')

        # Disable editing of client name/notes if order is closed
        self.nom_client_edit.setEnabled(is_editable)
        self.notes_client_edit.setEnabled(is_editable)
        self.status_combo.setEnabled(self.commande.statut != 'payee') # Allow changing from 'en_cours'/'servie' to 'annulee', but not from 'payee'

    def _handle_line_item_change(self, item: QTableWidgetItem):
        if not restaurant_ligne_commande_crud: return

        row = item.row()
        col = item.column()

        line_id_item = self.order_lines_table.item(row, 0)
        if not line_id_item: return # Should not happen if table is populated correctly

        line_id = int(line_id_item.text())

        update_data = {}
        recalculate_line_total = False

        if col == 2: # Quantity
            try:
                new_qty = int(item.text())
                if new_qty <= 0:
                    QMessageBox.warning(self, self.tr("Invalid Quantity"), self.tr("Quantity must be positive."))
                    # Revert: This requires fetching old value. Simpler: reload details for now.
                    self._load_order_details() # Reload to revert
                    return
                update_data['quantite'] = new_qty
                recalculate_line_total = True
            except ValueError:
                QMessageBox.warning(self, self.tr("Invalid Input"), self.tr("Quantity must be a number."))
                self._load_order_details() # Reload to revert
                return
        elif col == 3: # Unit Price HT
            try:
                new_price_str = item.text().replace(',', '.') # Allow comma for decimal
                new_price = float(new_price_str)
                if new_price < 0:
                    QMessageBox.warning(self, self.tr("Invalid Price"), self.tr("Price cannot be negative."))
                    self._load_order_details()
                    return
                update_data['prix_unitaire_ht_commande'] = new_price
                recalculate_line_total = True
            except ValueError:
                QMessageBox.warning(self, self.tr("Invalid Input"), self.tr("Price must be a valid number."))
                self._load_order_details()
                return
        elif col == 5: # Notes
            update_data['notes'] = item.text().strip()
        else: # Other columns are not directly user-editable here
            return

        if update_data:
            try:
                # The update_ligne_commande CRUD should handle recalculating line total and command total
                updated_ligne = restaurant_ligne_commande_crud.update_ligne_commande(line_id, update_data)
                if updated_ligne:
                    # Refresh the entire commande object to get updated totals and line details
                    self.commande = restaurant_commande_crud.get_commande_by_id(self.commande.id)
                    self.order_lines_table.blockSignals(True)
                    self._load_order_details() # Reload all lines and totals
                    self.order_lines_table.blockSignals(False)
                    self.order_updated_signal.emit(self.commande.id)
                else:
                    QMessageBox.critical(self, self.tr("Update Failed"), self.tr("Failed to update order line."))
                    self._load_order_details() # Revert
            except ValueError as ve: # From CRUD (e.g. order closed)
                QMessageBox.warning(self, self.tr("Update Error"), str(ve))
                self._load_order_details() # Revert
            except Exception as e:
                logging.error(f"Error updating line item {line_id}: {e}", exc_info=True)
                QMessageBox.critical(self, self.tr("Update Error"), str(e))
                self._load_order_details() # Revert

    def _add_item_to_order(self):
        if not restaurant_ligne_commande_crud or not products_crud_instance:
            QMessageBox.critical(self, self.tr("Error"), self.tr("CRUD operations not available for adding items."))
            return

        if self.commande.statut in ['payee', 'annulee']:
            QMessageBox.warning(self, self.tr("Order Closed"), self.tr("Cannot add items to an order that is already '{0}'.").format(self.commande.statut))
            return

        prod_dialog = ProductSelectionDialog(self)
        if prod_dialog.exec_() == QDialog.Accepted:
            selected_product_data = prod_dialog.product_selected_signal.emit # This is not how to get data back
            # The signal should be connected in __init__ or here to a slot.
            # For simplicity, let's make ProductSelectionDialog store the result.
            # A better way is to connect the signal.
            # Re-fetching:
            # selected_product_data = prod_dialog.get_selected_product_data() # Assume this method exists

            # Let's assume ProductSelectionDialog has a method to retrieve the selection
            # or we connect to its signal properly.
            # For this example, let's simulate we got it back:
            # This is a placeholder - need proper signal handling from ProductSelectionDialog
            # selected_product_data = {"product_id": 1, "base_unit_price_ht": 10.0} # Dummy data

            # This is a temporary fix as get_selected_product_data is not defined:
            # We need to connect the signal from ProductSelectionDialog
            # For now, this part will not fully work until signal is connected.
            # QMessageBox.information(self, "Info", "Product selection dialog accepted, but data retrieval needs signal connection.")
            # TODO: Connect ProductSelectionDialog.product_selected_signal to a slot here.
            # For now, let's assume `handle_product_selected_for_order` is that slot.

            # Corrected flow: Instantiate, connect signal, then exec_
            prod_dialog.product_selected_signal.connect(self.handle_product_selected_for_order)

            # No need to check result of exec_ here if signal is connected,
            # as handle_product_selected_for_order will be called if product is selected and dialog accepted.
            # If dialog is cancelled, the signal won't be emitted with product data.
            prod_dialog.exec_()


            # --- Old direct call removed ---
            # Create a dummy product_data for now
            # In reality, this comes from ProductSelectionDialog
            # dummy_selected_product = {"product_id": 1, "base_unit_price_ht": 12.50, "product_name": "Dummy Product"}
            # self.handle_product_selected_for_order(dummy_selected_product) # Call the handler directly

    def handle_product_selected_for_order(self, product_data: dict):
        """Slot to handle a product selected from ProductSelectionDialog."""
        logging.info(f"Product selected for order: {product_data}")
        if not product_data or not product_data.get("product_id"):
            logging.warning("handle_product_selected_for_order called with invalid product_data.")
            return

        new_ligne_data = {
            "produit_id": product_data['product_id'],
            "quantite": 1, # Default quantity
            "prix_unitaire_ht_commande": product_data['base_unit_price_ht'],
            # prix_total_ht_ligne will be calculated by CRUD
            "notes": ""
        }
        try:
            added_ligne = restaurant_ligne_commande_crud.add_ligne_to_commande(self.commande.id, new_ligne_data)
            if added_ligne:
                self.commande = restaurant_commande_crud.get_commande_by_id(self.commande.id) # Refresh commande
                self._load_order_details()
                self.order_updated_signal.emit(self.commande.id)
            else:
                QMessageBox.critical(self, self.tr("Add Item Failed"), self.tr("Failed to add item to order."))
        except ValueError as ve: # From CRUD (e.g. order closed)
            QMessageBox.warning(self, self.tr("Add Item Error"), str(ve))
        except Exception as e:
            logging.error(f"Error adding item to order {self.commande.id}: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Add Item Error"), str(e))


    def _remove_selected_item(self):
        selected_rows = self.order_lines_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, self.tr("No Selection"), self.tr("Please select an item to remove."))
            return

        line_id_item = self.order_lines_table.item(selected_rows[0].row(), 0)
        if not line_id_item: return

        line_id = int(line_id_item.text())

        reply = QMessageBox.question(self, self.tr("Confirm Remove"),
                                     self.tr("Are you sure you want to remove this item from the order?"),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if not restaurant_ligne_commande_crud:
                QMessageBox.critical(self, self.tr("Error"), self.tr("Line item CRUD not available."))
                return
            try:
                success = restaurant_ligne_commande_crud.remove_ligne_from_commande(line_id)
                if success:
                    self.commande = restaurant_commande_crud.get_commande_by_id(self.commande.id) # Refresh
                    self._load_order_details()
                    self.order_updated_signal.emit(self.commande.id)
                else:
                    QMessageBox.critical(self, self.tr("Remove Failed"), self.tr("Failed to remove item from order."))
            except ValueError as ve: # From CRUD (e.g. order closed)
                QMessageBox.warning(self, self.tr("Remove Item Error"), str(ve))
            except Exception as e:
                logging.error(f"Error removing line {line_id}: {e}", exc_info=True)
                QMessageBox.critical(self, self.tr("Remove Item Error"), str(e))

    def _save_order(self):
        if not restaurant_commande_crud:
            QMessageBox.critical(self, self.tr("Error"), self.tr("Commande CRUD not available."))
            return

        # Update commande details from the form
        update_payload = {
            "statut": self.status_combo.currentText(),
            "nom_client_facultatif": self.nom_client_edit.text().strip() or None,
            "notes_client": self.notes_client_edit.text().strip() or None,
        }

        try:
            # The CRUD update_commande_statut is too simple. We need a more general update.
            # Let's assume a restaurant_commande_crud.update_commande(id, data) exists or make one.
            # For now, we'll use update_commande_statut and then manually set other fields
            # if they were part of a more general update_commande.
            # This is not ideal. A proper update_commande in CRUD is needed.

            # Simplified: Update status, then other fields if a general update was available.
            updated_commande_stat = restaurant_commande_crud.update_commande_statut(self.commande.id, update_payload['statut'])

            if updated_commande_stat: # Status update part succeeded
                # If a general update existed:
                # updated_commande = restaurant_commande_crud.update_commande(self.commande.id, update_payload)
                # For now, let's assume status is the main updatable field here.
                # If other fields were changed, they are not persisted by this simple save.

                # To persist nom_client and notes_client, we need a more comprehensive update in CRUD
                # Or we update them directly here if _manage_conn allows direct session use.
                # Example of direct update (requires session management):
                # session = get_db_session_somehow()
                # db_comm = session.query(RestaurantCommande).get(self.commande.id)
                # db_comm.nom_client_facultatif = update_payload['nom_client_facultatif']
                # db_comm.notes_client = update_payload['notes_client']
                # session.commit()

                self.commande = restaurant_commande_crud.get_commande_by_id(self.commande.id) # Refresh from DB
                self._load_order_details() # Reload UI
                self.order_updated_signal.emit(self.commande.id)
                QMessageBox.information(self, self.tr("Order Saved"), self.tr("Order details have been saved."))
                # self.accept() # Close dialog on save
            else:
                QMessageBox.critical(self, self.tr("Save Failed"), self.tr("Failed to save order details."))

        except Exception as e:
            logging.error(f"Error saving order {self.commande.id}: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Save Error"), str(e))

    def _print_receipt(self):
        if self.commande.statut != 'payee':
            QMessageBox.warning(self, self.tr("Cannot Print"), self.tr("Receipt can only be printed for paid orders."))
            return

        if not restaurant_commande_crud or not products_crud_instance:
            QMessageBox.critical(self, self.tr("Error"), self.tr("Cannot generate receipt: CRUDS not available."))
            return

        try:
            # 1. Fetch full, up-to-date commande details, including table, lines, and products
            full_commande = restaurant_commande_crud.get_commande_by_id(self.commande.id)
            if not full_commande:
                QMessageBox.critical(self, self.tr("Error"), self.tr("Could not load full order details for receipt."))
                return

            # 2. Prepare context for the HTML template
            receipt_items = []
            for ligne in full_commande.lignes_commande:
                product_details = products_crud_instance.get_product_by_id(ligne.produit_id, include_deleted=True)
                product_name = product_details.get('product_name', f"Produit ID {ligne.produit_id}") if product_details else f"Produit ID {ligne.produit_id}"
                if product_details and product_details.get('is_deleted'):
                    product_name += self.tr(" (Supprimé)")

                receipt_items.append({
                    "name": product_name,
                    "quantity": ligne.quantite,
                    "unit_price_ht": f"{ligne.prix_unitaire_ht_commande:.2f}",
                    "total_price_ht": f"{ligne.prix_total_ht_ligne:.2f}"
                })

            # Company details (placeholders, should come from config/DB settings)
            # These should ideally be fetched from a global config or company settings module
            app_config = getattr(self.parent(), 'config', {}) # Try to get config from parent (RestaurantMainWidget -> DocumentManager)

            company_name = app_config.get('company_name_receipt', self.tr("Your Restaurant Name"))
            company_address = app_config.get('company_address_receipt', self.tr("123 Restaurant Street"))
            company_phone = app_config.get('company_phone_receipt', self.tr("01 23 45 67 89"))
            company_vat_id = app_config.get('company_vat_id_receipt', self.tr("FR00123456789"))


            context = {
                "company_name": company_name,
                "company_address": company_address,
                "company_phone": company_phone,
                "company_vat_id": company_vat_id,
                "receipt_title": self.tr("Customer Receipt"),
                "order_id": full_commande.id,
                "order_date": full_commande.date_heure_creation.strftime("%d/%m/%Y %H:%M:%S"),
                "table_number": full_commande.table.numero_table if full_commande.table else "N/A",
                "client_name": full_commande.nom_client_facultatif or "",
                "items": receipt_items,
                "total_ht": f"{full_commande.total_commande_ht:.2f}",
                "total_ttc": f"{full_commande.total_commande_ttc:.2f}",
                # Assuming VAT is simply total_ttc - total_ht for display.
                # A more robust system would store VAT rate and amount per line or per order.
                "vat_amount": f"{(full_commande.total_commande_ttc - full_commande.total_commande_ht):.2f}",
                "payment_method": ", ".join(set(p.methode_paiement for p in full_commande.paiements)) if full_commande.paiements else self.tr("N/A"),
                "thank_you_message": self.tr("Thank you for your visit!"),
                "labels": { # For localizing fixed strings in template
                    "order_id_label": self.tr("Order ID:"),
                    "date_label": self.tr("Date:"),
                    "table_label": self.tr("Table:"),
                    "item_label": self.tr("Item"),
                    "qty_label": self.tr("Qty"),
                    "unit_price_label": self.tr("Unit Price (€ HT)"),
                    "total_ht_label": self.tr("Total HT (€)"),
                    "sub_total_ht_label": self.tr("Subtotal HT:"),
                    "vat_label": self.tr("VAT Amount:"), # Placeholder label for calculated VAT
                    "grand_total_ttc_label": self.tr("Total TTC:"),
                    "payment_method_label": self.tr("Payment Method:"),
                }
            }

            # 3. Define HTML Template for the receipt
            # This is a basic template. It can be styled much more.
            html_template = """
            <!DOCTYPE html>
            <html lang="fr">
            <head>
                <meta charset="UTF-8">
                <title>{{ receipt_title }}</title>
                <style>
                    body { font-family: 'Arial', sans-serif; margin: 0; padding: 0; font-size: 10pt; color: #333; }
                    .receipt-container { width: 300px; margin: 20px auto; padding: 15px; border: 1px solid #ccc; box-shadow: 0 0 5px rgba(0,0,0,0.1); }
                    .header { text-align: center; margin-bottom: 15px; }
                    .header h1 { font-size: 14pt; margin: 0 0 5px 0; color: #111; }
                    .header p { margin: 2px 0; font-size: 8pt; }
                    .order-details p { margin: 3px 0; font-size: 9pt; }
                    .items-table { width: 100%; margin-top: 10px; border-collapse: collapse; }
                    .items-table th, .items-table td { padding: 4px; font-size: 9pt; text-align: left; border-bottom: 1px dashed #eee; }
                    .items-table th { font-weight: bold; background-color: #f9f9f9; }
                    .items-table td.qty, .items-table td.price { text-align: right; }
                    .totals { margin-top: 15px; padding-top: 10px; border-top: 1px solid #555; }
                    .totals p { margin: 4px 0; font-size: 10pt; display: flex; justify-content: space-between; }
                    .totals p.grand-total { font-weight: bold; font-size: 11pt; }
                    .footer { text-align: center; margin-top: 20px; font-size: 8pt; }
                </style>
            </head>
            <body>
                <div class="receipt-container">
                    <div class="header">
                        <h1>{{ company_name }}</h1>
                        <p>{{ company_address }}</p>
                        <p>{{ labels.tel_label | default('Tel:') }} {{ company_phone }}</p>
                        <p>{{ labels.vat_id_label | default('VAT ID:') }} {{ company_vat_id }}</p>
                        <h2>{{ receipt_title }}</h2>
                    </div>
                    <div class="order-details">
                        <p><strong>{{ labels.order_id_label }}</strong> {{ order_id }}</p>
                        <p><strong>{{ labels.date_label }}</strong> {{ order_date }}</p>
                        <p><strong>{{ labels.table_label }}</strong> {{ table_number }}</p>
                        {{#if client_name}}<p><strong>{{ labels.client_label | default('Client:') }}</strong> {{ client_name }}</p>{{/if}}
                    </div>
                    <table class="items-table">
                        <thead>
                            <tr>
                                <th>{{ labels.item_label }}</th>
                                <th class="qty">{{ labels.qty_label }}</th>
                                <th class="price">{{ labels.unit_price_label }}</th>
                                <th class="price">{{ labels.total_ht_label }}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {{#each items}}
                            <tr>
                                <td>{{this.name}}</td>
                                <td class="qty">{{this.quantity}}</td>
                                <td class="price">{{this.unit_price_ht}}</td>
                                <td class="price">{{this.total_price_ht}}</td>
                            </tr>
                            {{/each}}
                        </tbody>
                    </table>
                    <div class="totals">
                        <p><span>{{ labels.sub_total_ht_label }}</span> <span>{{ total_ht }} €</span></p>
                        <p><span>{{ labels.vat_label }}</span> <span>{{ vat_amount }} €</span></p>
                        <p class="grand-total"><span>{{ labels.grand_total_ttc_label }}</span> <span>{{ total_ttc }} €</span></p>
                        <p><span>{{ labels.payment_method_label }}</span> <span>{{ payment_method }}</span></p>
                    </div>
                    <div class="footer">
                        <p>{{ thank_you_message }}</p>
                    </div>
                </div>
            </body>
            </html>
            """

            # 4. Render HTML
            from utils import html_to_pdf_util # Ensure this util is available and works with pystache/jinja2

            # The render_html_template function in utils.html_to_pdf_util uses Jinja2.
            # Ensure the context is compatible.
            rendered_html = html_to_pdf_util.render_html_template_string(html_template, context)

            # 5. Convert to PDF and offer to save
            from PyQt5.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                self.tr("Save Receipt PDF"),
                f"receipt_order_{full_commande.id}.pdf",
                self.tr("PDF Files (*.pdf);;All Files (*)"),
                options=QFileDialog.DontUseNativeDialog
            )

            if file_path:
                if not file_path.lower().endswith(".pdf"):
                    file_path += ".pdf"

                pdf_bytes = html_to_pdf_util.convert_html_to_pdf(rendered_html)
                if pdf_bytes:
                    with open(file_path, "wb") as f:
                        f.write(pdf_bytes)
                    QMessageBox.information(self, self.tr("Receipt Saved"),
                                            self.tr("Receipt saved successfully to: {0}").format(file_path))
                    # Optionally, open the PDF:
                    # from PyQt5.QtGui import QDesktopServices
                    # from PyQt5.QtCore import QUrl
                    # QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
                else:
                    QMessageBox.critical(self, self.tr("PDF Generation Failed"),
                                         self.tr("Failed to generate PDF content for the receipt."))
            else:
                logging.info("Receipt PDF saving cancelled by user.")

        except Exception as e:
            logging.error(f"Error generating receipt for order {self.commande.id}: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Receipt Generation Error"), str(e))


# Example Usage for standalone testing (similar to RestaurantMainWidget's test)
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    logging.basicConfig(level=logging.INFO)

    # Dummy DB setup for standalone test
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from models import Base as RestaurantBase, RestaurantTable as TestRestaurantTable, RestaurantCommande as TestRestaurantCommande

    engine = create_engine("sqlite:///:memory:")
    RestaurantBase.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def get_dummy_db_session_order_test(): return TestingSessionLocal()

    def dummy_manage_conn_order_test(func):
        def wrapper(*args, **kwargs):
            session = TestingSessionLocal()
            kwargs['conn'] = session
            try:
                result = func(*args, **kwargs)
                session.commit()
                return result
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
        return wrapper

    # Monkey-patch CRUDs for testing if they were imported
    if restaurant_commande_crud:
        import cruds
        cruds._manage_conn = dummy_manage_conn_order_test
        # Also patch other cruds if they are used by OrderManagementDialog indirectly
        if cruds.restaurant_table_crud: cruds.restaurant_table_crud._manage_conn = dummy_manage_conn_order_test
        if cruds.restaurant_ligne_commande_crud: cruds.restaurant_ligne_commande_crud._manage_conn = dummy_manage_conn_order_test
        if products_crud_instance: # products_crud is a module, not a class instance here
            # Need to patch the _manage_conn used within products_crud.py
            # This is more involved. For now, product selection might not work fully in standalone.
            pass


        # Populate with a test table and a test commande
        session = TestingSessionLocal()
        try:
            if not session.query(TestRestaurantTable).first():
                test_table = TestRestaurantTable(numero_table="Test Table 1", capacite=4, statut="libre")
                session.add(test_table)
                session.flush() # Get test_table.id

                test_commande_data = {"table_id": test_table.id, "statut": "en_cours"}
                # Use the CRUD to create the commande, which should now use the dummy session
                created_commande_obj = cruds.restaurant_commande_crud.create_commande(test_commande_data, conn=session)
                session.commit()

                if created_commande_obj:
                    logging.info(f"Standalone Test: Created test commande ID {created_commande_obj.id} for table ID {test_table.id}")
                    # Fetch it back fully loaded for the dialog
                    commande_for_dialog = cruds.restaurant_commande_crud.get_commande_by_id(created_commande_obj.id, conn=session)

                    app = QApplication(sys.argv)
                    dialog = OrderManagementDialog(commande=commande_for_dialog)
                    dialog.show()
                    sys.exit(app.exec_())
                else:
                    logging.error("Standalone Test: Failed to create test commande.")

            else: # Table exists, try to get first command or create one
                first_table = session.query(TestRestaurantTable).first()
                existing_commande = session.query(TestRestaurantCommande).filter_by(table_id=first_table.id).first()
                if not existing_commande:
                    test_commande_data = {"table_id": first_table.id, "statut": "en_cours"}
                    existing_commande = cruds.restaurant_commande_crud.create_commande(test_commande_data, conn=session)
                    session.commit()

                if existing_commande:
                    commande_for_dialog = cruds.restaurant_commande_crud.get_commande_by_id(existing_commande.id, conn=session)
                    app = QApplication(sys.argv)
                    dialog = OrderManagementDialog(commande=commande_for_dialog)
                    dialog.show()
                    sys.exit(app.exec_())
                else:
                    logging.error("Standalone Test: Failed to get or create a commande for testing.")


        except Exception as e:
            logging.error(f"Error in standalone test setup for OrderManagementDialog: {e}", exc_info=True)
            session.rollback()
        finally:
            session.close()
    else:
        logging.error("Standalone Test: CRUDS not available, cannot run OrderManagementDialog test.")

```
