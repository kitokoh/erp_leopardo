import json
import logging
import os
from db.cruds.misc.locations_crud import get_or_add_country, get_or_add_city

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def seed_locations(conn, logger: logging.Logger):
    """
    Seeds countries and cities from a JSON file.
    """
    logger.info("Seeding locations from JSON file...")
    json_path = os.path.join(PROJECT_ROOT, "db", "seed_data", "default_locations.json")

    if not os.path.exists(json_path):
        logger.error(f"JSON file not found at: {json_path}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    countries_cities = data.get("countries_cities", {})
    for country_name, city_name in countries_cities.items():
        country_dict = get_or_add_country(country_name, conn=conn)
        if country_dict and 'id' in country_dict:
            country_id = country_dict['id']
            get_or_add_city(city_name, country_id, conn=conn)
        else:
            logger.error(f"Could not get or add country: {country_name}")

    logger.info("Finished seeding locations.")
