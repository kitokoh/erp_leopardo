import httpx # Changed from requests
import json
import logging
import os # For API_BASE_URL environment variable

# Configuration for the API base URL
# This should ideally come from a config file or environment variable
API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000") # Default for local development

# Placeholder for a function that retrieves the current auth token
# This needs to be implemented based on how your PyQt app stores the token after login.
def get_auth_token() -> str | None:
    """
    Retrieves the authentication token.
    Replace this with your actual token retrieval logic.
    """
    logging.debug("Attempting to retrieve auth token.")
    # Try to load from a common global place if main_window or app instance has it
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance()

    token_found_source = "Not found"

    if app:
        if hasattr(app, 'current_user_token') and app.current_user_token:
            logging.debug("Auth token found on QApplication instance.")
            token_found_source = "QApplication.current_user_token"
            return app.current_user_token

        # Fallback if not on app instance (less ideal, but for broad compatibility)
        # This assumes main_window might store it, which is common in some patterns.
        if hasattr(app, 'main_window') and app.main_window and \
           hasattr(app.main_window, 'current_user_token') and app.main_window.current_user_token:
            logging.debug("Auth token found on main_window instance.")
            token_found_source = "main_window.current_user_token"
            return app.main_window.current_user_token

    logging.warning(f"get_auth_token() did not find a token via standard app/main_window attributes. Source: {token_found_source}. Implement actual token retrieval if this is incorrect.")
    # Placeholder if above fails:
    # return "your_static_token_for_testing" # Replace with actual token retrieval for testing if needed
    return None


