# -*- coding: utf-8 -*-
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QApplication
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from app.db.connection import get_db_connection
from app.db.cruds.clients.client_document_notes_crud import (
    get_client_document_notes, get_client_document_note_by_id, delete_client_document_note
)
from app.services.auth.permissions import has_permission, P_MANAGE_CLIENT_DOCUMENTS
from .documents_tab import SUPPORTED_LANGUAGES

class DocumentNotesTab(QWidget):
    def __init__(self, client_info: dict, current_user_info: dict,
                 notification_manager: object,
                 main_module_client_document_note_dialog: callable,
                 parent_widget: QWidget,
                 parent=None):
        super().__init__(parent)
        self.client_info = client_info
        self.current_user_info = current_user_info
        self.notification_manager = notification_manager
        self.ClientDocumentNoteDialog = main_module_client_document_note_dialog
        self.parent_widget = parent_widget

        self._setup_ui()
        self.load_document_notes_filters()
        self.load_document_notes_table()

    def tr(self, text, disambiguation=None, n=-1):
        if self.parent_widget:
            return self.parent_widget.tr(text, disambiguation, n)
        return QApplication.translate("DocumentNotesTab", text, disambiguation, n)

    def _setup_ui(self):
        # UI setup code remains the same
        pass # Omitted for brevity

    def load_document_notes_filters(self):
        # This method doesn't use the DB, so it remains the same
        pass # Omitted for brevity

    def load_document_notes_table(self):
        self.document_notes_table.setRowCount(0)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        client_id = self.client_info.get("client_id")
        if not client_id:
            QApplication.restoreOverrideCursor()
            return

        doc_type_filter = self.doc_notes_type_filter_combo.currentData()
        lang_filter = self.doc_notes_lang_filter_combo.currentData()

        db_session = None
        try:
            db_session = get_db_connection()
            notes = get_client_document_notes(
                db_session, client_id, document_type=doc_type_filter, language_code=lang_filter, is_active=None
            )
            notes = notes if notes else []

            self.document_notes_table.setRowCount(len(notes))
            for row_idx, note in enumerate(notes):
                # UI population logic remains the same
                pass # Omitted for brevity

        except Exception as e:
            logging.error(f"Error loading document notes: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Impossible de charger les notes: {0}").format(str(e)))
        finally:
            if db_session:
                db_session.close()
            QApplication.restoreOverrideCursor()

    def on_add_document_note(self):
        # This method opens a dialog which should manage its own session.
        # The dialog itself will need to be refactored.
        if not self.ClientDocumentNoteDialog:
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Dialogue de note non chargé."))
            return
        dialog = self.ClientDocumentNoteDialog(client_id=self.client_info.get("client_id"), parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_document_notes_table()
            if self.notification_manager: self.notification_manager.show(self.tr("Succès"), self.tr("Note ajoutée."), type='SUCCESS')

    def on_edit_document_note_clicked(self, note_id):
        if not self.ClientDocumentNoteDialog:
            QMessageBox.critical(self, self.tr("Erreur"), self.tr("Dialogue de note non chargé."))
            return

        db_session = None
        try:
            db_session = get_db_connection()
            note_data = get_client_document_note_by_id(db_session, note_id)
            if note_data:
                dialog = self.ClientDocumentNoteDialog(client_id=self.client_info.get("client_id"), note_data=note_data, parent=self)
                if dialog.exec_() == QDialog.Accepted:
                    self.load_document_notes_table()
                    if self.notification_manager: self.notification_manager.show(self.tr("Succès"), self.tr("Note modifiée."), type='SUCCESS')
            else:
                QMessageBox.warning(self, self.tr("Erreur"), self.tr("Note non trouvée."))
        except Exception as e:
            logging.error(f"Error fetching note for editing: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur"), str(e))
        finally:
            if db_session:
                db_session.close()

    def on_delete_document_note_clicked(self, note_id):
        reply = QMessageBox.question(self, self.tr("Confirmer"), self.tr("Supprimer cette note?"), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        db_session = None
        try:
            db_session = get_db_connection()
            if delete_client_document_note(db_session, note_id):
                self.load_document_notes_table()
                if self.notification_manager: self.notification_manager.show(self.tr("Succès"), self.tr("Note supprimée."), type='SUCCESS')
            else:
                QMessageBox.warning(self, self.tr("Échec"), self.tr("Impossible de supprimer la note."))
        except Exception as e:
            logging.error(f"Error deleting document note: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur"), str(e))
        finally:
            if db_session:
                db_session.close()

    def apply_permissions_to_tab(self, can_manage_doc_notes: bool):
        # No DB calls here
        self.add_doc_note_button.setEnabled(can_manage_doc_notes)

    def refresh_tab_data(self):
        self.load_document_notes_filters()
        self.load_document_notes_table()
