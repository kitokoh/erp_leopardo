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
    get_product_by_id,
    get_products_for_client_or_project,
    get_contacts_for_client,
    get_country_by_id,
    get_city_by_id,
    get_project_by_id,
    get_client_document_notes,
    get_product_equivalencies_for_product, # Placeholder, might need to be products_crud.get_product_equivalents
    get_media_links_for_product, # Placeholder, might need to be products_crud.get_media_links_for_product
    get_personnel_for_company,
)
from db.utils import get_db_connection
# Assuming these config variables are correctly defined in your project.
# from db_config import APP_ROOT_DIR_CONTEXT, LOGO_SUBDIR_CONTEXT # Removed
# from config import MEDIA_FILES_BASE_PATH # Removed

# APP_ROOT_DIR_CONTEXT, LOGO_SUBDIR_CONTEXT, MEDIA_FILES_BASE_PATH will now be passed or derived from app_root_dir or config object

# Import config for MEDIA_FILES_BASE_PATH, assuming app_root_dir is for logos primarily
from app_setup import CONFIG as AppGlobalConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    document_type: str = None, # e.g., 'proforma_invoice', 'technical_sheet'
    additional_data: dict = None,
    db_conn=None,
    app_root_dir: str = None # Added app_root_dir parameter
) -> dict:
    """
    Fetches and structures data for document generation.

    Args:
        client_id: ID of the client.
        company_id: ID of the seller company.
        language_code: Language code for translations (e.g., 'en', 'es').
        project_id: Optional ID of the project.
        document_type: Optional type of the document being generated.
        additional_data: Optional dictionary for overrides or extra information.
        db_conn: Optional existing database connection.

    Returns:
        A dictionary containing structured data for the document.
    """
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

    conn = db_conn if db_conn else get_db_connection()

    try:
        # 1. Document Info (doc section)
        context["doc"]["current_date"] = datetime.date.today().strftime("%Y-%m-%d")
        context["doc"]["current_year"] = datetime.date.today().year
    context["doc"]["currency_symbol"] = additional_data.get("currency_symbol", "€") # This might need to be lang specific
        context["doc"]["vat_rate"] = Decimal(additional_data.get("vat_rate", "0.20")) # Example VAT
        context["doc"]["discount_rate"] = Decimal(additional_data.get("discount_rate", "0.00"))

    # 2. Language Info (lang section) & Localized Labels
        context["lang"]["code"] = language_code
    context["lang"]["text_direction"] = "rtl" if language_code == "ar" else "ltr"

    _labels = {
        "fr": {
            "proforma_invoice_title": "FACTURE PROFORMA",
            "from_seller": "De :",
            "to_client": "À :",
            "proforma_no": "Facture Proforma N° :",
            "date_label": "Date :", # Changed from "date" to avoid conflict with actual date value
            "project_id_label": "ID Projet :", # Changed from "project_id"
            "payment_terms_label": "Conditions de Paiement :", # Changed
            "delivery_terms_label": "Conditions de Livraison :", # Changed
            "item_ref": "Réf.",
            "item_description": "Description",
            "quantity": "Quantité",
            "unit_price": "Prix Unitaire",
            "total_price": "Prix Total",
            "client_order_ref_label": "Référence Commande Client :", # Changed
            "client_order_date_label": "Date Commande Client :", # Changed
            "sub_total": "Sous-total :",
            "discount": "Remise",
            "vat": "TVA",
            "grand_total": "Montant Total :",
            "bank_details_title": "Nos coordonnées bancaires :",
            "bank_name": "Banque :",
            "account_holder": "Titulaire du compte :",
            "iban": "IBAN :",
            "swift_bic": "SWIFT/BIC :",
            "bank_address": "Adresse de la banque :",
            "proforma_notice": "Ceci est une facture proforma et ne constitue pas une demande de paiement.",
            "thank_you_message": "Merci de votre confiance !",
            "no_products_listed": "Aucun produit listé."
        },
        "en": {
            "proforma_invoice_title": "PROFORMA INVOICE",
            "from_seller": "From:",
            "to_client": "To:",
            "proforma_no": "Proforma Invoice No:",
            "date_label": "Date:",
            "project_id_label": "Project ID:",
            "payment_terms_label": "Payment Terms:",
            "delivery_terms_label": "Delivery Terms:",
            "item_ref": "Ref.",
            "item_description": "Item Description",
            "quantity": "Quantity",
            "unit_price": "Unit Price",
            "total_price": "Total Price",
            "client_order_ref_label": "Client Order Reference:",
            "client_order_date_label": "Client Order Date:",
            "sub_total": "Subtotal:",
            "discount": "Discount",
            "vat": "VAT",
            "grand_total": "Grand Total:",
            "bank_details_title": "Our Bank Details:",
            "bank_name": "Bank:",
            "account_holder": "Account Holder:",
            "iban": "IBAN:",
            "swift_bic": "SWIFT/BIC:",
            "bank_address": "Bank Address:",
            "proforma_notice": "This is a proforma invoice and not a demand for payment.",
            "thank_you_message": "Thank you for your business!"
        },
        "ar": {
            "proforma_invoice_title": "فاتورة أولية",
            "from_seller": "من:",
            "to_client": "إلى:",
            "proforma_no": "رقم الفاتورة الأولية:",
            "date_label": "التاريخ:",
            "project_id_label": "معرف المشروع:",
            "payment_terms_label": "شروط الدفع:",
            "delivery_terms_label": "شروط التسليم:",
            "item_ref": "المرجع",
            "item_description": "وصف السلعة",
            "quantity": "الكمية",
            "unit_price": "سعر الوحدة",
            "total_price": "السعر الإجمالي",
            "client_order_ref_label": "مرجع طلب العميل:",
            "client_order_date_label": "تاريخ طلب العميل:",
            "sub_total": "المجموع الفرعي:",
            "discount": "خصم",
            "vat": "ضريبة القيمة المضافة",
            "grand_total": "المبلغ الإجمالي:",
            "bank_details_title": "تفاصيل حسابنا المصرفي:",
            "bank_name": "البنك:",
            "account_holder": "صاحب الحساب:",
            "iban": "رقم الحساب المصرفي الدولي:",
            "swift_bic": "رمز سويفت/BIC:",
            "bank_address": "عنوان البنك:",
            "proforma_notice": "هذه فاتورة أولية وليست مطالبة بالدفع.",
            "thank_you_message": "شكرا لتعاملكم معنا!"
        }
    }
    context["labels"] = _labels.get(language_code, _labels.get("en", {})) # Default to English labels if lang or specific label not found

    # Date formatting based on locale (simple version)
    # Storing the original YYYY-MM-DD date as well for potential machine use or other formatting needs
    context["doc"]["current_date_iso"] = context["doc"]["current_date"]
    try:
        current_date_obj = datetime.datetime.strptime(context["doc"]["current_date"], "%Y-%m-%d").date()
        if language_code == "fr":
            context["doc"]["current_date_formatted"] = current_date_obj.strftime("%d/%m/%Y")
        elif language_code == "en": # Add other locales as needed
            context["doc"]["current_date_formatted"] = current_date_obj.strftime("%m/%d/%Y")
        # Add other locales or use Babel for more robust i18n date formatting
        else: # Default
            context["doc"]["current_date_formatted"] = current_date_obj.strftime("%Y-%m-%d")
    except ValueError:
        logger.warning(f"Could not parse current_date '{context['doc']['current_date']}' for formatting.")
        context["doc"]["current_date_formatted"] = context["doc"]["current_date"] # Fallback to original string

        # 3. Seller Information (seller section)
        seller_company = get_company_by_id(conn, company_id)
        if seller_company:
            context["seller"]["name"] = seller_company.get("name")
            context["seller"]["address_line1"] = seller_company.get("address_line1")
            context["seller"]["address_line2"] = seller_company.get("address_line2")
            context["seller"]["city"] = seller_company.get("city_name") # Assuming city_name is available
            context["seller"]["postal_code"] = seller_company.get("postal_code")
            context["seller"]["country"] = seller_company.get("country_name") # Assuming country_name is available
            context["seller"]["phone"] = seller_company.get("phone")
            context["seller"]["email"] = seller_company.get("email")
            context["seller"]["website"] = seller_company.get("website")
            context["seller"]["vat_id"] = seller_company.get("vat_id")

            logo_relative_path = seller_company.get("logo_path")
            logo_filename = seller_company.get("logo_path") # Assume this is 'my_logo.png' or similar
            if logo_filename and app_root_dir:
                logo_subdir = AppGlobalConfig.get('company_logo_dir', 'company_logos') # Get from config or default
                logo_abs_path = os.path.join(app_root_dir, logo_subdir, logo_filename)
                if os.path.exists(logo_abs_path):
                    context["seller"]["logo_url"] = f"file:///{logo_abs_path.replace(os.sep, '/')}"
                else:
                    context["seller"]["logo_url"] = None
                    logger.warning(f"Seller logo file '{logo_filename}' not found at expected path: {logo_abs_path}")
            else:
                context["seller"]["logo_url"] = None
                if not app_root_dir and logo_filename :
                    logger.warning(f"app_root_dir not provided, cannot resolve seller logo path for '{logo_filename}'")


            # Parse payment_info and other_info for more seller details
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

            context["seller"]["vat_id"] = other_info.get("vat_id", seller_company.get("vat_id")) # Prioritize other_info
            context["seller"]["registration_number"] = other_info.get("registration_number")

            # Full address from DB, and construct city_zip_country if possible (difficult if address is one string)
            context["seller"]["address_full"] = seller_company.get("address")
            # Attempt to construct city_zip_country if parts are in other_info or payment_info, or parse from address_full
            # This is a simplified approach; robust parsing is complex.
            seller_city = other_info.get("city", payment_info.get("city", ""))
            seller_postal = other_info.get("postal_code", payment_info.get("postal_code", ""))
            seller_country_name = other_info.get("country", payment_info.get("country", "")) # Already have country_name from direct field

            _s_parts = [seller_city, seller_postal, context["seller"]["country"]] # Use already fetched country_name
            context["seller"]["city_zip_country"] = ", ".join(filter(None, [str(p).strip() for p in _s_parts if p])) or ""


            # Seller representative (simplified - picks the first one or based on a flag)
            personnel_list = get_personnel_for_company(conn, company_id)
            if personnel_list:
                # Prioritize personnel marked as 'representative' or similar if such a field exists
                representative = next((p for p in personnel_list if p.get("is_representative")), personnel_list[0])
                context["seller"]["representative_name"] = representative.get("full_name")
                context["seller"]["representative_email"] = representative.get("email")
                context["seller"]["representative_phone"] = representative.get("phone")
        else:
            logger.error(f"Seller company with ID {company_id} not found.")

        # 4. Client Information (client section)
        client_data = get_client_by_id(conn, client_id)
        if client_data:
            client_ctx = context["client"] # shortcut
            client_ctx["id"] = client_data.get("id")
            client_ctx["individual_name"] = client_data.get("name") # Individual client name field from DB
            client_ctx["company_name"] = client_data.get("company_name")
            client_ctx["display_name"] = client_data.get("company_name") or client_data.get("name")

            client_ctx["address_line1"] = client_data.get("address_line1")
            client_ctx["address_line2"] = client_data.get("address_line2")
            client_ctx["postal_code"] = client_data.get("postal_code")
            client_ctx["vat_id"] = client_data.get("vat_id")

            client_city_id = client_data.get("city_id")
            if client_city_id:
                city = get_city_by_id(conn, client_city_id)
                client_ctx["city"] = city.get("name") if city else None

            client_country_id = client_data.get("country_id")
            if client_country_id:
                country = get_country_by_id(conn, client_country_id)
                client_ctx["country"] = country.get("name") if country else None

            _c_parts = [client_ctx.get("city"), client_ctx.get("postal_code"), client_ctx.get("country")]
            client_ctx["city_zip_country"] = ", ".join(filter(None, [str(p).strip() for p in _c_parts if p])) or ""

            _c_addr_parts = [client_ctx.get("address_line1"), client_ctx.get("address_line2"), client_ctx.get("city_zip_country")]
            client_ctx["address_full"] = ", ".join(filter(None, [str(p).strip() for p in _c_addr_parts if p])) or ""

            primary_contact = None
            contacts = get_contacts_for_client(conn, client_id)
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
            project_data = get_project_by_id(conn, project_id)
            if project_data:
                context["project"]["id"] = project_data.get("id")
                context["project"]["name"] = project_data.get("name")
                context["project"]["identifier"] = project_data.get("identifier")
            else:
                logger.warning(f"Project with ID {project_id} not found.")
        elif "project_name" in additional_data or "project_identifier" in additional_data:
            context["project"]["name"] = additional_data.get("project_name")
            context["project"]["identifier"] = additional_data.get("project_identifier")
        elif client_data and client_data.get("default_project_identifier"): # Fallback to client's default project
             context["project"]["identifier"] = client_data.get("default_project_identifier")
             context["project"]["name"] = client_data.get("default_project_name") # if available


        # 6. Product Information (products section)
        product_ids_to_fetch = additional_data.get('lite_selected_products', []) # List of product IDs
        if not product_ids_to_fetch and 'linked_product_ids_for_doc' in additional_data:
             product_ids_to_fetch = additional_data.get('linked_product_ids_for_doc', [])

        products_raw = []
        if product_ids_to_fetch:
            for pid in product_ids_to_fetch:
                prod = get_product_by_id(conn, pid) # Assumes quantity is handled elsewhere or is 1
                if prod:
                    # Check if quantity is provided in additional_data, perhaps per product_id
                    quantity = additional_data.get("products_quantities", {}).get(pid, 1)
                    prod_with_quantity = {**prod, "quantity": quantity}
                    products_raw.append(prod_with_quantity)
        else:
            # Default: fetch all products linked to client or project
            products_raw = get_products_for_client_or_project(conn, client_id=client_id, project_id=project_id)
            # Ensure products_raw have a quantity, default to 1 if not present
            for prod in products_raw:
                if "quantity" not in prod:
                    prod["quantity"] = 1


        total_items_price = Decimal("0.0")
        for prod_data in products_raw:
            product_id = prod_data.get("id")
            if not product_id:
                logger.warning(f"Skipping product with missing ID: {prod_data}")
                continue

            # Base product details are already in prod_data if fetched by get_product_by_id
            # If get_products_for_client_or_project doesn't return full details, fetch them:
            # current_product_details = get_product_by_id(conn, product_id) or {}
            current_product_details = prod_data # Assuming prod_data has all base fields

            # Fetch product equivalents for the given language
            # This simulates products_crud.get_product_equivalents(product_id, language_code)
            # or the logic from _get_batch_products_and_equivalents
            equivalents = get_product_equivalencies_for_product(conn, product_id, language_code)

            translated_name = current_product_details.get("name") # Default to original name
            translated_description = current_product_details.get("description") # Default to original desc

            if equivalents: # Assuming equivalents is a list and we take the first one or best match
                # This logic might need refinement based on how equivalents are structured
                best_equivalent = equivalents[0] # Simplistic choice
                translated_name = best_equivalent.get("name", translated_name)
                translated_description = best_equivalent.get("description", translated_description)

            # Fetch media links
            # This simulates products_crud.get_media_links_for_product(product_id)
            media_links_raw = get_media_links_for_product(conn, product_id)
            media_links_processed = []
            if media_links_raw:
                for media_link in media_links_raw:
                    file_path = media_link.get("file_path")
                    if file_path and app_root_dir: # MEDIA_FILES_BASE_PATH was a dummy, use app_root_dir or config
                        # Use a configured base path for media, or derive from app_root_dir if necessary.
                        # Let's assume AppGlobalConfig.get('media_files_path', os.path.join(app_root_dir, 'media'))
                        # For simplicity, if app_root_dir is given, we'll use it. Otherwise, try config.

                        media_root = AppGlobalConfig.get('media_files_path')
                        if not media_root and app_root_dir: # Fallback if media_files_path not in config
                            media_root = os.path.join(app_root_dir, 'media')

                        if media_root:
                            abs_media_path = os.path.join(media_root, file_path.lstrip(os.sep))
                            if os.path.exists(abs_media_path):
                                 media_links_processed.append({
                                     "url": f"file://{abs_media_path.replace(os.sep, '/')}",
                                     "type": media_link.get("type", "image"),
                                     "description": media_link.get("description")
                                 })
                            else:
                                logger.warning(f"Media file not found: {abs_media_path} for product {product_id} (media_root: {media_root})")
                        else:
                             logger.warning(f"Media root path could not be determined. Cannot resolve media path for product {product_id}: {file_path}")
                    # Removed: elif file_path and not app_root_dir, as media_root logic covers this.


            quantity = Decimal(str(prod_data.get("quantity", 1)))
            unit_price = Decimal(str(current_product_details.get("unit_price", "0.00")))
            item_total_price = quantity * unit_price

            context["products"].append({
                "id": product_id,
                "original_name": current_product_details.get("name"),
                "original_description": current_product_details.get("description"),
                "sku": current_product_details.get("sku"),
                "name": translated_name,
                "description": translated_description,
                "quantity": quantity,
                "unit_price": format_currency(unit_price, context["doc"]["currency_symbol"]),
                "total_price": format_currency(item_total_price, context["doc"]["currency_symbol"]),
                "unit_price_decimal": unit_price,
                "total_price_decimal": item_total_price,
                "media_links": media_links_processed,
                # Add other product fields as necessary
            })
            total_items_price += item_total_price

        # 7. Totals Calculation (doc section)
        subtotal = total_items_price
        discount_amount = subtotal * context["doc"]["discount_rate"]
        subtotal_after_discount = subtotal - discount_amount
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


        # 8. Client-Specific Notes (doc section)
        # Ensure document_type is passed if notes are type-specific
        doc_type_for_notes = additional_data.get("document_type_for_notes", document_type)
        if doc_type_for_notes and client_id and language_code:
            notes = get_client_document_notes(conn, client_id, doc_type_for_notes, language_code)
            context["doc"]["client_specific_notes"] = notes # Assuming notes is a list of strings or a single string
        else:
            context["doc"]["client_specific_notes"] = []


        # 9. Placeholders Dictionary (placeholders section)
        # Basic placeholders, can be expanded
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

        # Add all product details to placeholders, prefixed for lists
        # For simplicity, this example doesn't create complex list placeholders here.
        # Typically, templating engines handle lists of objects directly.

    except Exception as e:
        logger.error(f"Error building document context: {e}", exc_info=True)
        # Ensure a partial context is still returned to avoid breaking consumers
    finally:
        if db_conn is None and conn: # Only close if created within this function
            conn.close()

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
