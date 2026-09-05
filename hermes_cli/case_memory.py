"""Case Memory — cross-investigation IOC correlation index.

Reads evidence-store JSON files (the format produced by
``optional-skills/security/oss-forensics/scripts/evidence-store.py``, or
any tool emitting the same ``evidence[]`` shape with an ``ioc_type`` field)
and folds their IOC entries into a global index under
``INDAGIS_HOME/case_memory/``. The payoff is ``correlate``: run it against
a fresh investigation's evidence store and it flags every indicator that
was *also* seen in a prior, unrelated case — infrastructure reuse across
campaigns is exactly the kind of connection a single-investigation tool
can't see and a human juggling many cases easily misses.

Mirrors ``hermes_cli/watch.py``'s structure and output style deliberately.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from hermes_cli.case_memory_state import (
    list_investigations,
    list_iocs,
    lookup_ioc,
    record_investigation,
    record_sighting,
    stats,
)
from hermes_cli.colors import Colors, color


def _load_evidence_store(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if not isinstance(data, dict) or "evidence" not in data:
        raise ValueError(
            "Not an evidence-store file — expected a JSON object with an "
            "'evidence' array (the format 'evidence-store.py' produces)."
        )
    return data


def _iocs_from_store(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [e for e in data.get("evidence", []) if e.get("type") == "ioc" and e.get("content")]


def case_ingest(store_path: str) -> None:
    try:
        data = _load_evidence_store(store_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(color(f"Failed to read {store_path}: {exc}", Colors.RED))
        return

    investigation = data.get("metadata", {}).get("investigation") or Path(store_path).stem
    resolved_path = str(Path(store_path).resolve())
    record_investigation(resolved_path, investigation)

    iocs = _iocs_from_store(data)
    new_correlations = 0
    for ioc in iocs:
        is_correlation = record_sighting(
            ioc_type=ioc.get("ioc_type"),
            value=ioc.get("content", ""),
            investigation=investigation,
            store_path=resolved_path,
            evidence_id=ioc.get("id"),
            actor=ioc.get("actor"),
            source=ioc.get("source"),
        )
        if is_correlation:
            new_correlations += 1

    print(color(f"✓ Ingested {len(iocs)} IOC(s) from '{investigation}'", Colors.GREEN))
    if new_correlations:
        print(
            color(
                f"  ⚠ {new_correlations} of them were already seen in a different "
                f"investigation — run 'indagis case correlate {store_path}' for details.",
                Colors.YELLOW,
            )
        )


def case_correlate(store_path: str) -> None:
    try:
        data = _load_evidence_store(store_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(color(f"Failed to read {store_path}: {exc}", Colors.RED))
        return

    investigation = data.get("metadata", {}).get("investigation") or Path(store_path).stem
    iocs = _iocs_from_store(data)
    if not iocs:
        print(color("No IOC-type evidence entries found in this store.", Colors.DIM))
        return

    found_any = False
    for ioc in iocs:
        value = ioc.get("content", "")
        existing = lookup_ioc(value)
        if existing is None:
            continue
        other_sightings = [s for s in existing["sightings"] if s.get("investigation") != investigation]
        if not other_sightings:
            continue
        found_any = True
        other_cases = sorted({s["investigation"] for s in other_sightings})
        print(f"  {color(value, Colors.YELLOW)} ({existing.get('type', 'OTHER')})")
        print(f"    also seen in: {', '.join(other_cases)}")

    if not found_any:
        print(color("No cross-investigation matches — every IOC in this store is new to Case Memory.", Colors.DIM))


def case_lookup(value: str) -> None:
    entry = lookup_ioc(value)
    if entry is None:
        print(color(f"No prior sighting of '{value}'.", Colors.DIM))
        return

    investigations = sorted({s["investigation"] for s in entry["sightings"]})
    print(f"IOC:          {entry.get('value')}")
    print(f"Type:         {entry.get('type')}")
    print(f"First seen:   {entry.get('first_seen')}")
    print(f"Last seen:    {entry.get('last_seen')}")
    print(f"Seen in {len(investigations)} investigation(s): {', '.join(investigations)}")
    print("Sightings:")
    for s in entry["sightings"]:
        actor = f" | actor: {s['actor']}" if s.get("actor") else ""
        print(f"    [{s.get('investigation')}] {s.get('evidence_id') or '?'} — {s.get('source') or '?'}{actor}")


def case_list(ioc_type: Optional[str] = None) -> None:
    entries = list_iocs(ioc_type)
    if not entries:
        print(color("No IOCs indexed yet.", Colors.DIM))
        print(color("Ingest an evidence store with 'indagis case ingest <path/to/evidence.json>'", Colors.DIM))
        return

    print()
    print(color("┌─────────────────────────────────────────────────────────────────────────┐", Colors.CYAN))
    print(color("│                     Case Memory — Indexed IOCs                          │", Colors.CYAN))
    print(color("└─────────────────────────────────────────────────────────────────────────┘", Colors.CYAN))
    print()

    for entry in entries:
        investigations = sorted({s["investigation"] for s in entry["sightings"]})
        cross = color(" [cross-case]", Colors.YELLOW) if len(investigations) > 1 else ""
        print(f"  {color(entry.get('value', '?'), Colors.YELLOW)} ({entry.get('type', 'OTHER')}){cross}")
        print(f"    Seen in: {', '.join(investigations)}")
        print(f"    Last seen: {entry.get('last_seen', '?')}")
        print()


def case_investigations() -> None:
    entries = list_investigations()
    if not entries:
        print(color("No investigations ingested yet.", Colors.DIM))
        return
    print()
    for entry in entries:
        print(f"  {color(entry.get('name', '?'), Colors.YELLOW)}")
        print(f"    Store:     {entry.get('store_path', '?')}")
        print(f"    Ingested:  {entry.get('first_ingested_at', '?')} (last: {entry.get('last_ingested_at', '?')})")
        print()


def case_stats() -> None:
    s = stats()
    print(f"Investigations:            {s['total_investigations']}")
    print(f"Indexed IOCs:               {s['total_iocs']}")
    print(f"Cross-investigation IOCs:   {s['cross_investigation_iocs']}")
    print(f"By type:                    {json.dumps(s['by_type'], indent=2)}")


def case_command(args) -> None:
    action = getattr(args, "case_command", None)
    if action in (None, "list"):
        case_list(ioc_type=getattr(args, "type", None))
    elif action == "ingest":
        case_ingest(args.store_path)
    elif action == "correlate":
        case_correlate(args.store_path)
    elif action == "lookup":
        case_lookup(args.value)
    elif action == "investigations":
        case_investigations()
    elif action == "stats":
        case_stats()
    else:
        print(color(f"Unknown case subcommand: {action}", Colors.RED), file=sys.stderr)
