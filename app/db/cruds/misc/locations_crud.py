import logging
from sqlalchemy.orm import Session
from app.models.db.locations.country import Country
from app.models.db.locations.city import City

logger = logging.getLogger(__name__)

def get_country_by_name(name: str, db: Session) -> Country | None:
    """
    Retrieves a country by its name using the ORM.
    """
    try:
        return db.query(Country).filter(Country.country_name == name).first()
    except Exception as e:
        logger.error(f"Error getting country by name '{name}': {e}", exc_info=True)
        return None

def get_country_by_id(id: int, db: Session) -> Country | None:
    """
    Retrieves a country by its ID using the ORM.
    """
    try:
        return db.query(Country).filter(Country.country_id == id).first()
    except Exception as e:
        logger.error(f"Error getting country by id {id}: {e}", exc_info=True)
        return None

def get_or_add_country(country_name: str, db: Session) -> Country | None:
    if not country_name:
        return None
    country = get_country_by_name(country_name, db)
    if country:
        return country

    new_country = Country(country_name=country_name)
    db.add(new_country)
    try:
        db.commit()
        db.refresh(new_country)
        return new_country
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to add new country '{country_name}': {e}", exc_info=True)
        return None

def get_all_countries(db: Session) -> list[Country]:
    """
    Retrieves all countries using the ORM.
    """
    try:
        return db.query(Country).order_by(Country.country_name).all()
    except Exception as e:
        logger.error(f"Database error in get_all_countries: {e}", exc_info=True)
        return []

def get_city_by_name_and_country_id(name: str, country_id: int, db: Session) -> City | None:
    """
    Retrieves a city by its name and country ID using the ORM.
    """
    try:
        return db.query(City).filter(City.city_name == name, City.country_id == country_id).first()
    except Exception as e:
        logger.error(f"Error getting city by name '{name}' and country_id {country_id}: {e}", exc_info=True)
        return None

def get_city_by_id(id: int, db: Session) -> City | None:
    """
    Retrieves a city by its ID using the ORM.
    """
    try:
        return db.query(City).filter(City.city_id == id).first()
    except Exception as e:
        logger.error(f"Error getting city by id {id}: {e}", exc_info=True)
        return None

def get_or_add_city(city_name: str, country_id: int, db: Session) -> City | None:
    if not city_name or not country_id:
        return None
    city = get_city_by_name_and_country_id(city_name, country_id, db)
    if city:
        return city

    new_city = City(city_name=city_name, country_id=country_id)
    db.add(new_city)
    try:
        db.commit()
        db.refresh(new_city)
        return new_city
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to add new city '{city_name}': {e}", exc_info=True)
        return None

def get_all_cities(db: Session, country_id: int = None) -> list[City]:
    """
    Retrieves all cities, optionally filtered by country_id, using the ORM.
    """
    try:
        query = db.query(City)
        if country_id is not None:
            query = query.filter(City.country_id == country_id)
        return query.order_by(City.city_name).all()
    except Exception as e:
        logger.error(f"Database error in get_all_cities (country_id={country_id}): {e}", exc_info=True)
        return []

__all__ = [
    "get_country_by_name", "get_country_by_id", "get_or_add_country", "get_all_countries",
    "get_city_by_name_and_country_id", "get_city_by_id", "get_or_add_city", "get_all_cities",
]
