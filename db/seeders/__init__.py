import logging
import sqlite3
from .seed_roles_and_permissions import seed_roles_and_permissions
from .seed_users import seed_users
from db.cruds.misc.locations_crud import get_or_add_country, get_or_add_city
from db.cruds.misc.status_settings_crud import get_status_setting_by_name
from db.cruds.clients.clients_crud import clients_crud_instance
from db.cruds.projects.projects_crud import projects_crud_instance
from db.cruds.misc.templates_crud import add_default_template_if_not_exists
from db.cruds.misc.application_settings_crud import set_setting
from db.hidroguc_product_seeder import seed_hidroguc_products
from sqlalchemy.orm import Session
from db import connection as db_connection_module

def seed_all(db_session: Session):
    """Master seeding function."""
    logger = logging.getLogger(__name__)
    logger.info("Starting database seeding...")

    # It's better to use the session for all operations if possible
    # but the old seed script mixes raw sqlite3 connections and sessions.
    # We will try to use the session where possible.

    # For raw sqlite3 operations, we can get the underlying connection
    raw_conn = db_session.connection().connection

    role_ids = seed_roles_and_permissions(raw_conn, logger)
    seed_users(db_session, logger, role_ids)

    # Simplified seeding for other data
    countries_cities = {"France": "Paris", "USA": "New York"}
    for country_name, city_name in countries_cities.items():
        country = get_or_add_country(country_name, conn=raw_conn)
        if country:
            get_or_add_city(city_name, country['country_id'], conn=raw_conn)

    # Seed hidroguc products
    seed_hidroguc_products(db_session, logger)

    logger.info("Database seeding complete.")
