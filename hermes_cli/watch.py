"""Signal Watch subcommand for the Indagis CLI.

A watch rule is a thin wrapper around a ``no_agent`` cron job (see
``cron/jobs.py``): creating a rule writes a two-line generated script under
``INDAGIS_HOME/scripts/`` and schedules it exactly like any other cron
watchdog. All scheduling, locking, and delivery routing is cron's; this
module owns only the rule registry (``hermes_cli/watch_state.py``) and the
checker dispatch (``hermes_cli/watch_checks.py``).

Mirrors ``hermes_cli/cron.py``'s structure and output style deliberately —
same box-table listing, same status coloring, same gateway-not-running
warning — so the two commands feel like one family.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from hermes_cli.colors import Colors, color
from hermes_cli.watch_checks import CHECKERS
from hermes_cli.watch_state import (
    create_watch_record,
    get_watch_record,
    get_watch_state,
    list_watch_records,
    remove_watch_record,
)

_SCRIPT_HEADER = '"""Signal Watch generated check script — do not edit by hand.\n\nManaged by \'indagis watch\'. To change this rule, remove it and create a new\none: \'indagis watch remove {watch_id}\'.\n"""\n\n'


def _script_filename(watch_id: str) -> str:
    return f"watch_{watch_id}.py"


def _write_generated_script(watch_id: str) -> Path:
    from hermes_constants import get_indagis_home

    scripts_dir = get_indagis_home() / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    path = scripts_dir / _script_filename(watch_id)
    body = (
        _SCRIPT_HEADER.format(watch_id=watch_id)
        + "from hermes_cli.watch_runner import run_watch\n"
        + f"run_watch({watch_id!r})\n"
    )
    path.write_text(body, encoding="utf-8")
    return path


def _warn_if_gateway_not_running() -> None:
    # Same underlying scheduler as cron — reuse its diagnostic verbatim
    # rather than duplicating the gateway-pid lookup.
    from hermes_cli.cron import _warn_if_gateway_not_running as _cron_warn

    _cron_warn()


def watch_create(
    kind: str,
    target: str,
    schedule: str,
    deliver: str,
    name: Optional[str] = None,
) -> None:
    from cron.jobs import create_job

    if kind not in CHECKERS:
        print(color(f"Unknown watch kind {kind!r}. Choose one of: {', '.join(CHECKERS)}", Colors.RED))
        return
    if not deliver:
        print(color("--deliver is required — a watch that fires and delivers nowhere is silent by design.", Colors.RED))
        return

    watch_id = None
    try:
        from hermes_cli.watch_state import generate_watch_id

        watch_id = generate_watch_id()
        _write_generated_script(watch_id)

        job = create_job(
            prompt=None,
            schedule=schedule,
            name=f"watch:{name or target}",
            script=_script_filename(watch_id),
            no_agent=True,
            deliver=deliver,
            repeat=None,
        )
        job_id = job.get("id") if isinstance(job, dict) else None
        if not job_id:
            raise RuntimeError(f"cron job creation returned no id: {job!r}")

        record = create_watch_record(
            watch_id=watch_id,
            kind=kind,
            target=target,
            name=name,
            cron_job_id=job_id,
            deliver=deliver,
            schedule=schedule,
        )
    except Exception as exc:  # noqa: BLE001 — surface any failure, then clean up
        if watch_id is not None:
            _cleanup_generated_script(watch_id)
        print(color(f"Failed to create watch: {exc}", Colors.RED))
        return

    print(color("✓ Watch created", Colors.GREEN))
    print(f"    ID:        {record['id']}")
    print(f"    Kind:      {kind}")
    print(f"    Target:    {target}")
    print(f"    Schedule:  {schedule}")
    print(f"    Deliver:   {deliver}")
    print(color("  First tick establishes a baseline — it won't alert until it sees a change.", Colors.DIM))
    _warn_if_gateway_not_running()


def _cleanup_generated_script(watch_id: str) -> None:
    from hermes_constants import get_indagis_home

    path = get_indagis_home() / "scripts" / _script_filename(watch_id)
    try:
        path.unlink()
    except OSError:
        pass


def watch_list(show_all: bool = False) -> None:
    from cron.jobs import get_job

    records = list_watch_records()
    if not records:
        print(color("No watch rules.", Colors.DIM))
        print(color("Create one with 'indagis watch create <kind> <target> --schedule ... --deliver ...'", Colors.DIM))
        return

    print()
    print(color("┌─────────────────────────────────────────────────────────────────────────┐", Colors.CYAN))
    print(color("│                          Signal Watch Rules                             │", Colors.CYAN))
    print(color("└─────────────────────────────────────────────────────────────────────────┘", Colors.CYAN))
    print()

    for record in records:
        job = get_job(record.get("cron_job_id", "")) or {}
        enabled = job.get("enabled", True)
        if not enabled and not show_all:
            continue
        status = color("[paused]", Colors.YELLOW) if not enabled else color("[active]", Colors.GREEN)
        last_status = job.get("last_status")
        last_run = job.get("last_run_at", "?")

        print(f"  {color(record['id'], Colors.YELLOW)} {status}")
        print(f"    Name:      {record.get('name', '?')}")
        print(f"    Kind:      {record.get('kind', '?')}")
        print(f"    Target:    {record.get('target', '?')}")
        print(f"    Schedule:  {job.get('schedule_display', record.get('schedule', '?'))}")
        print(f"    Deliver:   {record.get('deliver', '?')}")
        if last_status:
            display = color("ok", Colors.GREEN) if last_status == "ok" else color(f"{last_status}", Colors.RED)
            print(f"    Last run:  {last_run}  {display}")
        print()

    _warn_if_gateway_not_running()


