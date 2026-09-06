"""Coverage for the decision points in the billing mixin.

WHY THESE AND NOT THE SCREENS. ``cli_billing_mixin`` is 1566 lines, 32 methods,
and 28 of them had no test naming them. Most are interactive screens whose value
is what they print; pinning that in a test buys formatting churn, not safety.
Three methods are different — they *decide* something, and everything above them
trusts the answer:

  * ``_billing_require_admin`` gates every charge and auto-reload entry point.
  * ``_open_url_in_browser`` decides whether a real browser is launched, and
    carries a deliberate fail-open the docstring documents but nothing pinned.
  * ``_usage_bar_lines`` is the single source of truth for the dollar bars shown
    across /usage, /subscription and /topup.

The bars use the real ``UsageBar`` dataclass rather than a stand-in, so these
tests are bound to the actual contract and break if that contract moves.
"""

from __future__ import annotations

import types

import pytest

from agent.billing_usage import UsageBar
from hermes_cli.cli_billing_mixin import CLIBillingMixin


class _Mixin(CLIBillingMixin):
    """The mixin alone — HermesCLI's other bases are irrelevant to these three."""


@pytest.fixture
def mixin() -> _Mixin:
    return _Mixin()


def _state(**kw) -> types.SimpleNamespace:
    base = {"can_change_plan": True, "cli_billing_enabled": True, "portal_url": None}
    base.update(kw)
    return types.SimpleNamespace(**base)


# ── the authorization gate ───────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("can_change_plan", "cli_billing_enabled", "allowed"),
    [
        (True, True, True),
        (False, True, False),  # not an org admin/owner
        (True, False, False),  # remote spending switched off for the org
        (False, False, False),
    ],
)
def test_require_admin_needs_both_conditions(
    mixin: _Mixin,
    capsys,
    can_change_plan: bool,
    cli_billing_enabled: bool,
    allowed: bool,
) -> None:
    """Both flags must hold. Either one alone opening the gate would let a
    non-admin spend, or spend on an org that turned remote spending off."""
    got = mixin._billing_require_admin(
        _state(can_change_plan=can_change_plan, cli_billing_enabled=cli_billing_enabled)
    )
    assert got is allowed
    capsys.readouterr()


def test_require_admin_does_not_fail_open_on_a_malformed_state(mixin: _Mixin) -> None:
    """A state missing the flags must raise, not sail through. Silently treating
    an absent attribute as permission is how an authorization gate stops being
    one."""
    with pytest.raises(AttributeError):
        mixin._billing_require_admin(types.SimpleNamespace())


# ── the browser opener ───────────────────────────────────────────────────────


def test_open_url_refuses_an_empty_url(mixin: _Mixin) -> None:
    assert mixin._open_url_in_browser("") is False


def test_open_url_refuses_a_remote_session_without_touching_webbrowser(
    mixin: _Mixin, monkeypatch
) -> None:
    """Over SSH, webbrowser.open() can launch w3m/lynx, which seizes the TTY and
    returns True as though it had worked. The guard must short-circuit BEFORE the
    open call, not judge its result."""
    import hermes_cli.auth as auth
    import webbrowser

    monkeypatch.setattr(auth, "_is_remote_session", lambda: True)
    called: list = []
    monkeypatch.setattr(webbrowser, "open", lambda url: called.append(url) or True)

    assert mixin._open_url_in_browser("https://portal.example/x") is False
    assert called == [], "webbrowser.open ran despite the remote-session guard"


def test_open_url_refuses_when_no_graphical_browser_is_available(
    mixin: _Mixin, monkeypatch
) -> None:
    import hermes_cli.auth as auth
    import webbrowser

    monkeypatch.setattr(auth, "_is_remote_session", lambda: False)
    monkeypatch.setattr(auth, "_can_open_graphical_browser", lambda: False)
    called: list = []
    monkeypatch.setattr(webbrowser, "open", lambda url: called.append(url) or True)

    assert mixin._open_url_in_browser("https://portal.example/x") is False
    assert called == []


def test_open_url_opens_when_both_guards_pass(mixin: _Mixin, monkeypatch) -> None:
    import hermes_cli.auth as auth
    import webbrowser

    monkeypatch.setattr(auth, "_is_remote_session", lambda: False)
    monkeypatch.setattr(auth, "_can_open_graphical_browser", lambda: True)
    monkeypatch.setattr(webbrowser, "open", lambda url: True)

    assert mixin._open_url_in_browser("https://portal.example/x") is True


def test_open_url_returns_false_when_the_browser_itself_fails(
    mixin: _Mixin, monkeypatch
) -> None:
    import hermes_cli.auth as auth
    import webbrowser

    monkeypatch.setattr(auth, "_is_remote_session", lambda: False)
    monkeypatch.setattr(auth, "_can_open_graphical_browser", lambda: True)

    def _boom(url):
        raise OSError("no display")

    monkeypatch.setattr(webbrowser, "open", _boom)
    assert mixin._open_url_in_browser("https://portal.example/x") is False


