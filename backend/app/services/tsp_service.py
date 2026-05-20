from app.models.point import Point


def optimize_points(points: list[Point]) -> list[Point]:
    """
    Receive map points and return them in route order.

    First version:
        Return the same points without changing the order.

    Later version:
        Use distance calculation and OR-Tools to find a better order.
    """
    return points


# Example:
#
# Receive:
# [
#     Point(latitude=10.762622, longitude=106.660172),
#     Point(latitude=10.776889, longitude=106.700806),
# ]
#
# Return in first version:
# [
#     Point(latitude=10.762622, longitude=106.660172),
#     Point(latitude=10.776889, longitude=106.700806),
# ]
