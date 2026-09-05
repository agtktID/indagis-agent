"""Tests for hermes_cli/graph.py and hermes_cli/graph_cmd.py — the relationship graph.

The property that carries the module is hub exclusion. A graph whose edges
are dominated by one banal indicator is worse than no graph: it asserts a
relationship between every pair of cases an analyst has ever opened. Most of
what follows exists to pin that behaviour down from both sides — the hub must
not link, and `--include-hubs` must put the links back.
"""

import json

import pytest

from hermes_cli import graph, graph_cmd


def _ioc(value, kind, cases, *, actor=None):
    return {
        "type": kind,
        "value": value,
        "first_seen": "2026-01-01T00:00:00+00:00",
        "last_seen": "2026-01-02T00:00:00+00:00",
        "sightings": [
            {"investigation": case, "store_path": f"/s/{case}.json", "evidence_id": "ev-001", "actor": actor, "source": "recon"}
            for case in cases
        ],
    }


@pytest.fixture
def index(monkeypatch):
    """Install a fake Case Memory index.

    nightfall and harbour genuinely overlap on two indicators. 8.8.8.8 sits
    in all three cases — the hub. driftwood is held to the others by that
    hub alone, which is what makes it the control: if it ever shows up as
    linked at the default settings, hub exclusion is broken.
    """
    state = {
        "investigations": [
            {"name": "nightfall", "store_path": "/s/nightfall.json", "last_ingested_at": "2026-01-03T00:00:00+00:00"},
            {"name": "harbour", "store_path": "/s/harbour.json", "last_ingested_at": "2026-01-02T00:00:00+00:00"},
            {"name": "driftwood", "store_path": "/s/driftwood.json", "last_ingested_at": "2026-01-01T00:00:00+00:00"},
        ],
        "iocs": [
            _ioc("evil.example", "DOMAIN", ["nightfall", "harbour"], actor="analyst-a"),
            _ioc("9.9.9.1", "IPV4", ["nightfall", "harbour"]),
            _ioc("8.8.8.8", "IPV4", ["nightfall", "harbour", "driftwood"]),
            _ioc("only-nightfall.example", "DOMAIN", ["nightfall"]),
            _ioc("only-driftwood.example", "DOMAIN", ["driftwood"]),
        ],
    }

    def fake_iocs(ioc_type=None):
        return [e for e in state["iocs"] if ioc_type is None or e["type"] == ioc_type]

    monkeypatch.setattr("hermes_cli.case_memory_state.list_investigations", lambda: state["investigations"])
    monkeypatch.setattr("hermes_cli.case_memory_state.list_iocs", fake_iocs)
    return state


def _links(g):
    return {
        (e["source"].removeprefix("case:"), e["target"].removeprefix("case:")): e
        for e in g["edges"]
        if e["kind"] == "shared_ioc"
    }


class TestHubExclusion:
    def test_hub_links_nothing_by_default(self, index):
        g = graph.build_graph(hub_threshold=2)
        links = _links(g)

        assert ("harbour", "nightfall") in links
        # driftwood shares only the hub, so it must stand alone.
        assert not any("driftwood" in pair for pair in links)

    def test_hub_is_reported_rather_than_hidden(self, index):
        # "This indicator is in everything" is a finding; silently dropping
        # it would lose that.
        g = graph.build_graph(hub_threshold=2)
        assert [h["value"] for h in g["hubs"]] == ["8.8.8.8"]
        assert g["stats"]["hubs"] == 1

    def test_hub_is_still_a_node(self, index):
        g = graph.build_graph(hub_threshold=2)
        hub = next(n for n in g["nodes"] if n["label"] == "8.8.8.8")
        assert hub["hub"] is True
        assert hub["degree"] == 3

    def test_include_hubs_puts_the_links_back(self, index):
        # The mirror test: without it, "driftwood is unlinked" could pass
        # for a reason other than hub exclusion.
        g = graph.build_graph(hub_threshold=2, include_hubs=True)
        links = _links(g)

        assert ("driftwood", "harbour") in links
        assert ("driftwood", "nightfall") in links
        assert links[("harbour", "nightfall")]["weight"] == 3

    def test_hub_produces_no_sighting_edges_either(self, index):
        g = graph.build_graph(hub_threshold=2)
        hub_id = "ioc:IPV4:8.8.8.8"
        assert not [e for e in g["edges"] if hub_id in (e["source"], e["target"])]

    def test_default_threshold_leaves_a_small_graph_alone(self, index):
        # At the shipped default nothing here is a hub — the fixture's
        # 3-case indicator is a genuine pivot at that scale.
        g = graph.build_graph()
        assert g["hubs"] == []
        assert ("driftwood", "harbour") in _links(g)


