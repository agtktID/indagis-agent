#!/usr/bin/env bash
# Test harness for scripts/install_helpers.sh
#
# Asserts the 5-priority Indagis home resolution ladder behaves as
# documented in reports/plan-get-indagis-home-resolution.md (Draft 2
# Python equivalent). Runs in a subshell with controlled environment so
# HOME / INDAGIS_HOME / HERMES_HOME can be set without polluting the
# real filesystem or the user's actual ~/.indagis / ~/.hermes.
#
# Exit code 0 = all pass. Non-zero = first failing test.

set -u
set -o pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
HELPERS="$REPO_ROOT/scripts/install_helpers.sh"

if [ ! -f "$HELPERS" ]; then
    echo "FATAL: helpers file not found at $HELPERS" >&2
    exit 2
fi

PASS=0
FAIL=0
FAILURES=()

# Each test sources the helpers in a clean subshell with a controlled
# environment. We capture stdout (resolved path) and stderr (warnings)
# separately and assert on each independently.
run_test() {
    local name="$1"
    local expect_stdout_match="$2"
    local expect_stderr_match="$3"
    local env_setup="$4"

    local out err
    # env_setup is shell statements that are part of the bash -c body.
    # If env_setup is empty, we don't insert a stray "; " that would
    # produce a syntax error. We always prepend `set -u` for strict
    # variable checks. env -i gives us a clean environment so
    # HOME / INDAGIS_HOME / HERMES_HOME from the parent shell do not leak.
    #
    # $TEST_TMP interpolation happens in the parent shell BEFORE the
    # body is passed to bash -c (single-quote in the helper file
    # preserves the literal text on the inside).
    local body
    if [ -n "$env_setup" ]; then
        body="set -u; ${env_setup}; source '$HELPERS'; resolve_indagis_home"
    else
        body="set -u; source '$HELPERS'; resolve_indagis_home"
    fi
    body="${body//\$TEST_TMP/$TEST_TMP}"

    local rc
    env -i HOME="$TEST_TMP" USERPROFILE="$TEST_TMP" LOCALAPPDATA="" PATH="/usr/bin:/bin" \
        bash -c "$body" \
        >/tmp/indagis_test_out.$$ 2>/tmp/indagis_test_err.$$
    rc=$?
    out="$(cat /tmp/indagis_test_out.$$)"
    err="$(cat /tmp/indagis_test_err.$$)"

    rm -f /tmp/indagis_test_out.$$ /tmp/indagis_test_err.$$

    local ok=1
    local reason=""

    if [ "$rc" -ne 0 ]; then
        ok=0
        reason="exit code $rc"
    fi

    if [ -n "$expect_stdout_match" ]; then
        if ! printf '%s' "$out" | grep -qF -- "$expect_stdout_match"; then
            ok=0
            reason="stdout missing '$expect_stdout_match' (got: '$out', stderr: '$err')"
        fi
    fi

    if [ -n "$expect_stderr_match" ]; then
        if ! printf '%s' "$err" | grep -qF -- "$expect_stderr_match"; then
            ok=0
            reason="stderr missing '$expect_stderr_match' (got: '$err')"
        fi
    fi

    if [ "$ok" = "1" ]; then
        PASS=$((PASS + 1))
        echo "  PASS: $name"
    else
        FAIL=$((FAIL + 1))
        FAILURES+=("$name: $reason")
        echo "  FAIL: $name -- $reason"
    fi
}

# Set up an isolated filesystem tree for tests that need to test P2/P4.
TEST_TMP="$(mktemp -d)"
trap 'rm -rf "$TEST_TMP"' EXIT

# ─── P1: INDAGIS_HOME env var wins, no warning ─────────────────────
run_test "P1 INDAGIS_HOME explicit" \
    "$TEST_TMP/custom" \
    "" \
    "export INDAGIS_HOME='$TEST_TMP/custom'"

# ─── P2: ~/.indagis exists on disk, no warning ──────────────────────
mkdir -p "$TEST_TMP/.indagis"
run_test "P2 ~/.indagis exists" \
    "$TEST_TMP/.indagis" \
    "" \
    ""
rmdir "$TEST_TMP/.indagis"

# ─── P3: HERMES_HOME env var, legacy fallback ──────────────────────
# resolve_indagis_home itself does NOT emit the warning (the warning
# is emitted by install.sh, not the function — see install_helpers.sh
# comments). This test verifies the function returns the right path
# and stderr stays clean. install.sh separately fires the warning.
run_test "P3 HERMES_HOME legacy alias returns path, stderr clean" \
    "$TEST_TMP/legacy" \
    "" \
    "export HERMES_HOME='$TEST_TMP/legacy'"

# ─── P4: ~/.hermes exists, legacy fallback ─────────────────────────
mkdir -p "$TEST_TMP/.hermes"
run_test "P4 ~/.hermes exists returns path, stderr clean" \
    "$TEST_TMP/.hermes" \
    "" \
    ""
rmdir "$TEST_TMP/.hermes"

