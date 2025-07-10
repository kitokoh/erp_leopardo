# license_management/__init__.py
import logging
import uuid
from datetime import datetime, timedelta, timezone
import json # For parsing license key payload
import base64 # For decoding license key parts
import os # For public key file path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding # Renamed to avoid conflict
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature

from db.cruds import licenses_crud
import sqlite3

# Assuming APP_ROOT_DIR is available or can be imported for robust path construction
# If not, this needs to be configured or passed in.
# For now, let's assume a way to get APP_ROOT_DIR.
try:
    from app_setup import APP_ROOT_DIR
except ImportError:
    # Fallback if app_setup is not available at this import level (e.g. running standalone)
    APP_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logger.warning(f"Could not import APP_ROOT_DIR from app_setup, falling back to: {APP_ROOT_DIR}")

logger = logging.getLogger(__name__)
PUBLIC_KEY_FILE = os.path.join(APP_ROOT_DIR, "license_public_key.pem")
LOADED_PUBLIC_KEY = None

def load_public_key(public_key_path: str = PUBLIC_KEY_FILE) -> RSAPublicKey | None:
    """Loads the RSA public key from a PEM file."""
    global LOADED_PUBLIC_KEY
    if LOADED_PUBLIC_KEY is not None:
        return LOADED_PUBLIC_KEY

    if not os.path.exists(public_key_path):
        logger.error(f"Public key file not found at {public_key_path}. License verification will fail.")
        return None
    try:
        with open(public_key_path, 'rb') as f:
            public_key = serialization.load_pem_public_key(
                f.read(),
                backend=default_backend()
            )
        if not isinstance(public_key, RSAPublicKey):
            logger.error("Loaded key is not an RSA public key.")
            return None
        LOADED_PUBLIC_KEY = public_key
        logger.info(f"Public key successfully loaded from {public_key_path}.")
        return LOADED_PUBLIC_KEY
    except Exception as e:
        logger.error(f"Error loading public key: {e}", exc_info=True)
        return None

# Attempt to load the public key when the module is loaded
load_public_key()

LICENSE_TYPES = {
    "GRATUIT": "gratuit",
    "LIMITE": "limite",
    "COMPLET": "complet",
}
DEFAULT_ADMIN_LICENSE_TYPE = LICENSE_TYPES["COMPLET"]
# ADMIN_USERNAME = "admin" # Moved to be a class attribute of LicenseManager

