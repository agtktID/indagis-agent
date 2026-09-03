"""Tests for hermes_cli/watch_runner.py — the no_agent cron script entrypoint."""

from hermes_cli import watch_checks
from hermes_cli.watch_runner import main, run_watch
from hermes_cli.watch_state import create_watch_record, generate_watch_id, get_watch_state


def _make_rule(kind="url-hash", target="https://example.com"):
    watch_id = generate_watch_id()
    create_watch_record(
        watch_id=watch_id, kind=kind, target=target, name="test rule",
        cron_job_id="job1", deliver="local", schedule="every 1h",
    )
    return watch_id


class TestRunWatch:
    def test_missing_registry_entry_stays_silent(self, capsys):
        # A generated script surviving after its registry entry was removed
        # by hand must not alert about its own bookkeeping.
        run_watch("wch_doesnotexist")
        assert capsys.readouterr().out == ""

    def test_unknown_kind_prints_warning(self, monkeypatch, capsys):
        watch_id = _make_rule()
        from hermes_cli import watch_state

        record = watch_state.get_watch_record(watch_id)
        record["kind"] = "not-a-real-kind"
        watch_state._save_registry({watch_id: record})

        run_watch(watch_id)
        out = capsys.readouterr().out
        assert "unknown check kind" in out.lower()

    def test_silent_on_baseline_and_no_change(self, monkeypatch, capsys):
        watch_id = _make_rule()

        def fake_checker(target, state):
            return None, {**state, "hash": "x", "last_status": "ok"}

        monkeypatch.setitem(watch_checks.CHECKERS, "url-hash", fake_checker)

        run_watch(watch_id)
        assert capsys.readouterr().out == ""
        assert get_watch_state(watch_id)["hash"] == "x"

    def test_prints_alert_when_checker_fires(self, monkeypatch, capsys):
        watch_id = _make_rule()

        def fake_checker(target, state):
            return "something changed", {**state, "last_status": "ok"}

        monkeypatch.setitem(watch_checks.CHECKERS, "url-hash", fake_checker)

        run_watch(watch_id)
        out = capsys.readouterr().out
        assert "test rule" in out
        assert "something changed" in out

    def test_state_persisted_even_when_silent(self, monkeypatch):
        watch_id = _make_rule()

        def fake_checker(target, state):
            return None, {"marker": "persisted"}

        monkeypatch.setitem(watch_checks.CHECKERS, "url-hash", fake_checker)
        run_watch(watch_id)
        assert get_watch_state(watch_id)["marker"] == "persisted"


class TestMain:
    def test_no_args_returns_usage_error(self, capsys):
        assert main([]) == 2
        assert "usage" in capsys.readouterr().err.lower()

    def test_dispatches_to_run_watch(self, monkeypatch, capsys):
        watch_id = _make_rule()

        def fake_checker(target, state):
            return None, state

        monkeypatch.setitem(watch_checks.CHECKERS, "url-hash", fake_checker)
        assert main([watch_id]) == 0
