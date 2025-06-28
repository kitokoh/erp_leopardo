import unittest
import sqlite3
import os
import sys

# Adjust path to import db_manager from parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import db as db_manager

class TestDBContactsPagination(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_db_name = ":memory:"
        # Ensure a clean slate if a previous test run failed
        # No need to remove file for :memory: db

        # Set the override before initializing the database
        db_manager.connection.set_test_db_path_override(cls.test_db_name)
        db_manager.initialize_database(db_path_to_use=cls.test_db_name)

    @classmethod
    def tearDownClass(cls):
        db_manager.connection.clear_test_db_path_override()
        # No need to remove file for :memory: db

    def setUp(self):
        # The database schema is already initialized in setUpClass
        # and get_db_connection will use the override path.
        # We need to clear data from tables for each test for isolation.
        conn = db_manager.get_db_connection()
        cursor = conn.cursor()

        # DEBUG: Isolate lock issue
        try:
            print(f"Attempting DELETE FROM SAVTickets on {self.test_db_name}")
            cursor.execute("DELETE FROM SAVTickets")
            conn.commit()
            print(f"DELETE FROM SAVTickets committed on {self.test_db_name}")

            # Minimal deletes for TestDBContactsPagination to function if SAVTickets was the only lock
            print(f"Attempting other deletes on {self.test_db_name}")
            cursor.execute("DELETE FROM ClientContacts")
            cursor.execute("DELETE FROM ClientNotes")
            cursor.execute("DELETE FROM ClientDocuments")
            cursor.execute("DELETE FROM Templates")
            cursor.execute("DELETE FROM Contacts")
            cursor.execute("DELETE FROM Clients")
            conn.commit()
            print(f"Other core deletes committed on {self.test_db_name}")

        except sqlite3.Error as e:
            print(f"Error during delete in setUp for {self.test_db_name}: {e}")
            # conn.rollback() # Rollback might not be needed if error is before commit
            raise # Re-raise to see the original error in test output
        finally:
            if conn: # Ensure conn is not closed if an error occurred before close
                conn.close()
                print(f"Connection closed for {self.test_db_name} in setUp")

        # Add a test client
        # db_manager.add_client will use get_db_connection which respects the override
        self.test_client_id = db_manager.add_client({'client_name': 'Test Client For Pagination', 'project_identifier': 'PAG_TEST'})
        self.assertIsNotNone(self.test_client_id, "Failed to create test client")

        # Add test contacts
        self.num_total_contacts = 25
        self.contact_ids = []
        # Ensure contacts are added in a predictable order for name-based assertions
        for i in range(self.num_total_contacts):
            contact_data = {'name': f'Contact {i:02d}', 'email': f'contact{i:02d}@example.com'}
            contact_id = db_manager.add_contact(contact_data)
            self.assertIsNotNone(contact_id, f"Failed to create contact {i}")
            self.contact_ids.append(contact_id)
            link_id = db_manager.link_contact_to_client(self.test_client_id, contact_id)
            self.assertIsNotNone(link_id, f"Failed to link contact {i} to client")

    def tearDown(self):
        # self.conn.close() # Connection is managed per function call in db_manager or per test in setUp
        pass

    def test_get_all_contacts_no_limit(self):
        contacts = db_manager.get_contacts_for_client(self.test_client_id)
        self.assertEqual(len(contacts), self.num_total_contacts)
        # Verify names to ensure order (get_contacts_for_client has ORDER BY c.name)
        retrieved_names = [c['name'] for c in contacts] # Already sorted by SQL
        expected_names = [f'Contact {i:02d}' for i in range(self.num_total_contacts)]
        self.assertListEqual(retrieved_names, expected_names)

    def test_get_contacts_with_limit(self):
        limit = 10
        contacts = db_manager.get_contacts_for_client(self.test_client_id, limit=limit)
        self.assertEqual(len(contacts), limit)
        # Assuming ORDER BY c.name in get_contacts_for_client
        self.assertEqual(contacts[0]['name'], 'Contact 00')
        self.assertEqual(contacts[limit-1]['name'], f'Contact {limit-1:02d}')


    def test_get_contacts_with_limit_and_offset(self):
        limit = 10
        offset = 5
        contacts = db_manager.get_contacts_for_client(self.test_client_id, limit=limit, offset=offset)
        self.assertEqual(len(contacts), limit)
        # Assuming ORDER BY c.name
        self.assertEqual(contacts[0]['name'], f'Contact {offset:02d}') # First contact of this page
        self.assertEqual(contacts[limit-1]['name'], f'Contact {offset + limit - 1:02d}') # Last contact of this page

    def test_get_contacts_limit_greater_than_total(self):
        limit = self.num_total_contacts + 5
        contacts = db_manager.get_contacts_for_client(self.test_client_id, limit=limit)
        self.assertEqual(len(contacts), self.num_total_contacts)

    def test_get_contacts_offset_out_of_bounds(self):
        limit = 10
        offset = self.num_total_contacts
        contacts = db_manager.get_contacts_for_client(self.test_client_id, limit=limit, offset=offset)
        self.assertEqual(len(contacts), 0)

        offset_way_out = self.num_total_contacts + 100
        contacts_way_out = db_manager.get_contacts_for_client(self.test_client_id, limit=limit, offset=offset_way_out)
        self.assertEqual(len(contacts_way_out), 0)

    def test_get_contacts_limit_zero(self):
        contacts = db_manager.get_contacts_for_client(self.test_client_id, limit=0)
        self.assertEqual(len(contacts), 0)


class TestCarrierEmailDB(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_db_name = ":memory:"
        # No need to remove file for :memory: db

        db_manager.connection.set_test_db_path_override(cls.test_db_name)
        db_manager.initialize_database(db_path_to_use=cls.test_db_name)

    @classmethod
    def tearDownClass(cls):
        db_manager.connection.clear_test_db_path_override()
        # No need to remove file for :memory: db

    def setUp(self):
        # get_db_connection will use the override path.
        conn = db_manager.get_db_connection()
        cursor = conn.cursor()
        cursor = conn.cursor()

        # Comprehensive deletion order (same as above, ensure consistency)
        cursor.execute("DELETE FROM SAVTickets")
        cursor.execute("DELETE FROM proforma_invoices")
        cursor.execute("DELETE FROM Invoices")
        cursor.execute("DELETE FROM ClientProjectProducts")
        cursor.execute("DELETE FROM Tasks")
        cursor.execute("DELETE FROM KPIs")
        cursor.execute("DELETE FROM Projects")
        cursor.execute("DELETE FROM ClientDocuments")
        cursor.execute("DELETE FROM ImportantDates")
        cursor.execute("DELETE FROM Templates")
        cursor.execute("DELETE FROM ClientContacts")
        cursor.execute("DELETE FROM CompanyPersonnelContacts")
        cursor.execute("DELETE FROM ContactListMembers")
        cursor.execute("DELETE FROM PartnerContacts")
        cursor.execute("DELETE FROM ClientNotes")
        cursor.execute("DELETE FROM Client_AssignedPersonnel")
        cursor.execute("DELETE FROM Client_Transporters") # Specific to TestCarrierEmailDB
        cursor.execute("DELETE FROM Client_FreightForwarders")
        cursor.execute("DELETE FROM ClientOrder_MoneyTransferAgents")
        cursor.execute("DELETE FROM CoverPages")
        cursor.execute("DELETE FROM ActivityLog WHERE related_client_id IS NOT NULL")

        cursor.execute("DELETE FROM Contacts")
        cursor.execute("DELETE FROM Transporters") # Specific to TestCarrierEmailDB
        cursor.execute("DELETE FROM Clients")
        # Other tables as needed

        conn.commit()
        conn.close()

        # Add a test client
        # db_manager.add_client will use get_db_connection which respects the override
        self.client_id = db_manager.add_client({'client_name': 'Test Client for Carrier Email', 'project_identifier': 'CARRIER_EMAIL_TEST'})
        self.assertIsNotNone(self.client_id, "Failed to create test client for carrier email tests")

        # Add a test transporter
        self.transporter_id = db_manager.add_transporter({'name': 'Test Transporter'})
        self.assertIsNotNone(self.transporter_id, "Failed to create test transporter")

    def test_assign_transporter_default_email_status(self):
        """Test that assigning a transporter defaults email_status to 'Pending'."""
        assignment_id = db_manager.assign_transporter_to_client(self.client_id, self.transporter_id, "Details", 100.0)
        self.assertIsNotNone(assignment_id, "Failed to assign transporter to client")

        assigned_transporters = db_manager.get_assigned_transporters_for_client(self.client_id)
        self.assertEqual(len(assigned_transporters), 1)
        self.assertEqual(assigned_transporters[0]['email_status'], 'Pending')
        self.assertEqual(assigned_transporters[0]['client_transporter_id'], assignment_id)


    def test_update_client_transporter_email_status(self):
        """Test updating the email_status of a client-transporter assignment."""
        assignment_id = db_manager.assign_transporter_to_client(self.client_id, self.transporter_id, "Initial Details", 200.0)
        self.assertIsNotNone(assignment_id, "Failed to assign transporter for status update test")

        # Update status to "Sent"
        update_success_sent = db_manager.update_client_transporter_email_status(assignment_id, "Sent")
        self.assertTrue(update_success_sent, "Failed to update email_status to Sent")

        assigned_transporters_sent = db_manager.get_assigned_transporters_for_client(self.client_id)
        self.assertEqual(len(assigned_transporters_sent), 1)
        self.assertEqual(assigned_transporters_sent[0]['email_status'], "Sent")

        # Update status to "Failed"
        update_success_failed = db_manager.update_client_transporter_email_status(assignment_id, "Failed")
        self.assertTrue(update_success_failed, "Failed to update email_status to Failed")

        assigned_transporters_failed = db_manager.get_assigned_transporters_for_client(self.client_id)
        self.assertEqual(len(assigned_transporters_failed), 1)
        self.assertEqual(assigned_transporters_failed[0]['email_status'], "Failed")

        # Test updating a non-existent assignment_id
        non_existent_id = 99999
        update_fail_non_existent = db_manager.update_client_transporter_email_status(non_existent_id, "Sent")
        self.assertFalse(update_fail_non_existent, "Update should fail for non-existent assignment ID")


    def test_get_assigned_transporters_includes_email_status(self):
        """Test that get_assigned_transporters_for_client includes the email_status field."""
        assignment_id = db_manager.assign_transporter_to_client(self.client_id, self.transporter_id, "Details for get test", 300.0)
        self.assertIsNotNone(assignment_id)

        # First check: Default status
        assigned_transporters = db_manager.get_assigned_transporters_for_client(self.client_id)
        self.assertEqual(len(assigned_transporters), 1)
        self.assertIn('email_status', assigned_transporters[0])
        self.assertEqual(assigned_transporters[0]['email_status'], 'Pending')

        # Update status and check again
        db_manager.update_client_transporter_email_status(assignment_id, "CustomStatus")
        assigned_transporters_updated = db_manager.get_assigned_transporters_for_client(self.client_id)
        self.assertEqual(len(assigned_transporters_updated), 1)
        self.assertIn('email_status', assigned_transporters_updated[0])
        self.assertEqual(assigned_transporters_updated[0]['email_status'], 'CustomStatus')


if __name__ == '__main__':
    # This allows running the tests directly from this file
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
