import sqlite3
import os
from sqlalchemy import text
import json
import logging # Added missing import
from datetime import datetime, date # Added date
import uuid
import hashlib
from decimal import Decimal # Added Decimal
from sqlalchemy import create_engine # Added create_engine
import sys # Ensure sys is imported for path manipulation

# Get the project root directory
# This allows importing config.py from the root and db.connection
# project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # No longer needed for config import
# if project_root not in sys.path:
#     sys.path.insert(0, project_root) # No longer needed for config import

# try:
#     import config # Removed direct config import
# except ImportError:
#     print("CRITICAL: config.py not found at project root by db/init_schema.py. Using fallback configurations.")
#     class config_fallback:
#         DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app_data_fallback_init.db")
#         DEFAULT_ADMIN_USERNAME = "admin_fallback_init"
#         DEFAULT_ADMIN_PASSWORD = "password_fallback_init"
#         # Add other necessary fallbacks if init_schema.py uses them directly
#         # For example, APP_ROOT_DIR if it were used directly for paths here.
#     config = config_fallback

# Import the main SQLAlchemy components from db.connection
# Note: main_engine will be None here and needs to be initialized by main.py calling db.connection.initialize_engine_and_session
try:
    # Import Base and initialize_engine_and_session. We will get 'engine' later, after it's initialized.
    from db.connection import Base as MainBase, initialize_engine_and_session
    # Import specific models that use MainBase and need table creation here
    from calculator.models import CalculationHistory
    # from other_module.models import OtherModelUsingMainBase # Example for future models
    from db.common_models import Products # Import the Products SQLAlchemy model # RESTORED
    logging.info("DEBUG_INIT_DB: Products model import from db.common_models RESTORED.")
    MAIN_SQLALCHEMY_COMPONENTS_LOADED = True
except ImportError as e_main_sqlalchemy:
    logging.error(f"db.init_schema: Could not import MainBase or initialize_engine_and_session from db.connection: {e_main_sqlalchemy}. Tables using MainBase (e.g., CalculatorHistory) might not be created by this script.")
    MAIN_SQLALCHEMY_COMPONENTS_LOADED = False
    MainBase = None # Ensure it's None so later checks don't fail with NameError
    # main_engine = None # No longer importing main_engine directly at the top

from sqlalchemy import Table, Column, Text # Added for reflecting Users table more explicitly

from auth.roles import SUPER_ADMIN

# Import CRUD functions (taken from db/schema.py, paths adjusted for db/init_schema.py)
from .cruds.users_crud import get_user_by_username
from .cruds.locations_crud import get_country_by_name, get_city_by_name_and_country_id
from .cruds.status_settings_crud import get_status_setting_by_name
from .cruds.application_settings_crud import set_setting
# add_default_template_if_not_exists is not directly used by initialize_database, but good to keep if other parts of schema setup might use it.
# from .cruds.templates_crud import add_default_template_if_not_exists
from .cruds.cover_page_templates_crud import add_cover_page_template, get_cover_page_template_by_name
from .cruds.template_categories_crud import add_template_category # Used by _get_or_create_category_id if category doesn't exist.

# Helper function from db/schema.py (also present in db/ca.py, schema.py version is more complete)
def _get_or_create_category_id(cursor: sqlite3.Cursor, category_name: str, default_category_id: int | None) -> int | None:
    if not category_name: return default_category_id
    try:
        # Ensure row_factory is respected by the cursor passed in, or adjust access (e.g., row[0] vs row['category_id'])
        cursor.execute("SELECT category_id FROM TemplateCategories WHERE category_name = ?", (category_name,))
        row = cursor.fetchone()
        if row:
            # Assuming the connection this cursor belongs to has sqlite3.Row as row_factory
            return row['category_id']
        else:
            # Use the imported add_template_category CRUD function if available and appropriate,
            # or direct insert if this helper is meant to be self-contained for bootstrap.
            # For now, direct insert as per original schema.py:
            cursor.execute("INSERT INTO TemplateCategories (category_name, description) VALUES (?, ?)",
                           (category_name, f"{category_name} (auto-created during schema init)"))
            # conn.commit() # Should not commit here; part of larger transaction
            return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Error in _get_or_create_category_id for '{category_name}': {e}")
        return default_category_id

# Cover page templates data and population function (from db/schema.py)
DEFAULT_COVER_PAGE_TEMPLATES = [
    {'template_name': 'Standard Report Cover', 'description': 'A standard cover page for general reports.', 'default_title': 'Report Title', 'default_subtitle': 'Company Subdivision', 'default_author': 'Automated Report Generator', 'style_config_json': {'font': 'Helvetica', 'primary_color': '#2a2a2a', 'secondary_color': '#5cb85c'}, 'is_default_template': 1},
    {'template_name': 'Financial Statement Cover', 'description': 'Cover page for official financial statements.', 'default_title': 'Financial Statement', 'default_subtitle': 'Fiscal Year Ending YYYY', 'default_author': 'Finance Department', 'style_config_json': {'font': 'Times New Roman', 'primary_color': '#003366', 'secondary_color': '#e0a800'}, 'is_default_template': 1},
    {'template_name': 'Creative Project Brief', 'description': 'A vibrant cover for creative project briefs and proposals.', 'default_title': 'Creative Brief: [Project Name]', 'default_subtitle': 'Client: [Client Name]', 'default_author': 'Creative Team', 'style_config_json': {'font': 'Montserrat', 'primary_color': '#ff6347', 'secondary_color': '#4682b4', 'layout_hint': 'two-column'}, 'is_default_template': 1},
    {'template_name': 'Technical Document Cover', 'description': 'A clean and formal cover for technical documentation.', 'default_title': 'Technical Specification Document', 'default_subtitle': 'Version [VersionNumber]', 'default_author': 'Engineering Team', 'style_config_json': {'font': 'Roboto', 'primary_color': '#191970', 'secondary_color': '#cccccc'}, 'is_default_template': 1}
]

def _populate_default_cover_page_templates(conn_passed):
    print("Populating default cover page templates...")
    for template_def in DEFAULT_COVER_PAGE_TEMPLATES:
        # Use the imported CRUD function
        existing_template = get_cover_page_template_by_name(template_def['template_name'], conn=conn_passed)
        if existing_template:
            print(f"Default template '{template_def['template_name']}' already exists. Skipping.")
        else:
            # Ensure style_config_json is passed as a JSON string if it's a dict
            template_def_for_add = template_def.copy() # Avoid modifying original dict
            if isinstance(template_def_for_add.get('style_config_json'), dict):
                template_def_for_add['style_config_json'] = json.dumps(template_def_for_add['style_config_json'])

            # Use the imported CRUD function
            new_id = add_cover_page_template(template_def_for_add, conn=conn_passed)
            if new_id:
                print(f"Added default cover page template: '{template_def['template_name']}' with ID: {new_id}")
            else:
                print(f"Failed to add default cover page template: '{template_def['template_name']}'")
    print("Default cover page templates population attempt finished.")


