# This module will contain the logic for biometric authentication.
import platform
import logging
from app.db.cruds.users import users_crud

# security_module/biometric_auth.py
"""
Provides a unified BiometricAuthenticator class that acts as a facade for
OS-specific biometric handlers (Windows, macOS) and a local voice handler.

This module allows the main application to interact with biometric functionalities
through a common interface, abstracting away the OS-level details.
"""
import platform
import logging
from app.db.cruds.users import users_crud

# Dynamically import handlers based on OS
logger = logging.getLogger(__name__)
windows_handler_module = None
macos_handler_module = None
local_voice_handler_module = None # For future local voice processing

os_name = platform.system()

if os_name == "Windows":
    try:
        from .os_handlers import windows_handler as wh_module
        windows_handler_module = wh_module
        logger.info("Windows OS detected. Windows handler module loaded.")
    except ImportError as e:
        logger.error(f"Failed to import Windows biometric handler: {e}")
elif os_name == "Darwin": # macOS
    try:
        from .os_handlers import macos_handler as mh_module
        macos_handler_module = mh_module
        logger.info("macOS detected. macOS handler module loaded.")
    except ImportError as e:
        logger.error(f"Failed to import macOS biometric handler: {e}")
# Placeholder for Linux handler import
# elif os_name == "Linux":
#     try:
#         from .os_handlers import linux_handler as lh_module
#         linux_handler_module = lh_module
#         logger.info("Linux OS detected. Linux handler module loaded.")
#     except ImportError as e:
#         logger.error(f"Failed to import Linux biometric handler: {e}")

# try:
#     from .os_handlers import local_voice_handler as lvh_module
#     local_voice_handler_module = lvh_module
#     logger.info("Local voice handler module loaded.")
# except ImportError:
#     logger.warning("Local voice handler module not found or import error. Voice biometrics might be unavailable.")


