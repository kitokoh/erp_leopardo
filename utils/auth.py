# utils/auth.py
import logging
from passlib.context import CryptContext

# Setup CryptContext - this should ideally be done once per application
# Using bcrypt as the primary scheme.
# Adding sha256_crypt and sha512_crypt for compatibility with potentially older hashes.
# deprecated="auto" will re-hash passwords to bcrypt upon successful verification if they used an older scheme.
pwd_context = CryptContext(
    schemes=["bcrypt", "sha256_crypt", "sha512_crypt"],
    deprecated="auto"
)

def hash_password(password: str) -> str:
    """Hashes a password using the configured context."""
    # Be cautious logging plain passwords, even in debug. For "admin" it's known.
    # For real passwords, log only a confirmation or password length/type.
    logger.debug(f"Hashing password for input (len: {len(password)})")
    hashed = pwd_context.hash(password)
    logger.debug(f"Generated hash (bcrypt): {hashed[:10]}...{hashed[-5:]}") # Log prefix/suffix
    return hashed

def verify_password(plain_password: str, hashed_password: str) -> tuple[bool, str | None]:
    """
    Verifies a plain password against a hashed one and checks if the hash should be updated.

    Returns:
        tuple[bool, str | None]: (is_verified, new_hash_if_needed_or_None)
    """
    try:
        # verify_and_update returns (verified, new_hash_or_None)
        # new_hash_or_None is None if the hash is already in the default format.
        # It's a new hash string if the old hash was valid but used a deprecated scheme.
        verified, new_hash = pwd_context.verify_and_update(plain_password, hashed_password)
        return verified, new_hash
    except Exception as e:
        # Log unexpected errors during verification, e.g., malformed hash, unknown scheme
        logging.error(f"Error verifying password or during hash update check: {e}", exc_info=True)
        return False, None # Return False and no new hash on error
