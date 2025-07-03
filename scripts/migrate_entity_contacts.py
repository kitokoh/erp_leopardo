import sqlite3
import os
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add project root to sys.path to allow importing db module
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPTS_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from db.connection import get_db_connection
    import db.cruds.contacts_crud as contacts_crud
    import db.cruds.entity_contacts_crud as entity_contacts_crud
    # We might need CRUDs for Transporters, FreightForwarders, Partners if we decide to nullify their direct contact fields
    import db.cruds.transporters_crud as transporters_crud
    import db.cruds.freight_forwarders_crud as freight_forwarders_crud
    import db.cruds.partners_crud as partners_crud

except ImportError as e:
    logging.error(f"Failed to import necessary modules. Ensure you are running from a context where db modules are accessible: {e}")
    sys.exit(1)

# --- Configuration ---
# Entity type mapping: Table Name -> (Primary Key Column, EntityType String, Direct Contact Fields)
ENTITIES_TO_MIGRATE = {
    "Transporters": {
        "pk_column": "transporter_id",
        "entity_type_str": "Transporter",
        "contact_name_field": "contact_person",
        "email_field": "email",
        "phone_field": "phone",
        "crud_module": transporters_crud
    },
    "FreightForwarders": {
        "pk_column": "forwarder_id",
        "entity_type_str": "FreightForwarder",
        "contact_name_field": "contact_person",
        "email_field": "email",
        "phone_field": "phone",
        "crud_module": freight_forwarders_crud
    },
    "Partners": {
        "pk_column": "partner_id",
        "entity_type_str": "Partner",
        "contact_name_field": "contact_person_name", # Note: field name is different
        "email_field": "email",
        "phone_field": "phone",
        "crud_module": partners_crud
    }
}

# Column to mark successful migration (add this to tables manually or via another script if needed for idempotency)
MIGRATION_FLAG_COLUMN = "contact_info_migrated_at"

