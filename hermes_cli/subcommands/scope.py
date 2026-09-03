"""``indagis scope`` subcommand parser — Scope Sync.

Mirrors ``hermes_cli/subcommands/watch.py``'s shape: same
subparsers-with-dest pattern, same ``func=cmd_scope`` dispatch, handler
injected to avoid importing ``main`` (cycle avoidance).
"""

from __future__ import annotations

from typing import Callable


def build_scope_parser(subparsers, *, cmd_scope: Callable) -> None:
    """Attach the ``scope`` subcommand (and its sub-actions) to ``subparsers``."""
    scope_parser = subparsers.add_parser(
        "scope",
        help="Scope Sync — import authorized bounty scope, check targets against it",
        description=(
            "Import a scope export from your own bounty dashboard (JSON or "
            "CSV) and check targets against it before testing them. Reads "
            "a file you already have — never talks to a bounty platform "
            "directly."
        ),
    )
    scope_subparsers = scope_parser.add_subparsers(dest="scope_command")

    # scope list
    scope_subparsers.add_parser("list", help="List imported programs")

    # scope import
    scope_import = scope_subparsers.add_parser("import", help="Import a scope export file")
    scope_import.add_argument("program", help="Program name")
    scope_import.add_argument("file_path", help="Path to a .json or .csv scope export")

    # scope add
    scope_add = scope_subparsers.add_parser("add", help="Manually add one scope entry")
    scope_add.add_argument("program", help="Program name")
    scope_add.add_argument("target", help="Domain, URL, CIDR, wildcard (*.example.com), app ID, etc.")
    scope_add.add_argument("--type", help="e.g. domain, url, cidr, mobile, other")
    scope_add.add_argument("--description", help="Free-text note")
    scope_add.add_argument("--out-of-scope", action="store_true", help="Add as out-of-scope instead of in-scope")

    # scope show
    scope_show = scope_subparsers.add_parser("show", help="Show a program's full scope")
    scope_show.add_argument("program", help="Program name")

    # scope check
    scope_check = scope_subparsers.add_parser("check", help="Check whether a target is in scope")
    scope_check.add_argument("target", help="Domain, URL, or IP to check")
    scope_check.add_argument("--program", help="Limit the check to one program")

    # scope autopilot
    scope_autopilot = scope_subparsers.add_parser(
        "autopilot",
        help="Onboard every in-scope, host-shaped target onto Surface Diff monitoring",
    )
    scope_autopilot.add_argument("program", help="Program name")
    scope_autopilot.add_argument(
        "--schedule", required=True,
        help="Schedule like 'every 30m', 'every 2h', or '0 9 * * *' (cron expression)",
    )
    scope_autopilot.add_argument("--deliver", required=True, help="Delivery channel for surface-change alerts")
    scope_autopilot.add_argument(
        "--dry-run", action="store_true", help="List what would be onboarded without scheduling anything"
    )

    # scope remove
    scope_remove = scope_subparsers.add_parser("remove", aliases=["rm", "delete"], help="Remove a program's scope")
    scope_remove.add_argument("program", help="Program name")

    scope_parser.set_defaults(func=cmd_scope)
