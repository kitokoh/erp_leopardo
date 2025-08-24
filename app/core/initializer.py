# -*- coding: utf-8 -*-
import os
import sys
import logging
import subprocess
from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QLibraryInfo, QTranslator, QLocale

# Import the function directly to avoid circular import issues with the 'db' package
from app.db import connection
from app.db.db_seed import seed_all_data

def handle_critical_error(message, details=""):
    """Handles critical errors by logging and exiting, or showing a message box."""
    logging.critical(f"{message}: {details}", exc_info=True)
    if os.environ.get("TESTING") == "1":
        print(f"CRITICAL ERROR: {message}\n{details}")
        sys.exit(1)
    else:
        QMessageBox.critical(None, "Erreur Critique", f"{message}\n{details}")
        sys.exit(1)

def initialize_database(config, project_root):
    """
    Handles the entire database setup process in a robust, cross-platform way.
    - Runs Alembic migrations in a separate process to avoid silent exits.
    - Sets up the SQLAlchemy engine and session.
    - Seeds the database if it was newly created.
    """
    db_path = config.get('database_path')
    db_exists = os.path.exists(db_path) if db_path else False

    # 1. Run Alembic migrations using subprocess to ensure it completes
    try:
        logging.info("Running Alembic migrations via subprocess...")
        # Note: We use sys.executable to ensure we use the same python interpreter
        # that is running this script. 'poetry run' is not used here to make it
        # more portable in case the app is run without poetry.
        # The '-m alembic' part is key to running it as a module.
        alembic_command = [sys.executable, "-m", "alembic", "upgrade", "head"]

        # We need to set the PYTHONPATH for the subprocess so it can find the app modules
        env = os.environ.copy()
        env['PYTHONPATH'] = project_root + os.pathsep + env.get('PYTHONPATH', '')

        # Pass the correct database URL to the alembic subprocess
        if config.get('database_url'):
            env['ALEMBIC_DATABASE_URL'] = config['database_url']

        result = subprocess.run(
            alembic_command,
            check=True, capture_output=True, text=True, cwd=project_root, env=env
        )
        import time
        time.sleep(2) # HACK: Wait for file system to catch up
        logging.info("Alembic stdout:\n" + result.stdout)
        if result.stderr:
            logging.warning("Alembic stderr:\n" + result.stderr)
        logging.info("Alembic migrations completed successfully.")
    except subprocess.CalledProcessError as e:
        # This catches errors if the alembic command returns a non-zero exit code
        handle_critical_error(
            "Une erreur critique est survenue lors de la migration de la base de données.",
            f"Alembic Error:\n{e.stderr}"
        )
    except FileNotFoundError:
        # This catches errors if 'python' or 'alembic' can't be found
        handle_critical_error("Commande de migration non trouvée.", "sys.executable ou le module alembic est introuvable.")
    except Exception as e:
        handle_critical_error("Une erreur inattendue est survenue lors des migrations.", str(e))

    # 2. Initialize the SQLAlchemy engine and session for the application
    connection.set_db_config(config)
    try:
        connection.initialize_engine_and_session(config)
        logging.info("SQLAlchemy engine and session have been initialized.")
    except Exception as e:
        handle_critical_error("Une erreur critique est survenue lors de l'initialisation de la connexion à la base de données.", str(e))

    # 3. Seed the database if it was newly created
    if not db_exists:
        logging.info("Database was newly created. Running initial data seeding...")
        db_session = None
        try:
            db_session = connection.get_db_connection()
            seed_all_data(db_session)
            logging.info("Data seeding process completed.")
        except Exception as e_seed:
            logging.error(f"An error occurred during data seeding: {e_seed}", exc_info=True)
            # Not calling handle_critical_error here, as the app might still run without seeded data
        finally:
            if db_session:
                db_session.close()
                logging.info("Seeding database session closed.")

    # 4. Initialize the user profile management database (separate logic)
    from app.user_profile_management.database_setup import create_tables as create_user_profile_tables, seed_data as seed_user_profile_data
    try:
        logging.info("Initializing user profile management database...")
        create_user_profile_tables()
        seed_user_profile_data()
        logging.info("User profile management database initialized.")
    except Exception as e_user_profile:
        logging.error(f"Error initializing user profile management database: {e_user_profile}", exc_info=True)


def setup_qt_application(app, app_name="ClientDocManager", org_name="SaadiyaManagement"):
    """
    Configures basic Qt application settings like DPI, name, style, and font.
    """
    logging.info("Setting up Qt application attributes...")
    if hasattr(sys, 'frozen'):
        pass

    if hasattr(QApplication, 'AA_EnableHighDpiScaling'):
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(QApplication, 'AA_UseHighDpiPixmaps'):
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app.setApplicationName(app_name)
    app.setOrganizationName(org_name)
    app.setStyle("Fusion")

    default_font = QFont("Segoe UI", 9)
    if sys.platform != "win32":
        default_font = QFont("Arial", 10)
    app.setFont(default_font)
    logging.info("Qt application attributes set.")


def setup_translations(app, language_code, app_root_dir):
    """
    Loads and installs translators for the application.
    """
    logging.info(f"Setting up translations for language code: {language_code}")
    app_translator = QTranslator()
    translation_filename = "main.qm"
    lang_spec_translation_path = os.path.join(app_root_dir, "translations", "qm", language_code, translation_filename)

    if os.path.exists(lang_spec_translation_path):
        if app_translator.load(lang_spec_translation_path):
            app.installTranslator(app_translator)
            logging.info(f"Successfully loaded and installed application translation: {lang_spec_translation_path}")
        else:
            logging.warning(f"Failed to load application translation from {lang_spec_translation_path}.")
    else:
        logging.warning(f"Application translation file not found: {lang_spec_translation_path}")

    qt_translator = QTranslator()
    qt_translation_path_base = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
    if qt_translator.load(QLocale(language_code), "qtbase", "_", qt_translation_path_base):
        app.installTranslator(qt_translator)
        logging.info(f"Loaded Qt base translations for {language_code} from {qt_translation_path_base}")
    else:
        generic_locale_name = language_code.split('_')[0]
        if generic_locale_name != language_code:
            logging.info(f"Trying generic Qt base translations for {generic_locale_name}")
            if qt_translator.load(QLocale(generic_locale_name), "qtbase", "_", qt_translation_path_base):
                app.installTranslator(qt_translator)
                logging.info(f"Loaded generic Qt base translations for {generic_locale_name}.")
            else:
                logging.warning(f"Failed to load Qt base translations for {language_code} or {generic_locale_name}.")
        else:
            logging.warning(f"Failed to load Qt base translations for {language_code}.")
