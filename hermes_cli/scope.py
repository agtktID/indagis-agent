"""Scope Sync — import authorized bug bounty scope, then check targets
against it before touching them.

Reads a scope export the hunter already pulled from their own bounty
dashboard — JSON or CSV, whatever the platform hands out — and stores it
locally so 'indagis scope check <target>' can answer in-scope /
out-of-scope / unknown before a single request goes out. This module never
talks to a bounty platform itself: no scraping, no API keys, nothing that
could brush against a program's ToS. It only reads a file the hunter
already has.

Mirrors ``hermes_cli/watch.py``'s structure and output style deliberately.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from hermes_cli.colors import Colors, color
from hermes_cli.scope_state import (
    add_entry,
    check_target,
    get_program,
    import_scope,
    list_programs,
    remove_program,
)


def _parse_json_scope(path: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object with 'in_scope'/'out_of_scope' arrays")

    def _normalize(items: Any) -> List[Dict[str, Any]]:
        out = []
        for item in items or []:
            if isinstance(item, str):
                out.append({"target": item, "type": "other", "description": None})
            elif isinstance(item, dict) and item.get("target"):
                out.append({
                    "target": item["target"],
                    "type": item.get("type", "other"),
                    "description": item.get("description"),
                })
        return out

    return _normalize(data.get("in_scope")), _normalize(data.get("out_of_scope"))


def _parse_csv_scope(path: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Best-effort parse of a bounty-platform CSV export. Column names vary
    by platform, so this looks for the common ones rather than requiring
    an exact header: a target column (target/identifier/asset_identifier),
    an optional type column, and whatever tells us in vs. out of scope
    (an explicit 'scope' column, or an 'eligible_for_bounty' boolean)."""
    in_scope: List[Dict[str, Any]] = []
    out_of_scope: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = [fn.strip().lower() for fn in (reader.fieldnames or [])]
        target_col = next((c for c in fieldnames if c in ("target", "identifier", "asset_identifier")), None)
        if target_col is None:
            raise ValueError(
                "No target column found — expected one of: target, identifier, asset_identifier"
            )
        type_col = next((c for c in fieldnames if c in ("type", "asset_type")), None)
        scope_col = next((c for c in fieldnames if c == "scope"), None)
        eligible_col = next((c for c in fieldnames if c in ("eligible_for_bounty", "eligible")), None)

        for row in reader:
            row = {k.strip().lower(): v for k, v in row.items() if k}
            target = (row.get(target_col) or "").strip()
            if not target:
                continue
            entry = {"target": target, "type": (row.get(type_col) or "other").strip() if type_col else "other", "description": None}
            is_out = False
            if scope_col:
                is_out = (row.get(scope_col) or "").strip().lower() in ("out", "out_of_scope", "out-of-scope", "false", "no")
            elif eligible_col:
                is_out = (row.get(eligible_col) or "").strip().lower() in ("false", "no", "0", "")
            (out_of_scope if is_out else in_scope).append(entry)
    return in_scope, out_of_scope


def scope_import(program: str, file_path: str) -> None:
    path = Path(file_path)
    if not path.exists():
        print(color(f"No such file: {file_path}", Colors.RED))
        return
    try:
        if path.suffix.lower() == ".csv":
            in_scope, out_of_scope = _parse_csv_scope(path)
        else:
            in_scope, out_of_scope = _parse_json_scope(path)
    except (OSError, json.JSONDecodeError, ValueError, csv.Error) as exc:
        print(color(f"Failed to parse {file_path}: {exc}", Colors.RED))
        return

    if not in_scope and not out_of_scope:
        print(color("Parsed the file but found no scope entries — nothing imported.", Colors.YELLOW))
        return

    import_scope(program, in_scope, out_of_scope, source=str(path.resolve()))
    print(color(f"✓ Imported scope for '{program}'", Colors.GREEN))
    print(f"    In scope:      {len(in_scope)}")
    print(f"    Out of scope:  {len(out_of_scope)}")


def scope_add(program: str, target: str, entry_type: str, description: str, out_of_scope: bool) -> None:
    add_entry(program, target, entry_type, description, out_of_scope)
    bucket = "out-of-scope" if out_of_scope else "in-scope"
    print(color(f"✓ Added {target} to {program} ({bucket})", Colors.GREEN))


