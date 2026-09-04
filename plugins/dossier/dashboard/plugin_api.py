"""Dossier Builder dashboard plugin — backend API routes.

Mounted at /api/plugins/dossier/ by the dashboard plugin system
(hermes_cli.web_server._mount_plugin_api_routes). Backs the desktop app's
Dossier Builder plugin (apps/desktop/src/plugins/dossier/): a preview of
the Markdown dossier 'indagis dossier build' renders from an evidence
store.

Read-only by design. build_dossier() is a pure function — it reads an
evidence store and returns Markdown, writing nothing; the writing variant
(dossier_build, with its --out path) is deliberately NOT wrapped here, so
producing a dossier file on disk stays a CLI action
('indagis dossier build <store> --out <path>').

PATH ALLOWLIST — the security constraint that shapes this module.
'indagis dossier build' takes an arbitrary filesystem path, which is fine
for a CLI the operator types into but would be an arbitrary-file-read
primitive over HTTP: _load_evidence_store() opens whatever path it is
given, and any JSON file on disk carrying an 'evidence' array would be
rendered straight into the response.

So this router never passes a client-supplied path through. It resolves
the requested store against the investigations case memory has already
recorded (hermes_cli.case_memory_state.list_investigations(), whose
store_path values are paths the operator themselves pointed the CLI at via
'indagis case ingest'), and refuses anything not on that list. Comparison
is on the resolved real path, so '..' segments and symlinks cannot walk
out of the allowlist.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from hermes_cli.case_memory_state import list_investigations
from hermes_cli.dossier import build_dossier

router = APIRouter()


def _resolve_allowed(store_path: str) -> str:
    """Return the recorded store_path matching ``store_path``, or 404.

    Matching is done on the resolved real path so that '..' segments and
    symlinks cannot be used to reach a file that is not on the allowlist.
    The recorded string (not the caller's) is what gets handed to
    build_dossier().
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
            "'indagis case ingest' can be previewed here."
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


@router.get("/preview")
def preview(
    store_path: str = Query(..., description="Path of an already-ingested evidence store"),
    program: str | None = Query(None, description="Include a scope section for this program"),
) -> dict:
    allowed = _resolve_allowed(store_path)
    try:
        markdown = build_dossier(allowed, program=program)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Evidence store file is missing on disk") from None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    return {"store_path": allowed, "markdown": markdown}
