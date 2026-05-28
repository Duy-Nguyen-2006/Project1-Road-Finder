from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.route_api import router as route_router


def create_app() -> FastAPI:
    app = FastAPI(title="Road Finder API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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
