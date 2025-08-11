import unittest
from app.status_manager.status_models import Status, StatusType # Assuming status_manager is in PYTHONPATH

class TestStatusType(unittest.TestCase):
    def test_enum_values(self):
        self.assertEqual(StatusType.CLIENT.value, "Client")
        self.assertEqual(StatusType.COMMANDE.value, "Commande")
        self.assertEqual(StatusType.PROJECT.value, "Project")
        self.assertEqual(StatusType.TASK.value, "Task")
        self.assertEqual(StatusType.TICKET.value, "Ticket")

    def test_from_string_valid(self):
        self.assertEqual(StatusType.from_string("Client"), StatusType.CLIENT)
        self.assertEqual(StatusType.from_string("Commande"), StatusType.COMMANDE)
        # Add more cases if new types are added

    def test_from_string_invalid(self):
        with self.assertRaises(ValueError) as context:
            StatusType.from_string("InvalidType")
        self.assertIn("'InvalidType' is not a valid StatusType value", str(context.exception))

    def test_iteration(self):
        # Check if all defined members are iterable
        members = [member for member in StatusType]
        self.assertIn(StatusType.CLIENT, members)
        self.assertIn(StatusType.COMMANDE, members)
        self.assertTrue(len(members) >= 5) # At least the initial 5


class TestStatusModel(unittest.TestCase):
    def test_status_creation_defaults(self):
        status = Status()
        self.assertIsNone(status.status_id)
        self.assertEqual(status.name, "")
        self.assertEqual(status.type, StatusType.CLIENT) # Default type
        self.assertIsNone(status.color_hex)
        self.assertEqual(status.sort_order, 0)
        self.assertFalse(status.is_archival)
        self.assertIsNone(status.icon_name)

    def test_status_creation_with_values(self):
        status = Status(
            status_id=1,
            name="Prospect",
            type=StatusType.CLIENT,
            color_hex="#FFFF00",
            sort_order=10,
            is_archival=False,
            icon_name="client_prospect.svg"
        )
        self.assertEqual(status.status_id, 1)
        self.assertEqual(status.name, "Prospect")
        self.assertEqual(status.type, StatusType.CLIENT)
        self.assertEqual(status.color_hex, "#FFFF00")
        self.assertEqual(status.sort_order, 10)
        self.assertFalse(status.is_archival)
        self.assertEqual(status.icon_name, "client_prospect.svg")

    def test_status_creation_with_string_type(self):
        # Test __post_init__ for type conversion
        status = Status(name="Test Ticket", type="Ticket")
        self.assertEqual(status.type, StatusType.TICKET)

        with self.assertRaises(ValueError) as context:
            Status(name="Invalid Type Test", type="NonExistentType")
        self.assertIn("Invalid string for Status.type: NonExistentType", str(context.exception))


    def test_is_for_type_methods(self):
        client_status = Status(type=StatusType.CLIENT)
        commande_status = Status(type=StatusType.COMMANDE)
        self.assertTrue(client_status.is_for_client())
        self.assertFalse(client_status.is_for_commande())
        self.assertTrue(commande_status.is_for_commande())
        self.assertFalse(commande_status.is_for_client())

    def test_to_dict(self):
        status = Status(
            status_id=5,
            name="Test Status",
            type=StatusType.PROJECT,
            color_hex="#123456",
            sort_order=50,
            is_archival=True,
            icon_name="project_icon.png"
        )
        expected_dict = {
            "status_id": 5,
            "status_name": "Test Status",
            "status_type": "Project", # Enum value
            "color_hex": "#123456",
            "sort_order": 50,
            "is_archival": True,
            "icon_name": "project_icon.png"
        }
        self.assertEqual(status.to_dict(), expected_dict)

    def test_to_dict_with_none_values(self):
        status = Status(name="Minimal", type=StatusType.TASK)
        expected_dict = {
            "status_id": None,
            "status_name": "Minimal",
            "status_type": "Task",
            "color_hex": None,
            "sort_order": 0,
            "is_archival": False,
            "icon_name": None
        }
        self.assertEqual(status.to_dict(), expected_dict)

    def test_from_dict_full_data(self):
        data = {
            "status_id": 10,
            "status_name": "Achevée",
            "status_type": "Task",
            "color_hex": "#00FF00",
            "sort_order": 100,
            "is_archival": False, # Test with explicit False
            "icon_name": "task_done.svg"
        }
        status = Status.from_dict(data)
        self.assertIsNotNone(status)
        self.assertEqual(status.status_id, 10)
        self.assertEqual(status.name, "Achevée")
        self.assertEqual(status.type, StatusType.TASK)
        self.assertEqual(status.color_hex, "#00FF00")
        self.assertEqual(status.sort_order, 100)
        self.assertFalse(status.is_archival)
        self.assertEqual(status.icon_name, "task_done.svg")

    def test_from_dict_minimal_data(self):
        data = {"status_name": "Nouveau", "status_type": "Client"}
        status = Status.from_dict(data)
        self.assertIsNotNone(status)
        self.assertIsNone(status.status_id)
        self.assertEqual(status.name, "Nouveau")
        self.assertEqual(status.type, StatusType.CLIENT)
        self.assertIsNone(status.color_hex)
        self.assertEqual(status.sort_order, 0) # Default
        self.assertFalse(status.is_archival)    # Default
        self.assertIsNone(status.icon_name)

    def test_from_dict_is_archival_variations(self):
        data_true_bool = {"status_name": "Archived", "status_type": "Client", "is_archival": True}
        self.assertTrue(Status.from_dict(data_true_bool).is_archival)

        data_true_int = {"status_name": "Archived", "status_type": "Client", "is_archival": 1}
        self.assertTrue(Status.from_dict(data_true_int).is_archival)

        # Test with alternative key 'is_archival_status' from some CRUDs
        data_alt_key_true = {"status_name": "Old", "status_type": "Client", "is_archival_status": True}
        self.assertTrue(Status.from_dict(data_alt_key_true).is_archival)

        data_alt_key_int_true = {"status_name": "Old Int", "status_type": "Client", "is_archival_status": 1}
        self.assertTrue(Status.from_dict(data_alt_key_int_true).is_archival)

        data_false_bool = {"status_name": "Active", "status_type": "Client", "is_archival": False}
        self.assertFalse(Status.from_dict(data_false_bool).is_archival)

        data_false_int = {"status_name": "Active", "status_type": "Client", "is_archival": 0}
        self.assertFalse(Status.from_dict(data_false_int).is_archival)

        data_missing_archival = {"status_name": "New", "status_type": "Client"} # is_archival field missing
        self.assertFalse(Status.from_dict(data_missing_archival).is_archival) # Should default to False


    def test_from_dict_invalid_type_string(self):
        data = {"status_name": "Error", "status_type": "WrongType"}
        with self.assertRaises(ValueError) as context:
            Status.from_dict(data)
        self.assertIn("'WrongType' is not a valid StatusType value", str(context.exception))

    def test_from_dict_empty_or_none(self):
        self.assertIsNone(Status.from_dict(None))
        self.assertIsNone(Status.from_dict({})) # or raise error, current behavior is None due to missing required fields in a sense


if __name__ == '__main__':
    unittest.main()
