#!/usr/bin/env bash
# Test harness for the launcher shim block in scripts/install.sh (L1736-1860).
#
# Asserts that:
#   1. All 6 PATH shims are generated when setup_path runs.
#   2. The 3 indagis* shims contain the expected launch logic
#      (unset PYTHONPATH/PYTHONHOME + exec $HERMES_BIN ...).
#   3. The 3 hermes* shims are thin deprecated aliases that:
#      - warn on stderr ("deprecated name, use 'indagis*' instead"),
#      - keep stdout clean (no warning leaks into command output),
#      - delegate to the corresponding indagis* shim via exec.
#   4. End-to-end: running the generated `hermes --version` shim actually
#      delegates to indagis, with the warning cleanly on stderr.
#
# METHODOLOGY — important:
#
#   This test does NOT replay heredoc templates from install.sh into the
#   test file. Instead it invokes the REAL scripts/install.sh via its
#   documented --stage path API, which routes to setup_path() L1720-1975
#   without triggering clone_repo / install_uv / check_python (the rest
#   of main()). USE_VENV is forced false via --no-venv so the path
#   branches taken are the ones a non-venv user would hit. stdout and
#   stderr from install.sh are redirected to temp files for capture.
#
#   This is the closest thing to "sourcing" the real install.sh without
#   pulling the whole installer in: --stage path is the official entry
#   point that runs setup_path() exactly as the production installer
#   does. If install.sh's shim block drifts, this test fails with a
#   clear "missing file" / "wrong content" diagnostic.
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
FAILURES=()

# Isolated filesystem. The shims land in $TEST_TMP/shims (the install.sh
# default for non-root + non-FHS users is ~/.local/bin, which we override
# by setting HOME to a tempdir and ensuring no FHS root marker is in
# place — see env block below).
TEST_TMP="$(mktemp -d)"
SHIM_DIR_NAME="shims"
trap 'rm -rf "$TEST_TMP"' EXIT

# ─── 1. Invoke the REAL install.sh via --stage path (setup_path) ─────
#
# Variables that steer setup_path:
#   - HOME=$TEST_TMP → get_command_link_dir falls back to $HOME/.local/bin
#   - INSTALL_DIR=$TEST_TMP/install (required by require_install_dir)
#   - USE_VENV=false (--no-venv) → uses `which` instead of venv python
#   - NON_INTERACTIVE=true → no prompts
#
# Setup_path calls `which indagis || which hermes` to populate HERMES_BIN.
# We seed PATH with $TEST_TMP/mockbin FIRST so the mock is picked up.
mkdir -p "$TEST_TMP/install" "$TEST_TMP/mockbin"
MOCK_HERMES_BIN="$TEST_TMP/mockbin/indagis"
cat >"$MOCK_HERMES_BIN" <<'MOCKEOF'
#!/usr/bin/env bash
echo "Indagis v1.2.3"
for a in "$@"; do
    echo "arg: $a"
done
exit 0
MOCKEOF
chmod +x "$MOCK_HERMES_BIN"
# Also expose `hermes` as the secondary lookup target so `which` chain
# succeeds even if our mock is named indagis only.
ln -sf "$MOCK_HERMES_BIN" "$TEST_TMP/mockbin/hermes"

INSTALL_STDOUT="$TEST_TMP/install.stdout"
INSTALL_STDERR="$TEST_TMP/install.stderr"

# Run install.sh with all output redirected to temp files. The script's
# own log_* helpers go to stderr; the few `echo` lines (banner, success
# messages) go to stdout. Capturing both separately lets us assert on
# each channel independently.
HOME="$TEST_TMP" \
    INSTALL_DIR="$TEST_TMP/install" \
    USE_VENV=false \
    NON_INTERACTIVE=true \
    PATH="$TEST_TMP/mockbin:/usr/bin:/bin" \
    bash "$INSTALL_SH" --stage path --no-venv --non-interactive \
    >"$INSTALL_STDOUT" 2>"$INSTALL_STDERR"
INSTALL_RC=$?

# Install.sh's --stage path returns the exit code of setup_path. Any
# non-zero is a real failure we want to surface, not paper over.
if [ "$INSTALL_RC" -ne 0 ]; then
    FAIL=$((FAIL + 1))
    FAILURES+=("install.sh --stage path exited $INSTALL_RC. stderr: $(cat "$INSTALL_STDERR")")
    echo "  FAIL: install.sh --stage path invocation succeeded (exit $INSTALL_RC)"
    echo "--- install.sh stderr ---"
    cat "$INSTALL_STDERR"
    echo "--- end stderr ---"
    exit 1
else
    PASS=$((PASS + 1))
    echo "  PASS: install.sh --stage path invocation succeeded (exit 0)"
fi

