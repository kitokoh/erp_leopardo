# utils/security_helpers.py
import secrets
import hashlib
import os

# For password hashing, using passlib as it's already in use by users_crud via utils.py (which was a misremembered name)
# The actual password hashing functions (hash_password, verify_password) are in db/cruds/users_crud.py or its imported utils.
# This file will focus on token generation and hashing for session tokens.

def generate_secure_token(length: int = 32) -> str:
    """
    Generates a cryptographically secure URL-safe text string.
    Default length of 32 bytes results in a 43-character base64 string.
    A length of 48 bytes results in a 64-character base64 string.
    """
    return secrets.token_urlsafe(length)

def hash_token_for_storage(token: str) -> str:
    """
    Hashes a token using SHA256 for storage in the database.
    Returns the hex digest of the hash.
    """
    if not isinstance(token, str):
        raise TypeError("Token must be a string.")

    token_bytes = token.encode('utf-8')
    hashed_token = hashlib.sha256(token_bytes).hexdigest()
    return hashed_token

# Example of how password hashing might be structured if it were here
# from passlib.context import CryptContext
# PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")
#
# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     return PWD_CONTEXT.verify(plain_password, hashed_password)
#
# def get_password_hash(password: str) -> str:
#     return PWD_CONTEXT.hash(password)

if __name__ == '__main__':
    # Test token generation and hashing
    original_token = generate_secure_token(48)
    print(f"Original Token: {original_token}")
    print(f"Length of Original Token: {len(original_token)}")

    hashed_token = hash_token_for_storage(original_token)
    print(f"Hashed Token (SHA256 hex): {hashed_token}")
    print(f"Length of Hashed Token: {len(hashed_token)}")

    # Verification test (conceptual, as we only store the hash)
    # To verify, you would hash the input token and compare hashes.
    test_token_input = original_token
    hashed_test_input = hash_token_for_storage(test_token_input)
    print(f"Verification: Is hash of input same as stored hash? {hashed_test_input == hashed_token}")

    another_token = generate_secure_token(48)
    hashed_another_token = hash_token_for_storage(another_token)
    print(f"Verification: Is hash of different token same as stored hash? {hashed_another_token == hashed_token}")

    # Test with a common short token
    short_token = "short-and-simple"
    hashed_short_token = hash_token_for_storage(short_token)
    print(f"Original Short Token: {short_token}")
    print(f"Hashed Short Token: {hashed_short_token}")

    try:
        hash_token_for_storage(123) # type: ignore
    except TypeError as e:
        print(f"Caught expected TypeError: {e}")


