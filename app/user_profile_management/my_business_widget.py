import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel, QRadioButton, QComboBox,
    QListWidget, QListWidgetItem, QPushButton, QMessageBox, QHBoxLayout,
    QFormLayout, QLineEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from sqlalchemy.sql import text

from app.db.connection import get_db_connection

class MyBusinessWidget(QWidget):
    profile_updated = pyqtSignal()

    def __init__(self, user_id=1, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.current_profile_id = None
        self._init_ui()
        self._load_all_data()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)
        self.setWindowTitle("Mon Profil d'Entreprise")

        # Business Info
        info_group = QGroupBox("Informations Générales sur l'Entreprise")
        info_layout = QFormLayout()
        self.business_name_edit = QLineEdit()
        info_layout.addRow("Nom de l'entreprise:", self.business_name_edit)
        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)

        # Business Type
        type_group = QGroupBox("Type d'Entreprise")
        type_layout = QHBoxLayout()
        self.rb_b2b = QRadioButton("B2B (Business to Business)")
        self.rb_b2c = QRadioButton("B2C (Business to Consumer)")
        self.rb_b2b.toggled.connect(self._on_business_type_changed)
        type_layout.addWidget(self.rb_b2b)
        type_layout.addWidget(self.rb_b2c)
        type_group.setLayout(type_layout)
        main_layout.addWidget(type_group)

        # Sector
        sector_group = QGroupBox("Secteur d'Activité")
        sector_layout = QVBoxLayout()
        self.sector_combo = QComboBox()
        sector_layout.addWidget(self.sector_combo)
        sector_group.setLayout(sector_layout)
        main_layout.addWidget(sector_group)

        # Use Cases
        use_cases_group = QGroupBox("Cas d'Utilisation Principaux")
        use_cases_layout = QVBoxLayout()
        self.use_cases_list = QListWidget()
        self.use_cases_list.setSelectionMode(QListWidget.MultiSelection)
        use_cases_layout.addWidget(self.use_cases_list)
        use_cases_group.setLayout(use_cases_layout)
        main_layout.addWidget(use_cases_group)

        # Document Types
        documents_group = QGroupBox("Types de Documents Utilisés")
        documents_layout = QVBoxLayout()
        self.documents_list = QListWidget()
        documents_layout.addWidget(self.documents_list)
        documents_group.setLayout(documents_layout)
        main_layout.addWidget(documents_group)

        # Action Buttons
        buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Enregistrer")
        self.save_button.clicked.connect(self._save_profile)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.save_button)
        main_layout.addLayout(buttons_layout)

    def _load_all_data(self):
        """Loads initial data and then the user's profile in a single transaction."""
        db_session = None
        try:
            db_session = get_db_connection()
            self._populate_use_cases_and_docs(db_session)
            self._load_user_profile(db_session)
        except Exception as e:
            logging.error(f"Failed to load business profile data: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur de chargement", f"Impossible de charger les données du profil: {e}")
        finally:
            if db_session:
                db_session.close()

    def _populate_use_cases_and_docs(self, db):
        """Populates the Use Case and Document Type list widgets."""
        # Load Use Cases
        use_cases_query = text("SELECT id, name FROM UseCases ORDER BY name")
        result_use_cases = db.execute(use_cases_query)
        self.use_cases_list.clear()
        for row in result_use_cases:
            item = QListWidgetItem(row.name)
            item.setData(Qt.UserRole, row.id)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.use_cases_list.addItem(item)

        # Load Document Types
        doc_types_query = text("SELECT id, name FROM DocumentTypes ORDER BY name")
        result_doc_types = db.execute(doc_types_query)
        self.documents_list.clear()
        for row in result_doc_types:
            item = QListWidgetItem(row.name)
            item.setData(Qt.UserRole, row.id)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.documents_list.addItem(item)

    def _on_business_type_changed(self):
        """Populates the sectors combo box based on the selected business type."""
        db_session = None
        try:
            db_session = get_db_connection()
            self.sector_combo.clear()
            business_type = 'B2B' if self.rb_b2b.isChecked() else 'B2C'
            sectors_query = text("SELECT id, name FROM Sectors WHERE type_association = :type OR type_association = 'BOTH' ORDER BY name")
            result_sectors = db_session.execute(sectors_query, {"type": business_type})
            for row in result_sectors:
                self.sector_combo.addItem(row.name, userData=row.id)
        except Exception as e:
            logging.error(f"Failed to load sectors: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les secteurs d'activité: {e}")
        finally:
            if db_session:
                db_session.close()

    def _load_user_profile(self, db):
        """Loads the user's business profile using the provided DB session."""
        profile_query = text("SELECT id, name, business_type, sector_id FROM BusinessProfile WHERE user_id = :user_id")
        profile = db.execute(profile_query, {"user_id": self.user_id}).fetchone()

        if not profile:
            self.current_profile_id = None
            self.rb_b2b.setChecked(True) # Default selection, triggers sector load
            return

        self.current_profile_id = profile.id
        self.business_name_edit.setText(profile.name or "")

        # Set business type radio button, which will trigger sector loading via its signal
        if profile.business_type == 'B2C':
            self.rb_b2c.setChecked(True)
        else:
            self.rb_b2b.setChecked(True)

        # Set the correct sector in the now-populated combo box
        if profile.sector_id:
            index = self.sector_combo.findData(profile.sector_id)
            if index >= 0:
                self.sector_combo.setCurrentIndex(index)

        # Check the selected use cases
        use_cases_query = text("SELECT use_case_id FROM BusinessUseCases WHERE business_profile_id = :pid")
        selected_use_case_ids = {row.use_case_id for row in db.execute(use_cases_query, {"pid": profile.id})}
        for i in range(self.use_cases_list.count()):
            item = self.use_cases_list.item(i)
            is_checked = item.data(Qt.UserRole) in selected_use_case_ids
            item.setCheckState(Qt.Checked if is_checked else Qt.Unchecked)

        # Check the selected document types
        doc_types_query = text("SELECT document_type_id FROM BusinessSelectedDocuments WHERE business_profile_id = :pid")
        selected_doc_ids = {row.document_type_id for row in db.execute(doc_types_query, {"pid": profile.id})}
        for i in range(self.documents_list.count()):
            item = self.documents_list.item(i)
            is_checked = item.data(Qt.UserRole) in selected_doc_ids
            item.setCheckState(Qt.Checked if is_checked else Qt.Unchecked)

    def _save_profile(self):
        db_session = None
        try:
            db_session = get_db_connection()
            business_name = self.business_name_edit.text()
            business_type = 'B2B' if self.rb_b2b.isChecked() else 'B2C'
            sector_id = self.sector_combo.currentData()

            if self.current_profile_id:
                # Update existing profile
                update_sql = text("UPDATE BusinessProfile SET name=:name, business_type=:type, sector_id=:sid, updated_at=CURRENT_TIMESTAMP WHERE id=:pid")
                db_session.execute(update_sql, {"name": business_name, "type": business_type, "sid": sector_id, "pid": self.current_profile_id})
                profile_id = self.current_profile_id
            else:
                # Insert new profile
                insert_sql = text("INSERT INTO BusinessProfile (user_id, name, business_type, sector_id) VALUES (:uid, :name, :type, :sid)")
                result = db_session.execute(insert_sql, {"uid": self.user_id, "name": business_name, "type": business_type, "sid": sector_id})
                profile_id = result.lastrowid
                self.current_profile_id = profile_id

            # Update Use Cases
            db_session.execute(text("DELETE FROM BusinessUseCases WHERE business_profile_id = :pid"), {"pid": profile_id})
            selected_use_cases = [{"pid": profile_id, "uid": self.use_cases_list.item(i).data(Qt.UserRole)} for i in range(self.use_cases_list.count()) if self.use_cases_list.item(i).checkState() == Qt.Checked]
            if selected_use_cases:
                db_session.execute(text("INSERT INTO BusinessUseCases (business_profile_id, use_case_id) VALUES (:pid, :uid)"), selected_use_cases)

            # Update Document Types
            db_session.execute(text("DELETE FROM BusinessSelectedDocuments WHERE business_profile_id = :pid"), {"pid": profile_id})
            selected_docs = [{"pid": profile_id, "did": self.documents_list.item(i).data(Qt.UserRole)} for i in range(self.documents_list.count()) if self.documents_list.item(i).checkState() == Qt.Checked]
            if selected_docs:
                db_session.execute(text("INSERT INTO BusinessSelectedDocuments (business_profile_id, document_type_id) VALUES (:pid, :did)"), selected_docs)

            db_session.commit()
            QMessageBox.information(self, "Succès", "Profil d'entreprise enregistré avec succès.")
            self.profile_updated.emit()
        except Exception as e:
            if db_session:
                db_session.rollback()
            logging.error(f"Failed to save business profile: {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'enregistrement du profil: {e}")
        finally:
            if db_session:
                db_session.close()


