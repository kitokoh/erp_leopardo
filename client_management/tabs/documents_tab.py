# -*- coding: utf-8 -*-
import os
# import sys # No longer used
import logging
import shutil
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QInputDialog, QMessageBox, QFileDialog, QApplication, QSizePolicy
)
from PyQt5.QtGui import QIcon, QDesktopServices, QFont # QFont might be needed for font metrics if advanced stuff is done
from PyQt5.QtCore import Qt, QUrl

import db as db_manager
from db.cruds import client_documents_crud # users_crud removed
from excel_editor import ExcelEditor
from html_editor import HtmlEditor
# Other necessary dialogs and modules will be imported as needed, or passed from parent

# Globals that might be needed directly or passed from parent
SUPPORTED_LANGUAGES = ["en", "fr", "ar", "tr", "pt", "ru"] # Define supported languages

class DocumentsTab(QWidget):
    def __init__(self, client_info: dict, config: object, app_root_dir: str,
                 notification_manager: object, current_user_info: dict,
                 main_module_create_document_dialog: callable,
                 main_module_compile_pdf_dialog: callable,
                 main_module_generate_pdf_for_document: callable,
                 parent_widget: QWidget, # To access methods like tr() and potentially others
                 parent=None):
        super().__init__(parent)
        self.client_info = client_info
        self.config = config
        self.app_root_dir = app_root_dir
        self.notification_manager = notification_manager
        self.current_user_info = current_user_info
        self.current_user_id = self.current_user_info.get('user_id')

        # Store references to main module dialogs/functions passed from parent
        self.CreateDocumentDialog = main_module_create_document_dialog
        self.CompilePdfDialog = main_module_compile_pdf_dialog
        self.generate_pdf_for_document = main_module_generate_pdf_for_document

        self.parent_widget = parent_widget # Reference to ClientMainWidget
        self._is_populating_docs = False # Re-entrancy guard

        self._setup_ui()
        self.populate_doc_table() # Initial population

    def tr(self, text, disambiguation=None, n=-1):
        """Helper to access the parent's tr method for translations."""
        if self.parent_widget:
            return self.parent_widget.tr(text, disambiguation, n)
        return QApplication.translate("DocumentsTab", text, disambiguation, n)


    def _setup_ui(self):
        logging.info("DocumentsTab._setup_ui: Starting setup for Documents Tab Structure...")
        docs_layout = QVBoxLayout(self)

        # Filter layout
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
        self.doc_table.setColumnCount(6) # Nom, Type, Langue, Date, Fichier Original, Actions Rapides
        self.doc_table.setHorizontalHeaderLabels([
            self.tr("Nom"), self.tr("Type"), self.tr("Langue"),
            self.tr("Date"), self.tr("Fichier Original"), self.tr("Actions Rapides")
        ])
        self.doc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.doc_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch) # Nom
        self.doc_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents) # Type
        self.doc_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents) # Langue
        self.doc_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents) # Date
        self.doc_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents) # Fichier Original
        self.doc_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents) # Actions Rapides
        self.doc_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.doc_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        docs_layout.addWidget(self.doc_table)

        doc_btn_layout = QHBoxLayout()
        self.add_doc_btn = QPushButton(self.tr("Importer Document"))
        self.add_doc_btn.setIcon(QIcon(":/icons/file-plus.svg"))
        self.add_doc_btn.setToolTip(self.tr("Importer un fichier document existant pour ce client"))
        self.add_doc_btn.clicked.connect(self.add_document)
        doc_btn_layout.addWidget(self.add_doc_btn)

        self.refresh_docs_btn = QPushButton(self.tr("Actualiser"))
        self.refresh_docs_btn.setIcon(QIcon.fromTheme("view-refresh"))
        self.refresh_docs_btn.clicked.connect(self.populate_doc_table)
        doc_btn_layout.addWidget(self.refresh_docs_btn)

        self.add_template_btn = QPushButton(self.tr("Générer via Modèle"))
        self.add_template_btn.setIcon(QIcon.fromTheme("document-new", QIcon(":/icons/file-plus.svg")))
        self.add_template_btn.setToolTip(self.tr("Générer un nouveau document pour ce client à partir d'un modèle"))
        self.add_template_btn.clicked.connect(self.open_create_docs_dialog_from_parent) # Call parent's method
        doc_btn_layout.addWidget(self.add_template_btn)

        docs_layout.addLayout(doc_btn_layout)
        self._load_order_filters() # Load order filters initially

    def _load_order_filters(self):
        """Populates the order filter combo box for documents."""
        self.doc_order_filter_combo.blockSignals(True)
        self.doc_order_filter_combo.clear()
        self.doc_order_filter_combo.addItem(self.tr("Toutes les Commandes"), "ALL")
        self.doc_order_filter_combo.addItem(self.tr("Documents Généraux (Aucune Commande)"), "NONE")

        client_id = self.client_info.get('client_id')
        if client_id:
            try:
                order_identifiers = db_manager.get_distinct_order_identifiers_for_client(client_id)
                if order_identifiers:
                    for identifier_tuple in order_identifiers:
                        identifier = identifier_tuple[0] # Assuming it returns list of tuples
                        if identifier and identifier.strip():
                             self.doc_order_filter_combo.addItem(identifier, identifier)
            except Exception as e:
                logging.error(f"Error loading order filters for documents: {e}", exc_info=True)
        self.doc_order_filter_combo.blockSignals(False)
        # Set default selection if needed, e.g., "ALL"
        if self.doc_order_filter_combo.count() > 0:
            self.doc_order_filter_combo.setCurrentIndex(0)


    def populate_doc_table(self):
        if self._is_populating_docs: # Prevent re-entrancy
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

        filters = {
            "client_id": client_id,
            "order_identifier": selected_order_identifier if selected_order_identifier not in ["ALL", "NONE"] else None,
            "language_code": selected_language if selected_language != "ALL" else None,
            "document_type_generated": selected_doc_type if selected_doc_type != "ALL" else None,
        }
        if selected_order_identifier == "NONE": # Special case for documents with no order_identifier
            filters["order_identifier_is_null"] = True
            if "order_identifier" in filters: del filters["order_identifier"]


        try:
            documents = client_documents_crud.get_client_documents_with_filters(filters)

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
                    doc_name_item.setData(Qt.UserRole, doc_id) # Store ID for actions
                    self.doc_table.setItem(row_idx, 0, doc_name_item)
                    self.doc_table.setItem(row_idx, 1, QTableWidgetItem(doc.get("document_type_generated")))
                    self.doc_table.setItem(row_idx, 2, QTableWidgetItem(doc.get("language_code")))

                    created_at_str = doc.get("created_at")
                    date_display = ""
                    if created_at_str:
                        try:
                            dt_obj = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                            date_display = dt_obj.strftime('%Y-%m-%d %H:%M')
                        except ValueError:
                            date_display = created_at_str # Fallback
                    self.doc_table.setItem(row_idx, 3, QTableWidgetItem(date_display))

                    # Original File Link (if applicable)
                    original_file_path = doc.get("file_path_original")
                    if original_file_path:
                        link_widget = QLabel(f"<a href='file:///{original_file_path}'>{os.path.basename(original_file_path)}</a>")
                        link_widget.setOpenExternalLinks(True)
                        self.doc_table.setCellWidget(row_idx, 4, link_widget)
                    else:
                        self.doc_table.setItem(row_idx, 4, QTableWidgetItem(self.tr("N/A")))

                    # Action Buttons
                    actions_widget = QWidget()
                    actions_layout = QHBoxLayout(actions_widget)
                    actions_layout.setContentsMargins(2,2,2,2); actions_layout.setSpacing(3)

                    # Edit (conditionally based on type)
                    file_path_relative = doc.get("file_path_relative")
                    base_folder = self.client_info.get("base_folder_path", "")
                    full_file_path = os.path.join(base_folder, file_path_relative) if base_folder and file_path_relative else None

                    if full_file_path and os.path.exists(full_file_path):
                        if doc.get("document_type_generated") == "HTML":
                            edit_btn = QPushButton(QIcon(":/icons/edit.svg"), "") # Placeholder icon
                            edit_btn.setToolTip(self.tr("Modifier HTML"))
                            edit_btn.clicked.connect(lambda checked, p=full_file_path, d_id=doc_id: self.handle_edit_html_action(p, d_id))
                            actions_layout.addWidget(edit_btn)
                        elif doc.get("document_type_generated") == "XLSX":
                            edit_btn = QPushButton(QIcon(":/icons/edit.svg"), "")
                            edit_btn.setToolTip(self.tr("Modifier Excel"))
                            edit_btn.clicked.connect(lambda checked, p=full_file_path, d_id=doc_id: self.handle_edit_excel_action(p, d_id))
                            actions_layout.addWidget(edit_btn)
                        elif doc.get("document_type_generated") == "PDF": # View PDF
                            view_btn = QPushButton(QIcon(":/icons/eye.svg"), "") # Placeholder icon
                            view_btn.setToolTip(self.tr("Ouvrir PDF"))
                            view_btn.clicked.connect(lambda checked, p=full_file_path, d_id=doc_id: self._handle_edit_pdf_action(p, d_id)) # Renamed to reflect generic open
                            actions_layout.addWidget(view_btn)
                        # Add other types like DOCX if an editor is available

                    # Create New Version (if source_template_id exists)
                    if doc.get("source_template_id"):
                        version_btn = QPushButton(QIcon(":/icons/copy.svg"), "") # Placeholder
                        version_btn.setToolTip(self.tr("Créer une nouvelle version"))
                        version_btn.clicked.connect(lambda checked, old_id=doc_id, t_id=doc.get("source_template_id"): self.handle_create_new_version_clicked(old_id, t_id))
                        actions_layout.addWidget(version_btn)

                    # Delete
                    delete_btn = QPushButton(QIcon(":/icons/trash.svg"), "") # Placeholder
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
        # This method is almost identical to the one in ClientMainWidget
        # It needs self.client_info, self.config, self.current_user_id, self.tr
        available_languages = ["en", "fr", "ar", "tr", "pt"]
        selected_doc_language, ok = QInputDialog.getItem(
            self, self.tr("Sélectionner la langue"), self.tr("Langue du document:"),
            available_languages, 0, False
        )
        if not ok or not selected_doc_language:
            QMessageBox.information(self, self.tr("Annulé"), self.tr("L'opération d'ajout de document a été annulée."))
            return

        initial_dir = self.config.get("clients_dir", os.path.expanduser("~"))
        selected_file_path, _ = QFileDialog.getOpenFileName(
            self, self.tr("Sélectionner un document"), initial_dir, self.tr("Tous les fichiers (*.*)")
        )

        if selected_file_path:
            try:
                client_base_path = self.client_info.get("base_folder_path")
                if not client_base_path:
                    client_base_path = self.client_info.get("default_base_folder_path", "")
                if not client_base_path or not os.path.isdir(client_base_path):
                    QMessageBox.warning(self, self.tr("Erreur Dossier Client"), self.tr("Le chemin du dossier de base du client n'est pas configuré ou est invalide."))
                    return

                target_dir = os.path.join(client_base_path, selected_doc_language)
                # Simplified: For imported docs, order_identifier handling is deferred or part of CreateDocumentDialog.
                # Here, we focus on general documents or assume order_identifier is handled by the dialog if used.

                os.makedirs(target_dir, exist_ok=True)
                file_name = os.path.basename(selected_file_path)
                target_file_path = os.path.join(target_dir, file_name)

                if os.path.exists(target_file_path):
                    reply = QMessageBox.question(
                        self, self.tr("Fichier Existant"),
                        self.tr("Un fichier du même nom existe déjà. Voulez-vous le remplacer?"),
                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                    )
                    if reply == QMessageBox.No: return

                shutil.copy(selected_file_path, target_file_path)

                client_id = self.client_info.get("client_id")
                ext = os.path.splitext(file_name)[1].lower()
                doc_type_map = {".html": "HTML", ".pdf": "PDF", ".xlsx": "XLSX", ".docx": "DOCX"}
                document_type_generated = doc_type_map.get(ext, ext.upper().replace(".", "") or "OTHER")

                order_identifier = None # Default for imported general docs
                # If an order is selected in the filter, use it
                current_order_data = self.doc_order_filter_combo.currentData()
                if current_order_data not in ["ALL", "NONE"]:
                    order_identifier = current_order_data

                doc_db_data = {
                    "client_id": client_id, "document_name": file_name,
                    "file_name_on_disk": file_name,
                    "file_path_relative": os.path.join(selected_doc_language, file_name),
                    "document_type_generated": document_type_generated,
                    "language_code": selected_doc_language, "source_template_id": None,
                    "order_identifier": order_identifier, "user_id": self.current_user_id,
                    "notes": None, "version_tag": "1.0"
                }
                new_doc_id = db_manager.add_client_document(doc_db_data)
                if new_doc_id:
                    self.notification_manager.show(self.tr("Succès"), self.tr("Document importé."), type='SUCCESS')
                    self.populate_doc_table()
                else:
                    self.notification_manager.show(self.tr("Erreur DB"), self.tr("Échec de l'enregistrement DB."), type='ERROR')

            except Exception as e:
                logging.error(f"Error adding document: {e}", exc_info=True)
                self.notification_manager.show(self.tr("Erreur"), str(e), type='CRITICAL')

    def open_create_docs_dialog_from_parent(self):
        """Calls the parent's method to open the CreateDocumentDialog."""
        if self.parent_widget and hasattr(self.parent_widget, 'open_create_docs_dialog'):
            self.parent_widget.open_create_docs_dialog()
        else:
            logging.error("DocumentsTab: Parent widget or open_create_docs_dialog method not found.")
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible d'ouvrir le dialogue de création de document."))

    def open_compile_pdf_dialog_from_parent(self):
        """Calls the parent's method to open the CompilePdfDialog."""
        if self.parent_widget and hasattr(self.parent_widget, 'open_compile_pdf_dialog'):
            self.parent_widget.open_compile_pdf_dialog()
        else:
            logging.error("DocumentsTab: Parent widget or open_compile_pdf_dialog method not found.")
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible d'ouvrir le dialogue de compilation PDF."))

    def handle_edit_html_action(self, file_path, document_id):
        if file_path and os.path.exists(file_path):
            editor = HtmlEditor(file_path, document_id, self)
            if editor.exec_() == QDialog.Accepted:
                self.populate_doc_table()
        else:
            QMessageBox.warning(self, self.tr("Fichier Introuvable"), self.tr("Le fichier HTML est introuvable."))

    def handle_edit_excel_action(self, file_path, document_id):
        if file_path and os.path.exists(file_path):
            editor = ExcelEditor(file_path, document_id, self)
            if editor.exec_() == QDialog.Accepted:
                self.populate_doc_table()
        else:
            QMessageBox.warning(self, self.tr("Fichier Introuvable"), self.tr("Le fichier Excel est introuvable."))

    def _handle_edit_pdf_action(self, file_path, document_id): # Renamed from handle_edit_pdf_action for clarity
        if file_path and os.path.exists(file_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
        else:
            QMessageBox.warning(self, self.tr("Fichier Introuvable"), self.tr("Le fichier PDF est introuvable."))

    def handle_create_new_version_clicked(self, old_document_id, source_template_id):
        if not self.client_info or not self.client_info.get('client_id'):
            QMessageBox.warning(self, self.tr("Erreur Client"), self.tr("Informations client non disponibles."))
            return
        if not old_document_id or not source_template_id:
            QMessageBox.warning(self, self.tr("Données Manquantes"), self.tr("ID du document original ou ID du modèle source manquant."))
            return

        if not self.CreateDocumentDialog:
            logging.error("CreateDocumentDialog is not available in DocumentsTab.")
            QMessageBox.critical(self, self.tr("Erreur Composant"), self.tr("Le composant de création de document n'est pas chargé."))
            return

        dialog = self.CreateDocumentDialog(
            client_info=self.client_info,
            config=self.config,
            current_user_id=self.current_user_id,
            parent=self, # Parent for the dialog is this tab widget
            template_data={'template_id': source_template_id},
            old_document_id_to_version=old_document_id
        )
        if dialog.exec_() == QDialog.Accepted:
            self.populate_doc_table()
            self.notification_manager.show(self.tr("Nouvelle Version Créée"), self.tr("Nouvelle version créée."), type='SUCCESS')

    def delete_client_document_entry(self, document_id, file_path):
        if not document_id:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("ID du document manquant."))
            return

        file_display_name = os.path.basename(file_path) if file_path else self.tr("Inconnu")
        reply = QMessageBox.question(self, self.tr("Confirmer Suppression"),
                                     self.tr("Supprimer document ID {0} et fichier '{1}'?").format(document_id, file_display_name),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                db_deleted = db_manager.delete_client_document(document_id)
                if db_deleted:
                    if file_path and os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            self.notification_manager.show(self.tr("Succès"), self.tr("Document et fichier supprimés."), type='SUCCESS')
                        except OSError as e_file:
                            self.notification_manager.show(self.tr("Erreur Fichier"), self.tr("DB supprimé, échec suppression fichier: {0}").format(str(e_file)), type='ERROR')
                    else:
                         self.notification_manager.show(self.tr("Succès (Partiel)"), self.tr("DB supprimé. Fichier non trouvé."), type='WARNING')
                else:
                    self.notification_manager.show(self.tr("Erreur DB"), self.tr("Échec suppression DB."), type='ERROR')
            except Exception as e:
                self.notification_manager.show(self.tr("Erreur Suppression"), str(e), type='CRITICAL')
            finally:
                self.populate_doc_table()

    def notify(self, title, message, type='INFO'): # Convenience for notifications
        if self.notification_manager:
            self.notification_manager.show(title, message, type=type)
        else: # Fallback if notification_manager is None
            if type == 'ERROR' or type == 'CRITICAL':
                QMessageBox.critical(self, title, message)
            elif type == 'WARNING':
                QMessageBox.warning(self, title, message)
            else:
                QMessageBox.information(self, title, message)

    def refresh_tab_data(self):
        """Public method to refresh data, called by parent if needed."""
        self._load_order_filters() # Reload filters in case new orders were added
        self.populate_doc_table()

    def apply_permissions_to_tab(self, can_manage_documents: bool):
        """Applies permissions to buttons within this tab."""
        if hasattr(self, 'add_doc_btn'):
            self.add_doc_btn.setEnabled(can_manage_documents)
        if hasattr(self, 'add_template_btn'):
            self.add_template_btn.setEnabled(can_manage_documents)
        # Permissions for action buttons in the table are handled dynamically during populate_doc_table
        # based on the same can_manage_documents flag, or more granular if needed.
        # For example, delete_client_document_entry and handle_create_new_version_clicked
        # implicitly check this by enabling/disabling the buttons that call them.
        # If direct calls to these methods are possible elsewhere, they should also check permissions.
        # The action buttons in the table will be hidden/disabled by populate_doc_table if can_manage_documents is False.

        # Also, ensure the table itself respects read-only if no management rights.
        # This is generally handled by not providing edit/delete buttons.
        # If table had direct editing, it would need to be setReadOnly(!can_manage_documents)

# ```
