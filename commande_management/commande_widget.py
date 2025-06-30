# -*- coding: utf-8 -*-
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QMessageBox, QComboBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

import db
from db.cruds import commandes_crud # Assuming this will be created with necessary functions

# Placeholder for CommandeDialog - will be in commande_dialog.py
# from .commande_dialog import CommandeDialog

class CommandeWidget(QWidget):
    def __init__(self, client_info, current_user_info, parent=None):
        super().__init__(parent)
        self.client_info = client_info
        self.client_id = client_info.get("client_id")
        self.current_user_info = current_user_info
        self.logger = logging.getLogger(__name__)

        self.setup_ui()
        self.load_commandes()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel(f"Commandes pour {self.client_info.get('client_name', 'N/A')}")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Filters (Placeholder)
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filtrer par Statut:"))
        self.status_filter_combo = QComboBox()
        # TODO: Populate status_filter_combo with 'Commande' statuses from StatusSettings
        # self.status_filter_combo.currentIndexChanged.connect(self.load_commandes)
        filter_layout.addWidget(self.status_filter_combo)
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)

        # Table for Commandes
        self.commandes_table = QTableWidget()
        self.commandes_table.setColumnCount(7) # Example columns
        self.commandes_table.setHorizontalHeaderLabels([
            "Référence", "Date", "Description", "Statut", "Total HT", "Total TTC", "Actions"
        ])
        self.commandes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.commandes_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.commandes_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.commandes_table.itemDoubleClicked.connect(self.view_edit_commande)
        main_layout.addWidget(self.commandes_table)

        # Action Buttons
        buttons_layout = QHBoxLayout()
        self.add_commande_btn = QPushButton(QIcon.fromTheme("document-new"), "Nouvelle Commande")
        self.add_commande_btn.clicked.connect(self.add_new_commande)
        buttons_layout.addWidget(self.add_commande_btn)

        self.refresh_btn = QPushButton(QIcon.fromTheme("view-refresh"), "Actualiser")
        self.refresh_btn.clicked.connect(self.load_commandes)
        buttons_layout.addWidget(self.refresh_btn)

        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout)

        self.setLayout(main_layout)

    def load_commandes(self):
        self.commandes_table.setRowCount(0)
        if not self.client_id:
            self.logger.warning("Client ID is missing, cannot load commandes.")
            return

        try:
            # TODO: Implement filter application
            # status_filter_id = self.status_filter_combo.currentData()
            # filters = {'status_commande_id': status_filter_id} if status_filter_id else None
            commandes_list = commandes_crud.get_commandes_for_client(self.client_id) #, filters=filters)

            if commandes_list is None:
                self.logger.error(f"Failed to load commandes for client {self.client_id}. Received None.")
                QMessageBox.warning(self, "Erreur de Chargement", "Impossible de charger la liste des commandes.")
                commandes_list = []

            for row_idx, commande_data in enumerate(commandes_list):
                self.commandes_table.insertRow(row_idx)

                ref_item = QTableWidgetItem(commande_data.get("commande_reference", "N/A"))
                ref_item.setData(Qt.UserRole, commande_data.get("commande_id")) # Store ID
                self.commandes_table.setItem(row_idx, 0, ref_item)

                date_str = commande_data.get("commande_date", "")
                if date_str:
                    try:
                        dt_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        date_formatted = dt_obj.strftime('%Y-%m-%d %H:%M')
                    except ValueError:
                        date_formatted = date_str
                else:
                    date_formatted = "N/A"
                self.commandes_table.setItem(row_idx, 1, QTableWidgetItem(date_formatted))

                self.commandes_table.setItem(row_idx, 2, QTableWidgetItem(commande_data.get("description_commande", "")))
                self.commandes_table.setItem(row_idx, 3, QTableWidgetItem(commande_data.get("status_commande_name", "N/A")))

                total_ht = commande_data.get("total_ht", 0.0)
                total_ttc = commande_data.get("total_ttc", 0.0)
                currency = commande_data.get("currency", "EUR")

                ht_item = QTableWidgetItem(f"{total_ht:.2f} {currency}" if total_ht is not None else "N/A")
                ht_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.commandes_table.setItem(row_idx, 4, ht_item)

                ttc_item = QTableWidgetItem(f"{total_ttc:.2f} {currency}" if total_ttc is not None else "N/A")
                ttc_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.commandes_table.setItem(row_idx, 5, ttc_item)

                # Actions cell (View/Edit, Delete)
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0,0,0,0)
                actions_layout.setSpacing(5)

                view_btn = QPushButton(QIcon.fromTheme("document-open"), "")
                view_btn.setToolTip("Voir/Modifier Commande")
                view_btn.clicked.connect(lambda ch, cmd_id=commande_data.get("commande_id"): self.view_edit_commande(cmd_id=cmd_id))
                actions_layout.addWidget(view_btn)

                delete_btn = QPushButton(QIcon.fromTheme("edit-delete"), "")
                delete_btn.setToolTip("Supprimer Commande")
                delete_btn.clicked.connect(lambda ch, cmd_id=commande_data.get("commande_id"): self.delete_selected_commande(cmd_id))
                actions_layout.addWidget(delete_btn)

                actions_layout.addStretch()
                self.commandes_table.setCellWidget(row_idx, 6, actions_widget)

        except Exception as e:
            self.logger.error(f"Error loading commandes for client {self.client_id}: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue lors du chargement des commandes: {e}")

    def add_new_commande(self):
        self.logger.info(f"Add new commande initiated for client: {self.client_id}")
        # dialog = CommandeDialog(client_id=self.client_id, current_user_id=self.current_user_info.get('user_id'), parent=self)
        # if dialog.exec_() == QDialog.Accepted:
        #     self.load_commandes()
        #     # Potentially trigger project creation/linking here or in CommandeDialog
        QMessageBox.information(self, "Info", "La fonctionnalité d'ajout de commande sera implémentée avec CommandeDialog.")


    def view_edit_commande(self, item=None, cmd_id=None):
        if cmd_id is None: # Called from double click
            if item is None: return
            row = item.row()
            id_item = self.commandes_table.item(row, 0)
            if not id_item: return
            cmd_id = id_item.data(Qt.UserRole)

        if not cmd_id:
            QMessageBox.warning(self, "Erreur", "ID de commande non trouvé.")
            return

        self.logger.info(f"View/Edit commande initiated for commande_id: {cmd_id}")
        # dialog = CommandeDialog(client_id=self.client_id, commande_id_to_edit=cmd_id, current_user_id=self.current_user_info.get('user_id'), parent=self)
        # if dialog.exec_() == QDialog.Accepted:
        #     self.load_commandes()
        QMessageBox.information(self, "Info", f"La fonctionnalité de modification de commande (ID: {cmd_id}) sera implémentée avec CommandeDialog.")


    def delete_selected_commande(self, cmd_id=None):
        if cmd_id is None: # Called from a context menu or button not directly passing ID
            selected_items = self.commandes_table.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Sélection Requise", "Veuillez sélectionner une commande à supprimer.")
                return
            id_item = self.commandes_table.item(selected_items[0].row(), 0)
            if not id_item: return
            cmd_id = id_item.data(Qt.UserRole)

        if not cmd_id:
            QMessageBox.warning(self, "Erreur", "ID de commande non trouvé pour la suppression.")
            return

        commande_ref = "N/A"
        for i in range(self.commandes_table.rowCount()):
            if self.commandes_table.item(i,0).data(Qt.UserRole) == cmd_id:
                commande_ref = self.commandes_table.item(i,0).text()
                break

        reply = QMessageBox.question(self, "Confirmer Suppression",
                                     f"Êtes-vous sûr de vouloir supprimer la commande '{commande_ref}' (ID: {cmd_id}) et tous ses articles associés ?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                success = commandes_crud.delete_commande(cmd_id)
                if success:
                    QMessageBox.information(self, "Succès", f"Commande '{commande_ref}' supprimée avec succès.")
                    self.load_commandes()
                else:
                    QMessageBox.warning(self, "Échec", f"Impossible de supprimer la commande '{commande_ref}'.")
            except Exception as e:
                self.logger.error(f"Error deleting commande {cmd_id}: {e}", exc_info=True)
                QMessageBox.critical(self, "Erreur", f"Une erreur est survenue lors de la suppression : {e}")

    def populate_status_filters(self):
        """Populates the status filter combobox for Commandes."""
        self.status_filter_combo.blockSignals(True)
        self.status_filter_combo.clear()
        self.status_filter_combo.addItem("Tous les Statuts", None)
        try:
            statuses = db.get_all_status_settings(type_filter='Commande')
            if statuses:
                for status in sorted(statuses, key=lambda x: x.get('sort_order', 0)):
                    self.status_filter_combo.addItem(QIcon.fromTheme(status.get('icon_name', '')), status.get('status_name'), status.get('status_id'))
        except Exception as e:
            self.logger.error(f"Error loading 'Commande' statuses for filter: {e}", exc_info=True)
        self.status_filter_combo.blockSignals(False)

    def refresh_commandes(self):
        """Public method to refresh the list of commandes, e.g., after an external change."""
        self.load_commandes()

if __name__ == '__main__':
    # This is a basic example of how to run this widget standalone for testing
    # You'll need to mock client_info and current_user_info
    # and ensure the DB is initialized with 'Commande' statuses.
    from PyQt5.QtWidgets import QApplication
    import sys

    # Mock data
    mock_client_info = {
        "client_id": "test_client_uuid_123",
        "client_name": "Client Test SARL"
    }
    mock_user_info = {
        "user_id": "test_user_uuid_456",
        "username": "testuser"
    }

    # Initialize DB (ensure this path is correct and your init_schema creates Commande statuses)
    # You might need to adjust path to db if running this file directly
    # For testing, you might put this in a try-except or ensure DB is set up before running
    try:
        # Assuming db directory is a sibling of commande_management
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from db import initialize_database
        initialize_database() # Make sure this creates 'Commande' statuses
    except Exception as e:
        print(f"Could not initialize database for CommandeWidget test: {e}")


    app = QApplication(sys.argv)
    # Apply a style to make it look somewhat like the main app
    app.setStyle("Fusion")
    # You might load your main QSS file here if available
    # with open("../style.qss", "r") as f:
    #    app.setStyleSheet(f.read())

    widget = CommandeWidget(client_info=mock_client_info, current_user_info=mock_user_info)
    widget.setWindowTitle("Test CommandeWidget")
    widget.setGeometry(100, 100, 800, 600)
    widget.show()
    sys.exit(app.exec_())
