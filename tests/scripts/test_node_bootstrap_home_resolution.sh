#!/usr/bin/env bash
# Test harness for scripts/lib/node-bootstrap.sh
#
# Verifies that node-bootstrap.sh respects the Indagis home resolution
# purity contract (plan-get-indagis-home-resolution.md, section
# "Point d'attention pour Draft 4"):
#
#   1. node-bootstrap.sh MUST NOT hardcode $HOME/.hermes in its env-var
#      initialization (rebrand residue — Indagis default is ~/.indagis).
#   2. node-bootstrap.sh MUST source scripts/install_helpers.sh to obtain
#      resolve_indagis_home() — no duplicated resolution logic.
#   3. When the host script sources node-bootstrap.sh and the user has set
#      HERMES_HOME, $(resolve_indagis_home) MUST return the path on stdout
#      with no warning text leaking in (orchestrator fires the warning
#      explicitly before the capture, the function stays pure).
#   4. The deprecation warning MUST fire exactly once across the orchestrator
#      pattern (1 explicit fire + N $(...) captures), not N+1 times — that
#      regression is the Draft 2.1 bug we are guarding against.
#
# Runs in a subshell with a controlled env (HOME / INDAGIS_HOME /
# HERMES_HOME) and an isolated mktemp fixture dir so the real filesystem
# is never touched.
#
# Exit code 0 = all pass. Non-zero = first failing test.

set -u
set -o pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
HELPERS="$REPO_ROOT/scripts/install_helpers.sh"
NODE_BOOTSTRAP="$REPO_ROOT/scripts/lib/node-bootstrap.sh"

if [ ! -f "$HELPERS" ]; then
    echo "FATAL: helpers file not found at $HELPERS" >&2
    exit 2
fi
if [ ! -f "$NODE_BOOTSTRAP" ]; then
    echo "FATAL: node-bootstrap.sh not found at $NODE_BOOTSTRAP" >&2
    exit 2
fi

PASS=0
FAIL=0
FAILURES=()

# ─── Contract 1: source-level — no hardcoded $HOME/.hermes literal ───
#
# node-bootstrap.sh initialized HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
# before Draft 4. The rebrand target is INDAGIS_HOME + resolve_indagis_home.
# If the literal survives, the user's ~/.indagis is silently shadowed by
# their old ~/.hermes on next install — the exact bug Tranche 1 fixes.
#
# NOTE: this test deliberately does NOT scan the entire file for every
# occurrence of "/.hermes" because node-bootstrap.sh legitimately mentions
# ~/.hermes in comments (e.g. "prior Hermes-managed install"). It targets
# only the top-of-file env-var initialization where the rebrand residue
# would live.
NB_TEXT="$(cat "$NODE_BOOTSTRAP")"
if printf '%s\n' "$NB_TEXT" | head -30 | grep -qE '^HERMES_HOME="\$\{HERMES_HOME:-\$HOME/\.hermes\}"'; then
    FAIL=$((FAIL + 1))
    FAILURES+=("contract 1: HERMES_HOME initialization still hardcodes \$HOME/.hermes (rebrand residue)")
    echo "  FAIL: contract 1 — HERMES_HOME env-var init still uses \$HOME/.hermes literal"
else
    PASS=$((PASS + 1))
    echo "  PASS: contract 1 — HERMES_HOME init no longer hardcodes \$HOME/.hermes"
fi

# ─── Contract 2: source-level — node-bootstrap sources install_helpers ───
#
# The Draft 4 design reuses resolve_indagis_home() from install_helpers.sh
# rather than reimplementing the 5-priority ladder. Verify the source
# command is present (exact path substring to avoid matching unrelated
# `source` calls in functions like _nb_try_nvm which source nvm.sh).
# We accept any `source ... install_helpers.sh` line (the path prefix may
# be a relative `../install_helpers.sh`, an absolute variable like
# $_NB_SCRIPT_DIR/../install_helpers.sh, or the install.sh form).
#
# Important: we strip leading whitespace and skip lines that begin with
# `#` (comments) so a commented-out `source` line doesn't count as a hit.
# Without this, contract 2 would stay GREEN even if someone commented
# out the real source — exactly the failure mode that contract 3a/3b
# just exposed.
if printf '%s\n' "$NB_TEXT" \
    | grep -vE '^[[:space:]]*#' \
    | grep -qE '[[:space:]]*source[[:space:]]+.*install_helpers\.sh'; then
    PASS=$((PASS + 1))
    echo "  PASS: contract 2 — node-bootstrap sources scripts/install_helpers.sh (uncommented)"
else
    FAIL=$((FAIL + 1))
    FAILURES+=("contract 2: node-bootstrap.sh does not source install_helpers.sh (or source is commented out) — resolver missing or duplicated")
    echo "  FAIL: contract 2 — install_helpers.sh not sourced from node-bootstrap.sh"
