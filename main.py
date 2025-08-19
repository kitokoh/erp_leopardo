import sys
import os
import logging
from PyQt5.QtWidgets import QApplication, QMessageBox

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from PyQt5.QtWidgets import QDialog
from alembic.config import Config as AlembicConfig
from alembic import command
from app.core.app_setup import setup_logging, APP_ROOT_DIR, CONFIG
from app.db.connection import initialize_engine_and_session, set_db_config
from app.db.db_seed import seed_all_data
from app.views.gui.dialogs.login_dialog import LoginDialog
# from app.views.gui.main_window import DocumentManager # Temporarily disabled for login test
from app.services.auth import authentication

def run_migrations():
    """Finds the alembic.ini file and runs migrations."""
    logging.info("Attempting to run database migrations...")
    try:
        # Construct the path to alembic.ini. It's in the project root, which is where main.py is.
        alembic_ini_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'alembic.ini')
        if not os.path.exists(alembic_ini_path):
            logging.error(f"Alembic config file not found at: {alembic_ini_path}")
            return False

        alembic_cfg = AlembicConfig(alembic_ini_path)

        # Set the database URL for Alembic programmatically
        from app.db.connection import engine
        if engine:
            alembic_cfg.set_main_option('sqlalchemy.url', str(engine.url))
            logging.info(f"Alembic configured to use database: {str(engine.url)}")
        else:
            logging.error("Database engine not initialized. Cannot run migrations.")
            return False

        command.upgrade(alembic_cfg, "head")
        logging.info("Database migrations completed successfully.")
        return True
    except Exception as e:
        logging.critical(f"Failed to run database migrations: {e}", exc_info=True)
        return False

def main():
    """Main function to run the application."""
    # 1. Setup Logging
    setup_logging()
    logging.info("Application starting up...")
    from app.core.config import APP_ROOT_DIR, DATABASE_PATH
    print(f"APP_ROOT_DIR: {APP_ROOT_DIR}")
    print(f"DATABASE_PATH: {DATABASE_PATH}")

    # 2. Load Configuration
    # load_config() is called in app_setup, which is imported.
    # We can directly use the CONFIG object.
    if not CONFIG:
        logging.critical("Failed to load configuration. Exiting.")
        # Need to create a temporary QApplication to show a message box if GUI hasn't started
        temp_app_for_error = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, "Critical Error", "Failed to load configuration. The application cannot start.")
        return

    # 3. Initialize Database
    try:
        # Pass the loaded config to the db connection module
        set_db_config(CONFIG)
        initialize_engine_and_session(CONFIG)
        logging.info("Database engine and session initialized successfully.")
    except Exception as e:
        logging.critical(f"Failed to initialize database: {e}", exc_info=True)
        temp_app_for_error = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, "Database Error", f"Failed to initialize the database: {e}")
        return

    # 4. Run Migrations and Seeding
    if not run_migrations():
        temp_app_for_error = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, "Database Migration Error", "Could not apply database migrations. The application cannot start.")
        return

    try:
        logging.info("Running database seeders...")
        seed_all_data()
        logging.info("Database seeding completed.")
    except Exception as e:
        logging.critical(f"Failed to seed database: {e}", exc_info=True)
        temp_app_for_error = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, "Database Seeding Error", f"Could not seed the database: {e}")
        return


    # 5. Initialize QApplication
    app = QApplication(sys.argv)

    # Set a global exception handler
    def excepthook(exc_type, exc_value, exc_tb):
        logging.critical("Unhandled exception caught by excepthook", exc_info=(exc_type, exc_value, exc_tb))
        QMessageBox.critical(None, "Unhandled Exception", f"A critical error occurred: {exc_value}")
        sys.exit(1)

    sys.excepthook = excepthook


    # 5. Handle Login
    login_dialog = LoginDialog()
    if login_dialog.exec_() == QDialog.Accepted:
        # The dialog's _attempt_login now returns a tuple
        login_output = login_dialog.get_raw_login_output()
        if not login_output:
             QMessageBox.critical(None, "Login Error", "Failed to get login information from the dialog.")
             return

        success, error_message, user_info, license_info = login_output

        if success and user_info:
            logging.info(f"Login successful for user: {user_info.get('username')}")

            # 6. Instantiate and show the Main Window (Temporarily commented out to test login)
            # try:
            #     main_window = DocumentManager(
            #         app_root_dir=APP_ROOT_DIR,
            #         current_user_info=user_info,
            #         current_license_info=license_info,
            #         # session_manager can be added here if needed
            #     )
            #     main_window.show()
            #     logging.info("Main window (DocumentManager) shown.")

            #     # 7. Start Event Loop
            #     sys.exit(app.exec_())
            # except Exception as e:
            #     logging.critical(f"Failed to create or show main window: {e}", exc_info=True)
            #     QMessageBox.critical(None, "Application Error", f"Failed to create the main application window: {e}")

            # For testing, just show a success message and exit
            QMessageBox.information(None, "Login Successful", "Login was successful. The main window is currently disabled for testing.")
            sys.exit(0)

        else:
            logging.warning("Login failed or was cancelled.")
            # No need for a message here as the login dialog already shows one.
    else:
        logging.info("Login dialog was cancelled. Exiting application.")


if __name__ == "__main__":
    main()
