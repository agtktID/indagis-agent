"""MCP Vetting Firewall dashboard plugin — backend API routes.

Mounted at /api/plugins/mcp-audit/ by the dashboard plugin system
(hermes_cli.web_server._mount_plugin_api_routes). Backs the desktop app's
MCP Vetting Firewall plugin (apps/desktop/src/plugins/mcp-audit/): a
read-only browser over the audit verdicts hermes_cli/mcp_audit_state.py
already maintains — one row per MCP server, keyed by its config.yaml name.

Read-only by design: every handler wraps an existing
hermes_cli.mcp_audit_state read function. Running a new audit stays a CLI
action ('indagis mcp audit').
"""

from __future__ import annotations

from fastapi import APIRouter

from hermes_cli.mcp_audit_state import list_audit_records

router = APIRouter()


@router.get("/records")
def records() -> dict:
    return {"records": list_audit_records()}
