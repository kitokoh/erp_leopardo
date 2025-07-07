# -*- coding: utf-8 -*-
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit,
    QPushButton, QDialogButtonBox, QMessageBox, QComboBox, QCheckBox,
    QDoubleSpinBox, QLabel
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

# Assuming SUPPORTED_LANGUAGES is accessible, e.g., from a shared utils or config
# For now, define it here or import if available from a central place.
# from client_management.tabs.documents_tab import SUPPORTED_LANGUAGES
# As a fallback:
try:
    from client_management.tabs.documents_tab import SUPPORTED_LANGUAGES
except ImportError:
    logging.warning("Could not import SUPPORTED_LANGUAGES from documents_tab, using fallback.")
    SUPPORTED_LANGUAGES = {"en": "English", "fr": "Français", "es": "Español", "ar": "العربية"}


class GlobalProductEditDialog(QDialog):
    def __init__(self, product_data: dict = None, current_user_info: dict = None, parent=None):
        super().__init__(parent)
        self.product_data = product_data # None for add mode, pre-filled for edit mode
        self.current_user_info = current_user_info

        if self.product_data:
            self.setWindowTitle(self.tr("Modifier Produit Global"))
        else:
            self.setWindowTitle(self.tr("Ajouter Nouveau Produit Global"))

        self.setMinimumWidth(500)
        self._setup_ui()
        if self.product_data:
            self._populate_form()

    def tr(self, text, disambiguation=None, n=-1):
        return QApplication.translate("GlobalProductEditDialog", text, disambiguation, n)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.name_input = QLineEdit()
        name_layout = QHBoxLayout()
        name_layout.addWidget(self.name_input)
        self.suggest_name_translation_button = QPushButton(QIcon.fromTheme("text-x-generic"), self.tr("Suggérer"))
        self.suggest_name_translation_button.setToolTip(self.tr("Suggérer une traduction pour le nom du produit"))
        self.suggest_name_translation_button.clicked.connect(lambda: self._handle_suggest_translation("name"))
        name_layout.addWidget(self.suggest_name_translation_button)
        form_layout.addRow(self.tr("Nom du Produit *:"), name_layout)

        self.code_input = QLineEdit()
        form_layout.addRow(self.tr("Code Produit (SKU) *:"), self.code_input)

        self.description_input = QTextEdit()
        self.description_input.setFixedHeight(80)
        description_layout = QHBoxLayout()
        description_layout.addWidget(self.description_input)
        self.suggest_desc_translation_button = QPushButton(QIcon.fromTheme("text-x-generic"), self.tr("Suggérer"))
        self.suggest_desc_translation_button.setToolTip(self.tr("Suggérer une traduction pour la description"))
        self.suggest_desc_translation_button.clicked.connect(lambda: self._handle_suggest_translation("description"))
        description_layout.addWidget(self.suggest_desc_translation_button)
        form_layout.addRow(self.tr("Description:"), description_layout)

        self.category_input = QLineEdit()
        form_layout.addRow(self.tr("Catégorie:"), self.category_input)

        self.language_combo = QComboBox()
        for lang_code, lang_name in SUPPORTED_LANGUAGES.items():
            self.language_combo.addItem(self.tr(lang_name), lang_code) # Ensure lang_name is translatable
        form_layout.addRow(self.tr("Langue:"), self.language_combo)

        self.base_price_input = QDoubleSpinBox()
        self.base_price_input.setRange(0, 10000000)
        self.base_price_input.setDecimals(2)
        self.base_price_input.setSuffix(" €") # Assuming Euro, make configurable if needed
        form_layout.addRow(self.tr("Prix de Base Unitaire *:"), self.base_price_input)

        self.unit_of_measure_input = QLineEdit()
        form_layout.addRow(self.tr("Unité de Mesure:"), self.unit_of_measure_input)

        self.weight_input = QDoubleSpinBox()
        self.weight_input.setRange(0, 100000)
        self.weight_input.setDecimals(3)
        self.weight_input.setSuffix(" kg")
        form_layout.addRow(self.tr("Poids (Global):"), self.weight_input)

        self.dimensions_input = QLineEdit()
        self.dimensions_input.setPlaceholderText(self.tr("Ex: 100x50x30 cm"))
        form_layout.addRow(self.tr("Dimensions (Global):"), self.dimensions_input)

        self.is_active_checkbox = QCheckBox(self.tr("Produit Actif"))
        self.is_active_checkbox.setChecked(True) # Default to active for new products
        form_layout.addRow(self.is_active_checkbox)

        # Soft delete status (read-only display for existing products)
        if self.product_data and self.product_data.get('is_deleted'):
            self.is_deleted_label = QLabel(self.tr("<b style='color:red;'>Ce produit est marqué comme supprimé.</b>"))
            form_layout.addRow(self.is_deleted_label)


        main_layout.addLayout(form_layout)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        ok_button = button_box.button(QDialogButtonBox.Ok)
        ok_button.setText(self.tr("Sauvegarder"))
        ok_button.setIcon(QIcon(":/icons/save.svg")) # Placeholder, ensure icon exists

        cancel_button = button_box.button(QDialogButtonBox.Cancel)
        cancel_button.setText(self.tr("Annuler"))
        cancel_button.setIcon(QIcon(":/icons/dialog-cancel.svg"))

        button_box.accepted.connect(self.accept_data)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def _populate_form(self):
        if not self.product_data:
            return
        self.name_input.setText(self.product_data.get('product_name', ''))
        self.code_input.setText(self.product_data.get('product_code', ''))
        self.description_input.setPlainText(self.product_data.get('description', ''))
        self.category_input.setText(self.product_data.get('category', ''))

        lang_code = self.product_data.get('language_code', 'fr')
        lang_index = self.language_combo.findData(lang_code)
        if lang_index >= 0:
            self.language_combo.setCurrentIndex(lang_index)

        self.base_price_input.setValue(float(self.product_data.get('base_unit_price', 0.0)))
        self.unit_of_measure_input.setText(self.product_data.get('unit_of_measure', ''))
        self.weight_input.setValue(float(self.product_data.get('weight', 0.0)))
        self.dimensions_input.setText(self.product_data.get('dimensions', ''))
        self.is_active_checkbox.setChecked(bool(self.product_data.get('is_active', True)))

        # If editing a soft-deleted product, 'is_active' might be False.
        # Allow user to re-activate by checking 'is_active_checkbox'.
        # The 'is_deleted' flag itself is not directly editable here; un-deletion would be a separate action
        # or handled by making it active again + clearing deleted_at if that's the business logic.
        # For now, editing an 'is_deleted' product will update its fields, and if 'is_active' is checked,
        # the update_product CRUD should handle setting is_active=True. Soft delete removal is more complex.


    def accept_data(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, self.tr("Champ Requis"), self.tr("Le nom du produit est obligatoire."))
            self.name_input.setFocus()
            return
        if not self.code_input.text().strip():
            QMessageBox.warning(self, self.tr("Champ Requis"), self.tr("Le code produit (SKU) est obligatoire."))
            self.code_input.setFocus()
            return
        if self.base_price_input.value() < 0: # Price can be 0, but not negative
            QMessageBox.warning(self, self.tr("Valeur Invalide"), self.tr("Le prix de base ne peut pas être négatif."))
            self.base_price_input.setFocus()
            return

        self.accept() # Proceed to accept the dialog

    def get_product_data(self) -> dict:
        data = {
            "product_name": self.name_input.text().strip(),
            "product_code": self.code_input.text().strip(),
            "description": self.description_input.toPlainText().strip(),
            "category": self.category_input.text().strip(),
            "language_code": self.language_combo.currentData(),
            "base_unit_price": self.base_price_input.value(),
            "unit_of_measure": self.unit_of_measure_input.text().strip(),
            "weight": self.weight_input.value() if self.weight_input.value() > 0 else None, # Store None if 0
            "dimensions": self.dimensions_input.text().strip() if self.dimensions_input.text().strip() else None,
            "is_active": self.is_active_checkbox.isChecked()
        }
        if self.current_user_info: # Add user ID for tracking
            if self.product_data and self.product_data.get('product_id'): # Editing existing
                data['updated_by_user_id'] = self.current_user_info.get('user_id')
            else: # Adding new
                data['created_by_user_id'] = self.current_user_info.get('user_id')

        # If we are editing a product that was soft-deleted, and the user makes it active,
        # we might want to clear is_deleted and deleted_at.
        # This logic should ideally be in the CRUD update if "making active" implies "un-deleting".
        if self.product_data and self.product_data.get('is_deleted') and data['is_active']:
            data['is_deleted'] = 0 # Explicitly mark as not deleted
            data['deleted_at'] = None # Clear deleted_at timestamp

        return data

