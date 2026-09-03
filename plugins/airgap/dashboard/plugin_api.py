"""Air Gap dashboard plugin — backend API routes.

Mounted at /api/plugins/airgap/ by the dashboard plugin system
(hermes_cli.web_server._mount_plugin_api_routes). Backs the desktop app's
Air Gap plugin (apps/desktop/src/plugins/airgap/): a read-only view of the
lockdown manifest hermes_cli/airgap_state.py already maintains.

Read-only by design: the single handler wraps the existing
hermes_cli.airgap_state.load_manifest() read function. Locking down or
restoring stays a CLI action ('indagis airgap lockdown' / 'indagis airgap
restore').
"""

from __future__ import annotations

from fastapi import APIRouter

from hermes_cli.airgap_state import load_manifest

router = APIRouter()


@router.get("/manifest")
def manifest() -> dict:
    return {"manifest": load_manifest()}
