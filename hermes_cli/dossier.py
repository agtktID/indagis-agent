"""Dossier Builder — turn an evidence store into a shareable investigation
report (Markdown).

Case Memory (``hermes_cli/case_memory.py``) answers "have I seen this IOC
before" one indicator at a time. Scope Sync (``hermes_cli/scope.py``)
answers "is this target authorized" one target at a time. Neither produces
something you can actually hand to a client, a program owner, or a bounty
triage team — an investigation report needs the whole picture assembled
once: the evidence timeline, which IOCs cross-correlate with other cases,
whether the targets touched were in the authorized scope, and the chain of
custody, all in one document.

``build_dossier`` reads the same evidence-store JSON shape Case Memory
already ingests (metadata / evidence[] / chain_of_custody[] — see
``optional-skills/security/oss-forensics/scripts/evidence-store.py``) and
renders a single Markdown report. It is a read-only view: it never writes
to the evidence store, Case Memory's index, or Scope Sync's program list —
only to the report file the caller names.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from hermes_cli.case_memory_state import lookup_ioc
from hermes_cli.colors import Colors, color
from hermes_cli.scope_state import check_target, get_program
from hermes_time import now as _hermes_now


def _load_evidence_store(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if not isinstance(data, dict) or "evidence" not in data:
        raise ValueError(
            "Not an evidence-store file — expected a JSON object with an "
            "'evidence' array (the format 'evidence-store.py' produces)."
        )
    return data


def _integrity_issues(evidence: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Re-check each entry's recorded SHA-256 against its content.

    Mirrors ``evidence-store.py``'s own ``verify_integrity`` — duplicated
    rather than imported since that script lives under
    ``optional-skills/`` and isn't part of the installed package.
    """
    issues = []
    for entry in evidence:
        content = entry.get("content", "") or ""
        stored = entry.get("content_sha256")
        if not stored:
            continue
        computed = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if computed != stored:
            issues.append({"id": entry.get("id", "?"), "stored": stored, "computed": computed})
    return issues


def _scope_section(program: str, iocs: List[Dict[str, Any]]) -> List[str]:
    record = get_program(program)
    if record is None:
        return [
            "## Scope",
            "",
            f"Program `{program}` is not imported into Scope Sync — "
            "run `indagis scope import` first to include a scope check "
            "in this report.",
            "",
        ]

    lines = ["## Scope", "", f"**Program**: {program}", ""]
    domain_or_ip_types = {"DOMAIN", "IP_ADDRESS"}
    checked = [e for e in iocs if (e.get("ioc_type") in domain_or_ip_types)]
    if not checked:
        lines.append("No domain/IP-type IOCs in this evidence store to check against scope.")
        lines.append("")
        return lines

    out_of_scope_hits = []
    unmatched = []
    for entry in checked:
        value = entry.get("content", "")
        hits = check_target(value, program=program)
        if not hits:
            unmatched.append(value)
        elif any(h["verdict"] == "out-of-scope" for h in hits):
            out_of_scope_hits.append(value)

    lines.append(f"Checked {len(checked)} domain/IP indicator(s) against `{program}`'s imported scope.")
    lines.append("")
    if out_of_scope_hits:
        lines.append(f"⚠️ **{len(out_of_scope_hits)} indicator(s) matched an out-of-scope rule:**")
        for v in out_of_scope_hits:
            lines.append(f"- `{v}`")
        lines.append("")
    if unmatched:
        lines.append(f"{len(unmatched)} indicator(s) matched no scope rule (neither confirmed in-scope nor explicitly excluded):")
        for v in unmatched:
            lines.append(f"- `{v}`")
        lines.append("")
    if not out_of_scope_hits and not unmatched:
        lines.append("✓ Every checked indicator matched an in-scope rule.")
        lines.append("")
    return lines


