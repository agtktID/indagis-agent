"""Sock Puppet Manager dashboard plugin — backend API routes.

Mounted at /api/plugins/puppet/ by the dashboard plugin system
(hermes_cli.web_server._mount_plugin_api_routes). Backs the desktop app's
Sock Puppet Manager plugin (apps/desktop/src/plugins/puppet/): a read-only
browser over the persona registry hermes_cli/puppet_state.py already
maintains.

Read-only by design: every handler wraps an existing hermes_cli.puppet_state
read function. Creating, using, burning, or retiring a persona stays a CLI
action ('indagis puppet create' / 'use' / 'burn' / 'retire') — this plugin
never creates accounts or content, same as the CLI it mirrors.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from hermes_cli.puppet_state import get_persona, list_personas

router = APIRouter()


@router.get("/personas")
def personas(
    status: Optional[str] = Query(None, description="Filter by status: active, retired, burned"),
    investigation: Optional[str] = Query(None, description="Filter by investigation"),
) -> dict:
    return {"personas": list_personas(status=status, investigation=investigation)}


@router.get("/personas/{alias_or_id}")
def persona(alias_or_id: str) -> dict:
    record = get_persona(alias_or_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"No such persona: {alias_or_id!r}")
    return record
