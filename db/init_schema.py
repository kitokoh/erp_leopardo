import sqlite3
import os
import json
import logging
from datetime import datetime, date
import uuid
import hashlib
from decimal import Decimal
from sqlalchemy import create_engine
import sys

# Get the project root directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    import config
except ImportError:
    print("CRITICAL: config.py not found at project root by db/init_schema.py. Using fallback configurations.")
    class config_fallback:
        DATABASE_PATH = os.path.join(project_root, "app_data_fallback_init.db")
        DEFAULT_ADMIN_USERNAME = "admin_fallback_init"
        DEFAULT_ADMIN_PASSWORD = "password_fallback_init"
    config = config_fallback

try:
    from db.connection import Base as MainBase, engine as main_engine
    from calculator.models import CalculationHistory
    MAIN_SQLALCHEMY_COMPONENTS_LOADED = True
except ImportError as e_main_sqlalchemy:
    logging.error(f"db.init_schema: Could not import MainBase or main_engine from db.connection: {e_main_sqlalchemy}. Tables using MainBase might not be created by this script.")
    MAIN_SQLALCHEMY_COMPONENTS_LOADED = False
    MainBase = None
    main_engine = None

from auth.roles import SUPER_ADMIN
from .cruds.users_crud import get_user_by_username
from .cruds.locations_crud import get_country_by_name, get_city_by_name_and_country_id
from .cruds.status_settings_crud import get_status_setting_by_name
from .cruds.application_settings_crud import set_setting
from .cruds.cover_page_templates_crud import add_cover_page_template, get_cover_page_template_by_name
from .cruds.template_categories_crud import add_template_category

# Import schema modules (will be created in Phase 2)
from .schema import (
    s01_schema_core_structure,
    s02_schema_users_auth,
    s03_schema_clients_projects,
    s04_schema_products_inventory,
    s05_schema_documents_templates,
    s06_schema_partners,
    s07_schema_recruitment,
    s08_schema_accounting, # This will likely be handled by SQLAlchemy models
    s09_schema_misc_modules,
    s10_schema_indexes # Or handle indexes within each module
)


def _get_or_create_category_id(cursor: sqlite3.Cursor, category_name: str, default_category_id: int | None) -> int | None:
    if not category_name: return default_category_id
    try:
        cursor.execute("SELECT category_id FROM TemplateCategories WHERE category_name = ?", (category_name,))
        row = cursor.fetchone()
        if row:
            return row['category_id']
        else:
            cursor.execute("INSERT INTO TemplateCategories (category_name, description) VALUES (?, ?)",
                           (category_name, f"{category_name} (auto-created during schema init)"))
            return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Error in _get_or_create_category_id for '{category_name}': {e}")
        return default_category_id

DEFAULT_COVER_PAGE_TEMPLATES = [
    {'template_name': 'Standard Report Cover', 'description': 'A standard cover page for general reports.', 'default_title': 'Report Title', 'default_subtitle': 'Company Subdivision', 'default_author': 'Automated Report Generator', 'style_config_json': {'font': 'Helvetica', 'primary_color': '#2a2a2a', 'secondary_color': '#5cb85c'}, 'is_default_template': 1},
    {'template_name': 'Financial Statement Cover', 'description': 'Cover page for official financial statements.', 'default_title': 'Financial Statement', 'default_subtitle': 'Fiscal Year Ending YYYY', 'default_author': 'Finance Department', 'style_config_json': {'font': 'Times New Roman', 'primary_color': '#003366', 'secondary_color': '#e0a800'}, 'is_default_template': 1},
    {'template_name': 'Creative Project Brief', 'description': 'A vibrant cover for creative project briefs and proposals.', 'default_title': 'Creative Brief: [Project Name]', 'default_subtitle': 'Client: [Client Name]', 'default_author': 'Creative Team', 'style_config_json': {'font': 'Montserrat', 'primary_color': '#ff6347', 'secondary_color': '#4682b4', 'layout_hint': 'two-column'}, 'is_default_template': 1},
    {'template_name': 'Technical Document Cover', 'description': 'A clean and formal cover for technical documentation.', 'default_title': 'Technical Specification Document', 'default_subtitle': 'Version [VersionNumber]', 'default_author': 'Engineering Team', 'style_config_json': {'font': 'Roboto', 'primary_color': '#191970', 'secondary_color': '#cccccc'}, 'is_default_template': 1}
]

def _populate_default_cover_page_templates(conn_passed):
    print("Populating default cover page templates...")
    for template_def in DEFAULT_COVER_PAGE_TEMPLATES:
        existing_template = get_cover_page_template_by_name(template_def['template_name'], conn=conn_passed)
        if existing_template:
            print(f"Default template '{template_def['template_name']}' already exists. Skipping.")
        else:
            template_def_for_add = template_def.copy()
            if isinstance(template_def_for_add.get('style_config_json'), dict):
                template_def_for_add['style_config_json'] = json.dumps(template_def_for_add['style_config_json'])
            new_id = add_cover_page_template(template_def_for_add, conn=conn_passed)
            if new_id:
                print(f"Added default cover page template: '{template_def['template_name']}' with ID: {new_id}")
            else:
                print(f"Failed to add default cover page template: '{template_def['template_name']}'")
    print("Default cover page templates population attempt finished.")


