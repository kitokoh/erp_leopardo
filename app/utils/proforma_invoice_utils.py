import sqlite3 # Standard library, typically not used directly with SQLAlchemy
import uuid
import hashlib
from datetime import datetime, timezone, timedelta
import json
import os
import logging
from typing import Optional, List, Dict, Any, Union

# Attempt to import ProformaInvoice model for type hinting
try:
    from app.db.models.misc.proforma_invoices import ProformaInvoice
except ImportError:
    logging.warning("Could not import ProformaInvoice from db.models.misc. Type hinting will use Any.")
    ProformaInvoice = Any # Fallback type

# Attempt to import from db module
try:
    from app.db.connection import get_db_connection
    from app.db.cruds.misc.companies_crud import get_company_by_id as db_get_company_by_id
    from app.db.cruds.misc.company_personnel_crud import get_personnel_for_company as db_get_personnel_for_company
    from app.db.cruds.clients.clients_crud import get_client_by_id as db_get_client_by_id
    from app.db.cruds.misc.locations_crud import get_country_by_id as db_get_country_by_id, get_city_by_id as db_get_city_by_id
    from app.db.cruds.misc.contacts_crud import get_contacts_for_client as db_get_contacts_for_client
    from app.db.cruds.projects.projects_crud import get_project_by_id as db_get_project_by_id
    from app.db.cruds.products.products_crud import get_product_by_id as db_get_product_by_id
    from app.db.cruds.clients.client_project_products_crud import get_products_for_client_or_project as db_get_products_for_client_or_project
    from app.db.cruds.misc.notes_crud import get_effective_document_note as db_get_effective_document_note
    from app.db.cruds.misc.application_settings_crud import get_next_invoice_number
except ImportError as e:
    logging.warning(f"Could not import all dependencies from db or cruds: {e}. Using placeholder functions. Full functionality requires db modules to be correctly structured and accessible.")
    # Define placeholder functions if db.py or its functions are not found

    def get_db_connection(): raise NotImplementedError("get_db_connection not imported/defined from db.connection")
    def db_get_company_by_id(conn, company_id): return None # Adjusted signature for SQLite conn
    def db_get_personnel_for_company(conn, company_id): return [] # Adjusted signature
    def db_get_client_by_id(conn, client_id): return None # Adjusted signature
    def db_get_country_by_id(conn, country_id): return None # Adjusted signature
    def db_get_city_by_id(conn, city_id): return None # Adjusted signature
    def db_get_contacts_for_client(conn, client_id, is_primary=None): return [] # Adjusted signature
    def db_get_project_by_id(conn, project_id): return None # Adjusted signature

    class MockProduct: # Keep mock for db_get_product_by_id if its import fails
        def __init__(self, id, name, desc, lang, price, unit, weight=None, dims=None, code=None):
            self.id = id; self.name = name; self.description = desc; self.language_code = lang
            self.base_unit_price = price; self.unit_of_measure = unit
            self.product_weight_kg = weight; self.product_dimensions_cm = dims; self.product_code = code
    # Adjusted signature for db_get_product_by_id
    def db_get_product_by_id(conn, product_id): return MockProduct(id=product_id, name=f"Mock Product {product_id}", desc="Mock Desc", lang="en", price=10.0, unit="pcs", code=f"CODE-{product_id}")
    def db_get_products_for_client_or_project(conn, client_id, project_id=None): return [] # Adjusted signature
    def db_get_effective_document_note(conn, client_id, document_type, language_code): return "N/A" # Adjusted signature for new function


# --- Constants ---
# APP_ROOT_DIR_CONTEXT is this file's dir: utils/
APP_ROOT_DIR_CONTEXT = os.path.dirname(os.path.abspath(__file__))
# PROJECT_ROOT_DIR_CONTEXT is one level up from utils/
PROJECT_ROOT_DIR_CONTEXT = os.path.dirname(APP_ROOT_DIR_CONTEXT)

# Import get_doc_label from app_utils (which is in the same directory 'utils')
from .app_utils import get_doc_label
from PyQt5.QtCore import QLocale, QDate, QDateTime # Added QDate, QDateTime for date formatting

LOGO_SUBDIR_CONTEXT = os.path.join("resources", "company_logos") # Corrected typical path
CURRENCY_SYMBOLS = {
    "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥",
    # Add more as needed
}

# --- Helper Functions ---
# Ensure these functions are robust enough for various inputs (None, etc.)
def _parse_json_field(json_string, default_value=None):
    if default_value is None:
        default_value = {}
    if isinstance(json_string, (dict, list)): # Already parsed
        return json_string
    if isinstance(json_string, str):
        try:
            return json.loads(json_string)
        except json.JSONDecodeError:
            logging.warning(f"JSONDecodeError for string: {json_string[:100]}")
            return default_value
    return default_value

def _parse_key_value_string(kv_string, default_value=None):
    if default_value is None:
        default_value = {}
    if not isinstance(kv_string, str):
        return default_value
    parsed_data = {}
    try:
        pairs = kv_string.split(';')
        for pair in pairs:
            if ':' in pair:
                key, value = pair.split(':', 1)
                parsed_data[key.strip().lower().replace(" ", "_")] = value.strip()
    except Exception as e:
        logging.warning(f"Error parsing key-value string '{kv_string[:100]}': {e}")
        return default_value
    return parsed_data

def _format_address_parts(address_line1, city, postal_code, country):
    parts = [address_line1, city, postal_code, country]
    return ", ".join(filter(None, [str(p).strip() for p in parts if p and str(p).strip() != "N/A"])) or "N/A"

def format_currency(amount: Union[int, float, None], currency_code: str = "EUR", target_language_code: str = "fr") -> str:
    locale = QLocale(QLocale.Language[target_language_code.capitalize() if len(target_language_code)==2 else "AnyLanguage"]) # Get locale for lang

    if amount is None or not isinstance(amount, (int, float)):
        # Use get_doc_label for "N/A" to make it translatable too
        na_text = get_doc_label("not_applicable_short", target_language_code, "N/A")
        return f"{na_text} {CURRENCY_SYMBOLS.get(currency_code.upper(), currency_code)}"

    # QLocale.toCurrencyString can be very powerful if full ICU data is available with Qt installation.
    # It handles symbol placement, grouping, decimal separators according to locale and currency.
    # Example: return locale.toCurrencyString(float(amount), currency_code.upper())
    # For simpler number formatting with explicit symbol, which is often more reliable across minimal Qt installs:
    number_str = locale.toString(float(amount), 'f', 2) # 'f' for fixed point, 2 decimal places
    return f"{number_str} {CURRENCY_SYMBOLS.get(currency_code.upper(), currency_code)}"


