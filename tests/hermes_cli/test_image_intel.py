"""Tests for hermes_cli/image_intel.py and hermes_cli/image_cmd.py — Image Intel.

The fixtures build real JPEGs with real EXIF rather than mocking Pillow: the
whole point of the module is that it reads what a camera actually wrote, and a
mocked IFD would prove nothing about the DMS→decimal conversion or the sub-IFD
merge that the real tags exercise.
"""

import json

import pytest

from hermes_cli import image_cmd, image_intel

PIL = pytest.importorskip("PIL", reason="Pillow is a core dependency; skip only where it is absent")


def _build_image(path, *, gps=True, device=True, taken="2021:06:14 11:32:07"):
    """Write a JPEG carrying the metadata an OSINT analyst looks for.

    Coordinates are the Eiffel Tower (48°51'29.6"N 2°17'40.2"E) so the
    conversion has a known-correct expected value rather than a round number
    that a broken DMS formula could produce by accident.
    """
    from PIL import Image
    from PIL.ExifTags import GPS, IFD, Base
    from PIL.TiffImagePlugin import IFDRational as R

    image = Image.new("RGB", (32, 24), (30, 90, 150))
    exif = Image.Exif()

    if device:
        exif[Base.Make] = "NIKON CORPORATION"
        exif[Base.Model] = "NIKON D850"
        exif[Base.Software] = "Adobe Photoshop 25.0 (Windows)"
        sub = exif.get_ifd(IFD.Exif)
        sub[Base.BodySerialNumber] = "3018842"
        sub[Base.LensModel] = "24.0-70.0 mm f/2.8"
        if taken:
            sub[Base.DateTimeOriginal] = taken

    if gps:
        gps_ifd = exif.get_ifd(IFD.GPSInfo)
        gps_ifd[GPS.GPSLatitudeRef] = "N"
        gps_ifd[GPS.GPSLatitude] = (R(48, 1), R(51, 1), R(296, 10))
        gps_ifd[GPS.GPSLongitudeRef] = "E"
        gps_ifd[GPS.GPSLongitude] = (R(2, 1), R(17, 1), R(402, 10))
        gps_ifd[GPS.GPSAltitudeRef] = b"\x00"
        gps_ifd[GPS.GPSAltitude] = R(330, 1)
        gps_ifd[GPS.GPSDateStamp] = "2021:06:14"

    image.save(path, exif=exif)
    return path


class TestDmsConversion:
    def test_north_east_is_positive(self):
        assert image_intel._dms_to_degrees((48, 51, 29.6), "N") == pytest.approx(48.8582222, abs=1e-6)

    def test_south_and_west_are_negated(self):
        assert image_intel._dms_to_degrees((33, 51, 54.0), "S") == pytest.approx(-33.865, abs=1e-6)
        assert image_intel._dms_to_degrees((70, 40, 0.0), "W") == pytest.approx(-70.66667, abs=1e-4)

    def test_rational_tuples_are_accepted(self):
        assert image_intel._dms_to_degrees(((48, 1), (51, 1), (296, 10)), "N") == pytest.approx(
            48.8582222, abs=1e-6
        )

    @pytest.mark.parametrize("bad", [None, (), (1, 2), "not-a-coordinate", (1, 2, "x")])
    def test_malformed_input_returns_none_rather_than_guessing(self, bad):
        # A wrong coordinate is worse than no coordinate — it sends an analyst
        # to the wrong place with full confidence.
        assert image_intel._dms_to_degrees(bad, "N") is None


