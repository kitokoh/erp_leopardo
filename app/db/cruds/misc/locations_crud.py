import sqlite3
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from app.models.db.locations.country import Country
from app.models.db.locations.city import City
from app.db.generic_crud import _manage_conn, _convert_to_dict

# --- Countries CRUD ---
@_manage_conn
def get_country_by_name(name: str, conn: Session = None) -> dict | None:
    logger_crud = logging.getLogger(__name__)
    try:
        logger_crud.info(f"locations_crud.get_country_by_name: Querying for Name='{name}'")
        sql_query = text("SELECT * FROM Countries WHERE country_name = :name")
        result = conn.execute(sql_query, {"name": name})
        row = result.fetchone()
        if row:
            country_dict = _convert_to_dict(row)
            logger_crud.info(f"locations_crud.get_country_by_name: Found country '{name}' with data: {country_dict}")
            return country_dict
        else:
            logger_crud.warning(f"locations_crud.get_country_by_name: Country '{name}' NOT found.")
            return None
    except Exception as e:
        logging.error(f"Error getting country by name '{name}': {e}", exc_info=True)
        return None

@_manage_conn
def get_country_by_id(id: int, conn: Session = None) -> dict | None:
    try:
        sql_query = text("SELECT * FROM Countries WHERE country_id = :id")
        result = conn.execute(sql_query, {"id": id})
        row = result.fetchone()
        return _convert_to_dict(row) if row else None
    except Exception as e:
        logging.error(f"Error getting country by id {id}: {e}", exc_info=True)
        return None

def get_or_add_country(country_name: str, db: Session) -> Country | None:
    if not country_name:
        logging.warning("locations_crud.get_or_add_country: country_name is required.")
        return None

    logger_crud = logging.getLogger(__name__)
    logger_crud.info(f"locations_crud.get_or_add_country: Processing country: '{country_name}'")

    try:
        country = db.query(Country).filter(Country.country_name == country_name).first()
        if country:
            logger_crud.info(f"locations_crud.get_or_add_country: Found existing country '{country_name}' with data: {country}")
            return country

        else:
            logger_crud.info(f"locations_crud.get_or_add_country: Country '{country_name}' not found, adding it now.")
            new_country = Country(country_name=country_name)
            db.add(new_country)
            db.commit()
            db.refresh(new_country)
            logger_crud.info(f"locations_crud.get_or_add_country: Successfully added '{country_name}', new ID: {new_country.country_id}")
            return new_country
    except Exception as e:
        logger_crud.error(f"locations_crud.get_or_add_country: General error for '{country_name}': {e}", exc_info=True)
        db.rollback()
        return None

@_manage_conn
def add_country(data: dict, conn: Session = None) -> int | None:
    if 'country_name' not in data:
        logging.error("add_country: 'country_name' is required in data.")
        return None

    country_name = data['country_name']
    existing_country = get_country_by_name(country_name, conn=conn)
    if existing_country:
        return existing_country['country_id']

    now = datetime.utcnow()
    sql = text("INSERT INTO Countries (country_name, created_at, updated_at) VALUES (:name, :created, :updated)")
    params = {"name": country_name, "created": now, "updated": now}
    try:
        result = conn.execute(sql, params)
        conn.commit()
        return result.lastrowid
    except Exception as e:
        logging.error(f"Database error in add_country for '{country_name}': {e}", exc_info=True)
        conn.rollback()
        return None

@_manage_conn
def get_all_countries(conn: Session = None) -> list[dict]:
    try:
        countries = conn.query(Country).order_by(Country.country_name).all()
        return [
            {
                "country_id": c.country_id,
                "country_name": c.country_name,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            }
            for c in countries
        ]
    except Exception as e:
        logging.error(f"Database error in get_all_countries: {e}", exc_info=True)
        return []

# --- Cities CRUD ---
@_manage_conn
def get_city_by_name_and_country_id(name: str, country_id: int, conn: Session = None) -> dict | None:
    try:
        sql = text("SELECT * FROM Cities WHERE city_name = :name AND country_id = :country_id")
        result = conn.execute(sql, {"name": name, "country_id": country_id})
        row = result.fetchone()
        return _convert_to_dict(row) if row else None
    except Exception as e:
        logging.error(f"Error getting city by name '{name}' and country_id {country_id}: {e}", exc_info=True)
        return None

@_manage_conn
def get_city_by_id(id: int, conn: Session = None) -> dict | None:
    try:
        sql = text("SELECT * FROM Cities WHERE city_id = :id")
        result = conn.execute(sql, {"id": id})
        row = result.fetchone()
        return _convert_to_dict(row) if row else None
    except Exception as e:
        logging.error(f"Error getting city by id {id}: {e}", exc_info=True)
        return None

@_manage_conn
def add_city(data: dict, conn: Session = None) -> int | None:
    if not data.get('city_name') or not data.get('country_id'):
        logging.error("add_city requires 'city_name' and 'country_id'.")
        return None

    now = datetime.utcnow()
    sql = text("INSERT INTO Cities (city_name, country_id, created_at, updated_at) VALUES (:name, :country_id, :created, :updated)")
    params = {"name": data['city_name'], "country_id": data['country_id'], "created": now, "updated": now}
    try:
        result = conn.execute(sql, params)
        conn.commit()
        return result.lastrowid
    except Exception as e:
        logging.error(f"Database error in add_city for '{data['city_name']}': {e}", exc_info=True)
        conn.rollback()
        # Check for integrity error specifically if needed, but for now, just log and return None
        return None


def get_or_add_city(city_name: str, country_id: int, db: Session) -> City | None:
    if not city_name or not country_id:
        logging.warning("get_or_add_city: city_name and country_id are required.")
        return None

    logger_crud = logging.getLogger(__name__)
    logger_crud.info(f"locations_crud.get_or_add_city: Processing city: '{city_name}' for country_id: {country_id}")

    try:
        city = db.query(City).filter(City.city_name == city_name, City.country_id == country_id).first()
        if city:
            logger_crud.info(f"locations_crud.get_or_add_city: Found existing city '{city_name}' with data: {city}")
            return city

        else:
            logger_crud.info(f"locations_crud.get_or_add_city: City '{city_name}' not found, adding it now.")
            new_city = City(city_name=city_name, country_id=country_id)
            db.add(new_city)
            db.commit()
            db.refresh(new_city)
            logger_crud.info(f"locations_crud.get_or_add_city: Successfully added '{city_name}', new ID: {new_city.city_id}")
            return new_city
    except Exception as e:
        logger_crud.error(f"locations_crud.get_or_add_city: General error for '{city_name}': {e}", exc_info=True)
        db.rollback()
        return None

@_manage_conn
def get_all_cities(country_id: int = None, conn: Session = None) -> list[dict]:
    sql_str = "SELECT * FROM Cities"
    params = {}
    if country_id is not None:
        sql_str += " WHERE country_id = :country_id"
        params["country_id"] = country_id
    sql_str += " ORDER BY city_name"

    try:
        sql = text(sql_str)
        result = conn.execute(sql, params)
        return [_convert_to_dict(row) for row in result.fetchall()]
    except Exception as e:
        logging.error(f"Database error in get_all_cities (country_id={country_id}): {e}", exc_info=True)
        return []

__all__ = [
    "get_country_by_name",
    "get_country_by_id",
    "get_or_add_country",
    "add_country",
    "get_all_countries",
    "get_city_by_name_and_country_id",
    "get_city_by_id",
    "add_city",
    "get_or_add_city",
    "get_all_cities",
]
