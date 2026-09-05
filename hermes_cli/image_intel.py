"""Image Intel — metadata forensics on a picture.

The question an OSINT analyst asks of a photograph is rarely "what is in it"
— it is *where was this taken, when, and by which device*. Those three answers
live in EXIF, and they are what this module extracts.

Three findings carry most of the weight:

* **GPS** — a coordinate pair, when present, is the single highest-value
  field in the file.
* **Device fingerprint** — make, model and, when the camera writes them, the
  body and lens serial numbers. Serials are what tie *separate* photographs to
  the *same* physical device, which is a link no visual comparison gives you.
* **Timestamp disagreement** — EXIF ``DateTimeOriginal`` against the file's own
  mtime. They diverge for innocent reasons (a copy, an export) as often as
  guilty ones, so this module reports the discrepancy and refuses to call it
  tampering; that judgment is the analyst's.

Pillow does the EXIF decoding. It is already a core dependency of this project
(pinned in pyproject.toml for the vision tools), so nothing new is added, and
hand-rolling a TIFF IFD parser would only reintroduce the edge cases Pillow has
already absorbed.

Read-only: nothing here writes to the image. Metadata stripping is a separate,
explicit command that always writes to a NEW path.
"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Tags worth surfacing, in the order an analyst reads them. Everything else is
# still captured under ``all_tags`` — this list decides what gets a headline.
_DEVICE_TAGS = ("Make", "Model", "BodySerialNumber", "LensMake", "LensModel", "LensSerialNumber")
_SOFTWARE_TAGS = ("Software", "ProcessingSoftware", "HostComputer")
_TIME_TAGS = ("DateTimeOriginal", "DateTimeDigitized", "DateTime")


def _sha256_file(path: Path) -> str:
    """Hash the file itself, in chunks — an image can be large."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rational(value: Any) -> Optional[float]:
    """Coerce Pillow's IFDRational (and the raw (num, den) tuples older tags
    still carry) to a float, or None when it is neither."""
    try:
        if isinstance(value, tuple) and len(value) == 2:
            return float(value[0]) / float(value[1]) if value[1] else None
        return float(value)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def _dms_to_degrees(dms: Any, ref: Any) -> Optional[float]:
    """Convert EXIF degrees/minutes/seconds plus a hemisphere ref to a signed
    decimal degree. Returns None rather than guessing on malformed input —
    a wrong coordinate is worse than no coordinate."""
    try:
        degrees, minutes, seconds = (_rational(part) for part in dms)
    except (TypeError, ValueError):
        return None

    if degrees is None or minutes is None or seconds is None:
        return None

    value = degrees + minutes / 60 + seconds / 3600

    if isinstance(ref, str) and ref.upper() in ("S", "W"):
        value = -value

    return round(value, 7)


def _decode(value: Any) -> Any:
    """EXIF strings arrive as bytes often enough to be worth normalising, and
    trailing NULs are common. Undecodable bytes are reported as a hex preview
    rather than dropped — an unreadable tag is itself a signal."""
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8", "strict").rstrip("\x00").strip()
        except UnicodeDecodeError:
            return f"<{len(value)} bytes: {value[:16].hex()}…>"
    if isinstance(value, str):
        return value.rstrip("\x00").strip()
    return value


def _extract_gps(gps_ifd: Dict[str, Any]) -> Dict[str, Any]:
    """Pull a usable coordinate out of the GPS IFD."""
    lat = _dms_to_degrees(gps_ifd.get("GPSLatitude"), _decode(gps_ifd.get("GPSLatitudeRef")))
    lon = _dms_to_degrees(gps_ifd.get("GPSLongitude"), _decode(gps_ifd.get("GPSLongitudeRef")))

    if lat is None or lon is None:
        return {}

    out: Dict[str, Any] = {"latitude": lat, "longitude": lon}

    altitude = _rational(gps_ifd.get("GPSAltitude"))
    if altitude is not None:
        # Ref 1 means below sea level.
        below = str(_decode(gps_ifd.get("GPSAltitudeRef", 0))) in ("1", "b'\\x01'")
        out["altitude_m"] = round(-altitude if below else altitude, 2)

    stamp = _decode(gps_ifd.get("GPSDateStamp"))
    if stamp:
        out["gps_date"] = stamp

    # A link the analyst can open, rather than a coordinate they must paste.
    out["map_url"] = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=17/{lat}/{lon}"

    return out


