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
    get_equivalent_products,
    get_media_links_for_product, 
    get_personnel_for_company,
)
from db.connection import get_db_connection # Changed from db.utils
# Assuming these config variables are correctly defined in your project.
# from db_config import APP_ROOT_DIR_CONTEXT, LOGO_SUBDIR_CONTEXT # Removed
# from config import MEDIA_FILES_BASE_PATH # Removed

# APP_ROOT_DIR_CONTEXT, LOGO_SUBDIR_CONTEXT, MEDIA_FILES_BASE_PATH will now be passed or derived from app_root_dir or config object

# Import config for MEDIA_FILES_BASE_PATH, assuming app_root_dir is for logos primarily
from app_setup import CONFIG as AppGlobalConfig

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
    document_type: str = None, # e.g., 'proforma_invoice', 'technical_sheet'
    additional_data: dict = None,
    db_conn=None, # This parameter is now effectively ignored by internal calls if they are all decorated
    app_root_dir: str = None
) -> dict:
    """
    Fetches and structures data for document generation.
    Connections to DB for CRUD operations are managed by @_manage_conn decorator on CRUD functions.
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

    # conn = db_conn if db_conn else get_db_connection() # Connection now managed by @_manage_conn on each CRUD call

    try:
        # 1. Document Info (doc section)
        context["doc"]["current_date"] = datetime.date.today().strftime("%Y-%m-%d")
        context["doc"]["current_year"] = datetime.date.today().year
        context["doc"]["currency_symbol"] = additional_data.get("currency_symbol", "€")
        context["doc"]["vat_rate"] = Decimal(additional_data.get("vat_rate", "0.20"))
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
            "date_label": "Date :",
            "project_id_label": "ID Projet :",
            "payment_terms_label": "Conditions de Paiement :",
            "delivery_terms_label": "Conditions de Livraison :",
            "item_ref": "Réf.",
            "item_description": "Description",
            "quantity": "Quantité",
            "unit_price": "Prix Unitaire",
            "total_price": "Prix Total",
            "client_order_ref_label": "Référence Commande Client :",
            "client_order_date_label": "Date Commande Client :",
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
            "thank_you_message": "شكرا لتعاملكم معنا!",
            "no_products_listed": "لا توجد منتجات مدرجة."
        },
        "ru": {
            "proforma_invoice_title": "ПРОФОРМА-ИНВОЙС",
            "from_seller": "От:",
            "to_client": "Кому:",
            "proforma_no": "Проформа-инвойс №:",
            "date_label": "Дата:",
            "project_id_label": "ID Проекта:",
            "payment_terms_label": "Условия оплаты:",
            "delivery_terms_label": "Условия поставки:",
            "item_ref": "Арт.",
            "item_description": "Описание товара",
            "quantity": "Кол-во",
            "unit_price": "Цена за ед.",
            "total_price": "Сумма",
            "client_order_ref_label": "Номер заказа клиента:",
            "client_order_date_label": "Дата заказа клиента:",
            "sub_total": "Подытог:",
            "discount": "Скидка",
            "vat": "НДС",
            "grand_total": "Итого:",
            "bank_details_title": "Наши банковские реквизиты:",
            "bank_name": "Банк:",
            "account_holder": "Получатель:",
            "iban": "IBAN:",
            "swift_bic": "SWIFT/BIC:",
            "bank_address": "Адрес банка:",
            "proforma_notice": "Это проформа-инвойс и не является требованием к оплате.",
            "thank_you_message": "Спасибо за ваш бизнес!",
            "no_products_listed": "Товары отсутствуют.",
            "company_logo_alt": "Логотип компании",
            "phone_label": "Телефон:",
            "email_label": "Email:",
            "vat_id_label": "ИНН:",
            "reg_no_label": "Рег. номер:",
            "contact_label": "Контакт:"
            }
        }
        context["labels"] = _labels.get(language_code, _labels.get("en", {}))

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
            if logo_filename and app_root_dir:
                logo_subdir = AppGlobalConfig.get('company_logo_dir', 'company_logos')
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

        # 6. Product Information (products section)
        linked_products_data = get_products_for_client_or_project(client_id=client_id, project_id=project_id) # Removed conn
        linked_products_data = linked_products_data if linked_products_data else []

        processed_products_for_context = []
        total_items_price = Decimal("0.0")

        for linked_prod_info in linked_products_data:
            global_product_id = linked_prod_info.get("product_id")
            if not global_product_id:
                logger.warning(f"Skipping linked product entry due to missing global_product_id: {linked_prod_info}")
                continue

            global_product_details = get_product_by_id(global_product_id) # Removed conn
            if not global_product_details:
                logger.warning(f"Global product details not found for product_id: {global_product_id} (linked via client_project_product_id: {linked_prod_info.get('client_project_product_id')}). Skipping.")
                continue

            display_name = None
            display_description = None
            product_matches_target_language = False

            all_raw_equivalents = get_equivalent_products(global_product_id) # Removed conn

            found_equivalent_in_lang = None
            if all_raw_equivalents:
                for eq_prod in all_raw_equivalents:
                    if eq_prod.get("language_code") == language_code:
                        found_equivalent_in_lang = eq_prod
                        break

            if found_equivalent_in_lang:
                display_name = found_equivalent_in_lang.get("name", global_product_details.get("name"))
                display_description = found_equivalent_in_lang.get("description", global_product_details.get("description"))

                product_matches_target_language = True
            elif global_product_details.get("language_code") == language_code:
                display_name = global_product_details.get("name")
                display_description = global_product_details.get("description")
                product_matches_target_language = True
            
            if not product_matches_target_language:
                logger.info(f"Product ID {global_product_id} (Name: {global_product_details.get('name')}) will be excluded. Original lang: {global_product_details.get('language_code')}, Target lang: {language_code}.")
                continue

            quantity = Decimal(str(linked_prod_info.get("quantity", 1)))
            
            unit_price_override = linked_prod_info.get("unit_price_override")
            if unit_price_override is not None:
                unit_price = Decimal(str(unit_price_override))
            else:
                unit_price = Decimal(str(global_product_details.get("base_unit_price", "0.00")))
            
            item_total_price = quantity * unit_price
            total_items_price += item_total_price

            media_links_raw = get_media_links_for_product(global_product_id) # Removed conn
            media_links_processed = []
            if media_links_raw:
                for media_link in media_links_raw:
                    file_path = media_link.get("file_path")
                    if file_path and app_root_dir:
                        media_root = AppGlobalConfig.get('media_files_path')
                        if not media_root and app_root_dir: 
                            media_root = os.path.join(app_root_dir, 'media_files')
                        if media_root:
                            abs_media_path = os.path.join(media_root, file_path.lstrip(os.sep))
                            if os.path.exists(abs_media_path):
                                 media_links_processed.append({
                                     "url": f"file:///{abs_media_path.replace(os.sep, '/')}",
                                     "type": media_link.get("type", "image"),
                                     "description": media_link.get("description")
                                 })
                            else:
                                logger.warning(f"Media file not found: {abs_media_path} for product {global_product_id} (media_root: {media_root})")
                        else:
                             logger.warning(f"Media root path could not be determined. Cannot resolve media path for product {global_product_id}: {file_path}")
            
            processed_products_for_context.append({
                "id": global_product_id,
                "original_name": global_product_details.get("name"),
                "original_description": global_product_details.get("description"),
                "sku": global_product_details.get("product_code"),
                "name": display_name,
                "description": display_description,
                "quantity": quantity,
                "unit_price": format_currency(unit_price, context["doc"]["currency_symbol"]),
                "total_price": format_currency(item_total_price, context["doc"]["currency_symbol"]),
                "unit_price_decimal": unit_price,
                "total_price_decimal": item_total_price,
                "media_links": media_links_processed,
            })
        
        context["products"] = processed_products_for_context
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

        doc_type_for_notes = additional_data.get("document_type_for_notes", document_type)
        if doc_type_for_notes and client_id and language_code:
            notes = get_client_document_notes(client_id, doc_type_for_notes, language_code) # Removed conn
            context["doc"]["client_specific_notes"] = notes
        else:
            context["doc"]["client_specific_notes"] = []

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
