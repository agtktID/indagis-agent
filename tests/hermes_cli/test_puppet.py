"""Tests for hermes_cli/puppet.py and hermes_cli/puppet_state.py —
Sock Puppet Manager."""

from hermes_cli import puppet, puppet_state


class TestCreatePersona:
    def test_creates_with_platform_and_investigation(self, capsys):
        puppet.puppet_create("ghost1", "twitter", "gh0st_recon", "case-alpha", "cover story notes")
        out = capsys.readouterr().out
        assert "Created persona 'ghost1'" in out
        record = puppet_state.get_persona("ghost1")
        assert record["platforms"][0] == {"platform": "twitter", "handle": "gh0st_recon", "added_at": record["platforms"][0]["added_at"]}
        assert record["investigation"] == "case-alpha"
        assert record["status"] == "active"

    def test_duplicate_alias_rejected(self, capsys):
        puppet.puppet_create("ghost1", "twitter", "a", None, None)
        capsys.readouterr()
        puppet.puppet_create("ghost1", "linkedin", "b", None, None)
        assert "already exists" in capsys.readouterr().out

    def test_handle_collision_warns_but_still_creates(self, capsys):
        puppet.puppet_create("ghost1", "twitter", "shared_handle", None, None)
        capsys.readouterr()
        puppet.puppet_create("ghost2", "twitter", "shared_handle", None, None)
        out = capsys.readouterr().out
        assert "already used by 1 other active persona" in out
        assert puppet_state.get_persona("ghost2") is not None


class TestPuppetList:
    def test_empty(self, capsys):
        puppet.puppet_list(None, None)
        assert "No personas found" in capsys.readouterr().out

    def test_filters_by_status(self, capsys):
        puppet.puppet_create("ghost1", "twitter", "a", None, None)
        puppet.puppet_create("ghost2", "twitter", "b", None, None)
        puppet.puppet_burn("ghost2", "exposed by target")
        capsys.readouterr()

        puppet.puppet_list("active", None)
        out = capsys.readouterr().out
        assert "ghost1" in out
        assert "ghost2" not in out

    def test_filters_by_investigation(self, capsys):
        puppet.puppet_create("ghost1", "twitter", "a", "case-a", None)
        puppet.puppet_create("ghost2", "twitter", "b", "case-b", None)
        capsys.readouterr()

        puppet.puppet_list(None, "case-a")
        out = capsys.readouterr().out
        assert "ghost1" in out
        assert "ghost2" not in out


class TestPuppetShow:
    def test_unknown_alias(self, capsys):
        puppet.puppet_show("nope")
        assert "No such persona" in capsys.readouterr().out

    def test_shows_footprint_and_notes(self, capsys):
        puppet.puppet_create("ghost1", "twitter", "gh0st", "case-a", "recon persona")
        capsys.readouterr()
        puppet.puppet_show("ghost1")
        out = capsys.readouterr().out
        assert "twitter:gh0st" in out
        assert "recon persona" in out
        assert "case-a" in out

    def test_shows_burn_reason(self, capsys):
        puppet.puppet_create("ghost1", "twitter", "a", None, None)
        puppet.puppet_burn("ghost1", "target recognized handle")
        capsys.readouterr()
        puppet.puppet_show("ghost1")
        out = capsys.readouterr().out
        assert "target recognized handle" in out


class TestAddPlatform:
    def test_unknown_alias(self, capsys):
        puppet.puppet_add_platform("nope", "linkedin", "x")
        assert "No such persona" in capsys.readouterr().out

    def test_adds_to_footprint(self, capsys):
        puppet.puppet_create("ghost1", "twitter", "a", None, None)
        capsys.readouterr()
        puppet.puppet_add_platform("ghost1", "linkedin", "b")
        out = capsys.readouterr().out
        assert "Added linkedin:b" in out
        record = puppet_state.get_persona("ghost1")
        assert len(record["platforms"]) == 2

    def test_refuses_on_burned_persona(self, capsys):
        puppet.puppet_create("ghost1", "twitter", "a", None, None)
        puppet.puppet_burn("ghost1", "exposed")
        capsys.readouterr()
        puppet.puppet_add_platform("ghost1", "linkedin", "b")
        out = capsys.readouterr().out
        assert "burned" in out
        record = puppet_state.get_persona("ghost1")
        assert len(record["platforms"]) == 1

    def test_warns_on_handle_collision(self, capsys):
        puppet.puppet_create("ghost1", "twitter", "a", None, None)
        puppet.puppet_create("ghost2", "linkedin", "shared", None, None)
        capsys.readouterr()
        puppet.puppet_add_platform("ghost1", "linkedin", "shared")
        out = capsys.readouterr().out
        assert "already used by 1 other active persona" in out


