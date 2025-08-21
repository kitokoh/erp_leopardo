import sys
import os
import logging
from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import from the new core location
from app.core.app_setup import setup_logging, APP_ROOT_DIR, CONFIG
from app.core.initializer import initialize_database
from app.services.auth.login_window import LoginWindow as LoginDialog
from app.views.gui.main_window import DocumentManager
from app.services.auth import authentication
from app.telemetry import init_telemetry

def main():
    """Main function to run the application."""
    # 1. Setup Logging
    setup_logging()
    logging.info("Application starting up...")

    # 2. Initialize Database (This now handles everything: config, migrations, seeding)
    try:
        initialize_database(CONFIG, APP_ROOT_DIR)
        logging.info("Database initialization process completed successfully.")
    except SystemExit as e:
        # The initializer calls sys.exit on critical errors, so we just let it exit.
        logging.critical("Application startup aborted due to critical error during database initialization.")
        return # Exit the main function
    except Exception as e:
        logging.critical(f"An unhandled exception occurred during database initialization: {e}", exc_info=True)
        # Create a temporary app to show the message box if the main app hasn't started
        temp_app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, "Database Error", f"A critical error occurred during database setup: {e}")
        return

    # 2.5 Initialize Telemetry
    init_telemetry()
    logging.info("Telemetry manager initialized.")

    # 3. Initialize QApplication
    app = QApplication(sys.argv)

    # Set a global exception handler
    def excepthook(exc_type, exc_value, exc_tb):
        logging.critical("Unhandled exception caught by excepthook", exc_info=(exc_type, exc_value, exc_tb))
        QMessageBox.critical(None, "Unhandled Exception", f"A critical error occurred: {exc_value}")
        sys.exit(1)

    sys.excepthook = excepthook

    # 4. Handle Login
    login_dialog = LoginDialog()
    if login_dialog.exec_() == QDialog.Accepted:
        login_output = login_dialog.get_raw_login_output()
        if not login_output:
             QMessageBox.critical(None, "Login Error", "Failed to get login information from the dialog.")
             return

        success, error_message, user_info, license_info = login_output

        if success and user_info:
            logging.info(f"Login successful for user: {user_info.get('username')}")

            # 5. Instantiate and show the Main Window
            try:
                main_window = DocumentManager(
                    app_root_dir=APP_ROOT_DIR,
                    current_user_info=user_info,
                    current_license_info=license_info,
                )
                main_window.show()
                logging.info("Main window (DocumentManager) shown.")

                # 6. Start Event Loop
                sys.exit(app.exec_())
            except Exception as e:
                logging.critical(f"Failed to create or show main window: {e}", exc_info=True)
                QMessageBox.critical(None, "Application Error", f"Failed to create the main application window: {e}")
        else:
            logging.warning("Login failed or was cancelled.")
    else:
        logging.info("Login dialog was cancelled. Exiting application.")


if __name__ == "__main__":
    main()
