"""Surface Diff dashboard plugin — backend API routes.

Mounted at /api/plugins/surface/ by the dashboard plugin system
(hermes_cli.web_server._mount_plugin_api_routes). Backs the desktop app's
Surface Diff plugin (apps/desktop/src/plugins/surface/): a read-only
browser over the snapshots hermes_cli/surface_state.py already maintains,
and the diff between the two most recent ones for a target.

Read-only by design: every handler wraps an existing hermes_cli.surface_*
read function. Taking a new snapshot stays a CLI action
('indagis surface snapshot').
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from hermes_cli.surface_probe import diff_snapshots
from hermes_cli.surface_state import latest_two_snapshots, list_snapshots, list_targets, load_snapshot

router = APIRouter()


@router.get("/targets")
def targets() -> dict:
    return {"targets": [{"name": t, "snapshot_count": len(list_snapshots(t))} for t in list_targets()]}


@router.get("/snapshots")
def snapshots(target: str = Query(..., min_length=1)) -> dict:
    paths = list_snapshots(target)
    entries = []
    for path in paths:
        snapshot = load_snapshot(path)
        entries.append({"filename": path.name, "taken_at": (snapshot or {}).get("taken_at")})
    return {"snapshots": entries}


@router.get("/diff")
def diff(target: str = Query(..., min_length=1)) -> dict:
    if target not in list_targets():
        raise HTTPException(status_code=404, detail=f"Unknown target: {target!r}")

    pair = latest_two_snapshots(target)
    if pair is None:
        return {"available": False, "changes": [], "older_taken_at": None, "newer_taken_at": None}

    older, newer = pair
    return {
        "available": True,
        "changes": diff_snapshots(older, newer),
        "older_taken_at": older.get("taken_at"),
        "newer_taken_at": newer.get("taken_at"),
    }
