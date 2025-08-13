import unittest
from unittest.mock import patch, MagicMock
import os
import sys
from datetime import datetime

# Adjust sys.path to allow importing proforma_invoice_utils
# This assumes proforma_invoice_utils.py is in the parent directory of tests/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.proforma_invoice_utils import get_proforma_invoice_context_data, _format_address_parts, format_currency

# --- Mock ProformaInvoice and ProformaInvoiceItem classes ---
# These are simplified versions of what might be SQLAlchemy models
# Used to simulate data passed into get_proforma_invoice_context_data

class MockProformaInvoice:
    def __init__(self, **kwargs):
        self.id = "pf_test_id"
        self.client_id = "client_123"
        self.project_id = "proj_456"
        self.company_id = "comp_789"
        self.proforma_invoice_number = "PF-2024-001"
        self.currency = "EUR"
        self.payment_terms = "Net 30"
        self.delivery_terms = "EXW Factory"
        self.incoterms = "EXW"
        self.named_place_of_delivery = "Factory XYZ"
        self.notes = "Test notes for proforma"
        self.status = "DRAFT"
        self.created_date = datetime(2024, 1, 15, 10, 0, 0)
        self.sent_date = None
        self.subtotal_amount = 200.0
        self.discount_amount = 20.0  # 10% of 200
        self.vat_amount = 36.0       # 20% of (200 - 20)
        self.grand_total_amount = 216.0 # 180 + 36
        self.linked_document_id = None
        self.generated_invoice_id = None
        self.items = []
        self.client_order_ref = "CLIENT-PO-111"
        self.client_order_date = datetime(2024,1,10)
        # Allow overriding defaults with kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

class MockProformaInvoiceItem:
    def __init__(self, product_id, description, quantity, unit_price, total_price):
        self.product_id = product_id
        self.description = description # This is ProformaInvoiceItem.description (specific override for the line)
        self.quantity = quantity
        self.unit_price = unit_price
        self.total_price = total_price

