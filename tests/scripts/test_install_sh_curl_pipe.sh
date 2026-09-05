#!/usr/bin/env bash
# Test harness for the `curl … | bash` install path.
#
# WHY THIS EXISTS. scripts/install.sh sources its sibling
# scripts/install_helpers.sh via a BASH_SOURCE-relative path. That resolves
# correctly for a local checkout and NOT AT ALL for the one-liner the script's
# own header documents: piped to bash there is no script file, so
# BASH_SOURCE[0] is empty and $0 is literally "bash", the path resolves to the
# user's current directory, and `set -e` kills the install before it prints a
# single character.
#
# This was fixed once, in 464e40824 ("fix(install): add a download fallback for
# install_helpers.sh under curl|bash"), and the fix was then lost — that commit
# is not an ancestor of main. Nothing noticed, because every existing test
# sources install_helpers.sh directly from $REPO_ROOT and therefore cannot
# reach this failure. A defect that can silently come back is a defect that
# needs a test, so: this file.
#
# Two assertions, deliberately of different kinds:
#   1. STRUCTURAL (hermetic, no network) — the source must be guarded by a
#      file-existence test with a fallback. Catches the regression the instant
#      someone reverts to a bare `source`.
#   2. BEHAVIOURAL (needs network) — actually pipe the script into bash from a
#      directory that does not contain install_helpers.sh, and require it to
#      get past the sourcing block. Skipped when offline rather than failed,
#      because a missing network is not a bug in install.sh.
#
# Exit code 0 = all pass. Non-zero = first failing test.

set -u
set -o pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
INSTALL_SH="$REPO_ROOT/scripts/install.sh"

if [ ! -f "$INSTALL_SH" ]; then
    echo "FATAL: install.sh not found at $INSTALL_SH" >&2
    exit 2
fi

PASS=0
FAIL=0

ok()   { PASS=$((PASS + 1)); printf '  PASS  %s\n' "$1"; }
bad()  { FAIL=$((FAIL + 1)); printf '  FAIL  %s\n' "$1"; [ -n "${2:-}" ] && printf '        %s\n' "$2"; }
skip() { printf '  SKIP  %s\n' "$1"; }

echo "== install.sh under curl | bash =="

# ─── 1. Syntax, so a broken edit fails here rather than in a user's shell ───
if bash -n "$INSTALL_SH" 2>/dev/null; then
    ok "install.sh parses"
else
    bad "install.sh parses" "$(bash -n "$INSTALL_SH" 2>&1 | head -3)"
fi

# ─── 2. Structural: the source must not be bare ─────────────────────────────
# A bare `source "$_SCRIPT_DIR_HERE/install_helpers.sh"` with no guard is the
# exact shape of the regression. Anchored at column 0 on purpose: the guarded
# form is indented inside the `if`, so allowing leading whitespace here would
# match the correct code too and fail forever.
if grep -qE '^source "\$_SCRIPT_DIR_HERE/install_helpers\.sh"\s*$' "$INSTALL_SH"; then
    bad "the helpers source is guarded" \
        "found an unguarded 'source \$_SCRIPT_DIR_HERE/install_helpers.sh' — this breaks curl|bash"
else
    ok "the helpers source is guarded"
fi

if grep -q 'if \[ -f "\$_SCRIPT_DIR_HERE/install_helpers.sh" \]' "$INSTALL_SH"; then
    ok "a file-existence check precedes the source"
else
    bad "a file-existence check precedes the source"
fi

if grep -q 'raw.githubusercontent.com/agtktID/indagis-agent/main/scripts/install_helpers.sh' "$INSTALL_SH"; then
    ok "a download fallback URL is present"
else
    bad "a download fallback URL is present"
fi

# ─── 3. Behavioural: really pipe it into bash from an empty directory ───────
# The sourcing block is what we are testing; running the whole installer would
# mutate the machine. So feed bash only the prefix up to and including the
# block, located by its closing marker rather than a hardcoded line number —
# a fixed count silently stops testing the right thing the moment a line is
# added above it.
END_LINE="$(grep -n '^INDAGIS_HOME="\$(resolve_indagis_home)"' "$INSTALL_SH" | head -1 | cut -d: -f1)"

if [ -z "$END_LINE" ]; then
    bad "could not locate the end of the sourcing block" \
        "expected a line 'INDAGIS_HOME=\"\$(resolve_indagis_home)\"'"
else
    ok "located the sourcing block (ends line $END_LINE)"

    if ! curl -fsSL --max-time 15 -o /dev/null \
         "https://raw.githubusercontent.com/agtktID/indagis-agent/main/scripts/install_helpers.sh" 2>/dev/null; then
        skip "piped execution — raw.githubusercontent.com unreachable (offline, not a defect)"
    else
        WORKDIR="$(mktemp -d)"
        # No install_helpers.sh here; that is the whole point.
        OUTPUT="$(cd "$WORKDIR" && head -n "$END_LINE" "$INSTALL_SH" | bash 2>&1)"
        STATUS=$?
        rm -rf "$WORKDIR"

        if [ "$STATUS" -eq 0 ]; then
            ok "piped into bash from a directory without install_helpers.sh"
        else
            bad "piped into bash from a directory without install_helpers.sh" \
                "exit $STATUS: $(printf '%s' "$OUTPUT" | tail -2 | tr '\n' ' ')"
        fi
    fi
fi

echo
if [ "$FAIL" -eq 0 ]; then
    echo "== $PASS passed, 0 failed =="
    exit 0
fi

echo "== $PASS passed, $FAIL FAILED =="
exit 1
