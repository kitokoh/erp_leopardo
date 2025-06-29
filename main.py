# -*- coding: utf-8 -*-
import sys
import os

# Determine project root
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Ensure PROJECT_ROOT is at the beginning of sys.path for consistent module resolution
if PROJECT_ROOT in sys.path:
    # If it's present but not at the start, remove and re-insert at the front
    if sys.path[0] != PROJECT_ROOT:
        sys.path.remove(PROJECT_ROOT)
        sys.path.insert(0, PROJECT_ROOT)
        # Optional: log that it was moved
        # import logging
        # logging.info(f"Moved {PROJECT_ROOT} to the start of sys.path.")
else:
    # If it's not present at all, insert it at the start
    sys.path.insert(0, PROJECT_ROOT)
    # Optional: log that it was added
    # import logging
    # logging.info(f"Added {PROJECT_ROOT} to the start of sys.path.")

# For diagnostics (can be removed or commented out in production)
# print(f"[{os.path.basename(__file__)}] Effective sys.path[0]: {sys.path[0]}")
# print(f"[{os.path.basename(__file__)}] Full sys.path: {sys.path}")


from main_window import DocumentManager # The main application window

from main_window import DocumentManager # The main application window

import logging # For main.py's own logging needs, and for translator parts if setup_logging isn't called first
import icons_rc # Import the compiled resource file
# import subprocess # Removed as API server functions are moved
# import atexit # Removed as API server functions are moved

# Core PyQt5 imports for application execution
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import QLocale, QLibraryInfo, QTranslator, Qt, QSize
from PyQt5.QtGui import QFont, QPixmap, QMovie
from PyQt5.QtCore import QStringListModel

# Imports from project structure
from app_setup import (
    APP_ROOT_DIR, CONFIG,
    setup_logging, load_stylesheet_global, initialize_default_templates
)
from utils import save_config # Changed import from app_config to utils
from utils import is_first_launch, mark_initial_setup_complete
from auth.roles import SUPER_ADMIN
# Import InitialSetupDialog and PromptCompanyInfoDialog
from initial_setup_dialog import InitialSetupDialog, PromptCompanyInfoDialog
from PyQt5.QtWidgets import QDialog # Required for QDialog.Accepted check
# Import specific db functions needed
import db # Added import for db module
from db.db_seed import run_seed
from db import get_all_companies, add_company # Specific imports for company check
from db.cruds import users_crud # Corrected import for users_crud
# from db.cruds.application_settings_crud import get_setting # Removed direct import
# from db.init_schema import initialize_database # This will be db.initialize_database after this change
# from auth.login_window import LoginWindow # Replaced by LoginDialog
from dialogs.login_dialog import LoginDialog # New LoginDialog
from auth import authentication as auth_service # Import the auth service

from PyQt5.QtWidgets import QDialog # Required for QDialog.Accepted check (already present, but good to note)
# from initial_setup_dialog import InitialSetupDialog # Redundant import, already imported above
# import db as db_manager # For db initialization - already imported above, now using 'import db'
from notifications import NotificationManager # Added for notifications
# from db.cruds.users_crud import users_crud_instance # users_crud is used directly by auth_service
from PyQt5.QtWidgets import QMessageBox # Added for error dialog
from PyQt5.QtWidgets import QSplashScreen

import datetime # Added for session timeout
from PyQt5.QtCore import QSettings # Added for Remember Me

# Global variables for session information
CURRENT_SESSION_TOKEN = None
CURRENT_USER_ROLE = None
CURRENT_USER_ID = None
SESSION_START_TIME = None
# Initialize from CONFIG, providing a default if key is missing
# SESSION_TIMEOUT_SECONDS = CONFIG.get("session_timeout_minutes", 30) * 60
SESSION_TIMEOUT_SECONDS = 12 * 30 * 24 * 60 * 60 # Approx 12 months

# Global variable for the API server process (api_server_process) has been moved to api_server_manager.py

# --- DEVELOPMENT/TESTING FLAG ---
# Set to True to bypass the login screen for faster testing.
# WARNING: This will log in as the default admin user with super_admin privileges
# and should ONLY be used for development/testing purposes.
# Ensure this is set to False for production or normal use.
BYPASS_LOGIN_FOR_TESTING = False
# --- End Development/Testing: Bypass Login Flag ---

# Old database initialization block removed as it's now called directly in main()

# start_api_server() and stop_api_server() functions have been moved to api_server_manager.py

