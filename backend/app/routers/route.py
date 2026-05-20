from fastapi import APIRouter

from app.models.route import OptimizeRouteRequest, OptimizeRouteResponse
from app.services.tsp_service import optimize_points


router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/optimize-route")
def optimize_route(data_from_fe: OptimizeRouteRequest) -> OptimizeRouteResponse:
    route_result = optimize_points(data_from_fe.points)

    return OptimizeRouteResponse(ordered_points=route_result)


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