# Placeholder for _get_batch_products_and_equivalents
# This is a complex function that would normally interact with a ProductEquivalents table.
def _get_batch_products_and_equivalents(db_session, product_ids: List[str], target_language_code: str) -> Dict[str, Dict[str, Any]]:
    """
    Fetches product details and their equivalents based on target language.
    Real implementation would query Products and ProductEquivalents tables/models.
    """
    products_data: Dict[str, Dict[str, Any]] = {}
    if not product_ids:
        return products_data

    # The db_session here is expected to be an SQLite connection for db_get_product_by_id
    conn = db_session # Rename for clarity as it's an SQLite connection

    # Efficiently fetch all products in the list
    if product_ids:
        placeholders = ','.join('?' for _ in product_ids)
        # Ensure product_ids are of the correct type for the query (e.g., int if product_id is INTEGER)
        # Assuming product_id in Products table is INTEGER. If TEXT, this is fine.
        # The db_get_product_by_id mock uses int, but actual might be different.
        # For now, assuming product_ids in list are already compatible type or string.
        # Let's assume product_id is INTEGER for this example, so convert pid_str.
        try:
            # Convert product_ids to int if they are expected to be integers for the IN clause
            # This depends on the actual type of Products.product_id
            # If Products.product_id is TEXT, then pid_str is fine.
            # If Products.product_id is INTEGER, map(int, product_ids) is needed.
            # products_crud.get_product_by_id takes int.

            # Corrected approach: query all products using IN clause.
            # This requires products_crud to have a function like get_products_by_ids_list.
            # If not, we construct the SQL here.

            # Assuming product_id is INTEGER for Products table
            # Ensure product_ids are integers for the query
            int_product_ids = [int(pid) for pid in product_ids if pid is not None]
            if not int_product_ids: # If all product_ids were None or list became empty
                return products_data

            sql_batch = f"SELECT * FROM Products WHERE product_id IN ({','.join('?'*len(int_product_ids))})"
            cursor = conn.cursor()
            cursor.execute(sql_batch, tuple(int_product_ids))
            fetched_products_raw = cursor.fetchall()

            fetched_products_map = {str(p['product_id']): dict(p) for p in fetched_products_raw}

            for pid_str in product_ids: # Iterate original list to maintain order/check existence
                product_dict = fetched_products_map.get(pid_str)
                if product_dict:
                    products_data[pid_str] = {
                        "id": pid_str, # Use the string version of ID as key
                        "original_name": product_dict.get('product_name', 'N/A'),
                        "original_description": product_dict.get('description', 'N/A'),
                        "original_language_code": product_dict.get('language_code', 'N/A'),
                        "base_unit_price": product_dict.get('base_unit_price', 0.0),
                        "unit_of_measure": product_dict.get('unit_of_measure', 'N/A'),
                        "product_weight_kg": product_dict.get('weight', None),
                        "product_dimensions_cm": product_dict.get('dimensions', None),
                        "product_code": product_dict.get('product_code', 'N/A'),
                        "equivalent_name": None, # TODO: Implement actual equivalent fetching if needed
                        "equivalent_description": None,
                        "equivalent_language_code": None,
                    }
                    # Mock translation logic (can be enhanced with actual equivalent product fetching)
                    current_product_data = products_data[pid_str]
                    if target_language_code != current_product_data["original_language_code"]:
                        # This part needs to query for an equivalent product in the target language.
                        # For now, simple mock:
                        if target_language_code == 'fr' and current_product_data["original_language_code"] == 'en':
                             current_product_data["equivalent_name"] = f"{current_product_data['original_name']} (FR)"
                             current_product_data["equivalent_description"] = f"{current_product_data['original_description']} (Description Française)"
                             current_product_data["equivalent_language_code"] = "fr"
                        # Add more language pair mocks or a real lookup
                else:
                    logging.warning(f"Product with ID {pid_str} not found in batch fetch.")
                    products_data[pid_str] = None
        except sqlite3.Error as e_batch:
            logging.error(f"Failed to batch fetch products: {e_batch}", exc_info=True)
            # Fallback to individual fetches (original N+1) if batch fails, or handle error
            for pid_str_fallback in product_ids: # Fallback loop
                 product_dict_fallback = db_get_product_by_id(conn, int(pid_str_fallback)) # Assuming int ID
                 if product_dict_fallback:
                     products_data[pid_str_fallback] = { "id": pid_str_fallback, "original_name": product_dict_fallback.get('product_name', 'N/A'), # simplified
                                                          "original_description": product_dict_fallback.get('description', 'N/A'), "base_unit_price": product_dict_fallback.get('base_unit_price',0.0)}
                 else: products_data[pid_str_fallback] = None


    return products_data


