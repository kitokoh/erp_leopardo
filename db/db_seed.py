import sqlite3
import os
import json
import logging
from datetime import datetime, date
import uuid
import hashlib
from decimal import Decimal
import sys

# Get the project root directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    import config
except ImportError:
    print("CRITICAL: config.py not found at project root by db/db_seed.py. Using fallback configurations.")
    class config_fallback:
        DATABASE_PATH = os.path.join(project_root, "app_data_fallback_seed.db")
        DEFAULT_ADMIN_USERNAME = "admin_fallback_seed"
        DEFAULT_ADMIN_PASSWORD = "password_fallback_seed"
        # Add other necessary fallbacks if db_seed.py uses them directly
    config = config_fallback

# Import CRUDs that might be used by seeders (examples)
from .cruds.application_settings_crud import set_setting as crud_set_setting
from .cruds.users_crud import create_user, get_user_by_username
from .cruds.roles_crud import get_role_by_name
from .cruds.cover_page_templates_crud import add_cover_page_template, get_cover_page_template_by_name

# Import seeder modules (will be created in Phase 3)
from .seeders import (
    s01_seed_roles,
    s02_seed_permissions,
    s03_seed_role_permissions,
    s04_seed_admin_user,
    s05_seed_default_settings,
    s06_seed_statuses, # Statuses are pre-seeded in init_schema for FKs, but this could augment or verify
    s07_seed_default_templates,
    s08_seed_sample_data,
    s09_seed_partner_categories,
    s10_seed_accounting_defaults
)

# Example: Default cover page templates data (originally in init_schema.py)
# This kind of data should ideally live within its specific seeder module (e.g., s07_seed_default_templates.py)
DEFAULT_COVER_PAGE_TEMPLATES_DATA = [
    {'template_name': 'Standard Report Cover', 'description': 'A standard cover page for general reports.', 'default_title': 'Report Title', 'default_subtitle': 'Company Subdivision', 'default_author': 'Automated Report Generator', 'style_config_json': {'font': 'Helvetica', 'primary_color': '#2a2a2a', 'secondary_color': '#5cb85c'}, 'is_default_template': 1},
    {'template_name': 'Financial Statement Cover', 'description': 'Cover page for official financial statements.', 'default_title': 'Financial Statement', 'default_subtitle': 'Fiscal Year Ending YYYY', 'default_author': 'Finance Department', 'style_config_json': {'font': 'Times New Roman', 'primary_color': '#003366', 'secondary_color': '#e0a800'}, 'is_default_template': 1},
    # ... more templates
]

def seed_all_data():
    """
    Orchestrates the data seeding process by calling dedicated seeder functions.
    """
    logging.info("Starting database data seeding...")
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Call seeder functions from db.seeders modules
        # Note: Roles and Statuses are pre-seeded in init_schema.py due to FK constraints.
        # Seeders here can augment, verify, or add more complex/related data.
        
        # s01_seed_roles.seed_data(cursor, conn) # Example: if roles needed more complex seeding
        s02_seed_permissions.seed_data(cursor, conn) # This will populate Permissions table
        s03_seed_role_permissions.seed_data(cursor, conn) # This will link Roles and Permissions
        s04_seed_admin_user.seed_data(cursor, conn)
        s05_seed_default_settings.seed_data(cursor, conn) # For ApplicationSettings
        # s06_seed_statuses.seed_data(cursor, conn) # Statuses are mostly handled in init_schema
        s07_seed_default_templates.seed_data(cursor, conn) # For CoverPageTemplates, EmailTemplates etc.
        s08_seed_sample_data.seed_data(cursor, conn) # Countries, Cities, example client etc.
        s09_seed_partner_categories.seed_data(cursor, conn)
        s10_seed_accounting_defaults.seed_data(cursor, conn) # Base currency, fiscal year if not in init_schema

        # Example of moving _populate_default_cover_page_templates here
        # This would be inside s07_seed_default_templates.py typically
        # print("Populating default cover page templates from db_seed...")
        # for template_def in DEFAULT_COVER_PAGE_TEMPLATES_DATA:
        #     existing_template = get_cover_page_template_by_name(template_def['template_name'], conn=conn)
        #     if existing_template:
        #         print(f"Seed: Default template '{template_def['template_name']}' already exists. Skipping.")
        #     else:
        #         template_def_for_add = template_def.copy()
        #         if isinstance(template_def_for_add.get('style_config_json'), dict):
        #             template_def_for_add['style_config_json'] = json.dumps(template_def_for_add['style_config_json'])
        #         new_id = add_cover_page_template(template_def_for_add, conn=conn)
        #         if new_id:
        #             print(f"Seed: Added default cover page template: '{template_def['template_name']}' with ID: {new_id}")
        #         else:
        #             print(f"Seed: Failed to add default cover page template: '{template_def['template_name']}'")
        # print("Seed: Default cover page templates population attempt finished.")

        conn.commit()
        logging.info("Database data seeding committed successfully.")

    except sqlite3.Error as e:
        logging.error(f"SQLite error during seeding: {e}", exc_info=True)
        conn.rollback()
        logging.info("Database seeding rolled back due to error.")
    except Exception as e:
        logging.error(f"An unexpected error occurred during seeding: {e}", exc_info=True)
        conn.rollback()
        logging.info("Database seeding rolled back due to unexpected error.")
    finally:
        conn.close()
        logging.info("SQLite connection closed after seeding attempt.")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    # Ensure schema is created before seeding
    # In a real application, you might call init_schema.initialize_database() first
    # or ensure it's run as part of a larger setup script.
    print(f"Running db_seed.py directly. Database: {config.DATABASE_PATH}")
    print("NOTE: This script assumes the database schema has already been initialized by init_schema.py.")

    # For standalone testing, you might want to initialize schema first if it's not guaranteed
    # from db import init_schema
    # print("Initializing schema before seeding (for standalone test)...")
    # init_schema.initialize_database()
    # print("Schema initialization complete.")

    seed_all_data()
    print("Data seeding script complete.")
