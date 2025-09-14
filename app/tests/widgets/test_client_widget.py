import unittest
from unittest.mock import MagicMock, patch, call, ANY
from PyQt5.QtWidgets import QApplication, QDialog

# Ensure QApplication instance exists
# app = None # Managed by pytest-qt
# def setUpModule():
#     global app
#     app = QApplication.instance()
#     if app is None:
#         app = QApplication([])

# def tearDownModule():
#     global app
#     app = None

# Adjust the import path based on your project structure
from views.client_management.ui.client_main_widget import ClientMainWidget
from views.client_management.tabs.products_tab import ProductsTab # The class whose methods we'll test

# Mock external dependencies.
# db_manager is passed from ClientMainWidget to ProductsTab.
# ProductDialog and QMessageBox are likely imported directly in products_tab.py.

mock_config_for_main_widget = {
    'app_root_dir': '/fake/app_root',
    'templates_dir': '/fake/templates',
    'db_path': 'fake_db.db', # Required by ClientMainWidget
    # Add other necessary config keys if ClientMainWidget or ProductsTab expect them
}

# Patching ProductDialog and QMessageBox where they are imported by ProductsTab.
# Patching db_manager where it's imported by ClientMainWidget (and then passed to ProductsTab).
@patch('client_management.tabs.products_tab.ProductDialog')
@patch('client_management.tabs.products_tab.QMessageBox')
@patch('client_management.ui.client_main_widget.db_manager') # This mock will be passed to ProductsTab
class TestProductsTabAddProduct(unittest.TestCase): # Renamed class

    def setUp(self, mock_db_manager_for_main_widget, mock_qmessagebox, mock_product_dialog_class):
        # Store mocks from class decorator for use in tests if needed, or let them be used directly
        self.mock_db_manager = mock_db_manager_for_main_widget # This is the one ClientMainWidget uses and passes
        self.MockQMessageBox = mock_qmessagebox
        self.MockProductDialog = mock_product_dialog_class

        self.mock_client_info = {
            'client_id': 'client123',
            'client_name': 'Test Client',
            'project_id': 'project456', # Assuming project_id might be used
            'base_folder_path': '/fake/client/folder',
            # Add other fields ClientWidget constructor or setup_ui might need
            'status_id': 'status_active',
            'category': 'TestCategory',
            'selected_languages': 'fr,en', # ProductsTab might parse this or expect a list
        }
        # Removed duplicated/mis-indented block that was here

        self.mock_notification_manager = MagicMock()
        self.mock_main_window = MagicMock() # ClientMainWidget requires main_window

        # Instantiate ClientMainWidget. It will create ProductsTab.
        # No need to mock ClientMainWidget's internal methods like setup_ui unless they cause issues
        # unrelated to ProductsTab functionality.
        self.main_widget = ClientMainWidget(
            client_info=self.mock_client_info,
            config=mock_config_for_main_widget, # Use the module-level mock config
            app_root_dir=mock_config_for_main_widget['app_root_dir'],
            notification_manager=self.mock_notification_manager,
            main_window=self.mock_main_window
        )

        # Get the ProductsTab instance from ClientMainWidget
        # Assuming ClientMainWidget stores its ProductsTab as 'products_tab_widget'
        self.products_tab_widget = self.main_widget.products_tab_widget

        # ProductsTab's UI elements (products_table, product_lang_filter_combo, products_empty_label)
        # are created within its own setup_ui method.
        # Due to global Qt mocking, these attributes on products_tab_widget will already be MagicMocks.
        # We can directly use them or re-assign if specific mock behaviors are needed per test.
        # For example, self.products_tab_widget.products_table is already a MagicMock.
        # If we need to reset calls for a specific test:
        # self.products_tab_widget.products_table.reset_mock()

    def test_add_product_single_valid_product(self, mock_db_manager_param, mock_qmessagebox_param, mock_product_dialog_class_param):
        # The class-level mocks are passed as params. Use self.mock_db_manager, self.MockQMessageBox, self.MockProductDialog set in setUp.
        """Test adding a single valid product."""
        # Configure ProductDialog mock
        mock_dialog_instance = self.MockProductDialog.return_value
        mock_dialog_instance.exec_.return_value = QDialog.Accepted
        mock_dialog_instance.get_data.return_value = [
            {'product_id': 'prod1', 'name': 'Product 1', 'quantity': '2', 'unit_price': '10.50'}
        ]
        # Removed extra ']' that was here

        # Configure db_manager mocks (using self.mock_db_manager set in setUp)
        self.mock_db_manager.add_product_to_client_or_project.return_value = 1 # Simulate successful DB add
        self.mock_db_manager.get_products_for_client_or_project.return_value = [
            {'client_project_product_id': 1, 'product_id': 'prod1', 'product_name': 'Product 1',
             'quantity': 2.0, 'unit_price_override': 10.50, 'base_unit_price': 10.0,
             'total_price_calculated': 21.0, 'language_code': 'fr'}
        ]

        # QMessageBox is already mocked at class level by self.MockQMessageBox
        self.products_tab_widget.add_product()

        # Assertions
        self.MockProductDialog.assert_called_once_with(
            self.mock_client_info['client_id'],
            ANY, # app_root_dir
            client_info_for_location=self.mock_client_info, # ProductDialog expects this
            parent=self.products_tab_widget
        )

        expected_payload = {
            'client_id': self.mock_client_info['client_id'],
            'product_id': 'prod1',
            'quantity': 2.0,
            'unit_price_override': 10.50,
            'project_id': self.mock_client_info['project_id'],
            # ProductDialog's get_data now includes client_country_id and client_city_id
            # These should be part of the payload if add_product_to_client_or_project expects them.
            # Assuming add_product_to_client_or_project was updated to handle/ignore them.
            # If it strictly expects them, they need to be in mock_client_info and then here.
            # For now, assuming the original payload structure for the DB function is unchanged by this.
            'client_country_id': self.mock_client_info.get('country_id'), # Add if needed by DB func
            'client_city_id': self.mock_client_info.get('city_id'),       # Add if needed by DB func
        }
        # Filter out None values from expected_payload if country_id/city_id are not in mock_client_info
        # or if add_product_to_client_or_project doesn't want them if None.
        # For this test, let's assume they are not strictly required by the DB function if not present.
        # The ProductDialog *will* provide them if client_info_for_location has them.
        # Let's ensure mock_client_info has them for consistency.
        if 'country_id' not in self.mock_client_info: self.mock_client_info['country_id'] = 'test_country'
        if 'city_id' not in self.mock_client_info: self.mock_client_info['city_id'] = 'test_city'
        expected_payload['client_country_id'] = self.mock_client_info['country_id']
        expected_payload['client_city_id'] = self.mock_client_info['city_id']


        self.mock_db_manager.add_product_to_client_or_project.assert_called_once_with(expected_payload)

        # Check that load_products was called
        self.mock_db_manager.get_products_for_client_or_project.assert_called_once_with(self.mock_client_info['client_id'], project_id=None, language_code=None)

        # Check if products_table was populated
        self.products_tab_widget.products_table.setRowCount.assert_called_with(0) # Cleared first
        self.products_tab_widget.products_table.insertRow.assert_called_once_with(0) # Row 0

        # Verify setItem calls for the single product
        # Expected data from self.mock_db_manager.get_products_for_client_or_project
        # {'client_project_product_id': 1, 'product_id': 'prod1', 'product_name': 'Product 1',
        #  'quantity': 2.0, 'unit_price_override': 10.50, 'base_unit_price': 10.0,
        #  'total_price_calculated': 21.0, 'language_code': 'fr',
        #  'product_description': '', 'weight': None, 'dimensions': None } # Assuming defaults if not in mock

        # {'client_project_product_id': 1, 'product_id': 'prod1', 'product_name': 'Product 1',
        #  'quantity': 2.0, 'unit_price_override': 10.50, 'base_unit_price': 10.0,
        #  'total_price_calculated': 21.0, 'language_code': 'fr',
        #  'product_description': '', 'weight': None, 'dimensions': None } # Assuming defaults if not in mock

        # The global mock for QTableWidgetItem will be used. Its .text() method should work.
        # Let's ensure the mock data for get_products_for_client_or_project is comprehensive for table population.
        mock_product_data_for_table = {
            'client_project_product_id': 1, 'product_id': 'prod1', 'product_name': 'Product 1',
            'product_description': 'Desc 1', 'weight': 0.5, 'dimensions': '10x5x2',
            'quantity': 2.0, 'unit_price_override': 10.50, 'base_unit_price': 10.0,
            'total_price_calculated': 21.0, 'language_code': 'fr'
        }
        self.mock_db_manager.get_products_for_client_or_project.return_value = [mock_product_data_for_table]

        # Re-call add_product if the mock was updated *after* the initial call.
        # For this structure, get_products_for_client_or_project is called *within* add_product (via load_products).
        # So, the mock should be set correctly before add_product is called.
        # The previous call to self.products_tab_widget.add_product() used the earlier mock.
        # To test with this detailed mock_product_data_for_table, we might need to reset and recall,
        # or ensure the mock is this detailed from the start of the test.
        # Let's assume the mock was detailed enough. Or, for clarity, reset and recall.

        # Reset relevant mocks and call add_product again if a more detailed assertion is needed.
        # For now, let's assume the initial call to add_product and its subsequent load_products
        # correctly used the mock return value set for get_products_for_client_or_project.

        set_item_calls = self.products_tab_widget.products_table.setItem.call_args_list
        expected_row_0_texts = {
            0: str(mock_product_data_for_table['client_project_product_id']),
            1: mock_product_data_for_table['product_name'],
            2: mock_product_data_for_table['product_description'],
            3: f"{mock_product_data_for_table['weight']:.2f} kg", # Assuming formatting
            4: mock_product_data_for_table['dimensions'],
            5: str(mock_product_data_for_table['quantity']),
            6: f"{mock_product_data_for_table['unit_price_override']:.2f}",
            7: f"€ {mock_product_data_for_table['total_price_calculated']:.2f}"
        }
        actual_row_0_items = {args[0][1]: args[0][2].text() for args in set_item_calls if args[0][0] == 0}
        for col_idx, expected_text in expected_row_0_texts.items():
            self.assertEqual(actual_row_0_items.get(col_idx), expected_text, f"Mismatch in row 0, col {col_idx}")

        self.MockQMessageBox.information.assert_called_once()
        self.MockQMessageBox.warning.assert_not_called()


    def test_add_product_multiple_products_one_invalid_data(self, mock_db_manager_param, mock_qmessagebox_param, mock_product_dialog_class_param):
        """Test adding multiple products, one with invalid quantity."""
        mock_dialog_instance = self.MockProductDialog.return_value
        mock_dialog_instance.exec_.return_value = QDialog.Accepted
        mock_dialog_instance.get_data.return_value = [
            {'product_id': 'prod1', 'name': 'Product 1', 'quantity': '2', 'unit_price': '10.00', 'client_country_id': 'FR', 'client_city_id': 'PAR'}, # Added location
            {'product_id': 'prod2', 'name': 'Product 2', 'quantity': 'invalid_qty', 'unit_price': '20.00', 'client_country_id': 'FR', 'client_city_id': 'PAR'},
            {'product_id': 'prod3', 'name': 'Product 3', 'quantity': '3', 'unit_price': '5.00', 'client_country_id': 'FR', 'client_city_id': 'PAR'}
        ]

        self.mock_db_manager.add_product_to_client_or_project.side_effect = [1, 2] # Link IDs for prod1, prod3
        self.mock_db_manager.get_products_for_client_or_project.return_value = [
            {'client_project_product_id': 1, 'product_id': 'prod1', 'product_name': 'Product 1', 'quantity': 2.0, 'unit_price_override': 10.00, 'total_price_calculated': 20.0, 'language_code': 'fr', 'product_description': '', 'weight': None, 'dimensions': 'N/A'},
            {'client_project_product_id': 2, 'product_id': 'prod3', 'product_name': 'Product 3', 'quantity': 3.0, 'unit_price_override': 5.00, 'total_price_calculated': 15.0, 'language_code': 'fr', 'product_description': '', 'weight': None, 'dimensions': 'N/A'}
        ]

        self.products_tab_widget.add_product()

        # Assertions
        self.assertEqual(self.mock_db_manager.add_product_to_client_or_project.call_count, 2)
        calls_to_db_add = [
            call({'client_id': 'client123', 'product_id': 'prod1', 'quantity': 2.0, 'unit_price_override': 10.0, 'project_id': 'project456'}),
            call({'client_id': 'client123', 'product_id': 'prod3', 'quantity': 3.0, 'unit_price_override': 5.0, 'project_id': 'project456'})
        ]
        # Ensure mock_client_info has country/city for consistent payload
        if 'country_id' not in self.mock_client_info: self.mock_client_info['country_id'] = 'FR_test' # Ensure it has some value
        if 'city_id' not in self.mock_client_info: self.mock_client_info['city_id'] = 'PAR_test'

        calls_to_db_add = [
            call({'client_id': 'client123', 'product_id': 'prod1', 'quantity': 2.0, 'unit_price_override': 10.0, 'project_id': 'project456', 'client_country_id': self.mock_client_info['country_id'], 'client_city_id': self.mock_client_info['city_id']}),
            call({'client_id': 'client123', 'product_id': 'prod3', 'quantity': 3.0, 'unit_price_override': 5.0, 'project_id': 'project456', 'client_country_id': self.mock_client_info['country_id'], 'client_city_id': self.mock_client_info['city_id']})
        ]
        self.mock_db_manager.add_product_to_client_or_project.assert_has_calls(calls_to_db_add, any_order=False)

        self.MockQMessageBox.warning.assert_called_once()
        args, _ = self.MockQMessageBox.warning.call_args
        self.assertEqual(args[1], self.products_tab_widget.tr("Données Produit Invalides ou Manquantes"))

        self.mock_db_manager.get_products_for_client_or_project.assert_called_once_with(self.mock_client_info['client_id'], project_id=None, language_code=None)

        self.products_tab_widget.products_table.setRowCount.assert_called_with(0)
        self.assertEqual(self.products_tab_widget.products_table.insertRow.call_count, 2)
        self.products_tab_widget.products_table.insertRow.assert_any_call(0)
        self.products_tab_widget.products_table.insertRow.assert_any_call(1)

        prod1_data_for_table = {
            'client_project_product_id': 1, 'product_name': 'Product 1', 'product_description': '',
            'weight': None, 'dimensions': 'N/A', 'quantity': 2.0,
            'unit_price_override': 10.00, 'base_unit_price': 10.00, # Assuming base matches if override is same
            'total_price_calculated': 20.0
        }
        # Prod3 data
        prod3_data_for_table = {
            'client_project_product_id': 2, 'product_name': 'Product 3', 'product_description': '',
            'weight': None, 'dimensions': 'N/A', 'quantity': 3.0,
            'unit_price_override': 5.00, 'base_unit_price': 5.00,
            'total_price_calculated': 15.0
        }

        # The mock for get_products_for_client_or_project already returns detailed data.
        set_item_calls = self.products_tab_widget.products_table.setItem.call_args_list

        # Check Prod1 (row 0)
        expected_row_0_texts = {
            0: str(prod1_data_for_table['client_project_product_id']), 1: prod1_data_for_table['product_name'],
            2: prod1_data_for_table['product_description'], 3: f"{prod1_data_for_table['weight']:.2f} kg" if prod1_data_for_table['weight'] is not None else 'N/A',
            4: prod1_data_for_table['dimensions'], 5: str(prod1_data_for_table['quantity']),
            6: f"{prod1_data_for_table['unit_price_override']:.2f}", 7: f"€ {prod1_data_for_table['total_price_calculated']:.2f}"
        }
        actual_row_0_items = {args[0][1]: args[0][2].text() for args in set_item_calls if args[0][0] == 0}
        for col_idx, expected_text in expected_row_0_texts.items():
            self.assertEqual(actual_row_0_items.get(col_idx), expected_text, f"Mismatch in Prod1 (row 0), col {col_idx}")

        # Check Prod3 (row 1)
        expected_row_1_texts = {
            0: str(prod3_data_for_table['client_project_product_id']), 1: prod3_data_for_table['product_name'],
            2: prod3_data_for_table['product_description'], 3: f"{prod3_data_for_table['weight']:.2f} kg" if prod3_data_for_table['weight'] is not None else 'N/A',
            4: prod3_data_for_table['dimensions'], 5: str(prod3_data_for_table['quantity']),
            6: f"{prod3_data_for_table['unit_price_override']:.2f}", 7: f"€ {prod3_data_for_table['total_price_calculated']:.2f}"
        }
        actual_row_1_items = {args[0][1]: args[0][2].text() for args in set_item_calls if args[0][0] == 1}
        for col_idx, expected_text in expected_row_1_texts.items():
            self.assertEqual(actual_row_1_items.get(col_idx), expected_text, f"Mismatch in Prod3 (row 1), col {col_idx}")


    def test_add_product_db_failure(self, mock_db_manager_param, mock_qmessagebox_param, mock_product_dialog_class_param):
        """Test scenario where adding a product to DB fails."""
        mock_dialog_instance = self.MockProductDialog.return_value
        mock_dialog_instance.exec_.return_value = QDialog.Accepted
        mock_dialog_instance.get_data.return_value = [ # Ensure location data is provided by dialog mock
            {'product_id': 'prod1', 'name': 'Product 1', 'quantity': '1', 'unit_price': '10.00', 'client_country_id': 'FR', 'client_city_id': 'PAR'}
        ]

        self.mock_db_manager.add_product_to_client_or_project.return_value = None # Simulate DB failure
        self.mock_db_manager.get_products_for_client_or_project.return_value = [] # No products after failed add

        self.products_tab_widget.add_product()

        self.mock_db_manager.add_product_to_client_or_project.assert_called_once()
        # Check specific call to warning for DB error
        # self.MockQMessageBox.warning.assert_any_call(self.products_tab_widget, self.products_tab_widget.tr("Erreur Base de Données"), ANY)
        # More precise: find the call with "Erreur Base de Données"
        db_error_warning_found = False
        for call_obj in self.MockQMessageBox.warning.call_args_list:
            args, _ = call_obj
            if args[1] == self.products_tab_widget.tr("Erreur Base de Données"):
                db_error_warning_found = True
                self.assertIs(args[0], self.products_tab_widget) # Parent check
                # self.assertIn("échec de l'ajout du produit", args[2].lower()) # Check message body content
        self.assertTrue(db_error_warning_found, "DB error warning not found or with wrong title/parent.")


        self.mock_db_manager.get_products_for_client_or_project.assert_called_once()
        self.products_tab_widget.products_table.insertRow.assert_not_called()


if __name__ == '__main__':
    unittest.main()
