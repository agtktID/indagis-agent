"""Tests for the `indagis mcp audit` CLI handlers in hermes_cli/mcp_config.py."""

from hermes_cli import mcp_audit, mcp_audit_state, mcp_config


class _Args:
    def __init__(self, name=None):
        self.name = name


class TestCmdMcpAudit:
    def test_unknown_server(self, monkeypatch, capsys):
        monkeypatch.setattr(mcp_config, "_get_mcp_servers", lambda: {})
        mcp_config.cmd_mcp_audit(_Args("ghost"))
        out = capsys.readouterr().out
        assert "not found" in out

    def test_clean_audit_prints_success_and_saves_record(self, monkeypatch, capsys, tmp_path):
        monkeypatch.setattr(mcp_audit_state, "get_indagis_home", lambda: tmp_path)
        monkeypatch.setattr(mcp_config, "_get_mcp_servers", lambda: {"srv": {"command": "npx"}})
        monkeypatch.setattr(
            mcp_audit,
            "run_audit",
            lambda name, cfg, connect_timeout=None: {
                "server": "srv",
                "verdict": "clean",
                "tool_count": 2,
                "tool_hash": "h1",
                "findings": [],
            },
        )
        mcp_config.cmd_mcp_audit(_Args("srv"))
        out = capsys.readouterr().out
        assert "No tool-poisoning signals found" in out
        record = mcp_audit_state.get_audit_record("srv")
        assert record["verdict"] == "clean"
        assert record["tool_hash"] == "h1"

    def test_blocked_audit_prints_findings_and_verdict(self, monkeypatch, capsys, tmp_path):
        monkeypatch.setattr(mcp_audit_state, "get_indagis_home", lambda: tmp_path)
        monkeypatch.setattr(mcp_config, "_get_mcp_servers", lambda: {"srv": {"command": "npx"}})
        monkeypatch.setattr(
            mcp_audit,
            "run_audit",
            lambda name, cfg, connect_timeout=None: {
                "server": "srv",
                "verdict": "blocked",
                "tool_count": 1,
                "tool_hash": "h2",
                "findings": [
                    {"severity": "blocked", "pattern": "covert-action", "tool": "evil", "snippet": "do not tell"}
                ],
            },
        )
        mcp_config.cmd_mcp_audit(_Args("srv"))
        out = capsys.readouterr().out
        assert "covert-action" in out
        assert "BLOCKED" in out

    def test_drift_warning_on_changed_tool_hash(self, monkeypatch, capsys, tmp_path):
        monkeypatch.setattr(mcp_audit_state, "get_indagis_home", lambda: tmp_path)
        monkeypatch.setattr(mcp_config, "_get_mcp_servers", lambda: {"srv": {"command": "npx"}})
        mcp_audit_state.save_audit_record("srv", verdict="clean", tool_hash="old-hash", tool_count=1, findings=[])
        monkeypatch.setattr(
            mcp_audit,
            "run_audit",
            lambda name, cfg, connect_timeout=None: {
                "server": "srv",
                "verdict": "clean",
                "tool_count": 1,
                "tool_hash": "new-hash",
                "findings": [],
            },
        )
        mcp_config.cmd_mcp_audit(_Args("srv"))
        out = capsys.readouterr().out
        assert "Tool list changed since the last audit" in out

    def test_connection_failure_reported(self, monkeypatch, capsys):
        monkeypatch.setattr(mcp_config, "_get_mcp_servers", lambda: {"srv": {"command": "npx"}})

        def boom(name, cfg, connect_timeout=None):
            raise RuntimeError("connection refused")

        monkeypatch.setattr(mcp_audit, "run_audit", boom)
        mcp_config.cmd_mcp_audit(_Args("srv"))
        out = capsys.readouterr().out
        assert "Audit failed" in out
        assert "connection refused" in out

    def test_no_name_falls_back_to_list(self, monkeypatch, tmp_path):
        monkeypatch.setattr(mcp_audit_state, "get_indagis_home", lambda: tmp_path)
        called = []
        monkeypatch.setattr(mcp_config, "cmd_mcp_audit_list", lambda args=None: called.append(True))
        mcp_config.cmd_mcp_audit(_Args(None))
        assert called


class TestCmdMcpAuditList:
    def test_empty_state(self, monkeypatch, capsys, tmp_path):
        monkeypatch.setattr(mcp_audit_state, "get_indagis_home", lambda: tmp_path)
        mcp_config.cmd_mcp_audit_list()
        out = capsys.readouterr().out
        assert "No servers have been audited yet" in out

    def test_lists_stored_records(self, monkeypatch, capsys, tmp_path):
        monkeypatch.setattr(mcp_audit_state, "get_indagis_home", lambda: tmp_path)
        mcp_audit_state.save_audit_record("srv-a", verdict="clean", tool_hash="h1", tool_count=3, findings=[])
        mcp_audit_state.save_audit_record("srv-b", verdict="blocked", tool_hash="h2", tool_count=1, findings=[])
        mcp_config.cmd_mcp_audit_list()
        out = capsys.readouterr().out
        assert "srv-a" in out
        assert "srv-b" in out


class TestMcpCommandDispatch:
    def test_audit_action_routes_to_handler(self, monkeypatch):
        called = []
        monkeypatch.setattr(mcp_config, "cmd_mcp_audit", lambda args: called.append(args))
        mcp_config.mcp_command(_Args_with_action("audit", "srv"))
        assert called


class _Args_with_action:
    def __init__(self, mcp_action, name=None):
        self.mcp_action = mcp_action
        self.name = name
