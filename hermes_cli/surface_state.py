"""Storage for Surface Diff — timestamped attack-surface snapshots and the
diff between the two most recent ones.

Each snapshot fingerprints a host with nothing beyond the standard library
and ``requests`` (already a project dependency): resolved IPs, HTTP
response headers/status/title for the plain and TLS endpoints, and the TLS
certificate's subject/issuer/SANs/expiry. No port scanner, no external
recon binary — this is what a target already tells anyone who politely
asks, snapshotted and diffed over time so a new subdomain's certificate,
a header that reveals a stack change, or a DNS record swap surfaces on
its own instead of waiting for someone to notice by hand.

Snapshots live under ``surface/<target>/<timestamp>.json``, one JSON file
per run — append-only, so history is just "the files in this directory."
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from hermes_constants import get_indagis_home
from hermes_time import now as _hermes_now

_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_target_dir_name(target: str) -> str:
    return _SAFE_NAME_RE.sub("_", target.strip())[:200] or "target"


def target_dir(target: str) -> Path:
    d = get_indagis_home() / "surface" / _safe_target_dir_name(target)
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_snapshot(target: str, snapshot: Dict[str, Any]) -> Path:
    ts = _hermes_now()
    snapshot = dict(snapshot)
    snapshot["target"] = target
    snapshot["taken_at"] = ts.isoformat()
    path = target_dir(target) / f"{ts.strftime('%Y%m%dT%H%M%S%f')}.json"
    path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    return path


def list_snapshots(target: str) -> List[Path]:
    return sorted(target_dir(target).glob("*.json"))


def load_snapshot(path: Path) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


def latest_two_snapshots(target: str) -> Optional[List[Dict[str, Any]]]:
    paths = list_snapshots(target)
    if len(paths) < 2:
        return None
    older = load_snapshot(paths[-2])
    newer = load_snapshot(paths[-1])
    if older is None or newer is None:
        return None
    return [older, newer]


def list_targets() -> List[str]:
    base = get_indagis_home() / "surface"
    if not base.exists():
        return []
    return sorted(p.name for p in base.iterdir() if p.is_dir())