fi

# Set up an isolated filesystem tree for tests that need to mock files.
TEST_TMP="$(mktemp -d)"
trap 'rm -rf "$TEST_TMP"' EXIT

# ─── Contract 3: stdout purity from real node-bootstrap.sh ────────────
#
# Test design: source the REAL node-bootstrap.sh in a controlled env,
# then capture $(resolve_indagis_home) in the same shell. The resolved
# path MUST be on stdout alone — no warning text bleeding in. This is
# what node-bootstrap's callers (and any future orchestrators that
# source it) depend on for `$(resolve_indagis_home)` to return a
# clean path they can use as a directory.
#
# We use TWO scenarios (P1 wins over P3, then P3 alone) to cover both
# the case where an explicit INDAGIS_HOME is set AND the legacy
# HERMES_HOME fallback path. Both go through real node-bootstrap.sh.

# ─── Contract 3a: with INDAGIS_HOME set, $(resolve_indagis_home) from
#                    real node-bootstrap.sh returns the Indagis path
#                    cleanly. P1 wins over P3 (HERMES_HOME also set).
mkdir -p "$TEST_TMP/.indagis"

OUT="$(env -i HOME="$TEST_TMP" USERPROFILE="$TEST_TMP" LOCALAPPDATA="" \
    INDAGIS_HOME="$TEST_TMP/.indagis" HERMES_HOME="$TEST_TMP/legacy_hermes" \
    PATH="/usr/bin:/bin" \
    bash -c "
    set -u
    source '$NODE_BOOTSTRAP'
    resolve_indagis_home
" 2>/dev/null)"

if [ "$OUT" = "$TEST_TMP/.indagis" ]; then
    PASS=$((PASS + 1))
    echo "  PASS: contract 3a — \$(resolve_indagis_home) from real node-bootstrap returns P1 path cleanly"
else
    FAIL=$((FAIL + 1))
    FAILURES+=("contract 3a: stdout polluted: got '$OUT' (expected '$TEST_TMP/.indagis')")
    echo "  FAIL: contract 3a — stdout purity (got: '$OUT')"
fi

rmdir "$TEST_TMP/.indagis" 2>/dev/null || true

# ─── Contract 3b: P3 alone — no INDAGIS_HOME, only HERMES_HOME legacy.
#                    node-bootstrap's orchestrator fires the warning once
#                    at source time, then $(resolve_indagis_home) returns
#                    the HERMES_HOME path cleanly.
OUT="$(env -i HOME="$TEST_TMP" USERPROFILE="$TEST_TMP" LOCALAPPDATA="" \
    HERMES_HOME="$TEST_TMP/legacy_hermes" \
    PATH="/usr/bin:/bin" \
    bash -c "
    set -u
    source '$NODE_BOOTSTRAP'
    resolve_indagis_home
" 2>/dev/null)"

if [ "$OUT" = "$TEST_TMP/legacy_hermes" ]; then
    PASS=$((PASS + 1))
    echo "  PASS: contract 3b — \$(resolve_indagis_home) from real node-bootstrap returns P3 path cleanly"
else
    FAIL=$((FAIL + 1))
    FAILURES+=("contract 3b: stdout polluted: got '$OUT' (expected '$TEST_TMP/legacy_hermes')")
    echo "  FAIL: contract 3b — stdout purity on P3 (got: '$OUT')"
fi

