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

                    # Utiliser les champs de ligne spécifiques s'ils existent, sinon les champs globaux du produit
                    line_description = prod.get('line_description', prod.get('product_description', ''))
                    line_weight_val = prod.get('line_weight', prod.get('global_product_weight', ''))
                    line_dimensions_notes_val = prod.get('line_dimensions_notes', prod.get('global_product_dimensions', ''))


                    self.products_table.setItem(row, 1, QTableWidgetItem(prod.get('product_name')))
                    # self.products_table.setItem(row, 2, QTableWidgetItem(prod.get('description'))) # Old
                    # self.products_table.setItem(row, 3, QTableWidgetItem(str(prod.get('weight', '')))) # Old
                    # self.products_table.setItem(row, 4, QTableWidgetItem(prod.get('dimensions_notes'))) # Old

                    self.products_table.setItem(row, 2, QTableWidgetItem(line_description))
                    self.products_table.setItem(row, 3, QTableWidgetItem(str(line_weight_val)))
                    self.products_table.setItem(row, 4, QTableWidgetItem(line_dimensions_notes_val))


                    qty = float(prod.get('quantity', 0))
                    price_override = prod.get('unit_price_override', prod.get('price_override')) # Check both keys for safety
                    unit_price = price_override if price_override is not None else float(prod.get('base_unit_price', 0)) # Use base_unit_price as fallback
                    total_price = qty * unit_price

                    name_item = QTableWidgetItem(prod.get('product_name'))
                    name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable) # Non-editable
                    self.products_table.setItem(row, 1, name_item)

                    # desc_item = QTableWidgetItem(prod.get('description')) # Old
                    desc_item = QTableWidgetItem(line_description) # Description spécifique à la ligne
                    desc_item.setFlags(desc_item.flags() | Qt.ItemIsEditable) # Editable
                    self.products_table.setItem(row, 2, desc_item)

                    # weight_item = QTableWidgetItem(str(prod.get('weight', ''))) # Old
                    weight_item = QTableWidgetItem(str(line_weight_val))
                    weight_item.setFlags(weight_item.flags() | Qt.ItemIsEditable) # Editable
                    self.products_table.setItem(row, 3, weight_item)

                    # dims_item = QTableWidgetItem(prod.get('dimensions_notes')) # Old
                    dims_item = QTableWidgetItem(line_dimensions_notes_val)
                    dims_item.setFlags(dims_item.flags() | Qt.ItemIsEditable) # Editable
                    self.products_table.setItem(row, 4, dims_item)

                    qty = float(prod.get('quantity', 0))
                    # price_override = prod.get('price_override') # Old
                    # unit_price = price_override if price_override is not None else float(prod.get('unit_price', 0)) # Old
                    price_override = prod.get('unit_price_override', prod.get('price_override'))
                    unit_price = price_override if price_override is not None else float(prod.get('base_unit_price', 0))
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
                update_data['line_description'] = new_value_str
            elif col == 3: # Poids (Ligne)
                try:
                    update_data['line_weight'] = float(new_value_str.replace(",", ".")) if new_value_str.strip() else None
                except ValueError:
                    QMessageBox.warning(self, self.tr("Donnée Invalide"), self.tr("Le poids doit être un nombre."))
                    self.load_products() # Revert
                    self.products_table.blockSignals(False)
                    return
            elif col == 4: # Dimensions (Ligne)
                update_data['line_dimensions_notes'] = new_value_str
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
                    # Key in DB is unit_price_override
                    update_data['unit_price_override'] = float(new_value_str.replace("€", "").replace(",", ".").strip())
                    if update_data['unit_price_override'] < 0: raise ValueError("Price cannot be negative")
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
                # Utiliser la fonction CRUD mise à jour
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


