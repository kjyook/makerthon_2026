import requests
import json
from typing import List, Dict, Any

def fetch_osm_buildings(bbox: tuple) -> List[Dict[str, Any]]:
    """
    Fetch building data from OSM within a bounding box using Overpass API.
    bbox: (south, west, north, east)
    """
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    # south, west, north, east
    s, w, n, e = bbox
    
    overpass_query = f"""
    [out:json][timeout:25];
    (
      way["building"]({s},{w},{n},{e});
      relation["building"]({s},{w},{n},{e});
    );
    out body;
    >;
    out skel qt;
    """
    
    headers = {
        'User-Agent': 'Makerthon_Project_User/1.0',
        'Accept': 'application/json'
    }
    response = requests.post(overpass_url, data={'data': overpass_query}, headers=headers)
    try:
        data = response.json()
    except Exception as e:
        print(f"Error parsing Overpass JSON: {e}")
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text[:500]}")
        raise e
    
    # Group elements by type
    nodes = {node['id']: (node['lon'], node['lat']) for node in data['elements'] if node['type'] == 'node'}
    ways = [el for el in data['elements'] if el['type'] == 'way' and 'tags' in el]
    
    buildings = []
    for way in ways:
        # Determine building height
        try:
            raw_height = way['tags'].get('height')
            if raw_height:
                # Remove 'm' if present
                height = float(raw_height.replace('m', '').replace(' ', ''))
            else:
                levels = float(way['tags'].get('building:levels', 3))
                height = levels * 3.5
        except (ValueError, TypeError):
            height = 15.0 # Default fallback
            
        building_info = {
            'id': way['id'],
            'nodes': [nodes[node_id] for node_id in way['nodes'] if node_id in nodes],
            'tags': way['tags'],
            'height': height
        }
        buildings.append(building_info)
        
    return buildings

if __name__ == "__main__":
    # Test bbox for Songdo Central Park area
    test_bbox = (37.387, 126.63, 37.402, 126.647)
    buildings = fetch_osm_buildings(test_bbox)
    print(f"Fetched {len(buildings)} buildings.")
    if buildings:
        print(f"Sample building height: {buildings[0]['height']}m")
