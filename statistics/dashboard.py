# -*- coding: utf-8 -*-
import os
import logging
import sip # For checking if C++ object is deleted
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QSplitter, QHBoxLayout,
    QGroupBox, QFormLayout, QTableWidget, QHeaderView, QTabWidget, QProgressBar,
    QTableWidgetItem, QStackedWidget
)
from PyQt5.QtCore import Qt, QObject, pyqtSignal, pyqtSlot, QTimer # Added QTimer
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtGui import QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView

# Matplotlib imports
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


from datetime import datetime # Added for client acquisition stats
from dateutil.relativedelta import relativedelta # Added for client acquisition stats
import json # Added for robust JS string escaping
import folium
# import pandas as pd # pandas might not be directly needed in dashboard.py if map_utils handles its own data structures
from branca.colormap import StepColormap # Import StepColormap

from .map_utils import generate_folium_map_html # Import the new utility

from db import (
    get_total_clients_count,
    get_active_clients_count,
    get_country_by_name, # Added
    get_total_projects_count,
    get_active_projects_count,
    get_total_products_count,
    get_client_segmentation_by_city,
    get_client_segmentation_by_status,
    get_client_segmentation_by_category,
    get_client_counts_by_country,
    get_country_by_id,
    get_city_by_id,
    get_status_setting_by_id
)
# It seems db_manager is not directly imported, but functions are. If needed, import db as db_manager
from db.cruds.clients_crud import clients_crud_instance
# from db.cruds.proforma_invoices_crud import list_proforma_invoices # No longer directly used by dashboard
from db.connection import get_db_connection # Used by some stats methods
# It seems db_manager is not directly imported, but functions are. If needed, import db as db_manager
# from db.cruds.clients_crud import clients_crud_instance # Duplicate
from db.cruds.client_project_products_crud import get_product_usage_counts # Added for product popularity
from db.cruds.proforma_invoices_crud import get_total_sales_amount_for_period, get_total_proforma_sales_for_country_id # Added for sales trend and country stats
from db.cruds.projects_crud import get_active_project_count_by_country_id # Added for country stats


from app_setup import APP_ROOT_DIR


class MapInteractionHandler(QObject): # Remains as it's used for the new interactive map
    country_clicked_signal = pyqtSignal(str)
    client_clicked_on_map_signal = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)

    @pyqtSlot(str)
    def countryClicked(self, country_name):
        logging.info(f"MapInteractionHandler: countryClicked received: {country_name}")
        self.country_clicked_signal.emit(country_name)

    @pyqtSlot(str, str)
    def clientClickedOnMap(self, client_id, client_name):
        logging.info(f"MapInteractionHandler: clientClickedOnMap received ID: {client_id}, Name: {client_name}")
        self.client_clicked_on_map_signal.emit(client_id, client_name)

