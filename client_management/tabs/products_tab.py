# -*- coding: utf-8 -*-
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QApplication
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog

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
            self.tr("ID"), self.tr("Nom Produit"), self.tr("Description (Ligne)"), # Nom de colonne modifié pour clarté
            self.tr("Poids (Ligne)"), self.tr("Dimensions (Ligne)"),
            self.tr("Qté"), self.tr("Prix Unitaire (Ligne)"), self.tr("Prix Total")
        ])
        # Permettre l'édition directe pour certaines colonnes
        # self.products_table.setEditTriggers(QAbstractItemView.DoubleClicked) # Garder, ou affiner avec des delegates
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
            selected_lang_code = self.product_lang_filter_combo.currentData() # Keep this to potentially use for client-side filtering if needed

            # Remove language_code from the DB call as it's not supported by the CRUD function
            products = db_manager.get_products_for_client_or_project(client_id, project_id=None)

            # If language filtering is still desired, it would need to be done client-side now,
            # or the backend CRUD function get_products_for_client_or_project needs to be updated
            # to support language_code filtering.
            if selected_lang_code and products:
                products = [p for p in products if p.get('language_code') == selected_lang_code]


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

                    name_item = QTableWidgetItem(prod.get('product_name'))
                    name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable) # Non-editable
                    self.products_table.setItem(row, 1, name_item)

                    desc_item = QTableWidgetItem(prod.get('description')) # Description spécifique à la ligne
                    desc_item.setFlags(desc_item.flags() | Qt.ItemIsEditable) # Editable
                    self.products_table.setItem(row, 2, desc_item)

                    weight_item = QTableWidgetItem(str(prod.get('weight', '')))
                    weight_item.setFlags(weight_item.flags() | Qt.ItemIsEditable) # Editable
                    self.products_table.setItem(row, 3, weight_item)

                    dims_item = QTableWidgetItem(prod.get('dimensions_notes'))
                    dims_item.setFlags(dims_item.flags() | Qt.ItemIsEditable) # Editable
                    self.products_table.setItem(row, 4, dims_item)

                    qty = float(prod.get('quantity', 0))
                    price_override = prod.get('price_override')
                    unit_price = price_override if price_override is not None else float(prod.get('unit_price', 0))
                    total_price = qty * unit_price

                    qty_item = QTableWidgetItem(str(qty))
                    qty_item.setFlags(qty_item.flags() | Qt.ItemIsEditable) # Editable
                    self.products_table.setItem(row, 5, qty_item)

                    unit_price_item = QTableWidgetItem(f"{unit_price:.2f}") # Removed currency symbol for easier float conversion
                    unit_price_item.setFlags(unit_price_item.flags() | Qt.ItemIsEditable) # Editable
                    self.products_table.setItem(row, 6, unit_price_item)

                    total_price_item = QTableWidgetItem(f"{total_price:.2f} €")
                    total_price_item.setFlags(total_price_item.flags() & ~Qt.ItemIsEditable) # Non-editable
                    self.products_table.setItem(row, 7, total_price_item)
        except Exception as e:
            logging.error(f"Error loading products: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Chargement"), self.tr("Impossible de charger les produits: {0}").format(str(e)))
        finally:
            QApplication.restoreOverrideCursor()
            if hasattr(self.parent_widget, 'load_products_for_dimension_tab'): # Refresh dimension tab if parent has it
                self.parent_widget.load_products_for_dimension_tab()


    def handle_product_item_changed(self, item):
        if not item:
            return

        self.products_table.blockSignals(True) # Block signals to prevent recursion

        row = item.row()
        col = item.column()
        new_value_str = item.text()
        link_id_item = self.products_table.item(row, 0)
        if not link_id_item:
            self.products_table.blockSignals(False)
            return

        link_id = link_id_item.data(Qt.UserRole)
        if link_id is None:
            self.products_table.blockSignals(False)
            logging.warning(f"No link_id found for row {row} during item change.")
            return

        update_data = {}
        recalculate_total = False

        try:
            if col == 2: # Description (Ligne)
                update_data['description'] = new_value_str
            elif col == 3: # Poids (Ligne)
                try:
                    update_data['weight'] = float(new_value_str.replace(",", ".")) if new_value_str else None
                except ValueError:
                    QMessageBox.warning(self, self.tr("Donnée Invalide"), self.tr("Le poids doit être un nombre."))
                    self.load_products() # Revert
                    self.products_table.blockSignals(False)
                    return
            elif col == 4: # Dimensions (Ligne)
                update_data['dimensions_notes'] = new_value_str
            elif col == 5: # Qté
                try:
                    update_data['quantity'] = float(new_value_str.replace(",", "."))
                    if update_data['quantity'] < 0: raise ValueError("Quantity cannot be negative")
                    recalculate_total = True
                except ValueError:
                    QMessageBox.warning(self, self.tr("Donnée Invalide"), self.tr("La quantité doit être un nombre positif."))
                    self.load_products() # Revert
                    self.products_table.blockSignals(False)
                    return
            elif col == 6: # Prix Unitaire (Ligne)
                try:
                    update_data['price_override'] = float(new_value_str.replace("€", "").replace(",", ".").strip())
                    if update_data['price_override'] < 0: raise ValueError("Price cannot be negative")
                    recalculate_total = True
                except ValueError:
                    QMessageBox.warning(self, self.tr("Donnée Invalide"), self.tr("Le prix unitaire doit être un nombre positif."))
                    self.load_products() # Revert
                    self.products_table.blockSignals(False)
                    return
            else:
                self.products_table.blockSignals(False)
                return # No action for other columns

            if update_data:
                success = db_manager.update_client_project_product_details(link_id, update_data)
                if success:
                    if self.notification_manager:
                        self.notification_manager.show(self.tr("Succès"), self.tr("Produit mis à jour."), type="SUCCESS")
                    if recalculate_total:
                        # Re-fetch the updated item to get all necessary fields for total calculation
                        updated_item_data = db_manager.get_client_project_product_by_link_id(link_id)
                        if updated_item_data:
                            qty = float(updated_item_data.get('quantity', 0))
                            price_override = updated_item_data.get('price_override')
                            unit_price = price_override if price_override is not None else float(updated_item_data.get('unit_price', 0))
                            total_price = qty * unit_price
                            total_price_item = self.products_table.item(row, 7)
                            if total_price_item:
                                total_price_item.setText(f"{total_price:.2f} €")
                            else: # Should not happen if table is correctly populated
                                self.products_table.setItem(row, 7, QTableWidgetItem(f"{total_price:.2f} €"))
                        else:
                            self.load_products() # Fallback to full reload if fetching updated item fails
                else:
                    QMessageBox.warning(self, self.tr("Échec"), self.tr("Impossible de mettre à jour le produit."))
                    self.load_products() # Revert
        except Exception as e:
            logging.error(f"Error in handle_product_item_changed for link_id {link_id}: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Une erreur est survenue lors de la mise à jour."))
            self.load_products() # Revert to known state
        finally:
            self.products_table.blockSignals(False)


    def add_product(self):
        if not self.ProductDialog:
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Le composant d'ajout de produit n'est pas chargé."))
            return

        # Get app_root_dir from parent_widget (ClientMainWidget)
        app_root_dir = None
        if hasattr(self.parent_widget, 'app_root_dir'):
            app_root_dir = self.parent_widget.app_root_dir
        else:
            QMessageBox.critical(self, self.tr("Erreur Configuration"), self.tr("Le répertoire racine de l'application n'est pas accessible."))
            return

        dialog = self.ProductDialog(client_id=self.client_info.get('client_id'),
                                    app_root_dir=app_root_dir, # Pass app_root_dir
                                    # product_data=None, # Not editing an existing one here
                                    parent=self)
        if dialog.exec_() == QDialog.Accepted: # ProductDialog uses QDialog.Accepted
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


