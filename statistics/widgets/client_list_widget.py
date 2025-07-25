from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget, QHeaderView, QHBoxLayout, QTableWidgetItem
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import pyqtSignal, Qt
import logging

class StatusClientListWidget(QWidget):
    back_to_global_requested = pyqtSignal()
    view_client_detail_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("StatusClientListWidget")
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        self.title_label = QLabel(self.tr("Clients par Statut"))
        self.title_label.setObjectName("statusClientListTitle")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.title_label)

        self.clients_table = QTableWidget()
        self.clients_table.setObjectName("statusClientsTable")
        self.clients_table.setColumnCount(4)
        self.clients_table.setHorizontalHeaderLabels([
            self.tr("Nom Client"), self.tr("Société"), self.tr("Pays"), self.tr("Ville")
        ])
        self.clients_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.clients_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.clients_table.setSelectionMode(QTableWidget.SingleSelection)
        self.clients_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.clients_table.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: #e9ecef; padding: 4px; border: 1px solid #dee2e6; font-weight: bold; }")
        self.clients_table.verticalHeader().setVisible(False)
        self.clients_table.setAlternatingRowColors(True)
        self.clients_table.itemSelectionChanged.connect(self._on_table_selection_changed)
        self.clients_table.doubleClicked.connect(self._on_table_double_clicked)
        main_layout.addWidget(self.clients_table)

        buttons_layout = QHBoxLayout()
        self.view_client_button = QPushButton(self.tr("Voir Fiche Client"))
        self.view_client_button.setObjectName("viewClientButton")
        self.view_client_button.setIcon(QIcon(":/icons/eye.svg"))
        self.view_client_button.setEnabled(False)
        self.view_client_button.clicked.connect(self._emit_view_client_detail_signal)
        buttons_layout.addWidget(self.view_client_button)

        buttons_layout.addStretch()

        self.back_button = QPushButton(self.tr("Retour aux Stats Globales"))
        self.back_button.setObjectName("backToGlobalButton")
        self.back_button.setIcon(QIcon(":/icons/arrow-left-circle.svg"))
        self.back_button.clicked.connect(self.back_to_global_requested.emit)
        buttons_layout.addWidget(self.back_button)

        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)

    def update_display(self, status_name: str, clients: list[dict]):
        self.title_label.setText(self.tr("Clients - Statut: <b>{0}</b>").format(status_name))

        self.clients_table.setRowCount(0)
        self.clients_table.setSortingEnabled(False)

        if not clients:
            logging.info(f"StatusClientListWidget: No clients to display for status '{status_name}'.")
            self.clients_table.setRowCount(1)
            no_data_item = QTableWidgetItem(self.tr("Aucun client trouvé pour ce statut."))
            no_data_item.setTextAlignment(Qt.AlignCenter)
            self.clients_table.setItem(0, 0, no_data_item)
            if self.clients_table.columnCount() > 0:
                self.clients_table.setSpan(0, 0, 1, self.clients_table.columnCount())
            self.view_client_button.setEnabled(False)
            return

        self.clients_table.setRowCount(len(clients))
        for row, client_data in enumerate(clients):
            name_item = QTableWidgetItem(client_data.get("client_name", "N/A"))
            name_item.setData(Qt.UserRole, client_data.get("client_id"))
            self.clients_table.setItem(row, 0, name_item)
            self.clients_table.setItem(row, 1, QTableWidgetItem(client_data.get("company_name") or "N/A"))
            self.clients_table.setItem(row, 2, QTableWidgetItem(client_data.get("country", "N/A")))
            self.clients_table.setItem(row, 3, QTableWidgetItem(client_data.get("city", "N/A")))

        self.clients_table.setSortingEnabled(True)
        self.view_client_button.setEnabled(False)
        logging.info(f"StatusClientListWidget updated for status '{status_name}' with {len(clients)} clients.")

    def _on_table_selection_changed(self):
        if self.clients_table.rowCount() == 1 and self.clients_table.item(0,0) and \
           self.clients_table.item(0,0).text() == self.tr("Aucun client trouvé pour ce statut."):
            self.view_client_button.setEnabled(False)
        else:
            self.view_client_button.setEnabled(len(self.clients_table.selectedItems()) > 0)


    def _emit_view_client_detail_signal(self):
        selected_items = self.clients_table.selectedItems()
        if selected_items:
            selected_row = selected_items[0].row()
            client_id_item = self.clients_table.item(selected_row, 0)
            if client_id_item:
                client_id = client_id_item.data(Qt.UserRole)
                if client_id:
                    self.view_client_detail_requested.emit(str(client_id))
                else: logging.warning("No client_id in selected row's UserRole.")
            else: logging.warning("First item in selected row is None.")

    def _on_table_double_clicked(self, index):
        client_id_item = self.clients_table.item(index.row(), 0)
        if client_id_item:
            client_id = client_id_item.data(Qt.UserRole)
            if client_id: self.view_client_detail_requested.emit(str(client_id))
            else: logging.warning("No client_id in double-clicked row's UserRole.")
        else: logging.warning("First item in double-clicked row is None.")