def _read_exif(path: Path) -> Tuple[Dict[str, Any], Dict[str, Any], Optional[str]]:
    """Return (flat tag map, gps dict, error). Import is local so the module
    stays importable — and unit-testable — where Pillow is unavailable."""
    try:
        from PIL import ExifTags, Image
    except ImportError:  # pragma: no cover - Pillow is a core dependency
        return {}, {}, "Pillow is not installed"

    try:
        with Image.open(path) as image:
            exif = image.getexif()

            if not exif:
                return {}, {}, None

            tags = {ExifTags.TAGS.get(k, str(k)): _decode(v) for k, v in exif.items()}

            # The interesting fields (lens, serials, sub-second times) live in
            # the Exif sub-IFD, not the top level, so merge it in.
            try:
                for k, v in exif.get_ifd(ExifTags.IFD.Exif).items():
                    tags.setdefault(ExifTags.TAGS.get(k, str(k)), _decode(v))
            except (AttributeError, KeyError, ValueError):
                pass

            gps: Dict[str, Any] = {}
            try:
                raw_gps = exif.get_ifd(ExifTags.IFD.GPSInfo)
                if raw_gps:
                    gps = _extract_gps({ExifTags.GPSTAGS.get(k, str(k)): v for k, v in raw_gps.items()})
            except (AttributeError, KeyError, ValueError):
                pass

            return tags, gps, None
    except Exception as exc:  # noqa: BLE001 - a corrupt or non-image file is a finding, not a crash
        return {}, {}, f"{type(exc).__name__}: {exc}"


def _parse_exif_time(value: Any) -> Optional[datetime]:
    """EXIF times are 'YYYY:MM:DD HH:MM:SS', local to the camera and without a
    zone. Parsed naive and compared naively — see ``_timestamp_note``."""
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value.strip(), "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return None


def _timestamp_note(exif_time: Optional[datetime], mtime: datetime) -> Optional[Dict[str, Any]]:
    """Report an EXIF-vs-filesystem gap without interpreting it.

    EXIF carries no timezone, so any comparison against a UTC mtime is
    approximate by up to a day's worth of offset. A copied or exported file
    also legitimately carries a fresh mtime. So the threshold is deliberately
    loose and the wording deliberately neutral: this flags something to look
    at, never something to conclude from.
    """
    if exif_time is None:
        return None

    delta_hours = abs((mtime.replace(tzinfo=None) - exif_time).total_seconds()) / 3600

    if delta_hours < 48:
        return None

    return {
        "exif_taken": exif_time.isoformat(),
        "file_modified": mtime.isoformat(),
        "delta_hours": round(delta_hours, 1),
        "note": (
            "EXIF capture time and file mtime differ by more than two days. "
            "Copying, exporting or re-saving all do this — it is a prompt to "
            "check provenance, not evidence of tampering."
        ),
    }


def inspect_image(path: str) -> Dict[str, Any]:
    """Full metadata report for one image. Never modifies the file."""
    file_path = Path(path).expanduser()

    if not file_path.is_file():
        raise FileNotFoundError(f"No such file: {path}")

    stat = file_path.stat()
    mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)

    tags, gps, error = _read_exif(file_path)

    device = {k: tags[k] for k in _DEVICE_TAGS if tags.get(k)}
    software = {k: tags[k] for k in _SOFTWARE_TAGS if tags.get(k)}
    times = {k: tags[k] for k in _TIME_TAGS if tags.get(k)}

    report: Dict[str, Any] = {
        "path": str(file_path),
        "filename": file_path.name,
        "size_bytes": stat.st_size,
        # The same SHA-256 Custody Chain signs, so a dossier entry and a
        # signed export refer to the file by one identifier.
        "sha256": _sha256_file(file_path),
        "file_modified": mtime.isoformat(),
        "has_exif": bool(tags),
        "gps": gps,
        "device": device,
        "software": software,
        "timestamps": times,
        "all_tags": tags,
    }

    if error:
        report["error"] = error

    note = _timestamp_note(_parse_exif_time(times.get("DateTimeOriginal")), mtime)
    if note:
        report["timestamp_discrepancy"] = note

    # A serial number is the field that links two photographs to one physical
    # camera, so it is worth calling out rather than leaving in the pile.
    serials = {k: v for k, v in device.items() if "Serial" in k}
    if serials:
        report["device_fingerprint"] = serials

    return report