def watch_show(watch_id: str) -> None:
    from cron.jobs import get_job

    record = get_watch_record(watch_id)
    if record is None:
        print(color(f"No such watch: {watch_id}", Colors.RED))
        return
    job = get_job(record.get("cron_job_id", "")) or {}
    state = get_watch_state(watch_id)

    print(f"ID:        {record['id']}")
    print(f"Name:      {record.get('name', '?')}")
    print(f"Kind:      {record.get('kind', '?')}")
    print(f"Target:    {record.get('target', '?')}")
    print(f"Schedule:  {job.get('schedule_display', record.get('schedule', '?'))}")
    print(f"Deliver:   {record.get('deliver', '?')}")
    print(f"Created:   {record.get('created_at', '?')}")
    print(f"Cron job:  {record.get('cron_job_id', '?')} (enabled={job.get('enabled', '?')})")
    print(f"Last run:  {job.get('last_run_at', 'never')}  status={job.get('last_status', '?')}")
    if state:
        print("State:")
        for key, value in state.items():
            print(f"    {key}: {value}")


def watch_pause(watch_id: str) -> None:
    from cron.jobs import pause_job

    record = get_watch_record(watch_id)
    if record is None:
        print(color(f"No such watch: {watch_id}", Colors.RED))
        return
    result = pause_job(record["cron_job_id"])
    if result is None:
        print(color("Failed to pause — underlying cron job not found.", Colors.RED))
        return
    print(color(f"✓ Paused {watch_id}", Colors.GREEN))


def watch_resume(watch_id: str) -> None:
    from cron.jobs import resume_job

    record = get_watch_record(watch_id)
    if record is None:
        print(color(f"No such watch: {watch_id}", Colors.RED))
        return
    result = resume_job(record["cron_job_id"])
    if result is None:
        print(color("Failed to resume — underlying cron job not found.", Colors.RED))
        return
    print(color(f"✓ Resumed {watch_id}", Colors.GREEN))


def watch_remove(watch_id: str) -> None:
    from cron.jobs import remove_job

    record = get_watch_record(watch_id)
    if record is None:
        print(color(f"No such watch: {watch_id}", Colors.RED))
        return
    remove_job(record["cron_job_id"])
    _cleanup_generated_script(watch_id)
    remove_watch_record(watch_id)
    print(color(f"✓ Removed {watch_id}", Colors.GREEN))


def watch_run(watch_id: str) -> None:
    """Force an immediate, synchronous check — bypasses the cron scheduler
    entirely so a rule can be sanity-checked right after creation. Unlike
    the scheduled tick (silent when nothing changed), this always prints a
    result, since a human just asked for one."""
    record = get_watch_record(watch_id)
    if record is None:
        print(color(f"No such watch: {watch_id}", Colors.RED))
        return

    checker = CHECKERS.get(record["kind"])
    if checker is None:
        print(color(f"Unknown watch kind: {record['kind']}", Colors.RED))
        return

    state = get_watch_state(watch_id)
    alert_text, new_state = checker(record["target"], state)
    from hermes_cli.watch_state import save_watch_state

    save_watch_state(watch_id, new_state)

    if alert_text:
        print(color("Alert would fire:", Colors.YELLOW))
        print(alert_text)
    elif new_state.get("last_status") == "error":
        print(color("Check failed — see state above.", Colors.RED))
    else:
        print(color("No change detected.", Colors.DIM))


def watch_status() -> None:
    records = list_watch_records()
    print()
    print(f"Signal Watch: {len(records)} rule(s) registered.")
    _warn_if_gateway_not_running()


def watch_command(args) -> None:
    action = getattr(args, "watch_command", None)
    if action in (None, "list"):
        watch_list(show_all=getattr(args, "all", False))
    elif action == "create":
        watch_create(
            kind=args.kind,
            target=args.target,
            schedule=args.schedule,
            deliver=args.deliver,
            name=getattr(args, "name", None),
        )
    elif action == "show":
        watch_show(args.watch_id)
    elif action == "pause":
        watch_pause(args.watch_id)
    elif action == "resume":
        watch_resume(args.watch_id)
    elif action == "remove":
        watch_remove(args.watch_id)
    elif action == "run":
        watch_run(args.watch_id)
    elif action == "status":
        watch_status()
    else:
        print(color(f"Unknown watch subcommand: {action}", Colors.RED), file=sys.stderr)
