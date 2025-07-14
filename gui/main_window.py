# -*- coding: utf-8 -*-
import sys
import os

# --- sys.path MODIFICATION REMOVED ---
# Relying on main.py to set up sys.path correctly.
# _PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# if _PROJECT_ROOT not in sys.path:
#    sys.path.insert(0, _PROJECT_ROOT)
# ---

from PyQt5.QtCore import QDate
import logging

# --- BEGIN WORKAROUND for ModuleNotFoundError ---
# This workaround is removed as sys.path is now primarily managed by main.py
# and this file (gui/main_window.py) is no longer at the project root.
# Ensure the project root is in sys.path when main_window.py is loaded.
# This is a targeted fix for environments where main.py's sys.path modification
# might not be effective for all imports within main_window.py.
# _PROJECT_ROOT_MW = None
# try:
#     _current_file_path_mw = os.path.abspath(__file__)
#     _main_window_dir_mw = os.path.dirname(_current_file_path_mw)
#     # Assuming main_window.py is in the project root.
#     # If main_window.py is in a subdirectory, this logic needs to be adjusted
#     # to find the actual project root (e.g., os.path.dirname(_main_window_dir_mw) for one level up).
#     _PROJECT_ROOT_MW = _main_window_dir_mw
#
#     if _PROJECT_ROOT_MW not in sys.path:
#         sys.path.insert(0, _PROJECT_ROOT_MW)
#         # print(f"[MW_WORKAROUND] Added {_PROJECT_ROOT_MW} to sys.path[0]")
#     elif sys.path[0] != _PROJECT_ROOT_MW:
#         sys.path.remove(_PROJECT_ROOT_MW)
#         sys.path.insert(0, _PROJECT_ROOT_MW)
#         # print(f"[MW_WORKAROUND] Moved {_PROJECT_ROOT_MW} to sys.path[0]")
#     # else:
#         # print(f"[MW_WORKAROUND] {_PROJECT_ROOT_MW} already at sys.path[0]")
#
# except Exception as e_mw_path_setup:
#     # Use basic print here as logging might not be configured yet or could fail.
#     print(f"Error in main_window.py sys.path WORKAROUND: {e_mw_path_setup}. Project root may not be set correctly: {_PROJECT_ROOT_MW}")
# --- END WORKAROUND ---

# import logging # logging is already imported
import logging

from datetime import datetime # Added datetime import
from PyQt5.QtCore import QStringListModel
import functools # Ajouté pour partial

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit,
    QListWidget, QListWidgetItem,
    QFileDialog, QMessageBox, QDialog, QFormLayout, QComboBox,
    QInputDialog, QCompleter, QTabWidget, QAction, QMenu, QGroupBox,
    QStackedWidget, QDoubleSpinBox, QTableWidget, QTableWidgetItem, QAbstractItemView,
    QTextEdit, QSplitter, QApplication, QToolButton # Added QToolButton for inline actions

)
from PyQt5.QtGui import QIcon, QDesktopServices, QFont
from PyQt5.QtCore import Qt, QUrl, QTimer, pyqtSlot, QByteArray, QDate, QEvent # Added QDate and QEvent
# QWebEngineView might still be used by ClientWidget or other parts, so keep for now unless confirmed unused.
from PyQt5.QtWebEngineWidgets import QWebEngineView
# from PyQt5.QtWebChannel import QWebChannel # QWebChannel removed as DocumentManager no longer uses its own map.

import db as db_manager
from db.cruds.clients_crud import clients_crud_instance
from db.cruds.products_crud import products_crud_instance

import icons_rc
# import folium # No longer used directly by DocumentManager for its own map
# from statistics_module import MapInteractionHandler # DocumentManager no longer has its own map handler instance
from app_setup import APP_ROOT_DIR, CONFIG
# from ui_components import StatisticsWidget # StatisticsWidget removed from main_layout
from gui.ui_components import StatusDelegate # Still used for QListWidget
from gui.dialogs.map_client_dialog import MapClientDialog # Added for new client from map
# The get_country_by_name, get_or_add_country, etc. specific imports for handle_add_client_from_stats_map might become obsolete.
from db import get_country_by_name, get_or_add_country, get_city_by_name_and_country_id, get_or_add_city

from dialogs.statistics_add_client_dialog import StatisticsAddClientDialog # Import the new dialog

from utils.document_manager_logic import (
    handle_create_client_execution,
    load_and_display_clients,
    filter_and_display_clients,
    perform_old_clients_check,
    handle_open_edit_client_dialog,
    archive_client_status,
    permanently_delete_client
)
from dialogs import (
    TemplateDialog, AddNewClientDialog, ManageProductMasterDialog
)
# Removed: SettingsDialog as OriginalSettingsDialog, TransporterDialog, FreightForwarderDialog
# from product_management.list_dialog import ProductListDialog # Removed

# --- BEGIN TARGETED sys.path FIX for product_management import ---
# This workaround is removed as sys.path is now primarily managed by main.py
# import sys # Ensure sys is imported if not already (it is at the top)
# import os  # Ensure os is imported if not already (it is at the top)
# try:
#     _mw_file_path = os.path.abspath(__file__)
#     _project_root_for_pm = os.path.dirname(_mw_file_path) # Assuming main_window.py is in project root
#
#     if _project_root_for_pm not in sys.path:
#         sys.path.insert(0, _project_root_for_pm)
#     elif sys.path[0] != _project_root_for_pm:
#         sys.path.remove(_project_root_for_pm)
#         sys.path.insert(0, _project_root_for_pm)
# except Exception:
#     # Silently pass on error during this specific fix, relying on global error handling
#     # or allowing the ModuleNotFoundError to naturally occur if this fails.
#     pass
# --- END TARGETED sys.path FIX ---

# --- BEGIN Local sys.path adjustment in gui/main_window.py ---
# This is a targeted fix to ensure product_management can be imported from here.
# os and sys modules are imported at the top of this file.
try:
    _gui_main_window_file_path = os.path.abspath(__file__)
    _gui_dir = os.path.dirname(_gui_main_window_file_path)
    _project_root_local_calc = os.path.dirname(_gui_dir) # Project root is parent of 'gui'

    if _project_root_local_calc not in sys.path:
        sys.path.insert(0, _project_root_local_calc)
        print(f"DEBUG gui/main_window.py (LOCAL SYS.PATH MOD): Inserted project root {_project_root_local_calc}. New sys.path: {sys.path}")
    elif sys.path[0] != _project_root_local_calc:
        if _project_root_local_calc in sys.path: # Check before removing
             sys.path.remove(_project_root_local_calc)
        sys.path.insert(0, _project_root_local_calc)
        print(f"DEBUG gui/main_window.py (LOCAL SYS.PATH MOD): Moved project root {_project_root_local_calc} to start. New sys.path: {sys.path}")
    # else:
        # print(f"DEBUG gui/main_window.py (LOCAL SYS.PATH MOD): Project root {_project_root_local_calc} already at sys.path[0].")
except Exception as e_local_sys_path_mod:
    print(f"ERROR in gui/main_window.py local sys.path modification: {e_local_sys_path_mod}")
# --- END Local sys.path adjustment ---

print(f"DEBUG: Current sys.path before product_management import: {sys.path}")
print(f"DEBUG: Current working directory before product_management import: {os.getcwd()}")

from product_management.page import ProductManagementPage # Added
from PyQt5.QtWidgets import QSizePolicy

from dialogs.status_management_dialog import StatusManagementDialog # Added for status management
from dialogs.manage_saved_filters_dialog import ManageSavedFiltersDialog # Import for managing saved filters

from PyQt5.QtWidgets import QDateEdit


# Updated import for the refactored client widget
from client_management.ui.client_main_widget import ClientMainWidget
from client_management.client_controller import ClientController # Import ClientController
from project_management import MainDashboard as ProjectManagementDashboard
from statistics import StatisticsDashboard, StatisticsSummaryWidget # Updated import
from statistics.map_widget import HomePageMapWidget # Import HomePageMapWidget
# from statistics_panel import CollapsibleStatisticsWidget # Unused in main_window

from utils import save_config
from company_management import CompanyTabWidget
from settings.settings_page import SettingsPage # Import the new SettingsPage
from botpress_integration.ui_components import BotpressIntegrationUI # Import Botpress UI
from dialogs.carrier_map_dialog import CarrierMapDialog # Import CarrierMapDialog
from voice_input_service import VoiceInputService # Added import

from partners.partner_main_widget import PartnerMainWidget # Partner Management
from gui.widgets.inventory_browser_widget import InventoryBrowserWidget # Inventory Management
from camera_management.camera_management_widget import CameraManagementWidget # Camera Management

from PyQt5.QtGui import QColor, QPalette # For ClientListItemWidget text color

from recruitment.recruitment_dashboard import RecruitmentDashboard # Import RecruitmentDashboard

from ui.home.home_page_widget import HomePageWidget # Updated import path
from gui.widgets.experience_module_widget import ExperienceModuleWidget # Added
from services.download_monitor_service import DownloadMonitorService
from dialogs.assign_document_dialog import AssignDocumentToClientDialog
from db.cruds.client_documents_crud import add_client_document # For assign dialog
import os # For path checks in download monitor init
from db.cruds import user_saved_filters_crud # Import for saved filters

from calendar_module.calendar_widget import CalendarWidget # Import CalendarWidget
from user_management.page import UserManagementPage # Import UserManagementPage

from calculator.main_calculator_widget import MainCalculatorWidget # Import Calculator Widget
# from db.connection import SessionLocal as AppSessionLocal_MW # Import SessionLocal for calculator
from user_management.user_menu_button import UserMenuButton # Import UserMenuButton
from dialogs.edit_user_dialog import EditUserDialog # For handling edit/add user requests
from dialogs.role_management_dialog import RoleManagementDialog # Added for Role Management
from commande_management.commandes_dashboard_widget import CommandesDashboardWidget # Import CommandesDashboardWidget
from utils.app_constants import CONFIGURABLE_MODULES # Import from new location
from gui.widgets.sidebar_navigation_widget import SidebarNavigationWidget # Import de la Sidebar
from gui.widgets.notification_panel import NotificationPanel
from gui.widgets.categorized_completer import CategorizedCompleter, CategoryDelegate


# B2C Restaurant Module Import
from b2c.ges_restaurant.ui.main_widget import RestaurantMainWidget


# License Management Imports for feature constants and manager
from license_management import manager as license_manager # To call get_allowed_features
from license_management import (
    FEATURE_BASIC_CLIENT_DOCS, FEATURE_PROJECT_MANAGEMENT, FEATURE_STATISTICS_MODULE,
    FEATURE_PRODUCT_MANAGEMENT, FEATURE_PARTNER_MANAGEMENT, FEATURE_INVENTORY_MANAGEMENT,
    FEATURE_RECRUITMENT_MODULE, FEATURE_BOTPRESS_INTEGRATION, FEATURE_CALENDAR_MODULE,
    FEATURE_EXPERIENCE_MANAGEMENT, FEATURE_ADVANCED_REPORTING, FEATURE_API_ACCESS,
    FEATURE_USER_MANAGEMENT_FULL, FEATURE_SETTINGS_MANAGEMENT,
    FEATURE_COMMANDES_MANAGEMENT, FEATURE_CALCULATOR_MODULE
)

# Import for menu customization
from dialogs.menu_customization_dialog import MenuCustomizationDialog
from utils.app_constants import CONFIGURABLE_MODULES # For menu customization and default order
import json # For handling menu config storage
import random
from PyQt5.QtCore import pyqtSignal, QTimer, QEasingCurve, pyqtProperty # Added QTimer, QEasingCurve
from PyQt5.QtGui import QColor, QLinearGradient, QPalette # Added QColor
from PyQt5.QtWidgets import QGraphicsDropShadowEffect # Added QGraphicsDropShadowEffect
from PyQt5.QtCore import QPropertyAnimation # Added QPropertyAnimation
from PyQt5.QtWidgets import QFrame
from PyQt5.QtCore import QSize



class ClientListItemWidget(QWidget):
    # Signaux pour les actions en ligne
    editActionClicked = pyqtSignal()
    openFolderActionClicked = pyqtSignal()
    # archiveActionClicked = pyqtSignal() # Optionnel pour V1

    def __init__(self, client_data, parent=None):
        super().__init__(parent)
        self.client_data = client_data
        self.doc_manager = parent
        while self.doc_manager and not isinstance(self.doc_manager, DocumentManager):
            self.doc_manager = self.doc_manager.parent()

        self.init_ui()
        self.setMouseTracking(True) # Important pour enterEvent/leaveEvent sur le widget lui-même

    def _tr(self, text):
        if self.doc_manager and hasattr(self.doc_manager, 'tr'):
            return self.doc_manager.tr(text)
        return QApplication.translate("ClientListItemWidget", text)

    def init_ui(self):
        self.main_h_layout = QHBoxLayout(self) # Renommé pour clarté
        self.main_h_layout.setContentsMargins(8, 5, 8, 5)
        self.main_h_layout.setSpacing(8)

        # Status Indicator
        self.status_indicator_label = QLabel()
        self.status_indicator_label.setFixedSize(12, 12) # Circular indicator
        self.status_indicator_label.setStyleSheet("border-radius: 6px; background-color: #343A40;") # Default color

        # Text content layout (Client Name and Additional Info)
        text_content_layout = QVBoxLayout()
        text_content_layout.setContentsMargins(0,0,0,0)
        text_content_layout.setSpacing(2)

        self.client_name_label = QLabel() # Will be set in update_data
        self.client_name_label.setObjectName("clientNameInList") # For QSS styling
        font = self.client_name_label.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 1) # Slightly larger
        self.client_name_label.setFont(font)
        self.client_name_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        text_content_layout.addWidget(self.client_name_label)

        self.additional_info_label = QLabel() # Will be set in update_data
        self.additional_info_label.setObjectName("clientAdditionalInfoInList") # For QSS styling
        font_additional = self.additional_info_label.font()
        font_additional.setPointSize(font_additional.pointSize() -1) # Slightly smaller
        self.additional_info_label.setFont(font_additional)
        self.additional_info_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        palette = self.additional_info_label.palette()
        palette.setColor(QPalette.WindowText, QColor(Qt.gray))
        self.additional_info_label.setPalette(palette)
        text_content_layout.addWidget(self.additional_info_label)

        self.main_h_layout.addWidget(self.status_indicator_label)
        self.main_h_layout.addLayout(text_content_layout)
        self.main_h_layout.addStretch(1)

        # Layout pour les actions en ligne (initialement masqué)
        self.actions_layout = QHBoxLayout()
        self.actions_layout.setContentsMargins(0,0,0,0)
        self.actions_layout.setSpacing(5)

        self.edit_action_button = QToolButton(self)
        self.edit_action_button.setObjectName("listItemActionButton")
        self.edit_action_button.setIcon(QIcon(":/icons/pencil.svg"))
        self.edit_action_button.setToolTip(self.tr("Modifier ce client"))
        self.edit_action_button.setCursor(Qt.PointingHandCursor)
        self.edit_action_button.clicked.connect(self._on_edit_action_clicked)
        self.actions_layout.addWidget(self.edit_action_button)

        self.folder_action_button = QToolButton(self)
        self.folder_action_button.setObjectName("listItemActionButton")
        self.folder_action_button.setIcon(QIcon(":/icons/folder.svg"))
        self.folder_action_button.setToolTip(self.tr("Ouvrir le dossier de ce client"))
        self.folder_action_button.setCursor(Qt.PointingHandCursor)
        self.folder_action_button.clicked.connect(self._on_folder_action_clicked)
        self.actions_layout.addWidget(self.folder_action_button)

        # Ajouter d'autres boutons d'action ici si nécessaire (ex: archiver)

        for i in range(self.actions_layout.count()): # Cacher les boutons individuellement
            widget = self.actions_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(False)

        self.main_h_layout.addLayout(self.actions_layout) # Ajouter le layout des actions au layout principal

        self.update_data(self.client_data)

        self.setAutoFillBackground(True)
        # Le style QSS pour ClientListItemWidget:hover sera dans style.qss

    def _on_edit_action_clicked(self):
        self.editActionClicked.emit()

    def _on_folder_action_clicked(self):
        self.openFolderActionClicked.emit()

    def enterEvent(self, event: QEvent):
        super().enterEvent(event)
        for i in range(self.actions_layout.count()):
            widget = self.actions_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(True)

    def leaveEvent(self, event: QEvent):
        super().leaveEvent(event)
        # Vérifier si le curseur n'est pas sur l'un des boutons d'action avant de les cacher
        # Ceci est une simple vérification; une gestion plus robuste pourrait être nécessaire
        # si les boutons sont très proches ou si le comportement de leaveEvent est complexe.
        # Pour l'instant, on cache si la souris quitte le widget principal.
        # Si le curseur est sur un bouton, le leaveEvent du bouton sera déclenché avant celui du parent.
        # Cependant, pour éviter que les boutons ne disparaissent pendant que la souris se déplace
        # entre le widget principal et un bouton d'action, on pourrait vérifier si le curseur
        # est DANS le rectangle du widget ClientListItemWidget.
        # Si la souris quitte le widget, on cache.
        # Si elle est sur un bouton, le bouton reste visible.
        # La solution simple:
        for i in range(self.actions_layout.count()):
            widget = self.actions_layout.itemAt(i).widget()
            if widget and not widget.geometry().contains(widget.mapFromGlobal(QCursor.pos())): # QCursor n'est pas importé
                 widget.setVisible(False)
            elif widget: # Si le curseur est dessus, on le laisse visible (le hover du bouton prendra le relais)
                 pass # Le bouton reste visible s'il est survolé, sera caché si la souris quitte le bouton ET le parent.

        # Une approche plus simple et souvent suffisante :
        # Si la souris n'est plus sur le ClientListItemWidget lui-même, on cache les actions.
        # Les boutons eux-mêmes géreront leur propre état de survol.
        if not self.rect().contains(self.mapFromGlobal(QCursor.pos())): # QCursor n'est pas importé
            for i in range(self.actions_layout.count()):
                widget = self.actions_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(False)
        # Correction: La logique ci-dessus est complexe et peut mal se comporter.
        # Le plus simple est de cacher les boutons lorsque la souris quitte le ClientListItemWidget.
        # Si la souris est sur un bouton, le leaveEvent du ClientListItemWidget ne sera pas
        # immédiatement déclenché tant que la souris est sur l'enfant.
        # Quand la souris quitte l'enfant ET le parent, alors on cache.
        # Pour simplifier et éviter des clignotements :
        # On cache toujours quand on quitte le ClientListItemWidget. Si la souris entre ensuite sur un bouton,
        # le bouton sera toujours visible car il est un enfant. Le problème est si le bouton
        # est caché alors que la souris est dessus.
        # Solution plus robuste pour leaveEvent:
        # Vérifier si la souris est DANS le rectangle du widget. Si non, on cache.
        # Cela ne fonctionne pas bien si les boutons sont au bord.
        # Le plus simple est de cacher au leaveEvent du ClientListItemWidget.
        # Le hover des QToolButton les gardera stylés.
        for i in range(self.actions_layout.count()): # Masquer tous les boutons lorsque la souris quitte le widget principal
            widget = self.actions_layout.itemAt(i).widget()
            if widget:
                 widget.setVisible(False)


    def update_data(self, client_data):
        self.client_data = client_data
        self.client_name_label.setText(self.client_data.get('client_name', self._tr('Client Inconnu')))

        project_identifier = self.client_data.get('project_identifier', '')
        country_name = self.client_data.get('country', '') # Assuming country name is now in client_data

        additional_parts = []
        if project_identifier:
            additional_parts.append(f"{self._tr('Projet:')} {project_identifier}")
        if country_name:
            additional_parts.append(country_name)

        self.additional_info_label.setText(" | ".join(additional_parts))
        self.additional_info_label.setVisible(bool(additional_parts))

        self._update_status_indicator()

    def _update_status_indicator(self):
        status_name_str = self.client_data.get("status", "")
        status_lower = status_name_str.lower() if status_name_str else ""

        color = "#343A40" # Default (Dark Grey/Black)
        if "actif" in status_lower or "active" in status_lower: color = "#28A745" # Green
        elif "prospect" in status_lower: color = "#007BFF" # Blue
        elif "inactif" in status_lower or "inactive" in status_lower: color = "#FFC107" # Yellow/Orange
        elif "archivé" in status_lower or "archived" in status_lower: color = "#6c757d" # Grey
        elif "complété" in status_lower or "completed" in status_lower: color = "#663399" # Purple

        self.status_indicator_label.setStyleSheet(f"border-radius: 6px; background-color: {color};")

    # _get_status_icon_html is no longer needed as we use a styled QLabel


