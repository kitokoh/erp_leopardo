import os
import json
import datetime
import logging
from decimal import Decimal, ROUND_HALF_UP

# Assuming db.cruds and other necessary modules exist in the parent directory or are accessible.
# Adjust these imports based on the actual project structure.
from db.cruds import (
    get_company_by_id,
    get_client_by_id,
    # Make sure referents_crud is imported if not available through the main __init__
    referents_crud, # Added for referents report
    get_product_by_id,
    get_products_for_client_or_project,
    get_contacts_for_client,
    get_country_by_id,
    get_city_by_id,
    get_project_by_id,
    get_client_document_notes,
    get_equivalent_products,
    get_media_links_for_product,
    get_personnel_for_company,
    application_settings_crud, # Added for default footer notes
)
from db.connection import get_db_connection # Changed from db.utils
# Assuming these config variables are correctly defined in your project.
# from db_config import APP_ROOT_DIR_CONTEXT, LOGO_SUBDIR_CONTEXT # Removed
# from config import MEDIA_FILES_BASE_PATH # Removed

# APP_ROOT_DIR_CONTEXT, LOGO_SUBDIR_CONTEXT, MEDIA_FILES_BASE_PATH will now be passed or derived from app_root_dir or config object

# Import config for MEDIA_FILES_BASE_PATH, assuming app_root_dir is for logos primarily
# from app_setup import CONFIG as AppGlobalConfig # Removed
_module_config = None

def set_document_generator_config(config):
    """Sets the configuration for the document_generator module."""
    global _module_config
    if _module_config is not None:
        logger.warning("document_generator.context_builder.set_document_generator_config called multiple times.")
    _module_config = config
    logger.info("document_generator.context_builder: Configuration has been set.")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

    # Ensure all context population logic is within the main try-except-finally block.
def format_currency(amount, currency_symbol='€', decimal_places=2, language_code='en'):
    """
    Formats a numerical amount as a currency string, with basic localization.
    Example: 
        format_currency(Decimal('1234.567'), currency_symbol='$', language_code='en') == '$1,234.57'
        format_currency(Decimal('1234.567'), currency_symbol='€', language_code='fr') == '1 234,57 €'
    """
    if amount is None:
        # Fallback for None amount, trying to respect symbol placement for FR at least
        if language_code == 'fr':
            return f"0,00 {currency_symbol}"
        return f"{currency_symbol}0.00"

    if not isinstance(amount, Decimal):
        try:
            amount = Decimal(str(amount))
        except Exception:
            if language_code == 'fr':
                return f"0,00 {currency_symbol}"
            return f"{currency_symbol}0.00"

    quantizer = Decimal('0.1') ** decimal_places
    rounded_amount = amount.quantize(quantizer, ROUND_HALF_UP)
    
    abs_rounded_amount = abs(rounded_amount) # For formatting, sign handled later
    
    parts = str(abs_rounded_amount).split('.')
    integer_part_str = parts[0]
    decimal_part_str = parts[1] if len(parts) > 1 else '0' * decimal_places
    decimal_part_str = decimal_part_str.ljust(decimal_places, '0') # Ensure correct length

    if language_code == 'fr':
        thousands_sep = " "
        decimal_sep = ","
    else: # Default to EN-like
        thousands_sep = ","
        decimal_sep = "."

    # Add thousands separators
    reversed_integer_part = list(integer_part_str[::-1])
    formatted_integer_list = []
    for i, digit in enumerate(reversed_integer_part):
        if i > 0 and i % 3 == 0:
            formatted_integer_list.append(thousands_sep)
        formatted_integer_list.append(digit)
    formatted_integer_part = "".join(formatted_integer_list[::-1])
    
    sign = "-" if rounded_amount < 0 else ""

    if language_code == 'fr':
        return f"{sign}{formatted_integer_part}{decimal_sep}{decimal_part_str} {currency_symbol}"
    else: # Default (EN-like)
        return f"{sign}{currency_symbol}{formatted_integer_part}{decimal_sep}{decimal_part_str}"


