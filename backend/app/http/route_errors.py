from fastapi import HTTPException

from app.domain.errors import (
    ACCEPTED_AREA_DETAIL,
    NO_ROUTE_DETAIL,
    AcceptedAreaError,
    NoRouteError,
)


def http_exception_for_domain_error(error: Exception) -> HTTPException:
    if isinstance(error, AcceptedAreaError):
        return HTTPException(status_code=422, detail=ACCEPTED_AREA_DETAIL)
    if isinstance(error, NoRouteError):
        return HTTPException(status_code=404, detail=NO_ROUTE_DETAIL)
    raise error
