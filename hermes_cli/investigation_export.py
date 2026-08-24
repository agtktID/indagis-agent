"""Markdown/JSON export for Investigations.

Mirrors :mod:`hermes_cli.session_export` (format dispatch) and
:mod:`hermes_cli.session_export_md` (YAML frontmatter + SHA256 integrity
line). Intentionally filesystem-only and side-effect-free on the
investigations store: it formats already-loaded Investigation/Evidence/
Finding/timeline data and, optionally, writes it to a user-selected
directory.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Optional

from hermes_cli import investigation_db as idb

ExportFormat = Literal["markdown", "json"]

EXPORTER_VERSION = "hermes investigation export v1"
_SHA_LINE_RE = re.compile(r"- SHA256 of exported body: `([0-9a-f]{64})`")


def normalize_export_format(fmt: str) -> ExportFormat:
    """Return the canonical export format name."""
    value = (fmt or "markdown").strip().lower()
    if value == "md":
        value = "markdown"
    if value not in {"markdown", "json"}:
        raise ValueError(f"Unsupported investigation export format: {fmt}")
    return value  # type: ignore[return-value]


def _iso_timestamp(value: Any) -> str:
    if value is None or value == "":
        return ""
    try:
        ts = float(value)
    except (TypeError, ValueError):
        return str(value)
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def render_investigation_export(
    investigation: idb.Investigation,
    *,
    evidence: list[idb.Evidence],
    findings: list[idb.Finding],
    timeline: list[dict],
    fmt: str = "markdown",
) -> str:
    """Render an investigation + its evidence/findings/timeline as text."""
    export_format = normalize_export_format(fmt)
    if export_format == "json":
        return _render_json(investigation, evidence, findings, timeline)
    return _render_markdown(investigation, evidence, findings, timeline)


def _render_json(
    investigation: idb.Investigation,
    evidence: list[idb.Evidence],
    findings: list[idb.Finding],
    timeline: list[dict],
) -> str:
    payload = {
        "investigation": investigation.to_dict(),
        "evidence": [e.to_dict() for e in evidence],
        "findings": [f.to_dict() for f in findings],
        "timeline": timeline,
        "exported_at": _iso_timestamp(time.time()),
        "exporter": EXPORTER_VERSION,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def _frontmatter_value(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return json.dumps(value)
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False)
    return json.dumps(str(value), ensure_ascii=False)


def _frontmatter_line(key: str, value: Any) -> str:
    return f"{key}: {_frontmatter_value(value)}"


def _md_escape(value: object) -> str:
    """Neutralize Markdown structure characters in an interpolated field.

    Every value rendered into this export originates from analyst- or
    tool-supplied free text (description, summary, target, content_hash)
    that is validated for authorization and secrets, but never for
    Markdown safety. A value containing a backtick can break out of the
    single-backtick code spans used throughout this template, and a value
    containing a newline can inject a new Markdown block (e.g. a forged
    ``## heading``) into the exported report. Collapsing embedded
    newlines to a space and swapping backticks for a lookalike quote
    closes both vectors without needing every field to pre-validate its
    own contents.
    """
    text = str(value if value is not None else "")
    text = text.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
    text = text.replace("`", "'")
    return text


def _render_evidence_section(evidence: list[idb.Evidence]) -> list[str]:
    lines = ["## Evidence", ""]
    if not evidence:
        lines.append("_No evidence recorded._")
        lines.append("")
        return lines
    for e in evidence:
        lines.append(f"### {_md_escape(e.description)}")
        lines.append(f"- Source: `{_md_escape(e.source)}`")
        lines.append(f"- Tool: `{_md_escape(e.tool)}`")
        lines.append(f"- Target: `{_md_escape(e.target)}`")
        lines.append(f"- Observed: {_iso_timestamp(e.observed_at)}")
        lines.append(f"- Confidence: `{_md_escape(e.confidence)}`")
        if e.content_hash:
            lines.append(f"- Hash: `{_md_escape(e.content_hash)}`")
        lines.append(f"- Evidence ID: `{e.id}`")
        lines.append("")
    return lines


def _render_findings_section(findings: list[idb.Finding]) -> list[str]:
    lines = ["## Findings", ""]
    if not findings:
        lines.append("_No findings recorded._")
        lines.append("")
        return lines
    for f in findings:
        lines.append(f"### {_md_escape(f.summary)}")
        lines.append(f"- Severity: `{_md_escape(f.severity)}`")
        lines.append(f"- Source: `{_md_escape(f.source)}`")
        lines.append(f"- Tool: `{_md_escape(f.tool)}`")
        lines.append(f"- Target: `{_md_escape(f.target)}`")
        lines.append(f"- Observed: {_iso_timestamp(f.observed_at)}")
        lines.append(f"- Confidence: `{_md_escape(f.confidence)}`")
        if f.content_hash:
            lines.append(f"- Hash: `{_md_escape(f.content_hash)}`")
        if f.evidence_ids:
            lines.append(f"- Based on evidence: {', '.join(f'`{eid}`' for eid in f.evidence_ids)}")
        lines.append(f"- Finding ID: `{f.id}`")
        lines.append("")
    return lines


def _render_timeline_section(timeline: list[dict]) -> list[str]:
    lines = ["## Timeline", ""]
    if not timeline:
        lines.append("_No timeline events._")
        lines.append("")
        return lines
    for event in timeline:
        ts = _iso_timestamp(event.get("created_at"))
        lines.append(f"- {ts} — **{_md_escape(event['kind'])}**: {_md_escape(event['message'])}")
    lines.append("")
    return lines


def _export_body_without_hash(
    investigation: idb.Investigation,
    evidence: list[idb.Evidence],
    findings: list[idb.Finding],
    timeline: list[dict],
    *,
    exported_at: float,
) -> str:
    exported_iso = _iso_timestamp(exported_at)
    frontmatter = [
        "---",
        _frontmatter_line("investigation_id", investigation.id),
        _frontmatter_line("slug", investigation.slug),
        _frontmatter_line("objective", investigation.objective),
        _frontmatter_line("scope", investigation.scope),
        _frontmatter_line("status", investigation.status),
        _frontmatter_line("created_at", _iso_timestamp(investigation.created_at)),
        _frontmatter_line("updated_at", _iso_timestamp(investigation.updated_at)),
        _frontmatter_line("evidence_count", len(evidence)),
        _frontmatter_line("finding_count", len(findings)),
        _frontmatter_line("exported_at", exported_iso),
        _frontmatter_line("exporter", EXPORTER_VERSION),
        "---",
        "",
    ]

    parts: list[str] = ["\n".join(frontmatter)]
    parts.append(f"# {investigation.objective}\n")
    parts.append(f"Investigation ID: `{investigation.id}` (`{investigation.slug}`)\n")
    parts.append(f"Status: `{investigation.status}`\n")
    parts.append(f"Authorized scope: {', '.join(f'`{s}`' for s in investigation.scope)}\n")
    parts.append("\n".join(_render_evidence_section(evidence)))
    parts.append("\n".join(_render_findings_section(findings)))
    parts.append("\n".join(_render_timeline_section(timeline)))
    parts.append("## Export verification\n")
    parts.append(f"- Investigation id: `{investigation.id}`")
    parts.append(f"- Evidence count: `{len(evidence)}`")
    parts.append(f"- Finding count: `{len(findings)}`")
    parts.append(f"- Exported at: `{exported_iso}`")
    parts.append("- SHA256 of exported body: `__SHA256_PLACEHOLDER__`")
    return "\n".join(parts).rstrip() + "\n"


def _body_for_digest(text: str) -> str:
    return _SHA_LINE_RE.sub("- SHA256 of exported body: `pending`", text)


def _render_markdown(
    investigation: idb.Investigation,
    evidence: list[idb.Evidence],
    findings: list[idb.Finding],
    timeline: list[dict],
) -> str:
    exported_at = time.time()
    body = _export_body_without_hash(investigation, evidence, findings, timeline, exported_at=exported_at)
    digest_body = body.replace("`__SHA256_PLACEHOLDER__`", "`pending`")
    digest = hashlib.sha256(digest_body.encode("utf-8")).hexdigest()
    return body.replace("__SHA256_PLACEHOLDER__", digest)


def verify_markdown_export(text: str) -> tuple[bool, str]:
    """Check a rendered Markdown export's SHA256 integrity line."""
    match = _SHA_LINE_RE.search(text)
    if not match:
        return False, "sha256 marker missing"
    actual = hashlib.sha256(_body_for_digest(text).encode("utf-8")).hexdigest()
    if actual != match.group(1):
        return False, "sha256 mismatch"
    return True, "ok"


def safe_export_filename(investigation: idb.Investigation, *, fmt: str) -> str:
    """A deterministic, path-safe filename for an investigation export."""
    export_format = normalize_export_format(fmt)
    ext = "md" if export_format == "markdown" else "json"
    return f"{investigation.slug}.{ext}"


def write_investigation_export(
    investigation: idb.Investigation,
    *,
    evidence: list[idb.Evidence],
    findings: list[idb.Finding],
    timeline: list[dict],
    output_dir: Path | str,
    fmt: str = "markdown",
    force: bool = False,
    dry_run: bool = False,
) -> Path:
    """Render and write an investigation export file. Returns its path.

    When ``dry_run`` is true, the destination path is returned but nothing is
    written — callers use this to preview where the file would land.
    Raises ``FileExistsError`` when the destination exists and
    ``force=False``.
    """
    out_dir = Path(output_dir).expanduser()
    path = out_dir / safe_export_filename(investigation, fmt=fmt)
    if dry_run:
        return path
    out_dir.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        raise FileExistsError(str(path))
    text = render_investigation_export(
        investigation, evidence=evidence, findings=findings, timeline=timeline, fmt=fmt
    )
    path.write_text(text, encoding="utf-8")
    return path
