# controllers/client_controller.py
from app.db.connection import get_db_connection
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
        db_session = None
        try:
            db_session = get_db_connection()
            return get_all_countries(db_session)
        except Exception as e:
            logging.error(f"Error in ClientController.get_all_countries: {e}", exc_info=True)
            return []
        finally:
            if db_session:
                db_session.close()

    def get_cities_for_country(self, country_id):
        """Fetches all cities for a given country_id."""
        db_session = None
        try:
            db_session = get_db_connection()
            return get_all_cities(db_session, country_id=country_id)
        except Exception as e:
            logging.error(f"Error in ClientController.get_cities_for_country: {e}", exc_info=True)
            return []
        finally:
            if db_session:
                db_session.close()

    def add_country(self, country_name):
        """Adds a new country to the database. (Uses get_or_add for safety)"""
        if not country_name or not country_name.strip():
            return None
        db_session = None
        try:
            db_session = get_db_connection()
            country_data = get_or_add_country(db_session, country_name.strip())
            return country_data
        except Exception as e:
            logging.error(f"Error in ClientController.add_country: {e}", exc_info=True)
            return None
        finally:
            if db_session:
                db_session.close()

    def add_city(self, city_name, country_id):
        """Adds a new city to the database for the given country_id. (Uses get_or_add for safety)"""
        if not city_name or not city_name.strip() or country_id is None:
            return None
        db_session = None
        try:
            db_session = get_db_connection()
            city_data = get_or_add_city(db_session, city_name.strip(), country_id)
            return city_data
        except Exception as e:
            logging.error(f"Error in ClientController.add_city: {e}", exc_info=True)
            return None
        finally:
            if db_session:
                db_session.close()

    # --- Region Management (New) ---
    def get_all_regions(self):
        db_session = None
        try:
            db_session = get_db_connection()
            return get_all_regions(db_session)
        except Exception as e:
            logging.error(f"Error in ClientController.get_all_regions: {e}", exc_info=True)
            return []
        finally:
            if db_session:
                db_session.close()

    def get_regions_for_country(self, country_id: int):
        if country_id is None:
            return []
        db_session = None
        try:
            db_session = get_db_connection()
            return get_regions_for_country(db_session, country_id)
        except Exception as e:
            logging.error(f"Error in ClientController.get_regions_for_country (country_id: {country_id}): {e}", exc_info=True)
            return []
        finally:
            if db_session:
                db_session.close()

    def get_or_add_region(self, region_name: str, country_id: int):
        if not region_name or not region_name.strip() or country_id is None:
            logging.warning("Region name and country_id are required for get_or_add_region.")
            return None
        db_session = None
        try:
            db_session = get_db_connection()
            region_data = get_or_add_region(db_session, region_name.strip(), country_id)
            return region_data
        except Exception as e:
            logging.error(f"Error in ClientController.get_or_add_region for '{region_name}', country_id {country_id}: {e}", exc_info=True)
            return None
        finally:
            if db_session:
                db_session.close()

    # --- Client Management (existing, slightly refactored logging) ---
    def create_client(self, client_data: dict):
        from app.db.cruds.misc.status_settings_crud import get_status_setting_by_name
        from app.db.cruds.misc.templates_crud import get_all_templates
        from app.db.cruds.users import users_crud

        db_session = None
        try:
            db_session = get_db_connection()
            country_name = client_data.get('country_name', '').strip()
            city_name = client_data.get('city_name', '').strip()

            if not country_name:
                logging.error("Country name is required to create a client.")
                return {'success': False, 'error': "Country name is required."}

            country_obj = self.add_country(country_name)
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

            default_status_name = "Client Actif"
            status_obj = get_status_setting_by_name(db_session, default_status_name, "Client")
            final_status_id = status_obj.get('status_id') if status_obj else None
            if not final_status_id:
                logging.warning(f"Default client status '{default_status_name}' not found.")

            final_default_template_id = client_data.get('default_template_id')
            if final_default_template_id is None:
                all_templates = get_all_templates(db_session, apply_visibility_filter=False)
                if all_templates:
                    final_default_template_id = all_templates[0].get('template_id')
                else:
                    logging.warning("No templates found in DB.")

            db_client_data = {
                'client_name': client_data.get('client_name'),
                'company_name': client_data.get('company_name'),
                'primary_need_description': client_data.get('primary_need_description'),
                'country_id': final_country_id,
                'city_id': final_city_id,
                'project_identifier': client_data.get('project_identifier'),
                'status_id': client_data.get('status_id', final_status_id),
                'languages': client_data.get('selected_languages'),
                'default_template_id': final_default_template_id,
                'created_by_user_id': client_data.get('created_by_user_id')
            }

            for key in ['price', 'notes', 'category', 'lead_source']:
                if key in client_data:
                    db_client_data[key] = client_data[key]

            if not db_client_data.get('client_name') or not db_client_data.get('created_by_user_id'):
                return {'success': False, 'error': "Client name and creator ID are required."}

            result = clients_crud.add_client(db_session, db_client_data)

            if result and result.get('success'):
                new_client_id = result.get('client_id')
                created_client_details = clients_crud.get_client_by_id(db_session, new_client_id)

                log_data = {
                    "user_id": db_client_data.get('created_by_user_id'),
                    "action_type": "CLIENT_CREATED",
                    "details": f"Client '{created_client_details.get('client_name')}' créé.",
                    "related_entity_type": "Client", "related_entity_id": new_client_id,
                    "related_client_id": new_client_id
                }
                add_activity_log(db_session, log_data)
                return created_client_details
            else:
                error_message = result.get('error', 'Failed to create client.') if result else 'CRUD failed.'
                return {'success': False, 'error': error_message}

        except Exception as e:
            logging.exception(f"Unhandled exception in ClientController.create_client: {e}")
            return {'success': False, 'error': f"An unexpected error occurred: {str(e)}"}
        finally:
            if db_session:
                db_session.close()

    def make_client_referent(self, client_id: str, country_id: int, region_name: str | None,
                             city_name: str | None, notes: str | None, user_id: str):
        if not all([client_id, country_id, user_id]):
            return {'success': False, 'error': "Client ID, Country ID, and User ID are required."}

        db_session = None
        try:
            db_session = get_db_connection()
            from app.db.cruds.invoices import commandes_crud

            client_details = clients_crud.get_client_by_id(db_session, client_id)
            if not client_details:
                return {'success': False, 'error': f"Client with ID {client_id} not found."}

            client_orders = commandes_crud.get_commandes_for_client(db_session, client_id, limit=1)
            if not client_orders:
                logging.warning(f"Client {client_id} has no orders but is being made a referent.")

            final_region_id = self.get_or_add_region(region_name.strip(), country_id).get('region_id') if region_name and region_name.strip() else None
            final_city_id = self.add_city(city_name.strip(), country_id).get('city_id') if city_name and city_name.strip() else None

            referent_id = add_referent(
                db=db_session, client_id=client_id, country_id=country_id,
                region_id=final_region_id, city_id=final_city_id,
                notes=notes, created_by_user_id=user_id
            )
            if referent_id:
                log_data = {"user_id": user_id, "action_type": "REFERENT_CREATED", "details": f"Client '{client_details.get('client_name', client_id)}' est devenu référent.", "related_entity_type": "Referent", "related_entity_id": referent_id, "related_client_id": client_id}
                add_activity_log(db_session, log_data)
                return {'success': True, 'referent_id': referent_id}
            else:
                existing_referent = get_referent_by_client_id(db_session, client_id, include_inactive=True)
                if existing_referent:
                    return {'success': False, 'error': 'Client is already a referent.', 'referent_id': existing_referent['referent_id'], 'status': 'already_exists'}
                return {'success': False, 'error': 'Failed to create referent record.'}
        except Exception as e:
            logging.error(f"Exception in make_client_referent for client {client_id}: {e}", exc_info=True)
            return {'success': False, 'error': f"An unexpected error occurred: {str(e)}"}
        finally:
            if db_session:
                db_session.close()

    def update_referent_details(self, referent_id: str, country_id: int | None = None,
                                region_name: str | None = None, city_name: str | None = None,
                                notes: str | None = None, is_active: bool | None = None, user_id: str | None = None):
        if not referent_id:
            return {'success': False, 'error': "Referent ID is required."}

        db_session = None
        try:
            db_session = get_db_connection()
            update_data = {}
            current_referent = get_referent_by_id(db_session, referent_id)
            if not current_referent:
                return {'success': False, 'error': f"Referent with ID {referent_id} not found."}

            effective_country_id = country_id if country_id is not None else current_referent['country_id']
            if country_id is not None: update_data['country_id'] = country_id
            if notes is not None: update_data['notes'] = notes
            if is_active is not None: update_data['is_active'] = is_active

            if region_name is not None:
                update_data['region_id'] = self.get_or_add_region(region_name.strip(), effective_country_id).get('region_id') if region_name.strip() else None
            if city_name is not None:
                update_data['city_id'] = self.add_city(city_name.strip(), effective_country_id).get('city_id') if city_name.strip() else None

            if not update_data:
                return {'success': True, 'message': 'No changes provided.'}

            success = update_referent(db_session, referent_id, update_data)
            if success:
                if user_id:
                    log_data = {"user_id": user_id, "action_type": "REFERENT_UPDATED", "details": f"Referent ID {referent_id} mis à jour.", "related_entity_type": "Referent", "related_entity_id": referent_id, "related_client_id": current_referent['client_id']}
                    add_activity_log(db_session, log_data)
                return {'success': True, 'message': 'Referent updated successfully.'}
            else:
                return {'success': False, 'error': 'Failed to update referent.'}
        except Exception as e:
            logging.error(f"Exception updating referent {referent_id}: {e}", exc_info=True)
            return {'success': False, 'error': f"An unexpected error occurred: {str(e)}"}
        finally:
            if db_session:
                db_session.close()

    def set_referent_status(self, referent_id: str, is_active: bool, user_id: str | None = None):
        if referent_id is None or is_active is None:
            return {'success': False, 'error': "Referent ID and active status are required."}

        db_session = None
        try:
            db_session = get_db_connection()
            success = set_referent_active_status(db_session, referent_id, is_active)
            if success:
                action = "activated" if is_active else "deactivated"
                if user_id:
                    current_referent = get_referent_by_id(db_session, referent_id)
                    if current_referent:
                        log_data = {"user_id": user_id, "action_type": f"REFERENT_{action.upper()}", "details": f"Referent {referent_id} {action}.", "related_entity_type": "Referent", "related_entity_id": referent_id, "related_client_id": current_referent['client_id']}
                        add_activity_log(db_session, log_data)
                return {'success': True, 'message': f'Referent {action} successfully.'}
            else:
                return {'success': False, 'error': 'Failed to update referent status.'}
        except Exception as e:
            logging.error(f"Exception in set_referent_status for referent {referent_id}: {e}", exc_info=True)
            return {'success': False, 'error': f"An unexpected error occurred: {str(e)}"}
        finally:
            if db_session:
                db_session.close()

    def get_referent_profile_by_client_id(self, client_id: str, include_inactive: bool = False):
        if not client_id: return None
        db_session = None
        try:
            db_session = get_db_connection()
            basic_referent = get_referent_by_client_id(db_session, client_id, include_inactive=include_inactive)
            if not basic_referent: return None

            profile = basic_referent.copy()
            client_info = clients_crud.get_client_by_id(db_session, profile['client_id'])
            if client_info:
                profile['client_name'] = client_info.get('client_name')
                profile['company_name'] = client_info.get('company_name')

            country_info = get_country_by_id(db_session, profile['country_id'])
            if country_info: profile['country_name'] = country_info.get('country_name')

            if profile.get('region_id'):
                region_info = get_region_by_id(db_session, profile['region_id'])
                if region_info: profile['region_name'] = region_info.get('region_name')

            if profile.get('city_id'):
                city_info = get_city_by_id(db_session, profile['city_id'])
                if city_info: profile['city_name'] = city_info.get('city_name')

            return profile
        except Exception as e:
            logging.error(f"Error fetching referent profile for client_id {client_id}: {e}", exc_info=True)
            return None
        finally:
            if db_session:
                db_session.close()

    def get_client_by_id_for_dialog(self, client_id: str):
        if not client_id: return None
        db_session = None
        try:
            db_session = get_db_connection()
            return clients_crud.get_client_by_id(db_session, client_id)
        except Exception as e:
            logging.error(f"Error in get_client_by_id_for_dialog for client ID {client_id}: {e}", exc_info=True)
            return None
        finally:
            if db_session:
                db_session.close()
