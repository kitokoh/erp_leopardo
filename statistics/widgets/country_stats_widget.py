from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QGroupBox, QFormLayout, QHBoxLayout
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import pyqtSignal

class CountryStatsDisplayWidget(QWidget):
    back_to_global_requested = pyqtSignal()
    add_client_to_country_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CountryStatsDisplayWidget")
        self.current_country_name = None
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        self.title_label = QLabel(self.tr("Statistiques par Pays"))
        self.title_label.setObjectName("countryStatsTitle")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.title_label)

        stats_group = QGroupBox(self.tr("Détails"))
        stats_group.setObjectName("countryStatsGroup")
        form_layout = QFormLayout(stats_group)
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setSpacing(8)
        form_layout.setContentsMargins(10, 12, 10, 10)


        self.client_count_label = QLabel("N/A")
        self.project_count_label = QLabel("N/A")
        self.sales_value_label = QLabel("N/A")

        value_font = QFont()
        value_font.setBold(True)
        self.client_count_label.setFont(value_font)
        self.project_count_label.setFont(value_font)
        self.sales_value_label.setFont(value_font)

        self.client_count_label.setObjectName("countryStatLabelClientCount")
        self.project_count_label.setObjectName("countryStatLabelProjectCount")
        self.sales_value_label.setObjectName("countryStatLabelSalesValue")


        form_layout.addRow(self.tr("Clients Totaux:"), self.client_count_label)
        form_layout.addRow(self.tr("Projets Actifs:"), self.project_count_label)
        form_layout.addRow(self.tr("Ventes Proforma Totales:"), self.sales_value_label)

        main_layout.addWidget(stats_group)

        buttons_layout = QHBoxLayout()
        self.add_client_button = QPushButton(self.tr("Ajouter Client à ce Pays"))
        self.add_client_button.setObjectName("addClientToCountryButton")
        self.add_client_button.setIcon(QIcon(":/icons/user-add.svg"))
        self.add_client_button.clicked.connect(self._emit_add_client_signal)
        buttons_layout.addWidget(self.add_client_button)

        buttons_layout.addStretch()

        self.back_button = QPushButton(self.tr("Retour aux Stats Globales"))
        self.back_button.setObjectName("backToGlobalButton")
        self.back_button.setIcon(QIcon(":/icons/arrow-left-circle.svg"))
        self.back_button.clicked.connect(self.back_to_global_requested)
        buttons_layout.addWidget(self.back_button)

        main_layout.addLayout(buttons_layout)
        main_layout.addStretch(1)
        self.setLayout(main_layout)

    def update_display(self, country_name: str, client_count: int, project_count: int, sales_value: float):
        self.current_country_name = country_name
        self.title_label.setText(self.tr("Statistiques pour: <b>{0}</b>").format(country_name))
        self.client_count_label.setText(str(client_count))
        self.project_count_label.setText(str(project_count))
        self.sales_value_label.setText("€ {:,.2f}".format(sales_value))
        logging.info(f"CountryStatsDisplayWidget updated for {country_name}.")

    def _emit_add_client_signal(self):
        if self.current_country_name:
            self.add_client_to_country_requested.emit(self.current_country_name)
        else:
            logging.warning("CountryStatsDisplayWidget: _emit_add_client_signal called but current_country_name is not set.")
