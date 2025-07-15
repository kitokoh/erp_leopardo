# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QGridLayout
from .logic import install_and_launch_app

from .logic import is_installed

class AddonCard(QWidget):
    def __init__(self, name, app_id, parent=None):
        super().__init__(parent)
        self.name = name
        self.app_id = app_id
        self.status = "Non installé"

        self.layout = QVBoxLayout(self)
        self.name_label = QLabel(self.name)
        self.status_label = QLabel(self.status)
        self.install_button = QPushButton("Installer")
        self.install_button.clicked.connect(self.install)
        self.launch_button = QPushButton("Lancer")
        self.launch_button.clicked.connect(self.launch)
        self.launch_button.setVisible(False)
        self.uninstall_button = QPushButton("Désinstaller")
        self.uninstall_button.clicked.connect(self.uninstall)
        self.uninstall_button.setVisible(False)

        if self.app_id == "invoice-ninja" or self.app_id == "next-erp":
            self.install_button.setEnabled(False)
            self.status_label.setText("Désactivé")

from PyQt5.QtWidgets import QProgressBar

        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.status_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.install_button)
        self.layout.addWidget(self.launch_button)
        self.layout.addWidget(self.uninstall_button)

        self.update_status()

    def update_status(self):
        if is_installed(self.app_id):
            self.status = "Installé"
            self.install_button.setVisible(False)
            self.launch_button.setVisible(True)
            self.uninstall_button.setVisible(True)
        else:
            self.status = "Non installé"
            self.install_button.setVisible(True)
            self.launch_button.setVisible(False)
            self.uninstall_button.setVisible(False)
        self.status_label.setText(self.status)

    def launch(self):
        install_and_launch_app(self.app_id)

    def uninstall(self):
        from .logic import uninstall_app
        uninstall_app(self.app_id)
        self.update_status()

from PyQt5.QtWidgets import QMessageBox

    def install(self):
        self.install_button.setText("En cours...")
        self.install_button.setEnabled(False)
        self.status_label.setText("Installation en cours...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        success = install_and_launch_app(self.app_id)

        self.progress_bar.setVisible(False)

        if not success:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue lors de l'installation ou du lancement de {self.name}.")
            self.status = "Échec de l'installation"
            self.status_label.setText(self.status)

        self.update_status()
        self.install_button.setEnabled(True)

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
