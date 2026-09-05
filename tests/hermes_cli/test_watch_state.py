"""Tests for hermes_cli/watch_state.py — Signal Watch registry + state storage."""

from hermes_cli.watch_state import (
    create_watch_record,
    generate_watch_id,
    get_watch_record,
    get_watch_state,
    list_watch_records,
    remove_watch_record,
    save_watch_state,
)


class TestGenerateWatchId:
    def test_format(self):
        watch_id = generate_watch_id()
        assert watch_id.startswith("wch_")
        assert len(watch_id) == len("wch_") + 12

    def test_unique(self):
        assert generate_watch_id() != generate_watch_id()


class TestCreateWatchRecord:
    def test_uses_caller_supplied_id(self):
        """Regression guard: the registry key must match the caller-supplied
        watch_id, not one minted internally — a mismatch here means the
        generated cron script's embedded ID points at a registry entry
        that doesn't exist (the exact bug this module was fixed for)."""
        watch_id = generate_watch_id()
        record = create_watch_record(
            watch_id=watch_id,
            kind="url-hash",
            target="https://example.com",
            name="test rule",
            cron_job_id="job123",
            deliver="local",
            schedule="every 1h",
        )
        assert record["id"] == watch_id
        fetched = get_watch_record(watch_id)
        assert fetched is not None
        assert fetched["id"] == watch_id

    def test_default_name(self):
        watch_id = generate_watch_id()
        record = create_watch_record(
            watch_id=watch_id, kind="url-hash", target="https://x.test",
            name=None, cron_job_id="j1", deliver="local", schedule="every 1h",
        )
        assert record["name"] == "url-hash:https://x.test"

    def test_extra_defaults_to_empty_dict(self):
        watch_id = generate_watch_id()
        record = create_watch_record(
            watch_id=watch_id, kind="cve-keyword", target="openssl",
            name="n", cron_job_id="j1", deliver="local", schedule="every 1h",
        )
        assert record["extra"] == {}


class TestListAndGetWatchRecords:
    def test_list_empty(self):
        assert list_watch_records() == []

    def test_list_returns_all(self):
        for i in range(3):
            watch_id = generate_watch_id()
            create_watch_record(
                watch_id=watch_id, kind="url-hash", target=f"https://x{i}.test",
                name=None, cron_job_id=f"j{i}", deliver="local", schedule="every 1h",
            )
        assert len(list_watch_records()) == 3

    def test_get_missing_returns_none(self):
        assert get_watch_record("wch_doesnotexist") is None


class TestRemoveWatchRecord:
    def test_remove_existing(self):
        watch_id = generate_watch_id()
        create_watch_record(
            watch_id=watch_id, kind="url-hash", target="https://x.test",
            name=None, cron_job_id="j1", deliver="local", schedule="every 1h",
        )
        save_watch_state(watch_id, {"hash": "abc"})

        assert remove_watch_record(watch_id) is True
        assert get_watch_record(watch_id) is None
        # State is cleaned up alongside the registry entry.
        assert get_watch_state(watch_id) == {}

    def test_remove_missing_returns_false(self):
        assert remove_watch_record("wch_nope") is False


class TestWatchState:
    def test_get_state_defaults_empty(self):
        assert get_watch_state("wch_never_saved") == {}

    def test_save_and_get_roundtrip(self):
        save_watch_state("wch_abc", {"hash": "deadbeef", "last_status": "ok"})
        state = get_watch_state("wch_abc")
        assert state["hash"] == "deadbeef"
        assert state["last_status"] == "ok"
        assert "updated_at" in state

    def test_save_overwrites(self):
        save_watch_state("wch_abc", {"hash": "first"})
        save_watch_state("wch_abc", {"hash": "second"})
        assert get_watch_state("wch_abc")["hash"] == "second"

    def test_corrupted_registry_file_degrades_to_empty(self, monkeypatch):
        from hermes_cli import watch_state

        watch_state._registry_file().parent.mkdir(parents=True, exist_ok=True)
        watch_state._registry_file().write_text("not json{{{", encoding="utf-8")
        assert list_watch_records() == []
