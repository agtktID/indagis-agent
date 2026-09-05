"""Image Intel — terminal output for ``indagis image``.

Presentation only: every fact printed here comes from
``hermes_cli/image_intel.py``, which does the reading and never writes to the
source file. Mirrors ``hermes_cli/custody.py``'s structure and output style
deliberately — same ``Colors``/``color`` helpers, same ``*_command(args)``
dispatcher at the bottom.

Named ``image_cmd`` rather than ``image`` so that ``from PIL import Image``
inside the intel module can never resolve against a sibling of the same name.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict

from hermes_cli.colors import Colors, color


def _print_kv(label: str, value: Any, *, indent: str = "    ") -> None:
    print(f"{indent}{label:<22} {value}")


def _render_report(report: Dict[str, Any]) -> None:
    print(color(f"■ {report['filename']}", Colors.CYAN))
    _print_kv("SHA-256", report["sha256"])
    _print_kv("Size", f"{report['size_bytes']:,} bytes")
    _print_kv("File modified", report["file_modified"])

    if report.get("error"):
        print(color(f"    Could not read metadata: {report['error']}", Colors.YELLOW))

    if not report.get("has_exif"):
        print(color("    No EXIF metadata. Stripped on upload, or never written.", Colors.DIM))
        return

    gps = report.get("gps") or {}
    if gps:
        print()
        print(color("  GPS", Colors.GREEN))
        _print_kv("Coordinates", f"{gps['latitude']}, {gps['longitude']}")
        if "altitude_m" in gps:
            _print_kv("Altitude", f"{gps['altitude_m']} m")
        if "gps_date" in gps:
            _print_kv("GPS date", gps["gps_date"])
        _print_kv("Map", gps["map_url"])

    device = report.get("device") or {}
    if device:
        print()
        print(color("  Device", Colors.CYAN))
        for key, value in device.items():
            _print_kv(key, value)
        if report.get("device_fingerprint"):
            print(
                color(
                    "    A serial number ties separate photographs to the same "
                    "physical device.",
                    Colors.DIM,
                )
            )

    times = report.get("timestamps") or {}
    if times:
        print()
        print(color("  Timestamps", Colors.CYAN))
        for key, value in times.items():
            _print_kv(key, value)

    software = report.get("software") or {}
    if software:
        print()
        print(color("  Software", Colors.CYAN))
        for key, value in software.items():
            _print_kv(key, value)

    gap = report.get("timestamp_discrepancy")
    if gap:
        print()
        print(color(f"  ⚠ Timestamp gap — {gap['delta_hours']} h", Colors.YELLOW))
        print(color(f"    {gap['note']}", Colors.DIM))

    total = len(report.get("all_tags") or {})
    print()
    print(color(f"  {total} EXIF tag(s) total — use --json to see them all.", Colors.DIM))


def image_inspect(path: str, *, as_json: bool = False, evidence: str | None = None) -> None:
    from hermes_cli.image_intel import append_to_store, inspect_image

    try:
        report = inspect_image(path)
    except FileNotFoundError as exc:
        print(color(str(exc), Colors.RED), file=sys.stderr)
        return

    if as_json:
        print(json.dumps(report, indent=2, default=str))
    else:
        _render_report(report)

    if evidence:
        try:
            new_ids = append_to_store(evidence, report)
        except (FileNotFoundError, ValueError, OSError) as exc:
            print(color(f"Could not append to evidence store: {exc}", Colors.RED), file=sys.stderr)
            return
        if not as_json:
            print()
        print(color(f"✓ Appended {len(new_ids)} entr(ies) to {evidence}: {', '.join(new_ids)}", Colors.GREEN))
        print(color("  Re-sign it with 'indagis custody sign' — the digest has changed.", Colors.DIM))


def image_gps(path: str, *, as_json: bool = False) -> None:
    from hermes_cli.image_intel import inspect_image

    try:
        report = inspect_image(path)
    except FileNotFoundError as exc:
        print(color(str(exc), Colors.RED), file=sys.stderr)
        return

    gps = report.get("gps") or {}

    if as_json:
        print(json.dumps(gps, indent=2))
        return

    if not gps:
        print(color(f"No GPS coordinates in {report['filename']}.", Colors.DIM))
        return

    print(color(f"{gps['latitude']}, {gps['longitude']}", Colors.GREEN))
    if "altitude_m" in gps:
        _print_kv("Altitude", f"{gps['altitude_m']} m", indent="  ")
    _print_kv("Map", gps["map_url"], indent="  ")


def image_scrub(path: str, out_path: str) -> None:
    from hermes_cli.image_intel import scrub_image

    try:
        result = scrub_image(path, out_path)
    except FileNotFoundError as exc:
        print(color(str(exc), Colors.RED), file=sys.stderr)
        return
    except FileExistsError as exc:
        print(color(f"{exc} — pick an output path that does not exist yet.", Colors.RED), file=sys.stderr)
        return
    except Exception as exc:  # noqa: BLE001 - a corrupt or unsupported image is a message, not a traceback
        print(color(f"Could not scrub {path}: {type(exc).__name__}: {exc}", Colors.RED), file=sys.stderr)
        return

    print(color(f"✓ Wrote metadata-free copy to {result['output']}", Colors.GREEN))
    _print_kv("Tags removed", result["removed_tags"])
    _print_kv("GPS removed", "yes" if result["had_gps"] else "no GPS present")
    _print_kv("Tags remaining", result["remaining_tags"])
    _print_kv("Output SHA-256", result["output_sha256"])
    print(color("  The original is untouched.", Colors.DIM))


def image_command(args) -> None:
    action = getattr(args, "image_command", None)
    if action == "inspect":
        image_inspect(args.path, as_json=args.json, evidence=args.evidence)
    elif action == "gps":
        image_gps(args.path, as_json=args.json)
    elif action == "scrub":
        image_scrub(args.path, args.out)
    else:
        print(
            color(
                "Usage: indagis image {inspect|gps|scrub} — run 'indagis image --help' for details.",
                Colors.DIM,
            ),
            file=sys.stderr,
        )
