"""Custody Chain — Ed25519 signing and verification for evidence exports.

Operates on the evidence-store JSON format (see
``optional-skills/security/oss-forensics/scripts/evidence-store.py``) —
signing binds a private key to the exact set of evidence entries and their
already-computed SHA-256 content hashes, so a signed file can later be
verified against a public key: not just "the hash matches" (anyone can
recompute a hash) but "the investigator holding this key vouched for this
exact evidence set."

Mirrors ``hermes_cli/watch.py``'s structure and output style deliberately.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

from hermes_cli.colors import Colors, color
from hermes_cli.custody_state import (
    generate_key,
    key_exists,
    list_keys,
    load_public_key_b64,
    sign_digest,
    verify_signature,
)


def _load_evidence_store(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if not isinstance(data, dict) or "evidence" not in data:
        raise ValueError(
            "Not an evidence-store file — expected a JSON object with an "
            "'evidence' array (the format 'evidence-store.py' produces)."
        )
    return data


def _canonical_digest(data: Dict[str, Any]) -> bytes:
    """A digest over the (id, sha256(content)) pair of every evidence
    entry, sorted by ID. Deliberately recomputes the content hash from
    ``content`` itself rather than trusting the entry's own recorded
    ``content_sha256`` field — that field lives in the same file an
    attacker controls, so trusting it would let a tampered ``content``
    slip through as long as ``content_sha256`` was edited to match.
    Deterministic regardless of JSON whitespace/key order; any edit to an
    entry's content, or adding/removing one, changes the digest."""
    pairs = sorted(
        (e.get("id", ""), hashlib.sha256((e.get("content") or "").encode("utf-8")).hexdigest())
        for e in data.get("evidence", [])
    )
    canonical = json.dumps(pairs, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).digest()


def _sig_path(store_path: Path) -> Path:
    return store_path.with_suffix(store_path.suffix + ".sig.json")


def custody_keygen(name: str) -> None:
    try:
        result = generate_key(name)
    except FileExistsError as exc:
        print(color(str(exc), Colors.RED))
        return
    print(color(f"✓ Generated key '{name}'", Colors.GREEN))
    print(f"    Public key: {result['public_key']}")
    print(color("  Private key never leaves this machine — share only the public key above.", Colors.DIM))


def custody_keys() -> None:
    keys = list_keys()
    if not keys:
        print(color("No keys yet. Generate one with 'indagis custody keygen <name>'", Colors.DIM))
        return
    for name in keys:
        print(f"  {name}   {load_public_key_b64(name)}")


def custody_sign(store_path_str: str, key_name: str) -> None:
    store_path = Path(store_path_str)
    if not key_exists(key_name):
        print(color(f"No such key: {key_name}. Generate it with 'indagis custody keygen {key_name}'", Colors.RED))
        return
    try:
        data = _load_evidence_store(store_path_str)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(color(f"Failed to read {store_path_str}: {exc}", Colors.RED))
        return

    digest = _canonical_digest(data)
    signature_b64 = sign_digest(key_name, digest)

    from hermes_time import now as _hermes_now

    sig_record = {
        "evidence_store": str(store_path.resolve()),
        "evidence_count": len(data.get("evidence", [])),
        "digest_sha256": digest.hex(),
        "signature": signature_b64,
        "signer_key": key_name,
        "signer_public_key": load_public_key_b64(key_name),
        "signed_at": _hermes_now().isoformat(),
    }
    sig_path = _sig_path(store_path)
    sig_path.write_text(json.dumps(sig_record, indent=2), encoding="utf-8")

    print(color(f"✓ Signed {store_path} ({sig_record['evidence_count']} evidence entries)", Colors.GREEN))
    print(f"    Signature: {sig_path}")
    print(f"    Signed by: {key_name}")


