# -*- coding: utf-8 -*-
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QComboBox, QMessageBox, QApplication
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

        self.dim_product_selector_combo = QComboBox()
        self.dim_product_selector_combo.addItem(self.tr("Sélectionner un produit..."), None)
        prod_dims_layout.addWidget(self.dim_product_selector_combo)

        self.edit_client_product_dimensions_button = QPushButton(self.tr("Modifier Dimensions Produit (Global)"))
        self.edit_client_product_dimensions_button.setIcon(QIcon.fromTheme("document-edit", QIcon(":/icons/pencil.svg")))
        self.edit_client_product_dimensions_button.setEnabled(False) # Enabled when a product is selected
        prod_dims_layout.addWidget(self.edit_client_product_dimensions_button)

        prod_dims_layout.addStretch()

        # Connections
        self.dim_product_selector_combo.currentIndexChanged.connect(self.on_dim_product_selected)
        self.edit_client_product_dimensions_button.clicked.connect(self.on_edit_client_product_dimensions)

    def load_products_for_dimension_tab(self):
        """Populates the product selector combo box."""
        self.dim_product_selector_combo.blockSignals(True)
        current_selection = self.dim_product_selector_combo.currentData()
        self.dim_product_selector_combo.clear()
        self.dim_product_selector_combo.addItem(self.tr("Sélectionner un produit..."), None)

        try:
            all_global_products = db_manager.get_all_products(filters=None)
            if all_global_products:
                for prod_data in all_global_products:
                    product_name = prod_data.get('product_name', 'N/A')
                    global_product_id = prod_data.get('product_id')
                    lang_code = prod_data.get('language_code', '')
                    display_text = f"{product_name} ({lang_code}) - ID: {global_product_id}"
                    self.dim_product_selector_combo.addItem(display_text, global_product_id)

                # Try to restore previous selection if still valid
                idx = self.dim_product_selector_combo.findData(current_selection)
                if idx != -1:
                    self.dim_product_selector_combo.setCurrentIndex(idx)
                elif self.dim_product_selector_combo.count() > 0:
                     self.dim_product_selector_combo.setCurrentIndex(0) # Default to placeholder

        except Exception as e:
            logging.error(f"Error loading products for dimension tab: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur Chargement"), self.tr("Impossible de charger les produits."))

        self.dim_product_selector_combo.blockSignals(False)
        self.on_dim_product_selected() # Update button state

    def on_dim_product_selected(self, index=None):
        """Handles selection change in the product selector."""
        selected_global_product_id = self.dim_product_selector_combo.currentData()
        can_link_products = True # Default, or get from parent if more complex permission check needed
        if hasattr(self.parent_widget, 'current_user_info'): # Check if parent has user info for permissions
            from auth.permissions import has_permission, P_LINK_PRODUCTS_TO_CLIENT # Local import for safety
            role_name = self.parent_widget.current_user_info.get('role_name')
            if role_name:
                can_link_products = has_permission(role_name, P_LINK_PRODUCTS_TO_CLIENT)

        self.edit_client_product_dimensions_button.setEnabled(selected_global_product_id is not None and can_link_products)


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

    def apply_permissions_to_tab(self, can_link_products: bool):
        """Applies permissions to UI elements within this tab."""
        # The main button's enabled state is also controlled by product selection in on_dim_product_selected
        # This ensures the permission is the overarching factor.
        current_product_selected = self.dim_product_selector_combo.currentData() is not None
        self.edit_client_product_dimensions_button.setEnabled(can_link_products and current_product_selected)
        self.dim_product_selector_combo.setEnabled(can_link_products) # Disable selector if no permission

    def refresh_tab_data(self):
        """Public method to refresh data, callable from parent."""
        self.load_products_for_dimension_tab()

```