# setup_path writes shims to $HOME/.local/bin by default (non-root,
# non-FHS layout). That's our SHIM_DIR.
SHIM_DIR="$TEST_TMP/.local/bin"
if [ ! -d "$SHIM_DIR" ]; then
    FAIL=$((FAIL + 1))
    FAILURES+=("shim dir $SHIM_DIR not created (setup_path did not run). stderr: $(cat "$INSTALL_STDERR")")
    echo "  FAIL: shim directory $SHIM_DIR was created by setup_path"
    exit 1
else
    PASS=$((PASS + 1))
    echo "  PASS: shim directory $SHIM_DIR exists (setup_path ran)"
fi

# ─── 2. Assert all 6 files exist and are executable ─────────────────
for f in indagis hermes indagis-agent hermes-agent indagis-acp hermes-acp; do
    if [ ! -x "$SHIM_DIR/$f" ]; then
        FAIL=$((FAIL + 1))
        FAILURES+=("shim $f: missing or not executable at $SHIM_DIR/$f")
        echo "  FAIL: shim $f exists and is executable"
    else
        PASS=$((PASS + 1))
        echo "  PASS: shim $f exists and is executable"
    fi
done

# ─── 3. Assert content of indagis* primary shims ────────────────────
#
# Each primary shim must clear PYTHONPATH/PYTHONHOME and exec into the
# venv python + checked-in entrypoint. We don't pin the exact exec
# arguments (those vary by USE_VENV), only the load-bearing lines.

assert_contains() {
    local name="$1"
    local file="$2"
    local needle="$3"
    if grep -qF -- "$needle" "$file"; then
        PASS=$((PASS + 1))
        echo "  PASS: $name contains '$needle'"
    else
        FAIL=$((FAIL + 1))
        FAILURES+=("$name: file $file missing required line '$needle'")
        echo "  FAIL: $name contains '$needle' -- not found in $file"
    fi
}

# Primary shim exec assertion: match the resolved-path form, not the
# literal "$HERMES_BIN" (which is substituted at heredoc time by setup_path).
# Pattern: `exec "<resolved-path>"` somewhere in the file — followed by
# optional args, but always ending with "$@".
assert_contains_primary_exec() {
    local file="$1"
    if grep -qE '^exec "[^"]+".*"\$@"' "$file"; then
        PASS=$((PASS + 1))
        echo "  PASS: primary shim $file has exec \"<resolved-path>\" ... \"\$@\""
    else
        FAIL=$((FAIL + 1))
        FAILURES+=("primary shim $file missing exec \"<path>\" ... \"\$@\" form. contents: '$(cat "$file")'")
        echo "  FAIL: primary shim $file has exec-form line"
    fi
}

for shim in indagis indagis-agent indagis-acp; do
    f="$SHIM_DIR/$shim"
    assert_contains "primary shim $shim" "$f" "unset PYTHONPATH"
    assert_contains "primary shim $shim" "$f" "unset PYTHONHOME"
    # setup_path substitutes $HERMES_BIN at heredoc-expansion time, so
    # the shim contains the resolved absolute path (e.g. /tmp/foo/bin/indagis)
    # not the literal string "$HERMES_BIN". Match the form: an exec line
    # that begins with `exec "`. If USE_VENV=true the line also references
    # $HERMES_ENTRYPOINT, but --no-venv forces the simpler form.
    assert_contains_primary_exec "$f"
done

# ─── 4. Assert content of hermes* deprecated alias shims ─────────────
#
# Each alias shim must:
#   - warn on stderr (the >&2 redirect is the contract)
#   - delegate to its indagis* sibling via exec

for pair in "hermes:indagis" "hermes-agent:indagis-agent" "hermes-acp:indagis-acp"; do
    alias_name="${pair%:*}"
    primary_name="${pair#*:}"
    alias_file="$SHIM_DIR/$alias_name"
    primary_file="$SHIM_DIR/$primary_name"

    # Warning goes to stderr, not stdout. The '>&2' on the echo line is
    # load-bearing — if someone drops it the warning leaks into command
    # output (a real bug we want to catch).
    assert_contains "alias $alias_name" "$alias_file" "deprecated name, use '$primary_name' instead"
    assert_contains "alias $alias_name stderr redirect" "$alias_file" '>&2'

    # The exec line must reference the sibling primary shim, not the
    # python binary directly. If install.sh drifts to exec $HERMES_BIN
    # here, the warning gets emitted before any work, but the alias
    # becomes a 2nd copy of the launch logic — defeating the point.
    assert_contains "alias $alias_name delegates to primary" "$alias_file" "exec \"$SHIM_DIR/$primary_name\""
done

# ─── 5. REAL EXECUTION: run the hermes alias and assert behaviour ───
#
# Point 4 of the brief: actually launch hermes --version via the
# generated alias, capture stdout/stderr separately, prove that:
#   - exit code 0 (delegation didn't crash)
#   - stdout contains the delegated output (mock's "Indagis v1.2.3")
#   - stdout is NOT polluted by the warning
#   - stderr contains the deprecation warning
#   - hermes stdout == indagis stdout (byte-identical delegation)
#
# The mock binary is what `which indagis` resolved during setup_path,
# so it's already on PATH for the shim to find via exec $HERMES_BIN.

