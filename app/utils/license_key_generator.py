"""
License Key Generator Utility

This script generates RSA key pairs and creates signed license keys.
License data is provided as a JSON structure, signed with a private RSA key.
The application can then verify the license using the corresponding public key.
"""
import argparse
import json
import uuid
from datetime import datetime, timezone
import os

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import base64

KEY_SIZE = 2048
PUBLIC_EXPONENT = 65537

DEFAULT_PRIVATE_KEY_FILE = "license_private_key.pem"
DEFAULT_PUBLIC_KEY_FILE = "license_public_key.pem"

def generate_rsa_key_pair(private_key_path: str, public_key_path: str):
    """Generates an RSA key pair and saves them to PEM files."""
    private_key = rsa.generate_private_key(
        public_exponent=PUBLIC_EXPONENT,
        key_size=KEY_SIZE,
        backend=default_backend()
    )
    public_key = private_key.public_key()

    # Save private key
    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    with open(private_key_path, 'wb') as f:
        f.write(pem_private)
    print(f"Private key saved to {private_key_path}")

    # Save public key
    pem_public = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    with open(public_key_path, 'wb') as f:
        f.write(pem_public)
    print(f"Public key saved to {public_key_path}")

def load_private_key(private_key_path: str) -> rsa.RSAPrivateKey:
    """Loads an RSA private key from a PEM file."""
    with open(private_key_path, 'rb') as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None,
            backend=default_backend()
        )
    if not isinstance(private_key, rsa.RSAPrivateKey):
        raise TypeError("Loaded key is not an RSA private key.")
    return private_key

def create_signed_license_key(license_data: dict, private_key: rsa.RSAPrivateKey) -> str:
    """
    Creates a signed license key.
    The license data is serialized to JSON, signed, and then formatted.
    Format: base64_urlsafe(json_payload).base64_urlsafe(signature)
    """
    if 'key_id' not in license_data:
        license_data['key_id'] = str(uuid.uuid4())
    if 'generated_at' not in license_data:
        license_data['generated_at'] = datetime.now(timezone.utc).isoformat()
    if 'generator_version' not in license_data:
        license_data['generator_version'] = "1.0"

    # Serialize to a canonical JSON string (sorted keys, no indent)
    # This ensures the byte representation for signing is consistent.
    json_payload = json.dumps(license_data, sort_keys=True, separators=(',', ':')).encode('utf-8')

    signature = private_key.sign(
        json_payload,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

    encoded_payload = base64.urlsafe_b64encode(json_payload).decode('utf-8').rstrip('=')
    encoded_signature = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')

    return f"{encoded_payload}.{encoded_signature}"

def main():
    parser = argparse.ArgumentParser(description="License Key Generator Utility")
    parser.add_argument(
        'action',
        choices=['generate-keys', 'create-license'],
        help="Action to perform: 'generate-keys' or 'create-license'"
    )
    parser.add_argument(
        '--privkey',
        default=DEFAULT_PRIVATE_KEY_FILE,
        help=f"Path to the private key file (default: {DEFAULT_PRIVATE_KEY_FILE})"
    )
    parser.add_argument(
        '--pubkey',
        default=DEFAULT_PUBLIC_KEY_FILE,
        help=f"Path to the public key file (default: {DEFAULT_PUBLIC_KEY_FILE})"
    )
    parser.add_argument(
        '--data',
        type=str,
        help="JSON string or path to a JSON file containing license data for 'create-license' action."
    )
    parser.add_argument(
        '--license-type',
        choices=['gratuit', 'limite', 'complet'],
        help="Shortcut to set license_type."
    )
    parser.add_argument(
        '--description',
        type=str,
        help="Description for the license."
    )
    parser.add_argument(
        '--expiration-date',
        type=str, # YYYY-MM-DD
        help="Expiration date for the license (YYYY-MM-DD)."
    )
    parser.add_argument(
        '--customer-id',
        type=str,
        help="Customer identifier."
    )
    parser.add_argument(
        '--issued-to',
        type=str,
        help="Email or ID of the person/entity this license is issued to."
    )

    args = parser.parse_args()

    if args.action == 'generate-keys':
        if os.path.exists(args.privkey) or os.path.exists(args.pubkey):
            overwrite = input("Key file(s) already exist. Overwrite? (y/N): ").strip().lower()
            if overwrite != 'y':
                print("Key generation cancelled.")
                return
        generate_rsa_key_pair(args.privkey, args.pubkey)

    elif args.action == 'create-license':
        if not os.path.exists(args.privkey):
            print(f"Error: Private key file '{args.privkey}' not found. Generate keys first.")
            return

        private_key = load_private_key(args.privkey)
        license_data_dict = {}

        if args.data:
            if os.path.exists(args.data):
                with open(args.data, 'r') as f:
                    try:
                        license_data_dict = json.load(f)
                    except json.JSONDecodeError as e:
                        print(f"Error: Could not decode JSON from file '{args.data}': {e}")
                        return
            else: # Assume it's a JSON string
                try:
                    license_data_dict = json.loads(args.data)
                except json.JSONDecodeError as e:
                    print(f"Error: Could not decode JSON string from --data argument: {e}")
                    return

        # Override or set values from direct command line arguments
        if args.license_type:
            license_data_dict['license_type'] = args.license_type
        if args.description:
            license_data_dict['description'] = args.description
        if args.expiration_date:
            try:
                datetime.strptime(args.expiration_date, "%Y-%m-%d") # Validate date format
                license_data_dict['expiration_date'] = args.expiration_date
            except ValueError:
                print("Error: Invalid expiration_date format. Please use YYYY-MM-DD.")
                return
        if args.customer_id:
            license_data_dict['customer_id'] = args.customer_id
        if args.issued_to:
            license_data_dict['issued_to'] = args.issued_to

        if 'license_type' not in license_data_dict:
            print("Error: license_type is required. Use --license-type or provide in JSON data.")
            return

        signed_key = create_signed_license_key(license_data_dict, private_key)
        print("\nSigned License Key:")
        print(signed_key)

        print("\nDecoded Payload (for verification during generation):")
        try:
            payload_b64 = signed_key.split('.')[0]
            # Add padding if necessary for standard base64 decoding
            payload_json = base64.urlsafe_b64decode(payload_b64 + '=' * (-len(payload_b64) % 4)).decode('utf-8')
            print(json.dumps(json.loads(payload_json), indent=2))
        except Exception as e:
            print(f"Could not decode payload for verification: {e}")

if __name__ == "__main__":
    main()
"""
