from fastapi import HTTPException

from app.domain.errors import AcceptedAreaError, NoRouteError
from app.http.route_errors import http_exception_for_domain_error


def test_maps_accepted_area_to_422_detail():
    exc = http_exception_for_domain_error(AcceptedAreaError())
    assert isinstance(exc, HTTPException)
    assert exc.status_code == 422
    assert exc.detail == "Error: Not in accepted area"


def test_maps_no_route_to_404_detail():
    exc = http_exception_for_domain_error(NoRouteError())
    assert isinstance(exc, HTTPException)
    assert exc.status_code == 404
    assert exc.detail == "No route found between selected points"
