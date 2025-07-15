# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QGroupBox, QFormLayout, QLineEdit, QLabel, QProgressBar, QComboBox, QSplitter, QCheckBox
from PyQt5.QtCore import Qt, QDateTime, QTimer
from .next_erp_client import NextERPClient
from .cruds import add_or_update_product, get_product_by_next_erp_id
from db.cruds.products_crud import products_crud_instance
import db as db_manager
import json

class SynchronizationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_settings()
        self.sync_timer = QTimer(self)
        self.sync_timer.timeout.connect(self.start_synchronization)

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
        self.sync_deletions_checkbox = QCheckBox("Synchroniser les suppressions")
        self.sync_deletions_checkbox.setToolTip("Si coché, les éléments supprimés d'un côté seront supprimés de l'autre.")
        self.sync_button = QPushButton("Lancer la Synchronisation")
        self.sync_button.setToolTip("Démarre le processus de synchronisation.")
        self.sync_button.clicked.connect(self.start_synchronization)
        self.save_settings_button = QPushButton("Sauvegarder les Paramètres")
        self.save_settings_button.setToolTip("Enregistre les paramètres de l'API dans la base de données.")
        self.save_settings_button.clicked.connect(self.save_settings)
        actions_layout.addWidget(QLabel("Direction:"))
        actions_layout.addWidget(self.sync_direction_combo)
        actions_layout.addWidget(self.sync_deletions_checkbox)
        actions_layout.addStretch()
        actions_layout.addWidget(self.sync_button)
        actions_layout.addWidget(self.save_settings_button)
        top_layout.addWidget(actions_group)

        # Scheduler Group
        scheduler_group = QGroupBox("Planification Automatique")
        scheduler_layout = QHBoxLayout(scheduler_group)
        self.scheduler_checkbox = QCheckBox("Activer la synchronisation automatique")
        self.scheduler_checkbox.toggled.connect(self.toggle_scheduler)
        self.scheduler_interval_combo = QComboBox()
        self.scheduler_interval_combo.addItems(["Toutes les 5 minutes", "Toutes les 15 minutes", "Toutes les heures", "Tous les jours"])
        self.scheduler_interval_combo.setEnabled(False)
        scheduler_layout.addWidget(self.scheduler_checkbox)
        scheduler_layout.addWidget(self.scheduler_interval_combo)
        scheduler_layout.addStretch()
        top_layout.addWidget(scheduler_group)

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

        splitter.setSizes([250, 350])
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def load_settings(self):
        self.api_url_input.setText(db_manager.get_setting('next_erp_api_url', ''))
        self.api_key_input.setText(db_manager.get_setting('next_erp_api_key', ''))
        self.scheduler_checkbox.setChecked(db_manager.get_setting('sync_scheduler_enabled', 'false').lower() == 'true')
        self.scheduler_interval_combo.setCurrentText(db_manager.get_setting('sync_scheduler_interval', 'Toutes les heures'))

    def save_settings(self):
        db_manager.set_setting('next_erp_api_url', self.api_url_input.text())
        db_manager.set_setting('next_erp_api_key', self.api_key_input.text())
        db_manager.set_setting('sync_scheduler_enabled', str(self.scheduler_checkbox.isChecked()))
        db_manager.set_setting('sync_scheduler_interval', self.scheduler_interval_combo.currentText())
        self.log_message("Paramètres de synchronisation sauvegardés.", "INFO")
        self.toggle_scheduler(self.scheduler_checkbox.isChecked())

    def log_message(self, message, level="INFO"):
        timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        self.logs_text_edit.append(f"<b>[{level}]</b> {timestamp}: {message}")

    def toggle_scheduler(self, checked):
        self.scheduler_interval_combo.setEnabled(checked)
        if checked:
            interval_text = self.scheduler_interval_combo.currentText()
            interval_ms = 0
            if interval_text == "Toutes les 5 minutes":
                interval_ms = 5 * 60 * 1000
            elif interval_text == "Toutes les 15 minutes":
                interval_ms = 15 * 60 * 1000
            elif interval_text == "Toutes les heures":
                interval_ms = 60 * 60 * 1000
            elif interval_text == "Tous les jours":
                interval_ms = 24 * 60 * 60 * 1000

            if interval_ms > 0:
                self.sync_timer.start(interval_ms)
                self.log_message(f"Planificateur de synchronisation activé ({interval_text}).", "INFO")
        else:
            self.sync_timer.stop()
            self.log_message("Planificateur de synchronisation désactivé.", "INFO")

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

        if self.sync_deletions_checkbox.isChecked():
            self.sync_deletions(client)

        self.log_message("Synchronisation terminée.")

    def sync_app_to_next_erp(self, client):
        self.log_message("--- Synchronisation de l'application vers Next-ERP ---")
        products_to_sync = products_crud_instance.get_all_products()

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
                # Update local product with next_erp_id
                products_crud_instance.update_product(product.get('product_id'), {'next_erp_id': result.get('id')})
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
            add_or_update_product(product_data)
            self.progress_bar.setValue(i + 1)

    def sync_deletions(self, client):
        self.log_message("--- Synchronisation des suppressions ---")
        # App -> Next-ERP
        deleted_products = products_crud_instance.get_all_products(include_deleted=True, filters={'is_deleted': 1})
        for product in deleted_products:
            if product.get('next_erp_id'):
                self.log_message(f"Suppression du produit {product.get('product_name')} dans Next-ERP (ID: {product.get('next_erp_id')})")
                client.delete_product(product.get('next_erp_id'))

        # Next-ERP -> App
        all_local_products = products_crud_instance.get_all_products()
        all_next_erp_products = client.get_products()

        local_next_erp_ids = {p.get('next_erp_id') for p in all_local_products if p.get('next_erp_id')}
        next_erp_ids = {p.get('id') for p in all_next_erp_products}

        ids_to_delete_locally = local_next_erp_ids - next_erp_ids

        for next_erp_id in ids_to_delete_locally:
            product_to_delete = get_product_by_next_erp_id(next_erp_id)
            if product_to_delete:
                self.log_message(f"Suppression du produit {product_to_delete.get('product_name')} localement (ID Next-ERP: {next_erp_id})")
                products_crud_instance.delete_product(product_to_delete.get('product_id'))
