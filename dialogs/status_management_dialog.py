import sys
from PyQt5.QtWidgets import (
    QApplication, QDialog, QTableWidget, QTableWidgetItem,
    QPushButton, QVBoxLayout, QHBoxLayout, QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt

# Assuming db_manager.py is in the parent directory or accessible via PYTHONPATH
# For direct import if structure is /app/dialogs and /app/db
import os
import sys
# Add the parent directory of 'dialogs' to sys.path if db is a sibling directory
# This is a common way to handle imports in such structures when running files directly
# For a packaged application, you'd use relative imports like from ..db.cruds...
# current_dir = os.path.dirname(os.path.abspath(__file__))
# parent_dir = os.path.dirname(current_dir)
# if parent_dir not in sys.path:
#    sys.path.append(parent_dir)
# For this specific environment, let's assume direct import paths can be resolved
# or that the calling environment (e.g. main app) has set up sys.path correctly.
# We will try a relative import first, then a direct one if that fails (common for scripts)
# Updated imports to use the new status_manager service
try:
    # Assuming status_manager is in the parent directory or correctly in PYTHONPATH
    # For a typical project structure: from ..status_manager import status_service, Status, StatusType
    # If dialogs/ and status_manager/ are siblings under a common root (e.g. app/):
    # from ..status_manager import status_service, Status, StatusType
    # For now, trying a direct import style that might work if PYTHONPATH is set to project root
    from status_manager import status_service, status_models
    from .add_edit_status_dialog import AddEditStatusDialog
except ImportError as e:
    print(f"Error importing status_manager: {e}. Please ensure it's in PYTHONPATH.")
    # Fallback for running script directly or if relative import fails - this might not be ideal for status_manager
    # but we keep AddEditStatusDialog import for basic UI functionality if possible.
    # This dialog will be non-functional for data operations if status_manager fails to import.
    # Consider raising an error or disabling data operations if status_manager is critical.
    # For now, a print statement and None placeholders.
    status_service = None
    status_models = None
    try:
        from dialogs.add_edit_status_dialog import AddEditStatusDialog
    except ImportError: # If even local import fails
        from .add_edit_status_dialog import AddEditStatusDialog # Try relative one last time


class StatusManagementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Statuses")
        # Increased columns for is_archival and icon_name
        self.setMinimumSize(750, 450)
        self.init_ui()
        if status_service: # Only load if service is available
            self.load_statuses()
        else:
            QMessageBox.critical(self, "Service Error", "Status Manager Service not available. Cannot load statuses.")
        self._update_button_states()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.table_widget = QTableWidget()
        # Added "Is Archival" and "Icon Name"
        self.table_widget.setColumnCount(7)
        self.table_widget.setHorizontalHeaderLabels(["ID", "Name", "Type", "Color", "Sort Order", "Is Archival", "Icon Name"])
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers) # Disable editing directly in table
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows) # Select whole rows
        layout.addWidget(self.table_widget)

        # Buttons layout
        buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("Add")
        self.edit_button = QPushButton("Edit")
        self.delete_button = QPushButton("Delete") # Will be used in a future task
        self.close_button = QPushButton("Close")

        # Disable Edit and Delete buttons initially
        self.edit_button.setEnabled(False)
        self.delete_button.setEnabled(False)

        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.close_button)

        layout.addLayout(buttons_layout)

        # Connect signals
        self.add_button.clicked.connect(self.handle_add_status)
        self.edit_button.clicked.connect(self.handle_edit_status)
        self.delete_button.clicked.connect(self.handle_delete_status)
        self.close_button.clicked.connect(self.accept)
        self.table_widget.itemSelectionChanged.connect(self._update_button_states)


    def _update_button_states(self):
        """Enable/disable Edit and Delete buttons based on table selection."""
        is_row_selected = bool(self.table_widget.selectedItems())
        self.edit_button.setEnabled(is_row_selected)
        self.delete_button.setEnabled(is_row_selected) # Also manage delete button state

    def load_statuses(self):
        if not status_service:
            QMessageBox.critical(self, "Service Error", "Status Service not available.")
            return
        try:
            statuses = status_service.get_all_statuses() # Returns list of Status objects
        except Exception as e:
            QMessageBox.critical(self, "Service Error", f"Could not load statuses using service: {e}")
            statuses = []

        self.table_widget.setRowCount(0)

        if not statuses:
            return

        self.table_widget.setRowCount(len(statuses))
        for row_idx, status_obj in enumerate(statuses):
            status_id_item = QTableWidgetItem(str(status_obj.status_id))
            status_id_item.setData(Qt.UserRole, status_obj.status_id)

            name_item = QTableWidgetItem(status_obj.name)
            type_item = QTableWidgetItem(status_obj.type.value) # Use enum value
            color_item = QTableWidgetItem(status_obj.color_hex or "")
            sort_order_item = QTableWidgetItem(str(status_obj.sort_order))
            # New columns
            is_archival_item = QTableWidgetItem("Yes" if status_obj.is_archival else "No")
            icon_name_item = QTableWidgetItem(status_obj.icon_name or "")


            self.table_widget.setItem(row_idx, 0, status_id_item)
            self.table_widget.setItem(row_idx, 1, name_item)
            self.table_widget.setItem(row_idx, 2, type_item)
            self.table_widget.setItem(row_idx, 3, color_item)
            self.table_widget.setItem(row_idx, 4, sort_order_item)
            self.table_widget.setItem(row_idx, 5, is_archival_item)
            self.table_widget.setItem(row_idx, 6, icon_name_item)

    def handle_add_status(self):
        if not status_service or not status_models:
            QMessageBox.critical(self, "Service Error", "Status Service or Models not available.")
            return

        # Pass current types for the combo box in AddEditStatusDialog
        # This could be fetched from StatusType enum or dynamically from existing statuses.
        # For simplicity, using StatusType enum values.
        available_types = [st.value for st in status_models.StatusType]

        dialog = AddEditStatusDialog(self, available_status_types=available_types)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data() # This should include is_archival and icon_name
            try:
                # Convert string type back to StatusType enum member
                status_type_enum = status_models.StatusType.from_string(data["status_type"])

                added_status = status_service.add_status(
                    name=data["status_name"],
                    type=status_type_enum,
                    color_hex=data["color_hex"],
                    sort_order=data["sort_order"],
                    is_archival=data["is_archival"],
                    icon_name=data["icon_name"]
                )
                if added_status and added_status.status_id:
                    QMessageBox.information(self, "Success", f"Status '{data['status_name']}' added successfully.")
                    self.load_statuses()
                else:
                    # Check if add_status returned None due to CRUD failure or other reasons
                    error_msg = "Failed to add status"
                    if hasattr(added_status, 'error_message'): # If service returns more detailed error
                        error_msg += f": {added_status.error_message}"
                    QMessageBox.warning(self, "Failure", f"{error_msg}. Check logs.")
            except ValueError as ve: # For StatusType.from_string
                QMessageBox.critical(self, "Input Error", f"Invalid status type: {data['status_type']}. Error: {ve}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred while adding status: {e}")
                print(f"Error in handle_add_status: {e}")

    def handle_edit_status(self):
        if not status_service or not status_models:
            QMessageBox.critical(self, "Service Error", "Status Service or Models not available.")
            return

        selected_items = self.table_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select a status to edit.")
            return

        selected_row = self.table_widget.currentRow()
        id_item = self.table_widget.item(selected_row, 0)
        if not id_item:
            QMessageBox.critical(self, "Error", "Could not retrieve status ID from selected row.")
            return

        status_id = id_item.data(Qt.UserRole)
        if status_id is None:
            QMessageBox.critical(self, "Error", "No status ID associated with the selected row.")
            return

        try:
            # Fetch Status object using the service
            current_status_obj = status_service.get_status_by_id(status_id)
        except Exception as e:
            QMessageBox.critical(self, "Service Error", f"Could not fetch status details using service: {e}")
            return

        if not current_status_obj:
            QMessageBox.warning(self, "Not Found", f"Status with ID {status_id} not found via service.")
            return

        available_types = [st.value for st in status_models.StatusType]
        # Pass the Status object's dictionary representation to the dialog
        dialog = AddEditStatusDialog(self, status_data=current_status_obj.to_dict(), available_status_types=available_types)

        if dialog.exec_() == QDialog.Accepted:
            new_data = dialog.get_data() # This dict now includes is_archival and icon_name
            try:
                status_type_enum = status_models.StatusType.from_string(new_data["status_type"])
                success = status_service.update_status(
                    status_id=status_id, # Pass the original status_id
                    name=new_data["status_name"],
                    type=status_type_enum,
                    color_hex=new_data["color_hex"],
                    sort_order=new_data["sort_order"],
                    is_archival=new_data["is_archival"],
                    icon_name=new_data["icon_name"]
                )
                if success:
                    QMessageBox.information(self, "Success", f"Status '{new_data['status_name']}' updated successfully.")
                    self.load_statuses()
                else:
                    QMessageBox.warning(self, "Failure", f"Failed to update status '{new_data['status_name']}'. Check logs.")
            except ValueError as ve: # For StatusType.from_string
                QMessageBox.critical(self, "Input Error", f"Invalid status type: {new_data['status_type']}. Error: {ve}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred while updating status: {e}")
                print(f"Error in handle_edit_status: {e}")

    def handle_delete_status(self):
        if not status_service:
            QMessageBox.critical(self, "Service Error", "Status Service not available.")
            return

        selected_items = self.table_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select a status to delete.")
            return

        selected_row = self.table_widget.currentRow()
        id_item = self.table_widget.item(selected_row, 0)
        status_name_item = self.table_widget.item(selected_row, 1)

        if not id_item or not status_name_item:
            QMessageBox.critical(self, "Error", "Could not retrieve status details from selected row.")
            return

        status_id = id_item.data(Qt.UserRole)
        status_name = status_name_item.text()

        if status_id is None:
            QMessageBox.critical(self, "Error", "No status ID associated with the selected row.")
            return

        try:
            # Use the service's is_status_in_use (which needs to be fully implemented)
            if status_service.is_status_in_use(status_id):
                QMessageBox.warning(self, "Cannot Delete Status",
                                    f"The status '{status_name}' (ID: {status_id}) cannot be deleted "
                                    "because it is currently in use.") # Simpler message
                return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not verify if status is in use via service: {e}")
            return

        reply = QMessageBox.question(self, "Confirm Delete",
                                     f"Are you sure you want to delete the status '{status_name}' (ID: {status_id})?\n"
                                     "This action cannot be undone.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                if status_service.delete_status(status_id):
                    QMessageBox.information(self, "Success", f"Status '{status_name}' deleted successfully.")
                    self.load_statuses()
                else:
                    QMessageBox.warning(self, "Failure", f"Failed to delete status '{status_name}'. It might have already been deleted or an error occurred (check logs).")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred while deleting status: {e}")
                print(f"Error in handle_delete_status: {e}")


if __name__ == '__main__':
    # This part is for testing the dialog independently.
    # It now heavily relies on status_manager being correctly set up and accessible.
    # And db.db_manager for initialization if that's how the test DB is set up.

    # --- Setup for testing ---
    # This setup might need to be adapted based on your project structure and how DB is initialized.
    # Option 1: Run from project root with PYTHONPATH set.
    # Option 2: Add relative paths to sys.path if running this file directly.

    # Example of adding project root to sys.path if this script is run directly
    # This assumes 'dialogs' is one level down from project root.
    # current_script_dir = os.path.dirname(os.path.abspath(__file__))
    # project_root = os.path.dirname(current_script_dir)
    # if project_root not in sys.path:
    #     sys.path.insert(0, project_root)
    # print(f"Sys.path for testing: {sys.path}")

    # Ensure DB is initialized for testing (if your status_service relies on a live DB)
    # This part is highly dependent on your DB setup (e.g., using db_manager.init_db())
    # For now, we assume that if status_service is imported, it handles its DB connection.
    # If using a real DB, ensure it's initialized with the StatusSettings table.

    # Example of initializing a test DB (if you have such a setup)
    # try:
    #     from db.init_schema import initialize_database # Or your DB init function
    #     from db.connection import set_db_path, DB_PATH # If you can change DB path for test
    #     TEST_DB_NAME = "test_status_dialog.db"
    #     # set_db_path(TEST_DB_NAME) # Or however your app configures DB path
    #     # initialize_database({'database': {'path': TEST_DB_NAME, 'name': TEST_DB_NAME}}) # Pass appropriate config
    #     print(f"Test DB should be initialized at: {TEST_DB_NAME}")
    # except ImportError:
    #     print("Could not import DB initialization for testing. Status service might not work if DB is needed.")
    # except Exception as e:
    #     print(f"Error during DB initialization for testing: {e}")
    # --- End Setup for testing ---

    app = QApplication(sys.argv)

    if not status_service or not status_models:
        # If imports failed at the top, show a message and exit.
        # This check is a bit redundant if the class instantiation already showed a message,
        # but good for a standalone __main__ block.
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setText("Critical Import Error: StatusManager components (service or models) failed to import. The dialog cannot function.")
        msg_box.setInformativeText("Please check your PYTHONPATH and ensure the status_manager module is accessible.")
        msg_box.setWindowTitle("Application Error")
        msg_box.exec_()
        sys.exit(1)

    dialog = StatusManagementDialog()
    dialog.exec_()
    sys.exit(app.exec_())
