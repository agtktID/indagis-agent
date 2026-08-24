"""Tests for hermes_cli/investigation_export."""

from __future__ import annotations

import json

import pytest

from hermes_cli import investigation_db as idb
from hermes_cli import investigation_export as iexport


@pytest.fixture
def conn(tmp_path):
    c = idb.connect(db_path=tmp_path / "investigations.db")
    try:
        yield c
    finally:
        c.close()


@pytest.fixture
def populated_investigation(conn):
    inv_id = idb.create_investigation(
        conn, objective="Assess acme-corp exposure", scope=["acme.example"]
    )
    ev_id = idb.add_evidence(
        conn, inv_id, description="Open port 443", source="nmap-scan",
        tool="nmap", target="acme.example", confidence="high", content_hash="deadbeef",
    )
    idb.add_finding(
        conn, inv_id, summary="TLS misconfiguration", severity="high",
        evidence_ids=[ev_id], source="analyst", tool="manual",
        target="acme.example", confidence="high",
    )
    return idb.get_investigation(conn, inv_id)


def test_normalize_export_format():
    assert iexport.normalize_export_format("md") == "markdown"
    assert iexport.normalize_export_format("markdown") == "markdown"
    assert iexport.normalize_export_format("json") == "json"
    with pytest.raises(ValueError):
        iexport.normalize_export_format("yaml")


def test_render_json_is_valid_and_contains_provenance(conn, populated_investigation):
    inv = populated_investigation
    evidence = idb.list_evidence(conn, inv.id)
    findings = idb.list_findings(conn, inv.id)
    timeline = idb.get_timeline(conn, inv.id)

    text = iexport.render_investigation_export(
        inv, evidence=evidence, findings=findings, timeline=timeline, fmt="json"
    )
    payload = json.loads(text)

    assert payload["investigation"]["objective"] == "Assess acme-corp exposure"
    assert payload["evidence"][0]["provenance"]["tool"] == "nmap"
    assert payload["evidence"][0]["provenance"]["hash"] == "deadbeef"
    assert payload["findings"][0]["provenance"]["confidence"] == "high"
    assert len(payload["timeline"]) == 3


def test_render_markdown_has_frontmatter_and_sections(conn, populated_investigation):
    inv = populated_investigation
    evidence = idb.list_evidence(conn, inv.id)
    findings = idb.list_findings(conn, inv.id)
    timeline = idb.get_timeline(conn, inv.id)

    text = iexport.render_investigation_export(
        inv, evidence=evidence, findings=findings, timeline=timeline, fmt="markdown"
    )

    assert text.startswith("---\n")
    assert "objective:" in text
    assert "## Evidence" in text
    assert "## Findings" in text
    assert "## Timeline" in text
    assert "nmap" in text
    assert "deadbeef" in text
    assert "SHA256 of exported body:" in text


def test_markdown_integrity_hash_verifies(conn, populated_investigation):
    inv = populated_investigation
    evidence = idb.list_evidence(conn, inv.id)
    findings = idb.list_findings(conn, inv.id)
    timeline = idb.get_timeline(conn, inv.id)

    text = iexport.render_investigation_export(
        inv, evidence=evidence, findings=findings, timeline=timeline, fmt="markdown"
    )
    ok, reason = iexport.verify_markdown_export(text)
    assert ok is True, reason


def test_write_investigation_export_creates_file(conn, populated_investigation, tmp_path):
    inv = populated_investigation
    evidence = idb.list_evidence(conn, inv.id)
    findings = idb.list_findings(conn, inv.id)
    timeline = idb.get_timeline(conn, inv.id)
    out_dir = tmp_path / "export-out"

    path = iexport.write_investigation_export(
        inv, evidence=evidence, findings=findings, timeline=timeline,
        output_dir=out_dir, fmt="json",
    )

    assert path.exists()
    assert path.suffix == ".json"
    json.loads(path.read_text(encoding="utf-8"))


def test_write_investigation_export_dry_run_writes_nothing(conn, populated_investigation, tmp_path):
    inv = populated_investigation
    evidence = idb.list_evidence(conn, inv.id)
    findings = idb.list_findings(conn, inv.id)
    timeline = idb.get_timeline(conn, inv.id)
    out_dir = tmp_path / "export-out"

    path = iexport.write_investigation_export(
        inv, evidence=evidence, findings=findings, timeline=timeline,
        output_dir=out_dir, fmt="json", dry_run=True,
    )

    assert not path.exists()
    assert not out_dir.exists()
