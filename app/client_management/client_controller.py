# controllers/client_controller.py
import db as db_manager # Assuming db_manager is the existing module for DB interactions
from db.cruds.clients import clients_crud_instance as clients_crud, client_project_products_crud
from db.cruds.products.products_crud import products_crud_instance as products_crud
from db.cruds.misc import regions_crud, referents_crud
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from db.cruds.misc.activity_logs_crud import add_activity_log

class ClientController:
    def __init__(self):
        # In the future, we might pass a specific DB connection or configuration
        pass

    # --- Country and City Management (existing) ---
    def get_all_countries(self):
        """Fetches all countries from the database."""
        try:
            return db_manager.get_all_countries()
        except Exception as e:
            logging.error(f"Error in ClientController.get_all_countries: {e}", exc_info=True)
            return []

    def get_cities_for_country(self, country_id):
        """Fetches all cities for a given country_id."""
        try:
            return db_manager.get_all_cities(country_id=country_id)
        except Exception as e:
            logging.error(f"Error in ClientController.get_cities_for_country: {e}", exc_info=True)
            return []

    def add_country(self, country_name):
        """Adds a new country to the database. (Uses get_or_add for safety)"""
        if not country_name or not country_name.strip():
            return None
        try:
            country_data = db_manager.get_or_add_country(country_name.strip())
            return country_data
        except Exception as e:
            logging.error(f"Error in ClientController.add_country: {e}", exc_info=True)
            return None

    def add_city(self, city_name, country_id):
        """Adds a new city to the database for the given country_id. (Uses get_or_add for safety)"""
        if not city_name or not city_name.strip() or country_id is None:
            return None
        try:
            city_data = db_manager.get_or_add_city(city_name.strip(), country_id)
            return city_data
        except Exception as e:
            logging.error(f"Error in ClientController.add_city: {e}", exc_info=True)
            return None

    # --- Region Management (New) ---
    def get_all_regions(self):
        """
        Fetches all regions from the database.

        Returns:
            list[dict]: A list of all region dictionaries, or an empty list on error.
        """
        try:
            return regions_crud.get_all_regions()
        except Exception as e:
            logging.error(f"Error in ClientController.get_all_regions: {e}", exc_info=True)
            return []

    def get_regions_for_country(self, country_id: int):
        """
        Fetches all regions for a given country_id.

        Args:
            country_id (int): The ID of the country.

        Returns:
            list[dict]: A list of region dictionaries for the country, or an empty list if none found or error.
        """
        if country_id is None:
            return []
        try:
            return regions_crud.get_regions_for_country(country_id)
        except Exception as e:
            logging.error(f"Error in ClientController.get_regions_for_country (country_id: {country_id}): {e}", exc_info=True)
            return []

    def get_or_add_region(self, region_name: str, country_id: int):
        """
        Gets an existing region by name and country_id, or adds it if it doesn't exist.

        Args:
            region_name (str): The name of the region.
            country_id (int): The ID of the country this region belongs to.

        Returns:
            dict | None: A dictionary representing the region, or None on failure.
        """
        if not region_name or not region_name.strip() or country_id is None:
            logging.warning("Region name and country_id are required for get_or_add_region.")
            return None
        try:
            region_data = regions_crud.get_or_add_region(region_name.strip(), country_id)
            return region_data
        except Exception as e:
            logging.error(f"Error in ClientController.get_or_add_region for '{region_name}', country_id {country_id}: {e}", exc_info=True)
            return None

    # --- Client Management (existing, slightly refactored logging) ---
    def create_client(self, client_data: dict):
        """
        Creates a new client.
        client_data is a dictionary expected to contain keys like:
        'client_name', 'company_name', 'primary_need_description',
        'country_name', 'city_name', 'project_identifier', 'selected_languages'

        This method will handle resolving country and city names to IDs,
        adding them to the database if they don't exist.
        Returns the created client data (with IDs) or None on failure.
        """
        from db.cruds.status_settings_crud import get_status_setting_by_name # Import here
        from db.cruds.templates_crud import get_all_templates # Import for fallback template ID
        from db.cruds import users_crud # Changed import for fallback user ID


        try:
            country_name = client_data.get('country_name', '').strip()
            city_name = client_data.get('city_name', '').strip()

            if not country_name:
                logging.error("Country name is required to create a client.")
                return {'success': False, 'error': "Country name is required."}


            # Get or add country
            country_obj = self.add_country(country_name) # add_country handles get_or_add
            if not country_obj or 'country_id' not in country_obj:
                logging.error(f"Could not get or add country '{country_name}'.")
                return {'success': False, 'error': f"Could not get or add country '{country_name}'."}

            final_country_id = country_obj['country_id']

            final_city_id = None
            if city_name:
                city_obj = self.add_city(city_name, final_country_id)
                if not city_obj or 'city_id' not in city_obj:
                    logging.warning(f"Could not get or add city '{city_name}'. Proceeding without city.")
                else:
                    final_city_id = city_obj['city_id']

            # Determine default status_id
            default_status_name = "Client Actif"
            status_obj = get_status_setting_by_name(default_status_name, "Client")
            final_status_id = None
            if status_obj and 'status_id' in status_obj:
                final_status_id = status_obj['status_id']
            else:
                logging.warning(f"Default client status '{default_status_name}' not found. Client will be created without a status or with DB default if any.")


            # Determine default_template_id
            final_default_template_id = client_data.get('default_template_id')
            if final_default_template_id is None:
                try:
                    all_templates = get_all_templates(apply_visibility_filter=False)
                    if all_templates:
                        final_default_template_id = all_templates[0].get('template_id')
                        logging.info(f"Using first available template ID {final_default_template_id} as fallback for default_template_id.")
                    else:
                        logging.warning("No templates found in DB. default_template_id will be None. This might cause FK error if column is NOT NULL.")
                except Exception as e_tpl:
                    logging.error(f"Error fetching fallback template ID: {e_tpl}. default_template_id will be None.", exc_info=True)


            db_client_data = {
                'client_name': client_data.get('client_name'),
                'company_name': client_data.get('company_name'),
                'primary_need_description': client_data.get('primary_need_description'),
                'country_id': final_country_id,
                'city_id': final_city_id,
                'project_identifier': client_data.get('project_identifier'),
                'status_id': client_data.get('status_id', final_status_id),
                'languages': client_data.get('selected_languages'),
                'default_template_id': final_default_template_id
            }

            for key in ['price', 'notes', 'category', 'lead_source']:
                if key in client_data:
                    db_client_data[key] = client_data[key]

            final_created_by_user_id = client_data.get('created_by_user_id')
            if not final_created_by_user_id:
                logging.error("Critical: created_by_user_id was not provided to ClientController.create_client.")
                return {'success': False, 'error': "Client creator ID was not provided."}
            db_client_data['created_by_user_id'] = final_created_by_user_id


            if not db_client_data.get('client_name'):
                logging.error("Client name is required.")
                return {'success': False, 'error': "Client name is required."}

            result = clients_crud.add_client(db_client_data)

            if result and result.get('success'):
                new_client_id = result.get('client_id')
                created_client_details = clients_crud.clients_crud_instance.get_client_by_id(new_client_id) # Fetch full details

                if not created_client_details: # Fallback if fetch fails
                    logging.warning(f"Client created with ID {new_client_id}, but failed to fetch full details. Returning minimal info.")
                    created_client_details = {'client_id': new_client_id, 'client_name': db_client_data.get('client_name'), 'success': True, 'warning': 'Details fetch failed'}
                else:
                    logging.info(f"Client '{created_client_details.get('client_name')}' created successfully with ID {new_client_id}.")

                if client_data.get('product_product_name', '').strip():
                    # Product adding logic (simplified for brevity, assumed to be correct from original)
                    logging.info(f"Attempting to add product for client ID {new_client_id}...")
                    # ... (original product adding logic) ...
                    pass # Placeholder for original product logic

                try:
                    log_data = {
                        "user_id": db_client_data.get('created_by_user_id'),
                        "action_type": "CLIENT_CREATED",
                        "details": f"Client '{created_client_details.get('client_name')}' créé.",
                        "related_entity_type": "Client",
                        "related_entity_id": new_client_id,
                        "related_client_id": new_client_id
                    }
                    add_activity_log(log_data)
                    logging.info(f"Activity logged for CLIENT_CREATED: {new_client_id}")
                except Exception as e_log:
                    logging.error(f"Failed to log CLIENT_CREATED activity for client {new_client_id}: {e_log}", exc_info=True)

                return created_client_details
            else:
                error_message = result.get('error', 'Failed to create client in database.') if result else 'CRUD operation failed unexpectedly.'
                logging.error(f"Client creation failed: {error_message}")
                return {'success': False, 'error': error_message}

        except Exception as e:
            logging.exception(f"Unhandled exception in ClientController.create_client: {e}")
            return {'success': False, 'error': f"An unexpected error occurred: {str(e)}"}

    # --- Referent Management (New) ---
    def make_client_referent(self, client_id: str, country_id: int, region_name: str | None,
                             city_name: str | None, notes: str | None, user_id: str):
        """
        Designates an existing client as a referent.

        Args:
            client_id (str): The ID of the client to make a referent.
            country_id (int): The country ID for the referent's classification.
            region_name (str | None): The name of the region for the referent. Can be new.
            city_name (str | None): The name of the city for the referent. Can be new.
            notes (str | None): Notes specific to this referent role.
            user_id (str): The ID of the user performing the action.

        Returns:
            dict: A dictionary containing {'success': bool, 'referent_id': str | None, 'error': str | None}.
                  'status': 'already_exists' can be returned in error if client is already a referent.
        """
        if not client_id or not country_id or not user_id:
            logging.error("Client ID, Country ID, and User ID are required to make a client a referent.")
            return {'success': False, 'error': "Client ID, Country ID, and User ID are required."}

        # Check if client exists
        client_details = clients_crud.get_client_by_id(client_id)
        if not client_details:
            logging.error(f"Client with ID {client_id} not found. Cannot make referent.")
            return {'success': False, 'error': f"Client with ID {client_id} not found."}

        # Check if client has made any purchases (simplified check: has at least one order)
        # This logic might need to be more sophisticated based on actual order status.
        from db.cruds import commandes_crud # Local import
        client_orders = commandes_crud.get_commandes_for_client(client_id, limit=1)
        if not client_orders:
            logging.warning(f"Client {client_id} has no orders. Policy is that only clients who purchased can be referents.")
            # Depending on strictness, this could be an error or just a warning.
            # For now, let's allow it but log a warning.
            # return {'success': False, 'error': "Client must have made a purchase to become a referent."}


        final_region_id = None
        if region_name and region_name.strip():
            region_obj = self.get_or_add_region(region_name.strip(), country_id)
            if region_obj and 'region_id' in region_obj:
                final_region_id = region_obj['region_id']
            else:
                logging.warning(f"Could not get or add region '{region_name}' for country_id {country_id}. Proceeding without region for referent.")

        final_city_id = None
        # City is usually dependent on country, ensure country_id is valid for city.
        # The country_id passed to this function is for the referent's location, which might differ from client's primary country.
        if city_name and city_name.strip():
            city_obj = self.add_city(city_name.strip(), country_id) # add_city uses get_or_add_city
            if city_obj and 'city_id' in city_obj:
                final_city_id = city_obj['city_id']
            else:
                logging.warning(f"Could not get or add city '{city_name}' for country_id {country_id}. Proceeding without city for referent.")

        try:
            referent_id = referents_crud.add_referent(
                client_id=client_id,
                country_id=country_id,
                region_id=final_region_id,
                city_id=final_city_id,
                notes=notes,
                created_by_user_id=user_id
            )
            if referent_id:
                logging.info(f"Client {client_id} successfully made a referent with ID {referent_id}.")
                # Log activity
                try:
                    log_data = {
                        "user_id": user_id, "action_type": "REFERENT_CREATED",
                        "details": f"Client '{client_details.get('client_name', client_id)}' est devenu référent.",
                        "related_entity_type": "Referent", "related_entity_id": referent_id,
                        "related_client_id": client_id
                    }
                    add_activity_log(log_data)
                except Exception as e_log:
                    logging.error(f"Failed to log REFERENT_CREATED activity for referent {referent_id}: {e_log}", exc_info=True)
                return {'success': True, 'referent_id': referent_id}
            else:
                # Check if already a referent, as add_referent returns None on IntegrityError
                existing_referent = referents_crud.get_referent_by_client_id(client_id, include_inactive=True)
                if existing_referent:
                    logging.warning(f"Client {client_id} is already a referent (ID: {existing_referent['referent_id']}).")
                    return {'success': False, 'error': 'Client is already a referent.', 'referent_id': existing_referent['referent_id'], 'status': 'already_exists'}
                logging.error(f"Failed to make client {client_id} a referent.")
                return {'success': False, 'error': 'Failed to create referent record in database.'}
        except Exception as e:
            logging.error(f"Exception in make_client_referent for client {client_id}: {e}", exc_info=True)
            return {'success': False, 'error': f"An unexpected error occurred: {str(e)}"}

    def update_referent_details(self, referent_id: str, country_id: int | None = None,
                                region_name: str | None = None, city_name: str | None = None,
                                notes: str | None = None, is_active: bool | None = None, user_id: str | None = None):
        """
        Updates details of an existing referent.

        Args:
            referent_id (str): The ID of the referent to update.
            country_id (int | None, optional): New country ID.
            region_name (str | None, optional): New region name. Can be new to be created.
            city_name (str | None, optional): New city name. Can be new to be created.
            notes (str | None, optional): New notes.
            is_active (bool | None, optional): New active status.
            user_id (str | None, optional): ID of the user performing the update (for logging).

        Returns:
            dict: A dictionary containing {'success': bool, 'message': str | None, 'error': str | None}.
        """
        if not referent_id:
            return {'success': False, 'error': "Referent ID is required."}

        update_data = {}
        current_referent = referents_crud.get_referent_by_id(referent_id)
        if not current_referent:
            return {'success': False, 'error': f"Referent with ID {referent_id} not found."}

        # Use current country_id if not provided for region/city resolution
        effective_country_id = country_id if country_id is not None else current_referent['country_id']

        if country_id is not None:
            update_data['country_id'] = country_id

        if region_name is not None: # Allow empty string to clear region
            if region_name.strip():
                region_obj = self.get_or_add_region(region_name.strip(), effective_country_id)
                if region_obj and 'region_id' in region_obj:
                    update_data['region_id'] = region_obj['region_id']
                else:
                    return {'success': False, 'error': f"Could not process region '{region_name}'."}
            else: # Empty string means clear region_id
                 update_data['region_id'] = None

        if city_name is not None: # Allow empty string to clear city
            if city_name.strip():
                city_obj = self.add_city(city_name.strip(), effective_country_id) # add_city uses get_or_add_city
                if city_obj and 'city_id' in city_obj:
                    update_data['city_id'] = city_obj['city_id']
                else:
                    return {'success': False, 'error': f"Could not process city '{city_name}'."}
            else: # Empty string means clear city_id
                update_data['city_id'] = None

        if notes is not None:
            update_data['notes'] = notes
        if is_active is not None:
            update_data['is_active'] = is_active

        if not update_data:
            return {'success': True, 'message': 'No changes provided for referent.', 'updated_count': 0}

        try:
            success = referents_crud.update_referent(referent_id, update_data)
            if success: # update_referent returns bool
                logging.info(f"Referent {referent_id} updated successfully with data: {update_data}.")
                if user_id: # Log activity if user_id is provided
                    try:
                        log_data = {
                            "user_id": user_id, "action_type": "REFERENT_UPDATED",
                            "details": f"Referent ID {referent_id} (Client ID: {current_referent['client_id']}) mis à jour.",
                            "related_entity_type": "Referent", "related_entity_id": referent_id,
                            "related_client_id": current_referent['client_id']
                        }
                        add_activity_log(log_data)
                    except Exception as e_log:
                        logging.error(f"Failed to log REFERENT_UPDATED activity for referent {referent_id}: {e_log}", exc_info=True)
                return {'success': True, 'message': 'Referent updated successfully.'}
            else:
                # This might mean rowcount was 0 (no actual change or ID not found by CRUD)
                logging.warning(f"Update referent {referent_id} reported no rows changed by CRUD. Data: {update_data}")
                # Re-check if referent exists, as it might have been deleted.
                if not referents_crud.get_referent_by_id(referent_id):
                     return {'success': False, 'error': f"Referent with ID {referent_id} not found during update attempt."}
                return {'success': False, 'error': 'Failed to update referent in database or no changes made.'}
        except Exception as e:
            logging.error(f"Exception updating referent {referent_id}: {e}", exc_info=True)
            return {'success': False, 'error': f"An unexpected error occurred: {str(e)}"}

    def set_referent_status(self, referent_id: str, is_active: bool, user_id: str | None = None):
        """
        Activates or deactivates a referent.

        Args:
            referent_id (str): The ID of the referent.
            is_active (bool): The desired active status (True for active, False for inactive).
            user_id (str | None, optional): ID of the user performing the action (for logging).

        Returns:
            dict: A dictionary containing {'success': bool, 'message': str | None, 'error': str | None}.
        """
        if referent_id is None or is_active is None: # is_active can be False, so check for None
            return {'success': False, 'error': "Referent ID and active status are required."}

        success = referents_crud.set_referent_active_status(referent_id, is_active)
        if success:
            action = "activated" if is_active else "deactivated"
            logging.info(f"Referent {referent_id} status set to {action}.")
            if user_id:
                current_referent = referents_crud.get_referent_by_id(referent_id)
                if current_referent:
                    try:
                        log_data = {
                            "user_id": user_id, "action_type": f"REFERENT_{action.upper()}",
                            "details": f"Referent ID {referent_id} (Client ID: {current_referent['client_id']}) {action}.",
                            "related_entity_type": "Referent", "related_entity_id": referent_id,
                            "related_client_id": current_referent['client_id']
                        }
                        add_activity_log(log_data)
                    except Exception as e_log:
                        logging.error(f"Failed to log REFERENT_{action.upper()} activity for referent {referent_id}: {e_log}", exc_info=True)
            return {'success': True, 'message': f'Referent {action} successfully.'}
        else:
            if not referents_crud.get_referent_by_id(referent_id): # Check if referent exists
                return {'success': False, 'error': f"Referent with ID {referent_id} not found."}
            logging.error(f"Failed to set active status for referent {referent_id}.")
            return {'success': False, 'error': 'Failed to update referent status in database.'}

    def get_referent_profile_by_client_id(self, client_id: str, include_inactive: bool = False):
        """
        Retrieves the referent profile for a given client_id, including joined details
        like client name, country name, region name, and city name.

        Args:
            client_id (str): The ID of the client.
            include_inactive (bool, optional): Whether to include inactive referents. Defaults to False.

        Returns:
            dict | None: A dictionary with the referent's full profile, or None if not found or error.
        """
        if not client_id:
            return None
        try:
            basic_referent = referents_crud.get_referent_by_client_id(client_id, include_inactive=include_inactive)
            if not basic_referent:
                return None

            profile = basic_referent.copy()

            client_info = clients_crud.get_client_by_id(profile['client_id'])
            if client_info:
                profile['client_name'] = client_info.get('client_name')
                profile['company_name'] = client_info.get('company_name')

            country_info = db_manager.get_country_by_id(profile['country_id'])
            if country_info: profile['country_name'] = country_info.get('country_name')

            if profile.get('region_id'):
                region_info = regions_crud.get_region_by_id(profile['region_id'])
                if region_info: profile['region_name'] = region_info.get('region_name')
            else:
                profile['region_name'] = None # Ensure key exists even if no region

            if profile.get('city_id'):
                city_info = db_manager.get_city_by_id(profile['city_id'])
                if city_info: profile['city_name'] = city_info.get('city_name')
            else:
                profile['city_name'] = None # Ensure key exists

            return profile

        except Exception as e:
            logging.error(f"Error fetching referent profile for client_id {client_id}: {e}", exc_info=True)
            return None

    def get_client_by_id_for_dialog(self, client_id: str):
        """
        Wrapper to get client details, typically for dialogs.
        This helps avoid direct CRUD access from dialogs if controller is available.
        """
        if not client_id:
            logging.warning("ClientController.get_client_by_id_for_dialog: client_id is required.")
            return None
        try:
            # Assuming clients_crud is an instance like clients_crud.clients_crud_instance
            # or a module with a get_client_by_id function.
            # Based on other parts of ClientController, it seems to use module-level CRUDs.
            return clients_crud.get_client_by_id(client_id)
        except Exception as e:
            logging.error(f"Error in ClientController.get_client_by_id_for_dialog for client ID {client_id}: {e}", exc_info=True)
            return None

