import os
import sys
import logging

def main():
    """
    Runs a focused test of the database initialization and seeding process.
    """
    # Set up the environment
    try:
        # Add project root to sys.path
        PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
        if PROJECT_ROOT not in sys.path:
            sys.path.insert(0, PROJECT_ROOT)

        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s')
        logging.info("Starting database verification script.")
        logging.info(f"PROJECT_ROOT: {PROJECT_ROOT}")
        logging.info(f"sys.path: {sys.path}")

        # Import the necessary components
        from app_setup import CONFIG
        from main_crm import initialize_database

        logging.info("Imports successful.")

        # Run the database initialization process from main_crm.py
        initialize_database()

        logging.info("Database verification script finished successfully!")
        print("\n✅ DATABASE INITIALIZATION AND SEEDING SUCCEEDED.\n")

    except Exception as e:
        logging.error("Database verification FAILED.", exc_info=True)
        print(f"\n❌ DATABASE INITIALIZATION FAILED: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