class TestWeighting:
    def test_weight_is_the_count_of_shared_indicators(self, index):
        edge = _links(graph.build_graph(hub_threshold=2))[("harbour", "nightfall")]
        assert edge["weight"] == 2
        assert sorted(edge["shared"]) == ["9.9.9.1", "evil.example"]

    def test_min_shared_hides_weak_pairs(self, index):
        assert _links(graph.build_graph(hub_threshold=2, min_shared=3)) == {}
        assert _links(graph.build_graph(hub_threshold=2, min_shared=2)) != {}

    def test_shared_list_is_capped_but_the_weight_is_not(self, monkeypatch):
        # An edge citing hundreds of values is unreadable everywhere; the
        # weight must still report the true magnitude.
        many = [_ioc(f"v{i}.example", "DOMAIN", ["a", "b"]) for i in range(30)]
        monkeypatch.setattr(
            "hermes_cli.case_memory_state.list_investigations",
            lambda: [{"name": "a", "store_path": "/a"}, {"name": "b", "store_path": "/b"}],
        )
        monkeypatch.setattr("hermes_cli.case_memory_state.list_iocs", lambda ioc_type=None: many)

        edge = _links(graph.build_graph())[("a", "b")]
        assert edge["weight"] == 30
        assert len(edge["shared"]) == 12
        assert edge["shared_truncated"] == 18


class TestFilters:
    def test_type_filter_restricts_which_indicators_link(self, index):
        g = graph.build_graph(ioc_type="DOMAIN", hub_threshold=2)
        edge = _links(g)[("harbour", "nightfall")]
        assert edge["shared"] == ["evil.example"]  # 9.9.9.1 is IPV4

    def test_type_filter_can_empty_the_graph(self, index):
        assert _links(graph.build_graph(ioc_type="FILE_HASH")) == {}


class TestPivots:
    def test_ranks_by_how_many_cases_an_indicator_joins(self, index):
        top = graph.pivots(graph.build_graph(hub_threshold=2))
        assert [p["label"] for p in top] == ["9.9.9.1", "evil.example"]

    def test_excludes_hubs(self, index):
        # An indicator in everything points at nothing.
        assert "8.8.8.8" not in [p["label"] for p in graph.pivots(graph.build_graph(hub_threshold=2))]

    def test_excludes_single_case_indicators(self, index):
        assert "only-nightfall.example" not in [p["label"] for p in graph.pivots(graph.build_graph())]

    def test_limit_is_honoured(self, index):
        assert len(graph.pivots(graph.build_graph(hub_threshold=2), limit=1)) == 1


class TestNeighbourhood:
    def test_finds_an_indicator_by_its_plain_value(self, index):
        # An analyst pastes a domain, not "ioc:DOMAIN:evil.example".
        found = graph.neighbourhood(graph.build_graph(hub_threshold=2), "evil.example")
        assert found["node"]["kind"] == "ioc"
        assert sorted(n["node"]["label"] for n in found["neighbours"]) == ["harbour", "nightfall"]

    def test_is_case_insensitive(self, index):
        assert graph.neighbourhood(graph.build_graph(), "EVIL.EXAMPLE") is not None

    def test_finds_an_investigation_and_reports_the_link_weight(self, index):
        found = graph.neighbourhood(graph.build_graph(hub_threshold=2), "nightfall")
        link = next(n for n in found["neighbours"] if n["node"]["label"] == "harbour")
        assert (link["via"], link["weight"]) == ("shared_ioc", 2)

    def test_an_exact_id_still_works(self, index):
        assert graph.neighbourhood(graph.build_graph(), "ioc:DOMAIN:evil.example") is not None

    @pytest.mark.parametrize("query", ["", "   ", "nope.example"])
    def test_unknown_returns_none(self, index, query):
        assert graph.neighbourhood(graph.build_graph(), query) is None


