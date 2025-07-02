# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QTextEdit,
    QPushButton, QDialogButtonBox, QMessageBox, QLabel, QTableWidget,
    QTableWidgetItem, QAbstractItemView, QHeaderView, QGroupBox,
    QDoubleSpinBox, QComboBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt # For Qt.AlignRight, Qt.AlignVCenter, etc.

from db.cruds.products_crud import products_crud_instance
# Anticipated import, will be resolved when ProductDimensionUIDialog is moved
from .product_dimension_ui_dialog import ProductDimensionUIDialog


class ManageProductMasterDialog(QDialog):
    def __init__(self, app_root_dir, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Gérer Produits Globaux"))
        self.setMinimumSize(1000, 700)
        self.app_root_dir = app_root_dir
        self.selected_product_id = None
        self.load_products_triggered_by_text_change = False

        self.setup_ui()
        self._populate_master_category_filter() # Populate categories
        self.load_products() # Initial load
        self._clear_form_and_disable_buttons()

    def _populate_master_category_filter(self):
        self.category_filter_combo.blockSignals(True)
        self.category_filter_combo.clear()
        self.category_filter_combo.addItem(self.tr("Toutes Catégories"), None)
        try:
            categories = products_crud_instance.get_distinct_product_categories()
            if categories:
                for category_name in sorted(categories):
                    if category_name:
                        self.category_filter_combo.addItem(category_name, category_name)
        except AttributeError: # Should not happen if products_crud is updated
            logging.error("products_crud_instance.get_distinct_product_categories() not found.")
        except Exception as e:
            logging.error(f"Error populating master category filter: {e}", exc_info=True)
        self.category_filter_combo.blockSignals(False)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        top_layout = QHBoxLayout()

        product_list_group = QGroupBox(self.tr("Liste des Produits"))
        product_list_layout = QVBoxLayout(product_list_group)

        # Filter Layout
        filter_widget = QWidget()
        filters_layout = QHBoxLayout(filter_widget)
        filters_layout.setContentsMargins(0,0,0,0)

        self.search_product_input = QLineEdit()
        self.search_product_input.setPlaceholderText(self.tr("Nom, Code, Desc..."))
        self.search_product_input.textChanged.connect(self._trigger_load_products_from_search)
        filters_layout.addWidget(self.search_product_input, 1) # Stretch search input

        filters_layout.addWidget(QLabel(self.tr("Catégorie:")))
        self.category_filter_combo = QComboBox()
        self.category_filter_combo.addItem(self.tr("Toutes"), None)
        # TODO: Populate categories in a separate method after setup_ui
        self.category_filter_combo.currentIndexChanged.connect(self.load_products)
        filters_layout.addWidget(self.category_filter_combo)

        filters_layout.addWidget(QLabel(self.tr("Langue:")))
        self.language_filter_combo = QComboBox()
        self.language_filter_combo.addItem(self.tr("Toutes"), None)
        # Example languages, make this dynamic or match supported ones
        for lang_code in ["fr", "en", "ar", "tr", "pt"]:
            self.language_filter_combo.addItem(lang_code, lang_code)
        self.language_filter_combo.currentIndexChanged.connect(self.load_products)
        filters_layout.addWidget(self.language_filter_combo)

        product_list_layout.addWidget(filter_widget)

        self.products_table = QTableWidget()
        self.products_table.setColumnCount(5)
        self.products_table.setHorizontalHeaderLabels([
            "ID", self.tr("Nom Produit"), self.tr("Catégorie"),
            self.tr("Langue"), self.tr("Prix de Base Unitaire")
        ])
        self.products_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.products_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.products_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.products_table.hideColumn(0)
        self.products_table.itemSelectionChanged.connect(self.on_product_selection_changed)
        product_list_layout.addWidget(self.products_table)
        top_layout.addWidget(product_list_group, 2)

        self.product_form_group = QGroupBox(self.tr("Détails du Produit"))
        self.product_form_group.setDisabled(True)
        form_layout = QFormLayout(self.product_form_group)
        self.name_input = QLineEdit()
        form_layout.addRow(self.tr("Nom *:"), self.name_input) # Added asterisk
        self.product_code_input = QLineEdit()
        self.product_code_input.setToolTip(self.tr("Identifiant unique global du produit (SKU). Requis."))
        form_layout.addRow(self.tr("Code Produit *:"), self.product_code_input) # Added asterisk and tooltip
        self.description_input = QTextEdit()
        self.description_input.setFixedHeight(80)
        form_layout.addRow(self.tr("Description:"), self.description_input)
        self.category_input = QLineEdit()
        form_layout.addRow(self.tr("Catégorie:"), self.category_input)
        self.language_code_combo = QComboBox()
        self.language_code_combo.addItems(["fr", "en", "ar", "tr", "pt"])
        self.language_code_combo.setToolTip(self.tr("Langue principale de cette entrée de produit."))
        form_layout.addRow(self.tr("Code Langue *:"), self.language_code_combo) # Added asterisk
        self.base_unit_price_input = QDoubleSpinBox()
        self.base_unit_price_input.setRange(0.0, 1_000_000_000.0)
        self.base_unit_price_input.setDecimals(2)
        self.base_unit_price_input.setPrefix("€ ")
        form_layout.addRow(self.tr("Prix de Base Unitaire:"), self.base_unit_price_input)
        self.weight_input = QDoubleSpinBox()
        self.weight_input.setSuffix(" kg")
        self.weight_input.setRange(0.0, 10000.0)
        self.weight_input.setDecimals(3)
        form_layout.addRow(self.tr("Poids:"), self.weight_input)
        self.general_dimensions_input = QLineEdit()
        self.general_dimensions_input.setPlaceholderText(self.tr("ex: 100x50x25 cm"))
        form_layout.addRow(self.tr("Dimensions Générales (Produit):"), self.general_dimensions_input)
        top_layout.addWidget(self.product_form_group, 1)
        main_layout.addLayout(top_layout)

        buttons_layout = QHBoxLayout()
        self.add_new_product_button = QPushButton(self.tr("Ajouter Nouveau Produit"))
        self.add_new_product_button.setIcon(QIcon.fromTheme("list-add"))
        self.add_new_product_button.clicked.connect(self.on_add_new_product)
        buttons_layout.addWidget(self.add_new_product_button)
        self.save_product_button = QPushButton(self.tr("Enregistrer Modifications"))
        self.save_product_button.setIcon(QIcon.fromTheme("document-save"))
        self.save_product_button.setObjectName("primaryButton")
        self.save_product_button.clicked.connect(self.on_save_product)
        buttons_layout.addWidget(self.save_product_button)
        self.manage_detailed_dimensions_button = QPushButton(self.tr("Gérer Dimensions Détaillées"))
        self.manage_detailed_dimensions_button.setIcon(QIcon.fromTheme("view-grid"))
        self.manage_detailed_dimensions_button.clicked.connect(self.on_manage_detailed_dimensions)
        buttons_layout.addWidget(self.manage_detailed_dimensions_button)
        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout)

        dialog_button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        dialog_button_box.button(QDialogButtonBox.Ok).setText(self.tr("OK"))
        dialog_button_box.button(QDialogButtonBox.Cancel).setText(self.tr("Annuler"))
        dialog_button_box.accepted.connect(self.accept)
        dialog_button_box.rejected.connect(self.reject)
        main_layout.addWidget(dialog_button_box)
        self.setLayout(main_layout)

    def _trigger_load_products_from_search(self):
        self.load_products_triggered_by_text_change = True
        self.load_products()
        self.load_products_triggered_by_text_change = False

    def _clear_form_and_disable_buttons(self):
        self.name_input.clear()
        self.description_input.clear()
        self.category_input.clear()
        self.product_code_input.clear() # Clear product_code_input
        self.language_code_combo.setCurrentIndex(0)
        self.base_unit_price_input.setValue(0.0)
        self.weight_input.setValue(0.0)
        self.general_dimensions_input.clear()
        self.selected_product_id = None
        self.product_form_group.setDisabled(True)
        self.save_product_button.setDisabled(True)
        self.save_product_button.setText(self.tr("Enregistrer Modifications"))
        self.manage_detailed_dimensions_button.setDisabled(True)

    def load_products(self):
        current_selection_product_id = self.selected_product_id
        if self.load_products_triggered_by_text_change:
            current_selection_product_id = None

        self.products_table.setSortingEnabled(False)
        self.products_table.clearContents()
        self.products_table.setRowCount(0)

        search_text = self.search_product_input.text().strip()
        selected_category = self.category_filter_combo.currentData()
        selected_language = self.language_filter_combo.currentData()

        filters = {}
        if search_text:
            filters['search_term_generic'] = search_text # Use a new key for generic search
        if selected_category:
            filters['category'] = selected_category
        if selected_language:
            filters['language_code'] = selected_language

        include_deleted = False # For now, master list doesn't show deleted, can be a feature

        try:
            # products_crud_instance.get_all_products will need to be updated
            # to understand 'search_term_generic'
            products = products_crud_instance.get_all_products(
                filters=filters,
                include_deleted=include_deleted
            )
            if products is None: products = [] # Ensure iterable

            for row_idx, product_data in enumerate(products):
                self.products_table.insertRow(row_idx)
                id_item = QTableWidgetItem(str(product_data['product_id']))
                id_item.setData(Qt.UserRole, product_data['product_id'])
                self.products_table.setItem(row_idx, 0, id_item)
                self.products_table.setItem(row_idx, 1, QTableWidgetItem(product_data.get('product_name', '')))
                self.products_table.setItem(row_idx, 2, QTableWidgetItem(product_data.get('category', '')))
                self.products_table.setItem(row_idx, 3, QTableWidgetItem(product_data.get('language_code', '')))
                price_str = f"{product_data.get('base_unit_price', 0.0):.2f}"
                price_item = QTableWidgetItem(price_str)
                price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.products_table.setItem(row_idx, 4, price_item)
                if product_data['product_id'] == current_selection_product_id:
                    self.products_table.selectRow(row_idx)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur de Chargement"), self.tr("Impossible de charger les produits: {0}").format(str(e)))
        self.products_table.setSortingEnabled(True)
        if not self.products_table.selectedItems():
            self._clear_form_and_disable_buttons()

    def on_product_selection_changed(self):
        selected_items = self.products_table.selectedItems()
        if not selected_items:
            self._clear_form_and_disable_buttons(); return
        selected_row = selected_items[0].row()
        product_id_item = self.products_table.item(selected_row, 0)
        if not product_id_item:
            self._clear_form_and_disable_buttons(); return
        self.selected_product_id = product_id_item.data(Qt.UserRole)
        try:
            product_data = products_crud_instance.get_product_by_id(self.selected_product_id, include_deleted=True)
            if product_data:
                self.product_form_group.setDisabled(False)
                self.name_input.setText(product_data.get('product_name', ''))
                self.product_code_input.setText(product_data.get('product_code', '')) # Populate product_code_input
                self.description_input.setPlainText(product_data.get('description', ''))
                self.category_input.setText(product_data.get('category', ''))
                lang_idx = self.language_code_combo.findText(product_data.get('language_code', 'fr'))
                self.language_code_combo.setCurrentIndex(lang_idx if lang_idx != -1 else 0)
                base_price_from_db = product_data.get('base_unit_price')
                self.base_unit_price_input.setValue(float(base_price_from_db) if base_price_from_db is not None else 0.0)
                weight_from_db = product_data.get('weight')
                self.weight_input.setValue(float(weight_from_db) if weight_from_db is not None else 0.0)
                self.general_dimensions_input.setText(product_data.get('dimensions', ''))
                self.save_product_button.setText(self.tr("Enregistrer Modifications"))
                self.save_product_button.setEnabled(True)
                self.manage_detailed_dimensions_button.setEnabled(True)
            else:
                self._clear_form_and_disable_buttons()
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("Produit non trouvé."))
        except Exception as e:
            self._clear_form_and_disable_buttons()
            QMessageBox.critical(self, self.tr("Erreur de Chargement"), self.tr("Impossible de charger les détails du produit: {0}").format(str(e)))

    def on_add_new_product(self):
        self._clear_form_and_disable_buttons()
        self.products_table.clearSelection()
        self.product_form_group.setDisabled(False)
        self.save_product_button.setText(self.tr("Ajouter Produit"))
        self.save_product_button.setEnabled(True)
        self.manage_detailed_dimensions_button.setEnabled(False)
        self.name_input.setFocus()

    def on_save_product(self):
        name = self.name_input.text().strip()
        product_code = self.product_code_input.text().strip() # Retrieve product_code
        description = self.description_input.toPlainText().strip()
        category = self.category_input.text().strip()
        language_code = self.language_code_combo.currentText()
        base_unit_price = self.base_unit_price_input.value()
        weight = self.weight_input.value()
        dimensions = self.general_dimensions_input.text().strip()

        if not name:
            QMessageBox.warning(self, self.tr("Validation"), self.tr("Le nom du produit est requis.")); self.name_input.setFocus(); return
        if not product_code: # Validate product_code
            QMessageBox.warning(self, self.tr("Validation"), self.tr("Le code produit est requis.")); self.product_code_input.setFocus(); return
        if not language_code:
            QMessageBox.warning(self, self.tr("Validation"), self.tr("Le code langue est requis.")); self.language_code_combo.setFocus(); return

        product_data_dict = {
            'product_name': name, 'product_code': product_code, 'description': description, # Add product_code to dict
            'category': category, 'language_code': language_code,
            'base_unit_price': base_unit_price, 'weight': weight,
            'dimensions': dimensions, 'is_active': True
        }
        try:
            if self.selected_product_id is None:
                add_result = products_crud_instance.add_product(product_data_dict)
                if add_result['success']:
                    new_id = add_result['id']
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Produit ajouté avec succès (ID: {0}).").format(new_id))
                    self.load_products()
                    for r in range(self.products_table.rowCount()):
                        if self.products_table.item(r, 0).data(Qt.UserRole) == new_id:
                            self.products_table.selectRow(r); break
                    if not self.products_table.selectedItems(): self._clear_form_and_disable_buttons()
                else:
                    QMessageBox.warning(self, self.tr("Échec"), add_result.get('error', self.tr("Impossible d'ajouter le produit.")))
            else:
                update_result = products_crud_instance.update_product(self.selected_product_id, product_data_dict)
                if update_result['success']:
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Produit mis à jour avec succès."))
                    current_selected_row = self.products_table.currentRow()
                    self.load_products()
                    if current_selected_row >= 0 and current_selected_row < self.products_table.rowCount():
                         self.products_table.selectRow(current_selected_row)
                    if not self.products_table.selectedItems(): self._clear_form_and_disable_buttons()
                else:
                    QMessageBox.warning(self, self.tr("Échec"), update_result.get('error', self.tr("Impossible de mettre à jour le produit.")))
        except Exception as e:
            QMessageBox.critical(self, self.tr("Erreur Base de Données"), self.tr("Une erreur est survenue: {0}").format(str(e)))

    def on_manage_detailed_dimensions(self):
        if self.selected_product_id is not None:
            dialog = ProductDimensionUIDialog(self.selected_product_id, self.app_root_dir, self, read_only=False)
            dialog.exec_()
        else:
            QMessageBox.warning(self, self.tr("Aucun Produit Sélectionné"), self.tr("Veuillez sélectionner un produit pour gérer ses dimensions détaillées."))
