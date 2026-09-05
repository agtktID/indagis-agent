"""Tests for plugins/graph/dashboard/plugin_api.py — the Relationship Graph router.

Unlike the Dossier Builder and Image Intel routers there is no path
allowlist to defend, because nothing here opens a caller-supplied path. What
does need defending is the cost bound: the hub cut is what keeps one request
from pairing an indicator across an unbounded number of investigations, so a
client must not be able to raise the threshold arbitrarily.
"""

import importlib.util
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

_MODULE_PATH = Path(__file__).resolve().parents[2] / "plugins" / "graph" / "dashboard" / "plugin_api.py"


def _ioc(value, kind, cases):
    return {
        "type": kind,
        "value": value,
        "sightings": [{"investigation": c, "store_path": f"/s/{c}", "evidence_id": "ev-001", "actor": None, "source": "recon"} for c in cases],
    }


@pytest.fixture
def client(monkeypatch):
    spec = importlib.util.spec_from_file_location("indagis_graph_plugin_api", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    iocs = [
        _ioc("evil.example", "DOMAIN", ["nightfall", "harbour"]),
        _ioc("9.9.9.1", "IPV4", ["nightfall", "harbour"]),
        _ioc("8.8.8.8", "IPV4", ["nightfall", "harbour", "driftwood"]),
    ]
    monkeypatch.setattr(
        "hermes_cli.case_memory_state.list_investigations",
        lambda: [{"name": n, "store_path": f"/s/{n}"} for n in ("nightfall", "harbour", "driftwood")],
    )
    monkeypatch.setattr(
        "hermes_cli.case_memory_state.list_iocs",
        lambda ioc_type=None: [e for e in iocs if ioc_type is None or e["type"] == ioc_type],
    )

    app = FastAPI()
    app.include_router(module.router)
    return TestClient(app), module


class TestRoutes:
    def test_router_exposes_only_the_two_read_routes(self, client):
        _, module = client
        assert {route.path for route in module.router.routes} == {"/graph", "/node"}

    def test_graph_returns_links_and_pivots(self, client):
        http, _ = client
        payload = http.get("/graph", params={"hub_threshold": 2}).json()

        assert payload["stats"]["links"] == 1
        assert [p["label"] for p in payload["pivots"]] == ["9.9.9.1", "evil.example"]

    def test_hub_is_excluded_over_http_too(self, client):
        http, _ = client
        payload = http.get("/graph", params={"hub_threshold": 2}).json()

        assert [h["value"] for h in payload["hubs"]] == ["8.8.8.8"]
        pairs = {(e["source"], e["target"]) for e in payload["edges"] if e["kind"] == "shared_ioc"}
        assert not any("driftwood" in s or "driftwood" in t for s, t in pairs)

    def test_include_hubs_puts_the_links_back(self, client):
        http, _ = client
        payload = http.get("/graph", params={"hub_threshold": 2, "include_hubs": True}).json()
        assert payload["stats"]["links"] == 3

    def test_node_returns_a_neighbourhood(self, client):
        http, _ = client
        found = http.get("/node", params={"query": "evil.example", "hub_threshold": 2}).json()
        assert sorted(n["node"]["label"] for n in found["neighbours"]) == ["harbour", "nightfall"]

    def test_unknown_node_is_404(self, client):
        http, _ = client
        assert http.get("/node", params={"query": "nope.example"}).status_code == 404


class TestCostBound:
    """The hub cut is what bounds the pairing work, so a client must not be
    able to raise it out of range."""

    @pytest.mark.parametrize("bad", [0, -1, 101, 999999])
    def test_out_of_range_hub_threshold_is_refused(self, client, bad):
        http, _ = client
        assert http.get("/graph", params={"hub_threshold": bad}).status_code == 422

    def test_min_shared_below_one_is_refused(self, client):
        http, _ = client
        assert http.get("/graph", params={"min_shared": 0}).status_code == 422

    def test_the_ceiling_itself_is_allowed(self, client):
        http, _ = client
        assert http.get("/graph", params={"hub_threshold": 100}).status_code == 200

    def test_node_validates_the_same_way(self, client):
        # A bound enforced on one route and not the other is not a bound.
        http, _ = client
        assert http.get("/node", params={"query": "evil.example", "hub_threshold": 0}).status_code == 422