class TestInspectImage:
    def test_extracts_gps_device_and_hash(self, tmp_path):
        path = _build_image(tmp_path / "photo.jpg")
        report = image_intel.inspect_image(str(path))

        assert report["has_exif"] is True
        assert len(report["sha256"]) == 64
        assert report["gps"]["latitude"] == pytest.approx(48.8582222, abs=1e-6)
        assert report["gps"]["longitude"] == pytest.approx(2.2945, abs=1e-6)
        assert report["gps"]["altitude_m"] == pytest.approx(330.0)
        assert "openstreetmap.org" in report["gps"]["map_url"]
        assert report["device"]["Model"] == "NIKON D850"
        assert report["software"]["Software"].startswith("Adobe Photoshop")

    def test_serial_numbers_are_promoted_to_a_fingerprint(self, tmp_path):
        # Serials are what tie two photographs to one physical camera, so they
        # must not stay buried in the general tag pile.
        path = _build_image(tmp_path / "photo.jpg")
        report = image_intel.inspect_image(str(path))
        assert report["device_fingerprint"]["BodySerialNumber"] == "3018842"

    def test_sub_ifd_tags_are_merged(self, tmp_path):
        # LensModel and DateTimeOriginal live in the Exif sub-IFD, not the top
        # level; forgetting the merge silently loses the capture time.
        path = _build_image(tmp_path / "photo.jpg")
        report = image_intel.inspect_image(str(path))
        assert report["timestamps"]["DateTimeOriginal"] == "2021:06:14 11:32:07"
        assert report["device"]["LensModel"].startswith("24.0-70.0")

    def test_image_without_exif_is_not_an_error(self, tmp_path):
        from PIL import Image

        path = tmp_path / "bare.png"
        Image.new("RGB", (8, 8)).save(path)
        report = image_intel.inspect_image(str(path))
        assert report["has_exif"] is False
        assert report["gps"] == {}
        assert len(report["sha256"]) == 64

    def test_non_image_file_reports_rather_than_raises(self, tmp_path):
        path = tmp_path / "notes.txt"
        path.write_text("this is not a picture", encoding="utf-8")
        report = image_intel.inspect_image(str(path))
        assert "error" in report
        assert len(report["sha256"]) == 64  # the hash is still useful

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            image_intel.inspect_image(str(tmp_path / "nope.jpg"))

    def test_timestamp_gap_is_flagged_without_being_called_tampering(self, tmp_path):
        import os

        path = _build_image(tmp_path / "photo.jpg")
        os.utime(path, (1_700_000_000, 1_700_000_000))  # ~2023, EXIF says 2021
        report = image_intel.inspect_image(str(path))

        gap = report["timestamp_discrepancy"]
        assert gap["delta_hours"] > 48
        assert "not evidence of tampering" in gap["note"]

    def test_matching_timestamps_produce_no_gap(self, tmp_path):
        import calendar
        import os
        import time

        path = _build_image(tmp_path / "photo.jpg")
        exif_epoch = calendar.timegm(time.strptime("2021:06:14 11:32:07", "%Y:%m:%d %H:%M:%S"))
        os.utime(path, (exif_epoch, exif_epoch))
        assert "timestamp_discrepancy" not in image_intel.inspect_image(str(path))


class TestScrubImage:
    def test_removes_metadata_and_leaves_the_original_intact(self, tmp_path):
        source = _build_image(tmp_path / "photo.jpg")
        out = tmp_path / "clean.jpg"

        result = image_intel.scrub_image(str(source), str(out))

        assert result["had_gps"] is True
        assert result["removed_tags"] > 0
        assert result["remaining_tags"] == 0
        assert image_intel.inspect_image(str(out))["gps"] == {}
        # Evidence is immutable in this codebase — the source keeps its GPS.
        assert image_intel.inspect_image(str(source))["gps"]["latitude"] > 0

    def test_refuses_to_overwrite(self, tmp_path):
        source = _build_image(tmp_path / "photo.jpg")
        out = tmp_path / "clean.jpg"
        out.write_bytes(b"already here")
        with pytest.raises(FileExistsError):
            image_intel.scrub_image(str(source), str(out))
        assert out.read_bytes() == b"already here"

    def test_missing_source_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            image_intel.scrub_image(str(tmp_path / "nope.jpg"), str(tmp_path / "out.jpg"))

    def test_palette_image_keeps_its_colours(self, tmp_path):
        # A palette is pixel data, not metadata: scrubbing must not repaint
        # the picture grey.
        from PIL import Image

        source = tmp_path / "flag.png"
        Image.new("RGB", (8, 8), (200, 40, 60)).convert("P", palette=Image.ADAPTIVE).save(source)

        image_intel.scrub_image(str(source), str(tmp_path / "clean.png"))

        with Image.open(tmp_path / "clean.png") as cleaned:
            assert cleaned.convert("RGB").getpixel((0, 0)) == pytest.approx((200, 40, 60), abs=8)


