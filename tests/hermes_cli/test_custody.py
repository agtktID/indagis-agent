"""Tests for hermes_cli/custody.py — Custody Chain CLI: sign/verify/export.

Covers the tamper-detection fix directly: the signature must bind to
sha256(content) recomputed from each entry's own content, not to the
entry's self-reported content_sha256 field (which an attacker controls
in the same file).
"""

import hashlib
import json

from hermes_cli import custody


def _write_store(path, entries):
    path.write_text(json.dumps({"metadata": {}, "evidence": entries}), encoding="utf-8")


def _entry(eid, content):
    return {"id": eid, "content": content, "content_sha256": hashlib.sha256(content.encode()).hexdigest()}


class TestCustodyKeygen:
    def test_generates_and_prints_public_key(self, capsys):
        custody.custody_keygen("k1")
        out = capsys.readouterr().out
        assert "Generated key 'k1'" in out
        assert "Public key:" in out

    def test_duplicate_name_reported_not_raised(self, capsys):
        custody.custody_keygen("k1")
        capsys.readouterr()
        custody.custody_keygen("k1")
        assert "already exists" in capsys.readouterr().out


class TestCustodySignAndVerify:
    def test_sign_then_verify_succeeds(self, tmp_path, capsys):
        custody.custody_keygen("k1")
        capsys.readouterr()

        store = tmp_path / "evidence.json"
        _write_store(store, [_entry("EV-0001", "hello world")])

        custody.custody_sign(str(store), "k1")
        assert "Signed" in capsys.readouterr().out

        custody.custody_verify(str(store))
        out = capsys.readouterr().out
        assert "VALID" in out
        assert "k1" in out

    def test_sign_with_missing_key(self, tmp_path, capsys):
        store = tmp_path / "evidence.json"
        _write_store(store, [_entry("EV-0001", "hello")])
        custody.custody_sign(str(store), "nope")
        assert "No such key" in capsys.readouterr().out

    def test_verify_without_prior_signature(self, tmp_path, capsys):
        store = tmp_path / "evidence.json"
        _write_store(store, [_entry("EV-0001", "hello")])
        custody.custody_verify(str(store))
        assert "hasn't been signed" in capsys.readouterr().out

    def test_naive_content_tamper_detected(self, tmp_path, capsys):
        custody.custody_keygen("k1")
        capsys.readouterr()
        store = tmp_path / "evidence.json"
        _write_store(store, [_entry("EV-0001", "original")])
        custody.custody_sign(str(store), "k1")
        capsys.readouterr()

        data = json.loads(store.read_text())
        data["evidence"][0]["content"] = "TAMPERED"
        store.write_text(json.dumps(data), encoding="utf-8")

        custody.custody_verify(str(store))
        assert "TAMPERED" in capsys.readouterr().out

    def test_sneaky_content_and_hash_tamper_detected(self, tmp_path, capsys):
        """The real bug this module was fixed for: an attacker editing
        content AND recomputing content_sha256 to match must still be
        caught, since the digest is bound to content directly."""
        custody.custody_keygen("k1")
        capsys.readouterr()
        store = tmp_path / "evidence.json"
        _write_store(store, [_entry("EV-0001", "original")])
        custody.custody_sign(str(store), "k1")
        capsys.readouterr()

        data = json.loads(store.read_text())
        data["evidence"][0]["content"] = "TAMPERED VALUE"
        data["evidence"][0]["content_sha256"] = hashlib.sha256(b"TAMPERED VALUE").hexdigest()
        store.write_text(json.dumps(data), encoding="utf-8")

        custody.custody_verify(str(store))
        out = capsys.readouterr().out
        assert "TAMPERED" in out

    def test_swapped_public_key_reported_as_invalid(self, tmp_path, capsys):
        custody.custody_keygen("k1")
        custody.custody_keygen("attacker")
        capsys.readouterr()
        store = tmp_path / "evidence.json"
        _write_store(store, [_entry("EV-0001", "hello")])
        custody.custody_sign(str(store), "k1")
        capsys.readouterr()

        from hermes_cli.custody_state import load_public_key_b64

        sig_path = store.with_suffix(store.suffix + ".sig.json")
        sig = json.loads(sig_path.read_text())
        sig["signer_public_key"] = load_public_key_b64("attacker")
        sig_path.write_text(json.dumps(sig), encoding="utf-8")

        custody.custody_verify(str(store))
        out = capsys.readouterr().out
        assert "INVALID SIGNATURE" in out


class TestCustodyExport:
    def test_export_produces_bundle(self, tmp_path, capsys):
        custody.custody_keygen("k1")
        capsys.readouterr()
        store = tmp_path / "evidence.json"
        _write_store(store, [_entry("EV-0001", "hello")])
        custody.custody_sign(str(store), "k1")
        capsys.readouterr()

        out_path = tmp_path / "bundle.json"
        custody.custody_export(str(store), str(out_path))
        assert "self-verifying bundle" in capsys.readouterr().out

        bundle = json.loads(out_path.read_text())
        assert bundle["bundle_format"] == "indagis-custody-chain/1"
        assert bundle["evidence_store"]["evidence"][0]["id"] == "EV-0001"
        assert "signature" in bundle

    def test_export_without_signature(self, tmp_path, capsys):
        store = tmp_path / "evidence.json"
        _write_store(store, [_entry("EV-0001", "hello")])
        custody.custody_export(str(store), str(tmp_path / "out.json"))
        assert "sign it first" in capsys.readouterr().out


class TestCustodyVerifyExitCode:
    """`custody verify` returned 0 for TAMPERED, INVALID SIGNATURE and unsigned
    stores alike, so `custody verify x.json && ship_evidence` shipped a forged
    store with "✗ TAMPERED" printed directly above it. The detection was
    always correct; only the code a script can branch on was missing."""

    def test_valid_is_zero(self, tmp_path, capsys):
        custody.custody_keygen("k1")
        store = tmp_path / "evidence.json"
        _write_store(store, [_entry("EV-0001", "hello world")])
        custody.custody_sign(str(store), "k1")
        capsys.readouterr()
        assert custody.custody_verify(str(store)) == custody.CUSTODY_VERIFY_OK

    def test_tampered_is_non_zero(self, tmp_path, capsys):
        custody.custody_keygen("k1")
        store = tmp_path / "evidence.json"
        _write_store(store, [_entry("EV-0001", "hello world")])
        custody.custody_sign(str(store), "k1")
        # Rewrite the content after signing; the entry's self-reported hash is
        # updated too, exactly as an attacker editing the file would.
        _write_store(store, [_entry("EV-0001", "goodbye world")])
        capsys.readouterr()
        rc = custody.custody_verify(str(store))
        assert rc == custody.CUSTODY_VERIFY_FAILED
        assert rc != 0, "`custody verify && ship` must not ship a tampered store"
        assert "TAMPERED" in capsys.readouterr().out

    def test_unsigned_is_non_zero_and_distinct(self, tmp_path, capsys):
        store = tmp_path / "evidence.json"
        _write_store(store, [_entry("EV-0001", "hello world")])
        capsys.readouterr()
        rc = custody.custody_verify(str(store))
        assert rc == custody.CUSTODY_VERIFY_UNCHECKABLE
        assert rc != 0
        # "could not be checked" is not "checked and found bad".
        assert rc != custody.CUSTODY_VERIFY_FAILED