if __name__ == '__main__':
    import sys
    import os

    # For standalone testing, we need to ensure db.connection can be found
    # and that its configuration is set (or use a test DB path).
    # This setup is more involved than when running within the main application.

    # Add project root to sys.path to allow finding 'db' module
    current_script_path = os.path.abspath(__file__)
    project_root_for_test = os.path.dirname(os.path.dirname(current_script_path))
    if project_root_for_test not in sys.path:
        sys.path.insert(0, project_root_for_test)

    # Now try to import db.connection components again, as they might be available
    try:
        from db.connection import set_db_config, get_db_connection, initialize_engine_and_session
        from db.init_schema import initialize_database # To create schema if needed
        DB_CONNECTION_AVAILABLE_FOR_TEST = True
    except ImportError as e:
        print(f"ERROR in __main__: Could not import db modules for testing: {e}")
        DB_CONNECTION_AVAILABLE_FOR_TEST = False

    app = QApplication(sys.argv)

    if not DB_CONNECTION_AVAILABLE_FOR_TEST:
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setText("Erreur de Configuration de la Base de Données")
        error_dialog.setInformativeText(
            "Le module db.connection ou ses dépendances n'ont pas pu être importés. "
            "Assurez-vous que le PYTHONPATH est correct et que la base de données principale "
            "de l'application est accessible et initialisée.\n\n"
            "Ce widget ne peut pas fonctionner sans une connexion valide à la base de données."
        )
        error_dialog.setWindowTitle("Erreur Démarrage Widget")
        error_dialog.exec_()
        sys.exit(1)

    # --- Mock or use a real test database for standalone execution ---
    # Option 1: Use a dedicated test database file
    test_db_name = "my_business_widget_test.db"
    test_db_path = os.path.join(project_root_for_test, test_db_name) # Place it in project root

    # Mock application configuration for db.connection
    mock_app_config = {
        'database_path': test_db_path,
        'database_type': 'sqlite'
        # Add any other config keys db.connection or init_schema might expect
    }

    print(f"INFO in __main__: Using test database at: {test_db_path}")

    # Initialize db.connection with the mock config
    set_db_config(mock_app_config)
    initialize_engine_and_session(mock_app_config) # For SQLAlchemy if used by db.connection

    # Ensure the schema exists in the test database
    try:
        print(f"INFO in __main__: Initializing schema for test database: {test_db_path}...")
        initialize_database(mock_app_config) # This creates all tables including new ones
        print(f"INFO in __main__: Schema initialization complete for {test_db_path}.")
    except Exception as e_init_db:
        print(f"ERROR in __main__: Failed to initialize test database schema: {e_init_db}")
        # Depending on the error, you might want to exit or inform the user differently.
        # For now, we'll proceed, but the widget might fail if tables are missing.
        QMessageBox.critical(None, "Erreur Initialisation BD (Test)",
                             f"Impossible d'initialiser le schéma de la base de données de test:\n{e_init_db}")
        # sys.exit(1) # Might be too aggressive if some tables exist

    main_win = QWidget()
    layout = QVBoxLayout(main_win)

    # Instantiate the widget. It should now use the globally configured db.connection
    my_business_widget = MyBusinessWidget(user_id=1) # Example user_id

    layout.addWidget(my_business_widget)
    main_win.setWindowTitle("Test MyBusinessWidget (Standalone with Main DB Connection)")

    main_win.resize(600, 700)
    main_win.show()
    sys.exit(app.exec_())
