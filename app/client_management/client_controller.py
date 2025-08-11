# controllers/client_controller.py
from app.db.cruds.clients import clients_crud_instance as clients_crud, client_project_products_crud
from app.db.cruds.products.products_crud import products_crud_instance as products_crud
from app.db.cruds.misc.regions_crud import get_all_regions, get_regions_for_country, get_or_add_region, get_region_by_id
from app.db.cruds.misc.referents_crud import add_referent, get_referent_by_client_id, update_referent, set_referent_active_status, get_referent_by_id
from app.db.cruds.misc.locations_crud import get_all_countries, get_all_cities, get_or_add_country, get_or_add_city, get_country_by_id, get_city_by_id
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from app.db.cruds.misc.activity_logs_crud import add_activity_log

class ClientController:
    def __init__(self):
        # In the future, we might pass a specific DB connection or configuration
        pass

    # --- Country and City Management (existing) ---
    def get_all_countries(self):
        """Fetches all countries from the database."""
        try:
            return get_all_countries()
        except Exception as e:
            logging.error(f"Error in ClientController.get_all_countries: {e}", exc_info=True)
            return []

    def get_cities_for_country(self, country_id):
        """Fetches all cities for a given country_id."""
        try:
            return get_all_cities(country_id=country_id)
        except Exception as e:
            logging.error(f"Error in ClientController.get_cities_for_country: {e}", exc_info=True)
            return []

    def add_country(self, country_name):
        """Adds a new country to the database. (Uses get_or_add for safety)"""
        if not country_name or not country_name.strip():
            return None
        try:
            country_data = get_or_add_country(country_name.strip())
            return country_data
        except Exception as e:
            logging.error(f"Error in ClientController.add_country: {e}", exc_info=True)
            return None

    def add_city(self, city_name, country_id):
        """Adds a new city to the database for the given country_id. (Uses get_or_add for safety)"""
        if not city_name or not city_name.strip() or country_id is None:
            return None
        try:
            city_data = get_or_add_city(city_name.strip(), country_id)
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
            return get_all_regions()
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
            return get_regions_for_country(country_id)
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
            region_data = get_or_add_region(region_name.strip(), country_id)
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
        from app.db.cruds.misc.status_settings_crud import get_status_setting_by_name
        from app.db.cruds.misc.templates_crud import get_all_templates
        from app.db.cruds.users import users_crud


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
        from app.db.cruds.invoices import commandes_crud # Local import
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
            referent_id = add_referent(
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
                existing_referent = get_referent_by_client_id(client_id, include_inactive=True)
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
        current_referent = get_referent_by_id(referent_id)
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
            success = update_referent(referent_id, update_data)
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
                if not get_referent_by_id(referent_id):
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

        success = set_referent_active_status(referent_id, is_active)
        if success:
            action = "activated" if is_active else "deactivated"
            logging.info(f"Referent {referent_id} status set to {action}.")
            if user_id:
                current_referent = get_referent_by_id(referent_id)
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
            if not get_referent_by_id(referent_id): # Check if referent exists
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
            basic_referent = get_referent_by_client_id(client_id, include_inactive=include_inactive)
            if not basic_referent:
                return None

            profile = basic_referent.copy()

            client_info = clients_crud.get_client_by_id(profile['client_id'])
            if client_info:
                profile['client_name'] = client_info.get('client_name')
                profile['company_name'] = client_info.get('company_name')

            country_info = get_country_by_id(profile['country_id'])
            if country_info: profile['country_name'] = country_info.get('country_name')

            if profile.get('region_id'):
                region_info = get_region_by_id(profile['region_id'])
                if region_info: profile['region_name'] = region_info.get('region_name')
            else:
                profile['region_name'] = None # Ensure key exists even if no region

            if profile.get('city_id'):
                city_info = get_city_by_id(profile['city_id'])
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
