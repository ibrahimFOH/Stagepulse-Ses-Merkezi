import base64
import json
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

import pytest

from core.secure_store import (
    MAGIC_DEV, MAGIC_DPAPI, decrypt_bytes, encrypt_bytes, read_json, verify_offline_lease, write_json,
)


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


def _signed_offline_lease(private_key, claims):
    payload = json.dumps(claims, separators=(",", ":")).encode("utf-8")
    signature = private_key.sign(payload, padding.PKCS1v15(), hashes.SHA256())
    encode = lambda value: base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")
    return {"v": 1, "alg": "RS256", "payload": encode(payload), "signature": encode(signature)}


def _paid_claims(now_ms):
    issued = now_ms - 60_000
    return {
        "v": 1, "uid": "student-1", "device_hash": "a" * 64,
        "app_id": "ses-merkezi", "platform": "windows",
        "entitlement": "paid", "paid": True, "plan_code": "student",
        "bundle_code": "full_master", "license_expires_at_ms": now_ms + 30 * 86400000,
        "trial_expires_at_ms": None, "issued_at_ms": issued,
        "expires_at_ms": issued + 14 * 86400000,
    }


def test_offline_lease_accepts_valid_paid_signature_and_device_binding():
    now = 1_800_000_000_000
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    claims = _paid_claims(now)
    result = verify_offline_lease(
        _signed_offline_lease(private_key, claims), expected_user_id="student-1",
        expected_device_hash="a" * 64, expected_app_id="ses-merkezi",
        expected_platform="windows", public_key_pem=public_key, now_ms=now,
    )
    assert result["paid"] is True
    assert result["entitlement"] == "paid"


def test_offline_lease_rejects_wrong_user_device_app_or_platform():
    now = 1_800_000_000_000
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    envelope = _signed_offline_lease(private_key, _paid_claims(now))
    for field, value in (("expected_user_id", "other-user"), ("expected_device_hash", "b" * 64),
                         ("expected_app_id", "ses-merkezi-android"), ("expected_platform", "android")):
        kwargs = {"expected_user_id": "student-1", "expected_device_hash": "a" * 64,
                  "expected_app_id": "ses-merkezi", "expected_platform": "windows",
                  "public_key_pem": public_key, "now_ms": now}
        kwargs[field] = value
        with pytest.raises(ValueError, match="farklı kullanıcıya veya cihaza"):
            verify_offline_lease(envelope, **kwargs)


def test_offline_lease_rejects_expiry_clock_rollback_and_oversized_paid_grace():
    now = 1_800_000_000_000
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    claims = _paid_claims(now)
    expired = dict(claims, expires_at_ms=now)
    with pytest.raises(ValueError, match="süresi dolmuş"):
        verify_offline_lease(_signed_offline_lease(private_key, expired),
            expected_user_id="student-1", expected_device_hash="a" * 64,
            expected_app_id="ses-merkezi", expected_platform="windows",
            public_key_pem=public_key, now_ms=now)
    with pytest.raises(ValueError, match="geri alınmış"):
        verify_offline_lease(_signed_offline_lease(private_key, claims),
            expected_user_id="student-1", expected_device_hash="a" * 64,
            expected_app_id="ses-merkezi", expected_platform="windows",
            public_key_pem=public_key, now_ms=now, last_seen_ms=now + 10 * 60 * 1000)
    oversized = dict(claims, expires_at_ms=claims["issued_at_ms"] + 15 * 86400000)
    with pytest.raises(ValueError, match="sınırı geçersiz"):
        verify_offline_lease(_signed_offline_lease(private_key, oversized),
            expected_user_id="student-1", expected_device_hash="a" * 64,
            expected_app_id="ses-merkezi", expected_platform="windows",
            public_key_pem=public_key, now_ms=now)


def test_offline_trial_lease_is_limited_to_seven_days_and_trial_expiry():
    now = 1_800_000_000_000
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    issued = now - 60_000
    claims = {
        "v": 1, "uid": "student-1", "device_hash": "a" * 64,
        "app_id": "ses-merkezi", "platform": "windows",
        "entitlement": "trial", "paid": False, "plan_code": "trial",
        "bundle_code": "trial", "license_expires_at_ms": None,
        "trial_expires_at_ms": issued + 7 * 86400000, "issued_at_ms": issued,
        "expires_at_ms": issued + 7 * 86400000,
    }
    result = verify_offline_lease(
        _signed_offline_lease(private_key, claims), expected_user_id="student-1",
        expected_device_hash="a" * 64, expected_app_id="ses-merkezi",
        expected_platform="windows", public_key_pem=public_key, now_ms=now,
    )
    assert result["entitlement"] == "trial"
    too_long = dict(claims, expires_at_ms=issued + 8 * 86400000,
                    trial_expires_at_ms=issued + 8 * 86400000)
    with pytest.raises(ValueError, match="sınırı geçersiz"):
        verify_offline_lease(_signed_offline_lease(private_key, too_long),
            expected_user_id="student-1", expected_device_hash="a" * 64,
            expected_app_id="ses-merkezi", expected_platform="windows",
            public_key_pem=public_key, now_ms=now)
