#!/usr/bin/env python3
"""Offline Ho Chi Minh City road graph generator scaffold.

This script is intentionally separate from backend runtime. It documents the
approved generation workflow and can emit SPEC-shaped JSON to a temp/output
path for review. Backend startup must not import osmnx or networkx.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
DEFAULT_OUTPUT = REPO_ROOT / "backend" / "app" / "data" / "road_graph.generated.json"
MAX_OUTPUT_BYTES = 50 * 1024 * 1024

# Approved offline source expectation (do not download in scaffold dry-run).
GEOFABRIK_SOURCE_URL = "https://download.geofabrik.de/asia/vietnam-latest.osm.pbf"
GEOFABRIK_SNAPSHOT_NOTE = (
    "Pin the downloaded PBF snapshot date in commit notes when generating a real graph."
)

# MVP highway filters for drivable urban roads.
HIGHWAY_ALLOWLIST = (
    "motorway",
    "trunk",
    "primary",
    "secondary",
    "tertiary",
    "unclassified",
    "residential",
    "living_street",
    "service",
)

DEFAULT_GRAPH_VERSION = "hcm-v1"
DEFAULT_BBOX = {
    "min_latitude": 10.70,
    "min_longitude": 106.60,
    "max_latitude": 10.90,
    "max_longitude": 106.90,
}
DEFAULT_MAX_SNAP_DISTANCE_METERS = 200


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="SPEC-shaped JSON output path (default: backend/app/data/road_graph.generated.json)",
    )
    parser.add_argument(
        "--graph-version",
        default=DEFAULT_GRAPH_VERSION,
        help="Value written to metadata.graph_version",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print generation plan and schema rules without downloading OSM or writing output",
    )
    parser.add_argument(
        "--emit-sample",
        action="store_true",
        help="Write a tiny SPEC-shaped sample graph for schema/size smoke checks",
    )
    return parser


def sample_graph_payload(graph_version: str) -> dict:
    return {
        "metadata": {
            "graph_version": graph_version,
            "bbox": DEFAULT_BBOX,
            "max_snap_distance_meters": DEFAULT_MAX_SNAP_DISTANCE_METERS,
        },
        "nodes": {
            "sample-a": {"latitude": 10.778109, "longitude": 106.714456},
            "sample-b": {"latitude": 10.7792, "longitude": 106.7155},
        },
        "edges": [
            {"from": "sample-a", "to": "sample-b", "distance": 120.5},
        ],
    }


def resolve_safe_output_path(output: Path) -> Path:
    resolved = output.expanduser().resolve()
    repo_root = REPO_ROOT.resolve()
    if not resolved.is_relative_to(repo_root):
        raise SystemExit(
            f"Output path must stay inside the repository root: {resolved}"
        )
    return resolved


def validate_output_size(path: Path) -> None:
    size = path.stat().st_size
    if size >= MAX_OUTPUT_BYTES:
        raise SystemExit(
            f"Generated graph exceeds 50MB target: {size} bytes at {path}"
        )


def print_generation_plan() -> None:
    print("Offline HCM graph generator scaffold")
    print(f"Geofabrik source: {GEOFABRIK_SOURCE_URL}")
    print(f"Snapshot policy: {GEOFABRIK_SNAPSHOT_NOTE}")
    print(f"Highway allowlist: {', '.join(HIGHWAY_ALLOWLIST)}")
    print(f"graph_version default: {DEFAULT_GRAPH_VERSION}")
    print("Output schema: metadata + nodes(object) + edges(array)")
    print(f"Size validation: output must be < {MAX_OUTPUT_BYTES} bytes")
    print("Runtime packages (generator-only): osmnx, networkx")
    print("Planned flow:")
    print("  1. Download/clip Vietnam PBF to HCM bbox")
    print("  2. Build drivable graph with highway filters")
    print("  3. Export nodes keyed by ID and positive-distance edges")
    print("  4. Validate SPEC schema and size before replacing road_graph.json")


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    if args.dry_run:
        print_generation_plan()
        return 0

    if not args.emit_sample:
        print_generation_plan()
        print(
            "\nFull generation is not implemented in this scaffold. "
            "Use --emit-sample for schema smoke output or extend this script "
            "with osmnx/networkx in an offline environment."
        )
        return 2

    payload = sample_graph_payload(args.graph_version)
    output_path = resolve_safe_output_path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    validate_output_size(output_path)

    sys.path.insert(0, str(BACKEND_ROOT))
    from app.infrastructure.graph_loader import load_graph_data

    load_graph_data(output_path)
    print(f"Wrote SPEC-shaped sample graph to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
