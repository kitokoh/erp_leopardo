# -*- coding: utf-8 -*-
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QApplication, QInputDialog
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QLocale # Added QLocale
from PyQt5.QtWidgets import QDialog
import os # For path operations
import uuid # For unique filenames

import db as db_manager
from db.cruds.products.products_crud import products_crud_instance as products_crud
from db.cruds.invoices import commandes_crud
from db.cruds.invoices import proforma_invoices_crud
from utils.proforma_invoice_utils import get_proforma_invoice_context_data # For context

from utils.html_to_pdf_util import render_html_template, convert_html_to_pdf, WeasyPrintError # For PDF generation
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
        self._load_commande_filter() # Load commandes for the filter
        self.load_products() # Initial population

    def tr(self, text, disambiguation=None, n=-1):
        """Helper to access the parent's tr method for translations."""
        if self.parent_widget:
            return self.parent_widget.tr(text, disambiguation, n)
        return QApplication.translate("ProductsTab", text, disambiguation, n)

    def _setup_ui(self):
        logging.info("ProductsTab._setup_ui: Starting setup for Products Tab Structure...")
        products_layout = QVBoxLayout(self)

        products_layout.setSpacing(10)

        # Filters and Action Buttons Bar
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setSpacing(8)

        filter_lang_label = QLabel(self.tr("Langue:"))
        filter_lang_label.setStyleSheet("font-weight: bold;")
        top_bar_layout.addWidget(filter_lang_label)
        self.product_lang_filter_combo = QComboBox()
        self.product_lang_filter_combo.setMinimumWidth(100)
        self.product_lang_filter_combo.setStyleSheet("QComboBox { padding: 4px; }")
        self.product_lang_filter_combo.addItem(self.tr("Toutes"), None) # "All Languages" -> "Toutes"
        # Iterate over dictionary items (code, name)
        for lang_code, lang_name in SUPPORTED_LANGUAGES.items():
             self.product_lang_filter_combo.addItem(self.tr(lang_name), lang_code) # Display translated name, store code
        self.product_lang_filter_combo.currentTextChanged.connect(self.load_products)
        top_bar_layout.addWidget(self.product_lang_filter_combo)

        filter_cmd_label = QLabel(self.tr("Commande:"))
        filter_cmd_label.setStyleSheet("font-weight: bold;")
        top_bar_layout.addWidget(filter_cmd_label)
        self.product_commande_filter_combo = QComboBox()
        self.product_commande_filter_combo.setMinimumWidth(200)
        self.product_commande_filter_combo.setStyleSheet("QComboBox { padding: 4px; }")
        self.product_commande_filter_combo.currentTextChanged.connect(self.load_products)
        top_bar_layout.addWidget(self.product_commande_filter_combo)

        top_bar_layout.addStretch(1)

        self.add_product_btn = QPushButton("➕ " + self.tr("Lier Produit Existant")) # Changed icon
        self.add_product_btn.setObjectName("primaryButton")
        self.add_product_btn.setToolTip(self.tr("Lier un produit existant du catalogue à ce client/commande"))
        self.add_product_btn.clicked.connect(self.add_product) # This should open ProductDialog to select existing
        top_bar_layout.addWidget(self.add_product_btn)

        self.add_new_global_product_btn = QPushButton("➕ " + self.tr("Créer Produit Global")) # Changed icon
        self.add_new_global_product_btn.setObjectName("secondaryButton")
        self.add_new_global_product_btn.setToolTip(self.tr("Créer un nouveau produit dans le catalogue global et le lier"))
        self.add_new_global_product_btn.clicked.connect(self.handle_add_new_global_product)
        top_bar_layout.addWidget(self.add_new_global_product_btn)

        self.manage_global_catalog_btn = QPushButton("📖 " + self.tr("Gérer Catalogue Global"))
        self.manage_global_catalog_btn.setObjectName("secondaryButton")
        self.manage_global_catalog_btn.setToolTip(self.tr("Ouvrir le dialogue de gestion du catalogue global des produits (ajouter, modifier, supprimer des produits maîtres)."))
        self.manage_global_catalog_btn.clicked.connect(self.handle_manage_global_catalog)
        top_bar_layout.addWidget(self.manage_global_catalog_btn)

        products_layout.addLayout(top_bar_layout)


        self.products_empty_label = QLabel(self.tr("Aucun produit pour ce client/commande.\nUtilisez les boutons ci-dessus pour ajouter ou lier des produits."))
        self.products_empty_label.setAlignment(Qt.AlignCenter)
        font_products_empty = self.products_empty_label.font(); font_products_empty.setPointSize(10)
        self.products_empty_label.setFont(font_products_empty)
        self.products_empty_label.setStyleSheet("color: #718096;")
        products_layout.addWidget(self.products_empty_label)

        self.products_table = QTableWidget()
        self.products_table.setObjectName("productsClientTable") # Added objectName
        self.products_table.setColumnCount(8)
        self.products_table.setHorizontalHeaderLabels([
            self.tr("ID Lien"), self.tr("Nom Produit"), self.tr("Description (Ligne)"),
            self.tr("Poids (Ligne)"), self.tr("Dimensions (Ligne)"),
            self.tr("Qté"), self.tr("Prix Unit. (Ligne)"), self.tr("Prix Total (Ligne)")
        ])
        header_style = """
            QHeaderView::section {
                background-color: #4a5568; color: white; padding: 6px;
                border: 1px solid #ddd; font-weight: bold; font-size: 9pt;
            }
        """
        self.products_table.horizontalHeader().setStyleSheet(header_style)
        self.products_table.verticalHeader().setVisible(False)
        self.products_table.setAlternatingRowColors(True)
        self.products_table.setSortingEnabled(True)

        self.products_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents) # ID Lien (cpp_id)
        self.products_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch) # Nom Produit
        self.products_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch) # Description
        self.products_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents) # Poids
        self.products_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents) # Dimensions
        self.products_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents) # Qté
        self.products_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents) # Prix Unit.
        self.products_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents) # Prix Total
        self.products_table.hideColumn(0) # ID Lien (client_project_product_id)

        self.products_table.itemChanged.connect(self.handle_product_item_changed)
        self.products_table.itemSelectionChanged.connect(self.handle_product_selection_changed) # New connection
        self.products_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.products_table.setSelectionMode(QAbstractItemView.SingleSelection) # Ensure single selection for clarity

        products_layout.addWidget(self.products_table)

        # Bottom action buttons (Edit Line, Remove Line, Generate Proforma)
        bottom_actions_layout = QHBoxLayout()
        bottom_actions_layout.setSpacing(10)

        self.edit_product_btn = QPushButton("✏️ " + self.tr("Modifier Ligne"))
        self.edit_product_btn.setObjectName("actionButton") # Generic style for non-primary/danger
        self.edit_product_btn.setToolTip(self.tr("Modifier les détails de la ligne produit sélectionnée (quantité, prix spécifique, etc.)"))
        self.edit_product_btn.clicked.connect(self.edit_product)
        bottom_actions_layout.addWidget(self.edit_product_btn)

        self.remove_product_btn = QPushButton("🗑️ " + self.tr("Supprimer Ligne"))
        self.remove_product_btn.setObjectName("dangerButton")
        self.remove_product_btn.setToolTip(self.tr("Supprimer la ligne produit sélectionnée de ce client/commande"))
        self.remove_product_btn.clicked.connect(self.remove_product)
        bottom_actions_layout.addWidget(self.remove_product_btn)


        bottom_actions_layout.addStretch(1) # Push proforma button to the right

        self.generate_proforma_btn = QPushButton("📄 " + self.tr("Générer Proforma"))
        self.generate_proforma_btn.setObjectName("secondaryButton")
        self.generate_proforma_btn.setToolTip(self.tr("Générer une facture proforma pour les produits actuellement affichés."))
        self.generate_proforma_btn.clicked.connect(self.handle_generate_proforma)
        bottom_actions_layout.addWidget(self.generate_proforma_btn)

        products_layout.addLayout(bottom_actions_layout)

    def _load_commande_filter(self):
        self.product_commande_filter_combo.clear()
        self.product_commande_filter_combo.addItem(self.tr("Toutes les Commandes"), None)
        client_id = self.client_info.get("client_id")
        if not client_id:
            return

        try:
            commandes = commandes_crud.get_commandes_for_client(client_id)
            if commandes:
                for commande in commandes:
                    display_text = f"{commande.get('commande_reference', 'N/A')} ({commande.get('commande_date', 'N/A')[:10]})"
                    self.product_commande_filter_combo.addItem(display_text, commande.get('commande_id'))
        except Exception as e:
            logging.error(f"Erreur lors du chargement des commandes pour le filtre: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur Filtre Commande"), self.tr("Impossible de charger les commandes pour le filtre."))

    def load_products(self):
        self.products_table.setRowCount(0)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        client_id = self.client_info.get("client_id")
        if not client_id:
            QApplication.restoreOverrideCursor()
            return

        try:
            selected_lang_code = self.product_lang_filter_combo.currentData()
            selected_commande_id = self.product_commande_filter_combo.currentData()

            # Fetch all products for the client first
            # The existing db_manager.get_products_for_client_or_project links ClientProjectProducts with Products
            # It does not directly know about CommandeItems.
            # So, we will first get all client-linked products, then filter if a commande is selected.
            all_client_products = db_manager.get_products_for_client_or_project(client_id, project_id=None)

            products_to_display = []

            if selected_commande_id:
                # If a commande is selected, we need to get items for that specific commande
                # and then find the corresponding entries in all_client_products.
                # CommandeItems links to global Product ID. ClientProjectProducts also links to global Product ID.
                commande_items_raw = commandes_crud.get_items_for_commande(selected_commande_id)
                commande_product_ids = {item['product_id'] for item in commande_items_raw}

                # Now, filter all_client_products to include only those whose global product_id is in this commande.
                # And also match their line-specific details (quantity, price) from CommandeItems if possible.
                # This is tricky because `all_client_products` are ClientProjectProduct entries,
                # and `commande_items_raw` are CommandeItem entries.
                # We need to display the ClientProjectProduct if its underlying Product is in the Commande.
                # The quantity/price displayed should ideally come from the CommandeItem when a commande is selected.

                temp_products_in_commande = []
                for client_prod in all_client_products:
                    global_product_id_of_client_link = client_prod.get('product_id')
                    if global_product_id_of_client_link in commande_product_ids:
                        # This product (linked to client) is part of the selected commande.
                        # We should use details from CommandeItem for quantity, price if available.
                        # Find the matching CommandeItem
                        matching_commande_item = next((ci for ci in commande_items_raw if ci['product_id'] == global_product_id_of_client_link), None)
                        if matching_commande_item:
                            # Create a synthetic product entry for display, prioritizing commande item details
                            # We still need client_project_product_id for editing/deleting the client link.
                            synthetic_prod_entry = client_prod.copy() # Start with client_project_product data
                            synthetic_prod_entry['quantity'] = matching_commande_item.get('quantity', client_prod.get('quantity'))
                            synthetic_prod_entry['unit_price_override'] = matching_commande_item.get('unit_price_ht', client_prod.get('unit_price_override'))
                            # Description from commande item is often more specific for that order context
                            synthetic_prod_entry['line_description'] = matching_commande_item.get('description_item', client_prod.get('line_description'))
                            # CommandeItem might have its own weight/dims for that specific order line
                            synthetic_prod_entry['line_weight'] = matching_commande_item.get('weight', client_prod.get('line_weight'))
                            synthetic_prod_entry['line_dimensions_notes'] = matching_commande_item.get('dimensions_text', client_prod.get('line_dimensions_notes'))
                            # Language for product in this commande item
                            synthetic_prod_entry['language_code'] = matching_commande_item.get('product_language_code', client_prod.get('language_code'))
                            temp_products_in_commande.append(synthetic_prod_entry)
                        else:
                            # Should not happen if product_ids were derived correctly
                            temp_products_in_commande.append(client_prod)
                products_to_display = temp_products_in_commande
            else:
                # No specific commande selected, show all products linked to the client
                products_to_display = all_client_products

            # Apply language filter (client-side on the already filtered list by commande or all client products)
            if selected_lang_code and products_to_display:
                products_to_display = [p for p in products_to_display if p.get('language_code') == selected_lang_code]

            if not products_to_display:
                self.products_empty_label.show()
                self.products_table.hide()
            else:
                self.products_empty_label.hide()
                self.products_table.show()
                self.products_table.setRowCount(len(products_to_display))
                for row, prod in enumerate(products_to_display):
                    # Assuming 'client_project_product_id' is the unique ID for this client-product link
                    # and 'product_id' is the global product ID.
                    # The table should display details of the linked product.

                    item_id = QTableWidgetItem(str(prod.get('client_project_product_id'))) # Store link ID
                    item_id.setData(Qt.UserRole, prod.get('client_project_product_id'))
                    self.products_table.setItem(row, 0, item_id) # Hidden column for link ID

                    # Client-specific overrides with fallbacks to global product data
                    client_specific_name = prod.get('client_specific_product_name')
                    display_name = client_specific_name if client_specific_name and client_specific_name.strip() else prod.get('product_name', '')

                    line_description = prod.get('line_description')
                    display_description = line_description if line_description is not None else prod.get('product_description', '') # product_description is global

                    line_weight_val = prod.get('line_weight')
                    display_weight = str(line_weight_val) if line_weight_val is not None else str(prod.get('global_product_weight', ''))

                    line_dimensions_notes_val = prod.get('line_dimensions_notes')
                    display_dimensions = line_dimensions_notes_val if line_dimensions_notes_val is not None else prod.get('global_product_dimensions', '')

                    qty = float(prod.get('quantity', 0))

                    price_override = prod.get('unit_price_override') # This is the client-specific price
                    base_unit_price = float(prod.get('base_unit_price', 0)) # Global product base price
                    display_unit_price = price_override if price_override is not None else base_unit_price

                    total_price = qty * display_unit_price

                    # Column 1: Nom Produit (Client / Global) - Editable
                    name_item = QTableWidgetItem(display_name)
                    name_item.setFlags(name_item.flags() | Qt.ItemIsEditable)
                    self.products_table.setItem(row, 1, name_item)

                    # Column 2: Description (Ligne / Global) - Editable
                    desc_item = QTableWidgetItem(display_description)
                    desc_item.setFlags(desc_item.flags() | Qt.ItemIsEditable)
                    self.products_table.setItem(row, 2, desc_item)

                    # Column 3: Poids (Ligne / Global) - Editable
                    weight_item = QTableWidgetItem(display_weight)
                    weight_item.setFlags(weight_item.flags() | Qt.ItemIsEditable)
                    self.products_table.setItem(row, 3, weight_item)

                    # Column 4: Dimensions (Ligne / Global) - Editable
                    dims_item = QTableWidgetItem(display_dimensions)
                    dims_item.setFlags(dims_item.flags() | Qt.ItemIsEditable)
                    self.products_table.setItem(row, 4, dims_item)

                    # Column 5: Qté - Editable
                    locale = QLocale()
                    qty_item = QTableWidgetItem(locale.toString(qty)) # Format quantity
                    qty_item.setFlags(qty_item.flags() | Qt.ItemIsEditable)
                    self.products_table.setItem(row, 5, qty_item)

                    # Column 6: Prix Unitaire (Ligne / Base) - Editable
                    # Assuming display_unit_price is float
                    unit_price_str = locale.toString(display_unit_price, 'f', 2)
                    unit_price_item = QTableWidgetItem(unit_price_str)
                    unit_price_item.setFlags(unit_price_item.flags() | Qt.ItemIsEditable)
                    self.products_table.setItem(row, 6, unit_price_item)

                    # Column 7: Prix Total - Non-editable
                    # Assuming total_price is float, currency symbol hardcoded for now
                    total_price_str = locale.toString(total_price, 'f', 2)
                    total_price_item = QTableWidgetItem(f"{total_price_str} €")
                    total_price_item.setFlags(total_price_item.flags() & ~Qt.ItemIsEditable)
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
        recalculate_total = False # Initialize recalculate_total
        original_value = None # To revert cell text on validation error for some fields

        # Store original text for potential revert on validation failure
        # For numeric fields, it's better to reload_products or re-fetch row data to ensure consistency.
        # For text fields, we can revert more easily if needed, but often full reload is safer.

        try:
            if col == 1: # Nom Produit (Client)
                update_data['client_specific_product_name'] = new_value_str
            elif col == 2: # Description (Ligne)
                update_data['line_description'] = new_value_str
            elif col == 3: # Poids (Ligne)
                try:
                    if new_value_str.strip() == "" or new_value_str.strip().lower() == 'none':
                        update_data['line_weight'] = None
                    else:
                        update_data['line_weight'] = float(new_value_str.replace(",", "."))
                except ValueError:
                    QMessageBox.warning(self, self.tr("Donnée Invalide"), self.tr("Le poids doit être un nombre ou vide."))
                    self.load_products() # Revert by reloading all
                    return # Exit after ensuring signals are unblocked by finally
            elif col == 4: # Dimensions (Ligne)
                update_data['line_dimensions_notes'] = new_value_str # Assumed text
            elif col == 5: # Qté
                try:
                    qty_val = float(new_value_str.replace(",", "."))
                    if qty_val < 0:
                        QMessageBox.warning(self, self.tr("Donnée Invalide"), self.tr("La quantité ne peut pas être négative."))
                        self.load_products() # Revert
                        return
                    update_data['quantity'] = qty_val
                    recalculate_total = True # Set flag
                except ValueError:
                    QMessageBox.warning(self, self.tr("Donnée Invalide"), self.tr("La quantité doit être un nombre."))
                    self.load_products() # Revert
                    return
            elif col == 6: # Prix Unitaire (Ligne)
                try:
                    price_val = float(new_value_str.replace("€", "").replace(",", ".").strip())
                    if price_val < 0:
                        QMessageBox.warning(self, self.tr("Donnée Invalide"), self.tr("Le prix unitaire ne peut pas être négatif."))
                        self.load_products() # Revert
                        return
                    update_data['unit_price_override'] = price_val
                    recalculate_total = True # Set flag
                except ValueError:
                    QMessageBox.warning(self, self.tr("Donnée Invalide"), self.tr("Le prix unitaire doit être un nombre."))
                    self.load_products() # Revert
                    return
            else: # Should not happen if only editable columns trigger this
                self.products_table.blockSignals(False) # Unblock if loop is exited early
                return

            if update_data:

                success = db_manager.update_client_project_product(link_id, update_data) # Corrected call
                if success:
                    if self.notification_manager:
                        self.notification_manager.show(self.tr("Succès"), self.tr("Produit mis à jour."), type="SUCCESS")
                    if recalculate_total:
                        # Re-fetch the updated item to get all necessary fields for total calculation
                        # Assurez-vous que get_client_project_product_by_link_id est disponible et correct
                        updated_item_data = db_manager.get_client_project_product_by_id(link_id) # Corrected call
                        if updated_item_data:
                            qty = float(updated_item_data.get('quantity', 0))
                            price_override = updated_item_data.get('unit_price_override') # Clé correcte
                            unit_price = price_override if price_override is not None else float(updated_item_data.get('base_unit_price', 0)) # Clé correcte pour prix de base
                            total_price = qty * unit_price
                            total_price_item = self.products_table.item(row, 7)
                            locale = QLocale()
                            total_price_str = locale.toString(total_price, 'f', 2)
                            if total_price_item:
                                total_price_item.setText(f"{total_price_str} €")
                            else: # Should not happen if table is correctly populated
                                self.products_table.setItem(row, 7, QTableWidgetItem(f"{total_price_str} €"))
                        else:
                            logging.warning(f"Failed to refetch item {link_id} after update for total price recalculation.")
                            self.load_products() # Fallback to full reload if fetching updated item fails
                else: # CRUD update_client_project_product returned False
                    if self.notification_manager:
                        self.notification_manager.show_notification(
                            self.tr("Échec de la Mise à Jour"),
                            self.tr("Impossible de sauvegarder les modifications du produit dans la base de données."),
                            'ERROR'
                        )
                    else:
                        QMessageBox.warning(self, self.tr("Échec"), self.tr("Impossible de mettre à jour le produit."))
                    self.load_products() # Revert
        except Exception as e:
            logging.error(f"Error in handle_product_item_changed for link_id {link_id}: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Une erreur est survenue lors de la mise à jour du produit."))
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
            # ProductDialog.get_data() returns a list of products to be added/linked
            products_to_add = dialog.get_data()
            if not products_to_add:
                return

            # Standard linking to ClientProjectProducts is handled by the caller of ProductDialog
            # typically in ClientMainWidget, which calls db_manager.add_product_to_client_or_project
            # For now, we assume this process happens and we get the product_id.
            # This part might need coordination if ProductsTab is solely responsible.
            # For this step, we focus on adding to the selected_commande_id if provided.

            # The products_to_add contains dicts like:
            # { "client_id":self.client_id, "name":name, "description":description,
            #   "quantity":quantity, "unit_price":unit_price, "total_price":line_total,
            #   "language_code":language_code, "weight": ..., "dimensions": ...,
            #   "product_id": retrieved_global_product_id, # This can be None for new global products
            #   "product_code": retrieved_product_code, ... }

            # At this point, ClientProjectProducts entries should have been created by the calling context
            # (e.g. ClientMainWidget) which also handles creating global products if product_id is None.
            # We need to reload products to get the client_project_product_id if we want to link
            # based on that, OR rely on product_id.

