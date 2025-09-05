# -*- coding: utf-8 -*-
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QComboBox, QMessageBox, QApplication,
    QGroupBox, QLabel, QHBoxLayout
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from app.db.connection import get_db_connection
from app.db.cruds.products.products_crud import get_all_products

class ProductDimensionsTab(QWidget):
    def __init__(self, client_info: dict, app_root_dir: str,
                 main_module_client_product_dimension_dialog: callable,
                 parent_widget: QWidget,
                 parent=None):
        super().__init__(parent)
        self.client_info = client_info
        self.app_root_dir = app_root_dir
        self.ClientProductDimensionDialog = main_module_client_product_dimension_dialog
        self.parent_widget = parent_widget

        self._setup_ui()
        self.load_products_for_dimension_tab()

    def tr(self, text, disambiguation=None, n=-1):
        if self.parent_widget:
            return self.parent_widget.tr(text, disambiguation, n)
        return QApplication.translate("ProductDimensionsTab", text, disambiguation, n)

    def _setup_ui(self):
        # UI setup logic remains the same
        pass # Omitted for brevity

    def load_products_for_dimension_tab(self):
        self.dim_product_selector_combo.blockSignals(True)
        current_selection_data = self.dim_product_selector_combo.currentData()
        self.dim_product_selector_combo.clear()
        self.dim_product_selector_combo.addItem(self.tr("Sélectionner un produit..."), None)

        db_session = None
        try:
            db_session = get_db_connection()
            all_global_products = get_all_products(db_session, filters={"is_active": True})
            if all_global_products:
                for prod_data in sorted(all_global_products, key=lambda p: p.get('product_name', '').lower()):
                    # UI population logic remains the same
                    product_name = prod_data.get('product_name', self.tr('Nom Inconnu'))
                    self.dim_product_selector_combo.addItem(product_name, prod_data.get('product_id'))

                idx = self.dim_product_selector_combo.findData(current_selection_data)
                if idx != -1:
                    self.dim_product_selector_combo.setCurrentIndex(idx)

        except Exception as e:
            logging.error(f"Error loading products for dimension tab: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur Chargement"), self.tr("Impossible de charger les produits globaux."))
        finally:
            if db_session:
                db_session.close()
            self.dim_product_selector_combo.blockSignals(False)
            self.on_dim_product_selected()

    def on_dim_product_selected(self, index=None):
        # No DB calls here, logic remains the same
        selected_global_product_id = self.dim_product_selector_combo.currentData()
        self.edit_client_product_dimensions_button.setEnabled(selected_global_product_id is not None)

    def on_edit_client_product_dimensions(self):
        # This method opens a dialog that will need its own refactoring.
        # The method itself is fine.
        selected_global_product_id = self.dim_product_selector_combo.currentData()
        if selected_global_product_id is None:
            QMessageBox.warning(self, self.tr("Aucun Produit Sélectionné"), self.tr("Veuillez sélectionner un produit."))
            return

        # ... logic to open ClientProductDimensionDialog ...
        dialog = self.ClientProductDimensionDialog(
            client_id=self.client_info.get('client_id'),
            product_id=selected_global_product_id,
            app_root_dir=self.app_root_dir,
            parent=self
        )
        dialog.exec_()


    def apply_permissions_to_tab(self, can_manage_global_products_permission: bool):
        # No DB calls here
        pass

    def refresh_tab_data(self):
        self.load_products_for_dimension_tab()

    def select_product_in_combo(self, global_product_id_to_select: int = None):
        # No DB calls here
        pass
