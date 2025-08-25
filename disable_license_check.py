import logging
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.getcwd())

from app.db.connection import get_db_connection
from app.db.cruds.misc.application_settings_crud import settings_crud

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def disable_license_check():
    """
    Disables the license check by setting the 'check_license_on_startup' setting to 'False'.
    """
    db = None
    try:
        db = get_db_connection()
        log.info("Disabling license check...")
        settings_crud.set_setting(db, 'check_license_on_startup', 'False')
        log.info("License check disabled successfully.")
    except Exception as e:
        log.error(f"An error occurred while disabling the license check: {e}", exc_info=True)
    finally:
        if db:
            db.close()

if __name__ == "__main__":
    disable_license_check()