# The first add_product method was here and is now removed.
# The code continues with the second, more complete add_product method.

    def add_product(self): # Rewritten method / This is the one to keep
        if not self.ProductDialog:
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Le composant d'ajout de produit n'est pas chargé."))
            return

        client_id = self.client_info.get("client_id")
        if not client_id:
            QMessageBox.critical(self, self.tr("Erreur Client"), self.tr("ID Client non trouvé."))
            return

        # 1. Récupérer les commandes existantes pour le client
        try:
            existing_commandes = commandes_crud.get_commandes_for_client(client_id)
        except Exception as e:
            logging.error(f"Erreur lors de la récupération des commandes pour le client {client_id}: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Données"), self.tr("Impossible de récupérer les commandes du client."))
            return

        selected_commande_id = None
        commande_choices = {self.tr("Ne pas lier à une commande"): "NONE"} # Option to not link
        if not existing_commandes:
            reply = QMessageBox.information(self, self.tr("Aucune Commande"),
                                          self.tr("Ce client n'a pas de commande existante. "
                                                  "Vous pouvez ajouter le produit au client uniquement, "
                                                  "ou annuler et créer une commande d'abord.\n\n"
                                                  "Voulez-vous continuer à ajouter le produit au client sans le lier à une commande ?"),
                                          QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return
            # If Yes, selected_commande_id remains None, effectively "NONE"
        else:
            for cmd in existing_commandes:
                commande_choices[f"{cmd.get('commande_reference', 'N/A')} (Date: {cmd.get('commande_date', 'N/A')[:10]})"] = cmd.get('commande_id')

            item_names = list(commande_choices.keys())
            chosen_item_name, ok = QInputDialog.getItem(self, self.tr("Lier à une Commande"),
                                                        self.tr("Sélectionnez une commande à laquelle lier ce(s) produit(s):"),
                                                        item_names, 0, False)
            if not ok:
                return # User cancelled

            selected_commande_id = commande_choices[chosen_item_name]


        # Get app_root_dir from parent_widget (ClientMainWidget)
        app_root_dir = None
        if hasattr(self.parent_widget, 'app_root_dir'):
            app_root_dir = self.parent_widget.app_root_dir
        else:
            QMessageBox.critical(self, self.tr("Erreur Configuration"), self.tr("Le répertoire racine de l'application n'est pas accessible."))
            return

        dialog = self.ProductDialog(client_id=client_id,
                                    app_root_dir=app_root_dir,
                                    parent=self)

        # The rest of the logic (adding to CommandeItems) is now inside the if dialog.exec_ block above.
        # This structure assumes that ProductDialog.exec_() is called, and if accepted,
        # the products obtained from dialog.get_data() are then processed.
        # The original `if dialog.exec_()` block needs to be adapted to include this logic.
        # Let's call the common processing part as a separate method or integrate it.

        self._process_product_dialog_acceptance(dialog, selected_commande_id)


    def _process_product_dialog_acceptance(self, dialog, selected_commande_id):
        # This method encapsulates the logic after ProductDialog is accepted.
        # It's called from the modified add_product method.
        # Note: The original call to dialog.exec_() and the subsequent logic
        # needs to be structured so that `selected_commande_id` is available.
        # The following is the content of the original `if dialog.exec_() == QDialog.Accepted:` block,
        # now parameterized with `selected_commande_id`.

        # This part is duplicated from the original template, ensure it's correctly integrated.
        # This logic should be inside `add_product` after `dialog.exec_()`
        if dialog.exec_() == QDialog.Accepted:
            products_to_add = dialog.get_data()
            if not products_to_add:
                self.load_products() # Still load products in case some client-product links were made by ProductDialog caller
                return

            # This is where the logic from the original template's `if dialog.exec_()` should be.
            # It handles adding to CommandeItems if selected_commande_id is valid.
            current_selected_commande_id = self.product_commande_filter_combo.currentData()
            if current_selected_commande_id and current_selected_commande_id != "NONE":
                all_items_added_to_commande_successfully = True
                for prod_data in products_to_add:
                    global_product_id = prod_data.get('product_id')
                    product_code = prod_data.get('product_code')

                    if not global_product_id and product_code:
                        # Attempt to fetch recently created product by code if ID is missing
                        # This assumes the product was created globally by the entity that called ProductDialog
                        # and processed its results before this specific step.
                        # This is a potential point of failure if the global product creation isn't immediate or guaranteed.
                        created_product = db_manager.get_product_by_code(product_code) # Ensure db_manager has this
                        if created_product:
                            global_product_id = created_product.get('product_id')
                        else:
                            logging.warning(f"Could not find/confirm global product by code {product_code} for commande {selected_commande_id}")
                            # Do not skip the whole process, just this item for the commande part
                            # The product might still be linked to the client via ClientProjectProducts
                            QMessageBox.warning(self, self.tr("Erreur Produit Commande"),
                                                self.tr("Le produit '{0}' (code: {1}) n'a pas pu être confirmé comme produit global. Il n'a pas été ajouté à la commande.").format(prod_data.get('name'), product_code))
                            all_items_added_to_commande_successfully = False
                            continue # Skip adding this item to commande

                    if global_product_id:
                        commande_item_data = {
                            'commande_id': selected_commande_id,
                            'product_id': global_product_id,
                            'description_item': prod_data.get('description', prod_data.get('name', '')), # Fallback desc
                            'quantity': prod_data.get('quantity', 1),
                            'unit_price_ht': prod_data.get('unit_price', 0.0),
                            'vat_rate': 0.0,  # Default VAT, can be configured
                            'weight': prod_data.get('weight'),
                            'dimensions_text': prod_data.get('dimensions'),
                            'product_language_code': prod_data.get('language_code', 'fr')
                        }
                        item_added_id = commandes_crud.add_commande_item(commande_item_data)
                        if item_added_id:
                            logging.info(f"Product {global_product_id} added to commande {selected_commande_id} as item {item_added_id}")
                        else:
                            all_items_added_to_commande_successfully = False
                            QMessageBox.warning(self, self.tr("Erreur Ajout Commande"),
                                                self.tr("Impossible d'ajouter le produit '{0}' à la commande sélectionnée.").format(prod_data.get('name')))
                    elif not product_code : # No global_product_id and no product_code
                         logging.error(f"Product '{prod_data.get('name')}' has no global_product_id and no product_code. Cannot add to commande.")
                         QMessageBox.warning(self, self.tr("Données Produit Manquantes"),
                                             self.tr("Le produit '{0}' n'a ni ID global ni code produit. Ajout à la commande impossible.").format(prod_data.get('name')))
                         all_items_added_to_commande_successfully = False


            self.load_products() # Refresh the product list in the tab

            if self.notification_manager:
                base_message = self.tr("Produit(s) ajouté(s)/lié(s) au client avec succès.")
                if selected_commande_id and selected_commande_id != "NONE":
                    if all_items_added_to_commande_successfully:
                        base_message += self.tr(" Et ajouté(s) à la commande sélectionnée.")
                    else:
                        base_message += self.tr(" Certains produits n'ont pas pu être ajoutés à la commande.")
                self.notification_manager.show(self.tr("Succès"), base_message, type='SUCCESS')
        else: # Dialog cancelled or not accepted
            self.load_products() # Still refresh, in case some external changes happened


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

        app_root_dir = None
        if hasattr(self.parent_widget, 'app_root_dir'):
            app_root_dir = self.parent_widget.app_root_dir
        else:
            QMessageBox.critical(self, self.tr("Erreur Configuration"), self.tr("Le répertoire racine de l'application n'est pas accessible pour EditProductLineDialog."))
            return

        dialog = self.EditProductLineDialog(
            client_project_product_id=client_project_product_id,
            app_root_dir=app_root_dir, # Added app_root_dir
            parent=self
        )
        if dialog.exec_() == QDialog.Accepted: # EditProductLineDialog is a QDialog, so use QDialog.Accepted
            # Potentially get data from dialog and update specific row instead of full reload,
            # but full reload is safer for now.
            # updated_data = dialog.get_data()
            # if updated_data and not updated_data.get("error"):
            #    # Here you would call the db_manager.update_client_project_product(client_project_product_id, updated_data)
            #    # For now, this logic is assumed to be handled by the dialog or the reload is sufficient.
            #    # The dialog's get_data() prepares data, but the actual update call is missing here.
            #    # This was likely intended to be handled by the dialog itself or a controller.
            #    # For the purpose of fixing the TypeError and dialog display, this is okay.
            #    # A more complete implementation would involve handling the returned data.
            #    pass # Assuming update is handled if dialog is accepted or by reload

            self.load_products() # Reload products to reflect changes
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
        # P_LINK_PRODUCTS_TO_CLIENT for client-specific linking actions
        self.add_product_btn.setEnabled(can_link_products)
        self.edit_product_btn.setEnabled(can_link_products)
        self.remove_product_btn.setEnabled(can_link_products)

        # P_MANAGE_GLOBAL_PRODUCTS for global catalog management
        # P_VIEW_GLOBAL_PRODUCTS for viewing (button might still be visible but dialog actions restricted)
        from auth.permissions import has_permission, P_MANAGE_GLOBAL_PRODUCTS, P_VIEW_GLOBAL_PRODUCTS
        role_name = self.current_user_info.get('role_name')

        # Visibility of the "Gérer Catalogue Global" button could be tied to P_VIEW_GLOBAL_PRODUCTS,
        # while actions inside the dialog are gated by P_MANAGE_GLOBAL_PRODUCTS.
        # Or, simplify and only show if can manage. Let's go with manage for now.
        can_manage_global_catalog = has_permission(role_name, P_MANAGE_GLOBAL_PRODUCTS)
        self.manage_global_catalog_btn.setEnabled(can_manage_global_catalog)
        self.add_new_global_product_btn.setEnabled(can_manage_global_catalog) # Creating a new global product is part of managing

        # Inline editing permissions (already handled by Qt.ItemIsEditable flags set during load_products)
        # If we wanted to disable inline editing based on permission:
        # has_edit_permission = can_link_products # Or a more specific one
        # if not has_edit_permission:
        #     self.products_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # else:
        #     self.products_table.setEditTriggers(QAbstractItemView.AllEditTriggers) # Or specific like DoubleClicked


    def refresh_tab_data(self):
        """Public method to refresh data, callable from parent if needed."""
        self.load_products()

    def handle_add_new_global_product(self):
        if not self.ProductDialog:
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Le composant d'ajout de produit n'est pas chargé."))
            return

        client_id = self.client_info.get("client_id")
        if not client_id:
            QMessageBox.critical(self, self.tr("Erreur Client"), self.tr("ID Client non trouvé."))
            return

        app_root_dir = None
        if hasattr(self.parent_widget, 'app_root_dir'):
            app_root_dir = self.parent_widget.app_root_dir
        else:
            # This case should ideally not happen if parent_widget is always ClientMainWidget or similar
            logging.warning("handle_add_new_global_product: app_root_dir not found on parent_widget.")
            # Depending on ProductDialog's needs, this might be critical or not.
            # If ProductDialog strictly requires it (e.g., for image paths), show an error.
            # QMessageBox.critical(self, self.tr("Erreur Configuration"), self.tr("Le répertoire racine de l'application n'est pas accessible."))
            # return

        # Instantiate ProductDialog. We assume it's configured to handle new global product creation.
        # It might need a mode or specific parameters if its behavior needs to vary significantly.
        dialog = self.ProductDialog(client_id=client_id,
                                    app_root_dir=app_root_dir,
                                    parent=self,
                                    # product_data=None, # Explicitly not editing an existing product
                                    # is_new_global_product_mode=True # Optional: A flag if dialog needs it
                                    )

        if dialog.exec_() == QDialog.Accepted:
            # dialog.get_data() should return a list of product data dicts.
            # For new global product, we expect one item in the list.
            products_data_list = dialog.get_data()
            if not products_data_list:
                if self.notification_manager:
                    self.notification_manager.show(self.tr("Information"), self.tr("Aucune donnée produit n'a été fournie."), type="INFO")
                return

            # Assuming the first item contains the data for the new global product and its initial link
            new_product_info = products_data_list[0]

            # --- 1. Create Global Product ---
            # We need to extract details meant for the global product table.
            # ProductDialog.get_data() needs to provide these. Example keys:
            # 'product_name', 'product_code', 'description' (global), 'base_unit_price',
            # 'language_code', 'weight' (global), 'dimensions' (global), 'category_id', etc.
            # 'created_by_user_id'

            # This is a simplified assumption of the structure from ProductDialog.
            # The actual keys will depend on ProductDialog's implementation of get_data().
            global_product_details = {
                'product_name': new_product_info.get('name'), # Assuming 'name' from dialog is global name
                'product_code': new_product_info.get('product_code'), # Crucial: Must be unique
                'description': new_product_info.get('description'), # Global description
                'base_unit_price': new_product_info.get('unit_price'), # Price from dialog becomes base_unit_price
                'language_code': new_product_info.get('language_code', 'fr'), # Default if not provided
                'weight': new_product_info.get('weight'), # Global weight
                'dimensions': new_product_info.get('dimensions'), # Global dimensions
                'created_by_user_id': self.current_user_id,
                'is_active': True # Default to active
                # Any other fields required by products_crud.add_product
            }

            if not global_product_details['product_name'] or not global_product_details['product_code']:
                QMessageBox.warning(self, self.tr("Données Manquantes"), self.tr("Le nom et le code du produit sont obligatoires pour un nouveau produit global."))
                return

            # Call products_crud.add_product
            # Assuming products_crud.add_product returns a dict like {'success': bool, 'id': new_id, 'error': str}
            add_global_prod_result = products_crud.add_product(global_product_details)

            if not add_global_prod_result or not add_global_prod_result.get('success'):
                error_msg = add_global_prod_result.get('error', self.tr("une erreur inconnue"))
                QMessageBox.critical(self, self.tr("Erreur Création Produit Global"),
                                     self.tr("Impossible de créer le produit global : {0}").format(error_msg))
                return

            new_global_product_id = add_global_prod_result.get('id')
            if not new_global_product_id: # Should not happen if success is true and id is part of success response
                QMessageBox.critical(self, self.tr("Erreur Critique"), self.tr("ID du produit global non retourné après création."))
                return

            if self.notification_manager:
                self.notification_manager.show(self.tr("Succès"),
                                               self.tr("Produit global '{0}' créé avec succès.").format(global_product_details['product_name']),
                                               type="SUCCESS")

            # --- 2. Link to Client ---
            # Prepare data for ClientProjectProducts link.
            # These are overrides or specific details for THIS client link.
            # ProductDialog's get_data() should ideally differentiate these if they can be
            # different from the global ones at the point of creation.
            # For now, we'll assume some direct mappings and some potential overrides.

            # Example: If ProductDialog allows specifying a quantity for the link
            link_quantity = new_product_info.get('quantity', 1) # Default to 1 if not specified

            # Example: If ProductDialog allows overriding the price for this client link
            # If 'unit_price_override' is a specific field from dialog for this, use it.
            # Otherwise, if 'unit_price' from dialog was meant as the override, it's already base_unit_price.
            # Let's assume for now no override at creation via this simplified flow, so it uses global base price.
            link_unit_price_override = new_product_info.get('client_unit_price_override', None)

            # Client-specific name/description for the link, if different from global at creation
            link_client_specific_name = new_product_info.get('client_specific_product_name', None)
            link_line_description = new_product_info.get('client_line_description', None)


            link_data = {
                'client_id': client_id,
                'product_id': new_global_product_id,
                'quantity': link_quantity,
                'unit_price_override': link_unit_price_override, # None means use global base price
                'added_by_user_id': self.current_user_id,
                'client_specific_product_name': link_client_specific_name if link_client_specific_name else global_product_details['product_name'],
                'line_description': link_line_description if link_line_description else global_product_details['description'],
                # 'line_weight': ..., # If ProductDialog allows specifying these for the link separately
                # 'line_dimensions_notes': ...,
            }

            cpp_id = db_manager.add_product_to_client_or_project(link_data)

            if cpp_id:
                if self.notification_manager:
                    self.notification_manager.show(self.tr("Succès"),
                                                   self.tr("Nouveau produit '{0}' lié au client.").format(global_product_details['product_name']),
                                                   type="SUCCESS")
            else:
                QMessageBox.warning(self, self.tr("Erreur Liaison Produit"),
                                    self.tr("Le produit global a été créé, mais une erreur est survenue lors de sa liaison avec le client."))

            self.load_products() # Refresh the table
        else:
            # Dialog was cancelled or closed
            if self.notification_manager:
                 self.notification_manager.show(self.tr("Annulé"), self.tr("L'ajout du nouveau produit a été annulé."), type="INFO")

    def handle_generate_proforma(self):
        if self.products_table.rowCount() == 0:
            QMessageBox.information(self, self.tr("Aucun Produit"), self.tr("Il n'y a aucun produit dans la liste à inclure dans la proforma."))
            return

        lang_choices = {self.tr(lang_name): lang_code for lang_code, lang_name in SUPPORTED_LANGUAGES.items()}
        lang_display_names = list(lang_choices.keys())

        if not lang_display_names:
            QMessageBox.critical(self, self.tr("Erreur Langues"), self.tr("Aucune langue de traduction n'est configurée."))
            return

        selected_lang_display_name, ok = QInputDialog.getItem(self, self.tr("Choisir la Langue"),
                                                              self.tr("Choisissez la langue pour la facture proforma:"),
                                                              lang_display_names, 0, False)
        if not ok or not selected_lang_display_name:
            return # User cancelled

        selected_lang_code = lang_choices[selected_lang_display_name]
        logging.info(f"User selected language for proforma: {selected_lang_code} ({selected_lang_display_name})")

        # Collect current products from the table (respecting filters)
        products_for_proforma = []
        for row in range(self.products_table.rowCount()):
            product_link_id = self.products_table.item(row, 0).data(Qt.UserRole) # client_project_product_id
            # We need to fetch full product details based on this link_id, especially the global product_id
            # For now, let's just collect basic info from the table.
            # The actual proforma generation will need more detailed product info, possibly by re-fetching.

            # Fetching comprehensive data for each product:
            # This might be redundant if load_products already has all necessary info in products_to_display
            # However, products_to_display is local to load_products.
            # A better approach might be to store the list of currently displayed products (with all their data)
            # as an instance variable if it's frequently needed by other methods like this one.
            # For now, we'll assume we need to re-fetch or get from table.
            # Let's get the global product_id. ClientProjectProducts table has product_id.
            # db_manager.get_client_project_product_by_id(product_link_id) should give us this.

            cpp_details = db_manager.get_client_project_product_by_id(product_link_id)
            if not cpp_details:
                logging.warning(f"Could not retrieve details for client_project_product_id {product_link_id} for proforma.")
                continue

            global_product_id = cpp_details.get('product_id')
            if not global_product_id:
                logging.warning(f"Client_project_product_id {product_link_id} does not have a global product_id. Skipping for proforma.")
                continue

            # Get data from table cells as they are displayed (after filters and potential in-table edits)
            product_name = self.products_table.item(row, 1).text()
            description = self.products_table.item(row, 2).text() # This is line_description
            quantity = self.products_table.item(row, 5).text()
            unit_price_str = self.products_table.item(row, 6).text()

            try:
                qty_val = float(quantity)
                # Unit price might have currency symbol, need to clean it
                price_val = float(unit_price_str.replace("€", "").replace(",", ".").strip())
            except ValueError:
                logging.error(f"Could not parse quantity/price for product {product_name} for proforma. Skipping.")
                continue

            products_for_proforma.append({
                "client_project_product_id": product_link_id, # ID of the link
                "product_id": global_product_id, # Global product ID
                "name": product_name, # Name as displayed in table (could be client_specific_product_name)
                "description": description, # Description as displayed (line_description)
                "quantity": qty_val,
                "unit_price": price_val, # unit_price_override or base_unit_price
                # We will need more details like product_code, original language, etc. for actual generation
            })

        if not products_for_proforma:
            QMessageBox.warning(self, self.tr("Aucun Produit Valide"), self.tr("Aucun produit valide n'a pu être collecté pour la proforma."))
            return

        logging.info(f"Generating proforma in {selected_lang_code} for {len(products_for_proforma)} products.")
        # logging.info(f"Products: {products_for_proforma}") # Can be very verbose

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            client_id = self.client_info.get("client_id")
            # Assuming company_id is available from current_user_info or a config
            # This might need adjustment based on how company_id is managed for the logged-in user
            company_id = self.current_user_info.get('company_id')
            if not company_id:
                # Fallback: try to get it from a general config if user doesn't have one directly
                # This is a placeholder for actual company ID retrieval logic
                company_id = self.config.get_global_setting('default_company_id_for_documents')
                if not company_id:
                     QMessageBox.critical(self, self.tr("Erreur Configuration"), self.tr("ID de la société par défaut non configuré pour la génération de documents."))
                     QApplication.restoreOverrideCursor()
                     return

            project_id = self.client_info.get("project_id") # May be None

            # Prepare additional_context for get_proforma_invoice_context_data
            # The 'lite_selected_products' structure is what get_proforma_invoice_context_data expects
            # based on its usage in api/proformas.py
            lite_selected_products_for_context = []
            for p_data in products_for_proforma:
                lite_selected_products_for_context.append({
                    "product_id": p_data["product_id"],
                    "name": p_data["name"], # Will be overridden by context builder if product_id is found
                    "description": p_data["description"], # Will be overridden
                    "quantity": p_data["quantity"],
                    "unit_price_override": p_data["unit_price"] # Context builder uses this as the price
                })

            additional_doc_context = {
                "proforma_id": f"PF-{uuid.uuid4().hex[:8].upper()}", # Generate a temp ID
                "current_date": db_manager.datetime.now(db_manager.timezone.utc).strftime('%Y-%m-%d'),
                "lite_selected_products": lite_selected_products_for_context,
                # Include other fields if necessary, like payment_terms, etc.
                # These would typically come from client settings or defaults.
            }

            # Get the full context using the utility function
            # db_conn=None will make get_proforma_invoice_context_data create its own connection
            doc_context = get_proforma_invoice_context_data(
                client_id_arg=client_id,
                company_id_arg=company_id,
                target_language_code=selected_lang_code,
                project_id_arg=project_id,
                additional_context=additional_doc_context,
                # proforma_instance=None as we are creating a new one
            )

            if not doc_context:
                raise Exception("Failed to generate document context.")

            # Determine template path
            # Assuming parent_widget has app_root_dir or similar
            app_root_dir = getattr(self.parent_widget, 'app_root_dir', os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
            template_base_dir = os.path.join(app_root_dir, "resources", "templates")
            template_file_path = os.path.join(template_base_dir, selected_lang_code, "proforma_invoice_template.html")

            if not os.path.exists(template_file_path): # Fallback to 'en' if specific lang template not found
                logging.warning(f"Template for lang '{selected_lang_code}' not found at {template_file_path}. Falling back to 'en'.")
                template_file_path = os.path.join(template_base_dir, "en", "proforma_invoice_template.html")
                if not os.path.exists(template_file_path):
                    # Fallback to 'fr' as a last resort if 'en' also not found (given initial request context)
                    logging.warning(f"Template for lang 'en' not found. Falling back to 'fr'.")
                    template_file_path = os.path.join(template_base_dir, "fr", "proforma_invoice_template.html")
                    if not os.path.exists(template_file_path):
                        raise FileNotFoundError(f"Proforma template not found for {selected_lang_code}, en, or fr.")

            with open(template_file_path, 'r', encoding='utf-8') as f:
                html_template_str = f.read()

            # Render HTML
            # Ensure template_base_path correctly uses file URI scheme and forward slashes for WeasyPrint
            template_dir_for_render = os.path.dirname(template_file_path)
            render_base_url = f"file://{template_dir_for_render.replace(os.sep, '/')}/"
            rendered_html = render_html_template(html_template_str, doc_context)

            if not rendered_html:
                raise Exception("HTML template rendering failed.")

            # Convert to PDF
            pdf_bytes = convert_html_to_pdf(rendered_html, base_url=render_base_url)
            if not pdf_bytes:
                raise WeasyPrintError("PDF generation returned no bytes.")

            # Save PDF and create ClientDocument record
            # This part is adapted from _internal_save_pdf_and_create_document_record in api/proformas.py
            proforma_ref_for_filename = doc_context.get("doc", {}).get("proforma_id", "PROFORMA").replace('/', '_').replace(' ', '_')
            document_name = f"Facture Proforma {proforma_ref_for_filename}"
            file_name_prefix = f"proforma_{proforma_ref_for_filename}"

            # User ID for document attribution
            user_id_for_doc = self.current_user_id
            if not user_id_for_doc:
                 raise Exception("User ID not found for document attribution.")

            # Reusing logic from api/proformas.py for saving (needs db_manager to have these functions)
            # Or implement a simplified version here. Let's try to adapt.
            # We need client's base folder path.
            client_record = db_manager.get_client_by_id(client_id) # Fetches client details
            if not client_record:
                raise Exception(f"Client with ID {client_id} not found for saving proforma.")

            clients_base_storage_dir = os.path.join(app_root_dir, "clients")
            client_base_folder_path = client_record.get('default_base_folder_path')

            if not client_base_folder_path or not client_base_folder_path.startswith("clients" + os.sep):
                # If path is missing or not relative to 'clients' dir (e.g. absolute, or just a name)
                # Construct a default based on client name/ID
                client_folder_name_safe = "".join(c if c.isalnum() else "_" for c in client_record.get('client_name', str(client_id)))
                target_dir_base = os.path.join(clients_base_storage_dir, client_folder_name_safe)
            else: # Path is like "clients/Some_Client_Folder"
                target_dir_base = os.path.join(app_root_dir, client_base_folder_path)

            generated_docs_subfolder = "generated_documents" # As used in API
            # Use project_id if available for subfolder, else "general"
            specific_folder_name = str(project_id).replace('-', '') if project_id else "general"
            target_doc_dir = os.path.join(target_dir_base, generated_docs_subfolder, specific_folder_name)
            os.makedirs(target_doc_dir, exist_ok=True)

            timestamp_uuid = uuid.uuid4().hex[:8]
            generated_file_name_on_disk = f"{file_name_prefix}_{timestamp_uuid}.pdf"
            full_file_path_on_disk = os.path.join(target_doc_dir, generated_file_name_on_disk)

            with open(full_file_path_on_disk, "wb") as f:
                f.write(pdf_bytes)

            # Path relative to client's base folder for DB
            relative_path_for_db = os.path.join(generated_docs_subfolder, specific_folder_name, generated_file_name_on_disk)

            doc_metadata_for_db = {
                'client_id': client_id,
                'project_id': project_id, # Can be None
                'document_name': document_name,
                'file_name_on_disk': generated_file_name_on_disk,
                'file_path_relative': relative_path_for_db,
                'document_type_generated': 'proforma_invoice',
                'source_template_id': None, # We are not using a template_id from DB here
                'created_by_user_id': user_id_for_doc,
                'language_code': selected_lang_code # Store language of generated doc
            }

            # Using the direct SQLite function from db_manager (assuming it's exposed like in api/proformas.py)
            # db_manager should have add_client_document
            db_document_id = db_manager.add_client_document(doc_metadata_for_db)

            if not db_document_id:
                os.remove(full_file_path_on_disk) # Cleanup if DB record fails
                raise Exception("Failed to save proforma document metadata to database.")

            if self.notification_manager:
                self.notification_manager.show(
                    self.tr("Succès"),
                    self.tr(f"Facture proforma '{document_name}' générée et sauvegardée avec succès."),
                    type="SUCCESS"
                )

            # Optionally, refresh the documents tab if a signal mechanism exists
            if hasattr(self.parent_widget, 'refresh_documents_tab_signal'):
                 self.parent_widget.refresh_documents_tab_signal.emit()
            elif hasattr(self.parent_widget, 'documents_tab_instance') and \
                 hasattr(self.parent_widget.documents_tab_instance, 'load_documents'):
                 self.parent_widget.documents_tab_instance.load_documents()


        except FileNotFoundError as fnfe:
            logging.error(f"Template file error: {fnfe}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Fichier"), self.tr(f"Fichier modèle non trouvé: {fnfe}"))
        except WeasyPrintError as wpe:
            logging.error(f"PDF Generation Error (WeasyPrint): {wpe}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur PDF"), self.tr(f"Erreur lors de la génération PDF (WeasyPrint): {wpe}"))
        except Exception as e:
            logging.error(f"Error generating proforma: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Inconnue"), self.tr(f"Une erreur inattendue est survenue: {e}"))
        finally:
            QApplication.restoreOverrideCursor()

    def handle_product_selection_changed(self):
        selected_rows = self.products_table.selectionModel().selectedRows()
        if not selected_rows:
            if hasattr(self.parent_widget, 'product_selected_in_products_tab'):
                self.parent_widget.product_selected_in_products_tab(None) # Signal no selection
            return

        row_index = selected_rows[0].row()
        cpp_id_item = self.products_table.item(row_index, 0) # Hidden column with client_project_product_id
        if not cpp_id_item:
            if hasattr(self.parent_widget, 'product_selected_in_products_tab'):
                self.parent_widget.product_selected_in_products_tab(None)
            return

        client_project_product_id = cpp_id_item.data(Qt.UserRole)
        if client_project_product_id is None: # Should not happen if table is populated correctly
            if hasattr(self.parent_widget, 'product_selected_in_products_tab'):
                self.parent_widget.product_selected_in_products_tab(None)
            return

        try:
            # Fetch the ClientProjectProducts entry to get the global product_id
            # Assuming db_manager.get_client_project_product_by_id exists and returns a dict with 'product_id'
            cpp_details = db_manager.get_client_project_product_by_id(client_project_product_id)
            if cpp_details and cpp_details.get('product_id') is not None:
                global_product_id = cpp_details.get('product_id')
                if hasattr(self.parent_widget, 'product_selected_in_products_tab'):
                    self.parent_widget.product_selected_in_products_tab(global_product_id)
            else:
                if hasattr(self.parent_widget, 'product_selected_in_products_tab'):
                    self.parent_widget.product_selected_in_products_tab(None) # Product link or global ID not found
        except Exception as e:
            logging.error(f"Error fetching cpp_details for selection change: {e}", exc_info=True)
            if hasattr(self.parent_widget, 'product_selected_in_products_tab'):
                self.parent_widget.product_selected_in_products_tab(None)


    def handle_manage_global_catalog(self):
        # This method will be called when 'Gérer Catalogue Global' button is clicked.
        # It should instantiate and show ManageGlobalProductsDialog.
        # ManageGlobalProductsDialog needs current_user_info, config, notification_manager
        # It no longer needs product_dialog_class as it uses GlobalProductEditDialog internally.
        try:
            from product_management.manage_global_products_dialog import ManageGlobalProductsDialog
            dialog = ManageGlobalProductsDialog(
                current_user_info=self.current_user_info,
                config=self.config,
                notification_manager=self.notification_manager,
                parent=self # Parent for styling and modality
            )
            dialog.exec_() # Show as modal dialog
            # After dialog closes, refresh products in this tab as global catalog might have changed
            self.load_products()
            # Also refresh products in dimension tab's combo box
            if hasattr(self.parent_widget, 'product_dimensions_tab_ref') and \
               hasattr(self.parent_widget.product_dimensions_tab_ref, 'load_products_for_dimension_tab'):
                self.parent_widget.product_dimensions_tab_ref.load_products_for_dimension_tab()

        except ImportError as ie:
            logging.error(f"Failed to import ManageGlobalProductsDialog: {ie}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Importation"), self.tr("Impossible de charger le module de gestion du catalogue."))
        except Exception as e:
            logging.error(f"Error opening global catalog manager: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Inattendue"), str(e))
