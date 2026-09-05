"""Tests for plugins/image/dashboard/plugin_api.py — the Image Intel router.

The security property under test is the one that shapes the module: the
router must expose no way to read EXIF from a caller-supplied path, and the
store it does read must come off the case-memory allowlist. A regression
here is an arbitrary-file-read, so the allowlist tests drive the real
FastAPI app rather than calling the helper directly.
"""

import importlib.util
import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from hermes_cli import image_intel

_MODULE_PATH = Path(__file__).resolve().parents[2] / "plugins" / "image" / "dashboard" / "plugin_api.py"


def _load_router_module():
    spec = importlib.util.spec_from_file_location("indagis_image_plugin_api", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def client(monkeypatch, tmp_path):
    """A real app with the real router, over a real store on the allowlist."""
    module = _load_router_module()

    store = tmp_path / "case.json"
    store.write_text(
        json.dumps(
            {
                "evidence": [
                    {
                        "id": "ev-001",
                        "type": "image_metadata",
                        "source": "photo.jpg",
                        "content": "a" * 64,
                        "ioc_type": "FILE_HASH",
                        "notes": "NIKON D850 · serial present · GPS present",
                        "collected_at": "2026-01-02T00:00:00+00:00",
                        "verification": "unverified",
                    },
                    {
                        "id": "ev-002",
                        "type": "ioc",
                        "source": "photo.jpg",
                        "content": "48.8582222,2.2945",
                        "ioc_type": "GEO",
                        "notes": "EXIF GPS from photo.jpg",
                        "collected_at": "2026-01-02T00:00:00+00:00",
                    },
                    {
                        "id": "ev-003",
                        "type": "image_metadata",
                        "source": "nogps.jpg",
                        "content": "b" * 64,
                        "ioc_type": "FILE_HASH",
                        "notes": "no EXIF metadata",
                        "collected_at": "2026-01-03T00:00:00+00:00",
                    },
                ],
                "chain_of_custody": [],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        module, "list_investigations", lambda: [{"name": "op-nightfall", "store_path": str(store)}]
    )

    app = FastAPI()
    app.include_router(module.router)
    return TestClient(app), store


class TestAllowlist:
    def test_recorded_store_is_readable(self, client):
        http, store = client
        response = http.get("/images", params={"store_path": str(store)})
        assert response.status_code == 200
        assert response.json()["total"] == 2

    def test_unrecorded_path_is_404_and_leaks_nothing(self, client, tmp_path):
        http, _ = client
        other = tmp_path / "not-on-the-list.json"
        other.write_text('{"evidence": [{"id": "x", "type": "image_metadata", "source": "s", "content": "leak"}]}', encoding="utf-8")

        response = http.get("/images", params={"store_path": str(other)})

        assert response.status_code == 404
        assert "leak" not in response.text

    def test_traversal_cannot_walk_out(self, client, tmp_path):
        # Resolution happens on the real path, so a '..' detour that lands
        # somewhere off the list is still refused.
        http, store = client
        detour = f"{store.parent}/../{store.parent.name}/not-the-store.json"
        assert http.get("/images", params={"store_path": detour}).status_code == 404

    def test_symlink_to_an_allowed_name_is_still_judged_on_its_target(self, client, tmp_path):
        http, _ = client
        secret = tmp_path / "secret.json"
        secret.write_text('{"evidence": []}', encoding="utf-8")
        link = tmp_path / "looks-fine.json"
        link.symlink_to(secret)

        assert http.get("/images", params={"store_path": str(link)}).status_code == 404

    def test_traversal_onto_the_allowed_store_still_resolves_to_it(self, client, tmp_path):
        # The mirror of the test above: '..' is not itself the offence —
        # resolving to a store that IS on the list is fine.
        http, store = client
        detour = f"{store.parent}/../{store.parent.name}/{store.name}"
        assert http.get("/images", params={"store_path": detour}).status_code == 200


class TestNoInspectRoute:
    """The whole point of the module: no route reads an arbitrary image."""

    def test_router_exposes_only_the_two_read_routes(self):
        module = _load_router_module()
        paths = {route.path for route in module.router.routes}
        assert paths == {"/investigations", "/images"}

    def test_inspect_and_scrub_are_not_wrapped(self):
        source = _MODULE_PATH.read_text(encoding="utf-8")
        body = source.split('"""', 2)[2]  # skip the module docstring, which names them
        assert "inspect_image" not in body
        assert "scrub_image" not in body


class TestImagesPayload:
    def test_gps_is_paired_onto_its_image(self, client):
        http, store = client
        images = {entry["filename"]: entry for entry in http.get("/images", params={"store_path": str(store)}).json()["images"]}

        assert images["photo.jpg"]["gps"]["latitude"] == pytest.approx(48.8582222)
        assert "openstreetmap.org" in images["photo.jpg"]["gps"]["map_url"]
        assert images["nogps.jpg"]["gps"] is None

    def test_counts_match_the_listing(self, client):
        http, store = client
        payload = http.get("/images", params={"store_path": str(store)}).json()
        assert payload["total"] == len(payload["images"]) == 2
        assert payload["geolocated"] == sum(1 for e in payload["images"] if e["gps"])

    def test_newest_first(self, client):
        http, store = client
        payload = http.get("/images", params={"store_path": str(store)}).json()
        assert [e["filename"] for e in payload["images"]] == ["nogps.jpg", "photo.jpg"]

    def test_investigations_reports_whether_the_file_exists(self, client):
        http, store = client
        records = http.get("/investigations").json()["investigations"]
        assert records[0]["exists"] is True
        store.unlink()
        assert http.get("/investigations").json()["investigations"][0]["exists"] is False


class TestCollectStoreImages:
    """The pure function behind the route."""

    def _write(self, tmp_path, payload):
        store = tmp_path / "s.json"
        store.write_text(json.dumps(payload), encoding="utf-8")
        return str(store)

    def test_store_without_images_is_empty_not_an_error(self, tmp_path):
        path = self._write(tmp_path, {"evidence": [{"id": "ev-001", "type": "ioc", "content": "1.2.3.4"}]})
        assert image_intel.collect_store_images(path) == []

    def test_missing_evidence_array_is_empty(self, tmp_path):
        assert image_intel.collect_store_images(self._write(tmp_path, {"case_id": "x"})) == []

    def test_malformed_entries_are_skipped_not_fatal(self, tmp_path):
        # An evidence store is operator-editable, so one bad record must not
        # take down the listing.
        path = self._write(
            tmp_path,
            {
                "evidence": [
                    "not-a-dict",
                    {"type": "image_metadata"},  # no source
                    {"type": "image_metadata", "source": "ok.jpg", "content": "c" * 64},
                    {"ioc_type": "GEO", "source": "ok.jpg", "content": "not,coordinates"},
                ]
            },
        )
        entries = image_intel.collect_store_images(path)
        assert len(entries) == 1
        assert entries[0]["filename"] == "ok.jpg"
        assert entries[0]["gps"] is None  # the unparseable coordinate was dropped

    def test_non_object_json_raises(self, tmp_path):
        store = tmp_path / "list.json"
        store.write_text("[1, 2, 3]", encoding="utf-8")
        with pytest.raises(ValueError):
            image_intel.collect_store_images(str(store))

    def test_round_trip_from_append_to_store(self, tmp_path):
        # The real pairing test: what append_to_store writes must be exactly
        # what collect_store_images reads back.
        pytest.importorskip("PIL")
        from tests.hermes_cli.test_image_intel import _build_image

        store = tmp_path / "case.json"
        store.write_text('{"evidence": [], "chain_of_custody": []}', encoding="utf-8")
        report = image_intel.inspect_image(str(_build_image(tmp_path / "photo.jpg")))
        image_intel.append_to_store(str(store), report)

        entries = image_intel.collect_store_images(str(store))

        assert len(entries) == 1
        assert entries[0]["sha256"] == report["sha256"]
        assert entries[0]["gps"]["latitude"] == pytest.approx(report["gps"]["latitude"])
