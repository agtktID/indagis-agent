"""Surface Diff — continuous recon with automatic diffing.

Take a fingerprint of a host now, take another one later, and see exactly
what changed — a new IP, a reissued certificate with a new SAN (a
subdomain nobody announced), a header that reveals a stack migration, a
site that stopped answering. ``schedule`` turns that into a standing job
the same way Signal Watch does: a generated ``no_agent`` cron script, so
scheduling/locking/delivery are all reused rather than reinvented.

Mirrors ``hermes_cli/watch.py``'s structure and output style deliberately.
"""

from __future__ import annotations

import sys
from pathlib import Path

from hermes_cli.colors import Colors, color
from hermes_cli.surface_probe import diff_snapshots, take_snapshot
from hermes_cli.surface_state import latest_two_snapshots, list_snapshots, list_targets, load_snapshot, save_snapshot


def surface_snapshot(target: str, host: str) -> None:
    snapshot = take_snapshot(host)
    path = save_snapshot(target, snapshot)

    reachable = [s for s in ("http", "https") if snapshot.get(s) is not None]
    print(color(f"✓ Snapshot saved: {path}", Colors.GREEN))
    print(f"    IPs:       {', '.join(snapshot.get('ips') or []) or 'none resolved'}")
    print(f"    Reachable: {', '.join(reachable) or 'neither http nor https responded'}")
    if snapshot.get("tls_cert"):
        print(f"    TLS cert:  issuer={snapshot['tls_cert'].get('issuer')} not_after={snapshot['tls_cert'].get('not_after')}")


def surface_diff(target: str) -> None:
    pair = latest_two_snapshots(target)
    if pair is None:
        count = len(list_snapshots(target))
        if count == 0:
            print(color(f"No snapshots for '{target}' yet. Take one with 'indagis surface snapshot {target} <host>'", Colors.DIM))
        else:
            print(color(f"Only {count} snapshot — need at least 2 to diff. Take another one.", Colors.DIM))
        return

    older, newer = pair
    changes = diff_snapshots(older, newer)
    if not changes:
        print(color(f"No change between {older['taken_at']} and {newer['taken_at']}.", Colors.DIM))
        return

    print(color(f"Surface changed for '{target}' ({older['taken_at']} → {newer['taken_at']}):", Colors.YELLOW))
    for c in changes:
        print(f"  · {c}")


def surface_history(target: str) -> None:
    paths = list_snapshots(target)
    if not paths:
        print(color(f"No snapshots for '{target}'.", Colors.DIM))
        return
    for path in paths:
        snapshot = load_snapshot(path)
        taken_at = snapshot.get("taken_at", "?") if snapshot else "?"
        print(f"  {taken_at}   {path.name}")


def surface_targets() -> None:
    targets = list_targets()
    if not targets:
        print(color("No targets snapshotted yet.", Colors.DIM))
        return
    for t in targets:
        count = len(list_snapshots(t))
        print(f"  {color(t, Colors.YELLOW)}  ({count} snapshot(s))")


def _script_filename(target: str) -> str:
    from hermes_cli.surface_state import _safe_target_dir_name

    return f"surface_{_safe_target_dir_name(target)}.py"


def surface_schedule(target: str, host: str, schedule: str, deliver: str) -> None:
    from cron.jobs import create_job
    from hermes_constants import get_indagis_home

    if not deliver:
        print(color("--deliver is required — a schedule that fires and delivers nowhere is silent by design.", Colors.RED))
        return

    scripts_dir = get_indagis_home() / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    script_path = scripts_dir / _script_filename(target)
    body = (
        '"""Surface Diff generated check script — do not edit by hand.\n\n'
        f"Managed by 'indagis surface schedule'. To change it, remove the\n"
        f"underlying cron job ('indagis cron list' to find it) and re-run\n"
        f"'indagis surface schedule' with new arguments.\n\"\"\"\n\n"
        "from hermes_cli.surface_runner import run_surface_check\n"
        f"run_surface_check({target!r}, {host!r})\n"
    )
    script_path.write_text(body, encoding="utf-8")

    try:
        job = create_job(
            prompt=None,
            schedule=schedule,
            name=f"surface:{target}",
            script=_script_filename(target),
            no_agent=True,
            deliver=deliver,
            repeat=None,
        )
    except Exception as exc:  # noqa: BLE001 — surface any failure, then clean up the script
        try:
            script_path.unlink()
        except OSError:
            pass
        print(color(f"Failed to schedule: {exc}", Colors.RED))
        return

    job_id = job.get("id") if isinstance(job, dict) else None
    print(color(f"✓ Scheduled surface monitoring for '{target}'", Colors.GREEN))
    print(f"    Host:      {host}")
    print(f"    Schedule:  {schedule}")
    print(f"    Deliver:   {deliver}")
    print(f"    Cron job:  {job_id}")
    print(color("  Manage it like any cron job: 'indagis cron pause/resume/remove " + str(job_id) + "'", Colors.DIM))


def surface_command(args) -> None:
    action = getattr(args, "surface_command", None)
    if action in (None, "targets"):
        surface_targets()
    elif action == "snapshot":
        surface_snapshot(args.target, args.host)
    elif action == "diff":
        surface_diff(args.target)
    elif action == "history":
        surface_history(args.target)
    elif action == "schedule":
        surface_schedule(args.target, args.host, args.schedule, args.deliver)
    else:
        print(color(f"Unknown surface subcommand: {action}", Colors.RED), file=sys.stderr)
