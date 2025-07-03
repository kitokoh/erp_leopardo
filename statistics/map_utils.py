# -*- coding: utf-8 -*-
import logging
import os
import json
import folium
from branca.colormap import StepColormap

# These DB access functions are problematic if map_utils is to be generic.
# Ideally, the data should be fetched by the caller and passed into the map generation function.
from db import get_country_by_name # Used for popups
from db.cruds.clients_crud import clients_crud_instance # Used for popups

def generate_folium_map_html(
    geojson_path: str,
    clients_by_country_counts: list = None,
    all_clients_details_for_popups: list = None, # Expects a list of client dicts with 'country_name', 'city', 'client_name', 'client_id'
    app_translator_func=lambda x: x, # Simple default translator
    map_interaction_handler_name: str = "pyMapConnector",
    initial_location=[20, 0],
    initial_zoom=2
):
    """
    Generates the HTML content for a Folium map with client distribution and popups.

    Args:
        geojson_path (str): Absolute path to the world_countries.geojson file.
        clients_by_country_counts (list, optional): List of dicts, e.g., [{'country_name': 'X', 'client_count': Y}].
                                                    If None, no choropleth for client counts is added.
        all_clients_details_for_popups (list, optional): Pre-fetched list of client details for popups.
                                                        Each dict should contain at least 'country_name', 'city',
                                                        'client_name', 'client_id'. If None, detailed client popups are limited.
        app_translator_func (function, optional): Translator function (e.g., self.tr). Defaults to identity.
        map_interaction_handler_name (str, optional): JS name for the QWebChannel object.
        initial_location (list, optional): Initial map center [lat, lon].
        initial_zoom (int, optional): Initial map zoom level.

    Returns:
        str: HTML content of the generated map, or None if a critical error occurs.
    """
    logging.info("map_utils.generate_folium_map_html: Starting map generation...")

    if not os.path.exists(geojson_path):
        logging.error(f"map_utils: GeoJSON file not found at: {geojson_path}")
        return None

    try:
        m = folium.Map(location=initial_location, zoom_start=initial_zoom, tiles="CartoDB positron")
        logging.info(f"map_utils: folium.Map object created: {m}")

        # Client Distribution Layer (Choropleth)
        if clients_by_country_counts:
            logging.info("map_utils: Adding client distribution GeoJson...")
            counts_dict = {item['country_name']: item['client_count'] for item in clients_by_country_counts}
            max_observed_clients = max(item['client_count'] for item in clients_by_country_counts) if clients_by_country_counts else 0
            # Ensure vmax is at least a small positive number if max_observed_clients is 0, to prevent StepColormap issues.
            vmax_for_colormap = max(4, max_observed_clients) # Min value of 4 for better color steps if counts are low

            category_colors = ['#f7f7f7', '#c6dbef', '#6baed6', '#08519c'] # Example: Light grey to dark blue
            # Adjust index based on expected data range and color steps desired
            # If max_observed_clients is very low (e.g., 0 or 1), this index might need dynamic adjustment or simplification
            color_index = [0, 1, 2, max(3, vmax_for_colormap // 2 if vmax_for_colormap > 4 else 2) ] # Simplified index logic

            client_colormap = StepColormap(
                colors=category_colors,
                index=color_index,
                vmin=0,
                vmax=vmax_for_colormap,
                caption=app_translator_func("Nombre de Clients par Pays (Catégories)")
            )

            def style_function(feature):
                count = counts_dict.get(feature['properties']['name'], 0)
                return {'fillColor': client_colormap(count), 'color': '#555555', 'weight': 0.5, 'fillOpacity': 0.7}

            folium.GeoJson(
                geojson_path,
                name=app_translator_func("Distribution des Clients par Pays"),
                style_function=style_function,
                tooltip=folium.features.GeoJsonTooltip(fields=['name'], aliases=[app_translator_func('Pays:')], localize=True)
            ).add_to(m)
            client_colormap.add_to(m)
            logging.info("map_utils: Client distribution GeoJson added.")
        else:
            logging.info("map_utils: No client count data. Adding basic GeoJSON layer.")
            folium.GeoJson(
                geojson_path,
                name=app_translator_func("Pays (Base)"),
                tooltip=folium.features.GeoJsonTooltip(fields=['name'], aliases=[app_translator_func('Pays:')])
            ).add_to(m)
            logging.info("map_utils: Basic GeoJSON layer added.")

        # Interactive Popup Layer
        logging.info("map_utils: Preparing popup GeoJson...")
        popup_layer_geojson_data = json.loads(open(geojson_path, 'r', encoding='utf-8').read())

        for feature in popup_layer_geojson_data.get('features', []):
            country_name_prop = feature.get('properties', {}).get('name', 'N/A')
            if country_name_prop == 'N/A':
                continue

            country_client_count = 0
            if clients_by_country_counts:
                country_client_count = next((item['client_count'] for item in clients_by_country_counts if item['country_name'] == country_name_prop), 0)

            popup_html = f"<b>{country_name_prop}</b><br>"
            popup_html += f"{app_translator_func('Clients (Total)')}: {country_client_count}<br><hr>"

            # Populate city and client details if data is provided
            # This part is simplified; direct DB access here is not ideal for a util function.
            # The caller should ideally prepare this data.
            # For now, keeping a simplified version if all_clients_details_for_popups is available.
            city_client_map = {}
            if all_clients_details_for_popups:
                clients_in_this_country = [
                    c for c in all_clients_details_for_popups if c.get('country_name', '').lower() == country_name_prop.lower()
                ]
                for client in clients_in_this_country:
                    city_name = client.get('city', app_translator_func('Ville Inconnue'))
                    client_detail_name = client.get('client_name', app_translator_func('Client Inconnu'))
                    client_id = client.get('client_id')
                    if city_name not in city_client_map:
                        city_client_map[city_name] = []
                    if len(city_client_map[city_name]) < 3: # Limit to 3 clients per city in popup
                        city_client_map[city_name].append({'id': client_id, 'name': client_detail_name})

            if city_client_map:
                for city_name_iter, clients_in_city_list in city_client_map.items():
                    popup_html += f"<b>{app_translator_func('Ville')}: {city_name_iter}</b> ({len(clients_in_city_list)} {app_translator_func('client(s) affiché(s)')})<br>"
                    popup_html += "<ul>"
                    for client_data_item in clients_in_city_list:
                        js_client_id_arg = json.dumps(str(client_data_item['id'])) # Ensure ID is string
                        js_client_name_arg = json.dumps(client_data_item['name'])
                        onclick_js = f"{map_interaction_handler_name}.clientClickedOnMap({js_client_id_arg}, {js_client_name_arg}); return false;"
                        popup_html += f"<li><a href='#' onclick=\"{onclick_js}\">{client_data_item['name']}</a></li>"
                    popup_html += "</ul>"
            else:
                popup_html += f"{app_translator_func('Aucun client détaillé à afficher pour les villes.')}<br>"

            js_country_name_arg = json.dumps(country_name_prop)
            button_text = app_translator_func('Ajouter Client Ici')
            onclick_country_js = f"{map_interaction_handler_name}.countryClicked({js_country_name_arg}); return false;"
            popup_html += f"<br><button onclick=\"{onclick_country_js}\">{button_text}</button>"

            # Store the generated HTML in the feature's properties for the GeoJsonPopup
            if 'properties' not in feature: feature['properties'] = {}
            feature['properties']['popup_content'] = popup_html

        # Create the GeoJson layer with the modified GeoJSON data
        folium.GeoJson(
            popup_layer_geojson_data,
            name=app_translator_func("Informations Pays"),
            style_function=lambda x: {'fillColor':'transparent', 'color':'transparent', 'weight':0}, # Invisible layer for popups
            tooltip=None, # No default tooltip for this layer
            popup=folium.features.GeoJsonPopup(fields=['popup_content'], localize=True) # Use 'popup_content'
        ).add_to(m)
        logging.info("map_utils: Popup GeoJson layer configured and added.")

        folium.LayerControl().add_to(m)

        logging.info("map_utils: Rendering map to HTML...")
        map_html_content = m.get_root().render()
        logging.info(f"map_utils: Map HTML rendered. Content length: {len(map_html_content) if map_html_content else 0}")

        # Add QWebChannel JavaScript
        webchannel_setup_js = f"""
        <script type="text/javascript" src="qrc:///qtwebchannel/qwebchannel.js"></script>
        <script type="text/javascript">
            document.addEventListener("DOMContentLoaded", function() {{
                if (typeof QWebChannel !== 'undefined') {{
                    new QWebChannel(qt.webChannelTransport, function(channel) {{
                        window.{map_interaction_handler_name} = channel.objects.{map_interaction_handler_name};
                        if (window.{map_interaction_handler_name} === undefined) {{
                            console.error("{map_interaction_handler_name} object not found. Available:", Object.keys(channel.objects));
                        }} else {{
                            console.log("{map_interaction_handler_name} initialized successfully via WebChannel.");
                        }}
                    }});
                }} else {{
                    console.error("QWebChannel JavaScript library not loaded.");
                }}
            }});
        </script>
        """
        if "</body>" in map_html_content:
            map_html_content = map_html_content.replace("</body>", webchannel_setup_js + "</body>", 1)
        elif "</html>" in map_html_content: # Fallback if no body tag
            map_html_content = map_html_content.replace("</html>", webchannel_setup_js + "</html>", 1)
        else: # Fallback if no body or html tag
            map_html_content += webchannel_setup_js

        logging.info("map_utils: WebChannel JavaScript added to HTML content.")
        return map_html_content

    except Exception as e:
        logging.error(f"map_utils: General error generating Folium map HTML: {e}", exc_info=True)
        return None
