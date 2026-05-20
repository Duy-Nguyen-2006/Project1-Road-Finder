from fastapi import FastAPI

from app.routers.route import router as route_router


def create_app() -> FastAPI:
    app = FastAPI(title="Road Finder API")

    app.include_router(route_router)

    return app


app = create_app()


# Example:
#
# Uvicorn will use this app object to run the backend server.
#
# Run command later:
# uvicorn app.main:app --reload
#
# After the server runs, frontend can call:
# GET /health
# POST /optimize-route