class BiometricAuthenticator:
    """
    Facade class for handling various biometric authentication methods.
    It detects the operating system and loads the appropriate OS-specific handler
    for fingerprint and face authentication. It also loads a local handler for
    voice authentication if available.
    """

    def __init__(self, window_handle_provider=None):
        """
        Initializes the BiometricAuthenticator and loads appropriate handlers.

        Args:
            window_handle_provider (callable, optional): A function that can be called
                to get the current parent window handle (e.g., `self.winId()` from a QWidget).
                This may be needed by some OS-level biometric UI prompts.
        """
        self.handler = None # For OS-specific fingerprint/face
        self.voice_handler = None # For local voice handling
        self.window_handle_provider = window_handle_provider

        if os_name == "Windows" and windows_handler_module:
            self.handler = windows_handler_module.WindowsBiometricHandler()
            logger.info("Using WindowsBiometricHandler.")
        elif os_name == "Darwin" and macos_handler_module:
            self.handler = macos_handler_module.MacOSBiometricHandler()
            logger.info("Using MacOSBiometricHandler.")
        # elif os_name == "Linux" and linux_handler_module:
        #     self.handler = linux_handler_module.LinuxBiometricHandler()
        #     logger.info("Using LinuxBiometricHandler.")

        # self.voice_handler = None
        # if local_voice_handler_module:
        #      self.voice_handler = lvh_module.LocalVoiceHandler()
        #      logger.info("Using LocalVoiceHandler for voice biometrics.")

        if not self.handler and not self.voice_handler: # Check if any handler is set
            logger.warning(f"No suitable biometric handler initialized for OS: {os_name}. Biometric functions will be unavailable.")

    def get_window_handle(self):
        if self.window_handle_provider:
            try:
                return self.window_handle_provider()
            except Exception as e:
                logger.error(f"Error getting window handle from provider: {e}")
        return None

    def is_method_available(self, method: str) -> bool:
        """
        Checks if a specific biometric method (e.g., "fingerprint", "face", "voice")
        is available on the current system through the appropriate handler.
        Args:
            method: The biometric method to check.
        Returns:
            True if the method is available, False otherwise.
        """
        if method == "voice":
            return self.voice_handler.is_available() if self.voice_handler else False
        elif self.handler: # For fingerprint and face
            return self.handler.is_available(method)
        logger.debug(f"is_method_available: No suitable handler for method '{method}' or OS '{os_name}'.")
        return False

    def is_method_enabled_for_user(self, user_id: str, method: str) -> bool:
        """
        Checks if a specific biometric method is marked as enabled for the user
        in the application's database.
        Args:
            user_id: The application-specific ID of the user.
            method: The biometric method to check.
        Returns:
            True if enabled in the database, False otherwise.
        """
        if not user_id:
            logger.warning(f"Cannot check biometric status for method '{method}': user_id is None.")
            return False

        settings = users_crud.get_biometric_auth_status(user_id)
        if settings:
            if method == "fingerprint":
                return settings.get('is_fingerprint_auth_enabled', False)
            elif method == "face":
                return settings.get('is_face_auth_enabled', False)
            elif method == "voice":
                return settings.get('is_voice_auth_enabled', False)
        logger.warning(f"Could not retrieve biometric settings for app user {user_id} or method {method} not applicable in DB.")
        return False

    def enroll_biometric(self, user_app_id: str, method: str) -> bool:
        """
        Initiates the enrollment process for a given biometric method for the specified user.
        For fingerprint/face, this typically guides the user to OS settings or calls OS enrollment UI.
        For voice, this uses the local voice handler for enrollment.
        Updates the application's database if enrollment is successful.

        Args:
            user_app_id: The application-specific ID of the user.
            method: The biometric method ('fingerprint', 'face', 'voice').
        Returns:
            True if enrollment (OS/local) and subsequent DB update were successful, False otherwise.
        """
        enroll_success = False
        # voice_profile_id_to_store = None # Not currently used as local_voice_handler uses deterministic paths

        if method == "voice":
            if self.voice_handler and self.voice_handler.is_available():
                logger.info(f"Attempting voice enrollment for {user_app_id} via LocalVoiceHandler.")
                enroll_success = self.voice_handler.enroll(user_app_id)
            else:
                logger.warning(f"Cannot enroll voice: LocalVoiceHandler not available or not usable.")
                return False
        elif self.handler and self.is_method_available(method): # Fingerprint or Face via OS handler
            window_h = self.get_window_handle()
            enroll_success = self.handler.enroll(method, window_handle=window_h)
        else:
            logger.warning(f"Cannot enroll {method}: No suitable OS handler or method not available.")
            return False

        if enroll_success:
            logger.info(f"Enrollment for {method} successful for app user {user_app_id} (Handler part).")
            if users_crud.set_biometric_auth_status(user_app_id, method, enabled=True, template_id=None):
                logger.info(f"Database updated: {method} enabled for app user {user_app_id}.")
                return True
            else:
                logger.error(f"Enrollment for {method} (Handler) successful, but FAILED to mark as enabled in DB for app user {user_app_id}.")
                if method == "voice" and self.voice_handler: # Attempt cleanup if DB fails for voice
                    self.voice_handler.delete_enrollment(user_app_id)
                # For OS fingerprint/face, OS enrollment is system-wide; can't easily roll back just for this app.
                return False
        else:
            logger.warning(f"Enrollment for {method} failed for app user {user_app_id} (Handler part).")
            users_crud.set_biometric_auth_status(user_app_id, method, enabled=False, template_id=None) # Ensure disabled in DB
            return False

    def verify_biometric(self, user_app_id: str, method: str) -> bool:
        """
        Attempts to verify the user using the specified biometric method.
        The `user_app_id` is used to first check if the method is enabled for this user in the app's DB.
        Then, it calls the appropriate handler (OS or local voice) for actual verification.

        Args:
            user_app_id: The application-specific ID of the user attempting to log in.
            method: The biometric method ('fingerprint', 'face', 'voice').
        Returns:
            True if verification is successful, False otherwise.
        """
        if not self.is_method_enabled_for_user(user_app_id, method): # Check DB enablement first
            logger.warning(f"Cannot verify {method} for app user {user_app_id}: method not enabled for this user in app DB.")
            return False

        # Proceed with actual handler verification only if available and enabled in DB
        if method == "voice":
            if self.voice_handler and self.voice_handler.is_available():
                user_details = users_crud.get_user_by_id(user_app_id) # For username_hint
                username_hint = user_details.get('username') if user_details else ""
                logger.info(f"Attempting voice verification for {user_app_id} (hint: {username_hint}) via LocalVoiceHandler.")
                return self.voice_handler.verify(user_app_id, username_hint=username_hint)
            else:
                logger.warning(f"Cannot verify voice: LocalVoiceHandler not available or not usable (despite being enabled in DB).")
                return False
        elif self.handler and self.is_method_available(method): # Fingerprint or Face
            user_details = users_crud.get_user_by_id(user_app_id)
            username_hint = user_details.get('username') if user_details else ""
            window_h = self.get_window_handle()

            verification_success = self.handler.verify(method, username_hint=username_hint, window_handle=window_h)
            if verification_success:
                logger.info(f"OS-level verification for {method} successful for app user {user_app_id}.")
                return True
            else:
                logger.warning(f"OS-level verification for {method} failed for app user {user_app_id}.")
                return False
        else: # Should be caught by is_method_enabled_for_user or is_method_available if logic is sound
            logger.warning(f"Cannot verify {method}: No suitable handler or method not available (despite being enabled in DB).")
            return False

    def disable_biometric_method(self, user_app_id: str, method: str) -> bool:
        """
        Disables a biometric method for a user in the application's database.
        Also attempts to trigger any necessary cleanup via the relevant handler (e.g., deleting local voice profile).
        Args:
            user_app_id: The application-specific ID of the user.
            method: The biometric method to disable.
        Returns:
            True if the method was successfully marked as disabled in the database, False otherwise.
            Note: OS-level enrollment for fingerprint/face is typically not removed by the app.
        """
        cleanup_successful_or_not_applicable = True
        if method == "voice":
            if self.voice_handler:
                logger.info(f"Attempting to delete voice enrollment data for {user_app_id} as part of disabling.")
                cleanup_successful_or_not_applicable = self.voice_handler.delete_enrollment(user_app_id)
            else:
                logger.warning(f"Voice handler not available for deleting enrollment for {user_app_id} during disable.")
        elif self.handler and hasattr(self.handler, 'delete_enrollment'):
            # For OS handlers, delete_enrollment usually guides user to OS settings.
            logger.info(f"Calling OS handler to guide user for potential OS-level enrollment deletion for {method}.")
            self.handler.delete_enrollment(method) # This is a guidance step for OS handlers.

        # Regardless of OS/local cleanup result, update the application's database.
        if users_crud.set_biometric_auth_status(user_app_id, method, enabled=False, template_id=None):
            logger.info(f"Biometric method {method} disabled in DB for app user {user_app_id}.")
            return True
        else:
            logger.error(f"Failed to disable biometric method {method} in DB for app user {user_app_id}.")
            return False

    # Alias methods
    def enroll_fingerprint(self, user_id: str) -> bool: return self.enroll_biometric(user_id, "fingerprint")
    def verify_fingerprint(self, user_id: str) -> bool: return self.verify_biometric(user_id, "fingerprint")
    def disable_fingerprint(self, user_id: str) -> bool: return self.disable_biometric_method(user_id, "fingerprint")

    def enroll_face(self, user_id: str) -> bool: return self.enroll_biometric(user_id, "face")
    def verify_face(self, user_id: str) -> bool: return self.verify_biometric(user_id, "face")
    def disable_face(self, user_id: str) -> bool: return self.disable_biometric_method(user_id, "face")

    def enroll_voice(self, user_id: str) -> bool: return self.enroll_biometric(user_id, "voice") # Will use local voice handler logic if present
    def verify_voice(self, user_id: str) -> bool: return self.verify_biometric(user_id, "voice") # Ditto
    def disable_voice(self, user_id: str) -> bool: return self.disable_biometric_method(user_id, "voice")


