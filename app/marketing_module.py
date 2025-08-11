import sys
from PyQt5.QtCore import Qt, QTranslator, QLocale, QLibraryInfo, QPropertyAnimation, QThread, pyqtSignal, QTimer, QUrl, QSize
from PyQt5.QtGui import QIcon, QPixmap, QFont, QPainter, QColor, QLinearGradient, QGuiApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTabWidget, QTabBar, QFrame, QLabel, QWidget,
    QSplitter, QStackedWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QComboBox,
    QDialog, QDialogButtonBox, QFormLayout, QMenu, QMessageBox, QProgressDialog, QScrollArea, QToolButton,
    QCheckBox, QStatusBar, QSplashScreen, QWidgetAction, QLayout, QWidgetItem, QListWidget, QListWidgetItem, QGraphicsDropShadowEffect
)

class SplitScreenView(QWidget):
    def __init__(self, main_app):
        super().__init__()

class Nova360ProApp(QWidget):
    def __init__(self, main_app):
        super().__init__()

class Nova360Ultimate(QWidget):
    def __init__(self, main_app):
        super().__init__()

class LoaderThread(QThread):
    finished = pyqtSignal(object)
    def __init__(self, main_app):
        super().__init__()

class LoaderThreadTelecommande(QThread):
    finished = pyqtSignal(object)
    def __init__(self, main_app):
        super().__init__()

