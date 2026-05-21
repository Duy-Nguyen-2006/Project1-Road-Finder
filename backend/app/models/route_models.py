from pydantic import BaseModel

from app.models.point import Point


class OptimizeRouteRequest(BaseModel):
    points: list[Point]


class OptimizeRouteResponse(BaseModel):
    ordered_points: list[Point]


# Example:
#
# Frontend sends this request to backend:
# {
#     "points": [
#         {
#             "latitude": 10.762622,
#             "longitude": 106.660172
#         },
#         {
#             "latitude": 10.776889,
#             "longitude": 106.700806
#         },
#         {
#             "latitude": 10.779783,
#             "longitude": 106.699018
#         }
#     ]
# }
#
# Backend returns this response to frontend:
# {
#     "ordered_points": [
#         {
#             "latitude": 10.762622,
#             "longitude": 106.660172
#         },
#         {
#             "latitude": 10.779783,
#             "longitude": 106.699018
#         },
#         {
#             "latitude": 10.776889,
#             "longitude": 106.700806
#         }
#     ]
# }
