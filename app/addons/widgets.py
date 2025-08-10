# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QGridLayout
from .logic import install_and_launch_app

class AddonCard(QWidget):
    def __init__(self, name, app_id, parent=None):
        super().__init__(parent)
        self.name = name
        self.app_id = app_id

        self.layout = QVBoxLayout(self)
        self.name_label = QLabel(self.name)
        self.install_button = QPushButton("Installer et Lancer")
        self.install_button.clicked.connect(self.install)

        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.install_button)

    def install(self):
        install_and_launch_app(self.app_id)

class AddonsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QGridLayout(self)

        self.addons = [
            {"name": "Leopardo Agent", "app_id": "n8n"},
            {"name": "Leopardo Invoice", "app_id": "invoice-ninja"},
            {"name": "Leopardo Web ERP", "app_id": "next-erp"},
        ]

        for i, addon in enumerate(self.addons):
            card = AddonCard(addon["name"], addon["app_id"])
            self.layout.addWidget(card, i // 3, i % 3)
