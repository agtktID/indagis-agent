"""Runs test_install_sh_curl_pipe.sh under pytest.

WHY A WRAPPER. The bash harness next to this file is the real test; this
exists only so CI actually runs it. The `installer` CI lane is Windows-only
by construction — scripts/ci/classify_changes.py watches
``scripts/install.ps1``, ``scripts/install.cmd`` and ``scripts/tests/``, and
``installer-tests.yml`` runs PowerShell — so a diff touching *only*
``scripts/install.sh`` classifies as ``installer=false`` and the shell
harness would never execute. A regression test nothing runs is not a
regression test, and this defect has already come back once.

pytest's ``testpaths = ["tests"]`` collects this file, so the harness rides
the Python lane instead, which runs on every pull request.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

_HARNESS = Path(__file__).with_suffix(".sh")


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
def test_install_sh_survives_curl_pipe_bash():
    assert _HARNESS.is_file(), f"missing harness: {_HARNESS}"

    proc = subprocess.run(
        ["bash", str(_HARNESS)],
        capture_output=True,
        text=True,
        timeout=300,
    )
    # The harness prints its own per-assertion PASS/FAIL/SKIP lines, so on
    # failure the report is more useful than any message assembled here.
    assert proc.returncode == 0, (
        f"{_HARNESS.name} failed (exit {proc.returncode})\n"
        f"--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"
    )
