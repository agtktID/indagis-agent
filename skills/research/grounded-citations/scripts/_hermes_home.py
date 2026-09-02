"""Resolve INDAGIS_HOME for standalone skill scripts.

Skill scripts may run outside the Hermes process (system Python, nix env,
CI) where ``hermes_constants`` is not importable.  This module provides the
same ``get_indagis_home()`` contract without requiring it on ``sys.path``.

When ``hermes_constants`` IS available it is used directly so profile
resolution and any future enhancements are picked up automatically.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from hermes_constants import get_indagis_home as get_indagis_home
except (ModuleNotFoundError, ImportError):

    def get_indagis_home() -> Path:
        """Return the Hermes home directory.

        Mirrors ``hermes_constants.get_indagis_home()``'s resolution order:
        ``INDAGIS_HOME`` env -> ``~/.indagis`` (if present) -> ``HERMES_HOME``
        env (legacy alias) -> ``~/.hermes`` (if present, legacy alias) ->
        ``~/.indagis`` default.
        """
        val = os.environ.get("INDAGIS_HOME", "").strip()
        if val:
            return Path(val)
        default = Path.home() / ".indagis"
        if default.exists():
            return default
        legacy_env = os.environ.get("HERMES_HOME", "").strip()
        if legacy_env:
            return Path(legacy_env)
        legacy_default = Path.home() / ".hermes"
        if legacy_default.exists():
            return legacy_default
        return default
