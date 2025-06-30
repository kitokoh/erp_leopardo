# -*- coding: utf-8 -*-
import os
import logging
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
import pandas as pd
from branca.colormap import StepColormap # Import StepColormap

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
from db.cruds.proforma_invoices_crud import list_proforma_invoices # Added for proforma sales
from db.connection import get_db_connection # Added for proforma sales
# It seems db_manager is not directly imported, but functions are. If needed, import db as db_manager
from db.cruds.clients_crud import clients_crud_instance
from db.cruds.client_project_products_crud import get_product_usage_counts # Added for product popularity
from db.cruds.proforma_invoices_crud import get_total_sales_amount_for_period # Added for sales trend

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
        self._left_map_actual_layout = QVBoxLayout(self.left_widget_for_map)
        self._left_map_actual_layout.setContentsMargins(0,0,0,0)
        # self.left_widget_for_map.setLayout(self._left_map_actual_layout) # Redundant if QVBoxLayout constructor has parent


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

        # Ensure the container widget for the map exists
        if self.left_widget_for_map is None:
            logging.critical("StatisticsDashboard: self.left_widget_for_map is None at the start of _initialize_map_and_load_data. Cannot initialize map.")
            # This indicates a severe problem with the widget's construction or state.
            return

        # self._left_map_actual_layout should have been initialized in __init__
        # and is the correct layout for self.left_widget_for_map.
        # We verify if self.left_widget_for_map.layout() still reports it,
        # or if it somehow became None.

        current_layout_on_widget = self.left_widget_for_map.layout()

        if current_layout_on_widget is None:
            logging.warning("StatisticsDashboard: self.left_widget_for_map.layout() is None. "
                            "This is unexpected as it should have been set in __init__ via self._left_map_actual_layout. "
                            "Attempting to re-apply self._left_map_actual_layout if it exists, or recreate.")
            if self._left_map_actual_layout is not None:
                # Re-apply the layout instance we stored in __init__
                self.left_widget_for_map.setLayout(self._left_map_actual_layout)
            else:
                # This is a more critical state: self._left_map_actual_layout itself was not set in __init__
                logging.error("StatisticsDashboard: self._left_map_actual_layout is also None. This indicates an issue in __init__. Recreating layout.")
                self._left_map_actual_layout = QVBoxLayout(self.left_widget_for_map)
                self._left_map_actual_layout.setContentsMargins(0,0,0,0)
                # self.left_widget_for_map.setLayout() is implicitly called by QVBoxLayout constructor with parent
        elif current_layout_on_widget is not self._left_map_actual_layout:
            logging.warning("StatisticsDashboard: self.left_widget_for_map.layout() (is %s) is different from self._left_map_actual_layout (is %s). "
                            "This is highly unexpected. Trusting the instance variable self._left_map_actual_layout.",
                            id(current_layout_on_widget), id(self._left_map_actual_layout) )
            # If the widget has a *different* layout, and we are sure _left_map_actual_layout is the one we want,
            # we might need to re-set it. However, this situation implies external modification or a deep bug.
            # For now, we assume self._left_map_actual_layout is the intended one.
            # If self.left_widget_for_map.layout() returned a *different, valid* layout,
            # and self._left_map_actual_layout was also valid but different,
            # the original code would have updated self._left_map_actual_layout to match the widget.
            # The current CRITICAL error implies self._left_map_actual_layout becomes None.
            pass # We will proceed using self._left_map_actual_layout as defined in __init__

        # Final check on self._left_map_actual_layout, which should be the one from __init__
        if not self._left_map_actual_layout:
            logging.critical("StatisticsDashboard: self._left_map_actual_layout is None after checks. Cannot proceed with map initialization.")
            return

        if self.map_view is None:
            # Parent QWebEngineView to self.left_widget_for_map, which is its container
            self.map_view = QWebEngineView(self.left_widget_for_map) # Parent to the widget
            # Add the map_view to self._left_map_actual_layout, which is confirmed or restored/recreated.
            self._left_map_actual_layout.addWidget(self.map_view)
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
        logging.info(f"Map country clicked: {country_name}. Emitting request_add_client_for_country.")
        self.request_add_client_for_country.emit(country_name)

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

        self.stats_stack.setCurrentWidget(self.global_stats_widget) # Show global stats by default

    def _show_global_stats_view(self):
        self.stats_stack.setCurrentWidget(self.global_stats_widget)

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
        logging.info("Updating interactive map...")
        try:
            geojson_path = os.path.join(APP_ROOT_DIR, "assets", "world_countries.geojson")

            if not os.path.exists(geojson_path):
                logging.error(f"GeoJSON file not found at: {geojson_path}")
            error_message = self.tr("Les données géographiques de la carte (GeoJSON) sont introuvables. La carte ne peut pas être affichée. Veuillez vérifier l'installation de l'application ou contacter le support.")
            self._set_map_error_html(error_message)
            return

            m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB positron")
            # clients_by_country_counts = get_client_counts_by_country() # Removed redundant call

        # try:
            clients_by_country_counts = get_client_counts_by_country()
        except Exception as db_exc:
            logging.error(f"Database error while fetching client counts for map: {db_exc}", exc_info=True)
            error_message = self.tr("Erreur de récupération des données statistiques pour la carte : {error_details}. L'affichage de la carte est indisponible.").format(error_details=str(db_exc))
            self._set_map_error_html(error_message)
            return




            # The rest of the map generation logic follows...
            if clients_by_country_counts:
                counts_dict = {item['country_name']: item['client_count'] for item in clients_by_country_counts}
                max_observed_clients = max(item['client_count'] for item in clients_by_country_counts) if clients_by_country_counts else 0
                category_colors = ['#f7f7f7', '#c6dbef', '#6baed6', '#08519c']
                color_index = [0, 1, 2, 4]
                client_colormap = StepColormap(colors=category_colors, index=color_index, vmin=0, vmax=max(4, max_observed_clients), caption=self.tr("Nombre de Clients par Pays (Catégories)"))
                def style_function(feature):
                    count = counts_dict.get(feature['properties']['name'], 0)
                    return {'fillColor': client_colormap(count), 'color': '#555555', 'weight': 0.5, 'fillOpacity': 0.7}
                folium.GeoJson(geojson_path, name=self.tr("Distribution des Clients par Pays"), style_function=style_function, tooltip=folium.features.GeoJsonTooltip(fields=['name'], aliases=[self.tr('Pays:')], localize=True)).add_to(m)
                client_colormap.add_to(m)
            else:
                folium.GeoJson(geojson_path, name=self.tr("Pays (Base)"), tooltip=folium.features.GeoJsonTooltip(fields=['name'], aliases=[self.tr('Pays:')])).add_to(m)
                logging.info("StatisticsDashboard: No client count data. Added basic GeoJSON layer for choropleth.")

            popup_layer = folium.GeoJson(
                geojson_path,
                name=self.tr("Informations Pays"),
                style_function=lambda x: {'fillColor':'transparent', 'color':'transparent', 'weight':0},
                tooltip=None
            )

            for feature in popup_layer.data.get('features', []):
                country_name = feature.get('properties', {}).get('name', 'N/A')
                if country_name == 'N/A': continue
                country_client_count = next((item['client_count'] for item in clients_by_country_counts if item['country_name'] == country_name), 0)
                popup_html = f"<b>{country_name}</b><br>"
                popup_html += f"{self.tr('Clients (Total)')}: {country_client_count}<br><hr>"
                country_obj = get_country_by_name(country_name)
                city_client_map = {}
                if country_obj:
                    country_id = country_obj.get('country_id')
                    clients_in_country = clients_crud_instance.get_all_clients_with_details(filters={'country_id': country_id}, include_deleted=False)
                    if clients_in_country:
                        for client in clients_in_country:
                            city_name = client.get('city', self.tr('Ville Inconnue'))
                            client_detail_name = client.get('client_name', self.tr('Client Inconnu'))
                            client_id = client.get('client_id')
                            if city_name not in city_client_map: city_client_map[city_name] = []
                            if len(city_client_map[city_name]) < 3: city_client_map[city_name].append({'id': client_id, 'name': client_detail_name})
                if city_client_map:
                    for city_name_iter, clients_in_city_list in city_client_map.items():
                        popup_html += f"<b>{self.tr('Ville')}: {city_name_iter}</b> ({len(clients_in_city_list)} {self.tr('client(s) affiché(s)')})<br>"
                        popup_html += "<ul>"
                        for client_data_item in clients_in_city_list:
                            js_client_id_arg = json.dumps(client_data_item['id'])
                            js_client_name_arg = json.dumps(client_data_item['name'])
                            onclick_js = f"pyMapConnector.clientClickedOnMap({js_client_id_arg}, {js_client_name_arg}); return false;"
                            popup_html += f"<li><a href='#' onclick='{onclick_js}'>{client_data_item['name']}</a></li>"
                        popup_html += "</ul>"
                else:
                    popup_html += f"{self.tr('Aucun client détaillé à afficher pour les villes.')}<br>"

                js_country_name_arg = json.dumps(country_name)
                button_text = self.tr('Ajouter Client Ici')
                onclick_country_js = f"pyMapConnector.countryClicked({js_country_name_arg}); return false;"
                popup_html += f"<br><button onclick='{onclick_country_js}'>{button_text}</button>"
                feature['properties']['popup_content'] = popup_html

            popup_layer.add_child(folium.features.GeoJsonPopup(fields=['popup_content'], localize=True))
            popup_layer.add_to(m)
            folium.LayerControl().add_to(m)
            map_html_content = m.get_root().render()

            webchannel_setup_js = """
            <script type="text/javascript" src="qrc:///qtwebchannel/qwebchannel.js"></script>
            <script type="text/javascript">
                document.addEventListener("DOMContentLoaded", function() {
                    if (typeof QWebChannel !== 'undefined') {
                        new QWebChannel(qt.webChannelTransport, function(channel) {
                            window.pyMapConnector = channel.objects.pyMapConnector;
                            if (window.pyMapConnector === undefined) {
                                console.error("pyMapConnector object not found in channel.objects. Available objects:", Object.keys(channel.objects));
                            } else {
                                console.log("pyMapConnector initialized successfully.");
                            }
                        });
                    } else {
                        console.error("QWebChannel JavaScript library not loaded. pyMapConnector will not be available.");
                    }
                });
            </script>
            """
            if "</body>" in map_html_content:
                map_html_content = map_html_content.replace("</body>", webchannel_setup_js + "</body>", 1)
            elif "</html>" in map_html_content:
                map_html_content = map_html_content.replace("</html>", webchannel_setup_js + "</html>", 1)
            else:
                map_html_content += webchannel_setup_js

            if self.map_view:
                self.map_view.setHtml(map_html_content)
                logging.info("Interactive map updated successfully with QWebChannel JS.")
            else:
                logging.error("StatisticsDashboard: self.map_view is None. Cannot set HTML for the map.")

        except Exception as e:
            logging.error(f"General error updating interactive map: {e}", exc_info=True) # Changed log message slightly for clarity
            error_message = self.tr("Une erreur inattendue est survenue lors de la génération de la carte : {error_details}. L'affichage de la carte est indisponible. Veuillez réessayer ou contacter le support si le problème persiste.").format(error_details=str(e))
            self._set_map_error_html(error_message)

    def _set_map_error_html(self, message: str):
        """Helper function to set an error message HTML in the map_view."""
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
        self.segmentation_canvases = {} # For Matplotlib canvases

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
                # For chart tabs, we'll create a FigureCanvas later when data is available
                # We can store the layout or a placeholder widget if needed.
                # For simplicity, we'll store the layout and add the canvas to it in the update method.
                self.segmentation_canvases[key] = tab_layout # Store the layout for the canvas

            self.segmentation_tabs.addTab(tab_widget, title)


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

    def _update_status_segmentation_chart(self):
        logging.info("Updating status segmentation chart...")
        chart_layout = self.segmentation_canvases.get("status")
        if not chart_layout:
            logging.error("Chart layout for 'status' not found.")
            return

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
            )
            ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

            # Add a legend
            # Place legend outside the pie chart to avoid overlap, adjust bbox_to_anchor as needed
            ax.legend(wedges, labels, title=self.tr("Statuts"), loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
            fig.tight_layout() # Adjust layout to make room for legend if it's outside

            canvas = FigureCanvas(fig)
            chart_layout.addWidget(canvas)
            canvas.draw()
            logging.info("Status segmentation chart updated successfully.")

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