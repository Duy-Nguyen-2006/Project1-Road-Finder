from pydantic import BaseModel

# pydantic to validate data
# Example data from frontend:
# {
#     "latitude": 10.762622,
#     "longitude": 106.660172
# }
class Point(BaseModel):

    latitude: float
    longitude: float
