# -*- coding: utf-8 -*-
import os
import logging
import shutil
from datetime import datetime
import zipfile
from PyQt5.QtCore import QStandardPaths, QSize
from PyQt5.QtGui import QPixmap # For image preview
try:
    from PyQt5.QtPdf import QPdfDocument # For PDF preview
    QT_PDF_AVAILABLE = True
except ImportError:
    QT_PDF_AVAILABLE = False
    logging.warning("QtPdf module not found, PDF preview will be disabled.")


from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QInputDialog, QMessageBox, QFileDialog, QApplication, QSizePolicy,
    QLineEdit, QDateEdit, QSplitter # Added QSplitter for preview
)
from PyQt5.QtGui import QIcon, QDesktopServices, QFont
from PyQt5.QtCore import Qt, QUrl, QDate

import db as db_manager
from db.cruds import client_documents_crud, projects_crud

from excel_editor import ExcelEditor
from html_editor import HtmlEditor

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
        self.pdf_preview_doc = None # For QPdfDocument instance

        self._setup_ui()
        self._load_order_filters()

    def tr(self, text, disambiguation=None, n=-1):
        if self.parent_widget:
            return self.parent_widget.tr(text, disambiguation, n)
        return QApplication.translate("DocumentsTab", text, disambiguation, n)


    def _setup_ui(self):
        logging.info("DocumentsTab._setup_ui: Starting setup for Documents Tab Structure...")
        main_docs_layout = QHBoxLayout(self) # Main layout is now Horizontal for table + preview
        main_docs_layout.setContentsMargins(5,5,5,5)
        main_docs_layout.setSpacing(8)

        # Left side: Filters and Table
        left_panel_widget = QWidget()
        docs_layout = QVBoxLayout(left_panel_widget)
        docs_layout.setContentsMargins(0,0,0,0) # No margins for the internal left panel layout
        docs_layout.setSpacing(8)


        # --- Top Filter Row (Order, Language, Type) ---
        top_filter_row_layout = QHBoxLayout()
        top_filter_row_layout.setSpacing(10)

        doc_filter_label = QLabel(self.tr("Cmd:"))
        doc_filter_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        top_filter_row_layout.addWidget(doc_filter_label)
        self.doc_order_filter_combo = QComboBox()
        self.doc_order_filter_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.doc_order_filter_combo.setToolTip(self.tr("Filtrer par Commande/Projet"))
        self.doc_order_filter_combo.currentIndexChanged.connect(self.populate_doc_table)
        top_filter_row_layout.addWidget(self.doc_order_filter_combo)

        doc_lang_filter_label = QLabel(self.tr("Lang:"))
        doc_lang_filter_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        top_filter_row_layout.addWidget(doc_lang_filter_label)
        self.doc_language_filter_combo = QComboBox()
        self.doc_language_filter_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.doc_language_filter_combo.setToolTip(self.tr("Filtrer par Langue"))
        self.doc_language_filter_combo.addItem(self.tr("Toutes"), "ALL")
        for lang_code in SUPPORTED_LANGUAGES:
            self.doc_language_filter_combo.addItem(lang_code.upper(), lang_code)
        self.doc_language_filter_combo.currentIndexChanged.connect(self.populate_doc_table)
        top_filter_row_layout.addWidget(self.doc_language_filter_combo)

        doc_type_filter_label = QLabel(self.tr("Type:"))
        doc_type_filter_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        top_filter_row_layout.addWidget(doc_type_filter_label)
        self.doc_type_filter_combo = QComboBox()
        self.doc_type_filter_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.doc_type_filter_combo.setToolTip(self.tr("Filtrer par Type de Document"))
        self.doc_type_filter_combo.addItem(self.tr("Tous"), "ALL")
        self.doc_type_filter_combo.addItem("HTML", "HTML")
        self.doc_type_filter_combo.addItem("PDF", "PDF")
        self.doc_type_filter_combo.addItem("XLSX", "XLSX")
        self.doc_type_filter_combo.addItem("DOCX", "DOCX")
        self.doc_type_filter_combo.addItem(self.tr("Autre"), "OTHER")
        self.doc_type_filter_combo.currentIndexChanged.connect(self.populate_doc_table)
        top_filter_row_layout.addWidget(self.doc_type_filter_combo)
        docs_layout.addLayout(top_filter_row_layout)

        second_filter_row_layout = QHBoxLayout()
        second_filter_row_layout.setSpacing(10)

        self.doc_name_search_input = QLineEdit()
        self.doc_name_search_input.setPlaceholderText(self.tr("Rechercher par nom de document..."))
        self.doc_name_search_input.setClearButtonEnabled(True)
        self.doc_name_search_input.textChanged.connect(self.populate_doc_table)
        second_filter_row_layout.addWidget(self.doc_name_search_input)

        second_filter_row_layout.addWidget(QLabel(self.tr("Créé entre:")))
        self.doc_date_filter_start = QDateEdit()
        self.doc_date_filter_start.setCalendarPopup(True)
        self.doc_date_filter_start.setDisplayFormat("dd/MM/yyyy")
        self.doc_date_filter_start.setDate(QDate())
        self.doc_date_filter_start.dateChanged.connect(self.populate_doc_table)
        second_filter_row_layout.addWidget(self.doc_date_filter_start)

        second_filter_row_layout.addWidget(QLabel(self.tr("et")))
        self.doc_date_filter_end = QDateEdit()
        self.doc_date_filter_end.setCalendarPopup(True)
        self.doc_date_filter_end.setDisplayFormat("dd/MM/yyyy")
        self.doc_date_filter_end.setDate(QDate())
        self.doc_date_filter_end.dateChanged.connect(self.populate_doc_table)
        second_filter_row_layout.addWidget(self.doc_date_filter_end)

        self.reset_filters_btn = QPushButton(self.tr("Réinitialiser Filtres"))
        self.reset_filters_btn.setIcon(QIcon(":/icons/refresh-cw.svg"))
        self.reset_filters_btn.clicked.connect(self.reset_all_document_filters)
        second_filter_row_layout.addWidget(self.reset_filters_btn)

        docs_layout.addLayout(second_filter_row_layout)

        self.documents_empty_label = QLabel(self.tr("Aucun document trouvé pour ce client.\nUtilisez les boutons ci-dessous pour ajouter ou générer des documents."))
        self.documents_empty_label.setAlignment(Qt.AlignCenter)
        font_docs_empty = self.documents_empty_label.font(); font_docs_empty.setPointSize(10)
        self.documents_empty_label.setFont(font_docs_empty)
        docs_layout.addWidget(self.documents_empty_label)

        self.doc_table = QTableWidget()
        self.doc_table.setObjectName("documentsTable")
        self.doc_table.setColumnCount(6)
        self.doc_table.setHorizontalHeaderLabels([
            self.tr("Nom Document"), self.tr("Type"), self.tr("Langue"),
            self.tr("Date Création"), self.tr("Fichier Original"), self.tr("Actions")
        ])
        header_font = QFont(); header_font.setBold(True)
        self.doc_table.horizontalHeader().setFont(header_font)
        self.doc_table.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: #e9ecef; padding: 4px; border: 1px solid #dee2e6; font-weight: bold; }")
        self.doc_table.verticalHeader().setVisible(False)
        self.doc_table.setAlternatingRowColors(True)
        self.doc_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.doc_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.doc_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.doc_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.doc_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Interactive)
        self.doc_table.setColumnWidth(4, 150)
        self.doc_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.doc_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.doc_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.doc_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.doc_table.itemSelectionChanged.connect(self._update_bulk_action_buttons_state)
        self.doc_table.itemSelectionChanged.connect(self._handle_document_selection_for_preview) # Connect for preview
        docs_layout.addWidget(self.doc_table)

        actions_main_layout = QHBoxLayout()
        single_doc_actions_layout = QHBoxLayout(); single_doc_actions_layout.setSpacing(10)
        bulk_actions_layout = QHBoxLayout(); bulk_actions_layout.setSpacing(10)

        self.add_doc_btn = QPushButton(self.tr("Importer Document"))
        self.add_doc_btn.setIcon(QIcon(":/icons/file-plus.svg"))
        self.add_doc_btn.setToolTip(self.tr("Importer un fichier document existant pour ce client"))
        self.add_doc_btn.setObjectName("primaryButton")
        self.add_doc_btn.clicked.connect(self.add_document)
        single_doc_actions_layout.addWidget(self.add_doc_btn)

        self.refresh_docs_btn = QPushButton(self.tr("Actualiser"))
        self.refresh_docs_btn.setIcon(QIcon(":/icons/refresh-cw.svg"))
        self.refresh_docs_btn.clicked.connect(self.populate_doc_table)
        single_doc_actions_layout.addWidget(self.refresh_docs_btn)

        self.add_template_btn = QPushButton(self.tr("Générer via Modèle"))
        self.add_template_btn.setIcon(QIcon(":/icons/file-text.svg"))
        self.add_template_btn.setToolTip(self.tr("Générer un nouveau document pour ce client à partir d'un modèle"))
        self.add_template_btn.setObjectName("primaryButton")
        self.add_template_btn.clicked.connect(self.open_create_docs_dialog_from_parent)
        single_doc_actions_layout.addWidget(self.add_template_btn)

        actions_main_layout.addLayout(single_doc_actions_layout)
        actions_main_layout.addStretch(1)

        self.compile_selection_btn = QPushButton(self.tr("Compiler Sélection"))
        self.compile_selection_btn.setIcon(QIcon(":/icons/layers.svg"))
        self.compile_selection_btn.setToolTip(self.tr("Compiler les documents PDF sélectionnés en un seul fichier"))
        self.compile_selection_btn.setObjectName("secondaryButton")
        self.compile_selection_btn.setEnabled(False)
        self.compile_selection_btn.clicked.connect(self.handle_compile_selection_to_pdf)
        bulk_actions_layout.addWidget(self.compile_selection_btn)

        self.download_selection_btn = QPushButton(self.tr("Télécharger Sélection"))
        self.download_selection_btn.setIcon(QIcon(":/icons/download.svg"))
        self.download_selection_btn.setToolTip(self.tr("Télécharger les documents sélectionnés dans une archive ZIP"))
        self.download_selection_btn.setObjectName("secondaryButton")
        self.download_selection_btn.setEnabled(False)
        self.download_selection_btn.clicked.connect(self.handle_download_selection_as_zip)
        bulk_actions_layout.addWidget(self.download_selection_btn)

        self.delete_selection_btn = QPushButton(self.tr("Supprimer Sélection"))
        self.delete_selection_btn.setIcon(QIcon(":/icons/trash-2.svg"))
        self.delete_selection_btn.setToolTip(self.tr("Supprimer tous les documents sélectionnés"))
        self.delete_selection_btn.setObjectName("dangerButton")
        self.delete_selection_btn.setEnabled(False)
        self.delete_selection_btn.clicked.connect(self.handle_delete_selection)
        bulk_actions_layout.addWidget(self.delete_selection_btn)

        actions_main_layout.addLayout(bulk_actions_layout)
        docs_layout.addLayout(actions_main_layout)

        # Right side: Document Preview
        self.preview_area = QLabel(self.tr("Sélectionnez un document pour l'aperçu."))
        self.preview_area.setObjectName("documentPreviewArea")
        self.preview_area.setAlignment(Qt.AlignCenter)
        self.preview_area.setMinimumWidth(250) # Minimum width for the preview panel
        self.preview_area.setWordWrap(True)
        # Styling for the preview area (can be enhanced with QSS)
        self.preview_area.setStyleSheet("QLabel#documentPreviewArea { background-color: #fafafa; border: 1px solid #e0e0e0; padding: 10px; }")

        # Use QSplitter to manage table and preview
        self.docs_splitter = QSplitter(Qt.Horizontal)
        self.docs_splitter.addWidget(left_panel_widget) # Contains filters and table
        self.docs_splitter.addWidget(self.preview_area)
        self.docs_splitter.setSizes([700, 300]) # Initial sizes, adjust as needed

        main_docs_layout.addWidget(self.docs_splitter) # Add splitter to the main tab layout


    def reset_all_document_filters(self):
        self.doc_order_filter_combo.setCurrentIndex(0)
        self.doc_language_filter_combo.setCurrentIndex(0)
        self.doc_type_filter_combo.setCurrentIndex(0)
        self.doc_name_search_input.clear()
        self.doc_date_filter_start.setDate(QDate())
        self.doc_date_filter_end.setDate(QDate())
        self.populate_doc_table()


    def _update_bulk_action_buttons_state(self):
        selected_rows = self.doc_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0

        self.download_selection_btn.setEnabled(has_selection)
        self.delete_selection_btn.setEnabled(has_selection and self.can_manage_documents_permission)

        can_compile = False
        if has_selection and self.can_manage_documents_permission:
            all_pdfs = True
            if len(selected_rows) == 0:
                all_pdfs = False
            for index in selected_rows:
                doc_type_item = self.doc_table.item(index.row(), 1)
                if not doc_type_item or doc_type_item.text() != "PDF":
                    all_pdfs = False
                    break
            if all_pdfs:
                can_compile = True
        self.compile_selection_btn.setEnabled(can_compile)


    def handle_compile_selection_to_pdf(self):
        selected_rows = self.doc_table.selectionModel().selectedRows()
        if not selected_rows: return

        if not self.can_manage_documents_permission:
            self.notify(self.tr("Permissions Insuffisantes"), self.tr("Vous n'avez pas la permission de compiler des documents."), type="WARNING")
            return

        pdf_paths_to_compile = []
        for index in selected_rows:
            doc_id = self.doc_table.item(index.row(), 0).data(Qt.UserRole)
            doc_data = client_documents_crud.get_document_by_id(doc_id)
            if doc_data and doc_data.get("document_type_generated") == "PDF":
                file_path_relative = doc_data.get("file_path_relative")
                client_base_folder_path = self.client_info.get("base_folder_path", self.client_info.get("default_base_folder_path", ""))
                base_folder_abs = os.path.join(self.app_root_dir, client_base_folder_path)
                full_file_path = os.path.join(base_folder_abs, file_path_relative) if base_folder_abs and file_path_relative else None
                if full_file_path and os.path.exists(full_file_path):
                    pdf_paths_to_compile.append(full_file_path)
                else:
                    logging.warning(f"PDF file not found for document ID {doc_id} at path {full_file_path}. Skipping for compilation.")

        if not pdf_paths_to_compile:
            self.notify(self.tr("Aucun PDF Valide"), self.tr("Aucun fichier PDF valide trouvé pour les documents sélectionnés."), type="WARNING")
            return

        if len(pdf_paths_to_compile) < 1:
             self.notify(self.tr("Sélection Insuffisante"), self.tr("Veuillez sélectionner au moins un document PDF à compiler."), type="INFO")
             return

        client_name_safe = "".join(c if c.isalnum() else "_" for c in self.client_info.get("client_name", "compilation"))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_dir = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        suggested_pdf_name = os.path.join(default_dir, f"{client_name_safe}_compilation_{timestamp}.pdf")

        output_pdf_path, _ = QFileDialog.getSaveFileName(self, self.tr("Enregistrer PDF Compilé"), suggested_pdf_name, "PDF Files (*.pdf)")
        if not output_pdf_path: return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            from PyPDF2 import PdfMerger

            merger = PdfMerger()
            for pdf_path in pdf_paths_to_compile:
                try:
                    merger.append(pdf_path)
                except Exception as e_append:
                    logging.error(f"Error appending PDF {pdf_path} to merger: {e_append}", exc_info=True)
                    self.notify(self.tr("Erreur PDF Invalide"), self.tr("Le fichier PDF '{0}' est invalide ou corrompu et ne peut être ajouté.").format(os.path.basename(pdf_path)), type="ERROR")
                    QApplication.restoreOverrideCursor()
                    return

            if not merger.pages:
                self.notify(self.tr("Erreur"), self.tr("Aucun PDF valide n'a pu être traité pour la compilation."), type="ERROR")
                QApplication.restoreOverrideCursor()
                return

            with open(output_pdf_path, "wb") as fout:
                merger.write(fout)
            merger.close()

            self.notify(self.tr("Succès"), self.tr("PDFs compilés avec succès en '{0}'.").format(os.path.basename(output_pdf_path)), type="SUCCESS")

        except ImportError:
            self.notify(self.tr("Bibliothèque Manquante"), self.tr("La bibliothèque PyPDF2 est requise pour fusionner les PDFs. Veuillez l'installer (pip install PyPDF2)."), type="ERROR")
        except Exception as e:
            logging.error(f"Error compiling PDFs: {e}", exc_info=True)
            self.notify(self.tr("Erreur de Compilation"), self.tr("Impossible de compiler les PDFs: {0}").format(str(e)), type="ERROR")
        finally:
            QApplication.restoreOverrideCursor()


    def handle_download_selection_as_zip(self):
        selected_rows = self.doc_table.selectionModel().selectedRows()
        if not selected_rows:
            return

        file_paths_to_zip = []
        for index in selected_rows:
            doc_id = self.doc_table.item(index.row(), 0).data(Qt.UserRole)
            doc_data = client_documents_crud.get_document_by_id(doc_id)
            if doc_data:
                file_path_relative = doc_data.get("file_path_relative")
                client_base_folder_path = self.client_info.get("base_folder_path", self.client_info.get("default_base_folder_path", ""))
                base_folder_abs = os.path.join(self.app_root_dir, client_base_folder_path)
                full_file_path = os.path.join(base_folder_abs, file_path_relative) if base_folder_abs and file_path_relative else None
                if full_file_path and os.path.exists(full_file_path):
                    file_paths_to_zip.append(full_file_path)
                else:
                    logging.warning(f"File not found for document ID {doc_id} at path {full_file_path}. Skipping for ZIP.")

        if not file_paths_to_zip:
            self.notify(self.tr("Aucun Fichier"), self.tr("Aucun fichier valide trouvé pour les documents sélectionnés."), type="WARNING")
            return

        client_name_safe = "".join(c if c.isalnum() else "_" for c in self.client_info.get("client_name", "documents"))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_dir = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation) or QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        suggested_zip_name = os.path.join(default_dir, f"{client_name_safe}_selection_{timestamp}.zip")

        zip_file_path, _ = QFileDialog.getSaveFileName(self, self.tr("Enregistrer l'archive ZIP"), suggested_zip_name, "ZIP Files (*.zip)")

        if zip_file_path:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for file_path in file_paths_to_zip:
                        zf.write(file_path, os.path.basename(file_path))
                self.notify(self.tr("Succès"), self.tr("Documents téléchargés avec succès dans {0}.").format(os.path.basename(zip_file_path)), type="SUCCESS")
            except Exception as e:
                logging.error(f"Error creating ZIP archive: {e}", exc_info=True)
                self.notify(self.tr("Erreur ZIP"), self.tr("Impossible de créer l'archive ZIP: {0}").format(str(e)), type="ERROR")
            finally:
                QApplication.restoreOverrideCursor()


    def handle_delete_selection(self):
        selected_rows = self.doc_table.selectionModel().selectedRows()
        if not selected_rows:
            return

        if not self.can_manage_documents_permission:
            self.notify(self.tr("Permissions Insuffisantes"), self.tr("Vous n'avez pas la permission de supprimer des documents."), type="WARNING")
            return

        docs_to_process = []
        for index in selected_rows:
            doc_id = self.doc_table.item(index.row(), 0).data(Qt.UserRole)
            doc_name = self.doc_table.item(index.row(), 0).text()
            doc_data = client_documents_crud.get_document_by_id(doc_id)
            if doc_data:
                file_path_relative = doc_data.get("file_path_relative")
                client_base_folder_path = self.client_info.get("base_folder_path", self.client_info.get("default_base_folder_path", ""))
                base_folder_abs = os.path.join(self.app_root_dir, client_base_folder_path)
                full_file_path = os.path.join(base_folder_abs, file_path_relative) if base_folder_abs and file_path_relative else None
                docs_to_process.append({'id': doc_id, 'path': full_file_path, 'name': doc_name})

        if not docs_to_process:
            self.notify(self.tr("Erreur"), self.tr("Impossible de récupérer les détails des documents sélectionnés."), type="ERROR")
            return

        confirm_msg = self.tr("Êtes-vous sûr de vouloir supprimer les {0} documents suivants ?\n").format(len(docs_to_process))
        confirm_msg += "\n".join([f"- {d['name']}" for d in docs_to_process[:5]])
        if len(docs_to_process) > 5:
            confirm_msg += self.tr("\n... et {0} autres.").format(len(docs_to_process) - 5)

        reply = QMessageBox.question(self, self.tr("Confirmer Suppression Multiple"), confirm_msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            success_count = 0
            error_count = 0
            errors_list = []
            for doc_info in docs_to_process:
                try:
                    db_deleted = client_documents_crud.delete_client_document(doc_info['id'])
                    if db_deleted:
                        if doc_info['path'] and os.path.exists(doc_info['path']):
                            try:
                                os.remove(doc_info['path'])
                            except OSError as e_file_del:
                                logging.error(f"Error deleting file {doc_info['path']} for doc ID {doc_info['id']}: {e_file_del}", exc_info=True)
                                errors_list.append(f"{doc_info['name']}: {self.tr('Échec suppression fichier')}")
                        success_count += 1
                    else:
                        errors_list.append(f"{doc_info['name']}: {self.tr('Échec suppression DB')}")
                        error_count += 1
                except Exception as e_proc:
                    logging.error(f"Error processing deletion for doc ID {doc_info['id']}: {e_proc}", exc_info=True)
                    errors_list.append(f"{doc_info['name']}: {str(e_proc)}")
                    error_count += 1

            QApplication.restoreOverrideCursor()
            if error_count == 0:
                self.notify(self.tr("Succès"), self.tr("{0} document(s) supprimé(s) avec succès.").format(success_count), type="SUCCESS")
            else:
                error_details = "\n".join(errors_list[:3])
                if len(errors_list) > 3: error_details += "\n..."
                self.notify(self.tr("Résultat Suppression"), self.tr("{0} document(s) supprimé(s), {1} erreur(s).\n\nDétails:\n{2}").format(success_count, error_count, error_details), type="WARNING")
            self.populate_doc_table()


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
                    for identifier_str in sorted(list(set(fetched_order_identifiers))):
                        if identifier_str and identifier_str.strip():
                             self.doc_order_filter_combo.addItem(identifier_str, identifier_str)
            except Exception as e:
                logging.error(f"Error loading order filters for documents: {e}", exc_info=True)

        index_to_select = self.doc_order_filter_combo.findData(current_selection)
        if index_to_select != -1:
            self.doc_order_filter_combo.setCurrentIndex(index_to_select)
        elif self.doc_order_filter_combo.count() > 0:
            self.doc_order_filter_combo.setCurrentIndex(0)

        self.doc_order_filter_combo.blockSignals(False)
        if self.doc_order_filter_combo.currentIndex() == 0 and not self._is_populating_docs :
             self.populate_doc_table()


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
        search_name_term = self.doc_name_search_input.text().strip() if hasattr(self, 'doc_name_search_input') else None

        date_filter_start_qdate = self.doc_date_filter_start.date() if hasattr(self, 'doc_date_filter_start') else QDate()
        date_filter_end_qdate = self.doc_date_filter_end.date() if hasattr(self, 'doc_date_filter_end') else QDate()


        filters = {"client_id": client_id}
        if selected_order_identifier not in ["ALL", "NONE"] and selected_order_identifier is not None:
            filters["order_identifier"] = selected_order_identifier
        elif selected_order_identifier == "NONE":
            filters["order_identifier_is_null"] = True
        if selected_language != "ALL" and selected_language is not None:
            filters["language_code"] = selected_language
        if selected_doc_type != "ALL" and selected_doc_type is not None:
            filters["document_type_generated"] = selected_doc_type
        if search_name_term:
            filters["document_name_like"] = search_name_term

        if date_filter_start_qdate.isValid() and not date_filter_start_qdate.isNull():
            filters['created_at_start'] = date_filter_start_qdate.toString("yyyy-MM-ddT00:00:00Z")
        if date_filter_end_qdate.isValid() and not date_filter_end_qdate.isNull():
            filters['created_at_end'] = date_filter_end_qdate.toString("yyyy-MM-ddT23:59:59Z")


        crud_filters = {k: v for k, v in filters.items() if k != 'client_id'}

        try:
            documents = client_documents_crud.get_documents_for_client(client_id=client_id, filters=crud_filters)
            if not documents:
                self.documents_empty_label.show()
                self.doc_table.hide()
                self.preview_area.setText(self.tr("Aucun document à afficher.")) # Clear preview
                self.preview_area.setPixmap(QPixmap()) # Clear pixmap
            else:
                self.documents_empty_label.hide()
                self.doc_table.show()
                self.doc_table.setRowCount(len(documents))
                for row_idx, doc in enumerate(documents):
                    doc_id = doc.get("document_id")

                    doc_name_display = doc.get("document_name", self.tr("Sans nom"))
                    version_tag = doc.get("version_tag")
                    if version_tag and version_tag != "1.0": # Assuming "1.0" is default and not explicitly shown
                        doc_name_display += f" (v{version_tag})"

                    doc_name_item = QTableWidgetItem(doc_name_display)
                    doc_name_item.setData(Qt.UserRole, doc_id)

                    # Indicate if it's a version of another document (visual cue)
                    # This requires fetching the 'old_document_id' if it exists on the document versioning model
                    # For now, we rely on version_tag. A more complex model might have an 'is_version_of' field.
                    # if doc.get("is_version_of_id"): # Conceptual field
                    #    doc_name_item.setForeground(QColor("blue"))
                    #    doc_name_item.setToolTip(self.tr("Ceci est une version d'un autre document."))

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

                    original_file_path_relative = doc.get("file_path_original")
                    if original_file_path_relative:
                        abs_original_path = os.path.join(self.app_root_dir, original_file_path_relative) if not os.path.isabs(original_file_path_relative) else original_file_path_relative
                        link_widget = QLabel(f"<a href='file:///{abs_original_path}'>{os.path.basename(original_file_path_relative)}</a>")
                        link_widget.setOpenExternalLinks(True)
                        self.doc_table.setCellWidget(row_idx, 4, link_widget)
                    else:
                        self.doc_table.setItem(row_idx, 4, QTableWidgetItem(self.tr("N/A")))

                    actions_widget = QWidget()
                    actions_layout = QHBoxLayout(actions_widget)
                    actions_layout.setContentsMargins(2,2,2,2); actions_layout.setSpacing(3)

                    can_manage = self.can_manage_documents_permission

                    file_path_relative = doc.get("file_path_relative")
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
                            version_btn = QPushButton(QIcon(":/icons/copy.svg"), "")
                            version_btn.setToolTip(self.tr("Créer une nouvelle version"))
                            version_btn.clicked.connect(lambda checked, old_id=doc_id, t_id=doc.get("source_template_id"): self.handle_create_new_version_clicked(old_id, t_id))
                            actions_layout.addWidget(version_btn)

                        delete_btn = QPushButton(QIcon(":/icons/trash-2.svg"), "")
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
            self._update_bulk_action_buttons_state() # Update bulk buttons after table population
            self._handle_document_selection_for_preview() # Clear or update preview based on new selection (or lack thereof)


    def _handle_document_selection_for_preview(self):
        selected_items = self.doc_table.selectedItems()
        if not selected_items:
            self.preview_area.setText(self.tr("Sélectionnez un document pour un aperçu."))
            self.preview_area.setPixmap(QPixmap()) # Clear any existing pixmap
            return

        # Only show preview if exactly one row is selected
        selected_rows = self.doc_table.selectionModel().selectedRows()
        if len(selected_rows) != 1:
            self.preview_area.setText(self.tr("Sélectionnez un seul document pour l'aperçu."))
            self.preview_area.setPixmap(QPixmap())
            return

        selected_row = selected_rows[0].row()
        doc_id_item = self.doc_table.item(selected_row, 0)
        if not doc_id_item:
            self.preview_area.setText(self.tr("Erreur: Impossible de récupérer l'ID du document."))
            self.preview_area.setPixmap(QPixmap())
            return

        doc_id = doc_id_item.data(Qt.UserRole)
        doc_data = client_documents_crud.get_document_by_id(doc_id)

        if not doc_data:
            self.preview_area.setText(self.tr("Erreur: Document non trouvé dans la base de données."))
            self.preview_area.setPixmap(QPixmap())
            return

        file_path_relative = doc_data.get("file_path_relative")
        client_base_folder_path = self.client_info.get("base_folder_path", self.client_info.get("default_base_folder_path", ""))
        base_folder_abs = os.path.join(self.app_root_dir, client_base_folder_path)
        full_file_path = os.path.join(base_folder_abs, file_path_relative) if base_folder_abs and file_path_relative else None

        if not full_file_path or not os.path.exists(full_file_path):
            self.preview_area.setText(self.tr("Fichier document introuvable sur le disque."))
            self.preview_area.setPixmap(QPixmap())
            return

        doc_type = doc_data.get("document_type_generated", "").upper()

        self.preview_area.setText("") # Clear previous text
        self.preview_area.setPixmap(QPixmap()) # Clear previous pixmap

        if doc_type in ["PNG", "JPG", "JPEG", "BMP", "GIF"]:
            pixmap = QPixmap(full_file_path)
            if not pixmap.isNull():
                # Scale pixmap to fit the label while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(self.preview_area.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.preview_area.setPixmap(scaled_pixmap)
            else:
                self.preview_area.setText(self.tr("Impossible de charger l'aperçu de l'image."))
        elif doc_type == "PDF" and QT_PDF_AVAILABLE:
            if self.pdf_preview_doc: # Release previous document
                del self.pdf_preview_doc
                self.pdf_preview_doc = None

            self.pdf_preview_doc = QPdfDocument(self)
            status = self.pdf_preview_doc.load(full_file_path)

            if status == QPdfDocument.Error:
                self.preview_area.setText(self.tr("Erreur lors du chargement du PDF pour l'aperçu."))
                del self.pdf_preview_doc
                self.pdf_preview_doc = None
                return

            if self.pdf_preview_doc.pageCount() > 0:
                page = self.pdf_preview_doc.page(0) # Preview first page
                # Define a reasonable size for the preview image
                preview_size = QSize(self.preview_area.width() - 20, self.preview_area.height() - 20)
                if preview_size.width() <=0 or preview_size.height() <=0 :
                    preview_size = QSize(200,280) # Fallback size

                # Render with default quality options. For specific quality, QPainter might be needed.
                # The 'mode' argument for renderToImage is not standard in Qt5 QPdfPage.
                # It typically takes (width, height, sourceRect, backgroundColor).
                # For higher quality, one might need to render to a larger QImage then scale down,
                # or use QPainter with specific render hints if drawing manually.
                # For now, let's use the simpler call if specific mode is not critical.
                image = page.renderToImage(preview_size.width(), preview_size.height(), region=page.rect())
                if not image.isNull():
                    pixmap = QPixmap.fromImage(image)
                    # Scale smoothly after rendering to the target preview box size
                    self.preview_area.setPixmap(pixmap.scaled(self.preview_area.width() -10 , self.preview_area.height() -10, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                else:
                    self.preview_area.setText(self.tr("Impossible de générer l'aperçu de la page PDF."))
            else:
                self.preview_area.setText(self.tr("Le document PDF est vide."))
        else:
            self.preview_area.setText(self.tr("Aperçu non disponible pour ce type de document ({0}).").format(doc_type))



    def add_document(self):
        available_languages = SUPPORTED_LANGUAGES
        selected_doc_language, ok = QInputDialog.getItem(
            self, self.tr("Sélectionner la langue"), self.tr("Langue du document:"),
            available_languages, 0, False
        )
        if not ok or not selected_doc_language:
            self.notify(self.tr("Annulé"), self.tr("L'opération d'ajout de document a été annulée."), type='INFO')
            return

        initial_dir = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation) or self.app_root_dir

        selected_file_path, _ = QFileDialog.getOpenFileName(
            self, self.tr("Sélectionner un document"), initial_dir, self.tr("Tous les fichiers (*.*)")
        )

        if selected_file_path:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                client_relative_base_path = self.client_info.get("base_folder_path") or self.client_info.get("default_base_folder_path")
                if not client_relative_base_path:
                    self.notify(self.tr("Erreur Dossier Client"), self.tr("Le chemin du dossier de base du client n'est pas configuré."), type='ERROR')
                    QApplication.restoreOverrideCursor()
                    return

                client_abs_base_path = os.path.join(self.app_root_dir, client_relative_base_path)

                order_identifier_for_path = None
                order_identifier_for_db = None
                current_order_data = self.doc_order_filter_combo.currentData()
                if current_order_data not in ["ALL", "NONE"] and current_order_data is not None:
                    order_identifier_for_db = current_order_data
                    order_identifier_for_path = current_order_data.replace(':', '_').replace('/', '_').replace('\\', '_').replace(' ', '_')
                    target_lang_dir_abs = os.path.join(client_abs_base_path, order_identifier_for_path, selected_doc_language)
                else:
                    target_lang_dir_abs = os.path.join(client_abs_base_path, selected_doc_language)


                os.makedirs(target_lang_dir_abs, exist_ok=True)
                file_name = os.path.basename(selected_file_path)
                target_file_path_abs = os.path.join(target_lang_dir_abs, file_name)

                if os.path.exists(target_file_path_abs):
                    reply = QMessageBox.question(
                        self, self.tr("Fichier Existant"),
                        self.tr("Un fichier du même nom existe déjà ('{0}'). Voulez-vous le remplacer?").format(target_file_path_abs),
                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        QApplication.restoreOverrideCursor()
                        return

                shutil.copy(selected_file_path, target_file_path_abs)

                client_id = self.client_info.get("client_id")
                ext = os.path.splitext(file_name)[1].lower()
                doc_type_map = {".html": "HTML", ".pdf": "PDF", ".xlsx": "XLSX", ".docx": "DOCX"}
                document_type_generated = doc_type_map.get(ext, ext.upper().replace(".", "") or "OTHER")

                sub_path_parts = []
                if order_identifier_for_path: sub_path_parts.append(order_identifier_for_path)
                sub_path_parts.append(selected_doc_language)
                sub_path_parts.append(file_name)
                file_path_relative_to_client_base = os.path.join(*sub_path_parts)

                doc_db_data = {
                    "client_id": client_id, "document_name": file_name,
                    "file_name_on_disk": file_name,
                    "file_path_relative": file_path_relative_to_client_base,
                    "document_type_generated": document_type_generated,
                    "language_code": selected_doc_language, "source_template_id": None,
                    "order_identifier": order_identifier_for_db, "user_id": self.current_user_id,
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
            finally:
                QApplication.restoreOverrideCursor()

    def open_create_docs_dialog_from_parent(self):
        if self.parent_widget and hasattr(self.parent_widget, 'open_create_docs_dialog'):
            self.parent_widget.open_create_docs_dialog()
        else:
            logging.error("DocumentsTab: Parent widget or open_create_docs_dialog method not found.")
            self.notify(self.tr("Erreur"), self.tr("Impossible d'ouvrir le dialogue de création de document."), type='ERROR')

    def open_compile_pdf_dialog_from_parent(self):
        if self.parent_widget and hasattr(self.parent_widget, 'open_compile_pdf_dialog'):
            self.parent_widget.open_compile_pdf_dialog()
        else:
            logging.error("DocumentsTab: Parent widget or open_compile_pdf_dialog method not found.")
            self.notify(self.tr("Erreur"), self.tr("Impossible d'ouvrir le dialogue de compilation PDF."), type='ERROR')

    def handle_edit_html_action(self, file_path, document_id):
        if file_path and os.path.exists(file_path):
            editor = HtmlEditor(file_path, document_id, self)
            if editor.exec_() == QDialog.Accepted:
                self.populate_doc_table()
                self.notify(self.tr("HTML Modifié"), self.tr("Le document HTML a été sauvegardé."), type='SUCCESS')
        else:
            self.notify(self.tr("Fichier Introuvable"), self.tr("Le fichier HTML est introuvable:\n{0}").format(file_path), type='WARNING')

    def handle_edit_excel_action(self, file_path, document_id):
        if file_path and os.path.exists(file_path):
            editor = ExcelEditor(file_path, document_id, self)
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

    def delete_client_document_entry(self, document_id, file_path_abs):
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
        self._update_bulk_action_buttons_state()
        self.populate_doc_table()

[end of client_management/tabs/documents_tab.py]
