# -*- coding: utf-8 -*-
import logging
import os
import json
import folium
from branca.colormap import StepColormap

# It's better to get country details like coordinates from the geojson data if possible,
# or pass them explicitly.
# For now, assuming geojson has 'iso_a2' and 'name' properties.

def _calculate_bounds_from_geometry(geometry: dict):
    """
    Calculates the bounding box [[min_lat, min_lon], [max_lat, max_lon]]
    from a GeoJSON geometry. Returns None if bounds cannot be determined.
    """
    if not geometry or 'type' not in geometry or 'coordinates' not in geometry:
        return None

    coords_list = []
    geom_type = geometry['type']
    raw_coords = geometry['coordinates']

    if geom_type == 'Point':
        # For a point, fit_bounds might not work well without a small area.
        # We can return a small box around the point or let caller handle fixed zoom.
        # For now, let's return a very small bounding box.
        lon, lat = raw_coords
        delta = 0.001 # A small delta to create a tiny box
        return [[lat - delta, lon - delta], [lat + delta, lon + delta]]
    elif geom_type == 'Polygon':
        # raw_coords is a list of linear rings (first is exterior)
        # A linear ring is a list of [lon, lat] points
        for ring in raw_coords:
            for lon, lat in ring:
                coords_list.append((lon, lat))
    elif geom_type == 'MultiPolygon':
        # raw_coords is a list of Polygons
        # Each Polygon is a list of linear rings
        for polygon in raw_coords:
            for ring in polygon:
                for lon, lat in ring:
                    coords_list.append((lon, lat))
    else:
        # Other types like LineString, MultiLineString, GeometryCollection not handled for simplicity
        logging.warning(f"map_utils: Bounding box calculation not implemented for geometry type: {geom_type}")
        return None

    if not coords_list:
        return None

    min_lon = min(c[0] for c in coords_list)
    max_lon = max(c[0] for c in coords_list)
    min_lat = min(c[1] for c in coords_list)
    max_lat = max(c[1] for c in coords_list)

    # Folium fit_bounds expects [[south, west], [north, east]] which is [[min_lat, min_lon], [max_lat, max_lon]]
    return [[min_lat, min_lon], [max_lat, max_lon]]


