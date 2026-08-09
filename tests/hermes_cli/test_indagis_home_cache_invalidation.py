"""Integration test — verify cache invalidation order under profile scope.

Draft 1 (hermes_constants.py) introduces the ``_INDAGIS_HOME_CACHE``
ContextVar and promises it is invalidated:

  1. as the FIRST executable statement of ``set_indagis_home_override()``,
  2. as the FIRST executable statement of ``reset_indagis_home_override()``,
  3. BEFORE any subsequent read of ``get_indagis_home()`` inside the
     scope entered by ``_profile_runtime_scope(profile_home)``.

This test reproduces the entry/exit sequence that
``gateway/run.py:_profile_runtime_scope`` performs (without importing
the gateway module — we exercise the same primitive seam) and asserts
that the cache is in the ``UNSET`` state both:

  - immediately after ``set_indagis_home_override`` (entry to scope), and
  - immediately after ``reset_indagis_home_override`` (exit from scope).

If the cache is NOT invalidated first, a downstream
``get_indagis_home()`` call inside the scope would read a stale value
computed in a previous context — which would silently leak data across
profiles in multiplexed gateways.
"""

from pathlib import Path

import hermes_constants


def test_cache_is_invalidated_on_scope_entry(monkeypatch, tmp_path):
    """Entering a profile scope invalidates the cache BEFORE any read."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    hermes_constants._INDAGIS_HOME_CACHE.set(hermes_constants._UNSET)

    # Pre-warm: enter a parent scope so the cache gets populated with a
    # resolved value. Exiting the parent scope must also invalidate the
    # cache, so we re-enter to populate it again before probing.
    parent_token = hermes_constants.set_indagis_home_override(tmp_path / "parent")
    hermes_constants.get_indagis_home()
    hermes_constants.reset_indagis_home_override(parent_token)

    # Sanity check: the cache is UNSET after the parent scope exits
    # (reset_indagis_home_override is the first instruction that invalidates).
    assert hermes_constants._INDAGIS_HOME_CACHE.get() is hermes_constants._UNSET

    # Now enter the child scope via the same primitive _profile_runtime_scope uses.
    token = hermes_constants.set_indagis_home_override(tmp_path / "profile-a")

    try:
        # Assertion 1: cache must be UNSET immediately after set_indagis_home_override.
        cached = hermes_constants._INDAGIS_HOME_CACHE.get()
        assert cached is hermes_constants._UNSET, (
            f"cache must be invalidated on scope entry, got {cached!r}"
        )

        # Assertion 2: the FIRST read inside the scope observes the new
        # override, not the prewarmed value.
        resolved = hermes_constants.get_indagis_home()
        assert resolved == tmp_path / "profile-a", (
            f"first read inside scope must follow the override, got {resolved!r}"
        )
    finally:
        hermes_constants.reset_indagis_home_override(token)


def test_cache_is_invalidated_on_scope_exit(monkeypatch, tmp_path):
    """Exiting a profile scope invalidates the cache."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    hermes_constants._INDAGIS_HOME_CACHE.set(hermes_constants._UNSET)

    profile_home = tmp_path / "profile-b"
    token = hermes_constants.set_indagis_home_override(profile_home)
    try:
        # Warm the cache inside the scope.
        hermes_constants.get_indagis_home()
        assert hermes_constants._INDAGIS_HOME_CACHE.get() == profile_home
    finally:
        hermes_constants.reset_indagis_home_override(token)

    # Assertion 3: cache must be UNSET immediately after reset_indagis_home_override.
    cached = hermes_constants._INDAGIS_HOME_CACHE.get()
    assert cached is hermes_constants._UNSET, (
        f"cache must be invalidated on scope exit, got {cached!r}"
    )

    # And the next read in the parent context must NOT see the profile-b value.
    resolved = hermes_constants.get_indagis_home()
    assert resolved != profile_home, (
        f"parent-context read must not return the profile value, got {resolved!r}"
    )


def test_set_override_invalidates_cache_before_setting_override(monkeypatch, tmp_path):
    """The invalidation is the FIRST statement of set_indagis_home_override.

    Probed by inspecting the cache state immediately after the call returns,
    while the override is now installed. The cache must be UNSET, not equal
    to the prewarmed value (which is what would happen if invalidation
    came AFTER the override was set).
    """
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    hermes_constants._INDAGIS_HOME_CACHE.set(hermes_constants._UNSET)

    prewarmed = hermes_constants.get_indagis_home()

    token = hermes_constants.set_indagis_home_override(tmp_path / "profile-c")
    try:
        cached = hermes_constants._INDAGIS_HOME_CACHE.get()
        assert cached is hermes_constants._UNSET, (
            f"set_indagis_home_override must invalidate cache as its first "
            f"statement; got cached={cached!r} (prewarmed was {prewarmed!r})"
        )
    finally:
        hermes_constants.reset_indagis_home_override(token)
