"""Keeps the native-Windows guide honest about the install it documents.

WHY THIS WAS REWRITTEN. The previous version was named
``..._docs_match_installer`` but compared nothing: it asserted two hardcoded
literals — the pre-rename ``%LOCALAPPDATA%\\hermes`` path and a
``Get-Command hermes … hermes.exe`` line — against the doc. Both were wrong,
and the test passed because the doc and the expectation were stale together.
It pinned the defect in place instead of catching it: the guide told Windows
users to run a `hermes` binary that [project.scripts] does not define.

So each assertion below now derives its expectation from the source it
claims to check, and fails if the doc and that source ever diverge again.
"""

import re
import tomllib
from pathlib import Path

_DOC = Path("website/docs/user-guide/windows-native.md")
_INSTALL = Path("scripts/install.ps1")
_PYPROJECT = Path("pyproject.toml")


def test_guide_only_names_console_scripts_that_exist() -> None:
    """The guide's verification steps must invoke a binary that is built."""
    scripts = set(tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))["project"]["scripts"])
    assert "indagis" in scripts, "pyproject no longer defines the `indagis` entry point"

    doc = _DOC.read_text(encoding="utf-8")
    # Only invocation shapes are forbidden. The word itself still appears
    # legitimately: `%LOCALAPPDATA%\\hermes` as the documented upgrade
    # fallback, `~/.hermes` as an alternate data dir, and the HERMES_HOME
    # variable name — none of those claim a binary exists.
    forbidden = [
        "hermes.exe",       # never built; [project.scripts] has no `hermes`
        "hermes.cmd",       # no such shim is created anywhere in the repo
        "Get-Command hermes",
        "`hermes` command",
    ]
    named = [f for f in forbidden if f in doc]
    assert not named, (
        f"the guide names {named}, but [project.scripts] defines {sorted(scripts)} "
        "and the installer resolves venv\\Scripts\\indagis.exe"
    )


def test_guide_documents_the_path_the_installer_defaults_to() -> None:
    """install.ps1 resolves %LOCALAPPDATA%\\indagis for a fresh install."""
    install = _INSTALL.read_text(encoding="utf-8")
    assert "Join-Path $env:LOCALAPPDATA 'indagis'" in install, (
        "Get-IndagisPlatformDefaultHome no longer joins 'indagis' — "
        "if the default moved, this test and the guide both need updating"
    )

    doc = _DOC.read_text(encoding="utf-8")
    assert "%LOCALAPPDATA%\\indagis\\hermes-agent\\venv\\Scripts" in doc
    # The legacy path may still be mentioned, but only as the documented
    # fallback for an upgrade — never as where a fresh install goes.
    assert "%LOCALAPPDATA%\\hermes\\hermes-agent" not in doc


def test_installer_still_exposes_the_venv_scripts_dir() -> None:
    """Carried over from the original test: the PATH entry the guide promises."""
    assert '$hermesBin = "$InstallDir\\venv\\Scripts"' in _INSTALL.read_text(encoding="utf-8")
