"""``indagis custody`` subcommand parser — Custody Chain (evidence signing).

Mirrors ``hermes_cli/subcommands/watch.py``'s shape: same
subparsers-with-dest pattern, same ``func=cmd_custody`` dispatch, handler
injected to avoid importing ``main`` (cycle avoidance).
"""

from __future__ import annotations

from typing import Callable


def build_custody_parser(subparsers, *, cmd_custody: Callable) -> None:
    """Attach the ``custody`` subcommand (and its sub-actions) to ``subparsers``."""
    custody_parser = subparsers.add_parser(
        "custody",
        help="Custody Chain — Ed25519 signing and verification for evidence exports",
        description=(
            "Sign an evidence-store file (see the 'oss-forensics' skill) "
            "with a local Ed25519 key so its integrity and authorship can "
            "be verified later, then export a self-verifying bundle."
        ),
    )
    custody_subparsers = custody_parser.add_subparsers(dest="custody_command")

    # custody keys
    custody_subparsers.add_parser("keys", help="List local signing keys")

    # custody keygen
    custody_keygen = custody_subparsers.add_parser("keygen", help="Generate a new Ed25519 signing key")
    custody_keygen.add_argument("name", help="Name for the new key")

    # custody sign
    custody_sign = custody_subparsers.add_parser("sign", help="Sign an evidence-store file")
    custody_sign.add_argument("store_path", help="Path to an evidence-store JSON file")
    custody_sign.add_argument("--key", required=True, help="Name of the signing key to use")

    # custody verify
    custody_verify = custody_subparsers.add_parser("verify", help="Verify an evidence-store file's signature")
    custody_verify.add_argument("store_path", help="Path to a previously signed evidence-store JSON file")

    # custody export
    custody_export = custody_subparsers.add_parser(
        "export", help="Export a signed evidence store as one self-verifying bundle file"
    )
    custody_export.add_argument("store_path", help="Path to a previously signed evidence-store JSON file")
    custody_export.add_argument("--out", required=True, help="Path to write the bundle to")

    custody_parser.set_defaults(func=cmd_custody)
