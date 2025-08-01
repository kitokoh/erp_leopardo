# -*- coding: utf-8 -*-
import os
import sys # Ensure sys is imported for path manipulation
import types # For creating mock module objects

# --- Conditional mocking for __main__ START ---
# This MUST be before any problematic imports like 'db'

from dialogs.template_dialog import TemplateDialog # Added import

if __name__ == '__main__':
    print("MAIN_TOP: Pre-patching sys.modules for 'db' with a mock package structure.")

    # Create a mock 'db' module
    mock_db_module = types.ModuleType('db')

    # Create a mock 'db.utils' module
    mock_db_utils_module = types.ModuleType('db.utils')
    def mock_get_document_context_data(*args, **kwargs):
        print(f"MOCK db.utils.get_document_context_data called with args: {args}, kwargs: {kwargs}")
        return {} # Return an empty dict or whatever is appropriate
    mock_db_utils_module.get_document_context_data = mock_get_document_context_data

    # Assign mock_db_utils_module as an attribute of mock_db_module
    setattr(mock_db_module, 'utils', mock_db_utils_module)

    # Add get_user_google_account_by_google_account_id to the main mock_db_module
    def mock_get_user_google_account_by_google_account_id(*args, **kwargs):
        print(f"MOCK db.get_user_google_account_by_google_account_id called")
        return None
    def mock_update_user_google_account(*args, **kwargs):
        print(f"MOCK db.update_user_google_account called")
        return None
    def mock_add_user_google_account(*args, **kwargs): # Added this
        print(f"MOCK db.add_user_google_account called")
        return None
    def mock_get_user_google_account_by_user_id(*args, **kwargs): # Added this
        print(f"MOCK db.get_user_google_account_by_user_id called")
        return None
    def mock_get_user_google_account_by_id(*args, **kwargs): # Added this
        print(f"MOCK db.get_user_google_account_by_id called")
        return None
    def mock_delete_user_google_account(*args, **kwargs):
        print(f"MOCK db.delete_user_google_account called")
        return None
    def mock_add_contact_sync_log(*args, **kwargs): # Added this
        print(f"MOCK db.add_contact_sync_log called")
        return None
    def mock_get_contact_sync_log_by_local_contact(*args, **kwargs): # Added this
        print(f"MOCK db.get_contact_sync_log_by_local_contact called")
        return None
    def mock_get_contact_sync_log_by_google_contact_id(*args, **kwargs): # Added this
        print(f"MOCK db.get_contact_sync_log_by_google_contact_id called")
        return None
    def mock_update_contact_sync_log(*args, **kwargs): # Added this
        print(f"MOCK db.update_contact_sync_log called")
        return None
    def mock_delete_contact_sync_log(*args, **kwargs):
        print(f"MOCK db.delete_contact_sync_log called")
        return None
    def mock_db_initialize_database(*args, **kwargs): # Added this
        print(f"MOCK db.initialize_database called")
        pass
    def mock_db_add_company_personnel(*args, **kwargs): # Added this
        print(f"MOCK db.add_company_personnel called")
        return "mock_global_personnel_id"

    mock_db_module.get_user_google_account_by_google_account_id = mock_get_user_google_account_by_google_account_id
    mock_db_module.update_user_google_account = mock_update_user_google_account
    mock_db_module.add_user_google_account = mock_add_user_google_account
    mock_db_module.get_user_google_account_by_user_id = mock_get_user_google_account_by_user_id
    mock_db_module.get_user_google_account_by_id = mock_get_user_google_account_by_id
    mock_db_module.delete_user_google_account = mock_delete_user_google_account
    mock_db_module.add_contact_sync_log = mock_add_contact_sync_log
    mock_db_module.get_contact_sync_log_by_local_contact = mock_get_contact_sync_log_by_local_contact
    mock_db_module.get_contact_sync_log_by_google_contact_id = mock_get_contact_sync_log_by_google_contact_id
    mock_db_module.update_contact_sync_log = mock_update_contact_sync_log
    mock_db_module.delete_contact_sync_log = mock_delete_contact_sync_log
    mock_db_module.initialize_database = mock_db_initialize_database
    mock_db_module.add_company_personnel = mock_db_add_company_personnel

    def mock_db_get_personnel_for_company(*args, **kwargs): # Added this for the non-fatal error
        print(f"MOCK db.get_personnel_for_company called")
        return []
    mock_db_module.get_personnel_for_company = mock_db_get_personnel_for_company

    def mock_db_update_company_personnel(*args, **kwargs): # Added this for non-fatal error
        print(f"MOCK db.update_company_personnel called")
        return True
    mock_db_module.update_company_personnel = mock_db_update_company_personnel

    def mock_db_delete_company_personnel(*args, **kwargs): # Added this for non-fatal error
        print(f"MOCK db.delete_company_personnel called")
        return True
    mock_db_module.delete_company_personnel = mock_db_delete_company_personnel # Added this


    # Create a mock 'db.cruds' module
    mock_db_cruds_module = types.ModuleType('db.cruds')

    # Create a mock 'db.cruds.companies_crud' module
    mock_db_cruds_companies_crud_module = types.ModuleType('db.cruds.companies_crud')
    def mock_get_default_company(*args, **kwargs):
        print(f"MOCK db.cruds.companies_crud.get_default_company called")
        return None
    def mock_get_all_companies(*args, **kwargs):
        print(f"MOCK db.cruds.companies_crud.get_all_companies called")
        return []
    def mock_add_company(*args, **kwargs):
        print(f"MOCK db.cruds.companies_crud.add_company called")
        return "mock_company_id"
    def mock_update_company(*args, **kwargs):
        print(f"MOCK db.cruds.companies_crud.update_company called")
        return True
    def mock_delete_company(*args, **kwargs):
        print(f"MOCK db.cruds.companies_crud.delete_company called")
        return True
    def mock_get_company_details_by_id(*args, **kwargs):
        print(f"MOCK db.cruds.companies_crud.get_company_details_by_id called")
        return {}
    def mock_set_default_company(*args, **kwargs):
        print(f"MOCK db.cruds.companies_crud.set_default_company called")
        pass
    def mock_add_personnel_to_company(*args, **kwargs):
        print(f"MOCK db.cruds.companies_crud.add_personnel_to_company called")
        return "mock_personnel_id"
    def mock_update_personnel_in_company(*args, **kwargs):
        print(f"MOCK db.cruds.companies_crud.update_personnel_in_company called")
        return True
    def mock_delete_personnel_from_company(*args, **kwargs):
        print(f"MOCK db.cruds.companies_crud.delete_personnel_from_company called")
        return True
    def mock_get_personnel_by_company_id(*args, **kwargs):
        print(f"MOCK db.cruds.companies_crud.get_personnel_by_company_id called")
        return []
    def mock_get_company_by_id(*args, **kwargs): # Added this missing function
        print(f"MOCK db.cruds.companies_crud.get_company_by_id called")
        return None

    mock_db_cruds_companies_crud_module.get_default_company = mock_get_default_company
    mock_db_cruds_companies_crud_module.get_all_companies = mock_get_all_companies
    mock_db_cruds_companies_crud_module.get_company_by_id = mock_get_company_by_id # Added this
    mock_db_cruds_companies_crud_module.add_company = mock_add_company
    mock_db_cruds_companies_crud_module.update_company = mock_update_company
    mock_db_cruds_companies_crud_module.delete_company = mock_delete_company
    mock_db_cruds_companies_crud_module.get_company_details_by_id = mock_get_company_details_by_id
    mock_db_cruds_companies_crud_module.set_default_company = mock_set_default_company
    mock_db_cruds_companies_crud_module.add_personnel_to_company = mock_add_personnel_to_company
    mock_db_cruds_companies_crud_module.update_personnel_in_company = mock_update_personnel_in_company
    mock_db_cruds_companies_crud_module.delete_personnel_from_company = mock_delete_personnel_from_company
    mock_db_cruds_companies_crud_module.get_personnel_by_company_id = mock_get_personnel_by_company_id

    # Assign companies_crud to cruds
    setattr(mock_db_cruds_module, 'companies_crud', mock_db_cruds_companies_crud_module)

    # Assign cruds to db
    setattr(mock_db_module, 'cruds', mock_db_cruds_module)

    # Create a mock 'db.cruds.company_personnel_crud' module
    mock_db_cruds_company_personnel_crud_module = types.ModuleType('db.cruds.company_personnel_crud')
    def mock_cp_get_personnel_by_id(*args, **kwargs): print("MOCK cp_crud.get_personnel_by_id"); return None
    def mock_cp_get_all_personnel_with_company_info(*args, **kwargs): print("MOCK cp_crud.get_all_personnel_with_company_info"); return []
    def mock_cp_get_contacts_for_personnel(*args, **kwargs):
        print("MOCK cp_crud.get_contacts_for_personnel called")
        return []
    def mock_cp_add_company_personnel(*args, **kwargs):
        print("MOCK cp_crud.add_company_personnel called")
        return "mock_personnel_id"
    def mock_cp_get_personnel_for_company(*args, **kwargs):
        print("MOCK cp_crud.get_personnel_for_company called")
        return []
    def mock_cp_update_company_personnel(*args, **kwargs):
        print("MOCK cp_crud.update_company_personnel called")
        return True
    def mock_cp_delete_company_personnel(*args, **kwargs):
        print("MOCK cp_crud.delete_company_personnel called")
        return True
    def mock_cp_add_personnel_contact(*args, **kwargs):
        print("MOCK cp_crud.add_personnel_contact called")
        return "mock_contact_id"
    def mock_cp_update_personnel_contact_link(*args, **kwargs):
        print("MOCK cp_crud.update_personnel_contact_link called")
        return True
    def mock_cp_unlink_contact_from_personnel(*args, **kwargs):
        print("MOCK cp_crud.unlink_contact_from_personnel called")
        return True
    def mock_cp_delete_all_contact_links_for_personnel(*args, **kwargs): # Added this
        print("MOCK cp_crud.delete_all_contact_links_for_personnel called")
        return True

    mock_db_cruds_company_personnel_crud_module.get_personnel_by_id = mock_cp_get_personnel_by_id
    mock_db_cruds_company_personnel_crud_module.get_all_personnel_with_company_info = mock_cp_get_all_personnel_with_company_info
    mock_db_cruds_company_personnel_crud_module.get_contacts_for_personnel = mock_cp_get_contacts_for_personnel
    mock_db_cruds_company_personnel_crud_module.add_company_personnel = mock_cp_add_company_personnel
    mock_db_cruds_company_personnel_crud_module.get_personnel_for_company = mock_cp_get_personnel_for_company
    mock_db_cruds_company_personnel_crud_module.update_company_personnel = mock_cp_update_company_personnel
    mock_db_cruds_company_personnel_crud_module.delete_company_personnel = mock_cp_delete_company_personnel
    mock_db_cruds_company_personnel_crud_module.add_personnel_contact = mock_cp_add_personnel_contact
    mock_db_cruds_company_personnel_crud_module.update_personnel_contact_link = mock_cp_update_personnel_contact_link
    mock_db_cruds_company_personnel_crud_module.unlink_contact_from_personnel = mock_cp_unlink_contact_from_personnel
    mock_db_cruds_company_personnel_crud_module.delete_all_contact_links_for_personnel = mock_cp_delete_all_contact_links_for_personnel # Added this

    # Assign company_personnel_crud to cruds
    setattr(mock_db_cruds_module, 'company_personnel_crud', mock_db_cruds_company_personnel_crud_module)

    # Put the mock modules into sys.modules
    sys.modules['db'] = mock_db_module
    sys.modules['db.utils'] = mock_db_utils_module
    sys.modules['db.cruds'] = mock_db_cruds_module
    sys.modules['db.cruds.companies_crud'] = mock_db_cruds_companies_crud_module
    sys.modules['db.cruds.company_personnel_crud'] = mock_db_cruds_company_personnel_crud_module

    # Create a mock 'db.cruds.template_categories_crud' module
    mock_db_cruds_template_categories_crud_module = types.ModuleType('db.cruds.template_categories_crud')
    def mock_get_all_template_categories(*args, **kwargs):
        print("MOCK template_categories_crud.get_all_template_categories called")
        return []
    mock_db_cruds_template_categories_crud_module.get_all_template_categories = mock_get_all_template_categories
    setattr(mock_db_cruds_module, 'template_categories_crud', mock_db_cruds_template_categories_crud_module)
    sys.modules['db.cruds.template_categories_crud'] = mock_db_cruds_template_categories_crud_module

    # Create a mock 'db.cruds.templates_crud' module
    mock_db_cruds_templates_crud_module = types.ModuleType('db.cruds.templates_crud')
    def mock_get_distinct_template_languages(*args, **kwargs): print("MOCK templates_crud.get_distinct_template_languages called"); return []
    def mock_get_distinct_template_types(*args, **kwargs): print("MOCK templates_crud.get_distinct_template_types called"); return []
    def mock_get_filtered_templates(*args, **kwargs): print("MOCK templates_crud.get_filtered_templates called"); return []
    def mock_get_distinct_template_extensions(*args, **kwargs): print("MOCK templates_crud.get_distinct_template_extensions called"); return [] # Added mock
    mock_db_cruds_templates_crud_module.get_distinct_template_languages = mock_get_distinct_template_languages
    mock_db_cruds_templates_crud_module.get_distinct_template_types = mock_get_distinct_template_types
    mock_db_cruds_templates_crud_module.get_filtered_templates = mock_get_filtered_templates
    mock_db_cruds_templates_crud_module.get_distinct_template_extensions = mock_get_distinct_template_extensions # Added mock
    setattr(mock_db_cruds_module, 'templates_crud', mock_db_cruds_templates_crud_module)
    sys.modules['db.cruds.templates_crud'] = mock_db_cruds_templates_crud_module

    # Create a mock 'db.cruds.clients_crud' module
    mock_db_cruds_clients_crud_module = types.ModuleType('db.cruds.clients_crud')
    # Create a mock instance for clients_crud_instance
    class MockClientsCrudInstance:
        def get_all_clients(self, *args, **kwargs): print("MOCK clients_crud_instance.get_all_clients called"); return []
        # Add other methods that might be called on clients_crud_instance if new errors appear
    mock_db_cruds_clients_crud_module.clients_crud_instance = MockClientsCrudInstance()
    setattr(mock_db_cruds_module, 'clients_crud', mock_db_cruds_clients_crud_module)
    sys.modules['db.cruds.clients_crud'] = mock_db_cruds_clients_crud_module

    # Create a mock 'db.cruds.products_crud' module
    mock_db_cruds_products_crud_module = types.ModuleType('db.cruds.products_crud')
    class MockProductsCrudInstance:
        # Add mock methods here if product_dimension_ui_dialog calls any on products_crud_instance
        def get_all_products(self, *args, **kwargs): print("MOCK products_crud_instance.get_all_products called"); return []
    mock_db_cruds_products_crud_module.products_crud_instance = MockProductsCrudInstance()
    setattr(mock_db_cruds_module, 'products_crud', mock_db_cruds_products_crud_module)
    sys.modules['db.cruds.products_crud'] = mock_db_cruds_products_crud_module

    # Mock icons_rc to prevent SyntaxError during __main__ execution
    print("MAIN_TOP: Pre-patching sys.modules for 'icons_rc'")
    sys.modules['icons_rc'] = types.ModuleType('icons_rc_mock')

# --- Conditional mocking for __main__ END ---

import csv

# Adjust sys.path to allow finding modules in the current directory structure
# This needs to be done before other local package imports if running standalone
current_dir_for_standalone = os.path.dirname(os.path.abspath(__file__))
print(f"Executing from: {current_dir_for_standalone}") # Debug print
if current_dir_for_standalone not in sys.path:
    sys.path.insert(0, current_dir_for_standalone)
    print(f"Inserted into sys.path: {current_dir_for_standalone}") # Debug print
# If 'dialogs', 'company_management' etc. are in a parent or specific source directory:
# parent_dir_for_standalone = os.path.abspath(os.path.join(current_dir_for_standalone, '..'))
# if parent_dir_for_standalone not in sys.path:
#     sys.path.insert(0, parent_dir_for_standalone)

print(f"Initial sys.path: {sys.path}") # Debug print


from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTabWidget, QLabel,
    QFormLayout, QLineEdit, QComboBox, QSpinBox, QFileDialog, QCheckBox,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QMessageBox, QDialog, QTextEdit,
    QGroupBox, QRadioButton, QHeaderView, QListWidget, QListWidgetItem # Added QHeaderView, QListWidget, QListWidgetItem
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

# Assuming db_manager provides the necessary functions directly or via submodules
# This import will be problematic if 'db' is not in sys.path or structured as expected.
# For the __main__ block, we'll mock it.
try:
    import db as db_manager # If __name__ == '__main__', this should import MockDBForGlobalImport
    if __name__ == '__main__':
        print(f"MAIN_POST_DB_IMPORT: db_manager is {db_manager}")
except ImportError:
    print("ERROR: Failed to import 'db' module globally.") # Changed message for clarity
    db_manager = None # Will be replaced by mock in __main__ if None

try:
    from db.cruds.products_crud import products_crud_instance
except ImportError:
    print("ERROR: Failed to import 'products_crud_instance' from 'db.cruds.products_crud'. Export functionality will be affected.")
    products_crud_instance = None # Ensure it exists, even if None

# Import CONFIGURABLE_MODULES from gui.main_window
# This requires gui.main_window to be importable.
# If running settings_page.py standalone, this might need careful handling or mocking.
try:
    from utils.app_constants import CONFIGURABLE_MODULES # Import from new location
except ImportError as e_configurable_modules:
    print(f"ERROR settings_page.py: Could not import CONFIGURABLE_MODULES from utils.app_constants: {e_configurable_modules}")
    CONFIGURABLE_MODULES = [] # Fallback to empty list

from dialogs.transporter_dialog import TransporterDialog
from dialogs.freight_forwarder_dialog import FreightForwarderDialog
from company_management import CompanyTabWidget
from securite.security_settings_page import SecuritySettingsPage # Import de la nouvelle page
from dialogs.smtp_config_dialog import SmtpConfigDialog # Import the new dialog
try:
    from user_profile_management.my_business_widget import MyBusinessWidget
    USER_PROFILE_MODULE_AVAILABLE = True
except ImportError as e_user_profile:
    print(f"WARNING: Could not import MyBusinessWidget: {e_user_profile}. 'My Business' tab will be unavailable.")
    MyBusinessWidget = None # Placeholder
    USER_PROFILE_MODULE_AVAILABLE = False

class ImportInstructionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Product Import Instructions"))
        self.setMinimumWidth(600) # Set a minimum width for better readability
        self.setMinimumHeight(400) # Set a minimum height

        layout = QVBoxLayout(self)

        instructions_text_edit = QTextEdit()
        instructions_text_edit.setReadOnly(True)
        instructions_html = """
        <h3>Product CSV Import Guide</h3>
        <p>Please ensure your CSV file adheres to the following format and conventions.</p>

        <h4>Expected CSV Header:</h4>
        <p><code>product_id,product_name,product_code,description,category,language_code,base_unit_price,unit_of_measure,weight,dimensions,is_active,is_deleted</code></p>

        <h4>Field Definitions:</h4>
        <ul>
            <li><b>product_id</b>: Ignored during import (new IDs are auto-generated).</li>
            <li><b>product_name</b>: Text (Required).</li>
            <li><b>product_code</b>: Text (Required). Should be unique.</li>
            <li><b>description</b>: Text (Optional).</li>
            <li><b>category</b>: Text (Optional).</li>
            <li><b>language_code</b>: Text, e.g., 'en', 'fr' (Optional, defaults to 'fr' if empty).</li>
            <li><b>base_unit_price</b>: Number, e.g., 10.99 (Required).</li>
            <li><b>unit_of_measure</b>: Text, e.g., 'pcs', 'kg' (Optional).</li>
            <li><b>weight</b>: Number (Optional).</li>
            <li><b>dimensions</b>: Text, e.g., "LxWxH" (Optional).</li>
            <li><b>is_active</b>: Boolean, 'True' or 'False' (Optional, defaults to 'True' if empty or invalid).</li>
            <li><b>is_deleted</b>: Boolean, 'True' or 'False' (Optional, defaults to 'False' if empty or invalid).</li>
        </ul>

        <h4>Sample ChatGPT Prompt for Generating Data:</h4>
        <pre><code>Generate a CSV list of 10 sample products for an e-commerce store. The CSV should have the following columns: product_name,product_code,description,category,language_code,base_unit_price,unit_of_measure,weight,dimensions,is_active,is_deleted
Ensure `base_unit_price` is a number. `language_code` should be 'en' or 'fr'. `is_active` and `is_deleted` should be 'True' or 'False'.

Example Row:
My Awesome Product,PROD001,This is a great product.,Electronics,en,29.99,pcs,0.5,10x5x2 cm,True,False</code></pre>
        """
        instructions_text_edit.setHtml(instructions_html)
        layout.addWidget(instructions_text_edit)

        # Dialog buttons
        buttons_layout = QHBoxLayout()
        ok_button = QPushButton(self.tr("OK"))
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton(self.tr("Cancel"))
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