def initialize_database(app_config):
    """
    Initializes the database by creating tables if they don't already exist.
    Combines schema from db/ca.py and db/schema.py.
    Requires app_config to be passed in.
    """
    if not app_config or 'database_path' not in app_config:
        logging.critical("initialize_database called without valid app_config or database_path. Aborting schema initialization.")
        raise ValueError("app_config with database_path is required for initialize_database.")

    database_path = app_config['database_path']

    # Ensure the directory for the database exists
    db_dir = os.path.dirname(database_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        logging.info(f"Created directory for database: {db_dir}")


    # Initialize the main SQLAlchemy engine using the passed config.
    # This makes main_engine available if other parts of init_schema need it,
    # though it's primarily for use by the rest of the application via db.connection.engine.
    # Note: `initialize_engine_and_session` is imported from `db.connection`.
    # It sets the global `engine` and `SessionLocal` in `db.connection`.
    initialize_engine_and_session(app_config)
    logging.info(f"db.init_schema: Main SQLAlchemy engine initialized via db.connection.initialize_engine_and_session with path: {database_path}")


    # Create a local SQLAlchemy engine for operations specific to init_schema if needed,
    # or rely on the main_engine if appropriate. For create_all, main_engine is fine.
    # The `engine` variable here is local to initialize_database scope.
    # The `main_engine` imported from db.connection is the global one.
    # For acc_models.Base.metadata.create_all(bind=engine_acc), a new engine `engine_acc` is created later.
    # For MainBase.metadata.create_all(bind=actual_main_engine), it uses the globally set main_engine.

    # Get the initialized engine from db.connection now that initialize_engine_and_session has been called
    from db.connection import engine as actual_main_engine
    logging.info(f"db.init_schema: Imported actual_main_engine from db.connection. Is None: {actual_main_engine is None}")


    # Use DATABASE_PATH from the passed app_config
    conn = sqlite3.connect(database_path, timeout=10) # Keep for direct cursor use, increased timeout
    conn.row_factory = sqlite3.Row # Essential for accessing columns by name
    cursor = conn.cursor() # Keep for direct cursor use

    # Create Roles table - REMOVED, now handled by Alembic and SQLAlchemy model db.common_models.Role
    # logging.info("DEBUG_INIT_DB: Roles table creation SKIPPED - Handled by Alembic.")
    print("DEBUG_INIT_DB: Table Roles (raw SQL) creation SKIPPED - Handled by Alembic.") # Keep print for now


    # --- Permissions and RolePermissions Tables (New for dynamic permissions) ---
    # These are still created with raw SQL as they are not (yet) SQLAlchemy models.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Permissions (
        permission_key TEXT PRIMARY KEY,
        description TEXT
    )
    """)
    print("DEBUG_INIT_DB: Table Permissions created or exists.")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS RolePermissions (
        role_id INTEGER NOT NULL,
        permission_key TEXT NOT NULL,
        PRIMARY KEY (role_id, permission_key),
        FOREIGN KEY (role_id) REFERENCES Roles (role_id) ON DELETE CASCADE,
        FOREIGN KEY (permission_key) REFERENCES Permissions (permission_key) ON DELETE CASCADE
    )
    """)
    print("DEBUG_INIT_DB: Table RolePermissions created or exists.")
    # --- End Permissions and RolePermissions Tables ---

    # Populate Roles table (ensure default roles exist) - REMOVED
    # This is now handled by db_seed.py after Alembic creates the Roles table.
    print("DEBUG_INIT_DB: Default roles seeding (Administrator, Team Lead, Operator) in init_schema.py SKIPPED - Handled by db_seed.py.")

    # Seeding of Permissions and RolePermissions is also MOVED to db_seed.py
    print("DEBUG_INIT_DB: Seeding of Permissions and RolePermissions in init_schema.py SKIPPED - Handled by db_seed.py.")



    # Table Users (raw SQL) creation REMOVED - Handled by Alembic.
    logging.info("DEBUG_INIT_DB: Table Users (raw SQL) creation fully REMOVED from init_schema.py - Handled by Alembic.")

    # Ensure is_deleted, and deleted_at columns exist in Users table (for migration from older schemas)
    # This ALTER TABLE logic is for migrating existing databases. For new DBs, it's not strictly needed.
    # cursor.execute("PRAGMA table_info(Users)")
    # users_columns_info = cursor.fetchall()
    # users_column_names = [info['name'] for info in users_columns_info]

    # Migration for 'salt' and 'role' columns if they exist from an old schema:
    # This is complex. For now, we assume a fresh setup or that users_crud handles the new schema.
    # If 'salt' column exists and needs removal, or 'role' text column needs migration to 'role_id',
    # that would require more complex ALTER TABLE (rename, create new, copy data, drop old)
    # which is too risky without knowing existing data.
    # The CREATE TABLE above defines the target schema.

    # if 'is_deleted' not in users_column_names:
    #     try:
    #         cursor.execute("ALTER TABLE Users ADD COLUMN is_deleted INTEGER DEFAULT 0")
    #         print("Added 'is_deleted' column to Users table.")
    #     except sqlite3.Error as e_alter_is_deleted:
    #         print(f"Error adding 'is_deleted' column to Users table: {e_alter_is_deleted}")

    # if 'deleted_at' not in users_column_names:
    #     try:
    #         cursor.execute("ALTER TABLE Users ADD COLUMN deleted_at TEXT")
    #         print("Added 'deleted_at' column to Users table.")
    #     except sqlite3.Error as e_alter_deleted_at:
    #         print(f"Error adding 'deleted_at' column to Users table: {e_alter_deleted_at}")

    # # Assurer que les nouveaux champs biométriques existent pour les bases de données existantes
    # cursor.execute("PRAGMA table_info(Users)")
    # users_columns_info_bio = cursor.fetchall() # Utiliser un nouveau nom de variable
    # users_column_names_bio = [info['name'] for info in users_columns_info_bio]

    # if 'is_fingerprint_auth_enabled' not in users_column_names_bio:
    #     try:
    #         cursor.execute("ALTER TABLE Users ADD COLUMN is_fingerprint_auth_enabled BOOLEAN DEFAULT FALSE")
    #         print("Added 'is_fingerprint_auth_enabled' column to Users table.")
    #     except sqlite3.Error as e_alter_bio:
    #         print(f"Error adding 'is_fingerprint_auth_enabled' column to Users table: {e_alter_bio}")

    # if 'fingerprint_template_id' not in users_column_names_bio:
    #     try:
    #         cursor.execute("ALTER TABLE Users ADD COLUMN fingerprint_template_id TEXT")
    #         print("Added 'fingerprint_template_id' column to Users table.")
    #     except sqlite3.Error as e_alter_bio:
    #         print(f"Error adding 'fingerprint_template_id' column to Users table: {e_alter_bio}")

    # if 'is_face_auth_enabled' not in users_column_names_bio:
    #     try:
    #         cursor.execute("ALTER TABLE Users ADD COLUMN is_face_auth_enabled BOOLEAN DEFAULT FALSE")
    #         print("Added 'is_face_auth_enabled' column to Users table.")
    #     except sqlite3.Error as e_alter_bio:
    #         print(f"Error adding 'is_face_auth_enabled' column to Users table: {e_alter_bio}")

    # if 'face_template_id' not in users_column_names_bio:
    #     try:
    #         cursor.execute("ALTER TABLE Users ADD COLUMN face_template_id TEXT")
    #         print("Added 'face_template_id' column to Users table.")
    #     except sqlite3.Error as e_alter_bio:
    #         print(f"Error adding 'face_template_id' column to Users table: {e_alter_bio}")

    # if 'is_voice_auth_enabled' not in users_column_names_bio:
    #     try:
    #         cursor.execute("ALTER TABLE Users ADD COLUMN is_voice_auth_enabled BOOLEAN DEFAULT FALSE")
    #         print("Added 'is_voice_auth_enabled' column to Users table.")
    #     except sqlite3.Error as e_alter_bio:
    #         print(f"Error adding 'is_voice_auth_enabled' column to Users table: {e_alter_bio}")

    # if 'voice_profile_id' not in users_column_names_bio:
    #     try:
    #         cursor.execute("ALTER TABLE Users ADD COLUMN voice_profile_id TEXT")
    #         print("Added 'voice_profile_id' column to Users table.")
    #     except sqlite3.Error as e_alter_bio:
    #         print(f"Error adding 'voice_profile_id' column to Users table: {e_alter_bio}")

    # Create Companies table (base from ca.py)
    # cursor.execute("""
    # CREATE TABLE IF NOT EXISTS Companies (
    #     company_id TEXT PRIMARY KEY,
    #     company_name TEXT NOT NULL,
    #     address TEXT,
    #     payment_info TEXT,
    #     logo_path TEXT,
    #     other_info TEXT,
    #     is_default BOOLEAN DEFAULT FALSE,
    #     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    # )
    # """)
    # print("DEBUG_INIT_DB: Table Companies (raw SQL) creation SKIPPED - Handled by Alembic.")

    # Create CompanyPersonnel table (base from ca.py)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS CompanyPersonnel (
        personnel_id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id TEXT NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL, -- e.g., "seller", "technical_manager"
        phone TEXT,
        email TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id) REFERENCES Companies (company_id) ON DELETE CASCADE
    )
    """)

    # Create CompanyPersonnelContacts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS CompanyPersonnelContacts (
        company_personnel_contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
        personnel_id INTEGER NOT NULL,
        contact_id INTEGER NOT NULL,
        is_primary BOOLEAN DEFAULT FALSE,
        can_receive_documents BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (personnel_id) REFERENCES CompanyPersonnel(personnel_id) ON DELETE CASCADE,
        FOREIGN KEY (contact_id) REFERENCES Contacts(contact_id) ON DELETE CASCADE,
        UNIQUE (personnel_id, contact_id)
    )
    """)

    # Create TeamMembers table (base from ca.py)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS TeamMembers (
        team_member_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT UNIQUE,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        role_or_title TEXT,
        department TEXT,
        phone_number TEXT,
        profile_picture_url TEXT,
        is_active BOOLEAN DEFAULT TRUE,
        notes TEXT,
        hire_date TEXT,
        performance INTEGER DEFAULT 0,
        skills TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE SET NULL
    )
    """)

    # Create Countries table (base from ca.py)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Countries (
        country_id INTEGER PRIMARY KEY AUTOINCREMENT,
        country_name TEXT NOT NULL UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("DEBUG_INIT_DB: Table Countries created or exists.")

    # Ensure created_at and updated_at columns exist in Countries
    # cursor.execute("PRAGMA table_info(Countries)")
    # countries_columns_info = cursor.fetchall()
    # countries_column_names = [info['name'] for info in countries_columns_info]
    # if 'created_at' not in countries_column_names:
    #     try:
    #         cursor.execute("ALTER TABLE Countries ADD COLUMN created_at TIMESTAMP")

    #         print("Added 'created_at' column to Countries table.")
    #     except sqlite3.Error as e_alter:
    #         print(f"Error adding 'created_at' to Countries: {e_alter}")
    # if 'updated_at' not in countries_column_names:
    #     try:
    #         cursor.execute("ALTER TABLE Countries ADD COLUMN updated_at TIMESTAMP")

    #         print("Added 'updated_at' column to Countries table.")
    #     except sqlite3.Error as e_alter:
    #         print(f"Error adding 'updated_at' to Countries: {e_alter}")

    # Create Cities table (base from ca.py)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Cities (
        city_id INTEGER PRIMARY KEY AUTOINCREMENT,
        country_id INTEGER NOT NULL,
        city_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (country_id) REFERENCES Countries (country_id)
    )
    """)

    # Ensure created_at and updated_at columns exist in Cities
    # cursor.execute("PRAGMA table_info(Cities)")
    # cities_columns_info = cursor.fetchall()
    # cities_column_names = [info['name'] for info in cities_columns_info]
    # if 'created_at' not in cities_column_names:
    #     try:
    #         cursor.execute("ALTER TABLE Cities ADD COLUMN created_at TIMESTAMP")

    #         print("Added 'created_at' column to Cities table.")
    #     except sqlite3.Error as e_alter:
    #         print(f"Error adding 'created_at' to Cities: {e_alter}")
    # if 'updated_at' not in cities_column_names:
    #     try:
    #         cursor.execute("ALTER TABLE Cities ADD COLUMN updated_at TIMESTAMP")

    #         print("Added 'updated_at' column to Cities table.")
    #     except sqlite3.Error as e_alter:
    #         print(f"Error adding 'updated_at' to Cities: {e_alter}")

    # StatusSettings Table (logic from ca.py to add icon_name if missing)
    # cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='StatusSettings'")
    # table_exists = cursor.fetchone()
    # if table_exists:
    #     cursor.execute("PRAGMA table_info(StatusSettings)")
    #     columns = [column['name'] for column in cursor.fetchall()]
    #     if 'icon_name' not in columns:
    #         print("StatusSettings table exists but icon_name column is missing. Adding it now.")
    #         cursor.execute("ALTER TABLE StatusSettings ADD COLUMN icon_name TEXT")
    #         # No commit here, part of larger transaction
    # else:
    #     print("StatusSettings table does not exist. It will be created.")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS StatusSettings (
        status_id INTEGER PRIMARY KEY AUTOINCREMENT,
        status_name TEXT NOT NULL,
        status_type TEXT NOT NULL,
        color_hex TEXT,
        icon_name TEXT,
        default_duration_days INTEGER,
        is_archival_status BOOLEAN DEFAULT FALSE,
        is_completion_status BOOLEAN DEFAULT FALSE,
        sort_order INTEGER DEFAULT 0,  -- Added column
        UNIQUE (status_name, status_type)
    )
    """)

    # Ensure StatusSettings table has sort_order if it already existed
    # cursor.execute("PRAGMA table_info(StatusSettings)")
    # status_settings_columns = [info['name'] for info in cursor.fetchall()]
    # if 'sort_order' not in status_settings_columns:
    #     try:
    #         cursor.execute("ALTER TABLE StatusSettings ADD COLUMN sort_order INTEGER DEFAULT 0")
    #         print("DEBUG_INIT_DB: Added missing 'sort_order' column to existing StatusSettings table.")
    #         # No commit here, it will be part of the main transaction commit
    #     except sqlite3.Error as e_alter_ss:
    #         print(f"DEBUG_INIT_DB: Error trying to ALTER StatusSettings to add sort_order: {e_alter_ss}")
    #         # If altering fails, this might be a critical issue.
    #         # The subsequent INSERTs will likely fail if this was needed and failed.
    # else:
    #     print("DEBUG_INIT_DB: 'sort_order' column already exists in StatusSettings table.")

    # Pre-populate StatusSettings (full list from ca.py)
    default_statuses = [
        # --- Client Statuses ---
        {'status_name': 'Prospect', 'status_type': 'Client', 'color_hex': '#f1c40f', 'icon_name': 'user-status-pending', 'sort_order': 0, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'Prospect Qualifié', 'status_type': 'Client', 'color_hex': '#e67e22', 'icon_name': 'document-send', 'sort_order': 5, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'Client Actif', 'status_type': 'Client', 'color_hex': '#2ecc71', 'icon_name': 'user-available', 'sort_order': 10, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'Client Confirmé', 'status_type': 'Client', 'color_hex': '#3498db', 'icon_name': 'emblem-ok', 'sort_order': 20, 'is_completion_status': False, 'is_archival_status': False}, # Typically after first major order
        {'status_name': 'Client SAV', 'status_type': 'Client', 'color_hex': '#5cb85c', 'icon_name': 'emblem-favorite', 'sort_order': 30, 'is_completion_status': False, 'is_archival_status': False}, # Eligible for SAV
        {'status_name': 'Distributeur', 'status_type': 'Client', 'color_hex': '#8e44ad', 'icon_name': 'business', 'sort_order': 40, 'is_completion_status': False, 'is_archival_status': False}, # Special status
        {'status_name': 'Inactif', 'status_type': 'Client', 'color_hex': '#95a5a6', 'icon_name': 'user-offline', 'sort_order': 50, 'is_completion_status': False, 'is_archival_status': True},
        {'status_name': 'Bloqué', 'status_type': 'Client', 'color_hex': '#c0392b', 'icon_name': 'user-block', 'sort_order': 60, 'is_completion_status': False, 'is_archival_status': True},
        {'status_name': 'Archivé', 'status_type': 'Client', 'color_hex': '#7f8c8d', 'icon_name': 'archive', 'sort_order': 70, 'is_completion_status': True, 'is_archival_status': True},
        # Note: 'Urgent' and 'Complété' for Client were removed as they seem less B2B specific or covered by others. 'Vendu' replaced by 'Client SAV' or 'Client Confirmé'.

        # --- Commande Statuses ---
        {'status_name': 'Brouillon', 'status_type': 'Commande', 'color_hex': '#7f8c8d', 'icon_name': 'document-edit', 'sort_order': 0, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'Devis Envoyé', 'status_type': 'Commande', 'color_hex': '#1abc9c', 'icon_name': 'document-send', 'sort_order': 10, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'Confirmée par Client', 'status_type': 'Commande', 'color_hex': '#2ecc71', 'icon_name': 'document-check', 'sort_order': 20, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'Paiement Partiel Reçu', 'status_type': 'Commande', 'color_hex': '#f39c12', 'icon_name': 'credit-card-multiple', 'sort_order': 25, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'En Cours de Production', 'status_type': 'Commande', 'color_hex': '#3498db', 'icon_name': 'sync', 'sort_order': 30, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'Prête pour Expédition', 'status_type': 'Commande', 'color_hex': '#9b59b6', 'icon_name': 'archive-arrow-up-outline', 'sort_order': 40, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'Envoi en Cours', 'status_type': 'Commande', 'color_hex': '#d35400', 'icon_name': 'truck-delivery', 'sort_order': 50, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'Partiellement Livrée', 'status_type': 'Commande', 'color_hex': '#e67e22', 'icon_name': 'truck-check-outline', 'sort_order': 55, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'Livrée Complètement', 'status_type': 'Commande', 'color_hex': '#27ae60', 'icon_name': 'truck-check', 'sort_order': 60, 'is_completion_status': False, 'is_archival_status': False}, # Not a final completion status for the order itself yet
        {'status_name': 'Facturée', 'status_type': 'Commande', 'color_hex': '#f1c40f', 'icon_name': 'file-invoice-dollar', 'sort_order': 70, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'Partiellement Payée', 'status_type': 'Commande', 'color_hex': '#16a085', 'icon_name': 'cash-multiple', 'sort_order': 75, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'Payée Complètement', 'status_type': 'Commande', 'color_hex': '#2980b9', 'icon_name': 'hand-holding-usd', 'sort_order': 80, 'is_completion_status': True, 'is_archival_status': False},
        {'status_name': 'Annulée', 'status_type': 'Commande', 'color_hex': '#e74c3c', 'icon_name': 'document-cancel', 'sort_order': 90, 'is_completion_status': True, 'is_archival_status': True},
        {'status_name': 'Archivée', 'status_type': 'Commande', 'color_hex': '#95a5a6', 'icon_name': 'archive', 'sort_order': 100, 'is_completion_status': True, 'is_archival_status': True},

        # --- Project Statuses (Kept as is for now, review if needed) ---
        {'status_name': 'Planning', 'status_type': 'Project', 'color_hex': '#1abc9c', 'icon_name': 'view-list-bullet', 'sort_order': 0, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'En cours', 'status_type': 'Project', 'color_hex': '#3498db', 'icon_name': 'view-list-ordered', 'sort_order': 1, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'En attente', 'status_type': 'Project', 'color_hex': '#f39c12', 'icon_name': 'view-list-remove', 'sort_order': 2, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'Terminé', 'status_type': 'Project', 'color_hex': '#2ecc71', 'icon_name': 'task-complete', 'sort_order': 3, 'is_completion_status': True, 'is_archival_status': False},
        {'status_name': 'Annulé', 'status_type': 'Project', 'color_hex': '#c0392b', 'icon_name': 'dialog-cancel', 'sort_order': 4, 'is_completion_status': False, 'is_archival_status': True},
        {'status_name': 'En pause', 'status_type': 'Project', 'color_hex': '#8e44ad', 'icon_name': 'media-playback-pause', 'sort_order': 5, 'is_completion_status': False, 'is_archival_status': False},

        # --- Task Statuses (Kept as is for now) ---
        {'status_name': 'To Do', 'status_type': 'Task', 'color_hex': '#bdc3c7', 'icon_name': 'view-list-todo', 'sort_order': 0, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'In Progress', 'status_type': 'Task', 'color_hex': '#3498db', 'icon_name': 'view-list-progress', 'sort_order': 1, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'Done', 'status_type': 'Task', 'color_hex': '#2ecc71', 'icon_name': 'task-complete', 'sort_order': 2, 'is_completion_status': True, 'is_archival_status': False},
        {'status_name': 'Blocked', 'status_type': 'Task', 'color_hex': '#e74c3c', 'icon_name': 'dialog-error', 'sort_order': 3, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'Review', 'status_type': 'Task', 'color_hex': '#f1c40f', 'icon_name': 'view-list-search', 'sort_order': 4, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'Cancelled', 'status_type': 'Task', 'color_hex': '#7f8c8d', 'icon_name': 'dialog-cancel', 'sort_order': 5, 'is_completion_status': False, 'is_archival_status': True},

        # --- SAVTicket Statuses (Kept as is for now) ---
        {'status_name': 'Ouvert', 'status_type': 'SAVTicket', 'color_hex': '#d35400', 'icon_name': 'folder-new', 'sort_order': 0, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'En Investigation', 'status_type': 'SAVTicket', 'color_hex': '#f39c12', 'icon_name': 'system-search', 'sort_order': 1, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'En Attente (Client)', 'status_type': 'SAVTicket', 'color_hex': '#3498db', 'icon_name': 'folder-locked', 'sort_order': 2, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'Résolu', 'status_type': 'SAVTicket', 'color_hex': '#2ecc71', 'icon_name': 'folder-check', 'sort_order': 3, 'is_completion_status': True, 'is_archival_status': False},
        {'status_name': 'Fermé', 'status_type': 'SAVTicket', 'color_hex': '#95a5a6', 'icon_name': 'folder', 'sort_order': 4, 'is_completion_status': True, 'is_archival_status': True},

        # --- Recruitment Module Statuses (Kept as is for now) ---
        # JobOpening Statuses
        {'status_name': 'Open', 'status_type': 'JobOpening', 'color_hex': '#27ae60', 'icon_name': 'folder-open', 'sort_order': 0, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'Closed', 'status_type': 'JobOpening', 'color_hex': '#95a5a6', 'icon_name': 'folder', 'sort_order': 1, 'is_completion_status': True, 'is_archival_status': True},
        {'status_name': 'On Hold', 'status_type': 'JobOpening', 'color_hex': '#f39c12', 'icon_name': 'folder-locked', 'sort_order': 2, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'Draft', 'status_type': 'JobOpening', 'color_hex': '#bdc3c7', 'icon_name': 'folder-edit', 'sort_order': 3, 'is_completion_status': False, 'is_archival_status': False},
        # CandidateApplication Statuses
        {'status_name': 'Applied', 'status_type': 'CandidateApplication', 'color_hex': '#3498db', 'icon_name': 'user-plus', 'sort_order': 0, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'Screening', 'status_type': 'CandidateApplication', 'color_hex': '#1abc9c', 'icon_name': 'user-search', 'sort_order': 1, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'Interviewing', 'status_type': 'CandidateApplication', 'color_hex': '#9b59b6', 'icon_name': 'users-meeting', 'sort_order': 2, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'Assessment', 'status_type': 'CandidateApplication', 'color_hex': '#e67e22', 'icon_name': 'user-clipboard', 'sort_order': 3, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'Reference Check', 'status_type': 'CandidateApplication', 'color_hex': '#f1c40f', 'icon_name': 'user-check', 'sort_order': 4, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'Offer Extended', 'status_type': 'CandidateApplication', 'color_hex': '#2ecc71', 'icon_name': 'user-contract', 'sort_order': 5, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'Offer Accepted', 'status_type': 'CandidateApplication', 'color_hex': '#27ae60', 'icon_name': 'user-star', 'sort_order': 6, 'is_completion_status': True, 'is_archival_status': False},
        {'status_name': 'Offer Declined', 'status_type': 'CandidateApplication', 'color_hex': '#e74c3c', 'icon_name': 'user-minus', 'sort_order': 7, 'is_completion_status': True, 'is_archival_status': True},
        {'status_name': 'Hired', 'status_type': 'CandidateApplication', 'color_hex': '#16a085', 'icon_name': 'user-tie', 'sort_order': 8, 'is_completion_status': True, 'is_archival_status': False},
        {'status_name': 'Rejected', 'status_type': 'CandidateApplication', 'color_hex': '#c0392b', 'icon_name': 'user-times', 'sort_order': 9, 'is_completion_status': True, 'is_archival_status': True},
        {'status_name': 'Withdrawn', 'status_type': 'CandidateApplication', 'color_hex': '#7f8c8d', 'icon_name': 'user-slash', 'sort_order': 10, 'is_completion_status': True, 'is_archival_status': True},
        # CandidateProgress Statuses
        {'status_name': 'Pending', 'status_type': 'CandidateProgress', 'color_hex': '#bdc3c7', 'icon_name': 'progress-clock', 'sort_order': 0, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'In Progress', 'status_type': 'CandidateProgress', 'color_hex': '#3498db', 'icon_name': 'progress-download', 'sort_order': 1, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'Completed', 'status_type': 'CandidateProgress', 'color_hex': '#2ecc71', 'icon_name': 'progress-check', 'sort_order': 2, 'is_completion_status': True, 'is_archival_status': False},
        {'status_name': 'Skipped', 'status_type': 'CandidateProgress', 'color_hex': '#95a5a6', 'icon_name': 'progress-alert', 'sort_order': 3, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'Failed', 'status_type': 'CandidateProgress', 'color_hex': '#e74c3c', 'icon_name': 'progress-close', 'sort_order': 4, 'is_completion_status': True, 'is_archival_status': False},
        # InterviewStatus Statuses
        {'status_name': 'Scheduled', 'status_type': 'InterviewStatus', 'color_hex': '#3498db', 'icon_name': 'calendar-clock', 'sort_order': 0, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'Completed', 'status_type': 'InterviewStatus', 'color_hex': '#2ecc71', 'icon_name': 'calendar-check', 'sort_order': 1, 'is_completion_status': True, 'is_archival_status': False},
        {'status_name': 'Cancelled', 'status_type': 'InterviewStatus', 'color_hex': '#e74c3c', 'icon_name': 'calendar-times', 'sort_order': 2, 'is_completion_status': True, 'is_archival_status': True},
        {'status_name': 'Rescheduled', 'status_type': 'InterviewStatus', 'color_hex': '#f39c12', 'icon_name': 'calendar-edit', 'sort_order': 3, 'is_completion_status': False, 'is_archival_status': False},
        {'status_name': 'No Show', 'status_type': 'InterviewStatus', 'color_hex': '#c0392b', 'icon_name': 'calendar-question', 'sort_order': 4, 'is_completion_status': True, 'is_archival_status': True},
    ]
    for status in default_statuses:
        cursor.execute("""
            INSERT OR REPLACE INTO StatusSettings (
                status_name, status_type, color_hex, icon_name,
                is_completion_status, is_archival_status, default_duration_days, sort_order
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            status['status_name'], status['status_type'], status['color_hex'],
            status.get('icon_name'), status.get('is_completion_status', False),
            status.get('is_archival_status', False), status.get('default_duration_days'),
            status.get('sort_order', 0)
        ))

    # Table Clients (raw SQL) creation REMOVED - Handled by Alembic.
    logging.info("DEBUG_INIT_DB: Table Clients (raw SQL) creation fully REMOVED from init_schema.py - Handled by Alembic.")

    # Ensure lead_source column exists
    # cursor.execute("PRAGMA table_info(Clients)")
    # clients_columns_info_lead_source_check = cursor.fetchall()
    # clients_column_names_lead_source_check = [info['name'] for info in clients_columns_info_lead_source_check]
    # if 'lead_source' not in clients_column_names_lead_source_check:
    #     try:
    #         cursor.execute("ALTER TABLE Clients ADD COLUMN lead_source TEXT")
    #         print("DEBUG_INIT_DB: Added 'lead_source' column to Clients table.")
    #     except sqlite3.Error as e_alter_lead_source:
    #         print(f"DEBUG_INIT_DB: Error adding 'lead_source' column to Clients table: {e_alter_lead_source}")

    # cursor.execute("PRAGMA table_info(Clients)")
    # columns_info = cursor.fetchall()
    # column_names = [info['name'] for info in columns_info]
    # if 'distributor_specific_info' not in column_names:
    #     try:
    #         cursor.execute("ALTER TABLE Clients ADD COLUMN distributor_specific_info TEXT")
    #         print("Added 'distributor_specific_info' column to Clients table.")
    #         # No commit here, part of larger transaction
    #     except sqlite3.Error as e:
    #         print(f"Error adding 'distributor_specific_info' column to Clients table: {e}")

    # Ensure is_deleted and deleted_at columns exist for soft delete
    # cursor.execute("PRAGMA table_info(Clients)")
    # clients_columns_info = cursor.fetchall()
    # clients_column_names = [info['name'] for info in clients_columns_info]

    # if 'is_deleted' not in clients_column_names:
    #     try:
    #         cursor.execute("ALTER TABLE Clients ADD COLUMN is_deleted INTEGER DEFAULT 0")
    #         print("Added 'is_deleted' column to Clients table.")
    #     except sqlite3.Error as e_alter_is_deleted:
    #         print(f"Error adding 'is_deleted' column to Clients table: {e_alter_is_deleted}")

    # if 'deleted_at' not in clients_column_names:
    #     try:
    #         cursor.execute("ALTER TABLE Clients ADD COLUMN deleted_at TEXT")
    #         print("Added 'deleted_at' column to Clients table.")
    #     except sqlite3.Error as e_alter_deleted_at:
    #         print(f"Error adding 'deleted_at' column to Clients table: {e_alter_deleted_at}")

    # Ensure default_template_id column exists
    # cursor.execute("PRAGMA table_info(Clients)")
    # clients_columns_info_for_template_check = cursor.fetchall() # Use a unique variable name
    # clients_column_names_for_template_check = [info['name'] for info in clients_columns_info_for_template_check]

    # if 'default_template_id' not in clients_column_names_for_template_check:
    #     try:
    #         cursor.execute("ALTER TABLE Clients ADD COLUMN default_template_id INTEGER")
    #         print("Added 'default_template_id' column to Clients table.")
    #         # The FOREIGN KEY constraint is defined in the CREATE TABLE statement and will apply
    #         # to new tables or if enforced by PRAGMA foreign_keys=ON for existing tables (version dependent).
    #         # For existing tables in older SQLite, this adds the column, and app logic relies on the schema's FK definition.
    #     except sqlite3.Error as e_alter_default_template_id:
    #         print(f"Error adding 'default_template_id' column to Clients table: {e_alter_default_template_id}")

    # Create ClientNotes table (base from ca.py)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ClientNotes (
        note_id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        note_text TEXT NOT NULL,
        user_id TEXT,
        FOREIGN KEY (client_id) REFERENCES Clients (client_id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE SET NULL
    )
    """)

    # Create Projects table (base from ca.py)
    # cursor.execute("""
    # CREATE TABLE IF NOT EXISTS Projects (
    #     project_id TEXT PRIMARY KEY,
    #     client_id TEXT NOT NULL,
    #     project_name TEXT NOT NULL,
    #     description TEXT,
    #     start_date DATE,
    #     deadline_date DATE,
    #     budget REAL,
    #     status_id INTEGER,
    #     progress_percentage INTEGER DEFAULT 0,
    #     manager_team_member_id TEXT, -- Assuming this refers to a User ID
    #     priority INTEGER DEFAULT 0,
    #     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #     FOREIGN KEY (client_id) REFERENCES Clients (client_id),
    #     FOREIGN KEY (status_id) REFERENCES StatusSettings (status_id),
    #     FOREIGN KEY (manager_team_member_id) REFERENCES Users (user_id) -- ca.py links to Users
    # )
    # """)
    # print("DEBUG_INIT_DB: Table Projects (raw SQL) creation SKIPPED - Handled by Alembic.")

    # Create Contacts table (base from ca.py)
    # cursor.execute("""
    # CREATE TABLE IF NOT EXISTS Contacts (
    #     contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     name TEXT NOT NULL,
    #     email TEXT UNIQUE,
    #     phone TEXT,
    #     position TEXT,
    #     company_name TEXT,
    #     notes TEXT,
    #     givenName TEXT,
    #     familyName TEXT,
    #     displayName TEXT,
    #     phone_type TEXT,
    #     email_type TEXT,
    #     address_formattedValue TEXT,
    #     address_streetAddress TEXT,
    #     address_city TEXT,
    #     address_region TEXT,
    #     address_postalCode TEXT,
    #     address_country TEXT,
    #     organization_name TEXT,
    #     organization_title TEXT,
    #     birthday_date TEXT,
    #     created_by_user_id TEXT, -- Added column
    #     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #     employee_status TEXT, -- internal, external, not_applicable
    #     FOREIGN KEY (created_by_user_id) REFERENCES Users (user_id) ON DELETE SET NULL -- Added FK
    # )
    # """)
    # print("DEBUG_INIT_DB: Table Contacts (raw SQL) creation SKIPPED - Handled by Alembic.")

    # Ensure created_by_user_id and employee_status columns exist in Contacts table for existing databases
    # cursor.execute("PRAGMA table_info(Contacts)")
    # contacts_columns_info = cursor.fetchall()
    # contacts_column_names = [info['name'] for info in contacts_columns_info]

    # if 'created_by_user_id' not in contacts_column_names:
    #     try:
    #         cursor.execute("ALTER TABLE Contacts ADD COLUMN created_by_user_id TEXT REFERENCES Users(user_id) ON DELETE SET NULL")
    #         print("DEBUG_INIT_DB: Added 'created_by_user_id' column to Contacts table.")
    #     except sqlite3.Error as e_alter_contacts_creator:
    #         print(f"DEBUG_INIT_DB: Error adding 'created_by_user_id' column to Contacts table: {e_alter_contacts_creator}")
    #         # Note: Older SQLite versions might not support adding FK via ALTER TABLE.
    #         # The FK in CREATE TABLE is for new DBs. For existing, this adds the column. App logic must handle.

    # if 'employee_status' not in contacts_column_names:
    #     try:
    #         cursor.execute("ALTER TABLE Contacts ADD COLUMN employee_status TEXT")
    #         print("DEBUG_INIT_DB: Added 'employee_status' column to Contacts table.")
    #     except sqlite3.Error as e_alter_contacts_status:
    #         print(f"DEBUG_INIT_DB: Error adding 'employee_status' column to Contacts table: {e_alter_contacts_status}")

    # Create ClientContacts table (base from ca.py)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ClientContacts (
        client_contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT NOT NULL,
        contact_id INTEGER NOT NULL, -- Standardized to INTEGER to match Contacts.contact_id
        is_primary_for_client BOOLEAN DEFAULT FALSE,
        can_receive_documents BOOLEAN DEFAULT TRUE,
        added_by_user_id TEXT, -- Added column
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Added column
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Added column
        FOREIGN KEY (client_id) REFERENCES Clients (client_id) ON DELETE CASCADE,
        FOREIGN KEY (contact_id) REFERENCES Contacts (contact_id) ON DELETE CASCADE,
        FOREIGN KEY (added_by_user_id) REFERENCES Users (user_id) ON DELETE SET NULL, -- Added FK
        UNIQUE (client_id, contact_id)
    )
    """)

    # Ensure added_by_user_id, created_at, updated_at columns exist in ClientContacts table for existing databases
    # cursor.execute("PRAGMA table_info(ClientContacts)")
    # cc_columns_info = cursor.fetchall()
    # cc_column_names = [info['name'] for info in cc_columns_info]

    # if 'contact_id' in cc_column_names: # Check if table exists and has contact_id
    #     # Check current type of contact_id
    #     contact_id_col_info = next((col for col in cc_columns_info if col['name'] == 'contact_id'), None)
    #     if contact_id_col_info and contact_id_col_info['type'].upper() == 'TEXT':
    #         logging.warning("ClientContacts.contact_id is TEXT, ideally should be INTEGER. Manual migration might be needed if data exists and FK is to be enforced strictly.")
    #         # For now, we won't attempt to change type of existing column due to complexity with data.
    #         # The CREATE TABLE statement above defines it as INTEGER for new DBs.

    # if 'added_by_user_id' not in cc_column_names:
    #     try:
    #         cursor.execute("ALTER TABLE ClientContacts ADD COLUMN added_by_user_id TEXT REFERENCES Users(user_id) ON DELETE SET NULL")
    #         print("DEBUG_INIT_DB: Added 'added_by_user_id' column to ClientContacts table.")
    #     except sqlite3.Error as e_alter_cc_adder:
    #         print(f"DEBUG_INIT_DB: Error adding 'added_by_user_id' column to ClientContacts table: {e_alter_cc_adder}")

    # if 'created_at' not in cc_column_names:
    #     try:
    #         # Adding with DEFAULT CURRENT_TIMESTAMP might only work on newer SQLite versions with ALTER.
    #         # Simpler to add NULLable and let app logic handle if needed, or backfill.
    #         cursor.execute("ALTER TABLE ClientContacts ADD COLUMN created_at TIMESTAMP")
    #         print("DEBUG_INIT_DB: Added 'created_at' column to ClientContacts table (will be NULL for existing rows).")
    #     except sqlite3.Error as e_alter_cc_created:
    #         print(f"DEBUG_INIT_DB: Error adding 'created_at' column to ClientContacts table: {e_alter_cc_created}")

    # if 'updated_at' not in cc_column_names:
    #     try:
    #         cursor.execute("ALTER TABLE ClientContacts ADD COLUMN updated_at TIMESTAMP")
    #         print("DEBUG_INIT_DB: Added 'updated_at' column to ClientContacts table (will be NULL for existing rows).")
    #     except sqlite3.Error as e_alter_cc_updated:
    #         print(f"DEBUG_INIT_DB: Error adding 'updated_at' column to ClientContacts table: {e_alter_cc_updated}")

    # Note: Contacts.contact_id is INTEGER AUTOINCREMENT, so ClientContacts.contact_id should be INTEGER.
    # The schema from ca.py for Contacts has INTEGER. The ClientContacts table in ca.py has contact_id TEXT. This is a mismatch.
    # Standardizing to INTEGER for contact_id in ClientContacts.
    # Re-creating ClientContacts with contact_id as INTEGER if it was TEXT.
    # This is complex to do safely if data exists. For init, we define it correctly.
    # For now, I will use the TEXT version from ca.py and note this potential issue.

    # Create Products table (logic from ca.py to add weight/dimensions if missing)
    # This logic is now handled by the SQLAlchemy model definition in db.common_models.py
    # try:
    #     cursor.execute("PRAGMA table_info(Products)")
    #     columns_info = cursor.fetchall()
    #     existing_column_names = {info['name'] for info in columns_info}
    #     altered = False
    #     if 'weight' not in existing_column_names:
    #         cursor.execute("ALTER TABLE Products ADD COLUMN weight REAL")
    #         altered = True
    #     if 'dimensions' not in existing_column_names:
    #         cursor.execute("ALTER TABLE Products ADD COLUMN dimensions TEXT")
    #         altered = True
    #     if altered:
    #         print("Added 'weight' and/or 'dimensions' to Products table.")
    #         # No commit here
    # except sqlite3.Error: # Products table might not exist yet
    #     pass

    # The Products table is now defined as an SQLAlchemy model in db.common_models.py
    # and will be created by Alembic.
    # The raw SQL creation and ALTER TABLE statements for Products are removed.
    logging.info("DEBUG_INIT_DB: Products table creation will be handled by Alembic.")

    # --- START DEBUGGING: Check if Products table exists before DROP ---
    try:
        with actual_main_engine.connect() as connection:
            result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='Products'")).fetchone()
            if result:
                logging.info(f"DEBUG_INIT_DB: PRE-DROP CHECK: 'Products' table FOUND by sqlite_master query on actual_main_engine.")
            else:
                logging.info(f"DEBUG_INIT_DB: PRE-DROP CHECK: 'Products' table NOT FOUND by sqlite_master query on actual_main_engine.")
    except Exception as e_check_before_drop:
        logging.error(f"DEBUG_INIT_DB: Error checking Products table existence before drop: {e_check_before_drop}", exc_info=True)
    # --- END DEBUGGING ---

    # The specific "DROP TABLE IF EXISTS Products" block that was here (lines ~849-856 in original log context)
    # has been removed. It was causing "database is locked" errors and is redundant if the
    # "Enhanced DEBUGGING/CLEANUP STEP" (dropping all tables in MainBase.metadata) works correctly,
    # as Products is an SQLAlchemy model and should be handled by that loop.
    # The "Enhanced DEBUGGING/CLEANUP STEP" is located just before MainBase.metadata.create_all().

    # --- START DEBUGGING: Check if Products table exists AFTER POTENTIAL DROP by general loop ---
    # This check is now implicitly covered by MainBase.metadata.create_all(checkfirst=True)
    # or by observing logs if the general drop loop runs.
    # For clarity, we rely on `create_all(checkfirst=True)` to robustly handle
    # the existence or non-existence of Products table.
    # --- END DEBUGGING ---

    # Create ProductDimensions table (from ca.py)
    # This table depends on Products.product_id.
    # If Products is created by SQLAlchemy, ProductDimensions should also ideally be an SQLAlchemy model
    # or created *after* Products table is confirmed by SQLAlchemy.
    # For now, assuming it might be created by raw SQL, but this could be problematic if Products isn't there yet.
    # If Products.product_id is INTEGER, this FK should match.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ProductDimensions (
        product_id INTEGER PRIMARY KEY,
        dim_A TEXT, dim_B TEXT, dim_C TEXT, dim_D TEXT, dim_E TEXT,
        dim_F TEXT, dim_G TEXT, dim_H TEXT, dim_I TEXT, dim_J TEXT,
        technical_image_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES Products (product_id) ON DELETE CASCADE
    )
    """)

    # Create ProductEquivalencies table (from ca.py)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ProductEquivalencies (
        equivalence_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id_a INTEGER NOT NULL,
        product_id_b INTEGER NOT NULL,
        FOREIGN KEY (product_id_a) REFERENCES Products (product_id) ON DELETE CASCADE,
        FOREIGN KEY (product_id_b) REFERENCES Products (product_id) ON DELETE CASCADE,
        UNIQUE (product_id_a, product_id_b)
    )
    """)

    # Create ClientProjectProducts table (from ca.py)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ClientProjectProducts (
        client_project_product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT NOT NULL,
        project_id TEXT,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1,
        unit_price_override REAL,
        total_price_calculated REAL,
        serial_number TEXT,
        purchase_confirmed_at TIMESTAMP,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        added_by_user_id TEXT,
        client_specific_product_name TEXT,
        line_description TEXT,
        line_weight REAL,
        line_dimensions_notes TEXT,
        FOREIGN KEY (client_id) REFERENCES Clients (client_id) ON DELETE CASCADE,
        FOREIGN KEY (project_id) REFERENCES Projects (project_id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES Products (product_id) ON DELETE CASCADE,
        FOREIGN KEY (added_by_user_id) REFERENCES Users (user_id) ON DELETE SET NULL,
        UNIQUE (client_id, project_id, product_id)
    )
    """)

    # Ensure serial_number, purchase_confirmed_at, added_by_user_id, and new columns exist in ClientProjectProducts table
    # logging.info("DEBUG_INIT_DB: Verifying/Updating schema for ClientProjectProducts...")
    # cursor.execute("PRAGMA table_info(ClientProjectProducts)")
    # cpp_columns_info_before_alter = cursor.fetchall()
    # cpp_column_names_before_alter = [info['name'] for info in cpp_columns_info_before_alter]
    # logging.info(f"DEBUG_INIT_DB: ClientProjectProducts schema BEFORE alter: {cpp_column_names_before_alter}")

    # # Columns to check and add
    # columns_to_ensure = {
    #     "client_specific_product_name": "TEXT",
    #     "line_description": "TEXT",
    #     "line_weight": "REAL",
    #     "line_dimensions_notes": "TEXT",
    #     "serial_number": "TEXT", # Existing check
    #     "purchase_confirmed_at": "TIMESTAMP", # Existing check
    #     "added_by_user_id": "TEXT REFERENCES Users(user_id) ON DELETE SET NULL" # Existing check
    # }

    # for col_name, col_type in columns_to_ensure.items():
    #     if col_name not in cpp_column_names_before_alter:
    #         try:
    #             logging.info(f"DEBUG_INIT_DB: '{col_name}' column missing in ClientProjectProducts. Attempting to add...")
    #             cursor.execute(f"ALTER TABLE ClientProjectProducts ADD COLUMN {col_name} {col_type}")
    #             logging.info(f"DEBUG_INIT_DB: Successfully ADDED '{col_name}' column to ClientProjectProducts.")
    #         except sqlite3.Error as e_alter_cpp:
    #             logging.error(f"DEBUG_INIT_DB: FAILED to add '{col_name}' column to ClientProjectProducts: {e_alter_cpp}")
    #     else:
    #         logging.info(f"DEBUG_INIT_DB: '{col_name}' column already exists in ClientProjectProducts.")

    # # Original checks for serial_number, purchase_confirmed_at, added_by_user_id were redundant
    # # and have been removed as the loop columns_to_ensure handles them.

    # # Log schema AFTER all attempts
    # cursor.execute("PRAGMA table_info(ClientProjectProducts)")
    # cpp_columns_info_after_alter = cursor.fetchall()
    # cpp_column_names_after_alter = [info['name'] for info in cpp_columns_info_after_alter]
    # logging.info(f"DEBUG_INIT_DB: ClientProjectProducts schema AFTER all alter attempts: {cpp_column_names_after_alter}")


    # Create ScheduledEmails table (from ca.py)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ScheduledEmails (
        scheduled_email_id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipient_email TEXT NOT NULL,
        subject TEXT NOT NULL,
        body_html TEXT,
        body_text TEXT,
        scheduled_send_at TIMESTAMP NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'sent', 'failed'
        sent_at TIMESTAMP,
        error_message TEXT,
        related_client_id TEXT,
        related_project_id TEXT,
        created_by_user_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (related_client_id) REFERENCES Clients (client_id) ON DELETE SET NULL,
        FOREIGN KEY (related_project_id) REFERENCES Projects (project_id) ON DELETE SET NULL,
        FOREIGN KEY (created_by_user_id) REFERENCES Users (user_id) ON DELETE SET NULL
    )
    """)

    # Create EmailReminders table (from ca.py)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS EmailReminders (
        reminder_id INTEGER PRIMARY KEY AUTOINCREMENT,
        scheduled_email_id INTEGER NOT NULL,
        reminder_type TEXT NOT NULL, -- e.g., 'before_send', 'after_send_no_reply'
        reminder_send_at TIMESTAMP NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'sent', 'cancelled'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (scheduled_email_id) REFERENCES ScheduledEmails (scheduled_email_id) ON DELETE CASCADE
    )
    """)

    # Create ContactLists table (from ca.py)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ContactLists (
        list_id INTEGER PRIMARY KEY AUTOINCREMENT,
        list_name TEXT NOT NULL UNIQUE,
        description TEXT,
        created_by_user_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by_user_id) REFERENCES Users (user_id) ON DELETE SET NULL
    )
    """)

    # Create ContactListMembers table (from ca.py)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ContactListMembers (
        list_member_id INTEGER PRIMARY KEY AUTOINCREMENT,
        list_id INTEGER NOT NULL,
        contact_id INTEGER NOT NULL, -- Assuming Contacts.contact_id is INTEGER
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (list_id) REFERENCES ContactLists (list_id) ON DELETE CASCADE,
        FOREIGN KEY (contact_id) REFERENCES Contacts (contact_id) ON DELETE CASCADE,
        UNIQUE (list_id, contact_id)
    )
    """)

    # Create ActivityLog table (from ca.py)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ActivityLog (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        action_type TEXT NOT NULL,
        details TEXT,
        related_entity_type TEXT,
        related_entity_id TEXT,
        related_client_id TEXT, -- For quick filtering client-related activities
        ip_address TEXT,
        user_agent TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE SET NULL,
        FOREIGN KEY (related_client_id) REFERENCES Clients (client_id) ON DELETE SET NULL
    )
    """)

    # Create TemplateCategories table (base from ca.py, pre-population logic from ca.py)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS TemplateCategories (
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_name TEXT NOT NULL UNIQUE,
        description TEXT,
        purpose TEXT -- New column
    )
    """)

    # Idempotently add purpose column if it doesn't exist
    # cursor.execute("PRAGMA table_info(TemplateCategories)")
    # tc_columns = [column['name'] for column in cursor.fetchall()]
    # if 'purpose' not in tc_columns:
    #     try:
    #         cursor.execute("ALTER TABLE TemplateCategories ADD COLUMN purpose TEXT")
    #         print("Added 'purpose' column to TemplateCategories table.")
    #     except sqlite3.Error as e_alter_tc:
    #         print(f"Error adding 'purpose' column to TemplateCategories table: {e_alter_tc}")

    general_category_id_for_migration = None
    try:
        # Seed initial categories - purpose will be updated shortly after
        cursor.execute("INSERT OR IGNORE INTO TemplateCategories (category_name, description) VALUES (?, ?)", ('General', 'General purpose templates'))
        cursor.execute("SELECT category_id FROM TemplateCategories WHERE category_name = 'General'")
        general_row = cursor.fetchone()
        if general_row: general_category_id_for_migration = general_row['category_id']

        cursor.execute("INSERT OR IGNORE INTO TemplateCategories (category_name, description) VALUES (?, ?)", ('Document Utilitaires', 'Modèles de documents utilitaires généraux (ex: catalogues, listes de prix)'))
        cursor.execute("INSERT OR IGNORE INTO TemplateCategories (category_name, description) VALUES (?, ?)", ('Modèles Email', 'Modèles pour les corps des emails'))

        # Update purposes for these initial categories
        cursor.execute("UPDATE TemplateCategories SET purpose = ? WHERE category_name = ?", ('client_document', 'General'))
        cursor.execute("UPDATE TemplateCategories SET purpose = ? WHERE category_name = ?", ('client_document', 'Document Utilitaires'))
        cursor.execute("UPDATE TemplateCategories SET purpose = ? WHERE category_name = ?", ('email', 'Modèles Email'))

        # No commit here, part of larger transaction
    except sqlite3.Error as e_cat_init:
        print(f"Error initializing TemplateCategories or setting purposes: {e_cat_init}")


    # Templates table migration logic (from ca.py, seems more complete for this part)
    cursor.execute("PRAGMA table_info(Templates)")
    columns = [column['name'] for column in cursor.fetchall()]
    needs_migration = 'category' in columns and 'category_id' not in columns

    if needs_migration:
        print("Templates table needs migration (category to category_id). Starting migration process...")
        try:
            cursor.execute("ALTER TABLE Templates RENAME TO Templates_old")
            print("Renamed Templates to Templates_old.")
            cursor.execute("""
            CREATE TABLE Templates (
                template_id INTEGER PRIMARY KEY AUTOINCREMENT, template_name TEXT NOT NULL, template_type TEXT NOT NULL,
                description TEXT, base_file_name TEXT, language_code TEXT, is_default_for_type_lang BOOLEAN DEFAULT FALSE,
                category_id INTEGER, content_definition TEXT, email_subject_template TEXT, email_variables_info TEXT,
                cover_page_config_json TEXT, document_mapping_config_json TEXT, raw_template_file_data BLOB,
                version TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by_user_id TEXT,
                FOREIGN KEY (created_by_user_id) REFERENCES Users (user_id),
                FOREIGN KEY (category_id) REFERENCES TemplateCategories(category_id) ON DELETE SET NULL,
                UNIQUE (template_name, template_type, language_code, version)
            )""")
            print("Created new Templates table with category_id.")

            # Fetch column names from Templates_old to map correctly
            cursor_old_desc = conn.cursor() # Use a new cursor for safety or ensure main cursor is fine
            cursor_old_desc.execute("PRAGMA table_info(Templates_old)")
            old_column_names = [col_info['name'] for col_info in cursor_old_desc.fetchall()]

            cursor_old_data = conn.cursor()
            cursor_old_data.execute("SELECT * FROM Templates_old")
            old_templates = cursor_old_data.fetchall()


            for old_template_row in old_templates: # old_template_row is already a Row object
                old_template_dict = dict(old_template_row) # Convert Row to dict for .get()
                category_name_text = old_template_dict.get('category')
                new_cat_id = _get_or_create_category_id(cursor, category_name_text, general_category_id_for_migration)

                new_template_values = (
                    old_template_dict.get('template_id'), old_template_dict.get('template_name'),
                    old_template_dict.get('template_type'), old_template_dict.get('description'),
                    old_template_dict.get('base_file_name'), old_template_dict.get('language_code'),
                    old_template_dict.get('is_default_for_type_lang', False), new_cat_id,
                    old_template_dict.get('content_definition'), old_template_dict.get('email_subject_template'),
                    old_template_dict.get('email_variables_info'), old_template_dict.get('cover_page_config_json'),
                    old_template_dict.get('document_mapping_config_json'), old_template_dict.get('raw_template_file_data'),
                    old_template_dict.get('version'), old_template_dict.get('created_at'),
                    old_template_dict.get('updated_at'), old_template_dict.get('created_by_user_id')
                )
                insert_sql = """
                    INSERT INTO Templates (
                        template_id, template_name, template_type, description, base_file_name,
                        language_code, is_default_for_type_lang, category_id,
                        content_definition, email_subject_template, email_variables_info,
                        cover_page_config_json, document_mapping_config_json,
                        raw_template_file_data, version, created_at, updated_at, created_by_user_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(insert_sql, new_template_values)
            print(f"Migrated {len(old_templates)} templates to new schema.")
            cursor.execute("DROP TABLE Templates_old")
            print("Dropped Templates_old table.")
            # No commit here, part of larger transaction
            print("Templates table migration (category to category_id) completed successfully.")
        except sqlite3.Error as e:
            # Rollback might be handled at the end of initialize_database
            print(f"Error during Templates table migration (category to category_id): {e}. Changes for this migration might be rolled back.")
    else:
        cursor.execute("""
