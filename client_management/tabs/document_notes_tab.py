# -*- coding: utf-8 -*-
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QApplication
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

import db as db_manager
from auth.permissions import has_permission, P_MANAGE_CLIENT_DOCUMENTS # For button permissions
# Import SUPPORTED_LANGUAGES, assuming documents_tab is a sibling or from a central const
from .documents_tab import SUPPORTED_LANGUAGES

# Assuming ClientDocumentNoteDialog is passed or imported if self-contained
# For now, it will be passed via constructor from ClientMainWidget

class DocumentNotesTab(QWidget):
    def __init__(self, client_info: dict, current_user_info: dict,
                 notification_manager: object,
                 main_module_client_document_note_dialog: callable,
                 parent_widget: QWidget, # To access tr()
                 parent=None):
        super().__init__(parent)
        self.client_info = client_info
        self.current_user_info = current_user_info
        self.notification_manager = notification_manager
        self.ClientDocumentNoteDialog = main_module_client_document_note_dialog
        self.parent_widget = parent_widget

        self._setup_ui()
        self.load_document_notes_filters() # Load filters first
        self.load_document_notes_table()   # Then load table data

    def tr(self, text, disambiguation=None, n=-1):
        """Helper to access the parent's tr method for translations."""
        if self.parent_widget:
            return self.parent_widget.tr(text, disambiguation, n)
        return QApplication.translate("DocumentNotesTab", text, disambiguation, n)

    def _setup_ui(self):
        logging.info("DocumentNotesTab._setup_ui: Starting setup...")
        doc_notes_layout = QVBoxLayout(self)

        # Filters
        doc_notes_filters_layout = QHBoxLayout()
        doc_notes_filters_layout.addWidget(QLabel(self.tr("Type de Document:")))
        self.doc_notes_type_filter_combo = QComboBox()
        doc_notes_filters_layout.addWidget(self.doc_notes_type_filter_combo)

        doc_notes_filters_layout.addWidget(QLabel(self.tr("Langue:")))
        self.doc_notes_lang_filter_combo = QComboBox()
        doc_notes_filters_layout.addWidget(self.doc_notes_lang_filter_combo)
        doc_notes_filters_layout.addStretch()
        doc_notes_layout.addLayout(doc_notes_filters_layout)

        # Table
        self.document_notes_table = QTableWidget()
        self.document_notes_table.setColumnCount(6) # Type, Lang, Content, Standard, Active, Actions
        self.document_notes_table.setHorizontalHeaderLabels([
            self.tr("Type Document"), self.tr("Langue"),
            self.tr("Contenu de la Note"), self.tr("Standard"), self.tr("Actif"), self.tr("Actions")
        ])
        self.document_notes_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch) # Content
        self.document_notes_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents) # Standard
        self.document_notes_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents) # Active
        self.document_notes_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents) # Actions
        self.document_notes_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.document_notes_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        doc_notes_layout.addWidget(self.document_notes_table)

        # Buttons
        doc_notes_buttons_layout = QHBoxLayout()
        self.add_doc_note_button = QPushButton(self.tr("Ajouter Note"))
        self.add_doc_note_button.setIcon(QIcon.fromTheme("document-new"))
        doc_notes_buttons_layout.addWidget(self.add_doc_note_button)

        self.refresh_doc_notes_button = QPushButton(self.tr("Actualiser Liste"))
        self.refresh_doc_notes_button.setIcon(QIcon.fromTheme("view-refresh"))
        doc_notes_buttons_layout.addWidget(self.refresh_doc_notes_button)
        doc_notes_buttons_layout.addStretch()
        doc_notes_layout.addLayout(doc_notes_buttons_layout)

        # Connections
        self.doc_notes_type_filter_combo.currentIndexChanged.connect(self.load_document_notes_table)
        self.doc_notes_lang_filter_combo.currentIndexChanged.connect(self.load_document_notes_table)
        self.add_doc_note_button.clicked.connect(self.on_add_document_note)
        self.refresh_doc_notes_button.clicked.connect(self.load_document_notes_table)

    def load_document_notes_filters(self):
        self.doc_notes_type_filter_combo.blockSignals(True)
        self.doc_notes_lang_filter_combo.blockSignals(True)

        self.doc_notes_type_filter_combo.clear()
        self.doc_notes_type_filter_combo.addItem(self.tr("Tous Types"), None)
        # These should ideally come from a config or db_manager
        doc_types = ["Proforma", "Packing List", "Sales Conditions", "Certificate of Origin", "Bill of Lading", "Other"]
        for doc_type in doc_types:
            self.doc_notes_type_filter_combo.addItem(doc_type, doc_type)

        self.doc_notes_lang_filter_combo.clear()
        self.doc_notes_lang_filter_combo.addItem(self.tr("Toutes Langues"), None)
        # Should use SUPPORTED_LANGUAGES if available globally or passed
        langs = ["fr", "en", "ar", "tr", "pt"] # Example
        for lang in langs: # Replace with actual list of supported languages
            self.doc_notes_lang_filter_combo.addItem(lang, lang)

        self.doc_notes_type_filter_combo.blockSignals(False)
        self.doc_notes_lang_filter_combo.blockSignals(False)
        self.doc_notes_type_filter_combo.setCurrentIndex(0)
        self.doc_notes_lang_filter_combo.setCurrentIndex(0)

    def load_document_notes_table(self):
        self.document_notes_table.setRowCount(0)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        client_id = self.client_info.get("client_id")
        if not client_id:
            QApplication.restoreOverrideCursor()
            return

        doc_type_filter = self.doc_notes_type_filter_combo.currentData()
        lang_filter = self.doc_notes_lang_filter_combo.currentData()

        try:
            notes = db_manager.get_client_document_notes(
                client_id, document_type=doc_type_filter, language_code=lang_filter, is_active=None
            )
            notes = notes if notes else []

            self.document_notes_table.setRowCount(len(notes))
            for row_idx, note in enumerate(notes):
                note_id = note.get("note_id")
                type_item = QTableWidgetItem(note.get("document_type"))
                type_item.setData(Qt.UserRole, note_id)
                self.document_notes_table.setItem(row_idx, 0, type_item)
                self.document_notes_table.setItem(row_idx, 1, QTableWidgetItem(note.get("language_code")))

                note_content = note.get("note_content", "")
                lines = [line.strip() for line in note_content.split('\n') if line.strip()]
                html_content = "<ol style='margin:0px; padding-left: 15px;'>" + "".join([f"<li>{line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')}</li>" for line in lines]) + "</ol>" if lines else f"<p style='margin:0px; font-style:italic;'>{self.tr('Aucune note.')}</p>"
                note_label = QLabel(html_content); note_label.setWordWrap(True)
                self.document_notes_table.setCellWidget(row_idx, 2, note_label)

                standard_text = self.tr("Oui") if note.get("is_standard") else self.tr("Non") # Assuming 'is_standard' field
                standard_item = QTableWidgetItem(standard_text); standard_item.setTextAlignment(Qt.AlignCenter)
                self.document_notes_table.setItem(row_idx, 3, standard_item)

                active_text = self.tr("Oui") if note.get("is_active") else self.tr("Non")
                active_item = QTableWidgetItem(active_text); active_item.setTextAlignment(Qt.AlignCenter)
                self.document_notes_table.setItem(row_idx, 4, active_item)

                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(5,0,5,0); actions_layout.setSpacing(5)

                role_name = self.current_user_info.get('role_name')
                can_manage = has_permission(role_name, P_MANAGE_CLIENT_DOCUMENTS) # Or a more specific permission

                if can_manage:
                    edit_btn = QPushButton(QIcon(":/icons/pencil.svg"), ""); edit_btn.setToolTip(self.tr("Modifier"))
                    edit_btn.clicked.connect(lambda ch, nid=note_id: self.on_edit_document_note_clicked(nid))
                    actions_layout.addWidget(edit_btn)

                    delete_btn = QPushButton(QIcon(":/icons/trash.svg"), ""); delete_btn.setToolTip(self.tr("Supprimer"))
                    delete_btn.setObjectName("dangerButton")
                    delete_btn.clicked.connect(lambda ch, nid=note_id: self.on_delete_document_note_clicked(nid))
                    actions_layout.addWidget(delete_btn)

                actions_layout.addStretch()
                self.document_notes_table.setCellWidget(row_idx, 5, actions_widget)

            for i in [0,1,3,4,5]: self.document_notes_table.resizeColumnToContents(i)

        except Exception as e:
            logging.error(f"Error loading document notes: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Impossible de charger les notes: {0}").format(str(e)))
        finally:
            QApplication.restoreOverrideCursor()

    def on_add_document_note(self):
        if not self.ClientDocumentNoteDialog:
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Dialogue de note non chargé."))
            return
        dialog = self.ClientDocumentNoteDialog(client_id=self.client_info.get("client_id"), parent=self)
        if dialog.exec_() == QMessageBox.Accepted: # Assuming QDialog.Accepted
            self.load_document_notes_table()
            if self.notification_manager: self.notification_manager.show(self.tr("Succès"), self.tr("Note ajoutée."), type='SUCCESS')

    def on_edit_document_note_clicked(self, note_id):
        if not self.ClientDocumentNoteDialog:
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Dialogue de note non chargé."))
            return
        note_data = db_manager.get_client_document_note_by_id(note_id)
        if note_data:
            dialog = self.ClientDocumentNoteDialog(client_id=self.client_info.get("client_id"), note_data=note_data, parent=self)
            if dialog.exec_() == QMessageBox.Accepted: # Assuming QDialog.Accepted
                self.load_document_notes_table()
                if self.notification_manager: self.notification_manager.show(self.tr("Succès"), self.tr("Note modifiée."), type='SUCCESS')
        else:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Note non trouvée."))

    def on_delete_document_note_clicked(self, note_id):
        reply = QMessageBox.question(self, self.tr("Confirmer"), self.tr("Supprimer cette note?"), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                if db_manager.delete_client_document_note(note_id):
                    self.load_document_notes_table()
                    if self.notification_manager: self.notification_manager.show(self.tr("Succès"), self.tr("Note supprimée."), type='SUCCESS')
                else:
                    QMessageBox.warning(self, self.tr("Échec"), self.tr("Impossible de supprimer la note."))
            except Exception as e:
                logging.error(f"Error deleting document note: {e}", exc_info=True)
                QMessageBox.critical(self, self.tr("Erreur"), str(e))

    def apply_permissions_to_tab(self, can_manage_doc_notes: bool):
        self.add_doc_note_button.setEnabled(can_manage_doc_notes)
        # Edit/delete buttons in table are handled by load_document_notes_table based on permissions
        # If table was directly editable:
        # self.document_notes_table.setEditTriggers(QAbstractItemView.NoEditTriggers if not can_manage_doc_notes else QAbstractItemView.DoubleClicked)

    def refresh_tab_data(self):
        self.load_document_notes_filters()
        self.load_document_notes_table()

```