def initialize_database():
    """
    Orchestrates the database schema creation by calling dedicated modules.
    Seeding is handled by db_seed.py, which should be called after this.
    """
    engine = create_engine(f"sqlite:///{config.DATABASE_PATH}")
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    logging.info("Starting database schema initialization...")

    # Call schema creation functions from db.schema modules
    # These functions will contain the CREATE TABLE and CREATE INDEX statements
    s01_schema_core_structure.create_schema(cursor)
    s02_schema_users_auth.create_schema(cursor)
    s03_schema_clients_projects.create_schema(cursor)
    s04_schema_products_inventory.create_schema(cursor)
    s05_schema_documents_templates.create_schema(cursor)
    s06_schema_partners.create_schema(cursor)
    s07_schema_recruitment.create_schema(cursor)
    # s08_schema_accounting.create_schema(cursor) # This will be handled by SQLAlchemy models
    s09_schema_misc_modules.create_schema(cursor)

    # Option 1: Call a dedicated index creation module
    s10_schema_indexes.create_indexes(cursor)
    # Option 2: Indexes are created within each sXX_schema_... module (preferred)
    # If Option 2, then s10_schema_indexes might not be needed or could handle specific cross-module indexes.

    # --- Migrations for existing columns (Keep this logic here or move to relevant schema modules) ---
    # Example: Ensure is_deleted, and deleted_at columns exist in Users table
    cursor.execute("PRAGMA table_info(Users)")
    users_columns_info = cursor.fetchall()
    users_column_names = [info['name'] for info in users_columns_info]
    if 'is_deleted' not in users_column_names:
        try:
            cursor.execute("ALTER TABLE Users ADD COLUMN is_deleted INTEGER DEFAULT 0")
            logging.info("Added 'is_deleted' column to Users table.")
        except sqlite3.Error as e:
            logging.error(f"Error adding 'is_deleted' column to Users table: {e}")
    # ... (other migration checks can remain here or be moved)

    # --- Accounting Module Tables (SQLAlchemy part) ---
    try:
        logging.info("Creating Accounting Module Tables using SQLAlchemy engine.")
        from accounting import models as acc_models
        acc_models.Base.metadata.create_all(bind=engine, checkfirst=True)
        logging.info("Accounting Module Tables creation attempted using SQLAlchemy engine.")
        # Accounting indexes are expected to be defined in their SQLAlchemy models or created via s08_schema_accounting if manual
    except ImportError:
        logging.warning("Could not import accounting models. Skipping accounting table creation via SQLAlchemy.")
    except Exception as e_acc_schema:
        logging.error(f"CRITICAL ERROR during Accounting module SQLAlchemy schema creation: {e_acc_schema}")
        conn.rollback() # Rollback if this part fails critically

    # --- Create tables for MainBase (e.g., CalculatorHistory) ---
    if MAIN_SQLALCHEMY_COMPONENTS_LOADED and MainBase is not None and main_engine is not None:
        try:
            logging.info("Creating tables for MainBase (e.g., CalculatorHistory) using SQLAlchemy main_engine.")
            MainBase.metadata.create_all(bind=main_engine, checkfirst=True)
            logging.info("Tables for MainBase created successfully.")
        except Exception as e_main_base_create:
            logging.error(f"Error creating tables for MainBase: {e_main_base_create}", exc_info=True)
    else:
        logging.warning("Main SQLAlchemy components not loaded. Skipping MainBase.metadata.create_all().")


    # --- Seeding (This will be moved to db_seed.py) ---
    # For now, keeping essential seeding like default roles, statuses, and application settings.
    # More complex seeding (admin user, specific templates) will be in db_seed.py.

    # Populate Roles table (essential for FKs)
    default_roles = [
        {"role_name": "Administrator", "description": "Full system access."},
        {"role_name": "Team Lead", "description": "Manages projects and teams."},
        {"role_name": "Operator", "description": "Standard user with operational access."}
    ]
    for role_data in default_roles:
        cursor.execute("INSERT OR IGNORE INTO Roles (role_name, description) VALUES (?, ?)",
                       (role_data["role_name"], role_data["description"]))
    logging.info("Default roles seeded or already exist.")

    # Pre-populate StatusSettings (essential for FKs)
    default_statuses = [
        {'status_name': 'Prospect', 'status_type': 'Client', 'color_hex': '#f1c40f', 'icon_name': 'user-status-pending', 'sort_order': 0},
        # ... (include all default statuses as before)
        {'status_name': 'No Show', 'status_type': 'InterviewStatus', 'color_hex': '#c0392b', 'icon_name': 'calendar-question', 'sort_order': 4},
    ]
    for status in default_statuses:
        cursor.execute("""
            INSERT OR IGNORE INTO StatusSettings (
                status_name, status_type, color_hex, icon_name,
                is_completion_status, is_archival_status, default_duration_days, sort_order
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            status['status_name'], status['status_type'], status['color_hex'],
            status.get('icon_name'), status.get('is_completion_status', False),
            status.get('is_archival_status', False), status.get('default_duration_days'),
            status.get('sort_order', 0)
        ))
    logging.info("Default statuses seeded or already exist.")

    # Application Settings Seeding (basic ones)
    set_setting('initial_schema_version', '2.0_refactored', conn=conn)
    set_setting('default_app_language', 'en', conn=conn)
    logging.info("Basic application settings seeded.")

    # The rest of the seeding logic (admin user, permissions, cover pages, etc.)
    # will be moved to db_seed.py.
    # For example:
    # _populate_default_cover_page_templates(conn_passed=conn) # This will move
    # Seeding of Permissions, RolePermissions, admin user, etc. will move.

    try:
        conn.commit()
        logging.info("Database schema initialization and essential pre-seeding committed successfully.")
    except sqlite3.Error as e_commit:
        logging.error(f"Error committing schema changes: {e_commit}", exc_info=True)
        conn.rollback()
    finally:
        conn.close()
        logging.info("SQLite connection closed.")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    print(f"Running init_schema.py directly. Using database path: {config.DATABASE_PATH}")
    initialize_database()
    # Note: After this, db_seed.py should be run for full data seeding.
    print("Schema initialization script complete. Run db_seed.py for data seeding.")
