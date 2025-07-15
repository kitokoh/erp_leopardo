# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QGridLayout
from .logic import install_and_launch_app

from .logic import is_installed

class AddonCard(QWidget):
    def __init__(self, name, app_id, description, icon, parent=None):
        super().__init__(parent)
        self.name = name
        self.app_id = app_id
        self.status = "Non installé"

        self.layout = QVBoxLayout(self)
        self.name_label = QLabel(self.name)
        self.description_label = QLabel(description)
        self.icon_label = QLabel()
        self.icon_label.setPixmap(QPixmap(icon))
        self.status_label = QLabel(self.status)
        self.install_button = QPushButton("Installer")
        self.install_button.clicked.connect(self.install)
        self.launch_button = QPushButton("Lancer")
        self.launch_button.clicked.connect(self.launch)
        self.launch_button.setVisible(False)
from .config_dialog import ConfigDialog

        self.uninstall_button = QPushButton("Désinstaller")
        self.uninstall_button.clicked.connect(self.uninstall)
        self.uninstall_button.setVisible(False)
        self.config_button = QPushButton("Configurer")
        self.config_button.clicked.connect(self.configure)
        self.config_button.setVisible(False)
        self.update_button = QPushButton("Mettre à jour")
        self.update_button.clicked.connect(self.update_app)
        self.update_button.setVisible(False)

        if self.app_id == "invoice-ninja" or self.app_id == "next-erp":
            self.install_button.setEnabled(False)
            self.status_label.setText("Désactivé")

from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QProgressBar

        self.layout.addWidget(self.icon_label)
        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.description_label)
        self.layout.addWidget(self.status_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.install_button)
        self.layout.addWidget(self.launch_button)
        self.layout.addWidget(self.uninstall_button)
        self.layout.addWidget(self.config_button)
        self.layout.addWidget(self.update_button)

        self.update_status()

    def update_status(self):
        if is_installed(self.app_id):
            self.status = "Installé"
            self.install_button.setVisible(False)
            self.launch_button.setVisible(True)
            self.uninstall_button.setVisible(True)
            self.config_button.setVisible(True)
            self.update_button.setVisible(True)
        else:
            self.status = "Non installé"
            self.install_button.setVisible(True)
            self.launch_button.setVisible(False)
            self.uninstall_button.setVisible(False)
            self.config_button.setVisible(False)
            self.update_button.setVisible(False)
        self.status_label.setText(self.status)

    def update_app(self):
        from .logic import update_app
        update_app(self.app_id)
        self.update_status()

    def configure(self):
        from .logic import get_config, save_config
        config = get_config(self.app_id)
        dialog = ConfigDialog(self.app_id, config, self)
        if dialog.exec_():
            save_config(self.app_id, dialog.get_config())

    def launch(self):
        url = install_and_launch_app(self.app_id, self.parent().parent())
        if url and self.parent():
            self.parent().web_view.setUrl(url)
            self.parent().web_view.setVisible(True)

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

        success = install_and_launch_app(self.app_id, self.parent().parent())

        self.progress_bar.setVisible(False)

        if not success:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue lors de l'installation ou du lancement de {self.name}.")
            self.status = "Échec de l'installation"
            self.status_label.setText(self.status)

        self.update_status()
        self.install_button.setEnabled(True)

from PyQt5.QtWebEngineWidgets import QWebEngineView

import json

class AddonsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QGridLayout(self)
        self.web_view = QWebEngineView()
        self.web_view.setVisible(False)
        self.layout.addWidget(self.web_view, 0, 0, 1, 3)

        self.load_addons()

    def load_addons(self):
        # Load addons from json
        with open("addons/addons.json", "r") as f:
            addons = json.load(f)

        for i, addon in enumerate(addons):
            card = AddonCard(addon["name"], addon["app_id"], addon["description"], addon["icon"], self)
            self.layout.addWidget(card, (i // 3) + 1, i % 3)

        # Load addons from plugins
        for i, plugin_dir in enumerate(os.listdir("plugins")):
            manifest_path = os.path.join("plugins", plugin_dir, "manifest.json")
            if os.path.exists(manifest_path):
                with open(manifest_path, "r") as f:
                    manifest = json.load(f)

                card = AddonCard(manifest["name"], manifest["app_id"], manifest["description"], manifest["icon"], self)
                self.layout.addWidget(card, (len(addons) // 3) + (i // 3) + 1, i % 3)
