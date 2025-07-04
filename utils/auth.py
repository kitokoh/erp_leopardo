# utils/auth.py
import logging
from passlib.context import CryptContext

# Global logger for this module, used as a fallback if no logger is passed to functions.
# This retains the original behavior for calls not originating from the seed script.
module_logger = logging.getLogger(__name__)

# Setup CryptContext - this should ideally be done once per application
# Using bcrypt as the primary scheme.
# Adding sha256_crypt and sha512_crypt for compatibility with potentially older hashes.
# deprecated="auto" will re-hash passwords to bcrypt upon successful verification if they used an older scheme.
pwd_context = CryptContext(
    schemes=["bcrypt", "sha256_crypt", "sha512_crypt"],
    deprecated="auto"
)

def hash_password(password: str, logger_passed: logging.Logger | None = None) -> str:
    """
    Hashes a password using the configured context.
    Accepts an optional logger; otherwise, uses the module-level logger.
    """
    current_logger = logger_passed if logger_passed else module_logger
    # Be cautious logging plain passwords, even in debug. For "admin" it's known.
    # For real passwords, log only a confirmation or password length/type.
    current_logger.debug(f"Hashing password for input (len: {len(password)})")
    hashed = pwd_context.hash(password)
    current_logger.debug(f"Generated hash (bcrypt): {hashed[:10]}...{hashed[-5:]}") # Log prefix/suffix
    return hashed

def verify_password(plain_password: str, hashed_password: str, logger_passed: logging.Logger | None = None) -> tuple[bool, str | None]:
    """
    Verifies a plain password against a hashed one and checks if the hash should be updated.

    Returns:
        tuple[bool, str | None]: (is_verified, new_hash_if_needed_or_None)
    """
    current_logger = logger_passed if logger_passed else module_logger
    try:
        # verify_and_update returns (verified, new_hash_or_None)
        # new_hash_or_None is None if the hash is already in the default format.
        # It's a new hash string if the old hash was valid but used a deprecated scheme.
        verified, new_hash = pwd_context.verify_and_update(plain_password, hashed_password)
        return verified, new_hash
    except Exception as e:
        # Log unexpected errors during verification, e.g., malformed hash, unknown scheme
        current_logger.error(f"Error verifying password or during hash update check: {e}", exc_info=True)
        return False, None # Return False and no new hash on error
