"""``find_provider_dir`` must not walk out of the plugin tree.

WHY THIS EXISTS. Both provider registries resolved a name by joining it onto a
base directory:

    bundled = _MEMORY_PLUGINS_DIR / name

``Path.__truediv__`` walks happily: ``dir / "../../etc"`` is ``dir/../../etc``,
and ``is_dir()`` follows it straight out of the tree. Verified before the fix —
``find_provider_dir("../../../../../tmp/…")`` returned a path outside the
package.

That was NOT remotely exploitable: every HTTP route reaching it validates the
name against a strict charset first, and ``_require_valid_memory_provider_name``
in web_server.py says so in its own docstring. But the containment lived at the
boundary rather than in the function, and the function has seven callers. A
future caller that forgets the boundary check silently reopens the traversal —
and what it opens onto is a plugin manifest whose ``install`` command runs
through ``shell=True``.

So these tests pin the function's own behaviour, independent of who calls it.
"""

from __future__ import annotations

import pytest

from plugins.cron_providers import find_provider_dir as cron_find
from plugins.memory import find_provider_dir as memory_find

_FINDERS = pytest.mark.parametrize(
    "find", [memory_find, cron_find], ids=["memory", "cron_providers"]
)


@_FINDERS
@pytest.mark.parametrize(
    "hostile",
    ["..", ".", "a/b", "/etc", "", "../plugins", "./x"],
)
def test_a_name_that_is_not_one_plain_directory_is_refused(find, hostile: str) -> None:
    """Shape check. Most of these would return None even unguarded simply because
    nothing is there — which is why the test below exists and this one is not
    trusted on its own."""
    assert find(hostile) is None, (
        f"{hostile!r} resolved to a directory — the name reached the filesystem "
        "as a path rather than as a single component"
    )


@_FINDERS
def test_traversal_is_refused_even_when_the_target_really_exists(
    find, tmp_path, monkeypatch
) -> None:
    """The one that actually proves it.

    A `..` name only returns None on a real defect-free lookup; it ALSO returns
    None when the traversed-to path happens not to exist or not to look like a
    provider. The parametrised test above is therefore satisfied by an absent
    target, and passed against the unguarded code for exactly that reason.

    So this one builds a genuine provider directory outside the plugin tree and
    aims a relative path straight at it. Without the guard the lookup walks out
    and returns it; with the guard it does not.
    """
    import plugins.memory as memory_mod
    import plugins.cron_providers as cron_mod

    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "__init__.py").write_text("")

    base = tmp_path / "plugins_root"
    base.mkdir()

    mod = memory_mod if find is memory_find else cron_mod
    attr = "_MEMORY_PLUGINS_DIR" if find is memory_find else "_CRON_PLUGINS_DIR"
    monkeypatch.setattr(mod, attr, base)
    monkeypatch.setattr(mod, "_get_user_plugins_dir", lambda: None)

    # Sanity: the target is genuinely reachable by walking up one level, so a
    # None result below cannot be blamed on a missing directory.
    assert (base / ".." / "outside" / "__init__.py").exists()

    assert find("../outside") is None, (
        "the lookup walked out of the plugin tree to a directory that really exists"
    )


@_FINDERS
def test_a_symlinked_name_is_still_allowed(find, tmp_path, monkeypatch) -> None:
    """The guard checks the NAME, not the resolved target, on purpose.

    A user-installed plugin under $INDAGIS_HOME/plugins/ may legitimately be a
    symlink to a working copy elsewhere — that is how someone develops one.
    Containment against the resolved path would have blocked that, so the fix
    deliberately does not do it. This test records the choice, so a later
    "hardening" that swaps in resolve()-and-contain has to notice what it breaks.
    """
    import plugins.memory as memory_mod
    import plugins.cron_providers as cron_mod

    real = tmp_path / "real_provider"
    real.mkdir()
    (real / "__init__.py").write_text("")

    user_plugins = tmp_path / "user_plugins"
    user_plugins.mkdir()
    (user_plugins / "linked").symlink_to(real, target_is_directory=True)

    mod = memory_mod if find is memory_find else cron_mod
    monkeypatch.setattr(mod, "_get_user_plugins_dir", lambda: user_plugins)
    # The bundled branch must miss so the user branch is the one under test.
    monkeypatch.setattr(mod, "_MEMORY_PLUGINS_DIR", tmp_path / "nope", raising=False)
    monkeypatch.setattr(mod, "_CRON_PLUGINS_DIR", tmp_path / "nope", raising=False)
    monkeypatch.setattr(mod, "_is_memory_provider_dir", lambda p: True, raising=False)
    monkeypatch.setattr(mod, "_is_cron_provider_dir", lambda p: True, raising=False)

    assert find("linked") is not None


def test_the_real_bundled_providers_still_resolve() -> None:
    """The guard rejects a shape, not a vocabulary. If it ever starts refusing
    the providers actually shipped in this repo, it has overreached."""
    from plugins.memory import list_memory_provider_names

    names = list_memory_provider_names()
    assert names, (
        "no bundled memory providers discovered — fixture problem, not a result"
    )
    for name in names:
        assert memory_find(name) is not None, (
            f"bundled provider {name!r} no longer resolves"
        )