#: Exit codes for ``indagis custody verify``. A chain-of-custody check that
#: always exits 0 cannot be branched on, so ``custody verify x.json &&
#: ship_evidence`` would ship a forged store with "✗ TAMPERED" printed
#: directly above it. A failed integrity check and a store that could not be
#: checked at all are different facts, so they get different codes: the
#: first says the evidence is bad, the second says you do not yet know.
CUSTODY_VERIFY_OK = 0
CUSTODY_VERIFY_FAILED = 1
CUSTODY_VERIFY_UNCHECKABLE = 2


def custody_verify(store_path_str: str) -> int:
    store_path = Path(store_path_str)
    sig_path = _sig_path(store_path)
    if not sig_path.exists():
        print(color(f"No signature file found at {sig_path} — this evidence store hasn't been signed.", Colors.RED))
        return CUSTODY_VERIFY_UNCHECKABLE
    try:
        data = _load_evidence_store(store_path_str)
        sig_record = json.loads(sig_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(color(f"Failed to read {store_path_str} or its signature: {exc}", Colors.RED))
        return CUSTODY_VERIFY_UNCHECKABLE

    current_digest = _canonical_digest(data)
    recorded_digest = sig_record.get("digest_sha256", "")

    if current_digest.hex() != recorded_digest:
        print(color("✗ TAMPERED — evidence content no longer matches what was signed.", Colors.RED))
        print(f"    Signed digest:  {recorded_digest}")
        print(f"    Current digest: {current_digest.hex()}")
        return CUSTODY_VERIFY_FAILED

    valid = verify_signature(
        sig_record.get("signer_public_key", ""), current_digest, sig_record.get("signature", "")
    )
    if not valid:
        print(color("✗ INVALID SIGNATURE — digest matches but the signature does not verify against the recorded public key.", Colors.RED))
        return CUSTODY_VERIFY_FAILED

    print(color(f"✓ VALID — signed by '{sig_record.get('signer_key', '?')}' at {sig_record.get('signed_at', '?')}", Colors.GREEN))
    print(f"    Public key: {sig_record.get('signer_public_key', '?')}")
    print(f"    Evidence entries covered: {sig_record.get('evidence_count', '?')}")
    return CUSTODY_VERIFY_OK


def custody_export(store_path_str: str, out_path_str: str) -> None:
    store_path = Path(store_path_str)
    sig_path = _sig_path(store_path)
    if not sig_path.exists():
        print(color(f"No signature file found at {sig_path} — sign it first with 'indagis custody sign'.", Colors.RED))
        return
    try:
        data = _load_evidence_store(store_path_str)
        sig_record = json.loads(sig_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(color(f"Failed to read {store_path_str} or its signature: {exc}", Colors.RED))
        return

    bundle = {
        "bundle_format": "indagis-custody-chain/1",
        "evidence_store": data,
        "signature": sig_record,
        "verify_instructions": (
            "For each entry in 'evidence_store.evidence', recompute "
            "sha256(content) — do not trust the entry's own 'content_sha256' "
            "field. Build the sorted list of (id, recomputed hash) pairs, "
            "SHA-256 that, and compare to 'signature.digest_sha256'. Then "
            "verify 'signature.signature' against 'signature.signer_public_key' "
            "(Ed25519) over that digest. 'indagis custody verify' does this."
        ),
    }
    out_path = Path(out_path_str)
    out_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    print(color(f"✓ Exported self-verifying bundle to {out_path}", Colors.GREEN))


def custody_command(args) -> int | None:
    action = getattr(args, "custody_command", None)
    if action in (None, "keys"):
        custody_keys()
    elif action == "keygen":
        custody_keygen(args.name)
    elif action == "sign":
        custody_sign(args.store_path, args.key)
    elif action == "verify":
        return custody_verify(args.store_path)
    elif action == "export":
        custody_export(args.store_path, args.out)
    else:
        print(color(f"Unknown custody subcommand: {action}", Colors.RED), file=sys.stderr)
