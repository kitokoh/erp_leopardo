# -*- coding: utf-8 -*-
import sys
import os

# Determine project root and add it to sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
elif sys.path[0] != PROJECT_ROOT:
    # If it's in sys.path but not at the start, move it to the start
    sys.path.remove(PROJECT_ROOT)
    sys.path.insert(0, PROJECT_ROOT)

# Ensure this debug print is AFTER the sys.path modification and BEFORE any project imports
# print(f"DEBUG main.py: Initial PROJECT_ROOT: {PROJECT_ROOT}")
# print(f"DEBUG main.py: sys.path after modification in main.py: {sys.path}")
# print(f"DEBUG main.py: current working directory: {os.getcwd()}")

# Now, other imports can follow
import logging # For main.py's own logging needs, and for translator parts if setup_logging isn't called first
import icons_rc # Import the compiled resource file
import subprocess # Added for starting API server
import atexit # Added for stopping API server on exit

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
from settings.initial_setup_dialog import InitialSetupDialog, PromptCompanyInfoDialog
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
from user_profile_management.database_setup import create_tables as create_user_profile_tables
from user_profile_management.database_setup import seed_data as seed_user_profile_data

from PyQt5.QtWidgets import QDialog # Required for QDialog.Accepted check (already present, but good to note)
# from initial_setup_dialog import InitialSetupDialog # Redundant import, already imported above
# import db as db_manager # For db initialization - already imported above, now using 'import db'
from notifications import NotificationManager # Added for notifications
# from db.cruds.users_crud import users_crud_instance # users_crud is used directly by auth_service
from PyQt5.QtWidgets import QMessageBox # Added for error dialog
from PyQt5.QtWidgets import QSplashScreen

# --- Direct Re-calculation and Re-insertion of Project Root before gui.main_window import ---
# This is a more direct attempt to ensure the path is correct right before the import.
# os and sys modules should already be imported at the top of main.py.
current_file_path_for_gui_import = os.path.abspath(__file__)
project_root_calculated_for_gui_import = os.path.dirname(current_file_path_for_gui_import)

if project_root_calculated_for_gui_import not in sys.path:
    sys.path.insert(0, project_root_calculated_for_gui_import)
    logging.debug(f"main.py (PRE-GUI IMPORT): Inserted project root {project_root_calculated_for_gui_import}. New sys.path: {sys.path}")
elif sys.path[0] != project_root_calculated_for_gui_import:
    if project_root_calculated_for_gui_import in sys.path: # Check before removing
        sys.path.remove(project_root_calculated_for_gui_import)
    sys.path.insert(0, project_root_calculated_for_gui_import)
    logging.debug(f"main.py (PRE-GUI IMPORT): Moved project root {project_root_calculated_for_gui_import} to start. New sys.path: {sys.path}")
else:
    logging.debug(f"main.py (PRE-GUI IMPORT): Project root {project_root_calculated_for_gui_import} already correctly at sys.path[0]. Current sys.path: {sys.path}")
# --- End Direct Re-calculation ---

# PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__)) # Redundant: PROJECT_ROOT already defined and sys.path modified at the top
# if PROJECT_ROOT not in sys.path: # Redundant
#     sys.path.insert(0, PROJECT_ROOT) # Redundant

# logging.debug(f"main.py: sys.path is now: {sys.path}") # Redundant: sys.path printed after initial modification
# logging.debug(f"main.py: current working directory is: {os.getcwd()}") # Redundant: CWD printed after initial modification

# --- Le reste de vos imports dans main.py commence ici ---
# Par exemple:
# from some_module import something
# from gui.main_window import DocumentManager 
from gui.main_window import DocumentManager
import datetime # Added for session timeout
from PyQt5.QtCore import QSettings # Added for Remember Me

# Imports pour la gestion de licence
from db.connection import get_db_connection
from license_management import manager as license_manager
from license_management.ui import LicenseDialog # Décommenté

# Global variables for session information
CURRENT_SESSION_TOKEN = None
CURRENT_USER_ROLE = None
CURRENT_USER_ID = None
SESSION_START_TIME = None
# Initialize from CONFIG, providing a default if key is missing
# SESSION_TIMEOUT_SECONDS = CONFIG.get("session_timeout_minutes", 30) * 60
SESSION_TIMEOUT_SECONDS = 12 * 30 * 24 * 60 * 60 # Approx 12 months

# Global variable for the API server process
api_server_process = None

