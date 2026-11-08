"""Windows DPAPI ile kullanıcı hesabına bağlı şifreli yerel JSON deposu.

Windows'ta şifreleme anahtarı EXE'ye gömülmez; DPAPI current-user alanını kullanır.
Windows dışı geliştirme/test ortamlarında AES-GCM kullanılır.
"""
from __future__ import annotations

import base64
import json
import os
import secrets
import time
from pathlib import Path
from typing import Any

try:
    from cryptography.exceptions import InvalidTag
except ImportError:  # Windows DPAPI builds still use cryptography elsewhere, but keep import safe.
    InvalidTag = type("InvalidTag", (Exception,), {})

MAGIC_DPAPI = b"SPDP1\0"
MAGIC_DEV = b"SPDEV1\0"
AAD = b"stagepulse-ses-merkezi-v1"


def _dpapi(data: bytes, protect: bool) -> bytes:
    if os.name != "nt":
        raise OSError("Windows DPAPI yalnızca Windows'ta kullanılabilir.")
    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]

    source_buffer = ctypes.create_string_buffer(data, max(1, len(data)))
    source = DATA_BLOB(len(data), ctypes.cast(source_buffer, ctypes.POINTER(ctypes.c_ubyte)))
    target = DATA_BLOB()
    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    crypt32.CryptProtectData.argtypes = [
        ctypes.POINTER(DATA_BLOB), wintypes.LPCWSTR, ctypes.POINTER(DATA_BLOB),
        ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(DATA_BLOB),
    ]
    crypt32.CryptProtectData.restype = wintypes.BOOL
    crypt32.CryptUnprotectData.argtypes = [
        ctypes.POINTER(DATA_BLOB), ctypes.POINTER(wintypes.LPWSTR), ctypes.POINTER(DATA_BLOB),
        ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(DATA_BLOB),
    ]
    crypt32.CryptUnprotectData.restype = wintypes.BOOL
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p

    flags = 0x1  # CRYPTPROTECT_UI_FORBIDDEN
    if protect:
        ok = crypt32.CryptProtectData(ctypes.byref(source), "Stagepulse Ses Merkezi", None, None, None, flags, ctypes.byref(target))
    else:
        ok = crypt32.CryptUnprotectData(ctypes.byref(source), None, None, None, None, flags, ctypes.byref(target))
    if not ok:
        error = ctypes.get_last_error()
        raise OSError(error, "Windows DPAPI şifreleme/çözme işlemi başarısız oldu.")
    try:
        return ctypes.string_at(target.pbData, target.cbData)
    finally:
        if target.pbData:
            kernel32.LocalFree(ctypes.cast(target.pbData, ctypes.c_void_p))


