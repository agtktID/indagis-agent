"""Scope Sync dashboard plugin — backend API routes.

Mounted at /api/plugins/scope/ by the dashboard plugin system
(hermes_cli.web_server._mount_plugin_api_routes). Backs the desktop app's
Scope Sync plugin (apps/desktop/src/plugins/scope/): a read-only browser
over the authorized-scope registry hermes_cli/scope_state.py already
maintains, plus the same in-scope/out-of-scope verdict lookup
'indagis scope check' performs.

Read-only by design: every handler wraps existing read functions from
hermes_cli.scope_state. Importing a scope export, adding an entry,
removing a program, and onboarding a program onto continuous recon stay
CLI actions ('indagis scope import' / 'add' / 'remove' / 'autopilot').

check_target() is a pure lookup — it matches a string against already
imported scope rules and writes nothing — so exposing it here does not
open a write path.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from hermes_cli.scope_state import check_target, get_program, list_programs

router = APIRouter()


@router.get("/programs")
def programs() -> dict:
    return {"programs": list_programs()}


@router.get("/programs/{program}")
def program(program: str) -> dict:
    record = get_program(program)
    if record is None:
        raise HTTPException(status_code=404, detail=f"No such program: {program!r}")
    return record


@router.get("/check")
def check(
    target: str = Query(..., description="Host, domain or IP to check against imported scope"),
    program: str | None = Query(None, description="Restrict the check to one program"),
) -> dict:
    return {"target": target, "results": check_target(target, program=program)}
