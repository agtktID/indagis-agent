"""Tests for hermes_cli/surface.py — Surface Diff CLI command handlers."""

import pytest

from hermes_cli import surface


@pytest.fixture(autouse=True)
def _tmp_cron_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("cron.jobs.CRON_DIR", tmp_path / "cron")
    monkeypatch.setattr("cron.jobs.JOBS_FILE", tmp_path / "cron" / "jobs.json")
    monkeypatch.setattr("cron.jobs.OUTPUT_DIR", tmp_path / "cron" / "output")


def _fake_snapshot(ips):
    return {"host": "example.com", "ips": ips, "http": None, "https": None, "tls_cert": None}


class TestSurfaceSnapshot:
    def test_saves_and_reports(self, monkeypatch, capsys):
        monkeypatch.setattr(surface, "take_snapshot", lambda host: _fake_snapshot(["1.2.3.4"]))
        surface.surface_snapshot("acme", "example.com")
        out = capsys.readouterr().out
        assert "Snapshot saved" in out
        assert "1.2.3.4" in out


class TestSurfaceDiff:
    def test_not_enough_snapshots(self, capsys):
        surface.surface_diff("nope")
        assert "No snapshots" in capsys.readouterr().out

    def test_one_snapshot_reports_need_another(self, monkeypatch, capsys):
        monkeypatch.setattr(surface, "take_snapshot", lambda host: _fake_snapshot(["1.1.1.1"]))
        surface.surface_snapshot("acme", "example.com")
        capsys.readouterr()

        surface.surface_diff("acme")
        assert "Only 1 snapshot" in capsys.readouterr().out

    def test_reports_no_change(self, monkeypatch, capsys):
        monkeypatch.setattr(surface, "take_snapshot", lambda host: _fake_snapshot(["1.1.1.1"]))
        surface.surface_snapshot("acme", "example.com")
        surface.surface_snapshot("acme", "example.com")
        capsys.readouterr()

        surface.surface_diff("acme")
        assert "No change" in capsys.readouterr().out

    def test_reports_change(self, monkeypatch, capsys):
        monkeypatch.setattr(surface, "take_snapshot", lambda host: _fake_snapshot(["1.1.1.1"]))
        surface.surface_snapshot("acme", "example.com")
        monkeypatch.setattr(surface, "take_snapshot", lambda host: _fake_snapshot(["2.2.2.2"]))
        surface.surface_snapshot("acme", "example.com")
        capsys.readouterr()

        surface.surface_diff("acme")
        out = capsys.readouterr().out
        assert "Surface changed" in out
        assert "2.2.2.2" in out


class TestSurfaceHistoryAndTargets:
    def test_history_empty(self, capsys):
        surface.surface_history("nope")
        assert "No snapshots" in capsys.readouterr().out

    def test_history_lists_entries(self, monkeypatch, capsys):
        monkeypatch.setattr(surface, "take_snapshot", lambda host: _fake_snapshot(["1.1.1.1"]))
        surface.surface_snapshot("acme", "example.com")
        capsys.readouterr()
        surface.surface_history("acme")
        assert ".json" in capsys.readouterr().out

    def test_targets_empty(self, capsys):
        surface.surface_targets()
        assert "No targets" in capsys.readouterr().out

    def test_targets_lists_with_counts(self, monkeypatch, capsys):
        monkeypatch.setattr(surface, "take_snapshot", lambda host: _fake_snapshot(["1.1.1.1"]))
        surface.surface_snapshot("acme", "example.com")
        capsys.readouterr()
        surface.surface_targets()
        out = capsys.readouterr().out
        assert "acme" in out
        assert "1 snapshot" in out


class TestSurfaceSchedule:
    def test_requires_deliver(self, capsys):
        surface.surface_schedule("acme", "example.com", "every 1h", "")
        assert "--deliver is required" in capsys.readouterr().out

    def test_creates_cron_job_and_generated_script(self, capsys):
        from hermes_constants import get_indagis_home

        surface.surface_schedule("acme", "example.com", "every 6h", "local")
        out = capsys.readouterr().out
        assert "Scheduled surface monitoring for 'acme'" in out

        from cron.jobs import list_jobs

        jobs = list_jobs()
        assert len(jobs) == 1
        assert jobs[0]["no_agent"] is True
        assert jobs[0]["script"] == surface._script_filename("acme")

        script_path = get_indagis_home() / "scripts" / surface._script_filename("acme")
        assert script_path.exists()
        assert "run_surface_check" in script_path.read_text()
        assert "'acme'" in script_path.read_text()
        assert "'example.com'" in script_path.read_text()

    def test_invalid_schedule_cleans_up_script(self):
        from hermes_constants import get_indagis_home

        surface.surface_schedule("acme", "example.com", "not a valid schedule", "local")
        script_path = get_indagis_home() / "scripts" / surface._script_filename("acme")
        assert not script_path.exists()
