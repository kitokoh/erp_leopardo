# -*- coding: utf-8 -*-
import logging
import os # Added os import
import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QMessageBox, QComboBox,
    QInputDialog # Added QInputDialog
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QDialog



import db
from db.cruds import commandes_crud # Assuming this will be created with necessary functions
from config import CONFIG

# Placeholder for CommandeDialog - will be in commande_dialog.py
# from .commande_dialog import CommandeDialog

class CommandeWidget(QWidget):
    def __init__(self, client_info, current_user_info, parent=None):
        super().__init__(parent)
        self.client_info = client_info
        self.client_id = client_info.get("client_id")
        self.current_user_info = current_user_info
        self.logger = logging.getLogger(__name__)

        self.setup_ui()
        self.load_commandes()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Layout for filters and action buttons
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setSpacing(10)

        filter_label = QLabel(self.tr("Filtrer par Statut:"))
        filter_label.setStyleSheet("font-weight: bold;")
        top_bar_layout.addWidget(filter_label)

        self.status_filter_combo = QComboBox()
        self.status_filter_combo.setMinimumWidth(150)
        self.status_filter_combo.setStyleSheet("QComboBox { padding: 4px; }")
        self.populate_status_filters()
        self.status_filter_combo.currentIndexChanged.connect(self.load_commandes)
        top_bar_layout.addWidget(self.status_filter_combo)

        top_bar_layout.addStretch(1)

        self.add_commande_btn = QPushButton(QIcon(":/icons/plus-circle.svg"), self.tr("Nouvelle Commande"))
        self.add_commande_btn.setObjectName("primaryButton")
        self.add_commande_btn.setToolTip(self.tr("Créer une nouvelle commande pour ce client"))
        self.add_commande_btn.clicked.connect(self.add_new_commande)
        top_bar_layout.addWidget(self.add_commande_btn)

        self.refresh_btn = QPushButton(QIcon(":/icons/refresh-cw.svg"), self.tr("Actualiser"))
        self.refresh_btn.setObjectName("secondaryButton")
        self.refresh_btn.setToolTip(self.tr("Actualiser la liste des commandes"))
        self.refresh_btn.clicked.connect(self.load_commandes)
        top_bar_layout.addWidget(self.refresh_btn)

        main_layout.addLayout(top_bar_layout)

        # Table for Commandes
        self.commandes_table = QTableWidget()
        self.commandes_table.setObjectName("commandesTable")
        self.commandes_table.setColumnCount(7)
        self.commandes_table.setHorizontalHeaderLabels([
            self.tr("Référence"), self.tr("Date"), self.tr("Description"),
            self.tr("Statut"), self.tr("Total HT"), self.tr("Total TTC"), self.tr("Actions")
        ])

        # Style de l'en-tête
        header_style = """
            QHeaderView::section {
                background-color: #4a5568; /* Equivalent de Tailwind bg-gray-700 */
                color: white;
                padding: 6px;
                border: 1px solid #ddd;
                font-weight: bold;
                font-size: 9pt;
            }
        """
        self.commandes_table.horizontalHeader().setStyleSheet(header_style)
        self.commandes_table.verticalHeader().setVisible(False)
        self.commandes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) # Default
        self.commandes_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents) # Référence
        self.commandes_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents) # Date
        self.commandes_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents) # Statut
        self.commandes_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents) # Total HT
        self.commandes_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents) # Total TTC
        self.commandes_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents) # Actions

        self.commandes_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.commandes_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.commandes_table.setAlternatingRowColors(True)
        self.commandes_table.setSortingEnabled(True)
        self.commandes_table.itemDoubleClicked.connect(self.view_edit_commande)

        main_layout.addWidget(self.commandes_table)

        # Note: The duplicated action buttons layout was removed. The buttons are now in top_bar_layout.
        self.setLayout(main_layout)
        # self.populate_status_filters() # Already called in setup_ui


    def load_commandes(self):
        self.commandes_table.setRowCount(0)
        if not self.client_id:
            self.logger.warning("Client ID is missing, cannot load commandes.")
            return

        try:
            filters = {}
            status_filter_id = self.status_filter_combo.currentData()
            if status_filter_id is not None: # Make sure None (for "All Statuses") is handled correctly
                filters['status_commande_id'] = status_filter_id

            commandes_list = commandes_crud.get_commandes_for_client(self.client_id, filters=filters if filters else None)

            if commandes_list is None:
                self.logger.error(f"Failed to load commandes for client {self.client_id}. Received None.")
                QMessageBox.warning(self, "Erreur de Chargement", "Impossible de charger la liste des commandes.")
                commandes_list = []

            for row_idx, commande_data in enumerate(commandes_list):
                self.commandes_table.insertRow(row_idx)

                ref_item = QTableWidgetItem(commande_data.get("commande_reference", "N/A"))
                ref_item.setData(Qt.UserRole, commande_data.get("commande_id")) # Store ID

                # Add notes to tooltip
                notes_text = commande_data.get("notes", "")
                if notes_text:
                    tooltip_text = f"Référence: {commande_data.get('commande_reference', 'N/A')}\n" \
                                   f"Notes: {notes_text[:100]}{'...' if len(notes_text) > 100 else ''}"
                    ref_item.setToolTip(tooltip_text)
                else:
                    ref_item.setToolTip(f"Référence: {commande_data.get('commande_reference', 'N/A')}\nPas de notes.")

                self.commandes_table.setItem(row_idx, 0, ref_item)

                date_str = commande_data.get("commande_date", "")
                if date_str:
                    try:
                        # Ensure datetime.datetime is used for fromisoformat
                        dt_obj = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        date_formatted = dt_obj.strftime('%Y-%m-%d %H:%M')
                    except ValueError:
                        date_formatted = date_str
                else:
                    date_formatted = "N/A"
                self.commandes_table.setItem(row_idx, 1, QTableWidgetItem(date_formatted))

                self.commandes_table.setItem(row_idx, 2, QTableWidgetItem(commande_data.get("description_commande", "")))
                self.commandes_table.setItem(row_idx, 3, QTableWidgetItem(commande_data.get("status_commande_name", "N/A")))

                total_ht = commande_data.get("total_ht", 0.0)
                total_ttc = commande_data.get("total_ttc", 0.0)
                currency = commande_data.get("currency", "EUR")

                ht_item = QTableWidgetItem(f"{total_ht:.2f} {currency}" if total_ht is not None else "N/A")
                ht_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.commandes_table.setItem(row_idx, 4, ht_item)

                ttc_item = QTableWidgetItem(f"{total_ttc:.2f} {currency}" if total_ttc is not None else "N/A")
                ttc_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.commandes_table.setItem(row_idx, 5, ttc_item)

                # Actions cell (View/Edit, Delete)
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0,0,0,0)
                actions_layout.setSpacing(5)

                view_btn = QPushButton(QIcon(":/icons/eye.svg"), "")
                view_btn.setToolTip("Voir/Modifier Commande")
                view_btn.setProperty("class", "tableActionButton")
                view_btn.clicked.connect(lambda ch, cmd_id=commande_data.get("commande_id"): self.view_edit_commande(cmd_id=cmd_id))
                actions_layout.addWidget(view_btn)

                proforma_btn = QPushButton(QIcon(":/icons/file-text.svg"), "")
                proforma_btn.setToolTip("Générer Facture Proforma")
                proforma_btn.setProperty("class", "tableActionButton")
                proforma_btn.clicked.connect(lambda ch, cmd_id=commande_data.get("commande_id"): self.handle_generate_proforma_for_commande(cmd_id))
                actions_layout.addWidget(proforma_btn)

                delete_btn = QPushButton(QIcon(":/icons/trash-2.svg"), "")
                delete_btn.setToolTip("Supprimer Commande")
                delete_btn.setProperty("class", "dangerButtonTable")
                delete_btn.clicked.connect(lambda ch, cmd_id=commande_data.get("commande_id"): self.delete_selected_commande(cmd_id))
                actions_layout.addWidget(delete_btn)

                actions_layout.addStretch()
                self.commandes_table.setCellWidget(row_idx, 6, actions_widget)

            self.commandes_table.resizeRowsToContents()

        except Exception as e:
            self.logger.error(f"Error loading commandes for client {self.client_id}: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue lors du chargement des commandes: {e}")

    def add_new_commande(self):
        self.logger.info(f"Add new commande initiated for client: {self.client_id}")
        try:
            from .commande_dialog import CommandeDialog # Import here
            dialog = CommandeDialog(client_id=self.client_id, current_user_id=self.current_user_info.get('user_id'), parent=self)
            if dialog.exec_() == QDialog.Accepted:
                self.load_commandes()
                # Notify parent (ClientWidget) if it needs to refresh project lists or other client details
                if hasattr(self.parent(), 'refresh_display_full'): # Example method name
                    self.parent().refresh_display_full()
        except ImportError:
            self.logger.error("Failed to import CommandeDialog.")
            QMessageBox.critical(self, "Erreur Importation", "Le module CommandeDialog n'a pas pu être chargé.")
        except Exception as e:
            self.logger.error(f"Error opening CommandeDialog for new commande: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur Inattendue", f"Une erreur est survenue: {e}")


    def view_edit_commande(self, item=None, cmd_id=None):
        if cmd_id is None: # Called from double click
            if item is None: # Should not happen if triggered by double click signal with item
                # Try to get from current selection if item is None but was a context menu call or similar
                selected_items = self.commandes_table.selectedItems()
                if not selected_items:
                    self.logger.warning("view_edit_commande called without cmd_id and no selection in table.")
                    return
                row = self.commandes_table.row(selected_items[0]) # Use row of first selected item
                id_item = self.commandes_table.item(row, 0) # Assuming ID is in column 0
            else: # Called with item from double click
                row = item.row()
                id_item = self.commandes_table.item(row, 0) # Assuming ID is in column 0

            if not id_item:
                self.logger.warning(f"view_edit_commande: Could not get ID item from row {row if 'row' in locals() else 'N/A'}.")
                return
            cmd_id = id_item.data(Qt.UserRole)

        if not cmd_id:
            QMessageBox.warning(self, "Erreur", "ID de commande non trouvé.")
            return

        self.logger.info(f"View/Edit commande initiated for commande_id: {cmd_id}")
        try:
            from .commande_dialog import CommandeDialog # Import here
            dialog = CommandeDialog(client_id=self.client_id, commande_id_to_edit=cmd_id, current_user_id=self.current_user_info.get('user_id'), parent=self)
            if dialog.exec_() == QDialog.Accepted:
                self.load_commandes()
                # Notify parent (ClientWidget) if it needs to refresh project lists or other client details
                if hasattr(self.parent(), 'refresh_display_full'): # Example method name
                    self.parent().refresh_display_full()
        except ImportError:
            self.logger.error("Failed to import CommandeDialog.")
            QMessageBox.critical(self, "Erreur Importation", "Le module CommandeDialog n'a pas pu être chargé.")
        except Exception as e:
            self.logger.error(f"Error opening CommandeDialog for editing commande {cmd_id}: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur Inattendue", f"Une erreur est survenue: {e}")


    def delete_selected_commande(self, cmd_id=None):
        if cmd_id is None: # Called from a context menu or button not directly passing ID
            selected_items = self.commandes_table.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Sélection Requise", "Veuillez sélectionner une commande à supprimer.")
                return
            id_item = self.commandes_table.item(selected_items[0].row(), 0)
            if not id_item: return
            cmd_id = id_item.data(Qt.UserRole)

        if not cmd_id:
            QMessageBox.warning(self, "Erreur", "ID de commande non trouvé pour la suppression.")
            return

        commande_ref = "N/A"
        for i in range(self.commandes_table.rowCount()):
            if self.commandes_table.item(i,0).data(Qt.UserRole) == cmd_id:
                commande_ref = self.commandes_table.item(i,0).text()
                break

        reply = QMessageBox.question(self, "Confirmer Suppression",
                                     f"Êtes-vous sûr de vouloir supprimer la commande '{commande_ref}' (ID: {cmd_id}) et tous ses articles associés ?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                success = commandes_crud.delete_commande(cmd_id)
                if success:
                    QMessageBox.information(self, "Succès", f"Commande '{commande_ref}' supprimée avec succès.")
                    self.load_commandes()
                else:
                    QMessageBox.warning(self, "Échec", f"Impossible de supprimer la commande '{commande_ref}'.")
            except Exception as e:
                self.logger.error(f"Error deleting commande {cmd_id}: {e}", exc_info=True)
                QMessageBox.critical(self, "Erreur", f"Une erreur est survenue lors de la suppression : {e}")

    def handle_generate_proforma_for_commande(self, commande_id):
        """
        Handles the request to generate a proforma invoice for the given commande_id.
        This is a placeholder and will be implemented in the next steps.
        """
        self.logger.info(f"Génération de proforma demandée pour la commande ID: {commande_id}")

        try:
            from utils.app_constants import SUPPORTED_LANGUAGES # Import centralisé
            from db.cruds import client_documents_crud # Import pour la dernière langue de proforma

            # 1. Fetching commande details (header, items).
            commande_details = commandes_crud.get_commande_by_id(commande_id)
            if not commande_details:
                QMessageBox.warning(self, "Erreur", f"Impossible de trouver les détails pour la commande ID: {commande_id}")
                return

            commande_items = commandes_crud.get_items_for_commande(commande_id)
            if commande_items is None: # Check for None specifically, as empty list is valid
                QMessageBox.warning(self, "Erreur", f"Impossible de charger les articles pour la commande ID: {commande_id}")
                return

            # 2. Fetching client details. (client_id is in commande_details)
            client_id = commande_details.get("client_id")
            if not client_id: # Should not happen if DB is consistent
                QMessageBox.warning(self, "Erreur Données Commande", f"L'ID client est manquant pour la commande {commande_id}.")
                return

            # client_info for proforma generation should be fetched fresh
            # It's available in self.client_info if this widget is for a single client,
            # but it's better to fetch to ensure it's the most up-to-date for the document.
            client_info_for_doc = db.get_client_by_id(client_id) # Use direct import from db
            if not client_info_for_doc:
                QMessageBox.warning(self, "Erreur", f"Impossible de trouver les détails du client ID: {client_id}")
                return

            # Ensure base_folder_path is set for document saving logic later
            if not client_info_for_doc.get("default_base_folder_path"):
                 # This logic should ideally be centralized or handled more robustly
                client_name_for_folder = client_info_for_doc.get("client_name", "unknown_client")
                client_id_for_folder = client_info_for_doc.get("client_id", "no_id")
                sane_client_name = "".join(c if c.isalnum() else "_" for c in client_name_for_folder)
                # Assuming self.parent() or self.parent().parent() can give app_root_dir
                # This is a bit fragile. ClientWidget has self.app_root_dir
                app_root_dir = ""
                if hasattr(self, 'app_root_dir'): # If CommandeWidget itself has it
                    app_root_dir = self.app_root_dir
                elif hasattr(self.parent(), 'app_root_dir'): # If parent (ClientWidget) has it
                    app_root_dir = self.parent().app_root_dir

                if not app_root_dir:
                    self.logger.error("Could not determine app_root_dir for proforma generation path.")
                    QMessageBox.critical(self, "Erreur Configuration", "Chemin racine de l'application non défini.")
                    return

                clients_base_subdir = CONFIG.get('clients_dir', 'clients')
                relative_folder = os.path.join(clients_base_subdir, f"{sane_client_name}_{client_id_for_folder[:8]}")
                client_info_for_doc["default_base_folder_path"] = os.path.join(app_root_dir, relative_folder)
                # We also need the relative path for DB storage later
                client_info_for_doc["db_relative_base_folder_path"] = relative_folder
            else:
                # Ensure default_base_folder_path is absolute for saving, and store relative for DB
                app_root_dir = ""
                if hasattr(self, 'app_root_dir'): app_root_dir = self.app_root_dir
                elif hasattr(self.parent(), 'app_root_dir'): app_root_dir = self.parent().app_root_dir

                if not app_root_dir:
                    self.logger.error("Could not determine app_root_dir for proforma generation path (existing folder).")
                    QMessageBox.critical(self, "Erreur Configuration", "Chemin racine de l'application non défini (dossier existant).")
                    return

                client_info_for_doc["db_relative_base_folder_path"] = client_info_for_doc["default_base_folder_path"]
                client_info_for_doc["default_base_folder_path"] = os.path.join(app_root_dir, client_info_for_doc["default_base_folder_path"])


            # 3. Fetching company details.
            default_company = db.companies_crud.get_default_company()
            if not default_company:
                QMessageBox.warning(self, "Erreur Configuration", "Aucune société par défaut n'est configurée.")
                return

            self.logger.info(f"Données récupérées pour la proforma de la commande {commande_id}:")
            self.logger.info(f"  Commande: {commande_details}")
            self.logger.info(f"  Articles: {commande_items}")
            self.logger.info(f"  Client: {client_info_for_doc}")
            self.logger.info(f"  Société: {default_company}")

            # 4. Preparing context for the proforma template.
            # This needs to align with what `document_generator.context_builder.get_document_context` expects
            # or what `utils.generate_pdf_for_document` can work with.

            # Basic company context
            company_context = {
                'name': default_company.get('company_name'),
                'address': default_company.get('address'),
                'payment_info': default_company.get('payment_info'),
                # Add other company fields as needed by the template (e.g., VAT number, phone, email)
            }

            # Basic client context
            client_context = {
                'name': client_info_for_doc.get('client_name'),
                'company_name': client_info_for_doc.get('company_name'),
                'address': client_info_for_doc.get('address'), # Assuming client_info_for_doc has a primary address field
                'country': client_info_for_doc.get('country'), # Assuming country name is already resolved
                'city': client_info_for_doc.get('city'),     # Assuming city name is already resolved
                'project_identifier': client_info_for_doc.get('project_identifier'),
                # Add other client fields (e.g., contact person, client VAT number)
            }

            # Commande items context
            items_context = []
            for item in commande_items:
                items_context.append({
                    'product_name': item.get('product_name'),
                    'description': item.get('description_item'),
                    'quantity': item.get('quantity'),
                    'unit_price_ht': item.get('unit_price_ht'),
                    'vat_rate_percentage': item.get('vat_rate', 0.0) * 100,
                    'total_item_ht': item.get('total_item_ht'),
                    'total_item_ttc': item.get('total_item_ttc'),
                    'product_code': item.get('product_code')
                })

            # Main document context (for proforma)
            # The structure here should be what your Proforma HTML template expects.
            # This often includes a 'doc' object and an 'items' list.
            document_context = {
                'doc': {
                    'type': 'Facture Proforma', # Or get from template type later
                    'title': f"Facture Proforma - {commande_details.get('commande_reference')}",
                    'date': datetime.fromisoformat(commande_details.get('commande_date').replace('Z', '')).strftime('%d/%m/%Y') if commande_details.get('commande_date') else 'N/A',
                    'reference': commande_details.get('commande_reference'),
                    'project_name': commande_details.get('project_name', ''), # Name of linked project
                    'notes': commande_details.get('description_commande', ''),
                    'currency_symbol': commande_details.get('currency', 'EUR'), # Or get from company/client settings
                    # Totals (these might be calculated or from DB)
                    'total_ht': commande_details.get('total_ht', 0.0),
                    'total_ttc': commande_details.get('total_ttc', 0.0),
                    'total_vat': (commande_details.get('total_ttc', 0.0) or 0.0) - (commande_details.get('total_ht', 0.0) or 0.0),
                    # Add other fields like payment_terms, delivery_terms if stored on Commande
                },
                'client': client_context,
                'company': company_context,
                'items': items_context,
                'current_date': datetime.now().strftime('%d/%m/%Y'),
                # You might need other global variables like logo paths, etc.
            }

            # Ensure totals in document_context['doc'] are up-to-date if not directly from DB
            # or if there's a chance they are stale.
            calculated_ht = sum(it['total_item_ht'] for it in items_context)
            calculated_ttc = sum(it['total_item_ttc'] for it in items_context)
            document_context['doc']['total_ht'] = calculated_ht
            document_context['doc']['total_ttc'] = calculated_ttc
            document_context['doc']['total_vat'] = calculated_ttc - calculated_ht


            self.logger.info(f"Context préparé pour la proforma : {document_context}")

            # 5. Selecting the appropriate proforma template.
            # --- Language Selection ---
            # SUPPORTED_LANGUAGES est maintenant importé depuis utils.app_constants

            # Determine default language for dialog more intelligently
            default_lang_code_for_dialog = 'fr' # Ultimate fallback

            # 1. Try client's main language code (assuming a field like 'main_language_code' or 'language_preference')
            #    (This field needs to be added to Clients table and CRUDs if it doesn't exist)
            #    For now, let's assume client_info_for_doc might have 'language_code' field from Clients table
            if client_info_for_doc.get('language_code') and client_info_for_doc['language_code'] in SUPPORTED_LANGUAGES:
                default_lang_code_for_dialog = client_info_for_doc['language_code']
                self.logger.info(f"Using client's main language '{default_lang_code_for_dialog}' as default for proforma.")
            else:
                # 2. Try language of the last proforma for this client
                last_proforma_lang = None
                try:
                    # Need client_id, which is in client_info_for_doc or commande_details
                    client_id_for_last_doc = client_info_for_doc.get('client_id')
                    if client_id_for_last_doc:
                        # Get last proforma (e.g., PROFORMA_PDF type, ordered by creation_date desc)
                        # This requires client_documents_crud to have a suitable function.
                        # Let's assume a function get_last_document_language(client_id, doc_type_pattern)
                        # For now, a simplified conceptual check:
                        recent_docs = client_documents_crud.get_documents_for_client(
                            client_id=client_id_for_last_doc,
                            filters={"document_type_generated": "PROFORMA_PDF"}, # Or a more general proforma type
                            limit=1, order_by="created_at DESC"
                        )
                        if recent_docs and recent_docs[0].get('language_code') in SUPPORTED_LANGUAGES:
                            last_proforma_lang = recent_docs[0]['language_code']
                            default_lang_code_for_dialog = last_proforma_lang
                            self.logger.info(f"Using last proforma language '{last_proforma_lang}' as default.")
                except Exception as e_last_lang:
                    self.logger.warning(f"Could not fetch last proforma language: {e_last_lang}")

                # 3. Fallback to client's 'selected_languages' (existing logic) or 'fr'
                if not last_proforma_lang: # Only if step 2 didn't yield a result
                    if client_info_for_doc.get('selected_languages'):
                        try:
                            langs = client_info_for_doc['selected_languages']
                            if isinstance(langs, str):
                                langs = [lang.strip() for lang in langs.split(',') if lang.strip()]
                            if langs and langs[0] in SUPPORTED_LANGUAGES:
                                default_lang_code_for_dialog = langs[0]
                                self.logger.info(f"Using client's selected_languages[0] '{default_lang_code_for_dialog}' as default.")
                        except Exception as lang_ex:
                            self.logger.warning(f"Could not determine client's preferred language from selected_languages, defaulting to 'fr'. Error: {lang_ex}")
                            # default_lang_code_for_dialog remains 'fr' (ultimate fallback)
                    else:
                        self.logger.info(f"Client has no main language or selected_languages, defaulting to '{default_lang_code_for_dialog}'.")


            language_items = [f"{name} ({code})" for code, name in SUPPORTED_LANGUAGES.items()]

            default_idx = 0
            try:
                default_lang_item_str = f"{SUPPORTED_LANGUAGES.get(default_lang_code_for_dialog, 'French')} ({default_lang_code_for_dialog})"
                default_idx = language_items.index(default_lang_item_str)
            except ValueError: # Fallback if constructed string not found (e.g. lang code valid but name mapping issue)
                self.logger.warning(f"Could not find default language item string '{default_lang_item_str}' in list. Falling back to index 0 or 'fr'.")
                for i, item_str in enumerate(language_items):
                    if f"({default_lang_code_for_dialog})" in item_str: # Try matching by code only
                        default_idx = i
                        break
                else: # If code itself not found, try 'fr'
                    for i, item_str in enumerate(language_items):
                        if "(fr)" in item_str:
                            default_idx = i
                            break

            selected_lang_display, lang_ok = QInputDialog.getItem(
                self,
                self.tr("Sélectionner la Langue du Proforma"),
                self.tr("Langue pour la génération du document proforma :"),
                language_items,
                default_selection_idx, # Set default selection
                False # Not editable
            )

            if not lang_ok or not selected_lang_display:
                self.logger.info("Génération de proforma annulée par l'utilisateur (sélection de langue).")
                return # User cancelled

            # Extract code from "Name (code)"
            target_lang_code = selected_lang_display.split('(')[-1].replace(')', '').strip()
            self.logger.info(f"Langue sélectionnée pour la Proforma: {target_lang_code} ({selected_lang_display})")

            # --- End Language Selection ---

            from db.cruds import templates_crud # Local import for clarity
            # Assuming "HTML_PROFORMA" is the template_type for proforma invoices. This might need adjustment.
            proforma_template_type = "HTML_PROFORMA"
            default_proforma_template = templates_crud.get_template_by_type_lang_default(
                template_type=proforma_template_type,
                language_code=target_lang_code,
                client_id=None # Global default template
            )

            if not default_proforma_template:
                self.logger.error(f"No default Proforma template found for type '{proforma_template_type}' and language '{target_lang_code}'.")
                QMessageBox.warning(self, "Modèle Manquant",
                                    f"Aucun modèle de facture proforma par défaut trouvé pour la langue '{target_lang_code}'.")
                return

            template_base_filename = default_proforma_template.get('base_file_name')
            template_inherent_language = default_proforma_template.get('language_code', target_lang_code) # Use template's lang if specified

            # Construct path to the template file
            # Need app_root_dir for this. ClientWidget should have it.
            app_root_dir_for_template = ""
            if hasattr(self, 'app_root_dir'): app_root_dir_for_template = self.app_root_dir
            elif hasattr(self.parent(), 'app_root_dir'): app_root_dir_for_template = self.parent().app_root_dir

            if not app_root_dir_for_template:
                self.logger.error("app_root_dir not found for template path construction.")
                QMessageBox.critical(self, "Erreur Configuration", "Chemin racine de l'application non défini pour les modèles.")
                return

            template_file_on_disk_abs = os.path.join(
                app_root_dir_for_template, # This needs to be the actual root where "templates" folder is
                db_manager.CONFIG.get("templates_dir", "templates"), # e.g., "templates"
                template_inherent_language,
                template_base_filename
            )

            self.logger.info(f"Attempting to use proforma template: {template_file_on_disk_abs}")

            if not os.path.exists(template_file_on_disk_abs):
                self.logger.error(f"Default Proforma template file not found on disk: {template_file_on_disk_abs}")
                QMessageBox.warning(self, "Fichier Modèle Introuvable",
                                    f"Le fichier modèle Proforma '{template_base_filename}' est introuvable pour la langue '{template_inherent_language}'.")
                return

            # Store for next step
            self._current_proforma_generation_data = {
                "commande_id": commande_id,
                "commande_details": commande_details,
                "commande_items": commande_items,
                "client_info_for_doc": client_info_for_doc, # Has absolute default_base_folder_path and relative db_relative_base_folder_path
                "default_company": default_company,
                "document_context": document_context,
                "template_file_path": template_file_on_disk_abs,
                "target_language_code": target_lang_code, # Language used for selecting template and for PDF content
                "source_template_id": default_proforma_template.get('template_id')
            }

            self.logger.info(f"Modèle proforma '{template_base_filename}' sélectionné. Prêt pour la génération PDF.")

            # 6. Calling a utility function to create the PDF.
            from utils import generate_pdf_for_document # Ensure this is imported

            # app_root_dir is needed by generate_pdf_for_document for resolving paths (e.g. fonts, images in templates)
            # It was determined when constructing template_file_on_disk_abs
            app_root_dir = ""
            if hasattr(self, 'app_root_dir'): app_root_dir = self.app_root_dir
            elif hasattr(self.parent(), 'app_root_dir'): app_root_dir = self.parent().app_root_dir
            else: # Should have been caught earlier
                self.logger.critical("app_root_dir is still not available before PDF generation.")
                QMessageBox.critical(self, "Erreur Critique", "Configuration de l'application manquante pour la génération PDF.")
                return

            # The client_info passed to generate_pdf_for_document needs 'default_base_folder_path' to be absolute for saving
            # and 'db_relative_base_folder_path' for ClientDocuments entry.
            # self._current_proforma_generation_data['client_info_for_doc'] already has these correctly set.

            generated_pdf_path = generate_pdf_for_document(
                source_file_path=self._current_proforma_generation_data["template_file_path"],
                client_info=self._current_proforma_generation_data["client_info_for_doc"], # Contains absolute path for saving
                app_root_dir=app_root_dir,
                parent_widget=self, # For any UI interactions from the util
                target_language_code=self._current_proforma_generation_data["target_language_code"],
                project_id=self._current_proforma_generation_data["commande_details"].get("project_id"), # Project linked to commande
                additional_context=self._current_proforma_generation_data["document_context"], # The full context we built
                document_type_for_context="HTML_PROFORMA", # The type of the source template
                output_subfolder_name="Proformas" # Specific subfolder for proformas
            )

            if generated_pdf_path and os.path.exists(generated_pdf_path):
                self.logger.info(f"Facture Proforma PDF générée avec succès : {generated_pdf_path}")
                # Store for next steps (saving to DB, opening)
                self._current_proforma_generation_data["generated_pdf_path"] = generated_pdf_path

                # 7. Saving the PDF to the client's folder (already done by generate_pdf_for_document)
                # 8. Creating a ClientDocuments entry, linking it to the commande_id.
                try:
                    gen_data = self._current_proforma_generation_data
                    client_info = gen_data["client_info_for_doc"]

                    # Construct relative path for DB
                    # client_info["db_relative_base_folder_path"] should be like "clients/ClientName_ID"
                    # generated_pdf_path is absolute like ".../app_root/clients/ClientName_ID/Proformas/PF_123.pdf"
                    # We need the path relative to the "app_root" effectively, but stored as relative to client's base dir for ClientDocuments table.

                    # client_info["default_base_folder_path"] is the ABSOLUTE path to client's base dir (e.g. .../app_root/clients/ClientName_ID)
                    # client_info["db_relative_base_folder_path"] is the RELATIVE path from app_root (e.g. clients/ClientName_ID)

                    # The path stored in ClientDocuments.file_path_relative is relative TO the client's base folder path.
                    # So, if generated_pdf_path is /abs/path/to/clients_dir/ClientFolder/Proformas/doc.pdf
                    # and client_info["default_base_folder_path"] is /abs/path/to/clients_dir/ClientFolder
                    # then relative_pdf_path_for_db should be Proformas/doc.pdf

                    relative_pdf_path_for_db = os.path.relpath(generated_pdf_path, client_info["default_base_folder_path"])

                    proforma_doc_data = {
                        'document_id': str(uuid.uuid4()), # Generate new UUID for this document
                        'client_id': client_info.get("client_id"),
                        'project_id': gen_data["commande_details"].get("project_id"),
                        'commande_id': gen_data["commande_id"], # Link to the commande
                        'order_identifier': gen_data["commande_details"].get("commande_reference"), # Use commande_reference
                        'document_name': os.path.basename(generated_pdf_path),
                        'file_name_on_disk': os.path.basename(generated_pdf_path),
                        'file_path_relative': relative_pdf_path_for_db,
                        'document_type_generated': "PROFORMA_PDF",
                        'source_template_id': gen_data.get('source_template_id'),
                        'user_id': self.current_user_id, # User who initiated the action
                        'language_code': gen_data["target_language_code"],
                        'version_tag': "1.0"
                    }

                    from db.cruds import client_documents_crud # Local import
                    new_doc_db_id = client_documents_crud.add_client_document(proforma_doc_data)

                    if new_doc_db_id:
                        self.logger.info(f"Proforma PDF document record created in DB with ID: {new_doc_db_id} (generated UUID was {proforma_doc_data['document_id']})")

                        # 9. Notifying the user and potentially opening the PDF.
                        QDesktopServices.openUrl(QUrl.fromLocalFile(generated_pdf_path))
                        self.parent().notification_manager.show( # Assuming parent is ClientWidget which has notification_manager
                            self.tr("Proforma Générée et Enregistrée"),
                            self.tr(f"La facture proforma '{proforma_doc_data['document_name']}' a été créée et est prête."),
                            type='SUCCESS'
                        )

                        # 10. Refreshing document lists in the parent ClientWidget.
                        if hasattr(self.parent(), 'populate_doc_table'):
                            self.logger.info("Refreshing document table in parent ClientWidget.")
                            self.parent().populate_doc_table()
                        else:
                            self.logger.warning("Could not find 'populate_doc_table' on parent widget to refresh document list.")

                    else:
                        self.logger.error(f"Échec de la création de l'enregistrement ClientDocument pour la proforma {proforma_doc_data['document_name']}.")
                        QMessageBox.critical(self, "Erreur Base de Données", "Impossible d'enregistrer le document proforma dans la base de données.")
                        # Consider cleanup of the generated PDF file if DB entry fails
                        if os.path.exists(generated_pdf_path):
                            try: os.remove(generated_pdf_path)
                            except OSError: self.logger.error(f"Échec de la suppression du PDF généré après échec DB: {generated_pdf_path}")
                        return

                except Exception as e_db_save:
                    self.logger.error(f"Erreur lors de la sauvegarde du document proforma en DB pour la commande {commande_id}: {e_db_save}", exc_info=True)
                    QMessageBox.critical(self, "Erreur Sauvegarde DB", f"Une erreur est survenue lors de la sauvegarde du document proforma: {e_db_save}")
                    return
            else:
                self.logger.error(f"Échec de la génération du PDF pour la proforma de la commande {commande_id}.")
                QMessageBox.critical(self, "Échec Génération PDF", "La génération du fichier PDF pour la facture proforma a échoué.")
                return # Stop processing

        except Exception as e:
            self.logger.error(f"Erreur lors de la préparation ou génération de proforma pour la commande {commande_id}: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur Inattendue", f"Une erreur inattendue est survenue: {e}")

        # Implementation will involve:
        # 9. Notifying the user and potentially opening the PDF.
        # 10. Refreshing document lists.

    def populate_status_filters(self):
        """Populates the status filter combobox for Commandes."""
        self.logger.debug(f"Populating status filters for CommandeWidget (Client: {self.client_id})")
        self.status_filter_combo.blockSignals(True)
        self.status_filter_combo.clear()
        self.status_filter_combo.addItem("Tous les Statuts", None)
        try:
            statuses = db.get_all_status_settings(type_filter='Commande')
            if statuses:
                for status in sorted(statuses, key=lambda x: x.get('sort_order', 0)):
                    self.status_filter_combo.addItem(QIcon.fromTheme(status.get('icon_name', '')), status.get('status_name'), status.get('status_id'))
        except Exception as e:
            self.logger.error(f"Error loading 'Commande' statuses for filter: {e}", exc_info=True)
        self.status_filter_combo.blockSignals(False)

    def refresh_commandes(self):
        """Public method to refresh the list of commandes, e.g., after an external change."""
        self.load_commandes()

if __name__ == '__main__':
    # This is a basic example of how to run this widget standalone for testing
    # You'll need to mock client_info and current_user_info
    # and ensure the DB is initialized with 'Commande' statuses.
    from PyQt5.QtWidgets import QApplication
    import sys

    # Mock data
    mock_client_info = {
        "client_id": "test_client_uuid_123",
        "client_name": "Client Test SARL"
    }
    mock_user_info = {
        "user_id": "test_user_uuid_456",
        "username": "testuser"
    }

    # Initialize DB (ensure this path is correct and your init_schema creates Commande statuses)
    # You might need to adjust path to db if running this file directly
    # For testing, you might put this in a try-except or ensure DB is set up before running
    try:
        # Assuming db directory is a sibling of commande_management
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from db import initialize_database
        initialize_database() # Make sure this creates 'Commande' statuses
    except Exception as e:
        print(f"Could not initialize database for CommandeWidget test: {e}")


    app = QApplication(sys.argv)
    # Apply a style to make it look somewhat like the main app
    app.setStyle("Fusion")
    # You might load your main QSS file here if available
    # with open("../style.qss", "r") as f:
    #    app.setStyleSheet(f.read())

    widget = CommandeWidget(client_info=mock_client_info, current_user_info=mock_user_info)
    widget.setWindowTitle("Test CommandeWidget")
    widget.setGeometry(100, 100, 800, 600)
    widget.show()
    sys.exit(app.exec_())
