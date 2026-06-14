"""Backward-compatible re-exports; use app.application.snap_service instead."""

from app.application.snap_service import SnapResult, snap_point

__all__ = ["SnapResult", "snap_point"]
