import json
import os
import uuid
import logging
import sqlite3

from db.cruds.misc.locations_crud import get_or_add_country, get_or_add_city, get_country_by_name
from db.cruds.misc import regions_crud

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def seed_locations_from_json(conn: sqlite3.Connection, logger: logging.Logger):
    """Seeds countries and cities from the default_countries.json file."""
    logger.info("Seeding countries and cities from default_countries.json...")
    json_path = os.path.join(PROJECT_ROOT, "db", "seed_data", "default_countries.json")

    if not os.path.exists(json_path):
        logger.error(f"JSON file not found at: {json_path}. Skipping location seeding from JSON.")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        countries_cities = json.load(f)

    for country_name, city_name in countries_cities.items():
        country_dict = get_or_add_country(country_name, conn=conn)
        if country_dict and 'country_id' in country_dict:
            get_or_add_city(city_name, country_dict['country_id'], conn=conn)
        else:
            logger.error(f"Failed to get or add country '{country_name}'. Cannot add city '{city_name}'.")
    logger.info(f"Finished seeding {len(countries_cities)} countries/cities from JSON.")


def seed_countries_from_geojson(conn: sqlite3.Connection, logger: logging.Logger):
    """Seeds countries from the world_countries.geojson file."""
    logger.info("Attempting to seed countries from GeoJSON file...")
    cursor = conn.cursor()
    geojson_path = os.path.join(PROJECT_ROOT, "resources", "assets", "world_countries.geojson")

    if not os.path.exists(geojson_path):
        logger.error(f"GeoJSON file not found at: {geojson_path}. Skipping country seeding from GeoJSON.")
        return

    with open(geojson_path, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)

    added_count = 0
    skipped_count = 0
    for feature in geojson_data['features']:
        country_name = feature['properties']['name']
        country_iso_a2 = feature['properties']['iso_a2']

        existing_country = get_country_by_name(country_name, conn=conn)
        if existing_country:
            if not existing_country.get('iso_a2_code'):
                try:
                    cursor.execute("UPDATE Countries SET iso_a2_code = ? WHERE country_id = ?", (country_iso_a2, existing_country['country_id']))
                    logger.info(f"Updated missing iso_a2_code for existing country: {country_name}")
                except sqlite3.Error as e:
                    logger.error(f"Error updating iso_a2_code for {country_name}: {e}")
            skipped_count += 1
            continue

        country_id = str(uuid.uuid4())
        try:
            cursor.execute("INSERT INTO Countries (country_id, country_name, iso_a2_code) VALUES (?, ?, ?)",
                           (country_id, country_name, country_iso_a2))
            added_count += 1
        except sqlite3.IntegrityError:
            logger.warning(f"Country '{country_name}' already exists (IntegrityError). Skipping.")
            skipped_count += 1
        except Exception as e:
            logger.error(f"Error adding country '{country_name}': {e}")
            skipped_count += 1

    logger.info(f"Finished seeding countries from GeoJSON. Added: {added_count}, Skipped/Existing: {skipped_count}")


def seed_default_regions(conn: sqlite3.Connection, logger: logging.Logger):
    """Seeds default regions for a predefined list of countries."""
    logger.info("Attempting to seed default regions...")
    default_regions_data = {
        "France": ["Île-de-France", "Occitanie", "Nouvelle-Aquitaine", "Auvergne-Rhône-Alpes"],
        "USA": ["California", "New York", "Texas", "Florida"],
        "Algeria": ["Alger", "Oran", "Constantine"]
    }

    added_count = 0
    skipped_count = 0
    for country_name, region_names in default_regions_data.items():
        country = get_country_by_name(country_name, conn=conn)
        if not country or 'country_id' not in country:
            logger.warning(f"Country '{country_name}' not found for seeding its regions. Skipping.")
            skipped_count += len(region_names)
            continue

        country_id = country['country_id']
        for region_name in region_names:
            existing_region = regions_crud.get_region_by_name_and_country_id(region_name, country_id, conn=conn)
            if existing_region:
                skipped_count += 1
                continue

            region_id = regions_crud.add_region(region_name, country_id, conn=conn)
            if region_id:
                added_count += 1
                logger.info(f"Added region '{region_name}' to '{country_name}'.")
            else:
                logger.warning(f"Failed to add region '{region_name}' to '{country_name}'.")
                skipped_count +=1
    logger.info(f"Default regions seeding complete. Added: {added_count}, Skipped/Existing: {skipped_count}")


def seed_all_locations(conn: sqlite3.Connection, logger: logging.Logger):
    """Runs all location-related seeding functions."""
    logger.info("--- Starting all location seeding ---")
    seed_locations_from_json(conn, logger)
    seed_countries_from_geojson(conn, logger)
    seed_default_regions(conn, logger)
    logger.info("--- Finished all location seeding ---")
