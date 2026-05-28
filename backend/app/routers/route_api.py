from fastapi import APIRouter

from app.models.route_models import OptimizeRouteRequest, OptimizeRouteResponse
from app.services.tsp_service import optimize_points
from app.services.osm_service import fetch_intersections_in_city

router = APIRouter()

# Global module-level memory cache for real-world OSM intersection nodes
_intersections_cache = None


def get_cached_intersections():
    """
    Retrieve or initialize the cached list of OSM intersection nodes.
    Caches Ho Chi Minh City intersections (with core urban bounding box)
    to prevent slow, rate-limited public API queries on every route request.
    """
    global _intersections_cache
    if _intersections_cache is None:
        try:
            # Default bounding box for Ho Chi Minh City core urban area (matches frontend)
            bbox_tuple = (10.70, 106.60, 10.85, 106.80)
            print("Initializing backend intersections cache from OpenStreetMap Overpass API...")
            _intersections_cache = fetch_intersections_in_city("Ho Chi Minh City", bbox_tuple)
            print(f"Successfully cached {len(_intersections_cache)} intersections.")
        except Exception as e:
            print(f"Warning: Failed to fetch intersections for cache: {e}")
            _intersections_cache = []
    return _intersections_cache


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/optimize-route")
def optimize_route(data_from_fe: OptimizeRouteRequest) -> OptimizeRouteResponse:
    # Snap the input coordinates to the closest real-world intersection nodes,
    # then run the custom Branch & Bound TSP solver on the snapped coordinates.
    intersections = get_cached_intersections()
    route_result = optimize_points(data_from_fe.points, intersections)

    return OptimizeRouteResponse(ordered_points=route_result)


@router.get("/intersections")
def get_intersections(city_name: str = "Ho Chi Minh City", bbox: str = None) -> dict:
    """
    Fetch all intersections (ngã tư, ngã ba) from OpenStreetMap for a given city.
    Returns a list of points with latitude and longitude.
    
    Query params:
    - city_name: Name of the city (default: Ho Chi Minh City)
    - bbox: Optional bounding box as "min_lat,min_lon,max_lat,max_lon"
    """
    bbox_tuple = None
    if bbox:
        try:
            parts = bbox.split(',')
            bbox_tuple = tuple(float(x) for x in parts)
        except (ValueError, IndexError):
            return {"error": "Invalid bbox format. Use: min_lat,min_lon,max_lat,max_lon"}
            
    # If the requested query matches the cached region, return from cache directly
    if not bbox and city_name == "Ho Chi Minh City":
        cached = get_cached_intersections()
        if cached:
            return {"intersections": cached}
            
    intersections = fetch_intersections_in_city(city_name, bbox_tuple)
    return {"intersections": intersections}
