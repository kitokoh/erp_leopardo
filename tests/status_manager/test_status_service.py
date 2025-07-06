import unittest
from unittest.mock import patch, MagicMock

# Assuming status_manager and db.cruds are in PYTHONPATH
from status_manager.status_models import Status, StatusType
from status_manager import status_service

# Mock data for status_settings_crud responses
MOCK_DB_STATUS_ROW_CLIENT_PROSPECT = {
    "status_id": 1, "status_name": "Prospect", "status_type": "Client",
    "color_hex": "#ABCDEF", "sort_order": 10, "is_archival_status": 0, "icon_name": "icon_prospect"
}
MOCK_DB_STATUS_ROW_CLIENT_ACTIVE = {
    "status_id": 2, "status_name": "Actif", "status_type": "Client",
    "color_hex": "#123456", "sort_order": 20, "is_archival_status": 0, "icon_name": "icon_active"
}
MOCK_DB_STATUS_ROW_CLIENT_ARCHIVED = {
    "status_id": 3, "status_name": "Archivé", "status_type": "Client",
    "color_hex": "#CCCCCC", "sort_order": 100, "is_archival_status": 1, "icon_name": "icon_archived"
}
MOCK_DB_STATUS_ROW_COMMANDE_BROUILLON = {
    "status_id": 10, "status_name": "Brouillon", "status_type": "Commande",
    "color_hex": "#DEDEDE", "sort_order": 5, "is_archival_status": 0, "icon_name": "icon_draft"
}
MOCK_DB_STATUS_ROW_COMMANDE_LIVREE = {
    "status_id": 11, "status_name": "Livrée", "status_type": "Commande",
    "color_hex": "#00FF00", "sort_order": 50, "is_archival_status": 0, "icon_name": "icon_delivered"
}
MOCK_DB_STATUS_ROW_PROJECT_PLANNING = {
    "status_id": 20, "status_name": "Planning", "status_type": "Project",
    "color_hex": "#FFA500", "sort_order": 1, "is_archival_status": 0, "icon_name": "icon_planning"
}

ALL_MOCK_DB_STATUSES = [
    MOCK_DB_STATUS_ROW_CLIENT_PROSPECT, MOCK_DB_STATUS_ROW_CLIENT_ACTIVE, MOCK_DB_STATUS_ROW_CLIENT_ARCHIVED,
    MOCK_DB_STATUS_ROW_COMMANDE_BROUILLON, MOCK_DB_STATUS_ROW_COMMANDE_LIVREE, MOCK_DB_STATUS_ROW_PROJECT_PLANNING
]

