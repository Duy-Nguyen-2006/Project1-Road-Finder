ACCEPTED_AREA_DETAIL = "Error: Not in accepted area"


class AcceptedAreaError(Exception):
    """Point is outside accepted bbox or beyond max snap distance."""

    def __init__(self, message: str = ACCEPTED_AREA_DETAIL) -> None:
        super().__init__(message)
