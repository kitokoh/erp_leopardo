# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit,
    QPushButton, QDialogButtonBox, QDoubleSpinBox, QMessageBox
)
from PyQt5.QtGui import QIcon
# from PyQt5.QtCore import Qt # Qt not directly used, omitting for now

# Anticipated import, will be resolved when ProductDimensionUIDialog is moved
from .product_dimension_ui_dialog import ProductDimensionUIDialog
import db # For db_manager access
import logging # For error logging


class EditProductLineDialog(QDialog):
    def __init__(self, client_project_product_id, app_root_dir, parent=None): # Modified signature
        super().__init__(parent)
        self.client_project_product_id = client_project_product_id
        self.app_root_dir = app_root_dir
        self.product_data = self._load_product_data()

        if not self.product_data:
            QMessageBox.critical(parent, self.tr("Erreur Données Produit"),
                                 self.tr("Impossible de charger les données pour la ligne produit ID: {0}.\nLe dialogue pourrait ne pas fonctionner correctement.").format(self.client_project_product_id))
            self.product_data = {} # Ensure product_data is a dict to prevent errors in setup_ui

        self.setWindowTitle(self.tr("Modifier Ligne de Produit"))
        self.setMinimumSize(450, 300) # Adjusted for new button
        self.setup_ui()

    def _load_product_data(self):
        try:
            # Assuming db.get_client_project_product_by_id is available
            # This might need to be db.db_manager.get_client_project_product_by_id depending on how db_manager is structured
            data = db.get_client_project_product_by_id(self.client_project_product_id)
            if not data:
                logging.error(f"EditProductLineDialog: No data found for client_project_product_id {self.client_project_product_id}")
                return None
            return data
        except AttributeError: # If db.get_client_project_product_by_id doesn't exist, try db.db_manager
            try:
                data = db.db_manager.get_client_project_product_by_id(self.client_project_product_id)
                if not data:
                    logging.error(f"EditProductLineDialog: No data found (via db_manager) for client_project_product_id {self.client_project_product_id}")
                    return None
                return data
            except Exception as e_mgr:
                logging.error(f"EditProductLineDialog: Error loading product data (via db_manager) for ID {self.client_project_product_id}: {e_mgr}", exc_info=True)
                return None
        except Exception as e:
            logging.error(f"EditProductLineDialog: Error loading product data for ID {self.client_project_product_id}: {e}", exc_info=True)
            return None

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout(); form_layout.setSpacing(10)

        # Use self.product_data safely, defaulting if keys are missing or product_data is empty
        self.name_input = QLineEdit(self.product_data.get('client_specific_product_name', self.product_data.get('product_name', '')))
        form_layout.addRow(self.tr("Nom du Produit (Spécifique Client/Ligne):"), self.name_input)

        self.description_input = QTextEdit(self.product_data.get('line_description', self.product_data.get('product_description', '')))
        self.description_input.setFixedHeight(80)
        form_layout.addRow(self.tr("Description (Ligne):"), self.description_input)

        self.weight_input_edit = QDoubleSpinBox()
        self.weight_input_edit.setSuffix(" kg")
        self.weight_input_edit.setRange(0.0, 10000.0)
        self.weight_input_edit.setDecimals(2)
        retrieved_weight = self.product_data.get('line_weight', self.product_data.get('global_product_weight', 0.0))
        self.weight_input_edit.setValue(float(retrieved_weight) if retrieved_weight is not None else 0.0)
        form_layout.addRow(self.tr("Poids (Ligne):"), self.weight_input_edit)

        self.dimensions_input_edit = QLineEdit(self.product_data.get('line_dimensions_notes', self.product_data.get('global_product_dimensions', '')))
        self.dimensions_input_edit.setPlaceholderText(self.tr("LxlxH cm ou notes"))
        form_layout.addRow(self.tr("Dimensions (Ligne):"), self.dimensions_input_edit)

        self.view_detailed_dimensions_button = QPushButton(self.tr("Voir Dimensions Détaillées (Global Produit)"))
        self.view_detailed_dimensions_button.setText("↔️")
        self.view_detailed_dimensions_button.clicked.connect(self.on_view_detailed_dimensions)
        if not self.product_data.get('product_id'):
            self.view_detailed_dimensions_button.setEnabled(False)
        form_layout.addRow(self.view_detailed_dimensions_button)

        self.quantity_input = QDoubleSpinBox()
        self.quantity_input.setRange(0.01, 1000000) # Min quantity could be 0 if allowed
        self.quantity_input.setValue(float(self.product_data.get('quantity', 1.0)))
        form_layout.addRow(self.tr("Quantité:"), self.quantity_input)

        self.unit_price_input = QDoubleSpinBox()
        self.unit_price_input.setRange(0.00, 10000000); self.unit_price_input.setPrefix("€ "); self.unit_price_input.setDecimals(2)
        # Prioritize unit_price_override, then base_unit_price
        unit_price_to_display = self.product_data.get('unit_price_override')
        if unit_price_to_display is None:
            unit_price_to_display = self.product_data.get('base_unit_price', 0.0)
        self.unit_price_input.setValue(float(unit_price_to_display if unit_price_to_display is not None else 0.0))
        form_layout.addRow(self.tr("Prix Unitaire (Ligne):"), self.unit_price_input)

        layout.addLayout(form_layout); layout.addStretch()
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText(self.tr("OK")); button_box.button(QDialogButtonBox.Cancel).setText(self.tr("Annuler"))

        # Connect accepted signal to a method that validates before accepting
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box); self.setLayout(layout)

    def validate_and_accept(self):
        if not self.product_data: # Check if product_data failed to load
             QMessageBox.warning(self, self.tr("Erreur"), self.tr("Les données initiales du produit n'ont pas pu être chargées. Impossible de sauvegarder."))
             return # Do not accept
        # Add any other validation if needed here
        self.accept()


    def on_view_detailed_dimensions(self):
        # Ensure product_data is not empty and contains 'product_id'
        product_id = self.product_data.get('product_id') if self.product_data else None
        if product_id is not None:
            dialog = ProductDimensionUIDialog(product_id, self.app_root_dir, self, read_only=True)
            dialog.exec_()
        else:
            QMessageBox.information(self, self.tr("ID Produit Manquant"), self.tr("Aucun ID de produit global associé à cette ligne."))

    def get_data(self) -> dict:
        if not self.product_data: # If initial load failed or product_data is empty
            return {"error": self.tr("Les données initiales du produit n'ont pas pu être chargées.")}

        # The returned data should be what needs to be updated in ClientProjectProducts table
        return {
            "client_specific_product_name": self.name_input.text().strip(),
            "line_description": self.description_input.toPlainText().strip(),
            "quantity": self.quantity_input.value(),
            "unit_price_override": self.unit_price_input.value(), # This is the line-specific price
            "line_weight": self.weight_input_edit.value(),
            "line_dimensions_notes": self.dimensions_input_edit.text().strip(),
            # "product_id": self.product_data.get('product_id'), # Not directly editable here, but good for reference
            "client_project_product_id": self.client_project_product_id # Key for update
        }