# --- DEVELOPMENT/TESTING FLAG ---
# Set to True to bypass the login screen for faster testing.
# WARNING: This will log in as the default admin user with super_admin privileges
# and should ONLY be used for development/testing purposes.
# Ensure this is set to False for production or normal use.
BYPASS_LOGIN_FOR_TESTING = False
# --- End Development/Testing: Bypass Login Flag ---

# Old database initialization block removed as it's now called directly in main()

def start_api_server():
    """Starts the FastAPI server as a subprocess."""
    global api_server_process
    try:
        # Ensure the command is correctly formatted.
        # If 'api.main' is a module, uvicorn needs to be able to find it.
        # This might require adjusting PYTHONPATH or running from a specific directory.
        # For now, assume 'api.main:app' is discoverable by uvicorn in the current environment.
        command = ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

        # Using Popen for non-blocking execution.
        # Ensure that the subprocess's stdout/stderr are handled appropriately
        # to prevent blocking or deadlocks if they fill up.
        # For basic logging, we can capture them or redirect to DEVNULL if not needed.
        api_server_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Try to communicate with the process to get output.
        # This will wait for the process to terminate if it does so quickly.
        # If it's a long-running server, communicate() won't return until it's done,
        # so we need a timeout for the initial check.
        try:
            stdout, stderr = api_server_process.communicate(timeout=2) # Wait 2 seconds for initial output / quick failure
            # If communicate() returns, the process has terminated.
            logging.error(f"FastAPI server process terminated unexpectedly. Exit code: {api_server_process.returncode}")
            stdout_str = stdout.decode(errors='replace').strip()
            stderr_str = stderr.decode(errors='replace').strip()
            if stdout_str:
                logging.error(f"FastAPI Server Stdout:\n{stdout_str}")
            if stderr_str:
                logging.error(f"FastAPI Server Stderr:\n{stderr_str}")
            api_server_process = None # Reset as it failed
        except subprocess.TimeoutExpired:
            # This is the expected path for a successfully started server.
            # The process is still running after the timeout.
            if api_server_process.poll() is None:
                logging.info(f"FastAPI server process started successfully with PID: {api_server_process.pid}. Command: {' '.join(command)}")
                # Optionally, you could start threads here to monitor api_server_process.stdout and api_server_process.stderr
                # and log their output in real-time if continuous logging is needed.
            else:
                # Process terminated after TimeoutExpired was raised but before poll() - less likely but possible
                stdout, stderr = api_server_process.communicate() # get any final output
                logging.error(f"FastAPI server process failed to start or terminated shortly after. Exit code: {api_server_process.returncode}")
                stdout_str = stdout.decode(errors='replace').strip()
                stderr_str = stderr.decode(errors='replace').strip()
                if stdout_str:
                    logging.error(f"FastAPI Server Stdout (after timeout check):\n{stdout_str}")
                if stderr_str:
                    logging.error(f"FastAPI Server Stderr (after timeout check):\n{stderr_str}")
                api_server_process = None
        except Exception as e_comm:
            # Other errors during communicate
            logging.error(f"Error communicating with FastAPI server process: {e_comm}", exc_info=True)
            if api_server_process.poll() is not None:
                logging.error(f"FastAPI server process also terminated with exit code: {api_server_process.returncode}")
            api_server_process = None


    except FileNotFoundError:
        logging.error("Error starting FastAPI server: 'uvicorn' command not found. Ensure uvicorn is installed and in PATH.")
        api_server_process = None
    except Exception as e:
        logging.error(f"An unexpected error occurred while starting the FastAPI server process: {e}", exc_info=True)
        api_server_process = None

