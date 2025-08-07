# license_management/__init__.py
import logging

logger = logging.getLogger(__name__)

# --- Feature Constants ---
# Define all feature constants that other modules might import.
FEATURE_BASIC_CLIENT_DOCS = "feature_basic_client_docs"
FEATURE_PROJECT_MANAGEMENT = "feature_project_management"
FEATURE_STATISTICS_MODULE = "feature_statistics_module"
FEATURE_PRODUCT_MANAGEMENT = "feature_product_management"
FEATURE_PARTNER_MANAGEMENT = "feature_partner_management"
FEATURE_INVENTORY_MANAGEMENT = "feature_inventory_management"
FEATURE_RECRUITMENT_MODULE = "feature_recruitment_module"
FEATURE_BOTPRESS_INTEGRATION = "feature_botpress_integration"
FEATURE_CALENDAR_MODULE = "feature_calendar_module"
FEATURE_EXPERIENCE_MANAGEMENT = "feature_experience_management"
FEATURE_ADVANCED_REPORTING = "feature_advanced_reporting"
FEATURE_API_ACCESS = "feature_api_access"
FEATURE_USER_MANAGEMENT_FULL = "feature_user_management_full"
FEATURE_SETTINGS_MANAGEMENT = "feature_settings_management"
FEATURE_COMMANDES_MANAGEMENT = "feature_commandes_management"
FEATURE_CALCULATOR_MODULE = "feature_calculator_module"

class MockLicenseManager:
    """
    A simplified mock license manager for development.
    It always returns a valid 'complet' license.
    """
    def __init__(self):
        logger.info("Using MockLicenseManager for development.")
        self.default_license_details = {
            'license_id': 'dev-license-001',
            'user_id': 'any_user',
            'license_type': 'complet',
            'license_key': 'DEV-LICENSE-KEY',
            'is_active': True,
            'expiration_date': '2099-12-31T23:59:59Z',
            'allowed_features': {
                FEATURE_BASIC_CLIENT_DOCS,
                FEATURE_PROJECT_MANAGEMENT,
                FEATURE_STATISTICS_MODULE,
                FEATURE_PRODUCT_MANAGEMENT,
                FEATURE_PARTNER_MANAGEMENT,
                FEATURE_INVENTORY_MANAGEMENT,
                FEATURE_RECRUITMENT_MODULE,
                FEATURE_BOTPRESS_INTEGRATION,
                FEATURE_CALENDAR_MODULE,
                FEATURE_EXPERIENCE_MANAGEMENT,
                FEATURE_ADVANCED_REPORTING,
                FEATURE_API_ACCESS,
                FEATURE_USER_MANAGEMENT_FULL,
                FEATURE_SETTINGS_MANAGEMENT,
                FEATURE_COMMANDES_MANAGEMENT,
                FEATURE_CALCULATOR_MODULE,
            }
        }

    def check_license_validity(self, conn, user_id):
        """Always returns a valid license."""
        logger.debug(f"MockLicenseManager: check_license_validity called for user {user_id}. Returning default valid license.")
        # Return a copy to prevent modification of the default dict
        details = self.default_license_details.copy()
        details['user_id'] = user_id
        return True, "Licence de développement valide.", details

    def get_allowed_features(self, license_type: str) -> set:
        """Returns all features for any license type in mock mode."""
        logger.debug(f"MockLicenseManager: get_allowed_features called for type '{license_type}'. Returning all features.")
        return self.default_license_details['allowed_features']

# Instantiate the mock manager for the application to use
manager = MockLicenseManager()

# Define __all__ to make constants easily importable
__all__ = [
    'manager',
    'FEATURE_BASIC_CLIENT_DOCS', 'FEATURE_PROJECT_MANAGEMENT', 'FEATURE_STATISTICS_MODULE',
    'FEATURE_PRODUCT_MANAGEMENT', 'FEATURE_PARTNER_MANAGEMENT', 'FEATURE_INVENTORY_MANAGEMENT',
    'FEATURE_RECRUITMENT_MODULE', 'FEATURE_BOTPRESS_INTEGRATION', 'FEATURE_CALENDAR_MODULE',
    'FEATURE_EXPERIENCE_MANAGEMENT', 'FEATURE_ADVANCED_REPORTING', 'FEATURE_API_ACCESS',
    'FEATURE_USER_MANAGEMENT_FULL', 'FEATURE_SETTINGS_MANAGEMENT',
    'FEATURE_COMMANDES_MANAGEMENT', 'FEATURE_CALCULATOR_MODULE'
]
