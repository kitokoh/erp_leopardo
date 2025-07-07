# -*- coding: utf-8 -*-
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QComboBox, QMessageBox, QApplication,
    QGroupBox, QLabel, QHBoxLayout # Added missing imports
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

import db as db_manager
# ClientProductDimensionDialog will be passed from the parent (ClientMainWidget)

class ProductDimensionsTab(QWidget):
    def __init__(self, client_info: dict, app_root_dir: str,
                 main_module_client_product_dimension_dialog: callable,
                 parent_widget: QWidget, # To access tr() and potentially other parent methods/attributes
                 parent=None):
        super().__init__(parent)
        self.client_info = client_info
        self.app_root_dir = app_root_dir
        self.ClientProductDimensionDialog = main_module_client_product_dimension_dialog
        self.parent_widget = parent_widget # For tr() and other interactions if needed

        self._setup_ui()
        self.load_products_for_dimension_tab() # Initial population

    def tr(self, text, disambiguation=None, n=-1):
        """Helper to access the parent's tr method for translations."""
        if self.parent_widget:
            return self.parent_widget.tr(text, disambiguation, n)
        return QApplication.translate("ProductDimensionsTab", text, disambiguation, n)

    def _setup_ui(self):
        logging.info("ProductDimensionsTab._setup_ui: Starting setup...")
        prod_dims_layout = QVBoxLayout(self)
        prod_dims_layout.setSpacing(10)
        prod_dims_layout.setAlignment(Qt.AlignTop) # Align content to the top

        # Product Selector Section
        selector_group = QGroupBox(self.tr("Sélection du Produit Global"))
        selector_group_layout = QVBoxLayout(selector_group)

        selector_hbox = QHBoxLayout()
        selector_label = QLabel(self.tr("Produit Global:"))
        selector_label.setStyleSheet("font-weight: bold;")
        selector_hbox.addWidget(selector_label)

        self.dim_product_selector_combo = QComboBox()
        self.dim_product_selector_combo.addItem(self.tr("Sélectionner un produit..."), None)
        self.dim_product_selector_combo.setMinimumWidth(300)
        self.dim_product_selector_combo.setStyleSheet("QComboBox { padding: 4px; }")
        selector_hbox.addWidget(self.dim_product_selector_combo, 1) # Allow combo to stretch
        selector_group_layout.addLayout(selector_hbox)
        prod_dims_layout.addWidget(selector_group)

        # Action Button Section
        action_group = QGroupBox(self.tr("Actions"))
        action_group_layout = QVBoxLayout(action_group)

        self.edit_client_product_dimensions_button = QPushButton(self.tr("Gérer les Dimensions de ce Produit"))
        self.edit_client_product_dimensions_button.setIcon(QIcon(":/icons/edit-3.svg")) # Updated icon
        self.edit_client_product_dimensions_button.setObjectName("primaryButton") # Style as primary action
        self.edit_client_product_dimensions_button.setToolTip(self.tr("Ouvrir le dialogue pour ajouter ou modifier les dimensions spécifiques pour le produit global sélectionné."))
        self.edit_client_product_dimensions_button.setEnabled(False)
        action_group_layout.addWidget(self.edit_client_product_dimensions_button)
        prod_dims_layout.addWidget(action_group)

        prod_dims_layout.addStretch(1) # Pushes content to the top

        # Connections
        self.dim_product_selector_combo.currentIndexChanged.connect(self.on_dim_product_selected)
        self.edit_client_product_dimensions_button.clicked.connect(self.on_edit_client_product_dimensions)

    def load_products_for_dimension_tab(self):
        """Populates the product selector combo box."""
        self.dim_product_selector_combo.blockSignals(True)
        current_selection_data = self.dim_product_selector_combo.currentData() # Store current data (product_id)
        self.dim_product_selector_combo.clear()
        self.dim_product_selector_combo.addItem(self.tr("Sélectionner un produit..."), None)

        try:
            # Fetch all products, assuming this returns a list of dicts with 'product_id', 'product_name', 'product_code', 'language_code'
            all_global_products = db_manager.get_all_products(filters={"is_active": True}) # Fetch only active products
            if all_global_products:
                for prod_data in sorted(all_global_products, key=lambda p: p.get('product_name', '').lower()): # Sort alphabetically
                    product_name = prod_data.get('product_name', self.tr('Nom Inconnu'))
                    global_product_id = prod_data.get('product_id')
                    product_code = prod_data.get('product_code', '')
                    lang_code = prod_data.get('language_code', '')

                    display_text = f"{product_name}"
                    if product_code:
                        display_text += self.tr(" (Code: {0})").format(product_code)

                    if lang_code:
                        display_text += f" [{lang_code.upper()}]"
                    # display_text += f" - ID: {global_product_id}" # Keep ID for debugging if needed, but can be long for UI

                    self.dim_product_selector_combo.addItem(display_text, global_product_id) # Store global_product_id

                # Try to restore previous selection if still valid
                idx = self.dim_product_selector_combo.findData(current_selection_data)
                if idx != -1:
                    self.dim_product_selector_combo.setCurrentIndex(idx)
                elif self.dim_product_selector_combo.count() > 1: # If items were added, and previous not found
                     self.dim_product_selector_combo.setCurrentIndex(0) # Default to placeholder "Sélectionner..."
                # If count is 1 (only placeholder), it's already at index 0.

        except Exception as e:
            logging.error(f"Error loading products for dimension tab: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur Chargement"), self.tr("Impossible de charger la liste des produits globaux."))

        self.dim_product_selector_combo.blockSignals(False)
        self.on_dim_product_selected() # Update button state based on current selection (or lack thereof)

    def on_dim_product_selected(self, index=None): # index arg is optional, can be called directly
        """Handles selection change in the product selector."""
        selected_global_product_id = self.dim_product_selector_combo.currentData()

        can_manage_product_data = True # Default or more specific permission check
        # Example: Use a permission like P_MANAGE_GLOBAL_PRODUCTS if it exists
        # For now, using P_LINK_PRODUCTS_TO_CLIENT as a proxy, assuming it implies some level of product data management.
        if hasattr(self.parent_widget, 'current_user_info'):
            from auth.permissions import has_permission, P_MANAGE_GLOBAL_PRODUCTS
            role_name = self.parent_widget.current_user_info.get('role_name')
            if role_name:
                can_manage_product_data = has_permission(role_name, P_MANAGE_GLOBAL_PRODUCTS) # Changed permission


        self.edit_client_product_dimensions_button.setEnabled(selected_global_product_id is not None and can_manage_product_data)


    def on_edit_client_product_dimensions(self):
        selected_global_product_id = self.dim_product_selector_combo.currentData()
        if selected_global_product_id is None:
            QMessageBox.warning(self, self.tr("Aucun Produit Sélectionné"), self.tr("Veuillez sélectionner un produit."))
            return

        client_id = self.client_info.get('client_id') # This tab is for global product dims, client_id might not be strictly needed for the dialog's core logic but good for context
        if not client_id: # Or handle differently if truly global and not client-contextual for the dialog
            # For ClientProductDimensionDialog, client_id IS required by its signature.
             QMessageBox.critical(self, self.tr("Erreur Client"), self.tr("L'ID du client n'est pas disponible pour le dialogue de dimensions."))
             return


        if not self.ClientProductDimensionDialog:
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Dialogue de dimensions produit non chargé."))
            return

        dialog = self.ClientProductDimensionDialog(
            client_id=client_id,
            product_id=selected_global_product_id, # This is the global product_id
            app_root_dir=self.app_root_dir,
            parent=self # Parent for the dialog is this tab
        )
        if dialog.exec_() == QMessageBox.Accepted: # Assuming QDialog.Accepted or similar
            # Potentially refresh something if needed, e.g. if this dialog could change product names displayed elsewhere
            # For now, no specific refresh action after editing global dimensions from this tab.
            # However, if product list in ProductsTab needs refreshing (e.g. if names changed):
            if hasattr(self.parent_widget, 'products_tab_widget_ref'):
                 if hasattr(self.parent_widget.products_tab_widget_ref, 'refresh_tab_data'):
                     self.parent_widget.products_tab_widget_ref.refresh_tab_data()
            if hasattr(self.parent_widget, 'notification_manager'):
                 self.parent_widget.notification_manager.show(self.tr("Succès"), self.tr("Dimensions produit mises à jour."), type='SUCCESS')

    def apply_permissions_to_tab(self, can_manage_global_products_permission: bool): # Parameter name changed for clarity
        """Applies permissions to UI elements within this tab."""
        # The main button's enabled state is also controlled by product selection in on_dim_product_selected
        # This ensures the permission is the overarching factor.
        current_product_selected = self.dim_product_selector_combo.currentData() is not None

        # Use the specific permission for managing global products
        self.edit_client_product_dimensions_button.setEnabled(can_manage_global_products_permission and current_product_selected)
        self.dim_product_selector_combo.setEnabled(can_manage_global_products_permission) # Or view permission if separate

    def refresh_tab_data(self):
        """Public method to refresh data, callable from parent."""
        self.load_products_for_dimension_tab()

    def select_product_in_combo(self, global_product_id_to_select: int = None):
        """
        Selects a product in the dim_product_selector_combo based on its global_product_id.
        If global_product_id_to_select is None, it selects the placeholder item.
        """
        self.dim_product_selector_combo.blockSignals(True)
        if global_product_id_to_select is None:
            self.dim_product_selector_combo.setCurrentIndex(0) # Index 0 is "Sélectionner un produit..."
        else:
            found_index = self.dim_product_selector_combo.findData(global_product_id_to_select)
            if found_index != -1:
                self.dim_product_selector_combo.setCurrentIndex(found_index)
            else:
                logging.warning(f"ProductDimensionsTab: Product with global_id {global_product_id_to_select} not found in selector combo.")
                self.dim_product_selector_combo.setCurrentIndex(0) # Fallback to placeholder

        self.dim_product_selector_combo.blockSignals(False)
        # Manually trigger the handler for the selection change, as signals were blocked
        self.on_dim_product_selected(self.dim_product_selector_combo.currentIndex())