# ── the dollar bars ──────────────────────────────────────────────────────────


def test_no_usage_draws_nothing(mixin: _Mixin) -> None:
    assert mixin._usage_bar_lines(None, "Pro") == []


def test_a_zero_total_plan_bar_is_not_drawn(mixin: _Mixin) -> None:
    """A bar of nothing out of nothing is noise, not information."""
    usage = types.SimpleNamespace(
        plan_bar=UsageBar(kind="plan", remaining_usd=0.0, total_usd=0.0), topup_bar=None
    )
    assert mixin._usage_bar_lines(usage, "Pro") == []


def test_the_filled_run_reads_as_remaining_not_spent(mixin: _Mixin) -> None:
    """The docstring's contract: filled = remaining. A bar that filled up as the
    user spent would read as the exact opposite of the truth."""
    usage = types.SimpleNamespace(
        plan_bar=UsageBar(
            kind="plan", remaining_usd=8.0, total_usd=10.0, spent_usd=2.0
        ),
        topup_bar=None,
    )
    (line,) = mixin._usage_bar_lines(usage, "Pro")
    assert line.count("█") == 8 and line.count("░") == 2
    assert "$8.00 left of $10.00" in line
    assert "20% used" in line


def test_an_overspent_plan_clamps_the_bar_empty(mixin: _Mixin) -> None:
    """remaining can go negative; the bar must not render a negative run of
    blocks or overflow past ten."""
    usage = types.SimpleNamespace(
        plan_bar=UsageBar(
            kind="plan", remaining_usd=-5.0, total_usd=10.0, spent_usd=15.0
        ),
        topup_bar=None,
    )
    (line,) = mixin._usage_bar_lines(usage, "Pro")
    assert line.count("█") == 0 and line.count("░") == 10
    assert "100% used" in line, (
        "pct_used clamps at 100 even when spend exceeds the plan"
    )


def test_a_long_plan_name_is_truncated_to_the_column(mixin: _Mixin) -> None:
    """The label is a fixed 8-column gutter — a longer name must not shove the
    bar out of alignment with the row above it."""
    usage = types.SimpleNamespace(
        plan_bar=UsageBar(
            kind="plan", remaining_usd=5.0, total_usd=10.0, spent_usd=5.0
        ),
        topup_bar=None,
    )
    long_name, short_name = "Enterprise Unlimited", "Pro"
    (long_line,) = mixin._usage_bar_lines(usage, long_name)
    (short_line,) = mixin._usage_bar_lines(usage, short_name)

    # Assert the invariant (a fixed-width gutter) rather than a literal prefix —
    # the column width is the thing that must hold, and a literal is easy to
    # miscount by one, as this test originally did.
    assert long_line.index("[") == short_line.index("[") == len("  ") + 8
    assert long_line.startswith("  " + long_name[:8])
    assert short_line.startswith("  " + short_name.ljust(8))


def test_topup_is_drawn_full_and_only_when_there_is_a_balance(mixin: _Mixin) -> None:
    """A top-up has no denominator — it renders as a full bar of what is left,
    and disappears at zero rather than showing an empty one."""
    empty = types.SimpleNamespace(
        plan_bar=None,
        topup_bar=UsageBar(kind="topup", remaining_usd=0.0, total_usd=0.0),
    )
    assert mixin._usage_bar_lines(empty, None) == []

    funded = types.SimpleNamespace(
        plan_bar=None,
        topup_bar=UsageBar(kind="topup", remaining_usd=12.5, total_usd=12.5),
    )
    (line,) = mixin._usage_bar_lines(funded, None)
    assert line.count("█") == 10 and "░" not in line
    assert "$12.50 · never expires" in line


def test_the_bar_and_the_percentage_are_computed_from_different_fields(
    mixin: _Mixin,
) -> None:
    """Documenting a real subtlety rather than asserting it away: fill_fraction
    derives from remaining_usd and pct_used from spent_usd. When a credit or
    adjustment makes remaining != total - spent, the two disagree by design —
    the bar shows what is left, the percentage what was consumed. A reader who
    assumes they are complements would misread the row."""
    usage = types.SimpleNamespace(
        plan_bar=UsageBar(
            kind="plan", remaining_usd=9.0, total_usd=10.0, spent_usd=5.0
        ),
        topup_bar=None,
    )
    (line,) = mixin._usage_bar_lines(usage, "Pro")
    assert line.count("█") == 9, "the bar follows remaining"
    assert "50% used" in line, "the percentage follows spend"


def test_both_bars_render_in_plan_then_topup_order(mixin: _Mixin) -> None:
    usage = types.SimpleNamespace(
        plan_bar=UsageBar(
            kind="plan", remaining_usd=3.0, total_usd=10.0, spent_usd=7.0
        ),
        topup_bar=UsageBar(kind="topup", remaining_usd=20.0, total_usd=20.0),
    )
    plan, topup = mixin._usage_bar_lines(usage, "Pro")
    assert "left of" in plan and "never expires" in topup
