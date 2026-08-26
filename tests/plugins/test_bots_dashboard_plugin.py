"""Bots dashboard plugin: list + create Bot-Mode-managed profiles.

Attaches the plugin router to a bare FastAPI app (same harness as
test_kanban_board_project_api.py) and exercises GET/POST /bots.
"""

from __future__ import annotations

import importlib.util
import sys
import textwrap
from pathlib import Path

import pytest
import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _plugin_module():
    repo_root = Path(__file__).resolve().parents[2]
    plugin_file = repo_root / "plugins" / "bots" / "dashboard" / "plugin_api.py"
    spec = importlib.util.spec_from_file_location("hermes_bots_plugin_test", plugin_file)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def bots_home(tmp_path, monkeypatch):
    home = tmp_path / ".indagis"
    home.mkdir()
    monkeypatch.setenv("INDAGIS_HOME", str(home))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    return home


@pytest.fixture
def plugin_module(bots_home):
    return _plugin_module()


@pytest.fixture
def client(plugin_module):
    app = FastAPI()
    app.include_router(plugin_module.router, prefix="/api/plugins/bots")
    return TestClient(app)


def _make_bot_profile(home, name, *, title="", managed=True):
    d = home / "profiles" / name
    d.mkdir(parents=True, exist_ok=True)
    if managed:
        d.joinpath("profile.yaml").write_text(
            textwrap.dedent(
                f"""\
                description: teammate for tests
                ui_meta:
                  hermes-bots:
                    title: {title or "''"}
                """
            ),
            encoding="utf-8",
        )
    return d


def test_list_bots_excludes_unmanaged_profiles(client, bots_home):
    _make_bot_profile(bots_home, "researcher", title="Research Buddy", managed=True)
    _make_bot_profile(bots_home, "scratch", managed=False)

    r = client.get("/api/plugins/bots/bots")

    assert r.status_code == 200
    names = {b["name"] for b in r.json()["bots"]}
    assert names == {"researcher"}
    hit = next(b for b in r.json()["bots"] if b["name"] == "researcher")
    assert hit["handle"] == "researcher"
    assert hit["title"] == "Research Buddy"
    assert hit["is_default"] is False


def test_list_bots_default_profile_aliased_hermes(client, bots_home):
    bots_home.joinpath("profile.yaml").write_text(
        textwrap.dedent(
            """\
            ui_meta:
              hermes-bots:
                title: Main
            """
        ),
        encoding="utf-8",
    )

    r = client.get("/api/plugins/bots/bots")

    assert r.status_code == 200
    hit = next(b for b in r.json()["bots"] if b["is_default"])
    assert hit["name"] == "default"
    assert hit["handle"] == "hermes"
    assert hit["title"] == "Main"


def test_create_bot_writes_profile_and_ui_meta(client, bots_home):
    r = client.post(
        "/api/plugins/bots/bots",
        json={"name": "researcher", "title": "Research Buddy", "description": "Deep research"},
    )

    assert r.status_code == 200
    body = r.json()["bot"]
    assert body == {
        "name": "researcher",
        "handle": "researcher",
        "is_default": False,
        "title": "Research Buddy",
        "description": "Deep research",
    }

    profile_yaml = bots_home / "profiles" / "researcher" / "profile.yaml"
    assert profile_yaml.is_file()
    data = yaml.safe_load(profile_yaml.read_text(encoding="utf-8"))
    assert data["description"] == "Deep research"
    assert data["ui_meta"]["hermes-bots"]["title"] == "Research Buddy"

    listed = client.get("/api/plugins/bots/bots").json()["bots"]
    assert [b["name"] for b in listed] == ["researcher"]


def test_create_bot_rejects_duplicate_name(client, bots_home):
    client.post("/api/plugins/bots/bots", json={"name": "researcher"})

    r = client.post("/api/plugins/bots/bots", json={"name": "researcher"})

    assert r.status_code == 409


def test_create_bot_rejects_invalid_name(client, bots_home):
    r = client.post("/api/plugins/bots/bots", json={"name": "not a valid name!"})

    assert r.status_code == 400


def test_write_bot_meta_preserves_existing_profile_yaml_keys(plugin_module, bots_home):
    """_write_bot_meta must never clobber sibling keys already in the file."""
    d = _make_bot_profile(bots_home, "existing", managed=False)
    d.joinpath("profile.yaml").write_text(
        "description: hand-authored\nsome_other_key: keep-me\n", encoding="utf-8"
    )

    plugin_module._write_bot_meta(d, title="Existing Bot")

    data = yaml.safe_load((d / "profile.yaml").read_text(encoding="utf-8"))
    assert data["description"] == "hand-authored"
    assert data["some_other_key"] == "keep-me"
    assert data["ui_meta"]["hermes-bots"]["title"] == "Existing Bot"
