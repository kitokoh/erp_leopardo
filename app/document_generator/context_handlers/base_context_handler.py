import logging
from decimal import Decimal, ROUND_HALF_UP
import datetime
import json
import os

# Assuming access to db_manager and other cruds as in the original context_builder
# This might need adjustment based on actual import paths if refactoring context_builder
from db.cruds import (
    get_company_by_id,
    get_client_by_id,
    referents_crud,
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
    application_settings_crud,
    # Assuming commandes_crud is available, e.g., from db import commandes_crud
)
# This import might need to be relative if commandes_crud is in db.cruds package
# from db.cruds import commandes_crud # Or from db import commandes_crud if it's at that level

logger = logging.getLogger(__name__)

class BaseContextHandler:
    """
    Base class for document context handlers.
    Provides common utility functions and a structure for fetching context data.
    """
    def __init__(self, client_id: int, company_id: int, language_code: str,
                 app_root_dir: str, config: dict, additional_data: dict = None,
                 project_id: int = None, order_id: str = None):
        self.client_id = client_id
        self.company_id = company_id
        self.language_code = language_code
        self.app_root_dir = app_root_dir
        self.config = config # Storing the global config object
        self.additional_data = additional_data if additional_data else {}
        self.project_id = project_id
        self.order_id = order_id

        self.context = {
            "doc": {},
            "client": {},
            "seller": {},
            "project": {},
            "order": {}, # Added for order-specific details
            "items": [], # Unified list for products/order items
            "labels": {},
            "lang": {},
            "placeholders": {},
            "additional": self.additional_data, # Keep a reference to original additional_data
            "custom": {}, # For custom fields from additional_data
        }

    def _format_date(self, date_str_or_obj, date_format_iso="%Y-%m-%d"):
        # (Copied from original context_builder, can be made a staticmethod or utility function)
        if not date_str_or_obj:
            return "N/A"
        # ... (rest of the format_date logic) ...
        date_obj = None
        if isinstance(date_str_or_obj, str):
            try:
                if 'T' in date_str_or_obj: date_str_or_obj = date_str_or_obj.split('T')[0]
                possible_formats = [date_format_iso, "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"]
                parsed = False
                for fmt in possible_formats:
                    try:
                        date_obj = datetime.datetime.strptime(date_str_or_obj, fmt).date(); parsed = True; break
                    except ValueError: continue
                if not parsed: return date_str_or_obj
            except ValueError: return date_str_or_obj
        elif isinstance(date_str_or_obj, datetime.date): date_obj = date_str_or_obj
        elif isinstance(date_str_or_obj, datetime.datetime): date_obj = date_str_or_obj.date()
        else: return "N/A"

        if self.language_code == "fr": return date_obj.strftime("%d/%m/%Y")
        elif self.language_code == "en": return date_obj.strftime("%m/%d/%Y")
        return date_obj.strftime(date_format_iso)


    def _format_currency(self, amount, currency_symbol=None, decimal_places=2):
        # (Copied from original context_builder, can be made a staticmethod or utility function)
        _currency_symbol = currency_symbol if currency_symbol is not None else self.context.get("doc", {}).get("currency_symbol", "€")
        if amount is None:
            return f"0,00 {_currency_symbol}" if self.language_code == 'fr' else f"{_currency_symbol}0.00"
        # ... (rest of the format_currency logic) ...
        if not isinstance(amount, Decimal):
            try: amount = Decimal(str(amount))
            except Exception: return f"0,00 {_currency_symbol}" if self.language_code == 'fr' else f"{_currency_symbol}0.00"

        quantizer = Decimal('0.1') ** decimal_places
        rounded_amount = amount.quantize(quantizer, ROUND_HALF_UP)
        abs_rounded_amount = abs(rounded_amount)
        parts = str(abs_rounded_amount).split('.')
        integer_part_str = parts[0]
        decimal_part_str = parts[1] if len(parts) > 1 else '0' * decimal_places
        decimal_part_str = decimal_part_str.ljust(decimal_places, '0')

        thousands_sep, decimal_sep = (" ", ",") if self.language_code == 'fr' else (",", ".")

        reversed_integer_part = list(integer_part_str[::-1])
        formatted_integer_list = [digit + (thousands_sep if i > 0 and i % 3 == 0 else "") for i, digit in enumerate(reversed_integer_part)]
        formatted_integer_part = "".join(formatted_integer_list[::-1])
        sign = "-" if rounded_amount < 0 else ""

        if self.language_code == 'fr': return f"{sign}{formatted_integer_part}{decimal_sep}{decimal_part_str} {_currency_symbol}"
        return f"{sign}{_currency_symbol}{formatted_integer_part}{decimal_sep}{decimal_part_str}"

    def _load_common_data(self):
        """Loads data common to most/all documents."""
        # Document Info (doc section)
        self.context["doc"]["current_date"] = self._format_date(datetime.date.today(), self.language_code) # Use formatted
        self.context["doc"]["current_date_iso"] = datetime.date.today().strftime("%Y-%m-%d")
        self.context["doc"]["current_year"] = datetime.date.today().year
        self.context["doc"]["currency_symbol"] = self.additional_data.get("currency_symbol", self.config.get("default_currency_symbol", "€"))
        self.context["doc"]["vat_rate"] = Decimal(str(self.additional_data.get("vat_rate", self.config.get("default_vat_rate", "0.20"))))
        self.context["doc"]["discount_rate"] = Decimal(str(self.additional_data.get("discount_rate", "0.00")))

        # Language Info (lang section) & Localized Labels
        self.context["lang"]["code"] = self.language_code
        self.context["lang"]["text_direction"] = "rtl" if self.language_code == "ar" else "ltr"

        translations_base_path = os.path.join(self.app_root_dir, "translations", "doc_labels")
        labels_path = os.path.join(translations_base_path, f"{self.language_code}.json")
        loaded_labels = {}
        if os.path.exists(labels_path):
            try:
                with open(labels_path, 'r', encoding='utf-8') as f: loaded_labels = json.load(f)
            except Exception as e: logger.error(f"Error loading labels for {self.language_code}: {e}")
        else: # Fallback to English
            labels_path_en = os.path.join(translations_base_path, "en.json")
            if os.path.exists(labels_path_en):
                try:
                    with open(labels_path_en, 'r', encoding='utf-8') as f: loaded_labels = json.load(f)
                    logger.warning(f"Labels for {self.language_code} not found, using English fallback.")
                except Exception as e: logger.error(f"Error loading EN fallback labels: {e}")
            else: logger.error(f"EN fallback labels not found at {labels_path_en}")
        self.context["labels"] = loaded_labels

        # Seller Information
        seller_company = get_company_by_id(self.company_id)
        if seller_company:
            self.context["seller"] = {
                "name": seller_company.get("name"),
                "address": seller_company.get("address"), # Assuming a single 'address' field from new company structure
                "address_line1": seller_company.get("address_line1"), # Keep for compatibility if used
                "city_zip_country": ", ".join(filter(None, [seller_company.get("city_name"), seller_company.get("postal_code"), seller_company.get("country_name")])),
                "phone": seller_company.get("phone"),
                "email": seller_company.get("email"),
                "website": seller_company.get("website"),
                "vat_id": seller_company.get("vat_id"),
                "registration_number": seller_company.get("registration_number"), # Assuming this field exists
                "logo_url": "", # To be populated
            }
            logo_filename = seller_company.get("logo_path")
            if logo_filename and self.app_root_dir and self.config:
                logo_subdir = self.config.get('company_logo_dir', 'resources/company_logos') # Adjusted default path
                logo_abs_path = os.path.join(self.app_root_dir, logo_subdir, logo_filename)
                if os.path.exists(logo_abs_path):
                    self.context["seller"]["logo_url"] = f"file:///{os.path.normpath(logo_abs_path).replace(os.sep, '/')}"
                else: logger.warning(f"Seller logo {logo_filename} not found at {logo_abs_path}")

            # Payment info from JSON or dedicated fields
            payment_info_str = seller_company.get("payment_info", "{}")
            try: payment_info = json.loads(payment_info_str) if payment_info_str else {}
            except json.JSONDecodeError: payment_info = {}
            self.context["seller"].update({
                "bank_name": payment_info.get("bank_name"),
                "bank_account_holder_name": payment_info.get("bank_account_holder_name"),
                "bank_iban": payment_info.get("iban"),
                "bank_swift_bic": payment_info.get("swift_bic"),
                "bank_address": payment_info.get("bank_address"),
            })

        # Client Information
        client_data = get_client_by_id(self.client_id)
        if client_data:
            self.context["client"] = {
                "id": client_data.get("client_id"),
                "individual_name": client_data.get("name"),
                "company_name": client_data.get("company_name"),
                "display_name": client_data.get("company_name") or client_data.get("name"),
                "address_line1": client_data.get("address_line1"),
                "address_line2": client_data.get("address_line2"),
                "postal_code": client_data.get("postal_code"),
                "city": None, "country": None, # To be filled by city/country lookups
                "vat_id": None, "registration_number": None, # To be filled from notes/distributor_info
                "contact_name": None, "contact_email": None, "contact_phone": None,
            }
            client_city_id = client_data.get("city_id")
            if client_city_id: city_obj = get_city_by_id(client_city_id); self.context["client"]["city"] = city_obj.get("name") if city_obj else None
            client_country_id = client_data.get("country_id")
            if client_country_id: country_obj = get_country_by_id(client_country_id); self.context["client"]["country"] = country_obj.get("name") if country_obj else None
            self.context["client"]["city_zip_country"] = ", ".join(filter(None, [self.context["client"]["city"], self.context["client"]["postal_code"], self.context["client"]["country"]]))
            self.context["client"]["address_full"] = ", ".join(filter(None, [self.context["client"]["address_line1"], self.context["client"]["address_line2"], self.context["client"]["city_zip_country"]]))

            client_notes_raw = client_data.get('notes', "")
            client_dist_info_raw = client_data.get('distributor_specific_info', "")
            try: client_notes_json = json.loads(client_notes_raw) if client_notes_raw and client_notes_raw.strip().startswith('{') else {}
            except: client_notes_json = {}
            try: client_dist_info_json = json.loads(client_dist_info_raw) if client_dist_info_raw and client_dist_info_raw.strip().startswith('{') else {}
            except: client_dist_info_json = {}
            self.context["client"]["vat_id"] = client_dist_info_json.get("vat_id", client_notes_json.get("vat_id", self.additional_data.get("client_vat_id")))
            self.context["client"]["registration_number"] = client_dist_info_json.get("registration_number", client_notes_json.get("registration_number", self.additional_data.get("client_registration_number")))

            contacts = get_contacts_for_client(self.client_id)
            if contacts:
                primary_contact = next((c for c in contacts if c.get("is_primary")), contacts[0] if contacts else None)
                if primary_contact:
                    self.context["client"].update({
                        "contact_name": primary_contact.get("name"),
                        "contact_email": primary_contact.get("email"),
                        "contact_phone": primary_contact.get("phone"),
                    })

        # Project Information
        if self.project_id:
            project_data = get_project_by_id(self.project_id)
            if project_data: self.context["project"] = project_data # Use whole dict or cherry-pick
        elif "project_name" in self.additional_data or "project_identifier" in self.additional_data:
            self.context["project"]["name"] = self.additional_data.get("project_name")
            self.context["project"]["identifier"] = self.additional_data.get("project_identifier")
        elif client_data and client_data.get("default_project_identifier"):
             self.context["project"]["identifier"] = client_data.get("default_project_identifier")
             self.context["project"]["name"] = client_data.get("default_project_name") # Assuming this exists

        # Footer Notes
        custom_footer_notes = self.additional_data.get('footer_notes')
        if custom_footer_notes and custom_footer_notes.strip():
            self.context["doc"]["footer_notes"] = custom_footer_notes
        else:
            default_footer_key = f"default_document_footer_notes_{self.language_code}"
            self.context["doc"]["footer_notes"] = application_settings_crud.get_setting(default_footer_key, default="")

        # Custom fields from additional_data
        if "custom_fields" in self.additional_data and isinstance(self.additional_data["custom_fields"], dict):
            self.context["custom"] = self.additional_data["custom_fields"]

    def _calculate_totals(self):
        """Calculates subtotal, VAT, discount, and grand total based on items."""
        subtotal_ht = sum(item.get("total_price_decimal", Decimal("0.00")) for item in self.context["items"])

        discount_rate = self.context["doc"].get("discount_rate", Decimal("0.00"))
        vat_rate = self.context["doc"].get("vat_rate", Decimal("0.00"))

        discount_amount = subtotal_ht * discount_rate
        subtotal_after_discount = subtotal_ht - discount_amount
        vat_amount = subtotal_after_discount * vat_rate
        grand_total = subtotal_after_discount + vat_amount

        self.context["doc"]["subtotal_amount_raw"] = subtotal_ht
        self.context["doc"]["discount_amount_raw"] = discount_amount
        self.context["doc"]["vat_amount_raw"] = vat_amount
        self.context["doc"]["grand_total_amount_raw"] = grand_total

        cs = self.context["doc"]["currency_symbol"]
        self.context["doc"]["subtotal_amount"] = self._format_currency(subtotal_ht, cs)
        self.context["doc"]["discount_amount"] = self._format_currency(discount_amount, cs)
        self.context["doc"]["vat_amount"] = self._format_currency(vat_amount, cs)
        self.context["doc"]["grand_total_amount"] = self._format_currency(grand_total, cs)

    def _populate_items_from_order(self):
        """Populates self.context['items'] based on self.order_id."""
        if not self.order_id:
            logger.info("No order_id provided, skipping item population from order.")
            return

        # Ensure commandes_crud is accessible. This might require an import like:
        # from db.cruds import commandes_crud
        # For this example, I'll assume it's globally available or passed in.
        # If not, this line will fail.
        try:
            from db.cruds import commandes_crud # Attempting to import if not already
        except ImportError:
            logger.error("commandes_crud not available. Cannot populate items from order.")
            return

        order_details_raw = commandes_crud.get_commande_by_id(self.order_id)
        if order_details_raw:
            self.context["order"] = {
                "id": order_details_raw.get("commande_id"),
                "reference": order_details_raw.get("commande_reference"),
                "date": self._format_date(order_details_raw.get("commande_date")),
                "description": order_details_raw.get("description_commande"),
                # Add other order-level fields as needed
            }
            # Override doc currency with order currency if available
            if order_details_raw.get("currency"):
                 self.context["doc"]["currency_symbol"] = order_details_raw.get("currency")

            raw_items_data = commandes_crud.get_items_for_commande(self.order_id)
            if raw_items_data is None: raw_items_data = []

            processed_items = []
            for item_data in raw_items_data:
                global_product_id = item_data.get("product_id")
                display_name = item_data.get("description_item")
                display_description = "" # CommandeItem might not have long description

                if global_product_id:
                    original_product_details = get_product_by_id(global_product_id)
                    product_for_display = original_product_details # Default to original
                    if original_product_details:
                        original_product_lang = original_product_details.get("language_code")
                        if original_product_lang != self.language_code:
                            equivalents = get_equivalent_products(global_product_id)
                            if equivalents:
                                for eq in equivalents:
                                    if eq.get("language_code") == self.language_code:
                                        product_for_display = eq; break

                        display_name = product_for_display.get("product_name", display_name)
                        display_description = product_for_display.get("description", "")
                        if product_for_display.get("product_id") == global_product_id and \
                           product_for_display.get("language_code") != self.language_code:
                            display_name += f" ({product_for_display.get('language_code', '').upper()})"

                quantity = Decimal(str(item_data.get("quantity", 1)))
                unit_price_ht = Decimal(str(item_data.get("unit_price_ht", "0.00")))
                total_item_ht = Decimal(str(item_data.get("total_item_ht", "0.00")))

                media_links_processed = []
                # ... (media links logic from original context_builder, adapted for self.config and self.app_root_dir)

                processed_items.append({
                    "product_code": item_data.get("product_code", global_product_id),
                    "name": display_name,
                    "description": display_description,
                    "quantity": quantity,
                    "unit_price_formatted": self._format_currency(unit_price_ht),
                    "total_price_formatted": self._format_currency(total_item_ht),
                    "unit_price_decimal": unit_price_ht,
                    "total_price_decimal": total_item_ht,
                    # ... other item fields ...
                    "media_links": media_links_processed,
                })
            self.context["items"] = processed_items
        else:
            logger.warning(f"Order with ID {self.order_id} not found for item population.")
            self.context["items"] = [] # Ensure items is an empty list

    def get_context(self) -> dict:
        """
        Main method to build and return the full context.
        Subclasses should override _load_specific_data.
        """
        self._load_common_data()

        # If order_id is present, prioritize populating items from the order
        if self.order_id:
            self._populate_items_from_order()
        else:
            # Placeholder for logic if items need to be populated from project/client directly
            # when no order_id is given. This part needs specific implementation if required.
            logger.info("No order_id, item population from project/client not yet implemented in base handler.")
            self.context["items"] = []

        self._load_specific_data() # For subclasses to add their specific data
        self._calculate_totals() # Calculate totals after items are populated
        self._populate_placeholders() # Populate placeholders at the end

        return self.context

    def _load_specific_data(self):
        """
        Placeholder for subclasses to load document-type-specific data.
        This method should be overridden by concrete handlers.
        """
        logger.debug("BaseContextHandler._load_specific_data called. No specific data loaded by base.")
        pass

    def _populate_placeholders(self):
        """Populates the 'placeholders' part of the context with common values."""
        self.context["placeholders"] = {
            "BUYER_COMPANY_NAME": self.context["client"].get("company_name", self.context["client"].get("display_name")),
            "BUYER_CONTACT_NAME": self.context["client"].get("contact_name"),
            "SELLER_COMPANY_NAME": self.context["seller"].get("name"),
            "PROJECT_NAME": self.context["project"].get("name"),
            "PROJECT_IDENTIFIER": self.context["project"].get("identifier"),
            "CURRENT_DATE": self.context["doc"].get("current_date"), # Formatted date
            "GRAND_TOTAL_AMOUNT": self.context["doc"].get("grand_total_amount"), # Formatted
            "CURRENCY_SYMBOL": self.context["doc"].get("currency_symbol"),
            "FOOTER_NOTES": self.context["doc"].get("footer_notes"),
            # Add more common placeholders as needed
        }
        # Add custom fields to placeholders, prefixed
        for cf_key, cf_value in self.context.get("custom", {}).items():
            self.context["placeholders"][f"CUSTOM_{cf_key.upper()}"] = cf_value

# Example of a specific handler (would be in its own file, e.g., proforma_invoice_handler.py)
# class ProformaInvoiceContextHandler(BaseContextHandler):
#     def _load_specific_data(self):
#         super()._load_specific_data() # Call base if it ever does something
#         logger.info(f"ProformaInvoiceContextHandler loading specific data for client {self.client_id}")
#         self.context["doc"]["proforma_id"] = self.additional_data.get("proforma_id", f"PF-{datetime.datetime.now().strftime('%Y%m%d')}")
#         self.context["doc"]["payment_terms"] = self.additional_data.get("payment_terms", "Due on receipt")
#         # ... other proforma specific logic ...

#         # Example: Fetching client-specific notes for proforma
#         doc_type_for_notes = "PROFORMA_INVOICE_HTML" # Or derived from self.additional_data.get('document_type')
#         client_notes_records = get_client_document_notes(self.client_id, doc_type_for_notes, self.language_code, is_active=True)
#         self.context["doc"]["client_specific_notes"] = [note['note_content'] for note in client_notes_records] if client_notes_records else []
```
