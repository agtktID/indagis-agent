"""Sock Puppet Manager — local bookkeeping for OSINT investigation
personas: footprint, rotation, isolation.

This module never creates accounts, never talks to a platform, and never
generates handles or content — it only tracks what an OSINT investigator
already has to manage by hand: which persona belongs to which
investigation ("cloisonnement" — isolation, so a persona never gets
reused across cases), which platform handles make up its footprint
("empreinte"), and whether it's still safe to use. Retiring an exposed
persona and creating a fresh one is the rotation cycle
('indagis puppet burn' + 'indagis puppet create').

Mirrors ``hermes_cli/scope.py``'s structure and output style deliberately.
"""

from __future__ import annotations

import sys
from typing import Optional

from hermes_cli.colors import Colors, color
from hermes_cli.puppet_state import (
    add_platform,
    create_persona,
    find_handle_collisions,
    get_persona,
    list_personas,
    mark_used,
    set_status,
)

_STATUS_COLOR = {"active": Colors.GREEN, "retired": Colors.DIM, "burned": Colors.RED}


def puppet_create(alias: str, platform: str, handle: str, investigation: Optional[str], notes: Optional[str]) -> None:
    if get_persona(alias) is not None:
        print(color(f"A persona with alias '{alias}' already exists.", Colors.RED))
        return

    collisions = find_handle_collisions(platform, handle)
    if collisions:
        print(color(f"⚠ '{platform}:{handle}' is already used by {len(collisions)} other active persona(s):", Colors.YELLOW))
        for c in collisions:
            print(f"    {c['alias']} (investigation: {c.get('investigation') or 'none'})")
        print(color("  Reusing a handle across personas defeats isolation — creating it anyway.", Colors.DIM))

    record = create_persona(alias, platform=platform, handle=handle, investigation=investigation, notes=notes)
    print(color(f"✓ Created persona '{alias}' ({record['id']})", Colors.GREEN))
    print(f"    Platform:      {platform}:{handle}")
    print(f"    Investigation: {investigation or 'none'}")


def puppet_list(status: Optional[str], investigation: Optional[str]) -> None:
    personas = list_personas(status=status, investigation=investigation)
    if not personas:
        print(color("No personas found.", Colors.DIM))
        return

    print()
    print(f"  {'Alias':<20} {'Status':<10} {'Investigation':<20} {'Platforms':<10} {'Last used'}")
    print(f"  {'─' * 20} {'─' * 10} {'─' * 20} {'─' * 10} {'─' * 10}")
    for p in personas:
        status_str = color(p["status"], _STATUS_COLOR.get(p["status"], Colors.DIM))
        print(
            f"  {p['alias']:<20} {status_str:<10} {(p.get('investigation') or '—'):<20} "
            f"{len(p.get('platforms', [])):<10} {p.get('last_used_at') or 'never'}"
        )
    print()


def puppet_show(alias: str) -> None:
    record = get_persona(alias)
    if record is None:
        print(color(f"No such persona: {alias}", Colors.RED))
        return

    print(color(f"{record['alias']}", Colors.CYAN + Colors.BOLD) + f"  ({record['id']})")
    print(f"  Status:        {color(record['status'], _STATUS_COLOR.get(record['status'], Colors.DIM))}")
    print(f"  Investigation: {record.get('investigation') or 'none'}")
    print(f"  Created:       {record.get('created_at', '?')}")
    print(f"  Last used:     {record.get('last_used_at') or 'never'}")
    if record.get("burn_reason"):
        print(color(f"  Burn reason:   {record['burn_reason']}", Colors.RED))
    if record.get("notes"):
        print(f"  Notes:         {record['notes']}")
    print("  Footprint:")
    for p in record.get("platforms", []):
        print(f"    {p['platform']}:{p['handle']}  (added {p.get('added_at', '?')})")


def puppet_add_platform(alias: str, platform: str, handle: str) -> None:
    record = get_persona(alias)
    if record is None:
        print(color(f"No such persona: {alias}", Colors.RED))
        return
    if record["status"] != "active":
        print(color(f"'{alias}' is {record['status']} — not adding to a footprint that's out of rotation.", Colors.YELLOW))
        return

    collisions = find_handle_collisions(platform, handle, exclude_id=record["id"])
    if collisions:
        print(color(f"⚠ '{platform}:{handle}' is already used by {len(collisions)} other active persona(s):", Colors.YELLOW))
        for c in collisions:
            print(f"    {c['alias']}")

    add_platform(alias, platform, handle)
    print(color(f"✓ Added {platform}:{handle} to '{alias}'", Colors.GREEN))


def puppet_use(alias: str, investigation: Optional[str]) -> None:
    record = get_persona(alias)
    if record is None:
        print(color(f"No such persona: {alias}", Colors.RED))
        return

    if record["status"] == "burned":
        print(color(f"✗ '{alias}' is BURNED — do not use it. Reason: {record.get('burn_reason') or 'unspecified'}", Colors.RED))
        return
    if record["status"] == "retired":
        print(color(f"⚠ '{alias}' is retired. Using it anyway.", Colors.YELLOW))

    bound = record.get("investigation")
    if investigation and bound and bound != investigation:
        print(color(
            f"⚠ ISOLATION WARNING: '{alias}' was created for investigation "
            f"'{bound}', not '{investigation}'. Cross-case reuse burns your "
            f"OPSEC on both cases if this persona is ever exposed.",
            Colors.RED,
        ))

    mark_used(alias, investigation=investigation)
    print(color(f"✓ Recorded use of '{alias}'" + (f" on investigation '{investigation}'" if investigation else ""), Colors.GREEN))


def puppet_burn(alias: str, reason: Optional[str]) -> None:
    record = set_status(alias, "burned", reason=reason)
    if record is None:
        print(color(f"No such persona: {alias}", Colors.RED))
        return
    print(color(f"✓ '{alias}' marked BURNED — do not reuse.", Colors.RED))
    print(color("  Rotate: create a fresh persona with 'indagis puppet create' using new, unrelated handles.", Colors.DIM))


def puppet_retire(alias: str) -> None:
    record = set_status(alias, "retired")
    if record is None:
        print(color(f"No such persona: {alias}", Colors.RED))
        return
    print(color(f"✓ '{alias}' retired.", Colors.GREEN))


def puppet_command(args) -> None:
    action = getattr(args, "puppet_command", None)
    if action in (None, "list"):
        puppet_list(getattr(args, "status", None), getattr(args, "investigation", None))
    elif action == "create":
        puppet_create(args.alias, args.platform, args.handle, getattr(args, "investigation", None), getattr(args, "notes", None))
    elif action == "show":
        puppet_show(args.alias)
    elif action == "add-platform":
        puppet_add_platform(args.alias, args.platform, args.handle)
    elif action == "use":
        puppet_use(args.alias, getattr(args, "investigation", None))
    elif action == "burn":
        puppet_burn(args.alias, getattr(args, "reason", None))
    elif action == "retire":
        puppet_retire(args.alias)
    else:
        print(color(f"Unknown puppet subcommand: {action}", Colors.RED), file=sys.stderr)