class LicenseManager:
    ADMIN_USERNAME = "admin" # Class attribute

    def __init__(self):
        # licenses_crud is a module, not a class to instantiate here usually
        # We'll call its functions directly: licenses_crud.add_license(...) etc.
        logger.info("LicenseManager initialized.")

    def get_machine_identifier(self) -> str:
        """
        Retrieves a unique identifier for the current machine using the machineid library.
        Returns a hashed version of the ID for privacy if needed, but raw for better uniqueness.
        """
        try:
            import machineid
            current_machine_id = machineid.id()
            logger.debug(f"Retrieved machine identifier using machineid library: {current_machine_id}")
            return current_machine_id
        except ImportError:
            logger.error("machineid library not found. Please install it. Falling back to placeholder.")
            # Fallback to a less reliable or static ID if machineid is not available
            # This fallback should be logged and potentially alerted to the user/admin.
            return "fallback_machine_id_machineid_not_installed"
        except Exception as e:
            logger.error(f"Error getting machine identifier using machineid library: {e}", exc_info=True)
            # Fallback in case of any other error from machineid.id()
            return "error_getting_machine_id_via_library"

    def check_license_validity(self, conn: sqlite3.Connection, user_id: str) -> tuple[bool, str | None, dict | None]:
        """
        Checks if the user has a valid, active, and non-expired license.
        Returns:
            tuple[bool, str | None, dict | None]: (is_valid, message, license_details)
        """
        logger.debug(f"LicenseManager.check_license_validity CALLED for user_id: {user_id}. Connection type: {type(conn)}")
        if not conn or not user_id:
            logger.error("check_license_validity: Missing connection or user_id.")
            return False, "Internal error: Missing connection or user ID.", None

        try:
            logger.debug(f"LicenseManager.check_license_validity: Attempting licenses_crud.get_active_license_for_user for user {user_id}")
            license_details = licenses_crud.get_active_license_for_user(conn, user_id)
            logger.debug(f"LicenseManager.check_license_validity: licenses_crud.get_active_license_for_user returned: {type(license_details)}")

            if not license_details:
                logger.info(f"No active license found for user_id: {user_id}.")
                return False, "Aucune licence active trouvée pour cet utilisateur.", None

            # Check expiration (get_active_license_for_user should already handle this)
            # but double-checking here can be useful if the CRUD logic changes.
            expiration_date_str = license_details.get('expiration_date')
            if expiration_date_str:
                try:
                    # Assuming expiration_date_str is ISO format (YYYY-MM-DDTHH:MM:SS.ffffff[+HH:MM|Z])
                    # If it's just YYYY-MM-DD, parse accordingly or ensure CRUD stores full ISO
                    expiration_date = datetime.fromisoformat(expiration_date_str.replace("Z", "+00:00"))
                    if expiration_date.tzinfo is None: # If no timezone, assume UTC
                        expiration_date = expiration_date.replace(tzinfo=timezone.utc)

                    if expiration_date < datetime.now(timezone.utc):
                        logger.warning(f"License {license_details['license_id']} for user {user_id} has expired on {expiration_date_str}.")
                        # Optionally deactivate it here
                        # licenses_crud.deactivate_license(conn, license_details['license_id'])
                        return False, "Votre licence a expiré.", license_details
                except ValueError:
                    logger.error(f"Invalid date format for expiration_date ('{expiration_date_str}') for license {license_details['license_id']}.")
                    return False, "Format de date d'expiration de licence invalide.", license_details

            # Optionally, verify machine_info if it's part of your licensing scheme
            # current_machine_id = self.get_machine_identifier()
            # if license_details.get('machine_info') and license_details.get('machine_info') != current_machine_id:
            #     logger.warning(f"License {license_details['license_id']} for user {user_id} is for a different machine.")
            #     return False, "Licence valide pour une autre machine.", license_details

            logger.info(f"License {license_details['license_id']} for user {user_id} is valid.")
            return True, "Licence valide.", license_details

        except Exception as e:
            logger.error(f"Error during check_license_validity for user {user_id}: {e}", exc_info=True)
            return False, "Erreur interne lors de la vérification de la licence.", None
        except AttributeError as e_attr_cv: # Specific catch for AttributeError
            logger.error(f"AttributeError in check_license_validity for user {user_id}. Conn type: {type(conn)}. Error: {e_attr_cv}", exc_info=True)
            # import traceback # Already imported at module level
            logger.error(f"Traceback for AttributeError in check_license_validity:\n{traceback.format_exc()}")
            return False, f"Erreur interne (AttributeError) lors de la vérification de la licence: {e_attr_cv}", None
        except Exception as e_check_lic: # General catch-all
            logger.error(f"CRITICAL_ERROR_INSIDE_CHECK_LICENSE_VALIDITY (user: {user_id}, conn_type: {type(conn)}): Type: {type(e_check_lic).__name__}, Error: {str(e_check_lic)}")
            logger.error(traceback.format_exc()) # Print full traceback here
            # Now, instead of returning a generic message, let's return a more specific one OR re-raise
            # Forcing the specific error message to see if it appears in the GUI via main.py
            return False, f"Internal Crash in License Check: {type(e_check_lic).__name__}", None

    def create_default_admin_license(self, conn: sqlite3.Connection, user_id: str) -> tuple[bool, str | None, dict | None]:
        """
        Creates a default 6-month 'complet' license for the specified user_id.
        Typically used for the admin user on first setup or if their license is missing/invalid.
        """
        logger.debug(f"LicenseManager.create_default_admin_license called for user_id: {user_id}. Connection type: {type(conn)}")
        if not conn or not user_id:
            logger.error("create_default_admin_license: Missing connection or user_id.")
            return False, "Internal error: Missing connection or user ID for admin license creation.", None

        logger.info(f"Attempting to create default admin license for user_id: {user_id}")

        try:
            # Deactivate any existing active licenses for this admin user to avoid conflicts
            # This is a simple approach; a more complex one might archive them or handle differently.
            existing_license = licenses_crud.get_active_license_for_user(conn, user_id)
            if existing_license:
                logger.info(f"Deactivating existing license {existing_license['license_id']} for admin user {user_id} before creating new default one.")
                licenses_crud.deactivate_license(conn, existing_license['license_id'])

            now = datetime.now(timezone.utc)
            expiration = now + timedelta(days=6 * 30) # Approx 6 months

            new_license_id = str(uuid.uuid4())
            license_key = f"ADMIN-DEFAULT-{new_license_id[:8].upper()}" # Example key format

            license_data = {
                'license_id': new_license_id,
                'user_id': user_id,
                'license_type': DEFAULT_ADMIN_LICENSE_TYPE,
                'license_key': license_key,
                'activation_date': now,
                'expiration_date': expiration,
                'machine_info': self.get_machine_identifier(), # Store machine ID
                'is_active': True
            }

            created_id = licenses_crud.add_license(conn, license_data)
            if created_id:
                logger.info(f"Successfully created default admin license {created_id} (key: {license_key}) for user {user_id}, valid until {expiration.isoformat()}.")
                # Fetch the newly created license to return its full details
                newly_created_license_details = licenses_crud.get_active_license_for_user(conn, user_id)
                if newly_created_license_details:
                     return True, "Licence administrateur par défaut créée avec succès.", newly_created_license_details
                else:
                    # This case should ideally not happen if add_license and get_active_license work
                    logger.error(f"Failed to retrieve details of newly created admin license for user {user_id} despite successful add.")
                    return False, "Erreur: Impossible de récupérer les détails de la nouvelle licence admin.", None
            else:
                logger.error(f"Failed to add default admin license to database for user {user_id}.")
                return False, "Échec de la création de la licence administrateur par défaut en base de données.", None
        except AttributeError as e_attr_cdal: # Specific catch for AttributeError
            logger.error(f"AttributeError in create_default_admin_license for user {user_id}. Conn type: {type(conn)}. Error: {e_attr_cdal}", exc_info=True)
            # import traceback # Already imported at module level
            logger.error(f"Traceback for AttributeError in create_default_admin_license:\n{traceback.format_exc()}")
            return False, f"Erreur interne (AttributeError) lors de la création de la licence admin: {e_attr_cdal}", None
        except Exception as e: # General catch-all
            logger.error(f"Exception while creating default admin license for user {user_id}: {e}", exc_info=True)
            return False, "Erreur interne lors de la création de la licence administrateur.", None

    def get_current_license_display_info(self, conn: sqlite3.Connection, user_id: str) -> str:
        """Provides a string summary of the user's current license status."""
        is_valid, message, details = self.check_license_validity(conn, user_id)
        if is_valid and details:
            return f"Type: {details.get('license_type', 'N/A')}, Expire le: {details.get('expiration_date', 'N/A')}"
        elif details: # License exists but is not valid (e.g. expired)
             return f"Licence Invalide. Type: {details.get('license_type', 'N/A')}, Message: {message}"
        return message or "Statut de la licence inconnu."


    def activate_license(self, conn: sqlite3.Connection, user_id: str, license_key: str) -> tuple[bool, str | None, dict | None]:
        """
        Activates a license using a provided key.
        Placeholder: More complex logic for key validation, matching to product, etc., would go here.
        """
        logger.info(f"Attempting to activate license key {license_key} for user {user_id}.")
        # 1. Check if key exists and is not already active for another user/machine (complex)
        # For this version, we'll assume a key can be activated if found and not currently active for this user.

        existing_license_by_key = licenses_crud.get_license_by_key(conn, license_key)
        if not existing_license_by_key:
            return False, "Clé de licence invalide ou inexistante.", None

        if existing_license_by_key['user_id'] != user_id and existing_license_by_key['is_active']:
             # Simplified: If key is active for another user. Real check might involve machine_info too.
            return False, "Cette clé de licence est déjà active pour un autre utilisateur.", None

        if existing_license_by_key['user_id'] == user_id and existing_license_by_key['is_active']:
            # Check if it's actually valid or expired
            is_valid, msg, details = self.check_license_validity(conn, user_id)
            if is_valid:
                return True, "Cette clé de licence est déjà active et valide pour votre compte.", details
            # If not valid (e.g. expired but still marked active), allow re-activation/update below

        # Deactivate any other active licenses for this user
        current_active_license = licenses_crud.get_active_license_for_user(conn, user_id)
        if current_active_license and current_active_license['license_id'] != existing_license_by_key['license_id']:
            licenses_crud.deactivate_license(conn, current_active_license['license_id'])

        # Activate the new one
        now = datetime.now(timezone.utc)
        # Assuming the license_key comes with pre-defined expiration, type etc.
        # For this placeholder, we'll just mark it active and set activation date.
        # A real system might fetch license terms based on the key from a server.
        update_data = {
            'user_id': user_id, # Associate with this user
            'is_active': True,
            'activation_date': now.isoformat(),
            'machine_info': self.get_machine_identifier()
            # expiration_date should ideally be part of the license_key's definition
            # If activating a key means "start its term now", you might calculate expiration here.
        }

        # If the license key is for a specific term (e.g. 1 year from activation)
        # and this logic is not handled by an external server:
        # if existing_license_by_key.get("duration_days"): # Hypothetical field
        #     update_data['expiration_date'] = (now + timedelta(days=existing_license_by_key["duration_days"])).isoformat()

        if licenses_crud.update_license(conn, existing_license_by_key['license_id'], update_data):
            logger.info(f"License key {license_key} activated successfully for user {user_id}.")
            updated_license_details = licenses_crud.get_active_license_for_user(conn, user_id)
            return True, "Licence activée avec succès.", updated_license_details
        else:
            return False, "Échec de la mise à jour de la licence en base de données lors de l'activation.", None

    def activate_free_license(self, conn: sqlite3.Connection, user_id: str) -> tuple[bool, str | None, dict | None]:
        """Activates a basic 'gratuit' license with a short expiration (e.g., 7 days trial)."""
        logger.info(f"Attempting to activate free/trial license for user {user_id}")

        # Deactivate any existing active licenses for this user
        existing_license = licenses_crud.get_active_license_for_user(conn, user_id)
        if existing_license:
            logger.info(f"Deactivating existing license {existing_license['license_id']} for user {user_id} before creating free trial.")
            licenses_crud.deactivate_license(conn, existing_license['license_id'])

        now = datetime.now(timezone.utc)
        expiration = now + timedelta(days=7) # 7-day trial
        new_license_id = str(uuid.uuid4())
        license_key = f"FREE-TRIAL-{new_license_id[:8].upper()}"

        license_data = {
            'license_id': new_license_id,
            'user_id': user_id,
            'license_type': LICENSE_TYPES["GRATUIT"],
            'license_key': license_key,
            'activation_date': now,
            'expiration_date': expiration,
            'machine_info': self.get_machine_identifier(),
            'is_active': True
        }

        created_id = licenses_crud.add_license(conn, license_data)
        if created_id:
            logger.info(f"Successfully created free trial license {created_id} for user {user_id}, valid until {expiration.isoformat()}.")
            newly_created_license_details = licenses_crud.get_active_license_for_user(conn, user_id)
            if newly_created_license_details:
                 return True, "Licence d'essai gratuite activée.", newly_created_license_details
            else:
                logger.error(f"Failed to retrieve details of newly created free license for user {user_id}.")
                return False, "Erreur: Impossible de récupérer les détails de la nouvelle licence gratuite.", None
        else:
            logger.error(f"Failed to add free trial license to database for user {user_id}.")
            return False, "Échec de la création de la licence d'essai gratuite en base de données.", None