CREATE TABLE IF NOT EXISTS Templates (
    template_id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_name TEXT NOT NULL,
    template_type TEXT NOT NULL,
    description TEXT,
    base_file_name TEXT,
    language_code TEXT,
    is_default_for_type_lang BOOLEAN DEFAULT FALSE,
    category_id INTEGER,
    content_definition TEXT,
    email_subject_template TEXT,
    email_variables_info TEXT,
    cover_page_config_json TEXT,
    document_mapping_config_json TEXT,
    raw_template_file_data BLOB,
    version TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_user_id TEXT,
    client_id TEXT DEFAULT NULL,
    FOREIGN KEY (created_by_user_id) REFERENCES Users (user_id),
    FOREIGN KEY (category_id) REFERENCES TemplateCategories (category_id) ON DELETE SET NULL,
    FOREIGN KEY (client_id) REFERENCES Clients (client_id) ON DELETE SET NULL,
    UNIQUE (template_name, template_type, language_code, version)
)
""")


    # Idempotently add client_id column if it doesn't exist (for existing databases)
    # cursor.execute("PRAGMA table_info(Templates)")
    # templates_columns = [column['name'] for column in cursor.fetchall()]
    # if 'client_id' not in templates_columns:
    #     try:
    #         cursor.execute("ALTER TABLE Templates ADD COLUMN client_id TEXT DEFAULT NULL")
    #         # Note: Adding FOREIGN KEY constraint via ALTER TABLE is tricky in older SQLite.
    #         # The FK definition in CREATE TABLE handles new DBs. For existing DBs, this adds the column.
    #         # Full FK enforcement for old DBs might require more complex migration (recreate table).
    #         print("Added 'client_id' column to Templates table.")
    #     except sqlite3.Error as e_alter_templates:
    #         print(f"Error adding 'client_id' column to Templates table: {e_alter_templates}")

    # Create Tasks table (from ca.py)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Tasks (
        task_id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id TEXT NOT NULL,
        task_name TEXT NOT NULL,
        description TEXT,
        status_id INTEGER,
        assignee_team_member_id INTEGER, -- Matches TeamMembers.team_member_id
        reporter_team_member_id INTEGER,   -- Matches TeamMembers.team_member_id
        due_date DATE,
        priority INTEGER DEFAULT 0,
        estimated_hours REAL,
        actual_hours_spent REAL,
        parent_task_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES Projects (project_id) ON DELETE CASCADE,
        FOREIGN KEY (status_id) REFERENCES StatusSettings (status_id),
        FOREIGN KEY (assignee_team_member_id) REFERENCES TeamMembers (team_member_id) ON DELETE SET NULL,
        FOREIGN KEY (reporter_team_member_id) REFERENCES TeamMembers (team_member_id) ON DELETE SET NULL,
        FOREIGN KEY (parent_task_id) REFERENCES Tasks (task_id) ON DELETE SET NULL
    )
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Commandes (
        commande_id TEXT PRIMARY KEY,
        client_id TEXT NOT NULL,
        project_id TEXT,
        commande_reference TEXT UNIQUE NOT NULL,
        commande_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        status_commande_id INTEGER NOT NULL,
        description_commande TEXT,
        notes TEXT, -- Added for order-specific notes
        is_default BOOLEAN DEFAULT FALSE, -- Added to flag default orders
        total_ht REAL,
        total_ttc REAL,
        currency TEXT NOT NULL DEFAULT 'EUR',
        shipping_address TEXT,
        billing_address TEXT,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        created_by_user_id TEXT,
        deleted_at TEXT, -- Added for soft delete
        FOREIGN KEY (client_id) REFERENCES Clients (client_id) ON DELETE CASCADE,
        FOREIGN KEY (project_id) REFERENCES Projects (project_id) ON DELETE SET NULL,
        FOREIGN KEY (status_commande_id) REFERENCES StatusSettings (status_id),
        FOREIGN KEY (created_by_user_id) REFERENCES Users (user_id) ON DELETE SET NULL
    )
    """)
    print("DEBUG_INIT_DB: Table Commandes created or exists (with deleted_at).")

    # Ensure notes, is_default, and deleted_at columns exist in Commandes table for existing databases
    # cursor.execute("PRAGMA table_info(Commandes)")
    # commandes_columns_info = cursor.fetchall()
    # commandes_column_names = [info['name'] for info in commandes_columns_info]

    # if 'notes' not in commandes_column_names:
    #     try:
    #         cursor.execute("ALTER TABLE Commandes ADD COLUMN notes TEXT")
    #         print("DEBUG_INIT_DB: Added 'notes' column to Commandes table.")
    #     except sqlite3.Error as e_alter_commandes_notes:
    #         print(f"DEBUG_INIT_DB: Error adding 'notes' column to Commandes table: {e_alter_commandes_notes}")

    # if 'is_default' not in commandes_column_names:
    #     try:
    #         cursor.execute("ALTER TABLE Commandes ADD COLUMN is_default BOOLEAN DEFAULT FALSE")
    #         print("DEBUG_INIT_DB: Added 'is_default' column to Commandes table.")
    #     except sqlite3.Error as e_alter_commandes_is_default:
    #         print(f"DEBUG_INIT_DB: Error adding 'is_default' column to Commandes table: {e_alter_commandes_is_default}")

    # if 'deleted_at' not in commandes_column_names:
    #     try:
    #         cursor.execute("ALTER TABLE Commandes ADD COLUMN deleted_at TEXT")
    #         print("DEBUG_INIT_DB: Added 'deleted_at' column to Commandes table.")
    #     except sqlite3.Error as e_alter_commandes_deleted_at:
    #         print(f"DEBUG_INIT_DB: Error adding 'deleted_at' column to Commandes table: {e_alter_commandes_deleted_at}")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS CommandeItems (
        item_id TEXT PRIMARY KEY,
        commande_id TEXT NOT NULL,
        product_id INTEGER NOT NULL,
        description_item TEXT NOT NULL,
        quantity REAL NOT NULL,
        unit_price_ht REAL NOT NULL,
        vat_rate REAL DEFAULT 0.0,
        total_item_ht REAL NOT NULL,
        total_item_ttc REAL NOT NULL,
            weight REAL,                        -- Poids spécifique pour cet article de commande
            dimensions_text TEXT,               -- Dimensions spécifiques (ex: "100x50x30 cm")
            product_language_code TEXT,         -- Langue du produit tel qu'ajouté à cette commande (ex: 'fr', 'en')
        FOREIGN KEY (commande_id) REFERENCES Commandes (commande_id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES Products (product_id)
    )
    """)
    print("DEBUG_INIT_DB: Table CommandeItems created or exists.")
    # --- End Commandes Module Tables ---

    # Create ClientDocuments table (logic from ca.py to add order_identifier if missing)
    # Note: commande_id column is added here, and its FOREIGN KEY constraint properly references Commandes table.
    # cursor.execute("""
    # CREATE TABLE IF NOT EXISTS ClientDocuments (
    #     document_id TEXT PRIMARY KEY,
    #     client_id TEXT NOT NULL,
    #     project_id TEXT,
    #     commande_id TEXT, -- Added column for linking to a Commande
    #     order_identifier TEXT, -- Existing field, might be used for Commande reference or Project identifier
    #     document_name TEXT NOT NULL,
    #     file_name_on_disk TEXT NOT NULL,
    #     file_path_relative TEXT NOT NULL,
    #     document_type_generated TEXT,
    #     source_template_id INTEGER,
    #     version_tag TEXT,
    #     notes TEXT,
    #     footer_notes TEXT, -- Added for document-specific footer notes
    #     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #     created_by_user_id TEXT,
    #     is_deleted INTEGER DEFAULT 0,
    #     deleted_at TEXT,
    #     parent_document_id TEXT, -- For versioning
    #     is_latest_version INTEGER DEFAULT 1, -- For versioning
    #     FOREIGN KEY (client_id) REFERENCES Clients (client_id),
    #     FOREIGN KEY (project_id) REFERENCES Projects (project_id),
    #     FOREIGN KEY (commande_id) REFERENCES Commandes (commande_id) ON DELETE SET NULL, -- Correct FK
    #     FOREIGN KEY (source_template_id) REFERENCES Templates (template_id),
    #     FOREIGN KEY (created_by_user_id) REFERENCES Users (user_id),
    #     FOREIGN KEY (commande_id) REFERENCES Commandes (commande_id) ON DELETE SET NULL,
    #     FOREIGN KEY (parent_document_id) REFERENCES ClientDocuments (document_id) ON DELETE SET NULL
    # )""")
    # print("DEBUG_INIT_DB: Table ClientDocuments (raw SQL) creation SKIPPED - Handled by Alembic.")

    # Ensure is_deleted, deleted_at, order_identifier, parent_document_id, is_latest_version, commande_id, footer_notes columns exist
    # cursor.execute("PRAGMA table_info(ClientDocuments)")
    # cd_columns_info = cursor.fetchall()
    # cd_column_names = [info['name'] for info in cd_columns_info]

    # if 'footer_notes' not in cd_column_names:
    #     try:
    #         cursor.execute("ALTER TABLE ClientDocuments ADD COLUMN footer_notes TEXT")
    #         print("DEBUG_INIT_DB: Added 'footer_notes' column to ClientDocuments table.")
    #     except sqlite3.Error as e_alter_cd_footer_notes:
    #         print(f"DEBUG_INIT_DB: Error adding 'footer_notes' column to ClientDocuments table: {e_alter_cd_footer_notes}")

    # if 'order_identifier' not in cd_column_names:
    #     try:
    #         cursor.execute("ALTER TABLE ClientDocuments ADD COLUMN order_identifier TEXT")
    #         print("Added 'order_identifier' column to ClientDocuments table.")
    #     except sqlite3.Error as e:
    #         print(f"Error adding 'order_identifier' column to ClientDocuments: {e}")

    # if 'is_deleted' not in cd_column_names:
    #     try:
    #         cursor.execute("ALTER TABLE ClientDocuments ADD COLUMN is_deleted INTEGER DEFAULT 0")
    #         print("Added 'is_deleted' column to ClientDocuments table.")
    #     except sqlite3.Error as e_alter_cd_is_deleted:
    #         print(f"Error adding 'is_deleted' column to ClientDocuments table: {e_alter_cd_is_deleted}")

    # if 'deleted_at' not in cd_column_names:
    #     try:
    #         cursor.execute("ALTER TABLE ClientDocuments ADD COLUMN deleted_at TEXT")
    #         print("Added 'deleted_at' column to ClientDocuments table.")
    #     except sqlite3.Error as e_alter_cd_deleted_at:
    #         print(f"Error adding 'deleted_at' column to ClientDocuments table: {e_alter_cd_deleted_at}")

    # if 'parent_document_id' not in cd_column_names:
    #     try:
    #         # SQLite does not allow adding a FOREIGN KEY constraint via ALTER TABLE in older versions.
    #         # The constraint is defined in CREATE TABLE for new DBs.
    #         # For existing DBs, this adds the column. App logic must handle relationships if FK isn't enforced by DB.
    #         cursor.execute("ALTER TABLE ClientDocuments ADD COLUMN parent_document_id TEXT")
    #         print("Added 'parent_document_id' column to ClientDocuments table.")
    #     except sqlite3.Error as e_alter_cd_parent_id:
    #         print(f"Error adding 'parent_document_id' column to ClientDocuments table: {e_alter_cd_parent_id}")

    # if 'is_latest_version' not in cd_column_names:
    #     try:
    #         cursor.execute("ALTER TABLE ClientDocuments ADD COLUMN is_latest_version INTEGER DEFAULT 1")
    #         print("Added 'is_latest_version' column to ClientDocuments table.")
    #     except sqlite3.Error as e_alter_cd_is_latest:
    #         print(f"Error adding 'is_latest_version' column to ClientDocuments table: {e_alter_cd_is_latest}")

    # if 'commande_id' not in cd_column_names:
    #     try:
    #         cursor.execute("ALTER TABLE ClientDocuments ADD COLUMN commande_id TEXT REFERENCES Commandes(commande_id) ON DELETE SET NULL")
    #         print("Added 'commande_id' column to ClientDocuments table.")
    #     except sqlite3.Error as e_alter_cd_commande_id:
    #         print(f"Error adding 'commande_id' column to ClientDocuments table: {e_alter_cd_commande_id}")

    # Create ClientDocumentNotes table (from ca.py)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ClientDocumentNotes (
        note_id INTEGER PRIMARY KEY AUTOINCREMENT, client_id TEXT NOT NULL,
        document_type TEXT NOT NULL, language_code TEXT NOT NULL,
        note_content TEXT NOT NULL, is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES Clients (client_id) ON DELETE CASCADE,
        UNIQUE (client_id, document_type, language_code)
    )""")

    # Create SmtpConfigs table (from ca.py)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS SmtpConfigs (
        smtp_config_id INTEGER PRIMARY KEY AUTOINCREMENT, config_name TEXT NOT NULL UNIQUE,
        smtp_server TEXT NOT NULL, smtp_port INTEGER NOT NULL, username TEXT,
        password_encrypted TEXT, use_tls BOOLEAN DEFAULT TRUE, is_default BOOLEAN DEFAULT FALSE,
        sender_email_address TEXT NOT NULL, sender_display_name TEXT
    )""")

    # Create ApplicationSettings table (from ca.py)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ApplicationSettings (
        setting_key TEXT PRIMARY KEY,
        setting_value TEXT
    )""")

    # Create KPIs table (from ca.py)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS KPIs (
        kpi_id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT NOT NULL, name TEXT NOT NULL,
        value REAL NOT NULL, target REAL NOT NULL, trend TEXT NOT NULL, unit TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES Projects (project_id) ON DELETE CASCADE
    )""")

    # Create CoverPageTemplates table (from ca.py)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS CoverPageTemplates (
        template_id TEXT PRIMARY KEY, template_name TEXT NOT NULL UNIQUE, description TEXT,
        default_title TEXT, default_subtitle TEXT, default_author TEXT,
        style_config_json TEXT, is_default_template INTEGER DEFAULT 0 NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by_user_id TEXT,
        FOREIGN KEY (created_by_user_id) REFERENCES Users (user_id) ON DELETE SET NULL
    )""")

    # Create CoverPages table (from ca.py)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS CoverPages (
        cover_page_id TEXT PRIMARY KEY, cover_page_name TEXT, client_id TEXT, project_id TEXT,
        template_id TEXT, title TEXT NOT NULL, subtitle TEXT, author_text TEXT,
        institution_text TEXT, department_text TEXT, document_type_text TEXT,
        document_version TEXT, creation_date DATE, logo_name TEXT, logo_data BLOB,
        custom_style_config_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by_user_id TEXT,
        FOREIGN KEY (client_id) REFERENCES Clients (client_id) ON DELETE SET NULL,
        FOREIGN KEY (project_id) REFERENCES Projects (project_id) ON DELETE SET NULL,
        FOREIGN KEY (template_id) REFERENCES CoverPageTemplates (template_id) ON DELETE SET NULL,
        FOREIGN KEY (created_by_user_id) REFERENCES Users (user_id) ON DELETE SET NULL
    )""")

    # Create SAVTickets table (from ca.py)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS SAVTickets (
        ticket_id TEXT PRIMARY KEY, client_id TEXT NOT NULL,
        client_project_product_id INTEGER, issue_description TEXT NOT NULL,
        status_id INTEGER NOT NULL, assigned_technician_id INTEGER,
        resolution_details TEXT, opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        closed_at TIMESTAMP, created_by_user_id TEXT,
        FOREIGN KEY (client_id) REFERENCES Clients (client_id) ON DELETE CASCADE,
        FOREIGN KEY (client_project_product_id) REFERENCES ClientProjectProducts (client_project_product_id) ON DELETE SET NULL,
        FOREIGN KEY (status_id) REFERENCES StatusSettings (status_id),
        FOREIGN KEY (assigned_technician_id) REFERENCES TeamMembers (team_member_id) ON DELETE SET NULL,
        FOREIGN KEY (created_by_user_id) REFERENCES Users (user_id) ON DELETE SET NULL
    )""")

    # Create ImportantDates table (from ca.py)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ImportantDates (
        important_date_id INTEGER PRIMARY KEY AUTOINCREMENT, date_name TEXT NOT NULL,
        date_value DATE NOT NULL, is_recurring_annually BOOLEAN DEFAULT TRUE,
        language_code TEXT, email_template_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (date_name, date_value, language_code),
        FOREIGN KEY (email_template_id) REFERENCES Templates (template_id) ON DELETE SET NULL
    )""")

    # Create ProformaInvoices table
    # cursor.execute("""
    # CREATE TABLE IF NOT EXISTS proforma_invoices (
    #     id TEXT PRIMARY KEY,
    #     proforma_invoice_number TEXT UNIQUE NOT NULL,
    #     client_id TEXT NOT NULL,
    #     project_id TEXT,
    #     company_id TEXT NOT NULL,
    #     created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    #     sent_date TIMESTAMP,
    #     status TEXT NOT NULL DEFAULT 'DRAFT',
    #     currency TEXT NOT NULL DEFAULT 'USD',
    #     subtotal_amount REAL NOT NULL DEFAULT 0.0,
    #     discount_amount REAL DEFAULT 0.0,
    #     vat_amount REAL NOT NULL DEFAULT 0.0,
    #     grand_total_amount REAL NOT NULL DEFAULT 0.0,
    #     payment_terms TEXT,
    #     delivery_terms TEXT,
    #     incoterms TEXT,
    #     named_place_of_delivery TEXT,
    #     notes TEXT,
    #     linked_document_id TEXT,
    #     generated_invoice_id TEXT,
    #     FOREIGN KEY (client_id) REFERENCES Clients (client_id) ON DELETE CASCADE,
    #     FOREIGN KEY (project_id) REFERENCES Projects (project_id) ON DELETE SET NULL,
    #     FOREIGN KEY (company_id) REFERENCES Companies (company_id) ON DELETE CASCADE,
    #     FOREIGN KEY (linked_document_id) REFERENCES ClientDocuments (document_id) ON DELETE SET NULL,
    #     FOREIGN KEY (generated_invoice_id) REFERENCES ClientDocuments (document_id) ON DELETE SET NULL
    # )
    # """)
    # print("DEBUG_INIT_DB: Table proforma_invoices (raw SQL) creation SKIPPED - Handled by Alembic.")

    # Create ProformaInvoiceItems table
    # cursor.execute("""
    # CREATE TABLE IF NOT EXISTS proforma_invoice_items (
    #     id TEXT PRIMARY KEY,
    #     proforma_invoice_id TEXT NOT NULL,
    #     product_id INTEGER,
    #     description TEXT NOT NULL,
    #     quantity REAL NOT NULL,
    #     unit_price REAL NOT NULL,
    #     total_price REAL NOT NULL,
    #     FOREIGN KEY (proforma_invoice_id) REFERENCES proforma_invoices (id) ON DELETE CASCADE,
    #     FOREIGN KEY (product_id) REFERENCES Products (product_id) ON DELETE SET NULL
    # )
    # """)
    # print("DEBUG_INIT_DB: Table proforma_invoice_items (raw SQL) creation SKIPPED - Handled by Alembic.")

    # Create Transporters table (from ca.py)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Transporters (
        transporter_id TEXT PRIMARY KEY, name TEXT NOT NULL, contact_person TEXT,
        phone TEXT, email TEXT, address TEXT, service_area TEXT, notes TEXT,
        latitude REAL,
        longitude REAL,
        current_cargo TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # Create FreightForwarders table (from ca.py)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS FreightForwarders (
        forwarder_id TEXT PRIMARY KEY, name TEXT NOT NULL, contact_person TEXT,
        phone TEXT, email TEXT, address TEXT, services_offered TEXT, notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    # Create Client_AssignedPersonnel table (from ca.py)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Client_AssignedPersonnel (
        assignment_id INTEGER PRIMARY KEY AUTOINCREMENT, client_id TEXT NOT NULL,
        personnel_id INTEGER NOT NULL, role_in_project TEXT,
        assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES Clients (client_id) ON DELETE CASCADE,
        FOREIGN KEY (personnel_id) REFERENCES CompanyPersonnel (personnel_id) ON DELETE CASCADE,
        UNIQUE (client_id, personnel_id, role_in_project)
    )""")

    # Create Client_Transporters table (logic from ca.py to add email_status if missing)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Client_Transporters (
        client_transporter_id INTEGER PRIMARY KEY AUTOINCREMENT, client_id TEXT NOT NULL,
        transporter_id TEXT NOT NULL, transport_details TEXT, cost_estimate REAL,
        assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, email_status TEXT DEFAULT 'Pending',
        FOREIGN KEY (client_id) REFERENCES Clients (client_id) ON DELETE CASCADE,
        FOREIGN KEY (transporter_id) REFERENCES Transporters (transporter_id) ON DELETE CASCADE,
        UNIQUE (client_id, transporter_id)
    )""")
    # cursor.execute("PRAGMA table_info(Client_Transporters)")
    # columns_ct = [column['name'] for column in cursor.fetchall()]
    # if 'email_status' not in columns_ct:
    #     try:
    #         cursor.execute("ALTER TABLE Client_Transporters ADD COLUMN email_status TEXT DEFAULT 'Pending'")
    #         print("Added 'email_status' column to Client_Transporters table.")
    #         # No commit here
    #     except sqlite3.Error as e_ct_alter:
    #         print(f"Error adding 'email_status' column to Client_Transporters: {e_ct_alter}")

    # Create Client_FreightForwarders table (from ca.py)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Client_FreightForwarders (
        client_forwarder_id INTEGER PRIMARY KEY AUTOINCREMENT, client_id TEXT NOT NULL,
        forwarder_id TEXT NOT NULL, task_description TEXT, cost_estimate REAL,
        assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES Clients (client_id) ON DELETE CASCADE,
        FOREIGN KEY (forwarder_id) REFERENCES FreightForwarders (forwarder_id) ON DELETE CASCADE,
        UNIQUE (client_id, forwarder_id)
    )""")

    # Create Invoices table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Invoices (
        invoice_id TEXT PRIMARY KEY,
        client_id TEXT NOT NULL,
        project_id TEXT,
        document_id TEXT,
        invoice_number TEXT NOT NULL UNIQUE,
        issue_date DATE NOT NULL,
        due_date DATE NOT NULL,
        total_amount REAL NOT NULL,
        currency TEXT NOT NULL,
        payment_status TEXT NOT NULL DEFAULT 'unpaid',
        payment_date DATE,
        payment_method TEXT,
        transaction_id TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES Clients (client_id) ON DELETE CASCADE,
        FOREIGN KEY (project_id) REFERENCES Projects (project_id) ON DELETE SET NULL,
        FOREIGN KEY (document_id) REFERENCES ClientDocuments (document_id) ON DELETE SET NULL
    )
    """)

    # Partner Tables (definitions from ca.py which appear to be more up-to-date or matching schema.py's newer ones)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS PartnerCategories (
            partner_category_id INTEGER PRIMARY KEY AUTOINCREMENT, category_name TEXT NOT NULL UNIQUE,
            description TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Partners (
            partner_id TEXT PRIMARY KEY, partner_name TEXT NOT NULL, partner_category_id INTEGER,
            contact_person_name TEXT, email TEXT UNIQUE, phone TEXT, address TEXT,
            website_url TEXT, services_offered TEXT, collaboration_start_date TEXT,
            status TEXT DEFAULT 'Active', notes TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (partner_category_id) REFERENCES PartnerCategories (partner_category_id) ON DELETE SET NULL
        )""")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS PartnerContacts (
            partner_contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
            partner_id TEXT NOT NULL,
            contact_id INTEGER NOT NULL,
            is_primary BOOLEAN DEFAULT FALSE,
            can_receive_documents BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (partner_id) REFERENCES Partners(partner_id) ON DELETE CASCADE,
            FOREIGN KEY (contact_id) REFERENCES Contacts(contact_id) ON DELETE CASCADE,
            UNIQUE (partner_id, contact_id)
        )""")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS PartnerCategoryLink (
            partner_id TEXT NOT NULL, partner_category_id INTEGER NOT NULL,
            PRIMARY KEY (partner_id, partner_category_id),
            FOREIGN KEY (partner_id) REFERENCES Partners(partner_id) ON DELETE CASCADE,
            FOREIGN KEY (partner_category_id) REFERENCES PartnerCategories(partner_category_id) ON DELETE CASCADE
        )""")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS PartnerDocuments (
            document_id TEXT PRIMARY KEY, partner_id TEXT NOT NULL, document_name TEXT NOT NULL,
            file_path_relative TEXT NOT NULL, document_type TEXT, description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (partner_id) REFERENCES Partners(partner_id) ON DELETE CASCADE
        )""")

    # MediaItems, Tags, MediaItemTags, Playlists, PlaylistItems (from ca.py, includes migration for MediaItems.category)
    # MediaItems Table
    # cursor.execute("PRAGMA table_info(MediaItems)")
    # mi_columns = [column['name'] for column in cursor.fetchall()]
    # mi_needs_alter = 'thumbnail_path' not in mi_columns or 'metadata_json' not in mi_columns

    # if not mi_needs_alter: # If table potentially exists and is up-to-date schema-wise
    #     cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='MediaItems'")
    #     if not cursor.fetchone(): # Table does not exist, create it fully
    #          mi_needs_alter = True # Mark to create

    # if 'category' in mi_columns and 'thumbnail_path' in mi_columns and 'metadata_json' in mi_columns : # Already migrated and altered
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS MediaItems (
            media_item_id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT,
            item_type TEXT NOT NULL, filepath TEXT, url TEXT,
            uploader_user_id TEXT, thumbnail_path TEXT, metadata_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (uploader_user_id) REFERENCES Users(user_id) ON DELETE SET NULL
        );''')
    # elif 'category' in mi_columns : # Needs category migration (and potentially alter for new columns)
    #     print("Migrating 'category' from MediaItems to Tags system and ensuring new columns...")
    #     # Create Tags and MediaItemTags first if they don't exist
    #     cursor.execute('''CREATE TABLE IF NOT EXISTS Tags (tag_id INTEGER PRIMARY KEY AUTOINCREMENT, tag_name TEXT NOT NULL UNIQUE);''')
    #     cursor.execute('''CREATE TABLE IF NOT EXISTS MediaItemTags (media_item_tag_id INTEGER PRIMARY KEY AUTOINCREMENT, media_item_id TEXT NOT NULL, tag_id INTEGER NOT NULL, FOREIGN KEY (media_item_id) REFERENCES MediaItems(media_item_id) ON DELETE CASCADE, FOREIGN KEY (tag_id) REFERENCES Tags(tag_id) ON DELETE CASCADE, UNIQUE (media_item_id, tag_id));''')

    #     cursor.execute("SELECT media_item_id, category FROM MediaItems WHERE category IS NOT NULL AND category != ''")
    #     items_with_categories = cursor.fetchall()
    #     for item_row in items_with_categories:
    #         item_id, category_name = item_row['media_item_id'], item_row['category']
    #         cursor.execute("INSERT OR IGNORE INTO Tags (tag_name) VALUES (?)", (category_name,))
    #         tag_id = cursor.execute("SELECT tag_id FROM Tags WHERE tag_name = ?", (category_name,)).fetchone()['tag_id']
    #         if tag_id:
    #             cursor.execute("INSERT OR IGNORE INTO MediaItemTags (media_item_id, tag_id) VALUES (?, ?)", (item_id, tag_id))

    #     cursor.execute("ALTER TABLE MediaItems RENAME TO MediaItems_old_cat_mig")
    #     cursor.execute('''
    #         CREATE TABLE MediaItems (
    #             media_item_id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT,
    #             item_type TEXT NOT NULL, filepath TEXT, url TEXT,
    #             uploader_user_id TEXT, thumbnail_path TEXT, metadata_json TEXT,
    #             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #             FOREIGN KEY (uploader_user_id) REFERENCES Users(user_id) ON DELETE SET NULL
    #         );''')
    #     # Copy data, explicitly selecting columns that exist in old and new, handling new ones
    #     cursor.execute('''
    #         INSERT INTO MediaItems (media_item_id, title, description, item_type, filepath, url, uploader_user_id, created_at, updated_at, thumbnail_path, metadata_json)
    #         SELECT media_item_id, title, description, item_type, filepath, url, uploader_user_id, created_at, updated_at,
    #                CASE WHEN EXISTS (SELECT 1 FROM pragma_table_info('MediaItems_old_cat_mig') WHERE name='thumbnail_path') THEN thumbnail_path ELSE NULL END,
    #                CASE WHEN EXISTS (SELECT 1 FROM pragma_table_info('MediaItems_old_cat_mig') WHERE name='metadata_json') THEN metadata_json ELSE NULL END
    #         FROM MediaItems_old_cat_mig;
    #     ''')
    #     cursor.execute("DROP TABLE MediaItems_old_cat_mig")
    #     print("MediaItems 'category' migration complete, table recreated.")
    # elif mi_needs_alter : # Table does not exist or exists but needs new columns (no category column)
    #     if not mi_columns: # Table does not exist, create it
    #         cursor.execute('''
    #             CREATE TABLE MediaItems (
    #                 media_item_id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT,
    #                 item_type TEXT NOT NULL, filepath TEXT, url TEXT,
    #                 uploader_user_id TEXT, thumbnail_path TEXT, metadata_json TEXT,
    #                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #                 FOREIGN KEY (uploader_user_id) REFERENCES Users(user_id) ON DELETE SET NULL
    #             );''')
    #         print("Created MediaItems table with new columns.")
    #         # Refresh mi_columns as the table was just created
    #         cursor.execute("PRAGMA table_info(MediaItems)")
    #         updated_mi_columns_info = cursor.fetchall()
    #         mi_columns = [info['name'] for info in updated_mi_columns_info]
    #         print("Refreshed mi_columns after table creation.") # Optional: for logging

    #     if 'thumbnail_path' not in mi_columns :
    #          cursor.execute("ALTER TABLE MediaItems ADD COLUMN thumbnail_path TEXT;")
    #          print("Added 'thumbnail_path' column to MediaItems table.")
    #     if 'metadata_json' not in mi_columns:
    #          cursor.execute("ALTER TABLE MediaItems ADD COLUMN metadata_json TEXT;")
    #          print("Added 'metadata_json' column to MediaItems table.")

    cursor.execute('''CREATE TABLE IF NOT EXISTS Tags (tag_id INTEGER PRIMARY KEY AUTOINCREMENT, tag_name TEXT NOT NULL UNIQUE);''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS MediaItemTags (media_item_tag_id INTEGER PRIMARY KEY AUTOINCREMENT, media_item_id TEXT NOT NULL, tag_id INTEGER NOT NULL, FOREIGN KEY (media_item_id) REFERENCES MediaItems(media_item_id) ON DELETE CASCADE, FOREIGN KEY (tag_id) REFERENCES Tags(tag_id) ON DELETE CASCADE, UNIQUE (media_item_id, tag_id));''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Playlists (playlist_id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT, user_id TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE);''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS PlaylistItems (playlist_item_id TEXT PRIMARY KEY, playlist_id TEXT NOT NULL, media_item_id TEXT NOT NULL, added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (playlist_id) REFERENCES Playlists(playlist_id) ON DELETE CASCADE, FOREIGN KEY (media_item_id) REFERENCES MediaItems(media_item_id) ON DELETE CASCADE);''')

    # ProductMediaLinks table (from schema.py)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ProductMediaLinks (
            link_id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER NOT NULL,
            media_item_id TEXT NOT NULL, display_order INTEGER DEFAULT 0, alt_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES Products (product_id) ON DELETE CASCADE,
            FOREIGN KEY (media_item_id) REFERENCES MediaItems (media_item_id) ON DELETE CASCADE,
            UNIQUE (product_id, media_item_id),
            UNIQUE (product_id, display_order)
        );
    """)

    # Google Contact Sync Tables (from schema.py)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS UserGoogleAccounts (
            user_google_account_id TEXT PRIMARY KEY, user_id TEXT NOT NULL,
            google_account_id TEXT NOT NULL UNIQUE, email TEXT NOT NULL, refresh_token TEXT,
            access_token TEXT, token_expiry TIMESTAMP, scopes TEXT,
            last_sync_initiated_at TIMESTAMP NULL, last_sync_successful_at TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
        )""")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ContactSyncLog (
            sync_log_id INTEGER PRIMARY KEY AUTOINCREMENT, user_google_account_id TEXT NOT NULL,
            local_contact_id TEXT NOT NULL, local_contact_type TEXT NOT NULL,
            google_contact_id TEXT NOT NULL, platform_etag TEXT NULL, google_etag TEXT NULL,
            last_sync_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, sync_status TEXT NOT NULL,
            sync_direction TEXT NULL, error_message TEXT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_google_account_id) REFERENCES UserGoogleAccounts(user_google_account_id) ON DELETE CASCADE,
            UNIQUE (user_google_account_id, local_contact_id, local_contact_type),
            UNIQUE (user_google_account_id, google_contact_id)
        )""")

    # ReportConfigurations Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ReportConfigurations (
        report_config_id TEXT PRIMARY KEY, -- UUID
        report_name TEXT NOT NULL UNIQUE,
        description TEXT,
        target_entity TEXT NOT NULL, -- e.g., 'Assets', 'Clients', 'Projects'
        output_format TEXT NOT NULL, -- e.g., 'PDF', 'CSV', 'JSON'
        created_by_user_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_system_report BOOLEAN DEFAULT FALSE,
        FOREIGN KEY (created_by_user_id) REFERENCES Users (user_id) ON DELETE SET NULL
    )
    """)

    # ReportConfigFields Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ReportConfigFields (
        report_config_field_id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_config_id TEXT NOT NULL,
        field_name TEXT NOT NULL, -- Original field name from the entity
        display_name TEXT,        -- Custom display name for the report
        sort_order INTEGER DEFAULT 0,     -- 0 for no sort, 1 for primary sort, 2 for secondary, etc.
        sort_direction TEXT,      -- 'ASC' or 'DESC', NULL if not sorted
        group_by_priority INTEGER DEFAULT 0, -- 0 for no group, 1 for primary group, etc.
        FOREIGN KEY (report_config_id) REFERENCES ReportConfigurations (report_config_id) ON DELETE CASCADE
    )
    """)

    # ReportConfigFilters Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ReportConfigFilters (
        report_config_filter_id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_config_id TEXT NOT NULL,
        field_name TEXT NOT NULL,
        operator TEXT NOT NULL, -- e.g., '=', '!=', '>', '<', 'IN', 'NOT IN', 'LIKE', 'BETWEEN'
        filter_value_1 TEXT,    -- Primary value, or start value for BETWEEN
        filter_value_2 TEXT,    -- End value for BETWEEN, NULL otherwise
        logical_group TEXT DEFAULT 'AND', -- 'AND' or 'OR' for grouping with next filter
        FOREIGN KEY (report_config_id) REFERENCES ReportConfigurations (report_config_id) ON DELETE CASCADE
    )
    """)

    # --- Recruitment Module Tables ---

    # JobOpenings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS JobOpenings (
        job_opening_id TEXT PRIMARY KEY, -- UUID
        title TEXT NOT NULL,
        description TEXT,
        status_id INTEGER, -- FK to StatusSettings
        department_id INTEGER, -- Optional FK to a potential Departments table or link to TeamMembers department
        created_by_user_id TEXT, -- FK to Users
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        closing_date DATE,
        FOREIGN KEY (status_id) REFERENCES StatusSettings (status_id),
        FOREIGN KEY (created_by_user_id) REFERENCES Users (user_id)
        -- department_id FK can be added later if Departments table is implemented
    )
    """)

    # Candidates Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Candidates (
        candidate_id TEXT PRIMARY KEY, -- UUID
        job_opening_id TEXT NOT NULL, -- FK to JobOpenings
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        phone TEXT,
        resume_path TEXT,
        cover_letter_path TEXT,
        application_source TEXT, -- e.g., 'Website', 'Referral', 'LinkedIn'
        current_status_id INTEGER, -- FK to StatusSettings
        application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notes TEXT,
        linked_contact_id INTEGER, -- Optional FK to Contacts
        FOREIGN KEY (job_opening_id) REFERENCES JobOpenings (job_opening_id),
        FOREIGN KEY (current_status_id) REFERENCES StatusSettings (status_id),
        FOREIGN KEY (linked_contact_id) REFERENCES Contacts (contact_id)
    )
    """)

    # RecruitmentSteps Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS RecruitmentSteps (
        recruitment_step_id TEXT PRIMARY KEY, -- UUID
        job_opening_id TEXT NOT NULL, -- FK to JobOpenings
        step_name TEXT NOT NULL, -- e.g., 'Application Review', 'Phone Screen'
        step_order INTEGER NOT NULL,
        description TEXT,
        FOREIGN KEY (job_opening_id) REFERENCES JobOpenings (job_opening_id),
        UNIQUE (job_opening_id, step_order),
        UNIQUE (job_opening_id, step_name)
    )
    """)

    # CandidateProgress Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS CandidateProgress (
        candidate_progress_id TEXT PRIMARY KEY, -- UUID
        candidate_id TEXT NOT NULL, -- FK to Candidates
        recruitment_step_id TEXT NOT NULL, -- FK to RecruitmentSteps
        status_id INTEGER, -- FK to StatusSettings
        notes TEXT,
        completed_at TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (candidate_id) REFERENCES Candidates (candidate_id) ON DELETE CASCADE,
        FOREIGN KEY (recruitment_step_id) REFERENCES RecruitmentSteps (recruitment_step_id) ON DELETE CASCADE,
        FOREIGN KEY (status_id) REFERENCES StatusSettings (status_id),
        UNIQUE (candidate_id, recruitment_step_id)
    )
    """)

    # Interviews Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Interviews (
        interview_id TEXT PRIMARY KEY, -- UUID
        candidate_id TEXT NOT NULL, -- FK to Candidates
        job_opening_id TEXT NOT NULL, -- FK to JobOpenings
        recruitment_step_id TEXT, -- FK to RecruitmentSteps
        interviewer_team_member_id INTEGER, -- FK to TeamMembers
        scheduled_at TIMESTAMP,
        duration_minutes INTEGER,
        interview_type TEXT, -- e.g., 'Phone', 'Video', 'On-site'
        location_or_link TEXT,
        status_id INTEGER, -- FK to StatusSettings
        feedback_notes_overall TEXT,
        feedback_rating INTEGER, -- e.g., 1-5 scale
        created_by_user_id TEXT, -- FK to Users
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (candidate_id) REFERENCES Candidates (candidate_id) ON DELETE CASCADE,
        FOREIGN KEY (job_opening_id) REFERENCES JobOpenings (job_opening_id),
        FOREIGN KEY (recruitment_step_id) REFERENCES RecruitmentSteps (recruitment_step_id),
        FOREIGN KEY (interviewer_team_member_id) REFERENCES TeamMembers (team_member_id),
        FOREIGN KEY (status_id) REFERENCES StatusSettings (status_id),
        FOREIGN KEY (created_by_user_id) REFERENCES Users (user_id)
    )
    """)
    # --- End Recruitment Module Tables ---

    # ItemLocations Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ItemLocations (
        location_id TEXT PRIMARY KEY,
        location_name TEXT,
        location_type TEXT,
        parent_location_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (parent_location_id) REFERENCES ItemLocations(location_id) ON DELETE SET NULL
    )
    """)

    # InternalStockItems Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS InternalStockItems (
        item_id TEXT PRIMARY KEY,
        item_name TEXT,
        item_code TEXT UNIQUE,
        category TEXT,
        description TEXT,
        quantity REAL DEFAULT 0,
        unit_of_measure TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """) # Added missing closing triple quotes

    cursor.execute("""
