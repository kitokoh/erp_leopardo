import json
import os
import logging
from sqlalchemy.orm import Session
from app.models.db.locations import Country, City

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def seed_all_locations(db: Session, logger: logging.Logger):
    """
    Refactored function to seed locations from JSON using a bulk insert strategy.
    """
    logger.info("--- Starting refactored location seeding ---")
    json_path = os.path.join(PROJECT_ROOT, "db", "seed_data", "default_countries.json")

    if not os.path.exists(json_path):
        logger.error(f"JSON file not found: {json_path}. Skipping location seeding.")
        return

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            countries_cities = json.load(f)

        logger.info(f"Loaded {len(countries_cities)} country/city pairs from JSON.")

        # 1. Prepare country data
        existing_countries_q = db.query(Country.country_name).all()
        existing_countries = {c[0] for c in existing_countries_q}

        unique_countries_in_json = {country_name for country_name in countries_cities.keys()}

        new_country_mappings = [
            {"country_name": name} for name in unique_countries_in_json if name not in existing_countries
        ]

        # 2. Bulk insert new countries
        if new_country_mappings:
            logger.info(f"Adding {len(new_country_mappings)} new countries.")
            db.bulk_insert_mappings(Country, new_country_mappings)
            db.commit()
            logger.info("New countries have been bulk inserted.")
        else:
            logger.info("No new countries to add.")

        # 3. Get a map of all countries (new and existing) to their IDs
        all_countries_q = db.query(Country.country_id, Country.country_name).all()
        country_map = {name: id for id, name in all_countries_q}

        # 4. Prepare city data
        existing_cities_q = db.query(City.city_name, City.country_id).all()
        existing_cities = {(name, country_id) for name, country_id in existing_cities_q}

        city_mappings_to_insert = []
        for country_name, city_name in countries_cities.items():
            country_id = country_map.get(country_name)
            if not country_id:
                logger.warning(f"Could not find country ID for '{country_name}' while preparing cities. Skipping city '{city_name}'.")
                continue

            if (city_name, country_id) not in existing_cities:
                city_mappings_to_insert.append({
                    "city_name": city_name,
                    "country_id": country_id
                })

        # 5. Bulk insert new cities
        if city_mappings_to_insert:
            logger.info(f"Adding {len(city_mappings_to_insert)} new cities.")
            db.bulk_insert_mappings(City, city_mappings_to_insert)
            db.commit()
            logger.info("New cities have been bulk inserted.")
        else:
            logger.info("No new cities to add.")

        logger.info("--- Finished refactored location seeding ---")

    except Exception as e:
        logger.error(f"An error occurred during the refactored location seeding: {e}", exc_info=True)
        db.rollback()
