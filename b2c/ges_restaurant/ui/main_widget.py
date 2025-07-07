import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                             QScrollArea, QGridLayout, QFrame, QMessageBox, QDialog,
                             QLineEdit, QSpinBox, QComboBox, QFormLayout, QDialogButtonBox,
                             QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QFile, QTextStream # Added QFile, QTextStream
from PyQt5.QtGui import QIcon, QPalette, QColor
from typing import Optional
from typing import Dict
from typing import Any

# Assuming cruds are in the parent directory of ui (ges_restaurant.cruds)
# This needs careful path management when integrated into the main app.
try:
    from ..cruds import restaurant_table_crud, restaurant_commande_crud
    from ..models import RestaurantTable # For type hinting if needed
    # from db.cruds.products_crud import products_crud_instance # For product selection
except ImportError:
    logging.error("ges_restaurant.ui.main_widget: Failed to import CRUDS or Models. Relative imports might fail if not run as part of the main app.")
    # Provide dummy fallbacks if needed for standalone UI design, though functionality will be broken.
    restaurant_table_crud = None
    restaurant_commande_crud = None
    # products_crud_instance = None


# --- Add/Edit Table Dialog ---
class AddEditTableDialog(QDialog):
    def __init__(self, table_id: Optional[int] = None, parent=None):
        super().__init__(parent)
        self.table_id = table_id
        self.setWindowTitle(self.tr("Edit Table") if table_id else self.tr("Add New Table"))
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.numero_table_edit = QLineEdit()
        self.capacite_spinbox = QSpinBox()
        self.capacite_spinbox.setRange(1, 100)
        self.capacite_spinbox.setValue(4)
        self.statut_combo = QComboBox()
        self.statut_combo.addItems(['libre', 'occupee', 'reservee', 'a_nettoyer'])
        self.emplacement_edit = QLineEdit()

        form_layout.addRow(self.tr("Table Number/Name:"), self.numero_table_edit)
        form_layout.addRow(self.tr("Capacity:"), self.capacite_spinbox)
        form_layout.addRow(self.tr("Status:"), self.statut_combo)
        form_layout.addRow(self.tr("Location:"), self.emplacement_edit)

        layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        if self.table_id and restaurant_table_crud:
            self._load_table_data()

    def _load_table_data(self):
        try:
            table = restaurant_table_crud.get_table_by_id(self.table_id)
            if table:
                self.numero_table_edit.setText(table.numero_table)
                self.capacite_spinbox.setValue(table.capacite)
                self.statut_combo.setCurrentText(table.statut)
                self.emplacement_edit.setText(table.emplacement or "")
            else:
                QMessageBox.warning(self, self.tr("Error"), self.tr("Table not found."))
                self.reject() # Close dialog if table not found
        except Exception as e:
            logging.error(f"Error loading table data for ID {self.table_id}: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Load Error"), str(e))
            self.reject()


    def get_data(self) -> Optional[Dict[str, Any]]:
        if not self.numero_table_edit.text().strip():
            QMessageBox.warning(self, self.tr("Validation Error"), self.tr("Table number/name cannot be empty."))
            return None

        return {
            "numero_table": self.numero_table_edit.text().strip(),
            "capacite": self.capacite_spinbox.value(),
            "statut": self.statut_combo.currentText(),
            "emplacement": self.emplacement_edit.text().strip() or None
        }

    def accept(self):
        data = self.get_data()
        if data is None: # Validation failed in get_data
            return

        if not restaurant_table_crud:
            QMessageBox.critical(self, self.tr("Error"), self.tr("Table CRUD operations not available."))
            return super().reject()

        try:
            if self.table_id:
                result = restaurant_table_crud.update_table(self.table_id, data)
                if not result:
                     raise Exception("Update failed or table not found.")
            else:
                result = restaurant_table_crud.create_table(data)
                if not result:
                    raise Exception("Creation failed.")
            super().accept()
        except ValueError as ve: # Specific error for unique constraint or active commandes
            QMessageBox.critical(self, self.tr("Save Error"), str(ve))
            # Don't close dialog on this specific error, let user correct
        except Exception as e:
            logging.error(f"Error saving table: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Save Error"), str(e))
            # Potentially don't close dialog on generic error either unless it's unrecoverable
            # For now, keeping it open for user to retry or cancel.


