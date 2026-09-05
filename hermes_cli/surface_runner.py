"""Surface Diff script entrypoint — the generated cron script's target.

Takes a fresh snapshot, diffs it against the prior one, and prints a
result only when something changed (or on the very first snapshot for a
host, there's nothing to diff against yet, so it stays silent). Runs as a
``no_agent`` cron job (see ``cron/jobs.py``): whatever this prints to
stdout is delivered verbatim to the schedule's ``--deliver`` target.
"""

from __future__ import annotations

import sys

from hermes_cli.surface_probe import diff_snapshots, take_snapshot
from hermes_cli.surface_state import list_snapshots, load_snapshot, save_snapshot


def run_surface_check(target: str, host: str) -> None:
    prior_paths = list_snapshots(target)
    prior = load_snapshot(prior_paths[-1]) if prior_paths else None

    snapshot = take_snapshot(host)
    save_snapshot(target, snapshot)

    if prior is None:
        return

    changes = diff_snapshots(prior, snapshot)
    if changes:
        print(f"[{target}] Surface changed for {host}:")
        for c in changes:
            print(f"  · {c}")


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) < 2:
        print("usage: surface_runner.py <target> <host>", file=sys.stderr)
        return 2
    run_surface_check(argv[0], argv[1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
