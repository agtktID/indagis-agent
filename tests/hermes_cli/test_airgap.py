"""Tests for hermes_cli/airgap.py and airgap_state.py — Air Gap lockdown/restore."""

import pytest

from hermes_cli import airgap, watch
from hermes_cli.airgap_state import load_manifest
from hermes_cli.watch_state import list_watch_records


@pytest.fixture(autouse=True)
def _tmp_cron_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("cron.jobs.CRON_DIR", tmp_path / "cron")
    monkeypatch.setattr("cron.jobs.JOBS_FILE", tmp_path / "cron" / "jobs.json")
    monkeypatch.setattr("cron.jobs.OUTPUT_DIR", tmp_path / "cron" / "output")


@pytest.fixture(autouse=True)
def _silence_gateway_warning(monkeypatch):
    monkeypatch.setattr(watch, "_warn_if_gateway_not_running", lambda: None)


def _make_external_watch_rule(name="ext-watch", deliver="telegram"):
    watch.watch_create(kind="url-hash", target="https://example.com", schedule="every 1h", deliver=deliver, name=name)
    return list_watch_records()[0]


def _make_local_only_cron_job():
    from cron.jobs import create_job

    return create_job(prompt="a local reminder", schedule="every 1h", name="local-only", deliver="local", repeat=None)


class TestAirgapStatus:
    def test_not_locked_down_initially(self, capsys):
        airgap.airgap_status()
        assert "Not locked down" in capsys.readouterr().out

    def test_lists_external_automations(self, capsys):
        _make_external_watch_rule()
        airgap.airgap_status()
        out = capsys.readouterr().out
        assert "external deliver target: 1" in out

    def test_local_only_jobs_not_counted(self, capsys):
        _make_local_only_cron_job()
        airgap.airgap_status()
        out = capsys.readouterr().out
        assert "external deliver target: 0" in out


class TestAirgapLockdown:
    def test_pauses_external_watch_rule(self, capsys):
        record = _make_external_watch_rule()
        airgap.airgap_lockdown("client-x")
        out = capsys.readouterr().out
        assert "Locked down for engagement 'client-x'" in out
        assert "Paused 1" in out

        from cron.jobs import get_job

        assert get_job(record["cron_job_id"])["enabled"] is False

    def test_does_not_pause_local_only_jobs(self, capsys):
        job = _make_local_only_cron_job()
        airgap.airgap_lockdown("client-x")
        capsys.readouterr()

        from cron.jobs import get_job

        assert get_job(job["id"])["enabled"] is True

    def test_records_manifest(self):
        record = _make_external_watch_rule()
        airgap.airgap_lockdown("client-x")
        manifest = load_manifest()
        assert manifest["engagement"] == "client-x"
        assert record["cron_job_id"] in manifest["paused_cron_job_ids"]
        assert record["id"] in manifest["paused_watch_ids"]
        assert manifest["restored_at"] is None

    def test_double_lockdown_refuses(self, capsys):
        _make_external_watch_rule()
        airgap.airgap_lockdown("client-x")
        capsys.readouterr()

        airgap.airgap_lockdown("client-y")
        out = capsys.readouterr().out
        assert "Already locked down" in out


class TestAirgapRestore:
    def test_restores_exactly_what_was_paused(self, capsys):
        record = _make_external_watch_rule()
        airgap.airgap_lockdown("client-x")
        capsys.readouterr()

        airgap.airgap_restore()
        out = capsys.readouterr().out
        assert "Restored 1" in out

        from cron.jobs import get_job

        assert get_job(record["cron_job_id"])["enabled"] is True

    def test_restore_with_no_lockdown(self, capsys):
        airgap.airgap_restore()
        assert "No lockdown to restore" in capsys.readouterr().out

    def test_restore_twice_is_idempotent(self, capsys):
        _make_external_watch_rule()
        airgap.airgap_lockdown("client-x")
        capsys.readouterr()
        airgap.airgap_restore()
        capsys.readouterr()

        airgap.airgap_restore()
        out = capsys.readouterr().out
        assert "already restored" in out.lower()

    def test_marks_manifest_restored(self):
        _make_external_watch_rule()
        airgap.airgap_lockdown("client-x")
        airgap.airgap_restore()
        manifest = load_manifest()
        assert manifest["restored_at"] is not None


class TestAirgapReport:
    def test_no_lockdown(self, capsys):
        airgap.airgap_report()
        assert "nothing to report" in capsys.readouterr().out.lower()

    def test_reflects_lockdown_state(self, capsys):
        _make_external_watch_rule()
        airgap.airgap_lockdown("client-x")
        capsys.readouterr()

        airgap.airgap_report()
        out = capsys.readouterr().out
        assert "client-x" in out
        assert "still locked down" in out


class TestRemoteMcpServers:
    def test_reports_remote_transport_servers(self, monkeypatch, capsys):
        monkeypatch.setattr(
            "hermes_cli.mcp_config._get_mcp_servers",
            lambda config=None: {"remote-one": {"url": "https://example.com/mcp"}, "local-one": {"command": "some-binary"}},
        )
        airgap.airgap_status()
        out = capsys.readouterr().out
        assert "remote (http/https) transport: 1" in out
        assert "remote-one" in out
        assert "local-one" not in out
