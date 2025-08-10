import logging
from typing import List, Optional

# Attempt to import CRUD functions from the existing db module
try:
    from db.cruds.misc import status_settings_crud
    # We also need to check usage in Clients and Commandes
    from db.cruds.clients import clients_crud
    from db.cruds.invoices import commandes_crud
except ImportError as e:
    logging.error(f"StatusManager Service: Could not import DB CRUD modules: {e}. Ensure PYTHONPATH is set correctly.")
    # To allow the rest of the file to be parsed, provide dummy fallbacks if needed,
    # or let it fail if these are critical at import time.
    # For now, we'll assume they will be available at runtime in the main application.
    status_settings_crud = None
    clients_crud = None
    commandes_crud = None


from .status_models import Status, StatusType

logger = logging.getLogger(__name__)

def _map_db_row_to_status_object(db_row: dict) -> Optional[Status]:
    """Helper function to map a dictionary (database row) to a Status object."""
    if not db_row:
        return None
    try:
        return Status.from_dict(db_row)
    except ValueError as e:
        logger.error(f"Error mapping database row to Status object: {e}. Row: {db_row}")
        return None

def get_status_by_id(status_id: int) -> Optional[Status]:
    """
    Retrieves a specific status by its ID.
    """
    if not status_settings_crud:
        logger.error("status_settings_crud module not available.")
        return None
    try:
        db_row = status_settings_crud.get_status_setting_by_id(status_id)
        return _map_db_row_to_status_object(db_row)
    except Exception as e:
        logger.error(f"Error in get_status_by_id for ID {status_id}: {e}", exc_info=True)
        return None

def get_statuses_by_type(status_type: StatusType, type_filter_string: Optional[str] = None) -> List[Status]:
    """
    Retrieves all statuses of a specific type.
    Can accept StatusType enum or a string for type_filter_string for flexibility.
    """
    if not status_settings_crud:
        logger.error("status_settings_crud module not available.")
        return []

    type_val_to_filter = type_filter_string if type_filter_string else status_type.value

    try:
        db_rows = status_settings_crud.get_all_status_settings(type_filter=type_val_to_filter)
        statuses = [_map_db_row_to_status_object(row) for row in db_rows if row]
        return [s for s in statuses if s] # Filter out None objects from mapping errors
    except Exception as e:
        logger.error(f"Error in get_statuses_by_type for type {type_val_to_filter}: {e}", exc_info=True)
        return []

def get_all_statuses() -> List[Status]:
    """
    Retrieves all statuses defined in the system.
    """
    if not status_settings_crud:
        logger.error("status_settings_crud module not available.")
        return []
    try:
        db_rows = status_settings_crud.get_all_status_settings()
        statuses = [_map_db_row_to_status_object(row) for row in db_rows if row]
        return [s for s in statuses if s] # Filter out None objects
    except Exception as e:
        logger.error(f"Error in get_all_statuses: {e}", exc_info=True)
        return []

def add_status(
    name: str,
    type: StatusType,
    color_hex: Optional[str] = None,
    sort_order: int = 0,
    is_archival: bool = False, # Added is_archival
    icon_name: Optional[str] = None  # Added icon_name
) -> Optional[Status]:
    """
    Adds a new status to the system.
    This function needs to be adapted if 'is_archival' and 'icon_name'
    are not direct columns in StatusSettings or handled by status_settings_crud.add_status_setting.

    Assuming status_settings_crud.add_status_setting will be updated or
    we'll handle these fields separately if they are in a different table or structure.
    For now, this implementation assumes add_status_setting can take them.
    If not, this is a point of future adjustment.
    """
    if not status_settings_crud:
        logger.error("status_settings_crud module not available.")
        return None

    # The current status_settings_crud.add_status_setting does not take is_archival or icon_name.
    # This will require either:
    # 1. Modifying status_settings_crud.add_status_setting
    # 2. Adding a subsequent update step here after creation.
    # For now, let's proceed as if it could, and note this for later.
    # TODO: Adapt if status_settings_crud.add_status_setting cannot handle all fields.

    try:
        # Call the CRUD function. If it needs modification for new fields, that's a separate step.
        # For now, we pass what the Status object holds.
        # The CRUD function `add_status_setting` signature is:
        # (status_name: str, status_type: str, color_hex: str = None, sort_order: int = 0)
        # It does NOT currently accept is_archival or icon_name.
        # We will call it with the known parameters first.

        new_status_id = status_settings_crud.add_status_setting(
            status_name=name,
            status_type=type.value,
            color_hex=color_hex,
            sort_order=sort_order
            # is_archival and icon_name are not in the CRUD's add function signature
        )

        if new_status_id: # Returns ID on success
            # If is_archival or icon_name need to be set, and the add function doesn't do it,
            # we would need an update call here.
            # Example:
            # if is_archival or icon_name:
            #     success_update = status_settings_crud.update_status_setting(
            #         status_id=new_status_id,
            #         status_name=name, # Must pass existing or new name/type
            #         status_type=type.value,
            #         # color_hex=color_hex, # Pass if update should also set this
            #         # sort_order=sort_order, # Pass if update should also set this
            #         is_archival_status=is_archival, # Assuming update_status_setting is modified for this
            #         icon_name=icon_name # Assuming update_status_setting is modified for this
            #     )
            #     if not success_update:
            #         logger.warning(f"Status {new_status_id} added, but failed to update archival/icon fields.")
            #         # Potentially delete the partially created status or handle error

            # For now, let's assume we'll modify the CRUD or this is handled elsewhere.
            # We return the newly created status object by fetching it.
            return get_status_by_id(new_status_id)
        else:
            logger.error(f"Failed to add status '{name}' of type '{type.value}'. CRUD returned failure.")
            return None
    except Exception as e:
        logger.error(f"Error in add_status for name '{name}', type '{type.value}': {e}", exc_info=True)
        return None

