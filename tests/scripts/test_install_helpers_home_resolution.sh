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

# ─── P3: HERMES_HOME env var, legacy fallback + warning on stderr ──
run_test "P3 HERMES_HOME legacy alias" \
    "$TEST_TMP/legacy" \
    "HERMES_HOME" \
    "export HERMES_HOME='$TEST_TMP/legacy'"

# ─── P4: ~/.hermes exists, legacy fallback + warning on stderr ──────
mkdir -p "$TEST_TMP/.hermes"
run_test "P4 ~/.hermes exists" \
    "$TEST_TMP/.hermes" \
    "~/.hermes" \
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

# ─── Warning fires once per shell session (process-level guard) ─────
mkdir -p "$TEST_TMP/.hermes"
# Capture stderr from THREE consecutive resolve_indagis_home calls in the
# same shell session, and verify the warning fires exactly once.
err_thrice="$(
    env -i HOME="$TEST_TMP" USERPROFILE="$TEST_TMP" LOCALAPPDATA="" PATH="/usr/bin:/bin" \
        bash -c "
            source '$HELPERS'
            resolve_indagis_home >/dev/null
            resolve_indagis_home >/dev/null
            resolve_indagis_home >/dev/null
        " 2>&1 >/dev/null
)"
err_lines="$(printf '%s\n' "$err_thrice" | wc -l)"
if [ "$err_lines" -eq 6 ]; then
    # 6 lines = one full warning (6 lines in install_helpers.sh):
    # line 1: blank header
    # line 2: ⚠ Indagis Agent: ...
    # line 3: The deprecation alias...
    # line 4: Migrate by running:
    # line 5: mv ~/.hermes ~/.indagis
    # line 6: Then re-source your shell ...
    PASS=$((PASS + 1))
    echo "  PASS: legacy alias warning fires exactly once per session (6 lines for 3 calls)"
else
    FAIL=$((FAIL + 1))
    FAILURES+=("warning produced $err_lines lines for 3 calls, expected 6 (one full warning block)")
    echo "  FAIL: warning produced $err_lines lines for 3 calls, expected 6"
    echo "  --- captured stderr ---"
    printf '%s\n' "$err_thrice"
    echo "  --- end ---"
fi
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