def expire_session():
    global CURRENT_SESSION_TOKEN, CURRENT_USER_ROLE, CURRENT_USER_ID, SESSION_START_TIME
    CURRENT_SESSION_TOKEN = None
    CURRENT_USER_ROLE = None
    CURRENT_USER_ID = None
    SESSION_START_TIME = None
    logging.info("Session expired and token/user info cleared.")
    # In a real app, this would likely trigger a re-login UI flow.

def check_session_timeout() -> bool:
    """Checks if the current session has timed out. Returns True if timed out, False otherwise."""
    global CURRENT_SESSION_TOKEN, SESSION_START_TIME, SESSION_TIMEOUT_SECONDS
    if CURRENT_SESSION_TOKEN is None or SESSION_START_TIME is None:
        # No active session or session already marked as expired
        return False # Not "timed out now", but "no valid session"

    elapsed_time = datetime.datetime.now() - SESSION_START_TIME
    if elapsed_time.total_seconds() > SESSION_TIMEOUT_SECONDS:
        logging.info(f"Session timed out. Elapsed: {elapsed_time.total_seconds()}s, Timeout: {SESSION_TIMEOUT_SECONDS}s")
        expire_session()
        return True # Session has timed out
    return False # Session is still valid

def main():
    global CURRENT_SESSION_TOKEN, CURRENT_USER_ROLE, CURRENT_USER_ID, SESSION_START_TIME

    # 1. Configure logging as the very first step.
    setup_logging()
    logging.info("Application starting...")

    # API server start call and atexit registration have been removed.
    # The functions start_api_server() and stop_api_server() remain in the file
    # in case they are used by other parts of the system or for specific operational modes.

    # Initialize database after logging
    db.initialize_database()

    # --- Coordinated Data Seeding ---
    # This block handles the seeding of initial data after the schema is created,
    # using the dedicated seeding module.
    # MOVED EARLIER: run_seed() needs to happen AFTER initialize_database() and BEFORE UI elements try to read seeded settings.
    try:
        logging.info("Attempting to run data seeding if necessary...")
        run_seed() # Call the main seeding function from db_seed.py
        # run_seed() handles its own connection, commit, rollback, and logging.
        logging.info("Data seeding process via run_seed() completed.")
    except Exception as e_seed_run:
        # Catch any unexpected error from run_seed() itself, though it should handle its own.
        logging.error(f"An unexpected error occurred when calling run_seed(): {e_seed_run}", exc_info=True)
        # Depending on severity, might want to sys.exit(1) here if seeding is critical for app function
    # --- End Coordinated Data Seeding ---

    # Log the configured session timeout value
    logging.info(f"Session timeout is set to: {SESSION_TIMEOUT_SECONDS // 60} minutes ({SESSION_TIMEOUT_SECONDS} seconds).")

    # 2. Initialize Database (already done outside main for direct script execution,
    #    but if main could be called from elsewhere without the above block, ensure it's done)
    #    However, the current structure with the top-level if __name__ == "__main__" handles this.

    # 3. Set High DPI Scaling Attributes
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # 4. Create QApplication Instance
    app = QApplication(sys.argv)

    # Display Splash Screen using the new SplashWindow
    from ui.splash_screen import SplashWindow # Import the new class

    # Determine current language for splash screen - NOW SAFE TO CALL db.get_setting
    current_app_lang = QLocale.system().name().split('_')[0] # Default
    try:
        language_code_from_db_for_splash = db.get_setting('user_selected_language')
        if language_code_from_db_for_splash and isinstance(language_code_from_db_for_splash, str) and language_code_from_db_for_splash.strip():
            current_app_lang = language_code_from_db_for_splash.strip()
            logging.info(f"Splash screen language '{current_app_lang}' loaded from database setting.")
        else:
            sys_lang = QLocale.system().name().split('_')[0]
            current_app_lang = CONFIG.get("language", sys_lang if sys_lang in ["en", "fr", "ar"] else "en")
            logging.info(f"Splash screen language '{current_app_lang}' from config/system (DB setting not found or invalid).")
    except Exception as e_splash_lang:
        logging.error(f"Error getting language for splash screen, defaulting. Error: {e_splash_lang}")
        # current_app_lang remains system default or 'en'

    # APP_ROOT_DIR is available here from app_setup import
    splash = SplashWindow(app_root_dir=APP_ROOT_DIR, language_code=current_app_lang)
    splash.show_splash()

    # 5. Set Application Name and Style
    app.setApplicationName("ClientDocManager")
    app.setOrganizationName("SaadiyaManagement") # Added for QSettings consistency
    app.setStyle("Fusion") # Or any other style like "Windows", "GTK+"

    # 6. Set Default Font
    default_font = QFont("Segoe UI", 9)  # Default for Windows
    if sys.platform != "win32":  # Basic platform check for font
        default_font = QFont("Arial", 10) # Or "Helvetica", "DejaVu Sans" etc. for other platforms
    app.setFont(default_font)

    # 7. Load Global Stylesheet
    # load_stylesheet_global is imported from app_setup
    load_stylesheet_global(app) 
    
    # The inline app.setStyleSheet call that was here has been removed.
    # The global stylesheet is now solely loaded by load_stylesheet_global(app)
    # which loads style.qss.

    # 8. Setup Translations
    # Try to get language from DB settings
    # 8. Setup Translations
    language_code_from_db = db.get_setting('user_selected_language') # Use db.get_setting

    if language_code_from_db and isinstance(language_code_from_db, str) and language_code_from_db.strip():
        language_code = language_code_from_db.strip()
        logging.info(f"Language '{language_code}' loaded from database setting.")
    else:
        default_lang = QLocale.system().name().split('_')[0]
        language_code = CONFIG.get("language", default_lang if default_lang in ["en", "fr"] else "en") # Fallback to 'en' if system lang not supported
        if language_code_from_db is None:
            logging.info(f"Language '{language_code}' loaded from config/system locale (DB setting 'user_selected_language' not found).")
        else: # Empty string or not a string
            logging.warning(f"Language '{language_code}' loaded from config/system locale (DB setting 'user_selected_language' was invalid: '{language_code_from_db}'). Defaulting to '{language_code}'.")

    # Load application translations
    # First, try to load from the language-specific directory (e.g., translations/qm/fr/main.qm)
    app_translator = QTranslator()
    translation_filename = "main.qm" # Assuming your QM file is named main.qm
    lang_spec_translation_path = os.path.join(APP_ROOT_DIR, "translations", "qm", language_code, translation_filename)

    if os.path.exists(lang_spec_translation_path):
        if app_translator.load(lang_spec_translation_path):
            app.installTranslator(app_translator)
            logging.info(f"Successfully loaded and installed application translation: {lang_spec_translation_path}")
        else:
            logging.warning(f"Failed to load application translation from {lang_spec_translation_path}. Error: {app_translator.errorString()}")
    else:
        # Fallback to loading from the general qm directory (e.g., translations/qm/fr.qm or en.qm)
        # This might be useful if you don't use subdirectories per language for qm files.
        # However, current structure implies subdirectories.
        logging.warning(f"Application translation file not found at specific path: {lang_spec_translation_path}. Trying general path if applicable or skipping.")
        # Example of a more general path (adjust if your structure is different):
        # general_translation_path = os.path.join(APP_ROOT_DIR, "translations", "qm", f"{language_code}.qm")
        # if os.path.exists(general_translation_path):
        #    if app_translator.load(general_translation_path):
        #        app.installTranslator(app_translator)
        #        logging.info(f"Successfully loaded and installed application translation from general path: {general_translation_path}")
        #    else:
        #        logging.warning(f"Failed to load application translation from general path {general_translation_path}. Error: {app_translator.errorString()}")
        # else:
        #    logging.warning(f"No application translation file found for language '{language_code}'.")


    # Load Qt base translations
    qt_translator = QTranslator()
    qt_translation_path_base = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
    if qt_translator.load(QLocale(language_code), "qtbase", "_", qt_translation_path_base):
        app.installTranslator(qt_translator)
        logging.info(f"Loaded Qt base translations for {language_code} from {qt_translation_path_base}")
    else:
        # Try a more generic locale if the specific one (e.g., fr_FR) fails
        generic_locale_name = language_code.split('_')[0]
        if generic_locale_name != language_code: # Avoid redundant logging if already generic
            logging.info(f"Trying generic Qt base translations for {generic_locale_name} from {qt_translation_path_base}")
            if qt_translator.load(QLocale(generic_locale_name), "qtbase", "_", qt_translation_path_base):
                app.installTranslator(qt_translator)
                logging.info(f"Loaded generic Qt base translations for {generic_locale_name} from {qt_translation_path_base}")
            else:
                logging.warning(f"Failed to load Qt base translations for {language_code} or {generic_locale_name} from {qt_translation_path_base}")
        else:
            logging.warning(f"Failed to load Qt base translations for {language_code} from {qt_translation_path_base}")

    # 9. Initialize Default Templates (after DB and CONFIG are ready)
    # initialize_default_templates is imported from app_setup
    # This function is now responsible for ensuring default template FILES (Excel, general HTML) exist on disk.
    # Database seeding for templates is handled by db_manager.seed_initial_data.
    initialize_default_templates(CONFIG, APP_ROOT_DIR)
    logging.info("Call to app_setup.initialize_default_templates completed (ensures template files on disk).")

    # --- Startup Dialog Logic ---
    show_setup_prompt_config_value = CONFIG.get("show_initial_setup_on_startup", False)
    # Use CONFIG for directory paths in is_first_launch
    first_launch_detected = is_first_launch(APP_ROOT_DIR, CONFIG.get('templates_dir'), CONFIG.get('clients_dir'))
    companies_exist = bool(db.get_all_companies()) # Check once

    should_reset_config_flag_after_dialog = False

    if first_launch_detected:
        logging.info("Application detected first launch. InitialSetupDialog logic was previously commented out and has been removed.")
        # The original InitialSetupDialog instantiation and exec_() call were here.
        # If first_launch_detected is true, mark_initial_setup_complete would have been called on dialog acceptance.
        # For now, we assume that if this dialog was critical, its functionality is either deprecated
        # or handled elsewhere. If it needs to be restored, this is the section.
        # We will still re-check companies_exist after this block if first_launch was true.
        mark_initial_setup_complete(APP_ROOT_DIR, CONFIG.get('templates_dir'), CONFIG.get('clients_dir'))
        logging.info("Initial setup (first launch marker) marked as complete.")
        companies_exist = bool(db.get_all_companies()) # Re-check companies after setup

    # Now, handle the PromptCompanyInfoDialog based on company existence and the flag
    if not companies_exist:
        if first_launch_detected or show_setup_prompt_config_value: # Show if first launch OR if flag is true
            logging.info("No companies found and/or setup prompt explicitly enabled. Proceeding with logic for default company creation if applicable.")
            # The original PromptCompanyInfoDialog instantiation and exec_() call were here.
            # The following logic simulates an "accepted" dialog that opts for a default company.
            # This preserves the behavior of creating a default company if none exist
            # and either it's the first launch or the config flag is set.

            # Simulate conditions that would lead to default company creation
            # This replaces the simulated dialog object and its acceptance.
            # The key logic is to create a default company if 'use_default_company' path was taken.
            # We assume 'use_default_company' is the desired path if no actual dialog is shown.

            # Directly proceed to default company creation logic:
            logging.info("Attempting to add a default company as no companies exist and conditions are met.")
            default_company_data = {
                "company_name": "My Business", "address": "Not specified", "is_default": True,
                "logo_path": None, "payment_info": "", "other_info": "Default company auto-created."
            }
            new_company_id = add_company(default_company_data)
            if new_company_id:
                logging.info(f"Default company 'My Business' added with ID: {new_company_id}.")
                companies_exist = True # Update companies_exist status
            else:
                logging.error("Failed to add default company.")
            # The 'else' branch for user-entered company data (from the simulated dialog) is removed
            # as there's no dialog interaction.


            # If the prompt was shown because of the config flag (and not strictly first_launch path that also sets it)
            if show_setup_prompt_config_value and not first_launch_detected:
                should_reset_config_flag_after_dialog = True
        else:
            logging.info("No companies found, but setup prompt is not enabled by config and not first launch. Skipping company creation.")
    else: # Companies exist
        logging.info("Companies found in the database. No need to prompt for company info now.")
        # If companies exist, but the flag was true, it implies the user wanted to see the prompt (even if not strictly necessary).
        # Reset it as the condition (no companies) for the prompt to be useful wasn't met, or it was already met.
        if show_setup_prompt_config_value:
             should_reset_config_flag_after_dialog = True


    if should_reset_config_flag_after_dialog:
        logging.info("Resetting 'show_initial_setup_on_startup' flag to False.")
        CONFIG["show_initial_setup_on_startup"] = False
        save_config(CONFIG)

    proceed_to_main_app = False # Initialize before bypass and remember me

    # --- Development/Testing: Bypass Login ---
    # BYPASS_LOGIN_FOR_TESTING flag is removed; login is now mandatory.
    # If bypass is needed for development, it should be handled by temporarily
    # modifying the login logic or providing default credentials.

    # 10. Authentication Flow
    # QSettings for "Remember Me" is not implemented in this phase.
    # Login will be required each time.

    logged_in_user_info = None # To store user details after successful login

    # --- Remember Me - Attempt Auto Login ---
    remembered_username = auth_service.get_remembered_user()
    if remembered_username:
        logging.info(f"Attempting auto-login for remembered user: {remembered_username}")
        # In a real token system, we'd validate the token here.
        # For this simplified version, we fetch user details directly.
        # This assumes the user still exists and is active.
        user_details = users_crud.get_user_by_username(remembered_username) # Corrected usage

        if user_details and user_details.get('is_active'):
            auth_service.set_current_user(user_details) # Set the user as current
            logged_in_user_info = user_details
            proceed_to_main_app = True
            logging.info(f"Auto-login successful for user: {remembered_username}")
            SESSION_START_TIME = datetime.datetime.now() # Start session timer
        else:
            logging.warning(f"Auto-login failed for remembered user: {remembered_username}. User not found or inactive. Clearing preference.")
            auth_service.clear_remember_me_preference()
            proceed_to_main_app = False # Fallback to manual login
    else:
        proceed_to_main_app = False # No remembered user, proceed to manual login

    if not proceed_to_main_app: # If auto-login didn't happen or failed
        while True: # Loop until successful login or explicit exit
            login_dialog = LoginDialog()
            if login_dialog.exec_() == QDialog.Accepted:
                user_data_from_dialog = login_dialog.get_user_data() # This is already the full user_info from auth_service.login
                if user_data_from_dialog:
                    logged_in_user_info = user_data_from_dialog # Already set by auth_service.login and retrieved
                    if logged_in_user_info: # Should always be true if user_data_from_dialog is not None
                        logging.info(f"Manual login successful. User: {logged_in_user_info.get('username')}, Role: {logged_in_user_info.get('role_name')}")
                        # Save remember me preference based on checkbox in LoginDialog
                        # This is now handled inside auth_service.login based on the 'remember_me' param
                        # auth_service.save_remember_me_preference(logged_in_user_info['username'], login_dialog.is_remember_me_checked())
                        SESSION_START_TIME = datetime.datetime.now() # Start session timer
                        proceed_to_main_app = True
                        break # Exit login loop
                    else:
                        logging.error("Login dialog accepted, but no user data found in auth_service after manual login. Critical error.")
                        QMessageBox.critical(None, "Erreur Critique de Connexion", "Impossible de récupérer les informations utilisateur après la connexion.")
                        splash.hide()
                        sys.exit(1)
                else:
                    logging.error("Login dialog accepted, but get_user_data() returned None from manual login.")
                    QMessageBox.critical(None, "Erreur de Connexion", "Échec de la récupération des données utilisateur.")
            else: # LoginDialog was cancelled or closed
                logging.warning("Login dialog was cancelled or closed by the user. Exiting application.")
                splash.hide()
                sys.exit(0)

    if proceed_to_main_app and logged_in_user_info:
        # Pass the full user_info dictionary to DocumentManager
        main_window = DocumentManager(APP_ROOT_DIR, logged_in_user_info)

        # Setup Notification Manager
        # Ensure 'app' is the QApplication instance, available in this scope
        notification_manager = NotificationManager(parent_window=main_window)
        QApplication.instance().notification_manager = notification_manager

        main_window.show()
        splash.finish_splash(main_window) # Use the correct method in SplashWindow
        logging.info("Main window shown. Application is running.")
        sys.exit(app.exec_())
    else:
        # This path should ideally not be reached if logic is correct,
        # as either proceed_to_main_app is true or sys.exit() was called.
        logging.error("Fatal error in authentication flow. Application cannot start.")
        splash.hide() # Ensure splash screen is hidden on error
        sys.exit(1)

    # The following block seems redundant due to the logic above,
    # but if it's reached, ensure splash screen is handled.
    # Consider refactoring to avoid this redundancy.
    # login_dialog = LoginWindow() # Create LoginWindow instance
    # login_result = login_dialog.exec_() # Show login dialog modally
    #
    # if login_result == QDialog.Accepted:
    #     session_token = login_dialog.get_session_token()
    #     logged_in_user = login_dialog.get_current_user()
    #
    #     CURRENT_SESSION_TOKEN = session_token
    #     if logged_in_user:
    #         CURRENT_USER_ROLE = logged_in_user.get('role')
    #         CURRENT_USER_ID = logged_in_user.get('user_id')
    #         SESSION_START_TIME = datetime.datetime.now()
    #         logging.info(f"Login successful. User: {logged_in_user.get('username')}, Role: {CURRENT_USER_ROLE}, Token: {CURRENT_SESSION_TOKEN}, Session started: {SESSION_START_TIME}")
    #     else:
    #         logging.error("Login reported successful, but no user data retrieved. Exiting.")
    #         splash.hide()
    #         sys.exit(1)
    #
    #     main_window = DocumentManager(APP_ROOT_DIR, CURRENT_USER_ID)
    #     main_window.show()
    #     splash.finish(main_window)
    #     logging.info("Main window shown. Application is running.")
    #
    #     sys.exit(app.exec_())
    # else:
    #     logging.info("Login failed or cancelled. Exiting application.")
    #     splash.hide()
    #     sys.exit()

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