class DocumentManager(QMainWindow):
    def __init__(self, app_root_dir, current_user_info: dict, current_license_info: dict | None):
        super().__init__()

        # Make the window frameless
        self.setWindowFlags(Qt.FramelessWindowHint | self.windowFlags())

        self._gradient_pos = 0.0
        self.app_root_dir = app_root_dir
        self.current_user_info = current_user_info # Store the full user info dictionary
        self.current_license_info = current_license_info # Store license information
        self.current_user_id = self.current_user_info.get('user_id') # Extract user_id for existing usage

        # Extract allowed features from license_info or get them using license_manager
        if self.current_license_info and 'allowed_features' in self.current_license_info:
            self.allowed_features = self.current_license_info['allowed_features']
            logging.info(f"Allowed features loaded from current_license_info: {self.allowed_features}")
        elif self.current_license_info and self.current_license_info.get('license_type'):
            self.allowed_features = license_manager.get_allowed_features(self.current_license_info['license_type'])
            logging.info(f"Allowed features derived using license_manager.get_allowed_features for type '{self.current_license_info['license_type']}': {self.allowed_features}")
        else:
            self.allowed_features = set() # Default to no features if license info is missing or incomplete
            logging.warning("No valid license information to determine allowed features. Defaulting to empty set.")

        logging.info(f"DocumentManager initialized for user: {self.current_user_info.get('username')}, Role: {self.current_user_info.get('role_name')}, License active: {self.current_license_info.get('is_active') if self.current_license_info else 'N/A'}")
        logging.info(f"Effective allowed features for this session: {self.allowed_features}")

        # Instantiate ClientController
        self.client_controller_instance = ClientController()
        # Later, self.notification_manager will be set up and can be passed if ClientController needs it.


        self.setWindowTitle(self.tr("Gestionnaire de Documents Client")); self.setGeometry(100, 100, 1200, 800)
        self.setWindowIcon(QIcon(":/icons/logo.svg"))
        
        self.config = CONFIG
        self.module_states = {} # Initialize module states
        self._load_module_states() # Load initial module states from DB

        self.download_monitor_service = None # Initialize download monitor service

        # Use get_setting with default, falling back to config, then to a hardcoded default.
        self.config['google_maps_review_url'] = db_manager.get_setting(
            'google_maps_review_url',
            default=self.config.get('google_maps_review_url', 'https://maps.google.com/?cid=YOUR_CID_HERE_FALLBACK_CONFIG')
        )

        self.clients_data_map = {}
        self.current_offset = 0
        self.limit_per_page = 50
        self.total_filtered_clients = 0  # Added for pagination
        
        # La Sidebar est initialisée avant setup_ui_main pour être disponible lors de la construction du layout
        # self.sidebar_nav = SidebarNavigationWidget(parent=self) # REMOVED Sidebar instantiation
        # self.sidebar_nav.moduleSelected.connect(self.handle_sidebar_module_selection) # REMOVED
        # self.sidebar_nav.expansionToggled.connect(self.handle_sidebar_expansion_toggled) # REMOVED

        self.setup_ui_main() # Sets up self.main_area_stack

        # Initialize core widget instances that are always needed or fundamental
        self.home_page_widget_instance = HomePageWidget(main_window=self, parent=self)
        self.main_area_stack.addWidget(self.home_page_widget_instance)

        self.settings_page_instance = SettingsPage(
            main_config=self.config,
            app_root_dir=self.app_root_dir,
            current_user_id=self.current_user_id,
            parent=self
        )
        self.main_area_stack.addWidget(self.settings_page_instance)

        self.user_management_page_instance = UserManagementPage(current_user_info=self.current_user_info, parent=self)
        self.main_area_stack.addWidget(self.user_management_page_instance)

        self.commandes_dashboard_widget_instance = CommandesDashboardWidget(
            parent=self,
            current_user_info=self.current_user_info,
            app_root_dir=self.app_root_dir
        )
        self.main_area_stack.addWidget(self.commandes_dashboard_widget_instance)

        # Documents page (client list and tabs) is setup in setup_ui_main and added to stack there.

        # Initialize all other module widget instance attributes to None for lazy loading
        self.project_management_widget_instance = None
        self.statistics_dashboard_instance = None
        self.partner_management_widget_instance = None
        self.product_management_page_instance = None
        self.botpress_integration_ui_instance = None
        self.inventory_browser_widget_instance = None
        self.recruitment_dashboard_instance = None
        self.camera_management_widget_instance = None
        self.experience_management_widget_instance = None
        self.calendar_module_widget_instance = None
        self.calculator_module_widget_instance = None
        self.restaurant_widget_instance = None # For B2C Restaurant Module
        
        # For HomePage related widgets that might depend on other modules (like statistics)
        self.statistics_summary_widget_instance = None
        self.home_page_map_widget_instance = None

        # Conditionally create statistics-related widgets for HomePage if stats module is enabled
        # These are not full pages but components of HomePage.
        if self.module_states.get('statistics', True):
            self.statistics_summary_widget_instance = StatisticsSummaryWidget(parent=self)
            # No need to add to stack, it's part of HomePageWidget's layout
            self.home_page_map_widget_instance = HomePageMapWidget(app_translator_func=self.tr, parent=self)
            # No need to add to stack, it's part of HomePageWidget's layout

            if self.home_page_widget_instance:
                if hasattr(self.home_page_widget_instance, 'set_right_sidebar_widget'):
                    self.home_page_widget_instance.set_right_sidebar_widget(self.statistics_summary_widget_instance)
                if hasattr(self.home_page_widget_instance, 'set_bottom_widget'):
                    self.home_page_widget_instance.set_bottom_widget(self.home_page_map_widget_instance)
        else: # statistics module disabled
            if self.home_page_widget_instance:
                if hasattr(self.home_page_widget_instance, 'set_right_sidebar_widget'):
                    self.home_page_widget_instance.set_right_sidebar_widget(None)
                if hasattr(self.home_page_widget_instance, 'set_bottom_widget'):
                    self.home_page_widget_instance.set_bottom_widget(None)

        self.searchable_actions_map = {} # Initialize for create_actions_main

        # For App Title Animation - Initialize shadow effect before menus are created
        self.app_title_shadow_effect = QGraphicsDropShadowEffect(self)
        # self.app_title_label will be set in create_menus_main

        # Création des actions et menus (le menu Modules sera supprimé plus tard)
        self.create_actions_main(); self.create_menus_main()

        # REMOVED: Peupler la sidebar et définir son état initial
        # self._populate_sidebar()
        # try:
        #     saved_expanded_state = db_manager.get_setting('sidebar_expanded_state', default='True')
        #     initial_expanded_state = saved_expanded_state.lower() == 'true'
        # except Exception as e:
        #     logging.error(f"Error reading sidebar_expanded_state: {e}", exc_info=True)
        #     initial_expanded_state = True # Default to expanded if error
        # self.sidebar_nav.set_expanded_state(initial_expanded_state, animate=False)

        # Définir la vue d'accueil comme vue initiale
        self.main_area_stack.setCurrentWidget(self.home_page_widget_instance)
        # REMOVED: self.sidebar_nav.set_active_module('home')

        logging.debug("--- Widgets in main_area_stack after DocumentManager.__init__ (lazy loading setup) ---")
        for i in range(self.main_area_stack.count()):
            widget = self.main_area_stack.widget(i)
            logging.debug(f"  Index {i}: {widget} (Type: {type(widget).__name__})")
        logging.debug("-----------------------------------------------------------------")

        self.voice_input_service = VoiceInputService()

        QTimer.singleShot(0, self.load_clients_from_db_slot)
        self.check_timer = QTimer(self); self.check_timer.timeout.connect(self.check_old_clients_routine_slot); self.check_timer.start(3600000)
        self.init_or_update_download_monitor()
        self.populate_saved_filters_combo()

        # For App Title Animation
        # self.app_title_label is set in create_menus_main
        # self.app_title_shadow_effect is initialized earlier
        self.app_title_animation = QPropertyAnimation(self.app_title_shadow_effect, b"color", self)
        self.blur_animation = QPropertyAnimation(self.app_title_shadow_effect, b"blurRadius", self)
        self.gradient_animation = QPropertyAnimation(self, b"_gradient_position", self)
        self.app_title_animation_timer = QTimer(self)
        self.animation_sequences = []
        self.current_sequence_index = 0
        self._gradient_pos = 0.0

        self._setup_app_title_animation()



    def toggleMaximized(self):
        """Toggles between maximized and normal window state."""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _load_animation_styles(self):
        """Loads animation sequences from a JSON file."""
        try:
            animations_file_path = os.path.join(self.app_root_dir, "resources", "styles", "animations.json")
            logging.info(f"Loading animation sequences from: {animations_file_path}")
            with open(animations_file_path, 'r', encoding='utf-8') as f:
                animation_data = json.load(f)
                self.animation_sequences = animation_data.get("sequences", [])
            if not self.animation_sequences:
                logging.warning("Animation sequences file is empty or invalid.")
                self._create_default_animation_sequences()
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Could not load or parse animation sequences: {e}", exc_info=True)
            self._create_default_animation_sequences()

    def _create_default_animation_sequences(self):
        """Creates default animation sequences if the JSON file is missing or corrupt."""
        logging.info("Creating default animation sequences.")
        self.animation_sequences = [
            {"type": "calm", "duration": 20000},
            {"type": "glow_pulse", "duration": 10000, "start_color": "#3b82f6", "end_color": "#2563eb", "start_blur": 10, "end_blur": 25}
        ]


    def _setup_app_title_animation(self):
        if not self.app_title_label:
            logging.warning("App title label not initialized, cannot setup animation.")
            return

        self._load_animation_styles()
        if not self.animation_sequences:
            logging.error("No animation sequences loaded, cannot setup title animation.")
            return

        self.app_title_animation_timer.setSingleShot(True)
        self.app_title_animation_timer.timeout.connect(self._start_next_sequence)
        self._start_next_sequence()

    @pyqtProperty(float)
    def _gradient_position(self):
        return self._gradient_pos

    @_gradient_position.setter
    def _gradient_position(self, pos):
        self._gradient_pos = pos
        self._update_gradient()

    def _update_gradient(self):
        if not hasattr(self, 'gradient_animation_running') or not self.gradient_animation_running:
            return

        palette = self.app_title_label.palette()
        gradient = QLinearGradient(0, 0, self.app_title_label.width(), 0)

        # Clamping the gradient position to the valid range of 0 to 1
        start_pos = max(0, self._gradient_pos - 0.5)
        end_pos = min(1, self._gradient_pos + 0.5)

        gradient.setColorAt(start_pos, QColor(self.gradient_start_color))
        gradient.setColorAt(self._gradient_pos, QColor(self.gradient_end_color))
        gradient.setColorAt(end_pos, QColor(self.gradient_start_color))

        palette.setBrush(QPalette.WindowText, gradient)
        self.app_title_label.setPalette(palette)

    def _start_next_sequence(self):
        if not self.animation_sequences:
            return

        # Choose a random sequence
        sequence = random.choice(self.animation_sequences)

        seq_type = sequence.get("type")
        duration = sequence.get("duration", 1000)

        logging.debug(f"Starting animation sequence: {seq_type} for {duration}ms")
        self.gradient_animation_running = False
        self.app_title_label.setPalette(QApplication.style().standardPalette())


        if seq_type == "calm":
            self.app_title_shadow_effect.setColor(QColor(0,0,0,0))
            self.app_title_shadow_effect.setBlurRadius(0)
        elif seq_type == "glow_pulse":
            self.app_title_animation.setDuration(duration // 2)
            self.app_title_animation.setLoopCount(2)
            self.app_title_animation.setStartValue(QColor(sequence["start_color"]))
            self.app_title_animation.setEndValue(QColor(sequence["end_color"]))
            self.app_title_animation.start()

            self.blur_animation.setDuration(duration // 2)
            self.blur_animation.setLoopCount(2)
            self.blur_animation.setStartValue(sequence["start_blur"])
            self.blur_animation.setEndValue(sequence["end_blur"])
            self.blur_animation.start()
        elif seq_type == "subtle_glow":
            self.app_title_shadow_effect.setColor(QColor(sequence["color"]))
            self.app_title_shadow_effect.setBlurRadius(sequence["blur"])
        elif seq_type == "typewriter":
            self.app_title_label.setText("")
            self.typewriter_timer = QTimer(self)
            self.typewriter_text = "Leopardo ERP"
            self.typewriter_index = 0
            self.typewriter_timer.timeout.connect(self._typewriter_update)
            self.typewriter_timer.start(duration // len(self.typewriter_text))
        elif seq_type == "color_slide":
            self.gradient_animation_running = True
            self.gradient_start_color = sequence["start_color"]
            self.gradient_end_color = sequence["end_color"]
            self.gradient_animation.setDuration(duration)
            self.gradient_animation.setStartValue(0)
            self.gradient_animation.setEndValue(1)
            self.gradient_animation.start()


        self.app_title_animation_timer.start(duration)

    def _typewriter_update(self):
        if self.typewriter_index < len(self.typewriter_text):
            self.typewriter_index += 1
            self.app_title_label.setText(self.typewriter_text[:self.typewriter_index])
        else:
            self.typewriter_timer.stop()



    def get_statistics_widget_instance(self): # This method seems to refer to the dashboard, not the summary.
        """Lazily creates and returns the instance of the statistics dashboard if module is enabled."""
        if not self.module_states.get('statistics', True):
            return None
        if self.statistics_dashboard_instance is None:
            logging.info("DocumentManager: Lazily creating StatisticsDashboard for get_statistics_widget_instance.")
            self.statistics_dashboard_instance = StatisticsDashboard(parent=self)
            self.main_area_stack.addWidget(self.statistics_dashboard_instance)
            if hasattr(self.statistics_dashboard_instance, 'request_add_client_for_country'):
                self.statistics_dashboard_instance.request_add_client_for_country.connect(self.handle_add_client_from_stats_map)
            if hasattr(self.statistics_dashboard_instance, 'request_view_client_details'):
                self.statistics_dashboard_instance.request_view_client_details.connect(self.handle_view_client_from_stats_map)
            logging.info("DocumentManager: StatisticsDashboard instance lazily created and added to stack.")
        return self.statistics_dashboard_instance

    # Note: The duplicate get_statistics_widget_instance methods were removed.
    # The one above now handles lazy creation if needed.

    def _load_module_states(self):
        return None

    def _load_module_states(self):
        """Loads the enabled/disabled state of configurable modules from the database."""
        if not db_manager:
            logging.warning("DB manager not available, cannot load module states. All modules will default to enabled.")
            # Default all to True if DB is not available, so basic functionality isn't hindered
            for module_info in CONFIGURABLE_MODULES:
                self.module_states[module_info['name']] = True
            return

        logging.info("Loading module states...")
        for module_info in CONFIGURABLE_MODULES:
            # Default to 'True' (string) if setting is not found, then convert to boolean
            is_enabled_str = db_manager.get_setting(module_info['key'], default='True')
            logging.info(f"Module Key: {module_info['key']}, Value from DB (or default): '{is_enabled_str}'")
            is_enabled = is_enabled_str.lower() == 'true' if isinstance(is_enabled_str, str) else bool(is_enabled_str)
            self.module_states[module_info['name']] = is_enabled
            logging.info(f"Processed Module '{module_info['name']}' state: {'Enabled' if is_enabled else 'Disabled'}")
        logging.info("Module states loaded.")


    def init_or_update_download_monitor(self):
        if self.download_monitor_service is not None:
            logging.info("Stopping existing download monitor service...")
            self.download_monitor_service.stop()
            self.download_monitor_service = None
            logging.info("Existing download monitor service stopped.")

        enabled = self.config.get('download_monitor_enabled', False)
        monitor_path = self.config.get('download_monitor_path')

        if enabled and monitor_path and os.path.isdir(monitor_path):
            try:
                logging.info(f"Initializing download monitor for path: {monitor_path}")
                self.download_monitor_service = DownloadMonitorService(monitor_path)
                self.download_monitor_service.new_document_detected.connect(self.handle_new_document_detected)
                self.download_monitor_service.start()
                self.notify(self.tr("Download Monitoring"),
                            self.tr("Service started for folder: {0}").format(monitor_path),
                            type='INFO')
                logging.info(f"Download monitor service started for path: {monitor_path}")
            except Exception as e:
                logging.error(f"Failed to start download monitor service: {e}", exc_info=True)
                self.notify(self.tr("Download Monitoring Error"),
                            self.tr("Failed to start service: {0}").format(str(e)),
                            type='ERROR')
                if self.download_monitor_service: # ensure it's cleaned up if partially initialized
                    self.download_monitor_service.stop()
                    self.download_monitor_service = None
        elif enabled and (not monitor_path or not os.path.isdir(monitor_path)):
            logging.error(f"Download monitor enabled but path is invalid or not set: '{monitor_path}'")
            self.notify(self.tr("Download Monitoring Error"),
                        self.tr("Download monitor path is invalid or not set. Please check settings."),
                        type='ERROR')
        elif not enabled:
            logging.info("Download monitor is disabled in configuration.")
            # self.notify(self.tr("Download Monitoring"), self.tr("Service is disabled."), type='INFO') # Optional: notify if disabled

    @pyqtSlot(str)
    def handle_add_client_from_stats_map(self, country_name_str):
        logging.info(f"Received request to add client for country: {country_name_str} from statistics map.")
        try:
            # Utiliser AddNewClientDialog au lieu de StatisticsAddClientDialog
            dialog = AddNewClientDialog(parent=self, initial_country_name=country_name_str)

            if dialog.exec_() == QDialog.Accepted:
                client_data_from_dialog = dialog.get_data()
                logging.info(f"AddNewClientDialog accepted. Data: {client_data_from_dialog}")

                # AddNewClientDialog.get_data() retourne déjà created_by_user_id
                # et les noms de pays/ville qui seront résolus par client_controller.
                # Le client_controller s'attend à country_name et city_name, pas IDs.

                if not client_data_from_dialog.get('client_name'):
                    QMessageBox.critical(self, self.tr("Erreur Données"), self.tr("Le nom du client est requis."))
                    return

                if not client_data_from_dialog.get('country_name'):
                    QMessageBox.critical(self, self.tr("Erreur Données"), self.tr("Le nom du pays est requis."))
                    return

                # Appeler directement le client_controller pour créer le client
                created_client_info = self.client_controller_instance.create_client(client_data_from_dialog)

                if created_client_info and created_client_info.get('success'):
                    new_client_id = created_client_info.get('client_id')
                    if new_client_id:
                        self.notify(self.tr("Client Créé"),
                                    self.tr("Le client '{0}' a été créé avec succès.").format(created_client_info.get('client_name')),
                                    type='SUCCESS')
                        self.load_clients_from_db_slot() # Recharger la liste des clients
                        self.open_client_tab_by_id(new_client_id) # Ouvrir l'onglet du nouveau client
                    else:
                        QMessageBox.critical(self, self.tr("Erreur Création Client"),
                                             self.tr("Le client a été créé mais son ID n'a pas été retourné."))
                else:
                    error_msg = created_client_info.get('error', self.tr("Erreur inconnue lors de la création du client."))
                    QMessageBox.critical(self, self.tr("Erreur Création Client"), error_msg)
                    # Pas besoin de recharger la liste des clients ici car la création a échoué
            else:
                logging.info("AddNewClientDialog cancelled by user.")
        except Exception as e:
            logging.error(f"Error opening or executing AddNewClientDialog for country {country_name_str}: {e}", exc_info=True)
            QMessageBox.critical(self,
                                 self.tr("Erreur Dialogue"),
                                 self.tr("Impossible d'ouvrir le dialogue 'Ajouter Nouveau Client'. Veuillez consulter les logs pour plus de détails."))

    def handle_new_document_detected(self, file_path):
        logging.info(f"Main_window: New document detected by service: {file_path}")
        try:
            # Ensure clients_crud_instance and add_client_document are correctly referenced
            # clients_crud_instance is self.clients_crud_instance if available, or imported directly
            # add_client_document is imported directly
            dialog = AssignDocumentToClientDialog(
                file_path=file_path,
                current_user_id=self.current_user_id,
                clients_crud=clients_crud_instance,
                client_docs_crud_add_func=add_client_document, # Using the directly imported function
                parent=self
            )
            dialog.document_assigned.connect(self.handle_document_assigned_to_client)
            if dialog.exec_() == QDialog.Accepted:
                logging.info(f"Document assignment dialog accepted for {file_path}.")
            else:
                logging.info(f"Document assignment dialog cancelled for {file_path}.")
                # If cancelled, the file remains in the downloads folder.
                # Consider if any cleanup or notification is needed for the original file.
                # For now, leaving it as is.
        except Exception as e:
            logging.error(f"Error during handling of new document {file_path}: {e}", exc_info=True)
            self.notify(self.tr("Error Assigning Document"),
                        self.tr("An error occurred while trying to assign {0}: {1}").format(os.path.basename(file_path), str(e)),
                        type='ERROR')

    @pyqtSlot(str, str)
    def handle_document_assigned_to_client(self, client_id, new_document_id):
        logging.info(f"Main_window: Document {new_document_id} assigned to client {client_id}.")
        self.notify(self.tr("Document Assigned"),
                    self.tr("New document successfully assigned to client ID: {0} (Doc ID: {1})").format(client_id, new_document_id),
                    type='SUCCESS')

        # UI Refresh Logic
        try:
            for i in range(self.client_tabs_widget.count()):
                tab_widget_ref = self.client_tabs_widget.widget(i)
                if hasattr(tab_widget_ref, 'client_info') and \
                   tab_widget_ref.client_info.get("client_id") == client_id and \
                   hasattr(tab_widget_ref, 'refresh_documents_list'):
                    logging.info(f"Refreshing documents list for open tab of client {client_id}")
                    tab_widget_ref.refresh_documents_list() # Assuming this method exists on ClientWidget
                    break # Found and refreshed the relevant tab
        except Exception as e:
            logging.error(f"Error refreshing client tab after document assignment: {e}", exc_info=True)


    @pyqtSlot(str)
    def handle_add_client_from_stats_map(self, country_name_str):
        logging.info(f"Received request to add client for country: {country_name_str} from statistics map using new dialog.")        
        try:
            dialog = StatisticsAddClientDialog(initial_country_name=country_name_str, parent=self)

            if dialog.exec_() == QDialog.Accepted:
                new_client_data = dialog.get_data()
                logging.info(f"StatisticsAddClientDialog accepted. Data: {new_client_data}")

                if not new_client_data.get('country_id'):
                    QMessageBox.critical(self, self.tr("Erreur Pays"), self.tr("ID du pays non obtenu depuis le dialogue. Impossible de continuer."))
                    return

                client_data_for_db = {
                    "client_name": new_client_data["client_name"],
                    "company_name": new_client_data.get("company_name"),
                    "country_id": new_client_data["country_id"],
                    "city_id": new_client_data.get("city_id"),
                    "project_identifier": new_client_data.get("project_identifier"),
                    "primary_need_description": new_client_data.get("primary_need_description"),
                    "selected_languages": new_client_data.get("selected_languages"),
                    "created_by_user_id": self.current_user_id
                }

                logging.info(f"Proceeding to call handle_create_client_execution with data from new dialog: {client_data_for_db}")
                handle_create_client_execution(self, client_data_dict=client_data_for_db)
            else:
                logging.info("StatisticsAddClientDialog cancelled by user.")
        except Exception as e:
            logging.error(f"Error opening or executing StatisticsAddClientDialog for country {country_name_str}: {e}", exc_info=True)
            QMessageBox.critical(self,
                                 self.tr("Erreur Dialogue"),
                                 self.tr("Impossible d'ouvrir le dialogue 'Ajouter Client'. Veuillez consulter les logs de l'application pour plus de détails."))


    @pyqtSlot(str)
    def handle_view_client_from_stats_map(self, client_id_str):
        logging.info(f"Handling request to view client ID: {client_id_str} from statistics map.")
        self.main_area_stack.setCurrentWidget(self.documents_page_widget)
        self.open_client_tab_by_id(client_id_str)

    def notify(self, title, message, type='INFO', duration=5000, icon_path=None):

        """
        Convenience method to show a notification via the global NotificationManager.

        This method provides an easy way for parts of the DocumentManager (or its children,
        if they have a reference to it) to display notifications without needing to
        directly import or manage the NotificationManager.

        Args:
            title (str): The title of the notification.
            message (str): The main message content of the notification.
            type (str, optional): Type of notification ('INFO', 'SUCCESS', 'WARNING', 'ERROR').
                                  Defaults to 'INFO'.
            duration (int, optional): Duration in milliseconds before the notification auto-closes.
                                      Defaults to 5000ms.
            icon_path (str, optional): Path to a custom icon. If None, a default icon based
                                       on the 'type' will be used. Defaults to None.
        """
        from main import get_notification_manager # Local import

        manager = get_notification_manager()
        if manager:
            manager.show(title, message, type=type, duration=duration, icon_path=icon_path)
            if hasattr(self, 'notification_panel'):
                self.notification_panel.add_notification(title, message)
        else:
            logging.warning(f"Notification Manager not found. Notification: {title} - {message}")

    def setup_ui_main(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Nouveau layout vertical principal pour le central_widget
        new_main_vertical_layout = QVBoxLayout(central_widget)
        new_main_vertical_layout.setContentsMargins(0, 0, 0, 0)
        new_main_vertical_layout.setSpacing(0)

        # Placeholder pour la barre de menu supérieure (sera un QFrame ou similaire)
        self.top_menu_bar_widget = QFrame() # Sera configuré dans create_menus_main
        self.top_menu_bar_widget.setObjectName("topMenuBarWidget")
        # self.top_menu_bar_widget.setFixedHeight(50) # Hauteur typique pour une barre de menu
        # self.top_menu_bar_widget.setStyleSheet("background-color: #f0f2f5; border-bottom: 1px solid #d1d5db;") # Style initial
        new_main_vertical_layout.addWidget(self.top_menu_bar_widget)


        # Layout horizontal pour la sidebar et la zone de contenu principale (comme avant)
        main_horizontal_layout = QHBoxLayout() # Ce layout sera ajouté au new_main_vertical_layout
        main_horizontal_layout.setContentsMargins(0, 0, 0, 0)
        main_horizontal_layout.setSpacing(0)


        # REMOVED: Ajout de la sidebar
        # main_horizontal_layout.addWidget(self.sidebar_nav)

        # La QStackedWidget pour le contenu principal
        self.main_area_stack = QStackedWidget()
        # Add main_area_stack directly to new_main_vertical_layout if sidebar is gone,
        # or keep main_horizontal_layout if other elements might go beside the stack later.
        # For now, assuming main_area_stack will take the full width under the top_menu_bar.
        # So, main_horizontal_layout might become redundant if it only holds the stack.
        # Let's simplify: new_main_vertical_layout will hold top_menu_bar and then main_area_stack.
        # main_horizontal_layout.addWidget(self.main_area_stack, 1) # Old line

        # Ajout du layout horizontal (sidebar + stack) au layout vertical principal
        # new_main_vertical_layout.addLayout(main_horizontal_layout) # Old line

        new_main_vertical_layout.addWidget(self.main_area_stack, 1) # Add stack directly, it takes remaining space

        
        # -- Configuration de la page "Documents" (qui va dans le main_area_stack) --
        self.documents_page_widget = QWidget()
        # Le main_splitter est maintenant un enfant de documents_page_widget, pas directement de DocumentManager
        self.main_splitter = QSplitter(Qt.Horizontal, self.documents_page_widget)

        left_pane_widget = QWidget()
        left_pane_widget.setObjectName("leftPaneWidget") # Set object name for QSS
        left_pane_layout = QVBoxLayout(left_pane_widget)
        left_pane_layout.setContentsMargins(5,5,5,5) # Add some margins to the overall left pane
        left_pane_layout.setSpacing(8) # Adjust spacing between elements in left pane

        # Filter Search Group - Now uses QVBoxLayout for vertical stacking of filter groups
        filter_search_group = QGroupBox(self.tr("Filtres et Recherche Clients"))
        filter_search_group.setObjectName("filterSearchGroup") # For QSS styling
        filter_search_main_layout = QVBoxLayout(filter_search_group) # Changed to QVBoxLayout
        filter_search_main_layout.setSpacing(10) # Spacing within the filter group
        filter_search_main_layout.setContentsMargins(8, 8, 8, 8) # Padding inside the groupbox

        # --- Top line filters (Status, Search, More Filters button) ---
        top_filter_line_layout = QHBoxLayout()

        # Status Filter
        self.status_filter_button = QPushButton(self.tr("Statut: Tous")) # Button text will be updated
        self.status_filter_button.setObjectName("filterButton") # For styling
        self.status_filter_button.setToolTip(self.tr("Sélectionner plusieurs statuts client"))
        self.status_filter_button.clicked.connect(self.open_multi_select_status_dialog)
        self.selected_status_ids_filter = [] # Store selected status IDs
        top_filter_line_layout.addWidget(self.status_filter_button)


        # Search Input
        # search_input_layout_group = QWidget() # Container for label and input
        # search_input_v_layout = QVBoxLayout(search_input_layout_group)
        # search_input_v_layout.setContentsMargins(0,0,0,0)
        # self.search_label = QLabel(self.tr("Recherche:")) # Label for search
        # self.search_label.setVisible(False) # Hide label for compactness
        self.search_input_field = QLineEdit(); self.search_input_field.setPlaceholderText(self.tr("Rechercher client..."))
        self.search_input_field.textChanged.connect(self.filter_client_list_display_slot)
        # search_input_v_layout.addWidget(self.search_label)
        # search_input_v_layout.addWidget(self.search_input_field)
        top_filter_line_layout.addWidget(self.search_input_field) # Add input directly

        top_filter_line_layout.addStretch(1) # Pushes search and status to left, allows buttons to be at the end

        # "More Filters" Button (Icon Only)
        self.more_filters_button = QPushButton("") # No text
        self.more_filters_button.setObjectName("moreFiltersButton")
        self.more_filters_button.setIcon(QIcon(":/icons/chevron-down.svg"))
        self.more_filters_button.setCheckable(True)
        self.more_filters_button.toggled.connect(self.toggle_more_filters_visibility)
        self.more_filters_button.setToolTip(self.tr("Afficher/Masquer plus de filtres"))
        self.more_filters_button.setFixedSize(28, 28) # Make it small and square
        self.more_filters_button.setIconSize(QSize(16, 16)) # Ensure icon isn't too large
        self.more_filters_button.setStyleSheet("""
            QPushButton#moreFiltersButton {
                border: 1px solid #ced4da; /* Standard border */
                border-radius: 4px; /* Standard border-radius */
                padding: 4px; /* Adjust padding to center icon */
                background-color: #f8f9fa; /* Light background */
            }
            QPushButton#moreFiltersButton:hover {
                background-color: #e9ecef; /* Slightly darker on hover */
            }
            QPushButton#moreFiltersButton:checked {
                background-color: #dde2e6; /* Different background when checked (filters shown) */
                border-color: #adb5bd;
            }
        """)
        top_filter_line_layout.addWidget(self.more_filters_button)

        # "Réinitialiser Filtres" Button is now moved to the collapsible section
        # self.reset_filters_button = QPushButton("")
        # self.reset_filters_button.setObjectName("resetFiltersButton")
        # self.reset_filters_button.setIcon(QIcon(":/icons/refresh-cw.svg"))
        # self.reset_filters_button.clicked.connect(self.reset_all_filters_slot)
        # self.reset_filters_button.setToolTip(self.tr("Réinitialiser tous les filtres"))
        # top_filter_line_layout.addWidget(self.reset_filters_button) # Removed from here

        filter_search_main_layout.addLayout(top_filter_line_layout) # This is the single visible line of filters


        # --- Collapsible Filter Widget ---
        self.collapsible_filter_widget = QWidget()
        collapsible_layout = QVBoxLayout(self.collapsible_filter_widget)
        collapsible_layout.setContentsMargins(0, 5, 0, 5) # Adjusted margins for better spacing
        collapsible_layout.setSpacing(10)


        # Archive Filter (moved into collapsible area)
        archive_filter_layout_group = QWidget()
        archive_filter_v_layout = QVBoxLayout(archive_filter_layout_group)
        archive_filter_v_layout.setContentsMargins(0,0,0,0)
        archive_label = QLabel(self.tr("Filtre Archive:"))
        self.client_archive_filter_combo = QComboBox()
        self.client_archive_filter_combo.addItem(self.tr("Clients Actifs"), False)
        self.client_archive_filter_combo.addItem(self.tr("Clients Archivés (supprimés logiquement)"), True)
        self.client_archive_filter_combo.addItem(self.tr("Tout"), "all_status_types")
        self.client_archive_filter_combo.setCurrentIndex(0); self.client_archive_filter_combo.currentIndexChanged.connect(self.filter_client_list_display_slot)
        archive_filter_v_layout.addWidget(archive_label)
        archive_filter_v_layout.addWidget(self.client_archive_filter_combo)
        collapsible_layout.addWidget(archive_filter_layout_group)

        # Country Filter (moved into collapsible area)
        country_filter_layout_group = QWidget()
        country_filter_v_layout = QVBoxLayout(country_filter_layout_group)
        country_filter_v_layout.setContentsMargins(0,0,0,0)
        country_label = QLabel(self.tr("Pays:"))
        self.country_filter_combo = QComboBox()
        self.country_filter_combo.addItem(self.tr("Tous les pays"), None)
        self.load_countries_into_filter_combo()
        self.country_filter_combo.currentIndexChanged.connect(self.filter_client_list_display_slot)
        country_filter_v_layout.addWidget(country_label)
        country_filter_v_layout.addWidget(self.country_filter_combo)
        collapsible_layout.addWidget(country_filter_layout_group)

        # --- Date Filter Group (Horizontal, within collapsible area) ---
        date_filter_group_layout = QHBoxLayout()
        date_filter_label_start = QLabel(self.tr("Créé de:"))
        self.date_filter_start = QDateEdit()
        self.date_filter_start.setCalendarPopup(True)
        # self.date_filter_start.setClearButtonEnabled(True)
        self.date_filter_start.setDate(QDate()) # Null date initially
        self.date_filter_start.setDisplayFormat("yyyy-MM-dd")
        self.date_filter_start.dateChanged.connect(self.filter_client_list_display_slot)

        date_filter_label_end = QLabel(self.tr("à:"))
        self.date_filter_end = QDateEdit()
        self.date_filter_end.setCalendarPopup(True)
        # self.date_filter_end.setClearButtonEnabled(True)

        self.date_filter_end.setDate(QDate()) # Null date initially
        self.date_filter_end.setDisplayFormat("yyyy-MM-dd")
        self.date_filter_end.dateChanged.connect(self.filter_client_list_display_slot)

        date_filter_group_layout.addWidget(date_filter_label_start)
        date_filter_group_layout.addWidget(self.date_filter_start)
        date_filter_group_layout.addWidget(date_filter_label_end)
        date_filter_group_layout.addWidget(self.date_filter_end)
        date_filter_group_layout.addStretch(1)
        collapsible_layout.addLayout(date_filter_group_layout)
        # --- End Date Filter Group ---

        self.collapsible_filter_widget.setVisible(False) # Initially hidden
        filter_search_main_layout.addWidget(self.collapsible_filter_widget)

        # --- Category Filter (moved into collapsible area) ---
        category_filter_layout_group = QWidget()
        category_filter_v_layout = QVBoxLayout(category_filter_layout_group) # Changed to QVBoxLayout for consistency
        category_filter_v_layout.setContentsMargins(0,0,0,0) # No extra margins for the group itself
        category_label = QLabel(self.tr("Catégorie:"))
        self.category_filter_input = QLineEdit()
        self.category_filter_input.setPlaceholderText(self.tr("Filtrer par catégorie..."))
        self.category_filter_input.textChanged.connect(self.filter_client_list_display_slot)
        category_filter_v_layout.addWidget(category_label) # Label on top
        category_filter_v_layout.addWidget(self.category_filter_input) # Input below
        collapsible_layout.addWidget(category_filter_layout_group) # Add to collapsible


        # --- Saved Filters UI ---
        saved_filters_group = QGroupBox(self.tr("Filtres Sauvegardés")) # Optional: GroupBox for clarity
        saved_filters_main_layout = QVBoxLayout(saved_filters_group)

        load_filters_layout = QHBoxLayout()
        load_filters_layout.addWidget(QLabel(self.tr("Charger:")))
        self.load_filter_combo = QComboBox()
        self.load_filter_combo.addItem(self.tr("--- Sélectionner un filtre ---"), None)
        self.load_filter_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        load_filters_layout.addWidget(self.load_filter_combo)
        self.manage_filters_button = QPushButton(self.tr("Gérer..."))
        self.manage_filters_button.setIcon(QIcon(":/icons/settings.svg"))
        self.manage_filters_button.setToolTip(self.tr("Gérer les filtres sauvegardés"))
        self.manage_filters_button.clicked.connect(self.open_manage_filters_dialog_slot) # Connect placeholder
        load_filters_layout.addWidget(self.manage_filters_button)
        saved_filters_main_layout.addLayout(load_filters_layout)

        # Connect signal for loading a saved filter
        self.load_filter_combo.activated[int].connect(self.apply_saved_filter_slot)


        save_filter_layout = QHBoxLayout()
        self.saved_filter_name_input = QLineEdit()
        self.saved_filter_name_input.setPlaceholderText(self.tr("Nom du nouveau filtre sauvegardé"))
        save_filter_layout.addWidget(self.saved_filter_name_input)
        self.save_filter_button = QPushButton(self.tr("Sauvegarder Actuel"))
        self.save_filter_button.setIcon(QIcon(":/icons/save.svg"))
        self.save_filter_button.setToolTip(self.tr("Sauvegarder la configuration actuelle des filtres"))
        self.save_filter_button.clicked.connect(self.save_current_filter_slot) # Connect save button
        save_filter_layout.addWidget(self.save_filter_button)
        saved_filters_main_layout.addLayout(save_filter_layout)

        # filter_search_main_layout.addWidget(saved_filters_group) # Removed from main filter layout
        collapsible_layout.addWidget(saved_filters_group) # Added to collapsible layout
        # --- End Saved Filters UI ---

        # --- "Réinitialiser Filtres" Button (now in collapsible area) ---
        self.reset_filters_button = QPushButton(self.tr("Réinitialiser Tous les Filtres")) # Added text back for clarity in collapsible
        self.reset_filters_button.setObjectName("resetFiltersButton") # Keep object name for styling if any
        self.reset_filters_button.setIcon(QIcon(":/icons/refresh-cw.svg"))
        self.reset_filters_button.clicked.connect(self.reset_all_filters_slot)
        self.reset_filters_button.setToolTip(self.tr("Réinitialiser tous les filtres et masquer cette section"))
        collapsible_layout.addWidget(self.reset_filters_button) # Add to collapsible layout
        # --- End Réinitialiser Filtres Button ---


        # Remove the previous layout for reset_button_layout as it's now on the top line
        # filter_search_main_layout.addLayout(reset_button_layout) # This line is removed


        # The main stretch for filter_search_main_layout should be removed if we want the client list
        # to be directly under the collapsible_filter_widget (or top_filter_line_layout when collapsed).
        # filter_search_main_layout.addStretch(1) # REMOVE THIS to prevent pushing client list down

        # --- Sort Controls ---
        sort_controls_layout = QHBoxLayout()
        sort_label = QLabel(self.tr("Trier par:"))
        self.sort_by_combo = QComboBox()
        self.sort_by_combo.setObjectName("sortByCombo")
        # Options: Clé affichée -> valeur technique pour le backend/CRUD
        self.sort_by_combo.addItem(self.tr("Nom du Client"), "client_name")
        self.sort_by_combo.addItem(self.tr("Date de Création"), "created_at")
        self.sort_by_combo.addItem(self.tr("Pays"), "country_name")
        self.sort_by_combo.addItem(self.tr("ID Projet"), "project_identifier")
        self.sort_by_combo.addItem(self.tr("Statut"), "status_name")

        self.sort_order_combo = QComboBox()
        self.sort_order_combo.setObjectName("sortOrderCombo")
        self.sort_order_combo.addItem(self.tr("Ascendant"), "ASC")
        self.sort_order_combo.addItem(self.tr("Descendant"), "DESC")

        # Connecter les signaux des combos de tri pour rafraîchir la liste
        self.sort_by_combo.currentIndexChanged.connect(self.filter_client_list_display_slot)
        self.sort_order_combo.currentIndexChanged.connect(self.filter_client_list_display_slot)

        sort_controls_layout.addWidget(sort_label)
        sort_controls_layout.addWidget(self.sort_by_combo)
        sort_controls_layout.addWidget(self.sort_order_combo)
        sort_controls_layout.addStretch(1) # Pousse les contrôles de tri à gauche

        filter_search_main_layout.addLayout(sort_controls_layout) # Ajout du layout de tri au QGroupBox
        # --- End Sort Controls ---

        left_pane_layout.addWidget(filter_search_group)

        self.client_list_widget = QListWidget()
        self.client_list_widget.setObjectName("clientListWidget") # Set object name for QSS
        self.client_list_widget.setAlternatingRowColors(False) # Disable alternating colors, rely on item hover
        self.client_list_widget.setItemDelegate(StatusDelegate(self.client_list_widget)) # StatusDelegate might still be useful for item sizing or other non-background roles
        self.client_list_widget.itemClicked.connect(self.handle_client_list_click)
        self.client_list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.client_list_widget.customContextMenuRequested.connect(self.show_client_context_menu)
        self.client_list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff) # Often better for lists
        left_pane_layout.addWidget(self.client_list_widget)
        
        pagination_layout = QHBoxLayout()
        self.prev_page_button = QPushButton(self.tr("Précédent"))
        self.prev_page_button.setObjectName("prevPageButton")
        self.prev_page_button.clicked.connect(self.prev_page)

        self.next_page_button = QPushButton(self.tr("Suivant"))
        self.next_page_button.setObjectName("nextPageButton")
        self.next_page_button.clicked.connect(self.next_page)

        self.page_info_label = QLabel(self.tr("Page 1"))
        self.page_info_label.setObjectName("pageInfoLabel")

        # Nouveaux éléments pour la pagination améliorée
        go_to_label = QLabel(self.tr("Aller à :"))
        self.go_to_page_input = QLineEdit()
        self.go_to_page_input.setObjectName("goToPageInput")
        self.go_to_page_input.setFixedWidth(50) # Largeur pour ~3-4 chiffres
        self.go_to_page_input.setPlaceholderText(self.tr("Page"))
        self.go_to_page_button = QPushButton(self.tr("OK"))
        self.go_to_page_button.setObjectName("goToPageButton")

        self.go_to_page_button.clicked.connect(self._handle_go_to_page)
        self.go_to_page_input.returnPressed.connect(self._handle_go_to_page)

        pagination_layout.addWidget(self.prev_page_button)
        pagination_layout.addWidget(self.page_info_label)
        pagination_layout.addWidget(self.next_page_button)
        pagination_layout.addStretch(1) # Espace flexible
        pagination_layout.addWidget(go_to_label)
        pagination_layout.addWidget(self.go_to_page_input)
        pagination_layout.addWidget(self.go_to_page_button)

        left_pane_layout.addLayout(pagination_layout)
        
        # Buttons in a single row
        client_actions_layout = QHBoxLayout()
        self.add_new_client_button = QPushButton(self.tr("Ajouter Nouveau Client")); self.add_new_client_button.setIcon(QIcon(":/icons/user-add.svg")); self.add_new_client_button.setObjectName("primaryButton"); self.add_new_client_button.clicked.connect(self.open_add_new_client_dialog)
        client_actions_layout.addWidget(self.add_new_client_button)

        self.add_client_by_voice_button = QPushButton(self.tr("Ajouter par Voix")); self.add_client_by_voice_button.setIcon(QIcon(":/icons/mic.svg")); self.add_client_by_voice_button.setObjectName("primaryButton")
        self.add_client_by_voice_button.clicked.connect(self.handle_add_client_by_voice_clicked)
        self.add_client_by_voice_button.setEnabled(False) # Disable as requested
        self.add_client_by_voice_button.setToolTip(self.tr("Fonctionnalité en cours de développement"))
        client_actions_layout.addWidget(self.add_client_by_voice_button)


        left_pane_layout.addLayout(client_actions_layout)

        # map_group_box removed from here
        left_pane_widget.setLayout(left_pane_layout)
        self.main_splitter.addWidget(left_pane_widget)

        # Right pane for client tabs (no change here, it's a QSplitter itself)
        right_pane_splitter = QSplitter(Qt.Vertical)
        self.client_tabs_widget = QTabWidget(); self.client_tabs_widget.setTabsClosable(True); self.client_tabs_widget.tabCloseRequested.connect(self.close_client_tab)
        right_pane_splitter.addWidget(self.client_tabs_widget)
        self.main_splitter.addWidget(right_pane_splitter)

        # Load or set default splitter sizes
        saved_splitter_state_hex = db_manager.get_setting('client_list_splitter_state', default=None)
        if saved_splitter_state_hex:
            try:
                splitter_state_byte_array = QByteArray.fromHex(saved_splitter_state_hex.encode('utf-8'))
                if not self.main_splitter.restoreState(splitter_state_byte_array):
                    logging.warning("Failed to restore splitter state, applying defaults.")
                    self.main_splitter.setSizes([int(self.width() * 0.20), int(self.width() * 0.80)]) # Adjusted default
                else:
                    logging.info("Client list splitter state restored.")
            except Exception as e:
                logging.error(f"Error restoring splitter state: {e}. Applying defaults.", exc_info=True)
                self.main_splitter.setSizes([int(self.width() * 0.20), int(self.width() * 0.80)]) # Adjusted default
        else:
            # Adjusted default splitter sizes: left pane 20%, right pane 80%
            self.main_splitter.setSizes([int(self.width() * 0.20), int(self.width() * 0.80)])
            logging.info("Client list splitter: No saved state found, applied default sizes 20/80.")

        self.main_splitter.splitterMoved.connect(self.save_splitter_state)

        docs_page_layout = QVBoxLayout(self.documents_page_widget)
        docs_page_layout.addWidget(self.main_splitter) # Use self.main_splitter
        docs_page_layout.setContentsMargins(0,0,0,0)
        self.documents_page_widget.setLayout(docs_page_layout)

        self.main_area_stack.addWidget(self.documents_page_widget)

    def toggle_more_filters_visibility(self, checked):
        self.collapsible_filter_widget.setVisible(checked)
        if checked:
            self.more_filters_button.setIcon(QIcon(":/icons/chevron-up.svg")) # Change icon to up
            # self.more_filters_button.setText(self.tr("Moins de Filtres")) # Text removed
        else:
            self.more_filters_button.setIcon(QIcon(":/icons/chevron-down.svg")) # Change icon to down
            # self.more_filters_button.setText(self.tr("Plus de Filtres")) # Text removed


    def reset_all_filters_slot(self):
        """Resets all filter inputs to their default states and refreshes the client list."""
        logging.info("Resetting all filters.")

        # Reset Status Filter Button and selected IDs
        self.selected_status_ids_filter = []
        self.status_filter_button.setText(self.tr("Statut: Tous"))

        # Reset other ComboBoxes
        self.client_archive_filter_combo.setCurrentIndex(0)
        self.country_filter_combo.setCurrentIndex(0)

        # Reset Category Input
        if hasattr(self, 'category_filter_input'):
            self.category_filter_input.setText("")

        # Clear the search input field
        self.search_input_field.setText("")

        # Clear date filters
        if hasattr(self, 'date_filter_start'):
            self.date_filter_start.setDate(QDate()) # Set to null QDate
        if hasattr(self, 'date_filter_end'):
            self.date_filter_end.setDate(QDate()) # Set to null QDate


        # Collapse the "More Filters" section if it's open
        if self.collapsible_filter_widget.isVisible():
            self.more_filters_button.setChecked(False) # This will trigger toggle_more_filters_visibility

        # Refresh the client list
        self.filter_client_list_display_slot()

        self.notify(self.tr("Filtres Réinitialisés"), self.tr("Tous les filtres ont été réinitialisés."), type='INFO')


    def save_splitter_state(self, pos, index):
        """Saves the current state of the main_splitter."""
        try:
            splitter_state_byte_array = self.main_splitter.saveState()
            splitter_state_hex = splitter_state_byte_array.toHex().data().decode('utf-8')
            db_manager.set_setting('client_list_splitter_state', splitter_state_hex)
            logging.info(f"Client list splitter state saved (pos: {pos}, index: {index}).")
        except Exception as e:
            logging.error(f"Error saving splitter state: {e}", exc_info=True)

    def open_add_new_client_dialog(self):
        dialog = AddNewClientDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            client_data = dialog.get_data()
            if client_data: handle_create_client_execution(self, client_data_dict=client_data)

    def handle_add_client_by_voice_clicked(self):
        # Notify user that listening has started
        self.notify(self.tr("Voice Input"), self.tr("Veuillez parler maintenant pour ajouter un client..."), type='INFO', duration=5000)
        QApplication.processEvents() # Ensure notification is shown, good for long operations

        speech_result = self.voice_input_service.recognize_speech()

        if speech_result["success"]:
            recognized_text = speech_result["text"]
            self.notify(self.tr("Voice Input"), self.tr("Reconnu : '{0}'. Traitement des informations...").format(recognized_text), type='INFO', duration=3000)
            QApplication.processEvents()
            logging.info(f"Recognized text: {recognized_text}")

            extracted_info = self.voice_input_service.extract_client_info(recognized_text)
            logging.info(f"Extracted info for dialog: {extracted_info}")

            if extracted_info: # Check if dictionary is not empty
                dialog = AddNewClientDialog(self)
                dialog.populate_from_voice_data(extracted_info)
                if dialog.exec_() == QDialog.Accepted:
                    client_data = dialog.get_data()
                    if client_data: # Ensure data is valid before creating client
                        handle_create_client_execution(self, client_data_dict=client_data)
                # No specific message if dialog is cancelled by user after population
            else:
                logging.warning("Could not extract any client details from speech.")
                QMessageBox.information(self,
                                        self.tr("Aucune Information Extraite"),
                                        self.tr("Aucun détail client n'a pu être extrait de la parole. Le texte reconnu était : \"{0}\". Veuillez réessayer ou entrer manuellement les informations.").format(recognized_text))
        else:
            error_message = speech_result.get("message", self.tr("Erreur inconnue"))
            error_type = speech_result.get("error", "unknown_error")
            logging.error(f"Speech recognition failed: {error_message} (Type: {error_type})")

            if error_type == "microphone_error": # This is the custom error from voice_input_service if self.microphone is None or adjust... fails
                 QMessageBox.critical(self,
                                      self.tr("Erreur Microphone"),
                                      self.tr("Aucun microphone n'a été détecté ou il ne fonctionne pas correctement. Veuillez vérifier votre matériel et les permissions.\n\nDétail: {0}").format(error_message))
            elif error_type == "listen_error": # Custom error from voice_input_service
                 QMessageBox.critical(self,
                                      self.tr("Erreur d'Écoute"),
                                      self.tr("Un problème est survenu lors de la phase d'écoute via le microphone.\n\nDétail: {0}").format(error_message))
            elif error_type == "unknown_value":
                 QMessageBox.warning(self,
                                     self.tr("Erreur de Reconnaissance"),
                                     self.tr("Impossible de comprendre l'audio. Veuillez réessayer."))
            elif error_type == "request_error":
                 QMessageBox.critical(self,
                                      self.tr("Erreur d'API"),
                                      self.tr("Le service de reconnaissance vocale est indisponible. Vérifiez votre connexion internet ou réessayez plus tard.\n\nDétail: {0}").format(error_message))
            else: # Includes 'unexpected_error' or any other
                QMessageBox.critical(self,
                                     self.tr("Erreur Inattendue"),
                                     self.tr("Une erreur inattendue est survenue lors de la reconnaissance vocale: {0}").format(error_message))

    def create_actions_main(self): 
        # Assuming a home.svg icon will be added to icons/ directory and qrc
        # For now, using a placeholder if home.svg is not yet available in resources
        home_icon_path = ":/icons/home.svg"
        # A fallback icon if home.svg is not found in resources, for testing
        # if not QIcon.hasThemeIcon("home"): home_icon_path = ":/icons/dashboard.svg" # Example fallback
        self.home_action = QAction(QIcon(home_icon_path), self.tr("Accueil"), self)
        self.home_action.triggered.connect(self.show_home_view)

        self.settings_action = QAction(QIcon(":/icons/modern/settings.svg"), self.tr("Paramètres"), self); self.settings_action.triggered.connect(self.show_settings_page) # Changed to show_settings_page
        # self.template_action removed
        self.status_action = QAction(QIcon(":/icons/check-square.svg"), self.tr("Gérer les Statuts"), self); self.status_action.triggered.connect(self.open_status_management_dialog_slot)
        # self.status_action.setEnabled(False); # No longer hard-disabled
        # self.status_action.setToolTip(self.tr("Fonctionnalité de gestion des statuts prévue pour une future version.")) # Tooltip removed
        self.exit_action = QAction(QIcon(":/icons/log-out.svg"), self.tr("Quitter"), self); self.exit_action.setShortcut("Ctrl+Q"); self.exit_action.triggered.connect(self.close)
        self.project_management_action = QAction(QIcon(":/icons/dashboard.svg"), self.tr("Gestion de Projet"), self); self.project_management_action.triggered.connect(self.show_project_management_view)
        self.documents_view_action = QAction(QIcon(":/icons/modern/folder-docs.svg"), self.tr("Gestion Documents"), self); self.documents_view_action.triggered.connect(self.show_documents_view)
        self.product_list_action = QAction(QIcon(":/icons/book.svg"), self.tr("Product Management"), self); self.product_list_action.triggered.connect(self.show_product_management_page) # Connect to new method
        self.partner_management_action = QAction(QIcon(":/icons/team.svg"), self.tr("Partner Management"), self); self.partner_management_action.triggered.connect(self.show_partner_management_view)
        self.statistics_action = QAction(QIcon(":/icons/bar-chart.svg"), self.tr("Statistiques"), self); self.statistics_action.triggered.connect(self.show_statistics_view)
        self.open_carrier_map_action = QAction(QIcon(":/icons/map.svg"), self.tr("Carrier Map"), self) # Assuming map.svg or similar exists
        self.open_carrier_map_action.triggered.connect(self.open_carrier_map_dialog)
        self.botpress_integration_action = QAction(QIcon(":/icons/placeholder_icon.svg"), self.tr("Botpress Integration"), self) # Add a placeholder icon
        self.botpress_integration_action.triggered.connect(self.show_botpress_integration_view)
        self.inventory_browser_action = QAction(QIcon(":/icons/book.svg"), self.tr("Gestion Stock Atelier"), self) # Updated text
        self.inventory_browser_action.triggered.connect(self.show_inventory_browser_view)

        self.recruitment_action = QAction(QIcon(":/icons/users.svg"), self.tr("Recrutement"), self) # Use an existing icon or add new one
        self.recruitment_action.triggered.connect(self.show_recruitment_view)
        self.camera_management_action = QAction(QIcon(":/icons/video.svg"), self.tr("Gestion Caméras"), self)
        self.camera_management_action.triggered.connect(self.show_camera_management_view)

        self.experience_management_action = QAction(QIcon(":/icons/book.svg"), self.tr("Gestion des Connaissances"), self) # Consider a more specific icon if available
        self.experience_management_action.triggered.connect(self.show_experience_module_view)

        # Action for Calendar Module
        self.calendar_module_action = QAction(QIcon(":/icons/book.svg"), self.tr("Calendrier"), self) # Placeholder icon
        self.calendar_module_action.triggered.connect(self.show_calendar_module_view)

        # Action for managing users - Placeholder, actual UI for this is not yet built
        # but the action can be controlled by RBAC.
        self.manage_users_action = QAction(QIcon(":/icons/users.svg"), self.tr("Gérer les Utilisateurs"), self)
        self.manage_users_action.triggered.connect(self.show_user_management_page) # Connect to show page method

        # Action for Calculator Module
        self.calculator_module_action = QAction(QIcon(":/icons/bar-chart.svg"), self.tr("Calculatrices"), self) # Placeholder icon
        self.calculator_module_action.triggered.connect(self.show_calculator_module_view)

        # Action for Commande Management (Global View)
        self.commande_management_action = QAction(QIcon(":/icons/briefcase.svg"), self.tr("Gestion des Commandes"), self) # Replaced shopping-cart.svg with briefcase.svg
        self.commande_management_action.triggered.connect(self.show_commande_management_view)

        # Action for managing roles
        self.manage_roles_action = QAction(QIcon(":/icons/settings.svg"), self.tr("Gérer les Rôles"), self) # Replaced shield.svg with settings.svg
        self.manage_roles_action.triggered.connect(self.open_role_management_dialog)


        # Populate searchable_actions_map
        self.searchable_actions_map[self.tr("Accueil")] = self.home_action
        self.searchable_actions_map[self.tr("Calculatrices")] = self.calculator_module_action # Added Calculator action
        self.searchable_actions_map[self.tr("Paramètres")] = self.settings_action
        # self.searchable_actions_map[self.tr("Gérer les Modèles")] removed
        self.searchable_actions_map[self.tr("Gérer les Statuts")] = self.status_action
        self.searchable_actions_map[self.tr("Quitter")] = self.exit_action
        self.searchable_actions_map[self.tr("Gestion de Projet")] = self.project_management_action
        self.searchable_actions_map[self.tr("Gestion Documents")] = self.documents_view_action
        self.searchable_actions_map[self.tr("Product Management")] = self.product_list_action
        self.searchable_actions_map[self.tr("Partner Management")] = self.partner_management_action
        self.searchable_actions_map[self.tr("Statistiques")] = self.statistics_action
        self.searchable_actions_map[self.tr("Carrier Map")] = self.open_carrier_map_action
        self.searchable_actions_map[self.tr("Botpress Integration")] = self.botpress_integration_action
        self.searchable_actions_map[self.tr("Gestion Stock Atelier")] = self.inventory_browser_action
        self.searchable_actions_map[self.tr("Recrutement")] = self.recruitment_action
        self.searchable_actions_map[self.tr("Gestion Caméras")] = self.camera_management_action
        self.searchable_actions_map[self.tr("Gestion des Connaissances")] = self.experience_management_action
        self.searchable_actions_map[self.tr("Calendrier")] = self.calendar_module_action
        self.searchable_actions_map[self.tr("Gérer les Utilisateurs")] = self.manage_users_action
        self.searchable_actions_map[self.tr("Gestion des Commandes")] = self.commande_management_action
        self.searchable_actions_map[self.tr("Gérer les Rôles")] = self.manage_roles_action

        # Action for sidebar customization (anciennement menu customization) - REMOVED
        # self.customize_sidebar_action = QAction(QIcon(":/icons/edit.svg"), self.tr("Personnaliser la Barre Latérale"), self)
        # self.customize_sidebar_action.triggered.connect(self.open_sidebar_customization_dialog) # Renommer la méthode cible
        # self.searchable_actions_map[self.tr("Personnaliser la Barre Latérale")] = self.customize_sidebar_action

        # B2C Restaurant Module Action
        # TODO: Find or create a suitable icon e.g., :/icons/restaurant.svg or :/icons/utensils.svg
        self.restaurant_module_action = QAction(QIcon(":/icons/placeholder_icon.svg"), self.tr("Service Restaurant (B2C)"), self)
        self.restaurant_module_action.triggered.connect(self.show_restaurant_module_view)
        self.searchable_actions_map[self.tr("Service Restaurant (B2C)")] = self.restaurant_module_action

        # About Action (ensure it's created here for the map)
        self.about_action = QAction(QIcon(":/icons/help-circle.svg"), self.tr("À propos"), self)
        self.about_action.triggered.connect(self.show_about_dialog)
        self.searchable_actions_map[self.tr("À propos")] = self.about_action

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._update_search_completer)


    def _placeholder_manage_users(self):
        # This is a placeholder. Actual user management UI would be complex.
        # For now, it can just show a message or be a no-op if no UI is built yet.
        QMessageBox.information(self, self.tr("Gestion Utilisateurs"),
                                self.tr("La fonctionnalité de gestion des utilisateurs n'est pas encore implémentée dans l'interface graphique.\n"
                                        "Elle est accessible via les fonctions CRUD et le service d'authentification pour le moment."))


    def create_menus_main(self):
        # Clear the old QMenuBar content if it exists, as we are replacing it
        # self.menuBar().clear() # This is for QMainWindow's default menu bar. We're using a custom widget.

        # Configure the top_menu_bar_widget (QFrame)
        self.top_menu_bar_widget.setFixedHeight(50)
        self.top_menu_bar_widget.setStyleSheet("""
            QFrame#topMenuBarWidget {
                background-color: #f8fafc; /* Light grey, similar to modern UIs */
                border-bottom: 1px solid #e2e8f0; /* Subtle border */
            }
            QPushButton#topMenuButton {
                background-color: transparent;
                color: #4b5563; /* Dark grey text */
                border: none;
                font-size: 14px;
                padding: 8px 12px;
                border-radius: 4px;
            }
            QPushButton#topMenuButton:hover {
                background-color: #e5e7eb; /* Lighter grey on hover */
                color: #1f2937; /* Darker text on hover */
            }
            QPushButton#topMenuButton::menu-indicator {
                image: none; /* Hide default menu indicator if not desired */
            }
            QMenu {
                background-color: #ffffff;
                border: 1px solid #d1d5db;
                padding: 5px;
                border-radius: 6px;
            }
            QMenu::item {
                color: #4b5563;
                padding: 8px 20px;
                margin: 1px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #f3f4f6;
                color: #111827;
            }
            QMenu::separator {
                height: 1px;
                background: #e5e7eb;
                margin: 5px 0px;
            }
        """)

        top_bar_layout = QHBoxLayout(self.top_menu_bar_widget)
        top_bar_layout.setContentsMargins(10, 0, 10, 0) # Left/right padding, no top/bottom for frame
        top_bar_layout.setSpacing(10)

        # App Logo/Title (Optional)
        self.app_title_label = QLabel("Leopardo ERP") # Changed title & assign to self
        self.app_title_label.setObjectName("topMenuAppTitle")
        self.app_title_label.setStyleSheet("color: blue; font-size: 18px; font-weight: bold; padding-right: 15px;")
        self.app_title_label.setFixedWidth(200)

        # Setup shadow effect for animation
        self.app_title_shadow_effect.setBlurRadius(15)
        self.app_title_shadow_effect.setColor(QColor(0, 0, 0, 0)) # Start fully transparent
        self.app_title_shadow_effect.setOffset(0, 1) # Slight offset for a bit of depth
        self.app_title_label.setGraphicsEffect(self.app_title_shadow_effect)

        top_bar_layout.addWidget(self.app_title_label)


        # --- Define Menu Structure ---
        self.top_menu_buttons = {} # To store references

        # Helper to create module actions for the new "Modules" menu
        # These actions will call handle_sidebar_module_selection (which will be renamed or its logic adapted)
        module_menu_actions = []
        # Order can be defined here or taken from CONFIGURABLE_MODULES if its order is preferred.
        # Using CONFIGURABLE_MODULES to ensure all are covered and use their defined names/icons.
        for module_info in CONFIGURABLE_MODULES:
            action_attr_name = module_info['action_attr']
            q_action = getattr(self, action_attr_name, None)
            if q_action:
                # We need to ensure the action, when triggered from the top menu,
                # calls the correct view switching logic.
                # The QAction itself is already connected to a show_..._view method.
                module_menu_actions.append((q_action.text(), q_action))
            else:
                logging.warning(f"QAction instance for module {module_info['name']} (attr: {action_attr_name}) not found.")

        # Add core navigation items like "Accueil" and "Gestion Documents" if not in CONFIGURABLE_MODULES
        # or if they need special placement. For now, assuming they are QActions like others.
        # self.home_action and self.documents_view_action are already created.

        menu_definitions = [
            (self.tr("Accueil"), None, self.home_action), # Direct action, not a dropdown
            (self.tr("Modules"), None, module_menu_actions), # Dropdown for all other modules
            (self.tr("Statistiques"), None, self.statistics_action),
            (self.tr("Outils"), None, [
                (self.tr("Paramètres"), self.settings_action),
                (self.tr("Gérer les Statuts"), self.status_action),
                (self.tr("À propos"), self.about_action)
            ]),
            (self.tr("Administration"), None, [
                (self.tr("Gérer les Utilisateurs"), self.manage_users_action),
                (self.tr("Gérer les Rôles"), self.manage_roles_action)
            ]),
        ]

        for menu_title, menu_icon_path, actions_or_action_defs in menu_definitions:
            menu_button = QPushButton(menu_title)
            menu_button.setObjectName("topMenuButton")
            if menu_icon_path: # Not currently used for these main items
                menu_button.setIcon(QIcon(menu_icon_path))

            if isinstance(actions_or_action_defs, list): # It's a list of (text, QAction) for a dropdown
                if actions_or_action_defs: # If there are actions, create a dropdown menu
                    dropdown_menu = QMenu(self)
                    for action_text, q_action_obj in actions_or_action_defs:
                        if q_action_obj:
                            dropdown_menu.addAction(q_action_obj)
                        else:
                            logging.warning(f"QAction for '{action_text}' in menu '{menu_title}' not found.")
                    menu_button.setMenu(dropdown_menu)
            elif isinstance(actions_or_action_defs, QAction): # It's a single direct QAction
                menu_button.clicked.connect(actions_or_action_defs.trigger)

            top_bar_layout.addWidget(menu_button)
            self.top_menu_buttons[menu_title] = menu_button


        top_bar_layout.addStretch(1) # Pushes menu items to left, following items to right

        # Search bar (re-add with its completer)
        self.search_bar_line_edit = QLineEdit(self) # Already initialized in create_actions_main
        self.search_bar_line_edit.setObjectName("topMenuBarSearch") # Different object name for specific styling
        self.search_bar_line_edit.setPlaceholderText(self.tr("Rechercher..."))
        self.search_bar_line_edit.setFixedWidth(200) # Adjust width as needed
        self.search_bar_line_edit.setStyleSheet("""
            QLineEdit#topMenuBarSearch {
                padding: 5px 8px;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit#topMenuBarSearch:focus {
                border-color: #2563eb;
            }
        """)
        # Completer is already set up in create_actions_main
        self.search_completer = CategorizedCompleter(self)
        delegate = CategoryDelegate(self.search_completer.popup())
        self.search_completer.popup().setItemDelegate(delegate)
        self.search_bar_line_edit.setCompleter(self.search_completer)
        self.search_bar_line_edit.textChanged.connect(self.on_search_text_changed)
        self.search_completer.activated.connect(self.on_search_item_activated)
        top_bar_layout.addWidget(self.search_bar_line_edit)

        # Notifications Button
        self.notifications_button = QPushButton()
        self.notifications_button.setIcon(QIcon(":/icons/bell.svg"))
        self.notifications_button.setToolTip(self.tr("Notifications"))
        self.notifications_button.setObjectName("notificationButton")
        self.notification_panel = NotificationPanel(self)
        self.notifications_button.clicked.connect(self.notification_panel.toggle_panel)
        top_bar_layout.addWidget(self.notifications_button)

        # Notifications Button
        self.notifications_button = QPushButton()
        self.notifications_button.setIcon(QIcon(":/icons/bell.svg"))
        self.notifications_button.setToolTip(self.tr("Notifications"))
        self.notifications_button.setObjectName("notificationButton")
        top_bar_layout.addWidget(self.notifications_button)


        # User Menu Button (already initialized in create_actions_main)
        if not hasattr(self, 'user_menu_button_instance'): # Ensure it's created
            self.user_menu_button_instance = UserMenuButton(current_user_info=self.current_user_info, parent=self)
            self.user_menu_button_instance.setObjectName("userMenuButton")
            self.user_menu_button_instance.request_logout.connect(self._handle_logout)
            self.user_menu_button_instance.request_show_user_management_page.connect(self.show_user_management_page)
            self.user_menu_button_instance.request_open_edit_my_account_dialog.connect(self._handle_request_open_edit_my_account)
            self.user_menu_button_instance.request_open_add_user_dialog.connect(self._handle_request_open_add_user)

        self.user_menu_button_instance.setStyleSheet("""
            QPushButton#userMenuButton {
                background-color: transparent;
                color: #4b5563;
                border: none;
                padding: 5px 10px;
                font-size: 14px;
            }
            QPushButton#userMenuButton:hover {
                background-color: #e5e7eb;
                border-radius: 4px;
            }
        """)
        top_bar_layout.addWidget(self.user_menu_button_instance)

        # Window Controls (Minimize, Maximize, Close)
        window_controls_layout = QHBoxLayout()
        window_controls_layout.setSpacing(5)

        minimize_button = QToolButton()
        minimize_button.setText("—") # Or use an icon
        minimize_button.setToolTip(self.tr("Minimiser"))
        minimize_button.clicked.connect(self.showMinimized)

        maximize_button = QToolButton()
        maximize_button.setText("□") # Or use an icon
        maximize_button.setToolTip(self.tr("Agrandir / Restaurer"))
        maximize_button.clicked.connect(self.toggleMaximized)

        close_button = QToolButton()
        close_button.setText("✕") # Or use an icon
        close_button.setToolTip(self.tr("Fermer"))
        close_button.clicked.connect(self.close)

        for btn in [minimize_button, maximize_button, close_button]:
            btn.setObjectName("windowControlButton")
            btn.setFixedSize(28, 28)
            btn.setStyleSheet("""
                QToolButton#windowControlButton {
                    background-color: transparent;
                    border: none;
                    font-size: 16px;
                    color: #6b7280; /* Muted color */
                }
                QToolButton#windowControlButton:hover {
                    background-color: #e5e7eb;
                    border-radius: 4px;
                    color: #1f2937;
                }
            """)

        # Specific hover for close button
        close_button.setStyleSheet(close_button.styleSheet() + """
            QToolButton#windowControlButton:hover {
                background-color: #fee2e2; /* Light red on hover for close */
                color: #ef4444; /* Red text/icon */
            }
        """)

        window_controls_layout.addWidget(minimize_button)
        window_controls_layout.addWidget(maximize_button)
        window_controls_layout.addWidget(close_button)
        top_bar_layout.addLayout(window_controls_layout)

        self._update_user_display() # Initial update of user display
        self._apply_permissions() # Apply permissions on initial load

    def _apply_permissions(self):
        """Applies role-based permissions to UI elements."""
        from auth.permissions import has_permission, P_MANAGE_SYSTEM_SETTINGS, P_CREATE_CLIENT, \
                                     P_MANAGE_USERS, P_MANAGE_ROLES, P_ACCESS_PROJECT_MODULE, P_ACCESS_STATISTICS_MODULE, \
                                     P_ACCESS_PARTNER_MODULE, P_ACCESS_INVENTORY_MODULE, \
                                     P_ACCESS_RECRUITMENT_MODULE, P_ACCESS_EXPERIENCE_MODULE, \
                                     P_ACCESS_CALENDAR_MODULE, P_ACCESS_BOTPRESS_MODULE, \
                                     P_ACCESS_CARRIER_MAP_MODULE, P_ACCESS_CAMERA_MODULE, \
                                     P_MANAGE_GLOBAL_PRODUCTS, P_VIEW_GLOBAL_PRODUCTS, \
                                     P_ACCESS_CALCULATOR_MODULE, P_MANAGE_STATUSES # Added P_VIEW_GLOBAL_PRODUCTS

        role_name = self.current_user_info.get('role_name') if self.current_user_info else None
        role_name = self.current_user_info.get('role_name') if self.current_user_info else "UnknownRole"
        logging.info(f"Applying permissions for role: {role_name}")

        if not self.current_user_info: # Should not happen if login is enforced
            logging.error("_apply_permissions called with no current_user_info. Disabling most actions.")
            # Fallback to disable everything if user_info is missing
            is_admin_or_similar = False
            can_create_client = False
            # Disable all module actions
            for module_key in self.module_states.keys():
                action_attr_name = next((m['action_attr'] for m in CONFIGURABLE_MODULES if m['name'] == module_key), None)
                if action_attr_name and hasattr(self, action_attr_name):
                    getattr(self, action_attr_name).setVisible(False)
            self.settings_action.setEnabled(False)
            if hasattr(self, 'status_action'): self.status_action.setEnabled(False)
            self.admin_menu.menuAction().setVisible(False)
            self.add_new_client_button.setEnabled(False)
            self.add_client_by_voice_button.setEnabled(False)
            return

        is_admin_or_similar = has_permission(role_name, P_MANAGE_SYSTEM_SETTINGS)
        can_create_client = has_permission(role_name, P_CREATE_CLIENT)
        logging.info(f"  Role '{role_name}': P_MANAGE_SYSTEM_SETTINGS={is_admin_or_similar}, P_CREATE_CLIENT={can_create_client}")

        # --- Apply permissions to QActions (which are now in QMenus of the top menu buttons) ---
        # Settings Action
        self.settings_action.setEnabled(is_admin_or_similar)
        logging.info(f"  Action 'settings_action' enabled: {is_admin_or_similar} (P_MANAGE_SYSTEM_SETTINGS)")

        # Status Action
        if hasattr(self, 'status_action'):
            can_manage_statuses = has_permission(role_name, P_MANAGE_STATUSES)
            self.status_action.setEnabled(can_manage_statuses)
            logging.info(f"  Action 'status_action' enabled: {can_manage_statuses} (P_MANAGE_STATUSES)")


        # Customize Sidebar Action (assuming always enabled for logged-in users for now, or add a specific permission)
        if hasattr(self, 'customize_sidebar_action'):
            self.customize_sidebar_action.setEnabled(True) # Or add a specific permission check
            logging.info(f"  Action 'customize_sidebar_action' enabled: True (assuming)")


        # Admin Menu Actions (manage_users_action, manage_roles_action)
        can_manage_users = has_permission(role_name, P_MANAGE_USERS)
        can_manage_roles = has_permission(role_name, P_MANAGE_ROLES)

        can_manage_users_licensed = FEATURE_USER_MANAGEMENT_FULL in self.allowed_features
        self.manage_users_action.setEnabled(can_manage_users and can_manage_users_licensed)
        self.manage_roles_action.setEnabled(can_manage_roles and can_manage_users_licensed) # Assuming role management also tied to this feature
        logging.info(f"  Action 'manage_users_action' enabled: {self.manage_users_action.isEnabled()} (P_MANAGE_USERS={can_manage_users}, Licensed={can_manage_users_licensed})")
        logging.info(f"  Action 'manage_roles_action' enabled: {self.manage_roles_action.isEnabled()} (P_MANAGE_ROLES={can_manage_roles}, Licensed={can_manage_users_licensed})")

        # --- Control visibility of top-level menu buttons based on their actions' visibility ---
        # Example: Hide "Administration" button if both "Gérer les Utilisateurs" and "Gérer les Rôles" are disabled/hidden
        if hasattr(self, 'top_menu_buttons'):
            admin_button = self.top_menu_buttons.get(self.tr("Administration"))
            if admin_button:
                # An admin menu button should be visible if at least one of its actions is enabled.
                # QActions don't have isVisible(), use isEnabled() as a proxy for menu items.
                admin_menu_has_visible_action = self.manage_users_action.isEnabled() or self.manage_roles_action.isEnabled()
                admin_button.setVisible(admin_menu_has_visible_action)
                logging.info(f"  Top Menu Button 'Administration' visible: {admin_menu_has_visible_action}")

            tools_button = self.top_menu_buttons.get(self.tr("Outils"))
            if tools_button:
                tools_menu_has_visible_action = (self.settings_action.isEnabled() or
                                                 (hasattr(self, 'status_action') and self.status_action.isEnabled()) or
                                                 (hasattr(self, 'customize_sidebar_action') and self.customize_sidebar_action.isEnabled()))
                tools_button.setVisible(tools_menu_has_visible_action)
                logging.info(f"  Top Menu Button 'Outils' visible: {tools_menu_has_visible_action}")

            # File and Help menus are usually always visible.
            file_button = self.top_menu_buttons.get(self.tr("Fichier"))
            if file_button: file_button.setVisible(True) # Exit action always available

            help_button = self.top_menu_buttons.get(self.tr("Aide"))
            if help_button:
                 about_action = self.searchable_actions_map.get(self.tr("À propos"))
                 help_button.setVisible(about_action.isEnabled() if about_action else False)


        # Module Menu Actions & Feature Mapping (This part primarily affects sidebar now)
        # The QActions for modules are still used by the sidebar logic if they are added to it.
        # Their enabled/visible state here might affect if they *could* be added to a menu,
        # but the sidebar population logic (_populate_sidebar) has its own permission checks.
        # License feature checks will use module_config.get('license_feature').

        # Role-based permissions for modules (as before)
        module_role_permissions = {
            'project_management': P_ACCESS_PROJECT_MODULE,
            'product_management': (P_MANAGE_GLOBAL_PRODUCTS, P_VIEW_GLOBAL_PRODUCTS),
            'partner_management': P_ACCESS_PARTNER_MODULE,
            'statistics': P_ACCESS_STATISTICS_MODULE,
            'inventory_management': P_ACCESS_INVENTORY_MODULE,
            'experience_management': P_ACCESS_EXPERIENCE_MODULE,
            'calendar': P_ACCESS_CALENDAR_MODULE,
            'botpress_integration': P_ACCESS_BOTPRESS_MODULE,
            'carrier_map': P_ACCESS_CARRIER_MAP_MODULE,
            'camera_management': P_ACCESS_CAMERA_MODULE,
            'calculator': P_ACCESS_CALCULATOR_MODULE,
            'commandes_management': P_ACCESS_PROJECT_MODULE # Placeholder, uses project module perm for now
        }

        for module_config in CONFIGURABLE_MODULES:
            action_attr = module_config['action_attr']
            module_name = module_config['name']
            action_instance = getattr(self, action_attr, None)

            if not action_instance:
                logging.debug(f"  Module Action: '{action_attr}' not found as instance attribute, skipping permission check.")
                continue

            # Visibility is primarily controlled by module_states during menu creation.
            # Here, we ensure that if it was added to the menu (module enabled), its visibility
            # is then correctly set by permissions. If module was disabled, it's not in menu anyway.
            if not self.module_states.get(module_name, True): # If module is disabled via DB setting
                action_instance.setVisible(False) # Ensure it's hidden even if permissions would allow
                logging.info(f"  Module Action '{action_attr}' for '{module_name}': Module disabled by DB setting. Action HIDDEN.")
                continue

            perm_keys = module_role_permissions.get(module_name)
            permitted = False
            log_perm_details = ""

            if perm_keys:
                if isinstance(perm_keys, tuple): # Multiple permissions, OR logic
                    permitted = any(has_permission(role_name, pk) for pk in perm_keys)
                    log_perm_details = f"Permissions (OR logic): {perm_keys}, Result: {permitted}"
                else: # Single permission
                    permitted = has_permission(role_name, perm_keys)
                    log_perm_details = f"Permission: {perm_keys}, Result: {permitted}"
            else:
                # If no specific permission is defined for this module, assume visible if module is enabled.
                # Or, default to False if strict policy is desired. For now, assume visible.
                permitted = True
                log_perm_details = "No specific permission defined, defaulting to permitted if module is enabled."


            action_instance.setVisible(permitted)
            logging.info(f"  Module Action '{action_attr}' for '{module_name}': Role permitted: {permitted}. {log_perm_details}")

            # Additionally, check license feature for this module using the new structure
            if permitted: # Only check license if role permits
                license_feature = module_config.get('license_feature')
                if license_feature and license_feature not in self.allowed_features:
                    action_instance.setVisible(False) # Hide if license feature is required but not granted
                    logging.info(f"  Module Action '{action_attr}' for '{module_name}': HIDDEN due to missing license feature '{license_feature}'.")
                elif license_feature:
                    logging.info(f"  Module Action '{action_attr}' for '{module_name}': License feature '{license_feature}' GRANTED.")
                else:
                    logging.info(f"  Module Action '{action_attr}' for '{module_name}': No specific license feature required.")

            # Note: setEnabled could also be used if the action should be visible but greyed out.
            # For menu items, setVisible(False) effectively removes them.

        # Main Buttons on Document View
        log_msg_create_client = f"Permission P_CREATE_CLIENT for role '{role_name}': {'Granted' if can_create_client else 'Denied'}. "
        log_msg_create_client += f"Add New Client button {'enabled' if can_create_client else 'disabled'}."
        logging.info(log_msg_create_client)
        self.add_new_client_button.setEnabled(can_create_client)
        self.add_client_by_voice_button.setEnabled(can_create_client) # Assuming same permission
        logging.info(f"  Button 'add_new_client_button' enabled: {can_create_client}")
        logging.info(f"  Button 'add_client_by_voice_button' enabled: {can_create_client}")

        logging.info(f"Permissions application completed for role: {role_name}")



    def _update_user_display(self):
        if hasattr(self, 'user_menu_button_instance') and self.user_menu_button_instance:
            self.user_menu_button_instance.update_user_info(self.current_user_info)
        else:
            # Fallback or initial setup if button not yet created - though it should be.
            # This path is less likely if create_menus_main is called after current_user_info is set.
            if self.current_user_info:
                # self.user_info_label.setText(self.tr("Utilisateur: {0} ({1})").format(username, role_name)) # Old label
                # self.logout_button.setVisible(True) # Old button
                pass
            else:
                # self.user_info_label.setText(self.tr("Non connecté")) # Old label
                # self.logout_button.setVisible(False) # Old button
                pass

    def _handle_logout(self):
        # This method is now also connected to UserMenuButton.request_logout signal
        from auth import authentication as auth_service # Local import
        from dialogs.login_dialog import LoginDialog # Local import

        reply = QMessageBox.question(self, self.tr("Confirmation de Déconnexion"),
                                     self.tr("Êtes-vous sûr de vouloir vous déconnecter ?"),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.No:
            return

        auth_service.logout()
        self.current_user_info = None # Clear user info in main window
        self._update_user_display()

        # Optionally, close all tabs or reset parts of the UI
        # For example, close all client tabs:
        while self.client_tabs_widget.count() > 0:
            self.client_tabs_widget.removeTab(0)

        # Disable/hide UI elements that require login (to be implemented with RBAC)
        # For now, just clear the client list as an example of UI reset
        self.client_list_widget.clear()
        self.clients_data_map.clear()

        # Show login dialog again
        # This part is tricky as main.py initially handles the login loop.
        # A more robust way might be for DocumentManager to signal to main.py
        # that a logout occurred and main.py should re-trigger the login sequence.
        # For a simpler desktop app, restarting or re-showing login here can work.

        # Attempt to re-show login dialog.
        # This might need to be handled by exiting and restarting, or by a method in main.py
        # that can re-initialize the login loop.
        # For now, let's assume we re-show it directly, though this might have issues with app lifecycle.

        # A simple approach: hide main window, show login, if login ok, re-show main window.
        self.hide()
        login_dialog = LoginDialog(self) # Pass parent
        if login_dialog.exec_() == QDialog.Accepted:
            new_user_info = auth_service.get_current_user()
            if new_user_info:
                self.current_user_info = new_user_info
                self.current_user_id = self.current_user_info.get('user_id') # Update user_id
                self._update_user_display() # This will now call user_menu_button_instance.update_user_info()
                self._apply_permissions() # Re-apply permissions for the new user (menus etc.)
                self.load_clients_from_db_slot() # Reload data relevant to the new user
                # Potentially re-initialize other parts of the UI based on the new user/role
                self.show()
            else: # Should not happen if login_dialog.accept() implies success
                QMessageBox.critical(self, "Erreur de Reconnexion", "Impossible de récupérer les informations du nouvel utilisateur.")
                QApplication.instance().quit() # Exit if re-login fails critically
        else: # Login cancelled after logout
            QMessageBox.information(self, "Déconnexion", "Vous avez été déconnecté. L'application va se fermer.")
            QApplication.instance().quit() # Exit if user cancels login after logout

    def _handle_request_open_edit_my_account(self):
        if not self.current_user_info:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Aucun utilisateur n'est connecté."))
            return

        user_id_to_edit = self.current_user_info.get('user_id')
        if not user_id_to_edit:
            QMessageBox.critical(self, self.tr("Erreur Critique"), self.tr("ID utilisateur manquant pour l'utilisateur actuel."))
            return

        # Pass current_user_info as current_admin_user_info because the user is initiating the action on themselves.
        # EditUserDialog's internal logic will handle permissions for self-edit (e.g. role change).
        dialog = EditUserDialog(user_id=user_id_to_edit,
                                current_admin_user_info=self.current_user_info,
                                parent=self)
        if dialog.exec_() == QDialog.Accepted:
            # User data might have changed, re-fetch and update
            # This is important if e.g. full_name changed, to update display in UserMenuButton
            from auth import authentication as auth_service # Local import
            updated_user_info = auth_service.get_current_user() # Should reflect any changes if auth_service was updated by EditUserDialog
            if updated_user_info:
                 self.current_user_info = updated_user_info # Update main window's copy
                 self._update_user_display() # Refresh the UserMenuButton display
            # No need to reload client list or anything like that for self-account edit
            self.notify(self.tr("Compte Modifié"), self.tr("Vos informations de compte ont été mises à jour."), type='SUCCESS')


    def _handle_request_open_add_user(self):
        if not self.current_user_info:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Opération non permise sans être connecté."))
            return

        # current_user_info is passed as current_admin_user_info to EditUserDialog
        # The dialog itself (or the CRUD operation) will use P_MANAGE_USERS from this admin_user_info
        dialog = EditUserDialog(user_id=None, # Indicates "add" mode
                                current_admin_user_info=self.current_user_info,
                                parent=self)
        if dialog.exec_() == QDialog.Accepted:
            # If a user was added, and the current view is UserManagementPage, refresh its table
            if self.main_area_stack.currentWidget() == self.user_management_page_instance:
                if hasattr(self.user_management_page_instance, 'load_users_to_table'):
                    self.user_management_page_instance.load_users_to_table()
            self.notify(self.tr("Utilisateur Ajouté"), self.tr("Le nouvel utilisateur a été créé avec succès."), type='SUCCESS')


    @pyqtSlot(str)
    def handle_search_activation(self, text):
        logging.info(f"Search activated for: {text}")
        action_to_trigger = self.searchable_actions_map.get(text)
        if action_to_trigger:
            logging.info(f"Triggering action: {action_to_trigger.text()}")
            action_to_trigger.trigger()
            self.search_bar_line_edit.clear() # Clear search bar after activation
        else:
            logging.warning(f"No action found for search term: {text}")

    def handle_search_return_pressed(self):
        text = self.search_bar_line_edit.text()
        # Check if the current text is an exact match for a completer suggestion
        # This is a bit simplified; a more robust way might involve checking against the model
        if text in self.searchable_actions_map:
            self.handle_search_activation(text)
        # Optionally, if there's a unique completion, activate it,
        # or if multiple, do nothing or show popup. For now, exact match.

    def open_carrier_map_dialog(self):
        # This module is just a dialog, check its state if needed before opening
        if self.module_states.get('carrier_map', True):
            dialog = CarrierMapDialog(self)
            dialog.exec_()
        else:
            QMessageBox.information(self, self.tr("Module Désactivé"), self.tr("Le module 'Carrier Map' est actuellement désactivé."))
            logging.info("Carrier Map module is disabled. Dialog not opened.")


    def show_home_view(self):
        print("DocumentManager: show_home_view called.")
        if self.home_page_widget_instance:
            self.main_area_stack.setCurrentWidget(self.home_page_widget_instance)
        else:
            # This case should ideally not happen if initialization is correct
            logging.error("HomePageWidget instance is None. Cannot show home view.")
            QMessageBox.critical(self, self.tr("Erreur Critique"), self.tr("La page d'accueil n'a pas pu être chargée."))

    def show_project_management_view(self):
        if not self.module_states.get('project_management', True):
            QMessageBox.warning(self, self.tr("Module Désactivé"), self.tr("Le module Gestion de Projet est désactivé dans les paramètres."))
            logging.info("Project Management module is disabled by settings. View not shown.")
            return

        if self.project_management_widget_instance is None:
            logging.info("DocumentManager: Lazily creating ProjectManagementDashboard...")
            self.project_management_widget_instance = ProjectManagementDashboard(parent=self, current_user_info=self.current_user_info)
            self.main_area_stack.addWidget(self.project_management_widget_instance)
            logging.info("DocumentManager: ProjectManagementDashboard instance created and added to stack.")
            if hasattr(self.project_management_widget_instance, 'load_initial_data'):
                self.project_management_widget_instance.load_initial_data() # Ensure data is loaded on first show

        self.main_area_stack.setCurrentWidget(self.project_management_widget_instance)
        logging.info("Switched to Project Management view.")

    def show_documents_view(self):
        # This view (self.documents_page_widget) is initialized at startup.
        self.main_area_stack.setCurrentWidget(self.documents_page_widget)
        logging.info("Switched to Documents view.")

    def show_partner_management_view(self):
        if not self.module_states.get('partner_management', True):
            QMessageBox.warning(self, self.tr("Module Désactivé"), self.tr("Le module Gestion des Partenaires est désactivé dans les paramètres."))
            logging.info("Partner Management module is disabled by settings. View not shown.")
            return

        if self.partner_management_widget_instance is None:
            logging.info("DocumentManager: Lazily creating PartnerMainWidget...")
            self.partner_management_widget_instance = PartnerMainWidget(parent=self)
            self.main_area_stack.addWidget(self.partner_management_widget_instance)
            logging.info("DocumentManager: PartnerMainWidget instance created and added to stack.")
            if hasattr(self.partner_management_widget_instance, 'load_initial_data'):
                 self.partner_management_widget_instance.load_initial_data()

        self.main_area_stack.setCurrentWidget(self.partner_management_widget_instance)
        logging.info("Switched to Partner Management view.")

    def show_statistics_view(self):
        if not self.module_states.get('statistics', True):
            QMessageBox.warning(self, self.tr("Module Désactivé"), self.tr("Le module Statistiques est désactivé ou n'a pas pu être initialisé."))
            logging.info("Statistics module is disabled by settings. View not shown.")
            return

        # Use the getter which handles lazy creation
        target_widget = self.get_statistics_widget_instance()

        if target_widget:
            # Ensure it's in the stack (get_statistics_widget_instance should handle this)
            if self.main_area_stack.indexOf(target_widget) == -1:
                # This should ideally not happen if get_statistics_widget_instance works correctly
                logging.error(f"StatisticsDashboard instance {target_widget} was not in stack after lazy creation. Adding it now.")
                self.main_area_stack.addWidget(target_widget)

            self.main_area_stack.setCurrentWidget(target_widget)
            logging.info("Switched to Statistics view.")
        else:
            # This case means module is disabled or failed to init within the getter.
            # The getter itself would have logged details.
             QMessageBox.critical(self, self.tr("Erreur Module"), self.tr("Le module Statistiques n'a pas pu être chargé."))

    def show_inventory_browser_view(self):
        if not self.module_states.get('inventory_management', True):
            QMessageBox.warning(self, self.tr("Module Désactivé"), self.tr("Le module Gestion Stock Atelier est désactivé dans les paramètres."))
            logging.info("Inventory Management module is disabled by settings. View not shown.")
            return

        if self.inventory_browser_widget_instance is None:
            logging.info("DocumentManager: Lazily creating InventoryBrowserWidget...")
            self.inventory_browser_widget_instance = InventoryBrowserWidget(parent=self)
            self.main_area_stack.addWidget(self.inventory_browser_widget_instance)
            logging.info("DocumentManager: InventoryBrowserWidget instance created and added to stack.")
            if hasattr(self.inventory_browser_widget_instance, 'load_initial_data'):
                self.inventory_browser_widget_instance.load_initial_data()

        self.main_area_stack.setCurrentWidget(self.inventory_browser_widget_instance)
        logging.info("Switched to Inventory Browser view.")

    def show_botpress_integration_view(self):
        if not self.module_states.get('botpress_integration', True):
            QMessageBox.warning(self, self.tr("Module Désactivé"), self.tr("Le module Intégration Chatbot est désactivé dans les paramètres."))
            logging.info("Botpress Integration module is disabled by settings. View not shown.")
            return

        if self.botpress_integration_ui_instance is None:
            logging.info("DocumentManager: Lazily creating BotpressIntegrationUI...")
            self.botpress_integration_ui_instance = BotpressIntegrationUI(parent=self, current_user_id=self.current_user_id)
            self.main_area_stack.addWidget(self.botpress_integration_ui_instance)
            logging.info("DocumentManager: BotpressIntegrationUI instance created and added to stack.")
            # BotpressIntegrationUI typically loads its own settings/data in its __init__ or a dedicated load method.
            # If it has one like 'load_initial_data', call it here.

        self.main_area_stack.setCurrentWidget(self.botpress_integration_ui_instance)
        logging.info("Switched to Botpress Integration view.")

    def show_product_management_page(self):
        if not self.module_states.get('product_management', True):
            QMessageBox.warning(self, self.tr("Module Désactivé"), self.tr("Le module Gestion des Produits est désactivé dans les paramètres."))
            logging.info("Product Management module is disabled by settings. View not shown.")
            return

        if self.product_management_page_instance is None:
            logging.info("DocumentManager: Lazily creating ProductManagementPage...")
            self.product_management_page_instance = ProductManagementPage(current_user_info=self.current_user_info, parent=self)
            self.main_area_stack.addWidget(self.product_management_page_instance)
            logging.info("DocumentManager: ProductManagementPage instance created and added to stack.")
            if hasattr(self.product_management_page_instance, 'load_initial_data'):
                 self.product_management_page_instance.load_initial_data()

        self.main_area_stack.setCurrentWidget(self.product_management_page_instance)
        logging.info("Switched to Product Management page.")

    def show_recruitment_view(self):
        if not self.module_states.get('recruitment', True): # Assuming 'recruitment' is a valid key in module_states
            QMessageBox.warning(self, self.tr("Module Désactivé"), self.tr("Le module Recrutement est désactivé dans les paramètres."))
            logging.info("Recruitment module is disabled by settings. View not shown.")
            return

        if self.recruitment_dashboard_instance is None:
            logging.info("DocumentManager: Lazily creating RecruitmentDashboard...")
            self.recruitment_dashboard_instance = RecruitmentDashboard(parent=self) # Add current_user_info if needed by its constructor
            self.main_area_stack.addWidget(self.recruitment_dashboard_instance)
            logging.info("DocumentManager: RecruitmentDashboard instance created and added to stack.")
            # RecruitmentDashboard likely loads data per tab, or has an initial load.
            # If it has a general `load_initial_data` or `refresh_data`, call it.
            # For now, assuming its internal tab handling manages data loading.

        self.main_area_stack.setCurrentWidget(self.recruitment_dashboard_instance)
        logging.info("Switched to Recruitment view.")

    def show_camera_management_view(self):
        if not self.module_states.get('camera_management', True):
            QMessageBox.warning(self, self.tr("Module Désactivé"), self.tr("Le module Gestion Caméras est désactivé dans les paramètres."))
            logging.info("Camera Management module is disabled by settings. View not shown.")
            return

        if self.camera_management_widget_instance is None:
            logging.info("DocumentManager: Lazily creating CameraManagementWidget...")
            self.camera_management_widget_instance = CameraManagementWidget(parent=self, current_user_id=self.current_user_id)
            self.main_area_stack.addWidget(self.camera_management_widget_instance)
            logging.info("DocumentManager: CameraManagementWidget instance created and added to stack.")
            if hasattr(self.camera_management_widget_instance, 'load_initial_data'):
                self.camera_management_widget_instance.load_initial_data()
        else: # Widget exists, ensure user_id is current if it can change
            if hasattr(self.camera_management_widget_instance, 'set_current_user_id'):
                self.camera_management_widget_instance.set_current_user_id(self.current_user_id)


        self.main_area_stack.setCurrentWidget(self.camera_management_widget_instance)
        logging.info("Switched to Camera Management view.")

    def show_about_dialog(self): QMessageBox.about(self, self.tr("À propos"), self.tr("<b>Gestionnaire de Documents Client</b><br><br>Version 4.0<br>Application de gestion de documents clients avec templates Excel.<br><br>Développé par Saadiya Management (Concept)"))
        
    def execute_create_client_slot(self, client_data_dict=None):
        handle_create_client_execution(self, client_data_dict=client_data_dict)
        self.load_clients_from_db_slot()

    def load_clients_from_db_slot(self):
        # status_id_filter = self.status_filter_combo.currentData() # Old single status filter
        country_id_filter = self.country_filter_combo.currentData()
        category_filter_text = self.category_filter_input.text().strip() if hasattr(self, 'category_filter_input') else None

        archive_filter_data = self.client_archive_filter_combo.currentData()
        include_deleted_filter = False
        if archive_filter_data == "all_status_types": include_deleted_filter = True
        elif isinstance(archive_filter_data, bool): include_deleted_filter = archive_filter_data

        filters_for_crud = {}
        if self.selected_status_ids_filter: # Use the list of selected status IDs
            filters_for_crud['status_ids'] = self.selected_status_ids_filter

        if country_id_filter is not None: filters_for_crud['country_id'] = country_id_filter
        if category_filter_text: filters_for_crud['category'] = category_filter_text


        # Add date filters if they are set
        if hasattr(self, 'date_filter_start') and self.date_filter_start.date().isValid() and not self.date_filter_start.date().isNull():
            filters_for_crud['created_at_start'] = self.date_filter_start.date().toString("yyyy-MM-dd")

        if hasattr(self, 'date_filter_end') and self.date_filter_end.date().isValid() and not self.date_filter_end.date().isNull():
            filters_for_crud['created_at_end'] = self.date_filter_end.date().toString("yyyy-MM-dd")

        # Ajouter les paramètres de tri aux filtres passés au CRUD
        if hasattr(self, 'sort_by_combo') and self.sort_by_combo.currentData():
            filters_for_crud['order_by_field'] = self.sort_by_combo.currentData()
        if hasattr(self, 'sort_order_combo') and self.sort_order_combo.currentData():
            filters_for_crud['order_direction'] = self.sort_order_combo.currentData()

        # Note: la méthode get_all_clients_with_details a été modifiée pour extraire
        # 'order_by_field' et 'order_direction' de `filters` et les utiliser,
        # puis les retirer pour ne pas qu'ils soient interprétés comme des conditions WHERE.

        # Mettre à jour le nombre total de clients filtrés
        # Pour cela, il faut appeler la méthode CRUD sans limit/offset mais avec les filtres
        # Cela peut être coûteux si non optimisé. Idéalement, une méthode get_count(filters) serait mieux.
        # Pour l'instant, on récupère tout pour compter, puis on pagine.
        # La méthode CRUD get_all_clients_with_details s'attend à ce que order_by_field et order_direction soient dans filters.
        temp_filters_for_count = filters_for_crud.copy() # Copier pour ne pas modifier l'original pour la pagination

        all_matching_clients = clients_crud_instance.get_all_clients_with_details(
            filters=temp_filters_for_count,
            include_deleted=include_deleted_filter,
            limit=None, offset=0, conn=None # Pas de pagination pour le comptage
        )
        self.total_filtered_clients = len(all_matching_clients)

        # Charger et afficher la page actuelle de clients
        # `load_and_display_clients` utilise `get_all_clients_with_details` en interne.
        # Il faut s'assurer que `load_and_display_clients` passe bien les filtres (y compris de tri)
        # à `get_all_clients_with_details`.
        # La logique actuelle de `load_and_display_clients` devrait déjà le faire si `filters_for_crud` contient les clés de tri.
        load_and_display_clients(self, filters=filters_for_crud, limit=self.limit_per_page, offset=self.current_offset, include_deleted=include_deleted_filter)

        self.update_pagination_controls() # Mettre à jour les contrôles de pagination
        # filter_and_display_clients(self) # Cette ligne semble redondante si load_and_display_clients fait déjà l'affichage

    def filter_client_list_display_slot(self):
        self.current_offset = 0 # Réinitialiser à la première page lors d'un changement de filtre/tri
        self.load_clients_from_db_slot()

    def update_pagination_controls(self):
        current_page = (self.current_offset // self.limit_per_page) + 1
        if self.total_filtered_clients > 0:
            total_pages = (self.total_filtered_clients + self.limit_per_page - 1) // self.limit_per_page
        else:
            total_pages = 1 # ou 0 si self.total_filtered_clients est 0
        total_pages = max(1, total_pages) # Assurer qu'il y a au moins une page même si vide

        self.page_info_label.setText(self.tr("Page {0} / {1} ({2} éléments)").format(current_page, total_pages, self.total_filtered_clients))
        self.prev_page_button.setEnabled(self.current_offset > 0)
        self.next_page_button.setEnabled((self.current_offset + self.limit_per_page) < self.total_filtered_clients)

        # Activer/désactiver les contrôles "Aller à la page" en fonction du nombre de pages
        can_go_to_page = total_pages > 1
        if hasattr(self, 'go_to_page_input'): # Vérifier si les widgets existent
            self.go_to_page_input.setEnabled(can_go_to_page)
        if hasattr(self, 'go_to_page_button'):
            self.go_to_page_button.setEnabled(can_go_to_page)


    def _handle_go_to_page(self):
        if not hasattr(self, 'go_to_page_input') or not hasattr(self, 'total_filtered_clients'):
            return

        try:
            page_num_str = self.go_to_page_input.text().strip()
            if not page_num_str: # Si l'entrée est vide, ne rien faire
                return

            page_num = int(page_num_str)

            if self.total_filtered_clients > 0:
                total_pages = (self.total_filtered_clients + self.limit_per_page - 1) // self.limit_per_page
            else:
                total_pages = 1
            total_pages = max(1, total_pages)

            if 1 <= page_num <= total_pages:
                self.current_offset = (page_num - 1) * self.limit_per_page
                self.load_clients_from_db_slot()
                self.go_to_page_input.clear() # Vider le champ après navigation
            else:
                QMessageBox.warning(self, self.tr("Page Invalide"),
                                    self.tr("Veuillez entrer un numéro de page entre 1 et {0}.").format(total_pages))
                self.go_to_page_input.selectAll()
                self.go_to_page_input.setFocus()
        except ValueError:
            QMessageBox.warning(self, self.tr("Entrée Invalide"),
                                self.tr("Veuillez entrer un numéro de page valide."))
            self.go_to_page_input.selectAll()
            self.go_to_page_input.setFocus()


    def prev_page(self):
        if self.current_offset > 0:
            self.current_offset -= self.limit_per_page
            self.load_clients_from_db_slot()

    def next_page(self):
        # Advance only if there are more items based on total_filtered_clients
        if (self.current_offset + self.limit_per_page) < self.total_filtered_clients:
            self.current_offset += self.limit_per_page
            self.load_clients_from_db_slot()
        # update_pagination_controls will handle disabling the button if it's the last page


    def check_old_clients_routine_slot(self): perform_old_clients_check(self)
    def open_edit_client_dialog_slot(self, client_id): handle_open_edit_client_dialog(self, client_id)
    def set_client_status_archived_slot(self, client_id): archive_client_status(self, client_id)
    def delete_client_permanently_slot(self, client_id): permanently_delete_client(self, client_id)

    def toggle_search_input_visibility(self): # Renamed and removed 'checked' argument
        is_visible = not self.search_input_field.isVisible()
        self.search_input_field.setVisible(is_visible)
        self.search_label.setVisible(is_visible) # Toggle label visibility
        if is_visible:
            self.search_input_field.setFocus()
        # Removed button text change logic


    def execute_create_client(self, client_data_dict=None): self.execute_create_client_slot(client_data_dict=client_data_dict)
    def load_clients_from_db(self): self.load_clients_from_db_slot()
    def filter_client_list_display(self): self.filter_client_list_display_slot()
    def check_old_clients_routine(self): self.check_old_clients_routine_slot()
    def open_edit_client_dialog(self, client_id): self.open_edit_client_dialog_slot(client_id)
    def set_client_status_archived(self, client_id): self.set_client_status_archived_slot(client_id)
    def delete_client_permanently(self, client_id): self.delete_client_permanently_slot(client_id)

    # Old get_status_visual_indicator removed as its logic is now in ClientListItemWidget

    def add_client_to_list_widget(self, client_dict_data):
        item = QListWidgetItem(self.client_list_widget)
        # Pass self (DocumentManager instance) as parent to ClientListItemWidget
        # so it can access tr() or other methods if needed.
        # Or pass self.client_list_widget as parent for widget hierarchy.
        custom_widget = ClientListItemWidget(client_dict_data, self.client_list_widget)
        item.setSizeHint(custom_widget.sizeHint())

        # Store the raw client_dict_data in the QListWidgetItem's UserRole
        # This is crucial for context menus, click handling etc. to get the full data.
        item.setData(Qt.UserRole, client_dict_data)

        # Connecter les signaux des actions en ligne du custom_widget
        client_id_for_actions = client_dict_data.get("client_id")
        if client_id_for_actions:
            custom_widget.editActionClicked.connect(
                functools.partial(self.open_edit_client_dialog_slot, client_id_for_actions)
            )
            custom_widget.openFolderActionClicked.connect(
                functools.partial(self.open_client_folder_fs, client_id_for_actions)
            )
            # Connecter d'autres signaux ici si ajoutés (ex: archiveActionClicked)

        self.client_list_widget.addItem(item)
        self.client_list_widget.setItemWidget(item, custom_widget)


    def load_countries_into_filter_combo(self):
        current_selection_data = self.country_filter_combo.currentData()
        self.country_filter_combo.clear()
        self.country_filter_combo.addItem(self.tr("Tous les pays"), None)
        try:
            countries = db_manager.get_all_countries() # Attempt to get countries
            if countries is None: countries = []
            for country_dict in countries:
                self.country_filter_combo.addItem(country_dict['country_name'], country_dict.get('country_id'))
            
            # Restore previous selection if possible
            index = self.country_filter_combo.findData(current_selection_data)
            if index != -1: self.country_filter_combo.setCurrentIndex(index)
            else: self.country_filter_combo.setCurrentIndex(0) # Default to "All countries"
        except AttributeError:
            logging.warning("db_manager.get_all_countries() function might not exist or returned an unexpected type. Country filter will be empty.")
            # Optionally, disable the combo box or show a message
            # self.country_filter_combo.setEnabled(False)
        except Exception as e:
            logging.error(self.tr("Erreur chargement pays pour filtre: {0}").format(str(e)))
            # self.country_filter_combo.setEnabled(False)

    # load_statuses_into_filter_combo is no longer needed as statuses are loaded in MultiSelectStatusDialog
            
    def handle_client_list_click(self, item):
        logging.info(f"handle_client_list_click entered. Item text: {item.text()}, Item data: {item.data(Qt.UserRole)}")
        client_data = item.data(Qt.UserRole)
        if client_data and client_data.get("client_id"):
            self.open_client_tab_by_id(client_data["client_id"])
        
    def open_client_tab_by_id(self, client_id_to_open):
        # Attempt to fetch fresh client data directly from the database
        logging.info(f"open_client_tab_by_id: Called with client_id_to_open={client_id_to_open}")
        client_data_to_show = clients_crud_instance.get_client_by_id(client_id_to_open, include_deleted=True)
        logging.info(f"open_client_tab_by_id: client_data_to_show after fetching from DB: {client_data_to_show}")

        if client_data_to_show:
            # Ensure default_base_folder_path exists and is valid, then alias to base_folder_path
            current_default_path = client_data_to_show.get("default_base_folder_path")
            if not current_default_path or not current_default_path.strip():
                client_name_for_folder = client_data_to_show.get("client_name", "unknown_client")
                client_id_for_folder = client_data_to_show.get("client_id", "no_id")
                sane_client_name = "".join(c if c.isalnum() else "_" for c in client_name_for_folder)

                # Ensure clients_dir itself is a valid part of the path construction
                # CONFIG.get('clients_dir', 'clients') gives the relative path like 'clients'
                clients_base_subdir = CONFIG.get('clients_dir', 'clients') # e.g., "clients"

                relative_folder = os.path.join(clients_base_subdir, f"{sane_client_name}_{client_id_for_folder[:8]}")
                client_data_to_show["default_base_folder_path"] = relative_folder

                abs_folder_path = os.path.join(self.app_root_dir, relative_folder)
                try:
                    os.makedirs(abs_folder_path, exist_ok=True)
                    logging.info(f"Ensured client folder exists at: {abs_folder_path}")
                    # Update the database so this path is persistent
                    clients_crud_instance.update_client(client_id_to_open, {"default_base_folder_path": relative_folder})
                    logging.info(f"Client {client_id_to_open} was missing default_base_folder_path. Constructed, assigned, and DB updated: {relative_folder}.")
                except OSError as e_mkdir:
                    logging.error(f"Failed to create directory {abs_folder_path}: {e_mkdir}")
                    # Proceeding without this could still lead to issues, but client_data_to_show will have the path

            # Ensure base_folder_path is an alias to default_base_folder_path for ClientMainWidget
            client_data_to_show["base_folder_path"] = client_data_to_show.get("default_base_folder_path")

        if client_data_to_show and 'created_at' in client_data_to_show and client_data_to_show['created_at']:
            try:
                created_at_str = client_data_to_show['created_at']
                # Python's fromisoformat handles 'Z' correctly in 3.7+
                # If older version, might need: created_at_str = created_at_str.replace('Z', '+00:00')
                dt_object = datetime.fromisoformat(created_at_str.replace('Z', '+00:00')) # Ensure Z is handled
                client_data_to_show['creation_date'] = dt_object.strftime('%Y-%m-%d')
            except ValueError as e:
                logging.error(f"Error parsing 'created_at' timestamp: {client_data_to_show['created_at']} - {e}")
                client_data_to_show['creation_date'] = 'N/A' # Default on error
        elif client_data_to_show:
            client_data_to_show['creation_date'] = 'N/A' # Default if 'created_at' is missing or None

        if not client_data_to_show:
            # If fetching from DB fails, show an error and return.
            # Relying on self.clients_data_map might show stale or deleted client data.
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Impossible de récupérer les données à jour pour le client (ID: {0}). Le client pourrait ne pas exister ou être archivé.").format(client_id_to_open))
            return

        # Proceed with augmenting and displaying the fresh client_data_to_show
        if 'country' not in client_data_to_show and client_data_to_show.get('country_id'):
            country_obj = db_manager.get_country_by_id(client_data_to_show['country_id'])
            client_data_to_show['country'] = country_obj.get('country_name', "N/A") if country_obj else "N/A"
        if 'city' not in client_data_to_show and client_data_to_show.get('city_id'):
            city_obj = db_manager.get_city_by_id(client_data_to_show['city_id'])
            client_data_to_show['city'] = city_obj.get('city_name', "N/A") if city_obj else "N/A"
        if 'status' not in client_data_to_show and client_data_to_show.get('status_id'):
            status_obj = db_manager.get_status_setting_by_id(client_data_to_show['status_id'])
            client_data_to_show['status'] = status_obj.get('status_name', "N/A") if status_obj else "N/A"

        logging.info(f"open_client_tab_by_id: client_id_to_open={client_id_to_open}, "
                     f"client_data_to_show name={client_data_to_show.get('client_name')}, "
                     f"email={client_data_to_show.get('email')}, phone={client_data_to_show.get('phone')}")

        # Ensure selected_languages is a list, defaulting to ['fr'] if null/empty from DB
        selected_languages_value = client_data_to_show.get('selected_languages')
        if isinstance(selected_languages_value, str) and selected_languages_value.strip():
            # If it's a non-empty string, parse it
            parsed_langs = [lang.strip() for lang in selected_languages_value.split(',') if lang.strip()]
            client_data_to_show['selected_languages'] = parsed_langs if parsed_langs else ['fr']
        elif isinstance(selected_languages_value, list):
            # If it's already a list (e.g. from tests or direct data manipulation)
            # Use as is, but default to ['fr'] if the list is empty
            client_data_to_show['selected_languages'] = selected_languages_value if selected_languages_value else ['fr']
        else:
            # If it's None, empty string, or any other type, default to ['fr']
            client_data_to_show['selected_languages'] = ['fr']

        # A final safety net: if after all processing selected_languages is somehow empty (e.g. parsed string resulted in empty list), default to ['fr']
        if not client_data_to_show.get('selected_languages'):
            client_data_to_show['selected_languages'] = ['fr']

        logging.info(f"open_client_tab_by_id: client_data_to_show after augmentation: {client_data_to_show}")

        for i in range(self.client_tabs_widget.count()):
            tab_widget_ref = self.client_tabs_widget.widget(i)
            if hasattr(tab_widget_ref, 'client_info') and tab_widget_ref.client_info["client_id"] == client_id_to_open:
                logging.info(f"main_window.open_client_tab_by_id: Refreshing existing tab for client_id: {client_id_to_open}")
                self.client_tabs_widget.setCurrentIndex(i)
                if hasattr(tab_widget_ref, 'refresh_display'):
                    tab_widget_ref.refresh_display(client_data_to_show)
                return

        logging.info(f"main_window.open_client_tab_by_id: Preparing to instantiate ClientMainWidget with data: {client_data_to_show}")
        logging.info(f"main_window.open_client_tab_by_id: Attempting to create ClientMainWidget for client_id: {client_id_to_open}")
        try:
            notification_manager = QApplication.instance().notification_manager
            client_widget = ClientMainWidget( # Changed ClientWidget to ClientMainWidget
                client_info=client_data_to_show,
                config=self.config,
                app_root_dir=self.app_root_dir,
                notification_manager=notification_manager,
                current_user_info=self.current_user_info,
                client_controller_instance=self.client_controller_instance, # Pass ClientController instance
                parent=self
            )
            logging.info(f"main_window.open_client_tab_by_id: Successfully created ClientMainWidget for client_id: {client_id_to_open} with user_info.") # Log updated
        except Exception as e:
            logging.error(f"main_window.open_client_tab_by_id: Error instantiating ClientMainWidget for client_id: {client_id_to_open} - {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Critique"), self.tr("Impossible de créer l'onglet client. Erreur: {0}").format(str(e)))
            return

        logging.info(f"main_window.open_client_tab_by_id: Attempting to add ClientMainWidget to tab for client_id: {client_id_to_open}")
        try:
            client_name_for_tab = client_data_to_show.get("client_name", self.tr("Client Inconnu"))
            index = self.client_tabs_widget.addTab(client_widget, client_name_for_tab)
            self.client_tabs_widget.setCurrentIndex(index)
            logging.info(f"main_window.open_client_tab_by_id: Successfully added ClientMainWidget tab for client_id: {client_id_to_open} at index {index}")
        except Exception as e:
            logging.error(f"main_window.open_client_tab_by_id: Error adding ClientMainWidget to tab for client_id: {client_id_to_open} - {e}", exc_info=True)
            QMessageBox.critical(self, self.tr("Erreur Critique"), self.tr("Impossible d'ajouter l'onglet client au gestionnaire d'onglets. Erreur: {0}").format(str(e)))
            # Attempt to clean up the partially created widget if it exists
            if 'client_widget' in locals() and client_widget:
                client_widget.deleteLater()
            return
            
    def close_client_tab(self, index): 
        widget_to_close = self.client_tabs_widget.widget(index) 
        if widget_to_close: widget_to_close.deleteLater()
        self.client_tabs_widget.removeTab(index)
        
    def show_client_context_menu(self, pos):
        list_item = self.client_list_widget.itemAt(pos) 
        if not list_item: return
        client_data = list_item.data(Qt.UserRole)
        client_id_val = client_data.get("client_id") if client_data else None
        if not client_id_val: return

        menu = QMenu()
        open_action = menu.addAction(QIcon(":/icons/eye.svg"), self.tr("Ouvrir Fiche Client")); open_action.triggered.connect(lambda: self.open_client_tab_by_id(client_id_val))
        edit_action = menu.addAction(QIcon(":/icons/pencil.svg"), self.tr("Modifier Client")); edit_action.triggered.connect(lambda: self.open_edit_client_dialog_slot(client_id_val))
        open_folder_action = menu.addAction(QIcon(":/icons/folder.svg"), self.tr("Ouvrir Dossier Client")); open_folder_action.triggered.connect(lambda: self.open_client_folder_fs(client_id_val))
        menu.addSeparator()
        archive_action = menu.addAction(QIcon(":/icons/briefcase.svg"), self.tr("Archiver Client")); archive_action.triggered.connect(lambda: self.set_client_status_archived_slot(client_id_val))
        delete_action = menu.addAction(QIcon(":/icons/trash.svg"), self.tr("Supprimer Client")); delete_action.triggered.connect(lambda: self.delete_client_permanently_slot(client_id_val))
        menu.exec_(self.client_list_widget.mapToGlobal(pos))
        
    def open_client_folder_fs(self, client_id_val): 
        client_info = self.clients_data_map.get(client_id_val)
        if client_info and client_info.get("base_folder_path"):
            QDesktopServices.openUrl(QUrl.fromLocalFile(client_info["base_folder_path"]))
        else:
            QMessageBox.warning(self, self.tr("Erreur"), self.tr("Chemin du dossier non trouvé pour ce client."))
            self.notify(title=self.tr("Accès Dossier Échoué"),
                        message=self.tr("Chemin du dossier non trouvé pour le client '{0}'.").format(client_info.get('client_name', 'N/A') if client_info else 'N/A'),
                        type='WARNING')

    def show_settings_page(self):
        self.main_area_stack.setCurrentWidget(self.settings_page_instance)

        # SettingsPage is initialized at startup. We ensure its data is fresh when shown.
        if hasattr(self.settings_page_instance, 'refresh_all_data'): # Assuming a consolidated refresh method
            self.settings_page_instance.refresh_all_data()
        else: # Fallback to individual load methods if refresh_all_data doesn't exist
            if hasattr(self.settings_page_instance, '_load_all_settings_from_config'):
                self.settings_page_instance._load_all_settings_from_config()
            if hasattr(self.settings_page_instance, '_load_transporters_table'):
                self.settings_page_instance._load_transporters_table()
            if hasattr(self.settings_page_instance, '_load_forwarders_table'):
                self.settings_page_instance._load_forwarders_table()
            if hasattr(self.settings_page_instance, 'company_tab') and \
               hasattr(self.settings_page_instance.company_tab, 'load_all_data'):
                self.settings_page_instance.company_tab.load_all_data()

        # Ensure the save button signal is connected
        try:
            self.settings_page_instance.save_settings_button.clicked.disconnect(self._handle_settings_saved)
        except TypeError: # This happens if it was not connected before
            pass # No need to disconnect if not connected
        self.settings_page_instance.save_settings_button.clicked.connect(self._handle_settings_saved)
        logging.info("Switched to Settings Page and refreshed its data.")

    def open_multi_select_status_dialog(self):
        from dialogs.multi_select_status_dialog import MultiSelectStatusDialog # Local import

        dialog = MultiSelectStatusDialog(pre_selected_status_ids=self.selected_status_ids_filter, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.selected_status_ids_filter = dialog.get_selected_status_ids()
            if not self.selected_status_ids_filter: # Empty list means "All"
                self.status_filter_button.setText(self.tr("Statut: Tous"))
            elif len(self.selected_status_ids_filter) == 1:
                # Try to get status name for single selection display
                status_name = self.tr("Statut: Inconnu")
                try:
                    status_info = db_manager.get_status_setting_by_id(self.selected_status_ids_filter[0])
                    if status_info:
                        status_name = status_info.get('status_name', self.tr("Inconnu"))
                    self.status_filter_button.setText(self.tr("Statut: {0}").format(status_name))
                except Exception as e_status_name:
                    logging.error(f"Error fetching status name for ID {self.selected_status_ids_filter[0]}: {e_status_name}")
                    self.status_filter_button.setText(self.tr("Statut: ID {0}").format(self.selected_status_ids_filter[0]))
            else:
                self.status_filter_button.setText(self.tr("Statut: {0} sélectionnés").format(len(self.selected_status_ids_filter)))

            self.filter_client_list_display_slot() # Trigger refresh
        # If dialog is cancelled, self.selected_status_ids_filter remains unchanged.

    def _handle_settings_saved(self):
        """Called when 'Save All Settings' in SettingsPage is clicked."""
        logging.info("Handling settings saved signal from SettingsPage...")
        current_states_copy = dict(self.module_states)
        self._load_module_states()  # Reload from DB to get potentially changed states

        if current_states_copy != self.module_states:
            logging.info("Module states have changed. Prompting for restart to apply menu changes.")
            QMessageBox.information(self,
                                    self.tr("Redémarrage Requis"),
                                    self.tr("Les paramètres de visibilité des modules ont été modifiés. "
                                            "Veuillez redémarrer l'application pour que les changements de menu prennent pleinement effet."))
            # Menu changes will be visible on next startup due to _load_module_states and create_menus_main.
            # No immediate menu recreation here to keep it simple and enforce restart for full effect.

        self.init_or_update_download_monitor()
        logging.info("Settings saved. Checked for module changes and re-initialized download monitor.")

    def open_status_management_dialog_slot(self):
        logging.info("Opening Status Management Dialog.")
        dialog = StatusManagementDialog(parent=self)
        dialog.exec_()
        logging.info("Status Management Dialog closed. Refreshing client widgets and filters.")
        self.refresh_client_widgets_and_filters()

    def refresh_client_widgets_and_filters(self):
        logging.info("Refreshing client-related UI components after status changes.")
        self.load_statuses_into_filter_combo()

        for i in range(self.client_tabs_widget.count()):
            tab_widget = self.client_tabs_widget.widget(i)
            if isinstance(tab_widget, ClientMainWidget): # Check against ClientMainWidget
                client_id = tab_widget.client_info.get("client_id")
                if client_id:
                    fresh_data = clients_crud_instance.get_client_by_id(client_id, include_deleted=False)
                    if fresh_data:
                        # Augment with status name, country name etc. as done in open_client_tab_by_id
                        if 'status' not in fresh_data and fresh_data.get('status_id'):
                            status_obj = db_manager.get_status_setting_by_id(fresh_data['status_id'])
                            fresh_data['status'] = status_obj.get('status_name', "N/A") if status_obj else "N/A"
                        # ... (add other augmentations if needed for display) ...

                        if hasattr(tab_widget, 'refresh_display'):
                            tab_widget.refresh_display(fresh_data)
                        if hasattr(tab_widget, 'load_statuses_for_combos'): # If ClientMainWidget has such a method
                             tab_widget.load_statuses_for_combos()
                    else:
                         logging.warning(f"Could not re-fetch data for client ID: {client_id} in open tab.")
            # elif isinstance(tab_widget, ClientWidget): # Old type, handle if still possible
            #     # Similar logic for old ClientWidget if needed, but focus is on ClientMainWidget
            #     pass


        self.load_clients_from_db_slot() # Refresh main client list
        self.notify(self.tr("Mise à jour"), self.tr("Interface mise à jour suite aux changements de statuts."), "INFO")

    def closeEvent(self, event):
        logging.info("Close event triggered. Stopping services and saving config.")
        if self.download_monitor_service:
            logging.info("Stopping download monitor service due to application close.")
            self.download_monitor_service.stop()
        save_config(self.config)
        super().closeEvent(event)

    # Removed placeholder methods for load_countries_into_combo, load_cities_for_country, etc.
    # as they are typically part of specific dialogs, not general DocumentManager methods.
    def add_new_country_dialog(self):
        pass # Placeholder, likely belongs in a dialog context
    def add_new_city_dialog(self):
        pass

    def show_experience_module_view(self):
        if not self.module_states.get('experience_management', True): # Default to True if not in DB settings
            QMessageBox.warning(self, self.tr("Module Désactivé"), self.tr("Le module Gestion des Connaissances est désactivé dans les paramètres."))
            logging.info("Experience Management module is disabled by settings. View not shown.")
            return

        if self.experience_management_widget_instance is None:
            logging.info("DocumentManager: Lazily creating ExperienceModuleWidget...")
            self.experience_management_widget_instance = ExperienceModuleWidget(parent=self) # Add current_user_info if needed
            self.main_area_stack.addWidget(self.experience_management_widget_instance)
            logging.info("DocumentManager: ExperienceModuleWidget instance created and added to stack.")
            if hasattr(self.experience_management_widget_instance, 'load_initial_data'):
                self.experience_management_widget_instance.load_initial_data()

        self.main_area_stack.setCurrentWidget(self.experience_management_widget_instance)
        logging.info("Switched to Experience Management view.")

    def show_calendar_module_view(self):
        if not self.module_states.get('calendar', True):
            QMessageBox.warning(self, self.tr("Module Désactivé"), self.tr("Le module Calendrier est désactivé dans les paramètres."))
            logging.info("Calendar module is disabled by settings. View not shown.")
            return

        if self.calendar_module_widget_instance is None:
            logging.info("DocumentManager: Lazily creating CalendarWidget...")
            self.calendar_module_widget_instance = CalendarWidget(parent=self, current_user_id=self.current_user_id)
            self.main_area_stack.addWidget(self.calendar_module_widget_instance)
            logging.info("DocumentManager: CalendarWidget instance created and added to stack.")
            # Initial data load for calendar usually happens in its constructor or a specific load method called after.
            # Forcing a refresh of events and settings when shown for the first time (or if already exists).

        if hasattr(self.calendar_module_widget_instance, 'current_user_id'): # Update user_id if it can change
             self.calendar_module_widget_instance.current_user_id = self.current_user_id
        if hasattr(self.calendar_module_widget_instance, '_load_company_settings'): # Ensure settings are current
            self.calendar_module_widget_instance._load_company_settings()
        if hasattr(self.calendar_module_widget_instance, '_load_user_events'): # Refresh events
            self.calendar_module_widget_instance._load_user_events()

        self.main_area_stack.setCurrentWidget(self.calendar_module_widget_instance)
        logging.info("Switched to Calendar module view.")

    def show_user_management_page(self):
        # This page (self.user_management_page_instance) is initialized at startup.
        if self.user_management_page_instance:
            if hasattr(self.user_management_page_instance, 'load_users_to_table'):
                self.user_management_page_instance.load_users_to_table() # Refresh data
            self.main_area_stack.setCurrentWidget(self.user_management_page_instance)
            logging.info("Switched to User Management page.")
        else: # Should not happen
            logging.error("UserManagementPage instance is None. Cannot show user management view.")
            QMessageBox.critical(self, self.tr("Erreur Critique"), self.tr("La page de gestion des utilisateurs n'a pas pu être chargée."))

    def show_calculator_module_view(self):
        if not self.module_states.get('calculator', True):
            QMessageBox.warning(self, self.tr("Module Désactivé"), self.tr("Le module Calculatrices est désactivé dans les paramètres."))
            logging.info("Calculator module is disabled by settings. View not shown.")
            return

        if self.calculator_module_widget_instance is None:
            logging.info("DocumentManager: Lazily creating MainCalculatorWidget...")
            self.calculator_module_widget_instance = MainCalculatorWidget(
                parent=self,
                app_auth_manager=self, # Pass self (DocumentManager) as auth manager
                db_session_factory=None
            )
            self.main_area_stack.addWidget(self.calculator_module_widget_instance)
            logging.info("DocumentManager: MainCalculatorWidget instance created and added to stack.")
            # If MainCalculatorWidget has an initial data load method, call it here.
            # if hasattr(self.calculator_module_widget_instance, 'load_initial_data'):
            #     self.calculator_module_widget_instance.load_initial_data()
        else: # Widget exists, ensure auth manager is current if it could change
            if hasattr(self.calculator_module_widget_instance, 'app_auth_manager'):
                self.calculator_module_widget_instance.app_auth_manager = self


        self.main_area_stack.setCurrentWidget(self.calculator_module_widget_instance)
        logging.info("Switched to Calculator module view.")

    def show_commande_management_view(self):
        # This page (self.commandes_dashboard_widget_instance) is initialized at startup.
        if self.commandes_dashboard_widget_instance:
            if hasattr(self.commandes_dashboard_widget_instance, '_load_initial_data'):
                self.commandes_dashboard_widget_instance._load_initial_data() # Refresh data
            self.main_area_stack.setCurrentWidget(self.commandes_dashboard_widget_instance)
            logging.info("Switched to CommandesDashboardWidget.")
        else: # Should not happen
            logging.error("CommandesDashboardWidget instance is None. Cannot show view.")
            QMessageBox.critical(self, self.tr("Erreur Module Commande"), self.tr("Le module de gestion des commandes n'a pas pu être chargé."))

    def focus_on_project(self, project_id: str):
        """
        Switches to the Project Management dashboard and attempts to focus on/display
        the specified project.
        """
        if not project_id:
            self.notify(self.tr("Erreur"), self.tr("Aucun ID de projet fourni pour la navigation."), type='ERROR')
            return

        if self.project_management_widget_instance:
            self.main_area_stack.setCurrentWidget(self.project_management_widget_instance)
            if hasattr(self.project_management_widget_instance, 'find_and_display_project'):
                # This method needs to be implemented in ProjectManagementDashboard
                self.project_management_widget_instance.find_and_display_project(project_id)
                logging.info(f"Attempted to focus on project ID: {project_id} in Project Management Dashboard.")
            else:
                logging.warning(f"ProjectManagementDashboard does not have 'find_and_display_project' method. Cannot focus on project {project_id}.")
                self.notify(self.tr("Fonctionnalité Manquante"),
                            self.tr("Impossible de focaliser sur le projet spécifique dans le tableau de bord des projets."),
                            type='WARNING')
        else:
            self.notify(self.tr("Module Désactivé"), self.tr("Le module de gestion de projet est désactivé."), type='WARNING')
            logging.warning(f"Cannot focus on project {project_id}, Project Management module is not loaded/enabled.")

    # --- Saved Filters Methods ---
    def populate_saved_filters_combo(self):
        """Populates the combo box with filters saved by the current user."""
        self.load_filter_combo.blockSignals(True)
        self.load_filter_combo.clear()
        self.load_filter_combo.addItem(self.tr("--- Sélectionner un filtre ---"), None) # Placeholder

        if not self.current_user_id:
            logging.warning("populate_saved_filters_combo: No current_user_id, cannot load filters.")
            self.load_filter_combo.blockSignals(False)
            return

        try:
            saved_filters = user_saved_filters_crud.get_saved_filters_for_user(self.current_user_id)
            if saved_filters:
                for filt in saved_filters:
                    self.load_filter_combo.addItem(filt['filter_name'], filt['id'])
            logging.info(f"Populated saved filters combo with {len(saved_filters)} items for user {self.current_user_id}.")
        except Exception as e:
            logging.error(f"Error populating saved filters combo: {e}", exc_info=True)
            self.notify(self.tr("Erreur Filtres Sauvegardés"), self.tr("Impossible de charger les filtres sauvegardés."), type='ERROR')
        finally:
            self.load_filter_combo.blockSignals(False)

    def apply_saved_filter_slot(self, index: int):
        """Applies the selected saved filter to the UI controls and refreshes the client list."""
        if index == 0: # Placeholder selected
            return

        saved_filter_id = self.load_filter_combo.itemData(index)
        if saved_filter_id is None:
            return

        logging.info(f"Applying saved filter with ID: {saved_filter_id}")

        try:
            filter_data = user_saved_filters_crud.get_saved_filter_by_id(saved_filter_id, self.current_user_id)
            if not filter_data or 'filter_parameters' not in filter_data:
                self.notify(self.tr("Erreur Chargement Filtre"), self.tr("Filtre non trouvé ou corrompu."), type='ERROR')
                self.populate_saved_filters_combo() # Refresh combo in case filter was deleted elsewhere
                return

            params = filter_data['filter_parameters']

            # Block signals on individual filter controls to prevent multiple refreshes
            self.status_filter_combo.blockSignals(True)
            self.client_archive_filter_combo.blockSignals(True)
            self.country_filter_combo.blockSignals(True)
            self.search_input_field.blockSignals(True)
            if hasattr(self, 'date_filter_start'): self.date_filter_start.blockSignals(True)
            if hasattr(self, 'date_filter_end'): self.date_filter_end.blockSignals(True)
            if hasattr(self, 'more_filters_button'): self.more_filters_button.blockSignals(True)


            # Apply status filter (now multi-select)
            self.selected_status_ids_filter = params.get('status_ids', [])
            if not self.selected_status_ids_filter:
                self.status_filter_button.setText(self.tr("Statut: Tous"))
            elif len(self.selected_status_ids_filter) == 1:
                 # Try to get status name for single selection display
                status_name_display = self.tr("Statut: Inconnu")
                try:
                    status_info = db_manager.get_status_setting_by_id(self.selected_status_ids_filter[0])
                    if status_info: status_name_display = status_info.get('status_name', self.tr("Inconnu"))
                    self.status_filter_button.setText(self.tr("Statut: {0}").format(status_name_display))
                except Exception as e_status_name_saved:
                    logging.error(f"Error fetching status name for saved ID {self.selected_status_ids_filter[0]}: {e_status_name_saved}")
                    self.status_filter_button.setText(self.tr("Statut: ID {0}").format(self.selected_status_ids_filter[0]))
            else:
                self.status_filter_button.setText(self.tr("Statut: {0} sélectionnés").format(len(self.selected_status_ids_filter)))


            # Apply archive filter
            archive_idx = self.client_archive_filter_combo.findData(params.get('archive_filter'))
            self.client_archive_filter_combo.setCurrentIndex(archive_idx if archive_idx != -1 else 0)

            # Apply country filter
            country_idx = self.country_filter_combo.findData(params.get('country_id'))
            self.country_filter_combo.setCurrentIndex(country_idx if country_idx != -1 else 0)

            # Apply category filter
            if hasattr(self, 'category_filter_input'):
                self.category_filter_input.setText(params.get('category', ''))


            # Apply search term
            self.search_input_field.setText(params.get('search_term', ''))

            # Apply date filters
            show_collapsible = False # Flag to determine if advanced filter section should be visible
            if hasattr(self, 'date_filter_start'):
                date_start_str = params.get('created_at_start')
                if date_start_str:
                    self.date_filter_start.setDate(QDate.fromString(date_start_str, "yyyy-MM-dd"))
                    if self.date_filter_start.date().isValid(): show_collapsible = True
                else:
                    self.date_filter_start.setDate(QDate())

            if hasattr(self, 'date_filter_end'):
                date_end_str = params.get('created_at_end')
                if date_end_str:
                    self.date_filter_end.setDate(QDate.fromString(date_end_str, "yyyy-MM-dd"))
                    if self.date_filter_end.date().isValid(): show_collapsible = True
                else:
                    self.date_filter_end.setDate(QDate())

            # Determine if collapsible section should be shown
            if params.get('country_id') is not None or params.get('archive_filter') is not None: # Check other collapsible filters
                show_collapsible = True

            if hasattr(self, 'more_filters_button') and hasattr(self, 'collapsible_filter_widget'):
                if self.collapsible_filter_widget.isVisible() != show_collapsible:
                    self.more_filters_button.setChecked(show_collapsible) # This will trigger toggle_more_filters_visibility

            # Unblock signals
            self.status_filter_combo.blockSignals(False)
            self.client_archive_filter_combo.blockSignals(False)
            self.country_filter_combo.blockSignals(False)
            self.search_input_field.blockSignals(False)
            if hasattr(self, 'date_filter_start'): self.date_filter_start.blockSignals(False)
            if hasattr(self, 'date_filter_end'): self.date_filter_end.blockSignals(False)
            if hasattr(self, 'more_filters_button'): self.more_filters_button.blockSignals(False)


            # Refresh client list with applied filters
            self.filter_client_list_display_slot()
            self.notify(self.tr("Filtre Appliqué"), self.tr("Le filtre sauvegardé '{0}' a été appliqué.").format(filter_data['filter_name']), type='INFO')

        except Exception as e:
            logging.error(f"Error applying saved filter ID {saved_filter_id}: {e}", exc_info=True)
            self.notify(self.tr("Erreur Application Filtre"), self.tr("Une erreur est survenue lors de l'application du filtre."), type='ERROR')
        finally:
            # Reset combo to placeholder to allow re-selection or show current state is "custom"
            # This also prevents the slot from re-triggering if a programmatic change happened during filter application
            self.load_filter_combo.blockSignals(True)
            self.load_filter_combo.setCurrentIndex(0)
            self.load_filter_combo.blockSignals(False)

    def save_current_filter_slot(self):
        """Saves the current state of all filters under a user-provided name."""
        if not self.current_user_id:
            self.notify(self.tr("Erreur Utilisateur"), self.tr("Aucun utilisateur connecté. Impossible de sauvegarder le filtre."), type='ERROR')
            return

        filter_name = self.saved_filter_name_input.text().strip()
        if not filter_name:
            self.notify(self.tr("Nom Requis"), self.tr("Veuillez entrer un nom pour ce filtre sauvegardé."), type='WARNING')
            self.saved_filter_name_input.setFocus()
            return

        # Check for duplicate filter name for this user (optional, DB unique constraint can also handle this)
        # existing_filters = user_saved_filters_crud.get_saved_filters_for_user(self.current_user_id)
        # if any(f['filter_name'] == filter_name for f in existing_filters):
        #     reply = QMessageBox.question(self, self.tr("Nom Dupliqué"),
        #                                  self.tr("Un filtre avec ce nom existe déjà. Voulez-vous le remplacer?"),
        #                                  QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        #     if reply == QMessageBox.No:
        #         return
            # If Yes, would need to find existing ID and call update_saved_filter or delete then add.
            # For simplicity now, we'll assume add_saved_filter handles duplicates or DB constraint does.

        parameters_dict = {}

        # Status Filter (now multi-select)
        if self.selected_status_ids_filter: # Save if list is not empty
            parameters_dict['status_ids'] = self.selected_status_ids_filter

        # Archive Filter
        archive_data = self.client_archive_filter_combo.currentData()
        # Save explicit value, even if it's the default (False for "Active Clients")
        parameters_dict['archive_filter'] = archive_data # Stores False, True, or "all_status_types"

        # Country Filter
        country_data = self.country_filter_combo.currentData()
        if country_data is not None: # Only save if not "All Countries"
            parameters_dict['country_id'] = country_data

        # Category Filter
        if hasattr(self, 'category_filter_input'):
            category_text = self.category_filter_input.text().strip()
            if category_text:
                parameters_dict['category'] = category_text

        # Search Term
        search_text = self.search_input_field.text().strip()
        if search_text:
            parameters_dict['search_term'] = search_text

        # Date Filters
        if hasattr(self, 'date_filter_start') and self.date_filter_start.date().isValid() and not self.date_filter_start.date().isNull():
            parameters_dict['created_at_start'] = self.date_filter_start.date().toString("yyyy-MM-dd")

        if hasattr(self, 'date_filter_end') and self.date_filter_end.date().isValid() and not self.date_filter_end.date().isNull():
            parameters_dict['created_at_end'] = self.date_filter_end.date().toString("yyyy-MM-dd")

        if not parameters_dict: # No actual filter criteria were set
            self.notify(self.tr("Aucun Filtre Actif"), self.tr("Aucun critère de filtre n'est actuellement défini pour la sauvegarde."), type='INFO')
            return

        try:
            new_filter_id = user_saved_filters_crud.add_saved_filter(
                user_id=self.current_user_id,
                filter_name=filter_name,
                filter_parameters=parameters_dict
            )
            if new_filter_id:
                self.notify(self.tr("Filtre Sauvegardé"), self.tr("Le filtre '{0}' a été sauvegardé avec succès.").format(filter_name), type='SUCCESS')
                self.saved_filter_name_input.clear()
                self.populate_saved_filters_combo() # Refresh the combo box
                # Optionally, select the newly saved filter in the combo
                new_idx = self.load_filter_combo.findData(new_filter_id)
                if new_idx != -1:
                    self.load_filter_combo.setCurrentIndex(new_idx)
            else:
                # This might happen if DB unique constraint on (user_id, filter_name) is active and name exists
                self.notify(self.tr("Échec Sauvegarde"), self.tr("Impossible de sauvegarder le filtre. Un filtre avec ce nom existe peut-être déjà, ou une erreur de base de données s'est produite."), type='ERROR')
        except Exception as e:
            logging.error(f"Error saving filter '{filter_name}': {e}", exc_info=True)
            self.notify(self.tr("Erreur Sauvegarde"), self.tr("Une erreur est survenue: {0}").format(str(e)), type='ERROR')

    def open_manage_filters_dialog_slot(self):
        """Opens the dialog to manage saved filters."""
        if not self.current_user_id:
            self.notify(self.tr("Erreur Utilisateur"), self.tr("Aucun utilisateur connecté. Impossible de gérer les filtres."), type='ERROR')
            return

        logging.info(f"Opening ManageSavedFiltersDialog for user {self.current_user_id}.")
        dialog = ManageSavedFiltersDialog(current_user_id=self.current_user_id, parent=self)

        # exec_() is blocking. We check result or flag after it closes.
        dialog.exec_()

        if dialog.changes_made: # Check the custom flag
            logging.info("Changes were made in ManageSavedFiltersDialog. Refreshing load_filter_combo.")
            self.populate_saved_filters_combo()
            # Also reset the combo to the placeholder, as the list of available filters might have changed
            self.load_filter_combo.setCurrentIndex(0)
        else:
            logging.info("No changes reported from ManageSavedFiltersDialog.")

    def open_role_management_dialog(self):
        """Opens the Role Management dialog if the user has permission."""
        from auth.permissions import has_permission, P_MANAGE_ROLES # Local import for clarity

        if not self.current_user_info:
            QMessageBox.warning(self, self.tr("Accès Refusé"), self.tr("Vous devez être connecté pour gérer les rôles."))
            return

        user_role_name = self.current_user_info.get('role_name')
        if not has_permission(user_role_name, P_MANAGE_ROLES):
            QMessageBox.warning(self, self.tr("Permissions Insuffisantes"),
                                self.tr("Vous n'avez pas la permission de gérer les rôles."))
            return

        dialog = RoleManagementDialog(current_user_info=self.current_user_info, parent=self)
        dialog.roles_changed_signal.connect(self._handle_roles_changed)
        # Check if RoleManagementDialog has a 'changes_made_flag' or similar to decide if refresh is needed
        # For now, assuming exec_() implies potential changes if it doesn't return QDialog.Rejected
        # A more explicit way is for RoleManagementDialog to set a flag if actual changes occurred.
        dialog.exec_()
        # The connection to _handle_roles_changed should cover refreshes if the dialog emits the signal.
        # If the dialog only emits on *actual* changes, this is fine.
        # If it emits always on close (even without changes), _handle_roles_changed might do unnecessary work.
        # Let's assume RoleManagementDialog's signal is specific to actual data changes.


    def _handle_roles_changed(self):
        """
        Slot to handle the roles_changed_signal from RoleManagementDialog.
        Refreshes UI components that depend on the list of roles.
        """
        logging.info("MainWindow: Roles have changed. Refreshing relevant UI components.")
        self.notify(self.tr("Rôles Modifiés"), self.tr("La liste des rôles ou leurs permissions ont été mises à jour."), type='INFO')

        # 1. Refresh UserManagementPage's role filter and user table
        if self.user_management_page_instance:
            # Check if _populate_role_filter method exists
            if hasattr(self.user_management_page_instance, '_populate_role_filter'):
                logging.debug("Refreshing role filter in UserManagementPage.")
                self.user_management_page_instance._populate_role_filter()
            else:
                logging.warning("UserManagementPage does not have _populate_role_filter method.")

            # If UserManagementPage is the current view, also refresh its user table
            # as role names might have changed for listed users.
            if self.main_area_stack.currentWidget() == self.user_management_page_instance:
                if hasattr(self.user_management_page_instance, 'load_users_to_table'):
                    logging.debug("UserManagementPage is current view, refreshing user table.")
                    self.user_management_page_instance.load_users_to_table()
                else:
                    logging.warning("UserManagementPage does not have load_users_to_table method.")

        # 2. Re-apply permissions for the main window
        # This is important if the current user's role's permissions were changed.
        logging.debug("Re-applying permissions for MainWindow due to role changes.")
        self._apply_permissions() # This will now also consider license features

        # If user's own license type changed (e.g. admin changed it), re-fetch allowed_features
        # This is a bit indirect. A more direct way would be if EditUserDialog could signal license change.
        # For now, re-evaluating on any role change is a safe bet if EditUserDialog could also modify license.
        # However, EditUserDialog currently does not seem to modify licenses directly.
        # This is more relevant if the license itself is modified for the current user.
        if self.current_user_info and self.current_user_info.get('user_id') == self.current_user_id: # Check if current user was affected
            # Re-fetch license info for the current user, as their license type might have been part of the "role" change
            # or an admin modified their license in a user management screen that triggered this.
            conn_lic_refresh = None
            try:
                from db.connection import get_db_connection # Local import
                conn_lic_refresh = get_db_connection()
                is_valid, _, lic_details = license_manager.check_license_validity(conn_lic_refresh, self.current_user_id)
                if is_valid and lic_details:
                    self.current_license_info = lic_details # Update stored license info
                    self.allowed_features = lic_details.get('allowed_features', set())
                    logging.info(f"Refreshed license info for current user. New allowed features: {self.allowed_features}")
                    self._apply_permissions() # Re-apply with potentially new feature set
                elif lic_details: # License exists but is not valid (e.g., expired)
                    self.current_license_info = lic_details
                    self.allowed_features = set() # No features if license became invalid
                    logging.warning(f"Current user's license is now invalid after role/permission changes. Allowed features set to empty.")
                    self._apply_permissions()
                else: # No license found
                    self.current_license_info = None
                    self.allowed_features = set()
                    logging.warning(f"No license found for current user after role/permission changes. Allowed features set to empty.")
                    self._apply_permissions()

            except Exception as e_lic_refresh:
                logging.error(f"Error refreshing license info for current user after role change: {e_lic_refresh}", exc_info=True)
            finally:
                if conn_lic_refresh:
                    conn_lic_refresh.close()

        # 3. If EditUserDialog instances could be open and non-modal, they'd need updating.
        # For now, assuming EditUserDialog is modal and will fetch fresh roles upon its next opening.
        # If UserMenuButton displays role name and it could change, refresh it:
        # self._update_user_display() # Already done if _apply_permissions changes user_menu_button state.

        # If any other part of MainWindow directly displays role names or uses a role combo,
        # it should be refreshed here as well.
        # Example: If a ClientWidget had a role dropdown (it doesn't currently), it would need refresh.

    def show_restaurant_module_view(self):
        """Shows the B2C Restaurant Management module."""
        # Optional: Check module state if it's made configurable
        # if not self.module_states.get('b2c_restaurant', True): # Example key
        #     QMessageBox.warning(self, self.tr("Module Désactivé"), self.tr("Le module Service Restaurant est désactivé."))
        #     return

        # Optional: Check license feature if applicable
        # RESTAURANT_FEATURE_KEY = "FEATURE_B2C_RESTAURANT" # Define this constant
        # if RESTAURANT_FEATURE_KEY not in self.allowed_features:
        #    QMessageBox.warning(self, self.tr("Licence Requise"), self.tr("Votre licence actuelle ne permet pas d'accéder à ce module."))
        #    return

        if self.restaurant_widget_instance is None:
            logging.info("DocumentManager: Lazily creating RestaurantMainWidget...")
            try:
                self.restaurant_widget_instance = RestaurantMainWidget(
                    parent=self,
                    current_user_info=self.current_user_info
                )
                self.main_area_stack.addWidget(self.restaurant_widget_instance)
                logging.info("DocumentManager: RestaurantMainWidget instance created and added to stack.")
            except Exception as e:
                logging.error(f"Failed to create RestaurantMainWidget: {e}", exc_info=True)
                QMessageBox.critical(self, self.tr("Erreur Module"),
                                     self.tr("Le module Service Restaurant n'a pas pu être chargé : {0}").format(str(e)))
                self.restaurant_widget_instance = None # Ensure it's None on failure
                return # Don't proceed to show if creation failed

        if self.restaurant_widget_instance: # Check again in case creation failed
            if hasattr(self.restaurant_widget_instance, 'refresh_all_data'):
                self.restaurant_widget_instance.refresh_all_data()
            self.main_area_stack.setCurrentWidget(self.restaurant_widget_instance)
            logging.info("Switched to B2C Restaurant Management view.")
        else:
            # This case should be covered by the try-except above, but as a safeguard:
            logging.error("RestaurantMainWidget instance is None after attempting creation. Cannot show view.")
            QMessageBox.critical(self, self.tr("Erreur Critique"),
                                 self.tr("La page du Service Restaurant n'a pas pu être chargée."))


    def _handle_sidebar_config_changed(self):
        """Handles changes from the sidebar customization dialog."""
        logging.info("Configuration de la barre latérale utilisateur modifiée. Reconstruction de la barre latérale...")
        self._populate_sidebar() # Re-populate sidebar with new configuration
        self.notify(self.tr("Barre Latérale Mise à Jour"), self.tr("La barre latérale a été mise à jour selon vos préférences."), type='INFO')


    def _handle_menu_config_changed(self): # Kept for now, might be removed if menu is fully replaced
        logging.info("Configuration du menu utilisateur modifiée. Reconstruction des menus...")

        # Store the corner widget (search bar and user button) to restore it later
        corner_widget = self.menuBar().cornerWidget(Qt.TopRightCorner)
        # Temporarily remove it from the menu bar to prevent it from being deleted by clear()
        if corner_widget:
            self.menuBar().setCornerWidget(None)
            corner_widget.setParent(None) # Ensure it's not deleted with the old menubar

        self.menuBar().clear() # This clears all menus and actions within them.
        self.create_menus_main() # This will use the new configuration from the database.
        self._apply_permissions() # Re-apply permissions to the new menu structure.

        if corner_widget:
            self.menuBar().setCornerWidget(corner_widget, Qt.TopRightCorner)


            self.notify(self.tr("Menu Mis à Jour"), self.tr("Le menu principal a été mis à jour selon vos préférences."), type='INFO')

    # --- Sidebar Population and State Management --- (ALL REMOVED)
    # --- End Slots for Sidebar Interaction --- (ALL REMOVED)
            return

        available_modules_for_customization = []
        for module_info_const in CONFIGURABLE_MODULES:
            module_name = module_info_const['name']

            if not self.module_states.get(module_name, True):
                continue

            # The local _MODULE_TO_LICENSE_FEATURE_MAP is removed.
            # We now use the 'license_feature' directly from module_info_const (from CONFIGURABLE_MODULES).
            license_feature_key = module_info_const.get('license_feature')
            if license_feature_key and license_feature_key not in self.allowed_features:
                continue # Skip if license feature is required for this module and not granted to the user


            available_modules_for_customization.append(module_info_const)

        if not available_modules_for_customization:
            QMessageBox.information(self, self.tr("Aucun Module Configurable"),
                                    self.tr("Il n'y a actuellement aucun module que vous êtes autorisé à configurer."))
            return

        dialog = MenuCustomizationDialog( # TODO: This dialog might need to become SidebarCustomizationDialog
            current_user_id=self.current_user_id,
            configurable_modules=available_modules_for_customization,
            module_states=self.module_states,
            license_features=self.allowed_features,
            parent=self
        )

        # Pass the actual database access functions to the dialog
        # db_manager should be available as an import in main_window.py (e.g., import db as db_manager)
        if not db_manager: # Ensure db_manager is imported and available
             logging.error("db_manager not available in DocumentManager. Cannot open MenuCustomizationDialog.")
             QMessageBox.critical(self, self.tr("Erreur Critique"), self.tr("Le gestionnaire de base de données n'est pas disponible."))
             return

        # TODO: Adapt these keys if MenuCustomizationDialog is changed for sidebar config
        dialog.get_user_menu_config_func = lambda user_id: db_manager.get_setting(f"user_sidebar_config_{user_id}") # Changed key
        dialog.set_user_menu_config_func = lambda user_id, data: db_manager.set_setting(f"user_sidebar_config_{user_id}", json.dumps(data)) # Changed key

        dialog.menu_config_changed.connect(self._handle_sidebar_config_changed) # Connect to new handler
        if dialog.exec_() == QDialog.Accepted:
            pass

    def _handle_sidebar_config_changed(self):
        """Handles changes from the sidebar customization dialog."""
        logging.info("Configuration de la barre latérale utilisateur modifiée. Reconstruction de la barre latérale...")
        self._populate_sidebar() # Re-populate sidebar with new configuration
        self.notify(self.tr("Barre Latérale Mise à Jour"), self.tr("La barre latérale a été mise à jour selon vos préférences."), type='INFO')


    def _handle_menu_config_changed(self): # Kept for now, might be removed if menu is fully replaced
        logging.info("Configuration du menu utilisateur modifiée. Reconstruction des menus...")

        # Store the corner widget (search bar and user button) to restore it later
        corner_widget = self.menuBar().cornerWidget(Qt.TopRightCorner)
        # Temporarily remove it from the menu bar to prevent it from being deleted by clear()
        if corner_widget:
            self.menuBar().setCornerWidget(None)
            corner_widget.setParent(None) # Ensure it's not deleted with the old menubar

        self.menuBar().clear() # This clears all menus and actions within them.
        self.create_menus_main() # This will use the new configuration from the database.
        self._apply_permissions() # Re-apply permissions to the new menu structure.

        if corner_widget:
            self.menuBar().setCornerWidget(corner_widget, Qt.TopRightCorner)

        self.notify(self.tr("Menu Mis à Jour"), self.tr("Le menu principal a été mis à jour selon vos préférences."), type='INFO')

    # --- Sidebar Population and State Management --- (ALL REMOVED)
    # --- End Slots for Sidebar Interaction --- (ALL REMOVED)
    def on_search_text_changed(self, text):
        self.search_timer.start(300) # Debounce search queries

    def _update_search_completer(self):
        text = self.search_bar_line_edit.text()
        if len(text) < 2:
            self.search_completer.update_model({})
            return

        categories = {}

        # Actions
        action_results = [f"Action: {name}" for name in self.searchable_actions_map.keys() if text.lower() in name.lower()]
        if action_results:
            categories["Actions"] = action_results

        # Clients
        client_results = [f"Client: {client['client_name']}" for client in clients_crud_instance.search_clients_by_name(text)]
        if client_results:
            categories["Clients"] = client_results

        # Products
        product_results = [f"Product: {product['product_name']}" for product in products_crud_instance.search_products_by_name(text)]
        if product_results:
            categories["Products"] = product_results

        # Projects
        # project_results = [f"Project: {project['project_name']}" for project in projects_crud.search_projects_by_name(text)]
        # if project_results:
        #     categories["Projects"] = project_results

        self.search_completer.update_model(categories)

    def on_search_item_activated(self, activated_text):
        if activated_text.startswith("---"):
            return

        parts = activated_text.split(": ", 1)
        if len(parts) != 2:
            return

        item_type, item_name = parts
        if item_type == "Action":
            action = self.searchable_actions_map.get(item_name)
            if action:
                action.trigger()
        elif item_type == "Client":
            clients = clients_crud_instance.search_clients_by_name(item_name)
            if clients:
                self.open_client_tab_by_id(clients[0]['client_id'])
        elif item_type == "Product":
            # This would require a way to show a product's details, e.g., a product dialog
            pass
        # elif item_type == "Project":
            # This would require a way to show a project's details
            # pass