# ─── Contract 4: helper is PURE after node-bootstrap.sh has run ──────
#
# The Draft 2.1 bug: every $(resolve_indagis_home) inside an orchestrator
# re-fires the warning because each $(...) spawns a fresh subshell. The
# fix moved the warning fire into the orchestrator (one explicit call
# before the first capture) and made the helper pure.
#
# Test design — exactly mirrors test_install_helpers_home_resolution.sh
# lines 174-216 (the Draft 2.1 regression guard):
#
#   1. Source the REAL node-bootstrap.sh in a clean subshell with
#      HERMES_HOME=legacy_path. node-bootstrap's top-of-file orchestrator
#      fires the warning once, captures HERMES_HOME, exports it.
#   2. AFTER node-bootstrap has finished, wrap _indagis_warn_..._once
#      to count invocations to a per-test counter file.
#   3. Call resolve_indagis_home in the same shell (NOT in a subshell,
#      so the wrapper is reachable).
#
# Expected (GREEN, fix in place):
#   - node-bootstrap fired the warning ONCE during source → counter
#     captures this initial fire because the wrapper was already in
#     place. Wait — see note below.
#
#   Note on counting: install_helpers.sh defines _indagis_warn_..._once
#   as a fresh shell function. The wrapper defined BEFORE the source
#   gets clobbered when node-bootstrap re-sources install_helpers.sh.
#   That's why the wrapper is defined AFTER, and we measure only
#   post-source invocations.
#
# Expected (GREEN, helper pure):
#   - After node-bootstrap.sh finishes, calling resolve_indagis_home
#     must NOT call the warning function (helper is pure). Counter = 0.
#
# Expected (RED, Draft 2.1 bug re-introduced):
#   - helper fires warning inside → counter >= 1.
#
# This is the load-bearing contract. If a future refactor moves the
# warning back into resolve_indagis_home, this test fails with a
# clear "Draft 2.1 regression" message.
SCENARIO_DIR="$(mktemp -d)"
COUNTER="$SCENARIO_DIR/warning_call_count"
SCENARIO_BODY="$SCENARIO_DIR/body.sh"
{
    # Set HERMES_HOME to a legacy path so P3 (legacy alias) is the
    # active priority at source time of node-bootstrap.sh. This forces
    # the orchestrator pattern (warning + capture) to execute.
    printf 'export HERMES_HOME=%q\n' "$TEST_TMP/user_legacy"
    # Now source the REAL node-bootstrap.sh — its top-of-file orchestrator
    # block fires the warning and resolves HERMES_HOME.
    printf 'source %q\n' "$NODE_BOOTSTRAP"
    # AFTER node-bootstrap has done its work, wrap the warning function
    # so any future call to resolve_indagis_home that re-invokes the
    # warning gets counted. install_helpers.sh's definition of
    # _indagis_warn_legacy_alias_in_use_once has already run during the
    # source above; our wrapper replaces it in the current shell scope.
    printf '%s\n' '_orig_warn=_indagis_warn_legacy_alias_in_use_once'
    printf '%s\n' '_indagis_warn_legacy_alias_in_use_once() {'
    printf '%s\n' "    printf 'x' >>$(printf '%q' "$COUNTER")"
    printf '%s\n' '    _orig_warn "$@"'
    printf '%s\n' '}'
    # Now exercise the resolver. If helper is pure, no warning → counter
    # stays empty. If Draft 2.1 bug is back, helper fires → counter grows.
    printf '%s\n' 'resolved=$(resolve_indagis_home 2>/dev/null)'
    # Multiple captures to stress-test: even with 3 $(...) the helper
    # must remain pure (each capture is a fresh subshell that inherits
    # the current shell's function definitions; if the helper had
    # embedded the warning, each would count).
    printf '%s\n' 'r1=$(resolve_indagis_home 2>/dev/null)'
    printf '%s\n' 'r2=$(resolve_indagis_home 2>/dev/null)'
} >"$SCENARIO_BODY"
chmod +x "$SCENARIO_BODY"

env -i HOME="$TEST_TMP" USERPROFILE="$TEST_TMP" LOCALAPPDATA="" PATH="/usr/bin:/bin" \
    bash "$SCENARIO_BODY"

warn_count="$(wc -c <"$COUNTER" 2>/dev/null || echo 0)"

if [ "$warn_count" -eq 0 ]; then
    PASS=$((PASS + 1))
    echo "  PASS: contract 4 — helper is pure after real node-bootstrap.sh sources (no warning re-fired by \$(...) captures)"
else
    FAIL=$((FAIL + 1))
    FAILURES+=("contract 4: warning re-fired $warn_count times after sourcing real node-bootstrap.sh — Draft 2.1 bug re-introduced")
    echo "  FAIL: contract 4 — helper impure, warning fired $warn_count times post-source (Draft 2.1 regression)"
fi

rm -rf "$SCENARIO_DIR"

# ─── Contract 5: source-level — resolver is NOT called from inside node-bootstrap's
#                   ensure_node path with a polluted warning. We verify by
#                   asserting that node-bootstrap does NOT directly invoke
#                   _indagis_warn_legacy_alias_in_use_once (the orchestrator
#                   must fire it explicitly per the plan; if node-bootstrap
#                   fires it AND we source it, we get duplicate emissions).
#
# This is the load-bearing guard against re-introducing the Draft 2.1 bug
# in node-bootstrap.sh. We accept one explicit fire site (the source-from
# orchestrator boilerplate); multiple sites would mean the orchestrator
# is firing on every entry to ensure_node(), which is wrong.
fire_count="$(grep -c '_indagis_warn_legacy_alias_in_use_once' "$NODE_BOOTSTRAP" || true)"
if [ "$fire_count" -le 2 ]; then
    PASS=$((PASS + 1))
    echo "  PASS: contract 5 — _indagis_warn_legacy_alias_in_use_once referenced at most 2 times in node-bootstrap (1 source boilerplate + 1 fire)"
else
    FAIL=$((FAIL + 1))
    FAILURES+=("contract 5: _indagis_warn_legacy_alias_in_use_once appears $fire_count times in node-bootstrap.sh — risk of duplicate emission")
    echo "  FAIL: contract 5 — warning fired from too many sites ($fire_count)"
fi

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
