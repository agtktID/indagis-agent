"""Tests for hermes_cli/bounty.py — Bounty Ledger CLI command handlers."""

from hermes_cli import bounty
from hermes_cli.bounty_state import list_submissions


class TestBountyAdd:
    def test_logs_submission(self, capsys):
        bounty.bounty_add("AcmeCorp", "SSRF in webhook", "high", "hackerone", None, 4.0, None)
        out = capsys.readouterr().out
        assert "Submission logged" in out
        assert len(list_submissions()) == 1


class TestBountyUpdate:
    def test_valid_status(self, capsys):
        bounty.bounty_add("AcmeCorp", "SSRF", "high", None, None, None, None)
        submission_id = list_submissions()[0]["id"]
        bounty.bounty_update(submission_id, "accepted")
        assert f"{submission_id} → accepted" in capsys.readouterr().out

    def test_rejects_unknown_status(self, capsys):
        bounty.bounty_add("AcmeCorp", "SSRF", "high", None, None, None, None)
        submission_id = list_submissions()[0]["id"]
        bounty.bounty_update(submission_id, "not-a-real-status")
        assert "Unknown status" in capsys.readouterr().out

    def test_missing_submission(self, capsys):
        bounty.bounty_update("bty_nope", "accepted")
        assert "No such submission" in capsys.readouterr().out


class TestBountyPay:
    def test_records_payout(self, capsys):
        bounty.bounty_add("AcmeCorp", "SSRF", "high", None, None, None, None)
        submission_id = list_submissions()[0]["id"]
        bounty.bounty_pay(submission_id, 500.0, "USD")
        out = capsys.readouterr().out
        assert "500.0 USD" in out


class TestBountyStats:
    def test_no_submissions(self, capsys):
        bounty.bounty_stats()
        out = capsys.readouterr().out
        assert "Total submissions:    0" in out
        assert "n/a" in out

    def test_with_paid_submission(self, capsys):
        bounty.bounty_add("AcmeCorp", "SSRF", "high", None, None, 5.0, None)
        submission_id = list_submissions()[0]["id"]
        bounty.bounty_pay(submission_id, 500.0, "USD")
        out = capsys.readouterr().out
        bounty.bounty_stats()
        out = capsys.readouterr().out
        assert "$/hour (USD):        100.0" in out


class TestBountyRemove:
    def test_remove_existing(self, capsys):
        bounty.bounty_add("AcmeCorp", "SSRF", "high", None, None, None, None)
        submission_id = list_submissions()[0]["id"]
        bounty.bounty_remove(submission_id)
        assert "Removed" in capsys.readouterr().out
        assert list_submissions() == []

    def test_remove_missing(self, capsys):
        bounty.bounty_remove("bty_nope")
        assert "No such submission" in capsys.readouterr().out


class TestBountyCommandDispatch:
    def test_unknown_action(self, capsys):
        bounty.bounty_command(type("Args", (), {"bounty_command": "bogus"})())
        assert "Unknown bounty subcommand" in capsys.readouterr().err
