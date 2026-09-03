"""Tests for hermes_cli/scope.py — Scope Sync CLI command handlers, including
the JSON and CSV scope-export importers."""

import json

from hermes_cli import scope
from hermes_cli.scope_state import get_program


class TestScopeImportJson:
    def test_string_entries_normalized(self, tmp_path):
        path = tmp_path / "scope.json"
        path.write_text(json.dumps({"in_scope": ["example.com"], "out_of_scope": []}), encoding="utf-8")
        scope.scope_import("acme", str(path))
        program = get_program("acme")
        assert program["in_scope"][0] == {"target": "example.com", "type": "other", "description": None}

    def test_dict_entries_preserved(self, tmp_path):
        path = tmp_path / "scope.json"
        path.write_text(json.dumps({
            "in_scope": [{"target": "*.example.com", "type": "domain", "description": "all subs"}],
            "out_of_scope": [],
        }), encoding="utf-8")
        scope.scope_import("acme", str(path))
        entry = get_program("acme")["in_scope"][0]
        assert entry["type"] == "domain"
        assert entry["description"] == "all subs"

    def test_items_without_target_skipped(self, tmp_path, capsys):
        path = tmp_path / "scope.json"
        path.write_text(json.dumps({"in_scope": [{"type": "domain"}], "out_of_scope": ["real.test"]}), encoding="utf-8")
        scope.scope_import("acme", str(path))
        program = get_program("acme")
        assert program["in_scope"] == []
        assert program["out_of_scope"] == [{"target": "real.test", "type": "other", "description": None}]

    def test_missing_file(self, tmp_path, capsys):
        scope.scope_import("acme", str(tmp_path / "nope.json"))
        assert "No such file" in capsys.readouterr().out

    def test_malformed_json(self, tmp_path, capsys):
        path = tmp_path / "bad.json"
        path.write_text("not json{{{", encoding="utf-8")
        scope.scope_import("acme", str(path))
        assert "Failed to parse" in capsys.readouterr().out

    def test_empty_scope_reports_nothing_imported(self, tmp_path, capsys):
        path = tmp_path / "empty.json"
        path.write_text(json.dumps({"in_scope": [], "out_of_scope": []}), encoding="utf-8")
        scope.scope_import("acme", str(path))
        assert "nothing imported" in capsys.readouterr().out


class TestScopeImportCsv:
    def test_eligible_for_bounty_column(self, tmp_path):
        path = tmp_path / "scope.csv"
        path.write_text("target,type,eligible_for_bounty\napi.acme.test,domain,true\nstaging.acme.test,domain,false\n", encoding="utf-8")
        scope.scope_import("acme", str(path))
        program = get_program("acme")
        in_targets = {e["target"] for e in program["in_scope"]}
        out_targets = {e["target"] for e in program["out_of_scope"]}
        assert in_targets == {"api.acme.test"}
        assert out_targets == {"staging.acme.test"}

    def test_scope_column_overrides(self, tmp_path):
        path = tmp_path / "scope.csv"
        path.write_text("target,scope\nin.test,in\nout.test,out\n", encoding="utf-8")
        scope.scope_import("acme", str(path))
        program = get_program("acme")
        assert program["in_scope"][0]["target"] == "in.test"
        assert program["out_of_scope"][0]["target"] == "out.test"

    def test_identifier_column_accepted(self, tmp_path):
        path = tmp_path / "scope.csv"
        path.write_text("identifier,type\nmobile-app-id,mobile\n", encoding="utf-8")
        scope.scope_import("acme", str(path))
        assert get_program("acme")["in_scope"][0]["target"] == "mobile-app-id"

    def test_no_target_column_errors(self, tmp_path, capsys):
        path = tmp_path / "scope.csv"
        path.write_text("foo,bar\n1,2\n", encoding="utf-8")
        scope.scope_import("acme", str(path))
        assert "No target column found" in capsys.readouterr().out

    def test_rows_without_target_value_skipped(self, tmp_path):
        path = tmp_path / "scope.csv"
        path.write_text("target,type\n,domain\nreal.test,domain\n", encoding="utf-8")
        scope.scope_import("acme", str(path))
        assert len(get_program("acme")["in_scope"]) == 1


