from enum import Enum
from dataclasses import dataclass, field
from typing import Optional

class StatusType(Enum):
    """
    Enumeration for the types of entities that can have a status.
    The string value should match what's stored in the database (status_type column).
    """
    CLIENT = "Client"
    COMMANDE = "Commande" # French for Order
    PROJECT = "Project"
    TASK = "Task"
    TICKET = "Ticket"
    # Add other types as they become necessary, ensuring the string value
    # matches potential values in the StatusSettings.status_type column.

    @classmethod
    def from_string(cls, s: str):
        """
        Creates a StatusType member from a string.
        Raises ValueError if the string is not a valid StatusType.
        """
        for member in cls:
            if member.value == s:
                return member
        raise ValueError(f"'{s}' is not a valid StatusType value.")

@dataclass
class Status:
    """
    Represents a status entity in the application.
    """
    status_id: Optional[int] = None
    name: str = ""
    type: StatusType = StatusType.CLIENT # Default type, can be changed
    color_hex: Optional[str] = None
    sort_order: int = 0
    is_archival: bool = False # Indicates if this status means the entity is archived
    icon_name: Optional[str] = None # Name of an icon to associate with this status

    def __post_init__(self):
        # Ensure type is a StatusType instance if it's passed as a string
        if isinstance(self.type, str):
            try:
                self.type = StatusType.from_string(self.type)
            except ValueError as e:
                # Handle cases where an invalid string might be passed during initialization
                # Or re-raise, or default to a specific type. For now, let's re-raise.
                raise ValueError(f"Invalid string for Status.type: {self.type}. {e}") from e

    # Example of a method that might be useful
    def is_for_client(self) -> bool:
        return self.type == StatusType.CLIENT

    def is_for_commande(self) -> bool:
        return self.type == StatusType.COMMANDE

    # Add more specific type checks if needed
    # def is_for_project(self) -> bool:
    #     return self.type == StatusType.PROJECT
    # etc.

    def to_dict(self) -> dict:
        """Converts the Status object to a dictionary, suitable for CRUD operations."""
        return {
            "status_id": self.status_id,
            "status_name": self.name,
            "status_type": self.type.value, # Store the string value
            "color_hex": self.color_hex,
            "sort_order": self.sort_order,
            "is_archival": self.is_archival, # Assuming DB stores this as 0/1 or TRUE/FALSE
            "icon_name": self.icon_name
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Creates a Status object from a dictionary (e.g., from DB CRUD)."""
        if not data:
            return None
        return cls(
            status_id=data.get("status_id"),
            name=data.get("status_name", ""),
            type=StatusType.from_string(data.get("status_type", StatusType.CLIENT.value)), # Ensure type conversion
            color_hex=data.get("color_hex"),
            sort_order=data.get("sort_order", 0),
            is_archival=bool(data.get("is_archival", False) or data.get("is_archival_status", False)), # Support both db names
            icon_name=data.get("icon_name")
        )

if __name__ == '__main__':
    # Example Usage and Tests
    try:
        client_status = StatusType.from_string("Client")
        print(f"Successfully created StatusType from string: {client_status}")
    except ValueError as e:
        print(f"Error creating StatusType from string: {e}")

    try:
        invalid_status = StatusType.from_string("InvalidType")
    except ValueError as e:
        print(f"Correctly caught error for invalid StatusType string: {e}")

    # Test Status dataclass
    status1 = Status(status_id=1, name="Prospect", type=StatusType.CLIENT, color_hex="#FFFF00", sort_order=1)
    print(f"\nStatus 1: {status1}")
    print(f"Is for client: {status1.is_for_client()}")
    print(f"To dict: {status1.to_dict()}")

    status2_data_from_db = {
        "status_id": 2,
        "status_name": "En Cours",
        "status_type": "Commande", # String value from DB
        "color_hex": "#0000FF",
        "sort_order": 5,
        "is_archival_status": 0, # Example DB representation for boolean
        "icon_name": "commande_en_cours_icon"
    }
    status2 = Status.from_dict(status2_data_from_db)
    print(f"\nStatus 2 (from dict): {status2}")
    if status2:
        print(f"Is for commande: {status2.is_for_commande()}")
        print(f"Type: {status2.type}, Value: {status2.type.value}")
        print(f"Is archival: {status2.is_archival}")
        print(f"To dict: {status2.to_dict()}")


    status3_data_with_string_type = {
        "status_id": 3,
        "status_name": "Active Project",
        "status_type": "Project", # Pass as string
        "color_hex": "#00FF00",
        "sort_order": 2
    }
    status3 = Status.from_dict(status3_data_with_string_type)
    print(f"\nStatus 3 (from dict with string type): {status3}")
    if status3:
      print(f"Status 3 type: {status3.type}")

    try:
        status_invalid_type_data = {
            "status_id": 4,
            "status_name": "Invalid",
            "status_type": "NonExistentType",
        }
        status_invalid = Status.from_dict(status_invalid_type_data)
        print(f"\nStatus Invalid (from_dict): {status_invalid}")
    except ValueError as e:
        print(f"\nCorrectly caught error for invalid status_type in from_dict: {e}")

    # Test direct instantiation with string type
    try:
        status_direct_str_type = Status(name="Test Direct", type="Ticket")
        print(f"\nStatus direct string type: {status_direct_str_type}, type: {status_direct_str_type.type}")
    except ValueError as e:
        print(f"\nError instantiating Status with string type directly: {e}")

    # Test is_archival variations
    archival_data_true_1 = {"status_name": "Archived", "status_type": "Client", "is_archival": True}
    archival_data_true_2 = {"status_name": "Old", "status_type": "Client", "is_archival_status": 1}
    archival_data_false = {"status_name": "Active", "status_type": "Client", "is_archival": False}
    archival_data_none = {"status_name": "New", "status_type": "Client"}

    print(f"\nIs archival (True): {Status.from_dict(archival_data_true_1).is_archival}")
    print(f"Is archival (1): {Status.from_dict(archival_data_true_2).is_archival}")
    print(f"Is archival (False): {Status.from_dict(archival_data_false).is_archival}")
    print(f"Is archival (None): {Status.from_dict(archival_data_none).is_archival}")
