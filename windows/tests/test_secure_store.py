import json
from pathlib import Path

import pytest

from core.secure_store import MAGIC_DEV, MAGIC_DPAPI, decrypt_bytes, encrypt_bytes, read_json, write_json


def test_local_json_store_encrypts_and_roundtrips(tmp_path):
    path = tmp_path / "profile.dat"
    payload = {"student": "Ada", "note": "Türkçe ses mühendisliği"}
    write_json(path, payload)
    encrypted = path.read_bytes()
    assert encrypted.startswith(MAGIC_DPAPI if __import__("os").name == "nt" else MAGIC_DEV)
    assert "Türkçe".encode("utf-8") not in encrypted
    assert read_json(path, {}) == payload


def test_ciphertext_tamper_is_not_returned_as_plaintext(tmp_path):
    path = tmp_path / "profile.dat"
    write_json(path, {"ok": True})
    encrypted = bytearray(path.read_bytes())
    encrypted[-1] ^= 0x01
    path.write_bytes(encrypted)
    with pytest.raises(RuntimeError, match="Şifreli profil okunamadı"):
        read_json(path, {"fallback": True})
    backups = list(tmp_path.glob("profile.dat.bozuk.*.bak"))
    assert len(backups) == 1
    assert backups[0].read_bytes() == bytes(encrypted)


def test_unrecognized_plaintext_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="şifreli formatta"):
        decrypt_bytes(b'{"password":"plain"}', tmp_path / "p.dat")


def test_temp_file_is_not_left_after_write(tmp_path):
    path = tmp_path / "profile.dat"
    write_json(path, {"v": 1})
    assert sorted(p.name for p in tmp_path.iterdir() if p != path and not p.name.endswith(".devkey")) == []
