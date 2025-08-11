# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QTextBrowser, QApplication, QSizePolicy
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import Qt, QSize, pyqtSlot, QObject
import sys
import os

try:
    from app.db.cruds.misc import transporters_crud
    from app.statistics.map_utils import generate_folium_map_html
    from app.statistics.dashboard import MapInteractionHandler # Re-using this handler
except ImportError as e:
    print(f"Error importing modules in carrier_map_dialog.py: {e}")
    # Fallback for direct execution
    from app.db.cruds.misc import transporters_crud
    # In a real scenario, you'd want to ensure these paths are resolvable
    # For this fix, we assume the project structure allows these imports.
    generate_folium_map_html = None
    MapInteractionHandler = QObject # Basic fallback

class CarrierMapDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Carrier Map and Information"))
        self.setMinimumSize(1024, 768) # Increased size for better map view
        self.transporters = []
        self.map_interaction_handler = None
        self.web_channel = None
        self.setup_ui()
        self.load_carrier_data()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)

        # --- Left Pane (Carrier List & Details) ---
        left_pane_widget = QWidget()
        left_pane_layout = QVBoxLayout(left_pane_widget)
        left_pane_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        self.carrier_list_widget = QListWidget()
        self.carrier_list_widget.setObjectName("carrierListWidget")
        self.carrier_list_widget.currentItemChanged.connect(self.display_carrier_details)
        left_pane_layout.addWidget(self.carrier_list_widget)

        details_label = QLabel(self.tr("Carrier Details:"))
        left_pane_layout.addWidget(details_label)

        self.carrier_details_browser = QTextBrowser()
        self.carrier_details_browser.setObjectName("carrierDetailsBrowser")
        self.carrier_details_browser.setMinimumHeight(200)
        left_pane_layout.addWidget(self.carrier_details_browser)


        # --- Right Pane (Map View) ---
        right_pane_widget = QWidget()
        right_pane_layout = QVBoxLayout(right_pane_widget)
        right_pane_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.map_view = QWebEngineView()
        self.map_view.setObjectName("carrierMapView")
        self.map_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_pane_layout.addWidget(self.map_view)

        # Setup WebChannel for JS-Python communication
        if MapInteractionHandler is not QObject: # Check if import was successful
            self.map_interaction_handler = MapInteractionHandler(self)
            # Connect signals if needed, e.g., for clicking on a carrier on the map
            # self.map_interaction_handler.carrier_clicked_signal.connect(self.on_map_carrier_clicked)
            self.web_channel = QWebChannel(self.map_view.page())
            self.map_view.page().setWebChannel(self.web_channel)
            self.web_channel.registerObject("pyMapConnector", self.map_interaction_handler)


        main_layout.addWidget(left_pane_widget, 1)
        main_layout.addWidget(right_pane_widget, 3) # Give map more space


        # --- Bottom Pane for Close Button ---
        # To ensure the button is below everything and centered, we'll wrap main_layout in another QVBoxLayout
        outer_layout = QVBoxLayout() # Do not pass self
        outer_layout.addLayout(main_layout)

        self.close_button = QPushButton(self.tr("Close"))
        self.close_button.setObjectName("closeButton")
        self.close_button.clicked.connect(self.accept)

        button_layout = QHBoxLayout() # To center the button
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        button_layout.addStretch()
        outer_layout.addLayout(button_layout)

        self.setLayout(outer_layout) # Set the outermost layout for the dialog


    def load_carrier_data(self):
        self.carrier_list_widget.clear()
        try:
            self.transporters = transporters_crud.get_all_transporters()
            if not self.transporters:
                item = QListWidgetItem(self.tr("No carriers found."))
                item.setData(Qt.UserRole, None) # No data
                self.carrier_list_widget.addItem(item)
                return

            for transporter in self.transporters:
                item_text = transporter.get('name', self.tr('Unnamed Carrier'))
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, transporter)  # Store the whole dict
                self.carrier_list_widget.addItem(item)

            if self.carrier_list_widget.count() > 0:
                self.carrier_list_widget.setCurrentRow(0) # Select the first item

            self.refresh_map() # Initial map load

        except Exception as e:
            print(f"Error loading carrier data: {e}")
            item = QListWidgetItem(self.tr("Error loading carriers."))
            item.setData(Qt.UserRole, None)
            self.carrier_list_widget.addItem(item)
            self.carrier_details_browser.setHtml(f"<p style='color:red;'>{self.tr('Could not load carrier data:')}<br>{e}</p>")


    def display_carrier_details(self, current_item, previous_item):
        # previous_item is unused but part of the signal
        if not current_item:
            self.carrier_details_browser.clear()
            return

        transporter_data = current_item.data(Qt.UserRole)
        if not transporter_data:
            self.carrier_details_browser.setHtml(f"<p>{self.tr('No details available for this item.')}</p>")
            return

        details_html = f"""
            <h3>{self.tr('Carrier Details')}</h3>
            <p><b>{self.tr('Name:')}</b> {transporter_data.get('name', 'N/A')}</p>
            <p><b>{self.tr('Contact Person:')}</b> {transporter_data.get('contact_person', 'N/A')}</p>
            <p><b>{self.tr('Phone:')}</b> {transporter_data.get('phone', 'N/A')}</p>
            <p><b>{self.tr('Email:')}</b> {transporter_data.get('email', 'N/A')}</p>
            <p><b>{self.tr('Address:')}</b> {transporter_data.get('address', 'N/A')}</p>
            <p><b>{self.tr('Service Area:')}</b> {transporter_data.get('service_area', 'N/A')}</p>
            <hr>
            <p><b>{self.tr('Latitude:')}</b> {transporter_data.get('latitude', 'N/A')}</p>
            <p><b>{self.tr('Longitude:')}</b> {transporter_data.get('longitude', 'N/A')}</p>
            <p><b>{self.tr('Current Cargo:')}</b> {transporter_data.get('current_cargo') if transporter_data.get('current_cargo') else 'N/A'}</p>
        """
        self.carrier_details_browser.setHtml(details_html)
        self.refresh_map(focused_transporter=transporter_data)

    def _generate_carrier_map_html(self, focused_transporter=None):
        import folium

        # Default view if no carriers or focus
        initial_location = [46.2276, 2.2137] # France
        initial_zoom = 5

        if focused_transporter and focused_transporter.get('latitude') and focused_transporter.get('longitude'):
            initial_location = [focused_transporter['latitude'], focused_transporter['longitude']]
            initial_zoom = 13
        elif self.transporters:
            # Center on the average location of all transporters if no focus
            lats = [t['latitude'] for t in self.transporters if t.get('latitude')]
            lons = [t['longitude'] for t in self.transporters if t.get('longitude')]
            if lats and lons:
                initial_location = [sum(lats) / len(lats), sum(lons) / len(lons)]
                initial_zoom = 6

        m = folium.Map(location=initial_location, zoom_start=initial_zoom, tiles="CartoDB positron")

        # Add all transporters as markers
        for t in self.transporters:
            if t.get('latitude') and t.get('longitude'):
                is_focused = focused_transporter and t.get('id') == focused_transporter.get('id')
                folium.Marker(
                    location=[t['latitude'], t['longitude']],
                    popup=f"<b>{t.get('name', 'N/A')}</b><br>Contact: {t.get('contact_person', 'N/A')}",
                    tooltip=t.get('name', 'N/A'),
                    icon=folium.Icon(color='red', icon='info-sign') if is_focused else folium.Icon(color='blue')
                ).add_to(m)

        # The web channel script is not added here as it's complex and might not be needed
        # for a simple display map. For interaction (clicking markers to select in list),
        # it would be required. This implementation focuses on display first.
        return m._repr_html_()

    def refresh_map(self, focused_transporter=None):
        if hasattr(self, 'map_view'):
            map_html = self._generate_carrier_map_html(focused_transporter)
            self.map_view.setHtml(map_html)

    # Optional: Override sizeHint for better default sizing if needed
    # def sizeHint(self):
    #     return QSize(800, 600)