def migrate_contacts_for_table(table_name, config, conn):
    logging.info(f"--- Starting migration for table: {table_name} ---")
    cursor = conn.cursor()

    # Check if migration flag column exists, if not, we can't make it idempotent this way
    # For this script, we'll assume it's okay to run once or that duplicates are handled by unique constraints / logic
    # A more robust solution would add this column first.

    query = f"SELECT {config['pk_column']}, {config['contact_name_field']}, {config['email_field']}, {config['phone_field']} FROM {table_name}"
    # Optional: Add "WHERE {MIGRATION_FLAG_COLUMN} IS NULL" if using the flag column for idempotency

    cursor.execute(query)
    entities = cursor.fetchall()

    migrated_count = 0
    skipped_due_to_explicit_primary = 0
    skipped_no_direct_info = 0

    for entity_row in entities:
        entity_id = entity_row[config['pk_column']]
        direct_contact_name = (entity_row[config['contact_name_field']] or "").strip()
        direct_email = (entity_row[config['email_field']] or "").strip()
        direct_phone = (entity_row[config['phone_field']] or "").strip()

        logging.debug(f"Processing {config['entity_type_str']} ID: {entity_id} - DirectContact: {direct_contact_name}, Email: {direct_email}, Phone: {direct_phone}")

        if not direct_contact_name and not direct_email and not direct_phone:
            logging.debug(f"Skipping {config['entity_type_str']} ID: {entity_id} - No direct contact info.")
            skipped_no_direct_info += 1
            continue

        # Check if an explicit primary contact already exists via EntityContacts
        # Pass the connection to CRUD functions
        existing_entity_contacts = entity_contacts_crud.get_contacts_for_entity(entity_id, config['entity_type_str'], conn=conn)
        primary_entity_contact = next((c for c in existing_entity_contacts if c.get('is_primary')), None)

        if primary_entity_contact:
            logging.info(f"Skipping direct field migration for {config['entity_type_str']} ID: {entity_id}. Explicit primary contact (ID: {primary_entity_contact['contact_id']}) already exists via EntityContacts.")
            # Further logic could be added here to compare/warn if direct fields differ significantly
            skipped_due_to_explicit_primary += 1
            continue

        contact_to_link_id = None

        # 1. Try to find an existing contact by email
        if direct_email:
            # Pass the connection to CRUD functions
            existing_central_contact = contacts_crud.get_contact_by_email(direct_email, conn=conn)
            if existing_central_contact:
                contact_to_link_id = existing_central_contact['contact_id']
                logging.info(f"Found existing central contact ID {contact_to_link_id} for email {direct_email}.")
                # Update this existing contact if direct fields have more/different info
                update_payload = {}
                if direct_contact_name and existing_central_contact.get('displayName') != direct_contact_name:
                    update_payload['displayName'] = direct_contact_name
                    update_payload['name'] = direct_contact_name # ensure name is also updated
                if direct_phone and existing_central_contact.get('phone') != direct_phone:
                    update_payload['phone'] = direct_phone

                if update_payload:
                    logging.info(f"Updating central contact ID {contact_to_link_id} with: {update_payload}")
                    # Pass the connection to CRUD functions
                    contacts_crud.update_contact(contact_to_link_id, update_payload, conn=conn)

        # 2. If no existing contact found by email, create a new one
        if not contact_to_link_id:
            if not direct_contact_name: # Require a name to create a new contact
                logging.warning(f"Skipping creation for {config['entity_type_str']} ID: {entity_id} - Email '{direct_email}' not found, and no direct_contact_name provided to create new contact.")
                continue

            contact_details = {
                'displayName': direct_contact_name,
                'name': direct_contact_name,
                'email': direct_email if direct_email else None, # Allow null email if not provided
                'phone': direct_phone if direct_phone else None, # Allow null phone
                'employee_status': 'external', # Default
                # 'created_by_user_id': 'migration_script' # Optional: if your add_contact supports it
            }
            logging.info(f"Creating new central contact with details: {contact_details}")
            # Pass the connection to CRUD functions
            contact_to_link_id = contacts_crud.add_contact(contact_details, conn=conn)
            if contact_to_link_id:
                logging.info(f"Created new central contact ID {contact_to_link_id} for {config['entity_type_str']} ID: {entity_id}.")
            else:
                logging.error(f"Failed to create new central contact for {config['entity_type_str']} ID: {entity_id}.")
                continue # Skip to next entity if contact creation fails

        # 3. Link the contact (found or new) to the entity as primary
        if contact_to_link_id:
            link_details = {
                'role_in_entity': "Contact Principal (migré)",
                'is_primary': True,
                'can_receive_documents': True,
                'notes': "Automatiquement migré depuis les champs directs de l'entité."
            }

            # Check if this specific contact_id is already linked to this entity (even if not primary)
            already_linked_as_this_contact = next((c for c in existing_entity_contacts if c['contact_id'] == contact_to_link_id), None)

            if already_linked_as_this_contact:
                # If linked, but not primary, update it to be primary
                if not already_linked_as_this_contact.get('is_primary'):
                    logging.info(f"Updating existing link (ID: {already_linked_as_this_contact['entity_contact_id']}) for contact {contact_to_link_id} to be primary for {config['entity_type_str']} ID: {entity_id}.")
                    # Pass the connection to CRUD functions
                    entity_contacts_crud.update_entity_contact_link(already_linked_as_this_contact['entity_contact_id'], link_details, conn=conn)
                    migrated_count +=1
                else:
                    logging.info(f"Contact ID {contact_to_link_id} already linked and primary for {config['entity_type_str']} ID: {entity_id}. No change to link needed.")
                    # This case should ideally be caught by the initial `primary_entity_contact` check,
                    # but this is a safeguard.
            else:
                # Link new contact
                logging.info(f"Linking contact ID {contact_to_link_id} as primary to {config['entity_type_str']} ID: {entity_id}.")
                # Pass the connection to CRUD functions
                entity_contacts_crud.link_contact_to_entity(
                    entity_id=entity_id,
                    entity_type=config['entity_type_str'],
                    contact_id=contact_to_link_id,
                    **link_details,
                    conn=conn
                )
                migrated_count +=1

            # Optional: Nullify direct contact fields in the source table after successful migration
            # This is a destructive change, use with caution and after backups.
            # Example:
            # cursor.execute(f"UPDATE {table_name} SET {config['contact_name_field']}=NULL, {config['email_field']}=NULL, {config['phone_field']}=NULL WHERE {config['pk_column']}=?", (entity_id,))
            # logging.info(f"Nullified direct contact fields for {config['entity_type_str']} ID: {entity_id}")

    logging.info(f"--- Finished migration for table: {table_name} ---")
    logging.info(f"Successfully migrated/linked contacts for {migrated_count} entities.")
    logging.info(f"Skipped {skipped_due_to_explicit_primary} entities due to existing explicit primary contact.")
    logging.info(f"Skipped {skipped_no_direct_info} entities due to no direct contact info.")


def main():
    logging.info("Starting contact data migration process...")
    conn = None
    try:
        conn = get_db_connection()
        conn.execute("PRAGMA foreign_keys = ON;") # Ensure FKs are enforced

        for table_name, config_params in ENTITIES_TO_MIGRATE.items():
            migrate_contacts_for_table(table_name, config_params, conn)

        conn.commit()
        logging.info("Contact data migration process completed and committed successfully.")

    except sqlite3.Error as e:
        logging.error(f"A database error occurred during migration: {e}", exc_info=True)
        if conn:
            conn.rollback()
            logging.info("Transaction rolled back due to errors.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        if conn:
            conn.rollback()
            logging.info("Transaction rolled back due to unexpected errors.")
    finally:
        if conn:
            conn.close()
            logging.info("Database connection closed.")

if __name__ == "__main__":
    # Confirmation step
    # print("WARNING: This script will modify your database by migrating contact information.")
    # print("It is highly recommended to BACK UP YOUR DATABASE before proceeding.")
    # confirm = input("Type 'YES' to continue with the migration: ")
    # if confirm == "YES":
    #     main()
    # else:
    #     print("Migration cancelled by user.")
    logging.info("Script is ready. To run, uncomment the confirmation block and execute.")
    # For direct execution in dev/test, you might call main() directly after thorough checks.
    # main() # Use with caution
    pass
