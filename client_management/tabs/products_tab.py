# -*- coding: utf-8 -*-
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QApplication, QInputDialog
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog

import db as db_manager
from db.cruds import commandes_crud # Import direct pour add_commande_item
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
        products_btn_layout.addStretch() # Add some space before new button if desired

        self.add_new_global_product_btn = QPushButton(self.tr("➕ Nouveau Produit Global"))
        self.add_new_global_product_btn.setToolTip(self.tr("Ajouter un nouveau produit global et le lier à ce client."))
        self.add_new_global_product_btn.clicked.connect(self.handle_add_new_global_product)
        products_btn_layout.addWidget(self.add_new_global_product_btn)

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
                    qty_item = QTableWidgetItem(str(qty))
                    qty_item.setFlags(qty_item.flags() | Qt.ItemIsEditable)
                    self.products_table.setItem(row, 5, qty_item)

                    # Column 6: Prix Unitaire (Ligne / Base) - Editable
                    unit_price_item = QTableWidgetItem(f"{display_unit_price:.2f}")
                    unit_price_item.setFlags(unit_price_item.flags() | Qt.ItemIsEditable)
                    self.products_table.setItem(row, 6, unit_price_item)

                    # Column 7: Prix Total - Non-editable
                    total_price_item = QTableWidgetItem(f"{total_price:.2f} €") # Assuming Euro
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

            # For adding to CommandeItems, we need the global product_id.
            # Let's assume the products_to_add list from dialog.get_data() contains the definitive
            # product_id (either existing or newly created by the logic handling ProductDialog's output).

            if selected_commande_id and selected_commande_id != "NONE":
                for prod_data in products_to_add:
                    global_product_id = prod_data.get('product_id')
                    product_code = prod_data.get('product_code') # Available from get_data()

                    if not global_product_id:
                        # If product_id is None, it implies a new global product.
                        # The logic to create this global product and get its ID should ideally
                        # happen before this point, managed by whatever calls ProductDialog.
                        # For now, if product_id is None, we might try to find it by code,
                        # assuming it was just created. This is a bit fragile.
                        if product_code:
                            created_product = db_manager.get_product_by_code(product_code)
                            if created_product:
                                global_product_id = created_product.get('product_id')
                            else:
                                logging.warning(f"Could not find newly created global product by code {product_code} to add to commande {selected_commande_id}")
                                continue # Skip adding this item to the commande
                        else:
                            logging.warning(f"Product code missing for a new product, cannot add to commande {selected_commande_id}")
                            continue


                    if global_product_id:
                        commande_item_data = {
                            'commande_id': selected_commande_id,
                            'product_id': global_product_id,
                            'description_item': prod_data.get('description', ''),
                            'quantity': prod_data.get('quantity', 1),
                            'unit_price_ht': prod_data.get('unit_price', 0.0), # ProductDialog returns 'unit_price' which we use as HT here
                            'vat_rate': 0.0,  # Default VAT rate, adjust as needed
                            'weight': prod_data.get('weight'),
                            'dimensions_text': prod_data.get('dimensions'),
                            'product_language_code': prod_data.get('language_code', 'fr')
                        }
                        item_added_id = commandes_crud.add_commande_item(commande_item_data)
                        if item_added_id:
                            logging.info(f"Product {global_product_id} also added to commande {selected_commande_id} as item {item_added_id}")
                            if self.notification_manager:
                                self.notification_manager.show(
                                    self.tr("Produit Ajouté à la Commande"),
                                    self.tr("Le produit '{0}' a été ajouté à la commande sélectionnée.").format(prod_data.get('name')),
                                    type='INFO'
                                )
                        else:
                            QMessageBox.warning(self, self.tr("Erreur Commande"),
                                                self.tr("Impossible d'ajouter le produit '{0}' à la commande.").format(prod_data.get('name')))
                    else:
                        logging.warning(f"Global Product ID for '{prod_data.get('name')}' could not be determined. Cannot add to commande.")
                        QMessageBox.warning(self, self.tr("Erreur Produit"),
                                            self.tr("ID du produit global pour '{0}' non trouvé. Ajout à la commande échoué.").format(prod_data.get('name')))


            self.load_products() # Reload products in the tab
            if self.notification_manager:
                self.notification_manager.show(self.tr("Succès"), self.tr("Produit(s) ajouté(s)/lié(s) au client avec succès."), type='SUCCESS')


    def add_product(self): # Rewritten method
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
            if selected_commande_id and selected_commande_id != "NONE":
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
            add_global_prod_result = db_manager.products_crud.add_product(global_product_details)

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

