"""Tests for hermes_cli/scope_state.py — Scope Sync storage and matching."""

from hermes_cli.scope_state import (
    add_entry,
    check_target,
    get_program,
    import_scope,
    list_programs,
    remove_program,
)


class TestImportScope:
    def test_stores_program(self):
        import_scope("acme", [{"target": "example.com", "type": "domain", "description": None}], [], source="/tmp/x.json")
        program = get_program("acme")
        assert program["program"] == "acme"
        assert len(program["in_scope"]) == 1

    def test_reimport_replaces_wholesale(self):
        import_scope("acme", [{"target": "old.test", "type": "domain", "description": None}], [], source="a")
        import_scope("acme", [{"target": "new.test", "type": "domain", "description": None}], [], source="b")
        program = get_program("acme")
        assert len(program["in_scope"]) == 1
        assert program["in_scope"][0]["target"] == "new.test"


class TestAddEntry:
    def test_adds_to_in_scope_by_default(self):
        add_entry("acme", "example.com", "domain", None, out_of_scope=False)
        program = get_program("acme")
        assert program["in_scope"][0]["target"] == "example.com"
        assert program["out_of_scope"] == []

    def test_adds_to_out_of_scope(self):
        add_entry("acme", "blog.example.com", "domain", "excluded", out_of_scope=True)
        program = get_program("acme")
        assert program["out_of_scope"][0]["target"] == "blog.example.com"

    def test_appends_to_existing_program(self):
        add_entry("acme", "a.test", "domain", None, out_of_scope=False)
        add_entry("acme", "b.test", "domain", None, out_of_scope=False)
        assert len(get_program("acme")["in_scope"]) == 2


class TestListAndRemovePrograms:
    def test_list_sorted_by_name(self):
        import_scope("zeta", [], [], source="a")
        import_scope("alpha", [], [], source="b")
        names = [p["program"] for p in list_programs()]
        assert names == ["alpha", "zeta"]

    def test_remove_existing(self):
        import_scope("acme", [], [], source="a")
        assert remove_program("acme") is True
        assert get_program("acme") is None

    def test_remove_missing(self):
        assert remove_program("nope") is False


class TestCheckTarget:
    def _setup_program(self):
        import_scope(
            "acme",
            in_scope=[
                {"target": "*.example.com", "type": "domain", "description": None},
                {"target": "192.0.2.0/24", "type": "cidr", "description": None},
                {"target": "exact.test", "type": "domain", "description": None},
            ],
            out_of_scope=[{"target": "blog.example.com", "type": "domain", "description": None}],
            source="a",
        )

    def test_wildcard_matches_subdomain(self):
        self._setup_program()
        results = check_target("sub.example.com")
        assert any(r["verdict"] == "in-scope" for r in results)

    def test_wildcard_matches_bare_domain(self):
        self._setup_program()
        results = check_target("example.com")
        assert any(r["verdict"] == "in-scope" for r in results)

    def test_wildcard_does_not_match_unrelated_domain(self):
        self._setup_program()
        results = check_target("notexample.com")
        assert results == []

    def test_cidr_match(self):
        self._setup_program()
        results = check_target("192.0.2.42")
        assert any(r["verdict"] == "in-scope" and "192.0.2.0/24" in r["entry"]["target"] for r in results)

    def test_ip_outside_cidr_no_match(self):
        self._setup_program()
        results = check_target("203.0.113.1")
        assert results == []

    def test_exact_match(self):
        self._setup_program()
        results = check_target("exact.test")
        assert any(r["verdict"] == "in-scope" for r in results)

    def test_case_insensitive_match(self):
        self._setup_program()
        results = check_target("SUB.EXAMPLE.COM")
        assert any(r["verdict"] == "in-scope" for r in results)

    def test_out_of_scope_entry_reported(self):
        self._setup_program()
        results = check_target("blog.example.com")
        verdicts = {r["verdict"] for r in results}
        assert "out-of-scope" in verdicts

    def test_scoped_to_one_program(self):
        self._setup_program()
        import_scope("other", in_scope=[{"target": "exact.test", "type": "domain", "description": None}], out_of_scope=[], source="b")
        results = check_target("exact.test", program="acme")
        assert all(r["program"] == "acme" for r in results)
        assert len(results) == 1

    def test_unmatched_target_returns_empty(self):
        self._setup_program()
        assert check_target("totally-unrelated.net") == []
