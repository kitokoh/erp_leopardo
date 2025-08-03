import sqlite3
import uuid
from datetime import datetime
import logging
from ..generic_crud import GenericCRUD, _manage_conn

logger = logging.getLogger(__name__)

class RegionsCRUD(GenericCRUD):
    """
    Manages CRUD operations for Regions.
    Regions are geographical areas within a Country.
    """
    def __init__(self):
        """Initializes the RegionsCRUD class."""
        super().__init__(table_name="Regions", primary_key="region_id")

    @_manage_conn
    def add_region(self, region_name: str, country_id: int, conn: sqlite3.Connection = None) -> int | None:
        """
        Adds a new region to the database.

        Args:
            region_name (str): The name of the region.
            country_id (int): The ID of the country this region belongs to.
            conn (sqlite3.Connection, optional): Database connection. Managed by decorator.

        Returns:
            int | None: The ID of the newly added region, or None on failure.
                        If the region already exists (name and country_id match),
                        returns the ID of the existing region.
        """
        if not region_name or country_id is None:
            logger.error("Region name and country_id are required.")
            return None

        now = datetime.utcnow().isoformat() + "Z"
        sql = """
            INSERT INTO Regions (region_name, country_id, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """
        params = (region_name, country_id, now, now)
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            last_id = cursor.lastrowid
            logger.info(f"Region '{region_name}' added with ID: {last_id} for country_id {country_id}.")
            return last_id
        except sqlite3.IntegrityError as e:
            logger.warning(f"Failed to add region '{region_name}' for country_id {country_id} due to integrity error (likely duplicate): {e}")
            existing_region = self.get_region_by_name_and_country_id(region_name, country_id, conn=conn)
            if existing_region:
                logger.info(f"Region '{region_name}' already existed with ID {existing_region['region_id']}.")
                return existing_region['region_id']
            return None
        except sqlite3.Error as e:
            logger.error(f"SQLite error adding region '{region_name}' for country_id {country_id}: {e}", exc_info=True)
            return None

    @_manage_conn
    def get_region_by_id(self, region_id: int, conn: sqlite3.Connection = None) -> dict | None:
        """
        Fetches a region by its ID.

        Args:
            region_id (int): The ID of the region to fetch.
            conn (sqlite3.Connection, optional): Database connection.

        Returns:
            dict | None: A dictionary representing the region if found, otherwise None.
        """
        return self._get_by_id(region_id, conn)

    @_manage_conn
    def get_region_by_name_and_country_id(self, region_name: str, country_id: int, conn: sqlite3.Connection = None) -> dict | None:
        """
        Fetches a region by its name and country_id.

        Args:
            region_name (str): The name of the region.
            country_id (int): The ID of the country.
            conn (sqlite3.Connection, optional): Database connection.

        Returns:
            dict | None: A dictionary representing the region if found, otherwise None.
        """
        sql = "SELECT * FROM Regions WHERE region_name = ? AND country_id = ?"
        try:
            cursor = conn.cursor()
            cursor.execute(sql, (region_name, country_id))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error fetching region by name '{region_name}' and country_id {country_id}: {e}", exc_info=True)
            return None

    @_manage_conn
    def get_regions_for_country(self, country_id: int, conn: sqlite3.Connection = None) -> list[dict]:
        """
        Fetches all regions for a given country_id.

        Args:
            country_id (int): The ID of the country.
            conn (sqlite3.Connection, optional): Database connection.

        Returns:
            list[dict]: A list of dictionaries, where each dictionary is a region record.
        """
        sql = "SELECT * FROM Regions WHERE country_id = ? ORDER BY region_name"
        try:
            cursor = conn.cursor()
            cursor.execute(sql, (country_id,))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error fetching regions for country_id {country_id}: {e}", exc_info=True)
            return []

    @_manage_conn
    def get_all_regions(self, conn: sqlite3.Connection = None) -> list[dict]:
        """
        Fetches all regions from the database, ordered by country_id then region_name.

        Args:
            conn (sqlite3.Connection, optional): Database connection.

        Returns:
            list[dict]: A list of all region records.
        """
        return self._get_all(conn=conn, order_by="country_id, region_name")

    @_manage_conn
    def update_region(self, region_id: int, data: dict, conn: sqlite3.Connection = None) -> bool:
        """
        Updates a region's information. Allowed fields: 'region_name', 'country_id'.
        The 'updated_at' field is automatically set.

        Args:
            region_id (int): The ID of the region to update.
            data (dict): A dictionary containing the data to update.
            conn (sqlite3.Connection, optional): Database connection.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        if not region_id:
            logger.error("Region ID is required for update.")
            return False
        if not data:
            logger.warning("No data provided for region update.")
            return False

        allowed_fields = {'region_name', 'country_id'}
        update_fields = {k: v for k, v in data.items() if k in allowed_fields}

        if not update_fields:
            logger.warning("No valid fields to update for region.")
            return False

        update_fields['updated_at'] = datetime.utcnow().isoformat() + "Z"

        return self._update(region_id, update_fields, conn=conn)

    @_manage_conn
    def delete_region(self, region_id: int, conn: sqlite3.Connection = None) -> bool:
        """
        Deletes a region by its ID.
        Note: This is a hard delete. Consider implications if regions are linked elsewhere (e.g., Referents).
        The Referents table uses ON DELETE SET NULL for region_id, so this should be safe.

        Args:
            region_id (int): The ID of the region to delete.
            conn (sqlite3.Connection, optional): Database connection.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        return self._delete(region_id, conn=conn)

    @_manage_conn
    def get_or_add_region(self, region_name: str, country_id: int, conn: sqlite3.Connection = None) -> dict | None:
        """
        Gets an existing region by name and country_id, or adds it if it doesn't exist.

        Args:
            region_name (str): The name of the region.
            country_id (int): The ID of the country this region belongs to.
            conn (sqlite3.Connection, optional): Database connection.

        Returns:
            dict | None: A dictionary representing the region, or None on failure.
        """
        if not region_name or country_id is None:
            logger.error("Region name and country_id are required for get_or_add_region.")
            return None

        existing_region = self.get_region_by_name_and_country_id(region_name, country_id, conn=conn)
        if existing_region:
            return existing_region

        new_region_id = self.add_region(region_name, country_id, conn=conn)
        if new_region_id:
            return self.get_region_by_id(new_region_id, conn=conn)
        return None

regions_crud_instance = RegionsCRUD()

get_all_regions = regions_crud_instance.get_all_regions
get_region_by_id = regions_crud_instance.get_region_by_id
add_region = regions_crud_instance.add_region
update_region = regions_crud_instance.update_region
delete_region = regions_crud_instance.delete_region
get_regions_for_country = regions_crud_instance.get_regions_for_country
get_region_by_name_and_country_id = regions_crud_instance.get_region_by_name_and_country_id
get_or_add_region = regions_crud_instance.get_or_add_region

__all__ = [
    "RegionsCRUD", "regions_crud_instance",
    "get_all_regions", "get_region_by_id", "add_region", "update_region", "delete_region",
    "get_regions_for_country", "get_region_by_name_and_country_id", "get_or_add_region"
]
