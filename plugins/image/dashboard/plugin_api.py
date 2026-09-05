"""Image Intel dashboard plugin — backend API routes.

Mounted at /api/plugins/image/ by the dashboard plugin system
(hermes_cli.web_server._mount_plugin_api_routes). Backs the desktop app's
Image Intel plugin (apps/desktop/src/plugins/image/): a read-only view of
the photographs an investigation has already recorded.

WHAT THIS DELIBERATELY DOES NOT EXPOSE — the constraint that shapes the
whole module. The CLI's headline verb is 'indagis image inspect <path>',
which reads EXIF out of an arbitrary file. That is correct for a command
an operator types, and it would be an arbitrary-file-read primitive over
HTTP: a client could point it at any picture on the machine and read back
the owner's camera serials and home coordinates. So inspect_image() is NOT
wrapped here, at any path, under any parameter. Neither is scrub_image(),
which writes.

What is exposed instead is the *already-collected* side: images an
operator themselves put into a case with 'indagis image inspect <file>
--evidence <store>'. Those live in evidence stores case memory has
recorded, and reading them back adds no reach the operator did not
already grant.

PATH ALLOWLIST. The store a client names is still client-supplied, so it
gets the same treatment as the Dossier Builder router: resolved against
hermes_cli.case_memory_state.list_investigations(), whose store_path
values are paths the operator pointed the CLI at via 'indagis case
ingest'. Comparison is on the resolved real path, so '..' segments and
symlinks cannot walk out of the allowlist, and the recorded string — not
the caller's — is what gets opened.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from hermes_cli.case_memory_state import list_investigations
from hermes_cli.image_intel import collect_store_images

router = APIRouter()


def _resolve_allowed(store_path: str) -> str:
    """Return the recorded store_path matching ``store_path``, or 404.

    Matching is done on the resolved real path so that '..' segments and
    symlinks cannot be used to reach a file that is not on the allowlist.
    The recorded string (not the caller's) is what gets opened.
    """
    try:
        requested = Path(store_path).resolve()
    except (OSError, RuntimeError):
        raise HTTPException(status_code=400, detail="Malformed store path") from None

    for entry in list_investigations():
        recorded = entry.get("store_path")
        if not recorded:
            continue
        try:
            if Path(recorded).resolve() == requested:
                return recorded
        except (OSError, RuntimeError):
            continue

    raise HTTPException(
        status_code=404,
        detail=(
            "Unknown evidence store. Only stores already ingested with "
            "'indagis case ingest' can be read here."
        ),
    )


@router.get("/investigations")
def investigations() -> dict:
    """The picker: every evidence store case memory knows about."""
    records = []
    for entry in list_investigations():
        store_path = entry.get("store_path") or ""
        records.append({**entry, "exists": bool(store_path) and os.path.isfile(store_path)})
    return {"investigations": records}


@router.get("/images")
def images(
    store_path: str = Query(..., description="Path of an already-ingested evidence store"),
) -> dict:
    """Photographs recorded in one allowlisted store, newest first."""
    allowed = _resolve_allowed(store_path)
    try:
        entries = collect_store_images(allowed)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Evidence store file is missing on disk") from None
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None

    located = sum(1 for entry in entries if entry.get("gps"))

    return {
        "store_path": allowed,
        "images": entries,
        # Two figures the panel leads with, computed here so the UI does not
        # re-derive them and drift from the listing it sits above.
        "total": len(entries),
        "geolocated": located,
    }
