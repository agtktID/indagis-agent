"""Storage for Scope Sync — imported bug bounty program scope.

A bounty hunter's worst mistake is testing something out of scope — an
accidental knock on infrastructure the program owner never authorized
costs trust and can cross into unauthorized-access territory. This module
holds no live connection to any platform (no scraping, no API keys,
nothing that could violate a program's ToS): it imports a file the hunter
already exported from their own dashboard (HackerOne/Bugcrowd/Intigriti
all offer a CSV or JSON scope export) and answers one question locally —
'is this target in scope for this program'.

One flat JSON file (``scope/programs.json``) under ``INDAGIS_HOME``,
written only on import/add/remove — same proportionate atomic-replace
reasoning as ``watch_state.py``'s registry.
"""

from __future__ import annotations

import ipaddress
import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from hermes_constants import get_indagis_home
from hermes_time import now as _hermes_now
from utils import atomic_replace


def _scope_dir() -> Path:
    d = get_indagis_home() / "scope"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _programs_file() -> Path:
    return _scope_dir() / "programs.json"


def _atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp", prefix=".scope_")
    try:
        with open(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.flush()
        atomic_replace(tmp_path, path)
    except BaseException:
        try:
            Path(tmp_path).unlink()
        except OSError:
            pass
        raise


def _load() -> Dict[str, Dict[str, Any]]:
    path = _programs_file()
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(data, dict):
        return {}
    programs = data.get("programs", {})
    return programs if isinstance(programs, dict) else {}


def _save(programs: Dict[str, Dict[str, Any]]) -> None:
    _atomic_write_json(_programs_file(), {"programs": programs, "updated_at": _hermes_now().isoformat()})


def import_scope(
    program: str,
    in_scope: List[Dict[str, Any]],
    out_of_scope: List[Dict[str, Any]],
    source: str,
) -> Dict[str, Any]:
    """Replace a program's scope wholesale — a re-import reflects the
    platform's current state, not an incremental merge, since scope items
    also get *removed* from programs over time."""
    programs = _load()
    record = {
        "program": program,
        "in_scope": in_scope,
        "out_of_scope": out_of_scope,
        "source": source,
        "imported_at": _hermes_now().isoformat(),
    }
    programs[program] = record
    _save(programs)
    return record


def add_entry(program: str, target: str, entry_type: str, description: Optional[str], out_of_scope: bool) -> Dict[str, Any]:
    programs = _load()
    record = programs.get(program) or {
        "program": program, "in_scope": [], "out_of_scope": [], "source": "manual",
        "imported_at": _hermes_now().isoformat(),
    }
    bucket = "out_of_scope" if out_of_scope else "in_scope"
    record[bucket].append({"target": target, "type": entry_type, "description": description})
    programs[program] = record
    _save(programs)
    return record


def get_program(program: str) -> Optional[Dict[str, Any]]:
    return _load().get(program)


def list_programs() -> List[Dict[str, Any]]:
    return sorted(_load().values(), key=lambda p: p.get("program", ""))


def remove_program(program: str) -> bool:
    programs = _load()
    if program not in programs:
        return False
    del programs[program]
    _save(programs)
    return True


def _matches(pattern: str, target: str) -> bool:
    pattern = pattern.strip().lower()
    target = target.strip().lower()
    if not pattern:
        return False
    if pattern.startswith("*."):
        base = pattern[2:]
        return target == base or target.endswith("." + base)
    if "/" in pattern:
        try:
            return ipaddress.ip_address(target) in ipaddress.ip_network(pattern, strict=False)
        except ValueError:
            pass
    return target == pattern


def check_target(target: str, program: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return every (program, verdict, matched_entry) hit for ``target``
    across all imported programs, or just one when ``program`` is given.
    A target can legitimately match rules in more than one program."""
    programs = list_programs() if program is None else [p for p in [get_program(program)] if p]
    results = []
    for prog in programs:
        for entry in prog.get("out_of_scope", []):
            if _matches(entry.get("target", ""), target):
                results.append({"program": prog["program"], "verdict": "out-of-scope", "entry": entry})
        for entry in prog.get("in_scope", []):
            if _matches(entry.get("target", ""), target):
                results.append({"program": prog["program"], "verdict": "in-scope", "entry": entry})
    return results
