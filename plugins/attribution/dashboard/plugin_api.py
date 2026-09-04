"""Attribution Confidence dashboard plugin — backend API routes.

Mounted at /api/plugins/attribution/ by the dashboard plugin system
(hermes_cli.web_server._mount_plugin_api_routes). Backs the desktop app's
Attribution Confidence plugin (apps/desktop/src/plugins/attribution/): a
read-only NATO/Admiralty scorer over evidence-store files already known to
Case Memory, so the plugin never needs its own file picker.

Every handler wraps an existing hermes_cli.attribution / case_memory_state
read function — no new storage format, no write path.

PATH ALLOWLIST. score_evidence_store() takes a filesystem path, which is
fine for the CLI the operator types into but would be an arbitrary-file-read
primitive over HTTP: it hands the path straight to _load_evidence_store(),
which opens whatever it is given, so any JSON file on disk carrying an
'evidence' array would be scored and returned. So /score never passes a
client-supplied path through — it resolves the request against the stores
Case Memory has already recorded (paths the operator pointed the CLI at via
'indagis case ingest') and refuses anything else. Comparison is on the
resolved real path, so '..' segments and symlinks cannot walk out of the
allowlist, and the recorded string (not the caller's) is what gets scored.
Same constraint as plugins/dossier/dashboard/plugin_api.py.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from hermes_cli.attribution import CREDIBILITY_LABELS, RELIABILITY_LABELS, score_evidence_store
from hermes_cli.case_memory_state import list_investigations

router = APIRouter()


def _resolve_allowed(store_path: str) -> str:
    """Return the recorded store_path matching ``store_path``, or 404."""
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
            "'indagis case ingest' can be scored here."
        ),
    )


@router.get("/investigations")
def investigations() -> dict:
    return {"investigations": list_investigations()}


@router.get("/matrix")
def matrix() -> dict:
    return {"reliability": RELIABILITY_LABELS, "credibility": CREDIBILITY_LABELS}


@router.get("/score")
def score(store_path: str = Query(..., min_length=1)) -> dict:
    allowed = _resolve_allowed(store_path)
    try:
        return score_evidence_store(allowed)
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