def post_proforma_invoice(proforma_data: dict) -> tuple[bool, dict | str]:
    """
    Sends a POST request to create a new proforma invoice using httpx.

    Args:
        proforma_data: A dictionary containing the proforma invoice details.

    Returns:
        A tuple (success: bool, data: dict or error_message: str).
        If successful, data is the JSON response from the API.
        If failed, data is an error message string.
    """
    endpoint = f"{API_BASE_URL}/api/proformas/"
    token = get_auth_token()
    headers = {
        "Content-Type": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        logging.warning(f"Auth token not available for POST {endpoint}. Request might fail if auth is required.")

    try:
        logging.info(f"Sending POST request to {endpoint} with data: {json.dumps(proforma_data, indent=2)}")
        # Using httpx client
        with httpx.Client(timeout=30.0) as client: # Default timeout 30 seconds
            response = client.post(endpoint, headers=headers, json=proforma_data)

        logging.info(f"Response status code: {response.status_code}")
        if response.status_code == 201: # Created
            logging.info("Proforma invoice created successfully.")
            return True, response.json()
        else:
            error_message = f"API Error ({response.status_code})"
            try:
                error_details = response.json()
                error_message += f": {error_details.get('detail', response.text)}"
            except json.JSONDecodeError:
                error_message += f": {response.text}"
            logging.error(error_message)
            return False, error_message

    except httpx.ConnectError as e:
        error_msg = f"Connection Error: Could not connect to the API at {endpoint}. Details: {e}"
        logging.error(error_msg)
        return False, error_msg
    except httpx.TimeoutException as e:
        error_msg = f"Request Timeout: The request to {endpoint} timed out. Details: {e}"
        logging.error(error_msg)
        return False, error_msg
    except httpx.RequestError as e: # General httpx request error
        error_msg = f"Request Exception: An error occurred while making the request to {endpoint}. Details: {e}"
        logging.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"An unexpected error occurred: {e}"
        logging.exception(error_msg) # Log full traceback for unexpected errors
        return False, error_msg

def download_file(download_url: str, local_save_path: str) -> tuple[bool, str]:
    """
    Downloads a file from the given URL (typically a relative API path for a document) using httpx.

    Args:
        download_url: The relative URL path (e.g., /api/documents/xxx/download).
        local_save_path: The local path where the file should be saved.

    Returns:
        A tuple (success: bool, message: str).
        Message is the local_save_path if successful, or an error message if failed.
    """
    full_url = f"{API_BASE_URL}{download_url}"
    token = get_auth_token()
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        logging.warning(f"Auth token not available for GET {full_url}. Request might fail if auth is required.")

    try:
        logging.info(f"Sending GET request to {full_url} to download file.")
        with httpx.Client(timeout=60.0) as client: # Default timeout 60 seconds for downloads
            with client.stream("GET", full_url, headers=headers) as response:
                if response.status_code == 200:
                    with open(local_save_path, 'wb') as f:
                        for chunk in response.iter_bytes(chunk_size=8192):
                            f.write(chunk)
                    logging.info(f"File downloaded successfully to {local_save_path}")
                    return True, local_save_path
                else:
                    error_message = f"API Error ({response.status_code}) while downloading from {full_url}"
                    # Attempt to read error details, but response might not be json if streaming failed early
                    try:
                        # Need to read content before trying to parse as JSON if it's an error
                        error_content = response.read()
                        error_details = json.loads(error_content)
                        error_message += f": {error_details.get('detail', error_content.decode(errors='ignore'))}"
                    except Exception: # Broad exception for json.JSONDecodeError or if content already read
                        error_message += f": {response.text}" # response.text might be empty if streamed
                    logging.error(error_message)
                    return False, error_message

    except httpx.RequestError as e:
        error_msg = f"Request Exception during file download from {full_url}. Details: {e}"
        logging.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"An unexpected error occurred during file download: {e}"
        logging.exception(error_msg)
        return False, error_msg

if __name__ == '__main__':
    # Basic test for post_proforma_invoice
    # Ensure your FastAPI server is running at API_BASE_URL for this test to work.

    # Setup basic logging for the test
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')

    print("Testing api_client.py (using httpx)...")

    # --- Test post_proforma_invoice ---
    # Note: This test requires a valid auth token to be returned by get_auth_token()
    # and a running API server that can accept this payload.
    # You might need to adjust 'client_id' and 'company_id' to valid existing IDs in your DB.

    print(f"API Base URL for test: {API_BASE_URL}")
    retrieved_token = get_auth_token()
    print(f"Auth token for test: {'Token retrieved (see debug logs)' if retrieved_token else 'No token retrieved'}")

    test_proforma_payload = {
        "client_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11", # Replace with a valid client_id from your DB
        "company_id": "0e718801-9f2f-4e6a-9254-80c738f991f9", # Replace with a valid company_id
        "project_id": None, # Optional
        "currency": "EUR",
        "payment_terms": "Net 30",
        "delivery_terms": "EXW Seller's Factory",
        "incoterms": "EXW",
        "named_place_of_delivery": "Seller's Factory, Lyon",
        "notes": "Test proforma generated by api_client.py (httpx) test.",
        "vat_rate_percentage": 20.0,
        "discount_rate_percentage": 2.0,
        "target_language_code": "fr", # Test with French
        "items": [
            {
                "product_id": None, # Example: "prod-aaa-001" or None for custom item
                "description": "Produit de Test Alpha (API Client)",
                "quantity": 5,
                "unit_price": 120.50,
                "total_price": 602.50 # quantity * unit_price
            },
            {
                "product_id": None,
                "description": "Service Personnalisé Beta (API Client)",
                "quantity": 1,
                "unit_price": 350.00,
                "total_price": 350.00
            }
        ]
    }

    # print(f"\nAttempting to POST proforma invoice with payload:\n{json.dumps(test_proforma_payload, indent=2)}")
    # Commenting out the actual API call for safety in automated environments
    # To run this test:
    # 1. Ensure your FastAPI application is running and accessible at API_BASE_URL.
    # 2. Ensure the client_id and company_id in test_proforma_payload exist in your database.
    # 3. If your API requires authentication, ensure get_auth_token() can retrieve a valid token.
    #    You might need to manually set a token in get_auth_token() for this standalone test.
    #
    # success, result = post_proforma_invoice(test_proforma_payload)
    #
    # if success:
    #     print("\nProforma POST Test SUCCEEDED:")
    #     print(json.dumps(result, indent=2))
    #
    #     if isinstance(result, dict) and result.get("proforma_pdf_url"):
    #         pdf_url = result["proforma_pdf_url"]
    #         proforma_number = result.get("proforma_invoice_number", "unknown_proforma")
    #         # Ensure the current directory is writable or change save_path
    #         save_path = f"./test_downloaded_proforma_{proforma_number.replace('/', '_')}.pdf"
    #
    #         print(f"\nAttempting to download PDF from {pdf_url} to {save_path}...")
    #         dl_success, dl_message = download_file(pdf_url, save_path)
    #
    #         if dl_success:
    #             print(f"PDF Download Test SUCCEEDED. File saved to: {dl_message}")
    #         else:
    #             print(f"PDF Download Test FAILED. Error: {dl_message}")
    #     else:
    #         print("\nSkipping PDF download test as proforma_pdf_url was not found in POST response.")
    #
    # else:
    #     print("\nProforma POST Test FAILED:")
    #     print(f"Error: {result}")

    print("\n--- API Client Test Complete (httpx) ---")
    print("Note: Actual API interaction tests are commented out by default in the __main__ block.")
    print("Review and uncomment the test call to post_proforma_invoice and download_file as needed.")
