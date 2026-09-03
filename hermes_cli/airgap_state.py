"""Storage for Air Gap — the lockdown manifest.

Air Gap is an *auditor and pauser*, not a network firewall: it cannot make
a promise this codebase has no way to keep (blocking outbound traffic at
the OS level is out of scope for a CLI subcommand, and claiming otherwise
would be a dangerous false promise on a confidential engagement). What it
actually does, honestly:

* enumerates the automations already in this install that reach the
  network on a schedule with no human in the loop (cron jobs and Signal
  Watch rules with an external ``deliver`` target) and pauses them,
  recording exactly which ones it paused so ``restore`` can be precise;
* enumerates MCP servers configured with a remote (http/https) transport,
  which it cannot safely disable out from under a possibly-running
  session — it reports them so the operator can remove them by hand.

One manifest file (``airgap/manifest.json``) under ``INDAGIS_HOME``,
holding the lockdown's current state and the IDs it paused.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from hermes_constants import get_indagis_home
from hermes_time import now as _hermes_now
from utils import atomic_replace


def _airgap_dir() -> Path:
    d = get_indagis_home() / "airgap"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _manifest_file() -> Path:
    return _airgap_dir() / "manifest.json"


def _atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp", prefix=".airgap_")
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


def load_manifest() -> Optional[Dict[str, Any]]:
    path = _manifest_file()
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


def save_manifest(
    *,
    engagement: str,
    paused_cron_job_ids: List[str],
    paused_watch_ids: List[str],
    remote_mcp_servers: List[str],
) -> Dict[str, Any]:
    manifest = {
        "engagement": engagement,
        "locked_down_at": _hermes_now().isoformat(),
        "paused_cron_job_ids": paused_cron_job_ids,
        "paused_watch_ids": paused_watch_ids,
        "remote_mcp_servers_at_lockdown": remote_mcp_servers,
        "restored_at": None,
    }
    _atomic_write_json(_manifest_file(), manifest)
    return manifest


def mark_restored() -> Optional[Dict[str, Any]]:
    manifest = load_manifest()
    if manifest is None:
        return None
    manifest["restored_at"] = _hermes_now().isoformat()
    _atomic_write_json(_manifest_file(), manifest)
    return manifest


def clear_manifest() -> None:
    path = _manifest_file()
    try:
        path.unlink()
    except OSError:
        pass
