import unittest
import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime

# Adjust path to import from src
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "src"))

# Import the module to be tested
import database_manager

class TestDatabaseManager(unittest.TestCase):
    """
    Unit tests for database operations in `database_manager.py`.

    These tests use an in-memory SQLite database to ensure speed and isolation.
    Each test method operates on a fresh set of tables created in its `setUp`
    method. It verifies functionalities like table creation, data insertion,
    retrieval (by ID, all, filtered), status updates, duplicate handling
    (UNIQUE constraints), and expense summary calculations, including edge cases.
    """

    @classmethod
    def setUpClass(cls) -> None:
        """
        Overrides `database_manager.DATABASE_NAME` to use an in-memory database
        for all tests in this class. This change is global to the module being
        tested for the duration of these tests.
        """
        cls.original_db_name = database_manager.DATABASE_NAME
        # Note: While ":memory:" is often used, explicit connection passing per function
        # is the primary mechanism ensuring tests use the correct in-memory DB.
        # This override mainly affects functions that might *not* receive a conn object
        # if called internally by other functions (though current design passes conn).
        database_manager.DATABASE_NAME = ":memory:"

    @classmethod
    def tearDownClass(cls) -> None:
        """Restores the original `DATABASE_NAME` after all tests in the class have run."""
        database_manager.DATABASE_NAME = cls.original_db_name

    def setUp(self) -> None:
        """
        Sets up a fresh in-memory SQLite database and creates the necessary
        tables before each test method is run.
        A dedicated connection `self.conn` is established for each test and
        passed to the database manager functions to ensure operations occur
        on this specific in-memory database instance.
        """
        # Create a new in-memory database connection for each test
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row # To access columns by name

        # Create tables using this specific connection
        database_manager.create_tables(conn=self.conn)

        # Define sample invoice data for use in various tests
        self.sample_invoice_data_1 = {
            'supplier_name': 'Supplier Alpha',
            'invoice_number': 'INV-001',
            'invoice_date': '2023-01-15',
            'total_amount': 100.00,
            'currency': 'USD',
            'raw_text': 'Raw text for INV-001',
            'payment_status': 'À payer'
        }
        self.sample_invoice_data_2 = {
            'supplier_name': 'Supplier Beta',
            'invoice_number': 'INV-002',
            'invoice_date': '2023-02-20',
            'total_amount': 250.50,
            'currency': 'EUR',
            'raw_text': 'Raw text for INV-002',
            'payment_status': 'Payée',
            'payment_date': '2023-02-28'
        }
        self.sample_invoice_data_3 = { # For testing unpaid summary
            'supplier_name': 'Supplier Alpha', # Same supplier as 1
            'invoice_number': 'INV-003',
            'invoice_date': '2023-03-10',
            'total_amount': 75.25,
            'currency': 'USD',
            'raw_text': 'Raw text for INV-003',
            'payment_status': 'À payer'
        }


    def tearDown(self):
        """Close the connection after each test."""
        if self.conn:
            self.conn.close()
        # No need to delete :memory: db file

    def test_create_tables(self):
        """Test if tables are created."""
        # create_tables is called in setUp, so we just check if the table exists
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='invoices'")
        self.assertIsNotNone(cursor.fetchone(), "Table 'invoices' should exist after create_tables.")

    def test_save_and_get_invoice_data(self):
        """Test saving and retrieving a single invoice."""
        inserted_id = database_manager.save_invoice_data(self.sample_invoice_data_1, "invoice1.pdf", conn=self.conn)
        self.assertIsNotNone(inserted_id, "save_invoice_data should return an ID.")

        retrieved_invoice = database_manager.get_invoice_by_id(inserted_id, conn=self.conn)
        self.assertIsNotNone(retrieved_invoice, "get_invoice_by_id should retrieve the saved invoice.")
        self.assertEqual(retrieved_invoice['filename'], "invoice1.pdf")
        self.assertEqual(retrieved_invoice['supplier_name'], self.sample_invoice_data_1['supplier_name'])
        self.assertEqual(retrieved_invoice['invoice_number'], self.sample_invoice_data_1['invoice_number'])
        self.assertEqual(retrieved_invoice['total_amount'], self.sample_invoice_data_1['total_amount'])
        self.assertEqual(retrieved_invoice['payment_status'], 'À payer') # Default or as specified

    def test_save_invoice_duplicate_number(self):
        """Test UNIQUE constraint on invoice_number (and filename for composite)."""
        database_manager.save_invoice_data(self.sample_invoice_data_1, "invoice1.pdf", conn=self.conn)
        # Try saving the exact same invoice number and filename again
        duplicate_id = database_manager.save_invoice_data(self.sample_invoice_data_1, "invoice1.pdf", conn=self.conn)
        self.assertIsNone(duplicate_id, "Saving a duplicate invoice number and filename should fail.")

        # Try saving same invoice number but different filename (should also fail if invoice_number is globally unique)
        # If invoice_number is TEXT UNIQUE, this will fail.
        # If only (filename, invoice_number) is UNIQUE, this would pass.
        # Current schema has invoice_number TEXT UNIQUE AND UNIQUE(filename, invoice_number)
        # So this should fail on the invoice_number unique constraint.
        duplicate_id_diff_file = database_manager.save_invoice_data(self.sample_invoice_data_1, "invoice1_new.pdf", conn=self.conn)
        self.assertIsNone(duplicate_id_diff_file, "Saving a duplicate invoice number (even with different filename) should fail due to invoice_number UNIQUE constraint.")


    def test_get_all_invoices(self):
        """Test retrieving all invoices, with and without status filter."""
        id1 = database_manager.save_invoice_data(self.sample_invoice_data_1, "inv1.pdf", conn=self.conn) # À payer
        id2 = database_manager.save_invoice_data(self.sample_invoice_data_2, "inv2.pdf", conn=self.conn) # Payée

        all_invoices = database_manager.get_all_invoices(conn=self.conn)
        self.assertEqual(len(all_invoices), 2)

        unpaid_invoices = database_manager.get_all_invoices(status_filter='À payer', conn=self.conn)
        self.assertEqual(len(unpaid_invoices), 1)
        self.assertEqual(unpaid_invoices[0]['id'], id1)

        paid_invoices = database_manager.get_all_invoices(status_filter='Payée', conn=self.conn)
        self.assertEqual(len(paid_invoices), 1)
        self.assertEqual(paid_invoices[0]['id'], id2)

    def test_update_invoice_status(self):
        """Test updating an invoice's payment status and payment date."""
        inserted_id = database_manager.save_invoice_data(self.sample_invoice_data_1, "invoice_to_update.pdf", conn=self.conn)

        # Update to 'Payée' with a specific payment date
        payment_date_str = "2023-07-20"
        success = database_manager.update_invoice_status(inserted_id, "Payée", payment_date_str, conn=self.conn)
        self.assertTrue(success)

        updated_invoice = database_manager.get_invoice_by_id(inserted_id, conn=self.conn)
        self.assertEqual(updated_invoice['payment_status'], "Payée")
        self.assertEqual(updated_invoice['payment_date'], payment_date_str)

        # Update to 'Payée' without providing payment date (should use current date)
        id_for_auto_date = database_manager.save_invoice_data(self.sample_invoice_data_3, "invoice_auto_date.pdf", conn=self.conn)
        success_auto_date = database_manager.update_invoice_status(id_for_auto_date, "Payée", conn=self.conn)
        self.assertTrue(success_auto_date)

        updated_invoice_auto_date = database_manager.get_invoice_by_id(id_for_auto_date, conn=self.conn)
        self.assertEqual(updated_invoice_auto_date['payment_status'], "Payée")
        self.assertIsNotNone(updated_invoice_auto_date['payment_date']) # Check it's set
        self.assertEqual(updated_invoice_auto_date['payment_date'], datetime.now().strftime('%Y-%m-%d'))


    def test_get_expense_summary(self):
        """Test the expense summary calculation."""
        # No invoices initially
        summary_empty = database_manager.get_expense_summary(conn=self.conn)
        self.assertEqual(summary_empty['total_invoices'], 0)
        self.assertEqual(summary_empty['total_paid_amount'], 0.0)
        self.assertEqual(summary_empty['total_unpaid_amount'], 0.0)
        self.assertEqual(len(summary_empty['spending_by_supplier']), 0)

        # Add some invoices
        database_manager.save_invoice_data(self.sample_invoice_data_1, "s1_inv1.pdf", conn=self.conn) # Alpha, 100.00 USD, À payer
        database_manager.save_invoice_data(self.sample_invoice_data_2, "s2_inv1.pdf", conn=self.conn) # Beta,  250.50 EUR, Payée
        database_manager.save_invoice_data(self.sample_invoice_data_3, "s1_inv2.pdf", conn=self.conn) # Alpha,  75.25 USD, À payer

        summary_filled = database_manager.get_expense_summary(conn=self.conn)
        self.assertEqual(summary_filled['total_invoices'], 3)
        self.assertEqual(summary_filled['paid_invoices_count'], 1)
        self.assertAlmostEqual(summary_filled['total_paid_amount'], 250.50)
        self.assertEqual(summary_filled['unpaid_invoices_count'], 2)
        self.assertAlmostEqual(summary_filled['total_unpaid_amount'], 175.25) # 100.00 + 75.25

        self.assertEqual(len(summary_filled['spending_by_supplier']), 2)
        self.assertAlmostEqual(summary_filled['spending_by_supplier']['Supplier Alpha'], 175.25)
        self.assertAlmostEqual(summary_filled['spending_by_supplier']['Supplier Beta'], 250.50)

    def test_save_optional_fields_as_none(self):
        """Test saving an invoice where optional text fields are None."""
        minimal_data = {
            'invoice_number': 'INV-MINIMAL',
            'total_amount': 50.0,
            'raw_text': 'Minimal raw text.',
            # supplier_name, invoice_date, currency, etc., are missing (will be None)
        }
        inserted_id = database_manager.save_invoice_data(minimal_data, "minimal.pdf", conn=self.conn)
        self.assertIsNotNone(inserted_id)

        retrieved = database_manager.get_invoice_by_id(inserted_id, conn=self.conn)
        self.assertIsNotNone(retrieved)
        self.assertIsNone(retrieved['supplier_name'])
        self.assertIsNone(retrieved['invoice_date'])
        self.assertIsNone(retrieved['currency'])
        self.assertEqual(retrieved['total_amount'], 50.0)
        self.assertEqual(retrieved['payment_status'], 'À payer') # Default

    def test_update_status_non_existent_id(self):
        """Test updating status for an invoice ID that doesn't exist."""
        success = database_manager.update_invoice_status(99999, "Payée", conn=self.conn) # Assuming 99999 does not exist
        self.assertFalse(success, "Updating a non-existent invoice ID should return False.")

    def test_composite_unique_constraint_filename_invoice_number(self):
        """Test the composite UNIQUE constraint on (filename, invoice_number)."""
        # Base entry
        id1 = database_manager.save_invoice_data(self.sample_invoice_data_1, "unique_test.pdf", conn=self.conn)
        self.assertIsNotNone(id1)

        # Same filename, different invoice_number -> OK
        data_same_file_diff_inv = self.sample_invoice_data_1.copy()
        data_same_file_diff_inv['invoice_number'] = 'INV-UNIQUE-002'
        id2 = database_manager.save_invoice_data(data_same_file_diff_inv, "unique_test.pdf", conn=self.conn)
        self.assertIsNotNone(id2, "Should allow same filename if invoice_number is different.")

        # Different filename, same invoice_number -> FAIL (due to invoice_number TEXT UNIQUE)
        # This was already tested in test_save_invoice_duplicate_number
        # data_diff_file_same_inv = self.sample_invoice_data_1.copy()
        # id3 = database_manager.save_invoice_data(data_diff_file_same_inv, "unique_test_new.pdf")
        # self.assertIsNone(id3, "Should fail due to invoice_number being globally unique itself.")

        # To specifically test the composite constraint if invoice_number was NOT globally unique:
        # One would temporarily remove `UNIQUE` from `invoice_number TEXT UNIQUE` in schema.
        # For now, the existing test_save_invoice_duplicate_number covers the current schema's behavior.

    def test_get_expense_summary_edge_cases(self):
        """Test expense summary with no suppliers or zero amounts."""
        # 1. No suppliers (supplier_name is None)
        no_supplier_data = {'invoice_number': 'NS-001', 'total_amount': 100.0, 'payment_status': 'Payée', 'raw_text': '...'}
        database_manager.save_invoice_data(no_supplier_data, "no_supplier.pdf", conn=self.conn)

        summary = database_manager.get_expense_summary(conn=self.conn)
        self.assertEqual(summary['total_invoices'], 1)
        self.assertEqual(summary['paid_invoices_count'], 1)
        self.assertEqual(summary['total_paid_amount'], 100.0)
        self.assertEqual(len(summary['spending_by_supplier']), 0, "Spending by supplier should be empty if supplier names are null.")

        # Clean up for next part of test
        self.setUp() # Reset DB

        # 2. Invoices with zero or null amounts
        zero_amount_data_paid = {'supplier_name': 'ZeroSup', 'invoice_number': 'ZA-001', 'total_amount': 0.0, 'payment_status': 'Payée', 'raw_text': '...'}
        null_amount_data_unpaid = {'supplier_name': 'NullSup', 'invoice_number': 'NA-001', 'total_amount': None, 'payment_status': 'À payer', 'raw_text': '...'}
        database_manager.save_invoice_data(zero_amount_data_paid, "zero.pdf", conn=self.conn)
        database_manager.save_invoice_data(null_amount_data_unpaid, "null.pdf", conn=self.conn)

        summary_zero_null = database_manager.get_expense_summary(conn=self.conn)
        self.assertEqual(summary_zero_null['total_invoices'], 2)
        self.assertEqual(summary_zero_null['paid_invoices_count'], 1) # zero_amount_data_paid
        self.assertEqual(summary_zero_null['total_paid_amount'], 0.0)
        self.assertEqual(summary_zero_null['unpaid_invoices_count'], 1) # null_amount_data_unpaid
        self.assertEqual(summary_zero_null['total_unpaid_amount'], 0.0) # SUM(NULL) is 0 or NULL depending on SQL, here it's 0.0

        self.assertAlmostEqual(summary_zero_null['spending_by_supplier'].get('ZeroSup', 0.0), 0.0)
        # NullSup invoice has NULL total_amount, so it won't appear in `spending_by_supplier` due to `total_amount IS NOT NULL` clause
        self.assertIsNone(summary_zero_null['spending_by_supplier'].get('NullSup'))


if __name__ == '__main__':
    unittest.main()
