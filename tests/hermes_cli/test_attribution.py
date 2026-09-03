"""Tests for hermes_cli/attribution.py — Attribution Confidence Scorer."""

import json

import pytest

from hermes_cli import attribution, case_memory_state


def _ioc_entry(eid, ioc_type, content, verification="unverified"):
    return {
        "id": eid,
        "type": "ioc",
        "ioc_type": ioc_type,
        "content": content,
        "source": "dns lookup",
        "verification": verification,
    }


def _write_store(path, investigation, evidence):
    path.write_text(
        json.dumps({"metadata": {"investigation": investigation}, "evidence": evidence}),
        encoding="utf-8",
    )
    return str(path)


class TestConfidenceScore:
    def test_a1_is_maximum(self):
        assert attribution.confidence_score("A", "1") == 100

    def test_f6_is_minimum(self):
        assert attribution.confidence_score("F", "6") == 17

    def test_case_insensitive_reliability(self):
        assert attribution.confidence_score("a", "1") == attribution.confidence_score("A", "1")

    def test_unknown_codes_fall_back_to_worst(self):
        assert attribution.confidence_score("Z", "9") == 17


class TestScoreEntry:
    def test_uses_explicit_admiralty_fields_when_present(self):
        entry = {"id": "EV-1", "type": "ioc", "content": "x", "admiralty_reliability": "A", "admiralty_credibility": "1"}
        result = attribution.score_entry(entry)
        assert result["reliability"] == "A"
        assert result["credibility"] == "1"
        assert result["confidence"] == 100
        assert result["label"] == "high"

    def test_derives_from_verification_when_admiralty_fields_absent(self):
        entry = _ioc_entry("EV-1", "DOMAIN", "evil.example.com", verification="multi_source_verified")
        result = attribution.score_entry(entry)
        assert result["reliability"] == "B"
        assert result["credibility"] == "2"

    def test_unverified_defaults_to_cannot_be_judged(self):
        entry = _ioc_entry("EV-1", "DOMAIN", "evil.example.com", verification="unverified")
        result = attribution.score_entry(entry)
        assert result["reliability"] == "F"
        assert result["credibility"] == "6"
        assert result["label"] == "unassessed"

    def test_cross_case_correlation_upgrades_credibility(self):
        case_memory_state.record_sighting(
            ioc_type="IP_ADDRESS", value="198.51.100.1", investigation="prior-case",
            store_path="/tmp/prior.json", evidence_id="EV-1", actor=None, source="dns",
        )
        entry = _ioc_entry("EV-1", "IP_ADDRESS", "198.51.100.1", verification="unverified")
        result = attribution.score_entry(entry, investigation="new-case")
        assert result["corroborated_cross_case"] is True
        assert result["credibility"] == "1"
        assert result["confidence"] > 0

    def test_same_investigation_sighting_not_treated_as_corroboration(self):
        case_memory_state.record_sighting(
            ioc_type="IP_ADDRESS", value="198.51.100.1", investigation="case-a",
            store_path="/tmp/a.json", evidence_id="EV-1", actor=None, source="dns",
        )
        entry = _ioc_entry("EV-1", "IP_ADDRESS", "198.51.100.1", verification="unverified")
        result = attribution.score_entry(entry, investigation="case-a")
        assert result["corroborated_cross_case"] is False

    def test_non_ioc_entry_not_corroboration_checked(self):
        entry = {"id": "EV-1", "type": "git", "content": "irrelevant", "verification": "unverified"}
        result = attribution.score_entry(entry)
        assert result["corroborated_cross_case"] is False


class TestScoreEvidenceStore:
    def test_aggregate_report_structure(self, tmp_path):
        store = _write_store(
            tmp_path / "case.json",
            "campaign-alpha",
            [
                _ioc_entry("EV-1", "IP_ADDRESS", "198.51.100.1", verification="multi_source_verified"),
                _ioc_entry("EV-2", "DOMAIN", "evil.example.com", verification="unverified"),
            ],
        )
        report = attribution.score_evidence_store(store)
        assert report["investigation"] == "campaign-alpha"
        assert report["total_count"] == 2
        assert report["unassessed_count"] == 1
        assert 0 <= report["overall_confidence"] <= 100

    def test_empty_evidence_gives_zero_overall(self, tmp_path):
        store = _write_store(tmp_path / "case.json", "case-a", [])
        report = attribution.score_evidence_store(store)
        assert report["overall_confidence"] == 0
        assert report["entries"] == []

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(OSError):
            attribution.score_evidence_store(str(tmp_path / "nope.json"))

    def test_not_an_evidence_store_raises(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps({"not": "evidence"}), encoding="utf-8")
        with pytest.raises(ValueError):
            attribution.score_evidence_store(str(bad))


class TestAttributionScoreCli:
    def test_prints_report(self, tmp_path, capsys):
        store = _write_store(
            tmp_path / "case.json", "campaign-alpha",
            [_ioc_entry("EV-1", "IP_ADDRESS", "198.51.100.1", verification="multi_source_verified")],
        )
        attribution.attribution_score(store)
        out = capsys.readouterr().out
        assert "Attribution Confidence — campaign-alpha" in out
        assert "EV-1" in out
        assert "B2" in out

    def test_failure_prints_error(self, tmp_path, capsys):
        attribution.attribution_score(str(tmp_path / "nope.json"))
        assert "Failed to score" in capsys.readouterr().out


class TestAttributionMatrixCli:
    def test_prints_reference_table(self, capsys):
        attribution.attribution_matrix()
        out = capsys.readouterr().out
        assert "Completely reliable" in out
        assert "Confirmed by other sources" in out


class TestAttributionCommandDispatch:
    def test_score_action_routes(self, monkeypatch):
        called = []
        monkeypatch.setattr(attribution, "attribution_score", lambda store_path: called.append(store_path))
        args = type("Args", (), {"attribution_command": "score", "store_path": "x.json"})()
        attribution.attribution_command(args)
        assert called == ["x.json"]

    def test_matrix_action_routes(self, monkeypatch):
        called = []
        monkeypatch.setattr(attribution, "attribution_matrix", lambda: called.append(True))
        args = type("Args", (), {"attribution_command": "matrix"})()
        attribution.attribution_command(args)
        assert called

    def test_unknown_action(self, capsys):
        args = type("Args", (), {"attribution_command": "bogus"})()
        attribution.attribution_command(args)
        assert "Unknown attribution subcommand" in capsys.readouterr().err