class LoadingScreen(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

class QOverlayLayout(QLayout):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self.positions = {}

    def addWidget(self, widget, alignment=None):
        item = QWidgetItem(widget)
        self.addItem(item)
        if alignment is not None:
            self.positions[widget] = alignment
        return item

    def addItem(self, item):
        self.items.append(item)

    def count(self):
        return len(self.items)

    def itemAt(self, index):
        if 0 <= index < len(self.items):
            return self.items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self.items):
            return self.items.pop(index)
        return None

    def setGeometry(self, rect):
        super().setGeometry(rect)
        for i in range(self.count()):
            item = self.itemAt(i)
            if item is None:
                continue
            widget = item.widget()
            if widget is None:
                continue
            widget_rect = rect
            if widget in self.positions:
                alignment = self.positions[widget]
                size = widget.sizeHint()
                if alignment & Qt.AlignTop:
                    widget_rect.setTop(rect.top())
                    widget_rect.setBottom(rect.top() + size.height())
                elif alignment & Qt.AlignBottom:
                    widget_rect.setTop(rect.bottom() - size.height())
                    widget_rect.setBottom(rect.bottom())
                if alignment & Qt.AlignLeft:
                    widget_rect.setLeft(rect.left())
                    widget_rect.setRight(rect.left() + size.width())
                elif alignment & Qt.AlignRight:
                    widget_rect.setLeft(rect.right() - size.width())
                    widget_rect.setRight(rect.right())
                if alignment & Qt.AlignHCenter:
                    widget_rect.setLeft(rect.left() + (rect.width() - size.width()) // 2)
                    widget_rect.setRight(widget_rect.left() + size.width())
                elif alignment & Qt.AlignVCenter:
                    widget_rect.setTop(rect.top() + (rect.height() - size.height()) // 2)
                    widget_rect.setBottom(widget_rect.top() + size.height())
            widget.setGeometry(widget_rect)

class AccueilWidget(QWidget):
    def __init__(self):
        super().__init__()

class SearchWidget(QWidget):
    def __init__(self):
        super().__init__()

class SettingsWidget(QWidget):
    def __init__(self):
        super().__init__()

class HelpWidget(QWidget):
    def __init__(self):
        super().__init__()

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

class CertificateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

class Activite(QWidget):
    def __init__(self):
        super().__init__()

class InstanceTable(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

class MainWindow1(QWidget):
    def __init__(self, main_app):
        super().__init__()

class PDFEditorApp(QWidget):
    def __init__(self):
        super().__init__()

class WatermarkApp(QWidget):
    def __init__(self):
        super().__init__()

class MainWindowLink(QWidget):
    def __init__(self, main_app):
        super().__init__()

class PromptManager(QWidget):
    def __init__(self, main_app):
        super().__init__()

class ContactDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

class FlowManager:
    def __init__(self, db):
        pass
    def start_session(self):
        return {'dialogs': []}
    def end_session(self):
        pass

class DatabaseManager:
    def __init__(self):
        pass
    def close(self):
        pass

class InstallerPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

class ContactTable(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

class GroupTable(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

class MediaTable(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

class UpdaterWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

class LicenseChecker:
    def __init__(self, license_dir):
        pass
    def is_license_valid(self):
        return True

class GroupCounter:
    def __init__(self, file_path):
        pass
    def count_groups(self):
        return 0

class Dashboard(QWidget):
    def __init__(self, title, subtitle, validiter, Nombregroupes, totalshare, nexttimeshare):
        super().__init__()

class SpecialOfferWindow(QWidget):
    def __init__(self, main_app):
        super().__init__()

class DescriptionManager(QWidget):
    def __init__(self):
        super().__init__()

class MarketingAIAnalyzer(QWidget):
    def __init__(self, parent=None):
        super().__init__()

class CryptoStrategyApp(QWidget):
    def __init__(self, parent=None):
        super().__init__()

class MainWindowMail(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

class MainWindowattak(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

class MainWindowsales(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

class LoginModule(QWidget):
    def __init__(self):
        super().__init__()

class Browser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.splash = None
        self.show_splash_screen()
        self.translator = QTranslator()
        self.init_language()
        self.setWindowTitle(self.tr("Modern Browser"))
        self.setWindowIcon(QIcon("browser_icon.png"))
        self.setGeometry(220, 80,1200, 800)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.initUI()
        import time
        time.sleep(3)
        self.splash.finish(self)
        self.menu_config = {
            'visible_buttons': {
                'Tools': True,
                'Settings': True,
                'Data': True,
                'Support': True
            }
        }
        self.load_menu_config()
    def control_application(self):
        self.db = DatabaseManager()
        self.flow_manager = FlowManager( self.db)
        self.current_flow = self.flow_manager.start_session()
        self.current_step = 0
        self.run_next_dialog()
    def run_next_dialog(self):
        if self.current_step < len(self.current_flow['dialogs']):
            dialog_class, title = self.current_flow['dialogs'][self.current_step]
            self.dialog = dialog_class(title)
            self.dialog.finished.connect(self.on_dialog_finished)
            self.dialog.show()
        else:
            self.flow_manager.end_session()
    def on_dialog_finished(self, result):
        if result == QDialog.Accepted:
            self.current_step += 1
            self.run_next_dialog()
        else:
            self.flow_manager.end_session()
    def show_splash_screen(self):
        self.splash_pix = QPixmap("resources/images/splashScreer.png")
        if self.splash_pix.isNull():
                    print("Error: Splash screen image not found.")
                    return
        self.splash = QSplashScreen(self.splash_pix, Qt.WindowStaysOnTopHint)
        self.splash.setStyleSheet("background-color: #2E7D32;")
        self.splash.setFont(QFont("Arial", 12))
        self.splash.show()
        loading_message = "Loading, please wait..."
        self.splash.showMessage(
            loading_message,
            Qt.AlignBottom | Qt.AlignCenter,
            Qt.white
        )
    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.create_top_menu()
        self.main_layout.addWidget(self.top_menu, stretch=0)
        self.central_container = QSplitter(Qt.Horizontal)
        self.central_container.setChildrenCollapsible(False)
        self.central_container.setHandleWidth(10)
        self.central_container.setStyleSheet("""
            QSplitter::handle {
                background: #333333;
                width: 5px;
            }
            QSplitter::handle:hover {
                background: #444444;
            }
        """)
        self.browser_container = QWidget()
        self.browser_layout = QVBoxLayout(self.browser_container)
        self.browser_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.update_search_bar_visibility)
        self.tab_widget.setStyleSheet(self.tab_widget_style())
        self.browser_layout.addWidget(self.tab_widget)
        self.create_search_bar(self.browser_layout)
        self.central_container.addWidget(self.browser_container)
        self.main_layout.addWidget(self.central_container, stretch=1)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.open_home()
        QTimer.singleShot(200, self.control_application)
    def create_top_menu(self):
        self.is_user_logged_in = False
        self.is_enterprise_mode = False
        self.current_username = "Guest"
        self.load_session_state()
        self.menu_config = {
            'visible_buttons': {
                'Tools': False,
                'Data': False,
                'Support': False
            }
        }
        self.load_menu_config()
        self.top_menu = QFrame()
        self.top_menu.setFixedHeight(50)
        self.top_menu.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border-bottom: 1px solid #e2e8f0;
            }
        """)
        self.top_menu_layout = QHBoxLayout(self.top_menu)
        self.top_menu_layout.setContentsMargins(5, 5, 5, 5)
        self.top_menu_layout.setSpacing(10)
        self.app_title = QLabel("Leopardo AI")
        self.app_title.setStyleSheet("""
            QLabel {
                color: #2563eb;
                font-size: 18px;
                font-weight: bold;
                padding: 0 15px;
            }
        """)
        self.top_menu_layout.addWidget(self.app_title)
        self.menu_bar = QHBoxLayout()
        self.menu_bar.setSpacing(5)
        menu_items = [
            ("🏠", self.tr("Home"), "home", self.open_home, self.tr("Main dashboard"), []),
            ("🧰", self.tr("Tools"), "tools", None, self.tr("Document tools"), [
                ("🧠", self.tr("Management"), "Management", self.open_management, self.tr("Management tools"), []),
                ("📺", self.tr("Media"), "media", self.add_media_page, self.tr("Media Management"), []),
                ("🌍", self.tr("My Groups"), "grups", self.open_grups_window, self.tr("Group list"), []),
                ("👥", self.tr("Address book"), "contact", self.open_contacts_window, self.tr("Contact list"), []),
                ("🔗", self.tr("Links"), "links", self.open_links_window, self.tr("Manage links"), []),
                ("📝", self.tr("Desc & Prompts"), "prompts", self.open_prompts_window, self.tr("Useful prompts"), []),
            ]),
            ("✨", self.tr("Plans"), "Plans", None, self.tr("Plans options"), [
                ("🎯", self.tr("Marketing"), "Marketing", self.open_marketing, self.tr("Marketing tools"), []),
                ("📜", self.tr("Protocles"), "Protocoles", self.open_management, self.tr("Protocoles tools"), []),
                ("💸", self.tr("ADS"), "Ads", self.open_management, self.tr("Ads tools"), []),
                ("⏰", self.tr("Scheduler"), "scheduler", self.open_sheduling_window, self.tr("Task scheduling"), []),
            ]),
            ("⏯️", self.tr("Run"), "Run", self.open_manuelle_window, self.tr("Run Now"), []),
            ("💡", self.tr("Data"), "data", None, self.tr("Data management"), [
                ("🎭", self.tr("Prospects "), "Persona", self.open_persona_window, self.tr("View statistics"), []),
                ("🌍", self.tr("Groups "), "grups", self.open_grups_window, self.tr("Group list"), []),
                ("📈", self.tr("Stats"), "stats", self.open_statistics_window, self.tr("View statistics"), []),
                ("📥", self.tr("Import Data"), "import", self.open_imports_window, self.tr("Import data"), []),
                ("🗃️", self.tr("ADN Backup"), "backup", self.open_imports_window, self.tr("Backup enterprise data"), []),
            ]),
        ]
        self.menu_buttons = []
        self.sub_menus = {}
        self.current_open_menu = None
        self.menu_button_refs = {}
        for icon, text, identifier, action, tooltip, sub_items in menu_items:
            button = QPushButton(f"{icon} {text}")
            button.setFixedHeight(36)
            button.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #4b5563;
                    border: none;
                    font-size: 14px;
                    padding: 5px 10px;
                    border-radius: 4px;
                    transition: all 0.2s ease;
                }
                QPushButton:hover {
                    background-color: #e5e7eb;
                    color: #1f2937;
                    transform: translateY(-1px);
                }
            """)
            button.setToolTip(f"<b>{text}</b><br>{tooltip}")
            if action:
                button.clicked.connect(action)
            if identifier not in ["home", "tools", "data", "support", "upgrade", "settings", "beta"]:
                self.menu_button_refs[text] = button
            if sub_items:
                menu = QMenu()
                menu.setStyleSheet("""
                    QMenu {
                        background-color: #ffffff;
                        border: 1px solid #d1d5db;
                        padding: 5px;
                        border-radius: 8px;
                        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
                    }
                    QMenu::item {
                        color: #4b5563;
                        padding: 8px 25px;
                        margin: 2px;
                        border-radius: 4px;
                        font-size: 13px;
                        min-width: 150px;
                    }
                    QMenu::item:selected {
                        background-color: #f3f4f6;
                        color: #111827;
                    }
                    QMenu::item:disabled {
                        color: #9ca3af;
                    }
                    QMenu::icon {
                        padding-left: 10px;
                    }
                """)
                for sub_icon, sub_text, sub_id, sub_action, sub_tooltip, nested_sub_items in sub_items:
                    if nested_sub_items:
                        submenu = QMenu(sub_text)
                        submenu.setStyleSheet(menu.styleSheet())
                        for nest_icon, nest_text, nest_id, nest_action, nest_tooltip, _ in nested_sub_items:
                            action = submenu.addAction(f"{nest_icon} {nest_text}")
                            action.setToolTip(nest_tooltip)
                            if nest_action:
                                action.triggered.connect(nest_action)
                        menu.addMenu(submenu)
                    else:
                        action = menu.addAction(f"{sub_icon} {sub_text}")
                        action.setToolTip(sub_tooltip)
                        if sub_action:
                            action.triggered.connect(sub_action)
                button.setMenu(menu)
            self.menu_bar.addWidget(button)
            self.menu_buttons.append(button)
        self.top_menu_layout.addLayout(self.menu_bar)
        self.top_menu_layout.addStretch()
        self.create_notif()
        self.top_menu_layout.addStretch()
        self.control_buttons_layout = QHBoxLayout()
        self.control_buttons_layout.setSpacing(5)
        minimize_button = QPushButton("—")
        minimize_button.setFixedSize(26, 26)
        minimize_button.setStyleSheet(self.get_control_button_style("minimize"))
        minimize_button.clicked.connect(self.minimize_window)
        maximize_button = QPushButton("□")
        maximize_button.setFixedSize(26, 26)
        maximize_button.setStyleSheet(self.get_control_button_style("maximize"))
        maximize_button.clicked.connect(self.maximize_window)
        close_button = QPushButton("✕")
        close_button.setFixedSize(26, 26)
        close_button.setStyleSheet(self.get_control_button_style("close"))
        close_button.clicked.connect(self.close_window)
        self.control_buttons_layout.addWidget(minimize_button)
        self.control_buttons_layout.addWidget(maximize_button)
        self.control_buttons_layout.addWidget(close_button)
        self.user_button = QPushButton(f"👤 {self.current_username}")
        self.user_button.setFixedHeight(36)
        self.user_button.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #4b5563;
                border: 1px solid #d1d5db;
                font-size: 14px;
                padding: 5px 15px 5px 10px;
                border-radius: 18px;
                min-width: 100px;
                transition: all 0.2s ease;
            }
            QPushButton:hover {
                background-color: #f3f4f6;
                transform: translateY(-1px);
            }
        """)
        self.user_menu = QMenu()
        self.user_menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                border: 1px solid #d1d5db;
                padding: 8px;
                border-radius: 12px;
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
                margin-top: 5px;
            }
            QMenu::item {
                color: #4b5563;
                padding: 10px 25px;
                margin: 2px;
                border-radius: 6px;
                font-size: 13px;
                min-width: 180px;
            }
            QMenu::item:selected {
                background-color: #f3f4f6;
                color: #111827;
            }
            QMenu::separator {
                height: 1px;
                background: #e5e7eb;
                margin: 8px 2px;
            }
            QMenu::icon {
                padding-left: 10px;
            }
        """)
        self.login_action = self.user_menu.addAction("🔑 " + self.tr("Login"))
        self.logout_action = self.user_menu.addAction("🚪 " + self.tr("Logout"))
        self.user_menu.addSeparator()
        plan_section = self.user_menu.addAction("📋 " + self.tr("Data"))
        plan_section.setEnabled(False)
        self.marketing_plan_action = self.user_menu.addAction("   📢 " + self.tr("Contacts Prospect"))
        self.sales_plan_action = self.user_menu.addAction("   💰 " + self.tr("Data Groups"))
        self.user_menu.addSeparator()
        self.settings_action = self.user_menu.addAction("♻️ " + self.tr("Update"))
        settings_menu = self.user_menu.addMenu("⚙️ " + self.tr("Settings"))
        settings_menu.setStyleSheet(self.user_menu.styleSheet())
        settings_items = [
            ("🔌", self.tr("Add-On"), "add-on", self.add_on_page, self.tr("Add app")),
            ("📡", self.tr("Remote"), "remote", self.open_telecommande_window, self.tr("Remote control")),
            ("📦", self.tr("Installer"), "Installer", self.open_installer_window, self.tr("Add app")),
            ("🌐", self.tr("Connection"), "online_connect", self.connect_via_ssh, self.tr("Remote connection settings")),
            ("🗂️", self.tr("Instances"), "instances", self.open_instance, self.tr("Manage instances")),
            ("💎", self.tr("Upgrade"), "upgrade", self.open_upgrade_window, self.tr("Upgrade options")),
            ("📞", self.tr("Contact"), "contact", self.open_contact_window, self.tr("Contact us")),
            ("♟️", self.tr("Strategies"), "strategies", self.open_strategies_window, self.tr("Possible strategies")),
        ]
        for icon, text, identifier, action, tooltip in settings_items:
            act = settings_menu.addAction(f"{icon} {text}")
            act.setToolTip(tooltip)
            if action:
                act.triggered.connect(lambda _, f=action: self.check_pro_mode(f))
        self.user_menu.addSeparator()
        account_section = self.user_menu.addAction("👤 " + self.tr("Account"))
        account_section.setEnabled(False)
        self.switch_action = self.user_menu.addAction("   👥 " + self.tr("Switch Account"))
        self.subscription_action = self.user_menu.addAction("   🛒 " + self.tr("Subscription"))
        self.my_persona_action = self.user_menu.addAction("   🎭 " + self.tr("My Persona"))
        language_menu = self.user_menu.addMenu("   🌍 " + self.tr("Language"))
        language_menu.setStyleSheet(self.user_menu.styleSheet())
        language_items = [
            ("🗼", self.tr("French"), "french", lambda: self.switch_language("fr"), self.tr("French language")),
            ("🏰", self.tr("English"), "english", lambda: self.switch_language("en"), self.tr("English language")),
            ("🕋", self.tr("Arabic"), "arabic", lambda: self.switch_language("ar"), self.tr("Arabic language")),
            ("🕌", self.tr("Turkish"), "turkish", lambda: self.switch_language("tr"), self.tr("Turkish language")),
            ("🏖️", self.tr("Portuguese"), "portuguese", lambda: self.switch_language("pt"), self.tr("Portuguese language")),
        ]
        for icon, text, identifier, action, tooltip in language_items:
            act = language_menu.addAction(f"{icon} {text}")
            act.setToolTip(tooltip)
            if action:
                act.triggered.connect(action)
        self.login_action.triggered.connect(self.user_login)
        self.logout_action.triggered.connect(self.user_logout)
        self.marketing_plan_action.triggered.connect(lambda: self.open_plan("marketing"))
        self.sales_plan_action.triggered.connect(lambda: self.open_plan("sales"))
        self.settings_action.triggered.connect(self.open_user_settings)
        self.switch_action.triggered.connect(self.switch_account)
        self.subscription_action.triggered.connect(self.open_subscription)
        self.my_persona_action.triggered.connect(self.open_my_persona)
        self.user_button.setMenu(self.user_menu)
        self.top_menu_layout.addWidget(self.user_button)
        self.top_menu_layout.addLayout(self.control_buttons_layout)
        self.update_user_profile_section()
        self.update_menu_visibility()
        self.main_layout.insertWidget(0, self.top_menu)
        self.update_notification_count()
        self.update_message_count()
    def check_pro_mode(self, action_function):
        if self.is_enterprise_mode:
            action_function()
        else:
            QMessageBox.information(self,
                                self.tr("Pro Feature"),
                                self.tr("This feature is only available in Pro mode. Please upgrade to access all professional features."),
                                QMessageBox.Ok)
            self.open_upgrade_window()
    def create_notif(self):
        def create_button_with_badge(emoji_text, badge_color):
            button = QToolButton()
            button.setText(emoji_text)
            button.setFont(QFont("Segoe UI Emoji", 10))
            button.setStyleSheet("""
                QToolButton {
                    background-color: transparent;
                    border: none;
                    padding: 5px;
                }
                QToolButton:hover {
                    background-color: #e5e7eb;
                    border-radius: 6px;
                }
            """)
            badge = QLabel("0")
            badge.setStyleSheet(f"""
                QLabel {{
                    background-color: {badge_color};
                    color: white;
                    border-radius: 8px;
                    padding: 1px 5px;
                    font-size: 10px;
                    min-width: 6px;
                    max-width: 6px;
                    min-height: 6px;
                    max-height: 6px;
                }}
            """)
            badge.setAlignment(Qt.AlignCenter)
            overlay = QOverlayLayout(button)
            overlay.addWidget(badge, alignment=Qt.AlignTop | Qt.AlignRight)
            return button, badge
        self.notification_button, self.notification_badge = create_button_with_badge("🔔", "#ef4444")
        self.notification_menu = QMenu()
        self.notification_menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #d1d5db;
                min-width: 100px;
                max-height: 200px;
            }
            QMenu::item {
                padding: 8px 15px;
                border-bottom: 1px solid #f3f4f6;
            }
            QMenu::item:selected {
                background-color: #f3f4f6;
            }
        """)
        notif_header = QWidgetAction(self.notification_menu)
        notif_widget = QWidget()
        notif_layout = QHBoxLayout(notif_widget)
        notif_label = QLabel("🔔 Notifications")
        notif_label.setStyleSheet("font-weight: bold;")
        clear_btn = QPushButton("Tout marquer comme lu")
        clear_btn.setStyleSheet("""
            QPushButton {
                border: none;
                color: #3b82f6;
                background: transparent;
                padding: 0;
            }
            QPushButton:hover {
                text-decoration: underline;
            }
        """)
        clear_btn.clicked.connect(self.clear_all_notifications)
        notif_layout.addWidget(notif_label)
        notif_layout.addStretch()
        notif_layout.addWidget(clear_btn)
        notif_header.setDefaultWidget(notif_widget)
        self.notification_menu.addAction(notif_header)
        self.notification_menu.addSeparator()
        self.add_sample_notification("Nouveau message", "Visite https://leopardo-ai.web.app/ ", "5 min")
        self.notification_button.setMenu(self.notification_menu)
        self.notification_button.setPopupMode(QToolButton.InstantPopup)
        self.message_button, self.message_badge = create_button_with_badge("💬", "#3b82f6")
        self.message_menu = QMenu()
        self.message_menu.setStyleSheet(self.notification_menu.styleSheet())
        msg_header = QWidgetAction(self.message_menu)
        msg_widget = QWidget()
        msg_layout = QHBoxLayout(msg_widget)
        msg_label = QLabel("💬 Messages")
        msg_label.setStyleSheet("font-weight: bold;")
        new_msg_btn = QPushButton("Nouveau message")
        new_msg_btn.setStyleSheet(clear_btn.styleSheet())
        new_msg_btn.clicked.connect(self.open_new_message)
        msg_layout.addWidget(msg_label)
        msg_layout.addStretch()
        msg_layout.addWidget(new_msg_btn)
        msg_header.setDefaultWidget(msg_widget)
        self.message_menu.addAction(msg_header)
        self.message_menu.addSeparator()
        self.add_sample_message("Jean Dupont", "Réunion demain", "Bonjour, nous avons une réunion demain à 10h...", "10 min")
        self.message_button.setMenu(self.message_menu)
        self.message_button.setPopupMode(QToolButton.InstantPopup)
        self.top_menu_layout.addWidget(self.notification_button)
    def add_sample_notification(self, title, content, time):
        notification_action = QWidgetAction(self.notification_menu)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold;")
        content_label = QLabel(content)
        content_label.setWordWrap(True)
        content_label.setStyleSheet("color: #6b7280; font-size: 12px;")
        time_label = QLabel(time)
        time_label.setStyleSheet("color: #9ca3af; font-size: 10px;")
        time_label.setAlignment(Qt.AlignRight)
        layout.addWidget(title_label)
        layout.addWidget(content_label)
        layout.addWidget(time_label)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        notification_action.setDefaultWidget(widget)
        self.notification_menu.insertAction(self.notification_menu.actions()[1], notification_action)
        current_count = int(self.notification_badge.text())
        self.notification_badge.setText(str(current_count + 1))
    def add_sample_message(self, sender, subject, preview, time):
        message_action = QWidgetAction(self.message_menu)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        sender_label = QLabel(sender)
        sender_label.setStyleSheet("font-weight: bold;")
        subject_label = QLabel(subject)
        subject_label.setStyleSheet("color: #3b82f6;")
        preview_label = QLabel(preview)
        preview_label.setWordWrap(True)
        preview_label.setStyleSheet("color: #6b7280; font-size: 12px;")
        time_label = QLabel(time)
        time_label.setStyleSheet("color: #9ca3af; font-size: 10px;")
        time_label.setAlignment(Qt.AlignRight)
        layout.addWidget(sender_label)
        layout.addWidget(subject_label)
        layout.addWidget(preview_label)
        layout.addWidget(time_label)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        message_action.setDefaultWidget(widget)
        self.message_menu.insertAction(self.message_menu.actions()[1], message_action)
        current_count = int(self.message_badge.text())
        self.message_badge.setText(str(current_count + 1))
    def clear_all_notifications(self):
        self.notification_badge.setText("0")
    def open_new_message(self):
        print("Ouvrir l'éditeur de message")
    def update_notification_count(self):
        pass
    def update_message_count(self):
        pass
    def get_control_button_style(self, button_type):
        base_style = """
            QPushButton {
                color: white;
                border: none;
                font-weight: bold;
                border-radius: 13px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: %s;
            }
        """
        if button_type == "minimize":
            return base_style % "#d97706" + """
                QPushButton {
                    background-color: #f59e0b;
                }
                QPushButton:hover {
                    background-color: #d97706;
                }
            """
        elif button_type == "maximize":
            return base_style % "#059669" + """
                QPushButton {
                    background-color: #10b981;
                }
                QPushButton:hover {
                    background-color: #059669;
                }
            """
        elif button_type == "close":
            return base_style % "#dc2626" + """
                QPushButton {
                    background-color: #ef4444;
                }
                QPushButton:hover {
                    background-color: #dc2626;
                }
            """
        return base_style % "#e5e7eb"
    def load_session_state(self):
        import json, os
        user_data_dir = os.path.join(os.path.expanduser('~'), 'Leopardo')
        session_file = os.path.join(user_data_dir, 'resources', 'data', 'session.json')
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)
                self.is_user_logged_in = session_data.get('is_logged_in', False)
                self.current_username = session_data.get('username', 'Guest')
        except (FileNotFoundError, json.JSONDecodeError):
            self.is_user_logged_in = False
            self.current_username = 'Guest'
    def update_user_profile_section(self):
        if self.is_user_logged_in:
            self.user_button.setText(f"👤 {self.current_username}")
            self.login_action.setVisible(False)
            self.logout_action.setVisible(True)
            self.switch_action.setVisible(True)
        else:
            self.user_button.setText("👤 Guest")
            self.login_action.setVisible(True)
            self.logout_action.setVisible(False)
            self.switch_action.setVisible(False)
    def user_login(self):
        from ui.login import LoginModule
        self.login_module = LoginModule()
        self.login_module.show()
    def user_logout(self):
        import os
        user_data_dir = os.path.join(os.path.expanduser('~'), 'Leopardo')
        session_file = os.path.join(user_data_dir, 'resources', 'data', 'session.json')
        if os.path.exists(session_file):
            os.remove(session_file)
        self.is_user_logged_in = False
        self.current_username = 'Guest'
        self.update_user_profile_section()
        QMessageBox.information(
            self,
            self.tr("Déconnexion réussie"),
            self.tr("Vous avez été déconnecté avec succès.")
        )
    def switch_account(self):
        self.user_logout()
        self.user_login()
    def open_user_settings(self):
        from Updater.auto import UpdaterWindow
        window = UpdaterWindow(parent=self)
        window.show()
    def open_subscription(self):
        print("Subscription page opened")
    def open_my_persona(self):
        print("Subscription page opened")
    def open_plan(self, plan_type):
        if plan_type == "marketing":
            print("Opening Marketing Plan")
        elif plan_type == "sales":
            print("Opening Sales Plan")
    def open_home(self):
        tab_name = self.tr("🏠 Home")
        existing_tab_index = self.find_tab_by_name(tab_name)
        if existing_tab_index != -1:
            self.tab_widget.setCurrentIndex(existing_tab_index)
            return
        if not hasattr(self, 'home') or self.home is None:
            from promptes.promptmarketing import MarketingAIAnalyzer
            self.marketing = MarketingAIAnalyzer(parent=self)
        self.add_custom_tab(self.marketing, tab_name, "📊")
    def open_management(self):
        tab_name = self.tr("🧠 Management")
        existing_tab_index = self.find_tab_by_name(tab_name)
        if existing_tab_index != -1:
            self.tab_widget.setCurrentIndex(existing_tab_index)
            return
        if not hasattr(self, '🧠 Management') or self.management is None:
            from Home.homeManagement import MainDashboard
            self.management = MainDashboard()
        self.add_custom_tab(self.management, tab_name, "resources/icons/management.ico")
    def open_marketing(self):
        tab_name = self.tr("📣 Marketing Auto")
        existing_tab_index = self.find_tab_by_name(tab_name)
        if existing_tab_index != -1:
            self.tab_widget.setCurrentIndex(existing_tab_index)
            return
        if not hasattr(self, '📣 Marketing Auto') or self.marketingauto is None:
            from Home.home import HomePage
            self.marketingauto = HomePage(main_app=self)
        self.add_custom_tab(self.marketingauto, tab_name, "resources/icons/marketing.ico")
    def add_media_page(self):
        from facebooksmodule.media_manager import MediaTable
        tab_name = self.tr("📺 Medias")
        existing_tab_index = self.find_tab_by_name(tab_name)
        if existing_tab_index != -1:
            self.tab_widget.setCurrentIndex(existing_tab_index)
            return
        if not hasattr(self, '📺 Medias') or self.medias is None:
            self.medias = MediaTable(parent=self)
        self.add_custom_tab(self.medias, tab_name, "resources/icons/multi_fbb.ico")
    def open_grups_window(self):
        from facebooksmodule.group_manager import GroupTable
        tab_name = self.tr("👥 groups")
        existing_tab_index = self.find_tab_by_name(tab_name)
        if existing_tab_index != -1:
            self.tab_widget.setCurrentIndex(existing_tab_index)
            return
        if not hasattr(self, '👥 groups') or self.groups is None:
            self.groups = GroupTable(parent=self)
        self.add_custom_tab(self.groups, tab_name, "resources/icons/multi_fbb.ico")
    def open_contacts_window(self):
        from ModulesUI.whasapping.group_manager import ContactTable
        tab_name = self.tr("👥 contacts")
        existing_tab_index = self.find_tab_by_name(tab_name)
        if existing_tab_index != -1:
            self.tab_widget.setCurrentIndex(existing_tab_index)
            return
        if not hasattr(self, '👥 contacts') or self.contacts is None:
            self.contacts = ContactTable(parent=self)
        self.add_custom_tab(self.contacts, tab_name, "resources/icons/multi_fbb.ico")
    def open_links_window(self):
        from liens.gestionliens import MainWindowLink
        tab_name = self.tr("🔗 links")
        existing_tab_index = self.find_tab_by_name(tab_name)
        if existing_tab_index != -1:
            self.tab_widget.setCurrentIndex(existing_tab_index)
            return
        if not hasattr(self, '🔗 links') or self.links is None:
            self.links = MainWindowLink(main_app=self)
        self.add_custom_tab(self.links, tab_name, "resources/icons/multi_fbb.ico")
    def open_prompts_window(self):
        from promptes.promptes import PromptManager
        tab_name = self.tr("⚡prompts")
        existing_tab_index = self.find_tab_by_name(tab_name)
        if existing_tab_index != -1:
            self.tab_widget.setCurrentIndex(existing_tab_index)
            return
        if not hasattr(self, '⚡ prompts') or self.prompts is None:
            self.prompts = PromptManager(main_app=self)
        self.add_custom_tab(self.prompts, tab_name, "resources/icons/multi_fbc.ico")
    def open_sheduling_window(self):
        from statistique.activiteprogramme import Activite
        tab_name = self.tr("⏰ shedulings")
        existing_tab_index = self.find_tab_by_name(tab_name)
        if existing_tab_index != -1:
            self.tab_widget.setCurrentIndex(existing_tab_index)
            return
        if not hasattr(self, '⏰ shedulings') or self.sheduling is None:
            self.sheduling = Activite()
        self.add_custom_tab(self.sheduling, tab_name, "resources/icons/multi_fbb.ico")
    def open_manuelle_window(self):
        from Home.homerun import MainWindow
        tab_name = self.tr("🚀 Run")
        existing_tab_index = self.find_tab_by_name(tab_name)
        if existing_tab_index != -1:
            self.tab_widget.setCurrentIndex(existing_tab_index)
            return
        if not hasattr(self, ' 🚀 Run') or self.Manu is None:
            self.Manu = MainWindow(parent=self)
        self.add_custom_tab(self.Manu, tab_name, "resources/icons/multi_sfb.ico")
    def open_persona_window(self):
        tab_name = self.tr("statistiques")
        existing_tab_index = self.find_tab_by_name(tab_name)
        if existing_tab_index != -1:
            self.tab_widget.setCurrentIndex(existing_tab_index)
            return
        loading_screen = LoadingScreen(self)
        loading_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(loading_screen)
        loading_widget.setLayout(layout)
        new_tab_index = self.add_custom_ta(loading_widget, tab_name, "resources/icons/multi_fb.ico")
        if new_tab_index is None:
            raise RuntimeError("Failed to add a new tab. add_custom_tab returned None.")
        self.tab_widget.setCurrentIndex(new_tab_index)
        QTimer.singleShot(1000, lambda: self.load_statistics_content(new_tab_index))
    def open_statistics_window(self):
        tab_name = self.tr("statistiques")
        existing_tab_index = self.find_tab_by_name(tab_name)
        if existing_tab_index != -1:
            self.tab_widget.setCurrentIndex(existing_tab_index)
            return
        loading_screen = LoadingScreen(self)
        loading_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(loading_screen)
        loading_widget.setLayout(layout)
        new_tab_index = self.add_custom_ta(loading_widget, tab_name, "resources/icons/multi_fb.ico")
        if new_tab_index is None:
            raise RuntimeError("Failed to add a new tab. add_custom_tab returned None.")
        self.tab_widget.setCurrentIndex(new_tab_index)
        QTimer.singleShot(1000, lambda: self.load_statistics_content(new_tab_index))
    def open_imports_window(self):
        tab_name = self.tr("imports")
        existing_tab_index = self.find_tab_by_name(tab_name)
        if existing_tab_index != -1:
            self.tab_widget.setCurrentIndex(existing_tab_index)
            return
        if not hasattr(self, 'imports') or self.settings is None:
            self.settings = Nova360Ultimate(main_app=self)
        self.add_custom_tab(self.settings, tab_name, "resources/icons/multi_fb.ico")
    def add_on_page(self):
        from Installsweb.installdisign import InstallerDialog
        installer = InstallerDialog(self)
        installer.exec_()
    def open_telecommande_window(self):
        tab_name = self.tr("Remote Control")
        existing_tab_index = self.find_tab_by_name(tab_name)
        if existing_tab_index != -1:
            self.tab_widget.setCurrentIndex(existing_tab_index)
            return
        if not hasattr(self, 'telecommande') or self.telecommande is None:
            self.telecommande = SplitScreenView(main_app=self)
        self.add_custom_tab(self.telecommande, tab_name, "resources/icons/multi_fb.ico")
    def open_installer_window(self):
        from Installsweb.installdisign import InstallerPage
        tab_name = self.tr("Installer Premium")
        existing_tab_index = self.find_tab_by_name(tab_name)
        if existing_tab_index != -1:
            self.tab_widget.setCurrentIndex(existing_tab_index)
            return
        installer_page = InstallerPage(self)
        new_tab_index = self.add_custom_ta(installer_page, tab_name, "resources/icons/installer.ico")
        if new_tab_index is None:
            raise RuntimeError("Failed to add a new tab.")
        self.tab_widget.setCurrentIndex(new_tab_index)
    def connect_via_ssh(self):
        import atexit
        from online.online1 import RemoteAccessModal
        modal = RemoteAccessModal(self)
        modal.exec_()
        atexit.register(self.cleanup)
    def cleanup(self):
        if hasattr(self, 'remote_manager') and self.remote_manager.server:
            self.remote_manager.stop_server()
    def open_instance(self):
        tab_name = self.tr("Instances")
        existing_tab_index = self.find_tab_by_name(tab_name)
        if existing_tab_index != -1:
            self.tab_widget.setCurrentIndex(existing_tab_index)
            return
        if not hasattr(self, 'Instances') or self.instances is None:
            self.instances =InstanceTable(self)
        self.add_custom_tab(self.instances, tab_name, "resources/icons/multi_fb.ico")
    def open_upgrade_window(self):
        tab_name = self.tr("🚀 Upgrade")
        self.add_new_tab(QUrl("https://www.nova360.turknovatech.com/pricing"), tab_name, "resources/icons/tokk.ico")
        from Upgrade.upgrade import ContactDialog
        self.upgrades = ContactDialog()
        self.upgrades.show()
        existing_tab_index = self.find_tab_by_name(tab_name)
        if existing_tab_index != -1:
            self.tab_widget.setCurrentIndex(existing_tab_index)
            return
        if not hasattr(self, 'upgrades') or self.upgrades is None:
            from Upgrade.upgrade import ContactDialog
            self.upgrades = ContactDialog(parent=self)
            self.upgrades.show()
        self.add_custom_tab(self.upgrades, tab_name, "resources/icons/multi_fb.ico")
    def open_contact_window(self):
        self.add_new_tab(QUrl("https://script.google.com/macros/s/AKfycbzjBEtoeGcosEFv7yULAxa4RdPdTWUb7Tovtlr6Ym4EkDdttIYz2SU1s5HUHmqSaIDk1Q/exec"), self.tr("Contact"), "resources/icons/multi_fb.ico")
    def open_strategies_window(self):
        tab_name = self.tr("strategies")
        existing_tab_index = self.find_tab_by_name(tab_name)
        if existing_tab_index != -1:
            self.tab_widget.setCurrentIndex(existing_tab_index)
            return
        if not hasattr(self, 'strategies') or self.settings is None:
            self.settings = Nova360Ultimate(main_app=self)
        self.add_custom_tab(self.settings, tab_name, "resources/icons/multi_fb.ico")
    def find_tab_by_name(self, name):
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == name:
                return i
        return -1
    def close_tab(self, index):
        if self.tab_widget.count() > 1:
            self.tab_widget.removeTab(index)
    def update_search_bar_visibility(self, index):
        current_widget = self.tab_widget.widget(index)
        if isinstance(current_widget, QWebEngineView):
            self.url_bar.show()
        else:
            self.url_bar.hide()
    def tab_widget_style(self):
        return """
        QTabWidget::pane { border: 0; }
        QTabBar::tab {
            background: #3A3A3A;
            color: #FFFFFF;
            padding: 5px 15px;
            margin: 2px;
            border-radius: 5px;
        }
        QTabBar::tab:selected {
            background: #555555;
        }
        QTabBar::tab:hover {
            background: #4A4A4A;
        }
        """
    def create_search_bar(self, layout):
        search_bar_frame = QFrame()
        search_bar_frame.setStyleSheet("background-color: #333;")
        search_bar_layout = QHBoxLayout(search_bar_frame)
        search_bar_layout.setContentsMargins(5, 5, 5, 5)
        self.back_button = QPushButton("<")
        self.forward_button = QPushButton(">")
        self.refresh_button = QPushButton("⟳")
        self.home_button = QPushButton("🏠")
        for btn in [self.back_button, self.forward_button, self.refresh_button, self.home_button]:
            btn.setFixedSize(30, 30)
            btn.setStyleSheet(self.button_style())
            search_bar_layout.addWidget(btn)
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText(self.tr("Search or enter URL"))
        self.url_bar.setStyleSheet(self.url_bar_style())
        search_bar_layout.addWidget(self.url_bar, stretch=1)
        self.back_button.clicked.connect(self.navigate_back)
        self.forward_button.clicked.connect(self.navigate_forward)
        self.refresh_button.clicked.connect(self.refresh_page)
        self.home_button.clicked.connect(self.open_accueil_window)
        self.url_bar.returnPressed.connect(self.load_url)
        layout.addWidget(search_bar_frame)
        self.new_tab_button = QPushButton("+")
        self.new_tab_button.setFixedSize(30, 30)
        self.new_tab_button.setStyleSheet(self.button_style())
        self.new_tab_button.clicked.connect(self.open_new_tab)
        search_bar_layout.addWidget(self.new_tab_button)
    def button_style(self):
        return """
        QPushButton {
            background-color: #3A3A3A;
            color: #FFFFFF;
            border: none;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #555555;
        }
        QPushButton:pressed {
            background-color: #2A2A2A;
        }
        """
    def url_bar_style(self):
        return """
        QLineEdit {
            background-color: #3A3A3A;
            color: #FFFFFF;
            border: 1px solid #555555;
            border-radius: 5px;
            padding: 5px;
        }
        QLineEdit:focus {
            border: 1px solid #AAAAAA;
        }
        """
    def navigate_back(self):
        current_browser = self.tab_widget.currentWidget()
        if isinstance(current_browser, QWebEngineView):
            current_browser.back()
    def navigate_forward(self):
        current_browser = self.tab_widget.currentWidget()
        if isinstance(current_browser, QWebEngineView):
            current_browser.forward()
    def refresh_page(self):
        current_browser = self.tab_widget.currentWidget()
        if isinstance(current_browser, QWebEngineView):
            current_browser.reload()
    def load_url(self):
        current_browser = self.tab_widget.currentWidget()
        url = QUrl(self.url_bar.text())
        if url.scheme() == "":
            url.setScheme("http")
        current_browser.setUrl(url)
    def open_new_tab(self, tab_name="Dashboard", icon_path="resources/icons/tok.ico"):
        self.add_new_tab(QUrl("https://leopardo-ai.web.app/"), self.tr("Leopardo"), "resources/icons/tok.ico")
    def add_new_tab(self, content, label, icon_path="resources/icons/tok.ico"):
        existing_tab_index = self.find_tab_by_name(label)
        if existing_tab_index != -1:
            self.tab_widget.setCurrentIndex(existing_tab_index)
            return
        if isinstance(content, QUrl):
            browser = QWebEngineView()
            browser.setUrl(content)
            browser.setStyleSheet("""
                QWebEngineView {
                    background-color: white;
                    color: black;
                }
            """)
            widget_to_add = browser
        elif isinstance(content, QWidget):
            content.setStyleSheet("""
                QWidget {
                    background-color: white;
                    color: black;
                }
            """)
            widget_to_add = content
        else:
            raise TypeError(f"Unsupported type for 'content': {type(content)}")
        index = self.tab_widget.addTab(widget_to_add, "")
        self.tab_widget.setTabIcon(index, QIcon(icon_path))
        self.tab_widget.setTabText(index, label)
        self.tab_widget.setCurrentIndex(index)
        if isinstance(content, QUrl):
            widget_to_add.urlChanged.connect(self.update_url)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                background: white;
            }
            QTabWidget::tab-bar {
                background: lightgray;
            }
            QTabBar::tab {
                background: lightgray;
                color: black;
                padding: 5px;
            }
            QTabBar::tab:selected {
                background: white;
                color: black;
            }
        """)
    def add_custom_tab(self, widget, title, icon_path=None):
        if not hasattr(self, "tab_widget"):
            print("Error: The 'Browser' object does not have a 'tab_widget' attribute.")
            return
        index = self.tab_widget.addTab(widget, title)
        if icon_path:
            icon = QIcon(icon_path)
            self.tab_widget.setTabIcon(index, icon)
        self.tab_widget.setCurrentIndex(index)
    def add_custom_ta(self, widget, tab_name, icon_path):
        icon = QIcon(icon_path) if icon_path else QIcon()
        new_tab_index = self.tab_widget.addTab(widget, icon, tab_name)
        return new_tab_index
    def load_statistics_content(self, tab_index):
        if tab_index < 0 or tab_index >= self.tab_widget.count():
            print(f"Invalid tab index: {tab_index}")
            return
        try:
            license_checker = LicenseChecker(license_dir="C:\\bon")
            file_path = 'C:\\bon\\robot1\\data.json'
            group_counter = GroupCounter(file_path)
            Nombregroup = group_counter.count_groups()
            dash = Dashboard(
                title="wa+ CRM",
                subtitle="Analytics Overview",
                validiter=license_checker.is_license_valid(),
                Nombregroupes=Nombregroup,
                totalshare="Total partagé",
                nexttimeshare="Aucune"
            )
            self.tab_widget.removeTab(tab_index)
            self.add_custom_ta(dash, self.tr("statistiques"), "resources/icons/multi_fb.ico")
        except Exception as e:
            print(f"Erreur lors du chargement des statistiques : {e}")
    def init_language(self):
        import json, os
        user_data_dir = os.path.join(os.path.expanduser('~'), 'Leopardo')
        try:
            if os.path.exists(os.path.join(user_data_dir, 'resources', 'settings.json')):
                with open(os.path.join(user_data_dir, 'resources', 'settings.json'), 'r') as f:
                    preferences = json.load(f)
                    selected_language = preferences.get('language', 'en')
            else:
                system_locale = QLocale.system().name()[:2]
                language_map = {'en': 'en', 'fr': 'fr', 'tr': 'tr', 'ar': 'ar'}
                selected_language = language_map.get(system_locale, 'en')
        except (FileNotFoundError, json.JSONDecodeError):
            selected_language = 'en'
        self.switch_language(selected_language)
    def switch_language(self, language):
        import os
        user_data_dir = os.path.join(os.path.expanduser('~'), 'Leopardo')
        translator_path = os.path.join(user_data_dir, 'resources', 'lang', language, 'modules', 'main_fb_robot_translated.qm')
        if os.path.exists(translator_path):
            self.translator.load(translator_path)
        else:
            self.translator.load("")
        QApplication.instance().installTranslator(self.translator)
        self.save_language_choice(language)
        self.retranslateUi()
        self.show_success_message(self.tr("Language changed successfully!"))
    def save_language_choice(self, language):
        import json, os
        user_data_dir = os.path.join(os.path.expanduser('~'), 'Leopardo')
        preferences = {'language': language}
        with open(os.path.join(user_data_dir, 'resources', 'settings.json'), 'w') as f:
            json.dump(preferences, f)
    def retranslateUi(self):
        self.setWindowTitle(self.tr('AI FB ROBOT Pro'))
    def show_success_message(self, message):
        label = QLabel(message, self)
        label.setStyleSheet("""
            QLabel {
                background-color: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }
        """)
        label.setAlignment(Qt.AlignCenter)
        label.setWindowFlags(Qt.FramelessWindowHint | Qt.ToolTip)
        label.adjustSize()
        label.move(
            (self.width() - label.width()) // 2,
            (self.height() - label.height()) // 2
        )
        label.show()
        QTimer.singleShot(3000, label.close)
    def load_menu_config(self):
        pass
    def update_menu_visibility(self):
        pass
    def minimize_window(self):
        self.showMinimized()
    def maximize_window(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
    def close_window(self):
        self.close()
    def update_url(self, url):
        self.url_bar.setText(url.toString())
    def open_accueil_window(self):
        from Installsweb.installdisign import InstallerPage
        tab_name = self.tr("Home")
        existing_tab_index = self.find_tab_by_name(tab_name)
        if existing_tab_index != -1:
            self.tab_widget.setCurrentIndex(existing_tab_index)
            return
        installer_page = MainWindow1(main_app=self)
        new_tab_index = self.add_custom_ta(installer_page, tab_name, "resources/icons/installer.ico")
        if new_tab_index is None:
            raise RuntimeError("Failed to add a new tab.")
        self.tab_widget.setCurrentIndex(new_tab_index)
    def switch_to_enterprise(self):
        self.is_enterprise_mode = True
        self.update_user_buttons()
    def switch_to_personal(self):
        self.is_enterprise_mode = False
        self.update_user_buttons()
    def update_user_buttons(self):
        pass
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Browser()
    window.show()
    sys.exit(app.exec_())
