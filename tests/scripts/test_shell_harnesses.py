"""Runs the install-related bash harnesses in tests/scripts/ under pytest.

WHY THIS EXISTS. Three harnesses sat here referenced by nothing — no
workflow, no runner, no wrapper. The `installer` CI lane is Windows-only by
construction (scripts/ci/classify_changes.py watches scripts/install.ps1,
scripts/install.cmd and scripts/tests/, and installer-tests.yml runs
PowerShell), so nothing on Linux ever executed them. Between them they carry
46 assertions about home-directory resolution, launcher shims and the node
bootstrap, and not one had run.

pytest's ``testpaths = ["tests"]`` collects this file, so the harnesses ride
the Python lane, which runs on every pull request. Each gets its own test so
a failure names the harness rather than a single opaque "shell tests failed".

The harnesses print their own per-assertion PASS/FAIL/SKIP lines and exit
non-zero on failure; on a failure their output is attached verbatim, because
it says far more than any message assembled here. A harness may also exit 0
after printing SKIP when its preconditions are absent (no network, running
as root) — that is deliberate, and not something to fail the suite over.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

_HERE = Path(__file__).parent

#: Harnesses wrapped here. test_install_sh_curl_pipe.sh is absent on purpose:
#: it has had its own wrapper since the curl|bash fix.
_HARNESSES = [
    "test_install_helpers_home_resolution.sh",
    "test_install_sh_launcher_shims.sh",
    "test_node_bootstrap_home_resolution.sh",
]


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
@pytest.mark.parametrize("harness", _HARNESSES)
def test_shell_harness(harness: str) -> None:
    path = _HERE / harness
    assert path.is_file(), f"missing harness: {path}"

    proc = subprocess.run(
        ["bash", str(path)],
        capture_output=True,
        text=True,
        timeout=600,
        cwd=path.parents[2],
    )
    assert proc.returncode == 0, (
        f"{harness} failed (exit {proc.returncode})\n"
        f"--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"
    )
