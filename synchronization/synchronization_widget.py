# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QGroupBox, QFormLayout, QLineEdit, QLabel, QProgressBar, QComboBox, QSplitter
from PyQt5.QtCore import Qt
from .next_erp_client import NextERPClient
from db.cruds.products.products_crud import products_crud
import db as db_manager
import json

class SynchronizationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Vertical)

        # --- Top Pane (Settings and Actions) ---
        top_pane = QWidget()
        top_layout = QVBoxLayout(top_pane)

        # Settings Group
        settings_group = QGroupBox("Paramètres de Synchronisation")
        settings_group.setToolTip("Configurez ici les informations de connexion à l'API de Next-ERP.")
        settings_layout = QFormLayout()
        self.api_url_input = QLineEdit()
        self.api_url_input.setPlaceholderText("https://api.nexterp.com")
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Votre clé d'API secrète")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        settings_layout.addRow(QLabel("URL de l'API Next-ERP:"), self.api_url_input)
        settings_layout.addRow(QLabel("Clé d'API Next-ERP:"), self.api_key_input)
        settings_group.setLayout(settings_layout)
        top_layout.addWidget(settings_group)

        # Actions Group
        actions_group = QGroupBox("Actions")
        actions_layout = QHBoxLayout(actions_group)
        self.sync_direction_combo = QComboBox()
        self.sync_direction_combo.addItems(["App -> Next-ERP", "Next-ERP -> App", "Bidirectionnelle"])
        self.sync_direction_combo.setToolTip("Choisissez le sens de la synchronisation des données.")
        self.sync_button = QPushButton("Lancer la Synchronisation")
        self.sync_button.setToolTip("Démarre le processus de synchronisation.")
        self.sync_button.clicked.connect(self.start_synchronization)
        self.save_settings_button = QPushButton("Sauvegarder les Paramètres")
        self.save_settings_button.setToolTip("Enregistre les paramètres de l'API dans la base de données.")
        self.save_settings_button.clicked.connect(self.save_settings)
        actions_layout.addWidget(QLabel("Direction:"))
        actions_layout.addWidget(self.sync_direction_combo)
        actions_layout.addStretch()
        actions_layout.addWidget(self.sync_button)
        actions_layout.addWidget(self.save_settings_button)
        top_layout.addWidget(actions_group)

        top_layout.addStretch()
        top_pane.setLayout(top_layout)
        splitter.addWidget(top_pane)

        # --- Bottom Pane (Progress and Logs) ---
        bottom_pane = QWidget()
        bottom_layout = QVBoxLayout(bottom_pane)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        bottom_layout.addWidget(self.progress_bar)

        # Logs Group
        logs_group = QGroupBox("Journaux de Synchronisation")
        logs_layout = QVBoxLayout(logs_group)
        self.logs_text_edit = QTextEdit()
        self.logs_text_edit.setReadOnly(True)
        self.logs_text_edit.setLineWrapMode(QTextEdit.NoWrap)
        logs_layout.addWidget(self.logs_text_edit)
        bottom_layout.addWidget(logs_group)

        bottom_pane.setLayout(bottom_layout)
        splitter.addWidget(bottom_pane)

        splitter.setSizes([200, 400])
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def load_settings(self):
        self.api_url_input.setText(db_manager.get_setting('next_erp_api_url', ''))
        self.api_key_input.setText(db_manager.get_setting('next_erp_api_key', ''))

    def save_settings(self):
        db_manager.set_setting('next_erp_api_url', self.api_url_input.text())
        db_manager.set_setting('next_erp_api_key', self.api_key_input.text())
        self.log_message("Paramètres de synchronisation sauvegardés.", "INFO")

    def log_message(self, message, level="INFO"):
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        self.logs_text_edit.append(f"<b>[{level}]</b> {timestamp}: {message}")

    def start_synchronization(self):
        self.logs_text_edit.clear()
        self.progress_bar.setValue(0)
        self.log_message("Démarrage de la synchronisation...")

        api_url = self.api_url_input.text()
        api_key = self.api_key_input.text()

        if not api_url or not api_key:
            self.log_message("L'URL de l'API et la clé d'API doivent être configurées.", "ERREUR")
            return

        client = NextERPClient(api_url, api_key)
        sync_direction = self.sync_direction_combo.currentText()

        if sync_direction == "App -> Next-ERP":
            self.sync_app_to_next_erp(client)
        elif sync_direction == "Next-ERP -> App":
            self.sync_next_erp_to_app(client)
        elif sync_direction == "Bidirectionnelle":
            self.sync_app_to_next_erp(client)
            self.sync_next_erp_to_app(client)

        self.log_message("Synchronisation terminée.")

    def sync_app_to_next_erp(self, client):
        self.log_message("--- Synchronisation de l'application vers Next-ERP ---")
        products_to_sync = products_crud.get_all_products()

        if not products_to_sync:
            self.log_message("Aucun produit à synchroniser depuis l'application.")
            return

        total_products = len(products_to_sync)
        self.progress_bar.setMaximum(total_products)
        self.progress_bar.setFormat(f"Envoi vers Next-ERP: %v/%m")
        self.log_message(f"{total_products} produits à synchroniser.")

        for i, product in enumerate(products_to_sync):
            self.log_message(f"Synchronisation du produit: {product.get('product_name')}")
            self.log_message(f"  -> Données envoyées: {json.dumps(product, indent=2)}")
            result = client.sync_product(product)
            if result.get("status") == "success":
                self.log_message(f"  -> Succès: {json.dumps(result, indent=2)}", "SUCCES")
            else:
                self.log_message(f"  -> Échec: {json.dumps(result, indent=2)}", "ERREUR")
            self.progress_bar.setValue(i + 1)

    def sync_next_erp_to_app(self, client):
        self.log_message("--- Synchronisation de Next-ERP vers l'application ---")
        products_from_next_erp = client.get_products()

        if not products_from_next_erp:
            self.log_message("Aucun produit à synchroniser depuis Next-ERP.")
            return

        total_products = len(products_from_next_erp)
        self.progress_bar.setMaximum(total_products)
        self.progress_bar.setFormat(f"Réception de Next-ERP: %v/%m")
        self.log_message(f"{total_products} produits à synchroniser.")

        for i, product_data in enumerate(products_from_next_erp):
            self.log_message(f"Traitement du produit de Next-ERP: {product_data.get('product_name')}")
            self.log_message(f"  -> Données reçues: {json.dumps(product_data, indent=2)}")
            # In a real implementation, you would check if the product exists
            # and update it, or create it if it doesn't.
            # products_crud_instance.add_or_update_product(product_data)
            self.log_message("  -> Action: Mise à jour/création dans la base de données locale (simulée).", "INFO")
            self.progress_bar.setValue(i + 1)
from PyQt5.QtCore import QDateTime
