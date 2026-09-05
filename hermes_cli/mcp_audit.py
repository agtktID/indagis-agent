"""MCP Vetting Firewall — ``indagis mcp audit <name>``.

``hermes_cli/mcp_security.py`` scans a server's *launch config* (command,
args, env) for known backdoor shapes before it's ever spawned. This module
scans something different: the *running* server's advertised tool
``description`` and ``inputSchema`` fields — the actual attack surface in
real "tool poisoning" incidents (npm's ``postmark-mcp`` silently BCC'd
outbound mail from 437,000+ environments by hiding the behavior in a tool
description the model reads but the user never sees; a 2026 audit found
9/11 public MCP registries accept a malicious submission with no
meaningful review).

A launch-config scan can't catch this shape at all — the command is a
plain, harmless-looking ``npx some-package``. The payload lives entirely
in what the server *says its tools do* once connected, which is exactly
what a user approves without reading (a tool description is often 200+
words of TypeScript-schema boilerplate).

v1 is deliberately advisory, not a hard gate: it prints findings, stores
an audit record (verdict + tool-list hash) via ``mcp_audit_state.py``, and
flags drift — a tool list whose hash changed since the last audit — but
never blocks a server from connecting. Turning specific finding classes
into a hard gate is a follow-up once the pattern set has real-world
mileage; false positives that silently break a legitimate server would be
worse than the risk being mitigated.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
from typing import Any, Dict, List, Optional, Tuple

CheckResult = Dict[str, Any]

# ── Pattern catalogue ───────────────────────────────────────────────────
# Each entry: (severity, label, compiled regex). Matched against a tool's
# description and its inputSchema flattened to text. These are the same
# family of signals documented in 2026 "tool poisoning" writeups: text
# aimed at the *model* reading the description, not the user, so it reads
# as an instruction rather than documentation.

_INSTRUCTION_OVERRIDE = re.compile(
    r"\bignore (?:all )?(?:previous|prior|the above)\b"
    r"|\bdisregard (?:previous|prior|the system prompt)\b"
    r"|\boverrides? (?:any|all|other) (?:instructions|rules)\b"
    r"|\byou must (?:always|never|first)\b"
    r"|\bthis (?:tool|instruction) (?:takes|has) (?:priority|precedence)\b",
    re.IGNORECASE,
)

_COVERT_ACTION = re.compile(
    r"\bdo not (?:tell|inform|mention|show) the user\b"
    r"|\bwithout (?:telling|informing|notifying) the user\b"
    r"|\bsecretly\b"
    r"|\bhidden from the user\b"
    r"|\bthe user (?:does not|doesn't) need to (?:know|see)\b",
    re.IGNORECASE,
)

_EXFIL_INSTRUCTION = re.compile(
    r"\bbcc\b"
    r"|\bforward (?:a copy|all|every) (?:of )?(?:email|message)s?\b"
    r"|\balso send (?:a copy|this|it) to\b"
    r"|\bcc[: ]\S+@\S+"
    r"|\bexfiltrat",
    re.IGNORECASE,
)

_OTHER_TOOL_HIJACK = re.compile(
    r"\bwhen (?:calling|using) (?:the )?(?:tool )?['\"]?[\w.-]+['\"]? *,? *(?:also|instead|first)\b"
    r"|\bcall this (?:tool|function) (?:before|instead of|after) (?:any )?other tools\b"
    r"|\breplace (?:the )?(?:output|result) of (?:any )?other tool\b",
    re.IGNORECASE,
)

_ZERO_WIDTH = re.compile(r"[​‌‍⁠﻿]")

_BASE64_BLOB = re.compile(r"(?:[A-Za-z0-9+/]{4}){12,}={0,2}")

_PATTERNS: Tuple[Tuple[str, str, re.Pattern], ...] = (
    ("blocked", "instruction-override", _INSTRUCTION_OVERRIDE),
    ("blocked", "covert-action", _COVERT_ACTION),
    ("blocked", "exfiltration-instruction", _EXFIL_INSTRUCTION),
    ("warn", "other-tool-hijack", _OTHER_TOOL_HIJACK),
    ("warn", "zero-width-characters", _ZERO_WIDTH),
    ("warn", "embedded-base64-blob", _BASE64_BLOB),
)


def _schema_to_text(schema: Any) -> str:
    """Flatten an inputSchema (or any JSON-ish value) into scannable text.

    A malicious payload can hide in a property's own ``description`` field
    just as easily as in the tool's top-level description, so this walks
    the whole structure rather than reading only a top-level string.
    """
    if schema is None:
        return ""
    try:
        return json.dumps(schema, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(schema)


def scan_tool(name: str, description: str, input_schema: Any) -> List[Dict[str, Any]]:
    """Scan one tool's description + inputSchema for tool-poisoning signals.

    Returns a list of finding dicts: ``{severity, pattern, tool, snippet}``.
    Empty means nothing matched.
    """
    text = f"{description or ''}\n{_schema_to_text(input_schema)}"
    findings: List[Dict[str, Any]] = []
    for severity, label, pattern in _PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        snippet = match.group(0)
        if len(snippet) > 60:
            snippet = snippet[:57] + "..."
        findings.append(
            {
                "severity": severity,
                "pattern": label,
                "tool": name,
                "snippet": snippet,
            }
        )
    return findings


def _tool_list_hash(tools: List[Dict[str, Any]]) -> str:
    """Content hash of the full tool list — the drift-detection signal.

    Sorted by tool name so a server that merely reorders its tool list
    (no content change) doesn't register a spurious drift.
    """
    ordered = sorted(tools, key=lambda t: t.get("name", ""))
    canonical = json.dumps(ordered, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def fetch_full_tool_list(
    name: str, config: dict, connect_timeout: Optional[float] = None
) -> List[Dict[str, Any]]:
    """Connect to an MCP server and return its FULL, untruncated tool list.

    Mirrors ``mcp_config.py::_probe_single_server``'s connection handling
    (same ``_ensure_mcp_loop`` / ``_connect_server`` / ``_stop_mcp_loop_if_idle``
    primitives) but keeps the complete ``description`` and ``inputSchema``
    for every tool instead of truncating to an 80-character display string
    — a security scan needs the whole text, not a UI-friendly preview.
    """
    from hermes_cli.mcp_config import _resolve_mcp_server_config, _unwrap_exception_group
    from hermes_cli.mcp_security import validate_mcp_server_entry
    from tools.mcp_tool import (
        _ensure_mcp_loop,
        _run_on_mcp_loop,
        _connect_server,
        _stop_mcp_loop_if_idle,
    )

    issues = validate_mcp_server_entry(name, config)
    if issues:
        raise ValueError("; ".join(issues))

    config = _resolve_mcp_server_config(config)
    if connect_timeout is None:
        raw_timeout = config.get("connect_timeout", 30)
        try:
            connect_timeout = max(1.0, float(raw_timeout))
        except (TypeError, ValueError):
            connect_timeout = 30.0

    _ensure_mcp_loop()
    tools_found: List[Dict[str, Any]] = []

    async def _probe():
        server = await asyncio.wait_for(_connect_server(name, config), timeout=connect_timeout)
        try:
            for t in server._tools:
                tools_found.append(
                    {
                        "name": getattr(t, "name", "") or "",
                        "description": getattr(t, "description", "") or "",
                        "inputSchema": getattr(t, "inputSchema", None),
                    }
                )
        finally:
            await server.shutdown()

    try:
        _run_on_mcp_loop(_probe(), timeout=connect_timeout + 10)
    except BaseException as exc:
        raise _unwrap_exception_group(exc) from None
    finally:
        _stop_mcp_loop_if_idle()

    return tools_found


def run_audit(name: str, config: dict, connect_timeout: Optional[float] = None) -> Dict[str, Any]:
    """Fetch a server's tools, scan them, and return an audit result.

    Does not persist anything — callers combine this with
    ``mcp_audit_state`` to store the result and detect drift against a
    prior audit.
    """
    tools = fetch_full_tool_list(name, config, connect_timeout=connect_timeout)

    findings: List[Dict[str, Any]] = []
    for tool in tools:
        findings.extend(scan_tool(tool["name"], tool["description"], tool.get("inputSchema")))

    if any(f["severity"] == "blocked" for f in findings):
        verdict = "blocked"
    elif findings:
        verdict = "warn"
    else:
        verdict = "clean"

    return {
        "server": name,
        "verdict": verdict,
        "tool_count": len(tools),
        "tool_hash": _tool_list_hash(tools),
        "findings": findings,
    }
