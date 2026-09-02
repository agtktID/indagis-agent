"""Tests for env_with_legacy_alias(), the INDAGIS_*/HERMES_* fallback helper."""

import logging

from utils import env_with_legacy_alias


def test_prefers_new_name_when_both_set(monkeypatch):
    monkeypatch.setenv("INDAGIS_TEST_VAR", "new-value")
    monkeypatch.setenv("HERMES_TEST_VAR", "old-value")
    assert env_with_legacy_alias("INDAGIS_TEST_VAR", "HERMES_TEST_VAR") == "new-value"


def test_falls_back_to_legacy_name_when_new_unset(monkeypatch):
    monkeypatch.delenv("INDAGIS_TEST_VAR", raising=False)
    monkeypatch.setenv("HERMES_TEST_VAR", "old-value")
    assert env_with_legacy_alias("INDAGIS_TEST_VAR", "HERMES_TEST_VAR") == "old-value"


def test_falls_back_to_legacy_name_logs_deprecation_warning(monkeypatch, caplog):
    monkeypatch.delenv("INDAGIS_TEST_VAR", raising=False)
    monkeypatch.setenv("HERMES_TEST_VAR", "old-value")
    with caplog.at_level(logging.WARNING):
        env_with_legacy_alias("INDAGIS_TEST_VAR", "HERMES_TEST_VAR")
    assert any(
        "HERMES_TEST_VAR" in record.message and "deprecated" in record.message
        for record in caplog.records
    )


def test_new_name_set_does_not_log_deprecation_warning(monkeypatch, caplog):
    monkeypatch.setenv("INDAGIS_TEST_VAR", "new-value")
    monkeypatch.delenv("HERMES_TEST_VAR", raising=False)
    with caplog.at_level(logging.WARNING):
        env_with_legacy_alias("INDAGIS_TEST_VAR", "HERMES_TEST_VAR")
    assert not any("deprecated" in record.message for record in caplog.records)


def test_returns_default_when_neither_set(monkeypatch):
    monkeypatch.delenv("INDAGIS_TEST_VAR", raising=False)
    monkeypatch.delenv("HERMES_TEST_VAR", raising=False)
    assert env_with_legacy_alias("INDAGIS_TEST_VAR", "HERMES_TEST_VAR", default="fallback") == "fallback"


def test_empty_string_new_value_is_respected_not_treated_as_unset(monkeypatch):
    # Explicitly set to "" should win over the legacy var, same as os.getenv semantics.
    monkeypatch.setenv("INDAGIS_TEST_VAR", "")
    monkeypatch.setenv("HERMES_TEST_VAR", "old-value")
    assert env_with_legacy_alias("INDAGIS_TEST_VAR", "HERMES_TEST_VAR") == ""