class TestPuppetUse:
    def test_unknown_alias(self, capsys):
        puppet.puppet_use("nope", None)
        assert "No such persona" in capsys.readouterr().out

    def test_refuses_burned_persona(self, capsys):
        puppet.puppet_create("ghost1", "twitter", "a", None, None)
        puppet.puppet_burn("ghost1", "exposed")
        capsys.readouterr()
        puppet.puppet_use("ghost1", "case-a")
        out = capsys.readouterr().out
        assert "BURNED" in out
        record = puppet_state.get_persona("ghost1")
        assert record["last_used_at"] is None

    def test_binds_investigation_on_first_use(self, capsys):
        puppet.puppet_create("ghost1", "twitter", "a", None, None)
        capsys.readouterr()
        puppet.puppet_use("ghost1", "case-a")
        record = puppet_state.get_persona("ghost1")
        assert record["investigation"] == "case-a"
        assert record["last_used_at"] is not None

    def test_isolation_warning_on_cross_case_reuse(self, capsys):
        puppet.puppet_create("ghost1", "twitter", "a", "case-a", None)
        capsys.readouterr()
        puppet.puppet_use("ghost1", "case-b")
        out = capsys.readouterr().out
        assert "ISOLATION WARNING" in out
        assert "case-a" in out and "case-b" in out

    def test_no_warning_for_same_investigation(self, capsys):
        puppet.puppet_create("ghost1", "twitter", "a", "case-a", None)
        capsys.readouterr()
        puppet.puppet_use("ghost1", "case-a")
        out = capsys.readouterr().out
        assert "ISOLATION WARNING" not in out

    def test_retired_persona_warns_but_records_use(self, capsys):
        puppet.puppet_create("ghost1", "twitter", "a", None, None)
        puppet.puppet_retire("ghost1")
        capsys.readouterr()
        puppet.puppet_use("ghost1", None)
        out = capsys.readouterr().out
        assert "retired" in out
        record = puppet_state.get_persona("ghost1")
        assert record["last_used_at"] is not None


class TestBurnAndRetire:
    def test_burn_unknown(self, capsys):
        puppet.puppet_burn("nope", "reason")
        assert "No such persona" in capsys.readouterr().out

    def test_burn_sets_status_and_reason(self, capsys):
        puppet.puppet_create("ghost1", "twitter", "a", None, None)
        capsys.readouterr()
        puppet.puppet_burn("ghost1", "target recognized handle")
        out = capsys.readouterr().out
        assert "BURNED" in out
        record = puppet_state.get_persona("ghost1")
        assert record["status"] == "burned"
        assert record["burn_reason"] == "target recognized handle"

    def test_retire_unknown(self, capsys):
        puppet.puppet_retire("nope")
        assert "No such persona" in capsys.readouterr().out

    def test_retire_sets_status(self, capsys):
        puppet.puppet_create("ghost1", "twitter", "a", None, None)
        capsys.readouterr()
        puppet.puppet_retire("ghost1")
        record = puppet_state.get_persona("ghost1")
        assert record["status"] == "retired"


class TestPuppetCommandDispatch:
    def test_default_action_lists(self, monkeypatch):
        called = []
        monkeypatch.setattr(puppet, "puppet_list", lambda status, investigation: called.append((status, investigation)))
        args = type("Args", (), {"puppet_command": None})()
        puppet.puppet_command(args)
        assert called == [(None, None)]

    def test_create_action_routes(self, monkeypatch):
        called = []
        monkeypatch.setattr(puppet, "puppet_create", lambda *a: called.append(a))
        args = type("Args", (), {
            "puppet_command": "create", "alias": "g1", "platform": "twitter",
            "handle": "h", "investigation": "case-a", "notes": "n",
        })()
        puppet.puppet_command(args)
        assert called == [("g1", "twitter", "h", "case-a", "n")]

    def test_unknown_action(self, capsys):
        args = type("Args", (), {"puppet_command": "bogus"})()
        puppet.puppet_command(args)
        assert "Unknown puppet subcommand" in capsys.readouterr().err


class TestFindHandleCollisions:
    def test_excludes_own_id(self):
        record = puppet_state.create_persona("ghost1", platform="twitter", handle="a", investigation=None, notes=None)
        hits = puppet_state.find_handle_collisions("twitter", "a", exclude_id=record["id"])
        assert hits == []

    def test_ignores_non_active_personas(self):
        puppet_state.create_persona("ghost1", platform="twitter", handle="a", investigation=None, notes=None)
        puppet_state.set_status("ghost1", "burned")
        hits = puppet_state.find_handle_collisions("twitter", "a")
        assert hits == []
