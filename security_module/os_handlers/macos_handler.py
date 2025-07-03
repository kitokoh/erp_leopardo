# security_module/os_handlers/macos_handler.py
"""
Handles macOS Local Authentication interactions (Touch ID, Face ID) using PyObjC.

This module allows the application to:
- Check if biometric authentication (Touch ID or Face ID) is available and configured.
- Request biometric verification from the user.

Enrollment of biometrics (adding fingerprints or setting up Face ID) is managed
by the user through macOS System Settings (System Preferences). This handler
does not perform enrollment directly.
"""
import logging
import objc
import threading
from Foundation import NSObject # For PyObjC block signature if needed, or direct callable.

logger = logging.getLogger(__name__)

PYOBJC_AVAILABLE = False
LAContext = None
LAPolicyDeviceOwnerAuthenticationWithBiometrics = None

try:
    from LocalAuthentication import LAContext as TempLAContext, \
                                  LAPolicyDeviceOwnerAuthenticationWithBiometrics as TempLAPolicy
    LAContext = TempLAContext
    LAPolicyDeviceOwnerAuthenticationWithBiometrics = TempLAPolicy

    PYOBJC_AVAILABLE = True
    logger.info("Successfully imported LocalAuthentication framework via PyObjC.")
except ImportError:
    logger.warning("PyObjC or LocalAuthentication framework not found. macOS biometric features will be simulated.")
    # Define dummy classes if PyObjC is not available for graceful degradation
    class LAContext:
        def alloc(self): return self
        def init(self): return self
        def canEvaluatePolicy_error_(self, policy, error):
            logger.debug("LAContext.canEvaluatePolicy_error_ (simulated - PyObjC unavailable) returning False")
            return False
        def evaluatePolicy_localizedReason_reply_(self, policy, reason, reply_block_placeholder):
            logger.warning("LAContext.evaluatePolicy_localizedReason_reply_ (simulated - PyObjC unavailable)")
            # Simulate immediate failure for verify if PyObjC is not there by calling reply block
            if callable(reply_block_placeholder):
                # Simulate error object (very basic)
                sim_error = NSObject.alloc().init()
                # It's hard to create a full NSError without Foundation/ObjC runtime details here.
                # This reply signature for error might be incorrect for a direct Python callable.
                # PyObjC usually handles the bridging.
                # For simulation, just indicate failure.
                try:
                    reply_block_placeholder(False, sim_error)
                except Exception as e:
                    logger.error(f"Error in simulated reply_block_placeholder: {e}")
            else:
                logger.error("Simulated evaluatePolicy: reply_block_placeholder not callable.")



