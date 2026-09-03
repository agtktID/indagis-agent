"""Tests for hermes_cli/dossier.py — Dossier Builder."""

import hashlib
import json

from hermes_cli import case_memory_state, dossier, scope_state


def _sha256(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _ioc_entry(eid, ioc_type, content, actor=None, source="dns lookup"):
    return {
        "id": eid,
        "type": "ioc",
        "ioc_type": ioc_type,
        "content": content,
        "content_sha256": _sha256(content),
        "actor": actor,
        "source": source,
        "verification": "unverified",
        "event_timestamp": "2026-01-01T00:00:00Z",
    }


def _write_store(path, investigation, evidence, custody=None, target_repo=None):
    path.write_text(
        json.dumps(
            {
                "metadata": {"investigation": investigation, "target_repo": target_repo},
                "evidence": evidence,
                "chain_of_custody": custody or [],
            }
        ),
        encoding="utf-8",
    )
    return str(path)


class TestBuildDossier:
    def test_basic_report_structure(self, tmp_path):
        store = tmp_path / "case.json"
        _write_store(
            store,
            "campaign-alpha",
            [_ioc_entry("EV-0001", "IP_ADDRESS", "198.51.100.1")],
            custody=[{"evidence_id": "EV-0001", "action": "add", "timestamp": "2026-01-01T00:00:00Z", "source": "manual"}],
        )
        report = dossier.build_dossier(str(store))
        assert "# Investigation Dossier — campaign-alpha" in report
        assert "## Findings summary" in report
        assert "## Indicators of Compromise" in report
        assert "198.51.100.1" in report
        assert "## Evidence timeline" in report
        assert "## Chain of custody" in report
        assert "EV-0001" in report

    def test_missing_file_raises(self, tmp_path):
        import pytest

        with pytest.raises(OSError):
            dossier.build_dossier(str(tmp_path / "nope.json"))

    def test_not_an_evidence_store_raises(self, tmp_path):
        import pytest

        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps({"not": "evidence"}), encoding="utf-8")
        with pytest.raises(ValueError):
            dossier.build_dossier(str(bad))

    def test_integrity_check_passes_when_untampered(self, tmp_path):
        store = tmp_path / "case.json"
        _write_store(store, "case-a", [_ioc_entry("EV-0001", "DOMAIN", "evil.example.com")])
        report = dossier.build_dossier(str(store))
        assert "passed SHA-256 integrity re-check" in report

    def test_integrity_check_flags_tampering(self, tmp_path):
        store = tmp_path / "case.json"
        entry = _ioc_entry("EV-0001", "DOMAIN", "evil.example.com")
        entry["content"] = "tampered.example.com"  # content changed after hash was computed
        _write_store(store, "case-a", [entry])
        report = dossier.build_dossier(str(store))
        assert "failed integrity re-check" in report

    def test_cross_case_correlation_flagged(self, tmp_path):
        # First, another investigation sees this IOC.
        case_memory_state.record_sighting(
            ioc_type="IP_ADDRESS", value="198.51.100.1", investigation="prior-case",
            store_path="/tmp/prior.json", evidence_id="EV-1", actor=None, source="dns",
        )
        store = tmp_path / "case.json"
        _write_store(store, "campaign-alpha", [_ioc_entry("EV-0001", "IP_ADDRESS", "198.51.100.1")])
        report = dossier.build_dossier(str(store))
        assert "also seen in: prior-case" in report

    def test_no_correlation_shows_dash(self, tmp_path):
        store = tmp_path / "case.json"
        _write_store(store, "campaign-alpha", [_ioc_entry("EV-0001", "IP_ADDRESS", "203.0.113.9")])
        report = dossier.build_dossier(str(store))
        assert "| `203.0.113.9` | IP_ADDRESS | — |" in report

    def test_no_iocs_skips_ioc_section(self, tmp_path):
        store = tmp_path / "case.json"
        _write_store(store, "case-a", [{"id": "EV-0001", "type": "git", "content": "irrelevant", "source": "git fsck"}])
        report = dossier.build_dossier(str(store))
        assert "## Indicators of Compromise" not in report