if __name__ == '__main__':
    # Ensure the path includes the project root for db imports if run directly
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root_from_main = os.path.dirname(current_dir) # Go up one level from 'dialogs'
    if project_root_from_main not in sys.path:
        sys.path.insert(0, project_root_from_main)

    # Need to re-import if path was adjusted, for the __main__ block's context
    # This is a bit tricky for scripts run directly vs imported.
    # The try-except block for transporters_crud import at the top should handle most cases.

    app = QApplication(sys.argv)

    # Initialize DB (example, replace with your actual DB init logic if needed for testing)
    # This is crucial if get_all_transporters() relies on an initialized DB
    try:
        from db.init_schema import initialize_database
        # Determine DB path relative to project root
        db_path = os.path.join(project_root_from_main, "app_data.db") # Example path

        # A simple way to ensure config.py is findable and sets DATABASE_PATH
        # This is a workaround for direct script execution; normally config is imported from root
        class MockConfig:
            DATABASE_PATH = db_path
            DEFAULT_ADMIN_USERNAME = "admin_test" # Dummy value
            DEFAULT_ADMIN_PASSWORD = "password_test" # Dummy value

        import config as app_config # Try to import actual config
        app_config.DATABASE_PATH = db_path # Override if needed for testing

        if not os.path.exists(db_path):
            print(f"Database not found at {db_path}, initializing for test...")
            # Temporarily patch config if it's used by init_schema directly
            sys.modules['config'] = MockConfig
            initialize_database()
            # Restore original config module if it was loaded
            if 'app_config' in locals():
                 sys.modules['config'] = app_config
            print("Test database initialized.")
        else:
            print(f"Using existing database at {db_path} for test.")

    except ImportError as e:
        print(f"Could not import or initialize database for test: {e}")
    except Exception as e_db_init:
        print(f"Error during test database initialization: {e_db_init}")


    dialog = CarrierMapDialog()
    dialog.show()
    sys.exit(app.exec_())
