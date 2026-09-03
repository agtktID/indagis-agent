"""Tests for hermes_cli/bounty_state.py — the Bounty Ledger storage layer."""

from hermes_cli.bounty_state import (
    add_submission,
    generate_submission_id,
    get_submission,
    list_submissions,
    record_payout,
    remove_submission,
    stats,
    update_status,
)


def _add(program="AcmeCorp", title="SSRF", severity="high", hours=None):
    return add_submission(program=program, title=title, severity=severity, platform="hackerone", url=None, hours_spent=hours, notes=None)


class TestGenerateSubmissionId:
    def test_format(self):
        sid = generate_submission_id()
        assert sid.startswith("bty_")

    def test_unique(self):
        assert generate_submission_id() != generate_submission_id()


class TestAddSubmission:
    def test_starts_as_submitted(self):
        record = _add()
        assert record["status"] == "submitted"
        assert record["payout_amount"] is None
        assert len(record["history"]) == 1
        assert record["history"][0]["status"] == "submitted"

    def test_get_after_add(self):
        record = _add()
        assert get_submission(record["id"])["title"] == "SSRF"

    def test_get_missing(self):
        assert get_submission("bty_nope") is None


class TestListSubmissions:
    def test_filters_by_status(self):
        a = _add(title="A")
        _add(title="B")
        update_status(a["id"], "accepted")
        assert len(list_submissions(status="accepted")) == 1
        assert len(list_submissions()) == 2

    def test_filters_by_program(self):
        _add(program="AcmeCorp")
        _add(program="OtherCorp")
        assert len(list_submissions(program="AcmeCorp")) == 1

    def test_sorted_newest_first(self):
        _add(title="first")
        second = _add(title="second")
        assert list_submissions()[0]["id"] == second["id"]


class TestUpdateStatus:
    def test_appends_to_history(self):
        record = _add()
        updated = update_status(record["id"], "triaging")
        assert updated["status"] == "triaging"
        assert len(updated["history"]) == 2
        assert updated["history"][-1]["status"] == "triaging"

    def test_missing_submission(self):
        assert update_status("bty_nope", "accepted") is None


class TestRecordPayout:
    def test_sets_paid_fields_and_status(self):
        record = _add()
        updated = record_payout(record["id"], 1500.0, "USD")
        assert updated["status"] == "paid"
        assert updated["payout_amount"] == 1500.0
        assert updated["payout_currency"] == "USD"
        assert updated["paid_at"] is not None

    def test_missing_submission(self):
        assert record_payout("bty_nope", 100, "USD") is None


class TestRemoveSubmission:
    def test_remove_existing(self):
        record = _add()
        assert remove_submission(record["id"]) is True
        assert get_submission(record["id"]) is None

    def test_remove_missing(self):
        assert remove_submission("bty_nope") is False


class TestStats:
    def test_empty(self):
        s = stats()
        assert s["total_submissions"] == 0
        assert s["win_rate_pct"] is None

    def test_win_rate_and_payout(self):
        accepted = _add(title="accepted one", hours=4)
        _add(title="dup one")
        update_status(accepted["id"], "accepted")
        record_payout(accepted["id"], 1000.0, "USD")

        rejected = _add(title="dup")
        update_status(rejected["id"], "duplicate")

        s = stats()
        assert s["total_submissions"] == 3
        assert s["paid_count"] == 1
        assert s["total_payout_by_currency"] == {"USD": 1000.0}
        # 2 decided (accepted+duplicate), 1 accepted -> 50%
        assert s["win_rate_pct"] == 50.0
        assert s["total_hours_on_paid"] == 4

    def test_by_severity_uses_unspecified_default(self):
        add_submission(program="p", title="t", severity=None, platform=None, url=None, hours_spent=None, notes=None)
        s = stats()
        assert s["by_severity"] == {"unspecified": 1}
