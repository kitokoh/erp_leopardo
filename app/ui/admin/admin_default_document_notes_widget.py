# -*- coding: utf-8 -*-
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableWidget,
    QComboBox, QHeaderView, QMessageBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

# Assuming db module is accessible from project root
import db
from db.cruds import notes_crud

from .admin_add_edit_default_note_dialog import AddEditDefaultNoteDialog

class DefaultDocumentNotesAdminWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.setWindowTitle(self.tr("Administration des Notes de Document par Défaut"))
        self.setMinimumSize(800, 600)

        self._setup_ui()
        self._load_filters()
        self._load_notes_table()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- Header ---
        header_label = QLabel(self.tr("Gestion des Notes de Document par Défaut"))
        header_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        main_layout.addWidget(header_label)

        # --- Filters ---
        filter_group_layout = QHBoxLayout()

        filter_group_layout.addWidget(QLabel(self.tr("Type de Document:")))
        self.doc_type_filter_combo = QComboBox()
        self.doc_type_filter_combo.setMinimumWidth(200)
        filter_group_layout.addWidget(self.doc_type_filter_combo)

        filter_group_layout.addWidget(QLabel(self.tr("Langue:")))
        self.language_filter_combo = QComboBox()
        self.language_filter_combo.setMinimumWidth(100)
        filter_group_layout.addWidget(self.language_filter_combo)

        self.apply_filters_btn = QPushButton(self.tr("Appliquer Filtres"))
        self.apply_filters_btn.setIcon(QIcon.fromTheme("view-refresh"))
        self.apply_filters_btn.clicked.connect(self._load_notes_table)
        filter_group_layout.addWidget(self.apply_filters_btn)

        filter_group_layout.addStretch()
        main_layout.addLayout(filter_group_layout)

        # --- Table for Default Notes ---
        self.notes_table = QTableWidget()
        self.notes_table.setColumnCount(5) # ID, Type, Langue, Aperçu Note, Actions
        self.notes_table.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Type Document"), self.tr("Langue"),
            self.tr("Aperçu Note"), self.tr("Actions")
        ])
        self.notes_table.setColumnHidden(0, True) # Hide ID column
        self.notes_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.notes_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.notes_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.notes_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.notes_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.notes_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.notes_table.setAlternatingRowColors(True)
        main_layout.addWidget(self.notes_table)

        # --- Action Buttons ---
        action_buttons_layout = QHBoxLayout()
        self.add_note_btn = QPushButton(QIcon.fromTheme("list-add"), self.tr("Ajouter une Note par Défaut"))
        self.add_note_btn.clicked.connect(self._on_add_note_clicked)
        action_buttons_layout.addWidget(self.add_note_btn)

        action_buttons_layout.addStretch()
        main_layout.addLayout(action_buttons_layout)

        self.setLayout(main_layout)

    def _load_filters(self):
        self.logger.debug("Loading filters...")
        # Document Types Filter
        self.doc_type_filter_combo.blockSignals(True)
        self.doc_type_filter_combo.clear()
        self.doc_type_filter_combo.addItem(self.tr("Tous les Types"), None)
        # TODO: Dynamically populate this from `resources/templates` or a predefined list
        # For now, using a placeholder list based on previous findings
        placeholder_doc_types = sorted([
            "contact_page", "sales_contract_excel", "cover_page", "packing_list_html",
            "packing_list_excel", "product_images", "proforma_invoice_html", "proforma_invoice_excel",
            "sales_contract_html", "technical_specs_excel", "technical_specs_html", "warranty_document"
        ])
        for doc_type in placeholder_doc_types:
            self.doc_type_filter_combo.addItem(doc_type, doc_type)
        self.doc_type_filter_combo.blockSignals(False)

        # Language Filter
        self.language_filter_combo.blockSignals(True)
        self.language_filter_combo.clear()
        self.language_filter_combo.addItem(self.tr("Toutes les Langues"), None)
        # TODO: Get from a central config or list
        supported_languages = ["en", "fr", "ar", "tr", "pt", "ru"]
        for lang_code in sorted(supported_languages):
            self.language_filter_combo.addItem(lang_code, lang_code)
        self.language_filter_combo.blockSignals(False)

        self.logger.debug("Filters loaded.")

    def _load_notes_table(self):
        self.logger.info("Loading default document notes into table...")
        self.notes_table.setRowCount(0) # Clear table

        # TODO: Apply filters from combo boxes when calling notes_crud.list_default_document_notes()
        # For now, it lists all. The CRUD function itself might need filter parameters.
        # For simplicity in this step, we'll filter client-side after fetching all.

        try:
            all_notes = notes_crud.list_default_document_notes()
            if all_notes is None:
                self.logger.warning("list_default_document_notes returned None. Assuming empty list.")
                all_notes = []

            # Client-side filtering (temporary, ideally done in DB query)
            selected_doc_type = self.doc_type_filter_combo.currentData()
            selected_lang_code = self.language_filter_combo.currentData()

            filtered_notes = []
            for note in all_notes:
                match_doc_type = (selected_doc_type is None or note.get('document_type') == selected_doc_type)
                match_lang_code = (selected_lang_code is None or note.get('language_code') == selected_lang_code)
                if match_doc_type and match_lang_code:
                    filtered_notes.append(note)

            self.notes_table.setRowCount(len(filtered_notes))

            for row_idx, note_data in enumerate(filtered_notes):
                note_id = note_data.get('id')

                id_item = QTableWidgetItem(str(note_id))
                # id_item.setData(Qt.UserRole, note_id) # Storing ID in UserRole is good practice
                self.notes_table.setItem(row_idx, 0, id_item)

                self.notes_table.setItem(row_idx, 1, QTableWidgetItem(note_data.get('document_type', 'N/A')))
                self.notes_table.setItem(row_idx, 2, QTableWidgetItem(note_data.get('language_code', 'N/A')))

                content = note_data.get('note_content', '')
                preview = (content[:100] + '...') if len(content) > 100 else content
                content_item = QTableWidgetItem(preview)
                content_item.setToolTip(content) # Show full content on hover
                self.notes_table.setItem(row_idx, 3, content_item)

                # Actions cell
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0,0,0,0)
                actions_layout.setSpacing(5)

                edit_btn = QPushButton(QIcon.fromTheme("document-edit"), self.tr("Modifier"))
                edit_btn.clicked.connect(lambda ch, n_id=note_id: self._on_edit_note_clicked(n_id))
                actions_layout.addWidget(edit_btn)

                delete_btn = QPushButton(QIcon.fromTheme("edit-delete"), self.tr("Supprimer"))
                delete_btn.clicked.connect(lambda ch, n_id=note_id: self._on_delete_note_clicked(n_id))
                actions_layout.addWidget(delete_btn)

                actions_layout.addStretch()
                self.notes_table.setCellWidget(row_idx, 4, actions_widget)

        except Exception as e:
            self.logger.error(f"Error loading notes into table: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur de Chargement"),
                                 self.tr("Impossible de charger les notes par défaut : {0}").format(str(e)))

        self.logger.info(f"Table loaded with {self.notes_table.rowCount()} notes.")

    def _on_add_note_clicked(self):
        self.logger.debug("Add new default note button clicked.")
        dialog = AddEditDefaultNoteDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self._load_notes_table()


    def _on_edit_note_clicked(self, note_id):
        self.logger.debug(f"Edit default note button clicked for ID: {note_id}")

        # We need a way to get the full note data by ID from notes_crud
        # Let's assume notes_crud.get_default_document_note_by_id(note_id) exists or is added.
        # For now, we can try to find it in the currently loaded list (less ideal but works if list is complete)
        note_data_to_edit = None
        all_notes = notes_crud.list_default_document_notes() # Re-fetch to ensure data is fresh
        if all_notes:
            for note in all_notes:
                if note.get('id') == note_id:
                    note_data_to_edit = note
                    break

        if note_data_to_edit:
            dialog = AddEditDefaultNoteDialog(note_data=note_data_to_edit, parent=self)
            if dialog.exec_() == QDialog.Accepted:
                self._load_notes_table()
        else:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Note avec ID {0} non trouvée ou données de la note inaccessibles.").format(note_id))


    def _on_delete_note_clicked(self, note_id):
        self.logger.debug(f"Delete default note button clicked for ID: {note_id}")
        reply = QMessageBox.question(self, self.tr("Confirmer Suppression"),
                                     self.tr("Êtes-vous sûr de vouloir supprimer cette note par défaut (ID: {0})?").format(note_id),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                success = notes_crud.delete_default_document_note(note_id)
                if success:
                    QMessageBox.information(self, self.tr("Succès"), self.tr("Note par défaut supprimée avec succès."))
                    self._load_notes_table()
                else:
                    QMessageBox.warning(self, self.tr("Échec"), self.tr("Impossible de supprimer la note par défaut. Elle n'existe peut-être plus."))
            except Exception as e:
                self.logger.error(f"Error deleting default note ID {note_id}: {e}", exc_info=True)
                QMessageBox.critical(self, self.tr("Erreur"), self.tr("Une erreur est survenue lors de la suppression : {0}").format(str(e)))

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys

    # Basic logging for testing
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    # This test setup assumes the database (TEST_DB_PATH or actual) is initialized with tables
    # For a real test, you'd initialize a test DB here.
    # from db.init_schema import initialize_database
    # initialize_database() # Ensure this uses a test DB path if run directly

    app = QApplication(sys.argv)
    admin_widget = DefaultDocumentNotesAdminWidget()
    admin_widget.show()
    sys.exit(app.exec_())