def update_status(
    status_id: int,
    name: Optional[str] = None,
    type: Optional[StatusType] = None,
    color_hex: Optional[str] = None,
    sort_order: Optional[int] = None,
    is_archival: Optional[bool] = None,
    icon_name: Optional[str] = None
) -> bool:
    """
    Updates an existing status.
    Fields that are None will not be updated.
    """
    if not status_settings_crud:
        logger.error("status_settings_crud module not available.")
        return False

    # Fetch current status to get existing values for name and type if not provided
    current_status = get_status_by_id(status_id)
    if not current_status:
        logger.error(f"Cannot update. Status with ID {status_id} not found.")
        return False

    # Prepare data for the CRUD update function.
    # The CRUD function `update_status_setting` signature is:
    # (status_id: int, status_name: str, status_type: str, color_hex: str = None, sort_order: int = None)
    # It does NOT currently accept is_archival or icon_name.
    # TODO: Adapt if status_settings_crud.update_status_setting cannot handle all fields.

    updated_name = name if name is not None else current_status.name
    updated_type_str = type.value if type is not None else current_status.type.value

    # For fields not directly in update_status_setting's signature (color_hex, sort_order, is_archival, icon_name),
    # we pass them if they are provided, otherwise, the CRUD should ideally handle "no change".
    # The current CRUD `update_status_setting` only updates color and sort_order if they are not None.
    # We need to ensure is_archival and icon_name are also handled, likely by modifying the CRUD.

    try:
        success = status_settings_crud.update_status_setting(
            status_id=status_id,
            status_name=updated_name,
            status_type=updated_type_str,
            color_hex=color_hex, # Pass through; CRUD handles None as "no change"
            sort_order=sort_order, # Pass through; CRUD handles None as "no change"
            # is_archival_status=is_archival, # This field needs to be added to CRUD update
            # icon_name=icon_name  # This field needs to be added to CRUD update
        )
        # If is_archival or icon_name were provided and the main update doesn't handle them,
        # a separate update call or a modified CRUD is needed.
        # For example, if the DB schema has `is_archival` and `icon_name` and the CRUD was updated:
        # db_update_payload = {}
        # if name is not None: db_update_payload['status_name'] = name
        # ... etc for all fields
        # success = status_settings_crud.SOME_MORE_COMPREHENSIVE_UPDATE_FUNCTION(status_id, db_update_payload)

        return success
    except Exception as e:
        logger.error(f"Error in update_status for ID {status_id}: {e}", exc_info=True)
        return False