class TestEvidenceEntries:
    def test_gps_becomes_its_own_geo_indicator(self, tmp_path):
        report = image_intel.inspect_image(str(_build_image(tmp_path / "photo.jpg")))
        entries = image_intel.to_evidence_entries(report)

        assert [e["ioc_type"] for e in entries] == ["FILE_HASH", "GEO"]
        assert entries[1]["content"] == f"{report['gps']['latitude']},{report['gps']['longitude']}"

    def test_no_gps_means_one_entry(self, tmp_path):
        report = image_intel.inspect_image(str(_build_image(tmp_path / "photo.jpg", gps=False)))
        assert len(image_intel.to_evidence_entries(report)) == 1


class TestAppendToStore:
    def _store(self, tmp_path, **extra):
        store = tmp_path / "case.json"
        store.write_text(json.dumps({"evidence": [], "chain_of_custody": [], **extra}), encoding="utf-8")
        return store

    def test_appends_entries_and_custody_events(self, tmp_path):
        store = self._store(tmp_path)
        report = image_intel.inspect_image(str(_build_image(tmp_path / "photo.jpg")))

        new_ids = image_intel.append_to_store(str(store), report)
        data = json.loads(store.read_text(encoding="utf-8"))

        assert new_ids == ["ev-001", "ev-002"]
        assert len(data["evidence"]) == 2
        assert [c["source"] for c in data["chain_of_custody"]] == ["indagis image", "indagis image"]

    def test_content_hash_matches_what_dossier_re_checks(self, tmp_path):
        # dossier's integrity check recomputes sha256(content); if this field
        # were the file hash instead, every image entry would show as tampered.
        import hashlib

        store = self._store(tmp_path)
        report = image_intel.inspect_image(str(_build_image(tmp_path / "photo.jpg")))
        image_intel.append_to_store(str(store), report)

        for entry in json.loads(store.read_text(encoding="utf-8"))["evidence"]:
            expected = hashlib.sha256(entry["content"].encode("utf-8")).hexdigest()
            assert entry["content_sha256"] == expected

    def test_existing_entries_are_preserved_and_ids_continue(self, tmp_path):
        store = tmp_path / "case.json"
        store.write_text(
            json.dumps({"evidence": [{"id": "ev-001", "content": "earlier"}], "chain_of_custody": []}),
            encoding="utf-8",
        )
        report = image_intel.inspect_image(str(_build_image(tmp_path / "photo.jpg")))

        assert image_intel.append_to_store(str(store), report) == ["ev-002", "ev-003"]
        data = json.loads(store.read_text(encoding="utf-8"))
        assert data["evidence"][0]["content"] == "earlier"

    def test_missing_store_raises(self, tmp_path):
        report = image_intel.inspect_image(str(_build_image(tmp_path / "photo.jpg")))
        with pytest.raises(FileNotFoundError):
            image_intel.append_to_store(str(tmp_path / "nope.json"), report)

    def test_non_evidence_json_raises(self, tmp_path):
        store = tmp_path / "other.json"
        store.write_text('{"something": "else"}', encoding="utf-8")
        report = image_intel.inspect_image(str(_build_image(tmp_path / "photo.jpg")))
        with pytest.raises(ValueError):
            image_intel.append_to_store(str(store), report)