def scrub_image(path: str, out_path: str) -> Dict[str, Any]:
    """Write a copy with all metadata removed.

    The defensive half of the module: an investigator publishing a photograph
    should not ship their own camera serial or home coordinates with it.

    Always writes to a new path — silently overwriting the original would
    destroy evidence, and this codebase treats evidence as immutable.
    """
    from PIL import Image

    source = Path(path).expanduser()
    target = Path(out_path).expanduser()

    if not source.is_file():
        raise FileNotFoundError(f"No such file: {path}")

    if target.exists():
        raise FileExistsError(f"Refusing to overwrite {target}")

    before = inspect_image(str(source))

    with Image.open(source) as image:
        # Re-encoding from the raw pixel buffer is what actually drops the
        # metadata: copying the file and deleting tags leaves recoverable
        # remnants, and ``Image.copy()`` carries ``info`` across. ``frombytes``
        # builds a fresh image whose ``info`` starts empty.
        clean = Image.frombytes(image.mode, image.size, image.tobytes())
        if image.mode == "P" and image.palette is not None:
            # A palette is pixel data, not metadata — dropping it would change
            # the picture rather than clean it.
            clean.putpalette(image.palette)
        target.parent.mkdir(parents=True, exist_ok=True)
        clean.save(target)

    after = inspect_image(str(target))

    return {
        "source": str(source),
        "output": str(target),
        "removed_tags": len(before.get("all_tags", {})),
        "had_gps": bool(before.get("gps")),
        "remaining_tags": len(after.get("all_tags", {})),
        "output_sha256": after["sha256"],
    }


