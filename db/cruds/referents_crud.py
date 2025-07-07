import sqlite3
import uuid
from datetime import datetime
import logging
from .generic_crud import GenericCRUD, _manage_conn

logger = logging.getLogger(__name__)

class ReferentsCRUD(GenericCRUD):
    """
    Manages CRUD operations for Referents.
    A Referent is a Client who acts as a reference, possibly classified by location.
    """
    def __init__(self):
        """Initializes the ReferentsCRUD class."""
        super().__init__(table_name="Referents", primary_key="referent_id")

    @_manage_conn
    def add_referent(self, client_id: str, country_id: int, region_id: int | None,
                     city_id: int | None, notes: str | None, created_by_user_id: str,
                     conn: sqlite3.Connection = None) -> str | None:
        """
        Adds a new referent to the database. A client can only be a referent once.

        Args:
            client_id (str): The ID of the client becoming a referent.
            country_id (int): The ID of the country for this referent's classification.
            region_id (int | None): The ID of the region (optional).
            city_id (int | None): The ID of the city (optional).
            notes (str | None): Specific notes about this referent role.
            created_by_user_id (str): The ID of the user creating this referent entry.
            conn (sqlite3.Connection, optional): Database connection. Managed by decorator.

        Returns:
            str | None: The UUID of the newly added referent, or None on failure
                        (e.g., if client is already a referent).
        """
        if not all([client_id, country_id, created_by_user_id]):
            logger.error("Client ID, Country ID, and Created By User ID are required to add a referent.")
            return None

        new_referent_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + "Z"

        sql = """
            INSERT INTO Referents (referent_id, client_id, country_id, region_id, city_id,
                                   notes, created_by_user_id, referent_since, created_at, updated_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (new_referent_id, client_id, country_id, region_id, city_id,
                  notes, created_by_user_id, now, now, now, True)

        try:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            logger.info(f"Referent added for client_id '{client_id}' with referent_id: {new_referent_id}.")
            return new_referent_id
        except sqlite3.IntegrityError as e:
            logger.error(f"Failed to add referent for client_id '{client_id}' due to integrity error (client may already be a referent, or FK violation): {e}", exc_info=True)
            return None
        except sqlite3.Error as e:
            logger.error(f"SQLite error adding referent for client_id '{client_id}': {e}", exc_info=True)
            return None

    @_manage_conn
    def get_referent_by_id(self, referent_id: str, conn: sqlite3.Connection = None) -> dict | None:
        """
        Fetches a referent by their referent_id.

        Args:
            referent_id (str): The UUID of the referent to fetch.
            conn (sqlite3.Connection, optional): Database connection.

        Returns:
            dict | None: A dictionary representing the referent if found, otherwise None.
        """
        return self._get_by_id(referent_id, conn)

    @_manage_conn
    def get_referent_by_client_id(self, client_id: str, conn: sqlite3.Connection = None, include_inactive: bool = False) -> dict | None:
        """
        Fetches a referent by their associated client_id.

        Args:
            client_id (str): The UUID of the client.
            conn (sqlite3.Connection, optional): Database connection.
            include_inactive (bool, optional): If True, includes referents even if they are inactive.
                                               Defaults to False.

        Returns:
            dict | None: A dictionary representing the referent if found, otherwise None.
        """
        query = "SELECT * FROM Referents WHERE client_id = ?"
        params = [client_id]
        if not include_inactive:
            query += " AND is_active = TRUE"

        try:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error fetching referent by client_id '{client_id}': {e}", exc_info=True)
            return None

    @_manage_conn
    def get_all_referents(self, filters: dict = None, limit: int = None, offset: int = 0,
                          include_inactive: bool = False, conn: sqlite3.Connection = None) -> list[dict]:
        """
        Retrieves all referents, with optional filtering and pagination.
        Joins with Clients, Countries, Regions, Cities for more detailed output.

        Args:
            filters (dict, optional): A dictionary of filters.
                                      Supported keys: 'country_id', 'region_id', 'city_id', 'client_name'.
            limit (int, optional): Maximum number of records to return.
            offset (int, optional): Number of records to skip for pagination.
            include_inactive (bool, optional): If True, includes inactive referents. Defaults to False.
            conn (sqlite3.Connection, optional): Database connection.

        Returns:
            list[dict]: A list of dictionaries, each representing a referent with joined details.
        """
        cursor = conn.cursor()

        sql = """
            SELECT
                r.*,
                cl.client_name, cl.company_name,
                co.country_name,
                rg.region_name,
                ci.city_name
            FROM Referents r
            JOIN Clients cl ON r.client_id = cl.client_id
            JOIN Countries co ON r.country_id = co.country_id
            LEFT JOIN Regions rg ON r.region_id = rg.region_id
            LEFT JOIN Cities ci ON r.city_id = ci.city_id
        """

        q_params = []
        conditions = []

        if not include_inactive:
            conditions.append("r.is_active = TRUE")

        if filters:
            if 'country_id' in filters and filters['country_id'] is not None:
                conditions.append("r.country_id = ?")
                q_params.append(filters['country_id'])
            if 'region_id' in filters and filters['region_id'] is not None:
                conditions.append("r.region_id = ?")
                q_params.append(filters['region_id'])
            if 'city_id' in filters and filters['city_id'] is not None:
                conditions.append("r.city_id = ?")
                q_params.append(filters['city_id'])
            if 'client_name' in filters and filters['client_name']:
                conditions.append("cl.client_name LIKE ?")
                q_params.append(f"%{filters['client_name']}%")

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        sql += " ORDER BY cl.client_name"

        if limit is not None:
            sql += " LIMIT ? OFFSET ?"
            q_params.extend([limit, offset])

        try:
            cursor.execute(sql, tuple(q_params))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Failed to get all referents with details, filters '{filters}': {e}", exc_info=True)
            return []

    @_manage_conn
    def update_referent(self, referent_id: str, data: dict, conn: sqlite3.Connection = None) -> bool:
        """
        Updates a referent's information.
        Allowed fields: 'country_id', 'region_id', 'city_id', 'notes', 'is_active'.
        The 'updated_at' field is automatically set.

        Args:
            referent_id (str): The UUID of the referent to update.
            data (dict): A dictionary containing the data to update.
            conn (sqlite3.Connection, optional): Database connection.

        Returns:
            bool: True if the update was successful (at least one row affected), False otherwise.
        """
        if not referent_id:
            logger.error("Referent ID is required for update.")
            return False
        if not data:
            logger.warning("No data provided for referent update.")
            return False

        allowed_fields = {'country_id', 'region_id', 'city_id', 'notes', 'is_active'}
        update_fields = {k: v for k, v in data.items() if k in allowed_fields}

        if not update_fields:
            logger.warning("No valid fields to update for referent.")
            return False # Or True if no change is considered a success

        update_fields['updated_at'] = datetime.utcnow().isoformat() + "Z"

        return self.update(item_id=referent_id, data=update_fields, conn=conn) # Uses self.table_name and self.primary_key by default

    @_manage_conn
    def set_referent_active_status(self, referent_id: str, is_active: bool, conn: sqlite3.Connection = None) -> bool:
        """
        Sets the active status of a referent.

        Args:
            referent_id (str): The UUID of the referent.
            is_active (bool): The new active status.
            conn (sqlite3.Connection, optional): Database connection.

        Returns:
            bool: True if the status was updated successfully, False otherwise.
        """
        return self.update_referent(referent_id, {'is_active': is_active}, conn=conn)

    @_manage_conn
    def delete_referent(self, referent_id: str, conn: sqlite3.Connection = None) -> bool:
        """
        Deletes a referent by their referent_id. This is a hard delete.

        Args:
            referent_id (str): The UUID of the referent to delete.
            conn (sqlite3.Connection, optional): Database connection.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        return self._delete(referent_id, conn=conn)

referents_crud_instance = ReferentsCRUD()

add_referent = referents_crud_instance.add_referent
get_referent_by_id = referents_crud_instance.get_referent_by_id
get_referent_by_client_id = referents_crud_instance.get_referent_by_client_id
get_all_referents = referents_crud_instance.get_all_referents
update_referent = referents_crud_instance.update_referent
set_referent_active_status = referents_crud_instance.set_referent_active_status
delete_referent = referents_crud_instance.delete_referent

__all__ = [
    "ReferentsCRUD", "referents_crud_instance",
    "add_referent", "get_referent_by_id", "get_referent_by_client_id",
    "get_all_referents", "update_referent", "set_referent_active_status", "delete_referent"
]
