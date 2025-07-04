# This file makes the 'license_management' directory a Python package.
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PlaceholderCruds:
    def get_licenses_by_machine_info(self, conn, machine_id, license_type):
        logger.info(f"PlaceholderCruds.get_licenses_by_machine_info called for type: {license_type}. Returning empty list (simulating no existing free license).")
        # To test scenarios where a free license was already used, you could return a dummy license here.
        # For now, assume no prior free license for this user/machine to allow free activation path.
        return []

    def get_license_by_user_id(self, conn, user_id):
        logger.info(f"PlaceholderCruds.get_license_by_user_id called for user: {user_id}. Returning a dummy active license for testing.")
        # This could be made more sophisticated to "remember" if a free license was activated.
        # For now, it always returns a developer license if check_license_validity uses it.
        # However, check_license_validity itself will provide the main dummy license.
        # This method is mostly for _check_free_license_availability in ui.py
        return {
            "user_id": user_id,
            "license_key": "DUMMY-EXISTING-LICENSE",
            "license_type": "developer", # or "gratuit" to test blocking free license
            "is_active": True,
            "expiration_date": (datetime.utcnow() + timedelta(days=365)).isoformat() + "Z",
            "issued_at": datetime.utcnow().isoformat() + "Z",
            "machine_info": "dummy_machine_id_placeholder"
        }


class PlaceholderManager:
    def __init__(self):
        self.cruds = PlaceholderCruds()
        logger.info("PlaceholderManager initialized with dummy valid license logic.")

    def check_license_validity(self, conn, user_id):
        logger.info(f"PlaceholderManager.check_license_validity called for user_id: {user_id}. Returning dummy valid license.")
        dummy_license_details = {
            "user_id": user_id,
            "license_key": "DUMMY-LICENSE",
            "license_type": "developer",
            "is_active": True,
            "expiration_date": "2999-12-31T00:00:00Z", # Far future
            "issued_at": "2024-01-01T00:00:00Z",
            "machine_info": self.get_machine_identifier()
        }
        return True, "Dummy development license is active.", dummy_license_details

    def get_current_license_display_info(self, conn, user_id):
        logger.info(f"PlaceholderManager.get_current_license_display_info called for user_id: {user_id}.")
        # Fetch the "current" dummy license details
        _, _, lic_details = self.check_license_validity(conn, user_id)
        if lic_details and lic_details.get('is_active'):
            return (f"Type: {lic_details.get('license_type', 'N/A').capitalize()} (Dummy)\n"
                    f"Expires: {lic_details.get('expiration_date', 'N/A')}\n"
                    f"Key: {lic_details.get('license_key', 'N/A')}")
        return "License: Dummy Developer License (Active)\nExpires: Far Future\nKey: DUMMY-LICENSE"


    def activate_license(self, conn, user_id, license_key):
        logger.info(f"PlaceholderManager.activate_license called for user_id: {user_id}, key: {license_key}. Simulating successful activation.")
        # In a real scenario, this would validate the key and store it.
        # Here, we just acknowledge it and assume check_license_validity will provide the dummy.
        # No need to return license details, just success status and message.
        return True, f"Dummy license key '{license_key}' accepted for activation."

    def activate_free_license(self, conn, user_id):
        logger.info(f"PlaceholderManager.activate_free_license called for user_id: {user_id}. Simulating successful free license activation.")
        free_license_details = {
            "user_id": user_id,
            "license_key": "DUMMY-FREE-LICENSE",
            "license_type": "free_developer",
            "is_active": True,
            "expiration_date": (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z", # 30 days from now
            "issued_at": datetime.utcnow().isoformat() + "Z",
            "machine_info": self.get_machine_identifier()
        }
        # To make the UI update properly, this should now be the "active" license.
        # A simple way is to have check_license_validity check a global or instance var.
        # For now, this will make the UI happy, but a subsequent call to check_license_validity
        # from main.py might still return the generic DUMMY-LICENSE.
        # This is generally okay for unblocking, but true state would need more work.
        return free_license_details, "Dummy free 30-day developer license activated successfully."

    def get_machine_identifier(self):
        # logger.info("PlaceholderManager.get_machine_identifier called.") # Less verbose
        return "dummy_machine_id_placeholder_v2"

manager = PlaceholderManager()

# This allows `from license_management import manager` to work,
# and `manager.cruds` to be accessed.
# Calls to the methods will log warnings.
__all__ = ['manager']   # This is a placeholder manager for license management, simulating a valid license.
# In a real application, this would be replaced with actual license management logic.   