ACCEPTED_AREA_DETAIL = "Error: Not in accepted area"
NO_ROUTE_DETAIL = "No route found between selected points"


class AcceptedAreaError(Exception):
    """Point is outside accepted bbox or beyond max snap distance."""

    def __init__(self, message: str = ACCEPTED_AREA_DETAIL) -> None:
        super().__init__(message)


class NoRouteError(Exception):
    """Snapped start and end lie in disconnected graph components."""

    def __init__(self, message: str = NO_ROUTE_DETAIL) -> None:
        super().__init__(message)
