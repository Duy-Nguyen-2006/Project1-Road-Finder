from fastapi import APIRouter

from app.models.route_models import OptimizeRouteRequest, OptimizeRouteResponse
from app.services.tsp_service import optimize_points
from app.services.osm_service import fetch_intersections_in_city

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/optimize-route")
def optimize_route(data_from_fe: OptimizeRouteRequest) -> OptimizeRouteResponse:
    route_result = optimize_points(data_from_fe.points)

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
    
    intersections = fetch_intersections_in_city(city_name, bbox_tuple)
    return {"intersections": intersections}


# Example:
#
# GET /health
# Return:
# {
#     "status": "ok"
# }
#
# POST /optimize-route
# Receive:
# {
#     "points": [
#         {
#             "latitude": 10.762622,
#             "longitude": 106.660172
#         },
#         {
#             "latitude": 10.776889,
#             "longitude": 106.700806
#         }
#     ]
# }
#
# Return:
# {
#     "ordered_points": [
#         {
#             "latitude": 10.762622,
#             "longitude": 106.660172
#         },
#         {
#             "latitude": 10.776889,
#             "longitude": 106.700806
#         }
#     ]
# }
