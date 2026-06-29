"""Vercel serverless entry for the FastAPI backend."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND_ROOT = ROOT / "backend"
GRAPH_PATH = BACKEND_ROOT / "app" / "data" / "road_graph.hcm-v2-uw.json"

sys.path.insert(0, str(BACKEND_ROOT))
os.environ.setdefault("ROAD_FINDER_GRAPH_PATH", str(GRAPH_PATH))

from app.application.graph_runtime import build_graph_runtime
from app.main import create_app

app = create_app()
app.state.graph_runtime = build_graph_runtime(Path(os.environ["ROAD_FINDER_GRAPH_PATH"]))