if __name__ == '__main__':
    # Example usage for testing the module directly
    # This requires the DB to be initialized and a user to exist.
    # For standalone testing, you might need to mock users_crud or ensure DB setup.
    print("BiometricAuthenticator Self-Test (requires DB and user 'testuser')")

    # Setup a mock users_crud for standalone testing if db/cruds/users_crud.py is not available
    # or if you don't want to interact with the actual database during this test.
    class MockUsersCrud:
        _user_bio_settings = {}

        def get_biometric_auth_status(self, user_id):
            print(f"MOCK_CRUD: get_biometric_auth_status for {user_id}")
            return self._user_bio_settings.get(user_id, {
                'is_fingerprint_auth_enabled': False, 'fingerprint_template_id': None,
                'is_face_auth_enabled': False, 'face_template_id': None,
                'is_voice_auth_enabled': False, 'voice_profile_id': None,
            })

        def set_biometric_auth_status(self, user_id, method, enabled, template_id=None):
            print(f"MOCK_CRUD: set_biometric_auth_status for {user_id}, method {method}, enabled {enabled}, template_id {template_id}")
            if user_id not in self._user_bio_settings:
                self._user_bio_settings[user_id] = {}

            field_enabled = f"is_{method}_auth_enabled"
            field_template = f"{method}_template_id" if method != "voice" else "voice_profile_id"

            self._user_bio_settings[user_id][field_enabled] = enabled
            self._user_bio_settings[user_id][field_template] = template_id if enabled else None
            return True

    # Replace the actual users_crud with the mock for this test block
    users_crud = MockUsersCrud()

    authenticator = BiometricAuthenticator()
    test_user_id = "test_user_001"

    print(f"\n--- Testing Fingerprint Enrollment for user {test_user_id} ---")
    if authenticator.enroll_fingerprint(test_user_id):
        print(f"Fingerprint enrollment for {test_user_id} reported as successful.")
    else:
        print(f"Fingerprint enrollment for {test_user_id} reported as failed.")

    print(f"\n--- Checking if Fingerprint is Enabled for user {test_user_id} ---")
    if authenticator.is_method_enabled_for_user(test_user_id, "fingerprint"):
        print(f"Fingerprint is ENABLED for user {test_user_id}.")
    else:
        print(f"Fingerprint is DISABLED for user {test_user_id}.")

    print(f"\n--- Testing Fingerprint Verification for user {test_user_id} ---")
    if authenticator.verify_fingerprint(test_user_id):
        print(f"Fingerprint verification for {test_user_id} successful.")
    else:
        print(f"Fingerprint verification for {test_user_id} failed.")

    print(f"\n--- Disabling Fingerprint for user {test_user_id} ---")
    if authenticator.disable_fingerprint(test_user_id):
        print(f"Fingerprint disabled for {test_user_id}.")
    else:
        print(f"Failed to disable fingerprint for {test_user_id}.")

    print(f"\n--- Checking if Fingerprint is Enabled for user {test_user_id} (after disable) ---")
    if authenticator.is_method_enabled_for_user(test_user_id, "fingerprint"):
        print(f"Fingerprint is ENABLED for user {test_user_id}.")
    else:
        print(f"Fingerprint is DISABLED for user {test_user_id}.")
