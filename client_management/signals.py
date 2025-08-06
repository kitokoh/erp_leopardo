from PyQt5.QtCore import QObject, pyqtSignal

class ClientManagementSignals(QObject):
    # Signal to request a refresh of the client list in the main dashboard
    request_client_list_refresh = pyqtSignal()

    # Signal to indicate a client has been selected in the main dashboard
    # Emits the client_info dictionary
    client_selected = pyqtSignal(dict)

    # Signal to request opening a specific client's view
    # Emits the client_id
    request_client_view = pyqtSignal(int)

    # Signal to notify that a client's data has been updated
    # Emits the updated client_info dictionary
    client_updated = pyqtSignal(dict)

    # Signal to notify that a new client has been created
    # Emits the new client_info dictionary
    client_created = pyqtSignal(dict)

    # Signal to show a notification
    # Emits title (str), message (str), and type (str, e.g., 'SUCCESS', 'ERROR')
    show_notification = pyqtSignal(str, str, str)

# Create a global instance of the signals
client_management_signals = ClientManagementSignals()