if __name__ == '__main__':
    app = QApplication([])

    # Test Add mode
    add_dialog = GlobalProductEditDialog(current_user_info={'user_id': 'test_admin'})
    if add_dialog.exec_() == QDialog.Accepted:
        print("Data from Add Dialog:", add_dialog.get_product_data())

    # Test Edit mode
    sample_data = {
        'product_id': 1, 'product_name': 'Existing Product', 'product_code': 'EP001',
        'description': 'Some description', 'category': 'Test Cat', 'language_code': 'en',
        'base_unit_price': 19.99, 'unit_of_measure': 'piece', 'weight': 0.5,
        'dimensions': '10x5x2 cm', 'is_active': True, 'is_deleted': False
    }
    edit_dialog = GlobalProductEditDialog(product_data=sample_data, current_user_info={'user_id': 'test_admin'})
    if edit_dialog.exec_() == QDialog.Accepted:
        print("Data from Edit Dialog:", edit_dialog.get_product_data())

    # Test Edit mode for a soft-deleted product
    sample_deleted_data = {
        'product_id': 2, 'product_name': 'Deleted Product', 'product_code': 'DP002',
        'description': 'This was deleted', 'category': 'Old Cat', 'language_code': 'fr',
        'base_unit_price': 5.00, 'unit_of_measure': 'unit', 'weight': 0.1,
        'dimensions': '5x5x5 cm', 'is_active': False, 'is_deleted': True, 'deleted_at': 'some_timestamp'
    }
    edit_deleted_dialog = GlobalProductEditDialog(product_data=sample_deleted_data, current_user_info={'user_id': 'test_admin'})
    if edit_deleted_dialog.exec_() == QDialog.Accepted:
        print("Data from Edit Deleted Dialog:", edit_deleted_dialog.get_product_data())

    app.exec_()