def get_proforma_invoice_context_data(
    client_id_arg: Optional[str] = None,
    company_id_arg: Optional[str] = None,
    target_language_code: str = "fr",
    project_id_arg: Optional[str] = None,
    proforma_instance: Optional[ProformaInvoice] = None, # Type hint with actual ProformaInvoice model
    linked_product_ids_for_doc: Optional[List[str]] = None, # Not directly used if proforma_instance is primary
    additional_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:

    client_id = client_id_arg
    company_id = company_id_arg
    project_id = project_id_arg

    if proforma_instance:
        logging.info(f"Using ProformaInvoice instance {proforma_instance.id} for context data.")
        client_id = proforma_instance.client_id
        company_id = proforma_instance.company_id
        project_id = proforma_instance.project_id
        # target_language_code could also be on proforma_instance if that model stores it.
        # Example: target_language_code = getattr(proforma_instance, 'language_code', target_language_code)

    if additional_context is None:
        additional_context = {}

    context: Dict[str, Any] = {
        "doc": {}, "client": {}, "seller": {}, "project": {}, "order": {}, # Added "order"
        "products": [], "lang": {}, "additional": additional_context,
        "placeholders": {}
    }

    context["lang"]["target_language_code"] = target_language_code
    doc_ctx = context["doc"]
    order_ctx = context["order"] # For order-specific details

    # --- Populate Document Info (doc_ctx) & Order Info (order_ctx) ---
    # Priority: proforma_instance -> additional_context -> defaults
    if proforma_instance:
        doc_ctx["proforma_id"] = proforma_instance.proforma_invoice_number
        doc_ctx["payment_terms"] = proforma_instance.payment_terms
        doc_ctx["delivery_terms"] = proforma_instance.delivery_terms
        doc_ctx["incoterms"] = proforma_instance.incoterms
        doc_ctx["named_place_of_delivery"] = proforma_instance.named_place_of_delivery
        doc_ctx["currency_symbol"] = CURRENCY_SYMBOLS.get(str(proforma_instance.currency).upper(), str(proforma_instance.currency))
        doc_ctx["proforma_notes"] = proforma_instance.notes
        # Financials directly from instance
        doc_ctx["subtotal_amount_raw"] = float(proforma_instance.subtotal_amount)
        doc_ctx["discount_amount_raw"] = float(proforma_instance.discount_amount or 0.0)
        doc_ctx["vat_amount_raw"] = float(proforma_instance.vat_amount)
        doc_ctx["grand_total_amount_raw"] = float(proforma_instance.grand_total_amount)
        # Dates
        doc_ctx["current_date"] = proforma_instance.created_date.strftime('%Y-%m-%d') if proforma_instance.created_date else datetime.now(timezone.utc).strftime('%Y-%m-%d')
        doc_ctx["sent_date"] = proforma_instance.sent_date.strftime('%Y-%m-%d') if proforma_instance.sent_date else None
        # Order specific details can also be sourced from proforma_instance if available
        order_ctx["client_order_number"] = getattr(proforma_instance, 'client_order_ref', additional_context.get("client_order_number", "N/A"))
        order_ctx["client_order_date"] = getattr(proforma_instance, 'client_order_date', additional_context.get("client_order_date", "N/A"))
        if isinstance(order_ctx["client_order_date"], datetime): # Format if it's a datetime object
            order_ctx["client_order_date"] = order_ctx["client_order_date"].strftime('%Y-%m-%d')

    else:
        # Fallback to additional_context or defaults if no proforma_instance
        doc_ctx["proforma_id"] = additional_context.get("proforma_id", f"PF-{uuid.uuid4().hex[:8].upper()}")
        doc_ctx["payment_terms"] = additional_context.get("payment_terms", get_doc_label("payment_terms_default", target_language_code, "Advance Payment"))
        doc_ctx["delivery_terms"] = additional_context.get("delivery_terms", get_doc_label("delivery_terms_default", target_language_code, "As agreed"))
        doc_ctx["incoterms"] = additional_context.get("incoterms", "EXW") # Incoterms are standard, usually not translated
        doc_ctx["named_place_of_delivery"] = additional_context.get("named_place_of_delivery", get_doc_label("named_place_default", target_language_code, "Seller's premises"))
        doc_ctx["currency_symbol"] = CURRENCY_SYMBOLS.get(additional_context.get("currency_code", "EUR").upper(), additional_context.get("currency_code", "EUR"))
        doc_ctx["proforma_notes"] = additional_context.get("notes", "")

        # Date formatting using QLocale
        locale = QLocale(QLocale.Language[target_language_code.capitalize() if len(target_language_code)==2 else "AnyLanguage"])
        current_date_dt = datetime.strptime(additional_context.get("current_date", datetime.now(timezone.utc).strftime('%Y-%m-%d')), '%Y-%m-%d')
        doc_ctx["current_date"] = locale.toString(QDate(current_date_dt.year, current_date_dt.month, current_date_dt.day), QLocale.ShortFormat)

        sent_date_str = additional_context.get("sent_date")
        if sent_date_str:
            sent_date_dt = datetime.strptime(sent_date_str, '%Y-%m-%d')
            doc_ctx["sent_date"] = locale.toString(QDate(sent_date_dt.year, sent_date_dt.month, sent_date_dt.day), QLocale.ShortFormat)
        else:
            doc_ctx["sent_date"] = None

        # Order specific from additional_context
        order_ctx["client_order_number"] = additional_context.get("client_order_number", get_doc_label("not_applicable_short", target_language_code, "N/A"))
        order_ctx["client_order_date"] = additional_context.get("client_order_date", get_doc_label("not_applicable_short", target_language_code, "N/A"))


    # VAT and Discount rates often come from additional_context during creation/regeneration
    doc_ctx["vat_rate_percentage"] = float(additional_context.get("vat_rate_percentage", 20.0))
    doc_ctx["discount_rate_percentage"] = float(additional_context.get("discount_rate_percentage", 0.0))
    doc_ctx["current_year"] = str(datetime.now(timezone.utc).year)
    doc_ctx["vat_label"] = additional_context.get("vat_label", get_doc_label("vat", target_language_code, "VAT"))


    db_conn = None # This will be an SQLite connection
    try:
        # db_session from additional_context is expected to be an SQLite connection if provided by API layer
        # Otherwise, get_db_connection() provides a new SQLite connection.
        db_conn = additional_context.get("db_session") or get_db_connection()

        # --- Seller Data ---
        seller_ctx = context["seller"]
        # proforma_instance.company would be an SQLAlchemy object if ProformaInvoice model is fully fleshed out
        # For now, db_get_company_by_id returns a dict from SQLite.
        seller_company_dict: Optional[Dict] = None
        if proforma_instance and hasattr(proforma_instance, 'company') and proforma_instance.company:
            # If proforma_instance.company is an ORM object, we might need to adapt
            # For now, assume we pass its ID to db_get_company_by_id or it's already a dict.
            # This part needs careful handling depending on type of proforma_instance.company.
            # Assuming proforma_instance.company is already a dict-like structure or has an 'id'
            seller_company_id_to_fetch = getattr(proforma_instance.company, 'id', company_id)
            if seller_company_id_to_fetch: # Ensure we have an ID
                 seller_company_dict = db_get_company_by_id(db_conn, seller_company_id_to_fetch)
            logging.info(f"Using seller company from proforma_instance (ID: {seller_company_id_to_fetch}): {'Found' if seller_company_dict else 'Not Found'}")
        elif company_id:
            seller_company_dict = db_get_company_by_id(db_conn, company_id)
            logging.info(f"Fetched seller company by ID {company_id}: {'Found' if seller_company_dict else 'Not Found'}")

        if seller_company_dict:
            seller_ctx["id"] = seller_company_dict.get('company_id', company_id) # Use 'company_id' from dict
            seller_ctx["company_name"] = seller_company_dict.get('company_name', "N/A")
            seller_ctx["email"] = seller_company_dict.get('email', "N/A")
            seller_ctx["phone"] = seller_company_dict.get('phone', "N/A")
            seller_ctx["website"] = seller_company_dict.get('website', "N/A")

            raw_address = seller_company_dict.get('address', "")
            payment_info = _parse_json_field(seller_company_dict.get('payment_info', "{}"))
            other_info_raw = seller_company_dict.get('other_info', "")
            other_info_json = _parse_json_field(other_info_raw)
            other_info_kv = _parse_key_value_string(other_info_raw if isinstance(other_info_raw, str) else "")

            seller_ctx["bank_name"] = payment_info.get("bank_name", additional_context.get("seller_bank_name", "N/A"))
            seller_ctx["bank_account_number"] = payment_info.get("account_number", additional_context.get("seller_bank_account_number", "N/A"))
            seller_ctx["bank_swift_bic"] = payment_info.get("swift_bic", additional_context.get("seller_bank_swift_bic", "N/A"))
            seller_ctx["bank_address"] = payment_info.get("bank_address", additional_context.get("seller_bank_address", "N/A"))
            seller_ctx["bank_account_holder_name"] = payment_info.get("account_holder_name", seller_ctx["company_name"])
            seller_ctx["bank_iban"] = payment_info.get("iban", additional_context.get("seller_bank_iban", seller_ctx["bank_account_number"]))

            seller_ctx["vat_id"] = other_info_json.get("vat_id", other_info_kv.get("vat", other_info_kv.get("vat_id", additional_context.get("seller_vat_id", "N/A"))))
            seller_ctx["registration_number"] = other_info_json.get("registration_number", other_info_kv.get("reg", other_info_kv.get("registration_number", additional_context.get("seller_registration_number", "N/A"))))

            seller_ctx["address_line1"] = raw_address
            seller_ctx["city"] = payment_info.get("city", additional_context.get("seller_city", other_info_json.get("city",""))) # Try other_info_json as well
            seller_ctx["postal_code"] = payment_info.get("postal_code", additional_context.get("seller_postal_code", other_info_json.get("postal_code","")))
            seller_ctx["country"] = payment_info.get("country", additional_context.get("seller_country", other_info_json.get("country","")))
            seller_ctx["address"] = _format_address_parts(seller_ctx["address_line1"], seller_ctx["city"], seller_ctx["postal_code"], seller_ctx["country"])
            seller_ctx["city_zip_country"] = _format_address_parts(None, seller_ctx["city"], seller_ctx["postal_code"], seller_ctx["country"])

            seller_personnel_list = db_get_personnel_for_company(db_conn, seller_ctx["id"]) # Returns list of dicts
            seller_rep_dict = seller_personnel_list[0] if seller_personnel_list else {}
            seller_ctx["representative_name"] = f"{seller_rep_dict.get('first_name','')} {seller_rep_dict.get('last_name','')}".strip() or "N/A"

            logo_filename = seller_company_dict.get('logo_filename', seller_company_dict.get('logo_path', None)) or additional_context.get("seller_logo_filename")
            if logo_filename and isinstance(logo_filename, str) and not logo_filename.startswith("http"):
                # Construct path relative to project root where assets/logos might be
                # Assuming LOGO_SUBDIR_CONTEXT is "assets/logos"
                # And PROJECT_ROOT_DIR_CONTEXT is the actual project root.
                abs_logo_path = os.path.join(PROJECT_ROOT_DIR_CONTEXT, LOGO_SUBDIR_CONTEXT, os.path.basename(logo_filename))
                if os.path.exists(abs_logo_path):
                    seller_ctx["logo_path"] = f"file:///{abs_logo_path.replace(os.sep, '/')}"
                else:
                    seller_ctx["logo_path"] = None # Fallback if file not found
                    logging.warning(f"Seller logo file not found at expected path: {abs_logo_path}")
            elif logo_filename and isinstance(logo_filename, str):
                seller_ctx["logo_path"] = logo_filename # Assumed to be a full URL or accessible absolute path
            else:
                seller_ctx["logo_path"] = None
        else:
            logging.warning(f"Seller company data not found for ID {company_id}. Using fallbacks.")
            # Fallback logic (remains same)
            for k_seller in ["company_name", "email", "phone", "website", "bank_name", "bank_account_number", "bank_swift_bic", "bank_address", "bank_account_holder_name", "bank_iban", "vat_id", "registration_number", "address_line1", "city", "postal_code", "country", "address", "representative_name", "logo_path", "city_zip_country"]:
                seller_ctx[k_seller] = additional_context.get(f"seller_{k_seller}", "N/A")


        # --- Client Data ---
        client_ctx = context["client"]
        client_dict: Optional[Dict] = None # db_get_client_by_id returns a dict
        if proforma_instance and hasattr(proforma_instance, 'client') and proforma_instance.client:
            client_id_to_fetch = getattr(proforma_instance.client, 'id', client_id)
            if client_id_to_fetch:
                client_dict = db_get_client_by_id(db_conn, client_id_to_fetch)
            logging.info(f"Using client from proforma_instance (ID: {client_id_to_fetch}): {'Found' if client_dict else 'Not Found'}")
        elif client_id:
            client_dict = db_get_client_by_id(db_conn, client_id)
            logging.info(f"Fetched client by ID {client_id}: {'Found' if client_dict else 'Not Found'}")

        if client_dict:
            client_ctx["id"] = client_dict.get('client_id', client_id) # Use 'client_id' from dict
            client_ctx["company_name"] = client_dict.get('company_name', "N/A")
            client_ctx["contact_person_name_default"] = client_dict.get('client_name', "N/A")

            client_notes_raw = client_dict.get('notes', "")
            client_notes_json = _parse_json_field(client_notes_raw)
            client_notes_kv = _parse_key_value_string(client_notes_raw if isinstance(client_notes_raw, str) else "")

            client_dist_info_raw = client_dict.get('distributor_specific_info', "")
            client_dist_info_json = _parse_json_field(client_dist_info_raw)
            client_dist_info_kv = _parse_key_value_string(client_dist_info_raw if isinstance(client_dist_info_raw, str) else "")

            client_ctx["vat_id"] = client_notes_json.get("vat_id", client_notes_kv.get("vat", client_dist_info_json.get("vat_id", client_dist_info_kv.get("vat", additional_context.get("client_vat_id", "N/A")))))
            client_ctx["registration_number"] = client_notes_json.get("registration_number", client_notes_kv.get("reg", client_dist_info_json.get("registration_number", client_dist_info_kv.get("reg", additional_context.get("client_registration_number", "N/A")))))

            # Ensure primary_contacts is a list of dicts
            primary_contacts_list = db_get_contacts_for_client(db_conn, client_ctx["id"], is_primary=True) # Assuming this now returns list of dicts
            primary_contact_dict = primary_contacts_list[0] if primary_contacts_list else None

            if primary_contact_dict:
                client_ctx["representative_name"] = f"{primary_contact_dict.get('givenName','')} {primary_contact_dict.get('familyName','')}".strip() or client_ctx["contact_person_name_default"]
                client_ctx["email"] = primary_contact_dict.get('email', client_dict.get('email', "N/A"))
                client_ctx["phone"] = primary_contact_dict.get('phone', client_dict.get('phone', "N/A"))
                client_ctx["address_line1"] = primary_contact_dict.get('address_streetAddress', client_dict.get('address_line1', "N/A")) # Fallback to client's address_line1 if contact doesn't have one

                client_city_id = client_dict.get('city_id')
                client_city_obj = db_get_city_by_id(db_conn, client_city_id) if client_city_id else None
                client_ctx["city"] = primary_contact_dict.get('address_city', client_city_obj.get('name', "N/A") if client_city_obj else "N/A")

                client_ctx["postal_code"] = primary_contact_dict.get('address_postalCode', client_dict.get('postal_code', "N/A")) # Fallback

                client_country_id = client_dict.get('country_id')
                client_country_obj = db_get_country_by_id(db_conn, client_country_id) if client_country_id else None
                client_ctx["country"] = primary_contact_dict.get('address_country', client_country_obj.get('name', "N/A") if client_country_obj else "N/A")
            else: # Fallback if no primary contact
                client_ctx["representative_name"] = client_ctx["contact_person_name_default"]
                client_ctx["email"] = client_dict.get('email', additional_context.get("client_email", "N/A"))
                client_ctx["phone"] = client_dict.get('phone', additional_context.get("client_phone", "N/A"))
                client_ctx["address_line1"] = client_dict.get('address_line1', additional_context.get("client_address_line1", "N/A"))

                client_city_id_fb = client_dict.get('city_id')
                client_city_obj_fb = db_get_city_by_id(db_conn, client_city_id_fb) if client_city_id_fb else None
                client_ctx["city"] = client_city_obj_fb.get('name', additional_context.get("client_city", "N/A")) if client_city_obj_fb else additional_context.get("client_city", "N/A")

                client_ctx["postal_code"] = client_dict.get('postal_code', additional_context.get("client_postal_code", "N/A"))

                client_country_id_fb = client_dict.get('country_id')
                client_country_obj_fb = db_get_country_by_id(db_conn, client_country_id_fb) if client_country_id_fb else None
                client_ctx["country"] = client_country_obj_fb.get('name', additional_context.get("client_country", "N/A")) if client_country_obj_fb else additional_context.get("client_country", "N/A")


            client_ctx["address"] = _format_address_parts(client_ctx["address_line1"], client_ctx["city"], client_ctx["postal_code"], client_ctx["country"])
            client_ctx["city_zip_country"] = _format_address_parts(None, client_ctx["city"], client_ctx["postal_code"], client_ctx["country"])
        else: # Fallback if client_dict is None
            logging.warning(f"Client data not found for ID {client_id}. Using fallbacks.")
            for k_client in ["company_name", "email", "phone", "vat_id", "registration_number", "address_line1", "city", "postal_code", "country", "address", "representative_name", "city_zip_country"]:
                client_ctx[k_client] = additional_context.get(f"client_{k_client}", "N/A")

        # --- Project Data ---
        project_ctx = context["project"]
        project_dict: Optional[Dict] = None # db_get_project_by_id returns a dict
        if proforma_instance and hasattr(proforma_instance, 'project') and proforma_instance.project:
            project_id_to_fetch = getattr(proforma_instance.project, 'id', project_id)
            if project_id_to_fetch:
                project_dict = db_get_project_by_id(db_conn, project_id_to_fetch)
            logging.info(f"Using project from proforma_instance (ID: {project_id_to_fetch}): {'Found' if project_dict else 'Not Found'}")
        elif project_id:
            project_dict = db_get_project_by_id(db_conn, project_id)
            logging.info(f"Fetched project by ID {project_id}: {'Found' if project_dict else 'Not Found'}")

        if project_dict:
            project_ctx["id"] = project_dict.get('project_id', project_id) # Use 'project_id' from dict
            project_ctx["name"] = project_dict.get('name', "N/A")
            project_ctx["description"] = project_dict.get('description', "N/A")
            project_ctx["identifier"] = project_dict.get('project_identifier', "N/A")
        else: # Fallbacks
            project_ctx["id"] = project_id or "N/A"
            project_ctx["name"] = additional_context.get("project_name", "N/A")
            project_ctx["description"] = additional_context.get("project_description", "N/A")
            # Fallback for identifier might use client's project_identifier if project_id is not specified
            project_ctx["identifier"] = additional_context.get("project_identifier", (client_dict.get('project_identifier', "N/A") if client_dict else "N/A"))


        # --- Products Data ---
        products_list_for_doc = []
        products_table_html_rows_list = []
        subtotal_amount_calculated_from_items = 0.0
        product_items_to_process: List[Dict[str, Any]] = []
        product_ids_for_batch_fetch: List[str] = []

        if proforma_instance and hasattr(proforma_instance, 'items') and proforma_instance.items:
            logging.info(f"Processing {len(proforma_instance.items)} items from proforma_instance.")
            for item_instance in proforma_instance.items: # item_instance is an SQLAlchemy object
                product_items_to_process.append({
                    "product_id": str(getattr(item_instance, 'product_id', None)), # Ensure product_id is string
                    "quantity": float(getattr(item_instance, 'quantity', 0)),
                    "unit_price": float(getattr(item_instance, 'unit_price', 0.0)),
                    "description": getattr(item_instance, 'description', "N/A"), # This is ProformaInvoiceItem.description
                    "total_price": float(getattr(item_instance, 'total_price', 0.0)),
                })
                if getattr(item_instance, 'product_id', None):
                    product_ids_for_batch_fetch.append(str(getattr(item_instance, 'product_id')))

        elif additional_context.get('lite_selected_products'):
            logging.info("Processing items from additional_context['lite_selected_products'].")
            for item_data_ac in additional_context['lite_selected_products']:
                pid_ac = str(item_data_ac.get("product_id")) if item_data_ac.get("product_id") is not None else None
                if pid_ac: product_ids_for_batch_fetch.append(pid_ac)
                product_items_to_process.append({
                    "product_id": pid_ac,
                    "quantity": float(item_data_ac.get("quantity", 1)),
                    "unit_price_override": float(item_data_ac.get("unit_price_override")) if item_data_ac.get("unit_price_override") is not None else None,
                    "description_override": item_data_ac.get("description"),
                })

        product_details_batch = {}
        if product_ids_for_batch_fetch:
            # Pass db_conn (SQLite connection) to _get_batch_products_and_equivalents
            product_details_batch = _get_batch_products_and_equivalents(db_conn, list(set(product_ids_for_batch_fetch)), target_language_code)

        for item_data_to_render in product_items_to_process:
            p_id_render = item_data_to_render.get("product_id") # Already string or None
            # original_product_details will be a dict from product_details_batch
            original_product_details = product_details_batch.get(p_id_render) if p_id_render else None

            effective_unit_price = item_data_to_render.get("unit_price")
            if effective_unit_price is None:
                effective_unit_price = item_data_to_render.get("unit_price_override")
                if effective_unit_price is None and original_product_details:
                    effective_unit_price = original_product_details.get("base_unit_price", 0.0)
                elif effective_unit_price is None: # No price info at all
                    effective_unit_price = 0.0

            # Description priority: ProformaInvoiceItem.description -> item_data_ac.description -> Product.name
            description_for_render = item_data_to_render.get("description") # From ProformaInvoiceItem
            # Determine product name
            product_name_for_display = "N/A"
            if original_product_details:
                if target_language_code != original_product_details.get("original_language_code") and original_product_details.get("equivalent_name"):
                    product_name_for_display = original_product_details["equivalent_name"]
                else:
                    product_name_for_display = original_product_details.get("original_name", "N/A")
            elif item_data_to_render.get("description"): # Use item's description if no product details
                 product_name_for_display = item_data_to_render.get("description")
            elif item_data_to_render.get("description_override"):
                 product_name_for_display = item_data_to_render.get("description_override")
            else:
                 product_name_for_display = "Custom Item"


            # Determine product_description (secondary, potentially longer description)
            product_description_for_display = ""
            # Priority: item_data_to_render.description (from ProformaInvoiceItem) -> item_data_to_render.description_override -> original_product_details.description (translated or original)
            if item_data_to_render.get("description") and item_data_to_render.get("description") != product_name_for_display :
                product_description_for_display = item_data_to_render.get("description")
            elif item_data_to_render.get("description_override") and item_data_to_render.get("description_override") != product_name_for_display:
                product_description_for_display = item_data_to_render.get("description_override")
            elif original_product_details:
                temp_desc = ""
                if target_language_code != original_product_details.get("original_language_code") and original_product_details.get("equivalent_description"):
                    temp_desc = original_product_details["equivalent_description"]
                else:
                    temp_desc = original_product_details.get("original_description", "")

                if temp_desc != product_name_for_display: # Only use if different from the main name
                    product_description_for_display = temp_desc


            quantity_render = item_data_to_render.get("quantity", 0.0)
            total_price_render = item_data_to_render.get("total_price")
            if total_price_render is None: # Calculate if not provided (e.g. from proforma_instance.items)
                total_price_render = quantity_render * effective_unit_price

            if not proforma_instance: # If creating new, calculate subtotal iteratively
                subtotal_amount_calculated_from_items += total_price_render

            product_code_display = original_product_details.get("product_code", "N/A") if original_product_details else "N/A"
            original_name_if_translated = ""
            if original_product_details and \
               target_language_code != original_product_details.get("original_language_code") and \
               product_name_for_display != original_product_details.get("original_name"):
                original_name_if_translated = original_product_details.get("original_name","")


            product_entry = {
                "id": str(p_id_render) if p_id_render else uuid.uuid4().hex[:8],
                "product_code": product_code_display,
                "name": product_name_for_display,
                "description": product_description_for_display, # Secondary description
                "original_name": original_name_if_translated, # Original name if translated name is used
                "quantity": quantity_render,
                "unit_price_raw": float(effective_unit_price),
                "unit_price_formatted": format_currency(float(effective_unit_price), doc_ctx["currency_symbol"]),
                "total_price_raw": float(total_price_render),
                "total_price_formatted": format_currency(float(total_price_render), doc_ctx["currency_symbol"]),
                "unit_of_measure": original_product_details.get("unit_of_measure", "N/A") if original_product_details else "N/A",
                "original_name": original_product_details.get("original_name", "") if original_product_details else "",
                "weight_kg": original_product_details.get("product_weight_kg") if original_product_details else None,
                "dimensions_cm": original_product_details.get("product_dimensions_cm") if original_product_details else None,
            }
            products_list_for_doc.append(product_entry)
            products_table_html_rows_list.append(
                f"<tr><td>{len(products_list_for_doc)}</td>"
                f"<td>{product_entry['product_code']}</td>" # Added product code to table row
                f"<td><strong>{product_entry['name']}</strong></td>"
                f"<td class='number'>{product_entry['quantity']}</td>"
                f"<td class='number'>{product_entry['unit_price_formatted']}</td>"
                f"<td class='number'>{product_entry['total_price_formatted']}</td></tr>"
            )
        context["products"] = products_list_for_doc
        doc_ctx["products_table_rows"] = "".join(products_table_html_rows_list)

        # --- Totals Finalization (remains same) ---
        if not proforma_instance:
            doc_ctx["subtotal_amount_raw"] = subtotal_amount_calculated_from_items
            current_discount_rate = doc_ctx.get("discount_rate_percentage", 0.0)
            doc_ctx["discount_amount_raw"] = (current_discount_rate / 100.0) * doc_ctx["subtotal_amount_raw"]
            amount_after_discount = doc_ctx["subtotal_amount_raw"] - doc_ctx["discount_amount_raw"]
            current_vat_rate = doc_ctx.get("vat_rate_percentage", 20.0)
            doc_ctx["vat_amount_raw"] = (current_vat_rate / 100.0) * amount_after_discount
            doc_ctx["grand_total_amount_raw"] = amount_after_discount + doc_ctx["vat_amount_raw"]

        doc_ctx["subtotal_amount_formatted"] = format_currency(doc_ctx["subtotal_amount_raw"], doc_ctx["currency_symbol"])
        doc_ctx["discount_amount_formatted"] = format_currency(doc_ctx["discount_amount_raw"], doc_ctx["currency_symbol"])
        doc_ctx["vat_amount_formatted"] = format_currency(doc_ctx["vat_amount_raw"], doc_ctx["currency_symbol"])
        doc_ctx["grand_total_amount_formatted"] = format_currency(doc_ctx["grand_total_amount_raw"], doc_ctx["currency_symbol"])
        doc_ctx["grand_total_amount_words"] = additional_context.get("grand_total_amount_words", "N/A")

        # --- Client Specific Notes (remains same) ---
        doc_notes_type = additional_context.get("client_document_notes_type", "Proforma")
        if client_id:
            notes_text = db_get_effective_document_note(db_conn, client_id, doc_notes_type, target_language_code)
            doc_ctx["client_specific_footer_notes"] = notes_text.replace('\n', '<br>') if notes_text and isinstance(notes_text, str) else ""
        else:
            doc_ctx["client_specific_footer_notes"] = ""

    except Exception as e:
        logging.error(f"Error in get_proforma_invoice_context_data: {e}", exc_info=True)
        for section in ["doc", "client", "seller", "project", "order"]: # Added order
            if not context[section]:
                context[section] = {k: "Error - See Logs" for k in ["name", "id", "address"]}
        doc_ctx.setdefault("currency_symbol", "$")
        doc_ctx.setdefault("products_table_rows", "<tr><td colspan='6'>Error loading product data.</td></tr>") # colspan changed to 6

    finally:
        # Close connection only if it was opened by this function
        if db_conn and not additional_context.get("db_session"):
            db_conn.close()


    # --- Final Placeholder Mapping (remains largely same, added order placeholders) ---
    context["placeholders"]["PROFORMA_ID"] = doc_ctx.get("proforma_id", "N/A")
    context["placeholders"]["DATE"] = doc_ctx.get("current_date", "N/A")
    # ... (other doc placeholders remain same) ...
    context["placeholders"]["PROFORMA_NOTES"] = doc_ctx.get("proforma_notes", "")

    # Order specific placeholders
    order_ctx_final = context.get("order", {})
    context["placeholders"]["ORDER_CLIENT_NUMBER"] = order_ctx_final.get("client_order_number", "N/A")
    context["placeholders"]["ORDER_CLIENT_DATE"] = order_ctx_final.get("client_order_date", "N/A")


    # Seller details (remains same)
    seller_ctx_final = context.get("seller", {})
    # ... (all seller placeholders remain same) ...
    context["placeholders"]["SELLER_BANK_ADDRESS"] = seller_ctx_final.get("bank_address", "N/A")

    # Client details (remains same)
    client_ctx_final = context.get("client", {})
    # ... (all client placeholders remain same) ...
    context["placeholders"]["BUYER_COMPANY_REGISTRATION_NUMBER"] = client_ctx_final.get("registration_number", "N/A")

    # Project details (remains same)
    project_ctx_final = context.get("project", {})
    # ... (all project placeholders remain same) ...
    context["placeholders"]["PROJECT_NAME"] = project_ctx_final.get("name", "N/A")

    # Totals (remains same)
    # ... (all total placeholders remain same) ...
    context["placeholders"]["GRAND_TOTAL_AMOUNT_WORDS"] = doc_ctx.get("grand_total_amount_words", "N/A")

    # Merge any remaining additional_context items (remains same)
    for key, value in additional_context.items():
        context["placeholders"].setdefault(key.upper(), value)
        context["placeholders"].setdefault(key, value)

    # For direct access in template (remains same, added order)
    context["doc"].update(doc_ctx)
    context["seller"].update(seller_ctx)
    context["client"].update(client_ctx)
    context["project"].update(project_ctx)
    context["order"].update(order_ctx) # Added order

    return context

if __name__ == '__main__':
    # This section is for example usage and basic testing.
    print("Proforma Invoice Utilities Loaded - __main__ section.")

    # Example:
    # 1. Setup a dummy in-memory SQLite DB for testing
    #    (Requires defining schema for Companies, Clients, Products, Contacts etc. or using existing test DB setup)
    # 2. Populate with some test data for a company, a client, a contact, and a product.
    # 3. Call get_proforma_invoice_context_data with appropriate IDs and context.

    # Due to complexity of setting up a full mock DB here, this example will be conceptual.
    # In a real test suite, you'd use testing.fixtures or a dedicated test DB.

    # mock_db_conn = get_db_connection(":memory:") # Create in-memory for test
    # # ... (code to create tables and insert test data into mock_db_conn) ...

    # test_client_id = "client_test_123"
    # test_company_id = "company_test_abc"
    # test_product_id_str = "1" # Assuming product ID is string for _get_batch_products_and_equivalents

    # mock_additional_context = {
    #     "db_session": mock_db_conn, # Pass the connection
    #     "seller_city": "Paris",
    #     "seller_postal_code": "75001",
    #     "seller_country": "France",
    #     "client_order_number": "PO-CLIENT-007",
    #     "client_order_date": "2023-01-15",
    #     'lite_selected_products': [
    #         {"product_id": test_product_id_str, "quantity": 2, "unit_price_override": 150.0, "description": "Super Produit Spécial"}
    #     ]
    # }
    #
    # print(f"Testing get_proforma_invoice_context_data with client {test_client_id}, company {test_company_id}")
    # try:
    #     context_data = get_proforma_invoice_context_data(
    #         client_id_arg=test_client_id,
    #         company_id_arg=test_company_id,
    #         target_language_code="fr",
    #         additional_context=mock_additional_context
    #     )
    #     import pprint
    #     pprint.pprint(context_data)
    #     # Check specific fields
    #     # print(f"Seller Bank IBAN: {context_data.get('seller',{}).get('bank_iban')}")
    #     # print(f"Client VAT ID: {context_data.get('client',{}).get('vat_id')}")
    #     # print(f"Product Code for first product: {context_data.get('products',[{}])[0].get('product_code')}")
    #     # print(f"Client Order Number: {context_data.get('order',{}).get('client_order_number')}")

    # except Exception as e:
    #     print(f"Error during example test run: {e}", exc_info=True)
    # finally:
    #     if mock_db_conn:
    #         mock_db_conn.close()
    pass


def get_final_invoice_context_data(
    client_id: str,
    company_id: str,
    target_language_code: str,
    project_id: str = None,
    # line_items can be passed in additional_context:
    # e.g., additional_context['line_items'] = [{'product_id': X, 'quantity': Y, 'unit_price': Z}, ...]
    # linked_product_ids_for_doc is less likely for final invoice if prices/qtys are fixed from a quote/order
    additional_context: dict = None
) -> dict:
    if additional_context is None:
        additional_context = {}

    context = {
        "doc": {}, "client": {}, "seller": {}, "project": {},
        "products": [], "lang": {}, "additional": additional_context,
        "placeholders": {}
    }

    # --- Language & Static Text ---
    context["lang"]["target_language_code"] = target_language_code
    # Title can be set here or in template. If set here, it can be dynamic.
    # For multilingual, template is better for static titles.
    # We'll set a default that can be overridden by additional_context or template.
    context["doc"]["invoice_title"] = additional_context.get("invoice_title", get_doc_label("final_invoice_title", target_language_code, "INVOICE"))


    # --- Document Info (defaults and from additional_context) ---
    doc_ctx = context["doc"]
    locale = QLocale(QLocale.Language[target_language_code.capitalize() if len(target_language_code)==2 else "AnyLanguage"])

    # issue_date and due_date should ideally come from additional_context or be set when the invoice record is created.
    issue_date_str = additional_context.get("issue_date", datetime.now(timezone.utc).strftime('%Y-%m-%d'))
    issue_date_dt = datetime.strptime(issue_date_str, '%Y-%m-%d')
    doc_ctx["issue_date"] = locale.toString(QDate(issue_date_dt.year, issue_date_dt.month, issue_date_dt.day), QLocale.ShortFormat)

    default_due_date_dt = issue_date_dt + timedelta(days=30)
    due_date_str = additional_context.get("due_date", default_due_date_dt.strftime('%Y-%m-%d'))
    due_date_dt = datetime.strptime(due_date_str, '%Y-%m-%d')
    doc_ctx["due_date"] = locale.toString(QDate(due_date_dt.year, due_date_dt.month, due_date_dt.day), QLocale.ShortFormat)


    doc_ctx["currency_symbol"] = CURRENCY_SYMBOLS.get(additional_context.get("currency_code", "EUR").upper(), additional_context.get("currency_code", "EUR"))
    doc_ctx["payment_terms"] = additional_context.get("final_payment_terms", get_doc_label("final_invoice_payment_terms_default", target_language_code, "Payment due within 30 days."))
    doc_ctx["notes"] = additional_context.get("invoice_notes", "")

    # Tax details from additional_context or defaults
    doc_ctx["tax_label"] = additional_context.get("tax_label", get_doc_label("vat", target_language_code, "VAT"))
    doc_ctx["tax_rate_percentage"] = float(additional_context.get("tax_rate_percentage", 20.0)) # Default 20%
    doc_ctx["discount_rate_percentage"] = float(additional_context.get("discount_rate_percentage", 0.0))


    db_conn = None # Changed variable name
    try:
        db_conn = additional_context.get("db_session") or get_db_connection() # Corrected function call, "db_session" in context is now a connection

        # --- Invoice Number ---
        # Pass db_conn to get_next_invoice_number
        doc_ctx["invoice_number"] = additional_context.get("invoice_number") or get_next_invoice_number(db_conn)


        # --- Seller Data (largely reused from proforma) ---
        seller_ctx = context["seller"]
        seller_company_data = db_get_company_by_id(db_conn, company_id) if company_id else None # Use db_conn
        if seller_company_data:
            seller_ctx["id"] = seller_company_data.id
            seller_ctx["company_name"] = seller_company_data.name or "N/A"
            seller_ctx["email"] = seller_company_data.email or "N/A"
            seller_ctx["phone"] = seller_company_data.phone or "N/A"
            seller_ctx["website"] = seller_company_data.website or "N/A"

            raw_address = seller_company_data.address or ""
            payment_info = _parse_json_field(seller_company_data.payment_info)
            other_info_json = _parse_json_field(seller_company_data.other_info)

            # Bank details are crucial for final invoice
            seller_ctx["bank_name"] = payment_info.get("bank_name", additional_context.get("seller_bank_name", "N/A"))
            seller_ctx["bank_account_holder_name"] = payment_info.get("account_holder_name", seller_ctx["company_name"])
            seller_ctx["bank_iban"] = payment_info.get("iban", additional_context.get("seller_bank_iban", "N/A"))
            seller_ctx["bank_swift_bic"] = payment_info.get("swift_bic", additional_context.get("seller_bank_swift_bic", "N/A"))
            # seller_ctx["bank_account_number"] = payment_info.get("account_number", "N/A") # IBAN is usually preferred
            # seller_ctx["bank_address"] = payment_info.get("bank_address", "N/A")


            seller_ctx["vat_id"] = other_info_json.get("vat_id", additional_context.get("seller_vat_id", "N/A"))
            # seller_ctx["registration_number"] = other_info_json.get("registration_number", "N/A")

            seller_ctx["address_line1"] = raw_address
            seller_ctx["city"] = additional_context.get("seller_city", other_info_json.get("city", "N/A"))
            seller_ctx["postal_code"] = additional_context.get("seller_postal_code", other_info_json.get("postal_code", "N/A"))
            seller_ctx["country"] = additional_context.get("seller_country", other_info_json.get("country", "N/A"))
            seller_ctx["address"] = _format_address_parts(seller_ctx["address_line1"], seller_ctx["city"], seller_ctx["postal_code"], seller_ctx["country"])
            seller_ctx["city_zip_country"] = _format_address_parts(None, seller_ctx["city"], seller_ctx["postal_code"], seller_ctx["country"])


            logo_filename = seller_company_data.logo_filename or additional_context.get("seller_logo_filename")
            if logo_filename:
                 # Ensure APP_ROOT_DIR_CONTEXT is correctly defined for your app structure
                seller_ctx["logo_path"] = os.path.join(APP_ROOT_DIR_CONTEXT, LOGO_SUBDIR_CONTEXT, logo_filename)
            else:
                seller_ctx["logo_path"] = None
        else: # Fallbacks
            for k in ["company_name", "email", "phone", "website", "bank_name", "bank_account_holder_name", "bank_iban", "bank_swift_bic", "vat_id", "address_line1", "city", "postal_code", "country", "address", "logo_path", "city_zip_country"]:
                seller_ctx[k] = additional_context.get(f"seller_{k}", "N/A")

        # --- Client Data (largely reused) ---
        client_ctx = context["client"]
        client_data = db_get_client_by_id(db_conn, client_id) if client_id else None # Use db_conn
        if client_data:
            client_ctx["id"] = client_data.id
            client_ctx["company_name"] = client_data.company_name or "N/A"
            client_ctx["representative_name"] = client_data.client_name or "N/A" # Fallback representative

            client_dist_info_json = _parse_json_field(client_data.distributor_specific_info)
            client_ctx["vat_id"] = client_dist_info_json.get("vat_id", additional_context.get("client_vat_id", "N/A"))

            primary_contacts = db_get_contacts_for_client(db_conn, client_id, is_primary=True) # Use db_conn
            primary_contact = primary_contacts[0] if primary_contacts else None

            if primary_contact:
                client_ctx["representative_name"] = f"{primary_contact.first_name or ''} {primary_contact.last_name or ''}".strip() or client_ctx["representative_name"]
                client_ctx["address_line1"] = primary_contact.address_streetAddress or "N/A"
                client_ctx["city"] = primary_contact.address_city or (db_get_city_by_id(db_conn, client_data.city_id).name if client_data.city_id else "N/A") # Use db_conn
                client_ctx["postal_code"] = primary_contact.address_postalCode or "N/A"
                client_ctx["country"] = primary_contact.address_country or (db_get_country_by_id(db_conn, client_data.country_id).name if client_data.country_id else "N/A") # Use db_conn
            else:
                client_ctx["address_line1"] = additional_context.get("client_address_line1", "N/A")
                client_ctx["city"] = (db_get_city_by_id(db_conn, client_data.city_id).name if client_data.city_id else None) or additional_context.get("client_city", "N/A") # Use db_conn
                client_ctx["postal_code"] = additional_context.get("client_postal_code", "N/A")
                client_ctx["country"] = (db_get_country_by_id(db_conn, client_data.country_id).name if client_data.country_id else None) or additional_context.get("client_country", "N/A") # Use db_conn

            client_ctx["address"] = _format_address_parts(client_ctx["address_line1"], client_ctx["city"], client_ctx["postal_code"], client_ctx["country"])
            client_ctx["city_zip_country"] = _format_address_parts(None, client_ctx["city"], client_ctx["postal_code"], client_ctx["country"])
        else:
             for k in ["company_name", "representative_name", "address_line1", "city", "postal_code", "country", "address", "vat_id", "city_zip_country"]:
                client_ctx[k] = additional_context.get(f"client_{k}", "N/A")

        # --- Project Data (largely reused) ---
        project_ctx = context["project"]
        if project_id:
            project_data = db_get_project_by_id(db_conn, project_id) # Use db_conn
            if project_data:
                project_ctx["id"] = project_data.id
                project_ctx["name"] = project_data.name or "N/A"
            else: project_ctx["name"] = "Project Not Found"
        else: project_ctx["name"] = additional_context.get("project_name","N/A")


        # --- Products / Line Items ---
        products_list_for_doc = []
        subtotal_amount_calculated = 0.0

        # Line items for a final invoice should ideally come from `additional_context`
        # to reflect agreed-upon quantities and prices from an order or quote.
        line_items_source = additional_context.get('line_items', [])

        if line_items_source:
            all_product_ids_from_items = [item["product_id"] for item in line_items_source if "product_id" in item]
            product_details_batch = _get_batch_products_and_equivalents(db_conn, all_product_ids_from_items, target_language_code) # Use db_conn

            for item_data in line_items_source:
                p_id = item_data.get("product_id")
                original_product_details = product_details_batch.get(p_id)
                if not original_product_details:
                    # Product details not found, use provided item_data or skip
                    product_name_for_doc = item_data.get("name", "Unknown Product")
                    product_description_for_doc = item_data.get("description", "")
                    language_match = False # Cannot determine without original details
                    unit_of_measure = "N/A"
                else:
                    product_name_for_doc = original_product_details["original_name"]
                    product_description_for_doc = original_product_details["original_description"]
                    language_match = (original_product_details["original_language_code"] == target_language_code)
                    unit_of_measure = original_product_details["unit_of_measure"]
                    if not language_match and original_product_details["equivalent_name"]:
                        product_name_for_doc = original_product_details["equivalent_name"]
                        product_description_for_doc = original_product_details["equivalent_description"]
                        language_match = True

                quantity = float(item_data.get("quantity", 0))
                # Critical: unit_price for final invoice should be from item_data if provided
                unit_price = float(item_data.get("unit_price", original_product_details.get("base_unit_price", 0) if original_product_details else 0))

                total_price = quantity * unit_price
                subtotal_amount_calculated += total_price

                product_entry = {
                    "id": p_id, "name": product_name_for_doc, "description": product_description_for_doc,
                    "quantity": quantity,
                    "unit_price_raw": unit_price,
                    "unit_price_formatted": format_currency(unit_price, doc_ctx["currency_symbol"]),
                    "total_price_raw": total_price,
                    "total_price_formatted": format_currency(total_price, doc_ctx["currency_symbol"]),
                    "unit_of_measure": unit_of_measure, "language_match": language_match,
                }
                products_list_for_doc.append(product_entry)
        else:
            logging.warning("No 'line_items' provided in additional_context for final invoice. Product list will be empty.")
            # Optionally, could fall back to ClientProjectProducts like proforma, but this is less typical for final invoices.

        context["products"] = products_list_for_doc

        # --- Totals ---
        doc_ctx["subtotal_amount_raw"] = subtotal_amount_calculated
        doc_ctx["subtotal_amount_formatted"] = format_currency(subtotal_amount_calculated, doc_ctx["currency_symbol"])

        discount_amount = (doc_ctx["discount_rate_percentage"] / 100.0) * subtotal_amount_calculated
        doc_ctx["discount_amount_raw"] = discount_amount # Store raw value for template logic
        doc_ctx["discount_amount_formatted"] = format_currency(discount_amount, doc_ctx["currency_symbol"])

        amount_after_discount = subtotal_amount_calculated - discount_amount
        doc_ctx["amount_after_discount_raw"] = amount_after_discount # For tax calculation base

        tax_amount = (doc_ctx["tax_rate_percentage"] / 100.0) * amount_after_discount
        doc_ctx["tax_amount_raw"] = tax_amount
        doc_ctx["tax_amount_formatted"] = format_currency(tax_amount, doc_ctx["currency_symbol"])

        grand_total_amount = amount_after_discount + tax_amount
        doc_ctx["grand_total_amount_raw"] = grand_total_amount
        doc_ctx["grand_total_amount_formatted"] = format_currency(grand_total_amount, doc_ctx["currency_symbol"])
        doc_ctx["grand_total_amount_words"] = additional_context.get("grand_total_amount_words", "N/A") # Placeholder

    except Exception as e:
        logging.error(f"Error in get_final_invoice_context_data: {e}", exc_info=True)
        # Populate with N/A to prevent crashes in template rendering (similar to proforma)
        for section_key in ["doc", "client", "seller", "project"]:
            if not context[section_key]: # if section is empty due to early error
                context[section_key] = {k: "Error - See Logs" for k in ["name", "id", "address"]}
        doc_ctx.setdefault("currency_symbol", "$")
        doc_ctx.setdefault("invoice_number", "ERROR-GEN")
        # ... (add more critical fallbacks for doc_ctx if needed)
    finally:
        # Connection management: if this function created the connection, it should close it.
        # Assuming connection is managed by caller or a context manager via get_db_connection()
        if db_conn and not additional_context.get("db_session"): # "db_session" key in context is now a connection
            # This check is problematic if get_db_connection() returns a new connection each time
            # and is not a context manager. The caller of this function should manage the connection.
            # For now, let's assume the caller handles connection closing.
            pass

    # --- Final Placeholder Mapping (Flat dictionary for simple template engines) ---
    # This can be useful but for Handlebars/Jinja2, direct context access (e.g. {{doc.invoice_number}}) is common.
    # For consistency with proforma and potential simpler template engines, we can populate placeholders.

    # Document details
    context["placeholders"]["doc.invoice_title"] = doc_ctx.get("invoice_title", "INVOICE")
    context["placeholders"]["doc.invoice_number"] = doc_ctx.get("invoice_number", "N/A")
    context["placeholders"]["doc.issue_date"] = doc_ctx.get("issue_date", "N/A")
    context["placeholders"]["doc.due_date"] = doc_ctx.get("due_date", "N/A")
    context["placeholders"]["doc.payment_terms"] = doc_ctx.get("payment_terms", "N/A")
    context["placeholders"]["doc.notes"] = doc_ctx.get("notes", "")
    context["placeholders"]["doc.currency_symbol"] = doc_ctx.get("currency_symbol", "€")

    # Seller details
    context["placeholders"]["seller.company_name"] = seller_ctx.get("company_name", "N/A")
    context["placeholders"]["seller.address_line1"] = seller_ctx.get("address_line1", "N/A")
    context["placeholders"]["seller.city_zip_country"] = seller_ctx.get("city_zip_country", "N/A")
    context["placeholders"]["seller.phone"] = seller_ctx.get("phone", "N/A")
    context["placeholders"]["seller.email"] = seller_ctx.get("email", "N/A")
    context["placeholders"]["seller.website"] = seller_ctx.get("website", "N/A")
    context["placeholders"]["seller.vat_id"] = seller_ctx.get("vat_id", "N/A")
    context["placeholders"]["seller.logo_path"] = seller_ctx.get("logo_path")
    context["placeholders"]["seller.bank_name"] = seller_ctx.get("bank_name", "N/A")
    context["placeholders"]["seller.bank_account_holder_name"] = seller_ctx.get("bank_account_holder_name", "N/A")
    context["placeholders"]["seller.bank_iban"] = seller_ctx.get("bank_iban", "N/A")
    context["placeholders"]["seller.bank_swift_bic"] = seller_ctx.get("bank_swift_bic", "N/A")

    # Client details
    context["placeholders"]["client.company_name"] = client_ctx.get("company_name", "N/A")
    context["placeholders"]["client.representative_name"] = client_ctx.get("representative_name", "N/A")
    context["placeholders"]["client.address_line1"] = client_ctx.get("address_line1", "N/A")
    context["placeholders"]["client.city_zip_country"] = client_ctx.get("city_zip_country", "N/A")
    context["placeholders"]["client.vat_id"] = client_ctx.get("vat_id", "N/A")

    # Project details
    context["placeholders"]["project.name"] = project_ctx.get("name", "N/A")

    # Totals and Tax
    context["placeholders"]["doc.subtotal_amount_formatted"] = doc_ctx.get("subtotal_amount_formatted", "N/A")
    context["placeholders"]["doc.discount_rate_percentage"] = str(doc_ctx.get("discount_rate_percentage", "0.0"))
    context["placeholders"]["doc.discount_amount_raw"] = doc_ctx.get("discount_amount_raw", 0.0) # For conditional display
    context["placeholders"]["doc.discount_amount_formatted"] = doc_ctx.get("discount_amount_formatted", "N/A")
    context["placeholders"]["doc.tax_label"] = doc_ctx.get("tax_label", "VAT")
    context["placeholders"]["doc.tax_rate_percentage"] = str(doc_ctx.get("tax_rate_percentage", "0.0"))
    context["placeholders"]["doc.tax_amount_formatted"] = doc_ctx.get("tax_amount_formatted", "N/A")
    context["placeholders"]["doc.grand_total_amount_formatted"] = doc_ctx.get("grand_total_amount_formatted", "N/A")
    context["placeholders"]["doc.grand_total_amount_words"] = doc_ctx.get("grand_total_amount_words", "N/A")


    # Update main context sections for direct access if templates use e.g. {{doc.invoice_number}}
    context["doc"].update(doc_ctx)
    context["seller"].update(seller_ctx)
    context["client"].update(client_ctx)
    context["project"].update(project_ctx)

    # It's useful to return the full context dict which has nested structure
    # and also the flat placeholders dict if needed by a specific template engine.
    # For Handlebars/Jinja2, the nested context is usually preferred.
    # The template examples given use dot notation (e.g. {{doc.invoice_number}}),
    # so the nested context structure is what they'd use.
    # The `context["placeholders"]` can be removed if not used by the template engine.

    return context