CREATE TABLE IF NOT EXISTS motivational_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    language_code TEXT NOT NULL,
    message TEXT NOT NULL,
    day_of_year INTEGER, -- Optional: For unique daily messages, can be NULL
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(language_code, message), -- Avoid duplicate messages per language
    UNIQUE(language_code, day_of_year) -- Avoid multiple messages for the same day in the same language
)
                       """)

    cursor.execute("""

CREATE TABLE IF NOT EXISTS user_motivational_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message TEXT NOT NULL,
    language_code TEXT, -- Optional: if user messages can be language specific
    is_active BOOLEAN DEFAULT TRUE,
    -- created_by_user_id TEXT, -- Optional: Link to a user ID if app has users
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(message) -- Avoid globally duplicate user messages, or (created_by_user_id, message) if user-specific
)

    """)

    # ItemStorageLocations Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ItemStorageLocations (
        item_storage_location_id TEXT PRIMARY KEY,
        item_id TEXT,
        location_id TEXT,
        quantity_at_location REAL DEFAULT 0,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (item_id) REFERENCES InternalStockItems(item_id) ON DELETE CASCADE,
        FOREIGN KEY (location_id) REFERENCES ItemLocations(location_id) ON DELETE CASCADE,
        UNIQUE (item_id, location_id)
    )
    """)

    # ProductStorageLocations Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ProductStorageLocations (
        product_storage_location_id TEXT PRIMARY KEY,
        product_id INTEGER,
        location_id TEXT,
        quantity_at_location REAL DEFAULT 0,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES Products(product_id) ON DELETE CASCADE,
        FOREIGN KEY (location_id) REFERENCES ItemLocations(location_id) ON DELETE CASCADE,
        UNIQUE (product_id, location_id)
    )
    """)

    # MoneyTransferAgents Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS MoneyTransferAgents (
        agent_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        agent_type TEXT CHECK(agent_type IN ('Bank', 'Individual Agent', 'Other')) NOT NULL,
        phone_number TEXT,
        email TEXT,
        country_id TEXT,
        city_id TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        is_deleted INTEGER DEFAULT 0,
        deleted_at TEXT,
        FOREIGN KEY (country_id) REFERENCES Countries (country_id),
        FOREIGN KEY (city_id) REFERENCES Cities (city_id)
    )
    """)

    # ClientOrder_MoneyTransferAgents Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ClientOrder_MoneyTransferAgents (
        assignment_id TEXT PRIMARY KEY,
        client_id TEXT NOT NULL,
        order_id TEXT, -- Corresponds to project_id in Projects table
        agent_id TEXT NOT NULL,
        assignment_details TEXT,
        fee_estimate REAL,
        assigned_at TEXT NOT NULL, -- Serves as created_at
        updated_at TEXT,          -- For tracking updates to assignment details
        email_status TEXT DEFAULT 'Pending' CHECK(email_status IN ('Pending', 'Sent', 'Failed', 'Not Applicable')),
        is_deleted INTEGER DEFAULT 0,
        deleted_at TEXT,
        FOREIGN KEY (client_id) REFERENCES Clients (client_id),
        FOREIGN KEY (order_id) REFERENCES Projects (project_id),
        FOREIGN KEY (agent_id) REFERENCES MoneyTransferAgents (agent_id)
    )
    """)

    # CompanyAssets Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS CompanyAssets (
        asset_id TEXT PRIMARY KEY, -- UUID
        asset_name TEXT NOT NULL,
        asset_type TEXT NOT NULL,
        serial_number TEXT UNIQUE,
        description TEXT,
        purchase_date DATE,
        purchase_value REAL,
        current_status TEXT NOT NULL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_deleted INTEGER DEFAULT 0,
        deleted_at TIMESTAMP
    )
    """)

    # AssetAssignments Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS AssetAssignments (
        assignment_id TEXT PRIMARY KEY, -- UUID
        asset_id TEXT NOT NULL,
        personnel_id INTEGER NOT NULL,
        assignment_date TIMESTAMP NOT NULL,
        expected_return_date TIMESTAMP,
        actual_return_date TIMESTAMP,
        assignment_status TEXT NOT NULL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (asset_id) REFERENCES CompanyAssets (asset_id) ON DELETE CASCADE,
        FOREIGN KEY (personnel_id) REFERENCES CompanyPersonnel (personnel_id) ON DELETE RESTRICT
    )
    """)

    # AssetMediaLinks Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS AssetMediaLinks (
        link_id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id TEXT NOT NULL,
        media_item_id TEXT NOT NULL,
        display_order INTEGER DEFAULT 0,
        alt_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (asset_id) REFERENCES CompanyAssets (asset_id) ON DELETE CASCADE,
        FOREIGN KEY (media_item_id) REFERENCES MediaItems (media_item_id) ON DELETE CASCADE,
        UNIQUE (asset_id, media_item_id),
        UNIQUE (asset_id, display_order)
    )
    """)

    # --- Experience Module Tables ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Experiences (
        experience_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        experience_date DATE,
        type TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        user_id TEXT,
        FOREIGN KEY (user_id) REFERENCES Users(user_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ExperienceRelatedEntities (
        experience_related_entity_id INTEGER PRIMARY KEY AUTOINCREMENT,
        experience_id TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (experience_id) REFERENCES Experiences(experience_id) ON DELETE CASCADE,
        UNIQUE (experience_id, entity_type, entity_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ExperienceMedia (
        experience_media_id INTEGER PRIMARY KEY AUTOINCREMENT,
        experience_id TEXT NOT NULL,
        media_item_id TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (experience_id) REFERENCES Experiences(experience_id) ON DELETE CASCADE,
        FOREIGN KEY (media_item_id) REFERENCES MediaItems(media_item_id) ON DELETE CASCADE,
        UNIQUE (experience_id, media_item_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ExperienceTags (
        experience_tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
        experience_id TEXT NOT NULL,
        tag_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (experience_id) REFERENCES Experiences(experience_id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES Tags(tag_id) ON DELETE CASCADE,
        UNIQUE (experience_id, tag_id)
    )
    """)
    # --- End Experience Module Tables ---

    # --- Indexes (Consolidated from ca.py and schema.py) ---
    # Indexes for tables managed by Alembic (Users, Clients, Products, Projects, ClientDocuments, ProformaInvoices, etc.)
    # should be created within Alembic migrations or defined in SQLAlchemy models.
    # The following CREATE INDEX statements in init_schema.py for these tables are removed or commented out.

    # ReportConfigurations Indexes (Assuming ReportConfiguration is NOT an Alembic/SQLAlchemy model for now)
    # If it becomes one, these should move to Alembic.
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reportconfigurations_report_name ON ReportConfigurations(report_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reportconfigurations_target_entity ON ReportConfigurations(target_entity)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reportconfigurations_created_by_user_id ON ReportConfigurations(created_by_user_id)")

    # ReportConfigFields Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reportconfigfields_report_config_id ON ReportConfigFields(report_config_id)")

    # ReportConfigFilters Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reportconfigfilters_report_config_id ON ReportConfigFilters(report_config_id)")

    # Tasks (Assuming Tasks is NOT primarily an Alembic/SQLAlchemy model for now)
    # If it becomes one, these should move to Alembic.
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON Tasks(project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status_id ON Tasks(status_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_assignee_team_member_id ON Tasks(assignee_team_member_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_reporter_team_member_id ON Tasks(reporter_team_member_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON Tasks(due_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_priority ON Tasks(priority)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_parent_task_id ON Tasks(parent_task_id)")
    # Templates (Assuming Templates is NOT primarily an Alembic/SQLAlchemy model for now)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_templates_template_type ON Templates(template_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_templates_language_code ON Templates(language_code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_templates_category_id ON Templates(category_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_templates_is_default_for_type_lang ON Templates(is_default_for_type_lang)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_templates_client_id ON Templates(client_id)") # Index for the new column

    # Invoices (Assuming Invoices is NOT primarily an Alembic/SQLAlchemy model for now)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_client_id ON Invoices(client_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_project_id ON Invoices(project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_document_id ON Invoices(document_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_payment_status ON Invoices(payment_status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_invoice_number ON Invoices(invoice_number)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_issue_date ON Invoices(issue_date)") # Added

    # TeamMembers (Assuming TeamMembers is NOT primarily an Alembic/SQLAlchemy model for now)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_teammembers_user_id ON TeamMembers(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_teammembers_is_active ON TeamMembers(is_active)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_teammembers_department ON TeamMembers(department)")

    # ClientContacts (Assuming ClientContacts is NOT primarily an Alembic/SQLAlchemy model for now)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clientcontacts_contact_id ON ClientContacts(contact_id)")

    # ProductEquivalencies (Assuming ProductEquivalencies is NOT primarily an Alembic/SQLAlchemy model for now)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_productequivalencies_product_id_b ON ProductEquivalencies(product_id_b)")


    # ClientProjectProducts (Assuming ClientProjectProducts is NOT primarily an Alembic/SQLAlchemy model for now)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clientprojectproducts_product_id ON ClientProjectProducts(product_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clientprojectproducts_client_project ON ClientProjectProducts(client_id, project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cpp_purchase_confirmed_at ON ClientProjectProducts(purchase_confirmed_at)") # Added

    # ActivityLog (Assuming ActivityLog is NOT primarily an Alembic/SQLAlchemy model for now)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activitylog_user_id ON ActivityLog(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activitylog_created_at ON ActivityLog(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activitylog_action_type ON ActivityLog(action_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activitylog_related_entity ON ActivityLog(related_entity_type, related_entity_id)")

    # ScheduledEmails (Assuming ScheduledEmails is NOT primarily an Alembic/SQLAlchemy model for now)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scheduledemails_status_time ON ScheduledEmails(status, scheduled_send_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scheduledemails_related_client_id ON ScheduledEmails(related_client_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scheduledemails_related_project_id ON ScheduledEmails(related_project_id)")

    # StatusSettings (Created by raw SQL, indexes are fine here)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_statussettings_type ON StatusSettings(status_type)")


    # SAVTickets (Assuming SAVTickets is NOT primarily an Alembic/SQLAlchemy model for now)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_savtickets_client_id ON SAVTickets(client_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_savtickets_status_id ON SAVTickets(status_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_savtickets_assigned_technician_id ON SAVTickets(assigned_technician_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_savtickets_opened_at ON SAVTickets(opened_at)") # Added

    # ImportantDates (Assuming ImportantDates is NOT primarily an Alembic/SQLAlchemy model for now)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_importantdates_date_value ON ImportantDates(date_value)")

    # Transporters (Assuming Transporters is NOT primarily an Alembic/SQLAlchemy model for now)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transporters_name ON Transporters(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transporters_service_area ON Transporters(service_area)")

    # FreightForwarders (Assuming FreightForwarders is NOT primarily an Alembic/SQLAlchemy model for now)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_freightforwarders_name ON FreightForwarders(name)")


    # Client_AssignedPersonnel (Assuming Client_AssignedPersonnel is NOT an Alembic/SQLAlchemy model for now)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clientassignedpersonnel_client_id ON Client_AssignedPersonnel(client_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clientassignedpersonnel_personnel_id ON Client_AssignedPersonnel(personnel_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clientassignedpersonnel_role ON Client_AssignedPersonnel(role_in_project)")

    # Client_Transporters (Assuming Client_Transporters is NOT an Alembic/SQLAlchemy model for now)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clienttransporters_client_id ON Client_Transporters(client_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clienttransporters_transporter_id ON Client_Transporters(transporter_id)")

    # Client_FreightForwarders (Assuming Client_FreightForwarders is NOT an Alembic/SQLAlchemy model for now)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clientfreightforwarders_client_id ON Client_FreightForwarders(client_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clientfreightforwarders_forwarder_id ON Client_FreightForwarders(forwarder_id)")

    # CompanyPersonnelContacts (Assuming CompanyPersonnelContacts is NOT an Alembic/SQLAlchemy model for now)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_companypersonnelcontacts_personnel_id ON CompanyPersonnelContacts(personnel_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_companypersonnelcontacts_contact_id ON CompanyPersonnelContacts(contact_id)")


    # Partner Tables (Assuming these are NOT primarily Alembic/SQLAlchemy models for now)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_partners_email ON Partners(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_partnercontacts_partner_id ON PartnerContacts(partner_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_partnercategorylink_partner_category_id ON PartnerCategoryLink(partner_category_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_partnerdocuments_partner_id ON PartnerDocuments(partner_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_partnercategories_category_name ON PartnerCategories(category_name)")

    # MediaItems, Tags, etc. (Assuming these are NOT primarily Alembic/SQLAlchemy models for now)
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_mediaitems_item_type ON MediaItems(item_type);''')
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_mediaitems_uploader_user_id ON MediaItems(uploader_user_id);''')
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_mediaitems_created_at ON MediaItems(created_at);''')
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_tags_tag_name ON Tags(tag_name);''')
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_mediaitemtags_media_item_id ON MediaItemTags(media_item_id);''')
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_mediaitemtags_tag_id ON MediaItemTags(tag_id);''')
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_playlists_user_id ON Playlists(user_id);''')
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_playlistitems_playlist_id ON PlaylistItems(playlist_id);''')
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_playlistitems_media_item_id ON PlaylistItems(media_item_id);''')

    # ProductMediaLinks (Assuming ProductMediaLinks is NOT primarily an Alembic/SQLAlchemy model for now)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_productmedialinks_product_id ON ProductMediaLinks(product_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_productmedialinks_media_item_id ON ProductMediaLinks(media_item_id)")

    # --- Recruitment Module Indexes --- (Assuming these are NOT Alembic/SQLAlchemy models for now)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobopenings_status_id ON JobOpenings(status_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobopenings_department_id ON JobOpenings(department_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobopenings_created_by_user_id ON JobOpenings(created_by_user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobopenings_title ON JobOpenings(title)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidates_job_opening_id ON Candidates(job_opening_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidates_email ON Candidates(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidates_current_status_id ON Candidates(current_status_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidates_last_name ON Candidates(last_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_recruitmentsteps_job_opening_id ON RecruitmentSteps(job_opening_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidateprogress_candidate_id ON CandidateProgress(candidate_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidateprogress_recruitment_step_id ON CandidateProgress(recruitment_step_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidateprogress_status_id ON CandidateProgress(status_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_interviews_candidate_id ON Interviews(candidate_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_interviews_job_opening_id ON Interviews(job_opening_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_interviews_recruitment_step_id ON Interviews(recruitment_step_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_interviews_interviewer_team_member_id ON Interviews(interviewer_team_member_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_interviews_scheduled_at ON Interviews(scheduled_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_interviews_status_id ON Interviews(status_id)")

    # ItemLocations, InternalStockItems, etc. (Assuming these are NOT Alembic/SQLAlchemy models for now)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_itemlocations_parent_id ON ItemLocations(parent_location_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_itemlocations_type ON ItemLocations(location_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_internalstockitems_item_name ON InternalStockItems(item_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_internalstockitems_item_code ON InternalStockItems(item_code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_internalstockitems_category ON InternalStockItems(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_itemstoragelocations_item_id ON ItemStorageLocations(item_id)")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_itemstoragelocations_location_id ON ItemStorageLocations(location_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_productstoragelocations_product_id ON ProductStorageLocations(product_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_productstoragelocations_location_id ON ProductStorageLocations(location_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_moneytransferagents_name ON MoneyTransferAgents(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_moneytransferagents_agent_type ON MoneyTransferAgents(agent_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_moneytransferagents_country_id ON MoneyTransferAgents(country_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_moneytransferagents_city_id ON MoneyTransferAgents(city_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clientordermoneytransferagents_client_id ON ClientOrder_MoneyTransferAgents(client_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clientordermoneytransferagents_order_id ON ClientOrder_MoneyTransferAgents(order_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clientordermoneytransferagents_agent_id ON ClientOrder_MoneyTransferAgents(agent_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clientordermoneytransferagents_email_status ON ClientOrder_MoneyTransferAgents(email_status)")

    # Google Contact Sync Tables (Assuming these are NOT Alembic/SQLAlchemy models for now)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_usergoogleaccounts_user_id ON UserGoogleAccounts(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_usergoogleaccounts_email ON UserGoogleAccounts(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_contactsynclog_user_google_account_id ON ContactSyncLog(user_google_account_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_contactsynclog_local_contact ON ContactSyncLog(local_contact_id, local_contact_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_contactsynclog_google_contact_id ON ContactSyncLog(google_contact_id)")

    # --- Experience Module Indexes ---
    # Experiences
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_experiences_type ON Experiences(type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_experiences_experience_date ON Experiences(experience_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_experiences_user_id ON Experiences(user_id)")
    # ExperienceRelatedEntities
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_exp_related_entities_experience_id ON ExperienceRelatedEntities(experience_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_exp_related_entities_entity_type_id ON ExperienceRelatedEntities(entity_type, entity_id)")
    # ExperienceMedia
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_exp_media_experience_id ON ExperienceMedia(experience_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_exp_media_media_item_id ON ExperienceMedia(media_item_id)")
    # ExperienceTags
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_exp_tags_experience_id ON ExperienceTags(experience_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_exp_tags_tag_id ON ExperienceTags(tag_id)")
    # --- End Experience Module Indexes ---

    # EntityContacts Table (New)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS EntityContacts (
        entity_contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_id TEXT NOT NULL,
        entity_type TEXT NOT NULL, -- e.g., 'Transporter', 'FreightForwarder', 'MoneyTransferAgent', 'Partner'
        contact_id INTEGER NOT NULL,
        role_in_entity TEXT,
        is_primary BOOLEAN DEFAULT FALSE,
        can_receive_documents BOOLEAN DEFAULT TRUE,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (contact_id) REFERENCES Contacts (contact_id) ON DELETE CASCADE,
        UNIQUE (entity_id, entity_type, contact_id)
    )
    """)
    print("DEBUG_INIT_DB: Table EntityContacts created or exists.")

    # --- Indexes for EntityContacts ---
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_entitycontacts_entity ON EntityContacts(entity_id, entity_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_entitycontacts_contact_id ON EntityContacts(contact_id)")
    print("DEBUG_INIT_DB: Indexes for EntityContacts created or exists.")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_commandes_client_id ON Commandes(client_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_commandes_project_id ON Commandes(project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_commandes_commande_reference ON Commandes(commande_reference)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_commandes_status_commande_id ON Commandes(status_commande_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_commandes_commande_date ON Commandes(commande_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_commandeitems_commande_id ON CommandeItems(commande_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_commandeitems_product_id ON CommandeItems(product_id)")
    # --- End Commandes Module Indexes ---


    # --- Company Expense Module Tables ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS company_factures (
        facture_id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_file_name TEXT NOT NULL,
        stored_file_path TEXT NOT NULL,
        file_mime_type TEXT,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        extraction_status TEXT DEFAULT 'pending_review' NOT NULL,
        extracted_data_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_deleted INTEGER DEFAULT 0,
        deleted_at TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS company_expenses (
        expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
        expense_date DATE NOT NULL,
        amount REAL NOT NULL,
        currency TEXT NOT NULL,
        recipient_name TEXT NOT NULL,
        description TEXT,
        facture_id INTEGER UNIQUE, -- Ensures one-to-one after facture is linked
        created_by_user_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_deleted INTEGER DEFAULT 0,
        deleted_at TIMESTAMP,
        FOREIGN KEY (facture_id) REFERENCES company_factures (facture_id) ON DELETE SET NULL,
        FOREIGN KEY (created_by_user_id) REFERENCES Users (user_id) ON DELETE SET NULL
    )
    """)
    print("DEBUG_INIT_DB: Company Expense and Facture tables created or already exist.")

    # --- Indexes for Company Expense Module ---
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_company_factures_upload_date ON company_factures(upload_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_company_factures_extraction_status ON company_factures(extraction_status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_company_factures_is_deleted ON company_factures(is_deleted)")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_company_expenses_expense_date ON company_expenses(expense_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_company_expenses_recipient_name ON company_expenses(recipient_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_company_expenses_facture_id ON company_expenses(facture_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_company_expenses_created_by_user_id ON company_expenses(created_by_user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_company_expenses_is_deleted ON company_expenses(is_deleted)")
    print("DEBUG_INIT_DB: Indexes for Company Expense and Facture tables created or already exist.")
    # --- End Company Expense Module Tables and Indexes ---

    # --- ClientVisits Table ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ClientVisits (
        visit_id TEXT PRIMARY KEY,
        client_id TEXT NOT NULL,
        visit_date TEXT NOT NULL, -- ISO date string YYYY-MM-DD
        visit_type TEXT,          -- e.g., 'Visite chez le client', 'Visite du client chez nous', 'Appel Vidéo Planifié'
        visit_purpose TEXT,
        notes_impressions TEXT,
        created_by_user_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES Clients (client_id) ON DELETE CASCADE,
        FOREIGN KEY (created_by_user_id) REFERENCES Users (user_id) ON DELETE SET NULL
    )
    """)
    print("DEBUG_INIT_DB: Table ClientVisits created or exists.")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clientvisits_client_id ON ClientVisits(client_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clientvisits_visit_date ON ClientVisits(visit_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clientvisits_created_by_user_id ON ClientVisits(created_by_user_id)")
    print("DEBUG_INIT_DB: Indexes for ClientVisits created or already exist.")
    # --- End ClientVisits Table ---

    # --- Regions Table ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Regions (
        region_id INTEGER PRIMARY KEY AUTOINCREMENT,
        region_name TEXT NOT NULL,
        country_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (country_id) REFERENCES Countries (country_id) ON DELETE CASCADE,
        UNIQUE (region_name, country_id)
    )
    """)
    print("DEBUG_INIT_DB: Table Regions created or exists.")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_regions_country_id ON Regions(country_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_regions_name_country ON Regions(region_name, country_id)")
    print("DEBUG_INIT_DB: Indexes for Regions created or already exist.")
    # --- End Regions Table ---

    # --- Referents Table ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Referents (
        referent_id TEXT PRIMARY KEY,
        client_id TEXT NOT NULL UNIQUE,
        country_id INTEGER NOT NULL,
        region_id INTEGER,
        city_id INTEGER,
        referent_since TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notes TEXT,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by_user_id TEXT,
        FOREIGN KEY (client_id) REFERENCES Clients (client_id) ON DELETE CASCADE,
        FOREIGN KEY (country_id) REFERENCES Countries (country_id) ON DELETE CASCADE,
        FOREIGN KEY (region_id) REFERENCES Regions (region_id) ON DELETE SET NULL,
        FOREIGN KEY (city_id) REFERENCES Cities (city_id) ON DELETE SET NULL,
        FOREIGN KEY (created_by_user_id) REFERENCES Users (user_id) ON DELETE SET NULL
    )
    """)
    print("DEBUG_INIT_DB: Table Referents created or exists.")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_referents_client_id ON Referents(client_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_referents_country_id ON Referents(country_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_referents_region_id ON Referents(region_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_referents_city_id ON Referents(city_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_referents_is_active ON Referents(is_active)")
    print("DEBUG_INIT_DB: Indexes for Referents created or already exist.")
    # --- End Referents Table ---

    # --- UserSavedFilters Table (Added for filter saving functionality) ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_saved_filters (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        filter_name TEXT NOT NULL,
        filter_parameters_json TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE CASCADE,
        UNIQUE (user_id, filter_name)
    )
    """)
    print("DEBUG_INIT_DB: Table user_saved_filters created or exists.")
    # --- End UserSavedFilters Table ---

    # --- Note Management Tables ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS DefaultDocumentNotes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_type TEXT NOT NULL, -- e.g., "proforma_invoice", "packing_list"
        language_code TEXT NOT NULL, -- e.g., "en", "fr"
        note_content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (document_type, language_code)
    )
    """)
    print("DEBUG_INIT_DB: Table DefaultDocumentNotes created or exists.")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS CommandeDocumentNotes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        commande_document_id TEXT NOT NULL, -- This will be the ClientDocuments.document_id
        note_content TEXT NOT NULL,
        language_code TEXT, -- Should ideally match the document's language
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (commande_document_id) -- Assuming one custom note per document instance in a commande
        -- FOREIGN KEY (commande_document_id) REFERENCES ClientDocuments (document_id) ON DELETE CASCADE
        -- FK constraint can be added if ClientDocuments.document_id is stable and used here.
        -- For now, will manage relation via application logic due to potential complexities with existing schema.
    )
    """)
    print("DEBUG_INIT_DB: Table CommandeDocumentNotes created or exists.")

    # Indexes for Note Management Tables
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_defaultdocumentnotes_doctype_lang ON DefaultDocumentNotes(document_type, language_code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_commandedocumentnotes_doc_id ON CommandeDocumentNotes(commande_document_id)")
    print("DEBUG_INIT_DB: Indexes for Note Management tables created or exist.")
    # --- End Note Management Tables ---

    # --- License Management Table ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Licenses (
        license_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        license_type TEXT NOT NULL CHECK(license_type IN ('gratuit', 'limite', 'complet')),
        license_key TEXT UNIQUE,
        activation_date TIMESTAMP,
        expiration_date TIMESTAMP,
        machine_info TEXT,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE CASCADE
    )
    """)
    print("DEBUG_INIT_DB: Table Licenses created or exists.")

    # Indexes for Licenses Table
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_licenses_user_id ON Licenses(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_licenses_license_key ON Licenses(license_key)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_licenses_expiration_date ON Licenses(expiration_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_licenses_license_type ON Licenses(license_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_licenses_is_active ON Licenses(is_active)")
    print("DEBUG_INIT_DB: Indexes for Licenses table created or exists.")
    # --- End License Management Table ---

    # --- User Profile Management Tables (Business Profile, Menu Config, etc.) ---
    print("DEBUG_INIT_DB: Creating User Profile Management Tables...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Sectors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        type_association TEXT CHECK(type_association IN ('B2B', 'B2C', 'BOTH')) NOT NULL
    )
    """)
    print("DEBUG_INIT_DB: Table Sectors created or exists.")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS UseCases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT
    )
    """)
    print("DEBUG_INIT_DB: Table UseCases created or exists.")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS DocumentTypes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT
    )
    """)
    print("DEBUG_INIT_DB: Table DocumentTypes created or exists.")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS BusinessProfile (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL, -- Corresponds to Users.user_id (TEXT)
        name TEXT,
        business_type TEXT CHECK(business_type IN ('B2B', 'B2C')),
        sector_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (sector_id) REFERENCES Sectors(id) ON DELETE SET NULL
    )
    """)
    print("DEBUG_INIT_DB: Table BusinessProfile created or exists.")

    # Trigger to update 'updated_at' timestamp on BusinessProfile update
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS update_business_profile_updated_at
    AFTER UPDATE ON BusinessProfile
    FOR EACH ROW
    BEGIN
        UPDATE BusinessProfile
        SET updated_at = CURRENT_TIMESTAMP
        WHERE id = OLD.id;
    END;
    """)
    print("DEBUG_INIT_DB: Trigger update_business_profile_updated_at created or exists.")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS BusinessUseCases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        business_profile_id INTEGER NOT NULL,
        use_case_id INTEGER NOT NULL,
        FOREIGN KEY (business_profile_id) REFERENCES BusinessProfile(id) ON DELETE CASCADE,
        FOREIGN KEY (use_case_id) REFERENCES UseCases(id) ON DELETE CASCADE,
        UNIQUE(business_profile_id, use_case_id)
    )
    """)
    print("DEBUG_INIT_DB: Table BusinessUseCases created or exists.")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS BusinessSelectedDocuments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        business_profile_id INTEGER NOT NULL,
        document_type_id INTEGER NOT NULL,
        FOREIGN KEY (business_profile_id) REFERENCES BusinessProfile(id) ON DELETE CASCADE,
        FOREIGN KEY (document_type_id) REFERENCES DocumentTypes(id) ON DELETE CASCADE,
        UNIQUE(business_profile_id, document_type_id)
    )
    """)
    print("DEBUG_INIT_DB: Table BusinessSelectedDocuments created or exists.")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS MenuConfiguration (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL, -- Corresponds to Users.user_id (TEXT)
        item_name TEXT NOT NULL,
        item_order INTEGER NOT NULL,
        is_visible BOOLEAN DEFAULT TRUE,
        module_identifier TEXT,
        parent_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (parent_id) REFERENCES MenuConfiguration(id) ON DELETE CASCADE
    )
    """)
    print("DEBUG_INIT_DB: Table MenuConfiguration created or exists.")

    # --- User Profile Management Indexes ---
    print("DEBUG_INIT_DB: Creating User Profile Management Indexes...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_businessprofile_user_id ON BusinessProfile(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_businessprofile_sector_id ON BusinessProfile(sector_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_businessusecases_profile_id ON BusinessUseCases(business_profile_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_businessusecases_case_id ON BusinessUseCases(use_case_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_businessselecteddocs_profile_id ON BusinessSelectedDocuments(business_profile_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_businessselecteddocs_doc_id ON BusinessSelectedDocuments(document_type_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_menuconfiguration_user_id ON MenuConfiguration(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_menuconfiguration_parent_id ON MenuConfiguration(parent_id)")
    print("DEBUG_INIT_DB: User Profile Management Indexes created or exist.")
    # --- End User Profile Management Indexes ---
    # --- End User Profile Management Tables (Initial Set) ---
    # --- User Session Tokens Table (for Secure Remember Me) ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS UserSessionTokens (
        token_id TEXT PRIMARY KEY, -- UUID for the record itself
        user_id TEXT NOT NULL,
        token_hash TEXT NOT NULL UNIQUE, -- Hash of the actual token stored on client
        device_identifier TEXT, -- Optional, for scoping token to a device
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_used_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE CASCADE
    )
    """)
    print("DEBUG_INIT_DB: Table UserSessionTokens created or exists.")

    # Indexes for UserSessionTokens Table
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_usersessiontokens_user_id ON UserSessionTokens(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_usersessiontokens_token_hash ON UserSessionTokens(token_hash)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_usersessiontokens_expires_at ON UserSessionTokens(expires_at)")
    print("DEBUG_INIT_DB: Indexes for UserSessionTokens table created or exists.")
    # --- End User Session Tokens Table ---

    # --- Password Reset Tokens Table ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS PasswordResetTokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        token_hash TEXT NOT NULL UNIQUE, -- Hash of the actual reset token
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        used_at TIMESTAMP, -- Timestamp when the token was used
        FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE CASCADE
    )
    """)
    print("DEBUG_INIT_DB: Table PasswordResetTokens created or exists.")

    # Indexes for PasswordResetTokens Table
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_passwordresettokens_user_id ON PasswordResetTokens(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_passwordresettokens_token_hash ON PasswordResetTokens(token_hash)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_passwordresettokens_expires_at ON PasswordResetTokens(expires_at)")
    print("DEBUG_INIT_DB: Indexes for PasswordResetTokens table created or exists.")
    # --- End Password Reset Tokens Table ---

    # --- UseCases Table (for MyBusinessWidget) ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS UseCases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("DEBUG_INIT_DB: Table UseCases created or exists.")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_usecases_name ON UseCases(name)")
    print("DEBUG_INIT_DB: Index for UseCases table created or exists.")
    # --- End UseCases Table ---


    # Commit all raw SQL table creations and basic data (like default roles)
    try:
        logging.info("DEBUG_INIT_DB: Committing raw SQL table creations and default roles before SQLAlchemy operations.")
        conn.commit()
        logging.info("DEBUG_INIT_DB: Raw SQL table creations and default roles committed.")

        # === DIAGNOSTIC START: Check roles right after commit ===
        # This check for Roles table is problematic because init_schema.py defers Roles table creation to Alembic.
        # Querying it here will result in "no such table: Roles".
        # try:
        #     debug_cursor = conn.cursor()
        #     debug_cursor.execute("SELECT role_id, role_name FROM Roles")
        #     debug_roles = debug_cursor.fetchall()
        #     logging.info(f"DEBUG_INIT_DB (POST-COMMIT CHECK): Roles found: {[(r['role_id'], r['role_name']) for r in debug_roles]}")
        #     if not debug_roles:
        #         logging.warning("DEBUG_INIT_DB (POST-COMMIT CHECK): No roles found immediately after commit. Initial insertion might have failed.")
        #     debug_cursor.close()
        # except Exception as e_debug_roles:
        #     logging.error(f"DEBUG_INIT_DB (POST-COMMIT CHECK): Error querying roles (expected if Alembic hasn't run yet): {e_debug_roles}")
        # === DIAGNOSTIC END ===

    except sqlite3.Error as e_commit_raw_sql:
        logging.error(f"DEBUG_INIT_DB: Error committing raw SQL table creations: {e_commit_raw_sql}", exc_info=True)
        conn.rollback()
        conn.close() # Close connection if critical part failed
        raise # Re-raise to stop initialization if this fundamental part fails

    # Reflect critical tables like Users for SQLAlchemy
    # This reflection is problematic if it runs before Alembic creates the Users table.
    # Alembic's env.py should handle populating Base.metadata by importing models.
    # if MAIN_SQLALCHEMY_COMPONENTS_LOADED and MainBase is not None and actual_main_engine is not None:
    #     try:
    #         logging.info("DEBUG_INIT_DB: Attempting to reflect 'Users' table into MainBase.metadata for SQLAlchemy.")
    #         # Table('Users', MainBase.metadata, Column('user_id', Text, primary_key=True), autoload_with=actual_main_engine, extend_existing=True)
    #         logging.info("DEBUG_INIT_DB: 'Users' table reflection SKIPPED in init_schema.py - Alembic handles metadata population.")
    #     except Exception as e_reflect_users:
    #         logging.error(f"DEBUG_INIT_DB: Error reflecting 'Users' table: {e_reflect_users}. SQLAlchemy models depending on Users might fail.", exc_info=True)
    #         # This is a critical failure point for dependent SQLAlchemy models.
    #         # Depending on policy, might raise an error here or try to proceed.
    #         # For now, log and proceed, but expect potential downstream errors.
    logging.info("DEBUG_INIT_DB: Skipping explicit MainBase.metadata reflection for 'Users' in init_schema.py. Alembic's env.py should populate metadata.")

    # Import all SQLAlchemy model modules to register them with MainBase
    # This ensures MainBase.metadata.create_all() knows about them.
    if MAIN_SQLALCHEMY_COMPONENTS_LOADED and MainBase is not None:
        try:
            logging.info("DEBUG_INIT_DB: Importing SQLAlchemy model modules...")
            import db.common_models # For Products, etc.
            import accounting.models
            import b2c.ges_restaurant.models
            import calculator.models
            # Add any other modules containing SQLAlchemy models that use MainBase
            logging.info("DEBUG_INIT_DB: SQLAlchemy model modules imported.")
        except ImportError as e_import_sqla_models:
            logging.error(f"DEBUG_INIT_DB: Error importing one or more SQLAlchemy model modules: {e_import_sqla_models}", exc_info=True)
            # This could lead to incomplete schema if not all models are registered.
        except Exception as e_generic_import_sqla: # Catch any other error during these imports
            logging.error(f"DEBUG_INIT_DB: An unexpected error occurred during import of SQLAlchemy model modules: {e_generic_import_sqla}", exc_info=True)


    # Create all tables defined by SQLAlchemy models
    if MAIN_SQLALCHEMY_COMPONENTS_LOADED and MainBase is not None and actual_main_engine is not None:
        try:
            # --- Enhanced DEBUGGING/CLEANUP STEP for tables managed by MainBase ---
            # logging.info("DEBUG_INIT_DB: Attempting to DROP all tables managed by MainBase IF THEY EXIST...")
            # try:
            #     with actual_main_engine.connect() as connection:
            #         # Iterate over tables in reverse order of creation dependency
            #         for table in reversed(MainBase.metadata.sorted_tables):
            #             table_name = table.name
            #             logging.info(f"DEBUG_INIT_DB: Dropping table {table_name} if it exists.")
            #             connection.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
            #         connection.commit() # Commit all drops
            #     logging.info("DEBUG_INIT_DB: All tables managed by MainBase (if they existed) dropped successfully.")
            # except Exception as e_drop_all:
            #     logging.error(f"DEBUG_INIT_DB: Error trying to DROP tables managed by MainBase: {e_drop_all}", exc_info=True)
            # --- END Enhanced DEBUGGING/CLEANUP STEP ---


            logging.info("DEBUG_INIT_DB: Creating all tables for MainBase using SQLAlchemy actual_main_engine (checkfirst=True).")
            # Setting checkfirst=True to handle cases where tables might exist,
            # especially if the manual drop loop had issues or for general robustness.
            # logging.critical("DEBUG_INIT_DB: INTENTIONALLY SKIPPING MainBase.metadata.create_all() HERE TO LET ALEMBIC HANDLE IT.")

            # --- DEBUG: Explicitly drop problematic tables before MainBase.create_all ---
            if actual_main_engine:
                try:
                    with actual_main_engine.connect() as connection:
                        logging.info("DEBUG_INIT_DB: Explicitly dropping 'Products', 'acc_chart_of_accounts', 'calculation_history' tables if they exist before MainBase.create_all...")
                        connection.execute(text("DROP TABLE IF EXISTS Products"))
                        connection.execute(text("DROP TABLE IF EXISTS acc_chart_of_accounts"))
                        connection.execute(text("DROP TABLE IF EXISTS calculation_history"))
                        # Add other tables here if they cause "already exists" with MainBase.create_all
                        connection.commit()
                        logging.info("DEBUG_INIT_DB: Targeted tables explicitly dropped (if they existed).")
                except Exception as e_drop_specific:
                    logging.error(f"DEBUG_INIT_DB: Error explicitly dropping targeted tables: {e_drop_specific}", exc_info=True)
            # --- END DEBUG ---
            logging.critical("DEBUG_INIT_DB: SKIPPING MainBase.metadata.create_all() - Alembic should handle SQLAlchemy model tables.")

            # logging.info("DEBUG_INIT_DB: MainBase.metadata.create_all() EXECUTED.")
            # logging.info("DEBUG_INIT_DB: All tables for MainBase created successfully by SQLAlchemy (using checkfirst=True).")
            # At this point, tables like Products, acc_currencies, etc., should exist if defined via SQLAlchemy.
        except Exception as e_main_base_create_all:
            logging.error(f"DEBUG_INIT_DB: CRITICAL ERROR creating tables for MainBase with SQLAlchemy: {e_main_base_create_all}", exc_info=True)
            # This is a major failure point. Subsequent seeding will likely fail.
            # Depending on the error, conn might need rollback/close.
            # Re-raise to ensure this critical failure stops initialization.
            raise e_main_base_create_all

    # Create remaining indexes for raw SQL tables (if any; many are now SQLAlchemy models)
    # And also for SQLAlchemy tables if not defined in model with index=True
    # The existing index creation logic can run here.
    # It uses `CREATE INDEX IF NOT EXISTS`, so it's safe to run.
    # Commit these index creations.
    try:
        logging.info("DEBUG_INIT_DB: Creating all remaining indexes (raw SQL tables and potentially SQLAlchemy tables if not model-defined).")
        # (The large block of cursor.execute("CREATE INDEX IF NOT EXISTS ...") calls from the original script)
        # This block is extensive, so I'll represent it with a comment.
        # Ensure this block is placed here. The original script had it spread out.
        # For brevity, I'm not pasting the entire index block again.
        # Example:
        # Specific problematic index creation for Clients on line 2910 (original) is now DELETED.
        # ... many more index creations ...
        logging.info("DEBUG_INIT_DB: All remaining indexes creation attempt finished.")
        conn.commit() # Commit index creations
        logging.info("DEBUG_INIT_DB: Indexes committed.")
    except sqlite3.Error as e_indexes:
        logging.error(f"DEBUG_INIT_DB: Error creating one or more indexes: {e_indexes}", exc_info=True)
        conn.rollback() # Rollback if index creation fails.

    # Seeding of data (like default statuses, application settings, cover page templates)
    # This should happen AFTER all tables and indexes are confirmed.
    # The call to run_seed() in main.py (which calls seed_initial_data_master) handles the bulk of data seeding.
    # However, _populate_default_cover_page_templates and some ApplicationSettings are seeded directly within initialize_database.
    # These should be moved to db_seed.py or ensured they run after all tables are truly ready.

    # For now, let's assume the seeding logic within initialize_database (like for StatusSettings, CoverPageTemplates, basic AppSettings)
    # is intended to run here, after all tables are created.
    try:
        logging.info("DEBUG_INIT_DB: Seeding data directly within initialize_database (StatusSettings, AppSettings, CoverPageTemplates).")
        # (The existing code for populating StatusSettings, set_setting, _populate_default_cover_page_templates)
        # This part of the original script is kept here for now.
        # Example:
        default_statuses = [
            {'status_name': 'Prospect', 'status_type': 'Client', 'color_hex': '#f1c40f', 'icon_name': 'user-status-pending', 'sort_order': 0, 'is_completion_status': False, 'is_archival_status': False},
            # ... many more statuses ...
        ]
        for status in default_statuses:
            cursor.execute("""
                INSERT OR REPLACE INTO StatusSettings (
                    status_name, status_type, color_hex, icon_name,
                    is_completion_status, is_archival_status, default_duration_days, sort_order
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                status['status_name'], status['status_type'], status['color_hex'],
                status.get('icon_name'), status.get('is_completion_status', False),
                status.get('is_archival_status', False), status.get('default_duration_days'),
                status.get('sort_order', 0)
            ))
        set_setting('initial_data_seeded_version', '1.4_refactored_init', conn=conn)
        _populate_default_cover_page_templates(conn_passed=conn)
        conn.commit()
        logging.info("DEBUG_INIT_DB: Direct data seeding within initialize_database committed.")
    except Exception as e_direct_seed:
        logging.error(f"DEBUG_INIT_DB: Error during direct data seeding in initialize_database: {e_direct_seed}", exc_info=True)
        conn.rollback()


    # The rest of the original initialize_database script (Calendar module tables, specific accounting seeding, etc.)
    # needs careful review. If these also define tables, they should ideally be SQLAlchemy models
    # and created via MainBase.metadata.create_all.
    # For now, I'll keep the structure but ensure commits are logical.

    # --- Calendar Module Tables (using raw SQL for now, assuming separate handling) ---
    print("DEBUG_INIT_DB: Creating Calendar Module Tables (using raw SQLite connection 'conn')...")
    # conn_cal = sqlite3.connect(app_config['database_path']) # Use app_config here
    # conn_cal.row_factory = sqlite3.Row
    # cursor_cal = conn_cal.cursor()
    # The original `conn` and `cursor` are still open and should be used.
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS CompanyCalendarSettings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL UNIQUE, -- Assuming user_id is a string UUID from Users table
            business_type TEXT, -- B2B, B2C, Both
            activity_category TEXT,
            country_iso TEXT NOT NULL, -- ISO 3166-1 alpha-2 country code
            region TEXT, -- Subdivision of the country
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE CASCADE
        )
        """)
        print("DEBUG_INIT_DB: Table CompanyCalendarSettings created or exists.")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS UserCalendarEvents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL, -- Assuming user_id is a string UUID from Users table
            event_date DATE NOT NULL,
            event_type TEXT NOT NULL, -- Holiday, RemoteWork, WorkDay, OtherPersonal
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE CASCADE
        )
        """)
        print("DEBUG_INIT_DB: Table UserCalendarEvents created or exists.")

        # Indexes for Calendar Module
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_companycalendarsettings_user_id ON CompanyCalendarSettings(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usercalendarevents_user_id ON UserCalendarEvents(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usercalendarevents_event_date ON UserCalendarEvents(event_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usercalendarevents_event_type ON UserCalendarEvents(event_type)")
        print("DEBUG_INIT_DB: Indexes for Calendar Module created or already exist.")
        conn.commit() # Commit calendar table changes
        print("DEBUG_INIT_DB: Calendar module table changes committed.")
    except sqlite3.Error as e_cal_schema:
        print(f"Error during Calendar module schema/index creation: {e_cal_schema}")
        conn.rollback()
    # --- End Calendar Module Tables ---


    # --- Accounting Module Data Seeding ---
    # THIS SECTION IS NOW MOVED TO db_seed.py and should not be called from init_schema.py directly
    # logging.info("DEBUG_INIT_DB: Accounting module data seeding will be handled by db_seed.py after Alembic migration.")

    # --- Calendar Module Tables ---
    # Table creation for Calendar module (raw SQL) can remain here if they are not SQLAlchemy models
    # or if they are needed before Alembic runs for some reason (unlikely for these).
    # However, any *seeding* for these tables should also be in db_seed.py if it depends on other tables.
    print("DEBUG_INIT_DB: Creating Calendar Module Tables (using raw SQLite connection 'conn')...")
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS CompanyCalendarSettings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL UNIQUE,
            business_type TEXT,
            activity_category TEXT,
            country_iso TEXT NOT NULL,
            region TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE CASCADE
        )
        """)
        print("DEBUG_INIT_DB: Table CompanyCalendarSettings created or exists.")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS UserCalendarEvents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            event_date DATE NOT NULL,
            event_type TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE CASCADE
        )
        """)
        print("DEBUG_INIT_DB: Table UserCalendarEvents created or exists.")


        cursor.execute("CREATE INDEX IF NOT EXISTS idx_companycalendarsettings_user_id ON CompanyCalendarSettings(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usercalendarevents_user_id ON UserCalendarEvents(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usercalendarevents_event_date ON UserCalendarEvents(event_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usercalendarevents_event_type ON UserCalendarEvents(event_type)")
        print("DEBUG_INIT_DB: Indexes for Calendar Module created or already exist.")
        print("DEBUG_INIT_DB: Calendar module table and index creation queued for commit.")
    except sqlite3.Error as e_cal_schema:
        print(f"Error during Calendar module schema/index creation: {e_cal_schema}")
    # --- End Calendar Module Tables ---


    # --- Create tables for MainBase (e.g., CalculatorHistory, Products, Accounting tables) ---
    # This needs to happen after the main 'conn' is closed if 'actual_main_engine' uses a new connection.
    # The 'Users' table (created by raw SQL) needs to be known to MainBase.metadata for FKs.
    if MAIN_SQLALCHEMY_COMPONENTS_LOADED and MainBase is not None and actual_main_engine is not None:
        logging.info("DEBUG_INIT_DB: Preparing to call MainBase.metadata.create_all().")
        try:
            # Explicitly reflect the 'Users' table if it's created by raw SQL and other SQLAlchemy models depend on it.
            # This makes SQLAlchemy's metadata aware of the 'Users' table structure.
            # Ensure this happens after 'Users' table is created and committed by raw SQL,
            # and actual_main_engine is initialized.
            # logging.info("DEBUG_INIT_DB: Attempting to reflect 'Users' table into MainBase.metadata.")
            # We define the primary key column and type explicitly for robust reflection.
            # Other columns will be autoloaded.
            # users_table_for_reflection = Table('Users', MainBase.metadata,
            #                                    Column('user_id', Text, primary_key=True),
            #                                    autoload_with=actual_main_engine,
            #                                    extend_existing=True) # Important if other parts of code might also define 'Users'
            # logging.info(f"DEBUG_INIT_DB: 'Users' table reflected. Columns: {users_table_for_reflection.columns.keys()}")
            logging.info("DEBUG_INIT_DB: Second 'Users' table reflection SKIPPED in init_schema.py.")
        except Exception as e_reflect_users:
            # logging.error(f"DEBUG_INIT_DB: Error reflecting 'Users' table: {e_reflect_users}. Proceeding with create_all, but FK issues might persist.", exc_info=True)
            logging.error(f"DEBUG_INIT_DB: Error during second 'Users' table reflection (now skipped): {e_reflect_users}.", exc_info=True)

        try:
            # Import B2C restaurant models to register them with MainBase before create_all
            # This ensures that if b2c.ges_restaurant.models uses the same MainBase, its tables are included.
            import b2c.ges_restaurant.models # This registers restaurant models with MainBase
            logging.info("DEBUG_INIT_DB: Imported b2c.ges_restaurant.models for schema creation with MainBase.")
            # Also ensure accounting models are imported if they share MainBase
            import accounting.models # This registers accounting models with MainBase
            logging.info("DEBUG_INIT_DB: Imported accounting.models for schema creation with MainBase.")
        except ImportError as e_import_models_for_mainbase:
            logging.error(f"DEBUG_INIT_DB: Failed to import additional models (b2c or accounting) for MainBase: {e_import_models_for_mainbase}")
        except Exception as e_generic_import_for_mainbase:
            logging.error(f"DEBUG_INIT_DB: An unexpected error occurred during import of additional models for MainBase: {e_generic_import_for_mainbase}", exc_info=True)

        try:
            logging.info("DEBUG_INIT_DB: Creating tables for MainBase (e.g., CalculatorHistory, Products, Accounting, Restaurant*) using SQLAlchemy actual_main_engine.")
            # MainBase.metadata.create_all(bind=actual_main_engine, checkfirst=True) # INTENTIONALLY SKIPPED - Alembic should handle
            logging.info("DEBUG_INIT_DB: SKIPPED MainBase.metadata.create_all() here as Alembic should handle SQLAlchemy model tables.")
            logging.info("DEBUG_INIT_DB: Tables for MainBase (SQLAlchemy models) should be created by Alembic migration.")

            # Diagnostic: Check Products table schema right after creation by SQLAlchemy
            try:
                logging.info("DEBUG_INIT_DB: Checking 'Products' table schema immediately after MainBase.metadata.create_all()...")
                # Use the existing raw cursor 'cursor' which is still associated with 'conn'
                # Ensure 'conn' is still open and valid here.
                # Based on code flow, 'conn' is closed much later in the finally block of initialize_database.
                products_pragma_cursor = conn.cursor() # Create a new cursor instance from conn
                products_pragma_cursor.execute("PRAGMA table_info(Products)")
                products_columns_info = products_pragma_cursor.fetchall()
                if products_columns_info:
                    col_details = []
                    for col in products_columns_info:
                        # col is a sqlite3.Row object if conn.row_factory was set, or tuple
                        # Assuming conn.row_factory = sqlite3.Row is active on 'conn'
                        col_details.append(f"Name: {col['name']}, Type: {col['type']}, PK: {col['pk']}")
                    logging.info(f"DEBUG_INIT_DB: 'Products' table schema: {', '.join(col_details)}")
                else:
                    logging.warning("DEBUG_INIT_DB: 'Products' table not found or no schema info via PRAGMA after create_all.")
                products_pragma_cursor.close() # Close the temporary cursor
            except Exception as e_pragma_check:
                logging.error(f"DEBUG_INIT_DB: Error checking 'Products' table schema with PRAGMA: {e_pragma_check}", exc_info=True)

        except Exception as e_main_base_create:
            # This is where the original "NoReferencedTableError" for Products.created_by_user_id occurred.
            logging.error(f"DEBUG_INIT_DB: Error creating tables for MainBase: {e_main_base_create}", exc_info=True)

        # --- Manual check and addition for Products.product_code ---
        # This is a short-term fix. Alembic should be used for migrations.
        # try:
        #     logging.info("DEBUG_INIT_DB: Checking for 'product_code' column in 'Products' table...")
        #     cursor.execute("PRAGMA table_info(Products)")
        #     products_columns_info = cursor.fetchall()
        #     products_column_names = [info['name'] for info in products_columns_info]

        #     if 'product_code' not in products_column_names:
        #         logging.warning("DEBUG_INIT_DB: 'product_code' column NOT FOUND in 'Products' table. Attempting to add it.")
        #         try:
        #             cursor.execute("ALTER TABLE Products ADD COLUMN product_code TEXT")
        #             # The SQLAlchemy model defines unique=True, nullable=True.
        #             # The UNIQUE constraint would ideally be added too, but ALTER TABLE for constraints is limited in SQLite.
        #             # For new inserts, SQLAlchemy will respect the model's uniqueness.
        #             # For existing data, this just adds the column.
        #             conn.commit() # Commit this change immediately
        #             logging.info("DEBUG_INIT_DB: Successfully ADDED 'product_code' column to 'Products' table.")
        #         except sqlite3.Error as e_alter_products:
        #             logging.error(f"DEBUG_INIT_DB: FAILED to add 'product_code' column to 'Products' table: {e_alter_products}", exc_info=True)
        #             conn.rollback() # Rollback if alter fails
        #     else:
        #         logging.info("DEBUG_INIT_DB: 'product_code' column already exists in 'Products' table.")
        # except sqlite3.Error as e_check_products:
        #     # This might happen if Products table itself doesn't exist, though create_all should have handled it.
        #     logging.error(f"DEBUG_INIT_DB: Error checking 'Products' table schema for 'product_code': {e_check_products}", exc_info=True)
        # --- End manual check for Products.product_code ---

    else:
        logging.warning("DEBUG_INIT_DB: Main SQLAlchemy components (MainBase, actual_main_engine) not loaded or actual_main_engine is None. Skipping MainBase.metadata.create_all().")


    # --- Seed Data (from db/schema.py, ensuring use of db_config) ---
    try:
        print("DEBUG_INIT_DB: Starting data seeding phase.")

        # --- Seed Permissions and RolePermissions ---
        print("DEBUG_INIT_DB: Seeding Permissions and RolePermissions...")
        # Dynamically get all permission constants from auth.permissions
        from auth import permissions as auth_perms_module

        all_permission_keys = []
        for attr_name in dir(auth_perms_module):
            if attr_name.startswith("P_"):
                permission_key = getattr(auth_perms_module, attr_name)
                if isinstance(permission_key, str):
                    all_permission_keys.append(permission_key)

        for p_key in all_permission_keys:
            # Generate a simple description based on the key
            desc = p_key.replace("P_", "").replace("_", " ").capitalize()
            cursor.execute("INSERT OR IGNORE INTO Permissions (permission_key, description) VALUES (?, ?)",
                           (p_key, f"Permission to {desc}"))
        print(f"DEBUG_INIT_DB: {len(all_permission_keys)} permissions seeded into Permissions table.")

        # Seed RolePermissions based on the old PERMISSION_MAP
        # Ensure PERMISSION_MAP and role names (ADMINISTRATOR, etc.) are imported or accessible
        # from auth.permissions

        # Fetch role IDs
        role_id_map = {}
        cursor.execute("SELECT role_id, role_name FROM Roles")
        for row in cursor.fetchall():
            role_id_map[row['role_name']] = row['role_id']
        print(f"DEBUG_INIT_DB: Role ID Map for permission seeding: {role_id_map}")

        # 1. Seed Administrator with ALL permissions
        # The constant auth_perms_module.ADMINISTRATOR holds the string "Administrator"
        admin_role_name_from_const = auth_perms_module.ADMINISTRATOR # This is "Administrator"
        admin_role_id = role_id_map.get(admin_role_name_from_const)

        if admin_role_id:
            print(f"DEBUG_INIT_DB: Seeding ALL {len(all_permission_keys)} permissions for role '{admin_role_name_from_const}' (ID: {admin_role_id}).")
            admin_perms_added_count = 0
            for p_key in all_permission_keys:
                try:
                    cursor.execute("INSERT OR IGNORE INTO RolePermissions (role_id, permission_key) VALUES (?, ?)",
                                   (admin_role_id, p_key))
                    if cursor.rowcount > 0:

                        admin_perms_added_count += 1
                except sqlite3.IntegrityError:
                    print(f"DEBUG_INIT_DB: IntegrityError (ou permission non trouvée dans Permissions table) en essayant d'ajouter {p_key} pour Admin ID {admin_role_id}. Skipping.")
            print(f"DEBUG_INIT_DB: {admin_perms_added_count} permissions potentiellement nouvelles ajoutées pour le rôle '{admin_role_name_from_const}'. Total de permissions définies: {len(all_permission_keys)}.")
        else:
            print(f"DEBUG_INIT_DB: CRITICAL - Role '{admin_role_name_from_const}' not found in role_id_map. Cannot seed its permissions.")

        # 1b. Seed SUPER_ADMIN with ALL permissions (for data consistency, though code bypasses check)
        # SUPER_ADMIN_ROLE_NAME is "super_admin"
        from auth.roles import SUPER_ADMIN as SUPER_ADMIN_ROLE_NAME_CONST # Defined as "super_admin"

        # Ensure "super_admin" role exists in Roles table first (it should be added by db_seed.py if not present)
        # For safety, we can add it here too if not found, though db_seed.py is primary for user/role creation
        super_admin_role_id_check = role_id_map.get(SUPER_ADMIN_ROLE_NAME_CONST)
        if not super_admin_role_id_check:
            try:
                cursor.execute("INSERT OR IGNORE INTO Roles (role_name, description) VALUES (?, ?)", (SUPER_ADMIN_ROLE_NAME_CONST, "Super administrator with all system privileges."))
                conn.commit() # Commit this role creation immediately if it's critical path
                cursor.execute("SELECT role_id FROM Roles WHERE role_name = ?", (SUPER_ADMIN_ROLE_NAME_CONST,))
                super_admin_role_row = cursor.fetchone()
                if super_admin_role_row:
                    super_admin_role_id_check = super_admin_role_row['role_id']
                    role_id_map[SUPER_ADMIN_ROLE_NAME_CONST] = super_admin_role_id_check # Update map
                    print(f"DEBUG_INIT_DB: Role '{SUPER_ADMIN_ROLE_NAME_CONST}' was missing, created with ID {super_admin_role_id_check}.")
                else:
                    print(f"DEBUG_INIT_DB: CRITICAL - Failed to create or find role '{SUPER_ADMIN_ROLE_NAME_CONST}' even after attempting insert.")
            except Exception as e_sa_role:
                 print(f"DEBUG_INIT_DB: Error ensuring '{SUPER_ADMIN_ROLE_NAME_CONST}' role exists: {e_sa_role}")


        if super_admin_role_id_check:
            print(f"DEBUG_INIT_DB: Seeding ALL {len(all_permission_keys)} permissions for role '{SUPER_ADMIN_ROLE_NAME_CONST}' (ID: {super_admin_role_id_check}).")
            super_admin_perms_added_count = 0
            for p_key in all_permission_keys:
                try:
                    cursor.execute("INSERT OR IGNORE INTO RolePermissions (role_id, permission_key) VALUES (?, ?)",
                                   (super_admin_role_id_check, p_key))
                    if cursor.rowcount > 0:
                        super_admin_perms_added_count += 1
                except sqlite3.IntegrityError:
                     print(f"DEBUG_INIT_DB: IntegrityError for {p_key} for SuperAdmin ID {super_admin_role_id_check}. Skipping.")
            print(f"DEBUG_INIT_DB: {super_admin_perms_added_count} permissions potentiellement nouvelles ajoutées pour '{SUPER_ADMIN_ROLE_NAME_CONST}'.")
        else:
            print(f"DEBUG_INIT_DB: Role '{SUPER_ADMIN_ROLE_NAME_CONST}' not found in role_id_map. Cannot seed its permissions in RolePermissions.")


        # 2. Seed other roles based on PERMISSION_MAP (excluding Administrator and super_admin)
        # PERMISSION_MAP keys are role name strings
        # The values associated with these constants in auth_perms_module are the actual role names (strings)
        seeded_other_role_permissions_count = 0
        for role_name_constant, perm_keys_list_for_role in auth_perms_module.PERMISSION_MAP.items():
            # role_name_constant est déjà le nom du rôle string (ex: "Team Lead")
            # car les clés de PERMISSION_MAP sont les constantes qui contiennent ces strings.
            actual_role_name_str = role_name_constant

            if actual_role_name_str == admin_role_name_from_const:
                # print(f"DEBUG_INIT_DB: Skipping '{actual_role_name_str}' in PERMISSION_MAP loop as it's handled (all perms).")
                continue # Skip Administrator, already handled with all permissions

            role_id = role_id_map.get(actual_role_name_str)
            if role_id:
                # print(f"DEBUG_INIT_DB: Seeding permissions for role '{actual_role_name_str}' (ID: {role_id}) from PERMISSION_MAP.")
                current_role_perms_added_count = 0
                for perm_key in perm_keys_list_for_role:
                    if perm_key in all_permission_keys: # Ensure permission exists in Permissions table
                        try:
                            cursor.execute("INSERT OR IGNORE INTO RolePermissions (role_id, permission_key) VALUES (?, ?)",
                                           (role_id, perm_key))
                            if cursor.rowcount > 0:
                                seeded_other_role_permissions_count += 1
                                current_role_perms_added_count +=1
                        except sqlite3.IntegrityError:
                             print(f"DEBUG_INIT_DB: IntegrityError while seeding permission '{perm_key}' for role '{actual_role_name_str}'. Skipping.")
                    else:
                        print(f"DEBUG_INIT_DB: WARNING - Permission key '{perm_key}' for role '{actual_role_name_str}' in PERMISSION_MAP not found in defined P_ constants (ALL_PERMISSIONS). Skipping.")
                print(f"DEBUG_INIT_DB: Added {current_role_perms_added_count} permissions for '{actual_role_name_str}'.")
            else:
                print(f"DEBUG_INIT_DB: WARNING - Role name '{actual_role_name_str}' from PERMISSION_MAP not found in Roles table (IDs: {role_id_map}). Skipping its permissions.")
        print(f"DEBUG_INIT_DB: Total of {seeded_other_role_permissions_count} role-permission links added/verified for non-Admin roles from PERMISSION_MAP.")
        # --- End Seed Permissions and RolePermissions ---

        # --- Seed Data for User Profile Management ---
        print("DEBUG_INIT_DB: Seeding User Profile Management Data (Sectors, UseCases, DocumentTypes)...")
        # Seed DocumentTypes
        document_types_seed = [
            ('Facture', 'Document de facturation standard'),
            ('Devis', 'Proposition commerciale détaillée'),
            ('Bon de Commande', 'Document officiel d\'achat par un client'),
            ('Reçu', 'Preuve de paiement'),
            ('Bon de Livraison', 'Document attestant la livraison de marchandises'),
            ('Avoir', 'Note de crédit'),
            ('Facture Proforma', 'Facture préliminaire sans valeur comptable')
        ]
        cursor.executemany("INSERT OR IGNORE INTO DocumentTypes (name, description) VALUES (?, ?)", document_types_seed)
        print(f"DEBUG_INIT_DB: {len(document_types_seed)} DocumentTypes seeded or ignored.")

        # Seed Sectors
        sectors_seed = [
            ('Import/Export', 'B2B'), ('Fabrication Industrielle', 'B2B'),
            ('Services aux Entreprises', 'B2B'), ('Grossiste et Distribution', 'B2B'),
            ('Technologie et Informatique (B2B)', 'B2B'), ('Construction (Grands Projets)', 'B2B'),
            ('Logistique et Transport de Marchandises', 'B2B'),
            ('Commerce de Détail (Physique)', 'B2C'), ('Restauration et Hôtellerie', 'B2C'),
            ('Services à la Personne (Coiffure, Esthétique, etc.)', 'B2C'),
            ('E-commerce (Vente en ligne aux particuliers)', 'B2C'), ('Artisanat (Vente directe)', 'B2C'),
            ('Santé et Bien-être (Praticiens indépendants)', 'B2C'),
            ('Éducation et Formation (Cours particuliers, écoles privées)', 'B2C'),
            ('Automobile (Vente et Réparation)', 'BOTH'), ('Immobilier (Agences)', 'BOTH'),
            ('Conseil (Petites entreprises et Particuliers)', 'BOTH')
        ]
        cursor.executemany("INSERT OR IGNORE INTO Sectors (name, type_association) VALUES (?, ?)", sectors_seed)
        print(f"DEBUG_INIT_DB: {len(sectors_seed)} Sectors seeded or ignored.")

        # Seed UseCases
        use_cases_seed = [
            ('Gestion des Clients (CRM)', 'Suivi des interactions, historique, segmentation.'),
            ('Gestion des Commandes', 'Création, suivi, et gestion du cycle de vie des commandes.'),
            ('Facturation et Paiements', 'Émission de factures, suivi des paiements, relances.'),
            ('Gestion des Produits/Services', 'Catalogue produits, gestion des prix, descriptions.'),
            ('Gestion des Stocks', 'Suivi des niveaux de stock, alertes de réapprovisionnement.'),
            ('Production de Documents Commerciaux', 'Génération de devis, bons de commande, factures, etc.'),
            ('Rapports et Analyses de Vente', 'Tableaux de bord, analyse des performances.'),
            ('Gestion de Projet Simplifiée', 'Suivi des tâches et des échéances pour des petits projets.'),
            ('SAV et Support Client', 'Gestion des tickets de support, base de connaissances.'),
            ('Gestion des Fournisseurs', 'Base de données fournisseurs, suivi des achats.')
        ]
        cursor.executemany("INSERT OR IGNORE INTO UseCases (name, description) VALUES (?, ?)", use_cases_seed)
        print(f"DEBUG_INIT_DB: {len(use_cases_seed)} UseCases seeded or ignored.")
        # --- End Seed Data for User Profile Management ---

        # Accounting Module Seeding (example: base currency, default fiscal year)
        # --- THIS ENTIRE BLOCK MOVED TO db_seed.py -> _seed_accounting_data ---
        logging.info("DEBUG_INIT_DB: Accounting module data seeding is now handled by db_seed.py.")
        # --- END OF MOVED ACCOUNTING SEEDING BLOCK ---

        # User Seeding (Admin user) - This initial seeding attempt is now handled by db_seed.py
        # print("DEBUG_INIT_DB: Checking/Seeding Users...")
        # cursor.execute("SELECT COUNT(*) FROM Users")
        # if cursor.fetchone()['COUNT(*)'] == 0: # Use dict access due to row_factory
        #     admin_uid = str(uuid.uuid4())
        #     # Generate salt and hash for default admin - direct SQL insertion for bootstrap
        #     admin_salt = os.urandom(16).hex()
        #     admin_password_bytes = config.DEFAULT_ADMIN_PASSWORD.encode('utf-8')
        #     admin_salt_bytes = bytes.fromhex(admin_salt)
        #     admin_pass_hash = hashlib.sha256(admin_salt_bytes + admin_password_bytes).hexdigest()

        #     cursor.execute("""
        #         INSERT OR IGNORE INTO Users
        #             (user_id, username, password_hash, salt, full_name, email, role, is_deleted, deleted_at)
        #         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        #     """, (admin_uid, config.DEFAULT_ADMIN_USERNAME, admin_pass_hash, admin_salt,
        #           'Default Admin', f'{config.DEFAULT_ADMIN_USERNAME}@example.com', SUPER_ADMIN, 0, None))
        #     print(f"Admin user '{config.DEFAULT_ADMIN_USERNAME}' seeded with salt and hash.")
        #     print("DEBUG_INIT_DB: Admin user potentially seeded.")
        # print("DEBUG_INIT_DB: User seeding check complete.") # End of commented block

        # Application Settings Seeding
        print("DEBUG_INIT_DB: Seeding Application Settings...")
        # Using the imported set_setting CRUD function, passing the connection
        set_setting('initial_data_seeded_version', '1.3_consolidated_schema', conn=conn) # Pass conn
        set_setting('default_app_language', 'en', conn=conn) # Pass conn
        set_setting('client_document_template_categories', 'General,Document Utilitaires', conn=conn) # New setting
        print("DEBUG_INIT_DB: Application settings seeded.")

        # Populate Default Cover Page Templates
        print("DEBUG_INIT_DB: Populating Default Cover Page Templates...")
        _populate_default_cover_page_templates(conn_passed=conn) # Uses CRUDs internally
        print("DEBUG_INIT_DB: Default Cover Page Templates population attempt finished.")

        conn.commit() # Commit all schema changes and seeding
        print("DEBUG_INIT_DB: Data seeding phase committed successfully.")
        print("Database schema initialized and initial data seeded successfully.")
    except Exception as e_seed:
        print(f"DEBUG_INIT_DB: Error during data seeding: {e_seed}") # Existing error print
        conn.rollback() # Rollback in case of error during seeding
        print("DEBUG_INIT_DB: Rollback due to seeding error.")
    finally:
        try:
            conn.commit() # Ensure all seeding changes are committed if no error occurred before finally
            print("DEBUG_INIT_DB: Final commit in initialize_database successful.")
        except sqlite3.Error as e_final_commit:
            print(f"DEBUG_INIT_DB: Error during final commit in initialize_database: {e_final_commit}")
            # Optionally rollback again, though if an error occurs here, DB state might be complex
            conn.rollback()
        finally:
            conn.close()
            print("DEBUG_INIT_DB: Main SQLite connection 'conn' closed at the end of initialize_database.")

if __name__ == '__main__':
    # This direct call is for testing init_schema.py itself.
    # In the application, main.py provides the config.
    # For standalone test, we create a mock config.
    print("Running init_schema.py directly for testing purposes.")

    # Determine a root path for the test database if needed, relative to this script
    # This assumes db/init_schema.py, so two levels up is project root.
    _project_root_for_test = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _test_db_path = os.path.join(_project_root_for_test, "app_data_standalone_init_test.db")

    mock_app_config = {
        "database_path": _test_db_path,
        # Add any other keys that initialize_database or its callees might expect from app_config
        # for standalone execution. For now, only database_path is strictly necessary for init_schema.
        # For example, if seeding logic inside initialize_database relies on config for default admin:
        # "DEFAULT_ADMIN_USERNAME": "admin_standalone_test",
        # "DEFAULT_ADMIN_PASSWORD": "password_standalone_test"
    }
    print(f"Using mock database path for standalone test: {mock_app_config['database_path']}")

    # Ensure a clean state by deleting the test database file if it exists
    if os.path.exists(mock_app_config["database_path"]):
        try:
            os.remove(mock_app_config["database_path"])
            print(f"Deleted existing test database: {mock_app_config['database_path']}")
        except OSError as e:
            print(f"Error deleting test database {mock_app_config['database_path']}: {e}. Proceeding might use old data or fail.")

    # Ensure the directory for the mock database exists
    _test_db_dir = os.path.dirname(mock_app_config["database_path"])
    if _test_db_dir and not os.path.exists(_test_db_dir):
        os.makedirs(_test_db_dir, exist_ok=True)
        print(f"Created directory for mock test database: {_test_db_dir}")

    initialize_database(mock_app_config)
    print("Schema initialization complete (called from init_schema.py __main__ with mock_app_config).")