"""``indagis attribution`` subcommand parser — Attribution Confidence Scorer.

Mirrors ``hermes_cli/subcommands/dossier.py``'s shape: subparsers-with-dest,
``func=cmd_attribution`` dispatch, handler injected to avoid importing
``main`` (cycle avoidance).
"""

from __future__ import annotations

from typing import Callable


def build_attribution_parser(subparsers, *, cmd_attribution: Callable) -> None:
    """Attach the ``attribution`` subcommand (and its sub-actions) to ``subparsers``."""
    attribution_parser = subparsers.add_parser(
        "attribution",
        help="Attribution Confidence Scorer — NATO/Admiralty source-reliability rating",
        description=(
            "Rate an evidence store's findings on the NATO/Admiralty "
            "two-axis scale (source reliability A-F × information "
            "credibility 1-6), cross-referenced against Case Memory: an "
            "IOC independently seen in another investigation upgrades its "
            "credibility automatically."
        ),
    )
    attribution_subparsers = attribution_parser.add_subparsers(dest="attribution_command")

    p = attribution_subparsers.add_parser("score", help="Score an evidence store's findings")
    p.add_argument("store_path", help="Path to the evidence-store JSON file")

    attribution_subparsers.add_parser("matrix", help="Print the Admiralty reliability/credibility reference table")

    attribution_parser.set_defaults(func=cmd_attribution)
