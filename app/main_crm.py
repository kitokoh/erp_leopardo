# -*- coding: utf-8 -*-
import sys
import os

# Determine project root and add it to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Ensure this debug print is AFTER the sys.path modification and BEFORE any project imports
# print(f"DEBUG main.py: Initial PROJECT_ROOT: {PROJECT_ROOT}")
# print(f"DEBUG main.py: sys.path after modification in main.py: {sys.path}")
# print(f"DEBUG main.py: current working directory: {os.getcwd()}")

# Now, other imports can follow
import logging # For main.py's own logging needs, and for translator parts if setup_logging isn't called first
from app import icons_rc # Import the compiled resource file
import atexit # Added for stopping API server on exit

# Core PyQt5 imports for application execution
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import QLocale, QLibraryInfo, QTranslator, Qt, QSize
from PyQt5.QtGui import QFont, QPixmap, QMovie
from PyQt5.QtCore import QStringListModel

# Imports from project structure
from app.app_setup import (
    APP_ROOT_DIR, CONFIG,
    setup_logging, load_stylesheet_global, initialize_default_templates
)
from app.utils import save_config # Changed import from app_config to utils
from app.utils import is_first_launch, mark_initial_setup_complete
from app.auth.roles import SUPER_ADMIN
# Import InitialSetupDialog and PromptCompanyInfoDialog
from app.settings.initial_setup_dialog import InitialSetupDialog, PromptCompanyInfoDialog
from PyQt5.QtWidgets import QDialog # Required for QDialog.Accepted check
# Import specific db functions needed
import app.db as db
# from db.init_schema import initialize_database as initialize_database_from_schema # This is now handled by the core initializer
# from db.cruds.misc.application_settings_crud import get_setting, set_setting
# from db.db_seed import run_seed, seed_only_hidroguc_products
# from db.cruds.misc.companies_crud import get_all_companies, add_company
# from db.cruds.users import users_crud
# from auth.login_window import LoginWindow # Replaced by LoginDialog
# from gui.dialogs.login_dialog import LoginDialog # New LoginDialog
# from auth import authentication as auth_service # Import the auth service
# from user_profile_management.database_setup import create_tables as create_user_profile_tables
# from user_profile_management.database_setup import seed_data as seed_user_profile_data

from PyQt5.QtWidgets import QDialog, QMessageBox, QSplashScreen, QMainWindow
# from initial_setup_dialog import InitialSetupDialog # Redundant import, already imported above
# import db as db_manager # For db initialization - already imported above, now using 'import db'
from app.notifications import NotificationManager # Added for notifications
# from db.cruds.users_crud import users_crud_instance # users_crud is used directly by auth_service
# from PyQt5.QtWidgets import QMessageBox # Added for error dialog
# from PyQt5.QtWidgets import QSplashScreen

from app.gui.main_window import DocumentManager
from PyQt5.QtCore import QSettings # Added for Remember Me
from PyQt5.QtCore import Qt

# Imports pour la gestion de licence
# from db.connection import get_db_connection # Moved into functions
from app.license_management import manager as license_manager
from app.license_management.ui import LicenseDialog # Décommenté
from app.auth.session_manager import SessionManager
from app.core.initializer import initialize_database, setup_qt_application, setup_translations
from app.auth.auth_flow_manager import AuthFlowManager
from app.core.api_server_manager import APIServerManager

# --- DEVELOPMENT/TESTING FLAG ---
# Set to True to bypass the login screen for faster testing.
# WARNING: This will log in as the default admin user with super_admin privileges
# and should ONLY be used for development/testing purposes.
# Ensure this is set to False for production or normal use.
BYPASS_LOGIN_FOR_TESTING = False
# --- End Development/Testing: Bypass Login Flag ---