# Instantiate the manager for the application to use
manager = LicenseManager()

# Define Feature Constants
# These constants represent distinct features or modules controllable by licenses.
FEATURE_BASIC_CLIENT_DOCS = "feature_basic_client_docs" # Basic document management for clients
FEATURE_PROJECT_MANAGEMENT = "feature_project_management"   # Access to the project management module
FEATURE_STATISTICS_MODULE = "feature_statistics_module"     # Access to statistics and reporting
FEATURE_PRODUCT_MANAGEMENT = "feature_product_management"   # Access to global product management
FEATURE_PARTNER_MANAGEMENT = "feature_partner_management"   # Access to partner management
FEATURE_INVENTORY_MANAGEMENT = "feature_inventory_management" # Access to inventory/stock management
FEATURE_RECRUITMENT_MODULE = "feature_recruitment_module"   # Access to recruitment tools
FEATURE_BOTPRESS_INTEGRATION = "feature_botpress_integration" # Chatbot integration
FEATURE_CALENDAR_MODULE = "feature_calendar_module"         # Calendar functionality
FEATURE_EXPERIENCE_MANAGEMENT = "feature_experience_management" # Knowledge base
FEATURE_ADVANCED_REPORTING = "feature_advanced_reporting"   # More detailed or custom reports
FEATURE_API_ACCESS = "feature_api_access"                   # Programmatic API access
FEATURE_USER_MANAGEMENT_FULL = "feature_user_management_full" # Ability to manage users, roles (distinct from self-account edit)
FEATURE_SETTINGS_MANAGEMENT = "feature_settings_management" # Access to application-wide settings
FEATURE_COMMANDES_MANAGEMENT = "feature_commandes_management" # Access to order management dashboard
FEATURE_CALCULATOR_MODULE = "feature_calculator_module"       # Access to calculators

