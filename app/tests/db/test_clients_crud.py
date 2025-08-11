import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os
from datetime import datetime

import logging
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Import the new models
from app.db.models import Base, Client, StatusSetting, User
# Import the instance for testing
from app.db.cruds.clients_crud import clients_crud_instance

# Helper for date formatting consistent with the app
def format_datetime_for_db(dt_obj):
    return dt_obj.isoformat() + "Z"

class TestClientsCRUD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        logging.disable(logging.NOTSET)

    def setUp(self):
        # Use an in-memory SQLite database for tests
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

        # Use the global instance for tests
        self.clients_crud = clients_crud_instance

        # Sample data
        self.user_id1 = "user_test_1"
        self.user1 = User(user_id=self.user_id1, username='testuser1', email='test1@example.com', hashed_password='123')
        self.session.add(self.user1)
        self.session.commit()

        self.client_data1 = {
            'client_name': 'Test Client 1',
            'created_by_user_id': self.user_id1,
            'price': 100.50,
            'company_name': 'Test Company A',
            'category': 'Test Category'
        }
        self.client_data2 = {
            'client_name': 'Test Client 2',
            'created_by_user_id': 'user_test_2',
            'price': 200.75
        }

    def tearDown(self):
        self.session.close()
        Base.metadata.drop_all(self.engine)

    @patch('db.cruds.clients_crud.status_service')
    def test_add_client_success(self, mock_status_service):
        # Mock the status service to return dummy IDs
        mock_status_service.get_default_status_for_commande_creation.return_value.status_id = 1
        mock_status_service.get_default_status_for_type.return_value.status_id = 1

        result = self.clients_crud.add_client(self.client_data1, conn=self.session)
        self.assertTrue(result['success'])
        self.assertIsNotNone(result.get('client_id'))
        client_id = result['client_id']

        # Verify in DB
        db_client = self.session.query(Client).filter_by(client_id=client_id).first()
        self.assertIsNotNone(db_client)
        self.assertEqual(db_client.client_name, self.client_data1['client_name'])
        self.assertEqual(db_client.is_deleted, 0)

        # Verify that a default order and project were created
        from db.models import Commande, Project
        default_order = self.session.query(Commande).filter_by(client_id=client_id, is_default=True).first()
        self.assertIsNotNone(default_order)
        default_project = self.session.query(Project).filter_by(client_id=client_id).first()
        self.assertIsNotNone(default_project)
        self.assertEqual(default_order.project_id, default_project.project_id)

    def test_add_client_missing_required_field(self):
        invalid_data = self.client_data1.copy()
        del invalid_data['client_name']
        result = self.clients_crud.add_client(invalid_data, conn=self.session)
        self.assertFalse(result['success'])
        self.assertIn("Missing required field: client_name", result['error'])

    def test_add_client_invalid_price_type(self):
        invalid_data = self.client_data1.copy()
        invalid_data['price'] = "not_a_number"
        result = self.clients_crud.add_client(invalid_data, conn=self.session)
        self.assertFalse(result['success'])
        self.assertIn("Invalid data type for price", result['error'])

    def test_get_client_by_id_exists(self):
        add_result = self.clients_crud.add_client(self.client_data1, conn=self.session)
        client_id = add_result['client_id']

        client = self.clients_crud.get_client_by_id(client_id, conn=self.session)
        self.assertIsNotNone(client)
        self.assertEqual(client['client_name'], self.client_data1['client_name'])

    def test_get_client_by_id_not_exists(self):
        client = self.clients_crud.get_client_by_id("non_existent_id", conn=self.session)
        self.assertIsNone(client)

    def test_soft_delete_client(self):
        add_result = self.clients_crud.add_client(self.client_data1, conn=self.session)
        client_id = add_result['client_id']

        delete_result = self.clients_crud.delete_client(client_id, conn=self.session)
        self.assertTrue(delete_result['success'])

        # Verify soft delete in DB
        db_client = self.session.query(Client).filter_by(client_id=client_id).first()
        self.assertIsNotNone(db_client)
        self.assertEqual(db_client.is_deleted, 1)
        self.assertIsNotNone(db_client.deleted_at)

        # Verify getter excludes soft-deleted by default
        client = self.clients_crud.get_client_by_id(client_id, conn=self.session)
        self.assertIsNone(client)

        # Verify getter includes soft-deleted when asked
        client_incl_deleted = self.clients_crud.get_client_by_id(client_id, conn=self.session, include_deleted=True)
        self.assertIsNotNone(client_incl_deleted)
        self.assertEqual(client_incl_deleted['client_name'], self.client_data1['client_name'])

    def test_delete_non_existent_client(self):
        delete_result = self.clients_crud.delete_client("non_existent_id", conn=self.session)
        self.assertFalse(delete_result['success'])
        self.assertIn("not found or already deleted", delete_result.get('error', ''))


    def test_get_all_clients(self):
        self.clients_crud.add_client(self.client_data1, conn=self.session)
        self.clients_crud.add_client(self.client_data2, conn=self.session)

        all_clients = self.clients_crud.get_all_clients(conn=self.session)
        self.assertEqual(len(all_clients), 2)

        # Test pagination
        paginated_clients = self.clients_crud.get_all_clients(conn=self.session, limit=1, offset=0)
        self.assertEqual(len(paginated_clients), 1)

        # Test soft delete filtering
        client1_id = self.session.query(Client).filter_by(client_name=self.client_data1['client_name']).first().client_id
        self.clients_crud.delete_client(client1_id, conn=self.session)

        all_active_clients = self.clients_crud.get_all_clients(conn=self.session)
        self.assertEqual(len(all_active_clients), 1)
        self.assertEqual(all_active_clients[0]['client_name'], self.client_data2['client_name'])

        all_clients_incl_deleted = self.clients_crud.get_all_clients(conn=self.session, include_deleted=True)
        self.assertEqual(len(all_clients_incl_deleted), 2)

    def test_get_all_clients_empty(self):
        clients = self.clients_crud.get_all_clients(conn=self.session)
        self.assertEqual(len(clients), 0)

    def test_update_client_success(self):
        add_result = self.clients_crud.add_client(self.client_data1, conn=self.session)
        client_id = add_result['client_id']

        update_data = {'client_name': 'Updated Name', 'price': 150.00}
        update_result = self.clients_crud.update_client(client_id, update_data, conn=self.session)
        self.assertTrue(update_result['success'])
        self.assertEqual(update_result['updated_count'], 1)

        updated_db_client = self.clients_crud.get_client_by_id(client_id, conn=self.session)
        self.assertEqual(updated_db_client['client_name'], 'Updated Name')
        self.assertEqual(updated_db_client['price'], 150.00)

    def test_update_client_non_existent(self):
        update_result = self.clients_crud.update_client("non_existent_id", {'client_name': 'New Name'}, conn=self.session)
        self.assertTrue(update_result['success'])
        self.assertEqual(update_result['updated_count'], 0)

    def test_update_client_invalid_data_type(self):
        add_result = self.clients_crud.add_client(self.client_data1, conn=self.session)
        client_id = add_result['client_id']

        update_data = {'price': 'not_a_valid_price'}
        update_result = self.clients_crud.update_client(client_id, update_data, conn=self.session)
        self.assertFalse(update_result['success'])
        self.assertIn("Invalid data type for price", update_result['error'])

    def test_add_client_note(self):
        add_client_res = self.clients_crud.add_client(self.client_data1, conn=self.session)
        client_id = add_client_res['client_id']

        note_text = "This is a test note."
        add_note_res = self.clients_crud.add_client_note(client_id, note_text, self.user_id1, conn=self.session)
        self.assertTrue(add_note_res['success'])
        self.assertIsNotNone(add_note_res['note_id'])

        notes = self.clients_crud.get_client_notes(client_id, conn=self.session)
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0]['note_text'], note_text)
        self.assertEqual(notes[0]['user_id'], self.user_id1)

    def test_get_client_notes_no_notes(self):
        add_client_res = self.clients_crud.add_client(self.client_data1, conn=self.session)
        client_id = add_client_res['client_id']
        notes = self.clients_crud.get_client_notes(client_id, conn=self.session)
        self.assertEqual(len(notes), 0)

    def _insert_client(self, client_id, created_at_dt, created_by_user_id="test_user", is_deleted=0, deleted_at_dt=None, status_id=None, client_name="Test Client"):
        new_client = Client(
            client_id=client_id,
            client_name=client_name,
            created_at=created_at_dt,
            updated_at=created_at_dt,
            created_by_user_id=created_by_user_id,
            is_deleted=is_deleted,
            deleted_at=deleted_at_dt,
            status_id=status_id
        )
        self.session.add(new_client)
        self.session.commit()

    def _insert_status_setting(self, status_id, status_name, status_type, is_archival_status):
        new_status = StatusSetting(
            status_id=status_id,
            status_name=status_name,
            status_type=status_type,
            is_archival_status=bool(is_archival_status)
        )
        self.session.add(new_status)
        self.session.commit()

    def test_get_clients_count_created_between_no_deleted(self):
        date_2023_01_15 = datetime(2023, 1, 15, 12, 0, 0)
        date_2023_02_10 = datetime(2023, 2, 10, 12, 0, 0)
        date_2023_03_05 = datetime(2023, 3, 5, 12, 0, 0)

        self._insert_client("client1", date_2023_01_15)
        self._insert_client("client2", date_2023_02_10)
        self._insert_client("client3", date_2023_02_10, is_deleted=1)
        self._insert_client("client4", date_2023_03_05)

        start_iso = format_datetime_for_db(datetime(2023, 2, 1, 0, 0, 0))
        end_iso = format_datetime_for_db(datetime(2023, 2, 28, 23, 59, 59))

        count = self.clients_crud.get_clients_count_created_between(start_iso, end_iso, conn=self.session, include_deleted=False)
        self.assertEqual(count, 1)

    def test_get_clients_count_created_between_with_deleted(self):
        date_2023_02_10 = datetime(2023, 2, 10, 12, 0, 0)
        self._insert_client("client2", date_2023_02_10)
        self._insert_client("client3", date_2023_02_10, is_deleted=1)

        start_iso = format_datetime_for_db(datetime(2023, 2, 1, 0, 0, 0))
        end_iso = format_datetime_for_db(datetime(2023, 2, 28, 23, 59, 59))

        count = self.clients_crud.get_clients_count_created_between(start_iso, end_iso, conn=self.session, include_deleted=True)
        self.assertEqual(count, 2)

    def test_get_clients_count_created_between_no_match(self):
        start_iso = format_datetime_for_db(datetime(2023, 4, 1, 0, 0, 0))
        end_iso = format_datetime_for_db(datetime(2023, 4, 30, 23, 59, 59))
        count = self.clients_crud.get_clients_count_created_between(start_iso, end_iso, conn=self.session)
        self.assertEqual(count, 0)

    def test_get_total_clients_count_up_to_date_basic(self):
        date_2023_01_10 = datetime(2023, 1, 10, 10, 0, 0)
        date_2023_02_15 = datetime(2023, 2, 15, 10, 0, 0)
        date_2023_03_20 = datetime(2023, 3, 20, 10, 0, 0)

        self._insert_client("c1", date_2023_01_10)
        self._insert_client("c2", date_2023_02_15)
        self._insert_client("c3", date_2023_02_15, is_deleted=1, deleted_at_dt=datetime(2023, 3, 1, 0, 0, 0))
        self._insert_client("c4", datetime(2023, 3, 21, 0, 0, 0))
        self._insert_client("c5", date_2023_01_10, is_deleted=1, deleted_at_dt=date_2023_03_20)

        date_iso_end = format_datetime_for_db(date_2023_03_20)
        count = self.clients_crud.get_total_clients_count_up_to_date(date_iso_end, conn=self.session)
        self.assertEqual(count, 3)

    def test_get_total_clients_count_up_to_date_includes_deleted_after_target(self):
        self._insert_client("c1", datetime(2023,1,1,10,0,0), is_deleted=1, deleted_at_dt=datetime(2023,3,1,10,0,0))
        date_iso_end = format_datetime_for_db(datetime(2023,2,1,10,0,0))
        count = self.clients_crud.get_total_clients_count_up_to_date(date_iso_end, conn=self.session)
        self.assertEqual(count, 1)

    def test_get_total_clients_count_up_to_date_excludes_deleted_before_target(self):
        self._insert_client("c1", datetime(2023,1,1,10,0,0), is_deleted=1, deleted_at_dt=datetime(2023,1,15,10,0,0))
        date_iso_end = format_datetime_for_db(datetime(2023,2,1,10,0,0))
        count = self.clients_crud.get_total_clients_count_up_to_date(date_iso_end, conn=self.session)
        self.assertEqual(count, 0)

    def test_get_active_clients_count_up_to_date_basic(self):
        active_status_id = "status_active"
        archival_status_id = "status_archival"
        self._insert_status_setting(active_status_id, "Active", "Client", 0)
        self._insert_status_setting(archival_status_id, "Archived", "Client", 1)

        date_target = datetime(2023, 3, 15, 0, 0, 0)

        self._insert_client("active1", datetime(2023, 1, 1), status_id=active_status_id)
        self._insert_client("active2", datetime(2023, 1, 5))
        self._insert_client("archived1", datetime(2023, 1, 10), status_id=archival_status_id)
        self._insert_client("active_later", datetime(2023, 4, 1), status_id=active_status_id)
        self._insert_client("active_then_deleted", datetime(2023, 1, 15), status_id=active_status_id, is_deleted=1, deleted_at_dt=datetime(2023, 2, 1))
        self._insert_client("active_deleted_later", datetime(2023, 1, 20), status_id=active_status_id, is_deleted=1, deleted_at_dt=datetime(2023, 4, 1))

        date_iso_end = format_datetime_for_db(date_target)
        count = self.clients_crud.get_active_clients_count_up_to_date(date_iso_end, conn=self.session)
        self.assertEqual(count, 3)

if __name__ == '__main__':
    unittest.main()
