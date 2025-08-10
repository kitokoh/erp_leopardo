import sqlite3
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel, QRadioButton, QComboBox,
    QListWidget, QListWidgetItem, QPushButton, QMessageBox, QHBoxLayout,
    QFormLayout, QLineEdit, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal
from sqlalchemy.sql import text # Added for SQLAlchemy raw SQL

# Assuming db.connection is accessible in PYTHONPATH
# This is the main way to get DB connection for the application
try:
    from db.connection import get_db_connection
    DB_CONNECTION_AVAILABLE = True
except ImportError:
    # Fallback for environments where db.connection might not be setup,
    # though this widget is unlikely to function correctly without it.
    DB_CONNECTION_AVAILABLE = False
    def get_db_connection(): # Mock function
        raise ImportError("db.connection module not found. Cannot connect to the database.")



class MyBusinessWidget(QWidget):
    profile_updated = pyqtSignal()

    def __init__(self, user_id=1, parent=None): # user_id can be passed dynamically
        super().__init__(parent)
        self.user_id = user_id
        # self.db_path is no longer needed as get_db_connection handles it globally

        if not DB_CONNECTION_AVAILABLE:
            self._show_db_error()
            # Optionally disable the widget or parts of it
            # For now, methods will raise errors if get_db_connection fails.

        self._init_ui()
        if DB_CONNECTION_AVAILABLE: # Only load data if DB is connectable
            self._load_initial_data()

        self._load_user_profile()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        # Business Info Group
        info_group = QGroupBox("Informations Générales sur l'Entreprise")
        info_layout = QFormLayout()
        self.business_name_edit = QLineEdit()
        info_layout.addRow("Nom de l'entreprise:", self.business_name_edit)
        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)

        # Business Type Group
        type_group = QGroupBox("Type d'Entreprise")
        type_layout = QHBoxLayout()
        self.rb_b2b = QRadioButton("B2B (Business to Business)")
        self.rb_b2c = QRadioButton("B2C (Business to Consumer)")
        self.rb_b2b.toggled.connect(self._on_business_type_changed)
        type_layout.addWidget(self.rb_b2b)
        type_layout.addWidget(self.rb_b2c)
        type_group.setLayout(type_layout)
        main_layout.addWidget(type_group)

        # Sector Group
        sector_group = QGroupBox("Secteur d'Activité")
        sector_layout = QVBoxLayout()
        self.sector_combo = QComboBox()
        sector_layout.addWidget(self.sector_combo)
        sector_group.setLayout(sector_layout)
        main_layout.addWidget(sector_group)

        # Use Cases Group
        use_cases_group = QGroupBox("Cas d'Utilisation Principaux")
        use_cases_layout = QVBoxLayout()
        self.use_cases_list = QListWidget()
        self.use_cases_list.setSelectionMode(QListWidget.MultiSelection) # Allow text-based multi-selection if checkboxes are an issue
        use_cases_layout.addWidget(self.use_cases_list)
        use_cases_group.setLayout(use_cases_layout)
        main_layout.addWidget(use_cases_group)

        # Document Types Group
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

        self.setLayout(main_layout)
        self.setWindowTitle("Mon Profil d'Entreprise")

    def _show_db_error(self):
        error_label = QLabel("ERREUR: Connexion à la base de données non disponible.\nLe module 'db.connection' n'a pas pu être chargé ou configuré.\nCe widget ne fonctionnera pas correctement.")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet("color: red; font-weight: bold;")
        layout = QVBoxLayout(self) # Create a layout if one doesn't exist
        layout.addWidget(error_label)
        self.setLayout(layout)


    def _get_db_connection(self):
        # Uses the globally available get_db_connection from db.connection
        if not DB_CONNECTION_AVAILABLE:
             # This case should ideally be handled by disabling UI elements
             # or by the initial check in __init__
            raise ConnectionError("Database connection is not available for MyBusinessWidget.")
        return get_db_connection() # This is the imported function


    def _load_initial_data(self):
        conn = self._get_db_connection() # conn is an SQLAlchemy Session
        if not conn: # Should be handled by _get_db_connection raising an error or initial check
            return

        try:
            # Load Use Cases
            use_cases_query = text("SELECT id, name FROM UseCases ORDER BY name")
            result_use_cases = conn.execute(use_cases_query)
            for row in result_use_cases:
                item = QListWidgetItem(row.name) # Access by attribute
                item.setData(Qt.UserRole, row.id) # Store ID
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
                self.use_cases_list.addItem(item)

            # Load Document Types
            doc_types_query = text("SELECT id, name FROM DocumentTypes ORDER BY name")
            result_doc_types = conn.execute(doc_types_query)
            for row in result_doc_types:
                item = QListWidgetItem(row.name) # Access by attribute
                item.setData(Qt.UserRole, row.id) # Store ID
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
                self.documents_list.addItem(item)

        except Exception as e:
            QMessageBox.critical(self, "Erreur de chargement",
                                 f"Erreur lors du chargement des données initiales: {e}")
            # Depending on how get_db_connection manages sessions, a rollback might be needed here
            # For now, assume session management is external or handled by get_db_connection context
        # finally:
            # conn.close() # Typically, session.close() is managed externally (e.g., request scope)

        # Sectors are loaded dynamically based on B2B/B2C choice

    def _on_business_type_changed(self):
        conn = self._get_db_connection() # conn is an SQLAlchemy Session
        if not conn:
            return
        # cursor = conn.cursor() # Remove this
        self.sector_combo.clear()

        business_type = None
        if self.rb_b2b.isChecked():
            business_type = 'B2B'
        elif self.rb_b2c.isChecked():
            business_type = 'B2C'

        if business_type:
            try:
                sectors_query = text("""
                    SELECT id, name FROM Sectors
                    WHERE type_association = :type_assoc OR type_association = 'BOTH'
                    ORDER BY name
                """)
                result_sectors = conn.execute(sectors_query, {"type_assoc": business_type})
                for row in result_sectors:
                    self.sector_combo.addItem(row.name, userData=row.id)
            except Exception as e:
                QMessageBox.critical(self, "Erreur de chargement des secteurs",
                                     f"Erreur lors du chargement des secteurs d'activité: {e}")
        # conn.close() # Session managed externally

    def _load_user_profile(self):
        conn = self._get_db_connection() # conn is an SQLAlchemy Session
        if not conn:
            return
        # cursor = conn.cursor() # Remove this

        try:
            profile_query = text("SELECT id, name, business_type, sector_id FROM BusinessProfile WHERE user_id = :user_id")
            profile_result = conn.execute(profile_query, {"user_id": self.user_id})
            profile = profile_result.fetchone()
        except Exception as e:
            QMessageBox.critical(self, "Erreur de chargement du profil",
                                 f"Erreur lors du chargement du profil utilisateur: {e}")
            # conn.close() # Session managed externally
            return # Exit if profile load fails

        # The rest of _load_user_profile needs to be refactored to use 'conn' (session)
        # for subsequent queries for BusinessUseCases and BusinessSelectedDocuments.
        # This will be handled in the next modification step for _load_user_profile.
        # For now, just replacing the initial part.

        # Placeholder for the rest of the logic that used the old 'cursor'
        # This will be refactored in the next step dedicated to _load_user_profile
        if profile:
            self.current_profile_id = profile.id # Access by attribute
            self.business_name_edit.setText(profile.name if profile.name else "")

            if profile.business_type == 'B2B':
                self.rb_b2b.setChecked(True)
            elif profile.business_type == 'B2C':
                self.rb_b2c.setChecked(True)

            # This call will repopulate sectors based on the type, using the refactored _on_business_type_changed
            # self._on_business_type_changed() # This might cause issues if called before sector_id is used below.
                                            # Let's defer this specific call or ensure sectors are loaded first.
                                            # For now, the original logic of _on_business_type_changed is called by setChecked.

            if profile.sector_id: # Ensure sectors are loaded for current business_type *before* finding data
                # Manually trigger sector load if not already done by radio button toggle
                # This ensures combo box is populated before we try to findData.
                if not self.sector_combo.count(): # If combo is empty, force load based on profile type
                    current_type_for_sectors = 'B2B' if profile.business_type == 'B2B' else 'B2C' if profile.business_type == 'B2C' else None
                    if current_type_for_sectors:
                        try:
                            sectors_query_for_profile = text("""
                                SELECT id, name FROM Sectors
                                WHERE type_association = :type_assoc OR type_association = 'BOTH'
                                ORDER BY name
                            """)
                            result_sectors_for_profile = conn.execute(sectors_query_for_profile, {"type_assoc": current_type_for_sectors})
                            for row_sector in result_sectors_for_profile:
                                self.sector_combo.addItem(row_sector.name, userData=row_sector.id)
                        except Exception as e_sector_load:
                             QMessageBox.critical(self, "Erreur chargement secteurs (profil)", f"{e_sector_load}")


                index = self.sector_combo.findData(profile.sector_id)
                if index >= 0:
                    self.sector_combo.setCurrentIndex(index)

            # Load selected use cases
            try:
                use_cases_query = text("SELECT use_case_id FROM BusinessUseCases WHERE business_profile_id = :profile_id")
                result_use_cases = conn.execute(use_cases_query, {"profile_id": self.current_profile_id})
                selected_use_case_ids = {row.use_case_id for row in result_use_cases}
                for i in range(self.use_cases_list.count()):
                    item = self.use_cases_list.item(i)
                    if item.data(Qt.UserRole) in selected_use_case_ids:
                        item.setCheckState(Qt.Checked)
                    else:
                        item.setCheckState(Qt.Unchecked)
            except Exception as e_uc:
                QMessageBox.critical(self, "Erreur chargement (Cas d'usage)", f"Erreur: {e_uc}")


            # Load selected document types
            try:
                doc_types_query = text("SELECT document_type_id FROM BusinessSelectedDocuments WHERE business_profile_id = :profile_id")
                result_doc_types = conn.execute(doc_types_query, {"profile_id": self.current_profile_id})
                selected_doc_ids = {row.document_type_id for row in result_doc_types}
                for i in range(self.documents_list.count()):
                    item = self.documents_list.item(i)
                    if item.data(Qt.UserRole) in selected_doc_ids:
                        item.setCheckState(Qt.Checked)
                    else:
                        item.setCheckState(Qt.Unchecked)
            except Exception as e_dt:
                QMessageBox.critical(self, "Erreur chargement (Types de doc)", f"Erreur: {e_dt}")
        else:
            self.current_profile_id = None
            # Default selection, triggers _on_business_type_changed which is now refactored
            # This will populate sectors for B2B by default.
            self.rb_b2b.setChecked(True)

        # conn.close() # Session managed externally

    def _save_profile(self):
        conn = self._get_db_connection() # conn is an SQLAlchemy Session
        if not conn:
            QMessageBox.critical(self, "Erreur", "Connexion à la base de données non disponible.")
            return

        business_name = self.business_name_edit.text()
        business_type = 'B2B' if self.rb_b2b.isChecked() else 'B2C'
        sector_id = self.sector_combo.currentData() # Assuming currentData returns the ID

        try:
            if self.current_profile_id:
                # Update existing profile
                update_profile_sql = text("""
                    UPDATE BusinessProfile SET name = :name, business_type = :type,
                           sector_id = :sector_id, updated_at = CURRENT_TIMESTAMP
                    WHERE id = :profile_id
                """)
                conn.execute(update_profile_sql, {
                    "name": business_name, "type": business_type,
                    "sector_id": sector_id, "profile_id": self.current_profile_id
                })
                profile_id = self.current_profile_id
            else:
                # Insert new profile
                insert_profile_sql = text("""
                    INSERT INTO BusinessProfile (user_id, name, business_type, sector_id)
                    VALUES (:user_id, :name, :type, :sector_id)
                """)
                result = conn.execute(insert_profile_sql, {
                    "user_id": self.user_id, "name": business_name,
                    "type": business_type, "sector_id": sector_id
                })
                # For SQLAlchemy with SQLite, lastrowid is often on the ResultProxy or its cursor attribute
                # For other DBs, result.inserted_primary_key might be used
                profile_id = result.lastrowid
                if profile_id is None and hasattr(result, 'inserted_primary_key') and result.inserted_primary_key:
                    profile_id = result.inserted_primary_key[0]
                self.current_profile_id = profile_id

            # Update BusinessUseCases
            delete_use_cases_sql = text("DELETE FROM BusinessUseCases WHERE business_profile_id = :profile_id")
            conn.execute(delete_use_cases_sql, {"profile_id": profile_id})

            selected_use_cases_data = []
            for i in range(self.use_cases_list.count()):
                item = self.use_cases_list.item(i)
                if item.checkState() == Qt.Checked:
                    # Each dict in the list corresponds to one row for executemany-like behavior
                    selected_use_cases_data.append({"profile_id": profile_id, "use_case_id": item.data(Qt.UserRole)})

            if selected_use_cases_data:
                # SQLAlchemy's session.execute can often handle a list of dicts for bulk inserts
                # if the underlying DBAPI driver supports it with its executemany.
                # The text() construct itself doesn't directly do executemany, but the session might.
                # For clarity and broader compatibility, loop if executemany behavior isn't direct.
                # However, modern SQLAlchemy often handles list of dicts for bulk operations.
                insert_use_case_sql = text("INSERT INTO BusinessUseCases (business_profile_id, use_case_id) VALUES (:profile_id, :use_case_id)")
                conn.execute(insert_use_case_sql, selected_use_cases_data)

            # Update BusinessSelectedDocuments
            delete_docs_sql = text("DELETE FROM BusinessSelectedDocuments WHERE business_profile_id = :profile_id")
            conn.execute(delete_docs_sql, {"profile_id": profile_id})

            selected_documents_data = []
            for i in range(self.documents_list.count()):
                item = self.documents_list.item(i)
                if item.checkState() == Qt.Checked:
                    selected_documents_data.append({"profile_id": profile_id, "document_type_id": item.data(Qt.UserRole)})

            if selected_documents_data:
                insert_doc_sql = text("INSERT INTO BusinessSelectedDocuments (business_profile_id, document_type_id) VALUES (:profile_id, :document_type_id)")
                conn.execute(insert_doc_sql, selected_documents_data)

            conn.commit()
            QMessageBox.information(self, "Succès", "Profil d'entreprise enregistré avec succès.")
            self.profile_updated.emit()
        except Exception as e: # Changed from sqlite3.Error to general Exception
            conn.rollback()
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'enregistrement du profil: {e}")
        # finally:
            # conn.close() # Session managed externally


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