def scope_list() -> None:
    programs = list_programs()
    if not programs:
        print(color("No scope imported yet.", Colors.DIM))
        print(color("Import one with 'indagis scope import <program> <file.json|.csv>'", Colors.DIM))
        return

    print()
    print(color("┌─────────────────────────────────────────────────────────────────────────┐", Colors.CYAN))
    print(color("│                      Scope Sync — Programs                              │", Colors.CYAN))
    print(color("└─────────────────────────────────────────────────────────────────────────┘", Colors.CYAN))
    print()

    for prog in programs:
        print(f"  {color(prog['program'], Colors.YELLOW)}")
        print(f"    In scope:      {len(prog.get('in_scope', []))}")
        print(f"    Out of scope:  {len(prog.get('out_of_scope', []))}")
        print(f"    Imported:      {prog.get('imported_at', '?')}  (source: {prog.get('source', '?')})")
        print()


def scope_show(program: str) -> None:
    prog = get_program(program)
    if prog is None:
        print(color(f"No such program: {program}", Colors.RED))
        return
    print(f"Program:   {prog['program']}")
    print(f"Imported:  {prog.get('imported_at', '?')} (source: {prog.get('source', '?')})")
    print("In scope:")
    for e in prog.get("in_scope", []):
        desc = f" — {e['description']}" if e.get("description") else ""
        print(f"    {color(e['target'], Colors.GREEN)} [{e.get('type', 'other')}]{desc}")
    print("Out of scope:")
    for e in prog.get("out_of_scope", []):
        desc = f" — {e['description']}" if e.get("description") else ""
        print(f"    {color(e['target'], Colors.RED)} [{e.get('type', 'other')}]{desc}")


#: Exit codes for ``indagis scope check``. This command is a pre-flight
#: safety gate — the module docstring tells you to check a target "before a
#: single request goes out" — so it is written into shell as
#: ``indagis scope check "$t" && run_scan "$t"``. That idiom is only safe if
#: a refusal is non-zero: returning 0 for OUT OF SCOPE means the wrapper
#: scans a host the program explicitly forbade, with the correct warning
#: printed right above it. Both refusals are non-zero for that reason, and
#: they are distinct so a caller that wants to treat "no rule matched"
#: differently from "explicitly forbidden" can.
SCOPE_CHECK_OK = 0
SCOPE_CHECK_OUT_OF_SCOPE = 1
SCOPE_CHECK_UNKNOWN = 2


def scope_check(target: str, program: str = None) -> int:
    results = check_target(target, program=program)
    if not results:
        print(color(f"⚠ '{target}' matches no imported scope rule — verdict unknown, treat as out of scope.", Colors.YELLOW))
        return SCOPE_CHECK_UNKNOWN

    out_hits = [r for r in results if r["verdict"] == "out-of-scope"]
    in_hits = [r for r in results if r["verdict"] == "in-scope"]

    if out_hits:
        print(color(f"✗ OUT OF SCOPE — do not test '{target}'", Colors.RED))
        for r in out_hits:
            print(f"    [{r['program']}] matched rule: {r['entry']['target']}")
        if in_hits:
            print(color("  (also matched an in-scope rule elsewhere — out-of-scope always wins)", Colors.DIM))
        return SCOPE_CHECK_OUT_OF_SCOPE

    print(color(f"✓ IN SCOPE — '{target}'", Colors.GREEN))
    for r in in_hits:
        print(f"    [{r['program']}] matched rule: {r['entry']['target']}")
    return SCOPE_CHECK_OK


#: Scope-entry ``type`` values that are never a fingerprintable host, no
#: matter how their ``target`` string looks — a reversed-domain mobile app
#: ID (``com.acme.mobileapp``) or a source-code repo path can read exactly
#: like a hostname to a string heuristic. Bounty platforms commonly use
#: these type names; unrecognized/unset types (including the "other"
#: default a plain string import gets) fall through to the shape check.
_NON_HOST_TYPES = frozenset({
    "mobile", "android", "ios", "hardware", "executable", "binary",
    "source_code", "source-code", "smart_contract", "smart-contract",
})


