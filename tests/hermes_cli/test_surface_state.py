"""Tests for hermes_cli/surface_state.py — snapshot storage."""

from hermes_cli.surface_state import (
    latest_two_snapshots,
    list_snapshots,
    list_targets,
    load_snapshot,
    save_snapshot,
)


class TestSaveAndListSnapshots:
    def test_save_creates_file_and_stamps_target(self):
        path = save_snapshot("pypi", {"host": "pypi.org", "ips": ["1.2.3.4"]})
        assert path.exists()
        data = load_snapshot(path)
        assert data["target"] == "pypi"
        assert "taken_at" in data

    def test_list_snapshots_sorted_chronologically(self):
        save_snapshot("pypi", {"host": "pypi.org"})
        save_snapshot("pypi", {"host": "pypi.org"})
        paths = list_snapshots("pypi")
        assert len(paths) == 2
        assert paths == sorted(paths)

    def test_unsafe_target_name_cannot_escape_the_surface_dir(self):
        """'..' survives as a substring inside the sanitized name, but with
        every '/' replaced it's one flat directory component — not a path
        traversal, since there's no separator left for '..' to act on."""
        path = save_snapshot("../../etc/passwd", {"host": "x"})
        assert "/" not in path.parent.name
        assert path.parent.parent.name == "surface"


class TestLatestTwoSnapshots:
    def test_none_with_fewer_than_two(self):
        assert latest_two_snapshots("nope") is None
        save_snapshot("pypi", {"host": "pypi.org"})
        assert latest_two_snapshots("pypi") is None

    def test_returns_older_then_newer(self):
        save_snapshot("pypi", {"host": "pypi.org", "marker": "first"})
        save_snapshot("pypi", {"host": "pypi.org", "marker": "second"})
        pair = latest_two_snapshots("pypi")
        assert pair[0]["marker"] == "first"
        assert pair[1]["marker"] == "second"


class TestLoadSnapshot:
    def test_corrupted_file_returns_none(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("not json{{{", encoding="utf-8")
        assert load_snapshot(bad) is None


class TestListTargets:
    def test_empty(self):
        assert list_targets() == []

    def test_lists_all_target_dirs(self):
        save_snapshot("pypi", {"host": "pypi.org"})
        save_snapshot("github", {"host": "github.com"})
        assert set(list_targets()) == {"pypi", "github"}
