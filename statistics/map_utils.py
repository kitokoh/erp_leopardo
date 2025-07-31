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
    Generates a very basic Folium map for debugging purposes.
    """
    logging.info("map_utils.generate_folium_map_html: Generating a BASIC debug map.")
    try:
        # Create a simple map centered on a default location.
        m = folium.Map(location=[48.8566, 2.3522], zoom_start=5, tiles="CartoDB positron")

        # Add a single marker to confirm something is visible.
        folium.Marker(
            [48.8566, 2.3522], popup="<i>Paris</i>"
        ).add_to(m)

        # Return the raw HTML of the simple map. No JS injection.
        map_html_content = m.get_root().render()
        logging.info("map_utils: Basic debug map HTML generated.")
        return map_html_content

    except Exception as e:
        logging.error(f"map_utils: Error generating BASIC debug map: {e}", exc_info=True)
        return "<html><body><h1>Failed to generate basic map</h1></body></html>"
