"""Windows DPAPI ile kullanıcı hesabına bağlı şifreli yerel JSON deposu.

Windows'ta şifreleme anahtarı EXE'ye gömülmez; DPAPI current-user alanını kullanır.
Windows dışı geliştirme/test ortamlarında AES-GCM kullanılır.
"""
from __future__ import annotations

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
