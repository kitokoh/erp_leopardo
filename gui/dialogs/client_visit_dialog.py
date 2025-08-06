# -*- coding: utf-8 -*-
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QTextEdit, QComboBox,
    QPushButton, QMessageBox, QDialogButtonBox, QDateEdit
)
from PyQt5.QtCore import Qt, QDate, QSettings
from PyQt5.QtGui import QIcon

# Assuming db_manager and client_visits_crud are accessible
# For development, you might need to adjust imports or use mocks if run standalone
try:
    import db as db_manager # General DB utilities if needed
    from db.cruds import client_visits_crud
except ImportError:
    logging.warning("ClientVisitDialog: db_manager or client_visits_crud not found. Using placeholder logic for DB interaction.")
    class MockClientVisitsCrud:
        def add_client_visit(self, visit_data):
            logging.info(f"Mock DB: Adding visit: {visit_data}")
            return {"success": True, "visit_id": "mock_visit_id_123"}
        def update_client_visit(self, visit_id, visit_data):
            logging.info(f"Mock DB: Updating visit {visit_id} with {visit_data}")
            return {"success": True}
    client_visits_crud = MockClientVisitsCrud()


class ClientVisitDialog(QDialog):
    """
    Dialog for adding or editing a client visit.
    """
    # Suggested visit types - these will also be loaded/saved from QSettings
    DEFAULT_VISIT_TYPES = [
        "Réunion physique", "Appel téléphonique", "Visioconférence",
        "Email important", "Visite de courtoisie", "Démonstration produit",
        "Formation", "Support technique", "Autre"
    ]
    VISIT_TYPES_SETTINGS_KEY = "visit_types"

    def __init__(self, client_id: str, current_user_id: str, visit_data: dict = None, parent=None):
        super().__init__(parent)
        self.client_id = client_id
        self.current_user_id = current_user_id
        self.visit_data = visit_data # If None, it's an "add" operation
        self.is_edit_mode = visit_data is not None

        self.setWindowTitle(self.tr("Modifier Visite Client") if self.is_edit_mode else self.tr("Ajouter Visite Client"))
        self.setMinimumWidth(450)
        self.setWindowIcon(QIcon(":/icons/calendar.svg")) # Consistent icon

        self._setup_ui()
        self._load_visit_types_to_combo()

        if self.is_edit_mode:
            self._populate_fields()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.visit_date_edit = QDateEdit(QDate.currentDate())
        self.visit_date_edit.setCalendarPopup(True)
        self.visit_date_edit.setDisplayFormat("yyyy-MM-dd")
        form_layout.addRow(self.tr("Date Visite:"), self.visit_date_edit)

        self.visit_type_combo = QComboBox()
        self.visit_type_combo.setEditable(True)
        self.visit_type_combo.setPlaceholderText(self.tr("Sélectionnez ou entrez un type"))
        form_layout.addRow(self.tr("Type de Visite:"), self.visit_type_combo)

        self.visit_purpose_edit = QLineEdit()
        self.visit_purpose_edit.setPlaceholderText(self.tr("Ex: Introduction, Suivi, Résolution problème..."))
        form_layout.addRow(self.tr("Objet/But:"), self.visit_purpose_edit)

        self.notes_impressions_edit = QTextEdit()
        self.notes_impressions_edit.setPlaceholderText(self.tr("Détails de la visite, impressions, prochaines étapes..."))
        self.notes_impressions_edit.setMinimumHeight(100)
        form_layout.addRow(self.tr("Notes/Impressions:"), self.notes_impressions_edit)

        main_layout.addLayout(form_layout)

        # Dialog buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        main_layout.addWidget(self.button_box)

    def _load_visit_types_to_combo(self):
        self.visit_type_combo.blockSignals(True)
        self.visit_type_combo.clear()

        settings = QSettings()
        stored_types = settings.value(self.VISIT_TYPES_SETTINGS_KEY, self.DEFAULT_VISIT_TYPES, type=list)

        unique_types_dict = {}
        # Add default types first, then stored types to ensure defaults are present
        # and user-added ones can override if they have same lowercase representation.
        all_types_to_consider = self.DEFAULT_VISIT_TYPES + stored_types
        for v_type in all_types_to_consider:
            if v_type.lower() not in unique_types_dict:
                unique_types_dict[v_type.lower()] = v_type

        sorted_unique_types = sorted(list(unique_types_dict.values()), key=str.lower)

        for v_type in sorted_unique_types:
            self.visit_type_combo.addItem(v_type)

        self.visit_type_combo.setCurrentIndex(-1) # No default selection
        self.visit_type_combo.blockSignals(False)

    def _populate_fields(self):
        if not self.visit_data:
            return

        visit_date_str = self.visit_data.get("visit_date")
        if visit_date_str:
            try:
                # Assuming date is stored as YYYY-MM-DD string
                self.visit_date_edit.setDate(QDate.fromString(visit_date_str, "yyyy-MM-dd"))
            except Exception as e:
                logging.error(f"Error parsing visit_date '{visit_date_str}': {e}")
                self.visit_date_edit.setDate(QDate.currentDate())

        visit_type = self.visit_data.get("visit_type", "")
        if visit_type:
            # Find if type exists, otherwise add it
            idx = self.visit_type_combo.findText(visit_type, Qt.MatchFixedString)
            if idx != -1:
                self.visit_type_combo.setCurrentIndex(idx)
            else:
                self.visit_type_combo.addItem(visit_type) # Add if not in standard list
                self.visit_type_combo.setCurrentText(visit_type)

        self.visit_purpose_edit.setText(self.visit_data.get("visit_purpose", ""))
        self.notes_impressions_edit.setPlainText(self.visit_data.get("notes_impressions", ""))

    def _save_new_visit_type(self, new_type_text: str):
        if not new_type_text:
            return
        settings = QSettings()
        stored_types = settings.value(self.VISIT_TYPES_SETTINGS_KEY, self.DEFAULT_VISIT_TYPES, type=list)
        if not any(vt.lower() == new_type_text.lower() for vt in stored_types):
            stored_types.append(new_type_text)
            stored_types.sort(key=str.lower)
            settings.setValue(self.VISIT_TYPES_SETTINGS_KEY, stored_types)
            logging.info(f"Added new visit type '{new_type_text}' to QSettings.")

    def accept(self):
        visit_date = self.visit_date_edit.date().toString("yyyy-MM-dd")
        visit_type = self.visit_type_combo.currentText().strip()
        visit_purpose = self.visit_purpose_edit.text().strip()
        notes_impressions = self.notes_impressions_edit.toPlainText().strip()

        if not all([visit_date, visit_type, visit_purpose]):
            QMessageBox.warning(self, self.tr("Champs Requis"),
                                self.tr("Date, Type, et Objet de la visite sont requis."))
            return

        # Save the entered visit type if it's new
        self._save_new_visit_type(visit_type)

        data_payload = {
            "client_id": self.client_id,
            "visit_date": visit_date,
            "visit_type": visit_type,
            "visit_purpose": visit_purpose,
            "notes_impressions": notes_impressions,
            "created_by_user_id": self.current_user_id
        }

        try:
            if self.is_edit_mode and self.visit_data.get("visit_id"):
                result = client_visits_crud.update_client_visit(self.visit_data["visit_id"], data_payload)
                action_verb = self.tr("modifiée")
            else:
                result = client_visits_crud.add_client_visit(data_payload)
                action_verb = self.tr("ajoutée")

            if result and result.get("success"):
                QMessageBox.information(self, self.tr("Succès"), self.tr("Visite client {0} avec succès.").format(action_verb))
                super().accept()
            else:
                error_msg = result.get("error", self.tr("Erreur inconnue.")) if result else self.tr("Erreur inconnue.")
                QMessageBox.critical(self, self.tr("Erreur Base de Données"),
                                     self.tr("Impossible de sauvegarder la visite client: {0}").format(error_msg))
        except Exception as e:
            logging.error(f"Error saving client visit: {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Critique"),
                                 self.tr("Une erreur inattendue est survenue: {0}").format(str(e)))

    def get_visit_data(self) -> dict:
        # This method might not be strictly necessary if dialog handles its own save,
        # but can be useful for testing or if parent needs data.
        return {
            "visit_id": self.visit_data.get("visit_id") if self.is_edit_mode else None,
            "client_id": self.client_id,
            "visit_date": self.visit_date_edit.date().toString("yyyy-MM-dd"),
            "visit_type": self.visit_type_combo.currentText().strip(),
            "visit_purpose": self.visit_purpose_edit.text().strip(),
            "notes_impressions": self.notes_impressions_edit.toPlainText().strip(),
            "created_by_user_id": self.current_user_id
        }

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    # Basic logging setup for testing
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Required for QSettings
    QCoreApplication.setOrganizationName("TestOrg")
    QCoreApplication.setApplicationName("TestAppForVisitDialog")

    app = QApplication(sys.argv)

    # Test "Add" mode
    dialog_add = ClientVisitDialog(client_id="test_client_001", current_user_id="user_test_adder")
    # dialog_add.show() # Uncomment to test add

    # Test "Edit" mode (requires mock data)
    mock_visit_to_edit = {
        "visit_id": "visit_xyz789",
        "client_id": "test_client_002",
        "visit_date": "2023-10-15",
        "visit_type": "Suivi Projet Spécial",
        "visit_purpose": "Discussion des étapes suivantes et blocages",
        "notes_impressions": "Le client est content mais inquiet pour le délai X.\nProchaine réunion fixée.",
        "created_by_user_id": "user_init",
        "created_at": "2023-10-15T10:00:00Z",
        "updated_at": "2023-10-15T10:00:00Z"
    }
    dialog_edit = ClientVisitDialog(client_id="test_client_002", current_user_id="user_test_editor", visit_data=mock_visit_to_edit)
    dialog_edit.show()


    sys.exit(app.exec_())
