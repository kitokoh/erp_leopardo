# -*- coding: utf-8 -*-
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QApplication
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

import db as db_manager
# Import SUPPORTED_LANGUAGES, assuming documents_tab is a sibling
from .documents_tab import SUPPORTED_LANGUAGES

# Assuming ProductDialog and EditProductLineDialog might be passed or imported if self-contained
# For now, they will be passed via constructor from ClientMainWidget's MAIN_MODULE_*

class ProductsTab(QWidget):
    def __init__(self, client_info: dict, config: object,
                 notification_manager: object, current_user_info: dict,
                 main_module_product_dialog: callable,
                 main_module_edit_product_line_dialog: callable,
                 parent_widget: QWidget, # To access tr() and other parent methods
                 parent=None):
        super().__init__(parent)
        self.client_info = client_info
        self.config = config
        self.notification_manager = notification_manager
        self.current_user_info = current_user_info
        self.current_user_id = self.current_user_info.get('user_id')

        self.ProductDialog = main_module_product_dialog
        self.EditProductLineDialog = main_module_edit_product_line_dialog
        self.parent_widget = parent_widget

        self._setup_ui()
        self.load_products() # Initial population

    def tr(self, text, disambiguation=None, n=-1):
        """Helper to access the parent's tr method for translations."""
        if self.parent_widget:
            return self.parent_widget.tr(text, disambiguation, n)
        return QApplication.translate("ProductsTab", text, disambiguation, n)

    def _setup_ui(self):
        logging.info("ProductsTab._setup_ui: Starting setup for Products Tab Structure...")
        products_layout = QVBoxLayout(self)

        # Product Filters
        product_filters_layout = QHBoxLayout()
        product_filters_layout.addWidget(QLabel(self.tr("Filtrer par langue:")))
        self.product_lang_filter_combo = QComboBox()
        self.product_lang_filter_combo.addItem(self.tr("All Languages"), None)
        for lang_code in SUPPORTED_LANGUAGES: # Use imported SUPPORTED_LANGUAGES
             self.product_lang_filter_combo.addItem(self.tr(f"{lang_code}"), lang_code)
        self.product_lang_filter_combo.currentTextChanged.connect(self.load_products)
        product_filters_layout.addWidget(self.product_lang_filter_combo)
        product_filters_layout.addStretch()
        products_layout.addLayout(product_filters_layout)

        self.products_empty_label = QLabel(self.tr("Aucun produit ajouté pour ce client.\nCliquez sur '➕ Ajouter' pour commencer."))
        self.products_empty_label.setAlignment(Qt.AlignCenter)
        font_products_empty = self.products_empty_label.font(); font_products_empty.setPointSize(10)
        self.products_empty_label.setFont(font_products_empty)
        products_layout.addWidget(self.products_empty_label)

        self.products_table = QTableWidget()
        self.products_table.setColumnCount(8) # ID, Name, Desc, Weight, Dims, Qty, Unit Price, Total Price
        self.products_table.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Nom Produit"), self.tr("Description"),
            self.tr("Poids"), self.tr("Dimensions"),
            self.tr("Qté"), self.tr("Prix Unitaire"), self.tr("Prix Total")
        ])
        self.products_table.setEditTriggers(QAbstractItemView.DoubleClicked) # Or NoEditTriggers if using dialog for all edits
        self.products_table.itemChanged.connect(self.handle_product_item_changed)
        self.products_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.products_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.products_table.hideColumn(0) # Hide internal product_id
        products_layout.addWidget(self.products_table)

        products_btn_layout = QHBoxLayout()
        self.add_product_btn = QPushButton(self.tr("Ajouter")); self.add_product_btn.setIcon(QIcon(":/icons/plus-circle.svg"))
        self.add_product_btn.setToolTip(self.tr("Ajouter un produit pour ce client/projet")); self.add_product_btn.clicked.connect(self.add_product)
        products_btn_layout.addWidget(self.add_product_btn)

        self.edit_product_btn = QPushButton(self.tr("Modifier")); self.edit_product_btn.setIcon(QIcon(":/icons/pencil.svg"))
        self.edit_product_btn.setToolTip(self.tr("Modifier le produit sélectionné")); self.edit_product_btn.clicked.connect(self.edit_product)
        products_btn_layout.addWidget(self.edit_product_btn)

        self.remove_product_btn = QPushButton(self.tr("Supprimer")); self.remove_product_btn.setIcon(QIcon(":/icons/trash.svg"))
        self.remove_product_btn.setToolTip(self.tr("Supprimer le produit sélectionné de ce client/projet")); self.remove_product_btn.setObjectName("dangerButton"); self.remove_product_btn.clicked.connect(self.remove_product)
        products_btn_layout.addWidget(self.remove_product_btn)

        products_layout.addLayout(products_btn_layout)

    def load_products(self):
        self.products_table.setRowCount(0)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        client_id = self.client_info.get("client_id")
        if not client_id:
            QApplication.restoreOverrideCursor()
            return

        try:
            # project_id = self.client_info.get("project_id") # Assuming project_id is part of client_info if relevant
            # For now, assume products are linked directly to client or a primary project_id in client_info
            # This might need adjustment if products are per-order/per-project within the client context.
            # The db_manager.get_products_for_client_or_project needs client_id and optionally project_id.
            # Let's assume for now we are loading products linked to the client generally.
            # If multiple projects exist, this logic might need a project selector.
            # For simplicity, using client_id and project_id=None (or a primary project_id from client_info)

            # Language filter
            selected_lang_code = self.product_lang_filter_combo.currentData()

            products = db_manager.get_products_for_client_or_project(client_id, project_id=None, language_code=selected_lang_code)

            if not products:
                self.products_empty_label.show()
                self.products_table.hide()
            else:
                self.products_empty_label.hide()
                self.products_table.show()
                self.products_table.setRowCount(len(products))
                for row, prod in enumerate(products):
                    # Assuming 'client_project_product_id' is the unique ID for this client-product link
                    # and 'product_id' is the global product ID.
                    # The table should display details of the linked product.

                    item_id = QTableWidgetItem(str(prod.get('client_project_product_id'))) # Store link ID
                    item_id.setData(Qt.UserRole, prod.get('client_project_product_id'))
                    self.products_table.setItem(row, 0, item_id) # Hidden column for link ID

                    self.products_table.setItem(row, 1, QTableWidgetItem(prod.get('product_name')))
                    self.products_table.setItem(row, 2, QTableWidgetItem(prod.get('description')))
                    self.products_table.setItem(row, 3, QTableWidgetItem(str(prod.get('weight', ''))))
                    self.products_table.setItem(row, 4, QTableWidgetItem(prod.get('dimensions_notes'))) # Or formatted dimensions

                    qty = float(prod.get('quantity', 0))
                    price_override = prod.get('price_override') # This could be None
                    unit_price = price_override if price_override is not None else float(prod.get('unit_price', 0))
                    total_price = qty * unit_price

                    qty_item = QTableWidgetItem(str(qty))
                    unit_price_item = QTableWidgetItem(f"{unit_price:.2f} €")
                    total_price_item = QTableWidgetItem(f"{total_price:.2f} €")

                    # Make Qty and Price Override editable if desired, or use dialogs
                    # For now, assume they are primarily set via EditProductLineDialog
                    # qty_item.setFlags(qty_item.flags() | Qt.ItemIsEditable)
                    # unit_price_item.setFlags(unit_price_item.flags() | Qt.ItemIsEditable) # If price_override is directly editable

                    self.products_table.setItem(row, 5, qty_item)
                    self.products_table.setItem(row, 6, unit_price_item)
                    self.products_table.setItem(row, 7, total_price_item)
        except Exception as e:
            logging.error(f"Error loading products: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Chargement"), self.tr("Impossible de charger les produits: {0}").format(str(e)))
        finally:
            QApplication.restoreOverrideCursor()
            if hasattr(self.parent_widget, 'load_products_for_dimension_tab'): # Refresh dimension tab if parent has it
                self.parent_widget.load_products_for_dimension_tab()


    def handle_product_item_changed(self, item):
        # This is called if table cells are directly editable.
        # If all edits go through EditProductLineDialog, this might not be needed
        # or could be used for quick updates if direct editing is enabled for some columns.
        # For now, this is a placeholder. The main editing path is via EditProductLineDialog.
        logging.debug(f"ProductsTab.handle_product_item_changed: Item {item.row()},{item.column()} changed to {item.text()}")
        # Example: If quantity (column 5) is directly editable:
        # if item.column() == 5:
        #     try:
        #         new_qty = float(item.text())
        #         link_id = self.products_table.item(item.row(), 0).data(Qt.UserRole)
        #         # db_manager.update_client_product_link_quantity(link_id, new_qty)
        #         # Recalculate total price and update table
        #         # self.load_products() # Or update row directly
        #     except ValueError:
        #         QMessageBox.warning(self, self.tr("Erreur"), self.tr("Quantité invalide."))
        #         self.load_products() # Revert
        pass


    def add_product(self):
        if not self.ProductDialog:
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Le composant d'ajout de produit n'est pas chargé."))
            return

        dialog = self.ProductDialog(client_id=self.client_info.get('client_id'),
                                    project_id=None, # Or a specific project_id if applicable
                                    parent=self)
        if dialog.exec_() == QMessageBox.Accepted: # Assuming ProductDialog returns Accepted/Rejected
            self.load_products()
            if self.notification_manager:
                self.notification_manager.show(self.tr("Succès"), self.tr("Produit ajouté/lié avec succès."), type='SUCCESS')

    def edit_product(self):
        selected_rows = self.products_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, self.tr("Sélection Requise"), self.tr("Veuillez sélectionner un produit à modifier."))
            return

        row_index = selected_rows[0].row()
        client_project_product_id = self.products_table.item(row_index, 0).data(Qt.UserRole) # Link ID

        if not client_project_product_id:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("ID de liaison produit non trouvé."))
            return

        if not self.EditProductLineDialog:
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Le composant de modification de ligne produit n'est pas chargé."))
            return

        dialog = self.EditProductLineDialog(client_project_product_id=client_project_product_id, parent=self)
        if dialog.exec_() == QMessageBox.Accepted:
            self.load_products()
            if self.notification_manager:
                self.notification_manager.show(self.tr("Succès"), self.tr("Ligne produit modifiée avec succès."), type='SUCCESS')

    def remove_product(self):
        selected_rows = self.products_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, self.tr("Sélection Requise"), self.tr("Veuillez sélectionner un produit à supprimer."))
            return

        row_index = selected_rows[0].row()
        client_project_product_id = self.products_table.item(row_index, 0).data(Qt.UserRole)
        product_name = self.products_table.item(row_index, 1).text()

        reply = QMessageBox.question(self, self.tr("Confirmer Suppression"),
                                     self.tr("Êtes-vous sûr de vouloir supprimer le lien vers le produit '{0}'?").format(product_name),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                success = db_manager.remove_product_from_client_or_project(client_project_product_id)
                if success:
                    self.load_products()
                    if self.notification_manager:
                        self.notification_manager.show(self.tr("Succès"), self.tr("Produit délié avec succès."), type='SUCCESS')
                else:
                    QMessageBox.warning(self, self.tr("Échec"), self.tr("Impossible de délier le produit."))
            except Exception as e:
                logging.error(f"Error removing product link: {e}", exc_info=True)
                QMessageBox.critical(self, self.tr("Erreur"), self.tr("Une erreur est survenue: {0}").format(str(e)))

    def apply_permissions_to_tab(self, can_link_products: bool):
        """Applies permissions to buttons within this tab."""
        self.add_product_btn.setEnabled(can_link_products)
        self.edit_product_btn.setEnabled(can_link_products) # Also depends on selection
        self.remove_product_btn.setEnabled(can_link_products) # Also depends on selection

        # Update button states based on selection as well (if needed)
        # For now, edit/remove are primarily permission-gated then selection-gated by their handlers.
        # If table had direct editing, set it read-only:
        # self.products_table.setEditTriggers(QAbstractItemView.NoEditTriggers if not can_link_products else QAbstractItemView.DoubleClicked)

    def refresh_tab_data(self):
        """Public method to refresh data, callable from parent if needed."""
        self.load_products()

# ```
