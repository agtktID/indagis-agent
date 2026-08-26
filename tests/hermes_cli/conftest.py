"""Fixtures shared across hermes_cli kanban tests."""

from __future__ import annotations

import pytest


@pytest.fixture
def all_assignees_spawnable(monkeypatch):
    """Pretend every assignee maps to a real Hermes profile.

    Most dispatcher tests use synthetic assignees ("alice", "bob") that
    don't correspond to actual profile directories on disk. Without this
    patch, the dispatcher's profile-exists guard (PR #20105) routes
    those tasks into ``skipped_nonspawnable`` instead of spawning, which
    would break tests that assert spawn behavior.
    """
    from hermes_cli import profiles
    monkeypatch.setattr(profiles, "profile_exists", lambda name: True)


@pytest.fixture(autouse=True)
def _suppress_concurrent_hermes_gate(request, monkeypatch):
    """Default ``_detect_concurrent_hermes_instances`` to ``[]`` for every test.

    The Windows update path now refuses to proceed when another
    ``hermes.exe`` is detected (issue #26670). On a developer's Windows
    machine running the test suite via ``hermes`` itself, this would
    flag the running agent as a concurrent instance and abort every
    ``cmd_update`` test. Tests that want to exercise the gate explicitly
    re-patch ``_detect_concurrent_hermes_instances`` with their own
    return value — autouse here gives a clean default without touching
    the rest of the suite.

    Tests that need to call the REAL function (e.g. unit tests for the
    helper itself) opt out with ``@pytest.mark.real_concurrent_gate``.
    """
    if request.node.get_closest_marker("real_concurrent_gate"):
        return
    try:
        from hermes_cli import main as _cli_main
    except Exception:
        return
    # raising=False: under pytest's per-test spawn isolation, a concurrent
    # xdist worker importing a module that transitively touches hermes_cli.main
    # can briefly expose a partially-initialized module object here — one where
    # _detect_concurrent_hermes_instances isn't defined yet. A bare setattr
    # would raise AttributeError and error the (unrelated) test. The attribute
    # always exists once main.py finishes importing, so a no-op when it's
    # transiently absent is the correct, race-free default.
    monkeypatch.setattr(
        _cli_main,
        "_detect_concurrent_hermes_instances",
        lambda *_a, **_k: [],
        raising=False,
    )


@pytest.fixture(autouse=True)
def _restore_dashboard_app_state():
    """Restore ``web_server.app.state.auth_required`` around every test.

    ``web_server.app`` is a module-level FastAPI singleton shared by every test
    in this directory, and the dashboard-auth files flip
    ``app.state.auth_required`` to exercise gated mode without putting it back.
    A leaked ``True`` makes ``auth_middleware`` skip the ``_SESSION_TOKEN``
    branch, so every later dashboard request 401s purely as a function of file
    ordering.
    """
    try:
        from hermes_cli import web_server
    except Exception:  # pragma: no cover - fastapi absent
        yield
        return

    sentinel = object()
    previous = getattr(web_server.app.state, "auth_required", sentinel)
    try:
        yield
    finally:
        if previous is sentinel:
            # Starlette's State is dict-backed: deleting an unset key raises
            # KeyError, not AttributeError.
            try:
                delattr(web_server.app.state, "auth_required")
            except (AttributeError, KeyError):
                pass
        else:
            web_server.app.state.auth_required = previous
