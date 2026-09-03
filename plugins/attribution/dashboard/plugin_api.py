"""Attribution Confidence dashboard plugin — backend API routes.

Mounted at /api/plugins/attribution/ by the dashboard plugin system
(hermes_cli.web_server._mount_plugin_api_routes). Backs the desktop app's
Attribution Confidence plugin (apps/desktop/src/plugins/attribution/): a
read-only NATO/Admiralty scorer over evidence-store files already known to
Case Memory, so the plugin never needs its own file picker.

Every handler wraps an existing hermes_cli.attribution / case_memory_state
read function — no new storage format, no write path.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from hermes_cli.attribution import CREDIBILITY_LABELS, RELIABILITY_LABELS, score_evidence_store
from hermes_cli.case_memory_state import list_investigations

router = APIRouter()


@router.get("/investigations")
def investigations() -> dict:
    return {"investigations": list_investigations()}


@router.get("/matrix")
def matrix() -> dict:
    return {"reliability": RELIABILITY_LABELS, "credibility": CREDIBILITY_LABELS}


@router.get("/score")
def score(store_path: str = Query(..., min_length=1)) -> dict:
    try:
        return score_evidence_store(store_path)
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