class TestProformaInvoiceUtils(unittest.TestCase):

    def test_format_address_parts_helper(self):
        self.assertEqual(_format_address_parts("1 Rue de la Paix", "Paris", "75001", "France"), "1 Rue de la Paix, Paris, 75001, France")
        self.assertEqual(_format_address_parts(None, "Lyon", "69000", "France"), "Lyon, 69000, France")
        self.assertEqual(_format_address_parts("Main St", None, None, "USA"), "Main St, USA")
        self.assertEqual(_format_address_parts(None, None, None, None), "N/A")
        self.assertEqual(_format_address_parts("N/A", "Berlin", "", "Germany"), "Berlin, Germany")


    def test_format_currency_helper(self):
        self.assertEqual(format_currency(1234.56, "€"), "1 234,56 €")
        self.assertEqual(format_currency(1000, "$", 0), "1 000 $")
        self.assertEqual(format_currency(None, "£"), "N/A £")
        self.assertEqual(format_currency(50.75, "USD", 2), "50,75 USD") # Test with explicit currency symbol

    @patch('app.utils.proforma_invoice_utils.get_db_connection')
    @patch('app.utils.proforma_invoice_utils.db_get_company_by_id')
    @patch('app.utils.proforma_invoice_utils.db_get_personnel_for_company')
    @patch('app.utils.proforma_invoice_utils.db_get_client_by_id')
    @patch('app.utils.proforma_invoice_utils.db_get_country_by_id')
    @patch('app.utils.proforma_invoice_utils.db_get_city_by_id')
    @patch('app.utils.proforma_invoice_utils.db_get_contacts_for_client')
    @patch('app.utils.proforma_invoice_utils.db_get_project_by_id')
    @patch('app.utils.proforma_invoice_utils._get_batch_products_and_equivalents')
    @patch('app.utils.proforma_invoice_utils.db_get_client_document_notes')
    @patch('os.path.exists') # Mock os.path.exists for logo file check
    def test_get_proforma_invoice_context_data_with_instance_french(
        self, mock_os_path_exists, mock_get_client_doc_notes, mock_get_batch_products,
        mock_get_project, mock_get_contacts, mock_get_city, mock_get_country,
        mock_get_client, mock_get_personnel, mock_get_company, mock_get_db_conn
    ):
        # --- Setup Mocks ---
        mock_db_conn_instance = MagicMock()
        mock_get_db_conn.return_value = mock_db_conn_instance
        mock_os_path_exists.return_value = True # Assume logo file exists

        mock_get_company.return_value = {
            'company_id': 'comp_789', 'company_name': 'Le Vendeur S.A.',
            'email': 'contact@levendeur.fr', 'phone': '0102030405',
            'address': '1 Rue du Commerce, 75000 Paris',
            'payment_info': '{"bank_name": "Banque Française", "iban": "FR_VENDEUR_IBAN", "bank_account_holder_name": "Le Vendeur S.A."}',
            'other_info': '{"vat_id": "FR_VAT_VENDEUR", "registration_number": "REG_VENDEUR_123"}',
            'logo_filename': 'vendeur_logo.png'
        }
        mock_get_personnel.return_value = [{'first_name': 'Jean', 'last_name': 'Dupont'}]

        mock_get_client.return_value = {
            'client_id': 'client_123', 'company_name': 'Acheteur International SARL',
            'client_name': 'Mme. Acheteur', # Default contact name if no primary contact
            'address_line1': '10 Avenue des Clients', 'city_id': 'city_client_id', 'country_id': 'country_client_id',
            'email': 'direct@acheteur.com',
            'notes': '{"vat_id": "FR_VAT_ACHETEUR"}'
        }
        # Simulate a primary contact being found
        mock_get_contacts.return_value = [{
            'givenName': 'Sophie', 'familyName': 'Martin', 'email': 'sophie.martin@acheteur.com',
            'phone': '0607080910', 'address_streetAddress': '10 Avenue des Clients',
            'address_city': 'Lyon', 'address_postalCode': '69002', 'address_country': 'France'
        }]
        # These mocks for city/country are fallbacks if contact doesn't have full address
        mock_get_city.return_value = {'name': 'Ville Client DB'}
        mock_get_country.return_value = {'name': 'Pays Client DB'}

        mock_get_project.return_value = {'project_id': 'proj_456', 'name': 'Projet Alpha', 'project_identifier': 'ALPHA-001'}

        # Items for the proforma instance
        item1_desc_override = "Description spécifique pour Article Alpha sur cette proforma"
        mock_pf_item1 = MockProformaInvoiceItem("prod_alpha", item1_desc_override, 2, 100.0, 200.0)
        mock_pf_item2 = MockProformaInvoiceItem("prod_beta", "Article Beta", 1, 50.0, 50.0) # No specific override, name will be from product_details

        # Mock for _get_batch_products_and_equivalents (products to be rendered)
        mock_get_batch_products.return_value = {
            "prod_alpha": {
                "id": "prod_alpha", "original_name": "Alpha Product English", "original_description": "Detailed English description for Alpha.",
                "original_language_code": "en", "base_unit_price": 100.0, "unit_of_measure": "pièce",
                "product_code": "ALPHA_SKU", "equivalent_name": "Produit Alpha Français", "equivalent_description": "Description française détaillée pour Alpha.",
                "equivalent_language_code": "fr"
            },
            "prod_beta": { # Product with no French equivalent name/desc, should use original
                "id": "prod_beta", "original_name": "Beta Product English", "original_description": "Detailed English description for Beta.",
                "original_language_code": "en", "base_unit_price": 50.0, "unit_of_measure": "set",
                "product_code": "BETA_SKU", "equivalent_name": None, "equivalent_description": None, # No French translation
                "equivalent_language_code": None
            }
        }
        mock_get_client_doc_notes.return_value = "Notes spécifiques au client pour la proforma en français."

        # Create the mock ProformaInvoice instance with items
        test_proforma = MockProformaInvoice(
            items=[mock_pf_item1, mock_pf_item2],
            subtotal_amount=250.0, # 2*100 + 1*50
            discount_amount=25.0,  # 10% of 250
            vat_amount=45.0,       # 20% of (250 - 25) = 20% of 225
            grand_total_amount=270.0 # 225 + 45
        )

        # --- Call the function under test ---
        # Patching PROJECT_ROOT_DIR_CONTEXT and LOGO_SUBDIR_CONTEXT for consistent test runs
        with patch.dict(sys.modules['app.utils.proforma_invoice_utils'].__dict__, {
            'PROJECT_ROOT_DIR_CONTEXT': os.path.abspath(os.path.join(os.path.dirname(__file__), '..')), # Assumes tests/ is one level down
            'LOGO_SUBDIR_CONTEXT': os.path.join("assets", "logos")
        }):
            context = get_proforma_invoice_context_data(
                proforma_instance=test_proforma,
                target_language_code="fr" # Test with French target language
            )

        # --- Assertions ---
        self.assertIsNotNone(context)

        # Seller details
        self.assertEqual(context['seller']['company_name'], 'Le Vendeur S.A.')
        self.assertEqual(context['seller']['vat_id'], 'FR_VAT_VENDEUR')
        self.assertTrue(context['seller']['logo_path'].endswith('assets/logos/vendeur_logo.png'))

        # Client details (should use primary contact Sophie Martin)
        self.assertEqual(context['client']['company_name'], 'Acheteur International SARL')
        self.assertEqual(context['client']['representative_name'], 'Sophie Martin')
        self.assertEqual(context['client']['email'], 'sophie.martin@acheteur.com')
        self.assertEqual(context['client']['address'], '10 Avenue des Clients, Lyon, 69002, France')
        self.assertEqual(context['client']['vat_id'], 'FR_VAT_ACHETEUR')

        # Document details
        self.assertEqual(context['doc']['proforma_id'], 'PF-2024-001')
        self.assertEqual(context['doc']['subtotal_amount_raw'], 250.0)
        self.assertEqual(context['doc']['discount_amount_raw'], 25.0)
        self.assertEqual(context['doc']['vat_amount_raw'], 45.0)
        self.assertEqual(context['doc']['grand_total_amount_raw'], 270.0)
        self.assertEqual(context['doc']['vat_label'], 'TVA') # Check VAT label for French
        self.assertEqual(context['doc']['client_specific_footer_notes'], "Notes spécifiques au client pour la proforma en français.")

        # Order details
        self.assertEqual(context['order']['client_order_number'], "CLIENT-PO-111")
        self.assertEqual(context['order']['client_order_date'], "2024-01-10")

        # Products details
        self.assertEqual(len(context['products']), 2)

        prod_alpha_ctx = context['products'][0]
        self.assertEqual(prod_alpha_ctx['product_code'], 'ALPHA_SKU')
        self.assertEqual(prod_alpha_ctx['name'], 'Produit Alpha Français') # French name from equivalent
        self.assertEqual(prod_alpha_ctx['original_name'], 'Alpha Product English') # Original name captured
         # Description from ProformaInvoiceItem.description, as it's different from "Produit Alpha Français"
        self.assertEqual(prod_alpha_ctx['description'], item1_desc_override)
        self.assertEqual(prod_alpha_ctx['quantity'], 2)
        self.assertEqual(prod_alpha_ctx['unit_price_raw'], 100.0)
        self.assertEqual(prod_alpha_ctx['total_price_formatted'], '200,00 €')

        prod_beta_ctx = context['products'][1]
        self.assertEqual(prod_beta_ctx['product_code'], 'BETA_SKU')
        self.assertEqual(prod_beta_ctx['name'], 'Beta Product English') # No French equivalent, uses original name
        self.assertEqual(prod_beta_ctx['original_name'], '') # Original name not stored if not translated
        # ProformaInvoiceItem.description ("Article Beta") is different from product name ("Beta Product English")
        self.assertEqual(prod_beta_ctx['description'], "Article Beta")
        self.assertEqual(prod_beta_ctx['quantity'], 1)
        self.assertEqual(prod_beta_ctx['unit_price_raw'], 50.0)

        # Check formatted totals
        self.assertEqual(context['doc']['grand_total_amount_formatted'], '270,00 €')
        self.assertEqual(context['doc']['discount_amount_formatted'], '25,00 €')
        self.assertEqual(context['doc']['vat_amount_formatted'], '45,00 €')

        # Verify DB connection mock calls
        mock_get_db_conn.assert_called_once()
        mock_db_conn_instance.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
