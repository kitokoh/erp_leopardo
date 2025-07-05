import sqlite3
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel, QRadioButton, QComboBox,
    QListWidget, QListWidgetItem, QPushButton, QMessageBox, QHBoxLayout,
    QFormLayout, QLineEdit, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal

# Assuming database_setup.py is in the same directory or accessible in PYTHONPATH
# For direct execution or testing, adjust path if necessary:
try:
    from .database_setup import get_db_connection, DB_NAME
except ImportError: # Fallback for direct execution
    from database_setup import get_db_connection, DB_NAME


class MyBusinessWidget(QWidget):
    profile_updated = pyqtSignal()

    def __init__(self, user_id=1, parent=None): # user_id is hardcoded for now
        super().__init__(parent)
        self.user_id = user_id
        self.db_path = DB_NAME # Use DB_NAME directly from database_setup

        self._init_ui()
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

    def _get_db_connection(self):
        # Overriding to use self.db_path which is set from imported DB_NAME
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

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
    # Ensure the DB exists for the test
    # conn = sqlite3.connect(DB_NAME) # This will create the file if it doesn't exist
    # conn.close()
    # from database_setup import create_tables, seed_data # Create and seed if running standalone
    # create_tables() # Make sure tables are created
    # seed_data() # Make sure seed data is available

    app = QApplication(sys.argv)

    # It's better to ensure DB is set up before launching the widget
    # For this standalone test, let's assume database_setup.py can be run or has been run
    # If not, we might need to call its main functions here.
    # For simplicity, we'll assume it's ready. If you get "no such table" errors,
    # ensure user_profile_data.db is created and populated by running database_setup.py first.

    # Check if DB exists, if not, create and seed it
    try:
        with open(DB_NAME, 'r') as f: # Simple check if file exists
            pass
        # Further check: ensure tables exist (optional, can be complex)
        temp_conn = sqlite3.connect(DB_NAME)
        temp_cursor = temp_conn.cursor()
        temp_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='BusinessProfile';")
        if not temp_cursor.fetchone():
            raise FileNotFoundError # Table not found, treat as if DB not set up
        temp_conn.close()

    except FileNotFoundError:
        print(f"Database {DB_NAME} not found or not initialized. Running setup...")
        try:
            # Attempt to import and run setup functions
            # This relative import might be tricky if the CWD isn't the project root
            # For robust standalone testing, it's better to run database_setup.py directly first
            # or adjust sys.path
            import os, sys
            # Add parent directory to sys.path to find database_setup if running from user_profile_management
            # current_dir = os.path.dirname(os.path.abspath(__file__))
            # project_root = os.path.dirname(current_dir) # Assuming this file is in user_profile_management
            # sys.path.insert(0, project_root)

            # Simpler: just assume it's in the same dir for this __main__ block
            from database_setup import create_tables, seed_data
            print("Creating tables and seeding data for standalone test...")
            create_tables()
            seed_data()
            print("Database setup complete for standalone test.")
        except Exception as e:
            print(f"Could not automatically set up database for test: {e}")
            print("Please ensure user_profile_data.db is correctly set up by running database_setup.py.")
            sys.exit(1)


    main_win = QWidget()
    layout = QVBoxLayout(main_win)
    my_business_widget = MyBusinessWidget(user_id=1) # Example user_id
    layout.addWidget(my_business_widget)
    main_win.setWindowTitle("Test MyBusinessWidget")
    main_win.resize(600, 700)
    main_win.show()
    sys.exit(app.exec_())
