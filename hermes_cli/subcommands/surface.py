"""``indagis surface`` subcommand parser — Surface Diff.

Mirrors ``hermes_cli/subcommands/watch.py``'s shape: same
subparsers-with-dest pattern, same ``func=cmd_surface`` dispatch, handler
injected to avoid importing ``main`` (cycle avoidance).
"""

from __future__ import annotations

from typing import Callable


def build_surface_parser(subparsers, *, cmd_surface: Callable) -> None:
    """Attach the ``surface`` subcommand (and its sub-actions) to ``subparsers``."""
    surface_parser = subparsers.add_parser(
        "surface",
        help="Surface Diff — continuous recon with automatic diffing",
        description=(
            "Fingerprint a host (resolved IPs, HTTP headers/title, TLS "
            "certificate) and diff it against the prior snapshot. "
            "'schedule' turns that into a standing cron job."
        ),
    )
    surface_subparsers = surface_parser.add_subparsers(dest="surface_command")

    # surface targets
    surface_subparsers.add_parser("targets", help="List targets with saved snapshots")

    # surface snapshot
    surface_snapshot = surface_subparsers.add_parser("snapshot", help="Take one snapshot now")
    surface_snapshot.add_argument("target", help="Name for this target (used to group its snapshots)")
    surface_snapshot.add_argument("host", help="Hostname to fingerprint")

    # surface diff
    surface_diff = surface_subparsers.add_parser("diff", help="Diff the two most recent snapshots")
    surface_diff.add_argument("target", help="Target name")

    # surface history
    surface_history = surface_subparsers.add_parser("history", help="List a target's snapshot history")
    surface_history.add_argument("target", help="Target name")

    # surface schedule
    surface_schedule = surface_subparsers.add_parser(
        "schedule", help="Schedule recurring snapshot + diff via cron"
    )
    surface_schedule.add_argument("target", help="Name for this target")
    surface_schedule.add_argument("host", help="Hostname to fingerprint")
    surface_schedule.add_argument("--schedule", required=True, help="Schedule like 'every 6h' or a cron expression")
    surface_schedule.add_argument("--deliver", required=True, help="Where change alerts go: telegram, slack, discord, or platform:chat_id")

    surface_parser.set_defaults(func=cmd_surface)
