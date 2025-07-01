# utils/security.py
import logging
from passlib.context import CryptContext

# Setup CryptContext
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def hash_password(password: str) -> str:
    """Hashes a password using the configured context."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> tuple[bool, str | None]:
    """
    Verifies a plain password against a hashed one and checks if the hash should be updated.

    Returns:
        tuple[bool, str | None]: (is_verified, new_hash_if_needed_or_None)
    """
    try:
        verified, new_hash = pwd_context.verify_and_update(plain_password, hashed_password)
        return verified, new_hash
    except Exception as e:
        logging.error(f"Error verifying password or during hash update check: {e}", exc_info=True)
        return False, None
