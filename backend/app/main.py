import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.application.graph_runtime import build_graph_runtime
from app.infrastructure.graph_loader import DEFAULT_GRAPH_PATH
from app.routers.route_api import router as route_router


def _graph_path_from_env() -> Path:
    override = os.environ.get("ROAD_FINDER_GRAPH_PATH")
    if override:
        return Path(override)
    return DEFAULT_GRAPH_PATH


@asynccontextmanager
async def _lifespan(app: FastAPI):
    app.state.graph_runtime = build_graph_runtime(_graph_path_from_env())
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Road Finder API", lifespan=_lifespan)

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
