import unittest
import sqlite3
import os
import uuid
from datetime import datetime

# Adjust path to import from the project root
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from db import initialize_database, get_db_connection
from db.cruds import notes_crud
from db.cruds import client_documents_crud # For setting up related data
from db.cruds import commandes_crud # For setting up related data

# Use an in-memory database for testing
TEST_DB_PATH = ":memory:"
# TEST_DB_PATH = "test_notes_crud.db" # Use a file for inspection if needed

class TestNotesCrud(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up the database schema once for all tests."""
        # Override DATABASE_PATH for testing
        cls.original_db_path = None
        if 'config' in sys.modules:
            if hasattr(sys.modules['config'], 'DATABASE_PATH'):
                cls.original_db_path = sys.modules['config'].DATABASE_PATH
            sys.modules['config'].DATABASE_PATH = TEST_DB_PATH

        initialize_database()

    @classmethod
    def tearDownClass(cls):
        """Restore original DB path and clean up test DB file if created."""
        if cls.original_db_path and 'config' in sys.modules:
            sys.modules['config'].DATABASE_PATH = cls.original_db_path

        if TEST_DB_PATH != ":memory:" and os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

    def setUp(self):
        """Set up a clean database connection and cursor for each test."""
        self.conn = get_db_connection(db_path=TEST_DB_PATH)
        self.conn.execute("DELETE FROM DefaultDocumentNotes")
        self.conn.execute("DELETE FROM CommandeDocumentNotes")
        self.conn.execute("DELETE FROM ClientDocuments")
        self.conn.execute("DELETE FROM Commandes")
        # Add other necessary table cleanups if they affect tests
        self.conn.commit()

    def tearDown(self):
        """Close the database connection after each test."""
        if self.conn:
            self.conn.close()

    # --- DefaultDocumentNotes Tests ---
    def test_add_and_get_default_document_note(self):
        note_id = notes_crud.add_default_document_note("proforma", "fr", "Note proforma FR.")
        self.assertIsNotNone(note_id)

        retrieved_note = notes_crud.get_default_document_note("proforma", "fr")
        self.assertIsNotNone(retrieved_note)
        self.assertEqual(retrieved_note['document_type'], "proforma")
        self.assertEqual(retrieved_note['language_code'], "fr")
        self.assertEqual(retrieved_note['note_content'], "Note proforma FR.")

        # Test getting non-existent note
        non_existent = notes_crud.get_default_document_note("invoice", "en")
        self.assertIsNone(non_existent)

    def test_add_default_document_note_unique_constraint(self):
        notes_crud.add_default_document_note("proforma", "fr", "Note 1")
        note_id_duplicate = notes_crud.add_default_document_note("proforma", "fr", "Note 2")
        self.assertIsNone(note_id_duplicate, "Should not add duplicate (doc_type, lang_code)")

    def test_update_default_document_note(self):
        note_id = notes_crud.add_default_document_note("proforma", "en", "Original EN note.")
        self.assertIsNotNone(note_id)

        success = notes_crud.update_default_document_note(note_id, note_content="Updated EN note.")
        self.assertTrue(success)

        updated_note = notes_crud.get_default_document_note("proforma", "en") # Assuming type/lang didn't change
        self.assertEqual(updated_note['note_content'], "Updated EN note.")
        self.assertIsNotNone(updated_note['updated_at'])

        # Test updating non-existent ID
        success_non_existent = notes_crud.update_default_document_note(99999, note_content="Test")
        self.assertFalse(success_non_existent)

    def test_delete_default_document_note(self):
        note_id = notes_crud.add_default_document_note("packing_list", "es", "Lista de empaque.")
        self.assertIsNotNone(note_id)

        success = notes_crud.delete_default_document_note(note_id)
        self.assertTrue(success)
        self.assertIsNone(notes_crud.get_default_document_note("packing_list", "es"))

        success_non_existent = notes_crud.delete_default_document_note(99999)
        self.assertFalse(success_non_existent)

    def test_list_default_document_notes(self):
        notes_crud.add_default_document_note("type1", "fr", "Note 1 FR")
        notes_crud.add_default_document_note("type1", "en", "Note 1 EN")
        notes_crud.add_default_document_note("type2", "fr", "Note 2 FR")

        all_notes = notes_crud.list_default_document_notes()
        self.assertEqual(len(all_notes), 3)
        # Check order if important (by document_type, then language_code)
        self.assertEqual(all_notes[0]['document_type'], 'type1')
        self.assertEqual(all_notes[0]['language_code'], 'en') # 'en' comes before 'fr'

    # --- CommandeDocumentNotes Tests ---
    def _setup_related_data(self):
        # Helper to create a client document and commande for tests
        client_id = str(uuid.uuid4()) # Assuming Client table is not strictly needed for these tests

        # Minimal Commande (Order) setup - only if list_commande_document_notes_for_commande is tested here
        commande_id = str(uuid.uuid4())
        # We need a status_id for Commande. Fetch or insert a dummy one.
        # For simplicity, assume a status_id=1 exists or this part is mocked.
        # This setup can become complex if full FK integrity is enforced and tested.
        # For now, focusing on notes_crud, so related data setup is minimal.

        # ClientDocument setup
        doc_id = str(uuid.uuid4())
        doc_data = {
            'document_id': doc_id, 'client_id': client_id,
            'document_name': 'Test Proforma', 'file_name_on_disk': 'test_proforma.pdf',
            'file_path_relative': 'fr/test_proforma.pdf', 'document_type_generated': 'PROFORMA_PDF',
            'language_code': 'fr', 'user_id': 'test_user',
            'commande_id': commande_id # Link to the commande
        }
        client_documents_crud.add_client_document(doc_data, conn=self.conn) # Use self.conn
        return doc_id, commande_id


    def test_add_and_get_commande_document_note(self):
        doc_id, _ = self._setup_related_data()
        note_id = notes_crud.add_commande_document_note(doc_id, "Custom note for this doc.", "fr")
        self.assertIsNotNone(note_id)

        retrieved = notes_crud.get_commande_document_note(doc_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['commande_document_id'], doc_id)
        self.assertEqual(retrieved['note_content'], "Custom note for this doc.")
        self.assertEqual(retrieved['language_code'], "fr")

    def test_add_commande_document_note_unique_constraint(self):
        doc_id, _ = self._setup_related_data()
        notes_crud.add_commande_document_note(doc_id, "Note 1", "fr")
        note_id_duplicate = notes_crud.add_commande_document_note(doc_id, "Note 2", "fr")
        self.assertIsNone(note_id_duplicate, "Should not add duplicate for commande_document_id")

    def test_update_commande_document_note(self):
        doc_id, _ = self._setup_related_data()
        note_id = notes_crud.add_commande_document_note(doc_id, "Original custom note", "fr")

        # Update by ID
        success_by_id = notes_crud.update_commande_document_note(note_id=note_id, note_content="Updated by ID")
        self.assertTrue(success_by_id)
        updated1 = notes_crud.get_commande_document_note(doc_id)
        self.assertEqual(updated1['note_content'], "Updated by ID")

        # Update by commande_document_id
        success_by_doc_id = notes_crud.update_commande_document_note(commande_document_id=doc_id, note_content="Updated by Doc ID", language_code="en")
        self.assertTrue(success_by_doc_id)
        updated2 = notes_crud.get_commande_document_note(doc_id)
        self.assertEqual(updated2['note_content'], "Updated by Doc ID")
        self.assertEqual(updated2['language_code'], "en") # Language also updated

    def test_upsert_commande_document_note(self):
        doc_id, _ = self._setup_related_data()

        # Test insert
        upsert_id1 = notes_crud.upsert_commande_document_note(doc_id, "First upsert (insert)", "fr")
        self.assertIsNotNone(upsert_id1)
        note1 = notes_crud.get_commande_document_note(doc_id)
        self.assertEqual(note1['note_content'], "First upsert (insert)")

        # Test update
        upsert_id2 = notes_crud.upsert_commande_document_note(doc_id, "Second upsert (update)", "fr")
        self.assertIsNotNone(upsert_id2)
        self.assertEqual(upsert_id1, upsert_id2) # Should be the same DB row ID
        note2 = notes_crud.get_commande_document_note(doc_id)
        self.assertEqual(note2['note_content'], "Second upsert (update)")

    def test_delete_commande_document_note(self):
        doc_id, _ = self._setup_related_data()
        note_id = notes_crud.add_commande_document_note(doc_id, "To be deleted", "fr")
        self.assertIsNotNone(note_id)

        # Delete by note_id
        success_by_id = notes_crud.delete_commande_document_note(note_id=note_id)
        self.assertTrue(success_by_id)
        self.assertIsNone(notes_crud.get_commande_document_note(doc_id))

        # Re-add and delete by commande_document_id
        notes_crud.add_commande_document_note(doc_id, "To be deleted again", "fr")
        success_by_doc_id = notes_crud.delete_commande_document_note(commande_document_id=doc_id)
        self.assertTrue(success_by_doc_id)
        self.assertIsNone(notes_crud.get_commande_document_note(doc_id))

    # --- get_effective_document_note Tests ---
    def test_get_effective_document_note(self):
        doc_id, _ = self._setup_related_data() # Creates ClientDocument with type PROFORMA_PDF, lang fr
        doc_type = "PROFORMA_PDF"
        lang_code = "fr"

        # Scenario 1: Only default note exists
        notes_crud.add_default_document_note(doc_type, lang_code, "Default French Proforma Note")
        effective1 = notes_crud.get_effective_document_note(doc_id, doc_type, lang_code)
        self.assertEqual(effective1, "Default French Proforma Note")

        # Scenario 2: Custom note exists (should override default)
        notes_crud.add_commande_document_note(doc_id, "Custom Note for this specific document", lang_code)
        effective2 = notes_crud.get_effective_document_note(doc_id, doc_type, lang_code)
        self.assertEqual(effective2, "Custom Note for this specific document")

        # Scenario 3: No custom, no default for this lang, but default for other lang
        notes_crud.delete_commande_document_note(commande_document_id=doc_id) # Remove custom
        notes_crud.add_default_document_note(doc_type, "en", "Default English Proforma Note")
        effective3 = notes_crud.get_effective_document_note(doc_id, doc_type, "de") # Request German
        self.assertIsNone(effective3, "Should be None if no specific lang and no fallback logic for lang")

        # Scenario 4: No custom, default for specific lang exists
        effective4 = notes_crud.get_effective_document_note(doc_id, doc_type, "en")
        self.assertEqual(effective4, "Default English Proforma Note")

        # Scenario 5: No notes at all
        notes_crud.delete_default_document_note(notes_crud.get_default_document_note(doc_type, lang_code)['id'])
        notes_crud.delete_default_document_note(notes_crud.get_default_document_note(doc_type, "en")['id'])
        effective5 = notes_crud.get_effective_document_note(doc_id, "unknown_type", "xx")
        self.assertIsNone(effective5)

    # Test for list_commande_document_notes_for_commande (requires more setup)
    def test_list_commande_document_notes_for_commande(self):
        # Setup: 2 commandes, each with some documents, some of which have custom notes.
        client_id = str(uuid.uuid4())

        # Commande 1
        cmd1_id = str(uuid.uuid4())
        # Assume status_id 1 exists or is not strictly enforced for this test's focus
        commandes_crud.add_commande({'commande_id': cmd1_id, 'client_id': client_id, 'commande_reference': 'CMD001', 'status_commande_id': 1}, conn=self.conn)

        doc1_cmd1_id = str(uuid.uuid4())
        client_documents_crud.add_client_document({'document_id': doc1_cmd1_id, 'client_id': client_id, 'commande_id': cmd1_id, 'document_name': 'Doc1Cmd1', 'file_name_on_disk':'d1c1.pdf', 'file_path_relative':'d1c1.pdf'}, conn=self.conn)
        notes_crud.add_commande_document_note(doc1_cmd1_id, "Note for Doc1 on Cmd1", "fr", conn=self.conn)

        doc2_cmd1_id = str(uuid.uuid4())
        client_documents_crud.add_client_document({'document_id': doc2_cmd1_id, 'client_id': client_id, 'commande_id': cmd1_id, 'document_name': 'Doc2Cmd1', 'file_name_on_disk':'d2c1.pdf', 'file_path_relative':'d2c1.pdf'}, conn=self.conn)
        # Doc2 on Cmd1 has no custom note

        # Commande 2
        cmd2_id = str(uuid.uuid4())
        commandes_crud.add_commande({'commande_id': cmd2_id, 'client_id': client_id, 'commande_reference': 'CMD002', 'status_commande_id': 1}, conn=self.conn)
        doc1_cmd2_id = str(uuid.uuid4())
        client_documents_crud.add_client_document({'document_id': doc1_cmd2_id, 'client_id': client_id, 'commande_id': cmd2_id, 'document_name': 'Doc1Cmd2', 'file_name_on_disk':'d1c2.pdf', 'file_path_relative':'d1c2.pdf'}, conn=self.conn)
        notes_crud.add_commande_document_note(doc1_cmd2_id, "Note for Doc1 on Cmd2", "en", conn=self.conn)

        # Test listing notes for Commande 1
        cmd1_notes = notes_crud.list_commande_document_notes_for_commande(cmd1_id, conn=self.conn)
        self.assertEqual(len(cmd1_notes), 1)
        self.assertEqual(cmd1_notes[0]['commande_document_id'], doc1_cmd1_id)
        self.assertEqual(cmd1_notes[0]['note_content'], "Note for Doc1 on Cmd1")

        # Test listing notes for Commande 2
        cmd2_notes = notes_crud.list_commande_document_notes_for_commande(cmd2_id, conn=self.conn)
        self.assertEqual(len(cmd2_notes), 1)
        self.assertEqual(cmd2_notes[0]['commande_document_id'], doc1_cmd2_id)

        # Test listing for a commande with no custom notes
        cmd3_id = str(uuid.uuid4())
        commandes_crud.add_commande({'commande_id': cmd3_id, 'client_id': client_id, 'commande_reference': 'CMD003', 'status_commande_id': 1}, conn=self.conn)
        doc1_cmd3_id = str(uuid.uuid4())
        client_documents_crud.add_client_document({'document_id': doc1_cmd3_id, 'client_id': client_id, 'commande_id': cmd3_id, 'document_name': 'Doc1Cmd3', 'file_name_on_disk':'d1c3.pdf', 'file_path_relative':'d1c3.pdf'}, conn=self.conn)
        cmd3_notes = notes_crud.list_commande_document_notes_for_commande(cmd3_id, conn=self.conn)
        self.assertEqual(len(cmd3_notes), 0)

if __name__ == '__main__':
    # Ensure config.DATABASE_PATH is set to TEST_DB_PATH before running tests
    # This is now handled in setUpClass
    unittest.main()
