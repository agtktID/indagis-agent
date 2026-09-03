"""``indagis dossier`` subcommand parser — investigation report generation.

Mirrors ``hermes_cli/subcommands/case.py``'s shape: subparsers-with-dest,
``func=cmd_dossier`` dispatch, handler injected to avoid importing ``main``
(cycle avoidance).
"""

from __future__ import annotations

from typing import Callable


def build_dossier_parser(subparsers, *, cmd_dossier: Callable) -> None:
    """Attach the ``dossier`` subcommand (and its sub-actions) to ``subparsers``."""
    dossier_parser = subparsers.add_parser(
        "dossier",
        help="Build a Markdown investigation report from an evidence store",
        description=(
            "Renders an evidence-store JSON file (the format "
            "'evidence-store.py' produces, also what 'indagis case ingest' "
            "reads) into a single Markdown dossier: findings summary, "
            "integrity check, IOC table with Case Memory cross-case "
            "correlation, evidence timeline, and chain of custody."
        ),
    )
    dossier_subparsers = dossier_parser.add_subparsers(dest="dossier_command")

    p = dossier_subparsers.add_parser("build", help="Build a dossier from an evidence store")
    p.add_argument("store_path", help="Path to the evidence-store JSON file")
    p.add_argument("--program", help="Scope Sync program name to check IOCs against")
    p.add_argument("--out", help="Write the report to this path instead of stdout")

    dossier_parser.set_defaults(func=cmd_dossier)