def generate_folium_map_html(
    geojson_path: str,
    clients_by_country_counts: list = None,
    all_clients_details_for_popups: list = None, # Expects a list of client dicts with 'country_name', 'city', 'client_name', 'client_id'
    app_translator_func=lambda x: x, # Simple default translator
    map_interaction_handler_name: str = "pyMapConnector",
    initial_location=[20, 0], # Default global view
    initial_zoom=2,           # Default global zoom
    focused_country_iso_a2: str = None, # New parameter
    scope: str = "international", # New parameter
    map_bounds=None
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
        initial_location (list, optional): Default initial map center [lat, lon] if no focus country.
        initial_zoom (int, optional): Default initial map zoom level if no focus country.
        focused_country_iso_a2 (str, optional): ISO A2 code of the country to focus on.
                                                If provided, map will center on this country.

    Returns:
        str: HTML content of the generated map, or None if a critical error occurs.
    """
    logging.info(f"map_utils.generate_folium_map_html: Starting map generation. Focus: {focused_country_iso_a2}, Scope: {scope}")

    if not os.path.exists(geojson_path):
        logging.error(f"map_utils: GeoJSON file not found at: {geojson_path}")
        return None

    map_location = initial_location
    map_zoom = initial_zoom
    geojson_data = None

    try:
        with open(geojson_path, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
    except Exception as e:
        logging.error(f"map_utils: Error reading or parsing GeoJSON file: {e}", exc_info=True)
        return None

    if focused_country_iso_a2 and geojson_data:
        focused_feature = None
        for feature in geojson_data.get('features', []):
            # Assuming 'iso_a2' or 'ISO_A2' might be the property name in GeoJSON
            if feature.get('properties', {}).get('iso_a2', '').lower() == focused_country_iso_a2.lower() or \
               feature.get('properties', {}).get('ISO_A2', '').lower() == focused_country_iso_a2.lower():
                focused_feature = feature
                break

        if focused_feature:
            try:
                # Attempt to find centroid or a representative point from geometry
                # This is a simplified approach; proper centroid calculation can be complex.
                # Using the first coordinate of the first polygon/multipolygon.
                geom_type = focused_feature.get('geometry', {}).get('type')
                coords = focused_feature.get('geometry', {}).get('coordinates')

                if geom_type == 'Polygon':
                    # For Polygon, coords is list of linear rings, first is exterior.
                    # Taking the first point of the exterior ring.
                    map_location = [coords[0][0][1], coords[0][0][0]] # [lat, lon]
                elif geom_type == 'MultiPolygon':
                    # For MultiPolygon, coords is list of Polygons.
                    # Taking the first point of the first exterior ring of the first polygon.
                    map_location = [coords[0][0][0][1], coords[0][0][0][0]] # [lat, lon]
                elif geom_type == 'Point':
                    map_location = [coords[1], coords[0]] # [lat, lon] for Point

                map_zoom = 5 # Zoom in more for a focused country
                logging.info(f"map_utils: Focusing on {focused_country_iso_a2}. New location: {map_location}, zoom: {map_zoom}")
            except Exception as e_centroid:
                logging.warning(f"map_utils: Could not determine center for {focused_country_iso_a2} from GeoJSON: {e_centroid}. Using default view.", exc_info=True)
        else:
            logging.warning(f"map_utils: Country with ISO A2 '{focused_country_iso_a2}' not found in GeoJSON. Using default view.")


    try:

        m = folium.Map(location=map_location, zoom_start=map_zoom, tiles="CartoDB positron", no_wrap=True, attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>')
        logging.info(f"map_utils: folium.Map object created: {m}")

        # Client Distribution Layer (Choropleth)
        if clients_by_country_counts:
            logging.info("map_utils: Adding client distribution GeoJson...")
            counts_dict = {item['country_name']: item['client_count'] for item in clients_by_country_counts}
            max_observed_clients = max(item['client_count'] for item in clients_by_country_counts) if clients_by_country_counts else 0
            vmax_for_colormap = max(4, max_observed_clients)

            category_colors = ['#f7f7f7', '#c6dbef', '#6baed6', '#08519c']
            color_index = [0, 1, 2, max(3, vmax_for_colormap // 2 if vmax_for_colormap > 4 else 2) ]

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
                geojson_data, # Use pre-loaded geojson_data
                name=app_translator_func("Distribution des Clients par Pays"),
                style_function=style_function,
                tooltip=folium.features.GeoJsonTooltip(fields=['name'], aliases=[app_translator_func('Pays:')], localize=True)
            ).add_to(m)
            client_colormap.add_to(m)
            logging.info("map_utils: Client distribution GeoJson added.")
        else:
            logging.info("map_utils: No client count data. Adding basic GeoJSON layer.")
            folium.GeoJson(
                geojson_data, # Use pre-loaded geojson_data
                name=app_translator_func("Pays (Base)"),
                tooltip=folium.features.GeoJsonTooltip(fields=['name'], aliases=[app_translator_func('Pays:')])
            ).add_to(m)
            logging.info("map_utils: Basic GeoJSON layer added.")

        # Interactive Popup Layer
        logging.info("map_utils: Preparing popup GeoJson...")
        # Create a deep copy for modification if necessary, or ensure properties are mutable
        # For this use case, directly modifying 'properties' of features in geojson_data is fine
        # as it's loaded fresh each call.

        for feature in geojson_data.get('features', []):
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
            button_text = app_translator_func('Détails Pays / Ajouter Client') # Changed button text for clarity
            onclick_country_js = f"{map_interaction_handler_name}.countryClicked({js_country_name_arg}); return false;"
            popup_html += f"<br><button onclick=\"{onclick_country_js}\">{button_text}</button>"

            if 'properties' not in feature: feature['properties'] = {}
            feature['properties']['popup_content'] = popup_html

        folium.GeoJson(
            geojson_data, # Use the modified geojson_data
            name=app_translator_func("Informations Pays"),
            style_function=lambda x: {'fillColor':'transparent', 'color':'transparent', 'weight':0},
            tooltip=None,
            popup=folium.features.GeoJsonPopup(fields=['popup_content'], localize=True)
        ).add_to(m)
        logging.info("map_utils: Popup GeoJson layer configured and added.")

        folium.LayerControl().add_to(m)

        logging.info("map_utils: Rendering map to HTML...")
        map_html_content = m.get_root().render()
        logging.info(f"map_utils: Map HTML rendered. Content length: {len(map_html_content) if map_html_content else 0}")

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

                            // The moveend event listener has been removed to prevent crashes.
                            // The map's last position will not be saved.
                        }}
                    }});
                }} else {{
                    console.error("QWebChannel JavaScript library not loaded.");
                }}
            }});
        </script>
        """
        if map_bounds:
            m.fit_bounds(map_bounds)

        if "</body>" in map_html_content:
            map_html_content = map_html_content.replace("</body>", webchannel_setup_js + "</body>", 1)
        elif "</html>" in map_html_content:
            map_html_content = map_html_content.replace("</html>", webchannel_setup_js + "</html>", 1)
        else:
            map_html_content += webchannel_setup_js

        logging.info("map_utils: WebChannel JavaScript added to HTML content.")

        # For debugging, save the HTML to a file
        with open("map.html", "w", encoding="utf-8") as f:
            f.write(map_html_content)

        return map_html_content

    except Exception as e:
        logging.error(f"map_utils: General error generating Folium map HTML: {e}", exc_info=True)
        return None
