"""The dashboard's git review endpoints must not let a revision become an option.

WHY THIS EXISTS. ``/api/git/review/diff`` and ``/api/git/review/list`` take a
``base`` query parameter and passed it straight into git's argument list in
revision position:

    _git_out(cwd, ["diff", base_ref, "--", file_path])

git reads a leading-dash argument there as an OPTION. ``git diff --output=PATH``
writes the diff to PATH and exits 0, so a read-only review endpoint became an
arbitrary file write anywhere the server process could reach. ``rev-parse``'s
``ref`` parameter had the same unguarded shape.

The first test below fails against the unfixed module — it writes the file. That
is the point: a test for an injection that cannot reproduce the injection proves
nothing.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from hermes_cli import web_git


def _run(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A tiny repo with one committed file and an uncommitted edit to it."""
    work = tmp_path / "repo"
    work.mkdir()
    _run(work, "init", "-q", ".")
    _run(work, "config", "user.email", "t@example.invalid")
    _run(work, "config", "user.name", "t")
    (work / "f.txt").write_text("original\n")
    _run(work, "add", "f.txt")
    _run(work, "commit", "-qm", "init")
    # A second ref, so ``--all`` returns more than one line and is a real
    # discriminator below — with a single ref it equals HEAD and the test would
    # pass whether or not the guard existed.
    _run(work, "branch", "side")
    (work / "f.txt").write_text("modified\n")
    return work


# ── the injection itself ─────────────────────────────────────────────────────


def test_review_diff_base_cannot_write_an_arbitrary_file(
    repo: Path, tmp_path: Path
) -> None:
    target = tmp_path / "PWNED"
    web_git.review_diff(str(repo), "f.txt", "lastTurn", f"--output={target}", False)
    assert not target.exists(), (
        f"`base` reached git as an option: it wrote {target}. "
        "A revision in argument position must be rejected or fenced."
    )


def test_review_list_base_cannot_write_an_arbitrary_file(
    repo: Path, tmp_path: Path
) -> None:
    target = tmp_path / "PWNED_LIST"
    web_git.review_list(str(repo), "lastTurn", f"--output={target}")
    assert not target.exists(), f"`base` reached git as an option: it wrote {target}"


@pytest.mark.parametrize("hostile", ["--git-dir", "--all", "--show-toplevel"])
def test_rev_parse_ref_cannot_change_the_question(repo: Path, hostile: str) -> None:
    """rev-parse is a weaker case than diff, and saying so precisely matters:
    ``git rev-parse --output=X`` writes nothing, it just echoes the string. So
    this is not the arbitrary write the diff endpoints had. It is still argument
    injection with disclosure — ``--git-dir`` answers with a filesystem path and
    ``--all`` dumps every ref — i.e. the endpoint answers a question the caller
    never asked. The guard costs nothing, so it is applied here too."""
    head = web_git.review_rev_parse(str(repo), "HEAD")
    assert web_git.review_rev_parse(str(repo), hostile) == head


@pytest.mark.parametrize(
    "hostile",
    [
        "--output=/tmp/x",
        "-o/tmp/x",
        "--exit-code",
        "-",
    ],
)
def test_option_shaped_revisions_are_refused(hostile: str) -> None:
    assert web_git._safe_rev(hostile) is None


# ── and the fix must not break legitimate use ────────────────────────────────


@pytest.mark.parametrize(
    "rev",
    ["HEAD", "HEAD~0", "main", "origin/main", "abc123", "v1.0", "HEAD^{commit}"],
)
def test_real_revisions_survive_the_guard(rev: str) -> None:
    """The guard rejects a *shape*, not a vocabulary — no revision syntax starts
    with a dash, so nothing legitimate is lost. A sanitiser that stripped
    characters would silently turn ``HEAD~3`` into ``HEAD3`` and diff the wrong
    thing; this one either passes the value through untouched or refuses it."""
    assert web_git._safe_rev(rev) == rev


def test_review_diff_still_diffs_against_a_real_base(repo: Path) -> None:
    out = web_git.review_diff(str(repo), "f.txt", "lastTurn", "HEAD", False)
    assert "-original" in out and "+modified" in out


def test_review_list_still_lists_against_a_real_base(repo: Path) -> None:
    result = web_git.review_list(str(repo), "lastTurn", "HEAD")
    assert result["base"] == "HEAD"
    assert [f["path"] for f in result["files"]] == ["f.txt"]


def test_rev_parse_returns_a_sha_not_the_sentinel(repo: Path) -> None:
    """``--end-of-options`` is deliberately absent from rev-parse: it echoes the
    sentinel on stdout, so passing it would make that the returned value."""
    sha = web_git.review_rev_parse(str(repo), "HEAD")
    assert sha is not None
    assert len(sha) == 40 and all(c in "0123456789abcdef" for c in sha)


def test_rev_parse_falls_back_to_head_when_ref_is_refused(repo: Path) -> None:
    """A refused ref must not silently resolve to something else — it takes the
    same path as no ref at all."""
    assert web_git.review_rev_parse(
        str(repo), "--output=/tmp/x"
    ) == web_git.review_rev_parse(str(repo), None)
