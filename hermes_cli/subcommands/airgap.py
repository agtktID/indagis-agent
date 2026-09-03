"""``indagis airgap`` subcommand parser — confidential/offline-only
engagement mode.

Mirrors ``hermes_cli/subcommands/watch.py``'s shape: same
subparsers-with-dest pattern, same ``func=cmd_airgap`` dispatch, handler
injected to avoid importing ``main`` (cycle avoidance).
"""

from __future__ import annotations

from typing import Callable


def build_airgap_parser(subparsers, *, cmd_airgap: Callable) -> None:
    """Attach the ``airgap`` subcommand (and its sub-actions) to ``subparsers``."""
    airgap_parser = subparsers.add_parser(
        "airgap",
        help="Air Gap — pause network-reaching automations for a confidential engagement",
        description=(
            "Pauses cron jobs and Signal Watch rules that deliver externally, "
            "and reports MCP servers with a remote transport. Not a network "
            "firewall — see 'indagis airgap status' for exactly what it does "
            "and does not control."
        ),
    )
    airgap_subparsers = airgap_parser.add_subparsers(dest="airgap_command")

    # airgap status
    airgap_subparsers.add_parser("status", help="Show current lockdown state and network-reaching automations")

    # airgap lockdown
    airgap_lockdown = airgap_subparsers.add_parser(
        "lockdown", help="Pause every automation with an external deliver target"
    )
    airgap_lockdown.add_argument("engagement", help="Name of the confidential engagement (for the audit record)")

    # airgap restore
    airgap_subparsers.add_parser("restore", help="Resume exactly what the last lockdown paused")

    # airgap report
    airgap_subparsers.add_parser("report", help="Print the audit record for the current/last lockdown")

    airgap_parser.set_defaults(func=cmd_airgap)
