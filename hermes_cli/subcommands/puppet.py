"""``indagis puppet`` subcommand parser — Sock Puppet Manager.

Mirrors ``hermes_cli/subcommands/scope.py``'s shape: same
subparsers-with-dest pattern, same ``func=cmd_puppet`` dispatch, handler
injected to avoid importing ``main`` (cycle avoidance).
"""

from __future__ import annotations

from typing import Callable


def build_puppet_parser(subparsers, *, cmd_puppet: Callable) -> None:
    """Attach the ``puppet`` subcommand (and its sub-actions) to ``subparsers``."""
    puppet_parser = subparsers.add_parser(
        "puppet",
        help="Sock Puppet Manager — OSINT persona bookkeeping (footprint, rotation, isolation)",
        description=(
            "Local metadata tracking for OSINT investigation personas — "
            "never creates accounts or generates content. Tracks which "
            "persona belongs to which investigation, its platform "
            "footprint, and whether it's still safe to use, so "
            "cross-case reuse and handle collisions get caught before "
            "they burn an investigation's OPSEC."
        ),
    )
    puppet_subparsers = puppet_parser.add_subparsers(dest="puppet_command")

    # puppet list
    puppet_list = puppet_subparsers.add_parser("list", help="List personas")
    puppet_list.add_argument("--status", choices=["active", "retired", "burned"], help="Filter by status")
    puppet_list.add_argument("--investigation", help="Filter by investigation")

    # puppet create
    puppet_create = puppet_subparsers.add_parser("create", help="Create a new persona")
    puppet_create.add_argument("alias", help="A memorable local name for this persona (not the platform handle)")
    puppet_create.add_argument("--platform", required=True, help="Platform name (e.g. twitter, linkedin, forum-xyz)")
    puppet_create.add_argument("--handle", required=True, help="The handle/username used on that platform")
    puppet_create.add_argument("--investigation", help="Investigation this persona is scoped to")
    puppet_create.add_argument("--notes", help="Free-text notes (cover story, purpose, etc.)")

    # puppet show
    puppet_show = puppet_subparsers.add_parser("show", help="Show a persona's full record and footprint")
    puppet_show.add_argument("alias", help="Persona alias or ID")

    # puppet add-platform
    puppet_add = puppet_subparsers.add_parser("add-platform", help="Add another platform handle to a persona's footprint")
    puppet_add.add_argument("alias", help="Persona alias or ID")
    puppet_add.add_argument("--platform", required=True, help="Platform name")
    puppet_add.add_argument("--handle", required=True, help="Handle/username on that platform")

    # puppet use
    puppet_use = puppet_subparsers.add_parser("use", help="Record use of a persona (checks isolation, refuses if burned)")
    puppet_use.add_argument("alias", help="Persona alias or ID")
    puppet_use.add_argument("--investigation", help="Investigation this use is for")

    # puppet burn
    puppet_burn = puppet_subparsers.add_parser("burn", help="Mark a persona compromised/exposed — never reuse it")
    puppet_burn.add_argument("alias", help="Persona alias or ID")
    puppet_burn.add_argument("--reason", help="Why it's burned")

    # puppet retire
    puppet_retire = puppet_subparsers.add_parser("retire", help="Retire a persona (investigation closed, not exposed)")
    puppet_retire.add_argument("alias", help="Persona alias or ID")

    puppet_parser.set_defaults(func=cmd_puppet)