def to_evidence_entries(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Shape an inspection as evidence-store entries.

    Matches the schema ``evidence-store.py`` writes and ``indagis dossier``
    and ``indagis case`` already read, so an image lands in a case the same
    way any other artefact does. GPS becomes its own entry because a
    coordinate is an indicator in its own right — one that Case Memory can
    then correlate across investigations.
    """
    entries: List[Dict[str, Any]] = [
        {
            "type": "image_metadata",
            "source": report["filename"],
            "content": report["sha256"],
            "ioc_type": "FILE_HASH",
            "notes": _summarise(report),
        }
    ]

    gps = report.get("gps")
    if gps:
        entries.append(
            {
                "type": "ioc",
                "source": report["filename"],
                "content": f"{gps['latitude']},{gps['longitude']}",
                "ioc_type": "GEO",
                "notes": f"EXIF GPS from {report['filename']} · {gps['map_url']}",
            }
        )

    return entries


def _summarise(report: Dict[str, Any]) -> str:
    """One line an analyst can read in a dossier without opening the JSON."""
    bits: List[str] = []

    device = report.get("device", {})
    if device.get("Make") or device.get("Model"):
        bits.append(f"{device.get('Make', '')} {device.get('Model', '')}".strip())

    if report.get("device_fingerprint"):
        bits.append("serial present")

    times = report.get("timestamps", {})
    if times.get("DateTimeOriginal"):
        bits.append(f"taken {times['DateTimeOriginal']}")

    if report.get("gps"):
        bits.append("GPS present")

    if report.get("software"):
        bits.append(f"software: {next(iter(report['software'].values()))}")

    if report.get("timestamp_discrepancy"):
        bits.append("timestamp gap")

    return " · ".join(bits) if bits else "no EXIF metadata"


def append_to_store(store_path: str, report: Dict[str, Any]) -> List[str]:
    """Append an inspection to an existing evidence store, returning the new
    entry ids.

    Only ever appends, and only to a store that already exists — this command
    does not create cases, and it never rewrites an entry someone else wrote.
    """
    import json

    store = Path(store_path).expanduser()

    if not store.is_file():
        raise FileNotFoundError(f"No such evidence store: {store_path}")

    with open(store, "r", encoding="utf-8-sig") as handle:
        data = json.load(handle)

    if not isinstance(data, dict) or "evidence" not in data:
        raise ValueError("Not an evidence-store file (expected a JSON object with an 'evidence' array)")

    existing = data.setdefault("evidence", [])
    custody = data.setdefault("chain_of_custody", [])
    now = datetime.now(timezone.utc).isoformat()
    new_ids: List[str] = []

    for entry in to_evidence_entries(report):
        entry_id = f"ev-{len(existing) + 1:03d}"
        existing.append(
            {
                "id": entry_id,
                **entry,
                # Hash the content field, matching evidence-store.py, so the
                # dossier's integrity re-check passes on these entries too.
                "content_sha256": hashlib.sha256(entry["content"].encode("utf-8")).hexdigest(),
                "collected_at": now,
                "verification": "unverified",
            }
        )
        custody.append({"action": "add", "evidence_id": entry_id, "timestamp": now, "source": "indagis image"})
        new_ids.append(entry_id)

    tmp = store.with_suffix(store.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
    os.replace(tmp, store)

    return new_ids


def collect_store_images(store_path: str) -> List[Dict[str, Any]]:
    """Every image already recorded in an evidence store, newest first.

    The read side of ``append_to_store``. A photograph enters a case as two
    entries — the ``image_metadata`` entry carrying the file hash, and, when
    the picture had coordinates, a separate ``GEO`` indicator. This walks
    those back into one record per image so a reader does not have to
    reassemble the pair themselves.

    Pairing is by ``source`` (the filename both entries were written with).
    Two different photographs sharing a filename would merge here; that is
    accepted rather than worked around, because the alternative — inventing
    a synthetic key — would not survive a store an operator edited by hand,
    and the file hash shown on each record is what actually distinguishes
    them.

    Returns [] for a store with no images. Never raises on a malformed
    entry: a store is operator-editable, so a bad record is skipped rather
    than taken down the whole listing.
    """
    import json

    store = Path(store_path).expanduser()

    with open(store, "r", encoding="utf-8-sig") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError("Not an evidence-store file (expected a JSON object)")

    entries = data.get("evidence")
    if not isinstance(entries, list):
        return []

    # Index the GEO indicators first so each image can pick up its own.
    coordinates: Dict[str, Dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("ioc_type") != "GEO":
            continue
        source = entry.get("source")
        content = entry.get("content")
        if not isinstance(source, str) or not isinstance(content, str):
            continue
        lat, _, lon = content.partition(",")
        try:
            latitude, longitude = float(lat), float(lon)
        except ValueError:
            continue
        coordinates[source] = {
            "latitude": latitude,
            "longitude": longitude,
            "map_url": (
                f"https://www.openstreetmap.org/?mlat={latitude}"
                f"&mlon={longitude}#map=17/{latitude}/{longitude}"
            ),
        }

    images: List[Dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("type") != "image_metadata":
            continue
        source = entry.get("source")
        if not isinstance(source, str):
            continue
        images.append(
            {
                "id": entry.get("id") or "",
                "filename": source,
                "sha256": entry.get("content") or "",
                "summary": entry.get("notes") or "",
                "collected_at": entry.get("collected_at") or "",
                "verification": entry.get("verification") or "unverified",
                "gps": coordinates.get(source),
            }
        )

    # Newest first. Entries without a timestamp sort last rather than
    # crashing the comparison.
    images.sort(key=lambda item: item["collected_at"] or "", reverse=True)

    return images
