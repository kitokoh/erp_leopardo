import sys
import os
import logging
import subprocess

# Configure logging FIRST
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add the project root to the Python path
sys.path.insert(0, os.getcwd())

from app.core.config import CONFIG
from app.db.connection import initialize_engine_and_session, get_db_connection
from app.db.cruds.clients import clients_crud
from app.db.cruds.clients import client_documents_crud
from app.db.cruds.users import users_crud

def run_db_initialization():
    """Runs the database initialization script as a separate process."""
    logging.info("Running database initialization script...")

    # Ensure the database file is deleted before initialization for a clean state
    db_path = CONFIG.get('database_path')
    if db_path and os.path.exists(db_path):
        try:
            os.remove(db_path)
            logging.info(f"Removed existing database file at {db_path}")
        except OSError as e:
            logging.error(f"Error removing database file: {e}")
            return False

    result = subprocess.run(
        ['poetry', 'run', 'python', 'run_db_init.py'],
        capture_output=True, text=True, check=False
    )

    if result.returncode != 0:
        logging.error("--- Database Initialization Failed! ---")
        logging.error(f"Return Code: {result.returncode}")
        logging.error(f"STDOUT:\n{result.stdout}")
        logging.error(f"STDERR:\n{result.stderr}")
        return False

    logging.info("--- Database Initialization Successful ---")
    # logging.info(f"STDOUT:\n{result.stdout}") # Can be noisy, enable if needed
    return True

def test_list_client_documents():
    """
    Tests that we can successfully retrieve a list of documents for a client.
    """
    logging.info("========== Starting Document Management Test ==========")

    # 0. Initialize the database from scratch
    if not run_db_initialization():
        logging.error("Aborting test due to database initialization failure.")
        return

    # 1. Initialize Environment for THIS process
    logging.info("Setting up test environment for test process...")
    if not CONFIG:
        logging.error("Failed to load configuration. Aborting test.")
        return
    initialize_engine_and_session(CONFIG)
    logging.info("Environment setup complete.")

    db_session = None
    try:
        db_session = get_db_connection()

        # 2. Get a client to test with (one should exist from seeding)
        logging.info("Fetching clients from the newly seeded database...")
        all_clients = clients_crud.get_all_clients(db_session)
        if not all_clients:
            logging.error("Seeding failed to create clients. Aborting.")
            return

        test_client = all_clients[0]
        client_id = test_client.get('client_id')
        client_name = test_client.get('client_name')
        logging.info(f"Found test client from seeder: '{client_name}' (ID: {client_id})")

        # 3. Call the document retrieval function
        logging.info(f"Attempting to retrieve documents for client ID: {client_id}")
        documents = client_documents_crud.get_documents_for_client(client_id, conn=db_session)

        # 4. Assert and report the result
        if documents is not None:
            logging.info(f"Successfully retrieved documents for client '{client_name}'.")
            logging.info(f"Number of documents found: {len(documents)}")
            if documents:
                for doc in documents:
                    logging.info(f"  - Doc ID: {doc.get('document_id')}, Name: {doc.get('document_name')}, Type: {doc.get('document_type_generated')}")
            else:
                logging.info("The client has no documents, which is a valid initial state.")
            logging.info("--- Document Management Test Successful ---")
        else:
            logging.error("Failed to retrieve documents. The function returned None, indicating an error.")
            logging.info("--- Document Management Test Failed ---")

    except Exception as e:
        logging.error(f"An unexpected error occurred during the document management test: {e}", exc_info=True)
        logging.info("--- Document Management Test Failed ---")
    finally:
        if db_session:
            db_session.close()
        logging.info("========== Test Finished ==========")

if __name__ == "__main__":
    test_list_client_documents()
