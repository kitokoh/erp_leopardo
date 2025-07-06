# -*- coding: utf-8 -*-
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QListWidget, QListWidgetItem,
    QDialogButtonBox, QPushButton, QApplication, QCheckBox
)
from PyQt5.QtCore import Qt

import db as db_manager # For fetching statuses

class MultiSelectStatusDialog(QDialog):
    def __init__(self, pre_selected_status_ids: list = None, parent=None):
        super().__init__(parent)
        self.pre_selected_status_ids = set(pre_selected_status_ids) if pre_selected_status_ids else set()
        self.setWindowTitle(self.tr("Sélectionner Statuts Client"))
        self.setMinimumWidth(350)
        self.setMinimumHeight(400)

        self._setup_ui()
        self._load_statuses()

    def tr(self, text, disambiguation=None, n=-1):
        return QApplication.translate("MultiSelectStatusDialog", text, disambiguation, n)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        self.status_list_widget = QListWidget()
        self.status_list_widget.setSpacing(3)
        main_layout.addWidget(self.status_list_widget)

        # Select All / Deselect All buttons
        select_buttons_layout = QHBoxLayout()
        self.select_all_button = QPushButton(self.tr("Tout Sélectionner"))
        self.select_all_button.clicked.connect(self._select_all_statuses)
        select_buttons_layout.addWidget(self.select_all_button)

        self.deselect_all_button = QPushButton(self.tr("Tout Désélectionner"))
        self.deselect_all_button.clicked.connect(self._deselect_all_statuses)
        select_buttons_layout.addWidget(self.deselect_all_button)
        main_layout.addLayout(select_buttons_layout)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def _load_statuses(self):
        self.status_list_widget.clear()
        try:
            # Assuming get_all_status_settings fetches all relevant statuses for clients
            client_statuses = db_manager.get_all_status_settings(type_filter='Client')
            if client_statuses:
                for status_dict in sorted(client_statuses, key=lambda x: x.get('status_name', '')):
                    status_id = status_dict.get('status_id')
                    status_name = status_dict.get('status_name', self.tr('Statut Inconnu'))

                    item = QListWidgetItem(self.status_list_widget)
                    checkbox = QCheckBox(status_name)
                    if status_id in self.pre_selected_status_ids:
                        checkbox.setChecked(True)

                    # Store status_id with the checkbox for easy retrieval
                    checkbox.setProperty("status_id", status_id)

                    self.status_list_widget.addItem(item)
                    self.status_list_widget.setItemWidget(item, checkbox)
            else:
                item = QListWidgetItem(self.tr("Aucun statut client défini."))
                item.setFlags(item.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEnabled)
                self.status_list_widget.addItem(item)

        except Exception as e:
            logging.error(f"Error loading client statuses into MultiSelectStatusDialog: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Chargement"), self.tr("Impossible de charger les statuts client."))

    def _select_all_statuses(self):
        for i in range(self.status_list_widget.count()):
            item = self.status_list_widget.item(i)
            widget = self.status_list_widget.itemWidget(item)
            if isinstance(widget, QCheckBox):
                widget.setChecked(True)

    def _deselect_all_statuses(self):
        for i in range(self.status_list_widget.count()):
            item = self.status_list_widget.item(i)
            widget = self.status_list_widget.itemWidget(item)
            if isinstance(widget, QCheckBox):
                widget.setChecked(False)

    def get_selected_status_ids(self) -> list[int]:
        selected_ids = []
        for i in range(self.status_list_widget.count()):
            item = self.status_list_widget.item(i)
            widget = self.status_list_widget.itemWidget(item)
            if isinstance(widget, QCheckBox) and widget.isChecked():
                status_id = widget.property("status_id")
                if status_id is not None:
                    selected_ids.append(status_id)
        return selected_ids

if __name__ == '__main__':
    # Example Usage (requires QApplication instance)
    app = QApplication([])

    # Mock db_manager for standalone testing if needed
    class MockStatus:
        def get_all_status_settings(self, type_filter=None):
            if type_filter == 'Client':
                return [
                    {'status_id': 1, 'status_name': 'Prospect'},
                    {'status_id': 2, 'status_name': 'Actif'},
                    {'status_id': 3, 'status_name': 'Inactif'},
                    {'status_id': 4, 'status_name': 'Archivé'}
                ]
            return []

    # db_manager = MockStatus() # Uncomment to use mock for standalone test if db import fails

    dialog = MultiSelectStatusDialog(pre_selected_status_ids=[1, 3])
    if dialog.exec_() == QDialog.Accepted:
        print("Selected Status IDs:", dialog.get_selected_status_ids())
    else:
        print("Dialog cancelled.")

    # app.exec_() # Not strictly necessary for non-GUI tests of dialog logic