# License Features Map
# Maps license types to a set of allowed feature constants.
LICENSE_FEATURES_MAP = {
    LICENSE_TYPES["GRATUIT"]: {
        FEATURE_BASIC_CLIENT_DOCS,
        # Potentially a very limited version of another module for trial
    },
    LICENSE_TYPES["LIMITE"]: {
        FEATURE_BASIC_CLIENT_DOCS,
        FEATURE_PROJECT_MANAGEMENT,
        FEATURE_PRODUCT_MANAGEMENT,
        FEATURE_COMMANDES_MANAGEMENT,
        FEATURE_CALENDAR_MODULE,
        FEATURE_CALCULATOR_MODULE,
        # Add other features appropriate for a 'limited' tier
    },
    LICENSE_TYPES["COMPLET"]: {
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
        FEATURE_API_ACCESS, # Example: API access only for top tier
        FEATURE_USER_MANAGEMENT_FULL, # Full user management for admins with complete license
        FEATURE_SETTINGS_MANAGEMENT, # Full settings management
        FEATURE_COMMANDES_MANAGEMENT,
        FEATURE_CALCULATOR_MODULE,
        # Add all other features
    },
}

class LicenseManager:
    ADMIN_USERNAME = "admin" # Class attribute

    def __init__(self):
        # licenses_crud is a module, not a class to instantiate here usually
        # We'll call its functions directly: licenses_crud.add_license(...) etc.
        logger.info("LicenseManager initialized.")

    def get_allowed_features(self, license_type: str) -> set[str]:
        """
        Returns a set of feature constants allowed for the given license type.
        If the license type is unknown, returns an empty set.
        """
        if license_type not in LICENSE_FEATURES_MAP:
            logger.warning(f"Unknown license type '{license_type}' provided to get_allowed_features. Returning empty set.")
            return set()
        return LICENSE_FEATURES_MAP[license_type]

    def get_machine_identifier(self) -> str:
        """
        Retrieves a unique identifier for the current machine.
        Placeholder: In a real scenario, this would involve OS-specific calls.
        """
        # For now, a static placeholder. In a real app, this needs to be robust.
        # Consider using libraries like 'machineid' or platform-specific APIs.
        # IMPORTANT: This ID should be stable for the machine.
        try:
            # Example using a hypothetical library or OS call
            # import machineid
            # current_machine_id = machineid.id()
            # For this placeholder:
            current_machine_id = "static_placeholder_machine_id_v1"
            logger.debug(f"Retrieved machine identifier: {current_machine_id}")
            return current_machine_id
        except Exception as e:
            logger.error(f"Error getting machine identifier: {e}", exc_info=True)
            return "error_getting_machine_id"

    def check_license_validity(self, conn: sqlite3.Connection, user_id: str) -> tuple[bool, str | None, dict | None]:
        """
        Checks if the user has a valid, active, and non-expired license.
        Returns:
            tuple[bool, str | None, dict | None]: (is_valid, message, license_details)
            license_details now also includes 'allowed_features' if valid.
        """
        if not conn or not user_id:
            logger.error("check_license_validity: Missing connection or user_id.")
            return False, "Internal error: Missing connection or user ID.", None

        try:
            license_details = licenses_crud.get_active_license_for_user(conn, user_id)

            if not license_details:
                logger.info(f"No active license found for user_id: {user_id}.")
                return False, "Aucune licence active trouvée pour cet utilisateur.", None

            expiration_date_str = license_details.get('expiration_date')
            if expiration_date_str:
                try:
                    expiration_date = datetime.fromisoformat(expiration_date_str.replace("Z", "+00:00"))
                    if expiration_date.tzinfo is None:
                        expiration_date = expiration_date.replace(tzinfo=timezone.utc)

                    if expiration_date < datetime.now(timezone.utc):
                        logger.warning(f"License {license_details['license_id']} for user {user_id} has expired on {expiration_date_str}.")
                        return False, "Votre licence a expiré.", license_details
                except ValueError:
                    logger.error(f"Invalid date format for expiration_date ('{expiration_date_str}') for license {license_details['license_id']}.")
                    return False, "Format de date d'expiration de licence invalide.", license_details

            logger.info(f"License {license_details['license_id']} for user {user_id} is valid.")
            # Add allowed features to the returned details
            license_details['allowed_features'] = self.get_allowed_features(license_details.get('license_type', ''))
            return True, "Licence valide.", license_details

        except Exception as e:
            logger.error(f"Error during check_license_validity for user {user_id}: {e}", exc_info=True)
            return False, "Erreur interne lors de la vérification de la licence.", None

    def create_default_admin_license(self, conn: sqlite3.Connection, user_id: str) -> tuple[bool, str | None, dict | None]:
        """
        Creates a default 6-month 'complet' license for the specified user_id.
        Typically used for the admin user on first setup or if their license is missing/invalid.
        """
        if not conn or not user_id:
            logger.error("create_default_admin_license: Missing connection or user_id.")
            return False, "Internal error: Missing connection or user ID for admin license creation.", None

        logger.info(f"Attempting to create default admin license for user_id: {user_id}")

        try:
            existing_license = licenses_crud.get_active_license_for_user(conn, user_id)
            if existing_license:
                logger.info(f"Deactivating existing license {existing_license['license_id']} for admin user {user_id} before creating new default one.")
                licenses_crud.deactivate_license(conn, existing_license['license_id'])

            now = datetime.now(timezone.utc)
            expiration = now + timedelta(days=6 * 30) # Approx 6 months

            new_license_id = str(uuid.uuid4())
            license_key = f"ADMIN-DEFAULT-{new_license_id[:8].upper()}"

            license_data = {
                'license_id': new_license_id,
                'user_id': user_id,
                'license_type': DEFAULT_ADMIN_LICENSE_TYPE,
                'license_key': license_key,
                'activation_date': now,
                'expiration_date': expiration,
                'machine_info': self.get_machine_identifier(),
                'is_active': True
            }

            created_id = licenses_crud.add_license(conn, license_data)
            if created_id:
                logger.info(f"Successfully created default admin license {created_id} (key: {license_key}) for user {user_id}, valid until {expiration.isoformat()}.")
                newly_created_license_details = licenses_crud.get_active_license_for_user(conn, user_id)
                if newly_created_license_details:
                     newly_created_license_details['allowed_features'] = self.get_allowed_features(newly_created_license_details.get('license_type', ''))
                     return True, "Licence administrateur par défaut créée avec succès.", newly_created_license_details
                else:
                    logger.error(f"Failed to retrieve details of newly created admin license for user {user_id} despite successful add.")
                    return False, "Erreur: Impossible de récupérer les détails de la nouvelle licence admin.", None
            else:
                logger.error(f"Failed to add default admin license to database for user {user_id}.")
                return False, "Échec de la création de la licence administrateur par défaut en base de données.", None

        except Exception as e:
            logger.error(f"Exception while creating default admin license for user {user_id}: {e}", exc_info=True)
            return False, "Erreur interne lors de la création de la licence administrateur.", None

    def get_current_license_display_info(self, conn: sqlite3.Connection, user_id: str) -> str:
        """Provides a string summary of the user's current license status."""
        is_valid, message, details = self.check_license_validity(conn, user_id)
        if is_valid and details:
            return f"Type: {details.get('license_type', 'N/A')}, Expire le: {details.get('expiration_date', 'N/A')}"
        elif details:
             return f"Licence Invalide. Type: {details.get('license_type', 'N/A')}, Message: {message}"
        return message or "Statut de la licence inconnu."


    def _verify_signed_license_payload(self, payload_json_str: str, signature_bytes: bytes) -> bool:
        """Verifies the signature of the JSON payload."""
        public_key = load_public_key()
        if not public_key:
            logger.error("Public key not loaded. Cannot verify license signature.")
            return False
        try:
            public_key.verify(
                signature_bytes,
                payload_json_str.encode('utf-8'),
                asym_padding.PSS(
                    mgf=asym_padding.MGF1(hashes.SHA256()),
                    salt_length=asym_padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except InvalidSignature:
            logger.warning("License signature verification failed: Invalid signature.")
            return False
        except Exception as e:
            logger.error(f"Error during license signature verification: {e}", exc_info=True)
            return False

    def activate_license(self, conn: sqlite3.Connection, user_id: str, signed_license_key_str: str) -> tuple[bool, str | None, dict | None]:
        """
        Activates a license using a provided signed key string.
        Format: base64_urlsafe(json_payload).base64_urlsafe(signature)
        """
        logger.info(f"Attempting to activate signed license key for user {user_id}.")

        if LOADED_PUBLIC_KEY is None:
            return False, "Erreur de configuration: Clé publique de vérification de licence non chargée.", None

        try:
            parts = signed_license_key_str.split('.')
            if len(parts) != 2:
                return False, "Format de clé de licence invalide.", None

            payload_b64, signature_b64 = parts

            # Decode payload (add padding if removed by rstrip('='))
            payload_json_str = base64.urlsafe_b64decode(payload_b64 + '=' * (-len(payload_b64) % 4)).decode('utf-8')
            # Decode signature
            signature_bytes = base64.urlsafe_b64decode(signature_b64 + '=' * (-len(signature_b64) % 4))

            if not self._verify_signed_license_payload(payload_json_str, signature_bytes):
                return False, "Signature de la clé de licence invalide.", None

            # Signature is valid, parse payload
            key_params = json.loads(payload_json_str)
            logger.info(f"License key signature verified. Payload: {key_params}")

            # Extract necessary parameters from the key
            license_type_from_key = key_params.get('license_type')
            expiration_date_from_key_str = key_params.get('expiration_date') # Expected YYYY-MM-DD
            # key_id_from_key = key_params.get('key_id') # Unique ID of the key itself

            if not license_type_from_key or license_type_from_key not in LICENSE_TYPES.values():
                return False, f"Type de licence '{license_type_from_key}' invalide dans la clé.", None

            # Convert expiration date string to datetime object if present
            expiration_date_obj = None
            if expiration_date_from_key_str:
                try:
                    expiration_date_obj = datetime.strptime(expiration_date_from_key_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                except ValueError:
                    return False, f"Format de date d'expiration '{expiration_date_from_key_str}' invalide dans la clé.", None

            # Activation Check: Prevent reuse of the same key string if already activated for this machine
            # (More sophisticated checks based on key_id and user_limit could be added if key_id is globally unique and managed by a central server)
            current_machine_id = self.get_machine_identifier()
            existing_activation = licenses_crud.get_license_by_key_and_machine(conn, signed_license_key_str, current_machine_id)

            if existing_activation:
                # Key already activated on this machine. Check if it's for the current user and still valid.
                if existing_activation['user_id'] == user_id:
                    is_valid_existing, msg_existing, details_existing = self.check_license_validity(conn, user_id)
                    if is_valid_existing:
                        return True, "Cette clé de licence est déjà active et valide pour votre compte sur cette machine.", details_existing
                    else:
                        # It was active for this user on this machine but expired/invalidated. Allow re-activation.
                        logger.info(f"Re-activating previously activated key {signed_license_key_str} for user {user_id} on machine {current_machine_id} as it's no longer valid ({msg_existing}).")
                else:
                    # Key activated on this machine but for a different user. Policy decision needed.
                    # For now, let's deny, assuming one key activation per machine, regardless of user.
                    # Or, if user_limit > 1 in key_params, this logic would need to be more complex.
                    logger.warning(f"License key {signed_license_key_str} already activated on machine {current_machine_id} by user {existing_activation['user_id']}.")
                    return False, "Cette clé de licence a déjà été activée sur cette machine par un autre utilisateur.", None


            # Deactivate any other active licenses for this user
            current_active_license = licenses_crud.get_active_license_for_user(conn, user_id)
            if current_active_license:
                licenses_crud.deactivate_license(conn, current_active_license['license_id'])

            # Add new license record based on signed key parameters
            new_license_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)

            license_data_to_add = {
                'license_id': new_license_id,
                'user_id': user_id,
                'license_type': license_type_from_key,
                'license_key': signed_license_key_str, # Store the full signed key
                'activation_date': now,
                'expiration_date': expiration_date_obj, # This can be None if key has no expiration
                'machine_info': current_machine_id,
                'is_active': True
            }

            created_db_id = licenses_crud.add_license(conn, license_data_to_add)
            if created_db_id:
                logger.info(f"Signed license key activated successfully for user {user_id}. DB ID: {created_db_id}")
                # Fetch the newly created license to return its full details, including allowed_features
                final_license_details = licenses_crud.get_active_license_for_user(conn, user_id)
                if final_license_details:
                    final_license_details['allowed_features'] = self.get_allowed_features(final_license_details.get('license_type', ''))
                return True, "Licence activée avec succès.", final_license_details
            else:
                return False, "Échec de l'enregistrement de la licence activée en base de données.", None

        except json.JSONDecodeError:
            logger.error("Failed to decode license payload JSON.", exc_info=True)
            return False, "Format de données de clé de licence invalide.", None
        except base64.binascii.Error: # Error from b64decode
            logger.error("Failed to decode base64 part of the license key.", exc_info=True)
            return False, "Encodage de clé de licence invalide.", None
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'activation de la clé de licence: {e}", exc_info=True)
            return False, f"Erreur inattendue: {str(e)}", None

    def activate_free_license(self, conn: sqlite3.Connection, user_id: str) -> tuple[bool, str | None, dict | None]:
        """Activates a basic 'gratuit' license with a short expiration (e.g., 7 days trial)."""
        logger.info(f"Attempting to activate free/trial license for user {user_id}")

        existing_license = licenses_crud.get_active_license_for_user(conn, user_id)
        if existing_license:
            logger.info(f"Deactivating existing license {existing_license['license_id']} for user {user_id} before creating free trial.")
            licenses_crud.deactivate_license(conn, existing_license['license_id'])

        now = datetime.now(timezone.utc)
        expiration = now + timedelta(days=7)
        new_license_id = str(uuid.uuid4())
        license_key = f"FREE-TRIAL-{new_license_id[:8].upper()}"

        license_data = {
            'license_id': new_license_id,
            'user_id': user_id,
            'license_type': LICENSE_TYPES["GRATUIT"],
            'license_key': license_key,
            'activation_date': now,
            'expiration_date': expiration,
            'machine_info': self.get_machine_identifier(),
            'is_active': True
        }

        created_id = licenses_crud.add_license(conn, license_data)
        if created_id:
            logger.info(f"Successfully created free trial license {created_id} for user {user_id}, valid until {expiration.isoformat()}.")
            newly_created_license_details = licenses_crud.get_active_license_for_user(conn, user_id)
            if newly_created_license_details:
                 newly_created_license_details['allowed_features'] = self.get_allowed_features(newly_created_license_details.get('license_type', ''))
                 return True, "Licence d'essai gratuite activée.", newly_created_license_details
            else:
                logger.error(f"Failed to retrieve details of newly created free license for user {user_id}.")
                return False, "Erreur: Impossible de récupérer les détails de la nouvelle licence gratuite.", None
        else:
            logger.error(f"Failed to add free trial license to database for user {user_id}.")
            return False, "Échec de la création de la licence d'essai gratuite en base de données.", None


# Instantiate the manager for the application to use
manager = LicenseManager()

__all__ = [
    'manager',
    'LICENSE_TYPES',
    'LICENSE_FEATURES_MAP',
    'FEATURE_BASIC_CLIENT_DOCS', 'FEATURE_PROJECT_MANAGEMENT', 'FEATURE_STATISTICS_MODULE',
    'FEATURE_PRODUCT_MANAGEMENT', 'FEATURE_PARTNER_MANAGEMENT', 'FEATURE_INVENTORY_MANAGEMENT',
    'FEATURE_RECRUITMENT_MODULE', 'FEATURE_BOTPRESS_INTEGRATION', 'FEATURE_CALENDAR_MODULE',
    'FEATURE_EXPERIENCE_MANAGEMENT', 'FEATURE_ADVANCED_REPORTING', 'FEATURE_API_ACCESS',
    'FEATURE_USER_MANAGEMENT_FULL', 'FEATURE_SETTINGS_MANAGEMENT',
    'FEATURE_COMMANDES_MANAGEMENT', 'FEATURE_CALCULATOR_MODULE'
]