class TestScopeSection:
    def test_program_not_imported(self, tmp_path):
        store = tmp_path / "case.json"
        _write_store(store, "case-a", [_ioc_entry("EV-0001", "DOMAIN", "evil.example.com")])
        report = dossier.build_dossier(str(store), program="acme-bounty")
        assert "not imported into Scope Sync" in report

    def test_in_scope_confirmed(self, tmp_path):
        scope_state.import_scope(
            "acme-bounty",
            in_scope=[{"target": "*.example.com", "type": "wildcard", "description": None}],
            out_of_scope=[],
            source="test",
        )
        store = tmp_path / "case.json"
        _write_store(store, "case-a", [_ioc_entry("EV-0001", "DOMAIN", "evil.example.com")])
        report = dossier.build_dossier(str(store), program="acme-bounty")
        assert "Every checked indicator matched an in-scope rule" in report

    def test_out_of_scope_flagged(self, tmp_path):
        scope_state.import_scope(
            "acme-bounty",
            in_scope=[],
            out_of_scope=[{"target": "internal.example.com", "type": "domain", "description": None}],
            source="test",
        )
        store = tmp_path / "case.json"
        _write_store(store, "case-a", [_ioc_entry("EV-0001", "DOMAIN", "internal.example.com")])
        report = dossier.build_dossier(str(store), program="acme-bounty")
        assert "matched an out-of-scope rule" in report
        assert "internal.example.com" in report

    def test_unmatched_target_reported(self, tmp_path):
        scope_state.import_scope(
            "acme-bounty",
            in_scope=[{"target": "*.example.com", "type": "wildcard", "description": None}],
            out_of_scope=[],
            source="test",
        )
        store = tmp_path / "case.json"
        _write_store(store, "case-a", [_ioc_entry("EV-0001", "DOMAIN", "unrelated.example.org")])
        report = dossier.build_dossier(str(store), program="acme-bounty")
        assert "matched no scope rule" in report


class TestDossierBuildHandler:
    def test_writes_to_out_path(self, tmp_path, capsys):
        store = tmp_path / "case.json"
        _write_store(store, "case-a", [_ioc_entry("EV-0001", "DOMAIN", "evil.example.com")])
        out = tmp_path / "report.md"
        dossier.dossier_build(str(store), out_path=str(out))
        assert "Dossier written to" in capsys.readouterr().out
        assert out.exists()
        assert "Investigation Dossier" in out.read_text(encoding="utf-8")

    def test_prints_to_stdout_without_out_path(self, tmp_path, capsys):
        store = tmp_path / "case.json"
        _write_store(store, "case-a", [_ioc_entry("EV-0001", "DOMAIN", "evil.example.com")])
        dossier.dossier_build(str(store))
        assert "Investigation Dossier" in capsys.readouterr().out

    def test_failure_prints_error(self, tmp_path, capsys):
        dossier.dossier_build(str(tmp_path / "nope.json"))
        assert "Failed to build dossier" in capsys.readouterr().out


class TestDossierCommandDispatch:
    def test_build_action_routes(self, monkeypatch):
        called = {}

        def fake(store_path, **kw):
            called["store_path"] = store_path
            called.update(kw)

        monkeypatch.setattr(dossier, "dossier_build", fake)
        args = type("Args", (), {"dossier_command": "build", "store_path": "x.json", "program": "p", "out": "o.md"})()
        dossier.dossier_command(args)
        assert called == {"store_path": "x.json", "program": "p", "out_path": "o.md"}

    def test_unknown_action(self, capsys):
        args = type("Args", (), {"dossier_command": "bogus"})()
        dossier.dossier_command(args)
        assert "Unknown dossier subcommand" in capsys.readouterr().err
