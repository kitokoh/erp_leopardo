# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QGridLayout
from .logic import install_and_launch_app, is_installed
from .process_manager import process_manager
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView
import json
import os
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QProgressBar, QHBoxLayout
from PyQt5.QtGui import QIcon
from .config_dialog import ConfigDialog

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

        self.buttons_layout = QHBoxLayout()

        self.install_button = QPushButton(QIcon(":/icons/download.svg"), " Installer")
        self.install_button.clicked.connect(self.install)

        self.launch_button = QPushButton(QIcon(":/icons/play.svg"), " Lancer")
        self.launch_button.clicked.connect(self.launch)
        self.launch_button.setVisible(False)

        self.stop_button = QPushButton(QIcon(":/icons/stop-circle.svg"), " Arrêter")
        self.stop_button.clicked.connect(self.stop)
        self.stop_button.setVisible(False)

        self.uninstall_button = QPushButton(QIcon(":/icons/trash-2.svg"), " Désinstaller")
        self.uninstall_button.clicked.connect(self.uninstall)
        self.uninstall_button.setVisible(False)

        self.config_button = QPushButton(QIcon(":/icons/settings.svg"), " Configurer")
        self.config_button.clicked.connect(self.configure)
        self.config_button.setVisible(False)

        self.update_button = QPushButton(QIcon(":/icons/refresh-cw.svg"), " Mettre à jour")
        self.update_button.clicked.connect(self.update_app)
        self.update_button.setVisible(False)

        self.buttons_layout.addWidget(self.install_button)
        self.buttons_layout.addWidget(self.launch_button)
        self.buttons_layout.addWidget(self.stop_button)
        self.buttons_layout.addWidget(self.uninstall_button)
        self.buttons_layout.addWidget(self.config_button)
        self.buttons_layout.addWidget(self.update_button)

        if self.app_id == "next-erp" and platform.system() != "Linux":
            self.install_button.setEnabled(False)
            self.status_label.setText("Désactivé (Linux seulement)")

        self.layout.addWidget(self.icon_label)
        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.description_label)
        self.layout.addWidget(self.status_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.layout.addWidget(self.progress_bar)
        self.layout.addLayout(self.buttons_layout)

        self.update_status()

    def update_status(self):
        if process_manager.is_running(self.app_id):
            self.status = "En cours d'exécution"
            self.install_button.setVisible(False)
            self.launch_button.setVisible(False)
            self.stop_button.setVisible(True)
            self.uninstall_button.setVisible(False)
            self.config_button.setVisible(False)
            self.update_button.setVisible(False)
        elif is_installed(self.app_id):
            self.status = "Installé"
            self.install_button.setVisible(False)
            self.launch_button.setVisible(True)
            self.stop_button.setVisible(False)
            self.uninstall_button.setVisible(True)
            self.config_button.setVisible(True)
            self.update_button.setVisible(True)
        else:
            self.status = "Non installé"
            self.install_button.setVisible(True)
            self.launch_button.setVisible(False)
            self.stop_button.setVisible(False)
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
        self.update_status()

    def stop(self):
        process_manager.stop(self.app_id)
        self.update_status()

    def uninstall(self):
        from .logic import uninstall_app
        uninstall_app(self.app_id)
        self.update_status()

from .thread import Thread

    def install(self):
        self.install_button.setText("En cours...")
        self.install_button.setEnabled(False)
        self.status_label.setText("Installation en cours...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        self.thread = Thread(install_and_launch_app, self.app_id, self.parent().parent())
        self.thread.finished.connect(self.on_install_finished)
        self.thread.start()

    def on_install_finished(self, success):
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
