"""Mission Control dashboard plugin — backend API routes.

Mounted at /api/plugins/mission-control/ by the dashboard plugin system
(hermes_cli.web_server._mount_plugin_api_routes). Backs the desktop app's
Mission Control page: one operational overview across the whole
investigation toolchain, so an operator can see the state of every subsystem
without visiting eleven pages.

This is an aggregator, not a new data source. Every figure below comes from
a state module that already owns it, through the same read functions the
per-feature plugins use. Nothing here writes, and nothing here computes a
number that its owning module could not.

Each subsystem is read defensively: a feature the operator has never used
has no state file at all, and one unconfigured subsystem must not take the
whole overview down with it. So every probe degrades to a 'no data' reading
rather than raising.
"""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter

router = APIRouter()


def _safe(fn: Callable[[], Any], default: Any) -> Any:
    """Run a subsystem probe, falling back rather than failing the overview.

    A never-used feature legitimately has no state on disk; that is a
    reading ('nothing yet'), not an error worth 500-ing the page over.
    """
    try:
        return fn()
    except Exception:  # noqa: BLE001 - one bad subsystem must not blank the board
        return default


@router.get("/overview")
def overview() -> dict:
    from hermes_cli.case_memory_state import list_investigations, stats
    from hermes_cli.puppet_state import list_personas
    from hermes_cli.scope_state import list_programs
    from hermes_cli.watch_state import list_watch_records

    case_stats = _safe(stats, {})
    investigations = _safe(list_investigations, [])
    personas = _safe(list_personas, [])
    programs = _safe(list_programs, [])
    watches = _safe(list_watch_records, [])

    # Scope entries are counted across programs so the tile reads as
    # "authorised surface", which is what an operator actually checks.
    in_scope = sum(len(p.get("in_scope", [])) for p in programs)
    out_of_scope = sum(len(p.get("out_of_scope", [])) for p in programs)

    return {
        "tiles": {
            "indicators": case_stats.get("total_iocs", 0),
            "investigations": len(investigations),
            "personas": len([p for p in personas if p.get("status") == "active"]),
            "watches": len(watches),
            "cross_case": case_stats.get("cross_investigation_iocs", 0),
            "ioc_types": len(case_stats.get("by_type", {})),
            "in_scope": in_scope,
            "out_of_scope": out_of_scope,
        },
        "subsystems": _subsystems(programs, watches, personas, investigations),
    }


def _subsystems(
    programs: list, watches: list, personas: list, investigations: list
) -> list[dict]:
    """Per-feature readiness rows for the diagnostics panel.

    'Readiness' here is deliberately simple and honest: it reports whether a
    subsystem has been configured and, where the underlying state carries a
    health signal, whether that signal is good. It is NOT a synthetic score
    — a number nobody can trace back to a real field would be worse than no
    number at all.
    """
    from cron.jobs import get_job

    rows: list[dict] = []

    rows.append(
        {
            "id": "scope",
            "label": "Authorized scope",
            "value": 100 if programs else 0,
            "tone": "nominal" if programs else "unknown",
            "detail": f"{len(programs)} program(s)",
        }
    )

    # Watch health is the share of rules whose cron job is enabled and whose
    # last run did not fail — the same join 'indagis watch list' performs.
    enabled = 0
    failing = 0
    for record in watches:
        job = _safe(lambda r=record: get_job(r.get("cron_job_id", "")) or {}, {})
        if job.get("enabled", True):
            enabled += 1
        if job.get("last_status") and job.get("last_status") != "ok":
            failing += 1

    if not watches:
        rows.append({"id": "watch", "label": "Signal watch", "value": 0, "tone": "unknown", "detail": "no rules"})
    else:
        pct = round((enabled / len(watches)) * 100)
        rows.append(
            {
                "id": "watch",
                "label": "Signal watch",
                "value": pct,
                "tone": "fault" if failing else "nominal" if pct == 100 else "caution",
                "detail": f"{enabled}/{len(watches)} active" + (f", {failing} failing" if failing else ""),
            }
        )

    burned = len([p for p in personas if p.get("status") == "burned"])
    rows.append(
        {
            "id": "puppet",
            "label": "Sock puppets",
            "value": 100 if personas else 0,
            "tone": "caution" if burned else "nominal" if personas else "unknown",
            "detail": f"{len(personas)} persona(s)" + (f", {burned} burned" if burned else ""),
        }
    )

    rows.append(
        {
            "id": "case",
            "label": "Case memory",
            "value": 100 if investigations else 0,
            "tone": "nominal" if investigations else "unknown",
            "detail": f"{len(investigations)} investigation(s)",
        }
    )

    return rows


@router.get("/airgap")
def airgap() -> dict:
    """Air-gap state gets its own route: it is a mode, not a metric, and the
    page renders it as a banner rather than a tile."""
    from hermes_cli.airgap_state import load_manifest

    manifest = _safe(load_manifest, None)
    return {"engaged": bool(manifest), "manifest": manifest}