def stop_api_server():
    """Stops the FastAPI server process if it is running."""
    global api_server_process
    if api_server_process and api_server_process.poll() is None: # Check if process exists and is running
        logging.info(f"Attempting to terminate API server process with PID: {api_server_process.pid}")
        try:
            api_server_process.terminate() # Send SIGTERM
            try:
                # Wait for a few seconds for graceful shutdown
                api_server_process.wait(timeout=5)
                logging.info(f"API server process with PID: {api_server_process.pid} terminated.")
            except subprocess.TimeoutExpired:
                logging.warning(f"API server process with PID: {api_server_process.pid} did not terminate in time. Sending SIGKILL.")
                api_server_process.kill() # Send SIGKILL
                api_server_process.wait() # Wait for kill to complete
                logging.info(f"API server process with PID: {api_server_process.pid} killed.")
            except Exception as e_wait: # Catch other errors during wait (e.g. process already died)
                logging.info(f"Error waiting for API server process {api_server_process.pid} to terminate: {e_wait}. It might have already exited.")
        except ProcessLookupError: # Raised if process does not exist (e.g. already terminated)
            logging.info(f"API server process with PID: {api_server_process.pid} not found. Likely already stopped.")
        except Exception as e:
            logging.error(f"Error terminating/killing API server process with PID: {api_server_process.pid}: {e}", exc_info=True)
    elif api_server_process: # Process exists but poll() is not None, meaning it already terminated
        logging.info(f"API server process with PID: {api_server_process.pid} was already stopped (return code: {api_server_process.returncode}).")
    else: # api_server_process is None
        logging.info("No API server process to stop (api_server_process is None).")

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
    logging.info(f"CONFIGURED DATABASE_PATH: {CONFIG.get('database_path', 'NOT FOUND IN CONFIG')}")

    # Start the API server - Commented out as per user request for local PyQt app
    # start_api_server()
    # logging.info("API server auto-start is disabled for local PyQt execution.") # Log message removed


    # Register the function to stop the API server on application exit
    # This ensures that if start_api_server() actually started a process,
    # we attempt to clean it up.
    atexit.register(stop_api_server)
    
    # Register logging.shutdown() to be called on exit to properly close handlers
    atexit.register(logging.shutdown)
    logging.info("logging.shutdown registered with atexit.")

    # Check if the database file already exists.
    db_path = CONFIG.get('database_path')
    db_exists = os.path.exists(db_path)

    # Initialize database after logging and API server start attempt
    if not db_exists:
        db.initialize_database(CONFIG) # Pass CONFIG here

    # Apply Alembic migrations
    try:
        from alembic.config import Config as AlembicConfig
        from alembic import command as alembic_command
        # os is imported globally, no need for local import here.

        # Construct the path to alembic.ini relative to the project root
        # PROJECT_ROOT is defined at the top of main.py
        alembic_ini_path = os.path.join(PROJECT_ROOT, 'alembic.ini')

        if not os.path.exists(alembic_ini_path):
            logging.error(f"Alembic configuration file not found at: {alembic_ini_path}")
        else:
            logging.info(f"Found Alembic config at: {alembic_ini_path}")
            alembic_cfg = AlembicConfig(alembic_ini_path)

            # Set the script location programmatically to avoid issues with relative paths in alembic.ini
            # when alembic is called from a different directory.
            # The 'here' variable in alembic.ini refers to the location of alembic.ini itself.
            # So, if alembic.ini correctly sets script_location = %(here)s/alembic, this might not be strictly needed
            # but can make it more robust if alembic commands are run from various places.
            # alembic_cfg.set_main_option("script_location", os.path.join(PROJECT_ROOT, "alembic"))

            # --- DEBUG: Check if DB file exists before Alembic upgrade ---
            db_path_for_alembic_check = CONFIG.get('database_path')
            if db_path_for_alembic_check and os.path.exists(db_path_for_alembic_check):
                logging.info(f"DEBUG_MAIN: Database file {db_path_for_alembic_check} EXISTS before Alembic upgrade. Size: {os.path.getsize(db_path_for_alembic_check)} bytes.")
            else:
                logging.info(f"DEBUG_MAIN: Database file {db_path_for_alembic_check} DOES NOT EXIST before Alembic upgrade.")
            # --- END DEBUG ---

            logging.info("Attempting to upgrade database schema to head using Alembic...")
            # logging.warning("DEBUG_MAIN: ALEMBIC UPGRADE TEMPORARILY COMMENTED OUT FOR TESTING.")
            alembic_command.stamp(alembic_cfg, "head")
            alembic_command.upgrade(alembic_cfg, "head") # RESTORED
            logging.info("Alembic upgrade head command completed.")
    except ImportError:
        logging.error("Alembic is not installed. Database migrations will be skipped. The application may not function correctly.")
        QMessageBox.critical(None, "Erreur Critique d'Initialisation",
                             "Alembic n'est pas installé. Les migrations de base de données ne peuvent pas être exécutées.\n"
                             "Veuillez installer Alembic (ex: pip install alembic) et redémarrer l'application.\n"
                             "L'application va maintenant se fermer.")
        sys.exit(1) # Exit if Alembic is not installed
    except Exception as e_alembic:
        logging.error(f"An error occurred during Alembic migration: {e_alembic}", exc_info=True)
        QMessageBox.critical(None, "Erreur de Migration de Base de Données",
                             f"Une erreur est survenue lors de la migration de la base de données avec Alembic:\n{e_alembic}\n"
                             "L'application ne peut pas continuer et va se fermer.")
        sys.exit(1) # Exit if migration fails

    # Set the database configuration for db.connection module
    # This must be done after app_setup.CONFIG is loaded and db structure might be initialized
    if hasattr(db, 'connection') and hasattr(db.connection, 'set_db_config'):
        db.connection.set_db_config(CONFIG)
        logging.info("main.py: db.connection.set_db_config(CONFIG) called.")
    else:
        logging.error("main.py: Could not find db.connection.set_db_config. DB calls might fail.")

    # Set the configuration for document_generator.context_builder
    try:
        from document_generator import context_builder as doc_gen_context_builder
        if hasattr(doc_gen_context_builder, 'set_document_generator_config'):
            doc_gen_context_builder.set_document_generator_config(CONFIG)
            logging.info("main.py: document_generator.context_builder.set_document_generator_config(CONFIG) called.")
        else:
            logging.error("main.py: Could not find document_generator.context_builder.set_document_generator_config.")
    except ImportError:
        logging.error("main.py: Failed to import document_generator.context_builder to set its config.")
    except Exception as e_docgen_conf:
        logging.error(f"main.py: Error setting document_generator config: {e_docgen_conf}", exc_info=True)


    # --- Create all tables ---
    from db.connection import Base as MainBase, engine as actual_main_engine
    if MainBase and actual_main_engine:
        logging.info("main.py: Creating all tables from MainBase metadata...")
        MainBase.metadata.create_all(bind=actual_main_engine)
        logging.info("main.py: All tables from MainBase metadata created.")
    else:
        logging.error("main.py: MainBase or actual_main_engine not available. Cannot create tables.")

    # --- Coordinated Data Seeding ---
    # This block handles the seeding of initial data after the schema is created,
    # using the dedicated seeding module.
    # MOVED EARLIER: run_seed() needs to happen AFTER initialize_database() and BEFORE UI elements try to read seeded settings.
    try:
        logging.info("Attempting to run data seeding if necessary...")
        if not db_exists:
            run_seed() # Call the main seeding function from db_seed.py
            # run_seed() handles its own connection, commit, rollback, and logging.
            logging.info("Data seeding process via run_seed() completed.")
        else:
            logging.info("Database already exists, skipping seeding.")
    except Exception as e_seed_run:
        # Catch any unexpected error from run_seed() itself, though it should handle its own.
        logging.error(f"An unexpected error occurred when calling run_seed(): {e_seed_run}", exc_info=True)
        # Depending on severity, might want to sys.exit(1) here if seeding is critical for app function
    # --- End Coordinated Data Seeding ---

    # --- Initialize User Profile Management Database ---
    try:
        logging.info("Attempting to initialize user profile management database...")
        create_user_profile_tables()
        seed_user_profile_data()
        logging.info("User profile management database initialized and seeded successfully.")
    except Exception as e_user_profile_db:
        logging.error(f"Error initializing user profile management database: {e_user_profile_db}", exc_info=True)
        # Depending on severity, you might want to show an error to the user or exit.
        # For now, just logging the error.
    # --- End User Profile Management Database Initialization ---

    # --- Token Cleanup on Startup ---
    conn_cleanup = None
    try:
        conn_cleanup = get_db_connection() # Get a connection for cleanup tasks
        if conn_cleanup:
            from db.cruds import user_session_tokens_crud, password_reset_tokens_crud

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
    theme = db.get_setting('theme', default='Light')
    if theme == 'Dark':
        dark_theme_path = os.path.join(APP_ROOT_DIR, "resources", "styles", "dark_theme.qss")
        if os.path.exists(dark_theme_path):
            with open(dark_theme_path, "r") as f:
                app.setStyleSheet(f.read())
        else:
            load_stylesheet_global(app)
    else:
        load_stylesheet_global(app)
    
    # The following app.setStyleSheet call has been removed to ensure style.qss is the single source of truth.
    # Basic styles that were here should be covered by or merged into style.qss.
    # For example, default QPushButton, QLineEdit, QGroupBox styles are now expected
    # to be defined comprehensively in style.qss.

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

    # --- Coordinated Data Seeding ---
    # This block handles the seeding of initial data after the schema is created,
    # using the dedicated seeding module.
    try:
        logging.info("Attempting to run data seeding if necessary...")
        # Check if the database is empty before seeding
        if users_crud.is_users_table_empty():
            logging.info("Users table is empty, running data seeding...")
            run_seed() # Call the main seeding function from db_seed.py
            logging.info("Data seeding process via run_seed() completed.")
        else:
            logging.info("Users table is not empty, skipping data seeding.")
    except Exception as e_seed_run:
        # Catch any unexpected error from run_seed() itself, though it should handle its own.
        logging.error(f"An unexpected error occurred when calling run_seed(): {e_seed_run}", exc_info=True)
    # --- End Coordinated Data Seeding ---

    # --- Startup Dialog Logic ---
    show_setup_prompt_config_value = CONFIG.get("show_initial_setup_on_startup", False)
    # Use CONFIG for directory paths in is_first_launch
    first_launch_detected = is_first_launch(APP_ROOT_DIR, CONFIG.get('templates_dir'), CONFIG.get('clients_dir'))
    companies_exist = bool(db.get_all_companies()) # Check once

    should_reset_config_flag_after_dialog = False

    if first_launch_detected:
        logging.info("Application detected first launch. Executing InitialSetupDialog.")
        # initial_setup_dialog = InitialSetupDialog()
        # result = initial_setup_dialog.exec_()
        # if result == QDialog.Accepted:
        #     # Use CONFIG for directory paths in mark_initial_setup_complete
        #     mark_initial_setup_complete(APP_ROOT_DIR, CONFIG.get('templates_dir'), CONFIG.get('clients_dir'))
        #     logging.info("Initial setup marked as complete.")
        #     companies_exist = bool(db.get_all_companies()) # Re-check companies after setup
        # else:
        #     logging.warning("InitialSetupDialog cancelled. Application may lack configurations.")
        #     # Potentially exit or show critical error if setup is vital

    # Now, handle the PromptCompanyInfoDialog based on company existence and the flag
    if not companies_exist:
        if first_launch_detected or show_setup_prompt_config_value: # Show if first launch OR if flag is true
            logging.info("No companies found or setup prompt explicitly enabled. Prompting for company information.")
            # prompt_dialog = PromptCompanyInfoDialog()
            # dialog_result_company = prompt_dialog.exec_()

            # if dialog_result_company == QDialog.Accepted:
            # Simulate dialog acceptance to proceed with default company creation if logic expects it
            dialog_result_company = QDialog.Accepted # SIMULATED ACCEPTANCE
            prompt_dialog = type('obj', (object,), {'use_default_company': True, 'get_company_data': lambda: None})() # SIMULATED DIALOG

            if dialog_result_company == QDialog.Accepted:
                if prompt_dialog.use_default_company:
                    logging.info("User opted to use a default company.")
                    default_company_data = {
                        "company_name": "My Business", "address": "Not specified", "is_default": True,
                        "logo_path": None, "payment_info": "", "other_info": "Default company created."
                    }
                    new_company_id = add_company(default_company_data)
                    if new_company_id:
                        logging.info(f"Default company 'My Business' added with ID: {new_company_id}.")
                        companies_exist = True # Update companies_exist status
                    else:
                        logging.error("Failed to add default company.")
                else: # User entered data
                    user_company_data = prompt_dialog.get_company_data()
                    if user_company_data and user_company_data['company_name']:
                        company_to_add = {
                            "company_name": user_company_data['company_name'],
                            "address": user_company_data.get('address', ''), "is_default": True,
                            "logo_path": None, "payment_info": "", "other_info": "Company created via prompt."
                        }
                        new_company_id = add_company(company_to_add)
                        if new_company_id:
                            logging.info(f"User-defined company '{company_to_add['company_name']}' added with ID: {new_company_id}.")
                            companies_exist = True # Update companies_exist status
                        else:
                            logging.error(f"Failed to add user-defined company '{company_to_add['company_name']}'.")
                    else:
                        logging.warning("Company prompt accepted, but no company name provided. No company added.")
            else: # Dialog was cancelled
                logging.warning("User cancelled company prompt.")

            # If the prompt was shown because of the config flag (and not strictly first_launch path that also sets it)
            if show_setup_prompt_config_value and not first_launch_detected:
                should_reset_config_flag_after_dialog = True
        else:
            logging.info("No companies found, but setup prompt is not enabled by config and not first launch. Skipping company prompt.")
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
    current_license_info = None # Pour stocker les détails de la licence

    # --- Remember Me - Attempt Auto Login with Token ---
    remembered_token = auth_service.get_remembered_token_from_settings()
    if remembered_token:
        logging.info("Attempting auto-login with session token.")
        # login_with_session_token returns: (success, message, user_data, license_info)
        token_auth_success, token_auth_message, token_user_info, token_license_info = auth_service.login_with_session_token(remembered_token)

        if token_auth_success and token_user_info:
            logged_in_user_info = token_user_info
            current_license_info = token_license_info # This now includes allowed_features
            logging.info(f"Auto-login with token successful for user: {logged_in_user_info.get('username')}")
            SESSION_START_TIME = datetime.datetime.now()

            if token_license_info and token_license_info.get('is_active'):
                logging.info(f"License is valid for token auto-login of {logged_in_user_info.get('username')}.")
                proceed_to_main_app = True
            else: # License is invalid or missing after token login
                license_issue_msg = token_auth_message or "Votre licence n'est plus valide."
                logging.warning(f"Token auto-login for {logged_in_user_info.get('username')} successful, but license is invalid: {license_issue_msg}")
                QMessageBox.warning(None, "Licence Requise", f"Votre session a été restaurée, mais votre licence n'est plus valide : {license_issue_msg}\nVeuillez vous reconnecter.")
                auth_service.logout() # This will clear QSettings token and attempt to clear DB token
                logged_in_user_info = None
                current_license_info = None
                proceed_to_main_app = False # Fall through to manual login
        else: # Token login failed (e.g. token invalid, expired, user inactive)
            logging.warning(f"Auto-login with token failed: {token_auth_message or 'Token invalid/expired'}. Proceeding to manual login.")
            # auth_service.login_with_session_token should have cleared the invalid token from QSettings.
            proceed_to_main_app = False
    else: # No token remembered
        proceed_to_main_app = False

    if not proceed_to_main_app:
        # Ensure any partial session from failed token login is cleared before manual login
        if auth_service.get_current_user(): # If _current_user_data was set by a failed token login path
            auth_service.logout()
        logged_in_user_info = None
        current_license_info = None

        while True: # Loop for manual login and license management
            login_dialog = LoginDialog()
            login_dialog_result = login_dialog.exec_()

            if login_dialog_result == QDialog.Accepted:
                # auth_service.login gère maintenant la vérification de la licence et retourne les infos
                # user_data_from_dialog est en fait le retour de auth_service.login()
                # qui est (success, error_message_or_None, user_info_or_None, license_info_or_None)

                raw_login_output = login_dialog.get_raw_login_output()
                if not raw_login_output or len(raw_login_output) != 4:
                    logging.error("Le retour de LoginDialog.get_raw_login_output() est invalide.")
                    QMessageBox.critical(None, "Erreur Critique", "Erreur interne lors de la récupération des informations de connexion.")
                    splash.hide()
                    sys.exit(1) # Quitter en cas d'erreur critique

                auth_success, auth_message, temp_user_info, temp_license_info = raw_login_output

                logged_in_user_info = temp_user_info # Peut être None si auth_success est False
                current_license_info = temp_license_info # Peut être None ou contenir des infos sur l'invalidité

                if auth_success and logged_in_user_info:
                    logging.info(f"Authentification manuelle réussie pour: {logged_in_user_info.get('username')}")
                    SESSION_START_TIME = datetime.datetime.now() # Démarrer le timer de session

                    # La licence a déjà été vérifiée dans auth_service.login.
                    # Si auth_message contient quelque chose, c'est probablement un message de licence.
                    if auth_message and "licence" in auth_message.lower(): # Si le message concerne la licence
                        logging.warning(f"Utilisateur {logged_in_user_info.get('username')} authentifié, mais problème de licence: {auth_message}")

                        # Proposer d'activer la licence gratuite si c'est pertinent
                        if "aucune licence" in auth_message.lower() or "expiré" in auth_message.lower():
                            conn_lic_man = None
                            try:
                                conn_lic_man = get_db_connection()
                                # Vérifier si une licence gratuite a déjà été utilisée sur cette machine pour cet utilisateur
                                machine_id = license_manager.get_machine_identifier()
                                existing_free_on_machine = license_manager.cruds.get_licenses_by_machine_info(conn_lic_man, machine_id, license_type="gratuit")
                                has_had_free_on_machine_for_user = any(lic['user_id'] == logged_in_user_info['user_id'] for lic in existing_free_on_machine)

                                if not has_had_free_on_machine_for_user:
                                    reply = QMessageBox.question(None, "Licence Gratuite",
                                                                 "Aucune licence valide trouvée. Souhaitez-vous activer une licence gratuite de 30 jours ?",
                                                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                                    if reply == QMessageBox.Yes:
                                        free_lic_details, free_msg = license_manager.activate_free_license(conn_lic_man, logged_in_user_info['user_id'])
                                        if free_lic_details:
                                            QMessageBox.information(None, "Licence Gratuite Activée", free_msg)
                                            current_license_info = free_lic_details # Mettre à jour avec la nouvelle licence
                                            proceed_to_main_app = True
                                            break # Sortir de la boucle de login, licence OK
                                        else:
                                            QMessageBox.warning(None, "Échec Activation Gratuite", free_msg)
                                            # Reste dans la boucle pour afficher la page de licence
                                    # Si l'utilisateur dit non, ou si la gratuite n'est pas proposée, on continue vers la page de licence
                            except Exception as e_free_act:
                                logging.error(f"Erreur lors de la tentative d'activation de la licence gratuite: {e_free_act}", exc_info=True)
                                QMessageBox.warning(None, "Erreur", "Une erreur est survenue lors de l'activation de la licence gratuite.")
                            finally:
                                if conn_lic_man:
                                    conn_lic_man.close()

                        # Si on n'a pas pu activer la gratuite ou si ce n'était pas pertinent, afficher la page de licence
                        if not proceed_to_main_app: # proceed_to_main_app est False ici si la gratuite n'a pas résolu
                            logging.info("Affichage de la LicenseDialog car la licence n'est pas valide après la tentative d'activation gratuite (ou si non applicable).")
                            license_dialog_instance = LicenseDialog(
                                current_user_info=logged_in_user_info,
                                initial_license_info=current_license_info, # Passer les infos de licence actuelles (potentiellement invalides)
                                parent=None # Ou login_dialog comme parent si on veut le lier
                            )

                            dialog_accepted = False
                            if license_dialog_instance.exec_() == QDialog.Accepted:
                                # LicenseDialog a été acceptée, ce qui signifie qu'une licence valide a été configurée.
                                # Récupérer les informations de licence mises à jour.
                                updated_license_details = license_dialog_instance.get_current_valid_license_info()
                                if updated_license_details and updated_license_details.get('is_active'):
                                    current_license_info = updated_license_details
                                    proceed_to_main_app = True
                                    dialog_accepted = True # Marquer que la dialog a été acceptée
                                    logging.info("LicenseDialog acceptée, licence valide obtenue.")
                                    break # Sortir de la boucle de login, licence OK
                                else:
                                    QMessageBox.critical(None, "Licence Toujours Invalide",
                                                         "La licence n'est toujours pas valide après la tentative de configuration. L'application va se fermer.")
                                    splash.hide()
                                    sys.exit(1)

                            if not dialog_accepted: # Si la LicenseDialog a été fermée/rejetée sans licence valide
                                QMessageBox.information(None, "Licence Requise",
                                                        "Une licence valide est requise pour continuer. L'application va se fermer.")
                                splash.hide()
                                sys.exit(0) # Quitter proprement

                    else: # Authentification OK et la licence était déjà valide (pas de auth_message de licence)
                        proceed_to_main_app = True
                        break # Sortir de la boucle de login, tout est OK

                else: # Échec de l'authentification (auth_success est False)
                    logging.warning(f"Échec de l'authentification manuelle: {auth_message}")
                    QMessageBox.warning(login_dialog, "Échec de la Connexion", auth_message or "Nom d'utilisateur ou mot de passe incorrect.")
                    # Reste dans la boucle de login

            else: # LoginDialog a été annulé ou fermé
                logging.warning("Login dialog was cancelled or closed by the user. Exiting application.")
                splash.hide()
                sys.exit(0) # Quitter l'application

    if proceed_to_main_app and logged_in_user_info and current_license_info is not None and current_license_info.get('is_active'):
        # Passer user_info et license_info à DocumentManager
        main_window = DocumentManager(APP_ROOT_DIR, logged_in_user_info, current_license_info)

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