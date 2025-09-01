import sqlite3 # Keep for type hints if necessary
import uuid
from datetime import datetime
import logging
from sqlalchemy.sql import text
from sqlalchemy.orm import Session # For type hinting Session
from ..generic_crud import GenericCRUD, _manage_conn, _is_sqlalchemy_obj

from app.models.db.clients.client import Client
from app.models.db.orders.commande import Commande
from app.models.db.projects.project import Project
from app.models.db.settings.status_setting import StatusSetting
from app.models.db.misc.templates import Template
from app.models.db.locations.country import Country
from app.models.db.locations.city import City

# --- Clients CRUD ---
class ClientsCRUD(GenericCRUD):
    """
    Manages CRUD operations for clients, including handling soft deletes,
    client notes, and various client segmentation/reporting queries.
    Inherits from GenericCRUD for basic operations.
    """
    def __init__(self):
        """
        Initializes the ClientsCRUD class, setting the table name and ID column
        for use with GenericCRUD methods.
        """
        self.table_name = "Clients"
        self.id_column = "client_id"
        self.logger = logging.getLogger(__name__) # Add logger instance

    def add_client(self, data: dict, conn: Session) -> dict:
        """
        Adds a new client to the database using the ORM.
        """
        # Circular import guard
        from app.status_manager import status_service, status_models

        self.logger.info(f"Attempting to add client with data: {data}")

        required_fields = ['client_name', 'created_by_user_id']
        for field in required_fields:
            if not data.get(field):
                self.logger.error(f"Missing required field: {field}")
                return {'success': False, 'error': f"Missing required field: {field}"}

        new_id = str(uuid.uuid4())
        folder_path = self.create_client_folder(new_id, data.get('client_name'))

        new_client = Client(
            client_id=new_id,
            client_name=data.get('client_name'),
            company_name=data.get('company_name'),
            primary_need_description=data.get('primary_need_description'),
            project_identifier=data.get('project_identifier', 'N/A'),
            country_id=data.get('country_id'),
            city_id=data.get('city_id'),
            default_base_folder_path=folder_path,
            status_id=data.get('status_id'),
            selected_languages=data.get('selected_languages'),
            price=data.get('price', 0),
            notes=data.get('notes'),
            category=data.get('category'),
            lead_source=data.get('lead_source'),
            created_by_user_id=data.get('created_by_user_id'),
            default_template_id=data.get('default_template_id')
        )
        conn.add(new_client)

        # Create default order and project
        default_order_status = status_service.get_default_status_for_commande_creation()
        default_project_status = status_service.get_default_status_for_type(status_models.StatusType.PROJECT, preferred_name="Planning")

        if default_order_status and default_project_status:
            new_commande = Commande(
                commande_id=str(uuid.uuid4()),
                client_id=new_id,
                commande_reference=f"DEF-ORD-{new_id[:8]}",
                status_commande_id=default_order_status.status_id,
                created_by_user_id=data.get('created_by_user_id'),
                notes=f"Default order automatically created for {data.get('client_name')}.",
                is_default=True,
                description_commande="Default Order"
            )
            conn.add(new_commande)

            new_project = Project(
                project_id=str(uuid.uuid4()),
                client_id=new_id,
                project_name=f"Default Project for {data.get('client_name')}",
                status_id=default_project_status.status_id,
                description=f"Default project automatically created for order {new_commande.commande_reference}.",
                manager_team_member_id=data.get('created_by_user_id')
            )
            conn.add(new_project)
            # The relationship should handle this, but explicit assignment is safe
            new_commande.project_id = new_project.project_id
        else:
            self.logger.warning("Could not find default statuses for Order or Project. Client will be created without them.")

        try:
            conn.commit()
            conn.refresh(new_client)
            self.logger.info(f"Successfully added client {new_client.client_id}")
            return {'success': True, 'client_id': new_client.client_id}
        except Exception as e:
            self.logger.error(f"Transaction failed during client creation: {e}", exc_info=True)
            conn.rollback()
            return {'success': False, 'error': f"Database transaction failed: {e}"}

    def create_client_folder(self, client_id: str, client_name: str) -> str | None:
        """
        Creates a folder for the client if it doesn't exist.
        """
        try:
            import os
            from app_setup import APP_ROOT_DIR
            sane_client_name = "".join(c if c.isalnum() else "_" for c in client_name)
            folder_name = f"{sane_client_name}_{client_id[:8]}"
            relative_folder_path = os.path.join("clients", folder_name)
            absolute_folder_path = os.path.join(APP_ROOT_DIR, relative_folder_path)
            os.makedirs(absolute_folder_path, exist_ok=True)
            return relative_folder_path
        except Exception as e:
            self.logger.error(f"Failed to create folder for client {client_id}: {e}", exc_info=True)
            return None

    def get_client_by_id(self, client_id: str, conn: Session, include_deleted: bool = False) -> Client | None:
        """
        Fetches a single client by their client_id using the ORM.

        Args:
            client_id (str): The UUID of the client to fetch.
            conn (Session): SQLAlchemy Session.
            include_deleted (bool, optional): If True, includes soft-deleted clients.
                                              Defaults to False.

        Returns:
            Client | None: The SQLAlchemy Client object if found, otherwise None.
        """
        try:
            query = conn.query(Client).filter(Client.client_id == client_id)
            if not include_deleted:
                # Assuming is_deleted is a boolean or 0/1
                query = query.filter(Client.is_deleted == False)

            client = query.first()
            return client
        except Exception as e:
            self.logger.error(f"Error getting client by ID {client_id}: {e}", exc_info=True)
            return None

    def get_client_by_project_identifier(self, project_identifier: str, conn: Session, include_deleted: bool = False) -> Client | None:
        """
        Fetches a single client by their project_identifier using the ORM.
        """
        try:
            query = conn.query(Client).filter(Client.project_identifier == project_identifier)
            if not include_deleted:
                query = query.filter(Client.is_deleted == False)

            client = query.first()
            return client
        except Exception as e:
            self.logger.error(f"Error getting client by project_identifier {project_identifier}: {e}", exc_info=True)
            return None

    def get_all_clients(self, filters: dict, conn: Session, limit: int = None, offset: int = 0, include_deleted: bool = False) -> list[dict]:
        """
        Retrieves all clients, with optional filtering, pagination, and inclusion of
        soft-deleted records.

        Args:
            filters (dict, optional): A dictionary of filters to apply (e.g., {'category': 'Tech'}).
                                      Valid filter keys: 'client_name', 'company_name', 'country_id',
                                      'city_id', 'status_id', 'category', 'created_by_user_id'.
            conn (sqlite3.Connection, optional): Database connection.
            limit (int, optional): Maximum number of records to return for pagination.
            offset (int, optional): Number of records to skip for pagination. Defaults to 0.
            include_deleted (bool, optional): If True, includes soft-deleted clients.
                                              Defaults to False.

        Returns:
            list[dict]: A list of dictionaries, where each dictionary is a client record.
        """
        sql_base = f"SELECT * FROM {self.table_name}"
        params_dict = {}
        conditions = []

        if not include_deleted:
            conditions.append("(is_deleted IS NULL OR is_deleted = 0)")

        if filters:
            valid_filters = ['client_name', 'company_name', 'country_id', 'city_id', 'status_id', 'category', 'created_by_user_id']
            for k, v in filters.items():
                if k in valid_filters:
                    param_name = f"filter_{k}"
                    if isinstance(v, str) and k in ['client_name', 'company_name', 'category']:
                        conditions.append(f"{k} LIKE :{param_name}")
                        params_dict[param_name] = f"%{v}%"
                    else:
                        conditions.append(f"{k} = :{param_name}")
                        params_dict[param_name] = v

        if conditions:
            sql_base += " WHERE " + " AND ".join(conditions)

        sql_base += " ORDER BY client_name" # Default ordering

        if limit is not None:
            sql_base += " LIMIT :limit OFFSET :offset"
            params_dict["limit"] = limit
            params_dict["offset"] = offset

        sql_query = text(sql_base)
        try:
            if _is_sqlalchemy_obj(conn):
                result = conn.execute(sql_query, params_dict)
            else:
                result = conn.execute(str(sql_query), params_dict)

            return [dict(row._mapping) if hasattr(row, '_mapping') else dict(row) for row in result.fetchall()]
        except Exception as e: # Changed to general Exception
            self.logger.error(f"Failed to get all clients with filters '{filters}': {e}", exc_info=True)
            return []

    def update_client(self, client_id: str, client_data: dict, conn: Session) -> dict:
        """
        Updates an existing client's information using the ORM.
        """
        if not client_id:
            return {'success': False, 'error': "Client ID is required for update."}
        if not client_data:
            return {'success': False, 'error': "No data provided for update."}

        try:
            client = conn.query(Client).filter(Client.client_id == client_id).first()
            if not client:
                return {'success': True, 'updated_count': 0}

            for key, value in client_data.items():
                if hasattr(client, key):
                    setattr(client, key, value)

            conn.commit()
            return {'success': True, 'updated_count': 1}
        except Exception as e:
            self.logger.error(f"Failed to update client {client_id}: {e}", exc_info=True)
            conn.rollback()
            return {'success': False, 'error': str(e)}

    def delete_client(self, client_id: str, conn: Session) -> dict:
        """
        Soft deletes a client by setting `is_deleted = True`, `deleted_at` to the current UTC timestamp,
        and updating the client's status to 'Archivé'. Uses the ORM.

        Args:
            conn (Session): SQLAlchemy Session.
            client_id (str): The UUID of the client to soft delete.

        Returns:
            dict: {'success': True, 'message': '...'} on success,
                  {'success': False, 'error': '...'} on failure.
        """
        # Circular import guard
        from status_manager import status_service

        if not client_id:
            self.logger.warning("delete_client called with no client_id.")
            return {'success': False, 'error': "Client ID is required for deletion."}

        try:
            client_to_delete = conn.query(Client).filter(Client.client_id == client_id, Client.is_deleted == False).first()

            if not client_to_delete:
                self.logger.warning(f"Client {client_id} not found or already deleted.")
                return {'success': False, 'error': f"Client {client_id} not found or already deleted."}

            client_to_delete.is_deleted = True
            client_to_delete.deleted_at = datetime.utcnow()

            message = f"Client {client_id} soft deleted."
            archived_status = status_service.get_archived_status_for_client(conn)

            if archived_status:
                client_to_delete.status_id = archived_status.status_id
                message += " Status updated to 'Archivé'."
            else:
                self.logger.error(f"Could not find 'Archivé' status for Client type. Status will not be updated during soft delete.")
                message += " Status NOT updated to 'Archivé' due to missing status configuration."

            conn.commit()
            self.logger.info(message)
            return {'success': True, 'message': message}
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Failed to soft delete client {client_id}: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def get_all_clients_with_details(self, filters: dict, conn: Session, limit: int = None, offset: int = 0, include_deleted: bool = False) -> list[dict]:
        """
        Retrieves all clients along with details from joined tables (Countries, Cities, StatusSettings).
        Supports pagination and filtering of soft-deleted records.

        Args:
            filters (dict, optional): A dictionary of filters to apply.
            conn (sqlite3.Connection, optional): Database connection.
            limit (int, optional): Maximum number of records for pagination.
            offset (int, optional): Offset for pagination.
            include_deleted (bool, optional): If True, includes soft-deleted clients. Defaults to False.

        Returns:
            list[dict]: A list of client records with joined details.
        """
        logging.info(f"get_all_clients_with_details called with filters: {filters}, include_deleted: {include_deleted}")
        params_dict = {} # For named parameters

        # Sorting parameters
        order_by_field = filters.pop('order_by_field', 'client_name') if filters else 'client_name'
        order_direction = filters.pop('order_direction', 'ASC').upper() if filters else 'ASC'
        if order_direction not in ['ASC', 'DESC']:
            order_direction = 'ASC'

        valid_sort_fields = {
            "client_name": "c.client_name", "created_at": "c.created_at",
            "country_name": "co.country_name", "project_identifier": "c.project_identifier",
            "status_name": "s.status_name"
        }

        sql_order_by_column = valid_sort_fields.get(order_by_field, "c.client_name")
        if order_by_field not in valid_sort_fields:
             self.logger.warning(f"Invalid order_by_field '{order_by_field}' requested. Defaulting to 'c.client_name'.")

        query_str = """
        SELECT c.client_id, c.client_name, c.company_name, c.primary_need_description,
               c.project_identifier, c.default_base_folder_path, c.selected_languages,
               c.price, c.notes, c.created_at, c.category, c.status_id, c.country_id, c.city_id,
               c.is_deleted, c.deleted_at, c.default_template_id,
               co.country_name AS country, ci.city_name AS city,
               s.status_name AS status, s.color_hex AS status_color, s.icon_name AS status_icon_name,
               t.template_name AS default_template_name
        FROM Clients c
        LEFT JOIN Countries co ON c.country_id = co.country_id
        LEFT JOIN Cities ci ON c.city_id = ci.city_id
        LEFT JOIN StatusSettings s ON c.status_id = s.status_id AND s.status_type = 'Client'
        LEFT JOIN Templates t ON c.default_template_id = t.template_id
        """

        conditions = []
        if not include_deleted:
            conditions.append("(c.is_deleted IS NULL OR c.is_deleted = 0)")

        if filters:
            # Handle multiple status IDs
            if 'status_ids' in filters and isinstance(filters['status_ids'], list) and filters['status_ids']:
                # For IN clauses with SQLAlchemy, it's often easier to let SQLAlchemy handle list expansion
                # or bind parameters one by one if not using ORM level constructs.
                # For text(), creating :status_id_0, :status_id_1 etc. is one way, or using a list expansion feature if driver supports.
                # Simpler for now: use multiple OR conditions if list is small, or rely on specific db driver features.
                # For this refactor, let's assume 'status_id' will be a single value or None for simplicity of text()
                # Or, if status_ids is a list, we might need to format the IN clause carefully (and safely).
                # Let's revert to single status_id for now for easier text() refactor.
                # Proper IN clause handling:
                status_id_conditions = []
                for i, status_id_val in enumerate(filters['status_ids']):
                    param_name = f"status_id_{i}"
                    status_id_conditions.append(f"c.status_id = :{param_name}")
                    params_dict[param_name] = status_id_val
                if status_id_conditions:
                    conditions.append(f"({ ' OR '.join(status_id_conditions) })")

            elif 'status_id' in filters and filters['status_id'] is not None: # Fallback for single status_id
                conditions.append("c.status_id = :status_id")
                params_dict["status_id"] = filters['status_id']

            if 'client_name' in filters and filters['client_name']:
                conditions.append("c.client_name LIKE :client_name")
                params_dict["client_name"] = f"%{filters['client_name']}%"
            if 'company_name' in filters and filters['company_name']:
                conditions.append("c.company_name LIKE :company_name")
                params_dict["company_name"] = f"%{filters['company_name']}%"
            if 'category' in filters and filters['category']:
                conditions.append("c.category LIKE :category")
                params_dict["category"] = f"%{filters['category']}%"
            if 'country_id' in filters and filters['country_id'] is not None:
                conditions.append("c.country_id = :country_id")
                params_dict["country_id"] = filters['country_id']
            if 'city_id' in filters and filters['city_id'] is not None:
                conditions.append("c.city_id = :city_id")
                params_dict["city_id"] = filters['city_id']

            if 'created_at_start' in filters and filters['created_at_start']:
                conditions.append("c.created_at >= :created_at_start")
                params_dict["created_at_start"] = filters['created_at_start'] + "T00:00:00Z"
            if 'created_at_end' in filters and filters['created_at_end']:
                conditions.append("c.created_at <= :created_at_end")
                params_dict["created_at_end"] = filters['created_at_end'] + "T23:59:59Z"

        if conditions:
            query_str += " WHERE " + " AND ".join(conditions)

        query_str += f" ORDER BY {sql_order_by_column} {order_direction}, c.client_name {order_direction}"

        if limit is not None:
            query_str += " LIMIT :limit OFFSET :offset"
            params_dict["limit"] = limit
            params_dict["offset"] = offset if offset is not None else 0

        sql_query = text(query_str)
        try:
            if _is_sqlalchemy_obj(conn):
                result = conn.execute(sql_query, params_dict)
            else:
                result = conn.execute(str(sql_query), params_dict)

            results_list = [dict(row._mapping) if hasattr(row, '_mapping') else dict(row) for row in result.fetchall()]
            logging.info(f"Found {len(results_list)} clients after filtering.")
            return results_list
        except Exception as e: # Changed to general Exception
            self.logger.error(f"Failed to get all clients with details: {e}", exc_info=True)
            return []

    def get_active_clients_count(self, conn: Session, include_deleted: bool = False) -> int:
        """
        Counts active clients. Active status is determined by `StatusSettings.is_archival_status`.
        Clients with no status are also considered active.

        Args:
            conn (sqlite3.Connection, optional): Database connection.
            include_deleted (bool, optional): If True, count includes clients that are soft-deleted
                                              but would otherwise be active. Defaults to False.

        Returns:
            int: The count of active clients.
        """
        sql_str = """SELECT COUNT(c.client_id) as active_count
                 FROM Clients c
                 LEFT JOIN StatusSettings ss ON c.status_id = ss.status_id
                 WHERE ((ss.is_archival_status IS NOT TRUE AND ss.is_archival_status != 1) OR c.status_id IS NULL)"""

        params_dict = {}

        if not include_deleted:
             sql_str += " AND (c.is_deleted IS NULL OR c.is_deleted = 0)"

        sql_query = text(sql_str)
        try:
            result = conn.execute(sql_query, params_dict)
            count = result.scalar_one_or_none()
            return count if count is not None else 0
        except Exception as e:
            self.logger.error(f"Failed to get active clients count: {e}", exc_info=True)
            return 0

    def get_client_counts_by_country(self, conn: Session, include_deleted: bool = False) -> list[dict]:
        """
        Gets client counts grouped by country.

        Args:
            conn (sqlite3.Connection, optional): Database connection.
            include_deleted (bool, optional): If True, calculation includes soft-deleted clients.
                                              Defaults to False.

        Returns:
            list[dict]: A list of {'country_name': name, 'client_count': count}.
        """
        sql_str = """SELECT co.country_name, COUNT(cl.client_id) as client_count
                 FROM Clients cl
                 JOIN Countries co ON cl.country_id = co.country_id
              """
        params_dict = {}
        conditions = []
        if not include_deleted:
            conditions.append("(cl.is_deleted IS NULL OR cl.is_deleted = 0)")

        if conditions:
            sql_str += " WHERE " + " AND ".join(conditions)

        sql_str += """
                 GROUP BY co.country_name
                 HAVING COUNT(cl.client_id) > 0
                 ORDER BY client_count DESC"""

        sql_query = text(sql_str)
        try:
            result = conn.execute(sql_query, params_dict)
            return [dict(row._mapping) if hasattr(row, '_mapping') else dict(row) for row in result.fetchall()]
        except Exception as e:
            self.logger.error(f"Failed to get client counts by country: {e}", exc_info=True)
            return []

    def get_client_segmentation_by_city(self, conn: Session, include_deleted: bool = False) -> list[dict]:
        """
        Gets client counts grouped by country and city.

        Args:
            conn (sqlite3.Connection, optional): Database connection.
            include_deleted (bool, optional): If True, calculation includes soft-deleted clients.
                                              Defaults to False.

        Returns:
            list[dict]: A list of {'country_name': c_name, 'city_name': ci_name, 'client_count': count}.
        """
        sql_str = """SELECT co.country_name, ci.city_name, COUNT(cl.client_id) as client_count
                 FROM Clients cl
                 JOIN Cities ci ON cl.city_id = ci.city_id
                 JOIN Countries co ON ci.country_id = co.country_id
              """
        params_dict = {}
        conditions = []
        if not include_deleted:
            conditions.append("(cl.is_deleted IS NULL OR cl.is_deleted = 0)")

        if conditions:
            sql_str += " WHERE " + " AND ".join(conditions)

        sql_str += """
                 GROUP BY co.country_name, ci.city_name
                 HAVING COUNT(cl.client_id) > 0
                 ORDER BY co.country_name, client_count DESC, ci.city_name"""

        sql_query = text(sql_str)
        try:
            result = conn.execute(sql_query, params_dict)
            return [dict(row._mapping) if hasattr(row, '_mapping') else dict(row) for row in result.fetchall()]
        except Exception as e:
            self.logger.error(f"Failed to get client segmentation by city: {e}", exc_info=True)
            return []

    def get_client_segmentation_by_status(self, conn: Session, include_deleted: bool = False) -> list[dict]:
        """
        Gets client counts grouped by status name.

        Args:
            conn (sqlite3.Connection, optional): Database connection.
            include_deleted (bool, optional): If True, calculation includes soft-deleted clients.
                                              Defaults to False.

        Returns:
            list[dict]: A list of {'status_name': name, 'client_count': count}.
        """
        params_dict = {}
        conditions = ["(ss.status_type = 'Client')"]
        if not include_deleted:
            conditions.append("(cl.is_deleted IS NULL OR cl.is_deleted = 0)")

        sql_str = f"""SELECT ss.status_name, COUNT(cl.client_id) as client_count
                  FROM Clients cl
                  JOIN StatusSettings ss ON cl.status_id = ss.status_id
                  WHERE {' AND '.join(conditions)}
                  GROUP BY ss.status_name
                  HAVING COUNT(cl.client_id) > 0
                  ORDER BY client_count DESC, ss.status_name"""

        sql_query = text(sql_str)
        try:
            result = conn.execute(sql_query, params_dict)
            return [dict(row._mapping) if hasattr(row, '_mapping') else dict(row) for row in result.fetchall()]
        except Exception as e:
            self.logger.error(f"Failed to get client segmentation by status: {e}", exc_info=True)
            return []

    def get_client_segmentation_by_category(self, conn: Session, include_deleted: bool = False) -> list[dict]:
        """
        Gets client counts grouped by category.

        Args:
            conn (sqlite3.Connection, optional): Database connection.
            include_deleted (bool, optional): If True, calculation includes soft-deleted clients.
                                              Defaults to False.

        Returns:
            list[dict]: A list of {'category': name, 'client_count': count}.
        """
        params_dict = {}
        conditions = ["(cl.category IS NOT NULL AND cl.category != '')"]
        if not include_deleted:
            conditions.append("(cl.is_deleted IS NULL OR cl.is_deleted = 0)")

        sql_str = f"""SELECT cl.category, COUNT(cl.client_id) as client_count
                  FROM Clients cl
                  WHERE {' AND '.join(conditions)}
                  GROUP BY cl.category
                  HAVING COUNT(cl.client_id) > 0
                  ORDER BY client_count DESC, cl.category"""

        sql_query = text(sql_str)
        try:
            result = conn.execute(sql_query, params_dict)
            return [dict(row._mapping) if hasattr(row, '_mapping') else dict(row) for row in result.fetchall()]
        except Exception as e:
            self.logger.error(f"Failed to get client segmentation by category: {e}", exc_info=True)
            return []

    def get_clients_by_archival_status(self, is_archived: bool, conn: Session, include_null_status_for_active: bool = True, include_deleted: bool = False) -> list[dict]:
        """
        Retrieves clients based on their archival status (derived from StatusSettings).

        Args:
            is_archived (bool): If True, fetches archived clients. If False, fetches active clients.
            include_null_status_for_active (bool, optional): If True and fetching active clients,
                                                             includes clients with no status_id. Defaults to True.
            conn (sqlite3.Connection, optional): Database connection.
            include_deleted (bool, optional): If True, includes soft-deleted clients that match
                                              the archival status criteria. Defaults to False.

        Returns:
            list[dict]: A list of client records.
        """
        params_dict = {}
        try:
            archival_status_text_query = text("SELECT status_id FROM StatusSettings WHERE status_type = 'Client' AND (is_archival_status = TRUE OR is_archival_status = 1)")
            archival_status_result = conn.execute(archival_status_text_query)
            archival_ids = [row[0] if not hasattr(row, '_mapping') else row.status_id for row in archival_status_result.fetchall()]

            base_query_str = """SELECT c.*, co.country_name AS country, ci.city_name AS city,
                                s.status_name AS status, s.color_hex AS status_color, s.icon_name AS status_icon_name,
                                t.template_name AS default_template_name
                                FROM Clients c
                                LEFT JOIN Countries co ON c.country_id = co.country_id
                                LEFT JOIN Cities ci ON c.city_id = ci.city_id
                                LEFT JOIN StatusSettings s ON c.status_id = s.status_id AND s.status_type = 'Client'
                                LEFT JOIN Templates t ON c.default_template_id = t.template_id"""
            conditions = []

            if not include_deleted:
                conditions.append("(c.is_deleted IS NULL OR c.is_deleted = 0)")

            if not archival_ids:
                if is_archived: return []
            else:
                if is_archived:
                    archival_id_conditions = []
                    for i, aid in enumerate(archival_ids):
                        param_name = f"archival_id_{i}"
                        archival_id_conditions.append(f":{param_name}")
                        params_dict[param_name] = aid
                    if archival_id_conditions:
                         conditions.append(f"c.status_id IN ({', '.join(archival_id_conditions)})")
                else:
                    not_archival_id_conditions = []
                    for i, aid in enumerate(archival_ids):
                        param_name = f"not_archival_id_{i}"
                        not_archival_id_conditions.append(f":{param_name}")
                        params_dict[param_name] = aid

                    not_in_clause = ""
                    if not_archival_id_conditions:
                        not_in_clause = f"c.status_id NOT IN ({', '.join(not_archival_id_conditions)})"

                    if include_null_status_for_active:
                        if not_in_clause:
                             conditions.append(f"({not_in_clause} OR c.status_id IS NULL)")
                        else:
                             conditions.append("c.status_id IS NOT NULL OR c.status_id IS NULL")
                    elif not_in_clause:
                        conditions.append(not_in_clause)


            sql_final_str = f"{base_query_str} {'WHERE ' + ' AND '.join(conditions) if conditions else ''} ORDER BY c.client_name;"
            sql_query = text(sql_final_str)

            result = conn.execute(sql_query, params_dict)
            return [dict(row._mapping) if hasattr(row, '_mapping') else dict(row) for row in result.fetchall()]
        except Exception as e:
            self.logger.error(f"Failed to get clients by archival status (is_archived={is_archived}): {e}", exc_info=True)
            return []

    def get_active_clients_per_country(self, conn: Session, include_deleted: bool = False) -> dict:
        """
        Retrieves active clients, mapping them by country.

        Args:
            conn (sqlite3.Connection, optional): Database connection.
            include_deleted (bool, optional): If True, includes soft-deleted clients in the map.
                                              Defaults to False.

        Returns:
            dict: A dictionary where keys are country names and values are lists of
                  client details ({'client_id', 'client_name'}).
        """
        clients_by_country_map = {}
        params_dict = {}
        try:
            archival_status_text_query = text("SELECT status_id FROM StatusSettings WHERE (is_archival_status = TRUE OR is_archival_status = 1) AND status_type = 'Client'")
            archival_status_result = conn.execute(archival_status_text_query)
            archival_ids = [row[0] if not hasattr(row, '_mapping') else row.status_id for row in archival_status_result.fetchall()]

            query_parts = [
                "SELECT",
                "    co.country_name,",
                "    cl.client_id,",
                "    cl.client_name",
                "FROM Clients cl",
                "JOIN Countries co ON cl.country_id = co.country_id"
            ]

            conditions = []
            if not include_deleted:
                conditions.append("(cl.is_deleted IS NULL OR cl.is_deleted = 0)")

            if archival_ids:
                archival_id_conditions = []
                for i, aid in enumerate(archival_ids):
                    param_name = f"archival_id_{i}"
                    archival_id_conditions.append(f":{param_name}")
                    params_dict[param_name] = aid
                if archival_id_conditions:
                    conditions.append(f"(cl.status_id IS NULL OR cl.status_id NOT IN ({', '.join(archival_id_conditions)}))")

            if conditions:
                query_parts.append(f"WHERE {' AND '.join(conditions)}")

            query_parts.append("ORDER BY co.country_name, cl.client_name;")
            sql_query_str = "\n".join(query_parts)
            sql_query = text(sql_query_str)

            result = conn.execute(sql_query, params_dict)

            for row in result:
                country = row.country_name if hasattr(row, '_mapping') else row['country_name']
                client_detail = {'client_id': row.client_id, 'client_name': row.client_name}
                if country not in clients_by_country_map:
                    clients_by_country_map[country] = []
                clients_by_country_map[country].append(client_detail)
        except Exception as e:
            self.logger.error(f"Failed to get active clients per country: {e}", exc_info=True)
        return clients_by_country_map

    # --- ClientNotes CRUD ---
    def add_client_note(self, client_id: str, note_text: str, conn: Session, user_id: str = None) -> dict:
        """
        Adds a note for a specific client.

        Args:
            client_id (str): The UUID of the client.
            note_text (str): The content of the note.
            user_id (str, optional): The UUID of the user adding the note.
            conn (sqlite3.Connection, optional): Database connection.

        Returns:
            dict: {'success': True, 'note_id': new_id} on success,
                  {'success': False, 'error': 'message'} on failure.
        """
        if not client_id or not note_text:
             return {'success': False, 'error': "Client ID and note text are required."}

        sql_query = text("INSERT INTO ClientNotes (client_id, note_text, user_id, timestamp) VALUES (:client_id, :note_text, :user_id, :timestamp)")
        now_utc_iso = datetime.utcnow().isoformat() + "Z"
        params_dict = {
            "client_id": client_id, "note_text": note_text,
            "user_id": user_id, "timestamp": now_utc_iso
        }
        try:
            result = conn.execute(sql_query, params_dict)
            last_id = result.lastrowid
            if last_id is None and hasattr(result, 'inserted_primary_key') and result.inserted_primary_key:
                last_id = result.inserted_primary_key[0]
            return {'success': True, 'note_id': last_id}
        except Exception as e:
            self.logger.error(f"Failed to add client note for client {client_id}: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def get_client_notes(self, client_id: str, conn: Session) -> list[dict]:
        """
        Retrieves all notes for a specific client, ordered by timestamp descending.
        Client notes are not subject to the client's soft delete status directly;
        they are always retrieved if the client_id exists.

        Args:
            client_id (str): The UUID of the client.
            conn (sqlite3.Connection, optional): Database connection.

        Returns:
            list[dict]: A list of note records.
        """
        sql_query = text("SELECT note_id, client_id, timestamp, note_text, user_id FROM ClientNotes WHERE client_id = :client_id ORDER BY timestamp DESC")
        try:
            result = conn.execute(sql_query, {"client_id": client_id})
            return [dict(row._mapping) if hasattr(row, '_mapping') else dict(row) for row in result.fetchall()]
        except Exception as e:
            self.logger.error(f"Failed to get client notes for client {client_id}: {e}", exc_info=True)
            return []

    def get_total_clients_count(self, conn: Session, include_deleted: bool = False) -> int:
        sql_str = "SELECT COUNT(client_id) as total_count FROM Clients"
        params_dict = {}
        conditions = []
        if not include_deleted:
            conditions.append("(is_deleted IS NULL OR is_deleted = 0)")

        if conditions:
            sql_str += " WHERE " + " AND ".join(conditions)

        sql_query = text(sql_str)
        try:
            result = conn.execute(sql_query, params_dict)
            count = result.scalar_one_or_none()
            return count if count is not None else 0
        except Exception as e:
            self.logger.error(f"Error getting total clients count (include_deleted={include_deleted}): {e}", exc_info=True)
            return 0

    def get_clients_count_created_between(self, start_date_iso: str, end_date_iso: str, conn: Session, include_deleted: bool = False) -> int:
        """
        Counts clients created within a specific date range.

        Args:
            start_date_iso (str): The start of the date range in ISO format (YYYY-MM-DDTHH:MM:SS.ffffffZ).
            end_date_iso (str): The end of the date range in ISO format (YYYY-MM-DDTHH:MM:SS.ffffffZ).
            conn (sqlite3.Connection, optional): Database connection. Managed by decorator.
            include_deleted (bool, optional): If True, includes soft-deleted clients. Defaults to False.

        Returns:
            int: The count of clients created within the specified range. Returns 0 on error or if none found.
        """
        query_str = "SELECT COUNT(client_id) as count FROM Clients WHERE created_at >= :start_date AND created_at <= :end_date"
        params_dict = {"start_date": start_date_iso, "end_date": end_date_iso}

        if not include_deleted:
            query_str += " AND (is_deleted IS NULL OR is_deleted = 0)"

        sql_query = text(query_str)
        try:
            result = conn.execute(sql_query, params_dict)
            count = result.scalar_one_or_none()
            return count if count is not None else 0
        except Exception as e:
            self.logger.error(f"Error getting clients count created between {start_date_iso} and {end_date_iso} (include_deleted={include_deleted}): {e}", exc_info=True)
            return 0

    def get_total_clients_count_up_to_date(self, date_iso_end: str, conn: Session) -> int:
        sql = """
            SELECT COUNT(client_id) as count
            FROM Clients
            WHERE created_at <= :date_iso_end
              AND (is_deleted = 0 OR is_deleted IS NULL OR deleted_at > :date_iso_end OR deleted_at IS NULL)
        """
        params_dict = {"date_iso_end": date_iso_end}
        sql_query = text(sql)
        try:
            result = conn.execute(sql_query, params_dict)
            count = result.scalar_one_or_none()
            self.logger.debug(f"Total clients count up to {date_iso_end}: {count if count is not None else 0}")
            return count if count is not None else 0
        except Exception as e:
            self.logger.error(f"DB error in get_total_clients_count_up_to_date for date {date_iso_end}: {e}", exc_info=True)
            return 0

    def get_active_clients_count_up_to_date(self, date_iso_end: str, conn: Session) -> int:
        sql = """
            SELECT COUNT(c.client_id) as count
            FROM Clients c
            LEFT JOIN StatusSettings ss ON c.status_id = ss.status_id AND ss.status_type = 'Client'
            WHERE c.created_at <= :date_iso_end
              AND (c.is_deleted = 0 OR c.is_deleted IS NULL OR c.deleted_at > :date_iso_end OR c.deleted_at IS NULL)
              AND ((ss.is_archival_status = 0 OR ss.is_archival_status IS NULL) OR c.status_id IS NULL)
        """
        params_dict = {"date_iso_end": date_iso_end}
        sql_query = text(sql)
        try:
            result = conn.execute(sql_query, params_dict)
            count = result.scalar_one_or_none()
            self.logger.debug(f"Active clients count up to {date_iso_end}: {count if count is not None else 0}")
            return count if count is not None else 0
        except Exception as e:
            self.logger.error(f"DB error in get_active_clients_count_up_to_date for {date_iso_end}: {e}", exc_info=True)
            return 0

    def get_clients_by_status_id(self, status_id: int, conn: Session, include_deleted: bool = False) -> list[dict]:
        """
        Retrieves clients matching a specific status_id, including details from joined tables.
        """
        params_dict = {"status_id": status_id}
        query_str = """
        SELECT c.client_id, c.client_name, c.company_name, c.primary_need_description,
               c.project_identifier, c.default_base_folder_path, c.selected_languages,
               c.price, c.notes, c.created_at, c.category, c.status_id, c.country_id, c.city_id,
               c.is_deleted, c.deleted_at, c.default_template_id,
               co.country_name AS country, ci.city_name AS city,
               s.status_name AS status, s.color_hex AS status_color, s.icon_name AS status_icon_name,
               t.template_name AS default_template_name
        FROM Clients c
        LEFT JOIN Countries co ON c.country_id = co.country_id
        LEFT JOIN Cities ci ON c.city_id = ci.city_id
        LEFT JOIN StatusSettings s ON c.status_id = s.status_id AND s.status_type = 'Client'
        LEFT JOIN Templates t ON c.default_template_id = t.template_id
        WHERE c.status_id = :status_id
        """

        if not include_deleted:
            query_str += " AND (c.is_deleted IS NULL OR c.is_deleted = 0)"

        query_str += " ORDER BY c.client_name"

        sql_query = text(query_str)
        try:
            result = conn.execute(sql_query, params_dict)
            return [dict(row._mapping) if hasattr(row, '_mapping') else dict(row) for row in result.fetchall()]
        except Exception as e:
            self.logger.error(f"Failed to get clients for status_id {status_id}: {e}", exc_info=True)
            return []

    def get_client_count_by_country_id(self, country_id: int, conn: Session, include_deleted: bool = False) -> int:
        """
        Counts clients for a specific country_id.

        Args:
            country_id (int): The ID of the country.
            conn (sqlite3.Connection, optional): Database connection.
            include_deleted (bool, optional): If True, includes soft-deleted clients. Defaults to False.

        Returns:
            int: The count of clients in the specified country.
        """
        sql_str = "SELECT COUNT(client_id) as count FROM Clients WHERE country_id = :country_id"
        params_dict = {"country_id": country_id}

        if not include_deleted:
            sql_str += " AND (is_deleted IS NULL OR is_deleted = 0)"

        sql_query = text(sql_str)
        try:
            result = conn.execute(sql_query, params_dict)
            count = result.scalar_one_or_none()
            return count if count is not None else 0
        except Exception as e:
            self.logger.error(f"Error getting client count for country_id {country_id}: {e}", exc_info=True)
            return 0

    def search_clients_by_name(self, name_query: str, conn: Session, limit: int = 10) -> list[dict]:
        """
        Searches for clients by name (client_name or company_name).
        """
        if not name_query:
            return []

        sql_query = text("""
            SELECT client_id, client_name, company_name
            FROM Clients
            WHERE (client_name LIKE :query OR company_name LIKE :query)
              AND (is_deleted IS NULL OR is_deleted = 0)
            ORDER BY client_name
            LIMIT :limit
        """)
        params = {"query": f"%{name_query}%", "limit": limit}

        try:
            result = conn.execute(sql_query, params)
            return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            self.logger.error(f"Failed to search clients by name '{name_query}': {e}", exc_info=True)
            return []

# Instantiate the CRUD class for easy import and use elsewhere
clients_crud_instance = ClientsCRUD()

# Expose specific CRUD methods for direct import
add_client = clients_crud_instance.add_client
get_all_clients = clients_crud_instance.get_all_clients
get_client_by_id = clients_crud_instance.get_client_by_id
get_client_by_project_identifier = clients_crud_instance.get_client_by_project_identifier
update_client = clients_crud_instance.update_client
delete_client = clients_crud_instance.delete_client
get_all_clients_with_details = clients_crud_instance.get_all_clients_with_details
get_active_clients_count = clients_crud_instance.get_active_clients_count
get_client_counts_by_country = clients_crud_instance.get_client_counts_by_country
get_client_segmentation_by_city = clients_crud_instance.get_client_segmentation_by_city
get_client_segmentation_by_status = clients_crud_instance.get_client_segmentation_by_status
get_client_segmentation_by_category = clients_crud_instance.get_client_segmentation_by_category
get_clients_by_archival_status = clients_crud_instance.get_clients_by_archival_status
get_active_clients_per_country = clients_crud_instance.get_active_clients_per_country
add_client_note = clients_crud_instance.add_client_note
get_client_notes = clients_crud_instance.get_client_notes
get_total_clients_count = clients_crud_instance.get_total_clients_count
get_clients_count_created_between = clients_crud_instance.get_clients_count_created_between
get_total_clients_count_up_to_date = clients_crud_instance.get_total_clients_count_up_to_date
get_active_clients_count_up_to_date = clients_crud_instance.get_active_clients_count_up_to_date # Added export

__all__ = [
    "add_client",
    "get_total_clients_count",
    "get_client_by_id",
    "get_client_by_project_identifier",
    "get_all_clients",
    "update_client",
    "delete_client", # Soft delete
    "get_all_clients_with_details",
    "get_active_clients_count",
    "get_client_counts_by_country",
    "get_client_segmentation_by_city",
    "get_client_segmentation_by_status",
    "get_client_segmentation_by_category",
    "get_clients_by_archival_status",
    "get_active_clients_per_country",
    "add_client_note",
    "get_client_notes",
    "get_clients_count_created_between",
    "get_total_clients_count_up_to_date",
    "get_active_clients_count_up_to_date",
    "get_client_count_by_country_id",
    "get_clients_by_status_id", # Added new function
    "search_clients_by_name",
    "ClientsCRUD", # Exporting the class itself for type hinting or direct instantiation
    "clients_crud_instance", # Exporting the instance if needed elsewhere
    "get_client_count_by_country_id"
]
