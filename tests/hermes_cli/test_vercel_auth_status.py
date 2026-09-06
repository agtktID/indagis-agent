"""``describe_vercel_auth`` reports auth state — and must never report the token.

WHY THIS EXISTS. The module had no test naming it, and its docstring carries a
security invariant nothing enforced: "Return Vercel auth status without exposing
secret values." It reads VERCEL_TOKEN and VERCEL_OIDC_TOKEN, both secrets, and
its output is printed to the terminal and lands in logs and support pastes. An
edit that added the value to a detail line — the obvious thing to reach for while
debugging "why does it say not configured" — would leak a credential into every
one of those places, and nothing would have objected.

So the first test below is the one that matters: whatever the branch, the secret's
VALUE never appears in the label or any detail line. The branch tests exist to
make sure that guarantee is being checked on real output rather than on an empty
object.
"""

from __future__ import annotations

import pytest

from hermes_cli.vercel_auth import describe_vercel_auth

_ALL_VARS = (
    "VERCEL_OIDC_TOKEN",
    "VERCEL_TOKEN",
    "VERCEL_PROJECT_ID",
    "VERCEL_TEAM_ID",
)

_SECRET = "s3cr3t-token-value-do-not-print"


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Start from no Vercel configuration; the ambient environment must not
    decide which branch a test exercises."""
    for name in _ALL_VARS:
        monkeypatch.delenv(name, raising=False)


def _all_text(status) -> str:
    return status.label + "\n" + "\n".join(status.detail_lines)


# ── the invariant ────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "env",
    [
        {"VERCEL_OIDC_TOKEN": _SECRET},
        {"VERCEL_TOKEN": _SECRET, "VERCEL_PROJECT_ID": "p", "VERCEL_TEAM_ID": "t"},
        {"VERCEL_TOKEN": _SECRET},
        {
            "VERCEL_TOKEN": _SECRET,
            "VERCEL_OIDC_TOKEN": _SECRET,
            "VERCEL_PROJECT_ID": "p",
        },
    ],
    ids=["oidc", "complete", "partial", "both"],
)
def test_the_token_value_never_reaches_the_output(monkeypatch, env: dict) -> None:
    """Every branch, one rule: names may be printed, values never."""
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    text = _all_text(describe_vercel_auth())
    assert _SECRET not in text, (
        f"the token value leaked into the status output:\n{text}"
    )


def test_variable_names_are_printed_because_they_are_not_the_secret(
    monkeypatch,
) -> None:
    """The counterpart to the rule above: naming which variable is missing is the
    whole point of the message, and a name is not a credential."""
    monkeypatch.setenv("VERCEL_TOKEN", _SECRET)
    text = _all_text(describe_vercel_auth())
    assert "VERCEL_PROJECT_ID" in text and "VERCEL_TEAM_ID" in text


# ── the four branches ────────────────────────────────────────────────────────


def test_nothing_configured(monkeypatch) -> None:
    status = describe_vercel_auth()
    assert status.ok is False
    assert status.label == "not configured"


def test_complete_access_token_tuple_is_ok(monkeypatch) -> None:
    for name in ("VERCEL_TOKEN", "VERCEL_PROJECT_ID", "VERCEL_TEAM_ID"):
        monkeypatch.setenv(name, "x")
    status = describe_vercel_auth()
    assert status.ok is True
    assert "access token" in status.label


@pytest.mark.parametrize(
    "present", ["VERCEL_TOKEN", "VERCEL_PROJECT_ID", "VERCEL_TEAM_ID"]
)
def test_a_partial_tuple_is_not_ok_and_names_what_is_missing(
    monkeypatch, present: str
) -> None:
    """Two of three is not authentication. Reporting ok here would send the user
    off to debug a deployment failure instead of the missing variable."""
    monkeypatch.setenv(present, "x")
    status = describe_vercel_auth()
    assert status.ok is False
    assert "partial" in status.label
    for name in ("VERCEL_TOKEN", "VERCEL_PROJECT_ID", "VERCEL_TEAM_ID"):
        if name != present:
            assert name in status.label


def test_oidc_alone_is_ok_and_carries_its_caveat(monkeypatch) -> None:
    monkeypatch.setenv("VERCEL_OIDC_TOKEN", "x")
    status = describe_vercel_auth()
    assert status.ok is True
    assert "OIDC" in status.label
    assert any("development-only" in line for line in status.detail_lines), (
        "an OIDC token expires quickly; reporting it as plain ok without the "
        "caveat sets up a long-running process to fail later for no visible reason"
    )


def test_oidc_wins_over_a_complete_token_tuple_but_says_so(monkeypatch) -> None:
    """Both configured: OIDC is reported as the active mode, and the tuple is
    still surfaced so the reader can tell the two apart."""
    monkeypatch.setenv("VERCEL_OIDC_TOKEN", "x")
    for name in ("VERCEL_TOKEN", "VERCEL_PROJECT_ID", "VERCEL_TEAM_ID"):
        monkeypatch.setenv(name, "y")
    status = describe_vercel_auth()
    assert status.ok is True
    assert "OIDC" in status.label
    assert any("also present" in line for line in status.detail_lines)


# ── the empty-string case ────────────────────────────────────────────────────


def test_a_blank_variable_counts_as_unset(monkeypatch) -> None:
    """``VERCEL_TOKEN=`` is how a variable looks when an env file defines it but
    leaves it empty. Treating that as configured would report ok and then fail at
    the API call with an authentication error instead of here, where the message
    can say which variable to fill in."""
    for name in ("VERCEL_TOKEN", "VERCEL_PROJECT_ID", "VERCEL_TEAM_ID"):
        monkeypatch.setenv(name, "")
    status = describe_vercel_auth()
    assert status.ok is False
    assert status.label == "not configured"
