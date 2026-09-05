"""Tests for hermes_cli/rules.py — Rule Forge CLI command handler."""

import yaml

from hermes_cli import rules
from hermes_cli.case_memory_state import record_sighting


def _seed_iocs():
    record_sighting(ioc_type="IP_ADDRESS", value="198.51.100.1", investigation="campaign-alpha", store_path="/a.json", evidence_id="e1", actor=None, source="s")
    record_sighting(ioc_type="IP_ADDRESS", value="198.51.100.1", investigation="campaign-beta", store_path="/b.json", evidence_id="e1", actor=None, source="s")
    record_sighting(ioc_type="DOMAIN", value="only-in-beta.test", investigation="campaign-beta", store_path="/b.json", evidence_id="e2", actor=None, source="s")


class TestRulesForge:
    def test_no_iocs_indexed(self, tmp_path, capsys):
        rules.rules_forge(investigation="all", out_dir=str(tmp_path / "out"), fmt="both")
        assert "No indexed IOCs" in capsys.readouterr().out

    def test_generates_both_formats_for_all(self, tmp_path, capsys):
        _seed_iocs()
        out_dir = tmp_path / "out"
        rules.rules_forge(investigation="all", out_dir=str(out_dir), fmt="both")
        out = capsys.readouterr().out
        assert "Generated rules for 2 indicator(s)" in out

        sigma_files = list((out_dir / "sigma").glob("*.yml"))
        yara_files = list((out_dir / "yara").glob("*.yar"))
        assert len(sigma_files) == 2
        assert len(yara_files) == 2

    def test_sigma_files_are_valid_yaml(self, tmp_path):
        _seed_iocs()
        out_dir = tmp_path / "out"
        rules.rules_forge(investigation="all", out_dir=str(out_dir), fmt="sigma")
        for path in (out_dir / "sigma").glob("*.yml"):
            rule = yaml.safe_load(path.read_text())
            assert "detection" in rule

    def test_yara_only_format_skips_sigma_dir(self, tmp_path, capsys):
        _seed_iocs()
        out_dir = tmp_path / "out"
        rules.rules_forge(investigation="all", out_dir=str(out_dir), fmt="yara")
        capsys.readouterr()
        assert not (out_dir / "sigma").exists()
        assert (out_dir / "yara").exists()

    def test_scoped_to_one_investigation(self, tmp_path, capsys):
        _seed_iocs()
        out_dir = tmp_path / "out"
        rules.rules_forge(investigation="campaign-alpha", out_dir=str(out_dir), fmt="both")
        assert "Generated rules for 1 indicator(s)" in capsys.readouterr().out

    def test_unknown_investigation_reports_nothing_found(self, tmp_path, capsys):
        _seed_iocs()
        rules.rules_forge(investigation="no-such-case", out_dir=str(tmp_path / "out"), fmt="both")
        assert "No indexed IOCs found for investigation 'no-such-case'" in capsys.readouterr().out

    def test_filenames_sanitized(self, tmp_path):
        record_sighting(ioc_type="MALICIOUS_URL", value="http://evil.test/a/b?x=1", investigation="c", store_path="p", evidence_id="e", actor=None, source="s")
        out_dir = tmp_path / "out"
        rules.rules_forge(investigation="all", out_dir=str(out_dir), fmt="yara")
        files = list((out_dir / "yara").glob("*.yar"))
        assert len(files) == 1
        assert "/" not in files[0].name


class TestRulesCommandDispatch:
    def test_unknown_action(self, capsys):
        rules.rules_command(type("Args", (), {"rules_command": "bogus"})())
        assert "Unknown rules subcommand" in capsys.readouterr().err

    def test_forge_dispatch_defaults_format_to_both(self, tmp_path, monkeypatch):
        called = {}
        monkeypatch.setattr(rules, "rules_forge", lambda **kw: called.update(kw))
        args = type("Args", (), {"rules_command": "forge", "investigation": "all", "out": str(tmp_path), "format": None})()
        rules.rules_command(args)
        assert called["fmt"] == "both"
