"""``indagis rules`` subcommand parser — Rule Forge.

Mirrors ``hermes_cli/subcommands/watch.py``'s shape: same
subparsers-with-dest pattern, same ``func=cmd_rules`` dispatch, handler
injected to avoid importing ``main`` (cycle avoidance).
"""

from __future__ import annotations

from typing import Callable


def build_rules_parser(subparsers, *, cmd_rules: Callable) -> None:
    """Attach the ``rules`` subcommand (and its sub-actions) to ``subparsers``."""
    rules_parser = subparsers.add_parser(
        "rules",
        help="Rule Forge — auto-generate Sigma/YARA rules from Case Memory findings",
        description=(
            "Turn IOCs already indexed by Case Memory into draft Sigma and "
            "YARA rules — a starting point for a detection engineer, not a "
            "drop-in ruleset."
        ),
    )
    rules_subparsers = rules_parser.add_subparsers(dest="rules_command")

    # rules forge
    rules_forge = rules_subparsers.add_parser("forge", help="Generate rules from indexed IOCs")
    rules_forge.add_argument(
        "investigation",
        nargs="?",
        default="all",
        help="Investigation name to scope to, or 'all' (default) for every indexed IOC",
    )
    rules_forge.add_argument("--out", required=True, help="Directory to write generated rules into")
    rules_forge.add_argument("--format", choices=["sigma", "yara", "both"], default="both", help="Which rule format(s) to generate (default: both)")

    rules_parser.set_defaults(func=cmd_rules)
