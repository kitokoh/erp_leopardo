# -*- coding: utf-8 -*-
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit,
    QComboBox, QPushButton, QMessageBox, QDialogButtonBox
)
from PyQt5.QtCore import Qt

import db # Assuming db module is accessible
from db.cruds import notes_crud

class AddEditDefaultNoteDialog(QDialog):
    def __init__(self, note_data=None, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.note_data_to_edit = note_data # If None, it's an "Add" operation

        if self.note_data_to_edit:
            self.setWindowTitle(self.tr("Modifier la Note par Défaut"))
        else:
            self.setWindowTitle(self.tr("Ajouter une Nouvelle Note par Défaut"))

        self.setMinimumSize(500, 400)
        self._setup_ui()
        self._populate_fields()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.doc_type_combo = QComboBox()
        self.doc_type_combo.setEditable(True) # Allow typing for new types, or use predefined
        # TODO: Populate this dynamically (see DefaultDocumentNotesAdminWidget._load_filters)
        placeholder_doc_types = sorted([
            "contact_page", "sales_contract_excel", "cover_page", "packing_list_html",
            "packing_list_excel", "product_images", "proforma_invoice_html", "proforma_invoice_excel",
            "sales_contract_html", "technical_specs_excel", "technical_specs_html", "warranty_document",
            "OTHER_CUSTOM_TYPE" # Example for custom
        ])
        for dt in placeholder_doc_types:
            self.doc_type_combo.addItem(dt)
        form_layout.addRow(self.tr("Type de Document:"), self.doc_type_combo)

        self.language_combo = QComboBox()
        # TODO: Populate from a central list of supported languages
        supported_languages = ["en", "fr", "ar", "tr", "pt", "ru"]
        for lang in sorted(supported_languages):
            self.language_combo.addItem(lang, lang)
        form_layout.addRow(self.tr("Langue:"), self.language_combo)

        self.note_content_edit = QTextEdit()
        self.note_content_edit.setPlaceholderText(self.tr("Saisissez ici le contenu de la note par défaut..."))
        self.note_content_edit.setMinimumHeight(150)
        form_layout.addRow(self.tr("Contenu de la Note:"), self.note_content_edit)

        main_layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self._on_save_clicked)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

        self.setLayout(main_layout)

    def _populate_fields(self):
        if self.note_data_to_edit:
            doc_type = self.note_data_to_edit.get('document_type')
            lang_code = self.note_data_to_edit.get('language_code')
            content = self.note_data_to_edit.get('note_content')

            # Set Document Type ComboBox
            index_dt = self.doc_type_combo.findText(doc_type, Qt.MatchFixedString)
            if index_dt >= 0:
                self.doc_type_combo.setCurrentIndex(index_dt)
            else: # If type not in list, add it and select
                self.doc_type_combo.addItem(doc_type)
                self.doc_type_combo.setCurrentIndex(self.doc_type_combo.findText(doc_type))

            # Set Language ComboBox
            index_lang = self.language_combo.findData(lang_code) # Assuming lang code is stored as data
            if index_lang >= 0:
                self.language_combo.setCurrentIndex(index_lang)
            else: # Fallback if lang code not found (should not happen if list is consistent)
                 self.language_combo.setCurrentIndex(0)


            self.note_content_edit.setPlainText(content)

    def _on_save_clicked(self):
        doc_type = self.doc_type_combo.currentText().strip()
        language_code = self.language_combo.currentData() # Get data (lang code)
        note_content = self.note_content_edit.toPlainText().strip()

        if not doc_type:
            QMessageBox.warning(self, self.tr("Champ Requis"), self.tr("Le type de document ne peut pas être vide."))
            return
        if not language_code:
            QMessageBox.warning(self, self.tr("Champ Requis"), self.tr("La langue doit être sélectionnée."))
            return
        if not note_content:
            QMessageBox.warning(self, self.tr("Champ Requis"), self.tr("Le contenu de la note ne peut pas être vide."))
            return

        try:
            if self.note_data_to_edit: # Editing existing note
                note_id = self.note_data_to_edit.get('id')
                success = notes_crud.update_default_document_note(
                    note_id=note_id,
                    document_type=doc_type,
                    language_code=language_code,
                    note_content=note_content
                )
                if success:
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Note par défaut mise à jour avec succès."))
                    super().accept()
                else:
                    # Check if it failed due to unique constraint (e.g., changed type/lang to an existing combo)
                    # This is a bit tricky as update_default_document_note returns bool.
                    # A more specific error from CRUD would be helpful.
                    existing_check = notes_crud.get_default_document_note(doc_type, language_code)
                    if existing_check and existing_check['id'] != note_id:
                         QMessageBox.warning(self, self.tr("Échec de la Mise à Jour"),
                                            self.tr("Une autre note existe déjà pour ce type de document et cette langue."))
                    else:
                        QMessageBox.warning(self, self.tr("Échec de la Mise à Jour"),
                                            self.tr("Impossible de mettre à jour la note par défaut. Vérifiez les logs."))
            else: # Adding new note
                new_note_id = notes_crud.add_default_document_note(
                    document_type=doc_type,
                    language_code=language_code,
                    note_content=note_content
                )
                if new_note_id:
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Nouvelle note par défaut ajoutée avec succès."))
                    super().accept()
                else:
                    QMessageBox.warning(self, self.tr("Échec de l'Ajout"),
                                        self.tr("Impossible d'ajouter la note par défaut. Une note pour ce type et cette langue existe peut-être déjà."))
        except Exception as e:
            self.logger.error(f"Error saving default document note: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Critique"),
                                 self.tr("Une erreur critique est survenue : {0}").format(str(e)))

    def get_data(self):
        # This dialog doesn't need to return data, as it performs DB operations directly.
        # If it were to return, it would be:
        # return {
        #     "document_type": self.doc_type_combo.currentText().strip(),
        #     "language_code": self.language_combo.currentData(),
        #     "note_content": self.note_content_edit.toPlainText().strip(),
        #     "id": self.note_data_to_edit.get('id') if self.note_data_to_edit else None
        # }
        return None

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    logging.basicConfig(level=logging.DEBUG)

    # Mock notes_crud for standalone testing if needed
    # class MockNotesCrud:
    #     def get_default_document_note(self, dt, lc): return None
    #     def update_default_document_note(self, **kwargs): return True
    #     def add_default_document_note(self, **kwargs): return 123
    # notes_crud = MockNotesCrud()

    app = QApplication(sys.argv)
    # Test Add mode
    # dialog_add = AddEditDefaultNoteDialog()
    # if dialog_add.exec_() == QDialog.Accepted:
    #     print("Add dialog accepted")

    # Test Edit mode (requires mock data)
    mock_note = {'id': 1, 'document_type': 'proforma_invoice_html', 'language_code': 'fr', 'note_content': 'Ceci est une note de test.'}
    dialog_edit = AddEditDefaultNoteDialog(note_data=mock_note)
    if dialog_edit.exec_() == QDialog.Accepted:
        print("Edit dialog accepted")

    # sys.exit(app.exec_()) # Comment out if just testing class definition
    print("AddEditDefaultNoteDialog class defined.")