class StatisticsDashboard(QWidget):
    request_add_client_for_country = pyqtSignal(str)
    request_view_client_details = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Tableau de Bord Statistiques Interactif"))

        main_layout = QVBoxLayout(self)

        # Global Refresh Button
        self.global_refresh_button = QPushButton(self.tr("Rafraîchir Tout le Tableau de Bord"))
        self.global_refresh_button.setIcon(QIcon.fromTheme("view-refresh", QIcon(":/icons/refresh-cw.svg")))
        self.global_refresh_button.clicked.connect(self.refresh_all_dashboard_content)
        main_layout.addWidget(self.global_refresh_button)

        # Main horizontal splitter
        main_splitter = QSplitter(Qt.Horizontal, self)

        # Left widget for Map
        self.left_widget_for_map = QWidget()
        # Create layout, set it as the layout for self.left_widget_for_map, AND store it
        self._left_map_actual_layout = QVBoxLayout() # Create layout without parent first
        self._left_map_actual_layout.setContentsMargins(0,0,0,0)
        self.left_widget_for_map.setLayout(self._left_map_actual_layout) # Explicitly set the layout


        self.map_view = None # Initialize as None
        main_splitter.addWidget(self.left_widget_for_map)

        # Right widget for Stats
        self.right_widget_for_stats = QWidget()
        right_stats_layout = QVBoxLayout(self.right_widget_for_stats)
        right_stats_layout.setContentsMargins(5,5,5,5)
        self.right_widget_for_stats.setLayout(right_stats_layout)
        main_splitter.addWidget(self.right_widget_for_stats)

        main_splitter.setSizes([int(self.width() * 0.6), int(self.width() * 0.4)]) # Initial sizing
        main_layout.addWidget(main_splitter)
        self.setLayout(main_layout)

        self.map_interaction_handler = None # Initialize as None

        self._setup_stats_display_ui(right_stats_layout)

        # Defer map component initialization and initial data load that depends on map
        QTimer.singleShot(0, self._initialize_map_and_load_data)

        logging.info("StatisticsDashboard initialized. Map components will be loaded via QTimer.")

    def _initialize_map_and_load_data(self):
        """Deferred initialization of map components and initial data load."""
        logging.info("StatisticsDashboard: _initialize_map_and_load_data called by QTimer.")

        # Ensure the container widget for the map exists and has its layout.
        # self._left_map_actual_layout is initialized in __init__ and set as the layout
        # for self.left_widget_for_map. We rely on that setup.
        if self.left_widget_for_map is None:
            logging.critical("StatisticsDashboard: self.left_widget_for_map is None. Cannot initialize map.")
            return

        # Verify that _left_map_actual_layout (which should be the layout of left_widget_for_map) is valid.
        # This also implicitly checks if left_widget_for_map.layout() is valid if _left_map_actual_layout
        # indeed points to it as intended by __init__.
        if self._left_map_actual_layout is None:
            logging.critical("StatisticsDashboard: self._left_map_actual_layout is None. This should have been set in __init__. Cannot proceed with map initialization.")
            return

        # As an additional check, ensure the widget's current layout is indeed the one we stored.
        # This can catch unexpected external modifications to the widget's layout.
        if self.left_widget_for_map.layout() is None:
            logging.critical("StatisticsDashboard: self.left_widget_for_map.layout() is None, but _left_map_actual_layout was expected to be set. Critical state inconsistency.")
            return
        elif self.left_widget_for_map.layout() is not self._left_map_actual_layout:
            logging.warning("StatisticsDashboard: self.left_widget_for_map.layout() differs from self._left_map_actual_layout. Using the widget's current layout.")
            self._left_map_actual_layout = self.left_widget_for_map.layout()


        # Now, self._left_map_actual_layout is confirmed to be the layout of self.left_widget_for_map
        if self.map_view is None:
            # Parent QWebEngineView to self.left_widget_for_map.
            # It will be managed by self._left_map_actual_layout.
            self.map_view = QWebEngineView(self.left_widget_for_map) # Parented to the widget
            self._left_map_actual_layout.addWidget(self.map_view) # Added to the layout
            logging.info("StatisticsDashboard: QWebEngineView (self.map_view) created and added to _left_map_actual_layout.")

            self.map_interaction_handler = MapInteractionHandler(self)
            self.map_interaction_handler.country_clicked_signal.connect(self._on_map_country_clicked)
            self.map_interaction_handler.client_clicked_on_map_signal.connect(self._display_client_details_in_panel)

            web_channel = QWebChannel(self.map_view.page())
            self.map_view.page().setWebChannel(web_channel)
            web_channel.registerObject("pyMapConnector", self.map_interaction_handler)
            logging.info("StatisticsDashboard: MapInteractionHandler and QWebChannel set up.")

        self.refresh_all_dashboard_content()
        # Removed diagnostic logging from the end of this method


    @pyqtSlot(str)
    def _on_map_country_clicked(self, country_name):
        logging.info(f"Map country clicked: {country_name}. Switching to country stats view.")
        self._show_country_stats_view(country_name)
        # The request_add_client_for_country signal is now emitted by CountryStatsDisplayWidget

    # This slot is now replaced by _display_client_details_in_panel if request_view_client_details signal is removed.
    # For now, keep it if the signal is still defined, but it won't be connected to map_interaction_handler.
    # If request_view_client_details is to be removed, this slot should also be removed or repurposed.
    # Based on instructions, the signal's connection is changed, not the signal itself removed yet.
    @pyqtSlot(str)
    def _on_map_client_clicked(self, client_id, client_name):
        # This method is kept for now in case request_view_client_details is used elsewhere,
        # but the map click will now go to _display_client_details_in_panel.
        logging.info(f"Legacy _on_map_client_clicked for {client_name} (ID: {client_id}). Emitting request_view_client_details if this signal is still used.")
        self.request_view_client_details.emit(client_id) # This signal might be deprecated for this class's map.

    def refresh_all_dashboard_content(self):
        logging.info("Refreshing all dashboard content...")
        self.refresh_statistics_data() # This updates non-map stats
        if self.map_view: # Only update map if it has been initialized
            self.update_map()
        else:
            logging.info("StatisticsDashboard: Map view not yet initialized, skipping map update in refresh_all_dashboard_content.")
        logging.info("All dashboard content refresh process initiated.")

    # Placeholder for _setup_stats_display_ui - to be filled in Phase 2
    def _setup_stats_display_ui(self, layout_to_populate):
        self.stats_stack = QStackedWidget()
        layout_to_populate.addWidget(self.stats_stack)

        # --- Global Stats Widget ---
        self.global_stats_widget = QWidget()
        global_stats_page_layout = QVBoxLayout(self.global_stats_widget)
        # global_stats_page_layout.setContentsMargins(0,0,0,0) # Keep consistent margins or remove if parent handles

        title_label = QLabel(self.tr("Statistiques Détaillées"))
        title_label.setObjectName("statisticsTitleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        global_stats_page_layout.addWidget(title_label)

        global_stats_group = QGroupBox(self.tr("Statistiques Globales"))
        global_stats_layout = QFormLayout(global_stats_group)
        self.stats_labels = {
            "total_clients": QLabel("0"), "active_clients": QLabel("0"),
            "total_projects": QLabel("0"), "active_projects": QLabel("0"),
            "total_products": QLabel("0"),
            "total_sales_proforma": QLabel("0"), # Added for proforma sales
            "new_clients_last_month": QLabel("0"), # Added for client acquisition
            "new_clients_last_quarter": QLabel("0"), # Added for client acquisition
            "total_clients_trend": QLabel("") # Added for client trend
        }

        total_clients_layout = QHBoxLayout()
        total_clients_layout.addWidget(self.stats_labels["total_clients"])
        total_clients_layout.addSpacing(10)
        self.stats_labels["total_clients_trend"].setObjectName("trendLabel")
        total_clients_layout.addWidget(self.stats_labels["total_clients_trend"])
        total_clients_layout.addStretch()
        global_stats_layout.addRow(self.tr("Nombre total de clients:"), total_clients_layout)

        active_clients_layout = QHBoxLayout()
        active_clients_layout.addWidget(self.stats_labels["active_clients"])
        active_clients_layout.addSpacing(10)
        self.stats_labels["active_clients_trend"] = QLabel("")
        self.stats_labels["active_clients_trend"].setObjectName("trendLabel")
        active_clients_layout.addWidget(self.stats_labels["active_clients_trend"])
        active_clients_layout.addStretch()
        global_stats_layout.addRow(self.tr("Nombre de clients actifs:"), active_clients_layout)

        global_stats_layout.addRow(self.tr("Nombre total de projets:"), self.stats_labels["total_projects"])
        global_stats_layout.addRow(self.tr("Nombre de projets actifs:"), self.stats_labels["active_projects"])
        global_stats_layout.addRow(self.tr("Nombre total de produits (BDD):"), self.stats_labels["total_products"])


        total_sales_proforma_layout = QHBoxLayout()
        total_sales_proforma_layout.addWidget(self.stats_labels["total_sales_proforma"])
        total_sales_proforma_layout.addSpacing(10)
        self.stats_labels["total_sales_proforma_trend"] = QLabel("")
        self.stats_labels["total_sales_proforma_trend"].setObjectName("trendLabel")
        total_sales_proforma_layout.addWidget(self.stats_labels["total_sales_proforma_trend"])
        total_sales_proforma_layout.addStretch()
        global_stats_layout.addRow(self.tr("Total Ventes (Proforma):"), total_sales_proforma_layout)

        global_stats_layout.addRow(self.tr("Nouveaux Clients (Mois Dernier):"), self.stats_labels["new_clients_last_month"])
        global_stats_layout.addRow(self.tr("Nouveaux Clients (Trimestre Dernier):"), self.stats_labels["new_clients_last_quarter"])
        global_stats_page_layout.addWidget(global_stats_group)

        health_score_group = QGroupBox(self.tr("Indice de Santé Commerciale"))
        health_score_layout = QVBoxLayout(health_score_group)
        self.health_score_value_label = QLabel("0 %")
        self.health_score_value_label.setAlignment(Qt.AlignCenter)
        self.health_score_value_label.setObjectName("healthScoreValueLabel")
        self.health_score_progress_bar = QProgressBar()
        self.health_score_progress_bar.setRange(0, 100); self.health_score_progress_bar.setValue(0)
        self.health_score_progress_bar.setTextVisible(False)
        health_score_layout.addWidget(self.health_score_value_label)
        health_score_layout.addWidget(self.health_score_progress_bar)
        global_stats_page_layout.addWidget(health_score_group)

        self.segmentation_tabs = QTabWidget()
        self._setup_segmentation_tab_ui_internal()
        global_stats_page_layout.addWidget(self.segmentation_tabs)
        self.global_stats_widget.setLayout(global_stats_page_layout)
        self.stats_stack.addWidget(self.global_stats_widget)

        # --- Client Details Widget ---
        self.client_details_widget = QWidget()
        client_details_page_layout = QVBoxLayout(self.client_details_widget)

        # Title for Client Details
        client_details_title = QLabel(self.tr("Détails du Client")) # Create a title
        client_details_title.setObjectName("clientDetailsTitleLabel") # Apply styling if needed
        client_details_title.setAlignment(Qt.AlignCenter)
        client_details_page_layout.addWidget(client_details_title)

        self.client_details_layout = QFormLayout() # For displaying client info
        # self.client_details_layout.setContentsMargins(5,5,5,5)
        client_details_page_layout.addLayout(self.client_details_layout)

        client_details_page_layout.addStretch(1) # Pushes button to bottom

        self.back_to_global_stats_button = QPushButton(self.tr("Retour aux Statistiques Globales"))
        self.back_to_global_stats_button.setIcon(QIcon.fromTheme("go-previous", QIcon(":/icons/arrow-left-circle.svg")))
        self.back_to_global_stats_button.clicked.connect(self._show_global_stats_view)
        client_details_page_layout.addWidget(self.back_to_global_stats_button)

        self.client_details_widget.setLayout(client_details_page_layout)
        self.stats_stack.addWidget(self.client_details_widget)

        # Country Stats Display Widget
        self.country_stats_display_widget = CountryStatsDisplayWidget(self)
        self.stats_stack.addWidget(self.country_stats_display_widget)
        self.country_stats_display_widget.back_to_global_requested.connect(self._show_global_stats_view)
        self.country_stats_display_widget.add_client_to_country_requested.connect(self.request_add_client_for_country)

        # Status Client List Widget
        self.status_client_list_widget = StatusClientListWidget(self)
        self.stats_stack.addWidget(self.status_client_list_widget)
        self.status_client_list_widget.back_to_global_requested.connect(self._show_global_stats_view)
        self.status_client_list_widget.view_client_detail_requested.connect(self.request_view_client_details.emit)


        self.stats_stack.setCurrentWidget(self.global_stats_widget) # Show global stats by default

    def _show_global_stats_view(self):
        self.stats_stack.setCurrentWidget(self.global_stats_widget)

    def _show_country_stats_view(self, country_name: str):
        """Fetches data and shows country-specific stats view."""
        logging.info(f"Fetching and showing stats for country: {country_name}")
        country_obj = get_country_by_name(country_name) # Assumes this function handles DB session
        if not country_obj:
            logging.error(f"Country '{country_name}' not found in DB.")
            self._show_global_stats_view() # Fallback
            # Optionally show a message to the user
            # (Requires self to be QWidget or have access to QMessageBox)
            if hasattr(self, 'parent') and callable(self.parent) and hasattr(self.parent(), 'notify'):
                 self.parent().notify("Erreur Données", f"Pays '{country_name}' non trouvé.", "ERROR")
            return

        country_id = country_obj['country_id']

        # These calls need a DB session. Assuming CRUD methods handle it via @_manage_conn
        # or that a session is passed if necessary (not shown here for brevity).
        # For SQLite, @_manage_conn usually creates a new connection per call.
        client_count = clients_crud_instance.get_client_count_by_country_id(country_id=country_id, include_deleted=False)
        project_count = get_active_project_count_by_country_id(country_id=country_id) # This is a direct import

        # For SQLAlchemy based CRUDs, a session needs to be passed or handled by the function.
        # Let's assume get_total_proforma_sales_for_country_id handles its session.
        db_session_proforma = get_db_connection() # Get a session for this call
        sales_value = 0.0
        try:
            sales_value = get_total_proforma_sales_for_country_id(db_session_proforma, country_id=country_id)
        finally:
            if db_session_proforma: db_session_proforma.close()

        self.country_stats_display_widget.update_display(country_name, client_count, project_count, sales_value)
        self.stats_stack.setCurrentWidget(self.country_stats_display_widget)

    @pyqtSlot(str, str)
    def _display_client_details_in_panel(self, client_id_str, client_name_str):
        logging.info(f"Displaying details for client: {client_name_str} (ID: {client_id_str}) in panel.")

        # Clear previous content from self.client_details_layout
        while self.client_details_layout.rowCount() > 0:
            self.client_details_layout.removeRow(0)


  

        try:
            client_data = clients_crud_instance.get_client_by_id(client_id_str, include_deleted=True)
            if not client_data:
                self.client_details_layout.addRow(QLabel(self.tr("Erreur:")), QLabel(self.tr("Client non trouvé.")))
                self.stats_stack.setCurrentWidget(self.client_details_widget)
                return

            country_name = self.tr("N/A")
            if client_data.get('country_id'):
                country_obj = get_country_by_id(client_data['country_id'])
                if country_obj: country_name = country_obj.get('country_name', self.tr("N/A"))

            city_name = self.tr("N/A")
            if client_data.get('city_id'):
                city_obj = get_city_by_id(client_data['city_id'])
                if city_obj: city_name = city_obj.get('city_name', self.tr("N/A"))

            status_name = self.tr("N/A")
            if client_data.get('status_id'):
                status_obj = get_status_setting_by_id(client_data['status_id'])
                if status_obj: status_name = status_obj.get('status_name', self.tr("N/A"))

            details_to_display = {
                self.tr("Nom Client:"): client_data.get('client_name', self.tr("N/A")),
                self.tr("Société:"): client_data.get('company_name', self.tr("N/A")) or self.tr("N/A"), # Ensure empty string becomes N/A
                self.tr("Pays:"): country_name,
                self.tr("Ville:"): city_name,
                self.tr("Statut:"): status_name,
                self.tr("Date Création:"): client_data.get('created_at_str', self.tr("N/A")), # Assuming 'created_at_str' exists
                self.tr("Besoin Principal:"): client_data.get('primary_need_description', self.tr("N/A")) or self.tr("N/A")
            }

            for label, value in details_to_display.items():
                value_label = QLabel(str(value))
                value_label.setWordWrap(True) # Allow text wrapping for longer values
                self.client_details_layout.addRow(QLabel(label), value_label)

        except Exception as e:
            logging.error(f"Error fetching/displaying client details for ID {client_id_str}: {e}", exc_info=True)
            self.client_details_layout.addRow(QLabel(self.tr("Erreur:")), QLabel(self.tr("Impossible de charger les détails du client.")))


        self.stats_stack.setCurrentWidget(self.client_details_widget)

    def refresh_statistics_data(self):
        logging.info("Refreshing statistics data panel...")
        self.update_global_stats()
        self.update_business_health_score()
        self.update_customer_segmentation_views()
        logging.info("Statistics data panel refresh complete.")

    # Placeholder for update_map - to be filled in Phase 3
    def update_map(self):
        logging.info("update_map: Method entered.")
        try:
            # GeoJSON path setup
            geojson_path = os.path.join(APP_ROOT_DIR, "resources", "assets", "world_countries.geojson")
            logging.info(f"update_map: Attempting to load GeoJSON from: {geojson_path}")

            if not os.path.exists(geojson_path):
                logging.error(f"GeoJSON file not found at: {geojson_path}.")
                error_message = self.tr("Les données géographiques de la carte (GeoJSON) sont introuvables...")
                self._set_map_error_html(error_message)
                return

            # Fetch data needed for the map
            clients_by_country_counts = None
            try:
                clients_by_country_counts = get_client_counts_by_country()
                logging.info(f"update_map: Fetched client_counts_by_country. Count: {len(clients_by_country_counts) if clients_by_country_counts else 0}")
            except Exception as db_exc:
                logging.error(f"Database error while fetching client counts for map: {db_exc}", exc_info=True)
                error_message = self.tr("Erreur de récupération des données statistiques (comptes par pays) pour la carte.").format(error_details=str(db_exc))
                self._set_map_error_html(error_message)
                return

            all_clients_for_main_map_popups = []
            try:
                all_clients_for_main_map_popups = clients_crud_instance.get_all_clients_with_details(include_deleted=False)
                logging.info(f"update_map: Fetched {len(all_clients_for_main_map_popups)} client details for popups.")
            except Exception as e_popup_data:
                logging.error(f"update_map: Error fetching all client details for popups: {e_popup_data}", exc_info=True)
                # Proceeding with empty list for popups, map will still render basic info.

            # Call the utility function to generate map HTML
            map_html_content = generate_folium_map_html(
                geojson_path=geojson_path,
                clients_by_country_counts=clients_by_country_counts,
                all_clients_details_for_popups=all_clients_for_main_map_popups,
                app_translator_func=self.tr, # Pass the instance's tr method
                map_interaction_handler_name="pyMapConnector" # Specific to this dashboard's handler
            )

            if map_html_content is None:
                logging.error("update_map: generate_folium_map_html returned None. Map generation failed.")
                self._set_map_error_html(self.tr("La génération du contenu HTML de la carte a échoué."))
                return

            if self.map_view:
                logging.info("update_map: About to set HTML content in QWebEngineView...")
                self.map_view.setHtml(map_html_content)
                logging.info(f"Map HTML content successfully set in QWebEngineView. Map should be attempting to render. HTML content length: {len(map_html_content)}.")
            else:
                logging.error("StatisticsDashboard: self.map_view is None. Cannot set HTML for the map after generation.")

        except Exception as e:
            logging.error(f"General error in update_map: {e}", exc_info=True)
            error_message = self.tr("Une erreur inattendue est survenue lors de la mise à jour de la carte.").format(error_details=str(e))
            self._set_map_error_html(error_message)

    def _set_map_error_html(self, message: str):
        """Helper function to set an error message HTML in the map_view."""
        logging.info(f"_set_map_error_html called. self.map_view is: {self.map_view}. Message: {message}")
        if self.map_view:
            # Basic styling for the error message
            # The button's onclick attempts to call a new method on pyMapConnector.
            # This 'requestMapRefresh' signal/slot needs to be added to MapInteractionHandler and StatisticsDashboard.
            # For this step, the JS call might not work fully yet, but the HTML structure is set.
            error_html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f8f9fa; }}
                    .error-container {{ text-align: center; padding: 30px; border: 1px solid #dc3545; background-color: #f8d7da; color: #721c24; border-radius: 8px; max-width: 80%; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
                    .error-icon {{ font-size: 32px; margin-bottom: 15px; color: #dc3545; }}
                    h3 {{ margin-top: 0; color: #721c24; font-size: 1.5em; }}
                    p {{ font-size: 1em; margin-bottom: 20px; }}
                    button {{
                        padding: 10px 20px;
                        font-size: 1em;
                        color: white;
                        background-color: #007bff;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                        transition: background-color 0.3s ease;
                    }}
                    button:hover {{ background-color: #0056b3; }}
                </style>
            </head>
            <body>
                <div class="error-container">
                    <div class="error-icon">⚠️</div>
                    <h3>{self.tr("Erreur d'Affichage de la Carte")}</h3>
                    <p>{message}</p>
                    <button onclick="if(window.pyMapConnector && typeof window.pyMapConnector.requestMapRefresh === 'function') {{ window.pyMapConnector.requestMapRefresh(); }} else {{ alert('{self.tr("Le mécanisme de rafraîchissement n\\'est pas encore pleinement disponible.")}'); }}">{self.tr("Réessayer")}</button>
                </div>
            </body>
            </html>
            """
            self.map_view.setHtml(error_html)
            logging.info(f"Displayed error HTML in map_view: {message}")
        else:
            logging.error("StatisticsDashboard: self.map_view is None. Cannot display error message in map_view.")


    # --- Methods to be ported from CollapsibleStatisticsWidget ---
    def update_global_stats(self):
        try:
            # Ensure clients_crud_instance is available, it should be from class level imports
            # If not, it might need to be passed or accessed via a global/app context

            current_total_clients = get_total_clients_count() # This is a direct import from db
            self.stats_labels["total_clients"].setText(str(current_total_clients))
            self.update_total_clients_trend(current_total_clients)

            current_active_clients = get_active_clients_count() # Direct import
            self.stats_labels["active_clients"].setText(str(current_active_clients))
            self.update_active_clients_trend(current_active_clients) # Update trend

            total_projects = get_total_projects_count()
            self.stats_labels["total_projects"].setText(str(total_projects))

            active_projects = get_active_projects_count()
            self.stats_labels["active_projects"].setText(str(active_projects))

            total_products = get_total_products_count()
            self.stats_labels["total_products"].setText(str(total_products))

            # Update for proforma sales (current month)
            sales_current_month = self.get_total_sales_from_proforma_current_month()
            self.stats_labels["total_sales_proforma"].setText("€ {:,.2f}".format(sales_current_month))
            self.update_total_sales_proforma_trend(sales_current_month) # Update trend

        except Exception as e:
            logging.error(f"Error updating global stats: {e}", exc_info=True)
            # Ensure all labels, including the new ones, are set to "Erreur"
            for key in self.stats_labels:
                self.stats_labels[key].setText(self.tr("Erreur"))
            # Clear specific trend labels that might not be covered by loop if keys differ
            self.stats_labels["total_clients_trend"].setText("")
            self.stats_labels["active_clients_trend"].setText("")
            self.stats_labels["total_sales_proforma_trend"].setText("")

        self.update_client_acquisition_stats() # Call to update new client stats


    def get_total_sales_from_proforma_current_month(self) -> float:
        """Fetches total sales from proforma invoices for the current calendar month."""
        db_session = None
        try:
            today = datetime.utcnow().date()
            start_of_current_month = today.replace(day=1)
            # Calculate the first day of the next month, then subtract one day to get the end of the current month
            end_of_current_month = (today.replace(day=1) + relativedelta(months=1)) - relativedelta(days=1)

            start_iso = start_of_current_month.strftime('%Y-%m-%dT00:00:00.000000Z')
            end_iso = end_of_current_month.strftime('%Y-%m-%dT23:59:59.999999Z')

            db_session = get_db_connection() # Get session for this call
            current_month_sales = get_total_sales_amount_for_period(db_session, start_iso, end_iso)
            return current_month_sales
        except Exception as e:
            logging.error(f"Error calculating total sales from proforma for current month: {e}", exc_info=True)
            return 0.0
        finally:
            if db_session: # Close session if obtained
                # This depends on how get_db_connection is implemented.
                # If it's a context manager or FastAPI-style dependency, direct close might not be needed.
                # Assuming direct close for now based on previous patterns for this file.
                try:
                    db_session.close()
                except Exception as e:
                    logging.error(f"Error closing db_session in get_total_sales_from_proforma_current_month: {e}", exc_info=True)


    def update_total_clients_trend(self, current_total_clients: int):
        """Updates the trend label for total clients."""
        try:
            today = datetime.utcnow().date()
            end_of_last_month_date = today.replace(day=1) - relativedelta(days=1)
            end_of_last_month_iso = end_of_last_month_date.strftime('%Y-%m-%dT23:59:59.999999Z')

            previous_total_clients = clients_crud_instance.get_total_clients_count_up_to_date(end_of_last_month_iso)

            trend_text = ""
            style = "color: gray;" # Default style
            if previous_total_clients > 0:
                percentage_change = ((current_total_clients - previous_total_clients) / previous_total_clients) * 100
                arrow = "→"
                if percentage_change > 0.5:
                    arrow = "↗"
                    style = "color: green;"
                elif percentage_change < -0.5:
                    arrow = "↘"
                    style = "color: red;"
                trend_text = f"{arrow} {percentage_change:.1f}%"
            elif current_total_clients > 0:
                trend_text = "↗ New"
                style = "color: green;"
            else:
                trend_text = "→ 0.0%"

            self.stats_labels["total_clients_trend"].setText(trend_text)
            self.stats_labels["total_clients_trend"].setStyleSheet(style)

        except Exception as e:
            logging.error(f"Error updating total clients trend: {e}", exc_info=True)
            self.stats_labels["total_clients_trend"].setText("")
            self.stats_labels["total_clients_trend"].setStyleSheet("")


    def update_active_clients_trend(self, current_active_clients: int):
        """Updates the trend label for active clients."""
        try:
            today = datetime.utcnow().date()
            end_of_last_month_date = today.replace(day=1) - relativedelta(days=1)
            end_of_last_month_iso = end_of_last_month_date.strftime('%Y-%m-%dT23:59:59.999999Z')

            # Ensure get_active_clients_count_up_to_date is available in clients_crud_instance
            previous_active_clients = clients_crud_instance.get_active_clients_count_up_to_date(end_of_last_month_iso)

            trend_text = ""
            style = "color: gray;" # Default style
            if previous_active_clients > 0:
                percentage_change = ((current_active_clients - previous_active_clients) / previous_active_clients) * 100
                arrow = "→"
                if percentage_change > 0.5:
                    arrow = "↗"
                    style = "color: green;"
                elif percentage_change < -0.5:
                    arrow = "↘"
                    style = "color: red;"
                trend_text = f"{arrow} {percentage_change:.1f}%"
            elif current_active_clients > 0:
                trend_text = "↗ New"
                style = "color: green;"
            else:
                trend_text = "→ 0.0%"

            self.stats_labels["active_clients_trend"].setText(trend_text)
            self.stats_labels["active_clients_trend"].setStyleSheet(style)

        except Exception as e:
            logging.error(f"Error updating active clients trend: {e}", exc_info=True)
            self.stats_labels["active_clients_trend"].setText("")
            self.stats_labels["active_clients_trend"].setStyleSheet("")


    def update_total_sales_proforma_trend(self, current_month_sales: float):
        """Updates the trend label for total proforma sales."""
        db_session = None
        try:
            today = datetime.utcnow().date()
            end_of_last_month_date = today.replace(day=1) - relativedelta(days=1)
            start_of_last_month_date = end_of_last_month_date.replace(day=1)

            start_prev_month_iso = start_of_last_month_date.strftime('%Y-%m-%dT00:00:00.000000Z')
            end_prev_month_iso = end_of_last_month_date.strftime('%Y-%m-%dT23:59:59.999999Z')

            db_session = get_db_connection() # Get session for this call
            previous_month_total_sales = get_total_sales_amount_for_period(db_session, start_prev_month_iso, end_prev_month_iso)

            trend_text = ""
            style = "color: gray;" # Default style
            if previous_month_total_sales > 0:
                percentage_change = ((current_month_sales - previous_month_total_sales) / previous_month_total_sales) * 100
                arrow = "→"
                if percentage_change > 0.5:
                    arrow = "↗"
                    style = "color: green;"
                elif percentage_change < -0.5:
                    arrow = "↘"
                    style = "color: red;"
                trend_text = f"{arrow} {percentage_change:.1f}%"
            elif current_month_sales > 0:
                trend_text = "↗ New"
                style = "color: green;"
            else:
                trend_text = "→ 0.0%"

            self.stats_labels["total_sales_proforma_trend"].setText(trend_text)
            self.stats_labels["total_sales_proforma_trend"].setStyleSheet(style)

        except Exception as e:
            logging.error(f"Error updating total sales proforma trend: {e}", exc_info=True)
            self.stats_labels["total_sales_proforma_trend"].setText("")
            self.stats_labels["total_sales_proforma_trend"].setStyleSheet("")
        finally:
            if db_session: # Close session if obtained
                try:
                    db_session.close()
                except Exception as e:
                    logging.error(f"Error closing db_session in update_total_sales_proforma_trend: {e}", exc_info=True)


    def update_client_acquisition_stats(self):
        """Updates labels for new clients acquired in the last month and last quarter."""
        try:
            today = datetime.utcnow().date()

            # Last Month Calculation
            end_of_last_month_date = today.replace(day=1) - relativedelta(days=1)
            start_of_last_month_date = end_of_last_month_date.replace(day=1)

            start_of_last_month_iso = start_of_last_month_date.strftime('%Y-%m-%dT00:00:00.000000Z')
            end_of_last_month_iso = end_of_last_month_date.strftime('%Y-%m-%dT23:59:59.999999Z')

            # Assuming clients_crud_instance is correctly imported and available
            count_last_month = clients_crud_instance.get_clients_count_created_between(
                start_date_iso=start_of_last_month_iso,
                end_date_iso=end_of_last_month_iso
            )
            self.stats_labels["new_clients_last_month"].setText(str(count_last_month))

            # Last Quarter Calculation
            current_quarter = (today.month - 1) // 3 + 1

            if current_quarter == 1:
                start_of_last_quarter_date = datetime(today.year - 1, 10, 1).date()
                end_of_last_quarter_date = datetime(today.year - 1, 12, 31).date()
            else:
                start_month_of_last_quarter = 3 * (current_quarter - 2) + 1
                end_month_of_last_quarter = 3 * (current_quarter - 1)

                start_of_last_quarter_date = datetime(today.year, start_month_of_last_quarter, 1).date()

                # Calculate last day of the end_month_of_last_quarter
                if end_month_of_last_quarter < 12:
                    last_day_of_end_month = (datetime(today.year, end_month_of_last_quarter + 1, 1).date() - relativedelta(days=1)).day
                else: # end_month_of_last_quarter is December
                    last_day_of_end_month = 31
                end_of_last_quarter_date = datetime(today.year, end_month_of_last_quarter, last_day_of_end_month).date()

            start_of_last_quarter_iso = start_of_last_quarter_date.strftime('%Y-%m-%dT00:00:00.000000Z')
            end_of_last_quarter_iso = end_of_last_quarter_date.strftime('%Y-%m-%dT23:59:59.999999Z')

            count_last_quarter = clients_crud_instance.get_clients_count_created_between(
                start_date_iso=start_of_last_quarter_iso,
                end_date_iso=end_of_last_quarter_iso
            )
            self.stats_labels["new_clients_last_quarter"].setText(str(count_last_quarter))

        except Exception as e:
            logging.error(f"Error updating client acquisition stats: {e}", exc_info=True)
            self.stats_labels["new_clients_last_month"].setText(self.tr("Erreur"))
            self.stats_labels["new_clients_last_quarter"].setText(self.tr("Erreur"))

    def update_business_health_score(self):
        try:
            # These are direct imports from db module, not using clients_crud_instance here.
            total_clients_count = get_total_clients_count()
            active_clients_count = get_active_clients_count()

            if total_clients_count > 0:
                health_score = (active_clients_count / total_clients_count) * 100
            else:
                health_score = 0

            self.health_score_value_label.setText(f"{health_score:.0f} %")
            self.health_score_progress_bar.setValue(int(health_score))
        except Exception as e:
            logging.error(f"Error updating business health score: {e}", exc_info=True)
            self.health_score_value_label.setText(self.tr("Erreur"))
            self.health_score_progress_bar.setValue(0)

    def _setup_segmentation_tab_ui_internal(self):
        self.segmentation_tables = {}
        self.segmentation_chart_pages = {} # New dictionary for storing page widgets of charts
        # self.segmentation_canvases = {} # Removed

        tab_configs = [
            ("country", self.tr("Par Pays"), ["Pays", "Nombre de Clients"], "table"),
            ("city", self.tr("Par Ville"), ["Pays", "Ville", "Nombre de Clients"], "table"),
            ("status", self.tr("Par Statut"), [], "chart"), # No headers for chart tab directly
            ("category", self.tr("Par Catégorie"), ["Catégorie", "Nombre de Clients"], "table"),
            ("product_popularity", self.tr("Par Popularité Produit"), [self.tr("Nom Produit"), self.tr("Nombre d'Utilisations")], "table")
        ]

        for key, title, headers, tab_type in tab_configs:
            tab_widget = QWidget()
            tab_layout = QVBoxLayout(tab_widget)

            if tab_type == "table":
                table_widget = QTableWidget()
                table_widget.setColumnCount(len(headers))
                table_widget.setHorizontalHeaderLabels(headers)
                table_widget.setEditTriggers(QTableWidget.NoEditTriggers)
                table_widget.setSelectionBehavior(QTableWidget.SelectRows)
                table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
                table_widget.setSortingEnabled(True)
                tab_layout.addWidget(table_widget)
                self.segmentation_tables[key] = table_widget
            elif tab_type == "chart":
                # For chart tabs, store the QWidget page itself.
                # The layout will be retrieved from this page widget when needed.
                self.segmentation_chart_pages[key] = tab_widget # Store the page widget

            self.segmentation_tabs.addTab(tab_widget, title)
        logging.debug(f"segmentation_chart_pages initialized: {self.segmentation_chart_pages}")
        logging.debug(f"segmentation_tables initialized: {self.segmentation_tables}")


    def _populate_table(self, table_key, data_fetch_func, column_keys):
        table = self.segmentation_tables.get(table_key)
        if not table: return
        table.setSortingEnabled(False)
        table.setRowCount(0)
        try:
            data_rows = data_fetch_func()
            if data_rows is None: data_rows = []
            for row_idx, row_data in enumerate(data_rows):
                table.insertRow(row_idx)
                for col_idx, col_key in enumerate(column_keys):
                    item_value = row_data.get(col_key, "")
                    table.setItem(row_idx, col_idx, QTableWidgetItem(str(item_value)))
        except Exception as e:
            logging.error(f"Error populating table {table_key}: {e}", exc_info=True)
        finally:
            table.setSortingEnabled(True)

    def _on_status_chart_slice_picked(self, event):
        logging.debug(f"Pie chart slice picked. Event: {event}, Artist: {event.artist}")
        if not hasattr(self, 'last_pie_chart_labels') or not self.last_pie_chart_labels:
            logging.warning("_on_status_chart_slice_picked: last_pie_chart_labels not available.")
            return

        # Find the index of the picked wedge
        # The order of patches in axes.patches usually corresponds to the order of data slices
        try:
            # Ensure we're looking at the correct axes. Pie chart is typically the first/only one.
            ax_patches = event.artist.axes.patches
            wedge_index = ax_patches.index(event.artist)

            if 0 <= wedge_index < len(self.last_pie_chart_labels):
                status_name = self.last_pie_chart_labels[wedge_index]
                logging.info(f"Clicked on status: {status_name} (index: {wedge_index})")

                # Fetch status_id from DB
                status_obj = get_status_setting_by_name(status_name, 'Client') # Assumes this handles DB session
                if not status_obj:
                    logging.error(f"Status '{status_name}' not found in DB for type 'Client'.")
                    if hasattr(self, 'parent') and callable(self.parent) and hasattr(self.parent(), 'notify'):
                        self.parent().notify("Erreur Données", f"Détails du statut '{status_name}' non trouvés.", "ERROR")
                    return

                status_id = status_obj['status_id']

                # Fetch clients for this status_id
                # clients_crud_instance.get_clients_by_status_id handles its own DB session via @_manage_conn
                clients = clients_crud_instance.get_clients_by_status_id(status_id=status_id, include_deleted=False)

                self.status_client_list_widget.update_display(status_name, clients)
                self.stats_stack.setCurrentWidget(self.status_client_list_widget)
            else:
                logging.warning(f"Picked wedge index {wedge_index} out of bounds for labels (len: {len(self.last_pie_chart_labels)}).")
        except ValueError:
            logging.warning("Picked artist not found in axes patches. Cannot determine status.")
        except Exception as e:
            logging.error(f"Error handling pie chart pick event: {e}", exc_info=True)


    def _update_status_segmentation_chart(self):
        logging.debug(f"Current segmentation_chart_pages at start of _update_status_segmentation_chart: {getattr(self, 'segmentation_chart_pages', 'Not Initialized')}")
        logging.info("Updating status segmentation chart...")

        page_widget = None
        if hasattr(self, 'segmentation_chart_pages'):
            page_widget = self.segmentation_chart_pages.get("status")

        logging.debug(f"Retrieved page_widget for 'status': {page_widget}")

        if page_widget is None:
            logging.error("Page widget for 'status' chart not found in self.segmentation_chart_pages.")
            return

        chart_layout = page_widget.layout()
        logging.debug(f"Retrieved chart_layout from page_widget: {chart_layout} (type: {type(chart_layout)})")

        chart_layout = page_widget.layout()
        logging.debug(f"Retrieved chart_layout from page_widget: {chart_layout} (type: {type(chart_layout)})")

        layout_usable = False
        if chart_layout is not None:
            sip_available = False
            is_deleted_by_sip = True # Assume deleted if sip check fails or sip not available
            try:
                import sip # Ensure sip is available in this scope if not globally
                is_deleted_by_sip = sip.isdeleted(chart_layout)
                sip_available = True
                logging.debug(f"sip.isdeleted(chart_layout) for 'status' returned: {is_deleted_by_sip}")
                if is_deleted_by_sip:
                    logging.error(f"Chart layout for 'status' ({chart_layout}) C++ object IS DELETED according to sip.isdeleted().")
            except ImportError:
                logging.warning("`sip` module could not be imported. Cannot perform sip.isdeleted() check.")
            except Exception as e_sip: # Catch other errors from sip, like NameError if sip itself isn't found
                logging.warning(f"Error calling or using sip.isdeleted(chart_layout): {e_sip}. Assuming layout might be unusable.")

            if not sip_available:
                # If sip check couldn't be done, rely on truthiness but log it.
                if not chart_layout:
                    logging.critical(f"CRITICAL FALLBACK: sip not available. Chart layout ({chart_layout}) evaluates to FALSY. Cannot proceed.")
                else:
                    logging.info("sip not available. Proceeding with chart layout as it's not None and truthy (fallback check).")
                    layout_usable = True # Trust truthiness if sip fails
            elif not is_deleted_by_sip:
                logging.info(f"Chart layout for 'status' ({chart_layout}) is not None and sip.isdeleted() is False. Proceeding to use.")
                layout_usable = True
            else: # Is None or sip.isdeleted() is True
                logging.error(f"Chart layout for 'status' ({chart_layout}) is unusable (None or deleted by sip). Cannot proceed.")
        else: # chart_layout was None from page_widget.layout()
            logging.error(f"Chart layout for 'status' is None (retrieved from page_widget.layout()). Page widget was: {page_widget}")
            # Attempt to re-set a layout (defensive)
            if page_widget and page_widget.layout() is None:
                logging.warning(f"Page widget {page_widget} for 'status' exists but has no layout. Attempting to set a new QVBoxLayout.")
                try:
                    new_layout = QVBoxLayout(page_widget)
                    page_widget.setLayout(new_layout)
                    chart_layout = new_layout
                    logging.info(f"Successfully set a new QVBoxLayout on page_widget for 'status': {chart_layout}")
                    layout_usable = True # New layout should be usable
                except Exception as e_set_layout:
                    logging.error(f"Failed to set a new layout on page_widget for 'status': {e_set_layout}", exc_info=True)
            # If still not usable, layout_usable remains False

        if not layout_usable:
            return # Exit if layout is not considered usable

        # Clear previous canvas if any
        while chart_layout.count():
            item = chart_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        try:
            status_data = get_client_segmentation_by_status()
            if not status_data:
                logging.info("No data for status segmentation chart.")
                no_data_label = QLabel(self.tr("Aucune donnée de statut client disponible pour afficher le graphique."))
                no_data_label.setAlignment(Qt.AlignCenter)
                chart_layout.addWidget(no_data_label)
                return

            labels = [item.get('status_name', 'N/A') for item in status_data]
            sizes = [item.get('client_count', 0) for item in status_data]

            # Filter out zero sizes to prevent display issues with pie chart
            filtered_labels = []
            filtered_sizes = []
            for label, size in zip(labels, sizes):
                if size > 0:
                    filtered_labels.append(label)
                    filtered_sizes.append(size)

            if not filtered_sizes: # All statuses have 0 clients
                logging.info("All statuses have 0 clients for status segmentation chart.")
                no_data_label = QLabel(self.tr("Aucun client trouvé pour les statuts existants."))
                no_data_label.setAlignment(Qt.AlignCenter)
                chart_layout.addWidget(no_data_label)
                return

            labels = filtered_labels
            sizes = filtered_sizes

            # Using a more Qt-friendly way to create the figure and canvas
            # plt.style.use('seaborn-v0_8-whitegrid') # Optional: for styling

            # Create a new figure and canvas each time to avoid issues with redrawing on the same canvas
            # It's generally safer for dynamic updates in Qt.
            fig = Figure(figsize=(5, 4), dpi=100) # Adjust figsize and dpi as needed
            ax = fig.add_subplot(111)

            # Generate distinct colors if many segments, or use default
            # colors = plt.cm.get_cmap('viridis', len(labels)).colors # Example: 'viridis' colormap

            wedges, texts, autotexts = ax.pie(
                sizes,
                autopct=lambda p: '{:.1f}% ({:.0f})'.format(p, p * sum(sizes) / 100), # Show percentage and absolute count
                startangle=90,
                # colors=colors # Optional: apply custom colors
                # picker=True # This might make the whole pie pickable, not individual wedges easily
            )
            ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

            # Make each wedge pickable
            for wedge in wedges:
                wedge.set_picker(True)
                wedge.set_pickradius(5) # Adjust pick radius as needed

            # Store labels for use in pick event handler
            self.last_pie_chart_labels = labels

            # Add a legend
            # Place legend outside the pie chart to avoid overlap, adjust bbox_to_anchor as needed
            ax.legend(wedges, labels, title=self.tr("Statuts"), loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
            fig.tight_layout() # Adjust layout to make room for legend if it's outside

            # Disconnect previous canvas's pick_event if it exists and is connected
            if hasattr(self, 'status_chart_canvas') and self.status_chart_canvas:
                try:
                    # Check if already connected to prevent multiple connections or errors on disconnect
                    # This is tricky as mpl_connect returns a cid, not easy to check if a specific handler is connected.
                    # For simplicity, we might risk disconnecting if not connected, or just connect once.
                    # A robust way is to store the cid and disconnect using it.
                    if hasattr(self, '_pick_event_cid') and self._pick_event_cid is not None:
                        self.status_chart_canvas.mpl_disconnect(self._pick_event_cid)
                        logging.debug("Disconnected old pick_event from status_chart_canvas.")
                except Exception as e_disconnect:
                    logging.warning(f"Could not disconnect old pick_event: {e_disconnect}")


            self.status_chart_canvas = FigureCanvas(fig) # Store canvas as instance variable
            self._pick_event_cid = self.status_chart_canvas.mpl_connect('pick_event', self._on_status_chart_slice_picked)
            logging.debug(f"Connected new pick_event to status_chart_canvas with CID: {self._pick_event_cid}")

            chart_layout.addWidget(self.status_chart_canvas)
            self.status_chart_canvas.draw()
            logging.info("Status segmentation chart updated successfully with pick events enabled.")

        except Exception as e:
            logging.error(f"Error updating status segmentation chart: {e}", exc_info=True)
            error_label = QLabel(self.tr("Erreur lors de la génération du graphique des statuts."))
            error_label.setAlignment(Qt.AlignCenter)
            chart_layout.addWidget(error_label)


    def update_customer_segmentation_views(self):
        self._populate_table("country", get_client_counts_by_country, ["country_name", "client_count"])
        self._populate_table("city", get_client_segmentation_by_city, ["country_name", "city_name", "client_count"])
        # self._populate_table("status", get_client_segmentation_by_status, ["status_name", "client_count"]) # Replaced by chart
        self._update_status_segmentation_chart() # New method for chart
        self._populate_table("category", get_client_segmentation_by_category, ["category", "client_count"])
        self._populate_table("product_popularity", get_product_usage_counts, ["product_name", "usage_count"])

    # --- End of Ported Methods ---
        # The old update_statistics_map method (which was the display-only map) is now removed.
        # self.update_map() is the current method for the interactive map.


class StatisticsSummaryWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("StatisticsSummaryWidget")
        self._init_ui()
        self.update_summary_stats() # Load stats on init

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)

        title_label = QLabel(self.tr("Aperçu Rapide"))
        title_label.setObjectName("summaryTitleLabel") # For styling if needed
        title_label.setAlignment(Qt.AlignCenter)
        # Consider a slightly smaller or different font for summary title
        font = title_label.font()
        font.setPointSize(font.pointSize() + 1) # Slightly larger
        font.setBold(True)
        title_label.setFont(font)
        layout.addWidget(title_label)

        stats_group = QGroupBox(self.tr("Statistiques Clés"))
        stats_layout = QFormLayout(stats_group)

        self.summary_labels = {
            "total_clients": QLabel("0"),
            "active_projects": QLabel("0"),
            "total_sales_current_month": QLabel("€ 0.00") # Example new stat for summary
        }

        stats_layout.addRow(self.tr("Clients Totaux:"), self.summary_labels["total_clients"])
        stats_layout.addRow(self.tr("Projets Actifs:"), self.summary_labels["active_projects"])
        stats_layout.addRow(self.tr("Ventes (Mois Actuel):"), self.summary_labels["total_sales_current_month"])

        layout.addWidget(stats_group)
        layout.addStretch(1) # Push content to the top

        self.setLayout(layout)

    def update_summary_stats(self):
        logging.info("StatisticsSummaryWidget: Updating summary stats...")
        try:
            total_clients = get_total_clients_count()
            self.summary_labels["total_clients"].setText(str(total_clients))

            active_projects = get_active_projects_count()
            self.summary_labels["active_projects"].setText(str(active_projects))

            # Re-use logic from StatisticsDashboard for sales calculation if complex,
            # or simplify if only current month is needed.
            # For now, direct call similar to what StatisticsDashboard would do:
            sales_current_month_val = 0.0
            db_session = None
            try:
                today = datetime.utcnow().date()
                start_of_current_month = today.replace(day=1)
                end_of_current_month = (today.replace(day=1) + relativedelta(months=1)) - relativedelta(days=1)
                start_iso = start_of_current_month.strftime('%Y-%m-%dT00:00:00.000000Z')
                end_iso = end_of_current_month.strftime('%Y-%m-%dT23:59:59.999999Z')
                db_session = get_db_connection()
                sales_current_month_val = get_total_sales_amount_for_period(db_session, start_iso, end_iso)
            except Exception as e_sales:
                logging.error(f"StatisticsSummaryWidget: Error fetching current month sales: {e_sales}", exc_info=True)
            finally:
                if db_session:
                    try: db_session.close()
                    except: pass # Ignore close error

            self.summary_labels["total_sales_current_month"].setText("€ {:,.2f}".format(sales_current_month_val))
            logging.info("StatisticsSummaryWidget: Summary stats updated.")

        except Exception as e:
            logging.error(f"StatisticsSummaryWidget: Error updating summary stats: {e}", exc_info=True)
            for key in self.summary_labels:
                self.summary_labels[key].setText(self.tr("Erreur"))

    def refresh_data(self): # Public method for external refresh if needed
        self.update_summary_stats()


class StatusClientListWidget(QWidget):
    """
    A widget to display a list of clients for a specific status.
    Emits signals for 'back' and 'view_client_detail'.
    """
    back_to_global_requested = pyqtSignal()
    view_client_detail_requested = pyqtSignal(str)  # Emits client_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("StatusClientListWidget")
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        self.title_label = QLabel("Clients par Statut") # Placeholder, updated by update_display
        font = self.title_label.font()
        font.setPointSize(font.pointSize() + 2)
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.title_label)

        self.clients_table = QTableWidget()
        self.clients_table.setColumnCount(4)
        self.clients_table.setHorizontalHeaderLabels([
            self.tr("Nom Client"), self.tr("Société"),
            self.tr("Pays"), self.tr("Ville")
        ])
        self.clients_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.clients_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.clients_table.setSelectionMode(QTableWidget.SingleSelection)
        self.clients_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.clients_table.itemSelectionChanged.connect(self._on_table_selection_changed)
        self.clients_table.doubleClicked.connect(self._on_table_double_clicked) # Handle double click
        main_layout.addWidget(self.clients_table)

        buttons_layout = QHBoxLayout()
        self.view_client_button = QPushButton(self.tr("Voir Fiche Client"))
        self.view_client_button.setIcon(QIcon(":/icons/eye.svg")) # Placeholder icon
        self.view_client_button.setEnabled(False) # Initially disabled
        self.view_client_button.clicked.connect(self._emit_view_client_detail_signal)
        buttons_layout.addWidget(self.view_client_button)

        buttons_layout.addStretch()

        self.back_button = QPushButton(self.tr("Retour aux Stats Globales"))
        self.back_button.setIcon(QIcon(":/icons/arrow-left-circle.svg"))
        self.back_button.clicked.connect(self.back_to_global_requested.emit)
        buttons_layout.addWidget(self.back_button)

        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)

    def update_display(self, status_name: str, clients: list[dict]):
        self.title_label.setText(self.tr("Clients - Statut: {0}").format(status_name))

        self.clients_table.setRowCount(0) # Clear previous data
        self.clients_table.setSortingEnabled(False) # Disable sorting during population

        if not clients:
            logging.info(f"StatusClientListWidget: No clients to display for status '{status_name}'.")
            # Optionally, display a message in the table or a separate label
            return

        for row, client_data in enumerate(clients):
            self.clients_table.insertRow(row)

            name_item = QTableWidgetItem(client_data.get("client_name", "N/A"))
            # Store client_id in the UserRole of the first item in the row for easy access
            name_item.setData(Qt.UserRole, client_data.get("client_id"))

            self.clients_table.setItem(row, 0, name_item)
            self.clients_table.setItem(row, 1, QTableWidgetItem(client_data.get("company_name", "N/A")))
            self.clients_table.setItem(row, 2, QTableWidgetItem(client_data.get("country", "N/A"))) # Assuming 'country' (name) is in client_data
            self.clients_table.setItem(row, 3, QTableWidgetItem(client_data.get("city", "N/A"))) # Assuming 'city' (name) is in client_data

        self.clients_table.setSortingEnabled(True)
        self.view_client_button.setEnabled(False) # Disable after repopulating
        logging.info(f"StatusClientListWidget updated for status '{status_name}' with {len(clients)} clients.")

    def _on_table_selection_changed(self):
        self.view_client_button.setEnabled(len(self.clients_table.selectedItems()) > 0)

    def _emit_view_client_detail_signal(self):
        selected_items = self.clients_table.selectedItems()
        if selected_items:
            # Get client_id from the first item in the selected row (stored in UserRole)
            selected_row = selected_items[0].row()
            client_id_item = self.clients_table.item(selected_row, 0) # Assuming client_id is on the first column's item
            if client_id_item:
                client_id = client_id_item.data(Qt.UserRole)
                if client_id:
                    self.view_client_detail_requested.emit(str(client_id))
                else:
                    logging.warning("StatusClientListWidget: No client_id found in selected table row's UserRole.")
            else:
                 logging.warning("StatusClientListWidget: First item in selected row is None, cannot get client_id.")

    def _on_table_double_clicked(self, index):
        # On double click, directly emit the view client detail signal for that row
        client_id_item = self.clients_table.item(index.row(), 0) # Assuming client_id is on the first column's item
        if client_id_item:
            client_id = client_id_item.data(Qt.UserRole)
            if client_id:
                self.view_client_detail_requested.emit(str(client_id))
            else:
                logging.warning("StatusClientListWidget: No client_id found in double-clicked table row's UserRole.")
        else:
            logging.warning("StatusClientListWidget: First item in double-clicked row is None, cannot get client_id.")

class CountryStatsDisplayWidget(QWidget):
    """
    A widget to display country-specific statistics.
    Emits signals for 'back' and 'add_client_to_country'.
    """
    back_to_global_requested = pyqtSignal()
    add_client_to_country_requested = pyqtSignal(str) # Emits country name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CountryStatsDisplayWidget")
        self.current_country_name = None # To store the name of the country being displayed
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        self.title_label = QLabel("Statistiques par Pays") # Placeholder, will be updated
        font = self.title_label.font()
        font.setPointSize(font.pointSize() + 2)
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.title_label)

        stats_group = QGroupBox(self.tr("Détails")) # GroupBox for the stats
        form_layout = QFormLayout(stats_group)

        self.client_count_label = QLabel("N/A")
        self.project_count_label = QLabel("N/A")
        self.sales_value_label = QLabel("N/A")

        form_layout.addRow(self.tr("Clients Totaux:"), self.client_count_label)
        form_layout.addRow(self.tr("Projets Actifs:"), self.project_count_label)
        form_layout.addRow(self.tr("Ventes Proforma Totales:"), self.sales_value_label)

        main_layout.addWidget(stats_group)

        # --- Action Buttons ---
        buttons_layout = QHBoxLayout()
        self.add_client_button = QPushButton(self.tr("Ajouter Client à ce Pays"))
        self.add_client_button.setIcon(QIcon(":/icons/user-add.svg")) # Placeholder icon
        self.add_client_button.clicked.connect(self._emit_add_client_signal)
        buttons_layout.addWidget(self.add_client_button)

        buttons_layout.addStretch() # Pushes back button to the right

        self.back_button = QPushButton(self.tr("Retour aux Stats Globales"))
        self.back_button.setIcon(QIcon(":/icons/arrow-left-circle.svg")) # Placeholder icon
        self.back_button.clicked.connect(self.back_to_global_requested)
        buttons_layout.addWidget(self.back_button)

        main_layout.addLayout(buttons_layout)
        main_layout.addStretch(1) # Push content to the top
        self.setLayout(main_layout)

    def update_display(self, country_name: str, client_count: int, project_count: int, sales_value: float):
        self.current_country_name = country_name # Store for the "Add Client" button
        self.title_label.setText(self.tr("Statistiques pour: {0}").format(country_name))
        self.client_count_label.setText(str(client_count))
        self.project_count_label.setText(str(project_count))
        self.sales_value_label.setText("€ {:,.2f}".format(sales_value))
        logging.info(f"CountryStatsDisplayWidget updated for {country_name}.")

    def _emit_add_client_signal(self):
        if self.current_country_name:
            self.add_client_to_country_requested.emit(self.current_country_name)
        else:
            logging.warning("CountryStatsDisplayWidget: _emit_add_client_signal called but current_country_name is not set.")