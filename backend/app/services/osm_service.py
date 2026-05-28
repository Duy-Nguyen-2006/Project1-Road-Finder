import requests
from typing import List, Dict, Any


def fetch_intersections_in_city(city_name: str = "Ho Chi Minh City", bbox: tuple = None) -> List[Dict[str, float]]:
    """
    Fetch all intersections (ngã tư - 4-way, ngã ba - 3-way) from OpenStreetMap for a given city.
    
    Uses Overpass API to query highway junctions with traffic signals or stop signs.
    Returns a list of points with latitude and longitude.
    
    Args:
        city_name: Name of the city to search in
        bbox: Optional bounding box (min_lat, min_lon, max_lat, max_lon) to limit search area
    """
    
    # Overpass API endpoint
    overpass_url = "https://overpass-api.de/api/interpreter"
    
    # Headers to avoid 406 error
    headers = {
        'User-Agent': 'RoadFinder/1.0',
        'Accept': 'application/json'
    }
    
    # If bbox is provided, use it directly; otherwise search by city name
    if bbox:
        min_lat, min_lon, max_lat, max_lon = bbox
        query = f"""
        [out:json][timeout:60];
        (
          node["highway"="traffic_signals"]({min_lat},{min_lon},{max_lat},{max_lon});
          node["highway"="stop"]({min_lat},{min_lon},{max_lat},{max_lon});
          node["junction"="yes"]({min_lat},{min_lon},{max_lat},{max_lon});
        );
        out center;
        """
    else:
        # Search by city name using area
        query = f"""
        [out:json][timeout:60];
        area["name"="{city_name}"]->.searchArea;
        (
          node["highway"="traffic_signals"](area.searchArea);
          node["highway"="stop"](area.searchArea);
          node["junction"="yes"](area.searchArea);
        );
        out center;
        """
    
    try:
        response = requests.post(overpass_url, data={'data': query}, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        intersections = []
        seen_coords = set()
        
        for element in data.get('elements', []):
            if element.get('type') == 'node':
                lat = element.get('lat')
                lon = element.get('lon')
                
                if lat and lon:
                    # Avoid duplicates by rounding coordinates
                    coord_key = (round(lat, 5), round(lon, 5))
                    if coord_key not in seen_coords:
                        seen_coords.add(coord_key)
                        intersections.append({
                            'latitude': lat,
                            'longitude': lon
                        })
        
        return intersections
        
    except requests.RequestException as e:
        print(f"Error fetching intersections: {e}")
        return []