# Patch status_settings_crud, clients_crud, and commandes_crud at the module level where status_service imports them
@patch('status_manager.status_service.status_settings_crud', autospec=True)
@patch('status_manager.status_service.clients_crud', autospec=True) # Not directly used yet, but for future is_status_in_use expansion
@patch('status_manager.status_service.commandes_crud', autospec=True) # Not directly used yet, but for future is_status_in_use expansion
class TestStatusService(unittest.TestCase):

    def test_get_status_by_id(self, mock_commandes_crud, mock_clients_crud, mock_ssc):
        mock_ssc.get_status_setting_by_id.return_value = MOCK_DB_STATUS_ROW_CLIENT_PROSPECT.copy()

        status = status_service.get_status_by_id(1)

        mock_ssc.get_status_setting_by_id.assert_called_once_with(1)
        self.assertIsNotNone(status)
        self.assertIsInstance(status, Status)
        self.assertEqual(status.status_id, 1)
        self.assertEqual(status.name, "Prospect")
        self.assertEqual(status.type, StatusType.CLIENT)
        self.assertEqual(status.color_hex, "#ABCDEF")
        self.assertEqual(status.sort_order, 10)
        self.assertFalse(status.is_archival) # is_archival_status: 0
        self.assertEqual(status.icon_name, "icon_prospect")

    def test_get_status_by_id_not_found(self, mock_commandes_crud, mock_clients_crud, mock_ssc):
        mock_ssc.get_status_setting_by_id.return_value = None
        status = status_service.get_status_by_id(999)
        mock_ssc.get_status_setting_by_id.assert_called_once_with(999)
        self.assertIsNone(status)

    def test_get_statuses_by_type(self, mock_commandes_crud, mock_clients_crud, mock_ssc):
        mock_ssc.get_all_status_settings.return_value = [
            MOCK_DB_STATUS_ROW_CLIENT_PROSPECT.copy(),
            MOCK_DB_STATUS_ROW_CLIENT_ACTIVE.copy()
        ]

        statuses = status_service.get_statuses_by_type(StatusType.CLIENT)

        mock_ssc.get_all_status_settings.assert_called_once_with(type_filter="Client")
        self.assertEqual(len(statuses), 2)
        self.assertTrue(all(isinstance(s, Status) for s in statuses))
        self.assertEqual(statuses[0].name, "Prospect")
        self.assertEqual(statuses[1].name, "Actif")

    def test_get_statuses_by_type_string_filter(self, mock_commandes_crud, mock_clients_crud, mock_ssc):
        mock_ssc.get_all_status_settings.return_value = [MOCK_DB_STATUS_ROW_COMMANDE_BROUILLON.copy()]

        statuses = status_service.get_statuses_by_type(StatusType.COMMANDE, type_filter_string="Commande")

        mock_ssc.get_all_status_settings.assert_called_once_with(type_filter="Commande")
        self.assertEqual(len(statuses), 1)
        self.assertEqual(statuses[0].name, "Brouillon")

    def test_get_all_statuses(self, mock_commandes_crud, mock_clients_crud, mock_ssc):
        mock_ssc.get_all_status_settings.return_value = [r.copy() for r in ALL_MOCK_DB_STATUSES]

        statuses = status_service.get_all_statuses()

        mock_ssc.get_all_status_settings.assert_called_once_with() # No filter
        self.assertEqual(len(statuses), len(ALL_MOCK_DB_STATUSES))
        self.assertTrue(all(isinstance(s, Status) for s in statuses))

    def test_add_status(self, mock_commandes_crud, mock_clients_crud, mock_ssc):
        # Mock the add_status_setting to return the new ID
        mock_ssc.add_status_setting.return_value = 123 # New status_id
        # Mock get_status_setting_by_id for the re-fetch after add
        new_status_data_from_db = {
            "status_id": 123, "status_name": "New Task Status", "status_type": "Task",
            "color_hex": "#000000", "sort_order": 5, "is_archival_status": 0, "icon_name": "task_new"
        }
        mock_ssc.get_status_setting_by_id.return_value = new_status_data_from_db

        added_status = status_service.add_status(
            name="New Task Status",
            type=StatusType.TASK,
            color_hex="#000000",
            sort_order=5,
            is_archival=False, # Note: is_archival & icon_name currently not passed to CRUD by service
            icon_name="task_new"
        )

        # Verify add_status_setting was called (even if it doesn't use all fields yet)
        mock_ssc.add_status_setting.assert_called_once_with(
            status_name="New Task Status",
            status_type="Task", # Enum value
            color_hex="#000000",
            sort_order=5
        )
        # Verify get_status_setting_by_id was called to fetch the new status
        mock_ssc.get_status_setting_by_id.assert_called_once_with(123)

        self.assertIsNotNone(added_status)
        self.assertEqual(added_status.status_id, 123)
        self.assertEqual(added_status.name, "New Task Status")
        # The actual is_archival and icon_name would depend on whether the add_status_setting
        # and subsequent get_status_setting_by_id mock included them.
        # Our get_status_setting_by_id mock *does* include them.
        self.assertFalse(added_status.is_archival)
        self.assertEqual(added_status.icon_name, "task_new")


    def test_update_status(self, mock_commandes_crud, mock_clients_crud, mock_ssc):
        # Mock get_status_setting_by_id for the initial fetch in update_status
        mock_ssc.get_status_setting_by_id.return_value = MOCK_DB_STATUS_ROW_PROJECT_PLANNING.copy()
        # Mock update_status_setting to return True (success)
        mock_ssc.update_status_setting.return_value = True

        status_id_to_update = MOCK_DB_STATUS_ROW_PROJECT_PLANNING["status_id"]
        success = status_service.update_status(
            status_id=status_id_to_update,
            name="Project Execution",
            color_hex="#FF0000"
            # is_archival and icon_name are not passed to CRUD by service yet
        )

        self.assertTrue(success)
        mock_ssc.get_status_setting_by_id.assert_called_once_with(status_id_to_update)
        mock_ssc.update_status_setting.assert_called_once_with(
            status_id=status_id_to_update,
            status_name="Project Execution", # New name
            status_type=MOCK_DB_STATUS_ROW_PROJECT_PLANNING["status_type"], # Original type
            color_hex="#FF0000", # New color
            sort_order=None # Not updated, so service passes None
            # is_archival_status and icon_name would be here if service passed them
        )

    def test_update_status_only_is_archival(self, mock_commandes_crud, mock_clients_crud, mock_ssc):
        # This test highlights the current limitation: is_archival is not passed to CRUD by service.
        # To make this test pass as intended, status_service.update_status and
        # status_settings_crud.update_status_setting would need modification.

        current_status_db = MOCK_DB_STATUS_ROW_CLIENT_ACTIVE.copy()
        mock_ssc.get_status_setting_by_id.return_value = current_status_db
        mock_ssc.update_status_setting.return_value = True # Assume CRUD update is successful

        status_id_to_update = current_status_db["status_id"]
        success = status_service.update_status(
            status_id=status_id_to_update,
            is_archival=True # Attempting to change only this
        )
        self.assertTrue(success)
        mock_ssc.update_status_setting.assert_called_once_with(
            status_id=status_id_to_update,
            status_name=current_status_db["status_name"], # Original name
            status_type=current_status_db["status_type"], # Original type
            color_hex=None, # Not updated
            sort_order=None  # Not updated
            # TODO: When service is updated, this call should include is_archival_status=True
        )
        # Add a note about the current state of the code:
        print("\nNOTE: test_update_status_only_is_archival: `is_archival` is not currently passed "
              "to the CRUD layer by `status_service.update_status`. Test verifies current behavior.")


    def test_is_status_in_use_by_client(self, mock_commandes_crud, mock_clients_crud, mock_ssc):
        mock_ssc.is_status_in_use.return_value = True # Simulates in use by a client
        # Mock commandes_crud check (assuming it will be added and return False for this test)
        # For now, this part of the service logic is a TODO.
        # mock_commandes_crud.get_commandes_by_status_id.return_value = [] # Example if it returns a list

        self.assertTrue(status_service.is_status_in_use(1))
        mock_ssc.is_status_in_use.assert_called_once_with(1)
        # mock_commandes_crud.get_commandes_by_status_id.assert_called_once_with(1) # When implemented

    def test_is_status_in_use_not_by_client_nor_commande(self, mock_commandes_crud, mock_clients_crud, mock_ssc):
        mock_ssc.is_status_in_use.return_value = False # Not in use by client
        # mock_commandes_crud.get_commandes_by_status_id.return_value = [] # Not in use by commande

        self.assertFalse(status_service.is_status_in_use(1))
        mock_ssc.is_status_in_use.assert_called_once_with(1)
        # mock_commandes_crud.get_commandes_by_status_id.assert_called_once_with(1) # When implemented

    def test_delete_status_not_in_use(self, mock_commandes_crud, mock_clients_crud, mock_ssc):
        # is_status_in_use (via its components) returns False
        mock_ssc.is_status_in_use.return_value = False
        # mock_commandes_crud.get_commandes_by_status_id.return_value = []

        mock_ssc.delete_status_setting.return_value = True # Simulate successful deletion

        self.assertTrue(status_service.delete_status(1))
        mock_ssc.delete_status_setting.assert_called_once_with(1)

    def test_delete_status_in_use(self, mock_commandes_crud, mock_clients_crud, mock_ssc):
        mock_ssc.is_status_in_use.return_value = True # Simulate in use

        self.assertFalse(status_service.delete_status(1))
        mock_ssc.delete_status_setting.assert_not_called() # Should not be called if in use

    # --- Test Utility Functions ---
    def test_get_default_status_for_type(self, mock_commandes_crud, mock_clients_crud, mock_ssc):
        # Mock get_all_status_settings (called by get_statuses_by_type)
        mock_ssc.get_all_status_settings.return_value = [
            MOCK_DB_STATUS_ROW_CLIENT_PROSPECT.copy(), # sort_order 10
            MOCK_DB_STATUS_ROW_CLIENT_ACTIVE.copy()    # sort_order 20
        ]

        default_client_status = status_service.get_default_status_for_type(StatusType.CLIENT)
        self.assertIsNotNone(default_client_status)
        self.assertEqual(default_client_status.name, "Prospect") # Assumes sorting by sort_order then name

        # Test with preferred name
        default_active_status = status_service.get_default_status_for_type(StatusType.CLIENT, preferred_name="Actif")
        self.assertIsNotNone(default_active_status)
        self.assertEqual(default_active_status.name, "Actif")

        mock_ssc.get_all_status_settings.assert_any_call(type_filter="Client")


    def test_get_default_status_for_client_creation(self, mock_commandes_crud, mock_clients_crud, mock_ssc):
        # Scenario 1: "Prospect" exists
        mock_ssc.get_all_status_settings.reset_mock() # Reset call counts for clarity
        mock_ssc.get_all_status_settings.return_value = [MOCK_DB_STATUS_ROW_CLIENT_PROSPECT.copy()]
        status = status_service.get_default_status_for_client_creation()
        self.assertEqual(status.name, "Prospect")

        # Scenario 2: "Prospect" does not exist, "Nouveau" exists
        mock_ssc.get_all_status_settings.reset_mock()
        mock_nouveau = {"status_id": 4, "status_name": "Nouveau", "status_type": "Client", "sort_order": 5}
        mock_ssc.get_all_status_settings.return_value = [mock_nouveau, MOCK_DB_STATUS_ROW_CLIENT_ACTIVE.copy()]
        status = status_service.get_default_status_for_client_creation()
        self.assertEqual(status.name, "Nouveau")

        # Scenario 3: Neither "Prospect" nor "Nouveau" exist, takes first by sort order
        mock_ssc.get_all_status_settings.reset_mock()
        mock_other = {"status_id": 5, "status_name": "AutreClient", "status_type": "Client", "sort_order": 1, "is_archival_status": 0, "icon_name": "icon_other"}
        # Ensure the mock returns data sorted by sort_order as the DB would
        mock_ssc.get_all_status_settings.return_value = [mock_other, MOCK_DB_STATUS_ROW_CLIENT_ACTIVE.copy()] # AutreClient (1), Active (20)
        status = status_service.get_default_status_for_client_creation()
        self.assertIsNotNone(status, "Status should not be None in scenario 3")
        self.assertEqual(status.name, "AutreClient") # Should pick AutreClient due to sort_order

    def test_get_default_status_for_commande_creation(self, mock_commandes_crud, mock_clients_crud, mock_ssc):
        mock_ssc.get_all_status_settings.return_value = [
            MOCK_DB_STATUS_ROW_COMMANDE_BROUILLON.copy(), # name "Brouillon"
            MOCK_DB_STATUS_ROW_COMMANDE_LIVREE.copy()
        ]
        status = status_service.get_default_status_for_commande_creation()
        self.assertIsNotNone(status)
        self.assertEqual(status.name, "Brouillon")
        mock_ssc.get_all_status_settings.assert_called_with(type_filter="Commande")


    def test_get_archived_status_for_client(self, mock_commandes_crud, mock_clients_crud, mock_ssc):
        # Scenario 1: A status has is_archival=True (or is_archival_status=1 in mock DB)
        mock_ssc.get_all_status_settings.reset_mock()
        mock_ssc.get_all_status_settings.return_value = [
            MOCK_DB_STATUS_ROW_CLIENT_ACTIVE.copy(), # is_archival_status: 0
            MOCK_DB_STATUS_ROW_CLIENT_ARCHIVED.copy() # is_archival_status: 1
        ]
        status = status_service.get_archived_status_for_client()
        self.assertIsNotNone(status)
        self.assertEqual(status.name, "Archivé")
        self.assertTrue(status.is_archival)

        # Scenario 2: No status has is_archival=True, but one is named "Archivé"
        mock_ssc.get_all_status_settings.reset_mock()
        mock_archived_by_name_only = MOCK_DB_STATUS_ROW_CLIENT_ARCHIVED.copy()
        mock_archived_by_name_only["is_archival_status"] = 0 # Simulate it's not True via flag

        mock_ssc.get_all_status_settings.return_value = [
            MOCK_DB_STATUS_ROW_CLIENT_ACTIVE.copy(),
            mock_archived_by_name_only
        ]
        status = status_service.get_archived_status_for_client()
        self.assertIsNotNone(status) # Should find it by name "Archivé" as fallback
        self.assertEqual(status.name, "Archivé")
        self.assertFalse(status.is_archival) # is_archival from data will be False

        # Scenario 3: No status is_archival=True and no status named "Archivé"
        mock_ssc.get_all_status_settings.reset_mock()
        mock_ssc.get_all_status_settings.return_value = [
            MOCK_DB_STATUS_ROW_CLIENT_ACTIVE.copy(),
            MOCK_DB_STATUS_ROW_CLIENT_PROSPECT.copy()
        ]
        status = status_service.get_archived_status_for_client()
        self.assertIsNone(status) # Should return None


if __name__ == '__main__':
    unittest.main()
