# -*- coding: utf-8 -*-
import os
# import sys # No longer used
import logging
import shutil
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QInputDialog, QMessageBox, QFileDialog, QApplication, QSizePolicy, QDialog,
    QMenu
)
from PyQt5.QtGui import QIcon, QDesktopServices, QFont
from PyQt5.QtCore import Qt, QUrl, QStandardPaths

from gui.widgets.pdf_viewer_widget import PdfViewerWidget # Ajout de l'importation
import db as db_manager
from db.cruds import client_documents_crud, projects_crud

from excel_editor import ExcelEditor
from gui.widgets.html_editor import HtmlEditor
from utils.app_constants import SUPPORTED_LANGUAGES # Import centralisé
# Other necessary dialogs and modules will be imported as needed, or passed from parent
from typing import Optional

class DocumentsTab(QWidget):
    def __init__(self, client_info: dict, config: object, app_root_dir: str,
                 notification_manager: object, current_user_info: dict,
                 main_module_create_document_dialog: callable,
                 main_module_compile_pdf_dialog: callable,
                 main_module_generate_pdf_for_document: callable,
                 parent_widget: QWidget,
                 parent=None):
        super().__init__(parent)
        self.client_info = client_info
        self.config = config
        self.app_root_dir = app_root_dir
        self.notification_manager = notification_manager
        self.current_user_info = current_user_info
        self.current_user_id = self.current_user_info.get('user_id')

        self.CreateDocumentDialog = main_module_create_document_dialog
        self.CompilePdfDialog = main_module_compile_pdf_dialog
        self.generate_pdf_for_document = main_module_generate_pdf_for_document # Garder pour génération PDF directe si utilisée ailleurs

        self.parent_widget = parent_widget
        self._is_populating_docs = False
        self.can_manage_documents_permission = False # Sera mis à jour par apply_permissions_to_tab

        self._setup_ui()
        self.populate_doc_table()

    def tr(self, text, disambiguation=None, n=-1):
        if self.parent_widget:
            return self.parent_widget.tr(text, disambiguation, n)
        return QApplication.translate("DocumentsTab", text, disambiguation, n)


    def _setup_ui(self):
        logging.info("DocumentsTab._setup_ui: Starting setup for Documents Tab Structure...")
        docs_layout = QVBoxLayout(self)
        docs_layout.setContentsMargins(5,5,5,5)
        docs_layout.setSpacing(8)

        self.doc_filter_layout_widget = QWidget()
        doc_filter_layout = QHBoxLayout(self.doc_filter_layout_widget)
        doc_filter_layout.setContentsMargins(0,0,0,0)

        doc_filter_label = QLabel(self.tr("Filtrer par Commande:"))
        doc_filter_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        doc_filter_layout.addWidget(doc_filter_label)
        self.doc_order_filter_combo = QComboBox()
        self.doc_order_filter_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.doc_order_filter_combo.currentIndexChanged.connect(self.populate_doc_table)
        doc_filter_layout.addWidget(self.doc_order_filter_combo)
        doc_filter_layout.addSpacing(10)

        doc_lang_filter_label = QLabel(self.tr("Filtrer par Langue:"))
        doc_lang_filter_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        doc_filter_layout.addWidget(doc_lang_filter_label)
        self.doc_language_filter_combo = QComboBox()
        self.doc_language_filter_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.doc_language_filter_combo.addItem(self.tr("Toutes"), "ALL")
        # Iterate over dictionary items (code, name) from imported constant
        for lang_code, lang_name in SUPPORTED_LANGUAGES.items(): # SUPPORTED_LANGUAGES est maintenant importé
            self.doc_language_filter_combo.addItem(self.tr(lang_name), lang_code) # Display translated name, store code

        self.doc_language_filter_combo.currentIndexChanged.connect(self.populate_doc_table)
        doc_filter_layout.addWidget(self.doc_language_filter_combo)
        doc_filter_layout.addSpacing(10)

        doc_type_filter_label = QLabel(self.tr("Filtrer par Type:"))
        doc_type_filter_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        doc_filter_layout.addWidget(doc_type_filter_label)
        self.doc_type_filter_combo = QComboBox()
        self.doc_type_filter_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.doc_type_filter_combo.addItem(self.tr("Tous"), "ALL")
        self.doc_type_filter_combo.addItem("HTML", "HTML")
        self.doc_type_filter_combo.addItem("EDITABLE_HTML", "EDITABLE_HTML") # Ajout du nouveau type
        self.doc_type_filter_combo.addItem("PDF", "PDF")
        self.doc_type_filter_combo.addItem("XLSX", "XLSX")
        self.doc_type_filter_combo.addItem("DOCX", "DOCX")
        self.doc_type_filter_combo.addItem(self.tr("Autre"), "OTHER")
        self.doc_type_filter_combo.currentIndexChanged.connect(self.populate_doc_table)
        doc_filter_layout.addWidget(self.doc_type_filter_combo)

        docs_layout.addWidget(self.doc_filter_layout_widget)
        # self.doc_filter_layout_widget.setVisible(True) # Déjà visible par défaut

        self.documents_empty_label = QLabel(self.tr("Aucun document trouvé pour ce client.\nUtilisez les boutons ci-dessous pour ajouter ou générer des documents."))
        self.documents_empty_label.setAlignment(Qt.AlignCenter)
        font_docs_empty = self.documents_empty_label.font()
        font_docs_empty.setPointSize(10)
        self.documents_empty_label.setFont(font_docs_empty)
        docs_layout.addWidget(self.documents_empty_label)

        self.doc_table = QTableWidget()
        self.doc_table.setObjectName("documentsTable")
        self.doc_table.setColumnCount(6)
        self.doc_table.setHorizontalHeaderLabels([
            self.tr("Nom Document"), self.tr("Type"), self.tr("Langue"),
            self.tr("Date Création"), self.tr("Fichier"), self.tr("Actions") # "Fichier Original" -> "Fichier"
        ])

        header_style = """
            QHeaderView::section {
                background-color: #4a5568; /* Equivalent de Tailwind bg-gray-700 */
                color: white;
                padding: 6px; /* Augmentation du padding */
                border: 1px solid #ddd;
                font-weight: bold;
                font-size: 9pt; /* Taille de police légèrement augmentée */
            }
        """
        self.doc_table.horizontalHeader().setStyleSheet(header_style)
        self.doc_table.verticalHeader().setVisible(False)
        self.doc_table.setAlternatingRowColors(True)
        self.doc_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.doc_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.doc_table.setSortingEnabled(True) # Activer le tri

        # Modes de redimensionnement des colonnes (ajustés pour une meilleure flexibilité)
        self.doc_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch) # Nom Document
        self.doc_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents) # Type
        self.doc_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents) # Langue
        self.doc_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents) # Date Création
        self.doc_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Interactive) # Fichier (Interactive pour que l'utilisateur puisse ajuster)
        self.doc_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents) # Actions
        self.doc_table.setColumnWidth(4, 180) # Largeur initiale pour Fichier

        docs_layout.addWidget(self.doc_table)

        # Barre d'actions sous le tableau
        doc_actions_bar = QHBoxLayout()
        doc_actions_bar.setSpacing(10)

        self.main_add_doc_action_btn = QPushButton("➕ " + self.tr("Ajouter/Générer Document"))
        self.main_add_doc_action_btn.setToolTip(self.tr("Options pour ajouter ou générer un nouveau document"))
        self.main_add_doc_action_btn.setObjectName("primaryButton")
        self.main_add_doc_action_btn.clicked.connect(self._open_add_document_menu)
        doc_actions_bar.addWidget(self.main_add_doc_action_btn)

        self.compile_pdf_btn_tab = QPushButton("📄 " + self.tr("Compiler PDF")) # Icon changed
        self.compile_pdf_btn_tab.setObjectName("secondaryButton")
        self.compile_pdf_btn_tab.setToolTip(self.tr("Compiler plusieurs documents PDF en un seul"))
        self.compile_pdf_btn_tab.clicked.connect(self.open_compile_pdf_dialog_from_parent) # Connects to parent's method
        doc_actions_bar.addWidget(self.compile_pdf_btn_tab)

        doc_actions_bar.addStretch()
        docs_layout.addLayout(doc_actions_bar)

        self._load_order_filters()

    def _open_add_document_menu(self):
        # This method will be implemented in the next step.
        # It will open a dialog or QMenu with options:
        # - Ajouter un document simple
        # - Importer un document existant
        # - Générer un document via modèle

        if not self.main_add_doc_action_btn: # Should not happen
            logging.error("main_add_doc_action_btn not initialized.")
            return

        menu = QMenu(self)

        action_simple = menu.addAction(self.tr("Ajouter un document simple"))
        action_simple.triggered.connect(self._handle_add_simple_document_action) # Placeholder

        action_import = menu.addAction(self.tr("Importer un document existant"))
        action_import.triggered.connect(self._handle_import_document_action) # Placeholder, will likely call self.add_document

        action_generate = menu.addAction(self.tr("Générer un document via modèle"))
        action_generate.triggered.connect(self._handle_generate_via_template_action) # Placeholder, will likely call self.add_document_from_template_action

        # Show the menu below the button
        button_pos = self.main_add_doc_action_btn.mapToGlobal(self.main_add_doc_action_btn.rect().bottomLeft())
        menu.exec_(button_pos)

    def _handle_add_simple_document_action(self):
        logging.info("Action: Ajouter un document simple selected.")
        # TODO: Implement logic for adding a simple document
        # This will likely involve a dialog to input document details (name, description).
        # The document needs to be associated with the current client_id and potentially a commande_id.
        # For a "simple" document, it might not have a physical file initially, or allow a generic upload.

        client_id = self.client_info.get("client_id")
        if not client_id:
            self.notify(self.tr("Erreur"), self.tr("ID Client non trouvé."), type='ERROR')
            return

        doc_name, ok = QInputDialog.getText(self, self.tr("Nom du Document Simple"), self.tr("Entrez le nom pour le document simple:"))
        if not ok or not doc_name.strip():
            self.notify(self.tr("Annulé"), self.tr("Ajout de document simple annulé."), type='INFO')
            return

        doc_name = doc_name.strip()

        # Optional: Ask for notes/description for this simple document
        doc_notes, notes_ok = QInputDialog.getMultiLineText(self, self.tr("Notes (Optionnel)"),
                                                            self.tr("Entrez des notes ou une description pour '{0}':").format(doc_name))
        if not notes_ok: # User cancelled notes input, but proceed with document name
            doc_notes = ""

        order_identifier = None
        current_order_data = self.doc_order_filter_combo.currentData()
        if current_order_data not in ["ALL", "NONE"] and current_order_data is not None:
            order_identifier = current_order_data

        # For a "simple" document, file_path_relative and file_name_on_disk might be None or specific placeholders
        # Language can be set to a default or also asked. For now, let's assume a default or None.
        # Let's ask for language for consistency

        # Use the same language selection logic as in add_document
        language_items_for_dialog_simple = [f"{self.tr(name)} ({code})" for code, name in SUPPORTED_LANGUAGES.items()]
        default_lang_code_simple = 'fr' # Ou une autre logique pour le défaut
        default_idx_simple = 0
        for i, item_str in enumerate(language_items_for_dialog_simple):
            if f"({default_lang_code_simple})" in item_str:
                default_idx_simple = i
                break

        selected_lang_item_str_simple, lang_ok = QInputDialog.getItem(
            self, self.tr("Sélectionner la langue"), self.tr("Langue du document '{0}':").format(doc_name),
            language_items_for_dialog_simple, default_idx_simple, False
        )

        selected_doc_language_code = default_lang_code_simple # Default if user cancels or error

        if lang_ok and selected_lang_item_str_simple:
            try:
                # Extract code from "Name (code)" format
                start_idx = selected_lang_item_str_simple.rfind('(')
                end_idx = selected_lang_item_str_simple.rfind(')')
                if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
                     temp_code = selected_lang_item_str_simple[start_idx+1:end_idx]
                else:
                     raise ValueError("Format de l'item de langue inattendu.")

                if temp_code not in SUPPORTED_LANGUAGES:
                    raise ValueError(f"Code langue '{temp_code}' non supporté.")
                selected_doc_language_code = temp_code
            except ValueError as e:
                self.notify(self.tr("Erreur de Langue"), f"{str(e)}. Utilisation de '{default_lang_code_simple}'.", type='WARNING')
                # selected_doc_language_code reste la valeur par défaut
        elif not lang_ok : # User cancelled dialog
             self.notify(self.tr("Langue par Défaut"), self.tr("Langue par défaut '{0}' sera utilisée.").format(default_lang_code_simple), type='INFO')
             # selected_doc_language_code reste la valeur par défaut


        doc_db_data = {
            "client_id": client_id,
            "document_name": doc_name,
            "file_name_on_disk": None, # No physical file for a "simple" document initially
            "file_path_relative": None,
            "document_type_generated": "NOTE", # Or "SIMPLE_DOCUMENT", "TEXT_NOTE"
            "language_code": selected_doc_language_code, # Utiliser le code extrait/par défaut
            "source_template_id": None,
            "order_identifier": order_identifier,
            "user_id": self.current_user_id,
            "notes": doc_notes.strip() if doc_notes else None, # Store notes
            "version_tag": "1.0"
        }

        try:
            new_doc_id = client_documents_crud.add_client_document(doc_db_data)
            if new_doc_id:
                self.notify(self.tr("Succès"), self.tr("Document simple '{0}' ajouté.").format(doc_name), type='SUCCESS')
                self.populate_doc_table() # Refresh table
            else:
                self.notify(self.tr("Erreur DB"), self.tr("Échec de l'enregistrement du document simple."), type='ERROR')
        except Exception as e:
            logging.error(f"Error adding simple document: {e}", exc_info=True)
            self.notify(self.tr("Erreur Inconnue"), str(e), type='CRITICAL')


    def _handle_import_document_action(self):
        logging.info("Action: Importer un document existant selected.")
        # This can reuse the existing self.add_document() method which handles file import.
        self.add_document() # self.add_document already handles file dialog and DB record.

    def _handle_generate_via_template_action(self):
        logging.info("Action: Générer un document via modèle selected.")
        # Appel de la nouvelle méthode qui gère le choix pour les HTML
        self.add_document_from_template_action_with_choice()


    def add_document_from_template_action_with_choice(self):
        if not self.CreateDocumentDialog: # CreateDocumentDialog est une référence à la classe du dialogue
            self.notify(self.tr("Erreur"), self.tr("Le composant de création de document n'est pas chargé."), type='CRITICAL')
            return

        current_order_identifier = self.doc_order_filter_combo.currentData()
        if current_order_identifier == "ALL" or current_order_identifier == "NONE":
            current_order_identifier = None

        # self.app_root_dir doit être correctement initialisé dans __init__ de DocumentsTab
        if not hasattr(self, 'app_root_dir') or not self.app_root_dir:
            logging.error("DocumentsTab: app_root_dir non initialisé. Impossible de continuer.")
            self.notify(self.tr("Erreur Configuration"), self.tr("Chemin racine de l'application non configuré."), type='CRITICAL')
            return

        create_doc_dialog = self.CreateDocumentDialog(
            client_info=self.client_info,
            config=self.config,
            app_root_dir=self.app_root_dir, # Passer app_root_dir
            current_user_id=self.current_user_id,
            order_identifier=current_order_identifier,
            parent=self
        )

        if create_doc_dialog.exec_() == QDialog.Accepted:
            self.populate_doc_table()
            # Les notifications sont maintenant plus granulaires et gérées par CreateDocumentDialog
            # ou basées sur l'action retournée.
            action_performed = create_doc_dialog.get_action_performed()
            # Importer les constantes ACTION_COPY_RAW, ACTION_GENERATE_DIRECT
            # from dialogs import ACTION_COPY_RAW, ACTION_GENERATE_DIRECT # Ou les définir localement/globalement

            # Pour éviter un import cyclique potentiel si dialogs.__init__ importe depuis DocumentsTab
            # On peut utiliser les chaînes directement ou s'assurer que les constantes sont accessibles
            # d'une manière non cyclique (par exemple, un fichier constants.py).
            # Pour l'instant, utilisons les chaînes directes, en supposant qu'elles correspondent.
            ACTION_COPY_RAW_CONST = "copy_raw"
            ACTION_GENERATE_DIRECT_CONST = "generate_direct"

            if action_performed == ACTION_COPY_RAW_CONST:
                self.notify(self.tr("Succès"), self.tr("Modèle HTML brut copié avec succès dans le dossier client."), type='SUCCESS')
            elif action_performed == ACTION_GENERATE_DIRECT_CONST:
                 self.notify(self.tr("Succès"), self.tr("Document généré avec succès à partir du modèle."), type='SUCCESS')
            # else: l'utilisateur a peut-être annulé le dialogue de choix ou le dialogue principal.
            # Aucune notification de succès spécifique n'est nécessaire si rien n'a été fait.

    def _load_order_filters(self):
        self.doc_order_filter_combo.blockSignals(True)
        current_selection = self.doc_order_filter_combo.currentData()
        self.doc_order_filter_combo.clear()
        self.doc_order_filter_combo.addItem(self.tr("Toutes les Commandes"), "ALL")
        self.doc_order_filter_combo.addItem(self.tr("Documents Généraux (Aucune Commande)"), "NONE")

        client_id = self.client_info.get('client_id')
        if client_id:
            try:
                projects = projects_crud.get_projects_by_client_id(client_id)
                fetched_order_identifiers = []
                if projects:
                    seen_identifiers = set()
                    for project in projects:
                        identifier = project.get('project_identifier') or project.get('project_name')
                        if identifier and identifier not in seen_identifiers:
                            fetched_order_identifiers.append(identifier)
                            seen_identifiers.add(identifier)
                if fetched_order_identifiers:
                    for identifier_str in sorted(list(set(fetched_order_identifiers))): # Sort and unique
                        if identifier_str and identifier_str.strip():
                             self.doc_order_filter_combo.addItem(identifier_str, identifier_str)
            except Exception as e:
                logging.error(f"Error loading order filters for documents: {e}", exc_info=True)

        index_to_select = self.doc_order_filter_combo.findData(current_selection)
        if index_to_select != -1:
            self.doc_order_filter_combo.setCurrentIndex(index_to_select)
        elif self.doc_order_filter_combo.count() > 0:
            self.doc_order_filter_combo.setCurrentIndex(0) # Default to "ALL"

        self.doc_order_filter_combo.blockSignals(False)

    def populate_doc_table(self):
        if self._is_populating_docs:
            return
        self._is_populating_docs = True
        self.doc_table.setRowCount(0)
        QApplication.setOverrideCursor(Qt.WaitCursor)

        client_id = self.client_info.get("client_id")
        if not client_id:
            QApplication.restoreOverrideCursor()
            self._is_populating_docs = False
            return

        selected_order_identifier = self.doc_order_filter_combo.currentData()
        selected_language = self.doc_language_filter_combo.currentData()
        selected_doc_type = self.doc_type_filter_combo.currentData()

        filters = {"client_id": client_id}
        if selected_order_identifier not in ["ALL", "NONE"]:
            filters["order_identifier"] = selected_order_identifier
        elif selected_order_identifier == "NONE":
            filters["order_identifier_is_null"] = True
        if selected_language != "ALL":
            filters["language_code"] = selected_language
        if selected_doc_type != "ALL":
            filters["document_type_generated"] = selected_doc_type

        crud_filters = {k: v for k, v in filters.items() if k != 'client_id'}

        try:
            documents = client_documents_crud.get_documents_for_client(client_id=client_id, filters=crud_filters)
            if not documents:
                self.documents_empty_label.show()
                self.doc_table.hide()
            else:
                self.documents_empty_label.hide()
                self.doc_table.show()
                self.doc_table.setRowCount(len(documents))
                for row_idx, doc in enumerate(documents):
                    doc_id = doc.get("document_id")
                    doc_name_item = QTableWidgetItem(doc.get("document_name"))
                    doc_name_item.setData(Qt.UserRole, doc_id)
                    self.doc_table.setItem(row_idx, 0, doc_name_item)
                    self.doc_table.setItem(row_idx, 1, QTableWidgetItem(doc.get("document_type_generated")))
                    self.doc_table.setItem(row_idx, 2, QTableWidgetItem(doc.get("language_code")))

                    created_at_str = doc.get("created_at")
                    date_display = self.tr("N/A")
                    if created_at_str:
                        try:
                            dt_obj = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                            date_display = dt_obj.strftime('%Y-%m-%d %H:%M')
                        except ValueError: date_display = created_at_str
                    self.doc_table.setItem(row_idx, 3, QTableWidgetItem(date_display))

                    original_file_path = doc.get("file_path_original")
                    if original_file_path:
                        abs_original_path = os.path.join(self.app_root_dir, original_file_path) if not os.path.isabs(original_file_path) else original_file_path
                        link_widget = QLabel(f"<a href='file:///{abs_original_path}'>{os.path.basename(original_file_path)}</a>")
                        link_widget.setOpenExternalLinks(True)
                        self.doc_table.setCellWidget(row_idx, 4, link_widget)
                    else:
                        self.doc_table.setItem(row_idx, 4, QTableWidgetItem(self.tr("N/A")))

                    actions_widget = QWidget()
                    actions_layout = QHBoxLayout(actions_widget)
                    actions_layout.setContentsMargins(2,2,2,2); actions_layout.setSpacing(3)

                    can_manage = self.can_manage_documents_permission

                    file_path_relative = doc.get("file_path_relative")
                    # Construct absolute path for local file operations
                    client_base_folder_path = self.client_info.get("base_folder_path", self.client_info.get("default_base_folder_path", ""))
                    base_folder_abs = os.path.join(self.app_root_dir, client_base_folder_path)
                    full_file_path = os.path.join(base_folder_abs, file_path_relative) if base_folder_abs and file_path_relative else None


                    if full_file_path and os.path.exists(full_file_path):
                        doc_type = doc.get("document_type_generated")

                        # Bouton Modifier pour HTML, EDITABLE_HTML et XLSX (si permission)
                        if doc_type in ["HTML", "EDITABLE_HTML"] and can_manage:
                            edit_btn = QPushButton("✏️")
                            edit_btn.setToolTip(self.tr("Modifier HTML"))
                            edit_btn.setProperty("class", "tableActionButton")
                            edit_btn.clicked.connect(lambda checked, p=full_file_path, d_id=doc_id: self.handle_edit_html_action(p, d_id))
                            actions_layout.addWidget(edit_btn)
                        elif doc_type == "XLSX" and can_manage:
                            edit_btn = QPushButton("✏️")
                            edit_btn.setToolTip(self.tr("Modifier Excel"))
                            edit_btn.setProperty("class", "tableActionButton")
                            edit_btn.clicked.connect(lambda checked, p=full_file_path, d_id=doc_id: self.handle_edit_excel_action(p, d_id))
                            actions_layout.addWidget(edit_btn)

                        # Bouton Générer Document Final pour EDITABLE_HTML (si permission)
                        if doc_type == "EDITABLE_HTML" and can_manage:
                            generate_final_btn = QPushButton("📄") # Icone "générer"
                            generate_final_btn.setToolTip(self.tr("Générer Document Final (PDF/HTML)"))
                            generate_final_btn.setProperty("class", "tableActionButton") # ou "primaryButtonTable" si on veut le mettre en évidence
                            generate_final_btn.clicked.connect(
                                lambda checked, d_id=doc_id, p=full_file_path, src_tpl_id=doc.get("source_template_id"):
                                self.handle_generate_from_raw_html_action(d_id, p, src_tpl_id)
                            )
                            actions_layout.addWidget(generate_final_btn)

                        # Bouton Ouvrir/Visualiser
                        view_btn = QPushButton("👁️")
                        view_btn.setToolTip(self.tr("Ouvrir Document"))
                        view_btn.setProperty("class", "tableActionButton")
                        view_btn.clicked.connect(lambda checked, p=full_file_path, d_id=doc_id: self._handle_view_document_action(p, d_id))
                        actions_layout.addWidget(view_btn)

                    if can_manage:
                        # Bouton Nouvelle Version (si applicable)
                        if doc.get("source_template_id") and doc_type != "EDITABLE_HTML": # Pas de "nouvelle version" pour un HTML brut éditable lui-même, mais pour ses enfants générés.
                                                                                         # Ou si on veut versionner l'EDITABLE_HTML lui-même, on enlève la condition doc_type != "EDITABLE_HTML"
                            version_btn = QPushButton("📋")
                            version_btn.setToolTip(self.tr("Créer une nouvelle version à partir du même modèle"))
                            version_btn.setProperty("class", "tableActionButton")
                            version_btn.clicked.connect(lambda checked, old_id=doc_id, t_id=doc.get("source_template_id"): self.handle_create_new_version_clicked(old_id, t_id))
                            actions_layout.addWidget(version_btn)

                        # Bouton Supprimer
                        delete_btn = QPushButton("🗑️")
                        delete_btn.setToolTip(self.tr("Supprimer Document"))
                        delete_btn.setProperty("class", "dangerButtonTable")
                        delete_btn.clicked.connect(lambda checked, d_id=doc_id, p=full_file_path: self.delete_client_document_entry(d_id, p))
                        actions_layout.addWidget(delete_btn)

                    # Bouton "Convertir en Facture" pour les Proformas PDF
                    if doc.get("document_type_generated", "").endswith("_PDF") and "PROFORMA" in doc.get("document_type_generated", "") and can_manage:
                        convert_btn = QPushButton("↪️")
                        convert_btn.setToolTip(self.tr("Convertir en Facture"))
                        convert_btn.setProperty("class", "tableActionButton")
                        convert_btn.clicked.connect(lambda checked, doc_id_proforma=doc_id: self.handle_convert_proforma_to_invoice(doc_id_proforma))
                        actions_layout.addWidget(convert_btn)

                    actions_layout.addStretch()
                    self.doc_table.setCellWidget(row_idx, 5, actions_widget)
                self.doc_table.resizeRowsToContents()
        except Exception as e:
            logging.error(f"Error populating documents table: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Chargement"), self.tr("Impossible de charger les documents: {0}").format(str(e)))
        finally:
            QApplication.restoreOverrideCursor()
            self._is_populating_docs = False

    def add_document(self):
        language_items_for_dialog = [f"{self.tr(name)} ({code})" for code, name in SUPPORTED_LANGUAGES.items()]
        default_lang_code = 'fr' # Ou une autre logique pour le défaut
        default_idx = 0
        for i, item_str in enumerate(language_items_for_dialog):
            if f"({default_lang_code})" in item_str: # Cherche "(fr)" par exemple

                default_idx = i
                break

        selected_lang_item_str, ok = QInputDialog.getItem(
            self, self.tr("Sélectionner la langue"), self.tr("Langue du document:"),
            language_items_for_dialog, default_idx, False
        )

        if not ok or not selected_lang_item_str:
            self.notify(self.tr("Annulé"), self.tr("L'opération d'ajout de document a été annulée."), type='INFO')
            return

        selected_doc_language_code = ""
        try:

            start_idx = selected_lang_item_str.rfind('(')
            end_idx = selected_lang_item_str.rfind(')')
            if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
                 selected_doc_language_code = selected_lang_item_str[start_idx+1:end_idx]
            else: # Should not happen if items are formatted correctly
                 raise ValueError("Format de l'item de langue inattendu.")


            if selected_doc_language_code not in SUPPORTED_LANGUAGES:
                raise ValueError(f"Code langue '{selected_doc_language_code}' non supporté.")
        except ValueError as e:
            self.notify(self.tr("Erreur de Langue"), str(e), type='ERROR')
            return

        clients_root_dir = os.path.join(self.app_root_dir, self.config.get("clients_dir", "clients"))
        initial_dir = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation) or clients_root_dir

        selected_file_path, _ = QFileDialog.getOpenFileName(
            self, self.tr("Sélectionner un document"), initial_dir, self.tr("Tous les fichiers (*.*)")
        )

        if selected_file_path:
            try:
                client_relative_base_path = self.client_info.get("base_folder_path") or self.client_info.get("default_base_folder_path")
                if not client_relative_base_path:
                    self.notify(self.tr("Erreur Dossier Client"), self.tr("Le chemin du dossier de base du client n'est pas configuré."), type='ERROR')
                    return

                client_abs_base_path = os.path.join(self.app_root_dir, client_relative_base_path)
                target_lang_dir_abs = os.path.join(client_abs_base_path, selected_doc_language_code)

                target_lang_dir_abs = os.path.join(client_abs_base_path, selected_doc_language_code) # Utiliser le code extrait

                # Handle order identifier for subfolder structure

                order_identifier = None
                current_order_data = self.doc_order_filter_combo.currentData()
                safe_order_subfolder = None # Initialiser safe_order_subfolder
                if current_order_data not in ["ALL", "NONE"] and current_order_data is not None:
                    order_identifier = current_order_data
                    safe_order_subfolder = order_identifier.replace(':', '_').replace('/', '_').replace('\\', '_').replace(' ', '_')
                    target_lang_dir_abs = os.path.join(client_abs_base_path, safe_order_subfolder, selected_doc_language_code) # Utiliser le code extrait


                os.makedirs(target_lang_dir_abs, exist_ok=True)
                file_name = os.path.basename(selected_file_path)
                target_file_path_abs = os.path.join(target_lang_dir_abs, file_name)

                if os.path.exists(target_file_path_abs):
                    reply = QMessageBox.question(
                        self, self.tr("Fichier Existant"),
                        self.tr("Un fichier du même nom existe déjà. Voulez-vous le remplacer?"),
                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                    )
                    if reply == QMessageBox.No: return

                shutil.copy(selected_file_path, target_file_path_abs)

                client_id = self.client_info.get("client_id")
                ext = os.path.splitext(file_name)[1].lower()
                doc_type_map = {".html": "HTML", ".pdf": "PDF", ".xlsx": "XLSX", ".docx": "DOCX"}
                document_type_generated = doc_type_map.get(ext, ext.upper().replace(".", "") or "OTHER")

                # File path relative to client's base folder
                file_path_relative_to_client_base = os.path.join(
                    (os.path.join(safe_order_subfolder, selected_doc_language_code) if order_identifier else selected_doc_language_code), # Utiliser le code extrait
                    file_name
                )


                doc_db_data = {
                    "client_id": client_id, "document_name": file_name,
                    "file_name_on_disk": file_name,
                    "file_path_relative": file_path_relative_to_client_base,
                    "document_type_generated": document_type_generated,
                    "language_code": selected_doc_language_code, "source_template_id": None, # Utiliser le code extrait

                    "order_identifier": order_identifier, "user_id": self.current_user_id,
                    "notes": None, "version_tag": "1.0"
                }
                new_doc_id = client_documents_crud.add_client_document(doc_db_data)
                if new_doc_id:
                    self.notify(self.tr("Succès"), self.tr("Document '{0}' importé et enregistré.").format(file_name), type='SUCCESS')
                    self.populate_doc_table()
                else:
                    self.notify(self.tr("Erreur DB"), self.tr("Échec de l'enregistrement DB du document importé."), type='ERROR')

            except Exception as e:
                logging.error(f"Error adding document: {e}", exc_info=True)
                self.notify(self.tr("Erreur Importation"), str(e), type='CRITICAL')

    def open_create_docs_dialog_from_parent(self):
        if self.parent_widget and hasattr(self.parent_widget, 'open_create_docs_dialog'):
            self.parent_widget.open_create_docs_dialog()
        else:
            logging.error("DocumentsTab: Parent widget or open_create_docs_dialog method not found.")
            self.notify(self.tr("Erreur"), self.tr("Impossible d'ouvrir le dialogue de création de document."), type='ERROR')

    def add_document_from_template_action(self):
        if not self.CreateDocumentDialog:
            self.notify(self.tr("Erreur"), self.tr("Le composant de création de document n'est pas chargé."), type='CRITICAL')
            return

        current_order_identifier = self.doc_order_filter_combo.currentData()
        if current_order_identifier == "ALL" or current_order_identifier == "NONE":
            current_order_identifier = None # Ne pas passer "ALL" ou "NONE" comme identifiant de commande

        dialog = self.CreateDocumentDialog(
            client_info=self.client_info,
            config=self.config,
            current_user_id=self.current_user_id,
            order_identifier=current_order_identifier, # Passer l'identifiant de commande
            parent=self
        )
        if dialog.exec_() == QDialog.Accepted:
            self.populate_doc_table()
            # Notification de succès gérée dans CreateDocumentDialog ou ici si nécessaire

    def open_compile_pdf_dialog_from_parent(self):
        if self.parent_widget and hasattr(self.parent_widget, 'open_compile_pdf_dialog'):
            self.parent_widget.open_compile_pdf_dialog()
        else:
            logging.error("DocumentsTab: Parent widget or open_compile_pdf_dialog method not found.")
            self.notify(self.tr("Erreur"), self.tr("Impossible d'ouvrir le dialogue de compilation PDF."), type='ERROR')

    def handle_edit_html_action(self, file_path, document_id):
        # S'assurer que HtmlEditor est importé
        from gui.widgets.html_editor import HtmlEditor
        if file_path and os.path.exists(file_path):
            # Le document_id passé ici est celui de l'enregistrement ClientDocument
            # HtmlEditor peut l'utiliser pour des opérations spécifiques si nécessaire (ex: mise à jour de notes)
            editor = HtmlEditor(file_path=file_path, client_data={"document_id": document_id}, parent=self)
            if editor.exec_() == QDialog.Accepted:
                self.populate_doc_table()
                self.notify(self.tr("HTML Modifié"), self.tr("Le document HTML a été sauvegardé."), type='SUCCESS')
        else:
            self.notify(self.tr("Fichier Introuvable"), self.tr("Le fichier HTML est introuvable:\n{0}").format(file_path), type='WARNING')

    def handle_edit_excel_action(self, file_path, document_id):
        # S'assurer que ExcelEditor est importé
        # from excel_editor import ExcelEditor # Déjà importé en haut du fichier
        if file_path and os.path.exists(file_path):
            editor = ExcelEditor(file_path, document_id, self)
            if editor.exec_() == QDialog.Accepted:
                self.populate_doc_table()
                self.notify(self.tr("Excel Modifié"), self.tr("Le document Excel a été sauvegardé."), type='SUCCESS')
        else:
            self.notify(self.tr("Fichier Introuvable"), self.tr("Le fichier Excel est introuvable:\n{0}").format(file_path), type='WARNING')

    def _handle_view_document_action(self, file_path, document_id):
        if file_path and os.path.exists(file_path):
            # Récupérer le type de document pour vérifier si c'est un PDF
            doc_details = client_documents_crud.get_document_by_id(document_id)
            doc_type = doc_details.get("document_type_generated", "").upper() if doc_details else ""

            if doc_type == "PDF" or file_path.lower().endswith(".pdf"):
                if self._should_use_internal_pdf_viewer():
                    # C'est un PDF, et la préférence est d'utiliser la visionneuse interne
                    try:
                        viewer = PdfViewerWidget(file_path, self) # self pour parent
                        # Connecter le signal de sauvegarde à une méthode de DocumentsTab
                        viewer.documentSavedAsNewVersion.connect(
                            lambda orig_path, new_path, doc_id=document_id:
                            self._handle_new_pdf_version_saved(doc_id, orig_path, new_path)
                        )
                        viewer.exec_() # Ouvre en tant que dialogue modal
                    except Exception as e:
                        logging.error(f"Erreur lors de l'ouverture de PdfViewerWidget pour {file_path}: {e}", exc_info=True)
                        self.notify(self.tr("Erreur Visionneuse PDF"),
                                    self.tr("Impossible d'ouvrir le PDF dans la visionneuse interne: {0}.\nTentative avec l'application externe.").format(str(e)),
                                    type='ERROR')
                        # Fallback vers l'ouverture externe en cas d'erreur avec la visionneuse interne
                        QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
                else:
                    # La préférence est d'utiliser l'application externe
                    QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
            else:
                # Pour les autres types, comportement normal
                QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
        else:
            self.notify(self.tr("Fichier Introuvable"), self.tr("Le document est introuvable:\n{0}").format(file_path), type='WARNING')

    def _should_use_internal_pdf_viewer(self) -> bool:
        # TODO: Lire cette préférence depuis les paramètres globaux de l'application.
        # Pour l'instant, on code en dur pour activer la visionneuse interne.
        # Mettre à False pour tester le comportement avec visionneuse externe.
        # Exemple:
        # app_settings = self.config.get_application_settings()
        # return app_settings.get("use_internal_pdf_viewer", True)
        return True # Par défaut, utiliser la visionneuse interne

    def _handle_new_pdf_version_saved(self, original_document_id: str, original_document_path: str, new_document_path: str):
        """
        Gère la notification qu'une nouvelle version d'un PDF annoté a été sauvegardée.
        original_document_id: L'ID en base de données du document original.
        original_document_path: Le chemin système du document original.
        new_document_path: Le chemin système vers le nouveau fichier PDF sauvegardé.
        """
        logging.info(
            f"Nouvelle version de document PDF sauvegardée. "
            f"Original ID: {original_document_id}, Original Path: {original_document_path}, Nouveau Path: {new_document_path}"
        )

        # Pour l'instant, afficher un message à l'utilisateur.
        # L'étape suivante serait d'ajouter ce nouveau document à la base de données
        # et de rafraîchir la table des documents.

        self.notify(
            self.tr("Nouvelle Version Enregistrée"),
            self.tr("Une nouvelle version du document a été enregistrée sous:\n{0}\n\n"
                    "L'intégration de ce nouveau fichier dans la liste des documents du client est une prochaine étape."
                    ).format(new_document_path),
            type='INFO'
        )

        # TODO:
        # 1. Déterminer le nom du document, type, langue etc. pour la nouvelle entrée DB.
        #    On pourrait se baser sur le document original.
        # 2. Construire le file_path_relative pour la nouvelle entrée.
        # 3. Appeler client_documents_crud.add_client_document().
        # 4. self.populate_doc_table() pour rafraîchir.
        try:
            original_doc_details = client_documents_crud.get_document_by_id(original_document_id)
            if not original_doc_details:
                self.notify(self.tr("Erreur"), self.tr("Impossible de récupérer les détails du document original pour créer la nouvelle version en base de données."), type='ERROR')
                return

            new_doc_name = os.path.basename(new_document_path)

            # Calculer file_path_relative
            # On suppose que new_document_path est un chemin absolu.
            # On a besoin du chemin de base des clients et du chemin de base de CE client.
            clients_root_abs = os.path.join(self.app_root_dir, self.config.get("clients_dir", "clients"))
            # Le new_document_path devrait être DANS un sous-dossier de clients_root_abs.
            # Si le PdfViewerWidget sauvegarde dans le même dossier que l'original (ou un sous-dossier prévisible),
            # on pourrait utiliser le base_folder_path du client.

            client_base_folder_abs = ""
            if self.client_info.get("base_folder_path"): # Chemin relatif au dossier 'clients'
                 client_base_folder_abs = os.path.join(clients_root_abs, self.client_info.get("base_folder_path"))
            elif self.client_info.get("default_base_folder_path"): # Chemin relatif à app_root_dir
                 client_base_folder_abs = os.path.join(self.app_root_dir, self.client_info.get("default_base_folder_path"))
            else:
                self.notify(self.tr("Erreur Configuration"), self.tr("Chemin du dossier client non trouvé. Impossible de déterminer le chemin relatif."), type="ERROR")
                return

            if not new_document_path.startswith(client_base_folder_abs):
                # Ceci est un problème si le fichier est sauvegardé en dehors du dossier attendu pour le client.
                # Pour l'instant, on va essayer de faire un relpath, mais il faut s'assurer que la sauvegarde se fait au bon endroit.
                # Idéalement, PdfViewerWidget devrait sauvegarder dans un sous-dossier de client_base_folder_abs.
                # On va supposer que `new_document_path` est DANS `client_base_folder_abs` ou un de ses sous-dossiers.
                # Pour l'instant, on calcule par rapport à app_root_dir, puis on ajuste.
                # Le file_path_relative dans la BDD est relatif au dossier racine de l'application pour les documents clients
                # Ex: clients/client_xyz/FR/document.pdf
                # Donc, on prend new_document_path et on le rend relatif à self.app_root_dir

                # Le chemin stocké en BDD est relatif à app_root_dir, mais doit commencer par le "clients_dir"
                # ex: "clients/client_name_country_id/lang/file.pdf"
                # new_document_path est absolu.
                # self.client_info.get("base_folder_path") est relatif à self.config.get("clients_dir")
                # ex: "client_name_country_id"
                # client_base_folder_path dans la DB pour un doc est relatif à la base du client.
                # ex: "fr/commande_xyz/doc.pdf"
                # Donc, new_document_path devrait être dans os.path.join(self.app_root_dir, self.client_info.get("default_base_folder_path"), ...)

                # Si new_document_path est /abs/path/to/app_root/clients/client_folder/lang/file.pdf
                # Et client_base_folder_abs est /abs/path/to/app_root/clients/client_folder/
                # Alors le file_path_relative pour la DB est lang/file.pdf
                file_path_relative_for_db = os.path.relpath(new_document_path, client_base_folder_abs)

            else: # Si new_document_path est déjà relatif au dossier client (moins probable ici)
                 file_path_relative_for_db = new_document_path


            new_version_tag = original_doc_details.get("version_tag", "1.0")
            try:
                # Essayer d'incrémenter la version si c'est un float ou int
                version_parts = new_version_tag.split('.')
                if len(version_parts) > 0 and version_parts[-1].isdigit():
                    version_parts[-1] = str(int(version_parts[-1]) + 1)
                    new_version_tag = ".".join(version_parts)
                else: # Sinon, ajouter un suffixe
                    new_version_tag += "_annotated"
            except:
                new_version_tag += "_annotated"


            new_doc_data = {
                "client_id": original_doc_details.get("client_id"),
                "document_name": new_doc_name,
                "file_name_on_disk": new_doc_name,
                "file_path_relative": file_path_relative_for_db,
                "document_type_generated": "PDF_ANNOTATED", # Ou juste PDF, ou un type spécifique
                "language_code": original_doc_details.get("language_code"),
                "source_template_id": original_doc_details.get("source_template_id"), # Peut-être None si c'était un import
                "order_identifier": original_doc_details.get("order_identifier"),
                "user_id": self.current_user_id,
                "notes": self.tr("Version annotée de '{0}'. Document original ID: {1}.").format(
                    original_doc_details.get("document_name"), original_document_id
                ),
                "parent_document_id": original_document_id, # Lier à l'original
                "version_tag": new_version_tag
            }

            new_doc_id = client_documents_crud.add_client_document(new_doc_data)
            if new_doc_id:
                self.notify(self.tr("Nouvelle Version Enregistrée"),
                            self.tr("La nouvelle version annotée '{0}' a été ajoutée à la base de données.").format(new_doc_name),
                            type='SUCCESS')
                self.populate_doc_table() # Rafraîchir la table
            else:
                self.notify(self.tr("Erreur Base de Données"),
                            self.tr("Échec de l'enregistrement de la nouvelle version en base de données."), type='ERROR')

        except Exception as e:
            logging.error(self.tr("Erreur lors de la gestion de la nouvelle version PDF sauvegardée: {0}").format(str(e)), exc_info=True)
            self.notify(self.tr("Erreur Inattendue"),
                        self.tr("Une erreur inattendue est survenue lors de l'enregistrement de la nouvelle version en base de données."), type='CRITICAL')


    def handle_create_new_version_clicked(self, old_document_id, source_template_id):
        if not self.client_info or not self.client_info.get('client_id'):
                try :
                    viewer.exec_() # Ouvre en tant que dialogue modal
                except Exception as e:
                    logging.error(f"Erreur lors de l'ouverture de PdfViewerWidget pour {file_path}: {e}", exc_info=True)
                    self.notify(self.tr("Erreur Visionneuse PDF"),
                                self.tr("Impossible d'ouvrir le PDF dans la visionneuse interne: {0}.\nTentative avec l'application externe.").format(str(e)),
                                type='ERROR')
                    # Fallback vers l'ouverture externe en cas d'erreur avec la visionneuse interne
                    QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
            # else:
            #     # Pour les autres types, comportement normal
            #     QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
        else:
            self.notify(self.tr("Fichier Introuvable"), self.tr("Le document est introuvable:\n{0}").format(file_path), type='WARNING')

    def handle_create_new_version_clicked(self, old_document_id, source_template_id):
        if not self.client_info or not self.client_info.get('client_id'):
            self.notify(self.tr("Erreur Client"), self.tr("Informations client non disponibles."), type='WARNING')
            return
        if not old_document_id or not source_template_id:
            self.notify(self.tr("Données Manquantes"), self.tr("ID du document original ou ID du modèle source manquant."), type='WARNING')
            return

        if not self.CreateDocumentDialog:
            logging.error("CreateDocumentDialog is not available in DocumentsTab.")
            self.notify(self.tr("Erreur Composant"), self.tr("Le composant de création de document n'est pas chargé."), type='CRITICAL')
            return

        # S'assurer que app_root_dir est passé à CreateDocumentDialog
        dialog = self.CreateDocumentDialog(
            client_info=self.client_info,
            config=self.config,
            app_root_dir=self.app_root_dir, # Ajout de app_root_dir
            current_user_id=self.current_user_id,
            parent=self,
            template_data={'template_id': source_template_id},
            old_document_id_to_version=old_document_id
        )
        if dialog.exec_() == QDialog.Accepted:
            self.populate_doc_table()
            self.notify(self.tr("Nouvelle Version Créée"), self.tr("Nouvelle version créée avec succès."), type='SUCCESS')

    def delete_client_document_entry(self, document_id, file_path_abs): # file_path is now absolute
        if not document_id:
            self.notify(self.tr("Erreur"), self.tr("ID du document manquant."), type='ERROR')
            return

        file_display_name = os.path.basename(file_path_abs) if file_path_abs else self.tr("Inconnu")
        reply = QMessageBox.question(self, self.tr("Confirmer Suppression"),
                                     self.tr("Supprimer document ID {0} et fichier '{1}'?").format(document_id, file_display_name),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                db_deleted = client_documents_crud.delete_client_document(document_id)
                if db_deleted:
                    if file_path_abs and os.path.exists(file_path_abs):
                        try:
                            os.remove(file_path_abs)
                            self.notify(self.tr("Succès"), self.tr("Document et fichier supprimés."), type='SUCCESS')
                        except OSError as e_file:
                            self.notify(self.tr("Erreur Fichier"), self.tr("DB supprimé, échec suppression fichier: {0}").format(str(e_file)), type='ERROR')
                    else:
                         self.notify(self.tr("Succès (Partiel)"), self.tr("DB supprimé. Fichier non trouvé sur le disque ou chemin non fourni."), type='WARNING')
                else:
                    self.notify(self.tr("Erreur DB"), self.tr("Échec suppression DB."), type='ERROR')
            except Exception as e:
                self.notify(self.tr("Erreur Suppression"), str(e), type='CRITICAL')
            finally:
                self.populate_doc_table()
                QApplication.restoreOverrideCursor()

    def notify(self, title, message, type='INFO'):
        if self.notification_manager:
            self.notification_manager.show(title, message, type=type)
        else:
            if type == 'ERROR' or type == 'CRITICAL': QMessageBox.critical(self, title, message)
            elif type == 'WARNING': QMessageBox.warning(self, title, message)
            else: QMessageBox.information(self, title, message)

    def refresh_tab_data(self):
        self._load_order_filters()
        self.populate_doc_table()

    def apply_permissions_to_tab(self, can_manage_documents: bool):
        if hasattr(self, 'main_add_doc_action_btn'):
            self.main_add_doc_action_btn.setEnabled(can_manage_documents)

        self.can_manage_documents_permission = can_manage_documents
        self.populate_doc_table() # Rafraîchir pour appliquer les permissions aux actions de ligne

    def handle_generate_from_raw_html_action(self, raw_document_id: str, raw_html_file_path: str, source_template_id: Optional[str]):
        """
        Gère la génération d'un document final (PDF/HTML rempli)
        à partir d'un fichier HTML brut existant dans le dossier client.
        """
        from typing import Optional # Assurez-vous que Optional est importé si ce n'est pas déjà fait en haut
        from PyQt5.QtCore import QUrl # Pour base_url Weasyprint
        # Importer HtmlEditor pour populate_html_content statique
        from gui.widgets.html_editor import HtmlEditor
        # Importer convert_html_to_pdf et WeasyPrintError
        from utils.html_to_pdf_util import convert_html_to_pdf, WeasyPrintError


        logging.info(f"Demande de génération depuis HTML brut: ID={raw_document_id}, Path='{raw_html_file_path}', SourceTemplateID='{source_template_id}'")

        if not raw_html_file_path or not os.path.exists(raw_html_file_path):
            self.notify(self.tr("Fichier Introuvable"), self.tr("Le fichier HTML brut source est introuvable :\n{0}").format(raw_html_file_path), type='WARNING')
            return

        try:
            with open(raw_html_file_path, 'r', encoding='utf-8') as f:
                raw_html_content = f.read()
        except IOError as e:
            self.notify(self.tr("Erreur Lecture"), self.tr("Impossible de lire le fichier HTML brut :\n{0}").format(e), type='ERROR')
            return

        if not raw_html_content.strip(): # Vérifier si le contenu est vide ou juste des espaces
            self.notify(self.tr("Contenu Vide"), self.tr("Le fichier HTML brut est vide."), type='WARNING')
            return

        raw_doc_db_details = client_documents_crud.get_document_by_id(raw_document_id)
        if not raw_doc_db_details:
            self.notify(self.tr("Erreur DB"), self.tr("Impossible de récupérer les détails du document HTML brut."), type='ERROR')
            return

        language_code_for_context = raw_doc_db_details.get('language_code', self.client_info.get('selected_languages', ['fr'])[0])
        original_template_name = "Document_HTML_Brut"
        original_template_type_base = "RAW_HTML_CONTENT" # Fallback si source_template_id n'est pas trouvé

        if source_template_id:
            template_info = db_manager.get_template_by_id(source_template_id)
            if template_info:
                original_template_name = template_info.get('template_name', original_template_name)
                original_template_type_base = template_info.get('template_type', original_template_type_base)
                # Nettoyer _HTML du type de base pour former le type final
                if original_template_type_base.endswith("_HTML"):
                    original_template_type_base = original_template_type_base[:-5]


        # S'assurer que default_company est bien récupéré
        default_company = db_manager.get_default_company()
        if not default_company or not default_company.get('company_id'):
            self.notify(self.tr("Erreur Configuration"), self.tr("Société par défaut non configurée."), type='ERROR')
            return

        document_context = db_manager.get_document_context_data(
            client_id=self.client_info.get('client_id'),
            company_id=default_company['company_id'],
            target_language_code=language_code_for_context,
            project_id=raw_doc_db_details.get('project_id'),
            order_id=raw_doc_db_details.get('order_identifier'),
            document_type=f"GENERATED_FROM_{raw_doc_db_details.get('document_type_generated')}",
            additional_context=self.client_info,
            app_root_dir=self.app_root_dir
        )

        if not document_context:
            self.notify(self.tr("Erreur Contexte"), self.tr("Impossible de générer le contexte pour le document."), type='ERROR')
            return

        populated_html = HtmlEditor.populate_html_content(raw_html_content, document_context)

        client_abs_base_path = os.path.join(self.app_root_dir, self.client_info.get("base_folder_path") or self.client_info.get("default_base_folder_path",""))

        doc_type_name_for_folder = original_template_name.replace(" ", "_").replace("/", "_") + "_Final"
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")

        final_doc_folder_level_parts = [language_code_for_context, doc_type_name_for_folder]
        if raw_doc_db_details.get('order_identifier'):
            safe_order_subfolder = raw_doc_db_details.get('order_identifier').replace(':', '_').replace('/', '_').replace('\\', '_').replace(' ', '_')
            final_doc_folder_level_parts.insert(0, safe_order_subfolder)

        final_doc_folder_abs = os.path.join(client_abs_base_path, *final_doc_folder_level_parts)
        os.makedirs(final_doc_folder_abs, exist_ok=True)

        base_final_filename = f"{os.path.splitext(raw_doc_db_details.get('file_name_on_disk'))[0]}_final_{timestamp_str}"

        final_generated_file_path = None
        final_output_filename = None
        final_document_type_for_db = None
        base_url_for_pdf = QUrl.fromLocalFile(os.path.dirname(raw_html_file_path)).toString()

        try:
            pdf_bytes = convert_html_to_pdf(populated_html, base_url=base_url_for_pdf)
            if pdf_bytes:
                final_output_filename = f"{base_final_filename}.pdf"
                final_generated_file_path = os.path.join(final_doc_folder_abs, final_output_filename)
                with open(final_generated_file_path, 'wb') as f_pdf: f_pdf.write(pdf_bytes)
                final_document_type_for_db = original_template_type_base + "_PDF"
                logging.info(f"Document PDF généré avec succès : {final_generated_file_path}")
            else:
                raise WeasyPrintError("La conversion PDF a retourné None.")
        except WeasyPrintError as e_pdf:
            logging.warning(f"Échec de la conversion PDF depuis HTML brut : {e_pdf}. Sauvegarde en HTML rempli.")
            self.notify(self.tr("Avertissement PDF"), self.tr("La conversion en PDF a échoué ({0}). Le document sera sauvegardé en HTML rempli.").format(str(e_pdf)[:100]), type='WARNING')

            final_output_filename = f"{base_final_filename}_populated.html"
            final_generated_file_path = os.path.join(final_doc_folder_abs, final_output_filename)
            try:
                with open(final_generated_file_path, 'w', encoding='utf-8') as f_html_pop: f_html_pop.write(populated_html)
                final_document_type_for_db = original_template_type_base + "_HTML_POPULATED"
                logging.info(f"Document HTML rempli sauvegardé : {final_generated_file_path}")
            except IOError as e_io_save_html:
                self.notify(self.tr("Erreur Sauvegarde HTML"), self.tr("Impossible de sauvegarder le HTML rempli : {0}").format(e_io_save_html), type='ERROR')
                return

        if not final_generated_file_path or not final_output_filename:
            self.notify(self.tr("Erreur Génération"), self.tr("Aucun fichier final n'a pu être généré."), type='ERROR')
            return

        final_file_path_relative_to_client_base = os.path.relpath(final_generated_file_path, client_abs_base_path)

        final_doc_db_data = {
            "client_id": self.client_info.get('client_id'),
            "document_name": final_output_filename,
            "file_name_on_disk": final_output_filename,
            "file_path_relative": final_file_path_relative_to_client_base,
            "document_type_generated": final_document_type_for_db,
            "language_code": language_code_for_context,
            "source_template_id": source_template_id,
            "parent_document_id": raw_document_id, # Lier au document HTML brut source
            "order_identifier": raw_doc_db_details.get('order_identifier'),
            "user_id": self.current_user_id,
            "notes": f"Généré à partir du document HTML brut ID: {raw_document_id}.",
            "version_tag": "1.0_generated"
        }

        new_final_doc_id = client_documents_crud.add_client_document(final_doc_db_data)
        if not new_final_doc_id:
            self.notify(self.tr("Erreur DB"), self.tr("Échec de l'enregistrement du document final généré en base de données."), type='ERROR')
            try:
                if final_generated_file_path and os.path.exists(final_generated_file_path):
                    os.remove(final_generated_file_path)
            except OSError: logging.warning(f"Impossible de supprimer {final_generated_file_path} après échec DB.")
            return

        self.notify(self.tr("Succès"), self.tr("Document final '{0}' généré avec succès.").format(final_output_filename), type='SUCCESS')
        self.populate_doc_table()

    def handle_convert_proforma_to_invoice(self, proforma_document_id: str):
        self.notify(self.tr("Information"), self.tr(f"Conversion de proforma ID {proforma_document_id} en facture demandée. Cette fonctionnalité est en cours de développement."), type='INFO')
        logging.info(f"Conversion de proforma ID {proforma_document_id} en facture demandée.")

        # 1. Récupérer les détails du document proforma

        proforma_doc = client_documents_crud.get_document_by_id(proforma_document_id)
        if not proforma_doc:
            self.notify(self.tr("Erreur"), self.tr("Document proforma non trouvé."), type='ERROR')
            return

        commande_id = proforma_doc.get('commande_id')
        if not commande_id:
            self.notify(self.tr("Erreur"), self.tr("Aucune commande n'est liée à cette proforma. Conversion manuelle requise."), type='WARNING')
            return

        # 2. Récupérer les détails de la commande et ses items
        # Assurez-vous que commandes_crud est importé ou accessible via db_manager
        commande_details = db_manager.commandes_crud.get_commande_by_id(commande_id)
        if not commande_details:
            self.notify(self.tr("Erreur"), self.tr(f"Détails de la commande ID {commande_id} non trouvés."), type='ERROR')
            return

        commande_items = db_manager.commandes_crud.get_items_for_commande(commande_id)
        if commande_items is None: # Peut retourner None en cas d'erreur DB
            self.notify(self.tr("Erreur"), self.tr(f"Articles pour la commande ID {commande_id} non trouvés."), type='ERROR')
            return

        # 3. Préparer les données pour le dialogue de facture
        # La structure exacte dépendra de ce que ManualInvoiceDialog attend
        invoice_data_prefill = {
            "client_id": commande_details.get("client_id"),
            "project_id": commande_details.get("project_id"),
            "commande_id_source": commande_id, # Pour référence
            "currency": commande_details.get("currency", "EUR"),
            "items": [],
            "notes": f"Basé sur la Proforma Doc ID: {proforma_document_id}, Commande Réf: {commande_details.get('commande_reference')}"
            # D'autres champs comme les termes de paiement pourraient être copiés de la commande/proforma

        }

        for item in commande_items:
            invoice_data_prefill["items"].append({
                "product_id": item.get("product_id"),
                "description": item.get("description_item"), # Ou product_name si description_item est vide
                "quantity": item.get("quantity"),
                "unit_price": item.get("unit_price_ht"),
                "vat_rate": item.get("vat_rate", 0.0) # Le dialogue de facture gérera probablement le %
                # ... autres champs que ManualInvoiceDialog pourrait attendre pour les items
            })

        # 4. Ouvrir le dialogue de création de facture
        try:
            from invoicing.manual_invoice_dialog import ManualInvoiceDialog # Importation locale
            # Il faut s'assurer que ManualInvoiceDialog peut accepter des données pré-remplies
            # Par exemple, via un paramètre `prefill_data` ou des setters.
            # Ceci est une supposition sur le fonctionnement de ManualInvoiceDialog.
            invoice_dialog = ManualInvoiceDialog(
                client_id=invoice_data_prefill["client_id"],
                current_user_id=self.current_user_id,
                prefill_data=invoice_data_prefill, # Paramètre hypothétique

                parent=self
            )

            if invoice_dialog.exec_() == QDialog.Accepted:
                new_invoice_id = invoice_dialog.get_created_invoice_id() # Méthode hypothétique
                if new_invoice_id:
                    self.notify(self.tr("Succès"), self.tr(f"Facture ID {new_invoice_id} créée avec succès à partir de la proforma."), type='SUCCESS')

                    # 5. Mettre à jour la proforma (par exemple, ajouter une note)
                    updated_proforma_notes = proforma_doc.get("notes", "") or ""
                    updated_proforma_notes += f"\nConvertie en Facture ID: {new_invoice_id} le {datetime.now().strftime('%Y-%m-%d %H:%M')}."

                    client_documents_crud.update_client_document_notes(proforma_document_id, updated_proforma_notes.strip())
                    # Idéalement, il y aurait un champ `linked_invoice_id` sur la table ClientDocuments ou ProformaInvoices.
                    # Ou un statut "Convertie" pour la proforma.

                    self.populate_doc_table() # Rafraîchir la liste des documents

                else:
                    self.notify(self.tr("Information"), self.tr("La facture a été créée mais son ID n'a pas pu être récupéré."), type='INFO')
            else:
                self.notify(self.tr("Annulé"), self.tr("Conversion en facture annulée."), type='INFO')

        except ImportError:
            self.logger.error("ManualInvoiceDialog n'a pas pu être importé.")
            self.notify(self.tr("Erreur"), self.tr("Le module de facturation n'est pas disponible."), type='CRITICAL')
        except Exception as e:
            self.logger.error(f"Erreur lors de la conversion proforma en facture : {e}", exc_info=True)

            self.notify(self.tr("Erreur Inattendue"), str(e), type='CRITICAL')
