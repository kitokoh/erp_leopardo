# -*- coding: utf-8 -*-
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QTextEdit,
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QDateEdit, QDialogButtonBox, QLabel,
    QDoubleSpinBox, QSpinBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QDate

import db # Assuming db.__init__ exposes necessary cruds
from db.cruds import commandes_crud, products_crud, projects_crud, status_settings_crud
from dialogs.product_dialog import ProductDialog # Import ProductDialog



class CommandeDialog(QDialog):
    def __init__(self, client_id, current_user_id, commande_id_to_edit=None, parent=None):
        super().__init__(parent)
        self.client_id = client_id
        self.current_user_id = current_user_id
        self.commande_id_to_edit = commande_id_to_edit
        self.commande_data = None # To store fetched data if editing
        self.commande_items_data = [] # To store line items

        self.logger = logging.getLogger(__name__)

        self.setWindowTitle("Nouvelle Commande" if not commande_id_to_edit else "Modifier Commande")
        self.setMinimumSize(900, 600) # Increased size for product list

        self.setup_ui()

        if not self.commande_id_to_edit: # New Commande
            self.commande_reference_edit.setText(commandes_crud.get_next_commande_reference())

        self.populate_combos()
        self._populate_product_selection_list() # Populate the new product list

        if self.commande_id_to_edit:
            self.load_commande_data_for_edit()

    def setup_ui(self):
        overall_layout = QHBoxLayout(self) # Main layout is now horizontal

        # --- Left Panel: Product Selection ---
        left_panel_widget = QWidget()
        left_panel_layout = QVBoxLayout(left_panel_widget)
        left_panel_layout.addWidget(QLabel(self.tr("Produits Disponibles:")))

        self.product_search_input = QLineEdit()
        self.product_search_input.setPlaceholderText(self.tr("Rechercher produit..."))
        self.product_search_input.textChanged.connect(self._filter_product_selection_list)
        left_panel_layout.addWidget(self.product_search_input)

        self.product_selection_list = QListWidget() # Using QListWidget for simplicity
        self.product_selection_list.itemDoubleClicked.connect(self.add_selected_product_from_list_to_table)
        left_panel_layout.addWidget(self.product_selection_list)

        add_selected_product_button = QPushButton(self.tr("Ajouter Produit Sélectionné"))
        add_selected_product_button.clicked.connect(self.add_selected_product_from_list_to_table)
        left_panel_layout.addWidget(add_selected_product_button)

        left_panel_widget.setMinimumWidth(250)
        left_panel_widget.setMaximumWidth(350)
        overall_layout.addWidget(left_panel_widget)

        # --- Right Panel: Commande Details and Items ---
        right_panel_widget = QWidget()
        main_layout = QVBoxLayout(right_panel_widget) # This was the original main_layout

        # Form for Commande Details
        form_layout = QFormLayout()

        self.commande_reference_edit = QLineEdit()
        self.commande_reference_edit.setPlaceholderText("Ex: CMD-2023-0001")
        form_layout.addRow("Référence Commande:", self.commande_reference_edit)

        self.commande_date_edit = QDateEdit(QDate.currentDate())
        self.commande_date_edit.setCalendarPopup(True)
        self.commande_date_edit.setDisplayFormat("yyyy-MM-dd")
        form_layout.addRow("Date Commande:", self.commande_date_edit)

        self.status_commande_combo = QComboBox()
        form_layout.addRow("Statut Commande:", self.status_commande_combo)

        self.description_commande_edit = QTextEdit()
        self.description_commande_edit.setFixedHeight(60)
        form_layout.addRow("Description:", self.description_commande_edit)

        self.notes_edit = QTextEdit() # Added notes field
        self.notes_edit.setFixedHeight(80) # Added notes field
        self.notes_edit.setPlaceholderText("Entrez des notes spécifiques à cette commande...") # Added notes field
        form_layout.addRow("Notes Commande:", self.notes_edit) # Added notes field

        # Project linking (optional or for later)
        self.project_combo = QComboBox()
        self.project_combo.addItem("Aucun Projet Lié", None)
        # TODO: Populate with projects for this client, or allow creating new
        form_layout.addRow("Projet Associé:", self.project_combo)

        main_layout.addLayout(form_layout)

        # Line Items Section
        main_layout.addWidget(QLabel("Articles de la Commande:"))
        self.items_table = QTableWidget()
        # Product, Desc, Qty, Unit Price HT, VAT (%), Weight, Dimensions, Lang, Total HT, Total TTC
        self.items_table.setColumnCount(10)
        self.items_table.setHorizontalHeaderLabels([
            "Produit", "Description", "Qté", "Prix Unitaire HT", "TVA (%)",
            "Poids", "Dimensions", "Langue Article", # Nouvelles colonnes
            "Total HT", "Total TTC"
        ])
        self.items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch) # Description
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.items_table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked | QAbstractItemView.EditKeyPressed) # Enable editing
        self.items_table.itemChanged.connect(self.handle_item_changed_in_table) # Connect signal for recalculation
        main_layout.addWidget(self.items_table)

        items_actions_layout = QHBoxLayout()
        self.add_item_btn = QPushButton(QIcon.fromTheme("list-add"), "Ajouter Article Sélectionné") # Text updated
        self.add_item_btn.setToolTip(self.tr("Ajoute le produit actuellement sélectionné dans la liste de gauche à la commande."))
        self.add_item_btn.clicked.connect(self.add_selected_product_from_list_to_table) # Connect to new method
        items_actions_layout.addWidget(self.add_item_btn)
        self.remove_item_btn = QPushButton(QIcon.fromTheme("list-remove"), "Supprimer Article")
        self.remove_item_btn.clicked.connect(self.remove_selected_item)
        items_actions_layout.addWidget(self.remove_item_btn)
        items_actions_layout.addStretch()
        main_layout.addLayout(items_actions_layout)

        # Totals (Display Only)
        totals_layout = QFormLayout()
        self.total_ht_label = QLabel("0.00 EUR")
        self.total_ttc_label = QLabel("0.00 EUR")
        self.total_ht_label.setStyleSheet("font-weight: bold;")
        self.total_ttc_label.setStyleSheet("font-weight: bold;")
        totals_layout.addRow("Total HT:", self.total_ht_label)
        totals_layout.addRow("Total TTC:", self.total_ttc_label)
        main_layout.addLayout(totals_layout)

        # Dialog Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept_dialog)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

        overall_layout.addWidget(right_panel_widget) # Add right panel to the main horizontal layout

    def _populate_product_selection_list(self):
        self.product_selection_list.clear()
        try:
            # Fetch all active global products
            all_products = products_crud.get_all_products(filters={'is_active': True})
            if all_products:
                for prod in sorted(all_products, key=lambda p: p.get('product_name', '').lower()):
                    item_text = f"{prod.get('product_name', 'N/A')} ({prod.get('product_code', 'N/A')})"
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, prod) # Store full product dict
                    self.product_selection_list.addItem(item)
            else:
                self.product_selection_list.addItem(self.tr("Aucun produit global trouvé."))
        except Exception as e:
            self.logger.error(f"Error populating product selection list: {e}", exc_info=True)
            self.product_selection_list.addItem(self.tr("Erreur chargement produits."))

    def _filter_product_selection_list(self, text):
        search_term = text.lower()
        for i in range(self.product_selection_list.count()):
            item = self.product_selection_list.item(i)
            if item:
                item_text = item.text().lower()
                # Also check product_code if available in UserRole data (more robust search)
                product_data = item.data(Qt.UserRole)
                code_match = False
                if isinstance(product_data, dict) and product_data.get('product_code','').lower().startswith(search_term):
                    code_match = True

                if search_term in item_text or code_match:
                    item.setHidden(False)
                else:
                    item.setHidden(True)

    def populate_combos(self):
        # Statuses
        self.status_commande_combo.clear()
        try:
            statuses = status_settings_crud.get_all_status_settings(type_filter='Commande')
            if statuses:
                for status in sorted(statuses, key=lambda x: x.get('sort_order', 0)):
                    self.status_commande_combo.addItem(status.get('status_name'), status.get('status_id'))
            else:
                self.status_commande_combo.addItem("Aucun Statut Défini", None)
        except Exception as e:
            self.logger.error(f"Error loading 'Commande' statuses: {e}", exc_info=True)
            QMessageBox.warning(self, "Erreur", "Impossible de charger les statuts de commande.")

        # Projects (for linking)
        self.project_combo.clear()
        self.project_combo.addItem("Aucun Projet Lié", None)
        self.project_combo.addItem("Créer un Nouveau Projet...", "CREATE_NEW") # Special value
        try:
            client_projects = projects_crud.get_projects_by_client_id(self.client_id)
            if client_projects:
                for proj in client_projects:
                    self.project_combo.addItem(f"{proj.get('project_name')} (ID: {proj.get('project_id')[:8]}...)", proj.get('project_id'))
        except Exception as e:
            self.logger.error(f"Error loading projects for client {self.client_id}: {e}", exc_info=True)
            # Non-critical, user can still create new

    def load_commande_data_for_edit(self):
        self.commande_data = commandes_crud.get_commande_by_id(self.commande_id_to_edit)
        if not self.commande_data:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les données de la commande ID: {self.commande_id_to_edit}")
            self.reject() # Close dialog if data load fails
            return

        self.commande_reference_edit.setText(self.commande_data.get("commande_reference", ""))

        commande_date_str = self.commande_data.get("commande_date")
        if commande_date_str:
            try:
                # Assuming ISO format from DB
                q_date = QDate.fromString(datetime.fromisoformat(commande_date_str.replace('Z', '')).strftime('%Y-%m-%d'), "yyyy-MM-dd")
                if q_date.isValid():
                    self.commande_date_edit.setDate(q_date)
            except ValueError:
                self.logger.warning(f"Invalid date format for commande_date: {commande_date_str}")

        status_id = self.commande_data.get("status_commande_id")
        if status_id:
            index = self.status_commande_combo.findData(status_id)
            if index != -1:
                self.status_commande_combo.setCurrentIndex(index)

        self.description_commande_edit.setPlainText(self.commande_data.get("description_commande", ""))

        project_id = self.commande_data.get("project_id")
        if project_id:
            index = self.project_combo.findData(project_id)
            if index != -1:
                self.project_combo.setCurrentIndex(index)
            else: # Project might not be in list if it was deleted, or from another context
                self.project_combo.addItem(f"Projet Lié (ID: {project_id[:8]}...)", project_id)
                self.project_combo.setCurrentIndex(self.project_combo.findData(project_id))

        self.notes_edit.setPlainText(self.commande_data.get("notes", "")) # Load notes

        # Load items
        self.commande_items_data = commandes_crud.get_items_for_commande(self.commande_id_to_edit)
        self.items_table.setRowCount(0) # Clear table
        for item_data in self.commande_items_data:
            self.add_item_to_table(item_data_to_load=item_data, is_loading=True)

        self.update_totals_display()


    def add_selected_product_from_list_to_table(self, list_item=None):
        """Adds the currently selected product from self.product_selection_list to the items_table."""
        selected_items = self.product_selection_list.selectedItems()
        if not selected_items:
            # If called by button click and nothing is selected, or if list_item is None (from double click on empty area)
            if list_item is None: # list_item is None if called by button and no selection
                 QMessageBox.information(self, self.tr("Sélection Requise"), self.tr("Veuillez sélectionner un produit dans la liste de gauche."))
                 return
            # If list_item is provided (from double click), use that directly
            product_data_global = list_item.data(Qt.UserRole) if list_item else None
        else: # Item selected and button clicked
            product_data_global = selected_items[0].data(Qt.UserRole)

        if not product_data_global or not isinstance(product_data_global, dict):
            self.logger.warning("No valid product data found for selected item in product_selection_list.")
            return

        # Prompt for quantity
        quantity, ok = QInputDialog.getDouble(self, self.tr("Quantité"), self.tr("Entrez la quantité pour '{0}':").format(product_data_global.get('product_name', 'N/A')), 1.0, 0.01, 10000, 2)
        if not ok or quantity <= 0:
            return # User cancelled or entered invalid quantity

        # Prepare item_data similar to what ProductDialog would return, but based on global product
        # This is for adding a *new* line item to the commande.
        item_data_for_table = {
            # Fields from the global product
            'product_id': product_data_global.get('product_id'),
            'product_code': product_data_global.get('product_code'),
            'name': product_data_global.get('product_name'), # This will be displayed in table's "Produit" column
            'description': product_data_global.get('description',''), # Global product description
            'weight': product_data_global.get('weight'),
            'dimensions': product_data_global.get('dimensions'),
            'language_code': product_data_global.get('language_code'),
            'base_unit_price': product_data_global.get('base_unit_price', 0.0), # Global base price

            # Fields specific to this commande line item
            'quantity': quantity,
            'unit_price': product_data_global.get('base_unit_price', 0.0), # Default to global base price for this line item
            # 'item_id' will be None for new items, set by DB later.
            # 'description_item' (specific desc for this line) can be same as global or edited later.
        }
        self.add_item_to_table(item_data_to_load=item_data_for_table, is_loading=False, from_product_list=True)


    def add_item_to_table(self, item_data_to_load=None, is_loading=False, from_product_list=False):
        # If from_product_list is True, item_data_to_load is already prepared by add_selected_product_from_list_to_table
        if not is_loading and not from_product_list:
            # This was the old path using ProductDialog. Now, directly use add_selected_product_from_list_to_table
            # or if the "Ajouter Article" button is kept, it should trigger selection from the list or a simplified input.
            # For now, let's assume "Ajouter Article" button will also use the selected product from the list.
            self.add_selected_product_from_list_to_table()
            return

        # If item_data_to_load is provided (either from DB load or from product_selection_list)
        if item_data_to_load:
            row_pos = self.items_table.rowCount()
            self.items_table.insertRow(row_pos)

            # Store full item_data in the first cell's UserRole for later retrieval/update
            product_name_item = QTableWidgetItem(item_data_to_load.get("product_name", "N/A"))
            product_name_item.setData(Qt.UserRole, item_data_to_load) # Store full dict
            product_name_item.setFlags(product_name_item.flags() & ~Qt.ItemIsEditable) # Product name not editable here
            self.items_table.setItem(row_pos, 0, product_name_item)

            desc_item = QTableWidgetItem(item_data_to_load.get("description_item", ""))
            desc_item.setFlags(desc_item.flags() & ~Qt.ItemIsEditable) # Description not editable here
            self.items_table.setItem(row_pos, 1, desc_item)

            qty_val = item_data_to_load.get("quantity", 0)
            qty_item = QTableWidgetItem(str(qty_val))
            qty_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            qty_item.setFlags(qty_item.flags() | Qt.ItemIsEditable)
            self.items_table.setItem(row_pos, 2, qty_item)

            price_val = item_data_to_load.get('unit_price_ht', 0.0)
            price_item = QTableWidgetItem(f"{price_val:.2f}")
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            price_item.setFlags(price_item.flags() | Qt.ItemIsEditable)
            self.items_table.setItem(row_pos, 3, price_item)

            vat_val = item_data_to_load.get('vat_rate', 0.0) * 100
            vat_item = QTableWidgetItem(f"{vat_val:.0f}") # Display as %
            vat_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            vat_item.setFlags(vat_item.flags() | Qt.ItemIsEditable)
            self.items_table.setItem(row_pos, 4, vat_item)

            # Poids (col 5)
            weight_val = item_data_to_load.get('weight', item_data_to_load.get('global_product_weight', '')) # Fallback to global product weight
            weight_item = QTableWidgetItem(str(weight_val))
            weight_item.setFlags(weight_item.flags() | Qt.ItemIsEditable)
            self.items_table.setItem(row_pos, 5, weight_item)

            # Dimensions (col 6)
            dims_val = item_data_to_load.get('dimensions_text', item_data_to_load.get('global_product_dimensions', '')) # Fallback to global
            dims_item = QTableWidgetItem(dims_val)
            dims_item.setFlags(dims_item.flags() | Qt.ItemIsEditable)
            self.items_table.setItem(row_pos, 6, dims_item)

            # Langue Article (col 7)
            lang_val = item_data_to_load.get('product_language_code', item_data_to_load.get('global_product_language_code', 'fr')) # Fallback to global then 'fr'
            lang_item = QTableWidgetItem(lang_val)
            lang_item.setFlags(lang_item.flags() | Qt.ItemIsEditable)
            self.items_table.setItem(row_pos, 7, lang_item)

            total_ht_val = item_data_to_load.get('total_item_ht', 0.0)
            total_ht_item = QTableWidgetItem(f"{total_ht_val:.2f}")
            total_ht_item.setFlags(total_ht_item.flags() & ~Qt.ItemIsEditable)
            total_ht_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.items_table.setItem(row_pos, 8, total_ht_item) # Adjusted index

            total_ttc_val = item_data_to_load.get('total_item_ttc', 0.0)
            total_ttc_item = QTableWidgetItem(f"{total_ttc_val:.2f}")
            total_ttc_item.setFlags(total_ttc_item.flags() & ~Qt.ItemIsEditable)
            total_ttc_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.items_table.setItem(row_pos, 9, total_ttc_item) # Adjusted index

            self.update_totals_display() # Update after adding an item

    def handle_item_changed_in_table(self, item):
        if self.items_table.signalsBlocked():
            return

        row = item.row()
        col = item.column()

        # React to changes in Qty, Price HT, VAT Rate columns for totals
        # Weight, Dimensions, Langue Article changes are saved but don't directly trigger total recalculation here.
        if col not in [2, 3, 4]: # 2: Qty, 3: Price HT, 4: VAT
            return

        try:
            self.items_table.blockSignals(True) # Prevent recursion

            qty_item = self.items_table.item(row, 2)
            price_ht_item = self.items_table.item(row, 3)
            vat_rate_percent_item = self.items_table.item(row, 4)
            qty_item = self.items_table.item(row, 2)
            price_ht_item = self.items_table.item(row, 3)
            vat_rate_percent_item = self.items_table.item(row, 4)
            # Les totaux de ligne sont dans les colonnes 8 (Total HT) et 9 (Total TTC)
            total_ht_cell_item = self.items_table.item(row, 8)
            total_ttc_cell_item = self.items_table.item(row, 9)

            if not all([qty_item, price_ht_item, vat_rate_percent_item, total_ht_cell_item, total_ttc_cell_item]):
                self.logger.warning(f"handle_item_changed_in_table: Missing cell item in row {row}. Aborting calculation for this row.")
                return

            try:
                qty = float(qty_item.text().replace(",", "."))
            except ValueError:
                self.logger.warning(f"Invalid quantity in row {row}: '{qty_item.text()}'. Using 0 for calculation.")
                qty = 0.0
                # Optionally revert cell text or show error to user

            try:
                price_ht = float(price_ht_item.text().replace("€", "").replace(",", ".").strip())
            except ValueError:
                self.logger.warning(f"Invalid price_ht in row {row}: '{price_ht_item.text()}'. Using 0.0 for calculation.")
                price_ht = 0.0

            try:
                vat_rate_percent_str = vat_rate_percent_item.text().replace("%", "").strip()
                vat_rate = float(vat_rate_percent_str.replace(",", ".")) / 100.0
            except ValueError:
                self.logger.warning(f"Invalid vat_rate_percent in row {row}: '{vat_rate_percent_item.text()}'. Using 0.0 for calculation.")
                vat_rate = 0.0


            current_total_ht = qty * price_ht
            current_total_ttc = current_total_ht * (1 + vat_rate)

            total_ht_cell_item.setText(f"{current_total_ht:.2f}")
            total_ttc_cell_item.setText(f"{current_total_ttc:.2f}")

            # No specific action needed for weight, dimensions, product_language_code changes
            # in this handler, as they don't directly affect line/order totals.
            # Their values are simply edited in the table and will be saved during _sync_commande_items.

            self.update_totals_display()

        except Exception as e:
            self.logger.error(f"Error in handle_item_changed_in_table for row {row}, col {col}: {e}", exc_info=True)
        finally:
            self.items_table.blockSignals(False)


    def remove_selected_item(self):
        current_row = self.items_table.currentRow()
        if current_row >= 0:
            item_widget = self.items_table.item(current_row, 0)
            if item_widget:
                item_data = item_widget.data(Qt.UserRole)
                item_id_to_delete = item_data.get('item_id') if item_data else None

                if self.commande_id_to_edit and item_id_to_delete: # Item exists in DB
                    # No direct DB delete here, will be handled during save_commande
                    pass

            self.items_table.removeRow(current_row)
            self.update_totals_display()
        else:
            QMessageBox.warning(self, "Sélection Requise", "Veuillez sélectionner un article à supprimer.")

    def update_totals_display(self):
        total_ht = 0.0
        total_ttc = 0.0
        for row in range(self.items_table.rowCount()):
            try:
                # Assuming data is stored or can be read from table cells
                # For simplicity, let's assume we re-fetch from stored item_data if available (complex for new items)
                # Or, if cells are directly editable widgets, get values from them.
                # This is a placeholder for robust calculation based on table content.

                # If loading existing items, their totals are already calculated.
                # If adding new items, their totals need to be calculated upon input.
                # This function should sum up total_item_ht and total_item_ttc from all rows.
                ht_cell_item = self.items_table.item(row, 8) # Total HT column (index 8)
                ttc_cell_item = self.items_table.item(row, 9) # Total TTC column (index 9)

                if ht_cell_item and ht_cell_item.text():
                    try:
                        total_ht += float(ht_cell_item.text().replace("€", "").replace(",", ".").strip())
                    except ValueError:
                        self.logger.warning(f"Could not parse Total HT from row {row}: '{ht_cell_item.text()}'")

                if ttc_cell_item and ttc_cell_item.text():
                    try:
                        total_ttc += float(ttc_cell_item.text().replace("€", "").replace(",", ".").strip())
                    except ValueError:
                        self.logger.warning(f"Could not parse Total TTC from row {row}: '{ttc_cell_item.text()}'")
            except Exception: # General exception to catch any other parsing error for the row
                self.logger.warning(f"Could not parse totals from row {row} for calculation due to unexpected error.", exc_info=True)
                pass # Skip row if parsing fails

        currency = self.commande_data.get("currency", "EUR") if self.commande_data else "EUR"
        self.total_ht_label.setText(f"{total_ht:.2f} {currency}")
        self.total_ttc_label.setText(f"{total_ttc:.2f} {currency}")


    def accept_dialog(self):
        # Data Validation
        commande_ref = self.commande_reference_edit.text().strip()
        if not commande_ref:
            QMessageBox.warning(self, "Validation", "La référence de la commande est obligatoire.")
            return

        status_id = self.status_commande_combo.currentData()
        if status_id is None:
            QMessageBox.warning(self, "Validation", "Le statut de la commande est obligatoire.")
            return

        commande_data_payload = {
            "client_id": self.client_id,
            "commande_reference": commande_ref,
            "commande_date": self.commande_date_edit.date().toString("yyyy-MM-dd") + "T00:00:00Z", # Store as ISO string
            "status_commande_id": status_id,
            "description_commande": self.description_commande_edit.toPlainText().strip(),
            "notes": self.notes_edit.toPlainText().strip(), # Added notes
            "project_id": self.project_combo.currentData() if self.project_combo.currentData() != "CREATE_NEW" else None,
            "created_by_user_id": self.current_user_id,
            # Totals will be calculated based on items or handled by a separate update later
            "total_ht": None, # Placeholder
            "total_ttc": None, # Placeholder
            "currency": "EUR" # Placeholder, could be configurable
        }

        if self.project_combo.currentData() == "CREATE_NEW":
            # Logic to create a new project
            project_name, ok = QInputDialog.getText(self, "Nouveau Projet", f"Nom du projet pour la commande {commande_ref}:")
            if ok and project_name.strip():
                # Default status for new project (e.g., 'Planning')
                planning_status = status_settings_crud.get_status_setting_by_name("Planning", "Project")
                if not planning_status:
                    QMessageBox.critical(self, "Erreur", "Statut 'Planning' par défaut introuvable pour les projets.")
                    return # Or handle differently

                new_project_data = {
                    "client_id": self.client_id,
                    "project_name": project_name.strip(),
                    "status_id": planning_status.get('status_id'),
                    "manager_team_member_id": self.current_user_id # Or prompt for manager
                }
                new_project_id = projects_crud.add_project(new_project_data)
                if new_project_id:
                    commande_data_payload["project_id"] = new_project_id
                else:
                    QMessageBox.warning(self, "Échec Création Projet", "Impossible de créer le projet associé. La commande sera sauvegardée sans projet lié pour le moment.")
            else: # User cancelled or entered empty project name
                QMessageBox.information(self, "Info", "Création de projet annulée. La commande sera sauvegardée sans projet lié pour le moment.")


        # Save/Update Commande
        if self.commande_id_to_edit:
            success = commandes_crud.update_commande(self.commande_id_to_edit, commande_data_payload)
            if success:
                self.logger.info(f"Commande {self.commande_id_to_edit} updated.")
                self._last_processed_project_id = commande_data_payload.get("project_id") # Store project_id

                self._sync_commande_items(self.commande_id_to_edit)
                super().accept()
            else:
                QMessageBox.critical(self, "Erreur", "Impossible de mettre à jour la commande.")
        else: # New Commande
            new_cmd_id = commandes_crud.add_commande(commande_data_payload)
            if new_cmd_id:
                self.logger.info(f"New commande {new_cmd_id} created.")
                self.commande_id_to_edit = new_cmd_id # So items can be linked
                self._last_processed_project_id = commande_data_payload.get("project_id") # Store project_id
                self._created_commande_id = new_cmd_id
                self._created_commande_ref = commande_data_payload.get("commande_reference")

                self._sync_commande_items(new_cmd_id)
                super().accept()
            else:
                QMessageBox.critical(self, "Erreur", "Impossible de créer la commande.")

    def _sync_commande_items(self, commande_id):
        """
        Synchronizes items in the table with the database for the given commande_id.
        - Deletes items from DB that are not in the table anymore.
        - Updates items in DB that have changed.
        - Adds new items from table to DB.
        """
        db_items_list = commandes_crud.get_items_for_commande(commande_id)
        db_item_ids = {item['item_id'] for item in db_items_list}

        table_item_ids_processed = set()

        # Update existing or add new items
        for row in range(self.items_table.rowCount()):
            table_item_widget = self.items_table.item(row, 0)
            if not table_item_widget: continue

            table_item_data_stored = table_item_widget.data(Qt.UserRole) # This is the full dict if loaded
            item_id_in_table = table_item_data_stored.get('item_id') if table_item_data_stored else None

            # Prepare payload from table row (this needs to be more robust if cells are widgets)
            # This example assumes data can be read from table cells if not in UserRole
            # or that UserRole is always populated correctly for new/edited items.
            # For simplicity, let's assume a helper method prepares this payload correctly.
            current_row_payload = self._get_payload_from_table_row(row, commande_id)
            if not current_row_payload: continue # Skip if row data is invalid

            if item_id_in_table and item_id_in_table in db_item_ids: # Item exists in DB, update it
                commandes_crud.update_commande_item(item_id_in_table, current_row_payload)
                table_item_ids_processed.add(item_id_in_table)
            elif not item_id_in_table: # New item, add it
                # current_row_payload should already have commande_id
                new_added_item_id = commandes_crud.add_commande_item(current_row_payload)
                if new_added_item_id:
                    table_item_ids_processed.add(new_added_item_id) # Should ideally match a generated UUID if not returned
            # Else: item_id_in_table is present but not in db_item_ids - this case shouldn't happen if logic is correct.

        # Delete items from DB that are no longer in the table
        for db_item_id_to_check in db_item_ids:
            if db_item_id_to_check not in table_item_ids_processed:
                self.logger.info(f"Deleting CommandeItem {db_item_id_to_check} as it's no longer in the table.")
                commandes_crud.delete_commande_item(db_item_id_to_check)

        self._recalculate_and_save_commande_totals(commande_id)

    def _create_global_product_if_needed(self, item_payload_from_row):
        """
        Checks if a global product needs to be created based on item_payload_from_row.
        If so, creates it and updates item_payload_from_row with the new product_id.
        Returns True if successful or not needed, False if creation failed.
        """
        if item_payload_from_row.get("product_id"): # Already an existing global product
            return True

        product_code = item_payload_from_row.get("product_code")
        original_name = item_payload_from_row.get("original_product_name")
        original_price = item_payload_from_row.get("original_base_unit_price")
        original_description = item_payload_from_row.get("original_product_description")

        if not (product_code and original_name):
            self.logger.error("Cannot create global product: product_code or original_name is missing.")
            QMessageBox.critical(self, "Erreur Création Produit", "Code ou nom manquant pour la création d'un nouveau produit global.")
            return False

        # Check if product with this code already exists (e.g., created by another line item in this same dialog session)
        existing_global_product = products_crud.get_product_by_code(product_code)
        if existing_global_product:
            item_payload_from_row["product_id"] = existing_global_product.get('product_id')
            self.logger.info(f"Found existing global product by code '{product_code}' with ID {item_payload_from_row['product_id']} during sync.")
            return True

        self.logger.info(f"Creating new global product: Code='{product_code}', Name='{original_name}'")
        new_global_product_data = {
            'product_name': original_name,
            'product_code': product_code,
            'description': original_description,
            'base_unit_price': original_price if original_price is not None else 0.0,
            # 'language_code': ??? # ProductDialog's get_data includes language_code, ensure it's passed here
            # 'category': ???
            # 'created_by_user_id': self.current_user_id # Important for tracking
            'is_active': True
        }
        # Add language_code if available from product_data_from_dialog (UserRole)
        # This assumes _get_payload_from_table_row stores it
        if item_payload_from_row.get("language_code"): # Check if this key exists from UserRole
            new_global_product_data['language_code'] = item_payload_from_row.get("language_code")
        else: # Fallback or default
            new_global_product_data['language_code'] = 'fr'

        if self.current_user_id:
             new_global_product_data['created_by_user_id'] = self.current_user_id
        else:
            self.logger.warning("current_user_id is not set in CommandeDialog. Cannot set created_by_user_id for new global product.")
            # Depending on DB constraints, this might fail if created_by_user_id is NOT NULL in Products.
            # For now, proceed without it if not available. DB will raise error if required.


        add_result = products_crud.add_product(product_data=new_global_product_data)
        if add_result and add_result.get('success'):
            new_global_id = add_result.get('id') # products_crud.add_product returns {'success': True, 'id': new_id}
            item_payload_from_row["product_id"] = new_global_id
            self.logger.info(f"New global product '{original_name}' created with ID: {new_global_id}.")
            return True
        else:
            error_msg = add_result.get('error', 'Unknown error') if add_result else 'Unknown error'
            self.logger.error(f"Failed to add new global product '{original_name}'. Error: {error_msg}")
            QMessageBox.critical(self, "Erreur Création Produit Global", f"Impossible de créer le produit global '{original_name}': {error_msg}")
            return False

    def _sync_commande_items(self, commande_id):
        """
        Synchronizes items in the table with the database for the given commande_id.
        - Deletes items from DB that are not in the table anymore.
        - Updates items in DB that have changed.
        - Adds new items from table to DB (creating global products if needed).
        """
        db_items_list = commandes_crud.get_items_for_commande(commande_id)
        db_item_ids = {item['item_id'] for item in db_items_list if item and 'item_id' in item} # Ensure item and item_id exist

        table_item_ids_processed = set()

        for row in range(self.items_table.rowCount()):
            item_payload = self._get_payload_from_table_row(row, commande_id)
            if not item_payload:
                self.logger.warning(f"Skipping row {row} in _sync_commande_items due to invalid payload.")
                continue

            # Ensure global product exists or is created
            if not self._create_global_product_if_needed(item_payload):
                # If global product creation fails, we might want to stop the whole sync or skip this item.
                # For now, let's skip this item to prevent further errors.
                self.logger.error(f"Skipping item sync for row {row} due to global product creation/retrieval failure.")
                continue

            # product_id should now be populated in item_payload
            if not item_payload.get("product_id"):
                self.logger.error(f"Critical: product_id still missing for item in row {row} after _create_global_product_if_needed. Payload: {item_payload}")
                QMessageBox.critical(self, "Erreur Interne", f"Erreur interne : ID produit manquant pour l'article à la ligne {row + 1} après tentative de création/récupération.")
                continue # Skip this item

            commande_item_id = item_payload.get('item_id') # This is CommandeItem.item_id if editing

            if commande_item_id and commande_item_id in db_item_ids: # Existing CommandeItem, update it
                success = commandes_crud.update_commande_item(commande_item_id, item_payload)
                if success:
                    table_item_ids_processed.add(commande_item_id)
                else:
                    self.logger.error(f"Failed to update CommandeItem {commande_item_id}.")
            else: # New CommandeItem, add it
                # Remove 'item_id' if it was part of payload but not for a DB existing item (should not happen here)
                item_payload.pop('item_id', None)
                new_added_item_id = commandes_crud.add_commande_item(item_payload)
                if new_added_item_id:
                    table_item_ids_processed.add(new_added_item_id)
                else:
                    self.logger.error(f"Failed to add new CommandeItem for product {item_payload.get('product_id')}.")

        # Delete items from DB that are no longer in the table
        for db_item_id_to_check in db_item_ids:
            if db_item_id_to_check not in table_item_ids_processed:
                self.logger.info(f"Deleting CommandeItem {db_item_id_to_check} as it's no longer in the table.")

                commandes_crud.delete_commande_item(db_item_id_to_check)

        self._recalculate_and_save_commande_totals(commande_id)


    def _get_payload_from_table_row(self, row_index, commande_id_for_new_items):
        """
        Helper to extract item data from a table row to a dictionary suitable for CRUD.
        It prioritizes data from `UserRole` (set by `ProductDialog`) and then current cell values.
        """
        payload = {}
        try:
            name_cell_item = self.items_table.item(row_index, 0)
            # product_data_from_dialog contains product_id, product_code, original name, desc, price from ProductDialog
            product_data_from_dialog = name_cell_item.data(Qt.UserRole) if name_cell_item else {}
            if not isinstance(product_data_from_dialog, dict):
                product_data_from_dialog = {}

            payload["commande_id"] = commande_id_for_new_items # This will be overridden if item already has an ID

            # These are critical for identifying/creating the global product
            payload["product_id"] = product_data_from_dialog.get('product_id') # Might be None if new global product
            payload["product_code"] = product_data_from_dialog.get('product_code')
            payload["original_product_name"] = product_data_from_dialog.get('name') # Name as defined in ProductDialog
            payload["original_product_description"] = product_data_from_dialog.get('description')
            payload["original_base_unit_price"] = product_data_from_dialog.get('unit_price') # Price as defined in ProductDialog
            payload["language_code"] = product_data_from_dialog.get('language_code', 'fr') # Language for new global product

            # These are values for the CommandeItem, potentially edited in the table
            payload["description_item"] = self.items_table.item(row_index, 1).text().strip()

            try:
                payload["quantity"] = float(self.items_table.item(row_index, 2).text().replace(",", "."))
            except ValueError:
                self.logger.error(f"Invalid quantity in row {row_index}. Defaulting to 0.")
                payload["quantity"] = 0.0

            try:
                payload["unit_price_ht"] = float(self.items_table.item(row_index, 3).text().replace("€", "").replace(",", ".").strip())
            except ValueError:
                self.logger.error(f"Invalid unit_price_ht in row {row_index}. Defaulting to 0.0.")
                payload["unit_price_ht"] = 0.0

            try:
                vat_text = self.items_table.item(row_index, 4).text().replace("%", "").strip()
                payload["vat_rate"] = float(vat_text.replace(",", ".")) / 100.0
            except ValueError:
                self.logger.error(f"Invalid vat_rate in row {row_index}. Defaulting to 0.0.")
                payload["vat_rate"] = 0.0

            # New fields: Poids, Dimensions, Langue Article
            try:
                payload["weight"] = float(self.items_table.item(row_index, 5).text().replace(",", ".")) if self.items_table.item(row_index, 5) and self.items_table.item(row_index, 5).text() else None
            except ValueError:
                self.logger.warning(f"Invalid weight in row {row_index}. Setting to None.")
                payload["weight"] = None

            payload["dimensions_text"] = self.items_table.item(row_index, 6).text().strip() if self.items_table.item(row_index, 6) and self.items_table.item(row_index, 6).text() else None
            payload["product_language_code"] = self.items_table.item(row_index, 7).text().strip() if self.items_table.item(row_index, 7) and self.items_table.item(row_index, 7).text() else None


            # Include item_id if it's an existing item being updated
            if product_data_from_dialog and product_data_from_dialog.get('item_id'): # 'item_id' here refers to CommandeItem.item_id if loaded for edit
                payload['item_id'] = product_data_from_dialog.get('item_id')

            # If product_id is None, we need product_code and name to try and create it
            if payload["product_id"] is None and not (payload.get("product_code") and payload.get("original_product_name")):
                self.logger.error(f"Row {row_index}: New global product indicated (no product_id) but missing product_code or original_product_name from ProductDialog data.")
                QMessageBox.warning(self, "Données Produit Manquantes", f"Les informations pour créer un nouveau produit global (code/nom) sont manquantes pour l'article à la ligne {row_index + 1}.")
                return None # Critical error for this row

            return payload

        except Exception as e:
            self.logger.error(f"Error extracting payload from table row {row_index}: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur Interne", f"Erreur lors de la lecture des données de la ligne d'article {row_index + 1}.")

            return None

    def _recalculate_and_save_commande_totals(self, commande_id):
        """Recalculates total_ht and total_ttc for the commande based on its items and updates the DB."""
        items = commandes_crud.get_items_for_commande(commande_id)
        if items is None: # Error fetching items
            self.logger.error(f"Could not fetch items for commande {commande_id} to recalculate totals.")
            return

        current_total_ht = sum(item.get('total_item_ht', 0.0) for item in items)
        current_total_ttc = sum(item.get('total_item_ttc', 0.0) for item in items)

        update_payload = {
            "total_ht": current_total_ht,
            "total_ttc": current_total_ttc
        }
        if not commandes_crud.update_commande(commande_id, update_payload):
            self.logger.error(f"Failed to update commande {commande_id} with recalculated totals.")
        else:
            self.logger.info(f"Commande {commande_id} totals updated: HT={current_total_ht}, TTC={current_total_ttc}")

    def get_created_project_id(self):
        """
        Returns the project_id that was created or linked during the dialog's execution.
        This should be called after accept_dialog() has successfully processed/saved the commande.
        """
        # self.commande_data might be populated if editing, or could be the payload if new
        # A more robust way is to store the determined project_id in an instance variable during accept_dialog
        if hasattr(self, '_last_processed_project_id'):
            return self._last_processed_project_id

        # Fallback: if editing, get it from the reloaded commande_data
        if self.commande_id_to_edit and self.commande_data:
            return self.commande_data.get("project_id")

        # Fallback: if new, it might be in the payload that was built (less ideal as payload is local to accept_dialog)
        # This indicates a need to store the project_id more reliably if created/selected.
        # For now, this method will primarily work if _last_processed_project_id is set in accept_dialog.
        self.logger.warning("get_created_project_id called but _last_processed_project_id not set and not editing.")
        return None

    def get_created_commande_id(self):
        """Returns the ID of the commande created or edited by this dialog instance."""
        return getattr(self, '_created_commande_id', None)

    def get_created_commande_reference(self):
        """Returns the reference of the commande created or edited by this dialog instance."""
        return getattr(self, '_created_commande_ref', None)



# Example usage (for testing, if run directly)
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    import os

    # Mock data for testing
    mock_client_id = "test_client_for_commande_dialog"
    mock_user_id = "test_user_for_commande_dialog"

    # Ensure DB is initialized (adjust path as needed)
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), '..')) # To find db package
        from db import initialize_database
        initialize_database()
        # You might want to add a mock client here for testing
        # db.add_client({'client_id': mock_client_id, 'client_name': 'Test Client Dialog', 'created_by_user_id': mock_user_id, 'project_identifier': 'P-DIALOG'})
    except Exception as e:
        print(f"DB init error for CommandeDialog test: {e}")

    app = QApplication(sys.argv)
    dialog = CommandeDialog(client_id=mock_client_id, current_user_id=mock_user_id)
    # To test editing:
    # Create a dummy commande first via CRUD, then pass its ID
    # example_cmd_id = commandes_crud.add_commande({ ... })
    # dialog = CommandeDialog(client_id=mock_client_id, current_user_id=mock_user_id, commande_id_to_edit=example_cmd_id)

    if dialog.exec_() == QDialog.Accepted:
        print("Commande Dialog Accepted/Saved.")
    else:
        print("Commande Dialog Cancelled.")
    sys.exit(app.exec_())
