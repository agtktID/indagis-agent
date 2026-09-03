"""Air Gap — confidential/offline-only engagement mode.

Deliberately not a network firewall — see ``airgap_state.py`` for why that
promise would be dishonest to make from a CLI subcommand. What this module
actually does: pause every network-reaching automation this install
already knows about (cron jobs and Signal Watch rules with an external
``--deliver`` target) for the duration of a confidential engagement, and
surface — without touching — the one thing it can't safely act on itself:
MCP servers configured with a remote transport. ``restore`` undoes exactly
what ``lockdown`` paused, nothing more.

Mirrors ``hermes_cli/watch.py``'s structure and output style deliberately.
"""

from __future__ import annotations

import sys
from typing import Any, Dict, List

from hermes_cli.airgap_state import clear_manifest, load_manifest, mark_restored, save_manifest
from hermes_cli.colors import Colors, color


def _remote_mcp_servers() -> List[str]:
    from hermes_cli.mcp_config import _get_mcp_servers

    servers = _get_mcp_servers()
    remote = []
    for name, cfg in servers.items():
        url = (cfg or {}).get("url") or ""
        if isinstance(url, str) and url.startswith(("http://", "https://")):
            remote.append(name)
    return sorted(remote)


def _network_reaching_jobs() -> List[Dict[str, Any]]:
    from cron.jobs import list_jobs

    jobs = list_jobs(include_disabled=False)
    return [j for j in jobs if (j.get("deliver") or "").strip() and j.get("deliver") != "local"]


def _watch_names_for_jobs(job_ids: List[str]) -> List[str]:
    from hermes_cli.watch_state import list_watch_records

    job_ids = set(job_ids)
    return [r["id"] for r in list_watch_records() if r.get("cron_job_id") in job_ids]


def airgap_status() -> None:
    manifest = load_manifest()
    locked_down = manifest is not None and manifest.get("restored_at") is None

    print()
    if locked_down:
        print(color(f"● LOCKED DOWN — engagement '{manifest['engagement']}' since {manifest['locked_down_at']}", Colors.YELLOW))
        print(f"    Paused cron jobs: {len(manifest.get('paused_cron_job_ids', []))}")
        print(f"    Paused watch rules: {len(manifest.get('paused_watch_ids', []))}")
    else:
        print(color("○ Not locked down.", Colors.DIM))

    jobs = _network_reaching_jobs()
    remote_mcp = _remote_mcp_servers()

    print()
    print(f"Active automations with an external deliver target: {len(jobs)}")
    for j in jobs:
        print(f"    {j.get('id', '?')}  {j.get('name', '?')}  →  {j.get('deliver')}")

    print()
    print(f"MCP servers with a remote (http/https) transport: {len(remote_mcp)}")
    for name in remote_mcp:
        print(f"    {name}")
    if remote_mcp:
        print(color("  ⚠ Air Gap cannot safely disable these itself — remove them by hand", Colors.YELLOW))
        print(color("    ('indagis mcp remove <name>') before starting a confidential engagement.", Colors.YELLOW))


def airgap_lockdown(engagement: str) -> None:
    from cron.jobs import pause_job

    existing = load_manifest()
    if existing is not None and existing.get("restored_at") is None:
        print(color(f"Already locked down for '{existing['engagement']}' — restore first.", Colors.RED))
        return

    jobs = _network_reaching_jobs()
    paused_job_ids = []
    for j in jobs:
        result = pause_job(j["id"], reason=f"airgap:{engagement}")
        if result is not None:
            paused_job_ids.append(j["id"])

    watch_ids = _watch_names_for_jobs(paused_job_ids)
    remote_mcp = _remote_mcp_servers()
    save_manifest(
        engagement=engagement,
        paused_cron_job_ids=paused_job_ids,
        paused_watch_ids=watch_ids,
        remote_mcp_servers=remote_mcp,
    )

    print(color(f"✓ Locked down for engagement '{engagement}'", Colors.GREEN))
    print(f"    Paused {len(paused_job_ids)} scheduled automation(s) with an external deliver target")
    if watch_ids:
        print(f"    ({len(watch_ids)} of those are Signal Watch rules: {', '.join(watch_ids)})")
    if remote_mcp:
        print(color(f"  ⚠ {len(remote_mcp)} MCP server(s) with remote transport still active — remove by hand:", Colors.YELLOW))
        for name in remote_mcp:
            print(f"      {name}")
    print(color("  This pauses known scheduled automations — it is not a network firewall.", Colors.DIM))
    print(color("  Model API calls, MCP tool calls, and manual commands still reach the network.", Colors.DIM))


def airgap_restore() -> None:
    from cron.jobs import resume_job

    manifest = load_manifest()
    if manifest is None:
        print(color("No lockdown to restore.", Colors.DIM))
        return
    if manifest.get("restored_at") is not None:
        print(color(f"Engagement '{manifest['engagement']}' was already restored at {manifest['restored_at']}.", Colors.DIM))
        return

    restored, failed = 0, []
    for job_id in manifest.get("paused_cron_job_ids", []):
        try:
            result = resume_job(job_id)
        except ValueError as exc:
            failed.append(f"{job_id} ({exc})")
            continue
        if result is not None:
            restored += 1
        else:
            failed.append(f"{job_id} (job no longer exists)")

    mark_restored()
    print(color(f"✓ Restored {restored} automation(s) from engagement '{manifest['engagement']}'", Colors.GREEN))
    if failed:
        print(color(f"  {len(failed)} could not be resumed automatically:", Colors.YELLOW))
        for f in failed:
            print(f"      {f}")


def airgap_report() -> None:
    manifest = load_manifest()
    if manifest is None:
        print(color("No lockdown recorded — nothing to report.", Colors.DIM))
        return

    print(f"Engagement:         {manifest['engagement']}")
    print(f"Locked down at:     {manifest['locked_down_at']}")
    print(f"Restored at:        {manifest.get('restored_at') or 'still locked down'}")
    print(f"Paused cron jobs:   {manifest.get('paused_cron_job_ids', [])}")
    print(f"Paused watch rules: {manifest.get('paused_watch_ids', [])}")
    print(f"Remote MCP servers present at lockdown: {manifest.get('remote_mcp_servers_at_lockdown', [])}")


def airgap_command(args) -> None:
    action = getattr(args, "airgap_command", None)
    if action in (None, "status"):
        airgap_status()
    elif action == "lockdown":
        airgap_lockdown(args.engagement)
    elif action == "restore":
        airgap_restore()
    elif action == "report":
        airgap_report()
    else:
        print(color(f"Unknown airgap subcommand: {action}", Colors.RED), file=sys.stderr)
