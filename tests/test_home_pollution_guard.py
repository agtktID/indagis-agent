"""Test for the real-`~` anti-pollution guard.

The guard is a session-scoped autouse finalizer in tests/conftest.py. It
snapshots ~/.indagis and ~/.hermes existence at conftest import and
fails the suite if either directory appears (or disappears) by session
end.

These tests exercise the guard logic directly without touching the
operator's real `~`. We test:

  1. `test_no_pollution_by_default` — sanity: a session that doesn't
     touch `~` lets the guard pass without raising. Runs the guard's
     snapshot-check logic in isolation against the real `~` and asserts
     the check returns no pollution (or matches the operator's actual
     state without flagging it).

  2. `test_pollution_detection_logic` — exercises the SAME snapshot
     comparison the guard does, but on a synthetic scenario: we snapshot
     "both existed", then synthesize "both gone", then assert the diff
     is detected as pollution.

  3. `test_guard_present_in_conftest` — meta-test: verifies the guard
     fixture exists in conftest.py (so a future refactor that removes
     it gets caught).
"""
from __future__ import annotations

import inspect
import re
from pathlib import Path

import pytest

import tests.conftest as conftest_module


def test_no_pollution_by_default():
    """Snapshot state matches current state: no pollution."""
    home = Path.home()
    ind_now = (home / ".indagis").exists()
    herm_now = (home / ".hermes").exists()
    # Run the same comparison the guard does. If the operator's machine
    # has both pre-existing (as on the development host), no pollution is
    # detected (delta is empty).
    polluted = []
    if ind_now != conftest_module._PRE_SANDBOX_HOME_INDAGIS_EXISTS:
        polluted.append("~/.indagis")
    if herm_now != conftest_module._PRE_SANDBOX_HOME_HERMES_EXISTS:
        polluted.append("~/.hermes")
    assert polluted == [], (
        f"Unexpected pollution detected by guard logic: {polluted}. "
        "Either the operator's home changed during the test (real pollution), "
        "or the snapshot at conftest import has drifted."
    )


def test_pollution_detection_logic():
    """The snapshot comparison detects synthetic pollution events.

    We do NOT actually mutate `Path.home()`. Instead, we exercise the
    guard's delta-detection logic against synthetic states and verify
    it correctly classifies them. This is a logic test, not an integration
    test — it stays valid even on the operator's machine where both
    ~/.indagis and ~/.hermes exist.
    """
    # ── Scenario A: snapshot says "both existed", current says "neither" ──
    snap_a = {"indagis": True, "hermes": True}
    cur_a = {"indagis": False, "hermes": False}
    polluted_a = _classify_pollution(snap_a, cur_a)
    assert polluted_a == ["~/.indagis (deleted)", "~/.indagis (deleted)"], (
        f"Scenario A: expected both deleted, got {polluted_a}"
    )

    # ── Scenario B: snapshot says "neither", current says "both created" ──
    snap_b = {"indagis": False, "hermes": False}
    cur_b = {"indagis": True, "hermes": True}
    polluted_b = _classify_pollution(snap_b, cur_b)
    assert polluted_b == ["~/.indagis (created)", "~/.indagis (created)"], (
        f"Scenario B: expected both created, got {polluted_b}"
    )

    # ── Scenario C: no change ──
    snap_c = {"indagis": True, "hermes": False}
    cur_c = {"indagis": True, "hermes": False}
    polluted_c = _classify_pollution(snap_c, cur_c)
    assert polluted_c == [], (
        f"Scenario C: expected no pollution, got {polluted_c}"
    )

    # ── Scenario D: partial change — only one branch moved ──
    snap_d = {"indagis": True, "hermes": False}
    cur_d = {"indagis": True, "hermes": True}
    polluted_d = _classify_pollution(snap_d, cur_d)
    assert polluted_d == ["~/.indagis (created)"], (
        f"Scenario D: expected only ~/.hermes created, got {polluted_d}"
    )


def _classify_pollution(snapshot: dict, current: dict) -> list:
    """Mirror the guard's delta logic. Returns list of "<path> (<direction>)"."""
    polluted = []
    for key in ("indagis", "hermes"):
        if current[key] != snapshot[key]:
            direction = "created" if current[key] else "deleted"
            polluted.append(f"~/.{key} ({direction})")
    return polluted


def test_guard_present_in_conftest():
    """The session-scoped autouse fixture `_home_pollution_guard` exists.

    This is a meta-test guarding the guard: a future refactor of
    conftest.py that accidentally removes the fixture gets caught here.
    """
    fixture_name = "_home_pollution_guard"
    assert hasattr(conftest_module, fixture_name), (
        f"conftest.py no longer defines `{fixture_name}`. The real-home "
        "anti-pollution guard has been removed — restore it before "
        "merging changes that touch conftest.py."
    )

    # The fixture must use `yield` (not return) so the pollution check
    # runs at session TEARDOWN, not at setup. We inspect the source code
    # directly because pytest's @fixture wrapper masks the generator
    # function nature from inspect.isgeneratorfunction.
    source = inspect.getsource(conftest_module)
    # Find the function definition block by matching the name + a yield
    # within the next ~80 lines (the function is short).
    pattern = re.compile(
        rf"def {fixture_name}\(.*?(?=\n(?:def |@pytest|\Z))",
        re.DOTALL,
    )
    match = pattern.search(source)
    assert match, f"could not locate `{fixture_name}` definition in conftest.py"
    body = match.group(0)
    assert "yield" in body, (
        f"`{fixture_name}` does not use `yield`. The pollution check "
        "must run at session teardown, not at setup. Use `yield` so the "
        "code after the yield runs in the finalizer."
    )


def test_guard_marker_exists():
    """The opt-out marker `allow_home_pollution` is documented.

    Tests that legitimately need to write to `~/.indagis` opt out via this
    marker. The marker doesn't need to be registered for the guard to
    work (pytest allows unknown markers with -W default), but the test
    suite documents the contract by checking that the marker name is
    referenced somewhere in conftest (so a rename gets caught).
    """
    source = Path(conftest_module.__file__).read_text()
    assert "allow_home_pollution" in source, (
        "The opt-out marker name `allow_home_pollution` is no longer "
        "documented in conftest.py. Either add it back to the guard's "
        "error message, or update this test."
    )