class TestDot:
    def test_draws_only_case_to_case_links(self, index):
        # Drawing the bipartite sighting edges too would hang every
        # indicator off the diagram as a leaf and bury the structure.
        dot = graph.to_dot(graph.build_graph(hub_threshold=2))
        assert '"harbour" -- "nightfall"' in dot
        assert "evil.example" not in dot

    def test_weight_drives_the_pen(self, index):
        assert 'label="2", penwidth=2.0' in graph.to_dot(graph.build_graph(hub_threshold=2))

    def test_quotes_are_escaped(self, monkeypatch):
        monkeypatch.setattr(
            "hermes_cli.case_memory_state.list_investigations",
            lambda: [{"name": 'we"ird', "store_path": "/a"}, {"name": "b", "store_path": "/b"}],
        )
        monkeypatch.setattr(
            "hermes_cli.case_memory_state.list_iocs",
            lambda ioc_type=None: [_ioc("x.example", "DOMAIN", ['we"ird', "b"])],
        )
        assert 'we\\"ird' in graph.to_dot(graph.build_graph())


class TestRobustness:
    def test_empty_index_is_an_empty_graph_not_a_crash(self, monkeypatch):
        monkeypatch.setattr("hermes_cli.case_memory_state.list_investigations", lambda: [])
        monkeypatch.setattr("hermes_cli.case_memory_state.list_iocs", lambda ioc_type=None: [])
        g = graph.build_graph()
        assert (g["nodes"], g["edges"]) == ([], [])
        assert g["stats"]["investigations"] == 0

    def test_malformed_entries_are_skipped(self, monkeypatch):
        # The index is a file on disk an operator can edit.
        monkeypatch.setattr(
            "hermes_cli.case_memory_state.list_investigations",
            lambda: [{"store_path": "/a"}, {"name": "", "store_path": "/b"}, {"name": "ok", "store_path": "/c"}],
        )
        monkeypatch.setattr(
            "hermes_cli.case_memory_state.list_iocs",
            lambda ioc_type=None: [
                {"type": "DOMAIN"},  # no value
                {"type": "DOMAIN", "value": "x.example", "sightings": ["not-a-dict", {"investigation": "ok"}]},
            ],
        )
        g = graph.build_graph()
        assert [n["label"] for n in g["nodes"] if n["kind"] == "investigation"] == ["ok"]
        assert [n["label"] for n in g["nodes"] if n["kind"] == "ioc"] == ["x.example"]

    def test_a_sighting_naming_an_unindexed_case_makes_no_edge(self, monkeypatch):
        # The index can carry a sighting for an investigation whose record
        # was removed; an edge to a node that does not exist would break
        # every renderer downstream.
        monkeypatch.setattr("hermes_cli.case_memory_state.list_investigations", lambda: [{"name": "a", "store_path": "/a"}])
        monkeypatch.setattr("hermes_cli.case_memory_state.list_iocs", lambda ioc_type=None: [_ioc("x.example", "DOMAIN", ["a", "ghost"])])

        g = graph.build_graph()
        ids = {n["id"] for n in g["nodes"]}
        for edge in g["edges"]:
            if edge["kind"] == "sighting":
                assert edge["target"] in ids

    def test_output_is_stable_across_runs(self, index):
        assert json.dumps(graph.build_graph(hub_threshold=2)) == json.dumps(graph.build_graph(hub_threshold=2))


class TestActors:
    def test_an_actor_becomes_a_node_linked_to_the_cases_it_touched(self, index):
        g = graph.build_graph(hub_threshold=2)
        actor = next(n for n in g["nodes"] if n["kind"] == "actor")
        assert actor["label"] == "analyst-a"
        assert actor["investigations"] == ["harbour", "nightfall"]


