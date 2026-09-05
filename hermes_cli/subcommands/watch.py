"""``indagis watch`` subcommand parser — Signal Watch rules.

Mirrors ``hermes_cli/subcommands/cron.py``'s shape: same
subparsers-with-dest pattern, same ``func=cmd_watch`` dispatch, handler
injected to avoid importing ``main`` (cycle avoidance).
"""

from __future__ import annotations

from typing import Callable

from hermes_cli.watch_checks import CHECKERS


def build_watch_parser(subparsers, *, cmd_watch: Callable) -> None:
    """Attach the ``watch`` subcommand (and its sub-actions) to ``subparsers``."""
    watch_parser = subparsers.add_parser(
        "watch",
        help="Signal Watch — proactive alerts on IOC/target changes",
        description=(
            "Schedule a periodic check that stays silent until its condition "
            "fires, then delivers an alert through the messaging gateway. "
            "Built on cron's no_agent watchdog pattern — see 'indagis cron'."
        ),
    )
    watch_subparsers = watch_parser.add_subparsers(dest="watch_command")

    # watch list
    watch_list = watch_subparsers.add_parser("list", help="List watch rules")
    watch_list.add_argument("--all", action="store_true", help="Include paused rules")

    # watch create
    watch_create = watch_subparsers.add_parser("create", help="Create a watch rule")
    watch_create.add_argument(
        "kind", choices=sorted(CHECKERS), help="What kind of check to run"
    )
    watch_create.add_argument(
        "target",
        help=(
            "What to watch: a domain for rdap-domain, a URL for url-hash, "
            "a free-text keyword (e.g. a product name) for cve-keyword, "
            "an email address for breach-email, a domain for breach-domain"
        ),
    )
    watch_create.add_argument(
        "--schedule",
        required=True,
        help="Schedule like 'every 30m', 'every 2h', or '0 9 * * *' (cron expression)",
    )
    watch_create.add_argument(
        "--deliver",
        required=True,
        help="Where alerts go: telegram, slack, discord, or platform:chat_id",
    )
    watch_create.add_argument("--name", help="Optional human-friendly rule name")

    # watch show
    watch_show = watch_subparsers.add_parser("show", help="Show a watch rule's detail and last-seen state")
    watch_show.add_argument("watch_id", help="Watch ID to show")

    # lifecycle actions
    watch_pause = watch_subparsers.add_parser("pause", help="Pause a watch rule")
    watch_pause.add_argument("watch_id", help="Watch ID to pause")

    watch_resume = watch_subparsers.add_parser("resume", help="Resume a paused watch rule")
    watch_resume.add_argument("watch_id", help="Watch ID to resume")

    watch_remove = watch_subparsers.add_parser(
        "remove", aliases=["rm", "delete"], help="Remove a watch rule"
    )
    watch_remove.add_argument("watch_id", help="Watch ID to remove")

    watch_run = watch_subparsers.add_parser(
        "run", help="Run a watch rule's check immediately (always prints a result)"
    )
    watch_run.add_argument("watch_id", help="Watch ID to check now")

    # watch status
    watch_subparsers.add_parser("status", help="Summary + gateway-running check")

    watch_parser.set_defaults(func=cmd_watch)
