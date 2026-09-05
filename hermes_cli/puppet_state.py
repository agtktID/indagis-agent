"""Storage for Sock Puppet Manager — local bookkeeping for OSINT
investigation personas.

This is a metadata tracker only: it never creates accounts, never talks
to any platform, and never generates handles, bios, or content. What it
tracks is exactly the operational-security bookkeeping an OSINT
investigator already has to do by hand — which persona belongs to which
investigation, which platform handles it's using, and whether it's still
safe to use — so cross-case contamination (the classic OSINT OPSEC
failure: reusing a persona across investigations, or reusing a handle
that's already tied to another persona) gets caught by the tool instead
of discovered after the fact.

One flat JSON file (``puppets/registry.json``) under ``INDAGIS_HOME``,
mirroring ``scope_state.py``'s proportionate atomic-replace reasoning —
writes are all human-driven CLI actions.
"""

from __future__ import annotations

import json
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from hermes_constants import get_indagis_home
from hermes_time import now as _hermes_now
from utils import atomic_replace

STATUSES = ("active", "retired", "burned")


def _puppet_dir() -> Path:
    d = get_indagis_home() / "puppets"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _registry_file() -> Path:
    return _puppet_dir() / "registry.json"


def _atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp", prefix=".puppet_")
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


def generate_puppet_id() -> str:
    return "sock_" + uuid.uuid4().hex[:12]


def _load() -> Dict[str, Dict[str, Any]]:
    path = _registry_file()
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(data, dict):
        return {}
    personas = data.get("personas", {})
    return personas if isinstance(personas, dict) else {}


def _save(personas: Dict[str, Dict[str, Any]]) -> None:
    _atomic_write_json(_registry_file(), {"personas": personas, "updated_at": _hermes_now().isoformat()})


def create_persona(
    alias: str, *, platform: str, handle: str, investigation: Optional[str], notes: Optional[str]
) -> Dict[str, Any]:
    personas = _load()
    puppet_id = generate_puppet_id()
    record = {
        "id": puppet_id,
        "alias": alias,
        "status": "active",
        "investigation": investigation,
        "notes": notes,
        "platforms": [{"platform": platform, "handle": handle, "added_at": _hermes_now().isoformat()}],
        "created_at": _hermes_now().isoformat(),
        "last_used_at": None,
        "burn_reason": None,
    }
    personas[puppet_id] = record
    _save(personas)
    return record


def find_handle_collisions(platform: str, handle: str, *, exclude_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Other active personas already using this exact platform+handle —
    an accidental footprint leak (two personas sharing a fingerprint)."""
    hits = []
    for record in _load().values():
        if record["id"] == exclude_id or record["status"] != "active":
            continue
        for p in record.get("platforms", []):
            if p.get("platform") == platform and p.get("handle") == handle:
                hits.append(record)
                break
    return hits


def get_persona(alias_or_id: str) -> Optional[Dict[str, Any]]:
    personas = _load()
    if alias_or_id in personas:
        return personas[alias_or_id]
    for record in personas.values():
        if record.get("alias") == alias_or_id:
            return record
    return None


def list_personas(*, status: Optional[str] = None, investigation: Optional[str] = None) -> List[Dict[str, Any]]:
    personas = list(_load().values())
    if status:
        personas = [p for p in personas if p.get("status") == status]
    if investigation:
        personas = [p for p in personas if p.get("investigation") == investigation]
    return sorted(personas, key=lambda p: p.get("created_at", ""), reverse=True)


def add_platform(alias_or_id: str, platform: str, handle: str) -> Optional[Dict[str, Any]]:
    personas = _load()
    record = get_persona(alias_or_id)
    if record is None:
        return None
    record["platforms"].append({"platform": platform, "handle": handle, "added_at": _hermes_now().isoformat()})
    personas[record["id"]] = record
    _save(personas)
    return record


def mark_used(alias_or_id: str, *, investigation: Optional[str]) -> Optional[Dict[str, Any]]:
    personas = _load()
    record = get_persona(alias_or_id)
    if record is None:
        return None
    record["last_used_at"] = _hermes_now().isoformat()
    if investigation and not record.get("investigation"):
        record["investigation"] = investigation
    personas[record["id"]] = record
    _save(personas)
    return record


def set_status(alias_or_id: str, status: str, *, reason: Optional[str] = None) -> Optional[Dict[str, Any]]:
    if status not in STATUSES:
        raise ValueError(f"Unknown status: {status!r} (expected one of {STATUSES})")
    personas = _load()
    record = get_persona(alias_or_id)
    if record is None:
        return None
    record["status"] = status
    if status == "burned":
        record["burn_reason"] = reason
    personas[record["id"]] = record
    _save(personas)
    return record
