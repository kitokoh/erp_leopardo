# -*- coding: utf-8 -*-
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QComboBox, QMessageBox, QDialogButtonBox, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal
import app.db as db_manager # Assuming db_manager is the way to access CRUD operations
from app.db.cruds.template_categories_crud import get_all_template_categories, add_template_category
from app.gui.widgets.html_editor import HtmlEditor # To launch the editor for the new template
import app.config # For templates_dir

class HtmlTemplateCreatorDialog(QDialog):
    template_created_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Create New HTML Template"))
        self.setMinimumWidth(500)
        self.config = config.get_config() # Load application configuration

        self.html_editor_instance = None # To keep track of the editor window

        self._setup_ui()
        self._connect_signals()
        self.populate_category_combo()
        self.populate_language_combo()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QGridLayout()

        self.name_label = QLabel(self.tr("Template Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(self.tr("e.g., Proforma Invoice Extra"))
        form_layout.addWidget(self.name_label, 0, 0)
        form_layout.addWidget(self.name_input, 0, 1, 1, 2) # Span 2 columns

        self.type_label = QLabel(self.tr("Template Type:"))
        self.type_combo = QComboBox()
        form_layout.addWidget(self.type_label, 1, 0)
        form_layout.addWidget(self.type_combo, 1, 1, 1, 2)

        self.language_label = QLabel(self.tr("Language:"))
        self.language_combo = QComboBox()
        form_layout.addWidget(self.language_label, 2, 0)
        form_layout.addWidget(self.language_combo, 2, 1, 1, 2)

        self.category_label = QLabel(self.tr("Category:"))
        self.category_combo = QComboBox()
        form_layout.addWidget(self.category_label, 3, 0)
        form_layout.addWidget(self.category_combo, 3, 1)

        self.new_category_button = QPushButton(self.tr("New Category..."))
        form_layout.addWidget(self.new_category_button, 3, 2)

        self.description_label = QLabel(self.tr("Description:"))
        self.description_input = QTextEdit()
        self.description_input.setFixedHeight(60)
        form_layout.addWidget(self.description_label, 4, 0)
        form_layout.addWidget(self.description_input, 4, 1, 1, 2)

        self.email_subject_label = QLabel(self.tr("Email Subject Template (if applicable):"))
        self.email_subject_input = QLineEdit()
        self.email_subject_input.setPlaceholderText(self.tr("e.g., Regarding your order {{order.id}}"))
        form_layout.addWidget(self.email_subject_label, 5, 0)
        form_layout.addWidget(self.email_subject_input, 5, 1, 1, 2)
        self.email_subject_label.hide() # Hidden by default
        self.email_subject_input.hide() # Hidden by default

        self.version_label = QLabel(self.tr("Version:"))
        self.version_input = QLineEdit("1.0")
        form_layout.addWidget(self.version_label, 6, 0)
        form_layout.addWidget(self.version_input, 6, 1, 1, 2)

        # Client ID - Optional
        self.client_id_label = QLabel(self.tr("Client ID (Optional):"))
        self.client_id_input = QLineEdit()
        self.client_id_input.setPlaceholderText(self.tr("Leave blank for global template"))
        form_layout.addWidget(self.client_id_label, 7, 0)
        form_layout.addWidget(self.client_id_input, 7, 1, 1, 2)

        main_layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        main_layout.addWidget(self.button_box)

    def _connect_signals(self):
        self.button_box.accepted.connect(self.accept_creation)
        self.button_box.rejected.connect(self.reject)
        self.new_category_button.clicked.connect(self._create_new_category)
        self.type_combo.currentTextChanged.connect(self._toggle_email_subject_visibility)

    def _populate_type_combo(self):
        self.type_combo.clear()
        self.type_combo.addItem(self.tr("-- Select Type --"), None)
        # Common document types, can be expanded
        doc_types = [
            "PROFORMA_INVOICE_HTML", "PACKING_LIST_HTML", "SALES_CONTRACT_HTML",
            "TECHNICAL_SPECIFICATIONS_HTML", "GENERAL_HTML_DOCUMENT",
            "EMAIL_BODY_HTML", "EMAIL_BODY_TXT",
            # Add more specific types as needed, e.g., from CreateDocumentDialog.DOCUMENT_TYPE_MAPPING
        ]
        # Add types from CreateDocumentDialog for consistency
        from dialogs.create_document_dialog import CreateDocumentDialog
        for key, info in CreateDocumentDialog.DOCUMENT_TYPE_MAPPING.items():
            if info["template_type_filter"] not in doc_types:
                 doc_types.append(info["template_type_filter"])

        # Remove duplicates and sort
        unique_doc_types = sorted(list(set(doc_types)))

        for doc_type in unique_doc_types:
            self.type_combo.addItem(doc_type, doc_type)

    def _toggle_email_subject_visibility(self, selected_type_text):
        is_email_type = selected_type_text and ("EMAIL_BODY" in selected_type_text.upper())
        self.email_subject_label.setVisible(is_email_type)
        self.email_subject_input.setVisible(is_email_type)

    def populate_category_combo(self):
        self.category_combo.clear()
        self.category_combo.addItem(self.tr("-- Select Category --"), None)
        try:
            categories = get_all_template_categories()
            if categories:
                for category in categories:
                    self.category_combo.addItem(category['category_name'], category['category_id'])
        except Exception as e:
            QMessageBox.warning(self, self.tr("Error"), self.tr("Could not load template categories: {0}").format(str(e)))
            print(f"Error loading categories: {e}")

    def populate_language_combo(self):
        self.language_combo.clear()
        # Standard languages, can be expanded or fetched from config/db if needed
        languages = ["en", "fr", "ar", "tr", "pt", "es", "ru"] # Added more common languages
        self.language_combo.addItem(self.tr("-- Select Language --"), None)
        for lang_code in sorted(languages):
            self.language_combo.addItem(lang_code, lang_code)

    def _create_new_category(self):
        from PyQt5.QtWidgets import QInputDialog # Local import to avoid circularity if this was a base class

        new_category_name, ok_name = QInputDialog.getText(self, self.tr("New Category Name"), self.tr("Enter name for new category:"))
        if ok_name and new_category_name.strip():
            new_category_purpose, ok_purpose = QInputDialog.getText(self, self.tr("New Category Purpose"),
                                                                    self.tr("Enter purpose (e.g., client_document, email, html_template):"),
                                                                    QLineEdit.Normal, "html_template") # Default purpose
            if ok_purpose: # User might cancel purpose input
                purpose_for_db = new_category_purpose.strip() if new_category_purpose.strip() else "html_template"

                category_id = add_template_category(
                    category_name=new_category_name.strip(),
                    description=f"{new_category_name.strip()} category", # Default description
                    purpose=purpose_for_db
                )
                if category_id:
                    QMessageBox.information(self, self.tr("Success"), self.tr("Category '{0}' created.").format(new_category_name.strip()))
                    self.populate_category_combo() # Refresh
                    # Optionally select the newly created category
                    index = self.category_combo.findData(category_id)
                    if index >= 0:
                        self.category_combo.setCurrentIndex(index)
                else:
                    QMessageBox.warning(self, self.tr("Error"), self.tr("Could not create category '{0}'.").format(new_category_name.strip()))
        elif ok_name and not new_category_name.strip():
            QMessageBox.warning(self, self.tr("Input Error"), self.tr("Category name cannot be empty."))


    def accept_creation(self):
        template_name = self.name_input.text().strip()
        language_code = self.language_combo.currentData()
        category_id = self.category_combo.currentData()
        client_id = self.client_id_input.text().strip() or None # None if empty

        if not template_name:
            QMessageBox.warning(self, self.tr("Input Error"), self.tr("Template name is required."))
            return
        if not language_code:
            QMessageBox.warning(self, self.tr("Input Error"), self.tr("Please select a language."))
            return
        if not category_id:
            QMessageBox.warning(self, self.tr("Input Error"), self.tr("Please select a category."))
            return

        # Prepare data for HtmlEditor
        # HtmlEditor will be launched without a file_path for new templates.
        # The actual saving of the template (DB record and file) will happen after HtmlEditor is closed and content is retrieved.

        # Dummy client_data for HtmlEditor preview context.
        # This should ideally be more robust or allow user input if complex placeholders are common in new templates.
        dummy_client_data_for_editor = {
            "client_id": client_id if client_id else "PREVIEW_CLIENT_ID", # Use provided client_id or a placeholder
            "Nom du client": "Client Preview Name",
            # Add other common fields that might be in a base HTML template skeleton
        }

        self.html_editor_instance = HtmlEditor(file_path=None, client_data=dummy_client_data_for_editor, parent=self)
        self.html_editor_instance.setWindowTitle(self.tr("Creating: {0} ({1})").format(template_name, language_code))

        # Connect a signal from HtmlEditor (if it has one for content saved/closed)
        # or override accept/reject in HtmlEditor if it's used modally.
        # For now, we'll assume HtmlEditor.accept() is called on successful save.
        if self.html_editor_instance.exec_() == QDialog.Accepted:
            # HtmlEditor was accepted (saved), now get content and save template
            html_content = self.html_editor_instance.raw_html_content_from_editor
            if not html_content:
                QMessageBox.warning(self, self.tr("Error"), self.tr("HTML content is empty. Template not created."))
                return

            self._save_new_template(template_name, language_code, category_id, client_id, html_content)
        else:
            # Editor was cancelled
            QMessageBox.information(self, self.tr("Cancelled"), self.tr("HTML template creation was cancelled."))


    def _save_new_template(self, name, language, category_id, client_id, html_content):
        base_file_name = f"{name.replace(' ', '_').lower()}_{language}.html"

        # Ensure templates directory for the language exists
        target_lang_dir = os.path.join(self.config["templates_dir"], language)
        try:
            os.makedirs(target_lang_dir, exist_ok=True)
        except OSError as e:
            QMessageBox.critical(self, self.tr("Directory Error"), self.tr("Could not create template directory: {0}\n{1}").format(target_lang_dir, str(e)))
            return

        full_file_path = os.path.join(target_lang_dir, base_file_name)

        # Check for file overwrite, though for new templates this should be less common if names are unique.
        if os.path.exists(full_file_path):
            reply = QMessageBox.question(self, self.tr("File Exists"),
                                         self.tr("A file named '{0}' already exists. Overwrite?").format(base_file_name),
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return

        try:
            with open(full_file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
        except IOError as e:
            QMessageBox.critical(self, self.tr("File Save Error"), self.tr("Could not save HTML file: {0}\n{1}").format(full_file_path, str(e)))
            return

        template_metadata = {
            'template_name': name,
            'template_type': 'document_html', # Specific type for these HTML templates
            'language_code': language,
            'base_file_name': base_file_name,
            'description': f"HTML Template: {name} ({language})",
            'category_id': category_id,
            'client_id': client_id,
            'is_default_for_type_lang': False,
            # 'raw_template_file_data': html_content # Optionally store in DB too, though file is primary
        }

        try:
            new_template_id = db_manager.add_template(template_metadata) # Using the existing CRUD
            if new_template_id:
                QMessageBox.information(self, self.tr("Success"), self.tr("HTML Template '{0}' created successfully.").format(name))
                self.template_created_signal.emit()
                super().accept() # Accept the HtmlTemplateCreatorDialog itself
            else:
                QMessageBox.warning(self, self.tr("DB Error"), self.tr("Failed to save template metadata to database."))
                # Cleanup created file if DB save fails?
                if os.path.exists(full_file_path):
                    try: os.remove(full_file_path)
                    except: pass # ignore cleanup error
        except Exception as e:
            QMessageBox.critical(self, self.tr("DB Error"), self.tr("An error occurred while saving template to database: {0}").format(str(e)))
            if os.path.exists(full_file_path):
                try: os.remove(full_file_path)
                except: pass


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)

    # Mocking config and db_manager for standalone testing
    class MockConfig:
        def get_config(self):
            return {"templates_dir": "./templates_test_dir"} # Use a local test dir

    config = MockConfig() # Override module-level config

    # Ensure test directory exists
    if not os.path.exists("./templates_test_dir"):
        os.makedirs("./templates_test_dir/fr", exist_ok=True)
        os.makedirs("./templates_test_dir/en", exist_ok=True)

    class MockDbManager:
        def get_all_template_categories(self):
            print("MockDb: get_all_template_categories called")
            return [
                {'category_id': 1, 'category_name': 'Factures'},
                {'category_id': 2, 'category_name': 'Contrats'}
            ]
        def add_template_category(self, category_name, description, purpose):
            print(f"MockDb: add_template_category called with {category_name}, {description}, {purpose}")
            return 3 # Dummy new ID

        def add_template(self, data):
            print(f"MockDb: add_template called with data: {data}")
            # Simulate file saving for test
            lang_dir = os.path.join(config.get_config()["templates_dir"], data['language_code'])
            if not os.path.exists(lang_dir): os.makedirs(lang_dir)
            file_path = os.path.join(lang_dir, data['base_file_name'])
            # In real scenario, html_content to write would come from HtmlEditor
            # For mock, we'll assume it's passed in data or use a placeholder
            # with open(file_path, 'w', encoding='utf-8') as f:
            #    f.write(data.get('raw_template_file_data', "<h1>Mock HTML Content</h1>"))
            print(f"MockDb: Simulated saving to {file_path}")
            return 101 # Dummy new template ID

    db_manager = MockDbManager() # Override module-level db_manager

    dialog = HtmlTemplateCreatorDialog()
    if dialog.exec_() == QDialog.Accepted:
        print("HTML Template Creator Dialog accepted.")
    else:
        print("HTML Template Creator Dialog cancelled.")

    sys.exit(app.exec_())
