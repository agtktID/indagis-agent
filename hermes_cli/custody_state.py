"""Storage for Custody Chain — Ed25519 keys for signing evidence exports.

``optional-skills/security/oss-forensics/scripts/evidence-store.py`` already
hashes every evidence entry with SHA-256 and keeps a chain-of-custody log,
but that hash alone proves nothing about *who* produced it — anyone with
the file can recompute a SHA-256 after editing it. What's missing is a
signature: a private key the investigator controls, so a signed export can
later be verified against a public key without trusting whoever is holding
the file at that moment.

Uses Ed25519 (``cryptography``, already a pinned project dependency — no
new dependency added) rather than inventing anything: fast, small
signatures, and a well-understood security margin.

Private keys live under ``custody/keys/<name>.key`` with 0600 permissions
and are never printed or logged; public keys live alongside as
``<name>.pub`` and are safe to share.
"""

from __future__ import annotations

import base64
import json
import os
import stat
from pathlib import Path
from typing import Any, Dict, List, Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from hermes_constants import get_indagis_home
from hermes_time import now as _hermes_now


def _keys_dir() -> Path:
    d = get_indagis_home() / "custody" / "keys"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _private_key_path(name: str) -> Path:
    return _keys_dir() / f"{name}.key"


def _public_key_path(name: str) -> Path:
    return _keys_dir() / f"{name}.pub"


def key_exists(name: str) -> bool:
    return _private_key_path(name).exists()


def generate_key(name: str) -> Dict[str, str]:
    if key_exists(name):
        raise FileExistsError(f"Key '{name}' already exists — remove it first or choose a different name.")

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    priv_raw = private_key.private_bytes(
        serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption()
    )
    pub_raw = public_key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)

    priv_path = _private_key_path(name)
    # O_EXCL: refuse to clobber a concurrently-created key of the same name.
    fd = os.open(str(priv_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(priv_raw)
    except BaseException:
        try:
            priv_path.unlink()
        except OSError:
            pass
        raise

    pub_b64 = base64.b64encode(pub_raw).decode("ascii")
    _public_key_path(name).write_text(pub_b64 + "\n", encoding="utf-8")

    return {"name": name, "public_key": pub_b64}


def list_keys() -> List[str]:
    return sorted(p.stem for p in _keys_dir().glob("*.key"))


def load_private_key(name: str) -> Ed25519PrivateKey:
    path = _private_key_path(name)
    if not path.exists():
        raise FileNotFoundError(f"No such key: {name}")
    raw = path.read_bytes()
    return Ed25519PrivateKey.from_private_bytes(raw)


def load_public_key_b64(name: str) -> str:
    path = _public_key_path(name)
    if not path.exists():
        raise FileNotFoundError(f"No public key on file for: {name}")
    return path.read_text(encoding="utf-8").strip()


def public_key_from_b64(pub_b64: str) -> Ed25519PublicKey:
    return Ed25519PublicKey.from_public_bytes(base64.b64decode(pub_b64))


def sign_digest(key_name: str, digest: bytes) -> str:
    private_key = load_private_key(key_name)
    signature = private_key.sign(digest)
    return base64.b64encode(signature).decode("ascii")


def verify_signature(pub_b64: str, digest: bytes, signature_b64: str) -> bool:
    try:
        public_key = public_key_from_b64(pub_b64)
        public_key.verify(base64.b64decode(signature_b64), digest)
        return True
    except (InvalidSignature, ValueError):
        return False