def _derive_host(entry: Dict[str, Any]) -> Optional[str]:
    """Turn one scope entry into a single fingerprintable host, or ``None``
    when the entry isn't shaped like one (a CIDR range, a mobile app ID, an
    email address — nothing Surface Diff's HTTP/TLS probe can snapshot)."""
    if (entry.get("type") or "").strip().lower() in _NON_HOST_TYPES:
        return None
    target = (entry.get("target") or "").strip()
    if not target or " " in target or "@" in target:
        return None
    if target.startswith("*."):
        # Wildcard domains fingerprint the base domain — the concrete host
        # a certificate/DNS change on the wildcard would actually show up on.
        return target[2:] or None
    if "://" in target:
        netloc = urlparse(target).netloc
        return netloc.split(":")[0] or None
    if "/" in target:
        # CIDR range or path-shaped entry — not a single host.
        return None
    return target


def scope_autopilot(program: str, schedule: str, deliver: str, *, dry_run: bool = False) -> None:
    """Onboard every in-scope, host-shaped target of ``program`` onto
    Surface Diff's continuous monitoring — Recon Autopilot.

    Scope Sync answers "is this target authorized" one target at a time;
    Surface Diff monitors one target at a time once you've told it to.
    Between the two, onboarding a program with dozens of in-scope assets
    means running 'indagis surface schedule' by hand for each one. This
    closes that loop: every in-scope entry that resolves to a concrete
    host gets scheduled, and — critically — out-of-scope entries are never
    even considered, so an autopilot run can't accidentally start probing
    something the program owner excluded.

    Targets already under Surface Diff monitoring (an existing snapshot
    directory) are skipped on a re-run rather than re-scheduled, so running
    this again after a scope re-import only onboards what's new.
    """
    from hermes_cli.surface import surface_schedule
    from hermes_cli.surface_state import list_targets

    prog = get_program(program)
    if prog is None:
        print(color(f"No such program: {program}", Colors.RED))
        return

    already_monitored = set(list_targets())
    candidates: List[str] = []
    skipped_unhostlike = 0
    for entry in prog.get("in_scope", []):
        host = _derive_host(entry)
        if host is None:
            skipped_unhostlike += 1
            continue
        candidates.append(host)

    new_targets = sorted({h for h in candidates if h not in already_monitored})
    skipped_existing = len(set(candidates)) - len(new_targets)

    print(color(f"Recon Autopilot — {program}", Colors.CYAN + Colors.BOLD))
    print(f"  In-scope entries:        {len(prog.get('in_scope', []))}")
    print(f"  Not host-shaped (skip):  {skipped_unhostlike}")
    print(f"  Already monitored:       {skipped_existing}")
    print(f"  New targets to onboard:  {len(new_targets)}")
    print()

    if not new_targets:
        print(color("Nothing new to onboard.", Colors.DIM))
        return

    if dry_run:
        print(color("Dry run — would schedule monitoring for:", Colors.YELLOW))
        for host in new_targets:
            print(f"    {host}")
        return

    for host in new_targets:
        surface_schedule(host, host, schedule, deliver)


def scope_remove(program: str) -> None:
    if not remove_program(program):
        print(color(f"No such program: {program}", Colors.RED))
        return
    print(color(f"✓ Removed scope for '{program}'", Colors.GREEN))


def scope_command(args) -> int | None:
    action = getattr(args, "scope_command", None)
    if action in (None, "list"):
        scope_list()
    elif action == "import":
        scope_import(args.program, args.file_path)
    elif action == "add":
        scope_add(
            program=args.program, target=args.target,
            entry_type=getattr(args, "type", None) or "other",
            description=getattr(args, "description", None),
            out_of_scope=getattr(args, "out_of_scope", False),
        )
    elif action == "show":
        scope_show(args.program)
    elif action == "check":
        return scope_check(args.target, program=getattr(args, "program", None))
    elif action == "autopilot":
        scope_autopilot(
            args.program, args.schedule, args.deliver, dry_run=getattr(args, "dry_run", False)
        )
    elif action == "remove":
        scope_remove(args.program)
    else:
        print(color(f"Unknown scope subcommand: {action}", Colors.RED), file=sys.stderr)
