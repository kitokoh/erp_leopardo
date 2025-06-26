# user_management/user_menu_button.py
import logging
from PyQt5.QtWidgets import QPushButton, QMenu, QAction, QLabel, QWidgetAction, QApplication, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, pyqtSignal

from auth.permissions import has_permission, P_MANAGE_USERS
# Import EditUserDialog relatively if UserMenuButton is in the same directory level as dialogs,
# or adjust path. Assuming main_window.py (parent) will handle dialog instantiation for now.

logger = logging.getLogger(__name__)

class UserMenuButton(QPushButton):
    # Signals to notify the main window to perform actions
    request_logout = pyqtSignal()
    request_show_user_management_page = pyqtSignal()
    request_open_edit_my_account_dialog = pyqtSignal() # Emits current_user_info
    request_open_add_user_dialog = pyqtSignal()

    def __init__(self, current_user_info: dict | None, parent=None):
        super().__init__(parent)
        self.current_user_info = current_user_info
        self.main_window_ref = parent # Assuming parent is DocumentManager (main window)

        self.setIcon(QIcon(":/icons/user.svg"))
        self.setFixedSize(32, 32) # Default size, can be styled further with QSS
        self.setToolTip(self.tr("Options Utilisateur"))
        self.setFlat(True) # Make it look less like a bulky button

        self.user_menu = QMenu(self)
        self.clicked.connect(self._show_user_menu)

        self._build_menu()

    def update_user_info(self, new_user_info: dict | None):
        """Updates the user info and rebuilds the menu if necessary."""
        self.current_user_info = new_user_info
        self._build_menu() # Rebuild menu as permissions/info might change

    def _build_menu(self):
        self.user_menu.clear()

        if not self.current_user_info:
            # Should not happen if button is only visible when logged in, but as a fallback:
            no_user_action = self.user_menu.addAction(self.tr("Non connecté"))
            no_user_action.setEnabled(False)
            return

        # 1. User Information Display (as a non-clickable QWidgetAction)
        username = self.current_user_info.get('username', 'N/A')
        role_name = self.current_user_info.get('role_name', self.tr('Rôle inconnu'))

        info_widget = QLabel(f"<b>{username}</b><br><small>{role_name}</small>")
        info_widget.setAlignment(Qt.AlignCenter)
        info_widget.setContentsMargins(10, 5, 10, 5) # Add some padding

        info_action_widget = QWidgetAction(self.user_menu)
        info_action_widget.setDefaultWidget(info_widget)
        self.user_menu.addAction(info_action_widget)
        self.user_menu.addSeparator()

        # 2. Modify My Account
        edit_my_account_action = QAction(QIcon(":/icons/settings.svg"), self.tr("Modifier Mon Compte"), self.user_menu)
        edit_my_account_action.triggered.connect(self._handle_edit_my_account)
        self.user_menu.addAction(edit_my_account_action)

        # 3. Logout
        logout_action = QAction(QIcon(":/icons/log-out.svg"), self.tr("Déconnexion"), self.user_menu)
        logout_action.triggered.connect(self._handle_logout) # Emit signal
        self.user_menu.addAction(logout_action)

        # 4. Admin-only section
        # Check P_MANAGE_USERS permission for the current user
        user_role = self.current_user_info.get('role_name')
        if has_permission(user_role, P_MANAGE_USERS):
            self.user_menu.addSeparator()

            manage_users_action = QAction(QIcon(":/icons/users.svg"), self.tr("Gérer les Utilisateurs"), self.user_menu)
            manage_users_action.triggered.connect(self._handle_show_user_management) # Emit signal
            self.user_menu.addAction(manage_users_action)

            create_user_action = QAction(QIcon(":/icons/user-plus.svg"), self.tr("Créer un Nouvel Utilisateur"), self.user_menu)
            create_user_action.triggered.connect(self._handle_add_user) # Emit signal
            self.user_menu.addAction(create_user_action)

    def _show_user_menu(self):
        # Position menu below the button
        # The menu is parented to self (the button), so it should position correctly by default
        # For more control: self.user_menu.popup(self.mapToGlobal(self.rect().bottomLeft()))
        self.user_menu.exec_(self.mapToGlobal(self.rect().bottomLeft() + Qt.QPoint(0, 5)))


    def _handle_edit_my_account(self):
        if self.current_user_info:
            logger.info(f"UserMenuButton: Emitting request_open_edit_my_account_dialog for user {self.current_user_info.get('username')}")
            self.request_open_edit_my_account_dialog.emit()
        else:
            logger.warning("UserMenuButton: Edit my account clicked, but no current_user_info.")


    def _handle_logout(self):
        logger.info("UserMenuButton: Emitting request_logout.")
        self.request_logout.emit()

    def _handle_show_user_management(self):
        logger.info("UserMenuButton: Emitting request_show_user_management_page.")
        self.request_show_user_management_page.emit()

    def _handle_add_user(self):
        logger.info("UserMenuButton: Emitting request_open_add_user_dialog.")
        self.request_open_add_user_dialog.emit()

if __name__ == '__main__':
    # Basic test for the UserMenuButton
    app = QApplication(sys.argv)
    import sys
    logging.basicConfig(level=logging.DEBUG)

    # Mock main window for context (not strictly needed for this simple test)
    # class MockMainWindow(QWidget):
    #     def __init__(self):
    #         super().__init__()
    #         self.user_info_for_button = {'username': 'testadmin', 'role_name': 'Administrator', 'user_id': 'admin001'}
    #         # self.user_info_for_button = {'username': 'testuser', 'role_name': 'Operator', 'user_id': 'user002'}
    #         # self.user_info_for_button = None # Test no user

    #         self.button = UserMenuButton(self.user_info_for_button, self)
    #         layout = QVBoxLayout(self)
    #         layout.addWidget(self.button)
    #         self.setLayout(layout)
    #         self.setWindowTitle("UserMenuButton Test")

    #         # Connect signals for logging
    #         self.button.request_logout.connect(lambda: print("Logout requested"))
    #         self.button.request_show_user_management_page.connect(lambda: print("Show User Management Page requested"))
    #         self.button.request_open_edit_my_account_dialog.connect(lambda: print(f"Edit My Account requested for {self.button.current_user_info}"))
    #         self.button.request_open_add_user_dialog.connect(lambda: print("Add User Dialog requested"))


    # window = MockMainWindow()
    # window.setGeometry(300, 300, 200, 100)
    # window.show()

    # Simplified test without mock window, directly creating button
    # Test case 1: Admin user
    admin_info = {'user_id': 'uuid-admin', 'username': 'SuperAdmin', 'role_name': 'Administrator', 'email': 'admin@example.com'}
    btn_admin = UserMenuButton(admin_info)
    btn_admin.setText("Admin Menu") # Text for visibility in test
    btn_admin.setFixedSize(150, 40)
    btn_admin.show()

    # Test case 2: Standard user
    operator_info = {'user_id': 'uuid-operator', 'username': 'StandardUser', 'role_name': 'Operator', 'email': 'op@example.com'}
    btn_operator = UserMenuButton(operator_info)
    btn_operator.setText("Operator Menu")
    btn_operator.setFixedSize(150, 40)
    btn_operator.move(0, 50) # Move so it doesn't overlap
    btn_operator.show()

    sys.exit(app.exec_())
