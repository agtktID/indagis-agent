"""
Loader for G0DM0D3 scripts. Handles the exec-scoping issues.

Usage in execute_code:
    exec(open(os.path.expanduser(
        os.path.join(os.environ.get("INDAGIS_HOME") or (os.path.expanduser("~/.indagis") if os.path.isdir(os.path.expanduser("~/.indagis")) else os.path.expanduser("~/.hermes")), "skills/red-teaming/godmode/scripts/load_godmode.py")
    )).read())
    
    # Now all functions are available:
    # - auto_jailbreak(), undo_jailbreak()
    # - race_models(), race_godmode_classic()
    # - generate_variants(), obfuscate_query(), detect_triggers()
    # - score_response(), is_refusal(), count_hedges()
    # - escalate_encoding()
"""

import os, sys
from pathlib import Path


def _gm_resolve_indagis_home() -> Path:
    """Mirrors hermes_constants.get_indagis_home()'s priority order.

    Standalone script (no import path to hermes_constants): INDAGIS_HOME env
    -> ~/.indagis (if present) -> HERMES_HOME env (legacy alias) -> ~/.hermes
    (if present, legacy alias) -> ~/.indagis default.
    """
    val = os.getenv("INDAGIS_HOME", "").strip()
    if val:
        return Path(val)
    default = Path.home() / ".indagis"
    if default.exists():
        return default
    legacy_env = os.getenv("HERMES_HOME", "").strip()
    if legacy_env:
        return Path(legacy_env)
    legacy_default = Path.home() / ".hermes"
    if legacy_default.exists():
        return legacy_default
    return default


_gm_scripts_dir = _gm_resolve_indagis_home() / "skills" / "red-teaming" / "godmode" / "scripts"

_gm_old_argv = sys.argv
sys.argv = ["_godmode_loader"]

def _gm_load(path):
    ns = dict(globals())
    ns["__name__"] = "_godmode_module"
    ns["__file__"] = str(path)
    exec(compile(open(path).read(), str(path), 'exec'), ns)
    return ns

for _gm_script in ["parseltongue.py", "godmode_race.py", "auto_jailbreak.py"]:
    _gm_path = _gm_scripts_dir / _gm_script
    if _gm_path.exists():
        _gm_ns = _gm_load(_gm_path)
        for _gm_k, _gm_v in _gm_ns.items():
            if not _gm_k.startswith('_gm_') and (callable(_gm_v) or _gm_k.isupper()):
                globals()[_gm_k] = _gm_v

sys.argv = _gm_old_argv

# Cleanup loader vars
for _gm_cleanup in ['_gm_scripts_dir', '_gm_old_argv', '_gm_load', '_gm_ns', '_gm_k',
                     '_gm_v', '_gm_script', '_gm_path', '_gm_cleanup',
                     '_gm_resolve_indagis_home']:
    globals().pop(_gm_cleanup, None)
