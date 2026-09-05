"""Tests for hermes_cli/case_memory.py — Case Memory CLI command handlers."""

import json

from hermes_cli import case_memory


def _write_store(path, investigation, evidence):
    path.write_text(json.dumps({"metadata": {"investigation": investigation}, "evidence": evidence}), encoding="utf-8")


def _ioc_entry(eid, ioc_type, content, actor=None, source="dns lookup"):
    return {"id": eid, "type": "ioc", "ioc_type": ioc_type, "content": content, "actor": actor, "source": source}


class TestCaseIngest:
    def test_ingests_iocs(self, tmp_path, capsys):
        store = tmp_path / "case1.json"
        _write_store(store, "campaign-alpha", [_ioc_entry("EV-0001", "IP_ADDRESS", "198.51.100.1")])

        case_memory.case_ingest(str(store))
        out = capsys.readouterr().out
        assert "Ingested 1 IOC" in out
        assert "campaign-alpha" in out

    def test_non_ioc_entries_are_skipped(self, tmp_path, capsys):
        store = tmp_path / "case1.json"
        _write_store(store, "case-a", [{"id": "EV-0001", "type": "git", "content": "irrelevant"}])
        case_memory.case_ingest(str(store))
        assert "Ingested 0 IOC" in capsys.readouterr().out

    def test_missing_file(self, tmp_path, capsys):
        case_memory.case_ingest(str(tmp_path / "nope.json"))
        assert "Failed to read" in capsys.readouterr().out

    def test_not_an_evidence_store(self, tmp_path, capsys):
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps({"not": "evidence"}), encoding="utf-8")
        case_memory.case_ingest(str(bad))
        assert "Failed to read" in capsys.readouterr().out

    def test_malformed_json(self, tmp_path, capsys):
        bad = tmp_path / "bad.json"
        bad.write_text("not json{{{", encoding="utf-8")
        case_memory.case_ingest(str(bad))
        assert "Failed to read" in capsys.readouterr().out

    def test_warns_on_cross_investigation_correlation(self, tmp_path, capsys):
        store1 = tmp_path / "case1.json"
        _write_store(store1, "campaign-alpha", [_ioc_entry("EV-0001", "IP_ADDRESS", "198.51.100.1")])
        case_memory.case_ingest(str(store1))
        capsys.readouterr()

        store2 = tmp_path / "case2.json"
        _write_store(store2, "campaign-beta", [_ioc_entry("EV-0001", "IP_ADDRESS", "198.51.100.1")])
        case_memory.case_ingest(str(store2))
        out = capsys.readouterr().out
        assert "already seen in a different investigation" in out


class TestCaseCorrelate:
    def test_no_matches_when_nothing_shared(self, tmp_path, capsys):
        store = tmp_path / "case1.json"
        _write_store(store, "case-a", [_ioc_entry("EV-0001", "DOMAIN", "unique.test")])
        case_memory.case_ingest(str(store))
        capsys.readouterr()

        case_memory.case_correlate(str(store))
        assert "No cross-investigation matches" in capsys.readouterr().out

    def test_reports_shared_ioc(self, tmp_path, capsys):
        store1 = tmp_path / "case1.json"
        _write_store(store1, "campaign-alpha", [_ioc_entry("EV-0001", "IP_ADDRESS", "198.51.100.1")])
        case_memory.case_ingest(str(store1))
        capsys.readouterr()

        store2 = tmp_path / "case2.json"
        _write_store(store2, "campaign-beta", [_ioc_entry("EV-0001", "IP_ADDRESS", "198.51.100.1")])
        case_memory.case_ingest(str(store2))
        capsys.readouterr()

        case_memory.case_correlate(str(store2))
        out = capsys.readouterr().out
        assert "198.51.100.1" in out
        assert "campaign-alpha" in out

    def test_no_ioc_entries(self, tmp_path, capsys):
        store = tmp_path / "empty.json"
        _write_store(store, "case-a", [])
        case_memory.case_correlate(str(store))
        assert "No IOC-type evidence" in capsys.readouterr().out


class TestCaseLookup:
    def test_lookup_missing(self, capsys):
        case_memory.case_lookup("nothing.test")
        assert "No prior sighting" in capsys.readouterr().out

    def test_lookup_existing(self, tmp_path, capsys):
        store = tmp_path / "case1.json"
        _write_store(store, "campaign-alpha", [_ioc_entry("EV-0001", "DOMAIN", "evil.test", actor="mallory")])
        case_memory.case_ingest(str(store))
        capsys.readouterr()

        case_memory.case_lookup("evil.test")
        out = capsys.readouterr().out
        assert "campaign-alpha" in out
        assert "mallory" in out


class TestCaseCommandDispatch:
    def test_default_action_is_list(self, monkeypatch):
        called = []
        monkeypatch.setattr(case_memory, "case_list", lambda **kw: called.append(kw))
        case_memory.case_command(type("Args", (), {"case_command": None})())
        assert called

    def test_unknown_action(self, capsys):
        case_memory.case_command(type("Args", (), {"case_command": "bogus"})())
        assert "Unknown case subcommand" in capsys.readouterr().err