class MacOSBiometricHandler:
    """
    Provides methods to interact with macOS Local Authentication framework
    for Touch ID and Face ID (where available on Mac hardware).
    """
    def __init__(self):
        """Initializes the handler. Logs a warning if PyObjC/LocalAuthentication is not available."""
        logger.info("MacOSBiometricHandler initialized.")
        if not PYOBJC_AVAILABLE:
            logger.warning("MacOSBiometricHandler running with SIMULATED LocalAuthentication due to missing PyObjC.")


    def is_available(self, method: str) -> bool:
        """
        Checks if biometric authentication (Touch ID/Face ID) is available and configured on the Mac.
        Args:
            method (str): "fingerprint" or "face". The check is generic for biometrics.

        Returns:
            bool: True if biometrics are available, False otherwise.
        """
        if not PYOBJC_AVAILABLE:
            logger.info(f"MacOSHandler (Simulated): Checking availability for {method} -> True (simulated as available)")
            return True

        context = LAContext.alloc().init()
        # error_ptr = objc.NULL # For NSError**
        # For canEvaluatePolicy, error is often passed as None for a quick check.

        can_evaluate = context.canEvaluatePolicy_error_(
            LAPolicyDeviceOwnerAuthenticationWithBiometrics, None
        )

        if can_evaluate:
            logger.info(f"MacOSHandler: Biometric authentication for '{method}' is available via LocalAuthentication.")
            return True
        else:

            logger.warning(f"MacOSHandler: Biometrics for '{method}' not available or not configured (canEvaluatePolicy returned False).")
            return False

    def enroll(self, method: str, window_handle=None) -> bool:
        """
        Informs that biometric enrollment (Touch ID/Face ID) is managed via macOS System Settings.
        Args:
            method (str): "fingerprint" or "face".
            window_handle: Not used for macOS enrollment by this handler.
        Returns:
            True if biometrics are generally available (implying user can enroll via OS), False otherwise.
        """
        logger.info(f"MacOSHandler: Enrollment for {method} is managed by the user in macOS System Settings.")
        available = self.is_available(method)
        if available:

            logger.info(f"Guidance: To enroll for {method}, please go to System Settings > Touch ID & Password (or Face ID & Password).")
        return available

    def verify(self, method: str, username_hint: str = "", window_handle=None) -> bool:
        """
        Requests biometric verification from the user via LocalAuthentication.
        Presents the standard macOS Touch ID or Face ID prompt.
        Args:
            method (str): "fingerprint" or "face". The OS determines which to use.
            username_hint (str): A hint incorporated into the reason string shown to the user.
            window_handle: Not directly used by LocalAuthentication's basic evaluation prompt.
        Returns:
            bool: True if verification is successful, False otherwise.
        """
        if not PYOBJC_AVAILABLE:
            logger.info(f"MacOSHandler (Simulated): Verifying {method} for user {username_hint}. Simulating SUCCESS.")

            return True

        if not self.is_available(method):
            logger.warning(f"MacOSHandler: Cannot verify {method}, method not available or not configured.")
            return False

        context = LAContext.alloc().init()
        reason_string = f"Authenticate with {method} to log in as {username_hint}" if username_hint \
                        else f"Authenticate using {method} for Leopard"

        auth_event = threading.Event()
        auth_result = {"success": False, "error_description": "Unknown"} # Store result from callback

        # Define the reply block (callback) for evaluatePolicy
        def reply_handler(success: bool, error: objc.objc_object): # Type hint for error
            # This block is called by LocalAuthentication on completion.
            try:
                if success:
                    auth_result["success"] = True
                    auth_result["error_description"] = None
                    logger.info(f"LocalAuthentication reply: Success for {method}.")
                else:
                    auth_result["success"] = False
                    if error is not None and error.isKindOfClass_(NSObject): # Check if error is a valid NSObject
                        auth_result["error_description"] = error.localizedDescription()
                        logger.warning(f"LocalAuthentication reply: Failure for {method}. Error: {error.localizedDescription()} (Code: {error.code()})")
                    else:
                        auth_result["error_description"] = "Unknown error or user cancellation."
                        logger.warning(f"LocalAuthentication reply: Failure for {method} ({auth_result['error_description']}). Error object: {error}")
            except Exception as e_callback:
                logger.error(f"Exception in LocalAuthentication reply_handler: {e_callback}", exc_info=True)
                auth_result["success"] = False
                auth_result["error_description"] = str(e_callback)
            finally:
                auth_event.set() # Signal that the authentication attempt has completed.

        logger.info(f"MacOSHandler: Calling evaluatePolicy for {method}. OS will prompt user. Reason: '{reason_string}'")
        try:
            context.evaluatePolicy_localizedReason_reply_(
                LAPolicyDeviceOwnerAuthenticationWithBiometrics,
                reason_string,
                reply_handler
            )
        except Exception as e_eval:
            logger.error(f"Exception calling evaluatePolicy_localizedReason_reply_: {e_eval}", exc_info=True)
            return False # Call itself failed

        # Wait for the callback to be executed and set the event.
        timeout_seconds = 60.0
        auth_event.wait(timeout=timeout_seconds)

        if not auth_event.is_set(): # Timeout occurred
            logger.warning(f"MacOSHandler: {method} verification timed out after {timeout_seconds}s (user may have ignored prompt or system issue).")
            # LAContext can be invalidated if it's stuck, but it's complex to manage perfectly.
            # context.invalidate() # This might be needed if the prompt is still somehow active.
            return False

        if auth_result["success"]:
            logger.info(f"MacOSHandler: {method} verification successful for {username_hint}.")
            return True
        else:
            logger.warning(f"MacOSHandler: {method} verification failed for {username_hint}. Reason: {auth_result['error_description']}")
            return False


    def delete_enrollment(self, method: str) -> bool:
        """
        Informs that biometric enrollment deletion is managed via macOS System Settings.
        """
        logger.info(f"MacOSHandler: Deletion of {method} enrollments is managed by the user in macOS System Settings.")
        return True


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    handler = MacOSBiometricHandler()

    print(f"\n--- Testing macOS Biometric Handler ---")

    test_method = "fingerprint"

    available = handler.is_available(test_method)
    print(f"Biometrics for '{test_method}' available on macOS: {available}")

    if available:
        print(f"\nEnrollment guidance for '{test_method}':")
        handler.enroll(test_method)

        print(f"\nAttempting '{test_method}' verification for 'TestUser':")
        # This should now trigger the actual macOS Touch ID/Face ID prompt if PyObjC is working.
        verified = handler.verify(test_method, username_hint='TestUser')
        print(f"Verification result for '{test_method}': {verified}")

        print(f"\nDeletion guidance for '{test_method}':")
        handler.delete_enrollment(test_method)
    else:
        print(f"Biometrics for '{test_method}' not available or PyObjC issue. Cannot run full test.")


    print("\nMacOSBiometricHandler test complete.")