HERMES_OUT="$TEST_TMP/hermes.stdout"
HERMES_ERR="$TEST_TMP/hermes.stderr"
bash "$SHIM_DIR/hermes" --version >"$HERMES_OUT" 2>"$HERMES_ERR"
HERMES_RC=$?

# 5a. Exit code 0 (delegation didn't crash).
if [ "$HERMES_RC" -eq 0 ]; then
    PASS=$((PASS + 1))
    echo "  PASS: hermes --version exits 0 (delegation completed)"
else
    FAIL=$((FAIL + 1))
    FAILURES+=("hermes --version: exit code $HERMES_RC, expected 0. stderr: $(cat "$HERMES_ERR")")
    echo "  FAIL: hermes --version exits 0 -- got $HERMES_RC"
fi

# 5b. Stdout contains the mock output (proves delegation actually ran).
if grep -qF -- "Indagis v1.2.3" "$HERMES_OUT"; then
    PASS=$((PASS + 1))
    echo "  PASS: hermes --version stdout contains 'Indagis v1.2.3' (delegated output present)"
else
    FAIL=$((FAIL + 1))
    FAILURES+=("hermes --version: stdout missing 'Indagis v1.2.3' (delegation failed). got stdout: '$(cat "$HERMES_OUT")'")
    echo "  FAIL: hermes --version stdout contains delegated output -- got '$(cat "$HERMES_OUT")'"
fi

# 5c. Stdout is NOT polluted by the deprecation warning.
if grep -qF -- "deprecated name" "$HERMES_OUT"; then
    FAIL=$((FAIL + 1))
    FAILURES+=("hermes --version: stdout polluted by warning text (warn leaked). got stdout: '$(cat "$HERMES_OUT")'")
    echo "  FAIL: hermes --version stdout is NOT polluted by warning"
else
    PASS=$((PASS + 1))
    echo "  PASS: hermes --version stdout is NOT polluted by warning (clean)"
fi

# 5d. Stderr contains the deprecation warning.
if grep -qF -- "hermes: deprecated name, use 'indagis' instead" "$HERMES_ERR"; then
    PASS=$((PASS + 1))
    echo "  PASS: hermes --version stderr contains the deprecation warning"
else
    FAIL=$((FAIL + 1))
    FAILURES+=("hermes --version: stderr missing deprecation warning. got stderr: '$(cat "$HERMES_ERR")'")
    echo "  FAIL: hermes --version stderr contains warning -- got '$(cat "$HERMES_ERR")'"
fi

# 5e. CRITICAL CROSS-CHECK: the delegated stdout from `hermes --version`
# is byte-identical to what `indagis --version` produced (minus the
# warning on stderr). Run indagis directly and diff stdout.
INDAGIS_OUT="$TEST_TMP/indagis.stdout"
bash "$SHIM_DIR/indagis" --version >"$INDAGIS_OUT" 2>/dev/null

if cmp -s "$HERMES_OUT" "$INDAGIS_OUT"; then
    PASS=$((PASS + 1))
    echo "  PASS: hermes --version stdout == indagis --version stdout (byte-identical delegation)"
else
    FAIL=$((FAIL + 1))
    FAILURES+=("delegation mismatch: hermes stdout differs from indagis stdout. hermes: '$(cat "$HERMES_OUT")' vs indagis: '$(cat "$INDAGIS_OUT")'")
    echo "  FAIL: hermes --version stdout == indagis --version stdout -- differ"
fi

# 5f. Same cross-check for hermes-agent → indagis-agent delegation.
HA_OUT="$TEST_TMP/hermes-agent.stdout"
HA_ERR="$TEST_TMP/hermes-agent.stderr"
IA_OUT="$TEST_TMP/indagis-agent.stdout"
bash "$SHIM_DIR/hermes-agent" --help >"$HA_OUT" 2>"$HA_ERR"
bash "$SHIM_DIR/indagis-agent" --help >"$IA_OUT" 2>/dev/null

_stdout_match=0
cmp -s "$HA_OUT" "$IA_OUT" && _stdout_match=1
_warning_on_stderr=0
grep -qF -- "hermes-agent: deprecated name, use 'indagis-agent' instead" "$HA_ERR" && _warning_on_stderr=1
if [ "$_stdout_match" = "1" ] && [ "$_warning_on_stderr" = "1" ]; then
    PASS=$((PASS + 1))
    echo "  PASS: hermes-agent --help delegates cleanly to indagis-agent (stdout equal, warning on stderr)"
else
    FAIL=$((FAIL + 1))
    FAILURES+=("hermes-agent delegation broken. stdout_match=$_stdout_match (expected 1). warning_on_stderr=$_warning_on_stderr (expected 1)")
    echo "  FAIL: hermes-agent --help delegation"
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
