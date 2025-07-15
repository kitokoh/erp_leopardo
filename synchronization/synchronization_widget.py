# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QGroupBox, QFormLayout, QLineEdit, QLabel
from .next_erp_client import NextERPClient
from db.cruds.products_crud import products_crud_instance
import db as db_manager

class SynchronizationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Settings Group ---
        settings_group = QGroupBox("Paramètres de Synchronisation")
        settings_layout = QFormLayout()
        self.api_url_input = QLineEdit()
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        settings_layout.addRow(QLabel("URL de l'API Next-ERP:"), self.api_url_input)
        settings_layout.addRow(QLabel("Clé d'API Next-ERP:"), self.api_key_input)
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)

        # --- Actions Group ---
        actions_layout = QHBoxLayout()
        self.sync_button = QPushButton("Lancer la Synchronisation")
        self.sync_button.clicked.connect(self.start_synchronization)
        self.save_settings_button = QPushButton("Sauvegarder les Paramètres")
        self.save_settings_button.clicked.connect(self.save_settings)
        actions_layout.addWidget(self.sync_button)
        actions_layout.addWidget(self.save_settings_button)
        main_layout.addLayout(actions_layout)

        # --- Logs Group ---
        logs_group = QGroupBox("Journaux de Synchronisation")
        logs_layout = QVBoxLayout()
        self.logs_text_edit = QTextEdit()
        self.logs_text_edit.setReadOnly(True)
        logs_layout.addWidget(self.logs_text_edit)
        logs_group.setLayout(logs_layout)
        main_layout.addWidget(logs_group)

        self.setLayout(main_layout)

    def load_settings(self):
        self.api_url_input.setText(db_manager.get_setting('next_erp_api_url', ''))
        self.api_key_input.setText(db_manager.get_setting('next_erp_api_key', ''))

    def save_settings(self):
        db_manager.set_setting('next_erp_api_url', self.api_url_input.text())
        db_manager.set_setting('next_erp_api_key', self.api_key_input.text())
        self.logs_text_edit.append("Paramètres de synchronisation sauvegardés.")

    def start_synchronization(self):
        self.logs_text_edit.clear()
        self.logs_text_edit.append("Démarrage de la synchronisation...")

        api_url = self.api_url_input.text()
        api_key = self.api_key_input.text()

        if not api_url or not api_key:
            self.logs_text_edit.append("Erreur: L'URL de l'API et la clé d'API doivent être configurées.")
            return

        client = NextERPClient(api_url, api_key)

        products_to_sync = products_crud_instance.get_all_products()

        if not products_to_sync:
            self.logs_text_edit.append("Aucun produit à synchroniser.")
            return

        self.logs_text_edit.append(f"{len(products_to_sync)} produits à synchroniser.")

        for product in products_to_sync:
            self.logs_text_edit.append(f"Synchronisation du produit: {product.get('product_name')}")
            result = client.sync_product(product)
            if result.get("status") == "success":
                self.logs_text_edit.append(f"  -> Succès: ID Next-ERP = {result.get('id')}")
            else:
                self.logs_text_edit.append(f"  -> Échec: {result.get('message')}")

        self.logs_text_edit.append("Synchronisation terminée.")
