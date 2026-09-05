"""``indagis bounty`` subcommand parser — Bounty Ledger.

Mirrors ``hermes_cli/subcommands/watch.py``'s shape: same
subparsers-with-dest pattern, same ``func=cmd_bounty`` dispatch, handler
injected to avoid importing ``main`` (cycle avoidance).
"""

from __future__ import annotations

from typing import Callable

from hermes_cli.bounty_state import STATUSES


def build_bounty_parser(subparsers, *, cmd_bounty: Callable) -> None:
    """Attach the ``bounty`` subcommand (and its sub-actions) to ``subparsers``."""
    bounty_parser = subparsers.add_parser(
        "bounty",
        help="Bounty Ledger — payout/ROI tracker for bug bounty submissions",
        description=(
            "Track submissions across bounty programs, their triage status, "
            "and any payout, so 'indagis bounty stats' can answer win rate "
            "and $/hour across every program at once."
        ),
    )
    bounty_subparsers = bounty_parser.add_subparsers(dest="bounty_command")

    # bounty list
    bounty_list = bounty_subparsers.add_parser("list", help="List submissions")
    bounty_list.add_argument("--status", choices=STATUSES, help="Filter by status")
    bounty_list.add_argument("--program", help="Filter by program name")

    # bounty add
    bounty_add = bounty_subparsers.add_parser("add", help="Log a new submission")
    bounty_add.add_argument("program", help="Bounty program / target name")
    bounty_add.add_argument("title", help="Short title of the finding")
    bounty_add.add_argument("--severity", help="e.g. critical, high, medium, low, info")
    bounty_add.add_argument("--platform", help="e.g. hackerone, bugcrowd, intigriti, direct")
    bounty_add.add_argument("--url", help="Link to the submitted report")
    bounty_add.add_argument("--hours", type=float, help="Hours spent finding/writing it up")
    bounty_add.add_argument("--notes", help="Free-text notes")

    # bounty show
    bounty_show = bounty_subparsers.add_parser("show", help="Show a submission's detail and history")
    bounty_show.add_argument("submission_id", help="Submission ID to show")

    # bounty update
    bounty_update = bounty_subparsers.add_parser("update", help="Update a submission's status")
    bounty_update.add_argument("submission_id", help="Submission ID to update")
    bounty_update.add_argument("status", choices=STATUSES, help="New status")

    # bounty pay
    bounty_pay = bounty_subparsers.add_parser("pay", help="Record a payout and mark the submission paid")
    bounty_pay.add_argument("submission_id", help="Submission ID that was paid")
    bounty_pay.add_argument("amount", type=float, help="Payout amount")
    bounty_pay.add_argument("--currency", default="USD", help="Currency code (default: USD)")

    # bounty remove
    bounty_remove = bounty_subparsers.add_parser("remove", aliases=["rm", "delete"], help="Remove a submission")
    bounty_remove.add_argument("submission_id", help="Submission ID to remove")

    # bounty stats
    bounty_subparsers.add_parser("stats", help="Win rate, total payout, $/hour across all submissions")

    bounty_parser.set_defaults(func=cmd_bounty)