def get_document_context(
    client_id: int,
    company_id: int,
    language_code: str,
    project_id: int = None,
    order_id: str = None, # Added order_id parameter
    document_type: str = None, # e.g., 'proforma_invoice', 'technical_sheet'
    additional_data: dict = None,
    db_conn=None, # This parameter is now effectively ignored by internal calls if they are all decorated
    app_root_dir: str = None
) -> dict:
    """
    Fetches and structures data for document generation.
    Connections to DB for CRUD operations are managed by @_manage_conn decorator on CRUD functions.
    """
    logger.info(f"get_document_context called with app_root_dir: {app_root_dir}, client_id: {client_id}, order_id: {order_id}, lang: {language_code}")
    if additional_data is None:
        additional_data = {}

    context = {
        "doc": {},
        "client": {},
        "seller": {},
        "project": {},
        "products": [],
        "lang": {},
        "placeholders": {},
        "additional": additional_data,
    }

    # conn = db_conn if db_conn else get_db_connection() # Connection now managed by @_manage_conn on each CRUD call

    try:
        # Determine translations base path (assuming it's relative to this file's location or project root)
        # For robustness, it's better if app_root_dir is used to construct this path.
        # If context_builder.py is in document_generator/, and translations/ is at project root:
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root_for_translations = os.path.dirname(current_script_dir) # Moves up one level from document_generator/

        # If app_root_dir is provided and reliable for finding 'translations' folder:
        if app_root_dir and os.path.isdir(os.path.join(app_root_dir, "translations", "doc_labels")):
            translations_base_path = os.path.join(app_root_dir, "translations", "doc_labels")
        else: # Fallback to path relative to this script
            translations_base_path = os.path.join(project_root_for_translations, "translations", "doc_labels")

        logger.info(f"Using translations base path: {translations_base_path}")

        # 1. Document Info (doc section)
        context["doc"]["current_date"] = datetime.date.today().strftime("%Y-%m-%d")
        context["doc"]["current_year"] = datetime.date.today().year
        context["doc"]["currency_symbol"] = additional_data.get("currency_symbol", "€")
        # Ensure rates are Decimal for precision
        context["doc"]["vat_rate"] = Decimal(str(additional_data.get("vat_rate", "0.20")))
        context["doc"]["discount_rate"] = Decimal(str(additional_data.get("discount_rate", "0.00")))


        # 2. Language Info (lang section) & Localized Labels
        context["lang"]["code"] = language_code
        context["lang"]["text_direction"] = "rtl" if language_code == "ar" else "ltr"

        # Load labels from JSON files
        default_lang_for_labels = "en" # Fallback language
        labels_path = os.path.join(translations_base_path, f"{language_code}.json")

        loaded_labels = {}
        if os.path.exists(labels_path):
            try:
                with open(labels_path, 'r', encoding='utf-8') as f:
                    loaded_labels = json.load(f)
                logger.info(f"Successfully loaded labels for language: {language_code} from {labels_path}")
            except Exception as e:
                logger.error(f"Error loading labels for language {language_code} from {labels_path}: {e}")
        else:
            logger.warning(f"Labels file not found for language: {language_code} at {labels_path}. Attempting fallback.")

        # Fallback labels if specific language file not found or loading failed
        if not loaded_labels and language_code != default_lang_for_labels:
            fallback_labels_path = os.path.join(translations_base_path, f"{default_lang_for_labels}.json")
            if os.path.exists(fallback_labels_path):
                try:
                    with open(fallback_labels_path, 'r', encoding='utf-8') as f:
                        loaded_labels = json.load(f)
                    logger.info(f"Using fallback labels from: {default_lang_for_labels}.json")
                except Exception as e:
                    logger.error(f"Error loading fallback labels for language {default_lang_for_labels}: {e}")
            else:
                logger.error(f"Fallback labels file '{default_lang_for_labels}.json' also not found at {fallback_labels_path}.")

        context["labels"] = loaded_labels

        context["doc"]["current_date_iso"] = context["doc"]["current_date"]
        try:
            current_date_obj = datetime.datetime.strptime(context["doc"]["current_date"], "%Y-%m-%d").date()
            if language_code == "fr":
                context["doc"]["current_date_formatted"] = current_date_obj.strftime("%d/%m/%Y")
            elif language_code == "en":
                context["doc"]["current_date_formatted"] = current_date_obj.strftime("%m/%d/%Y")
            else:
                context["doc"]["current_date_formatted"] = current_date_obj.strftime("%Y-%m-%d")
        except ValueError:
            logger.warning(f"Could not parse current_date '{context['doc']['current_date']}' for formatting.")
            context["doc"]["current_date_formatted"] = context["doc"]["current_date"]

        doc_identifier = additional_data.get('document_id', 
                                            additional_data.get('invoice_number', 
                                                                additional_data.get('proforma_id')))
        if not doc_identifier and document_type and 'proforma' in document_type.lower():
            doc_identifier = f"PF-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        context["doc"]["proforma_id"] = doc_identifier if doc_identifier else "N/A"
        context["doc"]["document_reference"] = doc_identifier if doc_identifier else "N/A"

        # 3. Seller Information (seller section)
        seller_company = get_company_by_id(company_id) # Removed conn
        if seller_company:
            context["seller"]["name"] = seller_company.get("name")
            context["seller"]["address_line1"] = seller_company.get("address_line1")
            context["seller"]["address_line2"] = seller_company.get("address_line2")
            context["seller"]["city"] = seller_company.get("city_name")
            context["seller"]["postal_code"] = seller_company.get("postal_code")
            context["seller"]["country"] = seller_company.get("country_name")
            context["seller"]["phone"] = seller_company.get("phone")
            context["seller"]["email"] = seller_company.get("email")
            context["seller"]["website"] = seller_company.get("website")
            context["seller"]["vat_id"] = seller_company.get("vat_id")

            logo_relative_path = seller_company.get("logo_path")
            logo_filename = seller_company.get("logo_path")
            context["seller"]["logo_url"] = "" # Default to empty string

            if _module_config is None:
                logger.error("Document generator configuration not set. Call set_document_generator_config first.")
                # Potentially raise an error or handle gracefully

            if logo_filename and app_root_dir and _module_config:
                logo_subdir = _module_config.get('company_logo_dir', 'company_logos')
                logo_abs_path = os.path.join(app_root_dir, logo_subdir, logo_filename)
                logger.info(f"Attempting to resolve seller logo. Subdir: '{logo_subdir}', Filename: '{logo_filename}', Absolute path: '{logo_abs_path}'")
                if os.path.exists(logo_abs_path):
                    context["seller"]["logo_url"] = f"file:///{logo_abs_path.replace(os.sep, '/')}"
                else:
                    logger.warning(f"Seller logo file '{logo_filename}' not found at expected path: {logo_abs_path}. 'logo_url' will be empty.")
            elif logo_filename and not app_root_dir:
                logger.warning(f"app_root_dir not provided for context_builder, cannot resolve seller logo path for '{logo_filename}'. 'logo_url' will be empty.")
            elif not logo_filename:
                logger.info("No logo_filename provided for seller company. 'logo_url' will be empty.")

            logger.info(f"Final context['seller']['logo_url']: '{context['seller']['logo_url']}'")

            payment_info_str = seller_company.get("payment_info", "{}")
            other_info_str = seller_company.get("other_info", "{}")
            try:
                payment_info = json.loads(payment_info_str) if payment_info_str else {}
            except json.JSONDecodeError:
                payment_info = {}
                logger.warning(f"Could not parse payment_info JSON for company {company_id}: {payment_info_str[:100]}")
            try:
                other_info = json.loads(other_info_str) if other_info_str else {}
            except json.JSONDecodeError:
                other_info = {}
                logger.warning(f"Could not parse other_info JSON for company {company_id}: {other_info_str[:100]}")

            context["seller"]["bank_name"] = payment_info.get("bank_name")
            context["seller"]["bank_account_holder_name"] = payment_info.get("bank_account_holder_name")
            context["seller"]["bank_iban"] = payment_info.get("iban")
            context["seller"]["bank_swift_bic"] = payment_info.get("swift_bic")
            context["seller"]["bank_address"] = payment_info.get("bank_address")
            
            context["seller"]["vat_id"] = other_info.get("vat_id", seller_company.get("vat_id"))
            context["seller"]["registration_number"] = other_info.get("registration_number")
            
            context["seller"]["address_full"] = seller_company.get("address")
            seller_city = other_info.get("city", payment_info.get("city", ""))
            seller_postal = other_info.get("postal_code", payment_info.get("postal_code", ""))
            seller_country_name = other_info.get("country", payment_info.get("country", ""))

            _s_parts = [seller_city, seller_postal, context["seller"]["country"]]
            context["seller"]["city_zip_country"] = ", ".join(filter(None, [str(p).strip() for p in _s_parts if p])) or ""

            personnel_list = get_personnel_for_company(company_id) # Removed conn
            if personnel_list:
                representative = next((p for p in personnel_list if p.get("is_representative")), personnel_list[0])
                context["seller"]["representative_name"] = representative.get("full_name")
                context["seller"]["representative_email"] = representative.get("email")
                context["seller"]["representative_phone"] = representative.get("phone")
        else:
            logger.error(f"Seller company with ID {company_id} not found.")

        # 4. Client Information (client section)
        client_data = get_client_by_id(client_id) # Removed conn
        if client_data:
            client_ctx = context["client"]
            client_ctx["id"] = client_data.get("client_id")
            client_ctx["individual_name"] = client_data.get("name") 
            client_ctx["company_name"] = client_data.get("company_name")
            client_ctx["display_name"] = client_data.get("company_name") or client_data.get("name")
            
            client_ctx["address_line1"] = client_data.get("address_line1", client_data.get("default_base_folder_path"))
            client_ctx["address_line2"] = client_data.get("address_line2") 
            client_ctx["postal_code"] = client_data.get("postal_code")

            client_notes_raw = client_data.get('notes', "")
            client_dist_info_raw = client_data.get('distributor_specific_info', "")

            client_notes_json = {}
            client_notes_kv = {}
            if isinstance(client_notes_raw, str):
                try: client_notes_json = json.loads(client_notes_raw) if client_notes_raw.strip().startswith('{') else {}
                except json.JSONDecodeError: pass
            
            client_dist_info_json = {}
            if isinstance(client_dist_info_raw, str):
                try: client_dist_info_json = json.loads(client_dist_info_raw) if client_dist_info_raw.strip().startswith('{') else {}
                except json.JSONDecodeError: pass

            client_ctx["vat_id"] = client_dist_info_json.get("vat_id", client_notes_json.get("vat_id", additional_data.get("client_vat_id")))
            client_ctx["registration_number"] = client_dist_info_json.get("registration_number", client_notes_json.get("registration_number", additional_data.get("client_registration_number")))

            client_city_id = client_data.get("city_id")
            if client_city_id:
                city = get_city_by_id(client_city_id) # Removed conn
                client_ctx["city"] = city.get("name") if city else None

            client_country_id = client_data.get("country_id")
            if client_country_id:
                country = get_country_by_id(client_country_id) # Removed conn
                client_ctx["country"] = country.get("name") if country else None
            
            _c_parts = [client_ctx.get("city"), client_ctx.get("postal_code"), client_ctx.get("country")]
            client_ctx["city_zip_country"] = ", ".join(filter(None, [str(p).strip() for p in _c_parts if p])) or ""
            
            _c_addr_parts = [client_ctx.get("address_line1"), client_ctx.get("address_line2"), client_ctx.get("city_zip_country")]
            client_ctx["address_full"] = ", ".join(filter(None, [str(p).strip() for p in _c_addr_parts if p])) or ""

            primary_contact = None
            contacts = get_contacts_for_client(client_id) # Removed conn
            if contacts:
                primary_contact = next((c for c in contacts if c.get("is_primary")), contacts[0] if contacts else None)
                if primary_contact:
                    client_ctx["contact_name"] = primary_contact.get("name")
                    client_ctx["contact_email"] = primary_contact.get("email")
                    client_ctx["contact_phone"] = primary_contact.get("phone")
        else:
            logger.error(f"Client with ID {client_id} not found.")

        # 5. Project Information (project section)
        if project_id:
            project_data = get_project_by_id(project_id) # Removed conn
            if project_data:
                context["project"]["id"] = project_data.get("id")
                context["project"]["name"] = project_data.get("name")
                context["project"]["identifier"] = project_data.get("identifier")
            else:
                logger.warning(f"Project with ID {project_id} not found.")
        elif "project_name" in additional_data or "project_identifier" in additional_data:
            context["project"]["name"] = additional_data.get("project_name")
            context["project"]["identifier"] = additional_data.get("project_identifier")
        elif client_data and client_data.get("default_project_identifier"):
             context["project"]["identifier"] = client_data.get("default_project_identifier")
             context["project"]["name"] = client_data.get("default_project_name")

        # 6. Order and Product/Item Information
        # This section will now primarily focus on order_id if provided.
        # The old logic for `get_products_for_client_or_project` might be a fallback
        # or used for documents not directly tied to a specific order.

        raw_items_data = []
        if order_id and commandes_crud:
            order_details = commandes_crud.get_commande_by_id(order_id)
            if order_details:
                context["order"] = {
                    "id": order_details.get("commande_id"),
                    "reference": order_details.get("commande_reference"),
                    "date": order_details.get("commande_date"),
                    "date_formatted": format_date(order_details.get("commande_date"), language_code),
                    "description": order_details.get("description_commande"),
                    "notes": order_details.get("notes"),
                    "total_ht_raw": Decimal(str(order_details.get("total_ht", "0.0"))),
                    "total_ttc_raw": Decimal(str(order_details.get("total_ttc", "0.0"))),
                    "currency": order_details.get("currency", "EUR"),
                    "project_id": order_details.get("project_id"),
                    "project_name": order_details.get("project_name"), # From JOIN in get_commande_by_id
                    "status_name": order_details.get("status_commande_name"),
                    # Add more fields from order_details as needed by templates
                }
                # Override doc currency with order currency if available
                context["doc"]["currency_symbol"] = context["order"]["currency"]

                # Use order's project_id if not already set from arguments
                if not project_id and context["order"].get("project_id"):
                    project_id = context["order"]["project_id"] # Update project_id for project context loading

                raw_items_data = commandes_crud.get_items_for_commande(order_id)
                if raw_items_data is None: raw_items_data = []
                logger.info(f"Loaded {len(raw_items_data)} items for order_id: {order_id}")
            else:
                logger.warning(f"Order with ID {order_id} not found.")

        # If no order_id, or if items are passed via additional_data (e.g. for non-order docs)
        # This part needs careful consideration on how 'products' vs 'items' are handled.
        # For now, if order_id, 'items' will be populated. If not, old 'products' logic could run.
        # Let's prioritize `items` from order.

        if not raw_items_data and not order_id: # Fallback to old product fetching if no order
            logger.info("No order_id provided, attempting to fetch products via get_products_for_client_or_project.")
            linked_products_data = get_products_for_client_or_project(client_id=client_id, project_id=project_id)
            linked_products_data = linked_products_data if linked_products_data else []
            # This `linked_products_data` needs to be transformed into a structure similar to `raw_items_data`
            # if we want a unified processing loop. For now, this path will lead to empty context["items"].
            # This section requires further refinement if non-order documents need product listings.
            # For this iteration, we focus on order-based documents.
            logger.warning("Non-order based product listing in context_builder needs review/implementation based on use-case.")


        processed_items_for_context = []
        calculated_subtotal_ht = Decimal("0.0")

        for item_data in raw_items_data: # Iterating over CommandeItems
            global_product_id = item_data.get("product_id")
            item_specific_lang_code = item_data.get("product_language_code")
            target_lang_for_this_item = item_specific_lang_code if item_specific_lang_code else language_code

            display_name = item_data.get("description_item") # Default to item's own description
            display_description = "" # CommandeItem might not have a separate long description field
            
            # Try to get product details in the target language for this item
            # This part needs robust multilingual product fetching logic.
            # For now, using placeholder logic:
            product_details_in_target_lang = None
            if global_product_id:
                # Ideal: products_crud.get_product_translation(global_product_id, target_lang_for_this_item, fallback_lang='en')
                # Simplified for now:
                global_product_base_info = get_product_by_id(global_product_id) # Gets default lang
                if global_product_base_info:
                    if global_product_base_info.get("language_code") == target_lang_for_this_item:
                        product_details_in_target_lang = global_product_base_info
                    else: # Try equivalents (simplified)
                        equivalents = get_equivalent_products(global_product_id)
                        if equivalents:
                            for eq in equivalents:
                                if eq.get("language_code") == target_lang_for_this_item:
                                    product_details_in_target_lang = eq
                                    break
                    if not product_details_in_target_lang: # Fallback to base if no translation found
                         product_details_in_target_lang = global_product_base_info
                         logger.warning(f"No translation for product {global_product_id} to lang {target_lang_for_this_item}. Using base: {global_product_base_info.get('name')}")

                if product_details_in_target_lang:
                    # Override item's description with product's name if item's description is empty or too generic
                    if not display_name or display_name == product_details_in_target_lang.get("product_code"):
                        display_name = product_details_in_target_lang.get("product_name", item_data.get("description_item"))
                    display_description = product_details_in_target_lang.get("description", "")


            quantity = Decimal(str(item_data.get("quantity", 1)))
            unit_price_ht = Decimal(str(item_data.get("unit_price_ht", "0.00")))
            total_item_ht = Decimal(str(item_data.get("total_item_ht", "0.00"))) # Use pre-calculated from DB
            calculated_subtotal_ht += total_item_ht

            # Media links (similar to previous product logic)
            media_links_processed = []
            if global_product_id and app_root_dir and _module_config:
                media_links_raw = get_media_links_for_product(global_product_id)
                if media_links_raw:
                    for media_link in media_links_raw:
                        file_path = media_link.get("file_path")
                        if file_path:
                            media_root = _module_config.get('media_files_path', os.path.join(app_root_dir, 'media_files'))
                            abs_media_path = os.path.join(media_root, file_path.lstrip(os.sep))
                            if os.path.exists(abs_media_path):
                                 media_links_processed.append({
                                     "url": f"file:///{abs_media_path.replace(os.sep, '/')}",
                                     "type": media_link.get("type", "image"), "description": media_link.get("description")
                                 })
            
            processed_items_for_context.append({
                "product_code": item_data.get("product_code", global_product_id), # From JOIN in get_items_for_commande
                "name": display_name,
                "description": display_description,
                "quantity": quantity,
                "unit_price_formatted": format_currency(unit_price_ht, context["doc"]["currency_symbol"], language_code=language_code),
                "total_price_formatted": format_currency(total_item_ht, context["doc"]["currency_symbol"], language_code=language_code),
                "unit_price_decimal": unit_price_ht,
                "total_price_decimal": total_item_ht,
                "vat_rate_percentage": Decimal(str(item_data.get("vat_rate", "0.0"))) * Decimal("100"),
                "total_ttc_formatted": format_currency(Decimal(str(item_data.get("total_item_ttc", "0.0"))), context["doc"]["currency_symbol"], language_code=language_code),
                "weight": item_data.get("weight"), # From CommandeItems
                "dimensions_text": item_data.get("dimensions_text"), # From CommandeItems
                "item_language_code": item_data.get("product_language_code"), # From CommandeItems
                "media_links": media_links_processed,
            })
        
        context["items"] = processed_items_for_context # Use "items" for generic line items

        # Use calculated subtotal from items if order details are not authoritative or need override
        subtotal_ht = calculated_subtotal_ht
        if order_id and context["order"].get("total_ht_raw") is not None: # Prefer order's total if available
            subtotal_ht = context["order"]["total_ht_raw"]

        # Recalculate totals based on context["items"] or order totals
        # Assuming discount_rate and vat_rate are for the whole order
        discount_amount = subtotal_ht * context["doc"]["discount_rate"]
        subtotal_after_discount = subtotal_ht - discount_amount
        vat_amount = subtotal_after_discount * context["doc"]["vat_rate"]
        grand_total = subtotal_after_discount + vat_amount

        context["doc"]["subtotal_amount_raw"] = subtotal
        context["doc"]["discount_amount_raw"] = discount_amount
        context["doc"]["vat_amount_raw"] = vat_amount
        context["doc"]["grand_total_amount_raw"] = grand_total

        cs = context["doc"]["currency_symbol"]
        context["doc"]["subtotal_amount"] = format_currency(subtotal, cs)
        context["doc"]["discount_amount"] = format_currency(discount_amount, cs)
        context["doc"]["vat_amount"] = format_currency(vat_amount, cs)
        context["doc"]["grand_total_amount"] = format_currency(grand_total, cs)

        doc_type_for_notes = additional_data.get("current_document_type_for_notes", document_type) # Use the key passed from create_document_dialog
        if doc_type_for_notes and client_id and language_code:
            # Explicitly fetch only active notes. conn is handled by @_manage_conn in get_client_document_notes
            client_notes_records = get_client_document_notes(client_id, doc_type_for_notes, language_code, is_active=True)
            # Templates likely expect a list of note strings, not dicts.
            context["doc"]["client_specific_notes"] = [note['note_content'] for note in client_notes_records] if client_notes_records else []
            if client_notes_records:
                logger.info(f"Fetched {len(client_notes_records)} active client-specific notes for doc type '{doc_type_for_notes}', lang '{language_code}'.")
            else:
                logger.info(f"No active client-specific notes found for doc type '{doc_type_for_notes}', lang '{language_code}'.")
        else:
            context["doc"]["client_specific_notes"] = []
            logger.info(f"Skipping client-specific notes fetch due to missing: doc_type_for_notes='{doc_type_for_notes}', client_id='{client_id}', or language_code='{language_code}'.")

        context["placeholders"]["BUYER_COMPANY_NAME"] = context["client"].get("company_name", context["client"].get("name"))
        context["placeholders"]["BUYER_CONTACT_NAME"] = context["client"].get("contact_name")
        context["placeholders"]["BUYER_ADDRESS_LINE1"] = context["client"].get("address_line1")
        context["placeholders"]["BUYER_CITY"] = context["client"].get("city")
        context["placeholders"]["BUYER_COUNTRY"] = context["client"].get("country")
        context["placeholders"]["SELLER_COMPANY_NAME"] = context["seller"].get("name")
        context["placeholders"]["SELLER_ADDRESS_LINE1"] = context["seller"].get("address_line1")
        context["placeholders"]["SELLER_CITY"] = context["seller"].get("city")
        context["placeholders"]["SELLER_COUNTRY"] = context["seller"].get("country")
        context["placeholders"]["SELLER_REPRESENTATIVE_NAME"] = context["seller"].get("representative_name")
        context["placeholders"]["SELLER_LOGO"] = context["seller"].get("logo_path")
        context["placeholders"]["PROJECT_NAME"] = context["project"].get("name")
        context["placeholders"]["PROJECT_IDENTIFIER"] = context["project"].get("identifier")
        context["placeholders"]["CURRENT_DATE"] = context["doc"]["current_date"]
        context["placeholders"]["GRAND_TOTAL_AMOUNT"] = context["doc"]["grand_total_amount"]
        context["placeholders"]["SUBTOTAL_AMOUNT"] = context["doc"]["subtotal_amount"]
        context["placeholders"]["CURRENCY_SYMBOL"] = context["doc"]["currency_symbol"]


        # <<< DEBUT SECTION POUR REFERENTS REPORT >>>
        if document_type == 'referents_report':
            logger.info(f"Building context for referents_report for client_id: {client_id}")

            target_client_info = {}
            # client_data_raw already contains info from get_client_by_id if client_id was valid
            client_data_raw_for_target = get_client_by_id(client_id) # Ensure fresh full data for IDs

            if client_data_raw_for_target:
                target_client_info['full_name'] = client_data_raw_for_target.get("company_name") or client_data_raw_for_target.get("client_name")
                target_client_info['company_name'] = client_data_raw_for_target.get("company_name")

                target_client_country_id = client_data_raw_for_target.get("country_id")
                target_client_city_id = client_data_raw_for_target.get("city_id")
                # Assuming region_id might be directly on client or derived if needed later
                # target_client_region_id = client_data_raw_for_target.get("region_id")

                target_client_info['country_id'] = target_client_country_id
                target_client_info['city_id'] = target_client_city_id
                # target_client_info['region_id'] = target_client_region_id

                # Get city and country names using existing CRUDs if IDs are present
                if target_client_city_id:
                    city_obj = get_city_by_id(target_client_city_id)
                    target_client_info['city'] = city_obj.get("name") if city_obj else None
                if target_client_country_id:
                    country_obj = get_country_by_id(target_client_country_id)
                    target_client_info['country'] = country_obj.get("name") if country_obj else None
            else: # Fallback if client_data_raw_for_target is None
                target_client_info['full_name'] = context.get("client", {}).get("display_name")
                target_client_info['company_name'] = context.get("client", {}).get("company_name")
                target_client_info['city'] = context.get("client", {}).get("city")
                target_client_info['country'] = context.get("client", {}).get("country")
                target_client_country_id = context.get("client", {}).get("country_id") # Might be missing if client not found initially
                target_client_city_id = context.get("client", {}).get("city_id")


            context['target_client'] = target_client_info

            # Récupérer les référents locaux
            local_referents_list = []
            if target_client_country_id:
                local_filters = {'country_id': target_client_country_id}
                # Optionnel: affiner par ville si disponible
                # if target_client_city_id: # This might be too restrictive, country level is often enough for "local"
                #     local_filters['city_id'] = target_client_city_id

                all_local_raw = referents_crud.get_all_referents(filters=local_filters, include_inactive=False)
                for ref_raw in all_local_raw:
                    if ref_raw.get('client_id') == client_id: # Exclude the target client itself
                        continue
                    local_referents_list.append({
                        'full_name': ref_raw.get('client_name'), # From joined Clients table
                        'company_name': ref_raw.get('company_name'), # From joined Clients table
                        'city': ref_raw.get('city_name'), # From joined Cities table
                        'region_name': ref_raw.get('region_name'), # From joined Regions table
                        'country': ref_raw.get('country_name') # From joined Countries table
                    })
            context['local_referents'] = local_referents_list
            logger.info(f"Found {len(local_referents_list)} local referents for country_id {target_client_country_id}.")

            # Récupérer les référents globaux (tous les référents actifs)
            global_referents_list = []
            all_global_raw = referents_crud.get_all_referents(include_inactive=False)
            for ref_raw in all_global_raw:
                if ref_raw.get('client_id') == client_id: # Exclude the target client itself
                    continue
                global_referents_list.append({
                    'full_name': ref_raw.get('client_name'),
                    'company_name': ref_raw.get('company_name'),
                    'city': ref_raw.get('city_name'),
                    'region_name': ref_raw.get('region_name'),
                    'country': ref_raw.get('country_name')
                })
            context['global_referents'] = global_referents_list
            logger.info(f"Found {len(global_referents_list)} global referents.")

            # Assurer la présence des autres champs attendus par le template
            # These are already populated earlier in the function for seller and doc sections.
            context['company_logo_path'] = context.get('seller', {}).get('logo_url')
            context['generation_date'] = context.get('doc', {}).get('current_date_formatted')
            context['company_details'] = context.get('seller')
        # <<< FIN SECTION POUR REFERENTS REPORT >>>

        # 7. Footer Notes
        custom_footer_notes = additional_data.get('footer_notes')
        final_footer_notes = ""
        if custom_footer_notes and custom_footer_notes.strip():
            final_footer_notes = custom_footer_notes
            logger.info(f"Using custom footer notes for document: {custom_footer_notes[:50]}...")
        else:
            default_footer_key = f"default_document_footer_notes_{language_code}"
            # The get_setting CRUD is already decorated with _manage_conn, so it handles its own connection.
            default_notes = application_settings_crud.get_setting(default_footer_key, default="")
            if default_notes and default_notes.strip():
                final_footer_notes = default_notes
                logger.info(f"Using default footer notes for language '{language_code}': {default_notes[:50]}...")
            else:
                logger.info(f"No custom or default footer notes found for language '{language_code}'. Footer notes will be empty.")

        context["doc"]["footer_notes"] = final_footer_notes
        context["placeholders"]["FOOTER_NOTES"] = final_footer_notes

    except Exception as e:
        logger.error(f"Error building document context: {e}", exc_info=True)
    # finally: # The conn variable is no longer managed at this level
        # if db_conn is None and conn:
            # conn.close()

    return context