class SettingsPage(QWidget):
    def __init__(self, main_config, app_root_dir, current_user_id, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsPage")
        self.main_config = main_config
        self.app_root_dir = app_root_dir
        self.current_user_id = current_user_id

        self.module_config = [
            {"key": "module_project_management_enabled", "label_text": self.tr("Project Management")},
            {"key": "module_product_management_enabled", "label_text": self.tr("Product Management")},
            {"key": "module_partner_management_enabled", "label_text": self.tr("Partner Management")},
            {"key": "module_statistics_enabled", "label_text": self.tr("Statistics")},
            {"key": "module_inventory_management_enabled", "label_text": self.tr("Inventory Management")},
            {"key": "module_botpress_integration_enabled", "label_text": self.tr("Botpress Integration")},
            {"key": "module_carrier_map_enabled", "label_text": self.tr("Carrier Map")},
            {"key": "module_camera_management_enabled", "label_text": self.tr("Camera Management")}, # New module
        ]
        self.module_radio_buttons = {} # To store radio buttons for easy access

        # This is important if db_manager was not imported successfully above
        # And we are not running the __main__ block (e.g. in actual app)
        # It relies on the global db_manager being set by the main application

        # In __main__ mode, db_manager might be MockDBForGlobalImport initially.
        # It will be replaced by the more complete MockDBManager instance from the __main__ block
        # before SettingsPage is fully used.
        # The critical part is that the *global symbol* 'db_manager' needs to be the correct mock
        # by the time methods using it are called, or it's passed to other objects.

        # For non-__main__ mode, the original logic applies.
        # For __main__ mode, the global 'db_manager' is what SettingsPage's __init__ will see.
        # This global 'db_manager' is explicitly set to a full MockDBManager instance
        # at the beginning of the 'if __name__ == "__main__":' block.
        global db_manager # Ensure we are referring to the global one

        if __name__ != '__main__': # Original logic for non-test mode
            if db_manager is None and 'db_manager' in globals() and globals()['db_manager'] is not None:
                pass
            elif db_manager is None :
                print("WARNING: db_manager is None in SettingsPage init and not running __main__")
        else: # In __main__ mode, db_manager should already be the MockDBManager instance.
            if db_manager is None: # Should not happen if __main__ block sets it
                 print("WARNING: db_manager is None in SettingsPage init even when running __main__!")
            # else:
            #    print(f"DEBUG SETTINGSPAGE __init__: db_manager is {type(db_manager)}")


        main_layout = QVBoxLayout(self)
        title_label = QLabel(self.tr("Application Settings"))
        title_label.setObjectName("pageTitleLabel")
        title_label.setAlignment(Qt.AlignLeft)
        main_layout.addWidget(title_label)

        self.tabs_widget = QTabWidget()
        self.tabs_widget.setObjectName("settingsTabs")

        # Initialize new tab structure
        self._setup_general_settings_tab()
        self._setup_company_personnel_tab()
        # self._setup_connectivity_services_tab() # This is now split
        self._setup_global_smtp_configs_tab()
        self._setup_user_email_assignment_tab()
        self._setup_application_modules_tab()
        self._setup_data_backup_tab()
        self._setup_logistics_tab()
        self._setup_document_templates_tab()
        self._setup_document_customization_tab()
        self._setup_menu_customization_tab() # New tab for menu customization
        self._setup_security_tab()
        self._setup_my_business_tab() # New tab for "My Business"


        main_layout.addWidget(self.tabs_widget)
        main_layout.addStretch(1) # Pushes tabs to the top, buttons to bottom

        # --- Buttons Layout ---
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10) # Standard spacing between buttons

        self.reload_settings_button = QPushButton(self.tr("🔄 Reload Current Settings"))
        self.reload_settings_button.setObjectName("secondaryButton") # For styling
        self.reload_settings_button.setToolTip(self.tr("Reloads all settings from the configuration, discarding any unsaved changes."))
        self.reload_settings_button.clicked.connect(self._load_all_settings_from_config)

        self.restore_defaults_button = QPushButton(self.tr("⚙️ Restore Default Settings"))
        self.restore_defaults_button.setObjectName("secondaryButton") # For styling
        self.restore_defaults_button.setToolTip(self.tr("Resets all settings to their original default values. This action requires confirmation and an application restart."))
        self.restore_defaults_button.clicked.connect(self._confirm_restore_defaults)

        self.save_settings_button = QPushButton(self.tr("💾 Save All Settings"))
        self.save_settings_button.setObjectName("primaryButton") # For styling
        self.save_settings_button.setToolTip(self.tr("Saves all current settings. Some changes may require an application restart."))
        self.save_settings_button.clicked.connect(self._save_all_settings)

        buttons_layout.addStretch(1) # Pushes buttons to the right
        buttons_layout.addWidget(self.reload_settings_button)
        buttons_layout.addWidget(self.restore_defaults_button)
        buttons_layout.addWidget(self.save_settings_button)

        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)

        self._load_all_settings_from_config() # Load initial settings

        if db_manager:
            # These are now part of specific tabs, their loading should be called from there or _load_all_settings_from_config
            # self._load_transporters_table() # Initial load for logistics tab
            # self._load_forwarders_table() # Initial load for logistics tab
            pass # Loading is handled by individual tab setup or _load_all_settings_from_config
        else:
            print("WARNING: db_manager not available. Some settings (e.g., Transporters, Forwarders, Modules) will not be loaded or saved.")

    # --- New Tab Setup Methods ---
    def _setup_general_settings_tab(self):
        tab_widget = QWidget()
        main_layout = QVBoxLayout(tab_widget)
        main_layout.setContentsMargins(15, 15, 15, 15) # Consistent margins
        main_layout.setSpacing(15) # Consistent spacing

        # --- Interface Settings Group ---
        interface_group = QGroupBox(self.tr("Interface & Display"))
        interface_layout = QFormLayout(interface_group)
        interface_layout.setSpacing(10)

        self.interface_lang_combo = QComboBox()
        self.lang_display_to_code = {
            self.tr("French (fr)"): "fr", self.tr("English (en)"): "en",
            self.tr("Arabic (ar)"): "ar", self.tr("Turkish (tr)"): "tr",
            self.tr("Portuguese (pt)"): "pt", self.tr("Russian (ru)"): "ru"
        }
        self.interface_lang_combo.addItems(list(self.lang_display_to_code.keys()))
        self.interface_lang_combo.setToolTip(self.tr("Select the application's display language. A restart is required for changes to take effect."))
        interface_layout.addRow(self.tr("Interface Language:"), self.interface_lang_combo)

        self.session_timeout_spinbox = QSpinBox()
        self.session_timeout_spinbox.setRange(5, 525600) # Min 5 mins, Max ~1 year (in minutes)
        self.session_timeout_spinbox.setSuffix(self.tr(" minutes"))
        self.session_timeout_spinbox.setToolTip(self.tr("Set session inactivity timeout. Examples: 1440 (1 day), 10080 (1 week), 43200 (30 days)."))
        interface_layout.addRow(self.tr("Session Timeout:"), self.session_timeout_spinbox)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems([self.tr("Light"), self.tr("Dark")])
        self.theme_combo.setToolTip(self.tr("Select the application theme. A restart may be required for all elements to update."))
        interface_layout.addRow(self.tr("Theme:"), self.theme_combo)

        main_layout.addWidget(interface_group)

        # --- Behavior Settings Group ---
        behavior_group = QGroupBox(self.tr("Application Behavior"))
        behavior_layout = QFormLayout(behavior_group)
        behavior_layout.setSpacing(10)

        self.reminder_days_spinbox = QSpinBox()
        self.reminder_days_spinbox.setRange(1, 365)
        self.reminder_days_spinbox.setToolTip(self.tr("Number of days of inactivity after which a client is considered 'old' for reminders."))
        behavior_layout.addRow(self.tr("Old Client Reminder (days):"), self.reminder_days_spinbox)

        self.google_maps_url_input = QLineEdit()
        self.google_maps_url_input.setPlaceholderText(self.tr("Enter full Google Maps review URL (e.g., https://maps.google.com/?cid=...)"))
        self.google_maps_url_input.setToolTip(self.tr("Link to your Google Maps page for client reviews."))
        behavior_layout.addRow(self.tr("Google Maps Review Link:"), self.google_maps_url_input)

        self.show_setup_prompt_checkbox = QCheckBox(self.tr("Show initial setup prompt on next startup if no company is configured"))
        self.show_setup_prompt_checkbox.setToolTip(self.tr("If checked, the initial company setup dialog will appear at startup if no default company exists."))
        behavior_layout.addRow(self.show_setup_prompt_checkbox)

        self.check_license_on_startup_checkbox = QCheckBox(self.tr("Vérifier la validité de la licence au démarrage"))
        self.check_license_on_startup_checkbox.setToolTip(self.tr("Si décoché, l'application ne vérifiera pas la licence au démarrage et autorisera l'accès."))
        behavior_layout.addRow(self.check_license_on_startup_checkbox) # Add to the form layout

        main_layout.addWidget(behavior_group)

        # --- Geographic Scope Settings Group ---
        geo_scope_group = QGroupBox(self.tr("Portée Géographique de l'Activité"))
        geo_scope_layout = QFormLayout(geo_scope_group)
        geo_scope_layout.setSpacing(10)

        self.geo_scope_combo = QComboBox()
        self.geo_scope_options = {
            self.tr("Internationale"): "international",
            self.tr("Régionale"): "regional",
            self.tr("Locale (Ville)"): "local"
        }
        self.geo_scope_combo.addItems(list(self.geo_scope_options.keys()))
        self.geo_scope_combo.setToolTip(self.tr("Définissez la portée géographique de votre activité pour adapter l'affichage des cartes."))
        geo_scope_layout.addRow(self.tr("Portée de l'activité :"), self.geo_scope_combo)

        main_layout.addWidget(geo_scope_group)
        main_layout.addStretch(1) # Push content to the top
        self.tabs_widget.addTab(tab_widget, self.tr("General"))

    def _setup_company_personnel_tab(self):
        # This tab uses the existing CompanyTabWidget
        self.company_tab_widget_instance = CompanyTabWidget( # Renamed to avoid conflict if self.company_tab was used elsewhere
            parent=self, # Pass self as parent
            app_root_dir=self.app_root_dir,
            current_user_id=self.current_user_id
        )
        # CompanyTabWidget is already a QWidget, so it can be added directly.
        # It should handle its own internal layout and group boxes if needed.
        self.tabs_widget.addTab(self.company_tab_widget_instance, self.tr("Company & Personnel"))
        # Loading and saving for this tab is presumably handled within CompanyTabWidget or called by _load/save_all_settings.

    # def _setup_connectivity_services_tab(self): -- This method is now removed and split --

    def _setup_global_smtp_configs_tab(self):
        """Sets up the tab for managing global SMTP configurations."""
        global_smtp_tab_widget = QWidget()
        main_layout = QVBoxLayout(global_smtp_tab_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        global_smtp_group = QGroupBox(self.tr("Configurations SMTP Globales"))
        global_smtp_group_layout = QVBoxLayout(global_smtp_group)

        self.smtp_configs_table = QTableWidget()
        self.smtp_configs_table.setObjectName("smtpConfigsTable")
        self.smtp_configs_table.setColumnCount(7)
        self.smtp_configs_table.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Nom Config"), self.tr("Serveur"),
            self.tr("Port"), self.tr("Utilisateur"), self.tr("Email Exp."), self.tr("Défaut Global")
        ])
        self.smtp_configs_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.smtp_configs_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.smtp_configs_table.horizontalHeader().setStretchLastSection(True)
        self.smtp_configs_table.setColumnHidden(0, True)
        self.smtp_configs_table.setColumnWidth(1, 150)
        self.smtp_configs_table.setColumnWidth(2, 150)
        self.smtp_configs_table.setColumnWidth(4, 120)
        self.smtp_configs_table.setColumnWidth(5, 150)
        self.smtp_configs_table.itemSelectionChanged.connect(self._update_smtp_buttons_state)
        global_smtp_group_layout.addWidget(self.smtp_configs_table)

        smtp_buttons_layout = QHBoxLayout()
        self.add_smtp_config_btn = QPushButton(self.tr("➕ Ajouter"))
        self.add_smtp_config_btn.setToolTip(self.tr("Ajouter une nouvelle configuration SMTP globale."))
        self.add_smtp_config_btn.clicked.connect(self._handle_add_smtp_config)
        smtp_buttons_layout.addWidget(self.add_smtp_config_btn)

        self.edit_smtp_config_btn = QPushButton(self.tr("✏️ Modifier"))
        self.edit_smtp_config_btn.setToolTip(self.tr("Modifier la configuration SMTP sélectionnée."))
        self.edit_smtp_config_btn.setEnabled(False)
        self.edit_smtp_config_btn.clicked.connect(self._handle_edit_smtp_config)
        smtp_buttons_layout.addWidget(self.edit_smtp_config_btn)

        self.delete_smtp_config_btn = QPushButton(self.tr("🗑️ Supprimer"))
        self.delete_smtp_config_btn.setObjectName("dangerButton")
        self.delete_smtp_config_btn.setToolTip(self.tr("Supprimer la configuration SMTP sélectionnée."))
        self.delete_smtp_config_btn.setEnabled(False)
        self.delete_smtp_config_btn.clicked.connect(self._handle_delete_smtp_config)
        smtp_buttons_layout.addWidget(self.delete_smtp_config_btn)

        smtp_buttons_layout.addStretch(1)

        self.set_global_default_smtp_btn = QPushButton(self.tr("⭐ Définir par Défaut (Global)"))
        self.set_global_default_smtp_btn.setToolTip(self.tr("Définir la configuration SMTP sélectionnée comme défaut global pour l'application."))
        self.set_global_default_smtp_btn.setEnabled(False)
        self.set_global_default_smtp_btn.clicked.connect(self._handle_set_global_default_smtp)
        smtp_buttons_layout.addWidget(self.set_global_default_smtp_btn)

        global_smtp_group_layout.addLayout(smtp_buttons_layout)
        main_layout.addWidget(global_smtp_group)
        main_layout.addStretch(1)
        self.tabs_widget.addTab(global_smtp_tab_widget, self.tr("Configurations SMTP Globales"))

    def _setup_user_email_assignment_tab(self):
        """Sets up the tab for assigning email configurations to users."""
        user_assignment_tab_widget = QWidget()
        main_layout = QVBoxLayout(user_assignment_tab_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        user_email_assignment_group = QGroupBox(self.tr("Affectation des Emails aux Utilisateurs"))
        assignment_main_layout = QVBoxLayout(user_email_assignment_group)
        assignment_main_layout.setSpacing(10)

        user_selection_layout = QHBoxLayout()
        user_selection_layout.addWidget(QLabel(self.tr("Utilisateur :")))
        self.assign_user_combo = QComboBox()
        self.assign_user_combo.setToolTip(self.tr("Sélectionner un utilisateur pour gérer ses affectations d'email."))
        self.assign_user_combo.currentIndexChanged.connect(self._load_assigned_smtp_for_selected_user)
        self.assign_user_combo.currentIndexChanged.connect(self._update_user_assignment_buttons_state)
        user_selection_layout.addWidget(self.assign_user_combo)
        user_selection_layout.addStretch(1)
        assignment_main_layout.addLayout(user_selection_layout)

        self.user_assigned_smtp_table = QTableWidget()
        self.user_assigned_smtp_table.setObjectName("userAssignedSmtpTable")
        self.user_assigned_smtp_table.setColumnCount(4)
        self.user_assigned_smtp_table.setHorizontalHeaderLabels([
            self.tr("ID Affect."), self.tr("Nom Config SMTP"),
            self.tr("Email Expéditeur"), self.tr("Défaut pour Utilisateur")
        ])
        self.user_assigned_smtp_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.user_assigned_smtp_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.user_assigned_smtp_table.horizontalHeader().setStretchLastSection(True)
        self.user_assigned_smtp_table.setColumnHidden(0, True)
        self.user_assigned_smtp_table.setColumnWidth(1, 200)
        self.user_assigned_smtp_table.setColumnWidth(2, 200)
        self.user_assigned_smtp_table.itemSelectionChanged.connect(self._update_user_assignment_buttons_state)
        assignment_main_layout.addWidget(self.user_assigned_smtp_table)

        assign_new_layout = QHBoxLayout()
        assign_new_layout.addWidget(QLabel(self.tr("Assigner Config Globale :")))
        self.assign_global_smtp_combo = QComboBox()
        self.assign_global_smtp_combo.setToolTip(self.tr("Choisir une configuration SMTP globale à assigner à l'utilisateur sélectionné."))
        self.assign_global_smtp_combo.currentIndexChanged.connect(self._update_user_assignment_buttons_state)
        assign_new_layout.addWidget(self.assign_global_smtp_combo)
        self.assign_smtp_to_user_btn = QPushButton(self.tr("➕ Assigner à l'Utilisateur"))
        self.assign_smtp_to_user_btn.setToolTip(self.tr("Assigner la configuration SMTP globale sélectionnée à l'utilisateur."))
        self.assign_smtp_to_user_btn.setEnabled(False)
        self.assign_smtp_to_user_btn.clicked.connect(self._handle_assign_smtp_to_user)
        assign_new_layout.addWidget(self.assign_smtp_to_user_btn)
        assign_new_layout.addStretch(1)
        assignment_main_layout.addLayout(assign_new_layout)

        user_assignment_buttons_layout = QHBoxLayout()
        self.set_user_default_smtp_btn = QPushButton(self.tr("⭐ Définir par Défaut (Utilisateur)"))
        self.set_user_default_smtp_btn.setToolTip(self.tr("Définir la configuration SMTP assignée sélectionnée comme défaut pour cet utilisateur."))
        self.set_user_default_smtp_btn.setEnabled(False)
        self.set_user_default_smtp_btn.clicked.connect(self._handle_set_user_default_smtp)
        user_assignment_buttons_layout.addWidget(self.set_user_default_smtp_btn)

        self.unassign_smtp_from_user_btn = QPushButton(self.tr("🗑️ Désassigner de l'Utilisateur"))
        self.unassign_smtp_from_user_btn.setObjectName("dangerButton")
        self.unassign_smtp_from_user_btn.setToolTip(self.tr("Désassigner la configuration SMTP de cet utilisateur."))
        self.unassign_smtp_from_user_btn.setEnabled(False)
        self.unassign_smtp_from_user_btn.clicked.connect(self._handle_unassign_smtp_from_user)
        user_assignment_buttons_layout.addWidget(self.unassign_smtp_from_user_btn)
        user_assignment_buttons_layout.addStretch(1)
        assignment_main_layout.addLayout(user_assignment_buttons_layout)

        main_layout.addWidget(user_email_assignment_group)
        main_layout.addStretch(1)
        self.tabs_widget.addTab(user_assignment_tab_widget, self.tr("Affectations Email Utilisateurs"))

    def _setup_application_modules_tab(self):
        modules_tab_widget = QWidget()
        main_layout = QVBoxLayout(modules_tab_widget) # Use QVBoxLayout for overall tab structure
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        modules_group = QGroupBox(self.tr("Module Activation Status"))
        modules_form_layout = QFormLayout(modules_group) # Use QFormLayout for label-widget pairs
        modules_form_layout.setSpacing(10)

        for module_info in self.module_config:
            key = module_info["key"]
            label_text = module_info["label_text"]
            module_label = QLabel(label_text)

            # Radio button group for each module
            radio_button_widget = QWidget() # Container for radio buttons
            radio_layout = QHBoxLayout(radio_button_widget)
            radio_layout.setContentsMargins(0,0,0,0) # No extra margins for this inner layout

            radio_enabled = QRadioButton(self.tr("Enabled"))
            radio_disabled = QRadioButton(self.tr("Disabled"))
            radio_layout.addWidget(radio_enabled)
            radio_layout.addWidget(radio_disabled)
            radio_layout.addStretch() # Pushes radio buttons to the left

            self.module_radio_buttons[key] = {"enabled": radio_enabled, "disabled": radio_disabled}
            modules_form_layout.addRow(module_label, radio_button_widget)

        main_layout.addWidget(modules_group)

        restart_notice_label = QLabel(self.tr("Changes to module activation require an application restart to take full effect."))
        restart_notice_label.setWordWrap(True)
        restart_notice_label.setStyleSheet("font-style: italic; color: grey;") # Informational style
        main_layout.addWidget(restart_notice_label)

        main_layout.addStretch(1) # Push content to the top
        self.tabs_widget.addTab(modules_tab_widget, self.tr("Application Modules"))

    def _setup_data_backup_tab(self):
        tab_widget = QWidget()
        main_layout = QVBoxLayout(tab_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # --- Database Settings Group ---
        db_group = QGroupBox(self.tr("Database Configuration"))
        db_form_layout = QFormLayout(db_group)
        db_form_layout.setSpacing(10)

        self.db_path_input = QLineEdit()
        self.db_path_input.setPlaceholderText(self.tr("Path to your SQLite database file"))
        self.db_path_input.setToolTip(self.tr("Select the application's database file. Changing this requires a restart."))
        db_path_browse_btn = QPushButton(self.tr("📁 Browse..."))
        db_path_browse_btn.clicked.connect(lambda: self._browse_db_file(self.db_path_input))
        db_path_layout = QHBoxLayout()
        db_path_layout.addWidget(self.db_path_input)
        db_path_layout.addWidget(db_path_browse_btn)
        db_form_layout.addRow(self.tr("Database File Path:"), db_path_layout)

        self.db_type_combo = QComboBox()
        self.db_type_combo.setToolTip(self.tr("Select the database system. Currently, only SQLite is fully supported."))
        self.db_type_combo.addItem("SQLite", "sqlite")
        # Add future options as disabled for now
        self.db_type_combo.addItem("PostgreSQL (experimental)", "postgresql")
        # self.db_type_combo.model().item(self.db_type_combo.count() - 1).setEnabled(False) # Temporarily enable for development
        self.db_type_combo.addItem("MySQL (experimental)", "mysql")
        self.db_type_combo.model().item(self.db_type_combo.count() - 1).setEnabled(False)
        db_form_layout.addRow(self.tr("Database Type:"), self.db_type_combo)

        # --- PostgreSQL Specific Settings (initially hidden) ---
        self.pg_settings_group = QGroupBox(self.tr("PostgreSQL Connection Details"))
        pg_settings_layout = QFormLayout(self.pg_settings_group)
        pg_settings_layout.setSpacing(10)

        self.pg_host_input = QLineEdit()
        self.pg_host_input.setPlaceholderText(self.tr("e.g., localhost or IP address"))
        pg_settings_layout.addRow(self.tr("PostgreSQL Host:"), self.pg_host_input)

        self.pg_port_spinbox = QSpinBox()
        self.pg_port_spinbox.setRange(1, 65535)
        self.pg_port_spinbox.setToolTip(self.tr("Default PostgreSQL port is 5432."))
        pg_settings_layout.addRow(self.tr("PostgreSQL Port:"), self.pg_port_spinbox)

        self.pg_user_input = QLineEdit()
        self.pg_user_input.setPlaceholderText(self.tr("Your PostgreSQL username"))
        pg_settings_layout.addRow(self.tr("PostgreSQL User:"), self.pg_user_input)

        self.pg_password_input = QLineEdit()
        self.pg_password_input.setEchoMode(QLineEdit.Password)
        self.pg_password_input.setPlaceholderText(self.tr("Your PostgreSQL password"))
        pg_settings_layout.addRow(self.tr("PostgreSQL Password:"), self.pg_password_input)

        self.pg_dbname_input = QLineEdit()
        self.pg_dbname_input.setPlaceholderText(self.tr("Name of the PostgreSQL database"))
        pg_settings_layout.addRow(self.tr("PostgreSQL Database Name:"), self.pg_dbname_input)

        # SSL Mode
        self.pg_ssl_mode_combo = QComboBox()
        self.pg_ssl_mode_combo.addItems(["disable", "allow", "prefer", "require", "verify-ca", "verify-full"])
        self.pg_ssl_mode_combo.setToolTip(self.tr("SSL connection mode. 'disable' for no SSL, 'require' for mandatory SSL."))
        pg_settings_layout.addRow(self.tr("PostgreSQL SSL Mode:"), self.pg_ssl_mode_combo)

        # SSL Root Certificate
        self.pg_ssl_rootcert_input = QLineEdit()
        self.pg_ssl_rootcert_input.setPlaceholderText(self.tr("Path to SSL root CA certificate file (optional)"))
        pg_ssl_rootcert_browse_btn = QPushButton(self.tr("Browse..."))
        pg_ssl_rootcert_browse_btn.clicked.connect(lambda: self._browse_file(self.pg_ssl_rootcert_input, self.tr("Select SSL Root CA File")))
        pg_ssl_rootcert_layout = QHBoxLayout()
        pg_ssl_rootcert_layout.addWidget(self.pg_ssl_rootcert_input)
        pg_ssl_rootcert_layout.addWidget(pg_ssl_rootcert_browse_btn)
        pg_settings_layout.addRow(self.tr("PostgreSQL SSL Root CA:"), pg_ssl_rootcert_layout)

        # SSL Client Certificate
        self.pg_ssl_clientcert_input = QLineEdit()
        self.pg_ssl_clientcert_input.setPlaceholderText(self.tr("Path to SSL client certificate file (optional)"))
        pg_ssl_clientcert_browse_btn = QPushButton(self.tr("Browse..."))
        pg_ssl_clientcert_browse_btn.clicked.connect(lambda: self._browse_file(self.pg_ssl_clientcert_input, self.tr("Select SSL Client Certificate File")))
        pg_ssl_clientcert_layout = QHBoxLayout()
        pg_ssl_clientcert_layout.addWidget(self.pg_ssl_clientcert_input)
        pg_ssl_clientcert_layout.addWidget(pg_ssl_clientcert_browse_btn)
        pg_settings_layout.addRow(self.tr("PostgreSQL SSL Client Cert:"), pg_ssl_clientcert_layout)

        # SSL Client Key
        self.pg_ssl_clientkey_input = QLineEdit()
        self.pg_ssl_clientkey_input.setPlaceholderText(self.tr("Path to SSL client key file (optional)"))
        pg_ssl_clientkey_browse_btn = QPushButton(self.tr("Browse..."))
        pg_ssl_clientkey_browse_btn.clicked.connect(lambda: self._browse_file(self.pg_ssl_clientkey_input, self.tr("Select SSL Client Key File")))
        pg_ssl_clientkey_layout = QHBoxLayout()
        pg_ssl_clientkey_layout.addWidget(self.pg_ssl_clientkey_input)
        pg_ssl_clientkey_layout.addWidget(pg_ssl_clientkey_browse_btn)
        pg_settings_layout.addRow(self.tr("PostgreSQL SSL Client Key:"), pg_ssl_clientkey_layout)



        db_form_layout.addRow(self.pg_settings_group) # Add the group to the main DB form layout
        self.pg_settings_group.setVisible(False) # Initially hidden

        self.db_type_combo.currentIndexChanged.connect(self._toggle_pg_settings_visibility) # Connect signal

        main_layout.addWidget(db_group)


        # --- Data Import/Export Group ---
        data_ops_group = QGroupBox(self.tr("Data Import & Export"))
        data_ops_layout = QVBoxLayout(data_ops_group) # QVBoxLayout for buttons
        data_ops_layout.setSpacing(10)

        self.import_products_btn = QPushButton(self.tr("⬆️ Import Products from CSV"))
        self.import_products_btn.setToolTip(self.tr("Import product data from a CSV file."))
        self.import_products_btn.clicked.connect(self._handle_import_products)
        data_ops_layout.addWidget(self.import_products_btn)

        self.export_products_btn = QPushButton(self.tr("⬇️ Export Products to CSV"))
        self.export_products_btn.setToolTip(self.tr("Export current product data to a CSV file."))
        self.export_products_btn.clicked.connect(self._handle_export_products)
        data_ops_layout.addWidget(self.export_products_btn)
        main_layout.addWidget(data_ops_group)

        # --- Download Monitoring Group ---
        download_monitor_group = QGroupBox(self.tr("Automated Download Monitoring"))
        download_monitor_form_layout = QFormLayout(download_monitor_group)
        download_monitor_form_layout.setSpacing(10)

        self.download_monitor_enabled_checkbox = QCheckBox(self.tr("Enable download monitoring service"))
        self.download_monitor_enabled_checkbox.setToolTip(self.tr("Monitors a specified folder for new downloads to process them automatically."))
        download_monitor_form_layout.addRow(self.download_monitor_enabled_checkbox)

        self.download_monitor_path_input = QLineEdit()
        self.download_monitor_path_input.setPlaceholderText(self.tr("Path to the folder to monitor"))
        browse_download_path_btn = QPushButton(self.tr("📁 Browse..."))
        browse_download_path_btn.clicked.connect(self._browse_download_monitor_path)
        download_path_layout = QHBoxLayout()
        download_path_layout.addWidget(self.download_monitor_path_input)
        download_path_layout.addWidget(browse_download_path_btn)
        download_monitor_form_layout.addRow(self.tr("Monitored Folder:"), download_path_layout)
        main_layout.addWidget(download_monitor_group)

        # --- Backup Settings Group ---
        backup_group = QGroupBox(self.tr("Remote Backup Configuration"))
        backup_form_layout = QFormLayout(backup_group)
        backup_form_layout.setSpacing(10)

        self.backup_server_address_input = QLineEdit()
        self.backup_server_address_input.setPlaceholderText(self.tr("e.g., backup.example.com or IP address"))
        backup_form_layout.addRow(self.tr("Server Address:"), self.backup_server_address_input)

        self.backup_port_input = QLineEdit() # Using QLineEdit for port as it might be non-numeric in some configs (e.g. service name)
        self.backup_port_input.setPlaceholderText(self.tr("e.g., 22 (SFTP), 443 (HTTPS)"))
        backup_form_layout.addRow(self.tr("Port:"), self.backup_port_input)

        self.backup_username_input = QLineEdit()
        self.backup_username_input.setPlaceholderText(self.tr("Username for backup server"))
        backup_form_layout.addRow(self.tr("Username:"), self.backup_username_input)

        self.backup_password_input = QLineEdit()
        self.backup_password_input.setEchoMode(QLineEdit.Password)
        self.backup_password_input.setPlaceholderText(self.tr("Password for backup server"))
        backup_form_layout.addRow(self.tr("Password:"), self.backup_password_input)

        self.run_backup_button = QPushButton(self.tr("☁️ Run Manual Backup Now"))
        self.run_backup_button.setObjectName("primaryButton")
        self.run_backup_button.setToolTip(self.tr("Initiates a manual backup to the configured remote server."))
        self.run_backup_button.clicked.connect(self._handle_run_backup)
        backup_form_layout.addRow(self.run_backup_button) # Add button to the form for alignment
        main_layout.addWidget(backup_group)

        main_layout.addStretch(1)
        self.tabs_widget.addTab(tab_widget, self.tr("Data & Backup"))


    def _setup_logistics_tab(self):
        tab_widget = QWidget()
        main_layout = QVBoxLayout(tab_widget) # Main layout for the tab
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # --- Transporters Group ---
        transporters_group = QGroupBox(self.tr("Manage Transporters"))
        transporters_group_layout = QVBoxLayout(transporters_group) # Layout for content within the group
        transporters_group_layout.setSpacing(10)

        self.transporters_table = QTableWidget()
        self.transporters_table.setColumnCount(6)
        self.transporters_table.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Name"), self.tr("Contact Person"),
            self.tr("Phone"), self.tr("Email"), self.tr("Service Area")
        ])
        self.transporters_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.transporters_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.transporters_table.horizontalHeader().setStretchLastSection(True)
        self.transporters_table.hideColumn(0) # Hide ID column
        self.transporters_table.itemSelectionChanged.connect(self._update_transporter_button_states)
        transporters_group_layout.addWidget(self.transporters_table)

        transporter_btns_layout = QHBoxLayout()
        self.add_transporter_btn = QPushButton(self.tr("➕ Add Transporter"))
        self.add_transporter_btn.clicked.connect(self._handle_add_transporter)
        self.edit_transporter_btn = QPushButton(self.tr("✏️ Edit Selected"))
        self.edit_transporter_btn.setEnabled(False)
        self.edit_transporter_btn.clicked.connect(self._handle_edit_transporter)
        self.delete_transporter_btn = QPushButton(self.tr("🗑️ Delete Selected"))
        self.delete_transporter_btn.setObjectName("dangerButton")
        self.delete_transporter_btn.setEnabled(False)
        self.delete_transporter_btn.clicked.connect(self._handle_delete_transporter)
        transporter_btns_layout.addWidget(self.add_transporter_btn)
        transporter_btns_layout.addWidget(self.edit_transporter_btn)
        transporter_btns_layout.addWidget(self.delete_transporter_btn)
        transporter_btns_layout.addStretch()
        transporters_group_layout.addLayout(transporter_btns_layout)
        main_layout.addWidget(transporters_group)

        # --- Freight Forwarders Group ---
        forwarders_group = QGroupBox(self.tr("Manage Freight Forwarders"))
        forwarders_group_layout = QVBoxLayout(forwarders_group) # Layout for content within the group
        forwarders_group_layout.setSpacing(10)

        self.forwarders_table = QTableWidget()
        self.forwarders_table.setColumnCount(6)
        self.forwarders_table.setHorizontalHeaderLabels([
            self.tr("ID"), self.tr("Name"), self.tr("Contact Person"),
            self.tr("Phone"), self.tr("Email"), self.tr("Services Offered")
        ])
        self.forwarders_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.forwarders_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.forwarders_table.horizontalHeader().setStretchLastSection(True)
        self.forwarders_table.hideColumn(0) # Hide ID column
        self.forwarders_table.itemSelectionChanged.connect(self._update_forwarder_button_states)
        forwarders_group_layout.addWidget(self.forwarders_table)

        forwarder_btns_layout = QHBoxLayout()
        self.add_forwarder_btn = QPushButton(self.tr("➕ Add Freight Forwarder"))
        self.add_forwarder_btn.clicked.connect(self._handle_add_forwarder)
        self.edit_forwarder_btn = QPushButton(self.tr("✏️ Edit Selected"))
        self.edit_forwarder_btn.setEnabled(False)
        self.edit_forwarder_btn.clicked.connect(self._handle_edit_forwarder)
        self.delete_forwarder_btn = QPushButton(self.tr("🗑️ Delete Selected"))
        self.delete_forwarder_btn.setObjectName("dangerButton")
        self.delete_forwarder_btn.setEnabled(False)
        self.delete_forwarder_btn.clicked.connect(self._handle_delete_forwarder)
        forwarder_btns_layout.addWidget(self.add_forwarder_btn)
        forwarder_btns_layout.addWidget(self.edit_forwarder_btn)
        forwarder_btns_layout.addWidget(self.delete_forwarder_btn)
        forwarder_btns_layout.addStretch()
        forwarders_group_layout.addLayout(forwarder_btns_layout)
        main_layout.addWidget(forwarders_group)

        main_layout.addStretch(1) # Push groups to the top
        self.tabs_widget.addTab(tab_widget, self.tr("Logistics"))

    def _setup_document_templates_tab(self):
        tab_widget = QWidget()
        main_layout = QVBoxLayout(tab_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # --- Template Directories Group ---
        template_dirs_group = QGroupBox(self.tr("Template Storage Locations"))
        template_dirs_form_layout = QFormLayout(template_dirs_group)
        template_dirs_form_layout.setSpacing(10)

        self.templates_dir_input = QLineEdit()
        self.templates_dir_input.setPlaceholderText(self.tr("Path to your global templates directory"))
        templates_browse_btn = QPushButton(self.tr("📁 Browse..."))
        templates_browse_btn.clicked.connect(lambda: self._browse_directory(self.templates_dir_input, self.tr("Select Global Templates Directory")))
        templates_dir_layout = QHBoxLayout()
        templates_dir_layout.addWidget(self.templates_dir_input)
        templates_dir_layout.addWidget(templates_browse_btn)
        template_dirs_form_layout.addRow(self.tr("Global Templates Directory:"), templates_dir_layout)

        self.clients_dir_input = QLineEdit() # Assuming this is for client-specific template overrides or client data
        self.clients_dir_input.setPlaceholderText(self.tr("Path to directory for client-specific data/templates"))
        clients_browse_btn = QPushButton(self.tr("📁 Browse..."))
        clients_browse_btn.clicked.connect(lambda: self._browse_directory(self.clients_dir_input, self.tr("Select Client Data Directory")))
        clients_dir_layout = QHBoxLayout()
        clients_dir_layout.addWidget(self.clients_dir_input)
        clients_dir_layout.addWidget(clients_browse_btn)
        template_dirs_form_layout.addRow(self.tr("Client Data/Templates Directory:"), clients_dir_layout)
        main_layout.addWidget(template_dirs_group)

        # --- Template Management Group ---
        template_mgmt_group = QGroupBox(self.tr("Global Template Administration"))
        template_mgmt_layout = QVBoxLayout(template_mgmt_group)
        template_mgmt_layout.setSpacing(10)

        manage_templates_btn = QPushButton(self.tr("🛠️ Open Global Template Manager"))
        manage_templates_btn.setToolTip(self.tr("Manage categories, languages, and extensions for all templates."))
        manage_templates_btn.clicked.connect(self._open_template_manager_dialog)
        template_mgmt_layout.addWidget(manage_templates_btn)
        main_layout.addWidget(template_mgmt_group)

        # --- Template Visibility Group ---
        template_visibility_group = QGroupBox(self.tr("Template Visibility & Selection"))
        template_visibility_layout = QVBoxLayout(template_visibility_group)
        template_visibility_layout.setSpacing(10)

        visibility_description = QLabel(self.tr("Control which templates are available for selection in document generation dialogs."))
        visibility_description.setWordWrap(True)
        template_visibility_layout.addWidget(visibility_description)

        self.template_visibility_table = QTableWidget()
        self.template_visibility_table.setColumnCount(5)
        self.template_visibility_table.setHorizontalHeaderLabels([
            self.tr("Template Name"), self.tr("Description"), self.tr("Type"),
            self.tr("Language"), self.tr("Visible (Editable)")
        ])
        self.template_visibility_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # EditTriggers will be handled by the checkbox delegate or cell widget
        self.template_visibility_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.template_visibility_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.template_visibility_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        template_visibility_layout.addWidget(self.template_visibility_table)

        visibility_btns_layout = QHBoxLayout()
        self.refresh_template_visibility_btn = QPushButton(self.tr("🔄 Refresh List"))
        self.refresh_template_visibility_btn.clicked.connect(self._load_template_visibility_data)
        visibility_btns_layout.addWidget(self.refresh_template_visibility_btn)
        visibility_btns_layout.addStretch()
        self.save_template_visibility_btn = QPushButton(self.tr("💾 Save Visibility Changes"))
        self.save_template_visibility_btn.clicked.connect(self._save_template_visibility_data)
        visibility_btns_layout.addWidget(self.save_template_visibility_btn)
        template_visibility_layout.addLayout(visibility_btns_layout)
        main_layout.addWidget(template_visibility_group)

        main_layout.addStretch(1)
        self.tabs_widget.addTab(tab_widget, self.tr("Document Templates"))

    def _setup_document_customization_tab(self):
        tab_widget = QWidget()
        main_layout = QVBoxLayout(tab_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        footer_notes_group = QGroupBox(self.tr("Default Document Footer Notes"))
        footer_notes_form_layout = QFormLayout(footer_notes_group)
        footer_notes_form_layout.setSpacing(10)

        self.footer_notes_edits = {} # Store QTextEdits by lang code
        # Assuming SUPPORTED_LANGUAGES is available or define it here
        # For now, let's use a predefined list similar to other parts of the app
        supported_langs_for_footers = [
            ("French", "fr"), ("English", "en"), ("Arabic", "ar"),
            ("Turkish", "tr"), ("Portuguese", "pt"), ("Russian", "ru")
        ]

        for lang_name, lang_code in supported_langs_for_footers:
            label = QLabel(self.tr(f"Default Footer ({lang_name} - {lang_code}):"))
            text_edit = QTextEdit()
            text_edit.setFixedHeight(60) # Small height for footer notes
            text_edit.setPlaceholderText(self.tr(f"Enter default footer for {lang_name} documents..."))
            footer_notes_form_layout.addRow(label, text_edit)
            self.footer_notes_edits[lang_code] = text_edit

        main_layout.addWidget(footer_notes_group)
        main_layout.addStretch(1)
        self.tabs_widget.addTab(tab_widget, self.tr("Document Customization"))

    def _get_user_menu_config_key(self):
        """Generates the DB setting key for the current user's menu configuration."""
        return f"user_menu_config_{self.current_user_id}"

    def _setup_menu_customization_tab(self):
        tab_widget = QWidget()
        main_layout = QVBoxLayout(tab_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        menu_custom_group = QGroupBox(self.tr("Customize 'Modules' Menu"))
        group_layout = QVBoxLayout(menu_custom_group)
        group_layout.setSpacing(10)

        instructions_label = QLabel(self.tr(
            "Check modules to include them in the 'Modules' menu. "
            "Use 'Move Up' and 'Move Down' to change their order. "
            "Unchecked modules will not appear in the menu, regardless of permissions. "
            "Permissions will still apply (an unchecked but permitted module won't show; "
            "a checked but non-permitted module also won't show)."
        ))
        instructions_label.setWordWrap(True)
        group_layout.addWidget(instructions_label)

        self.menu_modules_list_widget = QListWidget()
        self.menu_modules_list_widget.setDragDropMode(QAbstractItemView.InternalMove) # Allow drag-drop reordering
        group_layout.addWidget(self.menu_modules_list_widget)

        # Buttons for reordering (alternative or in addition to drag-drop)
        buttons_hbox = QHBoxLayout()
        self.move_module_up_btn = QPushButton(self.tr("🔼 Move Up"))
        self.move_module_up_btn.clicked.connect(self._move_menu_module_up)
        buttons_hbox.addWidget(self.move_module_up_btn)

        self.move_module_down_btn = QPushButton(self.tr("🔽 Move Down"))
        self.move_module_down_btn.clicked.connect(self._move_menu_module_down)
        buttons_hbox.addWidget(self.move_module_down_btn)

        buttons_hbox.addStretch()

        self.reset_menu_config_btn = QPushButton(self.tr("🔄 Reset Menu to Default"))
        self.reset_menu_config_btn.clicked.connect(self._reset_menu_config_to_default)
        buttons_hbox.addWidget(self.reset_menu_config_btn)
        group_layout.addLayout(buttons_hbox)

        main_layout.addWidget(menu_custom_group)
        main_layout.addStretch(1)
        self.tabs_widget.addTab(tab_widget, self.tr("Menu Customization"))

    def _populate_menu_modules_list(self, config=None):
        self.menu_modules_list_widget.clear()

        # CONFIGURABLE_MODULES is a list of dicts: {'key': db_key, 'name': internal_name, 'action_attr': action_name, 'widget_attr': widget_name}
        # We need the 'name' for identification and 'label_text' (from module_config in SettingsPage) or tr(internal_name) for display.

        # Create a mapping from module 'name' to its translatable label if available in self.module_config
        # This might be slightly redundant if CONFIGURABLE_MODULES already had a translatable label.
        # For now, module_config in SettingsPage is for module *activation*, not menu items directly.
        # Let's use the 'name' from CONFIGURABLE_MODULES and translate it if needed, or use a predefined mapping.

        module_display_names = {
            mod_info['name']: self.tr(mod_info['name'].replace('_', ' ').title())
            for mod_info in CONFIGURABLE_MODULES
        }
        # Override with more specific translations if available from self.module_config (which has 'label_text')
        # This assumes self.module_config's 'key' (like 'module_project_management_enabled') can be mapped to CONFIGURABLE_MODULES 'name'.
        # This mapping is a bit indirect. A direct `label` in CONFIGURABLE_MODULES would be cleaner.
        # For now, using module_display_names as defined above.

        default_order = [mod['name'] for mod in CONFIGURABLE_MODULES]
        default_visibility = {mod['name']: True for mod in CONFIGURABLE_MODULES}

        if config is None: # No saved config, use defaults
            current_order = default_order
            visibility_map = default_visibility
        else:
            current_order = config.get('order', default_order)
            visibility_map = config.get('visibility', default_visibility)
            # Ensure all known modules are present in current_order, add missing ones at the end
            for mod_name in default_order:
                if mod_name not in current_order:
                    current_order.append(mod_name)

        for module_name in current_order:
            module_info = next((m for m in CONFIGURABLE_MODULES if m['name'] == module_name), None)
            if not module_info:
                continue # Module from saved config no longer exists

            display_text = module_display_names.get(module_name, module_name)
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, module_name) # Store internal name
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if visibility_map.get(module_name, True) else Qt.Unchecked)
            self.menu_modules_list_widget.addItem(item)

    def _move_menu_module_up(self):
        current_row = self.menu_modules_list_widget.currentRow()
        if current_row > 0:
            item = self.menu_modules_list_widget.takeItem(current_row)
            self.menu_modules_list_widget.insertItem(current_row - 1, item)
            self.menu_modules_list_widget.setCurrentRow(current_row - 1)

    def _move_menu_module_down(self):
        current_row = self.menu_modules_list_widget.currentRow()
        if current_row < self.menu_modules_list_widget.count() - 1 and current_row != -1:
            item = self.menu_modules_list_widget.takeItem(current_row)
            self.menu_modules_list_widget.insertItem(current_row + 1, item)
            self.menu_modules_list_widget.setCurrentRow(current_row + 1)

    def _reset_menu_config_to_default(self):
        reply = QMessageBox.question(self, self.tr("Confirm Reset"),
                                     self.tr("Are you sure you want to reset the menu customization to default?"),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self._populate_menu_modules_list(config=None) # Pass None to load defaults
            # The actual save will happen when "Save All Settings" is clicked.
            QMessageBox.information(self, self.tr("Menu Reset"),
                                    self.tr("Menu customization has been reset to default. Click 'Save All Settings' to apply."))


    def _browse_download_monitor_path(self):
        start_dir = self.download_monitor_path_input.text()
        if not os.path.isdir(start_dir):
            # Default to user's standard Downloads directory if path is invalid or empty
            start_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
            if not os.path.isdir(start_dir): # Fallback if 'Downloads' doesn't exist
                start_dir = os.path.expanduser('~')


        dir_path = QFileDialog.getExistingDirectory(
            self,
            self.tr("Select Folder to Monitor for Downloads"),
            start_dir # Use a sensible starting directory
        )
        if dir_path:
            self.download_monitor_path_input.setText(dir_path)

    # Note: _setup_transporters_tab and _setup_freight_forwarders_tab are now part of _setup_logistics_tab
    # Their helper methods (_load_transporters_table, _handle_add_transporter, etc.) remain the same.
    # Similarly for _setup_data_management_tab, _setup_download_monitor_tab, _setup_backup_tab,
    # _setup_template_visibility_tab, _setup_global_template_management_tab
    # which are now integrated into the new composite tabs.

    def _load_transporters_table(self):
        if not db_manager:
            QMessageBox.warning(self, self.tr("Database Error"), self.tr("Database connection is not available. Cannot load transporters."))
            return
        self.transporters_table.setRowCount(0)
        self.transporters_table.setSortingEnabled(False)
        try:
            transporters = db_manager.get_all_transporters() or []
            for row_idx, t_data in enumerate(transporters):
                self.transporters_table.insertRow(row_idx)
                id_item = QTableWidgetItem(str(t_data.get('transporter_id')))
                self.transporters_table.setItem(row_idx, 0, id_item)
                name_item = QTableWidgetItem(t_data.get('name'))
                name_item.setData(Qt.UserRole, t_data.get('transporter_id'))
                self.transporters_table.setItem(row_idx, 1, name_item)
                self.transporters_table.setItem(row_idx, 2, QTableWidgetItem(t_data.get('contact_person')))
                self.transporters_table.setItem(row_idx, 3, QTableWidgetItem(t_data.get('phone')))
                self.transporters_table.setItem(row_idx, 4, QTableWidgetItem(t_data.get('email')))
                self.transporters_table.setItem(row_idx, 5, QTableWidgetItem(t_data.get('service_area')))
        except Exception as e:
            QMessageBox.warning(self, self.tr("DB Error"), self.tr("Error loading transporters: {0}").format(str(e)))
        self.transporters_table.setSortingEnabled(True)
        self._update_transporter_button_states()

    def _handle_add_transporter(self):
        if not db_manager: return
        dialog = TransporterDialog(parent=self) # db_manager is used inside the dialog
        if dialog.exec_() == QDialog.Accepted:
            self._load_transporters_table()

    def _handle_edit_transporter(self):
        if not db_manager: return
        selected_items = self.transporters_table.selectedItems()
        if not selected_items: return
        transporter_id = self.transporters_table.item(selected_items[0].row(), 0).text()
        transporter_data = db_manager.get_transporter_by_id(transporter_id)
        if transporter_data:
            dialog = TransporterDialog(transporter_data=transporter_data, parent=self)
            if dialog.exec_() == QDialog.Accepted:
                self._load_transporters_table()
        else:
            QMessageBox.warning(self, self.tr("Error"), self.tr("Transporter not found."))

    def _handle_delete_transporter(self):
        if not db_manager: return
        selected_items = self.transporters_table.selectedItems()
        if not selected_items: return
        transporter_id = self.transporters_table.item(selected_items[0].row(), 0).text()
        transporter_name = self.transporters_table.item(selected_items[0].row(), 1).text()

        reply = QMessageBox.question(self, self.tr("Confirm Delete"),
                                     self.tr("Are you sure you want to delete transporter '{0}'?").format(transporter_name),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if db_manager.delete_transporter(transporter_id):
                QMessageBox.information(self, self.tr("Success"), self.tr("Transporter deleted."))
                self._load_transporters_table()
            else:
                QMessageBox.warning(self, self.tr("DB Error"), self.tr("Could not delete transporter."))

    def _update_transporter_button_states(self):
        has_selection = bool(self.transporters_table.selectedItems())
        self.edit_transporter_btn.setEnabled(has_selection)
        self.delete_transporter_btn.setEnabled(has_selection)

    def _setup_freight_forwarders_tab(self):
        forwarders_tab = QWidget()
        forwarders_layout = QVBoxLayout(forwarders_tab)
        self.forwarders_table = QTableWidget()
        self.forwarders_table.setColumnCount(6) # ID, Name, Contact, Phone, Email, Services Offered
        self.forwarders_table.setHorizontalHeaderLabels([self.tr("ID"), self.tr("Name"), self.tr("Contact Person"), self.tr("Phone"), self.tr("Email"), self.tr("Services Offered")])
        self.forwarders_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.forwarders_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.forwarders_table.horizontalHeader().setStretchLastSection(True)
        self.forwarders_table.hideColumn(0) # Hide ID column
        self.forwarders_table.itemSelectionChanged.connect(self._update_forwarder_button_states)
        forwarders_layout.addWidget(self.forwarders_table)

        btns_layout = QHBoxLayout()
        self.add_forwarder_btn = QPushButton(self.tr("➕ Add Freight Forwarder"))
        self.add_forwarder_btn.clicked.connect(self._handle_add_forwarder)
        self.edit_forwarder_btn = QPushButton(self.tr("✏️ Edit Freight Forwarder")); self.edit_forwarder_btn.setEnabled(False)
        self.edit_forwarder_btn.clicked.connect(self._handle_edit_forwarder)
        self.delete_forwarder_btn = QPushButton(self.tr("🗑️ Delete Freight Forwarder")); self.delete_forwarder_btn.setObjectName("dangerButton"); self.delete_forwarder_btn.setEnabled(False)
        self.delete_forwarder_btn.clicked.connect(self._handle_delete_forwarder)
        btns_layout.addWidget(self.add_forwarder_btn); btns_layout.addWidget(self.edit_forwarder_btn); btns_layout.addWidget(self.delete_forwarder_btn)
        forwarders_layout.addLayout(btns_layout)
        self.tabs_widget.addTab(forwarders_tab, self.tr("Freight Forwarders"))

    def _load_forwarders_table(self):
        if not db_manager: return
        self.forwarders_table.setRowCount(0)
        self.forwarders_table.setSortingEnabled(False)
        try:
            forwarders = db_manager.get_all_freight_forwarders() or []
            for row_idx, f_data in enumerate(forwarders):
                self.forwarders_table.insertRow(row_idx)
                id_item = QTableWidgetItem(str(f_data.get('forwarder_id')))
                self.forwarders_table.setItem(row_idx, 0, id_item)
                name_item = QTableWidgetItem(f_data.get('name'))
                name_item.setData(Qt.UserRole, f_data.get('forwarder_id'))
                self.forwarders_table.setItem(row_idx, 1, name_item)
                self.forwarders_table.setItem(row_idx, 2, QTableWidgetItem(f_data.get('contact_person')))
                self.forwarders_table.setItem(row_idx, 3, QTableWidgetItem(f_data.get('phone')))
                self.forwarders_table.setItem(row_idx, 4, QTableWidgetItem(f_data.get('email')))
                self.forwarders_table.setItem(row_idx, 5, QTableWidgetItem(f_data.get('services_offered')))
        except Exception as e:
            QMessageBox.warning(self, self.tr("DB Error"), self.tr("Error loading freight forwarders: {0}").format(str(e)))
        self.forwarders_table.setSortingEnabled(True)
        self._update_forwarder_button_states()

    def _handle_add_forwarder(self):
        if not db_manager: return
        dialog = FreightForwarderDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self._load_forwarders_table()

    def _handle_edit_forwarder(self):
        if not db_manager: return
        selected_items = self.forwarders_table.selectedItems()
        if not selected_items: return
        forwarder_id = self.forwarders_table.item(selected_items[0].row(), 0).text()
        forwarder_data = db_manager.get_freight_forwarder_by_id(forwarder_id)
        if forwarder_data:
            dialog = FreightForwarderDialog(forwarder_data=forwarder_data, parent=self)
            if dialog.exec_() == QDialog.Accepted:
                self._load_forwarders_table()
        else:
            QMessageBox.warning(self, self.tr("Error"), self.tr("Freight Forwarder not found."))

    def _handle_delete_forwarder(self):
        if not db_manager: return
        selected_items = self.forwarders_table.selectedItems()
        if not selected_items: return
        forwarder_id = self.forwarders_table.item(selected_items[0].row(), 0).text()
        forwarder_name = self.forwarders_table.item(selected_items[0].row(), 1).text()

        reply = QMessageBox.question(self, self.tr("Confirm Delete"),
                                     self.tr("Are you sure you want to delete freight forwarder '{0}'?").format(forwarder_name),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if db_manager.delete_freight_forwarder(forwarder_id):
                QMessageBox.information(self, self.tr("Success"), self.tr("Freight Forwarder deleted."))
                self._load_forwarders_table()
            else:
                QMessageBox.warning(self, self.tr("DB Error"), self.tr("Could not delete freight forwarder."))

    def _update_forwarder_button_states(self):
        has_selection = bool(self.forwarders_table.selectedItems())
        self.edit_forwarder_btn.setEnabled(has_selection)
        self.delete_forwarder_btn.setEnabled(has_selection)

    def _setup_data_management_tab(self):
        data_management_tab_widget = QWidget()
        layout = QVBoxLayout(data_management_tab_widget)

        self.import_products_btn = QPushButton(self.tr("Import Products"))
        self.import_products_btn.clicked.connect(self._handle_import_products)
        layout.addWidget(self.import_products_btn)

        self.export_products_btn = QPushButton(self.tr("Export Products"))
        self.export_products_btn.clicked.connect(self._handle_export_products)
        layout.addWidget(self.export_products_btn)

        instructions_label = QLabel(self.tr("Instructions for import/export format and ChatGPT prompt will be displayed here."))
        instructions_label.setWordWrap(True)
        instructions_label.setStyleSheet("font-style: italic; color: grey;")
        layout.addWidget(instructions_label)

        layout.addStretch(1) # Add stretch to push elements to the top
        data_management_tab_widget.setLayout(layout)
        self.tabs_widget.addTab(data_management_tab_widget, self.tr("Data Management"))

    def _handle_export_products(self):
        if not products_crud_instance:
            QMessageBox.critical(self, self.tr("Error"), self.tr("Product data module is not available. Cannot export products."))
            return

        try:
            products = products_crud_instance.get_all_products(include_deleted=True, limit=None, offset=0)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Database Error"), self.tr("Failed to retrieve products from the database: {0}").format(str(e)))
            return

        if not products:
            QMessageBox.information(self, self.tr("No Products"), self.tr("There are no products to export."))
            return

        # Define default filename and path
        default_filename = "products_export.csv"
        # Suggest user's Documents directory or home directory as a default
        default_dir = os.path.join(os.path.expanduser('~'), 'Documents')
        if not os.path.exists(default_dir):
            default_dir = os.path.expanduser('~')
        suggested_filepath = os.path.join(default_dir, default_filename)

        # Open QFileDialog
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog # Optional: use Qt's dialog instead of native
        filePath, _ = QFileDialog.getSaveFileName(self,
                                                  self.tr("Save Product Export"),
                                                  suggested_filepath, # Default path and filename
                                                  self.tr("CSV Files (*.csv);;All Files (*)"),
                                                  options=options)

        if filePath:
            # Ensure the filename ends with .csv if the user didn't specify
            if not filePath.lower().endswith(".csv"):
                filePath += ".csv"

            header = ["product_id", "product_name", "product_code", "description", "category",
                      "language_code", "base_unit_price", "unit_of_measure", "weight",
                      "dimensions", "is_active", "is_deleted"]
            try:
                with open(filePath, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=header, extrasaction='ignore')
                    writer.writeheader()
                    for product in products:
                        # Ensure all fields are present, defaulting to empty string or appropriate representation
                        row_data = {field: getattr(product, field, '') for field in header}

                        # Handle complex types like 'dimensions' if it's an object/dict
                        if isinstance(row_data['dimensions'], (dict, list)):
                             row_data['dimensions'] = str(row_data['dimensions']) # Simple string representation

                        # Convert boolean values to string explicitly if needed by some CSV readers
                        row_data['is_active'] = str(row_data['is_active'])
                        row_data['is_deleted'] = str(row_data['is_deleted'])

                        writer.writerow(row_data)
                QMessageBox.information(self, self.tr("Export Successful"),
                                        self.tr("Products exported successfully to: {0}").format(filePath))
            except IOError as e:
                QMessageBox.critical(self, self.tr("Export Error"),
                                     self.tr("Failed to write to file: {0}\nError: {1}").format(filePath, str(e)))
            except Exception as e:
                QMessageBox.critical(self, self.tr("Export Error"),
                                     self.tr("An unexpected error occurred during export: {0}").format(str(e)))

    def _handle_import_products(self):
        if not products_crud_instance:
            QMessageBox.critical(self, self.tr("Error"), self.tr("Product data module is not available. Cannot import products."))
            return

        # Show instructions dialog first
        instructions_dialog = ImportInstructionsDialog(self)
        if not instructions_dialog.exec_() == QDialog.Accepted:
            return # User cancelled the instructions dialog

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        filePath, _ = QFileDialog.getOpenFileName(self,
                                                  self.tr("Open Product CSV File"),
                                                  os.path.expanduser('~'), # Default to home directory
                                                  self.tr("CSV Files (*.csv);;All Files (*)"),
                                                  options=options)

        if not filePath:
            return # User cancelled

        expected_headers = ["product_id", "product_name", "product_code", "description", "category",
                            "language_code", "base_unit_price", "unit_of_measure", "weight",
                            "dimensions", "is_active", "is_deleted"]

        successful_imports = 0
        failed_imports = 0
        error_details = []

        try:
            with open(filePath, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                # Validate header
                if not reader.fieldnames or not all(header in reader.fieldnames for header in ["product_name", "product_code", "base_unit_price"]): # Check for essential headers
                    QMessageBox.critical(self, self.tr("Invalid CSV Format"), self.tr("The CSV file is missing one or more required headers (product_name, product_code, base_unit_price) or is not a valid CSV."))
                    return

                for i, row in enumerate(reader):
                    line_num = i + 2 # Account for header and 0-based index
                    product_data = {}

                    # Required fields
                    product_name = row.get("product_name", "").strip()
                    product_code = row.get("product_code", "").strip()
                    base_unit_price_str = row.get("base_unit_price", "").strip()

                    if not product_name:
                        error_details.append(self.tr("Line {0}: Missing required field 'product_name'.").format(line_num))
                        failed_imports += 1
                        continue
                    if not product_code:
                        error_details.append(self.tr("Line {0}: Missing required field 'product_code' for product '{1}'.").format(line_num, product_name))
                        failed_imports += 1
                        continue
                    if not base_unit_price_str:
                        error_details.append(self.tr("Line {0}: Missing required field 'base_unit_price' for product '{1}'.").format(line_num, product_name))
                        failed_imports += 1
                        continue

                    try:
                        product_data["base_unit_price"] = float(base_unit_price_str)
                    except ValueError:
                        error_details.append(self.tr("Line {0}: Invalid format for 'base_unit_price' (must be a number) for product '{1}'.").format(line_num, product_name))
                        failed_imports += 1
                        continue

                    product_data["product_name"] = product_name
                    product_data["product_code"] = product_code

                    # Optional fields
                    product_data["description"] = row.get("description", "").strip()
                    product_data["category"] = row.get("category", "").strip()
                    product_data["language_code"] = row.get("language_code", "fr").strip() or "fr" # Default to 'fr'
                    product_data["unit_of_measure"] = row.get("unit_of_measure", "").strip()
                    product_data["weight"] = row.get("weight", "").strip() # Assuming weight is stored as string or number, CRUD should handle
                    product_data["dimensions"] = row.get("dimensions", "").strip() # Assuming dimensions stored as string, CRUD should handle

                    is_active_str = row.get("is_active", "True").strip().lower()
                    product_data["is_active"] = is_active_str in ['true', '1', 'yes']

                    is_deleted_str = row.get("is_deleted", "False").strip().lower()
                    product_data["is_deleted"] = is_deleted_str in ['true', '1', 'yes'] # Interpreting 'is_deleted' from CSV

                    try:
                        products_crud_instance.add_product(product_data)
                        successful_imports += 1
                    except Exception as e:
                        error_details.append(self.tr("Line {0}: Error importing product '{1}': {2}").format(line_num, product_name, str(e)))
                        failed_imports += 1

        except FileNotFoundError:
            QMessageBox.critical(self, self.tr("Error"), self.tr("The selected file was not found: {0}").format(filePath))
            return
        except Exception as e: # Catch other CSV parsing errors or unexpected issues
            QMessageBox.critical(self, self.tr("Import Error"), self.tr("An unexpected error occurred during import: {0}").format(str(e)))
            return

        # Show summary
        summary_message = self.tr("Import complete.\nSuccessfully imported: {0} products.\nFailed to import: {1} products.").format(successful_imports, failed_imports)
        if error_details:
            detailed_errors = "\n\n" + self.tr("Error Details (first 5 shown):") + "\n" + "\n".join(error_details[:5])
            if len(error_details) > 5:
                detailed_errors += "\n" + self.tr("...and {0} more errors.").format(len(error_details) - 5)
            # For very long error lists, consider writing to a log file instead of stuffing into QMessageBox
            if len(summary_message + detailed_errors) > 1000: # Rough limit for readability
                 detailed_errors = "\n\n" + self.tr("Numerous errors occurred. Please check data integrity. First few errors:\n") + "\n".join(error_details[:3])
            summary_message += detailed_errors

        if failed_imports > 0:
            QMessageBox.warning(self, self.tr("Import Partially Successful"), summary_message)
        else:
            QMessageBox.information(self, self.tr("Import Successful"), summary_message)


    def _load_general_tab_data(self):
        # Loads settings for the "General" tab (Interface & Behavior groups)
        current_lang_code = self.main_config.get("language", "fr")
        code_to_display_text = {code: display for display, code in self.lang_display_to_code.items()}
        current_display_text = code_to_display_text.get(current_lang_code)
        if current_display_text:
            self.interface_lang_combo.setCurrentText(current_display_text)
        else: # Fallback if language code in config is invalid
            self.interface_lang_combo.setCurrentText(code_to_display_text.get("fr", list(self.lang_display_to_code.keys())[0]))

        self.session_timeout_spinbox.setValue(self.main_config.get("session_timeout_minutes", 259200)) # Default was 259200
        self.reminder_days_spinbox.setValue(self.main_config.get("default_reminder_days", 30))
        self.google_maps_url_input.setText(self.main_config.get("google_maps_review_url", "https://maps.google.com/?cid=YOUR_CID_HERE"))
        self.show_setup_prompt_checkbox.setChecked(self.main_config.get("show_initial_setup_on_startup", False))

        # Load the new license check setting
        if db_manager:
            check_license_str = db_manager.get_setting('check_license_on_startup', default='True')
            self.check_license_on_startup_checkbox.setChecked(check_license_str.lower() == 'true')

            # Load theme setting
            theme_value = db_manager.get_setting('theme', default='Light')
            self.theme_combo.setCurrentText(theme_value)

            # Load geographic scope
            geo_scope_value = db_manager.get_setting('geographic_scope', default='international')
            for display_text, value in self.geo_scope_options.items():
                if value == geo_scope_value:
                    self.geo_scope_combo.setCurrentText(display_text)
                    break
        else:
            self.check_license_on_startup_checkbox.setChecked(True) # Default to True if db_manager is not available
            print("WARNING: db_manager not available, 'check_license_on_startup' defaulted to True for UI.")
        print("General tab settings loaded.")

    def _load_connectivity_tab_data(self):
        # Loads Email (SMTP) settings
        self.smtp_server_input.setText(self.main_config.get("smtp_server", ""))
        self.smtp_port_spinbox.setValue(self.main_config.get("smtp_port", 587))
        self.smtp_user_input.setText(self.main_config.get("smtp_user", ""))
        self.smtp_pass_input.setText(self.main_config.get("smtp_password", ""))
        print("Connectivity (Email) settings loaded.")

    def _load_data_backup_tab_data(self):
        # Database path & type
        self.db_path_input.setText(self.main_config.get("database_path", os.path.join(os.getcwd(), "app_data.db")))
        current_db_type = self.main_config.get('database_type', 'sqlite')
        db_type_index = self.db_type_combo.findData(current_db_type)
        if db_type_index != -1:
            self.db_type_combo.setCurrentIndex(db_type_index)
        else:
            sqlite_index = self.db_type_combo.findData('sqlite') # Fallback
            if sqlite_index != -1: self.db_type_combo.setCurrentIndex(sqlite_index)

        # Download Monitoring
        self.main_config.setdefault("download_monitor_enabled", False) # Ensure key exists
        self.main_config.setdefault("download_monitor_path", os.path.join(os.path.expanduser('~'), 'Downloads')) # Ensure key exists
        self.download_monitor_enabled_checkbox.setChecked(self.main_config.get("download_monitor_enabled", False))
        default_download_path = os.path.join(os.path.expanduser('~'), 'Downloads')
        self.download_monitor_path_input.setText(self.main_config.get("download_monitor_path", default_download_path))

        # Backup Settings
        self.backup_server_address_input.setText(self.main_config.get("backup_server_address", ""))
        self.backup_port_input.setText(self.main_config.get("backup_port", "")) # Port is QLineEdit
        self.backup_username_input.setText(self.main_config.get("backup_username", ""))
        self.backup_password_input.setText(self.main_config.get("backup_password", ""))

        # Load PostgreSQL specific settings
        self.pg_host_input.setText(self.main_config.get("postgresql_host", "localhost"))
        self.pg_port_spinbox.setValue(self.main_config.get("postgresql_port", 5432))
        self.pg_user_input.setText(self.main_config.get("postgresql_user", ""))
        self.pg_password_input.setText(self.main_config.get("postgresql_password", ""))
        self.pg_dbname_input.setText(self.main_config.get("postgresql_dbname", ""))

        # Load PostgreSQL SSL settings
        self.pg_ssl_mode_combo.setCurrentText(self.main_config.get("postgresql_ssl_mode", "disable"))
        self.pg_ssl_rootcert_input.setText(self.main_config.get("postgresql_ssl_rootcert", ""))
        self.pg_ssl_clientcert_input.setText(self.main_config.get("postgresql_ssl_clientcert", ""))
        self.pg_ssl_clientkey_input.setText(self.main_config.get("postgresql_ssl_clientkey", ""))


        self._toggle_pg_settings_visibility() # Ensure correct visibility on load
        print("Data & Backup tab settings loaded.")

    # _load_connectivity_tab_data is no longer needed as SMTP is managed by its own table.
    # def _load_connectivity_tab_data(self):
    #     # Loads Email (SMTP) settings
    #     self.smtp_server_input.setText(self.main_config.get("smtp_server", ""))
    #     self.smtp_port_spinbox.setValue(self.main_config.get("smtp_port", 587))
    #     self.smtp_user_input.setText(self.main_config.get("smtp_user", ""))
    #     self.smtp_pass_input.setText(self.main_config.get("smtp_password", ""))
    #     print("Connectivity (Email) settings loaded.")

    def _toggle_pg_settings_visibility(self):
        selected_db_type = self.db_type_combo.currentData()
        is_pg_selected = selected_db_type == "postgresql"
        self.pg_settings_group.setVisible(is_pg_selected)
        # Adjust dialog size if necessary, though often Qt handles this
        # if self.pg_settings_group.isVisible():
        #     self.parentWidget().parentWidget().adjustSize() # May need to find the top-level dialog/window

    def _load_document_templates_tab_data(self):
        self.templates_dir_input.setText(self.main_config.get("templates_dir", ""))
        self.clients_dir_input.setText(self.main_config.get("clients_dir", "")) # Path for client-specific data/templates
        # Template visibility data is loaded via its own mechanism (_load_template_visibility_data)
        self._load_template_visibility_data()
        print("Document Templates tab settings loaded (excluding visibility table which has its own load).")


    def _browse_directory(self, line_edit_target, dialog_title):
        start_dir = line_edit_target.text()
        if not os.path.isdir(start_dir): start_dir = os.path.expanduser('~') # Default to home if invalid
        dir_path = QFileDialog.getExistingDirectory(self, dialog_title, start_dir)
        if dir_path: line_edit_target.setText(dir_path)

    def _browse_db_file(self, line_edit_target):
        current_path = line_edit_target.text()
        start_dir = os.path.dirname(current_path) if current_path and os.path.exists(os.path.dirname(current_path)) else os.path.expanduser('~')
        file_path, _ = QFileDialog.getOpenFileName(self, self.tr("Select Database File"), start_dir, self.tr("Database Files (*.db *.sqlite *.sqlite3);;All Files (*.*)"))
        if file_path: line_edit_target.setText(file_path)

    def _browse_file(self, line_edit_target, dialog_title, file_filter="All Files (*.*)"):
        current_path = line_edit_target.text()
        start_dir = os.path.dirname(current_path) if current_path and os.path.exists(os.path.dirname(current_path)) else os.path.expanduser('~')
        file_path, _ = QFileDialog.getOpenFileName(self, dialog_title, start_dir, file_filter)
        if file_path: line_edit_target.setText(file_path)

    def get_general_settings_data(self):
        # Collects data from the "General" tab
        selected_lang_display_text = self.interface_lang_combo.currentText()
        language_code = self.lang_display_to_code.get(selected_lang_display_text, "fr")
        return {
            "language": language_code,
            "default_reminder_days": self.reminder_days_spinbox.value(),
            "session_timeout_minutes": self.session_timeout_spinbox.value(),
            "google_maps_review_url": self.google_maps_url_input.text().strip(),
            "show_initial_setup_on_startup": self.show_setup_prompt_checkbox.isChecked(),
        }

    # get_connectivity_settings_data is no longer needed for main_config saving.
    # def get_connectivity_settings_data(self):
    #     # Collects Email (SMTP) settings
    #     return {
    #         "smtp_server": self.smtp_server_input.text().strip(),
    #         "smtp_port": self.smtp_port_spinbox.value(),
    #         "smtp_user": self.smtp_user_input.text().strip(),
    #         "smtp_password": self.smtp_pass_input.text() # Password not stripped
    #     }

    def get_data_backup_settings_data(self):
        # Collects Database, Download Monitor, and Backup server settings
        selected_db_type = self.db_type_combo.currentData() if self.db_type_combo.currentIndex() != -1 else "sqlite"
        return {
            "database_path": self.db_path_input.text().strip(),
            "database_type": selected_db_type,
            "download_monitor_enabled": self.download_monitor_enabled_checkbox.isChecked(),
            "download_monitor_path": self.download_monitor_path_input.text().strip(),
            "backup_server_address": self.backup_server_address_input.text().strip(),
            "backup_port": self.backup_port_input.text().strip(), # Port is QLineEdit
            "backup_username": self.backup_username_input.text().strip(),
            "backup_password": self.backup_password_input.text(), # Password not stripped

            # PostgreSQL specific settings
            "postgresql_host": self.pg_host_input.text().strip(),
            "postgresql_port": self.pg_port_spinbox.value(),
            "postgresql_user": self.pg_user_input.text().strip(),
            "postgresql_password": self.pg_password_input.text(), # Password not stripped
            "postgresql_dbname": self.pg_dbname_input.text().strip(),

            # PostgreSQL SSL Settings
            "postgresql_ssl_mode": self.pg_ssl_mode_combo.currentText(),
            "postgresql_ssl_rootcert": self.pg_ssl_rootcert_input.text().strip(),
            "postgresql_ssl_clientcert": self.pg_ssl_clientcert_input.text().strip(),
            "postgresql_ssl_clientkey": self.pg_ssl_clientkey_input.text().strip()

        }

    def get_document_templates_settings_data(self):
        return {
            "templates_dir": self.templates_dir_input.text().strip(),
            "clients_dir": self.clients_dir_input.text().strip(),
            # Template visibility settings are saved via _save_template_visibility_data, not directly into main_config here
        }

    def get_document_customization_settings_data(self):
        settings_data = {}
        if hasattr(self, 'footer_notes_edits'):
            for lang_code, text_edit_widget in self.footer_notes_edits.items():
                setting_key = f"default_document_footer_notes_{lang_code}"
                settings_data[setting_key] = text_edit_widget.toPlainText().strip()
        return settings_data

    def _load_document_customization_tab_data(self):
        if not db_manager:
            print("WARNING: db_manager not available for _load_document_customization_tab_data.")
            return
        if hasattr(self, 'footer_notes_edits'):
            for lang_code, text_edit_widget in self.footer_notes_edits.items():
                setting_key = f"default_document_footer_notes_{lang_code}"
                value = db_manager.get_setting(setting_key, default="")
                text_edit_widget.setPlainText(value)
            print("Document Customization (Footer Notes) settings loaded.")


    def _load_all_settings_from_config(self):
        self._load_general_tab_data()
        # self._load_connectivity_tab_data() # Removed, SMTP handled by _load_smtp_configs_table
        self._load_data_backup_tab_data() # For DB, Download Monitor, Backup
        self._load_document_templates_tab_data() # For Template Dirs
        self._load_document_customization_tab_data() # Load footer notes
        self._load_menu_customization_data() # Load menu customization settings

        self._load_modules_tab_data() # Loads from DB settings table

        # Company & Personnel tab loads its own data internally or via CompanyTabWidget
        # Logistics tab (Transporters, Forwarders) loads data from DB
        if db_manager:
            self._load_transporters_table()
            self._load_forwarders_table()
            self._load_smtp_configs_table() # Load SMTP configs table
        else:
            print("WARNING: db_manager not available. Transporter, Forwarder, and SMTP Config tables will not be loaded.")

        # Security tab is self-contained for now (biometric test page)
        # Template Visibility table has its own load method called by _load_document_templates_tab_data
        # Menu Customization tab data is loaded by _load_menu_customization_data

        # Load data for User Email Assignment section
        self._load_users_for_assignment_combo()
        self._load_available_global_smtp_configs_combo()
        # self._load_assigned_smtp_for_selected_user() # This is triggered by user combo change

        print("SettingsPage: All relevant settings sections reloaded.")

    def _load_menu_customization_data(self):
        if not db_manager:
            print("WARNING: db_manager not available. Cannot load menu customization settings.")
            self._populate_menu_modules_list(config=None) # Populate with defaults
            return

        config_key = self._get_user_menu_config_key()
        try:
            # Assuming get_setting returns None if key not found and default is None
            # And that it can handle JSON deserialization if value is a JSON string.
            # For simplicity, let's assume it returns a dict or None.
            menu_config_raw = db_manager.get_setting(config_key, default=None)
            menu_config = None
            if isinstance(menu_config_raw, str):
                import json
                try:
                    menu_config = json.loads(menu_config_raw)
                except json.JSONDecodeError:
                    logging.error(f"Failed to decode JSON for menu config key {config_key}")
                    menu_config = None # Fallback to default
            elif isinstance(menu_config_raw, dict):
                menu_config = menu_config_raw

            self._populate_menu_modules_list(config=menu_config) # menu_config is now definitely dict or None
            print(f"Menu customization settings loaded for user {self.current_user_id}. Config: {menu_config}")
        except Exception as e: # Catch other issues
            print(f"Error loading menu customization settings for key {config_key}: {e}")
            self._populate_menu_modules_list(config=None) # Populate with defaults on error


    def _save_all_settings(self):
        # Consolidate settings from various getters into main_config
        # self.get_connectivity_settings_data() is removed as SMTP is no longer part of main_config
        settings_collections = [
            self.get_general_settings_data(),
            # self.get_connectivity_settings_data(), # Removed
            self.get_data_backup_settings_data(),
            self.get_document_templates_settings_data(),
            # Document customization settings (footer notes) are saved directly to DB, not main_config
        ]
        for settings_group in settings_collections:
            for key, value in settings_group.items():
                self.main_config[key] = value

        # Save footer notes directly to DB settings
        if db_manager:
            footer_notes_data = self.get_document_customization_settings_data()
            for key, value in footer_notes_data.items():
                db_manager.set_setting(key, value)
            print("Default document footer notes saved to DB.")

            # Save the new license check setting directly to DB
            check_license_value = self.check_license_on_startup_checkbox.isChecked()
            db_manager.set_setting('check_license_on_startup', 'True' if check_license_value else 'False')
            print(f"License check on startup setting saved to DB: {check_license_value}")

            # Save theme setting
            theme_value = self.theme_combo.currentText()
            db_manager.set_setting('theme', theme_value)
            print(f"Theme setting saved to DB: {theme_value}")

            # Save geographic scope
            selected_geo_scope_display_text = self.geo_scope_combo.currentText()
            geo_scope_value = self.geo_scope_options.get(selected_geo_scope_display_text, "international")
            db_manager.set_setting('geographic_scope', geo_scope_value)
            print(f"Geographic scope setting saved to DB: {geo_scope_value}")
        else:
            print("WARNING: db_manager not available. Default footer notes and license check setting not saved to DB.")


        # Save module activation states (persisted in DB, not main_config directly)
        self._save_modules_tab_data() # Handles its own user feedback

        # Save template visibility settings (persisted via API/DB, not main_config)
        self._save_template_visibility_data() # This method handles its own QMessageBox for success/failure

        # CompanyTabWidget might have its own save mechanism, which should be triggered
        # if it manages data that needs saving beyond what's in main_config.
        # Example: if hasattr(self.company_tab_widget_instance, 'save_settings'):
        #              self.company_tab_widget_instance.save_settings()

        # Transporter and Forwarder data are managed via their respective dialogs and DB operations,
        # not typically saved through this main "Save All Settings" button unless there are global configs for them.

        # --- Persist main_config ---
        # This part depends on how main_config is actually saved to a file (e.g., JSON) in the application.
        # For now, we assume self.main_config is updated in memory, and a higher-level process saves it.
        # If SettingsPage were responsible for direct file I/O of main_config:
        # try:
        #     # actual_config_manager.save(self.main_config) # Example call
        #     pass # Assuming save is handled elsewhere or main_config is live
        # except Exception as e:
        #     QMessageBox.critical(self, self.tr("Error Saving Configuration"),
        #                          self.tr("Could not save the main configuration file: {0}").format(str(e)))
        #     return # Prevent further messages if main config save fails
        print("Main configuration dictionary (self.main_config) updated with new settings from UI.")

        # Save menu customization settings to DB
        self._save_menu_customization_data() # Handles its own user feedback

        # Determine if a restart is likely needed
        restart_needed_msg = ""
        # Simple check: if language or db_path changed from initial load, it's a good indicator.
        # This requires storing initial values if we want to be precise, or just always show a generic message.
        # For now, a generic but clear message is good.
        # A more sophisticated approach would be to track changes to specific sensitive settings.

        # Let's make the message more direct about the restart for key items.
        # We can check if specific known restart-requiring settings have changed
        # by comparing current self.main_config values with the ones at the start of the save operation,
        # or by having flags. For now, a general message will be used but enhanced.

        final_message = self.tr("Settings have been saved successfully.")
        potential_restart_message = self.tr(
            "Please note: Changes to settings like Interface Language, Database Path, "
                "Module Activation, or Menu Customization will require an application restart to take full effect."
            ) # Added Menu Customization to message

        # Check if any module activation changed - this is a clear restart trigger
        # This requires comparing current radio button states with initial states loaded into self.main_config
        # or, more simply, if _save_modules_tab_data actually performed any DB updates.
        # For now, the generic message is the most straightforward to implement.

        QMessageBox.information(self, self.tr("Settings Saved"), f"{final_message}\n\n{potential_restart_message}")
        print("All settings processed (main_config updated, modules, visibility, and menu config saved to DB/API).")

    def _save_menu_customization_data(self):
        if not db_manager:
            print("WARNING: db_manager not available. Cannot save menu customization settings.")
            QMessageBox.warning(self, self.tr("Database Error"),
                                self.tr("Database connection is not available. Menu customization settings cannot be saved."))
            return

        ordered_module_names = []
        visibility_map = {}
        for i in range(self.menu_modules_list_widget.count()):
            item = self.menu_modules_list_widget.item(i)
            module_name = item.data(Qt.UserRole)
            ordered_module_names.append(module_name)
            visibility_map[module_name] = item.checkState() == Qt.Checked

        config_to_save = {
            "order": ordered_module_names,
            "visibility": visibility_map
        }

        config_key = self._get_user_menu_config_key()
        try:
            # Assuming db_manager.set_setting can handle storing a dictionary
            # (e.g., by serializing to JSON internally if needed)
            db_manager.set_setting(config_key, config_to_save)
            print(f"Menu customization settings saved for user {self.current_user_id} under key {config_key}. Data: {config_to_save}")
            # No separate QMessageBox here, as it's part of "Save All Settings"
        except Exception as e:
            print(f"Error saving menu customization settings for key {config_key}: {e}")
            QMessageBox.critical(self, self.tr("Menu Save Error"),
                                 self.tr("Could not save menu customization settings: {0}").format(str(e)))


    def _confirm_restore_defaults(self):
        reply = QMessageBox.question(self, self.tr("Confirm Restore Defaults"),
                                     self.tr("Are you sure you want to restore all settings to their default values?\n"
                                             "This action cannot be easily undone and will require an application restart."),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self._restore_default_settings()

    def _restore_default_settings(self):
        # This method needs to:
        # 1. Define the default values for all settings in self.main_config.
        #    This might involve having a separate default_config dictionary.
        # 2. Reset self.main_config to these defaults.
        # 3. Persist self.main_config (e.g., save to JSON file).
        # 4. Reset module activation states in the database to their defaults.
        # 5. Reset template visibility settings to their defaults (if applicable).
        # 6. Reset menu customization settings for the current user to default.
        # 7. Reload the UI to reflect these defaults.
        # 8. Inform the user that a restart is necessary.

        # For demonstration, let's assume a default config structure
        # In a real app, this should come from a reliable source or be hardcoded carefully.
        default_config_values = {
            "language": "fr",
            "session_timeout_minutes": 259200,
            "default_reminder_days": 30,
            "google_maps_review_url": "https://maps.google.com/?cid=YOUR_CID_HERE",
            "show_initial_setup_on_startup": False,
            "smtp_server": "", "smtp_port": 587, "smtp_user": "", "smtp_password": "",
            "database_path": os.path.join(os.getcwd(), "app_data.db"), # Or an app data directory
            "database_type": "sqlite",
            "download_monitor_enabled": False,
            "download_monitor_path": os.path.join(os.path.expanduser('~'), 'Downloads'),
            "backup_server_address": "", "backup_port": "", "backup_username": "", "backup_password": "",
            "templates_dir": os.path.join(self.app_root_dir, "templates"), # Default relative to app
            "clients_dir": os.path.join(self.app_root_dir, "clients_data") # Default relative to app
            # Add other config keys with their defaults
        }

        # Reset main_config
        for key, value in default_config_values.items():
            self.main_config[key] = value
        print("Main config reset to defaults.")

        if db_manager:
            # Reset module activation settings in DB
            try:
                for module_info in self.module_config: # self.module_config from __init__
                    db_manager.set_setting(module_info["key"], 'True') # Default all to enabled
                print("Module activation settings reset to default (all enabled) in DB.")
            except Exception as e:
                print(f"Error resetting module settings in DB: {e}")
                QMessageBox.warning(self, self.tr("Module Reset Error"), self.tr("Could not reset all module activation settings in the database."))

            # Reset menu customization for the current user
            try:
                user_menu_config_key = self._get_user_menu_config_key()
                # Setting to None or an empty dict effectively removes/resets it,
                # so _load_menu_customization_data will use defaults.
                db_manager.set_setting(user_menu_config_key, None)
                print(f"User menu customization for user {self.current_user_id} reset in DB.")
            except Exception as e:
                print(f"Error resetting user menu customization in DB: {e}")
                QMessageBox.warning(self, self.tr("Menu Reset Error"), self.tr("Could not reset menu customization settings in the database."))

        # TODO: Reset template visibility settings (if applicable and stored in DB).

        # Persist the now default self.main_config (simulated)
        print("Default main_config would be persisted here (e.g., to a JSON file).")

        # Reload UI from the new (default) config
        self._load_all_settings_from_config() # This will also call _load_menu_customization_data

        QMessageBox.information(self, self.tr("Defaults Restored"),
                                self.tr("All settings have been restored to their default values. "
                                         "Please restart the application for all changes to take effect."))
        print("Settings restored to defaults. UI reloaded. Restart required.")


    def _setup_modules_tab(self): # This is the old _setup_modules_tab, now _setup_application_modules_tab
        modules_tab_widget = QWidget()
        modules_form_layout = QFormLayout(modules_tab_widget)
        modules_form_layout.setContentsMargins(10, 10, 10, 10)
        modules_form_layout.setSpacing(10)

        for module_info in self.module_config:
            key = module_info["key"]
            label_text = module_info["label_text"]

            module_label = QLabel(label_text)

            radio_group_box = QGroupBox() # Optional, for visual grouping
            radio_layout = QHBoxLayout()

            radio_enabled = QRadioButton(self.tr("Activé"))
            radio_disabled = QRadioButton(self.tr("Désactivé"))

            radio_layout.addWidget(radio_enabled)
            radio_layout.addWidget(radio_disabled)
            radio_group_box.setLayout(radio_layout)

            self.module_radio_buttons[key] = {"enabled": radio_enabled, "disabled": radio_disabled}

            modules_form_layout.addRow(module_label, radio_group_box)

        restart_notice_label = QLabel(self.tr("Un redémarrage de l'application est nécessaire pour que les modifications des modules prennent pleinement effet."))
        restart_notice_label.setWordWrap(True)
        restart_notice_label.setStyleSheet("font-style: italic; color: grey;")
        modules_form_layout.addRow(restart_notice_label)

        modules_tab_widget.setLayout(modules_form_layout)
        self.tabs_widget.addTab(modules_tab_widget, self.tr("Gestion des Modules"))

    def _load_modules_tab_data(self):
        if not db_manager:
            print("WARNING: db_manager not available. Cannot load module settings.")
            return

        for module_info in self.module_config:
            key = module_info["key"]
            # Default to True (enabled) if the setting is not found
            is_enabled_str = db_manager.get_setting(key, default='True')

            # Handle boolean True/False or string 'True'/'False'
            if isinstance(is_enabled_str, bool):
                is_enabled = is_enabled_str
            else:
                is_enabled = is_enabled_str.lower() == 'true'

            if key in self.module_radio_buttons:
                radios = self.module_radio_buttons[key]
                if is_enabled:
                    radios["enabled"].setChecked(True)
                else:
                    radios["disabled"].setChecked(True)
            else:
                print(f"Warning: Radio buttons for module key '{key}' not found.")
        print("Module settings loaded from DB.")

    def _save_modules_tab_data(self):
        if not db_manager:
            print("WARNING: db_manager not available. Cannot save module settings.")
            # Optionally, inform the user with a QMessageBox
            QMessageBox.warning(self, self.tr("Database Error"),
                                self.tr("Database connection is not available. Module settings cannot be saved."))
            return

        for module_info in self.module_config:
            key = module_info["key"]
            if key in self.module_radio_buttons:
                radios = self.module_radio_buttons[key]
                value_to_save = 'True' if radios["enabled"].isChecked() else 'False'
                try:
                    db_manager.set_setting(key, value_to_save)
                except Exception as e:
                    print(f"Error saving module setting {key}: {e}")
                    QMessageBox.critical(self, self.tr("Error Saving Module"),
                                         self.tr("Could not save setting for {0}: {1}").format(module_info["label_text"], str(e)))
            else:
                print(f"Warning: Radio buttons for module key '{key}' not found during save.")
        print("Module settings saved to DB.")

    def _setup_global_template_management_tab(self):
        template_management_tab = QWidget()
        tab_layout = QVBoxLayout(template_management_tab)
        tab_layout.setContentsMargins(10, 10, 10, 10)
        tab_layout.setSpacing(10)

        description_label = QLabel(self.tr("Manage global and client-specific document templates, including categories, languages, and extensions."))
        description_label.setWordWrap(True)
        tab_layout.addWidget(description_label)

        manage_templates_btn = QPushButton(self.tr("🛠️ Open Template Manager"))
        manage_templates_btn.setObjectName("manageTemplatesButton") # For styling
        manage_templates_btn.clicked.connect(self._open_template_manager_dialog)

        button_hbox = QHBoxLayout()
        button_hbox.addWidget(manage_templates_btn)

        tab_layout.addLayout(button_hbox)
        tab_layout.addStretch(1) # Add stretch to push content to the top

        self.tabs_widget.addTab(template_management_tab, self.tr("Template Management"))

    def _open_template_manager_dialog(self):
        # TemplateDialog expects config and parent
        dialog = TemplateDialog(config=self.main_config, parent=self)
        dialog.exec_()

    def _setup_template_visibility_tab(self):
        self.template_visibility_tab = QWidget()
        layout = QVBoxLayout(self.template_visibility_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Table for template visibility
        self.template_visibility_table = QTableWidget()
        self.template_visibility_table.setColumnCount(5)
        self.template_visibility_table.setHorizontalHeaderLabels([
            self.tr("Template Name"), self.tr("Description"), self.tr("Type"),
            self.tr("Language"), self.tr("Visible")
        ])
        self.template_visibility_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.template_visibility_table.setEditTriggers(QAbstractItemView.NoEditTriggers) # Non-editable text
        self.template_visibility_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.template_visibility_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.template_visibility_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents) # Checkbox column

        layout.addWidget(self.template_visibility_table)

        # Buttons layout
        buttons_layout = QHBoxLayout()
        self.refresh_template_visibility_btn = QPushButton(self.tr("🔄 Refresh List"))
        self.refresh_template_visibility_btn.clicked.connect(self._load_template_visibility_data)
        buttons_layout.addWidget(self.refresh_template_visibility_btn)

        buttons_layout.addStretch(1)

        self.save_template_visibility_btn = QPushButton(self.tr("💾 Save Visibility Settings"))
        self.save_template_visibility_btn.clicked.connect(self._save_template_visibility_data)
        buttons_layout.addWidget(self.save_template_visibility_btn)

        layout.addLayout(buttons_layout)
        self.tabs_widget.addTab(self.template_visibility_tab, self.tr("Template Visibility"))

        self._load_template_visibility_data() # Initial load

    def _load_template_visibility_data(self):
        print("SettingsPage: _load_template_visibility_data called (mocked).")
        # Mocked API call to GET /api/templates/visibility_settings
        # In a real scenario, this would use self._call_api or similar
        sample_data = [
            {"template_id": 101, "template_name": "Proforma Invoice (Basic)", "description": "Standard proforma template.", "template_type": "proforma_invoice_html", "language_code": "fr", "is_visible": True},
            {"template_id": 102, "template_name": "Cover Page (Modern)", "description": "Modern style cover page.", "template_type": "html_cover_page", "language_code": "fr", "is_visible": True},
            {"template_id": 103, "template_name": "Sales Quote (EN)", "description": "Standard sales quote in English.", "template_type": "document_word", "language_code": "en", "is_visible": False},
            {"template_id": 104, "template_name": "Product Catalog (Compact)", "description": "Compact product catalog.", "template_type": "document_pdf", "language_code": "fr", "is_visible": True},
            {"template_id": 105, "template_name": self.tr("Affichage Images Produit FR"), "description": self.tr("Affiche les images des produits, leur nom et leur code."), "template_type": "document_html", "language_code": "fr", "is_visible": True},
        ]
        # If using a real API call:
        # try:
        #     response = self._call_api(method="GET", endpoint="/api/templates/visibility_settings")
        #     if response and isinstance(response, list):
        #         sample_data = response
        #     else:
        #         QMessageBox.warning(self, self.tr("Error"), self.tr("Failed to load template visibility data from server.") + (f"\n{response.get('detail')}" if response else ""))
        #         sample_data = [] # Fallback to empty
        # except Exception as e:
        #     QMessageBox.critical(self, self.tr("API Error"), self.tr("Error calling API for template visibility: {0}").format(str(e)))
        #     sample_data = []

        self.template_visibility_table.setRowCount(0) # Clear table
        self.template_visibility_table.setSortingEnabled(False)

        for row_idx, t_data in enumerate(sample_data):
            self.template_visibility_table.insertRow(row_idx)

            name_item = QTableWidgetItem(t_data.get("template_name", "N/A"))
            # Store template_id in the first item's UserRole for easy retrieval
            name_item.setData(Qt.UserRole, t_data.get("template_id"))
            self.template_visibility_table.setItem(row_idx, 0, name_item)

            self.template_visibility_table.setItem(row_idx, 1, QTableWidgetItem(t_data.get("description", "")))
            self.template_visibility_table.setItem(row_idx, 2, QTableWidgetItem(t_data.get("template_type", "")))
            self.template_visibility_table.setItem(row_idx, 3, QTableWidgetItem(t_data.get("language_code", "")))

            # Checkbox for visibility
            checkbox_widget = QWidget() # Container for centering checkbox
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.setContentsMargins(0,0,0,0)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            visibility_checkbox = QCheckBox()
            visibility_checkbox.setChecked(t_data.get("is_visible", True))
            # Store template_id directly on checkbox too for convenience if needed, though UserRole on row is common
            visibility_checkbox.setProperty("template_id", t_data.get("template_id"))
            checkbox_layout.addWidget(visibility_checkbox)
            self.template_visibility_table.setCellWidget(row_idx, 4, checkbox_widget)

        self.template_visibility_table.setSortingEnabled(True)
        print(f"SettingsPage: Template visibility table populated with {len(sample_data)} items (mocked).")


    def _save_template_visibility_data(self):
        print("SettingsPage: _save_template_visibility_data called (mocked).")
        payload_items = []
        for row_idx in range(self.template_visibility_table.rowCount()):
            template_id_item = self.template_visibility_table.item(row_idx, 0)
            template_id = template_id_item.data(Qt.UserRole) if template_id_item else None

            visibility_cell_widget = self.template_visibility_table.cellWidget(row_idx, 4)
            if not (template_id and visibility_cell_widget):
                print(f"Warning: Missing data for row {row_idx}. Skipping.")
                continue

            # Assuming the cell widget is the QWidget container, find the QCheckBox
            visibility_checkbox = visibility_cell_widget.findChild(QCheckBox)
            if not visibility_checkbox:
                print(f"Warning: QCheckBox not found in cell for row {row_idx}, template_id {template_id}. Skipping.")
                continue

            is_visible = visibility_checkbox.isChecked()
            payload_items.append({"template_id": template_id, "is_visible": is_visible})

        payload = {"preferences": payload_items}
        print(f"SettingsPage: Payload for POST /api/templates/visibility_settings (mocked): {payload}")

        # Mocked API call
        # try:
        #     response = self._call_api(method="POST", endpoint="/api/templates/visibility_settings", data=payload)
        #     if response and response.get("message"):
        #         QMessageBox.information(self, self.tr("Success"), self.tr("Template visibility settings saved successfully."))
        #         self._load_template_visibility_data() # Refresh data
        #     else:
        #         QMessageBox.warning(self, self.tr("Save Error"), self.tr("Failed to save template visibility settings.") + (f"\nDetail: {response.get('detail')}" if response else ""))
        # except Exception as e:
        #     QMessageBox.critical(self, self.tr("API Error"), self.tr("Error calling API to save template visibility: {0}").format(str(e)))

        # For mocked version:
        QMessageBox.information(self, self.tr("Mock Save"), self.tr("Template visibility data (mocked) prepared. Check console for payload."))
        # self._load_template_visibility_data() # Optionally refresh after mock save too

    def _handle_run_backup(self):
        server_address = self.backup_server_address_input.text().strip()
        port = self.backup_port_input.text().strip()
        username = self.backup_username_input.text().strip()
        # For security, we retrieve the password but should be careful with logging or displaying it.
        # For this placeholder, we'll just acknowledge it's retrieved.
        password = self.backup_password_input.text() # No strip, as passwords can have leading/trailing spaces

        details_message = self.tr(
            "Backup process would start now with these details:\n\n"
            "Server Address: {0}\n"
            "Port: {1}\n"
            "Username: {2}\n"
            "Password: {3}" # In a real scenario, avoid displaying/logging the password
        ).format(
            server_address if server_address else self.tr("[Not provided]"),
            port if port else self.tr("[Not provided]"),
            username if username else self.tr("[Not provided]"),
            self.tr("********") if password else self.tr("[Not provided]") # Mask password in message
        )

        QMessageBox.information(
            self,
            self.tr("Run Backup"),
            details_message
        )
        # Actual backup logic would be implemented here or called from here.
        print(f"Backup Details: Address='{server_address}', Port='{port}', User='{username}', Password_Length='{len(password)}'")

    def _setup_security_tab(self):
        """
        Sets up the Security tab with the Biometric Authentication Test page.
        """
        # SecuritySettingsPage is already a QWidget, so it can be added directly as a tab.
        # It doesn't require self.main_config or other specific parameters from SettingsPage itself
        # for its current functionality (testing biometric simulations).
        self.security_test_page = SecuritySettingsPage()
        self.tabs_widget.addTab(self.security_test_page, self.tr("Security (Biometric Test)"))

    def _setup_my_business_tab(self):
        if USER_PROFILE_MODULE_AVAILABLE and MyBusinessWidget is not None:
            # Assuming current_user_id is available in self
            # If MyBusinessWidget needs the main_config or app_root_dir, pass them as well.
            # For now, it only seems to need user_id.
            self.my_business_widget_instance = MyBusinessWidget(user_id=self.current_user_id, parent=self)
            self.tabs_widget.addTab(self.my_business_widget_instance, self.tr("Mon Entreprise (Profil)"))
        else:
            # Create a placeholder tab indicating the module is unavailable
            unavailable_tab = QWidget()
            layout = QVBoxLayout(unavailable_tab)
            label = QLabel(self.tr("The 'My Business' module is currently unavailable.\nPlease check the application logs for more details (ImportError)."))
            label.setAlignment(Qt.AlignCenter)
            label.setWordWrap(True)
            layout.addWidget(label)
            self.tabs_widget.addTab(unavailable_tab, self.tr("Mon Entreprise (Profil) - Erreur"))

    # --- SMTP Configuration Management Methods ---
    def _load_smtp_configs_table(self):
        if not db_manager:
            QMessageBox.warning(self, self.tr("Erreur Base de Données"), self.tr("Connexion à la base de données non disponible. Impossible de charger les configurations SMTP."))
            return

        self.smtp_configs_table.setRowCount(0) # Clear existing rows
        self.smtp_configs_table.setSortingEnabled(False)
        try:
            configs = db_manager.get_all_smtp_configs() or []
            for row_idx, config_data in enumerate(configs):
                self.smtp_configs_table.insertRow(row_idx)

                # ID (hidden)
                id_item = QTableWidgetItem(str(config_data.get('smtp_config_id')))
                self.smtp_configs_table.setItem(row_idx, 0, id_item)

                # Config Name
                name_item = QTableWidgetItem(config_data.get('config_name'))
                name_item.setData(Qt.UserRole, config_data.get('smtp_config_id')) # Store ID for easy access
                self.smtp_configs_table.setItem(row_idx, 1, name_item)

                self.smtp_configs_table.setItem(row_idx, 2, QTableWidgetItem(config_data.get('smtp_server')))
                self.smtp_configs_table.setItem(row_idx, 3, QTableWidgetItem(str(config_data.get('smtp_port'))))
                self.smtp_configs_table.setItem(row_idx, 4, QTableWidgetItem(config_data.get('username')))
                self.smtp_configs_table.setItem(row_idx, 5, QTableWidgetItem(config_data.get('sender_email_address')))

                # Is Default Global
                default_checkbox = QCheckBox()
                default_checkbox.setChecked(bool(config_data.get('is_default')))
                default_checkbox.setEnabled(False) # Display only, actual setting via button
                cell_widget = QWidget()
                layout = QHBoxLayout(cell_widget)
                layout.addWidget(default_checkbox)
                layout.setAlignment(Qt.AlignCenter)
                layout.setContentsMargins(0,0,0,0)
                self.smtp_configs_table.setCellWidget(row_idx, 6, cell_widget)

        except Exception as e:
            logger.error(f"Error loading SMTP configurations into table: {e}", exc_info=True)
            QMessageBox.warning(self, self.tr("Erreur Chargement SMTP"), self.tr("Erreur lors du chargement des configurations SMTP: {0}").format(str(e)))
        finally:
            self.smtp_configs_table.setSortingEnabled(True)
            self._update_smtp_buttons_state()

    def _handle_add_smtp_config(self):
        if not db_manager: return
        dialog = SmtpConfigDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self._load_smtp_configs_table() # Refresh table

    def _handle_edit_smtp_config(self):
        if not db_manager: return
        selected_items = self.smtp_configs_table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, self.tr("Sélection Requise"), self.tr("Veuillez sélectionner une configuration SMTP à modifier."))
            return

        # Get ID from the hidden first column of the selected row
        config_id_str = self.smtp_configs_table.item(selected_items[0].row(), 0).text()
        try:
            config_id = int(config_id_str)
        except ValueError:
            QMessageBox.critical(self, self.tr("Erreur ID"), self.tr("ID de configuration SMTP invalide."))
            return

        dialog = SmtpConfigDialog(config_id=config_id, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self._load_smtp_configs_table()

    def _handle_delete_smtp_config(self):
        if not db_manager: return
        selected_items = self.smtp_configs_table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, self.tr("Sélection Requise"), self.tr("Veuillez sélectionner une configuration SMTP à supprimer."))
            return

        config_id_str = self.smtp_configs_table.item(selected_items[0].row(), 0).text()
        config_name = self.smtp_configs_table.item(selected_items[0].row(), 1).text() # For confirmation message
        try:
            config_id = int(config_id_str)
        except ValueError:
            QMessageBox.critical(self, self.tr("Erreur ID"), self.tr("ID de configuration SMTP invalide pour la suppression."))
            return

        reply = QMessageBox.question(self, self.tr("Confirmer Suppression"),
                                     self.tr("Êtes-vous sûr de vouloir supprimer la configuration SMTP '{0}'?").format(config_name),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if db_manager.delete_smtp_config(config_id):
                QMessageBox.information(self, self.tr("Succès"), self.tr("Configuration SMTP supprimée."))
                self._load_smtp_configs_table()
            else:
                QMessageBox.warning(self, self.tr("Échec"), self.tr("Impossible de supprimer la configuration SMTP."))

    def _handle_set_global_default_smtp(self):
        if not db_manager: return
        selected_items = self.smtp_configs_table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, self.tr("Sélection Requise"), self.tr("Veuillez sélectionner une configuration à définir comme défaut global."))
            return

        config_id_str = self.smtp_configs_table.item(selected_items[0].row(), 0).text()
        config_name = self.smtp_configs_table.item(selected_items[0].row(), 1).text()
        try:
            config_id = int(config_id_str)
        except ValueError:
            QMessageBox.critical(self, self.tr("Erreur ID"), self.tr("ID de configuration SMTP invalide pour la définition par défaut."))
            return

        # Check if it's already default
        current_data_item = self.smtp_configs_table.cellWidget(selected_items[0].row(), 6) # Checkbox widget
        if current_data_item:
            checkbox = current_data_item.findChild(QCheckBox)
            if checkbox and checkbox.isChecked():
                QMessageBox.information(self, self.tr("Information"), self.tr("La configuration '{0}' est déjà le défaut global.").format(config_name))
                return

        if db_manager.set_default_smtp_config(config_id):
            QMessageBox.information(self, self.tr("Succès"), self.tr("La configuration '{0}' est maintenant le défaut global.").format(config_name))
            self._load_smtp_configs_table()
        else:
            QMessageBox.warning(self, self.tr("Échec"), self.tr("Impossible de définir la configuration '{0}' comme défaut global.").format(config_name))

    def _update_smtp_buttons_state(self):
        has_selection = bool(self.smtp_configs_table.selectedItems())
        self.edit_smtp_config_btn.setEnabled(has_selection)
        self.delete_smtp_config_btn.setEnabled(has_selection)
        self.set_global_default_smtp_btn.setEnabled(has_selection)

        # Also check if the selected config is already default, if so, disable "Set Default"
        if has_selection:
            selected_row = self.smtp_configs_table.currentRow()
            default_widget = self.smtp_configs_table.cellWidget(selected_row, 6) # Column for "Default Global"
            if default_widget:
                checkbox = default_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    self.set_global_default_smtp_btn.setEnabled(False)
                    self.set_global_default_smtp_btn.setToolTip(self.tr("Cette configuration est déjà le défaut global."))
                else:
                    self.set_global_default_smtp_btn.setToolTip(self.tr("Définir cette configuration comme défaut global pour l'application."))
            else: # Should not happen if table is populated correctly
                 self.set_global_default_smtp_btn.setToolTip("")


    # --- User Email Assignment Methods ---
    def _load_users_for_assignment_combo(self):
        self.assign_user_combo.blockSignals(True)
        self.assign_user_combo.clear()
        self.assign_user_combo.addItem(self.tr("Sélectionner un utilisateur..."), None)
        if not db_manager:
            self.assign_user_combo.blockSignals(False)
            return
        try:
            # Assuming list_users returns a list of dicts with 'user_id' and 'username'
            users = db_manager.list_users(include_deleted=False, status_filter='active')
            for user in sorted(users, key=lambda u: u.get('username', '').lower()):
                display_name = f"{user.get('full_name', user.get('username', 'N/A'))} ({user.get('username', 'N/A')})"
                self.assign_user_combo.addItem(display_name, user.get('user_id'))
        except Exception as e:
            logger.error(f"Error loading users into assignment combo: {e}", exc_info=True)
        finally:
            self.assign_user_combo.blockSignals(False)

    def _load_available_global_smtp_configs_combo(self):
        self.assign_global_smtp_combo.blockSignals(True)
        self.assign_global_smtp_combo.clear()
        self.assign_global_smtp_combo.addItem(self.tr("Choisir une configuration SMTP globale..."), None)
        if not db_manager:
            self.assign_global_smtp_combo.blockSignals(False)
            return
        try:
            configs = db_manager.get_all_smtp_configs()
            for config in sorted(configs, key=lambda c: c.get('config_name', '').lower()):
                self.assign_global_smtp_combo.addItem(config.get('config_name'), config.get('smtp_config_id'))
        except Exception as e:
            logger.error(f"Error loading global SMTP configs into assignment combo: {e}", exc_info=True)
        finally:
            self.assign_global_smtp_combo.blockSignals(False)

    def _load_assigned_smtp_for_selected_user(self):
        self.user_assigned_smtp_table.setRowCount(0)
        selected_user_id = self.assign_user_combo.currentData()
        if not selected_user_id or not db_manager:
            self._update_user_assignment_buttons_state()
            return

        try:
            assigned_configs = db_manager.get_user_smtp_assignments(selected_user_id)
            self.user_assigned_smtp_table.setSortingEnabled(False)
            for row_idx, assignment_data in enumerate(assigned_configs):
                self.user_assigned_smtp_table.insertRow(row_idx)

                # Assignment ID (hidden)
                assign_id_item = QTableWidgetItem(str(assignment_data.get('assignment_id')))
                self.user_assigned_smtp_table.setItem(row_idx, 0, assign_id_item)

                # Config Name (from SmtpConfigs table via JOIN in get_user_smtp_assignments)
                config_name_item = QTableWidgetItem(assignment_data.get('config_name'))
                # Store assignment_id in UserRole for easy access from selection
                config_name_item.setData(Qt.UserRole, assignment_data.get('assignment_id'))
                self.user_assigned_smtp_table.setItem(row_idx, 1, config_name_item)

                self.user_assigned_smtp_table.setItem(row_idx, 2, QTableWidgetItem(assignment_data.get('sender_email_address')))

                # Is Default for User
                user_default_checkbox = QCheckBox()
                user_default_checkbox.setChecked(bool(assignment_data.get('is_default_for_user')))
                user_default_checkbox.setEnabled(False) # Display only
                cell_widget = QWidget()
                layout = QHBoxLayout(cell_widget)
                layout.addWidget(user_default_checkbox)
                layout.setAlignment(Qt.AlignCenter)
                layout.setContentsMargins(0,0,0,0)
                self.user_assigned_smtp_table.setCellWidget(row_idx, 3, cell_widget)

        except Exception as e:
            logger.error(f"Error loading assigned SMTP configs for user {selected_user_id}: {e}", exc_info=True)
        finally:
            self.user_assigned_smtp_table.setSortingEnabled(True)
            self._update_user_assignment_buttons_state()

    def _handle_assign_smtp_to_user(self):
        selected_user_id = self.assign_user_combo.currentData()
        selected_smtp_config_id = self.assign_global_smtp_combo.currentData()

        if not selected_user_id:
            QMessageBox.warning(self, self.tr("Utilisateur Non Sélectionné"), self.tr("Veuillez sélectionner un utilisateur."))
            return
        if not selected_smtp_config_id:
            QMessageBox.warning(self, self.tr("Configuration Non Sélectionnée"), self.tr("Veuillez sélectionner une configuration SMTP globale à assigner."))
            return

        if not db_manager: return

        # Check if this config is already assigned to the user
        existing_assignments = db_manager.get_user_smtp_assignments(selected_user_id)
        if any(a['smtp_config_id'] == selected_smtp_config_id for a in existing_assignments):
            QMessageBox.information(self, self.tr("Déjà Assigné"), self.tr("Cette configuration SMTP est déjà assignée à cet utilisateur."))
            return

        # For simplicity, new assignments are not set as user's default by default.
        # User can use "Set as User's Default" button after assignment.
        assignment_id = db_manager.assign_smtp_to_user(selected_user_id, selected_smtp_config_id, is_default_for_user=False)
        if assignment_id:
            QMessageBox.information(self, self.tr("Succès"), self.tr("Configuration SMTP assignée avec succès à l'utilisateur."))
            self._load_assigned_smtp_for_selected_user() # Refresh table
        else:
            QMessageBox.critical(self, self.tr("Échec"), self.tr("Impossible d'assigner la configuration SMTP à l'utilisateur."))

    def _handle_set_user_default_smtp(self):
        selected_user_id = self.assign_user_combo.currentData()
        selected_assignment_items = self.user_assigned_smtp_table.selectedItems()

        if not selected_user_id:
            QMessageBox.warning(self, self.tr("Utilisateur Non Sélectionné"), self.tr("Veuillez sélectionner un utilisateur."))
            return
        if not selected_assignment_items:
            QMessageBox.warning(self, self.tr("Affectation Non Sélectionnée"), self.tr("Veuillez sélectionner une affectation dans la table à définir comme défaut pour l'utilisateur."))
            return

        if not db_manager: return

        assignment_id = self.user_assigned_smtp_table.item(selected_assignment_items[0].row(), 0).text()
        config_name = self.user_assigned_smtp_table.item(selected_assignment_items[0].row(), 1).text()

        # Check if it's already default for user
        default_cell_widget = self.user_assigned_smtp_table.cellWidget(selected_assignment_items[0].row(), 3)
        if default_cell_widget:
            checkbox = default_cell_widget.findChild(QCheckBox)
            if checkbox and checkbox.isChecked():
                QMessageBox.information(self, self.tr("Information"), self.tr("La configuration '{0}' est déjà le défaut pour cet utilisateur.").format(config_name))
                return

        if db_manager.set_default_smtp_for_user(selected_user_id, assignment_id):
            QMessageBox.information(self, self.tr("Succès"), self.tr("La configuration '{0}' est maintenant le défaut pour l'utilisateur {1}.").format(config_name, self.assign_user_combo.currentText()))
            self._load_assigned_smtp_for_selected_user() # Refresh table
        else:
            QMessageBox.warning(self, self.tr("Échec"), self.tr("Impossible de définir la configuration comme défaut pour l'utilisateur."))

    def _handle_unassign_smtp_from_user(self):
        selected_assignment_items = self.user_assigned_smtp_table.selectedItems()
        if not selected_assignment_items:
            QMessageBox.warning(self, self.tr("Affectation Non Sélectionnée"), self.tr("Veuillez sélectionner une affectation à supprimer."))
            return

        if not db_manager: return

        assignment_id = self.user_assigned_smtp_table.item(selected_assignment_items[0].row(), 0).text()
        config_name = self.user_assigned_smtp_table.item(selected_assignment_items[0].row(), 1).text() # For message
        user_name = self.assign_user_combo.currentText()

        reply = QMessageBox.question(self, self.tr("Confirmer Désassignation"),
                                     self.tr("Êtes-vous sûr de vouloir désassigner la configuration '{0}' de l'utilisateur '{1}'?").format(config_name, user_name),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if db_manager.unassign_smtp_from_user(assignment_id):
                QMessageBox.information(self, self.tr("Succès"), self.tr("Configuration désassignée avec succès."))
                self._load_assigned_smtp_for_selected_user() # Refresh
            else:
                QMessageBox.warning(self, self.tr("Échec"), self.tr("Impossible de désassigner la configuration."))

    def _update_user_assignment_buttons_state(self):
        user_selected = bool(self.assign_user_combo.currentData())
        assignment_selected = bool(self.user_assigned_smtp_table.selectedItems())
        global_config_selected_for_assign = bool(self.assign_global_smtp_combo.currentData())

        self.assign_smtp_to_user_btn.setEnabled(user_selected and global_config_selected_for_assign)
        self.set_user_default_smtp_btn.setEnabled(user_selected and assignment_selected)
        self.unassign_smtp_from_user_btn.setEnabled(user_selected and assignment_selected)

        # Further refinement for "Set as User's Default"
        if user_selected and assignment_selected:
            selected_row = self.user_assigned_smtp_table.currentRow()
            default_widget = self.user_assigned_smtp_table.cellWidget(selected_row, 3) # Column for "Défaut pour Utilisateur"
            if default_widget:
                checkbox = default_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    self.set_user_default_smtp_btn.setEnabled(False)
                    self.set_user_default_smtp_btn.setToolTip(self.tr("Cette configuration est déjà le défaut pour cet utilisateur."))
                else:
                    self.set_user_default_smtp_btn.setToolTip(self.tr("Définir cette configuration comme défaut pour l'utilisateur sélectionné."))
            else: # Should not happen
                self.set_user_default_smtp_btn.setToolTip("")


    # --- End User Email Assignment Methods ---

    # --- End SMTP Configuration Management Methods ---


if __name__ == '__main__':
    print(f"Running in __main__ block. Current sys.path: {sys.path}") # Debug print
    from PyQt5.QtWidgets import QApplication
    # sys and os are already imported at the top

    # Mock db_manager for standalone testing
    # The global 'db_manager' will be replaced by an instance of this class.
    class MockDBManager:
        def get_all_transporters(self): print("MOCKDB: get_all_transporters"); return [{"transporter_id": "t1", "name": "Mock Transporter 1", "contact_person": "John T", "phone": "123", "email": "jt@example.com", "service_area": "Local"}, {"transporter_id": "t2", "name": "Mock Transporter 2", "contact_person": "Alice T", "phone": "456", "email": "at@example.com", "service_area": "National"}]
        def get_transporter_by_id(self, tid): print(f"MOCKDB: get_transporter_by_id {tid}"); return {"transporter_id": tid, "name": f"Mock Transporter {tid}", "contact_person":"Test", "phone":"Test", "email":"Test", "service_area":"Test"} if tid in ["t1", "t2"] else None
        def add_transporter(self, data): print(f"MOCKDB: add_transporter: {data}"); return "t_new_mock_id"
        def update_transporter(self, tid, data): print(f"MOCKDB: update_transporter {tid}: {data}"); return True
        def delete_transporter(self, tid): print(f"MOCKDB: delete_transporter {tid}"); return True

        def get_all_freight_forwarders(self): print("MOCKDB: get_all_freight_forwarders"); return [{"forwarder_id": "f1", "name": "Mock Forwarder 1", "contact_person": "Jane F", "phone": "456", "email": "jf@example.com", "services_offered": "Global"}, {"forwarder_id": "f2", "name": "Mock Forwarder 2", "contact_person": "Bob F", "phone": "789", "email": "bf@example.com", "services_offered": "Air, Sea"}]
        def get_freight_forwarder_by_id(self, fid): print(f"MOCKDB: get_freight_forwarder_by_id {fid}"); return {"forwarder_id": fid, "name": f"Mock Forwarder {fid}", "contact_person":"Test", "phone":"Test", "email":"Test", "services_offered":"Test"} if fid in ["f1", "f2"] else None
        def add_freight_forwarder(self, data): print(f"MOCKDB: add_freight_forwarder: {data}"); return "f_new_mock_id"
        def update_freight_forwarder(self, fid, data): print(f"MOCKDB: update_freight_forwarder {fid}: {data}"); return True
        def delete_freight_forwarder(self, fid): print(f"MOCKDB: delete_freight_forwarder {fid}"); return True

        def get_all_companies(self): print("MOCKDB: get_all_companies"); return [{"company_id": "c1", "company_name": "Mock Company Inc.", "is_default": True}]
        def get_personnel_for_company(self, cid, role=None): print(f"MOCKDB: get_personnel_for_company {cid}"); return [{"personnel_id": "p1", "name": "Mock User", "role": "Admin"}]
        def get_company_details(self, cid): print(f"MOCKDB: get_company_details {cid}"); return {"company_id": "c1", "company_name": "Mock Company Inc."}
        def initialize_database(self): print("MOCKDB: initialize_database")

        # Mock methods for module settings
        def __init__(self):
            print("MOCKDB: __init__")
            self.settings_cache = {} # Simple cache for mock settings

        def get_setting(self, key, default=None):
            print(f"MOCKDB: get_setting called for {key}, default: {default}")
            return self.settings_cache.get(key, default)

        def set_setting(self, key, value):
            print(f"MOCKDB: set_setting called for {key} with value {value}")
            self.settings_cache[key] = value
            return True

    # Crucially, make the global 'db_manager' this mock instance
    # This ensures SettingsPage uses this mock if its own 'import db' failed or was pre-empted.
    db_manager = MockDBManager()
    # print(f"MAIN_MID: Global db_manager is now {type(db_manager)}")

    # Mock dialogs to prevent them from trying to use real db_manager if they import it themselves
    class MockTransporterDialog(QDialog):
        def __init__(self, transporter_data=None, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Mock Transporter Dialog")
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("This is a Mock Transporter Dialog." + (" Editing mode." if transporter_data else " Adding mode.")))
            ok_button = QPushButton("OK")
            ok_button.clicked.connect(self.accept)
            layout.addWidget(ok_button)
            print(f"MockTransporterDialog initialized. Data: {transporter_data}")
        # exec_ is inherited

    class MockFreightForwarderDialog(QDialog):
        def __init__(self, forwarder_data=None, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Mock Freight Forwarder Dialog")
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("This is a Mock Freight Forwarder Dialog." + (" Editing mode." if forwarder_data else " Adding mode.")))
            ok_button = QPushButton("OK")
            ok_button.clicked.connect(self.accept)
            layout.addWidget(ok_button)
            print(f"MockFreightForwarderDialog initialized. Data: {forwarder_data}")

    # Monkey-patch the actual dialog imports if they are problematic during test
    # This is tricky because 'from X import Y' has already been processed for SettingsPage class
    # For this to work reliably for SettingsPage, these names would need to be re-resolved,
    # or SettingsPage imported *after* these patches.
    # However, if 'dialogs' itself isn't found, this won't help that part.
    # For now, let's assume the sys.path fix + db mock will allow 'dialogs' to be found.
    # If ModuleNotFoundError for 'dialogs' persists, then these patches are insufficient.
    # Corrected way to create mock modules for dialogs:
    mock_transporter_module = types.ModuleType(__name__ + '.mock_transporter_dialog')
    mock_transporter_module.TransporterDialog = MockTransporterDialog
    sys.modules['dialogs.transporter_dialog'] = mock_transporter_module

    mock_freight_forwarder_module = types.ModuleType(__name__ + '.mock_freight_forwarder_dialog')
    mock_freight_forwarder_module.FreightForwarderDialog = MockFreightForwarderDialog
    sys.modules['dialogs.freight_forwarder_dialog'] = mock_freight_forwarder_module

    # We also need to mock CompanyTabWidget if its import is failing or causing issues
    # from company_management import CompanyTabWidget
    class MockCompanyTabWidget(QWidget): # Ensure it's a QWidget
        def __init__(self, parent=None, app_root_dir=None, current_user_id=None):
            super().__init__(parent)
            self.setLayout(QVBoxLayout())
            self.layout().addWidget(QLabel("Mock Company Tab Widget"))
            print("MOCK_COMPANY_TAB: Initialized")

    # If 'company_management' module itself failed to load, this global needs to be our mock:
    # This is highly dependent on how 'company_management' is imported and used.
    # For now, if 'from company_management import CompanyTabWidget' failed, this won't fix it
    # unless we also patch 'company_management' in sys.modules.
    # Let's assume 'company_management' module loads but we want to mock the class.
    # This is more for replacing the class rather than fixing ModuleNotFoundError for the module.
    # To fix ModuleNotFoundError for 'company_management', sys.path must be correct.
    # For now, we are assuming the script will find 'company_management' due to sys.path.
    # The global name 'CompanyTabWidget' will be used by SettingsPage.
    # We are not explicitly overriding the global 'CompanyTabWidget' here yet, relying on MockDBManager
    # and hoping the dialogs issue gets resolved first.


    app = QApplication(sys.argv)
    mock_config = {
        "templates_dir": "./templates_mock", "clients_dir": "./clients_mock", "language": "en",
        "default_reminder_days": 15, "session_timeout_minutes": 60, "database_path": "mock_app.db",
        "google_maps_review_url": "https://maps.google.com/mock", "show_initial_setup_on_startup": True,
        "smtp_server": "smtp.mock.com", "smtp_port": 587, "smtp_user": "mock_user", "smtp_password": "mock_password",
        "download_monitor_enabled": False,
        "download_monitor_path": os.path.join(os.path.expanduser('~'), 'Downloads_mock')
    }
    # Add default module settings to mock_config for testing _load_modules_tab_data if it were to use main_config
    # However, our implementation uses db_manager.get_setting, so we'll pre-populate the MockDBManager's cache.
    if db_manager: # Ensure db_manager (MockDBManager instance) exists
        # Pre-populate module settings for testing _load_modules_tab_data
        print("MAIN: Pre-populating MockDBManager with initial module states...")
        db_manager.set_setting("module_project_management_enabled", "True")  # String 'True'
        db_manager.set_setting("module_product_management_enabled", "False") # String 'False'
        db_manager.set_setting("module_partner_management_enabled", "True")
        db_manager.set_setting("module_statistics_enabled", "False")
        # module_inventory_management_enabled will use the default 'True' from _load_modules_tab_data
        db_manager.set_setting("module_botpress_integration_enabled", "True")
        # module_carrier_map_enabled will use the default 'True'
        db_manager.set_setting("module_camera_management_enabled", "True") # For testing the new module

    mock_app_root_dir = os.path.abspath(os.path.dirname(__file__))
    mock_current_user_id = "test_user_settings_main"

    # For CompanyTabWidget, ensure its db calls are also covered by MockDBManager
    # CompanyTabWidget might also need specific setup or its own mocks if it's complex.

    settings_window = SettingsPage(
        main_config=mock_config,
        app_root_dir=mock_app_root_dir,
        current_user_id=mock_current_user_id
    )
    settings_window.setGeometry(100, 100, 950, 750)
    settings_window.setWindowTitle("Settings Page Test - Transporters & Forwarders")
    settings_window.show()
    sys.exit(app.exec_())