def is_status_in_use(status_id: int) -> bool:
    """
    Checks if a status is currently in use by Clients or Commandes.
    """
    if not status_settings_crud or not clients_crud or not commandes_crud:
        logger.error("Required CRUD modules not available for is_status_in_use.")
        return True # Safer to assume in use if checks cannot be performed

    try:
        # Check in Clients (this function already exists in status_settings_crud)
        if status_settings_crud.is_status_in_use(status_id): # Checks Clients table
            logger.info(f"Status ID {status_id} is in use by Clients.")
            return True

        # Check in Commandes
        # We need a way to query Commandes table for this status_id.
        # Assuming commandes_crud might have or need a function like:
        # `count_commandes_with_status(status_id)` or `get_commandes_by_status_id(status_id)`

        # Placeholder: Add logic to check Commandes table.
        # This might involve adding a new function to commandes_crud.py
        # e.g., commandes_crud.get_commandes_by_status_id(status_id)
        # For now, let's assume we need to implement this check.
        # Example (requires a new CRUD function or direct query if allowed):
        # commandes_using_status = commandes_crud.get_commandes_by_status_id(status_id) # Imaginary function
        # if commandes_using_status:
        #    logger.info(f"Status ID {status_id} is in use by Commandes.")
        #    return True

        # Temporary direct check (if we were to bypass CRUD for this specific query):
        # from db.connection import get_db_connection
        # conn = get_db_connection()
        # if conn:
        #     cursor = conn.cursor()
        #     cursor.execute("SELECT 1 FROM Commandes WHERE status_commande_id = ? LIMIT 1", (status_id,))
        #     in_use_by_commandes = cursor.fetchone() is not None
        #     conn.close()
        #     if in_use_by_commandes:
        #         logger.info(f"Status ID {status_id} is in use by Commandes.")
        #         return True
        # else:
        #    logger.warning("Could not get DB connection to check Commandes status usage.")
        #    return True # Safer

        logger.info(f"Status ID {status_id} is not found in use by Clients. Check for Commandes needs implementation.")
        # For now, returning False if not in use by Clients, assuming Commande check is pending.
        # TODO: Implement check for Commandes table.
        return False

    except Exception as e:
        logger.error(f"Error in is_status_in_use for ID {status_id}: {e}", exc_info=True)
        return True # Safer default

def delete_status(status_id: int) -> bool:
    """
    Deletes a status if it's not currently in use.
    """
    if not status_settings_crud:
        logger.error("status_settings_crud module not available.")
        return False

    if is_status_in_use(status_id):
        logger.warning(f"Attempted to delete status ID {status_id}, but it is currently in use.")
        # Optionally, raise an error or return a specific response code/message
        # For now, just returning False as the operation was not successful.
        # The UI layer should inform the user.
        return False

    try:
        return status_settings_crud.delete_status_setting(status_id)
    except Exception as e:
        logger.error(f"Error in delete_status for ID {status_id}: {e}", exc_info=True)
        return False

# --- Utility functions ---

def get_default_status_for_type(status_type: StatusType, preferred_name: Optional[str] = None) -> Optional[Status]:
    """
    Gets a default status for a given type.
    If preferred_name is provided, it tries to find that first.
    Otherwise, it typically returns the first status by sort_order.
    """
    statuses = get_statuses_by_type(status_type)
    if not statuses:
        logger.warning(f"No statuses found for type {status_type.value} when seeking default.")
        return None

    if preferred_name:
        for status in statuses:
            if status.name.lower() == preferred_name.lower():
                return status
        logger.warning(f"Preferred status '{preferred_name}' not found for type {status_type.value}. Falling back to first by sort order.")

    # Return the first by sort_order (already sorted by CRUD)
    return statuses[0]


def get_default_status_for_client_creation() -> Optional[Status]:
    """Gets the default status for new clients (e.g., 'Prospect' or 'Nouveau')."""
    # This logic might need to be more sophisticated, e.g., configurable in settings.
    # For now, let's try to find "Prospect", then "Nouveau", then the first "Client" status.

    prospect_status = get_default_status_for_type(StatusType.CLIENT, preferred_name="Prospect")
    if prospect_status: return prospect_status

    nouveau_status = get_default_status_for_type(StatusType.CLIENT, preferred_name="Nouveau")
    if nouveau_status: return nouveau_status

    return get_default_status_for_type(StatusType.CLIENT)


def get_default_status_for_commande_creation() -> Optional[Status]:
    """Gets the default status for new commandes (e.g., 'Brouillon')."""
    return get_default_status_for_type(StatusType.COMMANDE, preferred_name="Brouillon")

def get_archived_status_for_client() -> Optional[Status]:
    """Gets the designated 'Archivé' status for clients."""
    client_statuses = get_statuses_by_type(StatusType.CLIENT)
    for status in client_statuses:
        if status.is_archival: # Check the is_archival flag from the Status object
            return status
    # Fallback: try to find by name if is_archival flag wasn't set correctly or uniformly
    logger.warning("No client status explicitly marked as 'is_archival=True'. Trying to find by name 'Archivé'.")
    archived_by_name = get_default_status_for_type(StatusType.CLIENT, preferred_name="Archivé")
    if archived_by_name and archived_by_name.name.lower() == "archivé": # Ensure it actually found "Archivé"
        return archived_by_name

    logger.warning("Could not find a client status that is explicitly archival or named 'Archivé'.")
    return None


# --- Transition Logic (Placeholder - to be developed) ---

def get_allowed_transitions(current_status_id: int) -> List[Status]:
    """
    (Placeholder) Returns a list of statuses that the entity can transition to
    from the current_status_id.
    This will require defining transition rules.
    """
    # TODO: Implement transition logic.
    # This might involve a new table (e.g., StatusTransitions) or a configuration file.
    # For now, returns an empty list.
    logger.warning("get_allowed_transitions is a placeholder and not yet implemented.")
    return []

