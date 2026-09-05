"""Tests for hermes_cli/mcp_audit_state.py — MCP audit result storage."""

from hermes_cli import mcp_audit_state


class TestAuditRecordRoundtrip:
    def test_missing_record_returns_none(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mcp_audit_state, "get_indagis_home", lambda: tmp_path)
        assert mcp_audit_state.get_audit_record("nope") is None

    def test_save_then_get(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mcp_audit_state, "get_indagis_home", lambda: tmp_path)
        mcp_audit_state.save_audit_record(
            "srv", verdict="clean", tool_hash="abc123", tool_count=3, findings=[]
        )
        record = mcp_audit_state.get_audit_record("srv")
        assert record["verdict"] == "clean"
        assert record["tool_hash"] == "abc123"
        assert record["tool_count"] == 3
        assert "audited_at" in record

    def test_save_overwrites_prior_record(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mcp_audit_state, "get_indagis_home", lambda: tmp_path)
        mcp_audit_state.save_audit_record("srv", verdict="clean", tool_hash="h1", tool_count=1, findings=[])
        mcp_audit_state.save_audit_record("srv", verdict="warn", tool_hash="h2", tool_count=2, findings=[{"x": 1}])
        record = mcp_audit_state.get_audit_record("srv")
        assert record["verdict"] == "warn"
        assert record["tool_hash"] == "h2"

    def test_list_records(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mcp_audit_state, "get_indagis_home", lambda: tmp_path)
        mcp_audit_state.save_audit_record("a", verdict="clean", tool_hash="h1", tool_count=1, findings=[])
        mcp_audit_state.save_audit_record("b", verdict="blocked", tool_hash="h2", tool_count=2, findings=[])
        names = {r["name"] for r in mcp_audit_state.list_audit_records()}
        assert names == {"a", "b"}

    def test_remove_record(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mcp_audit_state, "get_indagis_home", lambda: tmp_path)
        mcp_audit_state.save_audit_record("a", verdict="clean", tool_hash="h1", tool_count=1, findings=[])
        assert mcp_audit_state.remove_audit_record("a") is True
        assert mcp_audit_state.get_audit_record("a") is None
        assert mcp_audit_state.remove_audit_record("a") is False

    def test_corrupt_file_treated_as_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(mcp_audit_state, "get_indagis_home", lambda: tmp_path)
        mcp_dir = tmp_path / "mcp"
        mcp_dir.mkdir(parents=True, exist_ok=True)
        (mcp_dir / "audit.json").write_text("{not json", encoding="utf-8")
        assert mcp_audit_state.list_audit_records() == []
