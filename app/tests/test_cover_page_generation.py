import os
import sys
import shutil
import subprocess
from datetime import datetime

# Add project root to sys.path
# The project root is three levels up from the current file.
# /app/app/tests/test_cover_page_generation.py -> /app
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import what we need to test
from app.document_generator.cover_page_generator import generate_cover_page_pdf
from app.db.cruds.clients.clients_crud import add_client, get_client_by_id, delete_client
from app.db.cruds.projects.projects_crud import add_project, get_project_by_id, delete_project
from app.db.cruds.misc.companies_crud import add_company, get_company_by_id, delete_company, set_default_company, get_default_company
from app.db.cruds.misc.locations_crud import add_country, get_country_by_name
from app.db.cruds.misc.locations_crud import add_city, get_city_by_name_and_country_id
from app.db.init_schema import initialize_database
from app.db.connection import initialize_engine_and_session, get_db_connection
from app.core.config import CONFIG

def setup_test_environment():
    print("--- 1. Setting up Test Environment ---")
    # Use the global CONFIG dictionary and override for test
    CONFIG['database_path'] = 'test_cover_page.db'
    CONFIG['templates_dir'] = 'templates_test'
    CONFIG['company_logo_dir'] = 'company_logos_test'

    # Set environment variable for Alembic to use the correct test database
    db_path = os.path.abspath(CONFIG['database_path'])
    env = os.environ.copy()
    env['ALEMBIC_DATABASE_URL'] = f"sqlite:///{db_path}"

    # Run alembic migrations to set up the schema
    alembic_command = ["poetry", "run", "alembic", "upgrade", "head"]
    # Use a try-except block to show more detailed error info if Alembic fails
    print(f"Running Alembic against: {env['ALEMBIC_DATABASE_URL']}")
    try:
        # Let output stream directly to console to see what's happening
        subprocess.run(alembic_command, check=True, env=env)
    except subprocess.CalledProcessError as e:
        print("Alembic command failed.")
        # Output will have been printed to stderr/stdout already
        raise

    initialize_engine_and_session(CONFIG)
    # initialize_database(CONFIG) # This is no longer needed as it's just directory creation
    print("Database initialized.")

    # Use paths from config
    APP_ROOT_DIR = project_root
    LOGO_DIR = os.path.join(APP_ROOT_DIR, 'app', CONFIG.get('company_logo_dir'))
    TEMPLATES_DIR = os.path.join(APP_ROOT_DIR, 'app', CONFIG.get('templates_dir'))

    os.makedirs(LOGO_DIR, exist_ok=True)
    print(f"Logo directory ensured: {LOGO_DIR}")
    os.makedirs(TEMPLATES_DIR, exist_ok=True)
    print(f"Templates directory ensured: {TEMPLATES_DIR}")

    dummy_logo_filename = 'cover_test_logo.png'
    dummy_logo_path = os.path.join(LOGO_DIR, dummy_logo_filename)
    try:
        with open(dummy_logo_path, 'w') as f:
            f.write("dummy logo content")
        print(f"Dummy logo created at: {dummy_logo_path}")
    except IOError as e:
        print(f"Error creating dummy logo: {e}. Test might fail on logo path check.")

    return CONFIG, LOGO_DIR, TEMPLATES_DIR, dummy_logo_filename

def cleanup_test_environment(config_dict, logo_dir, dummy_logo_filename):
    print("\n--- 4. Cleaning Up Test Environment ---")
    db_path = config_dict.get('database_path')
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Deleted test database: {db_path}")

    dummy_logo_path = os.path.join(logo_dir, dummy_logo_filename)
    if os.path.exists(dummy_logo_path):
        os.remove(dummy_logo_path)
        print(f"Deleted dummy logo: {dummy_logo_path}")

    templates_dir = os.path.join(project_root, 'app', config_dict.get('templates_dir'))
    if os.path.exists(templates_dir):
        shutil.rmtree(templates_dir)
        print(f"Deleted test templates directory: {templates_dir}")

    print("Test data cleanup finished.")

def test_cover_page_generation():
    print("--- Starting Cover Page Generation Test ---")
    config_dict, LOGO_DIR, TEMPLATES_DIR, dummy_logo_filename = setup_test_environment()
    db_session = get_db_connection()

    try:
        # 2. Create Test Data
        print("\n--- 2. Creating Test Data ---")

        # Default Company (Exporter)
        default_company_id = add_company({
            'company_name': 'Cover Test Exporter Inc.',
            'address': '1 Tech Park, Silicon Valley',
            'logo_path': dummy_logo_filename,
            'is_default': True
        }, conn=db_session)
        if not default_company_id: raise Exception("Failed to create 'Cover Test Exporter Inc.'")
        set_default_company(default_company_id, conn=db_session)
        default_company_check = get_default_company(conn=db_session)
        assert default_company_check and default_company_check['company_id'] == default_company_id, "Failed to set/get default company for exporter."
        print(f"Default Company: {default_company_check['company_name']} (ID: {default_company_id})")

        # Client Company
        country_id = add_country({'country_name': 'Client Nation'}, conn=db_session)['country_id']
        city_id = add_city({'country_id': country_id, 'city_name': 'Client City'}, conn=db_session)['city_id']

        client_id = add_client({
            'client_name': 'Mr. Client Contact',
            'company_name': 'Cover Test Client Corp.',
            'project_identifier': 'CVR-TST-01',
            'country_id': country_id,
            'city_id': city_id,
            'created_by_user_id': 'test-user'
        }, conn=db_session)['client_id']
        if not client_id: raise Exception("Failed to create client 'Cover Test Client Corp.'")
        print(f"Client: Cover Test Client Corp. (ID: {client_id})")

        # Project
        project_id_for_test = add_project({
            'client_id': client_id,
            'project_name': 'Annual Report Cover Test'
        }, conn=db_session)
        if not project_id_for_test: raise Exception("Failed to create project 'Annual Report Cover Test'")
        print(f"Project: Annual Report Cover Test (ID: {project_id_for_test})")

        # 3. Test PDF Generation
        print("\n--- 3. Testing PDF Generation ---")

        output_pdf_path = os.path.join(TEMPLATES_DIR, 'test_cover.pdf')

        success = generate_cover_page_pdf(
            client_id=client_id,
            company_id=default_company_id,
            language_code='en',
            output_pdf_path=output_pdf_path,
            project_id=project_id_for_test,
            document_type_for_context="Test Document",
            additional_context_overrides={
                "title": "Test Cover Page PDF",
                "subtitle": "A test subtitle for PDF"
            },
            db_conn=db_session
        )

        assert success is True
        assert os.path.exists(output_pdf_path)
        assert os.path.getsize(output_pdf_path) > 0

        print("PDF file generated successfully and is not empty.")

    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        print("TEST FAILED.")
        raise e
    finally:
        db_session.close()
        cleanup_test_environment(config_dict, LOGO_DIR, dummy_logo_filename)
        print("\n--- Cover Page Generation Test Finished ---")
