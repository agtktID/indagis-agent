# scripts/install_helpers.sh — extracted helpers from install.sh for unit tests
# This file is sourced by install.sh (Draft 2) AND by the test harness
# (tests/scripts/test_install_helpers_home_resolution.sh). It MUST NOT
# have side effects at source time (no top-level state mutation).
#
# All functions here use stdout for the resolved path (so callers can
# capture via $(...)) and stderr (>&2) for warnings. Mixing the two would
# corrupt captured values.

# Returns the platform-native default Indagis home path (POSIX or Windows).
# On POSIX: ~/.indagis. On Windows: %LOCALAPPDATA%\indagis (falls back to
# %USERPROFILE%\AppData\Local\indagis if LOCALAPPDATA is unset).
indagis_platform_default_home() {
    case "$(uname -s 2>/dev/null || echo unknown)" in
        MINGW*|MSYS*|CYGWIN*)
            local local_appdata="${LOCALAPPDATA:-}"
            if [ -n "$local_appdata" ]; then
                printf '%s\n' "$local_appdata/indagis"
            else
                printf '%s\n' "$USERPROFILE/AppData/Local/indagis"
            fi
            ;;
        *)
            printf '%s\n' "$HOME/.indagis"
            ;;
    esac
}

# Returns the legacy alias path (POSIX: ~/.hermes, Windows:
# %LOCALAPPDATA%\hermes). Returns empty string if the directory does not
# exist on disk (so callers can detect "not applicable" cleanly).
indagis_legacy_alias_home() {
    local legacy_path=""
    case "$(uname -s 2>/dev/null || echo unknown)" in
        MINGW*|MSYS*|CYGWIN*)
            local local_appdata="${LOCALAPPDATA:-}"
            if [ -n "$local_appdata" ]; then
                legacy_path="$local_appdata/hermes"
            else
                legacy_path="$USERPROFILE/AppData/Local/hermes"
            fi
            ;;
        *)
            legacy_path="$HOME/.hermes"
            ;;
    esac
    if [ -d "$legacy_path" ]; then
        printf '%s\n' "$legacy_path"
    fi
}

# Emits a one-shot stderr warning when resolution fell back to a legacy
# alias. Sets a process-level guard so the warning only fires once per
# shell session.
#
# IMPORTANT: this function writes to STDERR (>&2), not stdout. The
# resolve_indagis_home() function above uses `printf '%s\n' "$path"` on
# stdout so callers can capture the resolved path via $(resolve_indagis_home).
# If this warning were emitted on stdout, it would be captured as part of
# the path string and break every call site that uses $(resolve_indagis_home).
_indagis_warn_legacy_alias_in_use_once() {
    local resolved_via="$1"
    local legacy_path="$2"
    if [ -n "${_INDAGIS_LEGACY_ALIAS_WARNED:-}" ]; then
        return 0
    fi
    _INDAGIS_LEGACY_ALIAS_WARNED=1

    local migrate_cmd
    case "$(uname -s 2>/dev/null || echo unknown)" in
        MINGW*|MSYS*|CYGWIN*)
            migrate_cmd='move %LOCALAPPDATA%\hermes %LOCALAPPDATA%\indagis'
            ;;
        *)
            migrate_cmd='mv ~/.hermes ~/.indagis'
            ;;
    esac

    # All output goes to stderr (>&2).
    {
        printf '\n⚠ Indagis Agent: %s (%s) is used as a fallback.\n' "$resolved_via" "$legacy_path" >&2
        printf '  The deprecation alias will be removed in a future Indagis Agent release.\n' >&2
        printf '  Migrate by running:\n' >&2
        printf '    %s\n' "$migrate_cmd" >&2
        printf '  Then re-source your shell or restart the desktop app.\n' >&2
    }
}

# Applies the 5-priority resolution ladder for the Indagis home directory.
#
# Order:
#   P1: $INDAGIS_HOME env var         → path              [no warning]
#   P2: ~/.indagis exists             → path              [no warning]
#   P3: $HERMES_HOME env var          → legacy path       [WARNING on stderr]
#   P4: ~/.hermes exists              → legacy path       [WARNING on stderr]
#   P5: ~/.indagis                    → default (create)  [no warning]
#
# OUTPUT CHANNEL CONTRACT:
#   - stdout: the resolved path (single line, no trailing garbage).
#   - stderr: warnings only (legacy alias deprecation).
#   Callers MUST capture the result via $(resolve_indagis_home) and rely
#   on stderr going to the user's terminal independently.
resolve_indagis_home() {
    # P1: explicit INDAGIS_HOME env var.
    if [ -n "${INDAGIS_HOME:-}" ]; then
        printf '%s\n' "$INDAGIS_HOME"
        return 0
    fi

    local default_path
    default_path="$(indagis_platform_default_home)"

    # P2: ~/.indagis exists on disk.
    if [ -d "$default_path" ]; then
        printf '%s\n' "$default_path"
        return 0
    fi

    # P3: HERMES_HOME env var (legacy alias, WARNING on stderr).
    if [ -n "${HERMES_HOME:-}" ]; then
        _indagis_warn_legacy_alias_in_use_once "HERMES_HOME" "$HERMES_HOME"
        printf '%s\n' "$HERMES_HOME"
        return 0
    fi

    # P4: ~/.hermes exists (legacy alias, WARNING on stderr).
    local legacy_path
    legacy_path="$(indagis_legacy_alias_home)"
    if [ -n "$legacy_path" ]; then
        _indagis_warn_legacy_alias_in_use_once "~/.hermes" "$legacy_path"
        printf '%s\n' "$legacy_path"
        return 0
    fi

    # P5: fall back to the default path (will be created on first use).
    printf '%s\n' "$default_path"
}
