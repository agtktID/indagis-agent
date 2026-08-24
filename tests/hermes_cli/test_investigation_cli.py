"""Tests for the `hermes investigation` CLI dispatch (hermes_cli/investigation_cmd)."""

from __future__ import annotations

import argparse
import json

from hermes_cli import investigation_cmd
from hermes_cli import investigation_db as idb


def _run(argv):
    """Build the investigation subparser, parse argv, and dispatch. Returns rc."""
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    p = investigation_cmd.build_parser(sub)
    p.set_defaults(func=investigation_cmd.investigation_command)
    args = parser.parse_args(["investigation", *argv])
    return investigation_cmd.investigation_command(args)


def test_create_list_show(capsys, tmp_path):
    assert _run(["create", "Assess acme-corp exposure", "--scope", "acme.example"]) == 0
    out = capsys.readouterr().out
    assert "Created investigation" in out

    with idb.connect_closing() as conn:
        invs = idb.list_investigations(conn)
        assert len(invs) == 1
        assert invs[0].objective == "Assess acme-corp exposure"

    assert _run(["list"]) == 0
    assert "assess-acme-corp-exposure" in capsys.readouterr().out

    assert _run(["show", "assess-acme-corp-exposure"]) == 0
    assert "Assess acme-corp exposure" in capsys.readouterr().out


def test_open_is_an_alias_for_show(capsys):
    _run(["create", "Investigate phishing campaign", "--scope", "evil.example"])
    capsys.readouterr()
    assert _run(["open", "investigate-phishing-campaign"]) == 0
    assert "Investigate phishing campaign" in capsys.readouterr().out


def test_list_json_output(capsys):
    _run(["create", "I1", "--scope", "acme.example"])
    capsys.readouterr()
    assert _run(["list", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert isinstance(payload, list)
    assert payload[0]["objective"] == "I1"


def test_add_evidence_and_finding_flow(capsys):
    _run(["create", "I1", "--scope", "acme.example"])
    capsys.readouterr()

    rc = _run([
        "add-evidence", "i1",
        "--description", "Open port 443",
        "--source", "nmap-scan", "--tool", "nmap",
        "--target", "acme.example", "--confidence", "high",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Evidence added" in out

    with idb.connect_closing() as conn:
        inv = idb.get_investigation(conn, "i1")
        evidence = idb.list_evidence(conn, inv.id)
        assert len(evidence) == 1
        ev_id = evidence[0].id

    rc = _run([
        "add-finding", "i1",
        "--summary", "TLS misconfiguration", "--severity", "high",
        "--evidence", ev_id,
        "--source", "analyst", "--tool", "manual",
        "--target", "acme.example", "--confidence", "high",
    ])
    assert rc == 0
    assert "Finding added" in capsys.readouterr().out

    rc = _run(["show", "i1", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert len(payload["evidence"]) == 1
    assert len(payload["findings"]) == 1
    assert len(payload["timeline"]) == 3  # created, evidence_added, finding_added


def test_add_evidence_out_of_scope_is_refused(capsys):
    _run(["create", "I1", "--scope", "acme.example"])
    capsys.readouterr()

    rc = _run([
        "add-evidence", "i1",
        "--description", "Unauthorized probe",
        "--source", "s", "--tool", "t",
        "--target", "unrelated.example", "--confidence", "low",
    ])
    assert rc == 2
    err = capsys.readouterr().err
    assert "outside the authorized scope" in err

    with idb.connect_closing() as conn:
        inv = idb.get_investigation(conn, "i1")
        assert idb.list_evidence(conn, inv.id) == []


def test_add_evidence_dry_run_writes_nothing(capsys):
    _run(["create", "I1", "--scope", "acme.example"])
    capsys.readouterr()

    rc = _run([
        "add-evidence", "i1",
        "--description", "Would-be evidence",
        "--source", "s", "--tool", "t",
        "--target", "acme.example", "--confidence", "low",
        "--dry-run",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Would add evidence" in out
    assert "authorized" in out

    with idb.connect_closing() as conn:
        inv = idb.get_investigation(conn, "i1")
        assert idb.list_evidence(conn, inv.id) == []


def test_add_evidence_dry_run_reports_scope_violation_without_writing(capsys):
    _run(["create", "I1", "--scope", "acme.example"])
    capsys.readouterr()

    rc = _run([
        "add-evidence", "i1",
        "--description", "Would-be evidence",
        "--source", "s", "--tool", "t",
        "--target", "unrelated.example", "--confidence", "low",
        "--dry-run",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Would add evidence" in out
    assert "outside" in out

    with idb.connect_closing() as conn:
        inv = idb.get_investigation(conn, "i1")
        assert idb.list_evidence(conn, inv.id) == []


def test_export_markdown_and_json(capsys, tmp_path):
    _run(["create", "I1", "--scope", "acme.example"])
    capsys.readouterr()
    out_dir = tmp_path / "export-out"

    rc = _run(["export", "i1", "--format", "md", "--output", str(out_dir)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Exported" in out
    md_files = list(out_dir.glob("*.md"))
    assert len(md_files) == 1

    rc = _run(["export", "i1", "--format", "json", "--output", str(out_dir)])
    assert rc == 0
    json_files = list(out_dir.glob("*.json"))
    assert len(json_files) == 1


def test_export_dry_run_writes_nothing(capsys, tmp_path):
    _run(["create", "I1", "--scope", "acme.example"])
    capsys.readouterr()
    out_dir = tmp_path / "export-out"

    rc = _run(["export", "i1", "--format", "md", "--output", str(out_dir), "--dry-run"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Would export" in out
    assert not out_dir.exists()


def test_close_and_reopen(capsys):
    _run(["create", "I1", "--scope", "acme.example"])
    capsys.readouterr()

    assert _run(["close", "i1"]) == 0
    with idb.connect_closing() as conn:
        assert idb.get_investigation(conn, "i1").status == "closed"

    assert _run(["reopen", "i1"]) == 0
    with idb.connect_closing() as conn:
        assert idb.get_investigation(conn, "i1").status == "open"