def build_dossier(store_path: str, *, program: Optional[str] = None) -> str:
    """Render an evidence store as a Markdown investigation dossier."""
    data = _load_evidence_store(store_path)
    metadata = data.get("metadata", {})
    evidence = data.get("evidence", [])
    custody_log = data.get("chain_of_custody", [])
    investigation = metadata.get("investigation") or Path(store_path).stem

    lines: List[str] = [
        f"# Investigation Dossier — {investigation}",
        "",
        f"**Generated**: {_hermes_now().isoformat()}",
        f"**Evidence store**: `{store_path}`",
        f"**Target**: {metadata.get('target_repo') or 'n/a'}",
        f"**Evidence items**: {len(evidence)}",
        "",
    ]

    if program:
        iocs = [e for e in evidence if e.get("type") == "ioc" and e.get("content")]
        lines.extend(_scope_section(program, iocs))

    lines.append("## Findings summary")
    lines.append("")
    by_type: Dict[str, int] = {}
    for e in evidence:
        t = e.get("type", "unknown")
        by_type[t] = by_type.get(t, 0) + 1
    for t, count in sorted(by_type.items()):
        lines.append(f"- **{t}**: {count}")
    lines.append("")

    issues = _integrity_issues(evidence)
    if issues:
        lines.append(f"⚠️ **{len(issues)} evidence item(s) failed integrity re-check** (content changed since collection):")
        for i in issues:
            lines.append(f"- `{i['id']}`: stored `{i['stored'][:16]}...` vs computed `{i['computed'][:16]}...`")
    else:
        lines.append(f"✓ All {len(evidence)} evidence item(s) passed SHA-256 integrity re-check.")
    lines.append("")

    ioc_entries = [e for e in evidence if e.get("type") == "ioc" and e.get("content")]
    if ioc_entries:
        lines.append("## Indicators of Compromise")
        lines.append("")
        lines.append("| Value | Type | Cross-case correlation |")
        lines.append("|---|---|---|")
        for e in ioc_entries:
            value = e.get("content", "")
            ioc_type = e.get("ioc_type") or "OTHER"
            prior = lookup_ioc(value)
            if prior:
                other_cases = sorted({
                    s.get("investigation") for s in prior.get("sightings", [])
                    if s.get("investigation") != investigation
                })
                correlation = f"⚠️ also seen in: {', '.join(other_cases)}" if other_cases else "—"
            else:
                correlation = "—"
            lines.append(f"| `{value}` | {ioc_type} | {correlation} |")
        lines.append("")

    lines.append("## Evidence timeline")
    lines.append("")
    lines.append("| ID | Type | Source | Actor | Verification | Timestamp |")
    lines.append("|---|---|---|---|---|---|")
    for e in evidence:
        lines.append(
            f"| {e.get('id', '?')} | {e.get('type', '?')} | {e.get('source', '?')} "
            f"| {e.get('actor') or '—'} | {e.get('verification', '?')} "
            f"| {e.get('event_timestamp') or e.get('collected_at') or '?'} |"
        )
    lines.append("")

    if custody_log:
        lines.append("## Chain of custody")
        lines.append("")
        lines.append("| Evidence ID | Action | Timestamp | Source |")
        lines.append("|---|---|---|---|")
        for c in custody_log:
            lines.append(
                f"| {c.get('evidence_id', '?')} | {c.get('action', '?')} "
                f"| {c.get('timestamp', '?')} | {c.get('source', '?')} |"
            )
        lines.append("")

    return "\n".join(lines)


def dossier_build(store_path: str, *, program: Optional[str] = None, out_path: Optional[str] = None) -> None:
    try:
        report = build_dossier(store_path, program=program)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(color(f"Failed to build dossier from {store_path}: {exc}", Colors.RED))
        return

    if out_path:
        Path(out_path).write_text(report, encoding="utf-8")
        print(color(f"✓ Dossier written to {out_path}", Colors.GREEN))
    else:
        print(report)


def dossier_command(args) -> None:
    action = getattr(args, "dossier_command", None)
    if action == "build":
        dossier_build(args.store_path, program=getattr(args, "program", None), out_path=getattr(args, "out", None))
    else:
        import sys
        print(color(f"Unknown dossier subcommand: {action}", Colors.RED), file=sys.stderr)