class TestScopeCheckCli:
    def test_prints_in_scope(self, tmp_path, capsys):
        path = tmp_path / "s.json"
        path.write_text(json.dumps({"in_scope": ["example.com"], "out_of_scope": []}), encoding="utf-8")
        scope.scope_import("acme", str(path))
        capsys.readouterr()

        scope.scope_check("example.com")
        out = capsys.readouterr().out
        assert "IN SCOPE" in out

    def test_prints_out_of_scope(self, tmp_path, capsys):
        path = tmp_path / "s.json"
        path.write_text(json.dumps({"in_scope": [], "out_of_scope": ["blocked.test"]}), encoding="utf-8")
        scope.scope_import("acme", str(path))
        capsys.readouterr()

        scope.scope_check("blocked.test")
        out = capsys.readouterr().out
        assert "OUT OF SCOPE" in out

    def test_prints_unknown_for_unmatched(self, capsys):
        scope.scope_check("never-imported.test")
        out = capsys.readouterr().out
        assert "unknown" in out.lower()


class TestScopeRemoveCli:
    def test_remove_missing(self, capsys):
        scope.scope_remove("nope")
        assert "No such program" in capsys.readouterr().out


class TestDeriveHost:
    def test_plain_domain(self):
        assert scope._derive_host({"target": "example.com"}) == "example.com"

    def test_wildcard_strips_prefix(self):
        assert scope._derive_host({"target": "*.example.com"}) == "example.com"

    def test_url_extracts_netloc(self):
        assert scope._derive_host({"target": "https://sub.example.com:8443/path"}) == "sub.example.com"

    def test_cidr_returns_none(self):
        assert scope._derive_host({"target": "203.0.113.0/24"}) is None

    def test_email_returns_none(self):
        assert scope._derive_host({"target": "security@example.com"}) is None

    def test_empty_returns_none(self):
        assert scope._derive_host({"target": ""}) is None

    def test_ip_passes_through(self):
        assert scope._derive_host({"target": "198.51.100.1"}) == "198.51.100.1"

    def test_mobile_type_excluded_even_if_dotted(self):
        assert scope._derive_host({"target": "com.acme.mobileapp", "type": "mobile"}) is None

    def test_unset_type_falls_through_to_shape_check(self):
        assert scope._derive_host({"target": "example.com"}) == "example.com"


class TestScopeAutopilot:
    def test_unknown_program(self, capsys):
        scope.scope_autopilot("nope", "every 6h", "local")
        assert "No such program" in capsys.readouterr().out

    def test_dry_run_lists_without_scheduling(self, monkeypatch, capsys):
        from hermes_cli.scope_state import import_scope

        import_scope(
            "acme",
            in_scope=[{"target": "example.com", "type": "domain", "description": None}],
            out_of_scope=[],
            source="test",
        )
        called = []
        monkeypatch.setattr("hermes_cli.surface.surface_schedule", lambda *a, **k: called.append(a))
        scope.scope_autopilot("acme", "every 6h", "local", dry_run=True)
        out = capsys.readouterr().out
        assert "Dry run" in out
        assert "example.com" in out
        assert called == []

    def test_schedules_new_host_shaped_in_scope_targets(self, monkeypatch, capsys):
        from hermes_cli.scope_state import import_scope

        import_scope(
            "acme",
            in_scope=[
                {"target": "*.example.com", "type": "wildcard", "description": None},
                {"target": "203.0.113.0/24", "type": "cidr", "description": None},
                {"target": "com.acme.mobileapp", "type": "mobile", "description": None},
            ],
            out_of_scope=[{"target": "internal.example.com", "type": "domain", "description": None}],
            source="test",
        )
        called = []
        monkeypatch.setattr("hermes_cli.surface.surface_schedule", lambda *a, **k: called.append(a))
        scope.scope_autopilot("acme", "every 6h", "local")
        out = capsys.readouterr().out
        assert "New targets to onboard:  1" in out
        assert called == [("example.com", "example.com", "every 6h", "local")]
        # out-of-scope target must never be touched
        assert not any("internal.example.com" in str(c) for c in called)

    def test_skips_already_monitored_targets(self, monkeypatch, capsys):
        from hermes_cli.scope_state import import_scope
        from hermes_cli.surface_state import save_snapshot

        import_scope(
            "acme",
            in_scope=[{"target": "example.com", "type": "domain", "description": None}],
            out_of_scope=[],
            source="test",
        )
        save_snapshot("example.com", {"ips": ["198.51.100.1"]})
        called = []
        monkeypatch.setattr("hermes_cli.surface.surface_schedule", lambda *a, **k: called.append(a))
        scope.scope_autopilot("acme", "every 6h", "local")
        out = capsys.readouterr().out
        assert "Already monitored:       1" in out
        assert "Nothing new to onboard" in out
        assert called == []
