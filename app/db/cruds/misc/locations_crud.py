import sqlite3
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.db.locations.country import Country
from app.models.db.locations.city import City
from ..generic_crud import _manage_conn

# --- Countries CRUD ---
@_manage_conn
def get_country_by_name(name: str, conn: sqlite3.Connection = None) -> dict | None:
    logger_crud = logging.getLogger(__name__) # Use specific logger for this CRUD
    cursor=conn.cursor()
    try:
        logger_crud.info(f"locations_crud.get_country_by_name: Querying for Name='{name}'")
        cursor.execute("SELECT * FROM countries WHERE country_name = ?",(name,))
        row=cursor.fetchone()
        if row:
            logger_crud.info(f"locations_crud.get_country_by_name: Found country '{name}' with data: {dict(row)}")
            return {key: row[key] for key in row.keys()}
        else:
            logger_crud.warning(f"locations_crud.get_country_by_name: Country '{name}' NOT found.")
            return None

    except sqlite3.Error as e:
        logging.error(f"Error getting country by name '{name}': {e}")
        return None

@_manage_conn
def get_country_by_id(id: int, conn: sqlite3.Connection = None) -> dict | None:
    cursor=conn.cursor()
    try:
        cursor.execute("SELECT * FROM countries WHERE country_id = ?",(id,))
        row=cursor.fetchone()
        # return dict(row) if row else None
        return {key: row[key] for key in row.keys()} if row else None
    except sqlite3.Error as e:
        logging.error(f"Error getting country by id {id}: {e}")
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
        logger_crud.error(f"locations_crud.get_or_add_country: General error for '{country_name}': {e}")
        db.rollback()
        return None

@_manage_conn
def add_country(data: dict, conn: sqlite3.Connection = None) -> int | None:
    """
    Adds a new country. Expects data['country_name'].
    This is a simplified version. Consider using get_or_add_country for more robust addition.
    """
    if 'country_name' not in data:
        logging.error("add_country: 'country_name' is required in data.")
        return None

    country_name = data['country_name']
    existing_country = get_country_by_name(country_name, conn=conn) # Use passed connection
    if existing_country:
        return existing_country['country_id']

    now = datetime.utcnow().isoformat() + "Z"
    sql = "INSERT INTO countries (country_name, created_at, updated_at) VALUES (?, ?, ?)"
    params = (country_name, now, now)
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        return cursor.lastrowid
    except sqlite3.Error as e:
        logging.error(f"Database error in add_country for '{country_name}': {e}")
        return None

@_manage_conn
def get_all_countries(conn: Session = None) -> list[dict]:
    """
    Retrieves all countries.
    """
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
        logging.error(f"Database error in get_all_countries: {e}")
        return []

# --- Cities CRUD ---
@_manage_conn
def get_city_by_name_and_country_id(name: str, country_id: int, conn: sqlite3.Connection = None) -> dict | None:
    cursor=conn.cursor()
    try:
        cursor.execute("SELECT * FROM cities WHERE city_name = ? AND country_id = ?",(name,country_id))
        row=cursor.fetchone()
        # return dict(row) if row else None
        return {key: row[key] for key in row.keys()} if row else None
    except sqlite3.Error as e:
        logging.error(f"Error getting city by name '{name}' and country_id {country_id}: {e}")
        return None

@_manage_conn
def get_city_by_id(id: int, conn: sqlite3.Connection = None) -> dict | None:
    cursor=conn.cursor()
    try:
        cursor.execute("SELECT * FROM cities WHERE city_id = ?",(id,))
        row=cursor.fetchone()
        # return dict(row) if row else None
        return {key: row[key] for key in row.keys()} if row else None
    except sqlite3.Error as e:
        logging.error(f"Error getting city by id {id}: {e}")
        return None

@_manage_conn
def add_city(data: dict, conn: sqlite3.Connection = None) -> int | None:
    """
    Adds a new city to the Cities table.
    Expects data['city_name'] and data['country_id'].
    """
    if not data.get('city_name') or not data.get('country_id'):
        logging.error("add_city requires 'city_name' and 'country_id'.")
        return None

    # Simplified: direct insert without all fields from original schema example
    now = datetime.utcnow().isoformat() + "Z"
    sql = "INSERT INTO cities (city_name, country_id, created_at, updated_at) VALUES (?, ?, ?, ?)"
    params = (data['city_name'], data['country_id'], now, now)
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        logging.warning(f"City '{data['city_name']}' likely already exists for country_id {data['country_id']}.")
        existing_city = get_city_by_name_and_country_id(data['city_name'], data['country_id'], conn=conn)
        return existing_city['city_id'] if existing_city else None
    except sqlite3.Error as e:
        logging.error(f"Database error in add_city for '{data['city_name']}': {e}")
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
        logger_crud.error(f"locations_crud.get_or_add_city: General error for '{city_name}': {e}")
        db.rollback()
        return None

@_manage_conn
def get_all_cities(country_id: int = None, conn: sqlite3.Connection = None) -> list[dict]:
    """
    Retrieves all cities, optionally filtered by country_id.
    """
    cursor = conn.cursor()
    sql = "SELECT * FROM cities"
    params = []
    if country_id is not None:
        sql += " WHERE country_id = ?"
        params.append(country_id)
    sql += " ORDER BY city_name" # Or country_id, city_name
    try:
        cursor.execute(sql, params)
        # return [dict(row) for row in cursor.fetchall()]
        return [{key: item[key] for key in item.keys()} for item in cursor.fetchall()]
    except sqlite3.Error as e:
        logging.error(f"Database error in get_all_cities (country_id={country_id}): {e}")
        return []

__all__ = [
    "get_country_by_name",
    "get_country_by_id",
    "get_or_add_country",
    "add_country", # Keep for compatibility if used elsewhere, though get_or_add is preferred
    "get_all_countries",
    "get_city_by_name_and_country_id",
    "get_city_by_id",
    "add_city", # Keep for compatibility
    "get_or_add_city",
    "get_all_cities",
]
