"""``indagis image`` subcommand parser — Image Intel (metadata forensics).

Mirrors ``hermes_cli/subcommands/custody.py``'s shape: same
subparsers-with-dest pattern, same ``func=cmd_image`` dispatch, handler
injected to avoid importing ``main`` (cycle avoidance).
"""

from __future__ import annotations

from typing import Callable


def build_image_parser(subparsers, *, cmd_image: Callable) -> None:
    """Attach the ``image`` subcommand (and its sub-actions) to ``subparsers``."""
    image_parser = subparsers.add_parser(
        "image",
        help="Image Intel — EXIF, GPS and device fingerprints from a photograph",
        description=(
            "Read the metadata an image carries: GPS coordinates, the camera "
            "make/model and serial numbers that link separate photographs to "
            "one physical device, and the capture timestamps. Nothing here "
            "writes to the image; 'image scrub' produces a metadata-free copy "
            "at a new path."
        ),
    )
    image_subparsers = image_parser.add_subparsers(dest="image_command")

    # image inspect
    image_inspect = image_subparsers.add_parser(
        "inspect", help="Full metadata report — hash, EXIF, GPS, device, timestamps"
    )
    image_inspect.add_argument("path", help="Path to an image file")
    image_inspect.add_argument("--json", action="store_true", help="Emit the raw report as JSON")
    image_inspect.add_argument(
        "--evidence",
        metavar="STORE",
        help=(
            "Append the findings to an existing evidence-store JSON file "
            "(the format 'indagis dossier' and 'indagis custody' read)"
        ),
    )

    # image gps
    image_gps = image_subparsers.add_parser("gps", help="Coordinates and a map link, nothing else")
    image_gps.add_argument("path", help="Path to an image file")
    image_gps.add_argument("--json", action="store_true", help="Emit the coordinates as JSON")

    # image scrub
    image_scrub = image_subparsers.add_parser(
        "scrub", help="Write a metadata-free copy, leaving the original untouched"
    )
    image_scrub.add_argument("path", help="Path to the image to strip")
    image_scrub.add_argument(
        "--out", required=True, help="Path to write the stripped copy to (must not already exist)"
    )

    image_parser.set_defaults(func=cmd_image)
