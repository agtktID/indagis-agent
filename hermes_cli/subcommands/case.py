"""``indagis case`` subcommand parser — Case Memory.

Mirrors ``hermes_cli/subcommands/watch.py``'s shape: same
subparsers-with-dest pattern, same ``func=cmd_case`` dispatch, handler
injected to avoid importing ``main`` (cycle avoidance).
"""

from __future__ import annotations

from typing import Callable

# Mirrors IOC_TYPES in optional-skills/security/oss-forensics/scripts/evidence-store.py.
# Kept as a plain literal here rather than imported: that script lives under a
# hyphenated, non-package path and is loaded dynamically (see its own test),
# not meant to be imported as a module by the rest of the CLI.
_IOC_TYPES = [
    "COMMIT_SHA", "FILE_PATH", "API_KEY", "SECRET", "IP_ADDRESS",
    "DOMAIN", "PACKAGE_NAME", "ACTOR_USERNAME", "MALICIOUS_URL",
    "WORKFLOW_FILE", "BRANCH_NAME", "TAG_NAME", "RELEASE_NAME", "OTHER",
]


def build_case_parser(subparsers, *, cmd_case: Callable) -> None:
    """Attach the ``case`` subcommand (and its sub-actions) to ``subparsers``."""
    case_parser = subparsers.add_parser(
        "case",
        help="Case Memory — cross-investigation IOC correlation index",
        description=(
            "Index IOCs from evidence-store files (see 'oss-forensics' "
            "skill) so an indicator seen in one investigation is "
            "recognized when it resurfaces in another."
        ),
    )
    case_subparsers = case_parser.add_subparsers(dest="case_command")

    # case list
    case_list = case_subparsers.add_parser("list", help="List indexed IOCs")
    case_list.add_argument("--type", choices=sorted(_IOC_TYPES), help="Filter by IOC type")

    # case ingest
    case_ingest = case_subparsers.add_parser(
        "ingest", help="Index the IOCs from an evidence-store JSON file"
    )
    case_ingest.add_argument("store_path", help="Path to an evidence-store JSON file")

    # case correlate
    case_correlate = case_subparsers.add_parser(
        "correlate",
        help="Check an evidence store's IOCs against every prior investigation",
    )
    case_correlate.add_argument("store_path", help="Path to an evidence-store JSON file")

    # case lookup
    case_lookup = case_subparsers.add_parser("lookup", help="Look up one IOC by value")
    case_lookup.add_argument("value", help="The IOC value to look up (domain, IP, hash, etc.)")

    # case investigations
    case_subparsers.add_parser("investigations", help="List ingested investigations")

    # case stats
    case_subparsers.add_parser("stats", help="Summary statistics for the index")

    case_parser.set_defaults(func=cmd_case)
