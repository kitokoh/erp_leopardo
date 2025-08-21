# -*- coding: utf-8 -*-
import os
import sys
import logging
from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QLibraryInfo, QTranslator, QLocale

# Import the function directly to avoid circular import issues with the 'db' package
from app.db.connection import initialize_engine_and_session, set_db_config

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
    Handles the entire database setup process:
    - Checks for DB existence.
    - Applies Alembic migrations.
    - Sets up SQLAlchemy engine and session.
    - Seeds the database if it was newly created.
    """
    set_db_config(config)
    db_path = config.get('database_path')
    db_exists = os.path.exists(db_path) if db_path else False

    if not db_exists:
        logging.info("Database does not exist. It will be created by Alembic.")

    try:
        from alembic.config import Config as AlembicConfig
        from alembic import command as alembic_command
        alembic_ini_path = os.path.join(project_root, 'alembic.ini')

        if not os.path.exists(alembic_ini_path):
            raise FileNotFoundError(f"Alembic configuration file not found at: {alembic_ini_path}")

        alembic_cfg = AlembicConfig(alembic_ini_path)
        alembic_cfg.set_main_option('sqlalchemy.url', config['database_url'])
        logging.info("Attempting to upgrade database schema to head using Alembic...")
        alembic_command.upgrade(alembic_cfg, "head")
        logging.info("Alembic upgrade head command completed.")

        # HACK: Manually create ApplicationSettings table to bypass Alembic issue
        try:
            from app.db.connection import get_raw_sqlite_connection
            conn = get_raw_sqlite_connection(config['database_path'])
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS application_settings (
                    setting_key TEXT NOT NULL PRIMARY KEY,
                    setting_value TEXT
                )
            """)
            conn.commit()
            conn.close()
            logging.info("HACK: Manually ensured 'application_settings' table exists.")
        except Exception as e_hack:
            logging.error(f"HACK: Failed to manually create application_settings table: {e_hack}")
        # END HACK

    except ImportError:
        handle_critical_error("Alembic n'est pas installé. L'application ne peut pas démarrer.", "Alembic is not installed. Cannot proceed with database migrations.")
    except Exception as e_alembic:
        handle_critical_error("Une erreur critique est survenue lors de la migration de la base de données.", str(e_alembic))

    # Now that migrations are done, initialize the ORM engine
    try:
        initialize_engine_and_session(config)
        logging.info("SQLAlchemy engine and session have been initialized.")
    except Exception as e_orm_init:
        handle_critical_error("Impossible d'initialiser le moteur de la base de données ORM.", str(e_orm_init))

    # These imports are inside the function because they depend on the db path and alembic migrations running first
    from app.db.db_seed import seed_all_data as run_seed
    from app.user_profile_management.database_setup import create_tables as create_user_profile_tables, seed_data as seed_user_profile_data

    logging.info("Table creation is now handled by Alembic migrations. Skipping redundant create_all call.")

    if not db_exists:
        try:
            logging.info("Running initial data seeding...")
            run_seed()
            logging.info("Data seeding process completed.")
        except Exception as e_seed:
            logging.error(f"An error occurred during data seeding: {e_seed}", exc_info=True)

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
        # In a frozen app (PyInstaller), fonts might need special handling.
        # For now, we assume they are bundled correctly.
        pass

    # Set High DPI Scaling Attributes
    if hasattr(QApplication, 'AA_EnableHighDpiScaling'):
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(QApplication, 'AA_UseHighDpiPixmaps'):
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Set Application Name and Style
    app.setApplicationName(app_name)
    app.setOrganizationName(org_name)
    app.setStyle("Fusion")

    # Set Default Font
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
    # Load application translations
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

    # Load Qt base translations
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
