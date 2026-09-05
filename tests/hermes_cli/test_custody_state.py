"""Tests for hermes_cli/custody_state.py — Ed25519 key management."""

import base64

import pytest

from hermes_cli.custody_state import (
    generate_key,
    key_exists,
    list_keys,
    load_private_key,
    load_public_key_b64,
    sign_digest,
    verify_signature,
)


class TestGenerateKey:
    def test_creates_key_files(self, tmp_path):
        from hermes_constants import get_indagis_home

        result = generate_key("investigator1")
        assert result["name"] == "investigator1"
        assert base64.b64decode(result["public_key"])  # valid base64

        keys_dir = get_indagis_home() / "custody" / "keys"
        assert (keys_dir / "investigator1.key").exists()
        assert (keys_dir / "investigator1.pub").exists()

    def test_private_key_is_0600(self):
        import stat

        from hermes_constants import get_indagis_home

        generate_key("investigator1")
        priv_path = get_indagis_home() / "custody" / "keys" / "investigator1.key"
        mode = stat.S_IMODE(priv_path.stat().st_mode)
        assert mode == 0o600

    def test_duplicate_name_raises(self):
        generate_key("investigator1")
        with pytest.raises(FileExistsError):
            generate_key("investigator1")

    def test_key_exists(self):
        assert key_exists("investigator1") is False
        generate_key("investigator1")
        assert key_exists("investigator1") is True


class TestListKeys:
    def test_empty(self):
        assert list_keys() == []

    def test_sorted(self):
        generate_key("zeta")
        generate_key("alpha")
        assert list_keys() == ["alpha", "zeta"]


class TestSignAndVerify:
    def test_roundtrip(self):
        generate_key("k1")
        digest = b"\x00" * 32
        signature = sign_digest("k1", digest)
        pub_b64 = load_public_key_b64("k1")
        assert verify_signature(pub_b64, digest, signature) is True

    def test_wrong_digest_fails_verification(self):
        generate_key("k1")
        signature = sign_digest("k1", b"\x01" * 32)
        pub_b64 = load_public_key_b64("k1")
        assert verify_signature(pub_b64, b"\x02" * 32, signature) is False

    def test_wrong_key_fails_verification(self):
        generate_key("k1")
        generate_key("k2")
        digest = b"\x03" * 32
        signature = sign_digest("k1", digest)
        wrong_pub = load_public_key_b64("k2")
        assert verify_signature(wrong_pub, digest, signature) is False

    def test_garbage_public_key_fails_cleanly(self):
        assert verify_signature("not-valid-base64!!!", b"x" * 32, "also-not-valid") is False

    def test_load_missing_private_key_raises(self):
        with pytest.raises(FileNotFoundError):
            load_private_key("nope")

    def test_load_missing_public_key_raises(self):
        with pytest.raises(FileNotFoundError):
            load_public_key_b64("nope")
