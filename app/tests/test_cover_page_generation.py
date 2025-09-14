import os
import sys
import shutil
from datetime import datetime

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
sys.path.append(os.path.abspath('app/core'))


# Import what we need to test
from app.document_generator.cover_page_generator import generate_cover_page_html
from app.db.cruds.clients.clients_crud import add_client, get_client_by_id, delete_client
from app.db.cruds.projects.projects_crud import add_project, get_project_by_id, delete_project
from app.db.cruds.misc.companies_crud import add_company, get_company_by_id, delete_company, set_default_company, get_default_company
from app.db.cruds.misc.locations_crud import add_country, get_country_by_name, add_city, get_city_by_name_and_country_id
from app.db.init_schema import initialize_database
from app.db.connection import initialize_engine_and_session, get_db_connection
from config import CONFIG

def setup_test_environment():
    print("--- 1. Setting up Test Environment ---")
    config = CONFIG.copy()
    # Override config for test
    config['database_path'] = 'test_cover_page.db'
    config['templates_dir'] = 'templates_test'
    config['company_logo_dir'] = 'company_logos_test'

    initialize_engine_and_session(config)
    initialize_database(config)
    print("Database initialized.")

    # Use paths from config
    APP_ROOT_DIR = project_root
    LOGO_DIR = os.path.join(APP_ROOT_DIR, 'app', config.get('company_logo_dir'))
    TEMPLATES_DIR = os.path.join(APP_ROOT_DIR, 'app', config.get('templates_dir'))

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

    return config, LOGO_DIR, TEMPLATES_DIR, dummy_logo_filename

def cleanup_test_environment(config, logo_dir, dummy_logo_filename):
    print("\n--- 4. Cleaning Up Test Environment ---")
    db_path = config.get('database_path')
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Deleted test database: {db_path}")

    dummy_logo_path = os.path.join(logo_dir, dummy_logo_filename)
    if os.path.exists(dummy_logo_path):
        os.remove(dummy_logo_path)
        print(f"Deleted dummy logo: {dummy_logo_path}")

    templates_dir = os.path.join(project_root, 'app', config.get('templates_dir'))
    if os.path.exists(templates_dir):
        shutil.rmtree(templates_dir)
        print(f"Deleted test templates directory: {templates_dir}")

    print("Test data cleanup finished.")

def main():
    print("--- Starting Cover Page Generation Test ---")
    config, LOGO_DIR, TEMPLATES_DIR, dummy_logo_filename = setup_test_environment()
    db_session = next(get_db_connection())

    try:
        # 2. Create Test Data
        print("\n--- 2. Creating Test Data ---")

        # Default Company (Exporter)
        default_company_id = add_company(db_session, {
            'company_name': 'Cover Test Exporter Inc.',
            'address': '1 Tech Park, Silicon Valley',
            'logo_path': dummy_logo_filename,
            'is_default': True
        })
        if not default_company_id: raise Exception("Failed to create 'Cover Test Exporter Inc.'")
        set_default_company(db_session, default_company_id)
        default_company_check = get_default_company(db_session)
        assert default_company_check and default_company_check['company_id'] == default_company_id, "Failed to set/get default company for exporter."
        print(f"Default Company: {default_company_check['company_name']} (ID: {default_company_id})")

        # Client Company
        country_id = add_country(db_session, {'country_name': 'Client Nation'})['country_id']
        city_id = add_city(db_session, {'country_id': country_id, 'city_name': 'Client City'})['city_id']

        client_id = add_client(db_session, {
            'client_name': 'Mr. Client Contact',
            'company_name': 'Cover Test Client Corp.',
            'project_identifier': 'CVR-TST-01',
            'country_id': country_id,
            'city_id': city_id,
            'created_by_user_id': 'test-user'
        })['client_id']
        if not client_id: raise Exception("Failed to create client 'Cover Test Client Corp.'")
        print(f"Client: Cover Test Client Corp. (ID: {client_id})")

        # Project
        project_id_for_test = add_project(db_session, {
            'client_id': client_id,
            'project_name': 'Annual Report Cover Test'
        })
        if not project_id_for_test: raise Exception("Failed to create project 'Annual Report Cover Test'")
        print(f"Project: Annual Report Cover Test (ID: {project_id_for_test})")

        # 3. Test HTML Generation
        print("\n--- 3. Testing HTML Generation ---")

        context_data = {
            "client_id": client_id,
            "project_id": project_id_for_test,
            "document_title": "Test Cover Page",
            "document_subtitle": "A test subtitle",
            "document_version": "1.0-test"
        }

        html_content = generate_cover_page_html(db_session, context_data)

        assert html_content is not None
        assert "Cover Test Exporter Inc." in html_content
        assert "Cover Test Client Corp." in html_content
        assert "Annual Report Cover Test" in html_content
        assert "Test Cover Page" in html_content

        print("HTML content generated successfully and contains expected data.")

    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        print("TEST FAILED.")
    finally:
        db_session.close()
        cleanup_test_environment(config, LOGO_DIR, dummy_logo_filename)
        print("\n--- Cover Page Generation Test Finished ---")

if __name__ == '__main__':
    main()
