"""Storage for Signal Watch rules and their per-rule runtime state.

Signal Watch rules are thin wrappers around ``no_agent`` cron jobs (see
``cron/jobs.py``): the heavy lifting — scheduling, locking, delivery routing —
is all cron's. This module owns only the two things cron doesn't model:

* the **registry** (``watch/registry.json``) — one row per rule, mapping a
  watch ID to its kind/target/underlying cron job ID. Written only on
  create/pause/resume/remove, all human-driven CLI actions, so a plain
  atomic replace (no flock) is proportionate — this is not the high-frequency
  jobs.json cron writes on every tick.
* **per-rule state** (``watch/state/<id>.json``) — the last-seen value the
  checker compared against (a hash, a WHOIS field, a CVE ID set). Touched
  only by that one rule's own script execution; cron already serializes a
  single job's runs, so there is no concurrent-writer risk to guard against.
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


def _watch_dir() -> Path:
    d = get_indagis_home() / "watch"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _state_dir() -> Path:
    d = _watch_dir() / "state"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _registry_file() -> Path:
    return _watch_dir() / "registry.json"


def _atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp", prefix=".watch_")
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


def generate_watch_id() -> str:
    return "wch_" + uuid.uuid4().hex[:12]


def _load_registry() -> Dict[str, Dict[str, Any]]:
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
    rules = data.get("rules", {})
    return rules if isinstance(rules, dict) else {}


def _save_registry(rules: Dict[str, Dict[str, Any]]) -> None:
    _atomic_write_json(_registry_file(), {"rules": rules, "updated_at": _hermes_now().isoformat()})


def create_watch_record(
    *,
    watch_id: str,
    kind: str,
    target: str,
    name: Optional[str],
    cron_job_id: str,
    deliver: str,
    schedule: str,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Register a watch rule under a caller-supplied ``watch_id``.

    The ID must be the same one already used for the generated cron script
    filename (``watch_<id>.py``) — the registry key and the script's
    embedded ID have to match, or the scheduled run looks up a rule that
    isn't there. Generate it once with :func:`generate_watch_id` and reuse
    it for both.
    """
    record = {
        "id": watch_id,
        "kind": kind,
        "target": target,
        "name": name or f"{kind}:{target}",
        "cron_job_id": cron_job_id,
        "deliver": deliver,
        "schedule": schedule,
        "extra": extra or {},
        "created_at": _hermes_now().isoformat(),
    }
    rules = _load_registry()
    rules[watch_id] = record
    _save_registry(rules)
    return record


def list_watch_records() -> List[Dict[str, Any]]:
    return list(_load_registry().values())


def get_watch_record(watch_id: str) -> Optional[Dict[str, Any]]:
    return _load_registry().get(watch_id)


def remove_watch_record(watch_id: str) -> bool:
    rules = _load_registry()
    if watch_id not in rules:
        return False
    del rules[watch_id]
    _save_registry(rules)
    state_path = _state_dir() / f"{watch_id}.json"
    try:
        state_path.unlink()
    except OSError:
        pass
    return True


def get_watch_state(watch_id: str) -> Dict[str, Any]:
    path = _state_dir() / f"{watch_id}.json"
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def save_watch_state(watch_id: str, state: Dict[str, Any]) -> None:
    state = dict(state)
    state["updated_at"] = _hermes_now().isoformat()
    _atomic_write_json(_state_dir() / f"{watch_id}.json", state)
