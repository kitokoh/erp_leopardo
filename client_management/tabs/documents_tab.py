# -*- coding: utf-8 -*-
import os
# import sys # No longer used
import logging
import shutil
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QInputDialog, QMessageBox, QFileDialog, QApplication, QSizePolicy, QDialog
)
from PyQt5.QtGui import QIcon, QDesktopServices, QFont
from PyQt5.QtCore import Qt, QUrl, QStandardPaths

import db as db_manager
from db.cruds import client_documents_crud, projects_crud

from excel_editor import ExcelEditor
from gui.widgets.html_editor import HtmlEditor
# Other necessary dialogs and modules will be imported as needed, or passed from parent

SUPPORTED_LANGUAGES = ["en", "fr", "ar", "tr", "pt", "ru"]

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
        self.generate_pdf_for_document = main_module_generate_pdf_for_document

        self.parent_widget = parent_widget
        self._is_populating_docs = False
        self.can_manage_documents_permission = False

        self._setup_ui()
        self.populate_doc_table()

    def tr(self, text, disambiguation=None, n=-1):
        if self.parent_widget:
            return self.parent_widget.tr(text, disambiguation, n)
        return QApplication.translate("DocumentsTab", text, disambiguation, n)


    def _setup_ui(self):
        logging.info("DocumentsTab._setup_ui: Starting setup for Documents Tab Structure...")
        docs_layout = QVBoxLayout(self)
        docs_layout.setContentsMargins(5,5,5,5) # Reduced margins for a tighter look
        docs_layout.setSpacing(8) # Reduced spacing

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
        for lang_code in SUPPORTED_LANGUAGES:
            self.doc_language_filter_combo.addItem(lang_code, lang_code)
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
        self.doc_type_filter_combo.addItem("PDF", "PDF")
        self.doc_type_filter_combo.addItem("XLSX", "XLSX")
        self.doc_type_filter_combo.addItem("DOCX", "DOCX")
        self.doc_type_filter_combo.addItem(self.tr("Autre"), "OTHER")
        self.doc_type_filter_combo.currentIndexChanged.connect(self.populate_doc_table)
        doc_filter_layout.addWidget(self.doc_type_filter_combo)

        docs_layout.addWidget(self.doc_filter_layout_widget)
        self.doc_filter_layout_widget.setVisible(True)

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
            self.tr("Date Création"), self.tr("Fichier Original"), self.tr("Actions")
        ])
        header_font = QFont()
        header_font.setBold(True)
        self.doc_table.horizontalHeader().setFont(header_font)
        self.doc_table.horizontalHeader().setStyleSheet(
            "QHeaderView::section { background-color: #e9ecef; padding: 4px; border: 1px solid #dee2e6; font-weight: bold; }"
        )
        self.doc_table.verticalHeader().setVisible(False)
        self.doc_table.setAlternatingRowColors(True)

        self.doc_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.doc_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.doc_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.doc_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.doc_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Interactive)
        self.doc_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.doc_table.setColumnWidth(4, 150)

        self.doc_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.doc_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        docs_layout.addWidget(self.doc_table)

        doc_btn_layout = QHBoxLayout()
        doc_btn_layout.setSpacing(10)
        self.add_doc_btn = QPushButton(self.tr("Importer Document"))
        self.add_doc_btn.setIcon(QIcon(":/icons/file-plus.svg"))
        self.add_doc_btn.setToolTip(self.tr("Importer un fichier document existant pour ce client"))
        self.add_doc_btn.setObjectName("primaryButton") # Style as primary
        self.add_doc_btn.clicked.connect(self.add_document)
        doc_btn_layout.addWidget(self.add_doc_btn)

        self.refresh_docs_btn = QPushButton(self.tr("Actualiser"))
        self.refresh_docs_btn.setIcon(QIcon(":/icons/refresh-cw.svg")) # Use a more common refresh icon
        self.refresh_docs_btn.clicked.connect(self.populate_doc_table)
        doc_btn_layout.addWidget(self.refresh_docs_btn)

        self.add_template_btn = QPushButton(self.tr("Générer via Modèle"))
        self.add_template_btn.setIcon(QIcon(":/icons/file-text.svg")) # Icon for text/template based generation
        self.add_template_btn.setToolTip(self.tr("Générer un nouveau document pour ce client à partir d'un modèle"))
        self.add_template_btn.setObjectName("primaryButton")
        self.add_template_btn.clicked.connect(self.add_document_from_template_action) # Modifié pour appeler la méthode directe
        doc_btn_layout.addWidget(self.add_template_btn)

        doc_btn_layout.addStretch() # Push buttons to the left

        docs_layout.addLayout(doc_btn_layout)
        self._load_order_filters()

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
                        if doc_type == "HTML" and can_manage:
                            edit_btn = QPushButton(QIcon(":/icons/edit-2.svg"), "")
                            edit_btn.setToolTip(self.tr("Modifier HTML"))
                            edit_btn.clicked.connect(lambda checked, p=full_file_path, d_id=doc_id: self.handle_edit_html_action(p, d_id))
                            actions_layout.addWidget(edit_btn)
                        elif doc_type == "XLSX" and can_manage:
                            edit_btn = QPushButton(QIcon(":/icons/edit-2.svg"), "")
                            edit_btn.setToolTip(self.tr("Modifier Excel"))
                            edit_btn.clicked.connect(lambda checked, p=full_file_path, d_id=doc_id: self.handle_edit_excel_action(p, d_id))
                            actions_layout.addWidget(edit_btn)

                        view_icon_path = ":/icons/eye.svg"
                        if doc_type == "PDF": view_icon_path = ":/icons/file-text.svg"

                        view_btn = QPushButton(QIcon(view_icon_path), "")
                        view_btn.setToolTip(self.tr("Ouvrir Document"))
                        view_btn.clicked.connect(lambda checked, p=full_file_path, d_id=doc_id: self._handle_view_document_action(p, d_id))
                        actions_layout.addWidget(view_btn)

                    if can_manage:
                        if doc.get("source_template_id"):
                            version_btn = QPushButton(QIcon(":/icons/plus-square.svg"), "") # Remplacé copy.svg
                            version_btn.setToolTip(self.tr("Créer une nouvelle version"))
                            version_btn.clicked.connect(lambda checked, old_id=doc_id, t_id=doc.get("source_template_id"): self.handle_create_new_version_clicked(old_id, t_id))
                            actions_layout.addWidget(version_btn)

                        delete_btn = QPushButton(QIcon(":/icons/trash.svg"), "") # Remplacé trash-2.svg par trash.svg
                        delete_btn.setToolTip(self.tr("Supprimer Document"))
                        delete_btn.setObjectName("dangerButton")
                        delete_btn.clicked.connect(lambda checked, d_id=doc_id, p=full_file_path: self.delete_client_document_entry(d_id, p))
                        actions_layout.addWidget(delete_btn)

                    actions_layout.addStretch()
                    self.doc_table.setCellWidget(row_idx, 5, actions_widget)
        except Exception as e:
            logging.error(f"Error populating documents table: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Chargement"), self.tr("Impossible de charger les documents: {0}").format(str(e)))
        finally:
            QApplication.restoreOverrideCursor()
            self._is_populating_docs = False

    def add_document(self):
        available_languages = SUPPORTED_LANGUAGES
        selected_doc_language, ok = QInputDialog.getItem(
            self, self.tr("Sélectionner la langue"), self.tr("Langue du document:"),
            available_languages, 0, False
        )
        if not ok or not selected_doc_language:
            self.notify(self.tr("Annulé"), self.tr("L'opération d'ajout de document a été annulée."), type='INFO')
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

                # Construct absolute base path for the client
                client_abs_base_path = os.path.join(self.app_root_dir, client_relative_base_path)

                target_lang_dir_abs = os.path.join(client_abs_base_path, selected_doc_language)

                # Handle order identifier for subfolder structure
                order_identifier = None
                current_order_data = self.doc_order_filter_combo.currentData()
                if current_order_data not in ["ALL", "NONE"] and current_order_data is not None:
                    order_identifier = current_order_data
                    safe_order_subfolder = order_identifier.replace(':', '_').replace('/', '_').replace('\\', '_').replace(' ', '_')
                    target_lang_dir_abs = os.path.join(client_abs_base_path, safe_order_subfolder, selected_doc_language)

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
                    (os.path.join(safe_order_subfolder, selected_doc_language) if order_identifier else selected_doc_language),
                    file_name
                )

                doc_db_data = {
                    "client_id": client_id, "document_name": file_name,
                    "file_name_on_disk": file_name, # Storing just filename, path is derived
                    "file_path_relative": file_path_relative_to_client_base,
                    "document_type_generated": document_type_generated,
                    "language_code": selected_doc_language, "source_template_id": None,
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
        if file_path and os.path.exists(file_path):
            editor = HtmlEditor(file_path, document_id, self) # Pass self (DocumentsTab) as parent
            if editor.exec_() == QDialog.Accepted:
                self.populate_doc_table()
                self.notify(self.tr("HTML Modifié"), self.tr("Le document HTML a été sauvegardé."), type='SUCCESS')
        else:
            self.notify(self.tr("Fichier Introuvable"), self.tr("Le fichier HTML est introuvable:\n{0}").format(file_path), type='WARNING')

    def handle_edit_excel_action(self, file_path, document_id):
        if file_path and os.path.exists(file_path):
            editor = ExcelEditor(file_path, document_id, self) # Pass self (DocumentsTab) as parent
            if editor.exec_() == QDialog.Accepted:
                self.populate_doc_table()
                self.notify(self.tr("Excel Modifié"), self.tr("Le document Excel a été sauvegardé."), type='SUCCESS')
        else:
            self.notify(self.tr("Fichier Introuvable"), self.tr("Le fichier Excel est introuvable:\n{0}").format(file_path), type='WARNING')

    def _handle_view_document_action(self, file_path, document_id):
        if file_path and os.path.exists(file_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
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

        dialog = self.CreateDocumentDialog(
            client_info=self.client_info, config=self.config,
            current_user_id=self.current_user_id, parent=self,
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
                # Fetch the document to get its relative path for DB consistency if needed,
                # though delete_client_document should handle this.
                # For file deletion, file_path_abs is already what we need.
                db_deleted = client_documents_crud.delete_client_document(document_id) # Use the specific CRUD
                if db_deleted:
                    if file_path_abs and os.path.exists(file_path_abs):
                        try:
                            os.remove(file_path_abs)
                            self.notify(self.tr("Succès"), self.tr("Document et fichier supprimés."), type='SUCCESS')
                        except OSError as e_file:
                            self.notify(self.tr("Erreur Fichier"), self.tr("DB supprimé, échec suppression fichier: {0}").format(str(e_file)), type='ERROR')
                    else:
                         self.notify(self.tr("Succès (Partiel)"), self.tr("DB supprimé. Fichier non trouvé sur le disque."), type='WARNING')
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
        if hasattr(self, 'add_doc_btn'):
            self.add_doc_btn.setEnabled(can_manage_documents)
        if hasattr(self, 'add_template_btn'):
            self.add_template_btn.setEnabled(can_manage_documents)

        self.can_manage_documents_permission = can_manage_documents
        self.populate_doc_table() # Refresh table to show/hide row actions based on new permission
