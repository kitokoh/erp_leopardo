# security_module/os_handlers/windows_handler.py
"""
Handles Windows Biometric Framework (WBF) interactions using ctypes.

This module provides access to fingerprint and facial recognition
(Windows Hello) functionalities available on Windows.

Enrollment and deletion of biometric templates are generally managed
through Windows Settings by the user. This handler primarily focuses on:
- Checking sensor availability.
- Verifying the current user's identity using biometrics.
- Guiding the user for enrollment/deletion via OS settings.
"""
import ctypes
import logging
import sys # Import sys module

logger = logging.getLogger(__name__)

winbio_dll = None
# Only attempt to load winbio.dll on Windows platforms
if sys.platform == "win32":
    try:
        winbio_dll = ctypes.WinDLL('winbio.dll')
        logger.info("winbio.dll loaded successfully.")
    except OSError:
        logger.error("winbio.dll not found on Windows. Windows Biometric Framework will not be available.")
    except AttributeError:
        # This might happen if ctypes itself is incomplete, though unlikely for WinDLL.
        # More relevant if we were using ctypes.windll.winbio
        logger.error("ctypes.WinDLL attribute not found, cannot load winbio.dll.")
        winbio_dll = None # Ensure it's None
else:
    logger.info("Not on Windows platform. winbio.dll will not be loaded.")

# --- WBF Constants ---
WINBIO_TYPE_FINGERPRINT = 0x00000008
WINBIO_TYPE_FACIAL_FEATURES = 0x00000004
WINBIO_POOL_SYSTEM = 0x00000001
WINBIO_FLAG_DEFAULT = 0x00000000
WINBIO_ID_TYPE_WILDCARD = 0x00000003

WINBIO_UNIT_ID = ctypes.c_uint32
WINBIO_SESSION_HANDLE = ctypes.c_void_p
HRESULT = ctypes.c_long
S_OK = 0

WINBIO_E_NO_CAPTURE = HRESULT(0x8009802A).value
WINBIO_E_BAD_CAPTURE = HRESULT(0x8009802B).value
WINBIO_E_UNKNOWN_ID = HRESULT(0x80098031).value
WINBIO_E_DATABASE_NO_RESULTS = HRESULT(0x8009803E).value
WINBIO_E_NO_DEVICE = HRESULT(0x8009803F).value

# More accurate definition for the initial part of WINBIO_UNIT_SCHEMA
WINBIO_POOL_TYPE = ctypes.c_uint32
WINBIO_BIOMETRIC_TYPE = ctypes.c_uint32
WINBIO_BIOMETRIC_SUBTYPE = ctypes.c_ubyte
WINBIO_CAPABILITIES = ctypes.c_uint32
WINBIO_MAX_STRING_LEN = 256  # As per winbio.h
WINBIO_STRING = ctypes.c_wchar * WINBIO_MAX_STRING_LEN

class WINBIO_VERSION(ctypes.Structure):
    _fields_ = [
        ("MajorVersion", ctypes.c_long), # Using c_long as per common practice for DWORD-like fields
        ("MinorVersion", ctypes.c_long)  # Adjust if specific header shows WORD or other.
    ]

class WINBIO_UNIT_SCHEMA(ctypes.Structure):
    _fields_ = [
        ("UnitId", WINBIO_UNIT_ID),
        ("PoolType", WINBIO_POOL_TYPE),
        ("BiometricFactor", WINBIO_BIOMETRIC_TYPE),
        ("SensorSubtype", WINBIO_BIOMETRIC_SUBTYPE), # Typically followed by 3 bytes padding for alignment
        ("Capabilities", WINBIO_CAPABILITIES),
        ("DeviceInstanceId", WINBIO_STRING),
        ("Description", WINBIO_STRING),
        ("Manufacturer", WINBIO_STRING),
        ("Model", WINBIO_STRING),
        ("SerialNumber", WINBIO_STRING),
        ("FirmwareVersion", WINBIO_VERSION)
        # Note: HardwareVersion is not part of WINBIO_UNIT_SCHEMA in common SDKs,
        # it's often part of WINBIO_SENSOR_ATTRIBUTES.
        # The structure size will be determined by ctypes based on these fields and default packing.
    ]

class WINBIO_IDENTITY(ctypes.Structure):
    _fields_ = [
        ("Type", ctypes.c_uint32),
        ("Value", ctypes.c_ubyte * 32)
    ]