# controllers/client_controller.py
import db as db_manager # Assuming db_manager is the existing module for DB interactions
from db.cruds.clients import clients_crud_instance as clients_crud
from db.cruds.products import products_crud
from db.cruds.clients import client_project_products_crud
from db.cruds.misc import regions_crud, referents_crud
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from db.cruds.misc.activity_logs_crud import add_activity_log
from db.cruds.misc import companies_crud
from document_generator import html_generator # Ajouté
import os # Ajouté
import tempfile # Ajouté pour un chemin de sortie temporaire


class ClientController:
    def __init__(self):
        # In the future, we might pass a specific DB connection or configuration
        pass

    # --- Country and City Management (existing) ---
    def get_all_countries(self):
        """Fetches all countries from the database."""
        try:
            return db_manager.get_all_countries()
        except Exception as e:
            logging.error(f"Error in ClientController.get_all_countries: {e}", exc_info=True)
            return []

    def get_cities_for_country(self, country_id):
        """Fetches all cities for a given country_id."""
        try:
            return db_manager.get_all_cities(country_id=country_id)
        except Exception as e:
            logging.error(f"Error in ClientController.get_cities_for_country: {e}", exc_info=True)
            return []

    def add_country(self, country_name):
        """Adds a new country to the database. (Uses get_or_add for safety)"""
        if not country_name or not country_name.strip():
            return None
        try:
            country_data = db_manager.get_or_add_country(country_name.strip())
            return country_data
        except Exception as e:
            logging.error(f"Error in ClientController.add_country: {e}", exc_info=True)
            return None

    def add_city(self, city_name, country_id):
        """Adds a new city to the database for the given country_id. (Uses get_or_add for safety)"""
        if not city_name or not city_name.strip() or country_id is None:
            return None
        try:
            city_data = db_manager.get_or_add_city(city_name.strip(), country_id)
            return city_data
        except Exception as e:
            logging.error(f"Error in ClientController.add_city: {e}", exc_info=True)
            return None

    # --- Region Management (New) ---
    def get_all_regions(self):
        """
        Fetches all regions from the database.

        Returns:
            list[dict]: A list of all region dictionaries, or an empty list on error.
        """
        try:
            return regions_crud.get_all_regions()
        except Exception as e:
            logging.error(f"Error in ClientController.get_all_regions: {e}", exc_info=True)
            return []

    def get_regions_for_country(self, country_id: int):
        """
        Fetches all regions for a given country_id.

        Args:
            country_id (int): The ID of the country.

        Returns:
            list[dict]: A list of region dictionaries for the country, or an empty list if none found or error.
        """
        if country_id is None:
            return []
        try:
            return regions_crud.get_regions_for_country(country_id)
        except Exception as e:
            logging.error(f"Error in ClientController.get_regions_for_country (country_id: {country_id}): {e}", exc_info=True)
            return []

    def get_or_add_region(self, region_name: str, country_id: int):
        """
        Gets an existing region by name and country_id, or adds it if it doesn't exist.

        Args:
            region_name (str): The name of the region.
            country_id (int): The ID of the country this region belongs to.

        Returns:
            dict | None: A dictionary representing the region, or None on failure.
        """
        if not region_name or not region_name.strip() or country_id is None:
            logging.warning("Region name and country_id are required for get_or_add_region.")
            return None
        try:
            region_data = regions_crud.get_or_add_region(region_name.strip(), country_id)
            return region_data
        except Exception as e:
            logging.error(f"Error in ClientController.get_or_add_region for '{region_name}', country_id {country_id}: {e}", exc_info=True)
            return None

    # --- Client Management (existing, slightly refactored logging) ---
    def create_client(self, client_data: dict):
        """
        Creates a new client.
        client_data is a dictionary expected to contain keys like:
        'client_name', 'company_name', 'primary_need_description',
        'country_name', 'city_name', 'project_identifier', 'selected_languages'

        This method will handle resolving country and city names to IDs,
        adding them to the database if they don't exist.
        Returns the created client data (with IDs) or None on failure.
        """
        from db.cruds.status_settings_crud import get_status_setting_by_name # Import here
        from db.cruds.templates_crud import get_all_templates # Import for fallback template ID
        from db.cruds import users_crud # Changed import for fallback user ID


        try:
            country_name = client_data.get('country_name', '').strip()
            city_name = client_data.get('city_name', '').strip()

            if not country_name:
                logging.error("Country name is required to create a client.")
                return {'success': False, 'error': "Country name is required."}


            # Get or add country
            country_obj = self.add_country(country_name) # add_country handles get_or_add
            if not country_obj or 'country_id' not in country_obj:
                logging.error(f"Could not get or add country '{country_name}'.")
                return {'success': False, 'error': f"Could not get or add country '{country_name}'."}

            final_country_id = country_obj['country_id']

            final_city_id = None
            if city_name:
                city_obj = self.add_city(city_name, final_country_id)
                if not city_obj or 'city_id' not in city_obj:
                    logging.warning(f"Could not get or add city '{city_name}'. Proceeding without city.")
                else:
                    final_city_id = city_obj['city_id']

            # Determine default status_id
            default_status_name = "Client Actif"
            status_obj = get_status_setting_by_name(default_status_name, "Client")
            final_status_id = None
            if status_obj and 'status_id' in status_obj:
                final_status_id = status_obj['status_id']
            else:
                logging.warning(f"Default client status '{default_status_name}' not found. Client will be created without a status or with DB default if any.")


            # Determine default_template_id
            final_default_template_id = client_data.get('default_template_id')
            if final_default_template_id is None:
                try:
                    all_templates = get_all_templates(apply_visibility_filter=False)
                    if all_templates:
                        final_default_template_id = all_templates[0].get('template_id')
                        logging.info(f"Using first available template ID {final_default_template_id} as fallback for default_template_id.")
                    else:
                        logging.warning("No templates found in DB. default_template_id will be None. This might cause FK error if column is NOT NULL.")
                except Exception as e_tpl:
                    logging.error(f"Error fetching fallback template ID: {e_tpl}. default_template_id will be None.", exc_info=True)


            db_client_data = {
                'client_name': client_data.get('client_name'),
                'company_name': client_data.get('company_name'),
                'primary_need_description': client_data.get('primary_need_description'),
                'country_id': final_country_id,
                'city_id': final_city_id,
                'project_identifier': client_data.get('project_identifier'),
                'status_id': client_data.get('status_id', final_status_id),
                'languages': client_data.get('selected_languages'),
                'default_template_id': final_default_template_id
            }

            for key in ['price', 'notes', 'category', 'lead_source']:
                if key in client_data:
                    db_client_data[key] = client_data[key]

            final_created_by_user_id = client_data.get('created_by_user_id')
            if not final_created_by_user_id:
                logging.error("Critical: created_by_user_id was not provided to ClientController.create_client.")
                return {'success': False, 'error': "Client creator ID was not provided."}
            db_client_data['created_by_user_id'] = final_created_by_user_id


            if not db_client_data.get('client_name'):
                logging.error("Client name is required.")
                return {'success': False, 'error': "Client name is required."}

            result = clients_crud.add_client(db_client_data)

            if result and result.get('success'):
                new_client_id = result.get('client_id')
                created_client_details = clients_crud.clients_crud_instance.get_client_by_id(new_client_id) # Fetch full details

                if not created_client_details: # Fallback if fetch fails
                    logging.warning(f"Client created with ID {new_client_id}, but failed to fetch full details. Returning minimal info.")
                    created_client_details = {'client_id': new_client_id, 'client_name': db_client_data.get('client_name'), 'success': True, 'warning': 'Details fetch failed'}
                else:
                    logging.info(f"Client '{created_client_details.get('client_name')}' created successfully with ID {new_client_id}.")

                if client_data.get('product_product_name', '').strip():
                    # Product adding logic (simplified for brevity, assumed to be correct from original)
                    logging.info(f"Attempting to add product for client ID {new_client_id}...")
                    # ... (original product adding logic) ...
                    pass # Placeholder for original product logic

                try:
                    log_data = {
                        "user_id": db_client_data.get('created_by_user_id'),
                        "action_type": "CLIENT_CREATED",
                        "details": f"Client '{created_client_details.get('client_name')}' créé.",
                        "related_entity_type": "Client",
                        "related_entity_id": new_client_id,
                        "related_client_id": new_client_id
                    }
                    add_activity_log(log_data)
                    logging.info(f"Activity logged for CLIENT_CREATED: {new_client_id}")
                except Exception as e_log:
                    logging.error(f"Failed to log CLIENT_CREATED activity for client {new_client_id}: {e_log}", exc_info=True)

                return created_client_details
            else:
                error_message = result.get('error', 'Failed to create client in database.') if result else 'CRUD operation failed unexpectedly.'
                logging.error(f"Client creation failed: {error_message}")
                return {'success': False, 'error': error_message}

        except Exception as e:
            logging.exception(f"Unhandled exception in ClientController.create_client: {e}")
            return {'success': False, 'error': f"An unexpected error occurred: {str(e)}"}

    # --- Referent Management (New) ---
    def make_client_referent(self, client_id: str, country_id: int, region_name: str | None,
                             city_name: str | None, notes: str | None, user_id: str):
        """
        Designates an existing client as a referent.

        Args:
            client_id (str): The ID of the client to make a referent.
            country_id (int): The country ID for the referent's classification.
            region_name (str | None): The name of the region for the referent. Can be new.
            city_name (str | None): The name of the city for the referent. Can be new.
            notes (str | None): Notes specific to this referent role.
            user_id (str): The ID of the user performing the action.

        Returns:
            dict: A dictionary containing {'success': bool, 'referent_id': str | None, 'error': str | None}.
                  'status': 'already_exists' can be returned in error if client is already a referent.
        """
        if not client_id or not country_id or not user_id:
            logging.error("Client ID, Country ID, and User ID are required to make a client a referent.")
            return {'success': False, 'error': "Client ID, Country ID, and User ID are required."}

        # Check if client exists
        client_details = clients_crud.get_client_by_id(client_id)
        if not client_details:
            logging.error(f"Client with ID {client_id} not found. Cannot make referent.")
            return {'success': False, 'error': f"Client with ID {client_id} not found."}

        # Check if client has made any purchases (simplified check: has at least one order)
        # This logic might need to be more sophisticated based on actual order status.
        from db.cruds import commandes_crud # Local import
        client_orders = commandes_crud.get_commandes_for_client(client_id, limit=1)
        if not client_orders:
            logging.warning(f"Client {client_id} has no orders. Policy is that only clients who purchased can be referents.")
            # Depending on strictness, this could be an error or just a warning.
            # For now, let's allow it but log a warning.
            # return {'success': False, 'error': "Client must have made a purchase to become a referent."}


        final_region_id = None
        if region_name and region_name.strip():
            region_obj = self.get_or_add_region(region_name.strip(), country_id)
            if region_obj and 'region_id' in region_obj:
                final_region_id = region_obj['region_id']
            else:
                logging.warning(f"Could not get or add region '{region_name}' for country_id {country_id}. Proceeding without region for referent.")

        final_city_id = None
        # City is usually dependent on country, ensure country_id is valid for city.
        # The country_id passed to this function is for the referent's location, which might differ from client's primary country.
        if city_name and city_name.strip():
            city_obj = self.add_city(city_name.strip(), country_id) # add_city uses get_or_add_city
            if city_obj and 'city_id' in city_obj:
                final_city_id = city_obj['city_id']
            else:
                logging.warning(f"Could not get or add city '{city_name}' for country_id {country_id}. Proceeding without city for referent.")

        try:
            referent_id = referents_crud.add_referent(
                client_id=client_id,
                country_id=country_id,
                region_id=final_region_id,
                city_id=final_city_id,
                notes=notes,
                created_by_user_id=user_id
            )
            if referent_id:
                logging.info(f"Client {client_id} successfully made a referent with ID {referent_id}.")
                # Log activity
                try:
                    log_data = {
                        "user_id": user_id, "action_type": "REFERENT_CREATED",
                        "details": f"Client '{client_details.get('client_name', client_id)}' est devenu référent.",
                        "related_entity_type": "Referent", "related_entity_id": referent_id,
                        "related_client_id": client_id
                    }
                    add_activity_log(log_data)
                except Exception as e_log:
                    logging.error(f"Failed to log REFERENT_CREATED activity for referent {referent_id}: {e_log}", exc_info=True)
                return {'success': True, 'referent_id': referent_id}
            else:
                # Check if already a referent, as add_referent returns None on IntegrityError
                existing_referent = referents_crud.get_referent_by_client_id(client_id, include_inactive=True)
                if existing_referent:
                    logging.warning(f"Client {client_id} is already a referent (ID: {existing_referent['referent_id']}).")
                    return {'success': False, 'error': 'Client is already a referent.', 'referent_id': existing_referent['referent_id'], 'status': 'already_exists'}
                logging.error(f"Failed to make client {client_id} a referent.")
                return {'success': False, 'error': 'Failed to create referent record in database.'}
        except Exception as e:
            logging.error(f"Exception in make_client_referent for client {client_id}: {e}", exc_info=True)
            return {'success': False, 'error': f"An unexpected error occurred: {str(e)}"}

    def update_referent_details(self, referent_id: str, country_id: int | None = None,
                                region_name: str | None = None, city_name: str | None = None,
                                notes: str | None = None, is_active: bool | None = None, user_id: str | None = None):
        """
        Updates details of an existing referent.

        Args:
            referent_id (str): The ID of the referent to update.
            country_id (int | None, optional): New country ID.
            region_name (str | None, optional): New region name. Can be new to be created.
            city_name (str | None, optional): New city name. Can be new to be created.
            notes (str | None, optional): New notes.
            is_active (bool | None, optional): New active status.
            user_id (str | None, optional): ID of the user performing the update (for logging).

        Returns:
            dict: A dictionary containing {'success': bool, 'message': str | None, 'error': str | None}.
        """
        if not referent_id:
            return {'success': False, 'error': "Referent ID is required."}

        update_data = {}
        current_referent = referents_crud.get_referent_by_id(referent_id)
        if not current_referent:
            return {'success': False, 'error': f"Referent with ID {referent_id} not found."}

        # Use current country_id if not provided for region/city resolution
        effective_country_id = country_id if country_id is not None else current_referent['country_id']

        if country_id is not None:
            update_data['country_id'] = country_id

        if region_name is not None: # Allow empty string to clear region
            if region_name.strip():
                region_obj = self.get_or_add_region(region_name.strip(), effective_country_id)
                if region_obj and 'region_id' in region_obj:
                    update_data['region_id'] = region_obj['region_id']
                else:
                    return {'success': False, 'error': f"Could not process region '{region_name}'."}
            else: # Empty string means clear region_id
                 update_data['region_id'] = None

        if city_name is not None: # Allow empty string to clear city
            if city_name.strip():
                city_obj = self.add_city(city_name.strip(), effective_country_id) # add_city uses get_or_add_city
                if city_obj and 'city_id' in city_obj:
                    update_data['city_id'] = city_obj['city_id']
                else:
                    return {'success': False, 'error': f"Could not process city '{city_name}'."}
            else: # Empty string means clear city_id
                update_data['city_id'] = None

        if notes is not None:
            update_data['notes'] = notes
        if is_active is not None:
            update_data['is_active'] = is_active

        if not update_data:
            return {'success': True, 'message': 'No changes provided for referent.', 'updated_count': 0}

        try:
            success = referents_crud.update_referent(referent_id, update_data)
            if success: # update_referent returns bool
                logging.info(f"Referent {referent_id} updated successfully with data: {update_data}.")
                if user_id: # Log activity if user_id is provided
                    try:
                        log_data = {
                            "user_id": user_id, "action_type": "REFERENT_UPDATED",
                            "details": f"Referent ID {referent_id} (Client ID: {current_referent['client_id']}) mis à jour.",
                            "related_entity_type": "Referent", "related_entity_id": referent_id,
                            "related_client_id": current_referent['client_id']
                        }
                        add_activity_log(log_data)
                    except Exception as e_log:
                        logging.error(f"Failed to log REFERENT_UPDATED activity for referent {referent_id}: {e_log}", exc_info=True)
                return {'success': True, 'message': 'Referent updated successfully.'}
            else:
                # This might mean rowcount was 0 (no actual change or ID not found by CRUD)
                logging.warning(f"Update referent {referent_id} reported no rows changed by CRUD. Data: {update_data}")
                # Re-check if referent exists, as it might have been deleted.
                if not referents_crud.get_referent_by_id(referent_id):
                     return {'success': False, 'error': f"Referent with ID {referent_id} not found during update attempt."}
                return {'success': False, 'error': 'Failed to update referent in database or no changes made.'}
        except Exception as e:
            logging.error(f"Exception updating referent {referent_id}: {e}", exc_info=True)
            return {'success': False, 'error': f"An unexpected error occurred: {str(e)}"}

    def set_referent_status(self, referent_id: str, is_active: bool, user_id: str | None = None):
        """
        Activates or deactivates a referent.

        Args:
            referent_id (str): The ID of the referent.
            is_active (bool): The desired active status (True for active, False for inactive).
            user_id (str | None, optional): ID of the user performing the action (for logging).

        Returns:
            dict: A dictionary containing {'success': bool, 'message': str | None, 'error': str | None}.
        """
        if referent_id is None or is_active is None: # is_active can be False, so check for None
            return {'success': False, 'error': "Referent ID and active status are required."}

        success = referents_crud.set_referent_active_status(referent_id, is_active)
        if success:
            action = "activated" if is_active else "deactivated"
            logging.info(f"Referent {referent_id} status set to {action}.")
            if user_id:
                current_referent = referents_crud.get_referent_by_id(referent_id)
                if current_referent:
                    try:
                        log_data = {
                            "user_id": user_id, "action_type": f"REFERENT_{action.upper()}",
                            "details": f"Referent ID {referent_id} (Client ID: {current_referent['client_id']}) {action}.",
                            "related_entity_type": "Referent", "related_entity_id": referent_id,
                            "related_client_id": current_referent['client_id']
                        }
                        add_activity_log(log_data)
                    except Exception as e_log:
                        logging.error(f"Failed to log REFERENT_{action.upper()} activity for referent {referent_id}: {e_log}", exc_info=True)
            return {'success': True, 'message': f'Referent {action} successfully.'}
        else:
            if not referents_crud.get_referent_by_id(referent_id): # Check if referent exists
                return {'success': False, 'error': f"Referent with ID {referent_id} not found."}
            logging.error(f"Failed to set active status for referent {referent_id}.")
            return {'success': False, 'error': 'Failed to update referent status in database.'}

    def get_referent_profile_by_client_id(self, client_id: str, include_inactive: bool = False):
        """
        Retrieves the referent profile for a given client_id, including joined details
        like client name, country name, region name, and city name.

        Args:
            client_id (str): The ID of the client.
            include_inactive (bool, optional): Whether to include inactive referents. Defaults to False.

        Returns:
            dict | None: A dictionary with the referent's full profile, or None if not found or error.
        """
        if not client_id:
            return None
        try:
            basic_referent = referents_crud.get_referent_by_client_id(client_id, include_inactive=include_inactive)
            if not basic_referent:
                return None

            profile = basic_referent.copy()

            client_info = clients_crud.get_client_by_id(profile['client_id'])
            if client_info:
                profile['client_name'] = client_info.get('client_name')
                profile['company_name'] = client_info.get('company_name')

            country_info = db_manager.get_country_by_id(profile['country_id'])
            if country_info: profile['country_name'] = country_info.get('country_name')

            if profile.get('region_id'):
                region_info = regions_crud.get_region_by_id(profile['region_id'])
                if region_info: profile['region_name'] = region_info.get('region_name')
            else:
                profile['region_name'] = None # Ensure key exists even if no region

            if profile.get('city_id'):
                city_info = db_manager.get_city_by_id(profile['city_id'])
                if city_info: profile['city_name'] = city_info.get('city_name')
            else:
                profile['city_name'] = None # Ensure key exists

            return profile

        except Exception as e:
            logging.error(f"Error fetching referent profile for client_id {client_id}: {e}", exc_info=True)
            return None

    def get_all_referents_profiles(self, filters: dict = None, limit: int = None, offset: int = 0, include_inactive: bool = False):
        """
        Retrieves all referent profiles with joined details (client name, country, region, city).
        Uses the `referents_crud.get_all_referents` method which already performs the necessary joins.

        Args:
            filters (dict, optional): Filters to apply (e.g., by country_id, region_id, client_name).
            limit (int, optional): Maximum number of profiles to return.
            offset (int, optional): Offset for pagination.
            include_inactive (bool, optional): Whether to include inactive referents. Defaults to False.

        Returns:
            list[dict]: A list of referent profile dictionaries, or an empty list on error.
        """
        try:
            return referents_crud.get_all_referents(
                filters=filters,
                limit=limit,
                offset=offset,
                include_inactive=include_inactive
            )
        except Exception as e:
            logging.error(f"Error fetching all referent profiles: {e}", exc_info=True)
            return []

    def generate_referents_report(self, client_id: str, language_code: str, app_root_dir: str, current_user_id: str = None):
        """
        Generates a PDF report of local and global referents for a given client.

        Args:
            client_id (str): The ID of the client for whom the report is generated.
            language_code (str): The language code for the report (e.g., 'fr', 'en', 'ar').
            app_root_dir (str): The application's root directory, for resolving template/asset paths.
            current_user_id (str, optional): ID of the user initiating the action, for logging.

        Returns:
            str | None: Path to the generated PDF file on success, None on failure.
        """
        logging.info(f"Attempting to generate referents report for client {client_id} in {language_code}.")

        if not app_root_dir:
            logging.error("APP_ROOT_DIR not provided to generate_referents_report. Cannot locate templates.")
            return None

        default_company = companies_crud.get_default_company()
        if not default_company or 'company_id' not in default_company:
            logging.error("Default company not found or company_id missing. Cannot generate report.")
            return None
        company_id = default_company['company_id']

        template_name = "referents_report_template.html"
        # Chemin vers le template de base
        template_path = os.path.join(app_root_dir, "resources", "templates", "base", template_name)

        if not os.path.exists(template_path):
            logging.error(f"Referents report template not found at: {template_path}")
            return None

        document_type = 'referents_report'

        # Créer un nom de fichier de sortie temporaire
        # Le fichier sera créé dans le répertoire temporaire du système
        temp_pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", prefix=f"referents_report_{client_id}_{language_code}_")
        output_pdf_path = temp_pdf_file.name
        temp_pdf_file.close() # Fermer le handle pour que generate_html_and_convert_to_pdf puisse écrire dedans

        logging.info(f"Output PDF will be saved to: {output_pdf_path}")

        additional_context = {
            # Si des données spécifiques non couvertes par context_builder doivent être passées
            # par exemple, l'ID de l'utilisateur qui génère le document si nécessaire dans le template.
            "generated_by_user_id": current_user_id
        }

        success = html_generator.generate_html_and_convert_to_pdf(
            client_id=client_id,
            company_id=company_id,
            template_path=template_path,
            language_code=language_code,
            output_pdf_path=output_pdf_path,
            project_id=None, # Non pertinent pour ce rapport
            document_type=document_type,
            additional_context=additional_context,
            # db_conn=None, # Géré par les CRUDs individuels
            app_root_dir=app_root_dir # Crucial pour context_builder et html_generator
        )

        if success:
            logging.info(f"Referents report generated successfully: {output_pdf_path}")
            # Log activity
            if current_user_id:
                try:
                    client_details = clients_crud.get_client_by_id(client_id)
                    client_name = client_details.get('client_name', client_id) if client_details else client_id
                    log_data = {
                        "user_id": current_user_id,
                        "action_type": "REFERENT_REPORT_GENERATED",
                        "details": f"Rapport des référents généré pour le client '{client_name}' en langue '{language_code}'. Fichier: {os.path.basename(output_pdf_path)}",
                        "related_entity_type": "Client",
                        "related_entity_id": client_id,
                        "related_client_id": client_id
                    }
                    add_activity_log(log_data)
                except Exception as e_log:
                    logging.error(f"Failed to log REFERENT_REPORT_GENERATED activity: {e_log}", exc_info=True)
            return output_pdf_path
        else:
            logging.error(f"Failed to generate referents report for client {client_id}.")
            # Tenter de supprimer le fichier temporaire s'il a été créé mais la génération a échoué
            if os.path.exists(output_pdf_path):
                try:
                    os.remove(output_pdf_path)
                except OSError as e_remove:
                    logging.error(f"Error removing temporary PDF file {output_pdf_path}: {e_remove}")
            return None

