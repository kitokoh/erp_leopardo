import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFormLayout
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt
from datetime import datetime

class ClientDetailsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("clientDetailsWidget")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel(self.tr("Détails du Client"))
        title.setObjectName("clientDetailsTitleLabel")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.details_layout = QFormLayout()
        self.details_layout.setObjectName("clientDetailsFormLayout")
        self.details_layout.setLabelAlignment(Qt.AlignRight)
        self.details_layout.setSpacing(8)
        layout.addLayout(self.details_layout)

        layout.addStretch(1)

    def update_details(self, client_data):
        while self.details_layout.rowCount() > 0:
            self.details_layout.removeRow(0)

        if not client_data:
            self.details_layout.addRow(QLabel(self.tr("Erreur:")), QLabel(self.tr("Client non trouvé.")))
            return

        country_name = client_data.get('country', self.tr("N/A"))
        city_name = client_data.get('city', self.tr("N/A"))
        status_name = client_data.get('status', self.tr("N/A"))
        created_at_val = client_data.get('created_at')
        created_at_display = self.tr("N/A")
        if created_at_val:
            try:
                if isinstance(created_at_val, str):
                    dt_obj = datetime.fromisoformat(created_at_val.replace('Z', '+00:00'))
                else:
                    dt_obj = created_at_val
                created_at_display = dt_obj.strftime('%d %b %Y, %H:%M')
            except ValueError:
                logging.warning(f"Could not parse date: {created_at_val}")
                created_at_display = str(created_at_val)

        details_to_display = {
            self.tr("Nom Client:"): client_data.get('client_name', self.tr("N/A")),
            self.tr("Société:"): client_data.get('company_name') or self.tr("N/A"),
            self.tr("Pays:"): country_name,
            self.tr("Ville:"): city_name,
            self.tr("Statut:"): status_name,
            self.tr("Email:"): client_data.get('email') or self.tr("N/A"),
            self.tr("Téléphone:"): client_data.get('phone') or self.tr("N/A"),
            self.tr("Date Création:"): created_at_display,
            self.tr("Ident. Projet:"): client_data.get('project_identifier') or self.tr("N/A"),
            self.tr("Besoin Principal:"): client_data.get('primary_need_description') or self.tr("N/A")
        }

        for label_text, value_text in details_to_display.items():
            key_label = QLabel(f"<b>{label_text}</b>")
            value_label = QLabel(str(value_text))
            value_label.setWordWrap(True)
            value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self.details_layout.addRow(key_label, value_label)