# ─── P5: nothing set, default ~/.indagis, no warning ────────────────
run_test "P5 nothing set, default platform path" \
    "$TEST_TMP/.indagis" \
    "" \
    ""

# ─── Critical: stdout is a SINGLE clean path, never polluted by the
#                warning text. This is the load-bearing contract for
#                call sites that capture via $(resolve_indagis_home).
mkdir -p "$TEST_TMP/.hermes"
run_test "stdout stays clean of warning text on P4" \
    "$TEST_TMP/.hermes" \
    "" \
    ""
# Recapture and assert: stdout must equal exactly the path with no
# warning text leaking in.
out="$(env -i HOME="$TEST_TMP" USERPROFILE="$TEST_TMP" LOCALAPPDATA="" PATH="/usr/bin:/bin" bash -c "source '$HELPERS'; resolve_indagis_home" 2>/dev/null)"
if [ "$out" = "$TEST_TMP/.hermes" ]; then
    PASS=$((PASS + 1))
    echo "  PASS: stdout is exactly the resolved path (no warning leak)"
else
    FAIL=$((FAIL + 1))
    FAILURES+=("stdout purity: got '$out' (expected '$TEST_TMP/.hermes')")
    echo "  FAIL: stdout is exactly the resolved path -- got '$out'"
fi
rmdir "$TEST_TMP/.hermes"

# ─── Bug regression: warning must fire EXACTLY ONCE per install.sh
#     invocation, even when resolve_indagis_home is called multiple
#     times via $(...) captures. Each $(...) spawns a subshell whose
#     _INDAGIS_LEGACY_ALIAS_WARNED guard is invisible to the parent,
#     so any warning emitted inside resolve_indagis_home repeats
#     every time the function is called.
#
# Scenario (mirrors install.sh L48-55):
#   1. Orchestrator fires the warning ONCE explicitly.
#   2. Two $(resolve_indagis_home) captures happen.
#   3. Total calls to _indagis_warn_legacy_alias_in_use_once = 1.
#
# RED before the fix: 3 calls (1 orchestrator + 2 captures).
# GREEN after the fix: 1 call (orchestrator only).
#
# Implementation: wrap _indagis_warn_legacy_alias_in_use_once to count
# its invocations. The counter is a fresh file per scenario, written
# from inside the wrap function, so it's unaffected by subshell state.
mkdir -p "$TEST_TMP/.hermes"
SCENARIO_DIR="$(mktemp -d)"
COUNTER="$SCENARIO_DIR/warning_call_count"

# Wrapper that increments a per-scenario counter file before delegating.
SCENARIO_BODY="$SCENARIO_DIR/body.sh"
{
    printf '%s\n' '# P3 scenario: user has set HERMES_HOME, so P3 (legacy alias) is the active priority.'
    printf 'export HERMES_HOME=%q\n' "$TEST_TMP/user_legacy"
    printf 'source %q\n' "$HELPERS"
    printf '%s\n' '_warn_orig=_indagis_warn_legacy_alias_in_use_once'
    printf '%s\n' '_indagis_warn_legacy_alias_in_use_once() {'
    printf '%s\n' "    printf 'x' >>$(printf '%q' "$COUNTER")"
    printf '%s\n' '    _warn_orig "$@"'
    printf '%s\n' '}'
    printf '%s\n' "_indagis_warn_legacy_alias_in_use_once 'HERMES_HOME' \"\$HERMES_HOME\" 2>/dev/null"
    printf '%s\n' 'resolved1=$(resolve_indagis_home 2>/dev/null)'
    printf '%s\n' 'resolved2=$(resolve_indagis_home 2>/dev/null)'
} >"$SCENARIO_BODY"
chmod +x "$SCENARIO_BODY"

# Run the scenario in a clean env.
env -i HOME="$TEST_TMP" USERPROFILE="$TEST_TMP" LOCALAPPDATA="" PATH="/usr/bin:/bin" \
    bash "$SCENARIO_BODY"

# Count how many 'x' bytes the counter accumulated. Each fire = 1 byte.
warn_count="$(wc -c <"$COUNTER" 2>/dev/null || echo 0)"

# Expected: exactly 1 (orchestrator). Pre-fix = 3 (orchestrator + 2 captures).
if [ "$warn_count" -eq 1 ]; then
    PASS=$((PASS + 1))
    echo "  PASS: warning fires exactly once total across orchestrator + 2 \$(...) captures"
else
    FAIL=$((FAIL + 1))
    FAILURES+=("warning fired $warn_count times; expected 1 (warning fires inside resolve_indagis_home on every \$(...) capture — bug not fixed)")
    echo "  FAIL: warning fired $warn_count times, expected 1"
fi

rm -rf "$SCENARIO_DIR"
rmdir "$TEST_TMP/.hermes"

# ─── Summary ────────────────────────────────────────────────────────
echo ""
echo "=== Summary: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -gt 0 ]; then
    echo "Failures:"
    for f in "${FAILURES[@]}"; do
        echo "  - $f"
    done
    exit 1
fi
exit 0
