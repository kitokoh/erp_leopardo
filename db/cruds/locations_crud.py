import sqlite3
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from db.models.locations import Country, City
from .generic_crud import _manage_conn # get_db_connection is not used directly

# --- Countries CRUD ---
@_manage_conn
def get_country_by_name(name: str, conn: sqlite3.Connection = None) -> dict | None:
    logger_crud = logging.getLogger(__name__) # Use specific logger for this CRUD
    cursor=conn.cursor()
    try:
        logger_crud.info(f"locations_crud.get_country_by_name: Querying for Name='{name}'")
        cursor.execute("SELECT * FROM Countries WHERE country_name = ?",(name,))
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
        cursor.execute("SELECT * FROM Countries WHERE country_id = ?",(id,))
        row=cursor.fetchone()
        # return dict(row) if row else None
        return {key: row[key] for key in row.keys()} if row else None
    except sqlite3.Error as e:
        logging.error(f"Error getting country by id {id}: {e}")
        return None

@_manage_conn
def get_or_add_country(country_name: str, conn: Session = None) -> dict | None:
    if not country_name:
        logging.warning("locations_crud.get_or_add_country: country_name is required.")
        return None

    logger_crud = logging.getLogger(__name__)
    logger_crud.info(f"locations_crud.get_or_add_country: Processing country: '{country_name}'")

    try:
        # Use SQLAlchemy session to query
        existing_country = conn.query(Country).filter(Country.country_name == country_name).first()

        if existing_country:
            logger_crud.info(f"Found existing country '{country_name}' with ID {existing_country.country_id}")
            return {
                "country_id": existing_country.country_id,
                "country_name": existing_country.country_name,
                "created_at": existing_country.created_at.isoformat() if existing_country.created_at else None,
                "updated_at": existing_country.updated_at.isoformat() if existing_country.updated_at else None,
            }
        else:
            logger_crud.info(f"Country '{country_name}' not found, creating new one.")
            now = datetime.utcnow()
            new_country = Country(
                country_name=country_name,
                created_at=now,
                updated_at=now
            )
            conn.add(new_country)
            conn.flush() # Use flush to get the ID before commit
            logger_crud.info(f"Successfully added '{country_name}', new ID: {new_country.country_id}")
            return {
                "country_id": new_country.country_id,
                "country_name": new_country.country_name,
                "created_at": new_country.created_at.isoformat(),
                "updated_at": new_country.updated_at.isoformat(),
            }
    except Exception as e:
        logger_crud.error(f"Database error in get_or_add_country for '{country_name}': {e}", exc_info=True)
        # The decorator will handle rollback
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
    sql = "INSERT INTO Countries (country_name, created_at, updated_at) VALUES (?, ?, ?)"
    params = (country_name, now, now)
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        return cursor.lastrowid
    except sqlite3.Error as e:
        logging.error(f"Database error in add_country for '{country_name}': {e}")
        return None

@_manage_conn
def get_all_countries(conn: sqlite3.Connection = None) -> list[dict]:
    """
    Retrieves all countries using a raw sqlite3 connection.
    """
    logger_crud = logging.getLogger(__name__)
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        logger_crud.info("locations_crud.get_all_countries: Querying for all countries.")
        cursor.execute("SELECT * FROM Countries ORDER BY country_name")
        rows = cursor.fetchall()
        countries = [{key: row[key] for key in row.keys()} for row in rows]
        logger_crud.info(f"locations_crud.get_all_countries: Found {len(countries)} countries.")
        return countries
    except sqlite3.Error as e:
        logger_crud.error(f"Database error in get_all_countries: {e}")
        # In case of an error, it's safer to return an empty list
        # as the caller expects a list.
        return []

# --- Cities CRUD ---
@_manage_conn
def get_city_by_name_and_country_id(name: str, country_id: int, conn: Session = None) -> dict | None:
    try:
        city = conn.query(City).filter(City.city_name == name, City.country_id == country_id).first()
        if city:
            return {
                "city_id": city.city_id, "city_name": city.city_name, "country_id": city.country_id,
                "created_at": city.created_at.isoformat() if city.created_at else None,
                "updated_at": city.updated_at.isoformat() if city.updated_at else None,
            }
        return None
    except Exception as e:
        logging.error(f"Error getting city by name '{name}' and country_id {country_id}: {e}", exc_info=True)
        return None

@_manage_conn
def get_city_by_id(id: int, conn: Session = None) -> dict | None:
    try:
        city = conn.query(City).filter(City.city_id == id).first()
        if city:
            return {
                "city_id": city.city_id, "city_name": city.city_name, "country_id": city.country_id,
                "created_at": city.created_at.isoformat() if city.created_at else None,
                "updated_at": city.updated_at.isoformat() if city.updated_at else None,
            }
        return None
    except Exception as e:
        logging.error(f"Error getting city by id {id}: {e}", exc_info=True)
        return None

@_manage_conn
def get_or_add_city(city_name: str, country_id: int, conn: Session = None) -> dict | None:
    if not city_name or not country_id:
        logging.warning("get_or_add_city: city_name and country_id are required.")
        return None

    logger_crud = logging.getLogger(__name__)
    logger_crud.info(f"Processing city: '{city_name}' for country_id: {country_id}")

    try:
        existing_city = conn.query(City).filter(City.city_name == city_name, City.country_id == country_id).first()

        if existing_city:
            logger_crud.info(f"Found existing city '{city_name}' with ID {existing_city.city_id}")
            return {"city_id": existing_city.city_id, "city_name": existing_city.city_name, "country_id": existing_city.country_id}
        else:
            logger_crud.info(f"City '{city_name}' not found, creating new one.")
            now = datetime.utcnow()
            new_city = City(
                city_name=city_name,
                country_id=country_id,
                created_at=now,
                updated_at=now
            )
            conn.add(new_city)
            conn.flush()
            logger_crud.info(f"Successfully added '{city_name}', new ID: {new_city.city_id}")
            return {"city_id": new_city.city_id, "city_name": new_city.city_name, "country_id": new_city.country_id}
    except Exception as e:
        logger_crud.error(f"Database error in get_or_add_city for '{city_name}': {e}", exc_info=True)
        return None

@_manage_conn
def get_all_cities(country_id: int = None, conn: Session = None) -> list[dict]:
    """
    Retrieves all cities, optionally filtered by country_id.
    """
    try:
        query = conn.query(City)
        if country_id is not None:
            query = query.filter(City.country_id == country_id)
        cities = query.order_by(City.city_name).all()
        return [
            {"city_id": c.city_id, "city_name": c.city_name, "country_id": c.country_id}
            for c in cities
        ]
    except Exception as e:
        logging.error(f"Database error in get_all_cities (country_id={country_id}): {e}", exc_info=True)
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
