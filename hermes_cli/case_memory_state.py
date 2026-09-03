"""Storage for Case Memory — a global index correlating IOCs across
investigations.

Investigation-scoped evidence already exists (see
``optional-skills/security/oss-forensics/scripts/evidence-store.py``'s
``EvidenceStore``, and any other tool that produces the same evidence-store
JSON shape: a ``metadata``/``evidence``/``chain_of_custody`` document with
``ioc_type`` on entries). What's missing is memory *across* those files: an
IP or domain that showed up in an investigation six months ago and just
resurfaced in a new one is exactly the kind of connection a human forgets
and a re-run agent has no way to know about.

Case Memory owns exactly one thing: ``case_memory/index.json``, a global
map from a normalized IOC (type + value) to every investigation that has
seen it. It never modifies an evidence-store file — ``ingest`` only reads
one and folds its IOC entries into the index.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from hermes_constants import get_indagis_home
from hermes_time import now as _hermes_now
from utils import atomic_replace


def _case_memory_dir() -> Path:
    d = get_indagis_home() / "case_memory"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _index_file() -> Path:
    return _case_memory_dir() / "index.json"


def _atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp", prefix=".case_memory_")
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


def normalize_ioc(ioc_type: Optional[str], value: str) -> str:
    """Fold an IOC to one canonical key regardless of source casing.

    Domains, URLs, and hashes are case-insensitive in practice even where
    the spec allows mixed case, and stray leading/trailing whitespace is
    common in copy-pasted evidence content — normalize both away so the
    same indicator always lands under the same key.
    """
    return (value or "").strip().lower()


def _ioc_key(ioc_type: Optional[str], value: str) -> str:
    return f"{ioc_type or 'OTHER'}:{normalize_ioc(ioc_type, value)}"


def _load_index() -> Dict[str, Any]:
    path = _index_file()
    if not path.exists():
        return {"iocs": {}, "investigations": {}}
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"iocs": {}, "investigations": {}}
    if not isinstance(data, dict):
        return {"iocs": {}, "investigations": {}}
    data.setdefault("iocs", {})
    data.setdefault("investigations", {})
    return data


def _save_index(data: Dict[str, Any]) -> None:
    data["updated_at"] = _hermes_now().isoformat()
    _atomic_write_json(_index_file(), data)


def record_investigation(store_path: str, name: str) -> None:
    data = _load_index()
    entry = data["investigations"].get(store_path, {})
    entry["name"] = name
    entry["store_path"] = store_path
    entry["last_ingested_at"] = _hermes_now().isoformat()
    entry.setdefault("first_ingested_at", entry["last_ingested_at"])
    data["investigations"][store_path] = entry
    _save_index(data)


def record_sighting(
    *,
    ioc_type: Optional[str],
    value: str,
    investigation: str,
    store_path: str,
    evidence_id: Optional[str],
    actor: Optional[str],
    source: Optional[str],
) -> bool:
    """Fold one IOC sighting into the index.

    Returns True if this indicator had already been seen under a
    *different* investigation before this call — i.e. this sighting is a
    cross-investigation correlation, not just a repeat within the same
    case.
    """
    key = _ioc_key(ioc_type, value)
    data = _load_index()
    entry = data["iocs"].get(key)
    is_new_correlation = False
    if entry is None:
        entry = {
            "type": ioc_type or "OTHER",
            "value": value,
            "first_seen": _hermes_now().isoformat(),
            "sightings": [],
        }
    else:
        prior_investigations = {s.get("investigation") for s in entry.get("sightings", [])}
        if investigation not in prior_investigations and prior_investigations:
            is_new_correlation = True

    entry["last_seen"] = _hermes_now().isoformat()
    entry["sightings"].append(
        {
            "investigation": investigation,
            "store_path": store_path,
            "evidence_id": evidence_id,
            "actor": actor,
            "source": source,
            "seen_at": _hermes_now().isoformat(),
        }
    )
    data["iocs"][key] = entry
    _save_index(data)
    return is_new_correlation


def lookup_ioc(value: str) -> Optional[Dict[str, Any]]:
    """Find an indicator by value alone, regardless of its recorded type —
    an analyst pasting a value usually doesn't know or care which IOC_TYPE
    bucket it was filed under originally."""
    data = _load_index()
    needle = normalize_ioc(None, value)
    for entry in data["iocs"].values():
        if normalize_ioc(entry.get("type"), entry.get("value", "")) == needle:
            return entry
    return None


def list_iocs(ioc_type: Optional[str] = None) -> List[Dict[str, Any]]:
    data = _load_index()
    entries = list(data["iocs"].values())
    if ioc_type:
        entries = [e for e in entries if e.get("type") == ioc_type]
    return sorted(entries, key=lambda e: e.get("last_seen", ""), reverse=True)


def list_investigations() -> List[Dict[str, Any]]:
    data = _load_index()
    return sorted(
        data["investigations"].values(), key=lambda e: e.get("last_ingested_at", ""), reverse=True
    )


def stats() -> Dict[str, Any]:
    data = _load_index()
    by_type: Dict[str, int] = {}
    cross_investigation = 0
    for entry in data["iocs"].values():
        by_type[entry.get("type", "OTHER")] = by_type.get(entry.get("type", "OTHER"), 0) + 1
        investigations = {s.get("investigation") for s in entry.get("sightings", [])}
        if len(investigations) > 1:
            cross_investigation += 1
    return {
        "total_iocs": len(data["iocs"]),
        "total_investigations": len(data["investigations"]),
        "by_type": by_type,
        "cross_investigation_iocs": cross_investigation,
    }
