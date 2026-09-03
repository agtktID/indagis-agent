"""Bounty Ledger dashboard plugin — backend API routes.

Mounted at /api/plugins/bounty/ by the dashboard plugin system
(hermes_cli.web_server._mount_plugin_api_routes). Backs the desktop app's
Bounty Ledger plugin (apps/desktop/src/plugins/bounty/): a read-only
browser over the submission ledger hermes_cli/bounty_state.py already
maintains.

Read-only by design: every handler wraps an existing
hermes_cli.bounty_state read function. Recording a submission or payout
stays a CLI action ('indagis bounty add' / 'indagis bounty pay').
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from hermes_cli.bounty_state import list_submissions, stats

router = APIRouter()


@router.get("/submissions")
def submissions(
    status: Optional[str] = Query(None, description="Filter by submission status"),
    program: Optional[str] = Query(None, description="Filter by program name"),
) -> dict:
    return {"submissions": list_submissions(status=status, program=program)}


@router.get("/stats")
def get_stats() -> dict:
    return stats()