# WINBIO_BIOMETRIC_SUBTYPE = ctypes.c_ubyte # Moved earlier
WINBIO_REJECT_REASON = ctypes.c_uint32

class WindowsBiometricHandler:
    """
    Provides methods to interact with the Windows Biometric Framework (WBF).
    Manages a WBF session and calls WBF API functions via ctypes.
    """
    def __init__(self):
        """Initializes the handler and attempts to load winbio.dll."""
        self.session_handle = WINBIO_SESSION_HANDLE()
        self.current_session_factor = None
        self.winbio = winbio_dll
        if not self.winbio:
            logger.warning("WindowsBiometricHandler initialized, but winbio.dll was not loaded. Biometric functions will be unavailable.")

    def _ensure_session_for_factor(self, factor: ctypes.c_uint32) -> bool:
        """
        Ensures a WBF session is open for the specified biometric factor.
        If a session is open for a different factor, it's closed and a new one is opened.
        Args:
            factor: The WINBIO_BIOMETRIC_TYPE (e.g., WINBIO_TYPE_FINGERPRINT).
        Returns:
            True if a session is successfully opened or already open for the factor, False otherwise.
        """
        if not self.winbio:
            logger.error("Cannot ensure WinBio session: winbio.dll not loaded.")
            return False
        if self.session_handle.value and self.current_session_factor == factor:
            return True # Session already open for this factor
        if self.session_handle.value: # A session is open, but for a different factor
            self._close_session()

        try:
            self.winbio.WinBioOpenSession.argtypes = [
                ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32,
                ctypes.POINTER(WINBIO_UNIT_ID), ctypes.c_size_t,
                ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(WINBIO_SESSION_HANDLE)
            ]
            self.winbio.WinBioOpenSession.restype = HRESULT
        except AttributeError:
             logger.error("winbio.dll not available for setting up WinBioOpenSession.")
             return False

        hr = self.winbio.WinBioOpenSession(
            factor, WINBIO_POOL_SYSTEM, WINBIO_FLAG_DEFAULT,
            None, 0, None, ctypes.byref(self.session_handle)
        )
        if hr != S_OK:
            self.session_handle = WINBIO_SESSION_HANDLE() # Ensure handle is null on failure
            self.current_session_factor = None
            logger.error(f"WinBioOpenSession for factor {factor} failed with HRESULT: {hr:#0x}")
            return False
        else:
            self.current_session_factor = factor
            logger.info(f"WinBioOpenSession for factor {factor} successful. Handle: {self.session_handle.value}")
            return True

    def _close_session(self):
        """Closes the current WBF session if one is open."""
        if not self.winbio or not (self.session_handle and self.session_handle.value):
            return
        try:
            self.winbio.WinBioCloseSession.argtypes = [WINBIO_SESSION_HANDLE]
            self.winbio.WinBioCloseSession.restype = HRESULT
            hr = self.winbio.WinBioCloseSession(self.session_handle)
            if hr != S_OK:
                logger.error(f"WinBioCloseSession failed with HRESULT: {hr:#0x}")
            else:
                logger.info(f"WinBioCloseSession for factor {self.current_session_factor} successful.")
        except AttributeError:
            logger.error("winbio.dll not available for WinBioCloseSession.")
        finally:
            self.session_handle = WINBIO_SESSION_HANDLE() # Clear handle
            self.current_session_factor = None

    def is_available(self, method: str) -> bool:
        """
        Checks if a biometric sensor for the specified method (e.g., "fingerprint", "face")
        is available on the system.
        Args:
            method: The biometric method string.
        Returns:
            True if available, False otherwise.
        """
        target_factor = 0
        if method == "fingerprint": target_factor = WINBIO_TYPE_FINGERPRINT
        elif method == "face": target_factor = WINBIO_TYPE_FACIAL_FEATURES
        else:
            logger.warning(f"is_available: Unsupported method '{method}' for Windows.")
            return False

        if not self._ensure_session_for_factor(target_factor): # Ensures session is open for the correct factor
            return False

        # ptr_to_unit_schemas will receive a pointer to the first WINBIO_UNIT_SCHEMA in an array.
        # It should be of type POINTER(WINBIO_UNIT_SCHEMA).
        ptr_to_unit_schemas = ctypes.POINTER(WINBIO_UNIT_SCHEMA)() # This is WINBIO_UNIT_SCHEMA*
        unit_count = ctypes.c_size_t()

        try:
            self.winbio.WinBioEnumBiometricUnits.argtypes = [
                WINBIO_SESSION_HANDLE,
                ctypes.c_uint32,
                # Parameter in C is PWINBIO_UNIT_SCHEMA** (pointer to a pointer to schema)
                ctypes.POINTER(ctypes.POINTER(WINBIO_UNIT_SCHEMA)),
                ctypes.POINTER(ctypes.c_size_t)
            ]
            self.winbio.WinBioEnumBiometricUnits.restype = HRESULT
        except AttributeError:
            logger.error("winbio.dll not available for WinBioEnumBiometricUnits setup.")
            return False

        hr = self.winbio.WinBioEnumBiometricUnits(
            self.session_handle,
            target_factor,
            ctypes.byref(ptr_to_unit_schemas), # Pass address of our WINBIO_UNIT_SCHEMA* variable
            ctypes.byref(unit_count)
        )

        available = False
        if hr == S_OK:
            available = unit_count.value > 0
            logger.info(f"WinBioEnumBiometricUnits: {unit_count.value} unit(s) for {method} (factor {target_factor}). Available: {available}")

            # ptr_to_unit_schemas now holds the actual pointer to the array allocated by WinBio.
            # This is the pointer (type: WINBIO_UNIT_SCHEMA*) that needs to be freed.
            # WinBioFree expects a PVOID, which WINBIO_UNIT_SCHEMA* is compatible with.
            if ptr_to_unit_schemas: # Check if the pointer itself is not NULL (i.e., ptr_to_unit_schemas.value is not 0)
                try:
                    # Ensure WinBioFree argtypes is set once, ideally during handler initialization or first use.
                    # For safety, can be set here if there's doubt.
                    if not hasattr(self.winbio.WinBioFree, 'argtypes') or not self.winbio.WinBioFree.argtypes:
                        self.winbio.WinBioFree.argtypes = [ctypes.c_void_p]
                        self.winbio.WinBioFree.restype = HRESULT # WinBioFree returns HRESULT

                    free_hr = self.winbio.WinBioFree(ptr_to_unit_schemas)
                    if free_hr != S_OK:
                        logger.warning(f"WinBioFree failed with HRESULT: {free_hr:#0x} for pointer {ptr_to_unit_schemas}")
                except AttributeError:
                     logger.error("winbio.dll not available for WinBioFree.")
                except Exception as e:
                    logger.error(f"Exception during WinBioFree: {e}")
        elif hr == WINBIO_E_NO_DEVICE:
            logger.info(f"WinBioEnumBiometricUnits: No devices for {method} (factor {target_factor}).")
        else:
            logger.error(f"WinBioEnumBiometricUnits for {method} failed with HRESULT: {hr:#0x}")
        return available

    def enroll(self, method: str, window_handle=None) -> bool:
        """
        Guides the user to enroll biometrics via Windows Settings.
        WBF enrollment is complex to trigger directly for a specific application user
        without deeper system integration or admin rights.
        Args:
            method: The biometric method string.
            window_handle: (Optional) Handle to the parent window, not directly used here.
        Returns:
            True if the method is available (implying user can enroll via OS), False otherwise.
        """
        logger.info(f"WindowsHandler: True enrollment for '{method}' should be done via Windows Settings (e.g., Windows Hello Setup).")
        logger.info("This function confirms method availability and simulates that the user has been guided to complete OS enrollment.")
        # A real application might open ms-settings:signinoptions or ms-settings:signinoptions-launchfaceenrollment etc.
        # For now, we just check availability and assume user handles the OS part.
        return self.is_available(method)

    def verify(self, method: str, username_hint: str = "", window_handle=None) -> bool:
        """
        Verifies the current logged-on user using the specified biometric method.
        Args:
            method: "fingerprint" or "face".
            username_hint: (Optional) A hint for the user, not directly used by WinBioVerify with WILDCARD.
            window_handle: (Optional) Handle to the parent window.
        Returns:
            True if verification is successful, False otherwise.
        """
        target_factor = 0
        if method == "fingerprint": target_factor = WINBIO_TYPE_FINGERPRINT
        elif method == "face": target_factor = WINBIO_TYPE_FACIAL_FEATURES
        else:
            logger.warning(f"verify: Unsupported method '{method}' for Windows.")
            return False

        if not self._ensure_session_for_factor(target_factor):
            return False

        identity = WINBIO_IDENTITY()
        identity.Type = WINBIO_ID_TYPE_WILDCARD # Verifies current console user
        sub_factor = WINBIO_BIOMETRIC_SUBTYPE(0) # WINBIO_SUBTYPE_NO_INFORMATION or WINBIO_SUBTYPE_ANY
        unit_id_out = WINBIO_UNIT_ID()
        match_out = ctypes.c_bool()
        reject_detail_out = WINBIO_REJECT_REASON()

        try:
            self.winbio.WinBioVerify.argtypes = [
                WINBIO_SESSION_HANDLE, ctypes.POINTER(WINBIO_IDENTITY), WINBIO_BIOMETRIC_SUBTYPE,
                ctypes.POINTER(WINBIO_UNIT_ID), ctypes.POINTER(ctypes.c_bool), ctypes.POINTER(WINBIO_REJECT_REASON)
            ]
            self.winbio.WinBioVerify.restype = HRESULT
        except AttributeError:
            logger.error("winbio.dll not available for WinBioVerify setup.")
            return False

        logger.info(f"Calling WinBioVerify for {method} (factor {target_factor}). User hint: '{username_hint}'")
        # Note: window_handle is not directly used by WinBioVerify, but system UI might appear.
        # For custom UI or focus management, WinBioSetWindowAssociation might be needed prior.
        hr = self.winbio.WinBioVerify(
            self.session_handle, ctypes.byref(identity), sub_factor,
            ctypes.byref(unit_id_out), ctypes.byref(match_out), ctypes.byref(reject_detail_out)
        )
        if hr == S_OK:
            if match_out.value:
                logger.info(f"WinBioVerify successful for {method}: Match found. Unit ID: {unit_id_out.value}")
                return True
            else:
                logger.warning(f"WinBioVerify for {method}: No match. Reject reason: {reject_detail_out.value:#0x}")
                return False
        elif hr == WINBIO_E_UNKNOWN_ID or hr == WINBIO_E_DATABASE_NO_RESULTS :
            logger.warning(f"WinBioVerify for {method}: No biometric enrollment found for the current user or no match (HRESULT: {hr:#0x}).")
        elif hr == WINBIO_E_BAD_CAPTURE:
             logger.warning(f"WinBioVerify for {method}: Bad capture (e.g., swipe too fast, face not clear). HRESULT: {hr:#0x}.")
        else:
            logger.error(f"WinBioVerify for {method} failed with HRESULT: {hr:#0x}. Reject reason (if any): {reject_detail_out.value:#0x}")
        return False

    def delete_enrollment(self, method: str) -> bool:
        """
        Guides the user to delete enrollments via Windows Settings.
        Direct programmatic deletion is typically system-wide and may require higher privileges.
        """
        logger.info(f"WindowsHandler: True deletion of OS-level '{method}' enrollments should be done via Windows Settings.")
        # Application should disable the method in its own DB.
        return True # Indicates app has handled its part of the "deletion" (which is guidance).

    def __del__(self):
        """Ensures the WBF session is closed when the handler is garbage collected."""
        self._close_session()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    handler = WindowsBiometricHandler()
    if winbio_dll: # Check if DLL was loaded
        print("\n--- Testing Fingerprint ---")
        fp_avail = handler.is_available('fingerprint')
        print(f"Fingerprint available: {fp_avail}")
        if fp_avail:
            print(f"Guidance for fingerprint enrollment (user action in OS Settings): {handler.enroll('fingerprint')}")
            # To test verify, ensure fingerprint is enrolled for the current Windows user
            print(f"Attempting fingerprint verification (current user): {handler.verify('fingerprint', username_hint='CurrentUser')}")

        print("\n--- Testing Face ---")
        # Ensure a session for face is established if different from fingerprint
        # Note: is_available now handles opening session for the specific factor.
        face_avail = handler.is_available('face')
        print(f"Face available: {face_avail}")
        if face_avail:
            print(f"Guidance for face enrollment (user action in OS Settings): {handler.enroll('face')}")
            # To test verify, ensure face is enrolled (Windows Hello) for the current Windows user
            print(f"Attempting face verification (current user): {handler.verify('face', username_hint='CurrentUser')}")
    else:
        print("winbio.dll was not loaded. Cannot run WBF tests.")

    # Explicitly close session at the end of tests if needed, or rely on __del__
    # handler._close_session() # Already called by __del__

    print("\nWindowsBiometricHandler test complete.")