class TestImageCommand:
    """The CLI layer — dispatch and output, driven the way argparse drives it."""

    class _Args:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    def test_inspect_prints_the_headline_facts(self, tmp_path, capsys):
        path = _build_image(tmp_path / "photo.jpg")
        image_cmd.image_command(self._Args(image_command="inspect", path=str(path), json=False, evidence=None))
        out = capsys.readouterr().out
        assert "NIKON D850" in out
        assert "48.8582222" in out
        assert "openstreetmap.org" in out

    def test_inspect_json_is_parseable(self, tmp_path, capsys):
        path = _build_image(tmp_path / "photo.jpg")
        image_cmd.image_command(self._Args(image_command="inspect", path=str(path), json=True, evidence=None))
        report = json.loads(capsys.readouterr().out)
        assert report["device"]["Make"] == "NIKON CORPORATION"

    def test_inspect_with_evidence_appends_and_says_so(self, tmp_path, capsys):
        path = _build_image(tmp_path / "photo.jpg")
        store = tmp_path / "case.json"
        store.write_text('{"evidence": [], "chain_of_custody": []}', encoding="utf-8")

        image_cmd.image_command(
            self._Args(image_command="inspect", path=str(path), json=False, evidence=str(store))
        )
        out = capsys.readouterr().out
        assert "ev-001" in out
        assert "custody sign" in out  # the digest changed; the user must re-sign
        assert len(json.loads(store.read_text(encoding="utf-8"))["evidence"]) == 2

    def test_gps_without_coordinates_says_so_quietly(self, tmp_path, capsys):
        path = _build_image(tmp_path / "photo.jpg", gps=False)
        image_cmd.image_command(self._Args(image_command="gps", path=str(path), json=False))
        assert "No GPS coordinates" in capsys.readouterr().out

    def test_scrub_reports_what_it_removed(self, tmp_path, capsys):
        path = _build_image(tmp_path / "photo.jpg")
        image_cmd.image_command(
            self._Args(image_command="scrub", path=str(path), out=str(tmp_path / "clean.jpg"))
        )
        out = capsys.readouterr().out
        assert "metadata-free copy" in out
        assert "Tags remaining" in out
        assert out.split("Tags remaining")[1].split("\n")[0].strip() == "0"

    def test_missing_file_is_a_message_not_a_traceback(self, tmp_path, capsys):
        image_cmd.image_command(
            self._Args(image_command="inspect", path=str(tmp_path / "nope.jpg"), json=False, evidence=None)
        )
        assert "No such file" in capsys.readouterr().err

    def test_unknown_subcommand_prints_usage(self, capsys):
        image_cmd.image_command(self._Args(image_command=None))
        assert "indagis image" in capsys.readouterr().err


class TestParserWiring:
    """The command must exist as argparse actually builds it — the check that
    caught a documented 'airgap engage' verb that was never implemented."""

    def test_image_subcommands_parse(self):
        import argparse

        from hermes_cli.subcommands.image import build_image_parser

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        build_image_parser(subparsers, cmd_image=lambda args: None)

        args = parser.parse_args(["image", "inspect", "p.jpg", "--json", "--evidence", "c.json"])
        assert (args.image_command, args.path, args.json, args.evidence) == ("inspect", "p.jpg", True, "c.json")

        args = parser.parse_args(["image", "gps", "p.jpg"])
        assert (args.image_command, args.json) == ("gps", False)

        args = parser.parse_args(["image", "scrub", "p.jpg", "--out", "clean.jpg"])
        assert (args.image_command, args.out) == ("scrub", "clean.jpg")

    def test_scrub_requires_an_output_path(self):
        import argparse

        from hermes_cli.subcommands.image import build_image_parser

        parser = argparse.ArgumentParser()
        build_image_parser(parser.add_subparsers(dest="command"), cmd_image=lambda args: None)
        with pytest.raises(SystemExit):
            parser.parse_args(["image", "scrub", "p.jpg"])

    def test_image_is_a_known_builtin_subcommand(self):
        # Missing from this set, the command still works but pays a plugin
        # discovery pass on every invocation.
        from hermes_cli.main import _BUILTIN_SUBCOMMANDS

        assert "image" in _BUILTIN_SUBCOMMANDS