class TestGraphCommand:
    class _Args:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    def _args(self, **kwargs):
        base = dict(hub_threshold=2, include_hubs=False, min_shared=1, type=None, json=False, dot=False)
        base.update(kwargs)
        return self._Args(**base)

    def test_show_prints_the_link_its_indicators_and_the_hub(self, index, capsys):
        graph_cmd.graph_command(self._args(graph_command="show"))
        out = capsys.readouterr().out
        assert "harbour ── nightfall" in out
        assert "evil.example" in out
        assert "8.8.8.8" in out  # named as an excluded hub
        assert "Strongest pivots" in out

    def test_show_json_is_parseable(self, index, capsys):
        graph_cmd.graph_command(self._args(graph_command="show", json=True))
        assert json.loads(capsys.readouterr().out)["stats"]["links"] == 1

    def test_show_dot_emits_a_graph(self, index, capsys):
        graph_cmd.graph_command(self._args(graph_command="show", dot=True))
        assert capsys.readouterr().out.startswith("graph indagis {")

    def test_filtered_empty_result_does_not_claim_the_cases_are_unrelated(self, index, capsys):
        # The bug this test exists for: saying "no two investigations share
        # an indicator" when a filter did the hiding would send an analyst
        # away with the opposite of the truth.
        graph_cmd.graph_command(self._args(graph_command="links", min_shared=3))
        out = capsys.readouterr().out
        assert "min-shared 3" in out
        assert "share an indicator yet" not in out

    def test_genuinely_empty_result_does_say_so(self, monkeypatch, capsys):
        monkeypatch.setattr("hermes_cli.case_memory_state.list_investigations", lambda: [{"name": "a", "store_path": "/a"}])
        monkeypatch.setattr("hermes_cli.case_memory_state.list_iocs", lambda ioc_type=None: [])
        graph_cmd.graph_command(self._args(graph_command="links"))
        assert "share an indicator yet" in capsys.readouterr().out

    def test_empty_index_points_at_the_command_that_fills_it(self, monkeypatch, capsys):
        monkeypatch.setattr("hermes_cli.case_memory_state.list_investigations", lambda: [])
        monkeypatch.setattr("hermes_cli.case_memory_state.list_iocs", lambda ioc_type=None: [])
        graph_cmd.graph_command(self._args(graph_command="show"))
        assert "case ingest" in capsys.readouterr().out

    def test_node_reports_connections(self, index, capsys):
        graph_cmd.graph_command(self._args(graph_command="node", query="evil.example"))
        out = capsys.readouterr().out
        assert "2 connection(s)" in out
        assert "nightfall" in out

    def test_unknown_node_is_a_message_not_a_traceback(self, index, capsys):
        graph_cmd.graph_command(self._args(graph_command="node", query="nope.example"))
        assert "Nothing indexed under" in capsys.readouterr().err

    def test_unknown_subcommand_prints_usage(self, index, capsys):
        graph_cmd.graph_command(self._args(graph_command="bogus"))
        assert "indagis graph" in capsys.readouterr().err

    def test_bare_graph_defaults_to_show(self, index, capsys):
        graph_cmd.graph_command(self._args(graph_command=None))
        assert "Relationship graph" in capsys.readouterr().out


class TestParserWiring:
    """The commands must exist as argparse actually builds them — the check
    that caught a documented 'airgap engage' verb that was never implemented."""

    def _parser(self):
        import argparse

        from hermes_cli.subcommands.graph import build_graph_parser

        parser = argparse.ArgumentParser()
        build_graph_parser(parser.add_subparsers(dest="command"), cmd_graph=lambda args: None)
        return parser

    def test_every_documented_form_parses(self):
        parser = self._parser()

        args = parser.parse_args(["graph", "show", "--type", "DOMAIN", "--hub-threshold", "9", "--include-hubs", "--min-shared", "2", "--json"])
        assert (args.graph_command, args.type, args.hub_threshold, args.include_hubs, args.min_shared) == ("show", "DOMAIN", 9, True, 2)

        assert parser.parse_args(["graph", "show", "--dot"]).dot is True
        assert parser.parse_args(["graph", "links"]).graph_command == "links"
        assert parser.parse_args(["graph", "node", "evil.example"]).query == "evil.example"

    def test_defaults_match_the_engine(self):
        # A parser default that drifts from the engine's would make the
        # documented threshold a lie.
        assert self._parser().parse_args(["graph", "show"]).hub_threshold == graph.DEFAULT_HUB_THRESHOLD

    def test_node_requires_a_query(self):
        with pytest.raises(SystemExit):
            self._parser().parse_args(["graph", "node"])

    def test_an_invented_verb_is_rejected(self):
        with pytest.raises(SystemExit):
            self._parser().parse_args(["graph", "cluster"])

    def test_graph_is_a_known_builtin_subcommand(self):
        from hermes_cli.main import _BUILTIN_SUBCOMMANDS

        assert "graph" in _BUILTIN_SUBCOMMANDS
