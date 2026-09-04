"""Signal Watch dashboard plugin — backend API routes.

Mounted at /api/plugins/watch/ by the dashboard plugin system
(hermes_cli.web_server._mount_plugin_api_routes). Backs the desktop app's
Signal Watch plugin (apps/desktop/src/plugins/watch/): a read-only browser
over the watch rules hermes_cli/watch_state.py already maintains, joined
with each rule's underlying cron job status (enabled/paused, last run) —
the same join hermes_cli/watch.py's own 'watch list'/'watch show' CLI
output does.

Read-only by design: every handler wraps existing read functions from
hermes_cli.watch_state and cron.jobs. Creating, pausing, resuming, or
removing a rule stays a CLI action ('indagis watch create' / 'pause' /
'resume' / 'remove').
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from cron.jobs import get_job
from hermes_cli.watch_state import get_watch_record, get_watch_state, list_watch_records

router = APIRouter()


def _enrich(record: dict) -> dict:
    job = get_job(record.get("cron_job_id", "")) or {}
    return {
        **record,
        "enabled": job.get("enabled", True),
        "last_run_at": job.get("last_run_at"),
        "last_status": job.get("last_status"),
        "schedule_display": job.get("schedule_display", record.get("schedule")),
    }


@router.get("/rules")
def rules() -> dict:
    return {"rules": [_enrich(r) for r in list_watch_records()]}


@router.get("/rules/{watch_id}")
def rule(watch_id: str) -> dict:
    record = get_watch_record(watch_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"No such watch: {watch_id!r}")
    return {**_enrich(record), "state": get_watch_state(watch_id)}
