"""Regression tests for the Python Indagis home resolution ladder.

Behavior contract for the 5-priority resolution ladder (see
reports/plan-get-indagis-home-resolution.md):

  P1: $INDAGIS_HOME  → path
  P2: ~/.indagis     → path (if exists) [priority default, no warning]
  P3: $HERMES_HOME   → path (legacy alias, WARNING)
  P4: ~/.hermes      → path (legacy alias, WARNING)
  P5: ~/.indagis     → create on first use [fallback]

These tests assert the TARGET behavior. Before Draft 1 lands, P3/P4 must
FAIL (because the current code is Indagis-only and ignores legacy aliases).
After Draft 1 lands, all 6 must pass.
"""

from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from pathlib import Path

import pytest

import hermes_constants


@pytest.fixture(autouse=True)
def reset_home_cache(monkeypatch):
    """Keep the ContextVar cache and process environment isolated per test."""
    monkeypatch.delenv("INDAGIS_HOME", raising=False)
    monkeypatch.delenv("HERMES_HOME", raising=False)
    hermes_constants._INDAGIS_HOME_CACHE.set(hermes_constants._UNSET)
    yield
    hermes_constants._INDAGIS_HOME_CACHE.set(hermes_constants._UNSET)


def _reset_profile_warning(monkeypatch):
    monkeypatch.setattr(hermes_constants, "_profile_fallback_warned", False)


def _reset_legacy_warning(monkeypatch):
    """Reset the legacy-alias deprecation guard if Draft 1 has added it.

    Draft 1 will introduce ``_legacy_alias_warned``; until then this is a
    no-op. Using ``raising=False`` keeps the helper safe across the TDD
    transition (before/after the helper exists).
    """
    if hasattr(hermes_constants, "_legacy_alias_warned"):
        monkeypatch.setattr(hermes_constants, "_legacy_alias_warned", False)


# ─────────────────────────────────────────────────────────────────
# P1: explicit INDAGIS_HOME env var wins, no warning
# ─────────────────────────────────────────────────────────────────
def test_priority_1_explicit_indagis_home(monkeypatch, tmp_path, capsys):
    custom = tmp_path / "custom"
    monkeypatch.setenv("INDAGIS_HOME", str(custom))

    assert hermes_constants.get_indagis_home() == custom
    assert "Indagis Agent" not in capsys.readouterr().err


# ─────────────────────────────────────────────────────────────────
# P2: ~/.indagis exists → use it (default), no warning
# ─────────────────────────────────────────────────────────────────
def test_priority_2_existing_indagis_default(monkeypatch, tmp_path, capsys):
    _reset_profile_warning(monkeypatch)
    indagis = tmp_path / ".indagis"
    indagis.mkdir()
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    # Pin to the POSIX branch: on native Windows the platform default
    # resolves via LOCALAPPDATA instead of Path.home(), so without this
    # the assertion below only passes by accident of running on a POSIX
    # CI runner.
    monkeypatch.setattr(hermes_constants.sys, "platform", "linux")

    assert hermes_constants.get_indagis_home() == indagis
    assert "Indagis Agent" not in capsys.readouterr().err


# ─────────────────────────────────────────────────────────────────
# P3: HERMES_HOME env var → legacy alias fallback + WARNING
# Target: returns HERMES_HOME path AND emits a deprecation warning.
# Before Draft 1: code is Indagis-only → returns ~/.indagis (no warning)
# → test FAILS.
# ─────────────────────────────────────────────────────────────────
def test_priority_3_explicit_legacy_alias(monkeypatch, tmp_path, capsys):
    _reset_profile_warning(monkeypatch)
    _reset_legacy_warning(monkeypatch)
    legacy = tmp_path / "legacy"
    monkeypatch.setenv("HERMES_HOME", str(legacy))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    # CIBLE : doit retourner le chemin legacy (repli)
    assert hermes_constants.get_indagis_home() == legacy

    # CIBLE : doit émettre un warning de dépréciation sur stderr
    err = capsys.readouterr().err
    assert "Indagis Agent" in err, (
        f"Expected legacy-alias deprecation warning on stderr, got: {err!r}"
    )
    assert "HERMES_HOME" in err, (
        f"Expected warning to mention HERMES_HOME, got: {err!r}"
    )


# ─────────────────────────────────────────────────────────────────
# P4: ~/.hermes exists → legacy alias fallback + WARNING
# Target: returns ~/.hermes AND emits a deprecation warning.
# Before Draft 1: code is Indagis-only → returns ~/.indagis (no warning)
# → test FAILS.
# ─────────────────────────────────────────────────────────────────
def test_priority_4_existing_platform_legacy_default(monkeypatch, tmp_path, capsys):
    _reset_profile_warning(monkeypatch)
    _reset_legacy_warning(monkeypatch)
    legacy = tmp_path / ".hermes"
    legacy.mkdir()
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    # Pin to the POSIX branch: on native Windows the legacy-alias default
    # is %LOCALAPPDATA%\hermes, not ~/.hermes, so without this the
    # assertion below only passes by accident of running on a POSIX CI
    # runner.
    monkeypatch.setattr(hermes_constants.sys, "platform", "linux")

    # CIBLE : doit retourner ~/.hermes (repli), pas ~/.indagis
    assert hermes_constants.get_indagis_home() == legacy

    # CIBLE : doit émettre un warning de dépréciation sur stderr
    err = capsys.readouterr().err
    assert "Indagis Agent" in err, (
        f"Expected legacy-alias deprecation warning on stderr, got: {err!r}"
    )
    assert ".indagis" in err, (
        f"Expected warning to mention ~/.hermes, got: {err!r}"
    )


# ─────────────────────────────────────────────────────────────────
# P5: nothing set → return ~/.indagis (does not create it)
# ─────────────────────────────────────────────────────────────────
def test_priority_5_missing_defaults_returns_new_platform_default(monkeypatch, tmp_path):
    _reset_profile_warning(monkeypatch)
    _reset_legacy_warning(monkeypatch)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    # Pin to the POSIX branch: on native Windows this resolves via
    # LOCALAPPDATA instead of Path.home(), so without this the assertion
    # below only passes by accident of running on a POSIX CI runner.
    monkeypatch.setattr(hermes_constants.sys, "platform", "linux")

    result = hermes_constants.get_indagis_home()

    assert result == tmp_path / ".indagis"
    assert not result.exists()


# ─────────────────────────────────────────────────────────────────
# Concurrency: contexts do not share the cache
# ─────────────────────────────────────────────────────────────────
def test_concurrent_contexts_do_not_share_home_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    barrier = __import__("threading").Barrier(2)
    homes = (tmp_path / "profile-a", tmp_path / "profile-b")

    def resolve(home):
        def scoped():
            token = hermes_constants.set_indagis_home_override(home)
            try:
                barrier.wait(timeout=5)
                first = hermes_constants.get_indagis_home()
                barrier.wait(timeout=5)
                second = hermes_constants.get_indagis_home()
                return first, second
            finally:
                hermes_constants.reset_indagis_home_override(token)

        return copy_context().run(scoped)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(resolve, homes))

    assert results == [(homes[0], homes[0]), (homes[1], homes[1])]