def _dev_key(path: Path) -> bytes:
    key_path = path.with_suffix(path.suffix + ".devkey")
    key_path.parent.mkdir(parents=True, exist_ok=True)
    if key_path.exists():
        key = key_path.read_bytes()
        if len(key) != 32:
            raise ValueError("Geliştirme veri anahtarı bozuk.")
        return key
    key = secrets.token_bytes(32)
    try:
        fd = os.open(key_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        return _dev_key(path)
    with os.fdopen(fd, "wb") as stream:
        stream.write(key)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.chmod(key_path, 0o600)
    except OSError:
        pass
    return key


def encrypt_bytes(data: bytes, path: Path) -> bytes:
    if os.name == "nt":
        return MAGIC_DPAPI + _dpapi(data, True)
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    nonce = secrets.token_bytes(12)
    return MAGIC_DEV + nonce + AESGCM(_dev_key(path)).encrypt(nonce, data, AAD)


def decrypt_bytes(data: bytes, path: Path) -> bytes:
    if data.startswith(MAGIC_DPAPI):
        if os.name != "nt":
            raise ValueError("Bu profil, Windows kullanıcı hesabına bağlı DPAPI ile şifrelenmiş.")
        return _dpapi(data[len(MAGIC_DPAPI):], False)
    if data.startswith(MAGIC_DEV):
        if os.name == "nt":
            raise ValueError("Geliştirme profili Windows DPAPI deposuna otomatik taşınamaz.")
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        payload = data[len(MAGIC_DEV):]
        if len(payload) < 13:
            raise ValueError("Şifreli veri bozuk.")
        return AESGCM(_dev_key(path)).decrypt(payload[:12], payload[12:], AAD)
    raise ValueError("Profil şifreli formatta değil veya bozuk.")


def read_json(path: Path, fallback: Any) -> Any:
    try:
        raw = decrypt_bytes(path.read_bytes(), path)
        return json.loads(raw.decode("utf-8"))
    except FileNotFoundError:
        return fallback
    except (OSError, ValueError, json.JSONDecodeError, UnicodeDecodeError, InvalidTag) as exc:
        backup = path.with_suffix(path.suffix + ".bozuk." + str(int(time.time())) + ".bak")
        try:
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup.write_bytes(path.read_bytes())
        except OSError:
            backup = None
        detail = f" Bozuk kopya: {backup.name}." if backup is not None else " Bozuk kopya yedeklenemedi."
        raise RuntimeError("Şifreli profil okunamadı." + detail + f" Ayrıntı: {exc}") from exc


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plain = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    encrypted = encrypt_bytes(plain, path)
    temp = path.with_suffix(path.suffix + f".{secrets.token_hex(4)}.tmp")
    try:
        with temp.open("xb") as stream:
            stream.write(encrypted)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        try:
            temp.unlink(missing_ok=True)
        except OSError:
            pass

OFFLINE_PAID_LEASE_MS = 14 * 24 * 60 * 60 * 1000
OFFLINE_TRIAL_LEASE_MS = 7 * 24 * 60 * 60 * 1000
OFFLINE_CLOCK_SKEW_MS = 5 * 60 * 1000


def _decode_base64url(value: str) -> bytes:
    if not isinstance(value, str) or not value or len(value) > 16384:
        raise ValueError("Offline lisans alanı geçersiz.")
    padded = value + ("=" * (-len(value) % 4))
    try:
        return base64.urlsafe_b64decode(padded.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise ValueError("Offline lisans kodlaması geçersiz.") from exc


def verify_offline_lease(
    envelope: Any,
    *,
    expected_user_id: str,
    expected_device_hash: str,
    expected_app_id: str,
    expected_platform: str,
    public_key_pem: bytes | str,
    now_ms: int | None = None,
    last_seen_ms: int = 0,
) -> dict[str, Any]:
    """Verify the server-signed RS256 offline entitlement and its binding."""
    if not isinstance(envelope, dict) or envelope.get("v") != 1 or envelope.get("alg") != "RS256":
        raise ValueError("Offline lisans zarfı desteklenmiyor.")
    payload_bytes = _decode_base64url(envelope.get("payload", ""))
    signature = _decode_base64url(envelope.get("signature", ""))
    if len(payload_bytes) > 4096 or len(signature) != 256:
        raise ValueError("Offline lisans boyutu geçersiz.")

    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.exceptions import InvalidSignature

    try:
        pem_bytes = public_key_pem.encode("ascii") if isinstance(public_key_pem, str) else bytes(public_key_pem)
        if not pem_bytes.startswith(b"-----BEGIN PUBLIC KEY-----"):
            raise ValueError("Offline lisans açık anahtarı bulunamadı.")
        public_key = serialization.load_pem_public_key(pem_bytes)
        public_key.verify(signature, payload_bytes, padding.PKCS1v15(), hashes.SHA256())
        claims = json.loads(payload_bytes.decode("utf-8"))
    except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError, InvalidSignature) as exc:
        raise ValueError("Offline lisans imzası doğrulanamadı.") from exc

    if not isinstance(claims, dict) or claims.get("v") != 1:
        raise ValueError("Offline lisans içeriği geçersiz.")
    if (
        claims.get("uid") != expected_user_id
        or claims.get("device_hash") != expected_device_hash
        or claims.get("app_id") != expected_app_id
        or claims.get("platform") != expected_platform
    ):
        raise ValueError("Offline lisans farklı kullanıcıya veya cihaza ait.")

    issued_at = claims.get("issued_at_ms")
    expires_at = claims.get("expires_at_ms")
    if not isinstance(issued_at, int) or not isinstance(expires_at, int) or issued_at <= 0 or expires_at <= issued_at:
        raise ValueError("Offline lisans zamanı geçersiz.")
    current = int(time.time() * 1000) if now_ms is None else int(now_ms)
    if current < int(last_seen_ms or 0) - OFFLINE_CLOCK_SKEW_MS:
        raise ValueError("Sistem saati geri alınmış.")
    if issued_at > current + OFFLINE_CLOCK_SKEW_MS or current >= expires_at:
        raise ValueError("Offline lisans süresi dolmuş veya henüz başlamamış.")

    duration = expires_at - issued_at
    entitlement = claims.get("entitlement")
    is_paid = claims.get("paid") is True
    if is_paid:
        license_expiry = claims.get("license_expires_at_ms")
        if entitlement != "paid" or duration > OFFLINE_PAID_LEASE_MS:
            raise ValueError("Ücretli offline lisans sınırı geçersiz.")
        if license_expiry is not None and (
            not isinstance(license_expiry, int) or expires_at > license_expiry or current >= license_expiry
        ):
            raise ValueError("Ücretli lisansın asıl süresi dolmuş.")
    else:
        trial_expiry = claims.get("trial_expires_at_ms")
        if entitlement != "trial" or duration > OFFLINE_TRIAL_LEASE_MS:
            raise ValueError("Deneme offline lisans sınırı geçersiz.")
        if not isinstance(trial_expiry, int) or expires_at > trial_expiry or current >= trial_expiry:
            raise ValueError("Deneme süresi dolmuş.")

    return claims
