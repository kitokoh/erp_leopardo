import sys
from PyQt5.QtWidgets import (
    QApplication, QDialog, QLineEdit, QComboBox, QSpinBox, QCheckBox,
    QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QFormLayout, QMessageBox
)
from PyQt5.QtCore import Qt
from typing import Optional, List, Dict, Any

class AddEditStatusDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None,
                 status_data: Optional[Dict[str, Any]] = None,
                 available_status_types: Optional[List[str]] = None):
        super().__init__(parent)
        self.status_data = status_data  # For pre-filling in edit mode
        self.available_status_types = available_status_types or ["Client", "Project", "Task", "Ticket", "Commande"]


        if self.status_data:
            self.setWindowTitle("Edit Status")
        else:
            self.setWindowTitle("Add New Status")

        self.init_ui()
        if self.status_data:
            self.prefill_data()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.type_combo = QComboBox()
        self.type_combo.addItems(self.available_status_types)
        self.type_combo.setEditable(True) # Allow free text input for new types

        self.color_edit = QLineEdit()
        self.color_edit.setPlaceholderText("#RRGGBB (e.g., #FF0000) or empty")
        self.sort_order_spinbox = QSpinBox()
        self.sort_order_spinbox.setRange(0, 999)

        # New fields
        self.is_archival_checkbox = QCheckBox("Is Archival Status")
        self.icon_name_edit = QLineEdit()
        self.icon_name_edit.setPlaceholderText("e.g., icon_name.svg (optional)")

        form_layout.addRow(QLabel("Name:"), self.name_edit)
        form_layout.addRow(QLabel("Type:"), self.type_combo)
        form_layout.addRow(QLabel("Color (Hex):"), self.color_edit)
        form_layout.addRow(QLabel("Sort Order:"), self.sort_order_spinbox)
        form_layout.addRow(QLabel("Archival:"), self.is_archival_checkbox)
        form_layout.addRow(QLabel("Icon Name:"), self.icon_name_edit)

        main_layout.addLayout(form_layout)

        # Buttons
        buttons_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")

        buttons_layout.addStretch()
        buttons_layout.addWidget(self.ok_button)
        buttons_layout.addWidget(self.cancel_button)

        main_layout.addLayout(buttons_layout)

        # Connect signals
        self.ok_button.clicked.connect(self.accept_dialog)
        self.cancel_button.clicked.connect(self.reject)

    def prefill_data(self):
        """Prefills the dialog fields if status_data is provided (for editing)."""
        if self.status_data:
            self.name_edit.setText(self.status_data.get("status_name", "")) # dict key is status_name

            type_value = self.status_data.get("status_type", "") # dict key is status_type
            # Ensure type_value is a string, as self.available_status_types contains strings
            if not isinstance(type_value, str): # If it's StatusType enum from direct obj
                 type_value = str(type_value.value if hasattr(type_value, 'value') else type_value)


            type_index = self.type_combo.findText(type_value, Qt.MatchFixedString)
            if type_index >= 0:
                self.type_combo.setCurrentIndex(type_index)
            else:
                # If type from data is not in predefined list, add it and select it
                # This handles custom types that might exist in DB but not in default list
                self.type_combo.addItem(type_value)
                self.type_combo.setCurrentText(type_value)

            self.color_edit.setText(self.status_data.get("color_hex", "") or "") # Ensure empty string if None
            self.sort_order_spinbox.setValue(self.status_data.get("sort_order", 0))

            # Prefill new fields
            # The key from Status.to_dict() is 'is_archival'
            self.is_archival_checkbox.setChecked(bool(self.status_data.get("is_archival", False)))
            self.icon_name_edit.setText(self.status_data.get("icon_name", "") or "") # Ensure empty string if None


    def get_data(self) -> Dict[str, Any]:
        """Returns the entered data as a dictionary."""
        color_text = self.color_edit.text().strip()
        icon_text = self.icon_name_edit.text().strip()
        return {
            "status_name": self.name_edit.text().strip(),
            "status_type": self.type_combo.currentText().strip(),
            "color_hex": color_text if color_text else None,
            "sort_order": self.sort_order_spinbox.value(),
            "is_archival": self.is_archival_checkbox.isChecked(),
            "icon_name": icon_text if icon_text else None,
        }

    def accept_dialog(self):
        """Validates input before accepting."""
        data = self.get_data()
        if not data["status_name"]:
            QMessageBox.warning(self, "Input Error", "Status Name cannot be empty.")
            return
        if not data["status_type"]:
            QMessageBox.warning(self, "Input Error", "Status Type cannot be empty.")
            return

        # Optional: Validate color_hex format if needed (e.g., regex for #RRGGBB)
        color = data["color_hex"]
        if color and not (color.startswith("#") and len(color) == 7):
            try:
                # Check if it's a valid hex by attempting to convert the R, G, B parts
                int(color[1:3], 16)
                int(color[3:5], 16)
                int(color[5:7], 16)
            except (ValueError, IndexError):
                QMessageBox.warning(self, "Input Error", "Color Hex code should be in #RRGGBB format (e.g., #FF0000) or empty.")
                return

        self.accept()


if __name__ == '__main__':
    # This part is for testing the dialog independently
    app = QApplication(sys.argv)

    # Test Add mode
    # Example of providing available types, similar to how StatusManagementDialog would do it.
    # In a real scenario, these types might come from status_models.StatusType
    test_available_types = ["Client", "Commande", "Project", "Task", "Ticket", "CustomType1"]

    print("--- Testing Add Mode ---")
    add_dialog = AddEditStatusDialog(available_status_types=test_available_types)
    if add_dialog.exec_() == QDialog.Accepted:
        print("Add Dialog Accepted. Data:", add_dialog.get_data())
    else:
        print("Add Dialog Canceled.")

    # Test Edit mode (example data from Status.to_dict() format)
    print("\n--- Testing Edit Mode ---")
    sample_edit_data = {
        "status_id": 1, # Not used by dialog UI directly but good for context
        "status_name": "In Progress",
        "status_type": "Project", # This should be a string
        "color_hex": "#FFA500",
        "sort_order": 10,
        "is_archival": True,
        "icon_name": "icon_progress.svg"
    }
    edit_dialog = AddEditStatusDialog(status_data=sample_edit_data, available_status_types=test_available_types)
    if edit_dialog.exec_() == QDialog.Accepted:
        print("Edit Dialog Accepted. Data:", edit_dialog.get_data())
    else:
        print("Edit Dialog Canceled.")

    # Test Edit mode with a custom type not in the initial list
    print("\n--- Testing Edit Mode with Custom Type ---")
    custom_type_data = {
        "status_name": "Special Task",
        "status_type": "SuperCustomTask", # This type is not in test_available_types initially
        "color_hex": "#001122",
        "sort_order": 1,
        "is_archival": False,
        "icon_name": "custom.png"
    }
    edit_custom_dialog = AddEditStatusDialog(status_data=custom_type_data, available_status_types=test_available_types)
    if edit_custom_dialog.exec_() == QDialog.Accepted:
        print("Edit Custom Type Dialog Accepted. Data:", edit_custom_dialog.get_data())
        # Verify that "SuperCustomTask" is now available in the combo box if it was added by prefill_data
        combo_items = [edit_custom_dialog.type_combo.itemText(i) for i in range(edit_custom_dialog.type_combo.count())]
        print(f"Combo box items after editing custom type: {combo_items}")
        assert "SuperCustomTask" in combo_items
    else:
        print("Edit Custom Type Dialog Canceled.")

    sys.exit(app.exec_())