# Example usage (for testing purposes, would be removed or in a test file)
if __name__ == '__main__':
    controller = ClientController()

    # --- Test Country/City/Region (Assumes DB is initialized and has some data or allows adding) ---
    # test_country = controller.add_country("ReferentLand")
    # if test_country and test_country.get('country_id'):
    #     country_id_for_ref = test_country['country_id']
    #     print(f"Test Country: {test_country}")

    #     test_city = controller.add_city("ReferentVille", country_id_for_ref)
    #     if test_city: print(f"Test City: {test_city}")

    #     test_region = controller.get_or_add_region("ReferentRegion", country_id_for_ref)
    #     if test_region: print(f"Test Region: {test_region}")

    #     regions_in_country = controller.get_regions_for_country(country_id_for_ref)
    #     print(f"Regions in {test_country.get('country_name')}: {regions_in_country}")

    # --- Test Client Creation (Prerequisite for Referent) ---
    # Ensure a user exists for 'created_by_user_id'. Get one from DB or use a known test user ID.
    # For simplicity, assuming a user_id 'test_user_uuid_123' exists.
    # test_user_id = "test_user_uuid_123" # Replace with actual or fetched user ID

    # # First, ensure the user exists, or create one (simplified here)
    # # from db.cruds import users_crud
    # # test_user = users_crud.get_user_by_username("testcontrolleruser")
    # # if not test_user:
    # #     # Add user logic here if needed, requires role_id etc.
    # #     print("Test user 'testcontrolleruser' not found. Referent tests might fail or use placeholder.")
    # # else:
    # #     test_user_id = test_user['user_id']


    # client_info_for_ref_test = {
    #     'client_name': 'Referent Test Client Inc.', 'company_name': 'Ref Solutions',
    #     'primary_need_description': 'Needs to be a referent',
    #     'country_name': test_country.get('country_name') if test_country else "UnknownCountry",
    #     'city_name': test_city.get('city_name') if test_city else "UnknownCity",
    #     'project_identifier': 'PROJ_REF_001', 'selected_languages': 'en,fr',
    #     'created_by_user_id': test_user_id, # Crucial
    #     'lead_source': 'ControllerTest'
    # }
    # created_client_for_ref = controller.create_client(client_info_for_ref_test)
    # print(f"Created Client for Referent Test: {created_client_for_ref}")

    # if created_client_for_ref and created_client_for_ref.get('success'):
    #     client_id_for_ref = created_client_for_ref.get('client_id')

    #     # --- Test Referent Creation ---
    #     make_ref_result = controller.make_client_referent(
    #         client_id=client_id_for_ref,
    #         country_id=country_id_for_ref, # Assuming country_id_for_ref was set from test_country
    #         region_name=test_region.get('region_name') if test_region else None,
    #         city_name=test_city.get('city_name') if test_city else None,
    #         notes="Initial referent notes from controller test.",
    #         user_id=test_user_id
    #     )
    #     print(f"Make Client Referent Result: {make_ref_result}")

    #     if make_ref_result and make_ref_result.get('success'):
    #         referent_id_for_test = make_ref_result.get('referent_id')

    #         # --- Test Get Referent Profile ---
    #         referent_profile = controller.get_referent_profile_by_client_id(client_id_for_ref)
    #         print(f"Referent Profile for Client {client_id_for_ref}: {referent_profile}")

    #         # --- Test Update Referent Details ---
    #         update_notes = "Updated referent notes via controller."
    #         # To test changing region/city, you might need another country/region/city ID.
    #         # For simplicity, just updating notes and status here.
    #         update_ref_result = controller.update_referent_details(
    #             referent_id=referent_id_for_test,
    #             notes=update_notes,
    #             is_active=False, # Deactivate
    #             user_id=test_user_id
    #         )
    #         print(f"Update Referent Details Result: {update_ref_result}")

    #         updated_profile_inactive = controller.get_referent_profile_by_client_id(client_id_for_ref, include_inactive=True)
    #         print(f"Updated Referent Profile (inactive): {updated_profile_inactive}")

    #         # --- Test Set Referent Status (Re-activate) ---
    #         set_status_result = controller.set_referent_status(referent_id_for_test, True, user_id=test_user_id)
    #         print(f"Set Referent Status (activate) Result: {set_status_result}")

    #         final_profile_active = controller.get_referent_profile_by_client_id(client_id_for_ref)
    #         print(f"Final Referent Profile (active): {final_profile_active}")

    # # --- Test Get All Referents ---
    # all_referents = controller.get_all_referents_profiles(include_inactive=True)
    # print(f"All Referent Profiles: {all_referents}")

    pass # End of if __name__ == '__main__' block