if __name__ == '__main__':
    # This is a placeholder for testing the function.
    # You would need a running database and actual data to test this properly.
    logger.info("Starting context builder test run...")

    # Example Usage (requires database setup and mock CRUD functions or a live DB)
    # Create a dummy connection or mock get_db_connection and CRUDs for local testing.

    # Mock db_connection and cruds for standalone testing if needed:
    class MockDbConnection:
        def cursor(self): return self
        def execute(self, query, params=None): return self
        def fetchone(self): return None
        def fetchall(self): return []
        def close(self): pass

    def mock_get_db_connection():
        return MockDbConnection()

    # Replace actual get_db_connection with mock for this test
    # global get_db_connection # If you need to reassign global, not usually recommended
    # original_get_db_conn = get_db_connection
    # get_db_connection = mock_get_db_connection

    # Mock CRUD functions (replace with more detailed mocks as needed)
    # For example:
    # def mock_get_company_by_id(conn, company_id):
    #     return {"id": company_id, "name": "Test Seller Inc.", "logo_path": "dummy_logo.png"}
    # global get_company_by_id
    # get_company_by_id = mock_get_company_by_id

    try:
        # Note: Without proper mocks for all DB calls, this will likely log errors.
        test_context = get_document_context(
            client_id=1,
            company_id=1,
            language_code='en',
            project_id=1,
            additional_data={
                "currency_symbol": "$",
                "vat_rate": "0.10",
                # "lite_selected_products": [101, 102],
                # "products_quantities": {101: 2, 102: 5}
            },
            app_root_dir=os.getcwd() # Example for testing, provide a sensible path
            # db_conn=mock_get_db_connection() # Pass mock connection
        )
        logger.info(f"Generated context (test run, likely with errors if DB not mocked):")
        # Using json.dumps for pretty printing, handling Decimal by converting to str
        # logger.info(json.dumps(test_context, indent=2, default=str))

    except Exception as e:
        logger.error(f"Error during test run: {e}", exc_info=True)
    finally:
        # Restore original functions if they were globally mocked
        # get_db_connection = original_get_db_conn
        logger.info("Context builder test run finished.")

    # To run this file directly for testing:
    # Ensure that the paths for db.cruds, db.utils, db_config, config are correct
    # or provide mock implementations for them.
    # Example:
    # PYTHONPATH=. python document_generator/context_builder.py (if run from project root)
