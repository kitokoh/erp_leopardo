# -*- coding: utf-8 -*-
import sys
import os
import logging
import atexit

# Core PyQt5 imports for application execution
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QLocale
# Determine project root and add it to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Imports from project structure after path setup
from .core.app_setup import (
    APP_ROOT_DIR, CONFIG,
    setup_logging, load_stylesheet_global, initialize_default_templates
)
from .utils import save_config, is_first_launch
from . import db
from .notifications import NotificationManager
from .views.gui.main_window import DocumentManager
from .services.auth.session_manager import SessionManager
from .core.initializer import initialize_database, setup_qt_application, setup_translations
from .services.auth.auth_flow_manager import AuthFlowManager

class CRMModule(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | self.windowFlags())
        self.setWindowTitle("CRM Module")
        self.setGeometry(100, 100, 1200, 800)
        self.main_widget = None
        self.session_manager = None

def main():
    # 1. Configure logging as the very first step.
    setup_logging()
    logging.info("Application starting...")
    atexit.register(logging.shutdown)
    logging.info("logging.shutdown registered with atexit.")

    # 2. Setup database connection
    logging.info("Setting up database connection.")
    if hasattr(db, 'connection') and hasattr(db.connection, 'set_db_config'):
        db.connection.set_db_config(CONFIG)
    else:
        logging.error("Could not find db.connection.set_db_config. DB calls might fail.")
    initialize_database(CONFIG, PROJECT_ROOT)

    # --- Import DB-dependent modules AFTER initialization ---
    from .db.db_seed import seed_all_data as run_seed
    from .db.seeders.hidroguc_product_seeder import seed_hidroguc_products as seed_only_hidroguc_products
    from .db.connection import get_db_connection
    from .db.cruds.misc.application_settings_crud import get_setting
    from .db.cruds.users import users_crud
    from .db.cruds.misc.companies_crud import get_all_companies, add_company
    from .document_generator import context_builder as doc_gen_context_builder
    from .db.cruds.users import user_session_tokens_crud, password_reset_tokens_crud
    from .ui.splash_screen import SplashWindow

    # 3. Seed Hidroguc products
    db_session_for_hidroguc = None
    try:
        db_session_for_hidroguc = get_db_connection()
        if db_session_for_hidroguc:
            seed_only_hidroguc_products(db=db_session_for_hidroguc, logger_passed=logging.getLogger(__name__))
            db_session_for_hidroguc.commit()
    except Exception as e:
        logging.error(f"An error occurred during Hidroguc product seeding: {e}", exc_info=True)
        if db_session_for_hidroguc:
            db_session_for_hidroguc.rollback()
    finally:
        if db_session_for_hidroguc:
            db_session_for_hidroguc.close()

    # 4. Configure document generator
    if hasattr(doc_gen_context_builder, 'set_document_generator_config'):
        doc_gen_context_builder.set_document_generator_config(CONFIG)

    # 5. Token Cleanup on Startup
    conn_cleanup = None
    try:
        conn_cleanup = get_db_connection()
        if conn_cleanup:
            user_session_tokens_crud.cleanup_expired_tokens(conn_cleanup)
            password_reset_tokens_crud.cleanup_expired_or_used_tokens(conn_cleanup)
            conn_cleanup.commit()
    except Exception as e:
        logging.error(f"Error during token cleanup on startup: {e}", exc_info=True)
        if conn_cleanup: conn_cleanup.rollback()
    finally:
        if conn_cleanup: conn_cleanup.close()

    # 6. Initialize SessionManager
    timeout_minutes = 12 * 30 * 24 * 60  # Approx 12 months
    session_manager = SessionManager(timeout_minutes=timeout_minutes)

    # 7. Create and setup QApplication
    app = QApplication(sys.argv)
    setup_qt_application(app)

    # 8. Determine language and setup translations
    language_code_from_db = get_setting('user_selected_language')
    sys_lang = QLocale.system().name().split('_')[0]
    current_app_lang = language_code_from_db.strip() if language_code_from_db else CONFIG.get("language", sys_lang if sys_lang in ["en", "fr", "ar"] else "en")
    setup_translations(app, current_app_lang, APP_ROOT_DIR)

    # 9. Show Splash Screen
    splash = SplashWindow(app_root_dir=APP_ROOT_DIR, language_code=current_app_lang)
    splash.show_splash()

    # 10. Load Stylesheet
    theme = get_setting('theme', default='Light')
    load_stylesheet_global(app, theme)

    # 11. Initialize Default Templates
    initialize_default_templates(CONFIG, APP_ROOT_DIR)

    # 12. Coordinated Data Seeding
    db_session_for_check = db.connection.get_db_connection()
    if users_crud.is_users_table_empty(db=db_session_for_check):
        run_seed()
    db_session_for_check.close()

    # 13. Startup Dialog Logic
    companies_exist = bool(get_all_companies())
    if not companies_exist:
        # Simplified logic for headless/test environment
        default_company_data = {"company_name": "My Business", "address": "Not specified", "is_default": True}
        add_company(default_company_data)

    # 14. Authentication Flow
    auth_flow_manager = AuthFlowManager(session_manager, splash)
    auth_success, user_info, license_info = auth_flow_manager.execute_auth_flow()

    if auth_success and user_info and license_info:
        main_window = CRMModule()
        main_window.main_widget = DocumentManager(APP_ROOT_DIR, user_info, license_info, session_manager=session_manager)
        main_window.setCentralWidget(main_window.main_widget)
        QApplication.instance().notification_manager = NotificationManager(parent_window=main_window)
        splash.finish_splash(main_window)
        main_window.showMaximized()
        sys.exit(app.exec_())
    else:
        logging.info("Authentication failed or was cancelled. Exiting application.")
        sys.exit(0)

def get_notification_manager():
    app_instance = QApplication.instance()
    return getattr(app_instance, 'notification_manager', None)

if __name__ == "__main__":
    main()