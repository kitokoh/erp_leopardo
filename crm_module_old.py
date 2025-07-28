import sys
from PyQt5.QtWidgets import QApplication
from gui.main_window import DocumentManager

def launch_crm():
    """
    This function launches the main CRM application window.
    """
    # It's assumed that the necessary setup (db, logging, etc.) has already been done
    # by the main application that calls this module.

    # Dummy user and license info for now. This will need to be passed in from the
    # main application in a real scenario.
    user_info = {'username': 'testuser', 'role': 'admin', 'user_id': 1}
    license_info = {'is_active': True, 'allowed_features': ['all']}

    # The APP_ROOT_DIR will also need to be passed in or determined.
    # For now, we'll assume the current working directory is the app root.
    import os
    app_root_dir = os.getcwd()

    app = QApplication.instance() # Get the existing application instance
    if not app: # If no instance exists, create one
        app = QApplication(sys.argv)

    main_window = DocumentManager(app_root_dir, user_info, license_info)
    main_window.show()

if __name__ == '__main__':
    # This allows the module to be run directly for testing purposes.
    launch_crm()
    sys.exit(QApplication.instance().exec_())