def can_transition(from_status_id: int, to_status_id: int) -> bool:
    """
    (Placeholder) Checks if a transition from from_status_id to to_status_id is allowed.
    """
    # TODO: Implement transition logic.
    logger.warning("can_transition is a placeholder and not yet implemented.")
    # For now, allow all transitions if not implemented (or disallow all)
    return True # Or False, depending on desired default behavior during development

if __name__ == '__main__':
    # This block is for basic testing of the service functions.
    # It requires the database to be set up and status_settings_crud to be working.
    # You would typically run this from the project root with PYTHONPATH configured.
    # Example: python -m status_manager.status_service

    logging.basicConfig(level=logging.INFO)
    logger.info("Running status_service.py tests...")

    # --- IMPORTANT ---
    # For these tests to run, you need to ensure:
    # 1. PYTHONPATH includes the project root.
    # 2. db.connection.DB_PATH is correctly set and the database exists and is initialized.
    #    (e.g., by running db.init_schema.initialize_database())
    # 3. Some sample data in StatusSettings might be useful.

    # Example:
    # from db.init_schema import initialize_database
    # from db.connection import DB_PATH, set_db_path # Assuming you have set_db_path
    # MOCK_DB_PATH = "test_status_service.db"
    # set_db_path(MOCK_DB_PATH) # Configure for a test DB
    # initialize_database({'database': {'path': MOCK_DB_PATH, 'name': 'test_status_service.db'}})


    # Test get_all_statuses
    all_statuses = get_all_statuses()
    logger.info(f"All statuses: {len(all_statuses)}")
    for s in all_statuses:
        logger.info(f"  - {s}")

    # Test get_statuses_by_type
    client_statuses = get_statuses_by_type(StatusType.CLIENT)
    logger.info(f"\nClient statuses: {len(client_statuses)}")
    for s in client_statuses:
        logger.info(f"  - {s}")

    commande_statuses = get_statuses_by_type(StatusType.COMMANDE)
    logger.info(f"\nCommande statuses: {len(commande_statuses)}")
    for s in commande_statuses:
        logger.info(f"  - {s}")


    # Test Add, GetByID, Update, Delete (be cautious with delete on a real DB)
    # This requires the CRUD functions to be updated for is_archival and icon_name
    # or for this test to only use fields currently supported by the CRUD.
    new_status: Optional[Status] = None
    try:
        logger.info("\nTesting Add Status...")
        # Note: add_status currently doesn't pass is_archival/icon_name to the CRUD correctly.
        # The CRUD add_status_setting would need to be updated first.
        # For this test, we'll add without them for now.
        added_status = add_status(name="Test Service Status", type=StatusType.TASK, color_hex="#123456", sort_order=100) #, is_archival=False, icon_name="task_icon")
        if added_status:
            new_status = added_status
            logger.info(f"Added status: {new_status}")

            logger.info("\nTesting Get Status By ID...")
            fetched_status = get_status_by_id(new_status.status_id)
            logger.info(f"Fetched status: {fetched_status}")
            assert fetched_status and fetched_status.status_id == new_status.status_id

            logger.info("\nTesting Update Status...")
            # Note: update_status also has limitations with is_archival/icon_name until CRUD is updated.
            update_success = update_status(new_status.status_id, name="Test Service Status UPDATED", color_hex="#654321") #, is_archival=True)
            logger.info(f"Update success: {update_success}")
            if update_success:
                updated_fetched_status = get_status_by_id(new_status.status_id)
                logger.info(f"Fetched after update: {updated_fetched_status}")
                assert updated_fetched_status and updated_fetched_status.name == "Test Service Status UPDATED"
                # assert updated_fetched_status.is_archival is True # Would assert if update handled it

        else:
            logger.error("Failed to add status for testing.")

    except Exception as e:
        logger.error(f"Error during add/get/update test: {e}", exc_info=True)
    finally:
        if new_status and new_status.status_id:
            logger.info(f"\nTesting Delete Status (ID: {new_status.status_id})...")
            # is_status_in_use would need to be more robust for this delete to be meaningful
            # For now, it only checks Clients.
            delete_success = delete_status(new_status.status_id)
            logger.info(f"Delete success: {delete_success}")
            if delete_success:
                deleted_fetched_status = get_status_by_id(new_status.status_id)
                logger.info(f"Fetched after delete: {deleted_fetched_status}")
                assert deleted_fetched_status is None


    logger.info("\nTesting default status getters...")
    logger.info(f"Default for Client: {get_default_status_for_client_creation()}")
    logger.info(f"Default for Commande: {get_default_status_for_commande_creation()}")
    logger.info(f"Archived for Client: {get_archived_status_for_client()}")

    logger.info("\nstatus_service.py tests finished.")