class CRMModule(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | self.windowFlags())
        self.setWindowTitle("CRM Module")
        self.setGeometry(100, 100, 1200, 800)
        self.main_widget = None
        self.session_manager = None  # Initialize session_manager attribute
        self.init_app()

    def init_app(self):
        # 1. Configure logging as the very first step.
        setup_logging()
        logging.info("Application starting...")
        logging.info(f"CONFIGURED DATABASE_PATH: {CONFIG.get('database_path', 'NOT FOUND IN CONFIG')}")

        # Register logging.shutdown() to be called on exit to properly close handlers
        atexit.register(logging.shutdown)
        logging.info("logging.shutdown registered with atexit.")

        # Set the database configuration for db.connection module
        # This must be done after app_setup.CONFIG is loaded and before any db operations
        if hasattr(db, 'connection') and hasattr(db.connection, 'set_db_config'):
            db.connection.set_db_config(CONFIG)
            logging.info("main.py: db.connection.set_db_config(CONFIG) called.")
        else:
            logging.error("main.py: Could not find db.connection.set_db_config. DB calls might fail.")
        # Initialize the database. This function now encapsulates all DB setup.
        initialize_database(CONFIG, PROJECT_ROOT)

        # --- Import DB-dependent modules AFTER initialization ---

        from app.db.db_seed import seed_all_data as run_seed
        from app.db.seeders.hidroguc_product_seeder import seed_hidroguc_products as seed_only_hidroguc_products
        from app.db.connection import get_db_connection
        from app.db.cruds.misc.application_settings_crud import get_setting
        from app.db.cruds.users import users_crud
        from app.db.cruds.misc.companies_crud import get_all_companies, add_company
        # --- End DB-dependent imports ---


        # Seed Hidroguc products with proper session management
        db_session_for_hidroguc = None
        try:
            db_session_for_hidroguc = get_db_connection()
            main_logger = logging.getLogger(__name__)
            if db_session_for_hidroguc:
                seed_only_hidroguc_products(db=db_session_for_hidroguc, logger_passed=main_logger)
                db_session_for_hidroguc.commit() # Commit the changes from the seeder
            else:
                main_logger.error("Could not get a database session for seeding Hidroguc products.")
        except Exception as e_hidro_seed:
            main_logger.error(f"An error occurred during Hidroguc product seeding: {e_hidro_seed}", exc_info=True)
            if db_session_for_hidroguc:
                db_session_for_hidroguc.rollback()
        finally:
            if db_session_for_hidroguc:
                db_session_for_hidroguc.close()

        # Set the configuration for document_generator.context_builder
        try:
            from app.document_generator import context_builder as doc_gen_context_builder
            if hasattr(doc_gen_context_builder, 'set_document_generator_config'):
                doc_gen_context_builder.set_document_generator_config(CONFIG)
                logging.info("main.py: document_generator.context_builder.set_document_generator_config(CONFIG) called.")
            else:
                logging.error("main.py: Could not find document_generator.context_builder.set_document_generator_config.")
        except ImportError:
            logging.error("main.py: Failed to import document_generator.context_builder to set its config.")
        except Exception as e_docgen_conf:
            logging.error(f"main.py: Error setting document_generator config: {e_docgen_conf}", exc_info=True)

        # --- Token Cleanup on Startup ---
        conn_cleanup = None
        try:
            conn_cleanup = get_db_connection() # Get a connection for cleanup tasks
            if conn_cleanup:
                from app.db.cruds import user_session_tokens_crud
                from app.db.cruds.users import password_reset_tokens_crud

                cleaned_session_tokens = user_session_tokens_crud.cleanup_expired_tokens(conn_cleanup)
                logging.info(f"Cleaned up {cleaned_session_tokens} expired 'Remember Me' session tokens on startup.")
                cleaned_reset_tokens = password_reset_tokens_crud.cleanup_expired_or_used_tokens(conn_cleanup)
                logging.info(f"Cleaned up {cleaned_reset_tokens} expired/used password reset tokens on startup.")

                conn_cleanup.commit() # Commit changes from cleanup
            else:
                logging.error("Could not get DB connection for token cleanup on startup.")
        except Exception as e_cleanup:
            logging.error(f"Error during token cleanup on startup: {e_cleanup}", exc_info=True)
            if conn_cleanup:
                conn_cleanup.rollback() # Rollback if error during cleanup
        finally:
            if conn_cleanup:
                conn_cleanup.close()
        # --- End Token Cleanup ---

        # The session timeout is now managed within the SessionManager.
        # timeout_minutes = CONFIG.get("session_timeout_minutes", 30)
        timeout_minutes = 12 * 30 * 24 * 60 # Approx 12 months
        self.session_manager = SessionManager(timeout_minutes=timeout_minutes)
        logging.info(f"SessionManager initialized with a timeout of {timeout_minutes} minutes.")

        # 2. Create QApplication Instance
        app = QApplication.instance() or QApplication(sys.argv)

        # 3. Setup basic Qt application settings
        setup_qt_application(app)

        # 4. Determine language for splash screen and translations
        current_app_lang = QLocale.system().name().split('_')[0] # Default
        try:
            language_code_from_db = get_setting('user_selected_language')
            if language_code_from_db and isinstance(language_code_from_db, str) and language_code_from_db.strip():
                current_app_lang = language_code_from_db.strip()
                logging.info(f"Language '{current_app_lang}' loaded from database setting.")
            else:
                sys_lang = QLocale.system().name().split('_')[0]
                current_app_lang = CONFIG.get("language", sys_lang if sys_lang in ["en", "fr", "ar"] else "en")
                logging.info(f"Language '{current_app_lang}' from config/system (DB setting not found or invalid).")
        except Exception as e_lang:
            logging.error(f"Error getting language, defaulting. Error: {e_lang}")
            # current_app_lang remains system default or 'en'

        # 5. Display Splash Screen
        from app.ui.splash_screen import SplashWindow
        splash = SplashWindow(app_root_dir=APP_ROOT_DIR, language_code=current_app_lang)
        splash.show_splash()

        # 6. Load Global Stylesheet
        theme = get_setting('theme', default='Light')
        if theme == 'Dark':
            dark_theme_path = os.path.join(APP_ROOT_DIR, "resources", "styles", "dark_theme.qss")
            if os.path.exists(dark_theme_path):
                with open(dark_theme_path, "r") as f:
                    app.setStyleSheet(f.read())
            else:
                load_stylesheet_global(app)
        else:
            load_stylesheet_global(app)

        # 7. Setup Translations
        setup_translations(app, current_app_lang, APP_ROOT_DIR)

        # 9. Initialize Default Templates
        initialize_default_templates(CONFIG, APP_ROOT_DIR)
        logging.info("Call to app_setup.initialize_default_templates completed (ensures template files on disk).")

        # --- Coordinated Data Seeding ---
        try:
            logging.info("Attempting to run data seeding if necessary...")
            db_session_for_check = db.connection.get_db_connection()
            if users_crud.is_users_table_empty(db=db_session_for_check):
                logging.info("Users table is empty, running data seeding...")
                run_seed()
                logging.info("Data seeding process via run_seed() completed.")
            else:
                logging.info("Users table is not empty, skipping data seeding.")
            db_session_for_check.close()
        except Exception as e_seed_run:
            logging.error(f"An unexpected error occurred when calling run_seed(): {e_seed_run}", exc_info=True)
        # --- End Coordinated Data Seeding ---

        # --- Startup Dialog Logic ---
        show_setup_prompt_config_value = CONFIG.get("show_initial_setup_on_startup", False)
        first_launch_detected = is_first_launch(APP_ROOT_DIR, CONFIG.get('templates_dir'), CONFIG.get('clients_dir'))
        companies_exist = bool(get_all_companies())

        should_reset_config_flag_after_dialog = False

        if not companies_exist:
            if first_launch_detected or show_setup_prompt_config_value:
                dialog_result_company = QDialog.Accepted
                prompt_dialog = type('obj', (object,), {'use_default_company': True, 'get_company_data': lambda: None})()

                if dialog_result_company == QDialog.Accepted:
                    if prompt_dialog.use_default_company:
                        default_company_data = {
                            "company_name": "My Business", "address": "Not specified", "is_default": True,
                            "logo_path": None, "payment_info": "", "other_info": "Default company created."
                        }
                        new_company_id = add_company(default_company_data)
                        if new_company_id:
                            companies_exist = True
                if show_setup_prompt_config_value and not first_launch_detected:
                    should_reset_config_flag_after_dialog = True

        if should_reset_config_flag_after_dialog:
            CONFIG["show_initial_setup_on_startup"] = False
            save_config(CONFIG)

        # --- Authentication Flow ---
        auth_flow_manager = AuthFlowManager(self.session_manager, splash)
        auth_success, user_info, license_info = auth_flow_manager.execute_auth_flow()

        if auth_success and user_info and license_info:
            # The auth flow manager now handles starting the session.
            # We just need to create the main window.
            self.main_widget = DocumentManager(APP_ROOT_DIR, user_info, license_info, session_manager=self.session_manager)
            self.setCentralWidget(self.main_widget)
            notification_manager = NotificationManager(parent_window=self)
            QApplication.instance().notification_manager = notification_manager
            splash.finish_splash(self)
            self.showMaximized()
        else:
            # AuthFlowManager handled user cancellation or a critical failure.
            # It has already hidden the splash screen. We just need to exit.
            logging.info("Authentication failed or was cancelled. Exiting application.")
            sys.exit(0)

def main():
    # Instantiate the API server manager. Its __init__ registers the shutdown hook.
    api_server_manager = APIServerManager()
    # To start the server (optional, disabled for now):
    # api_server_manager.start_server()

    app = QApplication(sys.argv)
    crm_module = CRMModule()
    crm_module.showMaximized()
    sys.exit(app.exec_())

def get_notification_manager():
    """
    Global accessor for the NotificationManager instance.

    Returns:
        NotificationManager or None: The global NotificationManager instance if it has been set
                                     on the QApplication instance, otherwise None.
    """
    app_instance = QApplication.instance()
    if hasattr(app_instance, 'notification_manager'):
        return app_instance.notification_manager
    logging.warning("NotificationManager not found on QApplication instance.")
    return None

if __name__ == "__main__":
    main()