# --- Single Table Widget (for the grid display) ---
class RestaurantUITableWidget(QFrame):
    """
    Represents a single table in the UI.
    Displays table number, status, and capacity.
    Changes background color based on status.
    """
    table_clicked = pyqtSignal(int) # Emits table_id when clicked

    def __init__(self, table_data: RestaurantTable, parent=None):
        super().__init__(parent)
        self.table_data = table_data
        self._init_ui()

    def _init_ui(self):
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setLineWidth(2)
        self.setMinimumSize(120, 100) # Min size for visibility
        self.setMaximumSize(180, 150) # Max size to keep grid organized

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5,5,5,5)
        layout.setSpacing(3)

        self.numero_label = QLabel(f"<b>{self.table_data.numero_table}</b>")
        self.numero_label.setAlignment(Qt.AlignCenter)

        self.statut_label = QLabel(self.table_data.statut.capitalize())
        self.statut_label.setAlignment(Qt.AlignCenter)

        self.capacite_label = QLabel(f"Capacité: {self.table_data.capacite}")
        self.capacite_label.setAlignment(Qt.AlignCenter)
        self.capacite_label.setStyleSheet("font-size: 8pt; color: grey;")

        # Simple icon based on status (could be more elaborate)
        icon_text = "🍽️" # Default
        if self.table_data.statut == 'occupee': icon_text = "🧑‍🤝‍🧑"
        elif self.table_data.statut == 'reservee': icon_text = "📅"
        elif self.table_data.statut == 'a_nettoyer': icon_text = "🧹"

        self.icon_label = QLabel(icon_text)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 20pt;")


        layout.addWidget(self.icon_label)
        layout.addWidget(self.numero_label)
        layout.addWidget(self.statut_label)
        layout.addWidget(self.capacite_label)

        self.update_style()

    def update_table_data(self, new_table_data: RestaurantTable):
        self.table_data = new_table_data
        self.numero_label.setText(f"<b>{self.table_data.numero_table}</b>")
        self.statut_label.setText(self.table_data.statut.capitalize())
        self.capacite_label.setText(f"Capacité: {self.table_data.capacite}")

        icon_text = "🍽️"
        if self.table_data.statut == 'occupee': icon_text = "🧑‍🤝‍🧑"
        elif self.table_data.statut == 'reservee': icon_text = "📅"
        elif self.table_data.statut == 'a_nettoyer': icon_text = "🧹"
        self.icon_label.setText(icon_text)

        self.update_style()

    def update_style(self):
        status_colors = {
            'libre': '#D4EFDF',    # Light Green
            'occupee': '#FADBD8',  # Light Red
            'reservee': '#FCF3CF', # Light Yellow
            'a_nettoyer': '#EAECEE' # Light Grey
        }
        border_colors = {
            'libre': '#A9DFBF',
            'occupee': '#F5B7B1',
            'reservee': '#F9E79F',
            'a_nettoyer': '#D5DBDB'
        }
        text_colors = {
            'libre': '#1E8449',
            'occupee': '#C0392B',
            'reservee': '#B7950B',
            'a_nettoyer': '#566573'
        }

        bg_color = status_colors.get(self.table_data.statut, '#FFFFFF')
        border_color = border_colors.get(self.table_data.statut, '#CCCCCC')
        text_color = text_colors.get(self.table_data.statut, '#000000')

        self.setStyleSheet(f"""
            RestaurantUITableWidget {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 8px;
            }}
            QLabel {{
                color: {text_color};
                background-color: transparent; /* Ensure labels don't obscure frame background */
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.table_clicked.emit(self.table_data.id)
        super().mousePressEvent(event)


# --- Main Restaurant Module Widget ---
class RestaurantMainWidget(QWidget):
    def __init__(self, parent=None, current_user_info=None):
        super().__init__(parent)
        self.current_user_info = current_user_info # Store for potential use
        self.all_table_widgets: Dict[int, RestaurantUITableWidget] = {} # To store references to table widgets by id

        self._load_stylesheet() # Load QSS first
        self._init_ui() # Then initialize UI elements

        if restaurant_table_crud:
            self.load_tables_display()
        else:
            self._show_crud_error_message("Restaurant Table CRUD")

    def _load_stylesheet(self):
        import os # Make sure os is imported
        try:
            module_path = os.path.dirname(__file__)
            style_file_path = os.path.join(module_path, "..", "styles", "restaurant_style.qss")

            if os.path.exists(style_file_path):
                file = QFile(style_file_path) # QFile needs to be imported from PyQt5.QtCore
                if file.open(QFile.ReadOnly | QFile.Text):
                    stream = QTextStream(file) # QTextStream needs to be imported from PyQt5.QtCore
                    stylesheet = stream.readAll()
                    self.setStyleSheet(stylesheet)
                    file.close()
                    logging.info(f"Stylesheet {style_file_path} loaded for RestaurantMainWidget.")
                else:
                    logging.warning(f"Could not open stylesheet file: {style_file_path} - {file.errorString()}")
            else:
                logging.warning(f"Stylesheet file not found: {style_file_path}")
        except Exception as e:
            logging.error(f"Error loading stylesheet for RestaurantMainWidget: {e}", exc_info=True)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15,15,15,15)
        main_layout.setSpacing(10)

        # Header / Title
        title_label = QLabel(self.tr("Restaurant Management"))
        # title_label.setStyleSheet("font-size: 20pt; font-weight: bold; color: #2c3e50;") # Will be handled by QSS
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Action Buttons (Add Table, Refresh)
        action_layout = QHBoxLayout()
        self.add_table_button = QPushButton(self.tr("Add Table"))
        self.add_table_button.setIcon(QIcon(":/icons/plus-circle.svg"))
        self.add_table_button.setObjectName("primaryActionButton") # For QSS styling
        # self.add_table_button.setStyleSheet("padding: 8px 15px; font-size: 10pt;")
        self.add_table_button.clicked.connect(self.open_add_table_dialog)


        self.refresh_button = QPushButton(self.tr("Refresh Tables"))
        self.refresh_button.setIcon(QIcon(":/icons/refresh-cw.svg"))
        self.refresh_button.setObjectName("refreshButton") # For QSS styling
        # self.refresh_button.setStyleSheet("padding: 8px 15px; font-size: 10pt;")
        self.refresh_button.clicked.connect(self.load_tables_display)

        action_layout.addWidget(self.add_table_button)
        action_layout.addStretch()
        action_layout.addWidget(self.refresh_button)
        main_layout.addLayout(action_layout)

        # Scroll Area for Tables Grid
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("tablesScrollArea")
        self.scroll_area.setWidgetResizable(True)
        # self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #f4f6f6; }") # To QSS file

        self.tables_container_widget = QWidget()
        self.tables_container_widget.setObjectName("tablesContainerWidget")
        self.grid_layout = QGridLayout(self.tables_container_widget)
        self.grid_layout.setSpacing(15)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.scroll_area.setWidget(self.tables_container_widget)
        main_layout.addWidget(self.scroll_area)

        # Placeholder for selected table details / actions
        self.selected_table_details_area = QFrame()
        self.selected_table_details_area.setObjectName("selectedTableDetailsArea")
        self.selected_table_details_area.setFrameShape(QFrame.StyledPanel)
        self.selected_table_details_area.setMinimumHeight(150)
        self.selected_table_details_area.setVisible(False)

        selected_details_layout = QVBoxLayout(self.selected_table_details_area)
        self.selected_table_label = QLabel(self.tr("No table selected."))
        self.selected_table_label.setObjectName("selectedTableNameLabel")
        self.selected_table_label.setAlignment(Qt.AlignCenter)
        # self.selected_table_label.setStyleSheet("font-size: 12pt; color: #7f8c8d;")

        self.manage_commande_button = QPushButton(self.tr("Manage Order for this Table"))
        self.manage_commande_button.setObjectName("primaryActionButton")
        self.manage_commande_button.setProperty("primaryAction", True) # Custom property for QSS
        self.manage_commande_button.setIcon(QIcon(":/icons/file-text.svg"))
        self.manage_commande_button.clicked.connect(self.manage_selected_table_order)
        self.manage_commande_button.setEnabled(False)
        # self.manage_commande_button.setStyleSheet("padding: 8px 15px; font-size: 10pt; background-color: #3498db; color: white; border-radius: 5px;")

        self.edit_table_button_detail = QPushButton(self.tr("Edit Table Details"))
        self.edit_table_button_detail.setObjectName("editTableDetailButton")
        self.edit_table_button_detail.setIcon(QIcon(":/icons/edit.svg"))
        self.edit_table_button_detail.clicked.connect(self.edit_selected_table_details)
        self.edit_table_button_detail.setEnabled(False)
        # self.edit_table_button_detail.setStyleSheet("padding: 6px 12px; font-size: 9pt;")


        selected_details_layout.addWidget(self.selected_table_label)

        buttons_detail_layout = QHBoxLayout()
        buttons_detail_layout.addStretch()
        buttons_detail_layout.addWidget(self.edit_table_button_detail)
        buttons_detail_layout.addWidget(self.manage_commande_button)
        buttons_detail_layout.addStretch()
        selected_details_layout.addLayout(buttons_detail_layout)

        main_layout.addWidget(self.selected_table_details_area)

        self.current_selected_table_id = None

    def _handle_order_updated(self, commande_id: int):
        """Slot to refresh UI elements when an order is updated."""
        logging.info(f"RestaurantMainWidget: Received order_updated_signal for commande_id: {commande_id}")
        self.load_tables_display() # Refresh the main table grid

        # If the updated order belongs to the currently selected table, refresh its details view
        if self.current_selected_table_id:
            try:
                # Check if the commande_id corresponds to the current_selected_table_id
                # This might require fetching the commande to get its table_id if not readily available
                # For now, let's assume if a table is selected, its details might need refresh
                # A more precise check would be:
                # updated_commande = restaurant_commande_crud.get_commande_by_id(commande_id)
                # if updated_commande and updated_commande.table_id == self.current_selected_table_id:

                current_table_widget = self.all_table_widgets.get(self.current_selected_table_id)
                if current_table_widget:
                    updated_table_data_for_detail = restaurant_table_crud.get_table_by_id(self.current_selected_table_id)
                    if updated_table_data_for_detail:
                        current_table_widget.update_table_data(updated_table_data_for_detail) # Update the widget in the grid
                        self.handle_table_click(self.current_selected_table_id) # Refresh the details panel
            except Exception as e:
                logging.error(f"Error refreshing selected table details after order update: {e}", exc_info=True)


    def _show_crud_error_message(self, crud_name="CRUD"):
        QMessageBox.critical(self, self.tr("Initialization Error"),
                             self.tr(f"{crud_name} operations are not available. The module might not function correctly."))

    def load_tables_display(self):
        if not restaurant_table_crud:
            self._show_crud_error_message("Restaurant Table CRUD")
            return

        # Clear existing table widgets from the layout
        for i in reversed(range(self.grid_layout.count())):
            widget_to_remove = self.grid_layout.itemAt(i).widget()
            if widget_to_remove:
                self.grid_layout.removeWidget(widget_to_remove)
                widget_to_remove.deleteLater()
        self.all_table_widgets.clear()

        try:
            tables = restaurant_table_crud.get_all_tables(limit=200) # Get a reasonable number of tables
        except Exception as e:
            logging.error(f"Error loading tables from DB: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Load Error"), self.tr("Could not load tables from the database."))
            return

        if not tables:
            # Handle case with no tables (e.g., show a message in the grid area)
            no_tables_label = QLabel(self.tr("No tables found. Please add tables."))
            no_tables_label.setAlignment(Qt.AlignCenter)
            self.grid_layout.addWidget(no_tables_label, 0, 0, 1, 4) # Span across a few columns
            return

        # Determine grid columns (e.g., 4 or 5 per row)
        # This could be dynamic based on window width, but fixed for now.
        cols = 5
        row, col = 0, 0
        for table_data in tables:
            table_widget = RestaurantUITableWidget(table_data)
            table_widget.table_clicked.connect(self.handle_table_click)
            self.grid_layout.addWidget(table_widget, row, col)
            self.all_table_widgets[table_data.id] = table_widget

            col += 1
            if col >= cols:
                col = 0
                row += 1

        # Add stretch to the end of the grid if needed, to keep items aligned left/top
        # self.grid_layout.setRowStretch(row + 1, 1)
        # self.grid_layout.setColumnStretch(cols, 1)
        self.tables_container_widget.adjustSize() # Adjust size of container

    def handle_table_click(self, table_id: int):
        self.current_selected_table_id = table_id
        table_widget = self.all_table_widgets.get(table_id)
        if table_widget:
            table_data = table_widget.table_data
            self.selected_table_label.setText(
                self.tr("Selected: <b>{0}</b> (Status: {1}, Capacity: {2})")
                .format(table_data.numero_table, table_data.statut.capitalize(), table_data.capacite)
            )
            self.selected_table_details_area.setVisible(True)
            self.manage_commande_button.setEnabled(True)
            self.edit_table_button_detail.setEnabled(True)

            # Example: Change border of selected table
            for tid, tw_widget in self.all_table_widgets.items():
                if tid == table_id:
                    tw_widget.setLineWidth(3) # Highlight selected
                    # tw_widget.setStyleSheet(tw_widget.styleSheet() + "border: 3px solid #3498db;")
                else:
                    tw_widget.setLineWidth(2) # Reset others
                    # tw_widget.update_style() # Reapply original style
                tw_widget.update() # Force repaint
        else:
            self.selected_table_details_area.setVisible(False)
            self.manage_commande_button.setEnabled(False)
            self.edit_table_button_detail.setEnabled(False)


    def open_add_table_dialog(self):
        dialog = AddEditTableDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_tables_display() # Refresh display
            QMessageBox.information(self, self.tr("Success"), self.tr("Table added successfully."))

    def edit_selected_table_details(self):
        if self.current_selected_table_id is None:
            QMessageBox.warning(self, self.tr("No Selection"), self.tr("Please select a table to edit."))
            return

        dialog = AddEditTableDialog(table_id=self.current_selected_table_id, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_tables_display() # Refresh display
            # Update the selected table details area if the same table is still selected
            current_table_widget = self.all_table_widgets.get(self.current_selected_table_id)
            if current_table_widget: # Should exist if ID is still valid
                try: # Re-fetch data to ensure it's fresh
                    updated_table_data = restaurant_table_crud.get_table_by_id(self.current_selected_table_id)
                    if updated_table_data:
                         current_table_widget.update_table_data(updated_table_data)
                         self.handle_table_click(self.current_selected_table_id) # Re-trigger click to update details panel
                except Exception as e:
                    logging.error(f"Failed to refresh selected table after edit: {e}")
            QMessageBox.information(self, self.tr("Success"), self.tr("Table details updated successfully."))


    def manage_selected_table_order(self):
        if self.current_selected_table_id is None:
            QMessageBox.warning(self, self.tr("No Table Selected"), self.tr("Please select a table to manage its order."))
            return

        table_widget = self.all_table_widgets.get(self.current_selected_table_id)
        if not table_widget: return

        table_data = table_widget.table_data

        # Placeholder for opening order management UI for this table
        # This would typically involve:
        # 1. Checking if there's an open order for this table.
        # 2. If yes, load it. If no, offer to create a new one.
        # 3. Open a new dialog or switch to an order management view.

        if not restaurant_commande_crud:
            self._show_crud_error_message("Restaurant Commande CRUD")
            return

        try:
            # Check for existing open orders for this table
            open_commandes = restaurant_commande_crud.get_commandes_for_table(
                table_id=table_data.id,
                statut='en_cours' # Or any other "open" statuses like 'servie'
            )

            active_commande = None
            if open_commandes:
                active_commande = open_commandes[0] # Take the most recent open one
                msg = self.tr("Table '{0}' has an existing open order (ID: {1}). Do you want to view/edit it, or start a new one (this will archive the current one if not empty)?")\
                      .format(table_data.numero_table, active_commande.id)
                # For now, let's just proceed with the existing open order if found.
                # A more complex UI would ask the user.
                QMessageBox.information(self, self.tr("Open Order Found"),
                                        self.tr("Loading existing open order {0} for table {1}.")
                                        .format(active_commande.id, table_data.numero_table))
            else:
                # No open order, confirm creation of a new one
                reply = QMessageBox.question(self, self.tr("New Order"),
                                             self.tr("No open order for table '{0}'. Start a new order?")
                                             .format(table_data.numero_table),
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if reply == QMessageBox.No:
                    return

                # Create a new basic commande (actual items added in order dialog)
                new_commande_data = {
                    "table_id": table_data.id,
                    "statut": "en_cours", # Default status
                    # 'created_by_user_id': self.current_user_info.get('user_id') if self.current_user_info else None
                }
                active_commande = restaurant_commande_crud.create_commande(new_commande_data)
                if not active_commande:
                    QMessageBox.critical(self, self.tr("Error"), self.tr("Failed to create a new order for the table."))
                    return
                QMessageBox.information(self, self.tr("New Order Created"),
                                        self.tr("New order {0} started for table {1}.")
                                        .format(active_commande.id, table_data.numero_table))
                # Update table status to 'occupee' if it was 'libre'
                if table_data.statut == 'libre' and restaurant_table_crud:
                    restaurant_table_crud.update_table(table_data.id, {'statut': 'occupee'})
                    self.load_tables_display() # Refresh grid to show new status


            # Now, open the order management dialog/view with `active_commande`
            # This part is a placeholder for the actual Order Management UI
            if active_commande:
                logging.info(f"Proceed to manage order ID: {active_commande.id} for table {table_data.numero_table}")
                # Need to import OrderManagementDialog
                from .order_management_dialog import OrderManagementDialog # Local import

                # Fetch the full commande object again to ensure all relationships are loaded for the dialog
                # This is important if the initial create_commande or get_commandes_for_table didn't eager load everything.
                detailed_commande_for_dialog = restaurant_commande_crud.get_commande_by_id(active_commande.id)

                if not detailed_commande_for_dialog:
                    QMessageBox.critical(self, self.tr("Error"), self.tr("Failed to load full order details for management."))
                    return

                order_dialog = OrderManagementDialog(commande=detailed_commande_for_dialog, parent=self)
                order_dialog.order_updated_signal.connect(self._handle_order_updated)
                order_dialog.exec_() # Modal dialog
                # After dialog closes, refresh tables as status might have changed
                # self.load_tables_display() # _handle_order_updated will do this
            else:
                # This case should be handled by logic above, but as a fallback:
                QMessageBox.warning(self, self.tr("Order Issue"), self.tr("Could not determine or create an order for this table."))

        except Exception as e:
            logging.error(f"Error managing order for table {table_data.id if table_data else 'N/A'}: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Order Management Error"), str(e))

    def refresh_all_data(self):
        """Public method to refresh the main display, e.g., when this widget becomes visible."""
        logging.info("RestaurantMainWidget: Refreshing all data.")
        self.load_tables_display()
        # Reset selected table details
        self.current_selected_table_id = None
        self.selected_table_details_area.setVisible(False)
        self.manage_commande_button.setEnabled(False)
        self.edit_table_button_detail.setEnabled(False)
        self.selected_table_label.setText(self.tr("No table selected."))


if __name__ == '__main__':
    # This is for standalone testing of the widget.
    # In the main app, this widget will be integrated into DocumentManager's QStackedWidget.
    import sys
    from PyQt5.QtWidgets import QApplication

    # Setup basic logging for standalone test
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s')

    # --- Dummy DB Setup for Standalone Test ---
    # This is a simplified in-memory DB for testing UI components without the full app.
    # It won't persist data.
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    # Assuming models.py is in the parent directory relative to this ui/main_widget.py
    # For standalone, need to adjust path to import models.py from ges_restaurant
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from models import Base as RestaurantBase # Import Base from ges_restaurant.models

    # Dummy get_db_connection and _manage_conn for standalone test
    engine = create_engine("sqlite:///:memory:")
    RestaurantBase.metadata.create_all(engine) # Create tables defined in ges_restaurant.models
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def get_dummy_db_session():
        return TestingSessionLocal()

    def dummy_manage_conn(func):
        def wrapper(*args, **kwargs):
            session = TestingSessionLocal()
            kwargs['conn'] = session
            try:
                result = func(*args, **kwargs)
                session.commit() # Commit for operations that modify
                return result
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
        return wrapper

    # Monkey-patch the cruds module's _manage_conn if it was using the fallback
    # This is tricky because the cruds module itself tries to import.
    # For a clean standalone test, cruds.py might need to accept a session factory.
    # For now, let's assume cruds.py's _manage_conn is the one we want to patch or that
    # it will correctly use a get_db_connection that we can patch.

    if restaurant_table_crud: # If cruds were imported (even with dummy _manage_conn)
        # This is a bit of a hack. Ideally, CRUD classes would take a session/engine.
        # Here, we're trying to make the imported cruds use our in-memory DB for the test.
        # This assumes the cruds module defined its own _manage_conn or uses one we can replace.
        # If cruds.py imported a global get_db_connection, we'd patch that.
        import cruds
        cruds._manage_conn = dummy_manage_conn
        # If cruds.py used `from db.connection import get_db_connection`, we'd need to patch that module's function.
        # This level of patching is complex for a simple test.

        # Pre-populate with some data for testing
        def populate_test_data():
            session = TestingSessionLocal()
            try:
                if not session.query(cruds.RestaurantTable).first(): # Check if data exists
                    tables_data = [
                        {"numero_table": "T1", "capacite": 4, "statut": "libre", "emplacement": "Fenêtre"},
                        {"numero_table": "T2", "capacite": 2, "statut": "occupee", "emplacement": "Centre"},
                        {"numero_table": "T3", "capacite": 6, "statut": "reservee", "emplacement": "Terrasse"},
                        {"numero_table": "Bar 1", "capacite": 1, "statut": "libre", "emplacement": "Bar"},
                        {"numero_table": "Salon VIP", "capacite": 8, "statut": "a_nettoyer", "emplacement": "VIP"},
                    ]
                    for t_data in tables_data:
                        # Use the CRUD function which now uses dummy_manage_conn
                        cruds.restaurant_table_crud.create_table(t_data, conn=session) # Pass session explicitly if needed by dummy
                    session.commit()
                    logging.info("Populated test database with sample tables.")
            except Exception as e:
                logging.error(f"Error populating test data: {e}", exc_info=True)
                session.rollback()
            finally:
                session.close()
        populate_test_data()


    app = QApplication(sys.argv)
    # Apply a basic style for better appearance in standalone test
    app.setStyleSheet("""
        QWidget { font-size: 10pt; }
        QPushButton { padding: 8px; border-radius: 4px; background-color: #e0e0e0; }
        QPushButton:hover { background-color: #d0d0d0; }
        QFrame[frameShape="6"] { /* StyledPanel */
            border-radius: 8px;
        }
    """)

    # Dummy current_user_info for testing
    test_user_info = {"user_id": 1, "username": "test_user", "role_name": "admin"}

    main_view = RestaurantMainWidget(current_user_info=test_user_info)
    main_view.setWindowTitle("Restaurant Module - Standalone Test")
    main_view.setGeometry(100, 100, 900, 700)
    main_view.show()

    # Ensure main_view has access to the (dummy) CRUD operations
    if not restaurant_table_crud: # If initial import failed
        main_view._show_crud_error_message("Restaurant Table CRUD (Standalone Test)")


    sys.exit(app.exec_())
