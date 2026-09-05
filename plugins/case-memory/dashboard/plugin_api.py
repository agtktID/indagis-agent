"""Case Memory dashboard plugin — backend API routes.

Mounted at /api/plugins/case-memory/ by the dashboard plugin system
(hermes_cli.web_server._mount_plugin_api_routes). Backs the desktop app's
Case Memory plugin (apps/desktop/src/plugins/case-memory/): a read-only
browser over the cross-investigation IOC correlation index that
hermes_cli/case_memory_state.py already maintains.

Read-only by design for this first slice: every handler is a thin wrapper
around an existing hermes_cli.case_memory_state read function, so this
router introduces no new storage format or write path — 'indagis case
ingest' remains the only way to add data to the index.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from hermes_cli import case_memory_state

router = APIRouter()


@router.get("/iocs")
def list_iocs(ioc_type: Optional[str] = Query(None, description="Filter by IOC type, e.g. IP_ADDRESS")) -> dict:
    return {"iocs": case_memory_state.list_iocs(ioc_type=ioc_type)}


@router.get("/investigations")
def list_investigations() -> dict:
    return {"investigations": case_memory_state.list_investigations()}


@router.get("/stats")
def get_stats() -> dict:
    return case_memory_state.stats()


@router.get("/lookup")
def lookup(value: str = Query(..., min_length=1)) -> dict:
    return {"ioc": case_memory_state.lookup_ioc(value)}
