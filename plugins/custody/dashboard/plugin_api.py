"""Custody Chain dashboard plugin — backend API routes.

Mounted at /api/plugins/custody/ by the dashboard plugin system
(hermes_cli.web_server._mount_plugin_api_routes). Backs the desktop app's
Custody Chain plugin (apps/desktop/src/plugins/custody/): a read-only
inventory of the Ed25519 signing keys hermes_cli/custody_state.py already
manages.

SECURITY: this router exposes key *names* and *public keys* only — never
private key material. hermes_cli.custody_state.load_private_key() and
sign_digest() are intentionally not wrapped here; signing an export stays
a CLI action ('indagis custody sign'), which is also where the private
key file is ever read from disk.
"""

from __future__ import annotations

from fastapi import APIRouter

from hermes_cli.custody_state import list_keys, load_public_key_b64

router = APIRouter()


@router.get("/keys")
def keys() -> dict:
    entries = []
    for name in list_keys():
        try:
            public_key = load_public_key_b64(name)
        except (FileNotFoundError, OSError):
            public_key = None
        entries.append({"name": name, "public_key": public_key})
    return {"keys": entries}
