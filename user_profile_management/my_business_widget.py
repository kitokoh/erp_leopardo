import sqlite3
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel, QRadioButton, QComboBox,
    QListWidget, QListWidgetItem, QPushButton, QMessageBox, QHBoxLayout,
    QFormLayout, QLineEdit, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal

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
        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Load Use Cases
        cursor.execute("SELECT id, name FROM UseCases ORDER BY name")
        for row in cursor.fetchall():
            item = QListWidgetItem(row['name'])
            item.setData(Qt.UserRole, row['id']) # Store ID
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.use_cases_list.addItem(item)

        # Load Document Types
        cursor.execute("SELECT id, name FROM DocumentTypes ORDER BY name")
        for row in cursor.fetchall():
            item = QListWidgetItem(row['name'])
            item.setData(Qt.UserRole, row['id']) # Store ID
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.documents_list.addItem(item)

        conn.close()
        # Sectors are loaded dynamically based on B2B/B2C choice

    def _on_business_type_changed(self):
        conn = self._get_db_connection()
        cursor = conn.cursor()
        self.sector_combo.clear()

        business_type = None
        if self.rb_b2b.isChecked():
            business_type = 'B2B'
        elif self.rb_b2c.isChecked():
            business_type = 'B2C'

        if business_type:
            cursor.execute("SELECT id, name FROM Sectors WHERE type_association = ? OR type_association = 'BOTH' ORDER BY name", (business_type,))
            for row in cursor.fetchall():
                self.sector_combo.addItem(row['name'], userData=row['id'])
        conn.close()

    def _load_user_profile(self):
        conn = self._get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, name, business_type, sector_id FROM BusinessProfile WHERE user_id = ?", (self.user_id,))
        profile = cursor.fetchone()

        if profile:
            self.current_profile_id = profile['id']
            self.business_name_edit.setText(profile['name'] if profile['name'] else "")

            if profile['business_type'] == 'B2B':
                self.rb_b2b.setChecked(True)
            elif profile['business_type'] == 'B2C':
                self.rb_b2c.setChecked(True)

            # Ensure sectors are loaded for the current business type before setting the value
            self._on_business_type_changed() # This will populate the combo box
            if profile['sector_id']:
                index = self.sector_combo.findData(profile['sector_id'])
                if index >= 0:
                    self.sector_combo.setCurrentIndex(index)

            # Load selected use cases
            cursor.execute("SELECT use_case_id FROM BusinessUseCases WHERE business_profile_id = ?", (self.current_profile_id,))
            selected_use_case_ids = {row['use_case_id'] for row in cursor.fetchall()}
            for i in range(self.use_cases_list.count()):
                item = self.use_cases_list.item(i)
                if item.data(Qt.UserRole) in selected_use_case_ids:
                    item.setCheckState(Qt.Checked)
                else:
                    item.setCheckState(Qt.Unchecked)


            # Load selected document types
            cursor.execute("SELECT document_type_id FROM BusinessSelectedDocuments WHERE business_profile_id = ?", (self.current_profile_id,))
            selected_doc_ids = {row['document_type_id'] for row in cursor.fetchall()}
            for i in range(self.documents_list.count()):
                item = self.documents_list.item(i)
                if item.data(Qt.UserRole) in selected_doc_ids:
                    item.setCheckState(Qt.Checked)
                else:
                    item.setCheckState(Qt.Unchecked)

        else:
            self.current_profile_id = None
            self.rb_b2b.setChecked(True) # Default selection
            self._on_business_type_changed() # Load B2B sectors by default


        conn.close()

    def _save_profile(self):
        conn = self._get_db_connection()
        cursor = conn.cursor()

        business_name = self.business_name_edit.text()
        business_type = 'B2B' if self.rb_b2b.isChecked() else 'B2C'
        sector_id = self.sector_combo.currentData()

        try:
            if self.current_profile_id:
                cursor.execute("""
                    UPDATE BusinessProfile SET name = ?, business_type = ?, sector_id = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (business_name, business_type, sector_id, self.current_profile_id))
                profile_id = self.current_profile_id
            else:
                cursor.execute("""
                    INSERT INTO BusinessProfile (user_id, name, business_type, sector_id)
                    VALUES (?, ?, ?, ?)
                """, (self.user_id, business_name, business_type, sector_id))
                profile_id = cursor.lastrowid
                self.current_profile_id = profile_id

            # Update BusinessUseCases
            # First, remove existing associations for this profile
            cursor.execute("DELETE FROM BusinessUseCases WHERE business_profile_id = ?", (profile_id,))
            # Then, add selected ones
            selected_use_cases = []
            for i in range(self.use_cases_list.count()):
                item = self.use_cases_list.item(i)
                if item.checkState() == Qt.Checked:
                    selected_use_cases.append((profile_id, item.data(Qt.UserRole)))
            if selected_use_cases:
                cursor.executemany("INSERT INTO BusinessUseCases (business_profile_id, use_case_id) VALUES (?, ?)", selected_use_cases)

            # Update BusinessSelectedDocuments
            cursor.execute("DELETE FROM BusinessSelectedDocuments WHERE business_profile_id = ?", (profile_id,))
            selected_documents = []
            for i in range(self.documents_list.count()):
                item = self.documents_list.item(i)
                if item.checkState() == Qt.Checked:
                    selected_documents.append((profile_id, item.data(Qt.UserRole)))
            if selected_documents:
                cursor.executemany("INSERT INTO BusinessSelectedDocuments (business_profile_id, document_type_id) VALUES (?, ?)", selected_documents)

            conn.commit()
            QMessageBox.information(self, "Succès", "Profil d'entreprise enregistré avec succès.")
            self.profile_updated.emit()
        except sqlite3.Error as e:
            conn.rollback()
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'enregistrement du profil: {e}")
        finally:
            conn.close()


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
