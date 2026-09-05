"""Storage for MCP Vetting Firewall audit results (``mcp/audit.json``).

One row per server name, keyed by the name used in ``config.yaml``'s
``mcp_servers`` map. Each row records the last audit's verdict, findings,
and a content hash of the server's advertised tool list (name +
description + inputSchema, untruncated) — the hash is how a re-audit
detects that a server's tools changed since it was last approved, the
exact signal that would have caught a postmark-mcp-style post-approval
behavior change (a server silently altering what a previously-vetted tool
does, after the user already trusted it).

Mirrors the storage shape used by Signal Watch (``watch_state.py``): a
single small JSON file, atomic-replaced on every write, no locking needed
because writes are all human-driven CLI actions (``indagis mcp audit``),
not high-frequency background ticks.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from hermes_constants import get_indagis_home
from hermes_time import now as _hermes_now
from utils import atomic_replace


def _mcp_dir() -> Path:
    d = get_indagis_home() / "mcp"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _audit_file() -> Path:
    return _mcp_dir() / "audit.json"


def _atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp", prefix=".mcp_audit_")
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


def _load_all() -> Dict[str, Dict[str, Any]]:
    path = _audit_file()
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    servers = data.get("servers", {}) if isinstance(data, dict) else {}
    return servers if isinstance(servers, dict) else {}


def _save_all(servers: Dict[str, Dict[str, Any]]) -> None:
    _atomic_write_json(_audit_file(), {"servers": servers, "updated_at": _hermes_now().isoformat()})


def get_audit_record(name: str) -> Optional[Dict[str, Any]]:
    """Return the last stored audit result for ``name``, or ``None``."""
    return _load_all().get(name)


def save_audit_record(
    name: str,
    *,
    verdict: str,
    tool_hash: str,
    tool_count: int,
    findings: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Persist an audit result, returning the stored record.

    ``verdict`` is ``"clean"``, ``"warn"``, or ``"blocked"`` — advisory
    only in v1 (see ``mcp_audit.py`` module docstring); nothing here
    prevents the server from being used.
    """
    record = {
        "name": name,
        "verdict": verdict,
        "tool_hash": tool_hash,
        "tool_count": tool_count,
        "findings": findings,
        "audited_at": _hermes_now().isoformat(),
    }
    servers = _load_all()
    servers[name] = record
    _save_all(servers)
    return record


def list_audit_records() -> List[Dict[str, Any]]:
    return list(_load_all().values())


def remove_audit_record(name: str) -> bool:
    servers = _load_all()
    if name not in servers:
        return False
    del servers[name]
    _save_all(servers)
    return True
