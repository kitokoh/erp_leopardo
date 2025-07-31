# -*- coding: utf-8 -*-
import logging
import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from PyQt5.QtCore import pyqtSlot, QObject, pyqtSignal, QTimer
from PyQt5.QtWebChannel import QWebChannel

from app_setup import APP_ROOT_DIR
from .map_utils import generate_folium_map_html
# For fetching data for the map - consider if this widget should do it, or receive data
from db import get_client_counts_by_country # Example, might need more data

# A simplified MapInteractionHandler for the home page map, if needed.
# Or, the home page map might be non-interactive beyond Folium's defaults.
class HomePageMapInteractionHandler(QObject):
    # Define signals if the home page map needs to communicate back to Python
    # For example: home_country_clicked = pyqtSignal(str)
    map_view_changed_signal = pyqtSignal(float, float, int)
    country_clicked_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    @pyqtSlot(str)
    def countryClicked(self, country_name):
        self.country_clicked_signal.emit(country_name)

    @pyqtSlot(float, float, int)
    def onMapViewChanged(self, lat, lng, zoom):
        self.map_view_changed_signal.emit(lat, lng, zoom)


class HomePageMapWidget(QWidget):
    def __init__(self, app_translator_func=lambda x: x, parent=None):
        super().__init__(parent)
        self.setObjectName("HomePageMapWidget")
        self.app_translator_func = app_translator_func # Store translator

        self._init_ui()
        # Load map data shortly after UI is set up, using a QTimer for non-blocking init
        QTimer.singleShot(0, self.refresh_map)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0) # No margins for the map widget itself

        self.map_view = QWebEngineView()
        self.map_view.settings().setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        self.map_view.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        layout.addWidget(self.map_view)
        self.setLayout(layout)

        # Setup for QWebChannel if this map needs JS-Python interaction
        # For a simple display map, this might not be strictly necessary unless popups have callbacks.
        # The generate_folium_map_html util expects a pyMapConnector name.
        self.interaction_handler = HomePageMapInteractionHandler(self)
        self.web_channel = QWebChannel(self.map_view.page())
        self.map_view.page().setWebChannel(self.web_channel)
        # Use a distinct name if both maps could be active and have channels.
        self.web_channel.registerObject("pyHomePageMapConnector", self.interaction_handler)
        self.interaction_handler.map_view_changed_signal.connect(self._on_map_view_changed)

    def _on_map_view_changed(self, lat, lng, zoom):
        from db import get_setting, set_setting, get_db_connection
        db_session = get_db_connection()
        try:
            set_setting('map_last_lat', str(lat), db_session)
            set_setting('map_last_lng', str(lng), db_session)
            set_setting('map_last_zoom', str(zoom), db_session)
        finally:
            db_session.close()

    def refresh_map(self):
        logging.info("HomePageMapWidget: Refreshing map...")
        try:
            # 1. Fetch data (simplified for home page map)
            # This widget will fetch its own data.
            # For consistency, it should use the same DB functions as StatisticsDashboard.
            clients_by_country = get_client_counts_by_country()

            # For popups, HomePageMapWidget might show simpler info or need fewer details.
            # For now, we'll pass None for all_clients_details_for_popups, meaning popups will be basic.
            # A more advanced version could fetch more details if required for home page popups.
            all_clients_details = None

            geojson_path = os.path.join(APP_ROOT_DIR, "resources", "assets", "world_countries.geojson")

            # 2. Generate Map HTML using the utility function
            from db import get_setting

            scope = get_setting('geographic_scope', 'international')
            last_lat = float(get_setting('map_last_lat', '20'))
            last_lng = float(get_setting('map_last_lng', '0'))
            last_zoom = int(get_setting('map_last_zoom', '2'))


            map_html = generate_folium_map_html(
                geojson_path=geojson_path,
                clients_by_country_counts=clients_by_country,
                all_clients_details_for_popups=all_clients_details, # Passing None for simpler popups
                app_translator_func=self.app_translator_func,
                map_interaction_handler_name="pyHomePageMapConnector", # Use the specific handler name
                initial_location=[last_lat, last_lng],
                initial_zoom=last_zoom,
                scope=scope
            )

            if map_html:
                self.map_view.setHtml(map_html)
                logging.info(f"HomePageMapWidget: Map HTML content set. Length: {len(map_html)}")
            else:
                self._display_error_html("Erreur de génération de la carte pour la page d'accueil.")
                logging.error("HomePageMapWidget: Failed to generate map HTML.")

        except Exception as e:
            logging.error(f"HomePageMapWidget: Error during map refresh: {e}", exc_info=True)
            self._display_error_html(f"Erreur inattendue: {e}")

    def _display_error_html(self, message: str):
        # Simplified error display for the home page map
        error_html = f"""
        <html><body style='display:flex; justify-content:center; align-items:center; height:100%; font-family:Arial,sans-serif;'>
        <div style='text-align:center; padding:20px; border:1px solid #cc0000; background-color:#ffeeee; color:#cc0000;'>
        <h4>{self.app_translator_func("Erreur Carte")}</h4><p>{message}</p>
        </div></body></html>
        """
        self.map_view.setHtml(error_html)
        logging.info(f"HomePageMapWidget: Displayed error HTML: {message}")

    # If HomePageMapWidget needs to handle signals from its MapInteractionHandler:
    # @pyqtSlot(str)
    # def _on_home_map_country_clicked(self, country_name):
    #     logging.info(f"HomePageMapWidget: Country clicked: {country_name}")
    #     # Potentially emit another signal or call a method on main_window
