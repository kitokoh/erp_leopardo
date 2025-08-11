import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox,
    QMessageBox, QLabel
)
from PyQt5.QtCore import Qt
import app.db # Assuming db.__init__ exposes notes_crud

class EditDocumentNoteDialog(QDialog):
    def __init__(self, document_id, document_type, language_code, parent=None):
        super().__init__(parent)
        self.document_id = document_id # This is ClientDocuments.document_id
        self.document_type = document_type
        self.language_code = language_code
        self.logger = logging.getLogger(__name__)

        self.setWindowTitle(self.tr("Modifier la Note du Document"))
        self.setMinimumSize(400, 300)

        self.setup_ui()
        self.load_current_note()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Info labels
        info_label_text = self.tr(
            f"Document ID: {self.document_id}\n"
            f"Type: {self.document_type}\n"
            f"Langue: {self.language_code}"
        )
        info_label = QLabel(info_label_text)
        main_layout.addWidget(info_label)

        self.note_text_edit = QTextEdit()
        self.note_text_edit.setPlaceholderText(self.tr("Entrez la note pour ce document..."))
        main_layout.addWidget(self.note_text_edit)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.save_note)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

        self.setLayout(main_layout)

    def load_current_note(self):
        try:
            # get_effective_document_note expects commande_document_id, which is our self.document_id
            effective_note = db.notes_crud.get_effective_document_note(
                commande_document_id=self.document_id,
                document_type=self.document_type,
                language_code=self.language_code
            )
            if effective_note:
                self.note_text_edit.setPlainText(effective_note)
            else:
                # If no note exists (neither custom nor default), placeholder will show.
                # We could also pre-fill with a message indicating no default note was found.
                # For now, empty is fine, relying on placeholder.
                self.logger.info(f"No existing effective note found for doc_id {self.document_id}, type {self.document_type}, lang {self.language_code}. Editor will be blank or show placeholder.")

        except Exception as e:
            self.logger.error(f"Error loading note for document {self.document_id}: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur Chargement Note"),
                                self.tr("Impossible de charger la note actuelle : {0}").format(str(e)))
            # Default to empty text edit if load fails
            self.note_text_edit.setPlainText("")


    def save_note(self):
        new_note_content = self.note_text_edit.toPlainText().strip()

        try:
            # upsert_commande_document_note handles creating new or updating existing custom note
            # It needs commande_document_id, which is our self.document_id
            result_id = db.notes_crud.upsert_commande_document_note(
                commande_document_id=self.document_id,
                note_content=new_note_content,
                language_code=self.language_code # Store with the document's language
            )

            if result_id is not None:
                self.logger.info(f"Note for document {self.document_id} saved/updated successfully (ID: {result_id}).")
                super().accept() # Close dialog with QDialog.Accepted result
            else:
                QMessageBox.warning(self, self.tr("Erreur Sauvegarde"),
                                    self.tr("Impossible de sauvegarder la note. Vérifiez les logs."))
        except Exception as e:
            self.logger.error(f"Error saving note for document {self.document_id}: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Critique"),
                                 self.tr("Une erreur critique est survenue lors de la sauvegarde de la note : {0}").format(str(e)))

    @staticmethod
    def get_note(document_id, document_type, language_code, parent=None):
        """Static method to launch the dialog and return the outcome."""
        dialog = EditDocumentNoteDialog(document_id, document_type, language_code, parent)
        result = dialog.exec_()
        return result == QDialog.Accepted

if __name__ == '__main__':
    # This example won't run correctly without a QApplication and a DB connection.
    # It's primarily for structural reference.
    # To test, you'd need to mock db.notes_crud or set up a test DB.
    print("EditDocumentNoteDialog class defined. For testing, integrate into an application.")
    # from PyQt5.QtWidgets import QApplication
    # import sys
    # app = QApplication(sys.argv)
    # # Setup mock db.notes_crud here if needed for standalone test
    # # dialog = EditDocumentNoteDialog("doc_123", "proforma_invoice", "fr")
    # # dialog.show()
    # # sys.exit(app.exec_())
