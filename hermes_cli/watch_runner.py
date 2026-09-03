"""Signal Watch script entrypoint.

A tiny generated script under ``INDAGIS_HOME/scripts/watch_<id>.py`` calls
``run_watch(watch_id)`` on cron's schedule. This module is the only thing
that generated script imports — everything else (checkers, state, registry)
lives here so the generated script stays a two-line stub.

Runs as a ``no_agent`` cron job (see ``cron/jobs.py``): whatever this prints
to stdout is delivered verbatim to the rule's ``--deliver`` target; printing
nothing means the tick was silent. That contract is why every branch below
either prints one alert message or returns without printing at all.
"""

from __future__ import annotations

import sys

from hermes_cli.watch_checks import CHECKERS
from hermes_cli.watch_state import get_watch_record, get_watch_state, save_watch_state


def run_watch(watch_id: str) -> None:
    record = get_watch_record(watch_id)
    if record is None:
        # The registry entry is gone (e.g. removed by hand) but the
        # generated script or its cron job wasn't cleaned up. Stay silent
        # rather than alerting about our own bookkeeping.
        return

    checker = CHECKERS.get(record["kind"])
    if checker is None:
        print(f"⚠️ Signal Watch '{record.get('name', watch_id)}': unknown check kind {record['kind']!r}")
        return

    state = get_watch_state(watch_id)
    alert_text, new_state = checker(record["target"], state)
    save_watch_state(watch_id, new_state)

    if alert_text:
        name = record.get("name") or record["target"]
        print(f"[{name}]\n{alert_text}")


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("usage: watch_runner.py <watch_id>", file=sys.stderr)
        return 2
    run_watch(argv[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
