"""Tests for hermes_cli/watch.py — Signal Watch CLI command handlers.

Uses the real cron.jobs module (redirected to a temp dir, same pattern as
tests/cron/test_jobs.py) rather than mocking it — watch_create's whole job
is wiring a watch rule to a real cron job correctly, so exercising the
real create_job/pause_job/resume_job/remove_job is the point.
"""

import pytest

from hermes_cli import watch
from hermes_cli.watch_state import get_watch_record, list_watch_records


@pytest.fixture(autouse=True)
def _tmp_cron_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("cron.jobs.CRON_DIR", tmp_path / "cron")
    monkeypatch.setattr("cron.jobs.JOBS_FILE", tmp_path / "cron" / "jobs.json")
    monkeypatch.setattr("cron.jobs.OUTPUT_DIR", tmp_path / "cron" / "output")


@pytest.fixture(autouse=True)
def _silence_gateway_warning(monkeypatch):
    monkeypatch.setattr(watch, "_warn_if_gateway_not_running", lambda: None)


class TestWatchCreate:
    def test_creates_registry_entry_and_cron_job(self, capsys):
        watch.watch_create(kind="url-hash", target="https://example.com", schedule="every 1h", deliver="local", name="my rule")
        out = capsys.readouterr().out
        assert "Watch created" in out

        records = list_watch_records()
        assert len(records) == 1
        record = records[0]
        assert record["kind"] == "url-hash"
        assert record["target"] == "https://example.com"

        from cron.jobs import get_job

        job = get_job(record["cron_job_id"])
        assert job is not None
        assert job["script"] == f"watch_{record['id']}.py"
        assert job["no_agent"] is True

    def test_script_filename_matches_registry_id(self, tmp_path, monkeypatch):
        """Regression guard for the watch_id-mismatch bug: the generated
        script's filename must embed the same ID as the registry key."""
        from hermes_constants import get_indagis_home

        watch.watch_create(kind="url-hash", target="https://example.com", schedule="every 1h", deliver="local")
        record = list_watch_records()[0]
        script_path = get_indagis_home() / "scripts" / f"watch_{record['id']}.py"
        assert script_path.exists()
        assert record["id"] in script_path.read_text()

    def test_unknown_kind_rejected(self, capsys):
        watch.watch_create(kind="not-a-kind", target="x", schedule="every 1h", deliver="local")
        assert "Unknown watch kind" in capsys.readouterr().out
        assert list_watch_records() == []

    def test_missing_deliver_rejected(self, capsys):
        watch.watch_create(kind="url-hash", target="https://x.test", schedule="every 1h", deliver="")
        assert "deliver is required" in capsys.readouterr().out
        assert list_watch_records() == []

    def test_invalid_schedule_cleans_up_generated_script(self, tmp_path):
        from hermes_constants import get_indagis_home

        watch.watch_create(kind="url-hash", target="https://x.test", schedule="not a valid schedule", deliver="local")
        assert list_watch_records() == []
        # No orphaned script left behind after the cron job creation failed.
        scripts_dir = get_indagis_home() / "scripts"
        assert not any(scripts_dir.glob("watch_*.py")) if scripts_dir.exists() else True


class TestWatchLifecycle:
    def _create(self):
        watch.watch_create(kind="url-hash", target="https://example.com", schedule="every 1h", deliver="local", name="rule")
        return list_watch_records()[0]["id"]

    def test_pause_and_resume(self, capsys):
        watch_id = self._create()
        from cron.jobs import get_job

        watch.watch_pause(watch_id)
        assert "Paused" in capsys.readouterr().out
        record = get_watch_record(watch_id)
        assert get_job(record["cron_job_id"])["enabled"] is False

        watch.watch_resume(watch_id)
        assert "Resumed" in capsys.readouterr().out
        assert get_job(record["cron_job_id"])["enabled"] is True

    def test_pause_missing_watch(self, capsys):
        watch.watch_pause("wch_nope")
        assert "No such watch" in capsys.readouterr().out

    def test_remove_deletes_registry_and_cron_job(self, capsys):
        watch_id = self._create()
        record = get_watch_record(watch_id)
        cron_job_id = record["cron_job_id"]

        watch.watch_remove(watch_id)
        assert "Removed" in capsys.readouterr().out
        assert get_watch_record(watch_id) is None

        from cron.jobs import get_job

        assert get_job(cron_job_id) is None

    def test_show_missing_watch(self, capsys):
        watch.watch_show("wch_nope")
        assert "No such watch" in capsys.readouterr().out

    def test_show_existing_watch(self, capsys):
        watch_id = self._create()
        watch.watch_show(watch_id)
        out = capsys.readouterr().out
        assert watch_id in out
        assert "url-hash" in out


class TestWatchRun:
    def test_forces_immediate_check_and_always_prints(self, monkeypatch, capsys):
        watch_id = self._make_rule()

        def fake_checker(target, state):
            return None, {**state, "last_status": "ok"}

        monkeypatch.setitem(watch.CHECKERS, "url-hash", fake_checker)
        watch.watch_run(watch_id)
        assert "No change detected" in capsys.readouterr().out

    def test_reports_alert_when_fired(self, monkeypatch, capsys):
        watch_id = self._make_rule()

        def fake_checker(target, state):
            return "it changed", state

        monkeypatch.setitem(watch.CHECKERS, "url-hash", fake_checker)
        watch.watch_run(watch_id)
        out = capsys.readouterr().out
        assert "Alert would fire" in out
        assert "it changed" in out

    def test_missing_watch(self, capsys):
        watch.watch_run("wch_nope")
        assert "No such watch" in capsys.readouterr().out

    def _make_rule(self):
        watch.watch_create(kind="url-hash", target="https://example.com", schedule="every 1h", deliver="local")
        return list_watch_records()[0]["id"]
