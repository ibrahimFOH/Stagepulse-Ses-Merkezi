# -*- coding: utf-8 -*-
"""Stagepulse Ses Mühendisliği Merkezi - tek pencere, çevrimdışı öncelikli uygulama."""
from __future__ import annotations

import json
import os
import shutil
import socket
import ipaddress
import math
import re
import struct
import sys
import threading
import time
import traceback
import webbrowser
import hashlib
import uuid
import tempfile
import subprocess
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse, urlsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from core.acoustic_api import AcousticAnalysisApi

APP_NAME = "Stagepulse Ses Mühendisliği Merkezi"
# 4.0.0: System Designer, SPL Coverage ve Sub-Top Alignment
APP_VERSION = "4.0.5"
SUPABASE_URL = "https://itasctyjzyewcykozuex.supabase.co"
SUPABASE_PUBLISHABLE_KEY = "sb_publishable_tP3CMhVAjv6FNtrkYfVEOA_dbF9m8Jb"
WEBSITE_URL = "https://stagepulse.com.tr"
UPDATE_CHANNEL = "stable"
UPDATE_MANIFEST_URL = f"https://itasctyjzyewcykozuex.supabase.co/functions/v1/ses-merkezi-updates?platform=windows&channel={UPDATE_CHANNEL}"
OFFLINE_TRIAL_LICENSE_GRACE_DAYS = 7
OFFLINE_PAID_LICENSE_GRACE_DAYS = 14
OFFLINE_LICENSE_GRACE_DAYS = OFFLINE_TRIAL_LICENSE_GRACE_DAYS
# Ücretli offline lisans en fazla 14 gün, deneme lisansı en fazla 7 gün geçerlidir.
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    RESOURCE_ROOT = Path(sys._MEIPASS).resolve()
    APP_HOME = Path(sys.executable).resolve().parent
else:
    RESOURCE_ROOT = Path(__file__).resolve().parent
    APP_HOME = RESOURCE_ROOT

UI_ROOT = RESOURCE_ROOT / "ui"
TOOLS_ROOT = RESOURCE_ROOT / "araclar"
DOCS_ROOT = RESOURCE_ROOT / "docs"

if os.name == "nt":
    DATA_ROOT = Path(os.environ.get("APPDATA", str(Path.home()))) / "Stagepulse" / "SesMerkezi"
else:
    DATA_ROOT = Path.home() / ".stagepulse" / "ses-merkezi"
DATA_ROOT.mkdir(parents=True, exist_ok=True)
PROFILE_PATH = DATA_ROOT / "ogrenci_profilleri.dat"
LEGACY_PROFILE_PATH = DATA_ROOT / "ogrenci_profilleri.json"
DEVICE_ID_PATH = DATA_ROOT / "cihaz_kimligi.dat"
LICENSE_CACHE_PATH = DATA_ROOT / "lisans_dogrulamasi.dat"
SESSION_PATH = DATA_ROOT / "hesap_oturumu.dat"

EDUCATIONAL_DOCS = [
    ("00_BASLANGIC_TR.md", "Başlangıç ve güvenli kullanım"),
    ("01_CANLI_SES_IS_AKISI_TR.md", "Canlı ses iş akışı"),
    ("02_PA_ARRAY_SUB_HIZALAMA_TR.md", "PA, array ve sub hizalama"),
    ("03_RF_KABLOSUZ_SISTEM_TR.md", "RF, kablosuz ve IEM"),
    ("04_SES_KALITE_KONTROL_TR.md", "Ses kalite kontrolü"),
    ("05_KONUSMA_KAYDI_HAZIRLIK_TR.md", "Konuşma kaydı"),
    ("06_YAPAY_ZEKA_ISTEMLERI_TR.md", "Yapay zekâ iş akışları"),
    ("07_GURULTU_YALITIM_RAPORU_TR.md", "Gürültü ve yalıtım"),
    ("08_SES_AI_ARASTIRMA_REHBERI_TR.md", "Ses analizi ve yapay zekâ araştırması"),
    ("09_API_GIZLILIK_TR.md", "Gizlilik ve API kullanımı"),
    ("10_MUZIK_PRODUKSIYONU_VE_OGRENME_TR.md", "Müzik prodüksiyonu"),
    ("MIKS_MASTERING_KAYNAK_REHBERI_TR.md", "Miks ve mastering kaynak rehberi"),
    ("EGITIM_DALLARI_USTA_YOLU_VE_FIYATLANDIRMA_TR.md", "Eğitim dalları, usta yolu ve paketler"),
]

# Dağıtıma yalnızca öğrenciye yönelik eğitim PDF'leri alınır. Eğitmen kitapları,
# fiyat teklifleri, iç denetim raporları ve teknik geliştirme belgeleri bu listede yoktur.
EDUCATIONAL_PDF_ROOT = RESOURCE_ROOT / "egitim_paketleri"
STUDENT_PDFS = [
    {"file": "00_Uygulama_Kullanimi_Ogrenci.pdf", "title": "Uygulamayı Kullanma Rehberi", "description": "Araçlar, çevrimdışı kullanım, mikrofon/RTA sorun giderme ve güvenli öğrenci akışı."},
    {"file": "01_Ses_Muhendisligi_Ogrenci_Ders_Kitabi.pdf", "title": "Ses Mühendisliği Öğrenci Ders Kitabı", "description": "Sıfırdan ileri seviyeye 35 ders; Türkçe anlatım, teknik terimler, formüller, uygulamalar ve vaka analizleri."},
    {"file": "02_Canli_Ses_Live_Sound_Ogrenci_Dersleri.pdf", "title": "Canlı Ses / Live Sound Öğrenci Dersleri", "description": "FOH, dijital konsol sinyal akışı, sahne patch, monitör/IEM, PA, DSP, gecikme ve canlı teslim iş akışları."},
    {"file": "03_Studio_Ses_Muhendisligi_Ogrenci_Dersleri.pdf", "title": "Stüdyo Ses Mühendisliği Öğrenci Dersleri", "description": "Stüdyo kayıt, düzenleme, miks, kalite kontrol, sorun giderme ve prodüksiyon çalışmaları."},
    {"file": "04_Dijital_Ses_Mikseri_Ogrenci_Calisma_Kitabi.pdf", "title": "Dijital Ses Mikseri Öğrenci Çalışma Kitabı", "description": "12 günlük uygulama planı, gözlenebilir kanıtlar, sinyal akışı, seviye ve güvenli kullanım alıştırmaları."},
    {"file": "05_Canli_Ses_Mikseri_Hizli_Basvuru.pdf", "title": "Canlı Ses Mikseri Hızlı Başvuru", "description": "Mikser başında hızlı başvuru için gain, phantom, HPF, mute, bus ve etkinlik öncesi kontroller."},
    {"file": "06_Ogrenci_Uygulama_Formlari.pdf", "title": "Öğrenci Uygulama Formları", "description": "Konsol, sinyal akışı, metre gözlemi, uygulama adımları ve öz değerlendirme kayıtları."},
    {"file": "07_Saha_Olcumu_SPL_Raporlama_Egitimi.pdf", "title": "Saha Ölçümü, SPL ve Raporlama Eğitimi", "description": "Ölçüm koşulları, sistem devreye alma, SPL veri kaydı, saha notları ve raporlama sınırları."},
    {"file": "08_SPL_Alan_RTA_Teknik_Uygulama_Eki.pdf", "title": "SPL, Alan Boyutlandırma ve RTA Teknik Uygulama Eki", "description": "Çözümlü dB/SPL, mesafe, alan kapsaması, oda modları, güvenli maruziyet ve gerçek zamanlı RTA karar desteği."},
    {"file": "09_SPL_dB_3D_Gorsel_Atlasi.pdf", "title": "SPL, dB ve 3D Görsel Atlası", "description": "Hesaplanan alan haritaları, gerçekçi kavramsal PA görseli, dB basınç/enerji ilişkileri ve sınırlar."},
    {"file": "10_Midas_M32_Live_Uygulamali_Egitim.pdf", "title": "Midas M32 Live Uygulamalı Eğitim", "description": "Sinyal akışı, gain staging, bus/monitor, AES50, efektler, sahne kayıtları ve canlı uygulama kontrol listeleri."},
    {"file": "11_Yamaha_CL5_Uygulamali_Egitim.pdf", "title": "Yamaha CL5 Uygulamalı Eğitim", "description": "Selected Channel, Centralogic, Dante, HA, mix bus, scene recall güvenliği ve canlı show iş akışı."},
    {"file": "12_Allen_Heath_Avantis_Uygulamali_Egitim.pdf", "title": "Allen & Heath Avantis Uygulamalı Eğitim", "description": "Continuity UI, bank view, I/O patch, bus, scene/show yönetimi, FX, opsiyonlar ve canlı sorun giderme."},
]


def _safe_json_file(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback


def _atomic_json_write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def _secure_read(path: Path, fallback: Any) -> Any:
    from core.secure_store import read_json
    return read_json(path, fallback)


def _secure_write(path: Path, data: Any) -> None:
    from core.secure_store import write_json
    write_json(path, data)


def _installation_device_hash() -> str:
    """Create a random per-installation identifier; do not collect a hardware fingerprint."""
    try:
        stored = _secure_read(DEVICE_ID_PATH, {})
        device_id = stored.get("id") if isinstance(stored, dict) else None
        if not isinstance(device_id, str) or len(device_id) < 32:
            device_id = str(uuid.uuid4()) + str(uuid.uuid4())
            _secure_write(DEVICE_ID_PATH, {"id": device_id, "created_at": time.time()})
        return hashlib.sha256(device_id.encode("utf-8")).hexdigest()
    except Exception as exc:
        raise RuntimeError(f"Bu Windows kullanıcısı için güvenli cihaz kimliği oluşturulamadı: {exc}") from exc


def _version_tuple(value: Any) -> tuple[int, ...]:
    pieces = str(value or "0").strip().split(".")
    if not pieces or any(not piece.isdigit() for piece in pieces):
        raise ValueError("Sürüm numarası geçersiz.")
    return tuple(int(piece) for piece in pieces[:4])


def _dialog_path(result: Any) -> str | None:
    if not result:
        return None
    if isinstance(result, (list, tuple)):
        return str(result[0]) if result else None
    return str(result)


class AppApi(AcousticAnalysisApi):
    """WebView2 ön yüzüne açılan sınırlı yerel API. Dosya yolları kullanıcı diyaloğuyla seçilir."""
    def __init__(self) -> None:
        self.window = None
        self._selected_wav_path: str | None = None
        self._ebu_test_folder: str | None = None
        self._rta_capture = None
        self._tf_capture = None
        self._session: dict[str, Any] | None = None  # Tokens are encrypted at rest with the Windows user DPAPI key.
        self._account_context: dict[str, Any] | None = None

    def _get_rta_capture(self):
        if self._rta_capture is None:
            from core.rta_capture import RTACapture
            self._rta_capture = RTACapture()
        return self._rta_capture

    def list_rta_devices(self) -> list[dict[str, Any]]:
        """List native PortAudio input devices; no WebView browser permission is needed."""
        from core.rta_capture import list_input_devices
        return list_input_devices()

    def start_rta(self, device_index: Any = None, fft_size: int = 16384) -> dict[str, Any]:
        """Start native PC microphone capture for the live RTA."""
        if device_index in (None, "", "default"):
            selected = None
        else:
            try:
                selected = int(device_index)
            except (TypeError, ValueError) as exc:
                raise ValueError("Mikrofon aygıt seçimi geçersiz.") from exc
        try:
            n = int(fft_size)
        except (TypeError, ValueError) as exc:
            raise ValueError("FFT boyutu sayısal olmalı.") from exc
        return self._get_rta_capture().start(selected, n)

    def calibrate_rta_spl(self, reference_spl_db: Any = 94.0) -> dict[str, Any]:
        """Calibrate the active native RTA input against a physical sound calibrator."""
        try:
            reference = float(reference_spl_db)
        except (TypeError, ValueError) as exc:
            raise ValueError("Kalibratör referansı sayısal olmalı.") from exc
        return self._get_rta_capture().calibrate_spl(reference)

    def get_rta_snapshot(self, mode: str = "third", min_hz: Any = 20,
                         max_hz: Any = 20000) -> dict[str, Any]:
        if mode not in ("third", "octave"):
            raise ValueError("Bant modu geçersiz.")
        try:
            low, high = float(min_hz), float(max_hz)
        except (TypeError, ValueError) as exc:
            raise ValueError("Frekans aralığı sayısal olmalı.") from exc
        if not (20 <= low < high <= 20000):
            raise ValueError("Frekans aralığı 20 Hz–20 kHz içinde olmalı.")
        return self._get_rta_capture().snapshot(mode, low, high)

    def stop_rta(self) -> dict[str, Any]:
        if self._rta_capture is None:
            return {"ok": True, "running": False}
        return self._rta_capture.stop()


    def send_osc_message(self, host: Any, port: Any, address: Any,
                         value: Any, value_type: Any = "float") -> dict[str, Any]:
        """Send one explicitly requested OSC message as a local UDP datagram."""
        try:
            target_ip = ipaddress.ip_address(str(host).strip())
        except ValueError as exc:
            raise ValueError("OSC hedefi geçerli bir IPv4 adresi olmalı.") from exc
        if target_ip.version != 4:
            raise ValueError("OSC hedefi IPv4 adresi olmalı.")
        port_text = str(port).strip()
        if not re.fullmatch(r"\d{1,5}", port_text):
            raise ValueError("OSC UDP portu 1–65535 arasında tam sayı olmalı.")
        target_port = int(port_text)
        if not 1 <= target_port <= 65535:
            raise ValueError("OSC UDP portu 1–65535 arasında olmalı.")
        osc_address = str(address).strip()
        if not re.fullmatch(r"/[A-Za-z0-9_./-]{1,127}", osc_address):
            raise ValueError("OSC adresi / ile başlamalı ve yalnızca harf, rakam, nokta, alt çizgi, tire veya / içermeli.")
        kind = str(value_type or "float").strip().lower()

        def padded_string(item: str) -> bytes:
            raw = item.encode("utf-8")
            if b"\x00" in raw:
                raise ValueError("OSC metin alanı boş karakter içeremez.")
            return raw + b"\x00" + (b"\x00" * (-(len(raw) + 1) % 4))

        if kind == "float":
            try:
                numeric = float(str(value).strip().replace(",", "."))
            except (TypeError, ValueError) as exc:
                raise ValueError("OSC float değeri sayısal olmalı.") from exc
            if not math.isfinite(numeric) or abs(numeric) > 3.4028235e38:
                raise ValueError("OSC float değeri sonlu ve geçerli olmalı.")
            argument = struct.pack(">f", numeric)
            tag = ",f"
        elif kind == "int":
            try:
                numeric = int(str(value).strip())
            except (TypeError, ValueError) as exc:
                raise ValueError("OSC integer değeri tam sayı olmalı.") from exc
            if not -2147483648 <= numeric <= 2147483647:
                raise ValueError("OSC integer değeri 32 bit sınırını aşamaz.")
            argument = struct.pack(">i", numeric)
            tag = ",i"
        elif kind == "string":
            string_value = str(value)
            if len(string_value.encode("utf-8")) > 256:
                raise ValueError("OSC metin değeri 256 UTF-8 baytını aşamaz.")
            argument = padded_string(string_value)
            tag = ",s"
        else:
            raise ValueError("OSC veri türü float, int veya string olmalı.")

        packet = padded_string(osc_address) + padded_string(tag) + argument
        if len(packet) > 1024:
            raise ValueError("OSC paketi 1024 bayt sınırını aşıyor.")
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp:
            udp.settimeout(1.0)
            udp.sendto(packet, (str(target_ip), target_port))
        return {
            "ok": True, "host": str(target_ip), "port": target_port,
            "address": osc_address, "value_type": kind, "bytes": len(packet),
            "acknowledged": False,
        }

    def _get_tf_capture(self):
        if self._tf_capture is None:
            from core.tf_capture import TFCapture
            self._tf_capture = TFCapture()
        return self._tf_capture

    def list_tf_devices(self) -> list[dict[str, Any]]:
        """List only native input devices with at least two simultaneous channels."""
        from core.rta_capture import list_input_devices
        return [device for device in list_input_devices()
                if int(device.get("max_input_channels", 0) or 0) >= 2]

    def start_tf(self, device_index: Any = None, fft_size: int = 16384,
                 averages: int = 8) -> dict[str, Any]:
        if device_index in (None, "", "default"):
            selected = None
        else:
            try:
                selected = int(device_index)
            except (TypeError, ValueError) as exc:
                raise ValueError("TF aygıt seçimi geçersiz.") from exc
        return self._get_tf_capture().start(selected, int(fft_size), int(averages))

    def get_tf_snapshot(self, mode: str = "third", min_hz: Any = 20,
                        max_hz: Any = 20000) -> dict[str, Any]:
        if mode not in ("third", "octave"):
            raise ValueError("TF bant modu geçersiz.")
        try:
            low, high = float(min_hz), float(max_hz)
        except (TypeError, ValueError) as exc:
            raise ValueError("TF frekans aralığı sayısal olmalı.") from exc
        if not (20 <= low < high <= 20000):
            raise ValueError("TF frekans aralığı 20 Hz–20 kHz içinde olmalı.")
        return self._get_tf_capture().snapshot(mode, low, high)

    def stop_tf(self) -> dict[str, Any]:
        if self._tf_capture is None:
            return {"ok": True, "running": False}
        return self._tf_capture.stop()

    def app_info(self) -> dict[str, Any]:
        cached = self._cached_license_status()
        return {
            "name": APP_NAME, "version": APP_VERSION,
            "mode": "7 günlük hesap denemesi veya FULL PAKET lisansı / çevrimdışı öncelikli",
            "demo_mode": False,
            "license_required_for_local_tools": True,
            "data_dir": str(DATA_ROOT), "runtime": "WebView2",
            "website": WEBSITE_URL, "update_manifest": UPDATE_MANIFEST_URL,
            "offline_license_grace_days": OFFLINE_LICENSE_GRACE_DAYS,
            "offline_paid_license_grace_days": OFFLINE_PAID_LICENSE_GRACE_DAYS,
            "offline_trial_license_grace_days": OFFLINE_TRIAL_LICENSE_GRACE_DAYS,
            "cached_license": cached,
            "backend": "Supabase lisans ve öğretmen onaylı ilerleme servisi",
        }

    def _cached_license_status(self) -> dict[str, Any]:
        cached = _secure_read(LICENSE_CACHE_PATH, {})
        if not isinstance(cached, dict):
            return {"active": False, "reason": "not_verified"}
        user_id = str(cached.get("user_id") or "")
        lease = cached.get("offline_lease")
        public_key = cached.get("offline_lease_public_key")
        if not user_id or not isinstance(lease, dict) or not isinstance(public_key, str):
            return {"active": False, "reason": "offline_lease_missing"}
        try:
            from core.secure_store import verify_offline_lease
            now_ms = int(time.time() * 1000)
            claims = verify_offline_lease(
                lease,
                expected_user_id=user_id,
                expected_device_hash=_installation_device_hash(),
                expected_app_id="ses-merkezi",
                expected_platform="windows",
                public_key_pem=public_key,
                now_ms=now_ms,
                last_seen_ms=int(cached.get("last_seen_at_ms") or 0),
            )
            _secure_write(LICENSE_CACHE_PATH, {
                "user_id": user_id,
                "offline_lease": lease,
                "offline_lease_public_key": public_key,
                "last_seen_at_ms": now_ms,
            })
            is_trial = claims.get("entitlement") == "trial"
            return {
                "active": True,
                "paid": claims.get("paid") is True,
                "trial_active": is_trial,
                "reason": "offline_grace",
                "plan_code": claims.get("plan_code", "trial" if is_trial else "student"),
                "bundle_code": claims.get("bundle_code", "trial" if is_trial else "start"),
                "expires_at": claims.get("license_expires_at_ms"),
                "lease_expires_at_ms": claims.get("expires_at_ms"),
                "user_id": user_id,
            }
        except (ValueError, TypeError, RuntimeError, OverflowError):
            return {"active": False, "reason": "offline_lease_invalid"}

    def load_profiles(self) -> dict[str, Any]:
        data = _secure_read(PROFILE_PATH, None)
        if data is None and PROFILE_PATH.is_file():
            raise RuntimeError("Şifreli öğrenci profili okunamıyor. Veri dosyası bozuk veya başka bir Windows kullanıcısına ait; kaydı otomatik sıfırlamadım.")
        if data is None and LEGACY_PROFILE_PATH.is_file():
            # One-time migration from the older plaintext JSON profile format.
            legacy = _safe_json_file(LEGACY_PROFILE_PATH, {"profiles": {}})
            if isinstance(legacy, dict) and isinstance(legacy.get("profiles"), dict):
                data = legacy
                _secure_write(PROFILE_PATH, data)
                try:
                    LEGACY_PROFILE_PATH.unlink()
                except OSError:
                    # The encrypted replacement is already written; leave a warning for the user rather than losing data.
                    pass
        if not isinstance(data, dict) or not isinstance(data.get("profiles"), dict):
            return {"profiles": {}}
        return data

    def save_profile(self, name: str, profile_json: str) -> dict[str, Any]:
        clean_name = " ".join(str(name).split())[:80]
        if not clean_name:
            raise ValueError("Öğrenci adı boş olamaz.")
        if len(str(profile_json).encode("utf-8")) > 1_000_000:
            raise ValueError("Öğrenci profili 1 MB sınırını aşamaz.")
        try:
            payload = json.loads(profile_json)
        except json.JSONDecodeError as exc:
            raise ValueError("Öğrenci verisi geçerli JSON değil.") from exc
        if not isinstance(payload, dict):
            raise ValueError("Öğrenci profili bir nesne olmalıdır.")
        data = self.load_profiles()
        data["profiles"][clean_name] = payload
        _secure_write(PROFILE_PATH, data)
        return {"ok": True, "name": clean_name, "count": len(data["profiles"])}

    def delete_profile(self, name: str) -> dict[str, Any]:
        data = self.load_profiles()
        data.get("profiles", {}).pop(str(name), None)
        _secure_write(PROFILE_PATH, data)
        return {"ok": True, "count": len(data.get("profiles", {}))}

    def list_docs(self) -> list[dict[str, str]]:
        return [{"file": filename, "title": title} for filename, title in EDUCATIONAL_DOCS if (DOCS_ROOT / filename).is_file()]

    def read_doc(self, filename: str) -> dict[str, str]:
        allowed = {name for name, _title in EDUCATIONAL_DOCS}
        name = Path(str(filename)).name
        if name not in allowed:
            raise ValueError("Bu belge öğrenci arayüzü için izin verilen listede değil.")
        path = (DOCS_ROOT / name).resolve()
        if DOCS_ROOT.resolve() not in path.parents or not path.is_file():
            raise FileNotFoundError("Belge bulunamadı.")
        return {"file": name, "title": dict(EDUCATIONAL_DOCS)[name], "content": path.read_text(encoding="utf-8")}

    def list_student_pdfs(self) -> list[dict[str, str]]:
        """Öğrenciye yönelik ve izin listesinde bulunan PDF'leri listeler."""
        result = []
        for item in STUDENT_PDFS:
            path = (EDUCATIONAL_PDF_ROOT / item["file"]).resolve()
            if path.is_file() and EDUCATIONAL_PDF_ROOT.resolve() in path.parents:
                result.append({**item, "url": "/egitim_paketleri/" + item["file"]})
        return result

    def save_student_pdf_dialog(self, filename: str) -> dict[str, Any]:
        """Yalnızca katalogdaki öğrenci PDF'sini kullanıcının seçtiği yere kopyalar."""
        import webview
        item = next((x for x in STUDENT_PDFS if x["file"] == Path(str(filename)).name), None)
        if item is None:
            raise ValueError("Bu dosya öğrenci eğitim kataloğunda bulunmuyor.")
        source = (EDUCATIONAL_PDF_ROOT / item["file"]).resolve()
        if EDUCATIONAL_PDF_ROOT.resolve() not in source.parents or not source.is_file():
            return {"ok": False, "error": "Seçilen eğitim PDF'si pakette bulunamadı."}
        destination = _dialog_path(self.window.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename=item["file"],
            file_types=("PDF dosyası (*.pdf)",),
        ))
        if not destination:
            return {"ok": False, "cancelled": True}
        target = Path(destination)
        if target.suffix.lower() != ".pdf":
            target = target.with_suffix(".pdf")
        if target.resolve() != source.resolve():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        return {"ok": True, "path": str(target), "title": item["title"]}

    def save_pdf_dialog(self) -> dict[str, Any]:
        """Eski arayüz çağrıları için ana öğrenci ders kitabını kaydeder."""
        return self.save_student_pdf_dialog(STUDENT_PDFS[1]["file"])


    def save_generated_pdf_dialog(self, filename: str, encoded: str) -> dict[str, Any]:
        """Kullanıcının ürettiği PDF'yi güvenli dosya seçiciyle dışa aktarır."""
        import base64
        import binascii
        import webview

        safe_name = Path(str(filename)).name
        if not safe_name.lower().endswith(".pdf"):
            safe_name = "Stagepulse_Katilim_Belgesi.pdf"
        if not encoded or len(encoded) > 24 * 1024 * 1024:
            raise ValueError("PDF verisi boş veya izin verilen boyutu aşıyor.")
        try:
            data = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("PDF verisi geçerli Base64 değil.") from exc
        if len(data) > 18 * 1024 * 1024 or not data.startswith(b"%PDF-"):
            raise ValueError("Yalnızca geçerli PDF dosyası dışa aktarılabilir.")
        destination = _dialog_path(self.window.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename=safe_name,
            file_types=("PDF dosyası (*.pdf)",),
        ))
        if not destination:
            return {"ok": False, "cancelled": True}
        target = Path(destination)
        if target.suffix.lower() != ".pdf":
            target = target.with_suffix(".pdf")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return {"ok": True, "path": str(target), "filename": target.name}

    def pick_wav(self) -> str | None:
        import webview
        chosen = _dialog_path(self.window.create_file_dialog(
            webview.OPEN_DIALOG, allow_multiple=False,
            file_types=("PCM WAV dosyaları (*.wav)",)
        ))
        self._selected_wav_path = str(Path(chosen).resolve()) if chosen else None
        return chosen

    def analyze_wav(self, path: str) -> dict[str, Any]:
        # Yalnızca native dosya seçicisinden yeni seçilmiş WAV okunabilir.
        chosen = self._selected_wav_path
        self._selected_wav_path = None
        if not chosen or not path or Path(path).resolve() != Path(chosen):
            raise ValueError("WAV analizinde dosyayı uygulamanın dosya seçicisiyle seçmelisin.")
        if Path(chosen).suffix.lower() != ".wav":
            raise ValueError("Bu analiz aracı yalnızca WAV dosyalarını destekler.")
        from core.audio_tools import analyze_wav
        return analyze_wav(chosen)

    def normalize_lufs_dialog(self, target_lufs: float = -14.0, target_tp: float = -1.0) -> dict[str, Any]:
        import webview
        src = _dialog_path(self.window.create_file_dialog(
            webview.OPEN_DIALOG, allow_multiple=False,
            file_types=("Desteklenen ses dosyaları (*.wav;*.flac;*.aiff;*.aif)",)
        ))
        if not src:
            return {"cancelled": True}
        default_name = Path(src).stem + f"_{str(target_lufs).replace('-', 'eksi').replace('.', '_')}LUFS.wav"
        out = _dialog_path(self.window.create_file_dialog(
            webview.SAVE_DIALOG, save_filename=default_name,
            file_types=("WAV PCM 24-bit (*.wav)",)
        ))
        if not out:
            return {"cancelled": True}
        if not out.lower().endswith(".wav"):
            out += ".wav"
        from core.audio_tools import normalize_lufs
        return normalize_lufs(src, out, float(target_lufs), float(target_tp))


    def select_ebu_test_folder(self) -> dict[str, Any]:
        """Select the extracted EBU Loudness Test Set folder using a native dialog."""
        import webview
        chosen = _dialog_path(self.window.create_file_dialog(
            webview.FOLDER_DIALOG, allow_multiple=False,
        ))
        self._ebu_test_folder = str(Path(chosen).resolve()) if chosen else None
        return {
            "ok": bool(self._ebu_test_folder),
            "cancelled": not bool(self._ebu_test_folder),
            "folder_name": Path(self._ebu_test_folder).name if self._ebu_test_folder else "",
        }

    def run_ebu_loudness_validation(self, tolerance_lu: Any = 0.2) -> dict[str, Any]:
        """Run EBU WAV validation with the reference table bundled in the application."""
        if not self._ebu_test_folder:
            raise RuntimeError("Önce çıkarılmış EBU Loudness Test Set klasörünü seç.")
        from core.audio_tools import validate_ebu_test_set
        return validate_ebu_test_set(
            self._ebu_test_folder, tolerance_lu=float(tolerance_lu)
        )

    def run_spl_filter_self_test(self) -> dict[str, Any]:
        """Run software-only A/C/Z weighting response checks."""
        from core.acoustic_engine import run_spl_filter_self_test
        return run_spl_filter_self_test()

    def ai_provider_catalog(self) -> list[dict[str, Any]]:
        from core.ai_providers import PROVIDERS
        return [{"id": key, **value} for key, value in PROVIDERS.items()]

    def ai_list_models(self) -> dict[str, Any]:
        """List only models installed in the local Ollama instance."""
        from core.ai_providers import list_ollama_models, select_ollama_model, PROVIDERS
        models = list_ollama_models(PROVIDERS["ollama"]["endpoint"])
        names = [item["name"] for item in models]
        return {
            "ok": True,
            "host": "http://127.0.0.1:11434",
            "models": models,
            "routes": {
                "general": select_ollama_model("Merhaba", names),
                "coding": select_ollama_model("Python kodunu debug et", names),
                "analysis": select_ollama_model("Kapsamlı SPL mühendislik analizi", names),
            },
        }

    def ai_chat(self, provider: str, model: str, api_key: str, prompt: str, endpoint: str = "",
                request_options: dict[str, Any] | None = None, keep_alive: str = "30m",
                think: bool = False) -> dict[str, Any]:
        """Run AI providers while a paid license or the authenticated demo is valid."""
        from core.ai_providers import PROVIDERS, _validate_endpoint, chat
        provider_id = str(provider or "auto").strip().lower()
        if provider_id == "auto":
            local_endpoint = PROVIDERS["ollama"]["endpoint"]
            _validate_endpoint("ollama", local_endpoint)
            if not self._cached_license_status().get("active"):
                raise RuntimeError("Stagepulse Ses Merkezi için etkin FULL PAKET lisansı veya süresi dolmamış demo gerekir.")
            try:
                result = chat("ollama", "auto", "", prompt, local_endpoint, request_options, keep_alive, think)
                result["provider"] = "auto"
                result["routing"] = "ollama"
                return result
            except Exception as local_error:
                if not str(api_key or "").strip():
                    raise RuntimeError(
                        "Yerel Ollama yanıt vermedi ve Groq yedek anahtarı girilmemiş. "
                        f"Ollama hatası: {local_error}"
                    ) from local_error
                if not self._cached_license_status().get("active"):
                    raise RuntimeError(
                        "Yerel Ollama yanıt vermedi. Groq yedeğine geçmek için etkin FULL PAKET lisansı veya demo gerekir. "
                        f"Ollama hatası: {local_error}"
                    ) from local_error
                fallback = chat(
                    "groq", PROVIDERS["groq"]["model"], api_key, prompt,
                    PROVIDERS["groq"]["endpoint"], request_options,
                )
                fallback["provider"] = "auto"
                fallback["routing"] = "groq"
                fallback["fallback_reason"] = str(local_error)[:500]
                return fallback
        if provider_id not in PROVIDERS:
            raise ValueError("Yalnızca otomatik, yerel Ollama veya Groq sağlayıcısı kullanılabilir.")
        raw_endpoint = str(endpoint or PROVIDERS[provider_id]["endpoint"]).strip()
        _validate_endpoint(provider_id, raw_endpoint)
        if not self._cached_license_status().get("active"):
            raise RuntimeError("Stagepulse Ses Merkezi için etkin FULL PAKET lisansı veya süresi dolmamış demo gerekir.")
        return chat(provider_id, model, api_key, prompt, raw_endpoint, request_options, keep_alive, think)


    def _auth_request(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        request = Request(
            SUPABASE_URL + path, data=data,
            headers={"Content-Type": "application/json", "Accept": "application/json", "apikey": SUPABASE_PUBLISHABLE_KEY},
            method="POST",
        )
        try:
            with urlopen(request, timeout=20) as response:
                raw = response.read(1_000_001)
            if len(raw) > 1_000_000:
                raise RuntimeError("Kimlik servisi yanıt sınırını aştı.")
            return json.loads(raw.decode("utf-8"))
        except HTTPError as exc:
            raw = exc.read(2048).decode("utf-8", errors="replace")
            try:
                info = json.loads(raw)
                detail = info.get("msg") or info.get("message") or info.get("error_description") or info.get("error") or ""
            except json.JSONDecodeError:
                detail = ""
            raise RuntimeError(str(detail or f"Kimlik servisi HTTP {exc.code} döndürdü.")[:400]) from exc
        except (URLError, TimeoutError) as exc:
            raise RuntimeError("Stagepulse hesabına ulaşılamadı. İnternet bağlantısını kontrol et.") from exc
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise RuntimeError("Kimlik servisi geçerli JSON döndürmedi.") from exc

    @staticmethod
    def _student_phone(identity: str) -> str | None:
        value = str(identity).strip()
        if "@" in value:
            return None
        digits = "".join(ch for ch in value if ch.isdigit())
        if digits.startswith("0") and len(digits) == 11:
            digits = "90" + digits[1:]
        elif digits.startswith("5") and len(digits) == 10:
            digits = "90" + digits
        if not digits.startswith("90") or len(digits) != 12 or not digits[2:].startswith("5"):
            raise ValueError("Telefonu 05xx xxx xx xx veya +90 5xx xxx xx xx biçiminde gir.")
        return "+" + digits

    @staticmethod
    def _auth_identity_payload(identity: str) -> dict[str, str]:
        value = str(identity).strip()
        if "@" in value:
            email = value.lower()
            if len(email) > 320 or email.count("@") != 1 or "." not in email.rsplit("@", 1)[-1]:
                raise ValueError("Geçerli e-posta adresi veya telefon numarası gir.")
            return {"email": email}
        phone = AppApi._student_phone(value)
        return {"email": phone.lstrip("+") + "@students.stagepulse.invalid"}

    def auth_signup(self, identity: str, password: str, display_name: str = "") -> dict[str, Any]:
        phone = self._student_phone(identity)
        password = str(password)
        display_name = " ".join(str(display_name).split())[:120]
        if len(password) < 8 or len(password) > 256:
            raise ValueError("Şifre en az 8, en fazla 256 karakter olmalı.")
        if phone:
            if len(display_name) < 2:
                raise ValueError("Öğrenci adı en az 2 karakter olmalı.")
            self._public_edge_call("student_signup", {"phone": phone, "password": password, "display_name": display_name})
            result = self._auth_request("/auth/v1/token?grant_type=password", {
                "email": phone.lstrip("+") + "@students.stagepulse.invalid", "password": password,
            })
        else:
            auth_identity = self._auth_identity_payload(identity)
            result = self._auth_request("/auth/v1/signup", {**auth_identity, "password": password, "data": {"display_name": display_name}})
        if result.get("access_token") and result.get("refresh_token"):
            self._session = result
            self._account_context = self._edge_call("context", {"device_hash": _installation_device_hash()})
            self._persist_auth_session()
            self._cache_server_license(self._account_context)
        session_created = bool(result.get("access_token"))
        message = (
            "Öğrenci hesabı oluşturuldu ve giriş yapıldı."
            if session_created
            else "Hesap oluşturuldu. Giriş yapmadan önce e-posta adresini doğrula."
        )
        return {"ok": True, "session_created": session_created, "message": message}

    def auth_login(self, identity: str, password: str) -> dict[str, Any]:
        phone = self._student_phone(identity)
        auth_identity = self._auth_identity_payload(identity)
        if not password:
            raise ValueError("Şifre gerekli.")
        credentials = {**auth_identity, "password": str(password)}
        try:
            result = self._auth_request("/auth/v1/token?grant_type=password", credentials)
        except RuntimeError as exc:
            detail = str(exc).lower()
            legacy_phone_error = any(marker in detail for marker in (
                "invalid login credentials",
                "invalid_credentials",
                "user not found",
                "kimlik servisi http 400",
                "kimlik servisi http 401",
            ))
            if not phone or not legacy_phone_error:
                raise
            # Eski Supabase Phone Auth hesaplarını, yeni dahili e-posta kimliğine geçmeden önce destekle.
            result = self._auth_request("/auth/v1/token?grant_type=password", {
                "phone": phone,
                "password": str(password),
            })
        if not result.get("access_token") or not result.get("user"):
            raise RuntimeError("Giriş başarısız. E-postayı doğruladığını ve doğru şifre kullandığını kontrol et.")
        if not result.get("refresh_token"):
            raise RuntimeError("Kimlik servisi yenileme belirteci döndürmedi; güvenli oturum saklanamadı.")
        self._session = result
        try:
            context = self._edge_call("context", {"device_hash": _installation_device_hash()})
        except Exception:
            self._session = None
            self._account_context = None
            raise
        self._account_context = context
        self._persist_auth_session()
        self._cache_server_license(context)
        return {"ok": True, "context": context}

    def _persist_auth_session(self) -> None:
        if not isinstance(self._session, dict) or not self._session.get("refresh_token"):
            raise RuntimeError("Yenilenebilir hesap oturumu bulunamadı.")
        _secure_write(SESSION_PATH, self._session)

    def _clear_auth_session(self) -> None:
        self._session = None
        self._account_context = None
        try:
            SESSION_PATH.unlink(missing_ok=True)
        except OSError:
            _secure_write(SESSION_PATH, {})
        _secure_write(LICENSE_CACHE_PATH, {"active": False, "verified_at": time.time(), "reason": "session_invalid"})

    def _auth_user_request(self, access_token: str) -> dict[str, Any] | None:
        request = Request(
            SUPABASE_URL + "/auth/v1/user",
            headers={"Accept": "application/json", "apikey": SUPABASE_PUBLISHABLE_KEY,
                     "Authorization": "Bearer " + access_token},
            method="GET",
        )
        try:
            with urlopen(request, timeout=12) as response:
                raw = response.read(1_000_001)
            if len(raw) > 1_000_000:
                raise RuntimeError("Kimlik servisi yanıt sınırını aştı.")
            return json.loads(raw.decode("utf-8"))
        except HTTPError as exc:
            if exc.code in (401, 403):
                return None
            raise RuntimeError(f"Kimlik servisi HTTP {exc.code} döndürdü.") from exc
        except (URLError, TimeoutError) as exc:
            raise RuntimeError("Stagepulse hesabına ulaşılamadı. İnternet bağlantısını kontrol et.") from exc
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise RuntimeError("Kimlik servisi geçerli JSON döndürmedi.") from exc

    def auth_restore(self) -> dict[str, Any]:
        """Restore a DPAPI-protected session; refresh only when the access token is invalid."""
        stored = _secure_read(SESSION_PATH, {})
        if not isinstance(stored, dict) or not stored.get("refresh_token"):
            self._session = None
            self._account_context = None
            return {"ok": True, "authenticated": False}
        access = str(stored.get("access_token") or "")
        try:
            user = self._auth_user_request(access) if access else None
        except RuntimeError as exc:
            message = str(exc)
            cached = self._cached_license_status()
            stored_user_id = (stored.get("user") or {}).get("id") if isinstance(stored.get("user"), dict) else None
            network_unavailable = "ulaşılamadı" in message.lower() or "çevrimiçi servisine" in message.lower()
            if network_unavailable and cached.get("active") and cached.get("user_id") == stored_user_id:
                self._session = stored
                return {"ok": True, "authenticated": False, "offline": True, "license": cached}
            raise
        if user is not None:
            self._session = stored
        else:
            try:
                refreshed = self._auth_request(
                    "/auth/v1/token?grant_type=refresh_token",
                    {"refresh_token": str(stored["refresh_token"])},
                )
            except RuntimeError as exc:
                message = str(exc)
                if any(code in message for code in ("HTTP 400", "HTTP 401", "HTTP 403")):
                    self._clear_auth_session()
                    return {"ok": True, "authenticated": False}
                cached = self._cached_license_status()
                stored_user_id = (stored.get("user") or {}).get("id") if isinstance(stored.get("user"), dict) else None
                network_unavailable = "ulaşılamadı" in message.lower() or "çevrimiçi servisine" in message.lower()
                if network_unavailable and cached.get("active") and cached.get("user_id") == stored_user_id:
                    self._session = stored
                    return {"ok": True, "authenticated": False, "offline": True, "license": cached}
                raise
            if not refreshed.get("access_token") or not refreshed.get("refresh_token"):
                self._clear_auth_session()
                return {"ok": True, "authenticated": False}
            self._session = refreshed
            self._persist_auth_session()
        try:
            context = self._edge_call("context", {"device_hash": _installation_device_hash()})
        except RuntimeError as exc:
            message = str(exc)
            cached = self._cached_license_status()
            stored_user_id = (stored.get("user") or {}).get("id") if isinstance(stored.get("user"), dict) else None
            network_unavailable = "ulaşılamadı" in message.lower() or "çevrimiçi servisine" in message.lower()
            if network_unavailable and cached.get("active") and cached.get("user_id") == stored_user_id:
                self._session = stored
                return {"ok": True, "authenticated": False, "offline": True, "license": cached}
            raise
        self._account_context = context
        self._cache_server_license(context)
        return {"ok": True, "authenticated": True, "context": context}

    def _public_edge_call(self, action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = {"action": action, **(payload or {}), "app_id": "ses-merkezi", "platform": "windows"}
        request = Request(
            SUPABASE_URL + "/functions/v1/ses-merkezi-desktop",
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json", "apikey": SUPABASE_PUBLISHABLE_KEY},
            method="POST",
        )
        try:
            with urlopen(request, timeout=20) as response:
                raw = response.read(1_000_001)
            if len(raw) > 1_000_000:
                raise RuntimeError("Stagepulse servis yanıtı sınırı aştı.")
            result = json.loads(raw.decode("utf-8"))
        except HTTPError as exc:
            raw = exc.read(2048).decode("utf-8", errors="replace")
            try:
                code = json.loads(raw).get("error", "SERVER_ERROR")
            except json.JSONDecodeError:
                code = "SERVER_ERROR"
            messages = {
                "RATE_LIMITED": "Çok fazla kayıt denemesi yapıldı. Bir süre sonra tekrar dene.",
                "PHONE_ALREADY_REGISTERED": "Bu telefon numarasıyla daha önce hesap oluşturulmuş. Giriş yapmayı dene.",
                "STUDENT_SIGNUP_UNAVAILABLE": "Öğrenci hesabı şu anda oluşturulamadı. Daha sonra tekrar dene.",
            }
            raise RuntimeError(messages.get(str(code), f"Öğrenci hesabı oluşturulamadı ({exc.code}, {code}).")) from exc
        except (URLError, TimeoutError) as exc:
            raise RuntimeError("Stagepulse hesabına ulaşılamadı. İnternet bağlantısını kontrol et.") from exc
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise RuntimeError("Stagepulse servisinden geçersiz yanıt alındı.") from exc
        if not isinstance(result, dict) or result.get("ok") is not True:
            raise RuntimeError(str(result.get("error", "SERVER_ERROR")) if isinstance(result, dict) else "Servis yanıtı geçersiz.")
        return result

    def _edge_call(self, action: str, payload: dict[str, Any] | None = None, function_slug: str = "ses-merkezi-desktop") -> dict[str, Any]:
        if not self._session or not self._session.get("access_token"):
            raise RuntimeError("Önce Stagepulse hesabına giriş yap.")
        body = {
            "action": action,
            **(payload or {}),
            "app_id": "ses-merkezi",
            "platform": "windows",
        }
        request = Request(
            SUPABASE_URL + "/functions/v1/" + function_slug,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json", "apikey": SUPABASE_PUBLISHABLE_KEY,
                     "Authorization": "Bearer " + str(self._session["access_token"])},
            method="POST",
        )
        try:
            with urlopen(request, timeout=20) as response:
                raw = response.read(1_000_001)
            if len(raw) > 1_000_000:
                raise RuntimeError("Stagepulse servis yanıtı sınırı aştı.")
            result = json.loads(raw.decode("utf-8"))
        except HTTPError as exc:
            raw = exc.read(2048).decode("utf-8", errors="replace")
            try:
                code = json.loads(raw).get("error", "SERVER_ERROR")
            except json.JSONDecodeError:
                code = "SERVER_ERROR"
            if exc.code == 401 or code == "UNAUTHENTICATED":
                self._clear_auth_session()
                raise RuntimeError("Oturum geçersiz veya iptal edilmiş. Yeniden giriş yap.") from exc
            messages = {
                "FORBIDDEN_OWNER_ONLY": "Bu işlem yalnızca Stagepulse öğretmen/yönetici hesabına açıktır.",
                "LICENSE_REQUIRED": "Bu öğrenci hesabı için geçerli lisans bulunamadı.",
                "LICENSE_INVALID_OR_EXPIRED": "Lisans anahtarı geçersiz veya süresi dolmuş.",
                "LICENSE_PAYMENT_REQUIRED": "Bu lisans için ödeme henüz onaylanmadı. Satış yöneticisinin ödeme kaydını onaylaması gerekir.",
                "LICENSE_ACTIVATION_LIMIT": "Bu lisansın cihaz aktivasyon sınırı doldu.",
                "STUDENT_ALREADY_LINKED": "Bu öğrenci hesabı başka bir öğretmen hesabına bağlı.",
                "ACCOUNT_NOT_ENROLLED": "Önce Stagepulse hesabına giriş yap ve öğretmeninin verdiği lisansı kullan.",
                "STUDENT_NOT_FOUND": "Öğrenci kaydı bulunamadı veya bu öğretmene bağlı değil.",
                "DEVICE_BOUND_TO_OTHER_USER": "Bu cihaz lisansı başka bir kullanıcı hesabına bağlı.",
            }
            raise RuntimeError(messages.get(str(code), f"Stagepulse servis isteği başarısız oldu ({exc.code}, {code}).")) from exc
        except (URLError, TimeoutError) as exc:
            raise RuntimeError("Stagepulse çevrimiçi servisine ulaşılamadı. Yerel araçlar çevrimdışı kullanılabilir.") from exc
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise RuntimeError("Stagepulse servisinden geçersiz yanıt alındı.") from exc
        if not isinstance(result, dict) or result.get("ok") is not True:
            raise RuntimeError(str(result.get("error", "SERVER_ERROR")) if isinstance(result, dict) else "Servis yanıtı geçersiz.")
        if action == "context":
            self._account_context = result
            self._cache_server_license(result)
        return result

    def _cache_server_license(self, context: dict[str, Any] | None) -> None:
        if not isinstance(context, dict):
            return
        user = context.get("user") if isinstance(context.get("user"), dict) else {}
        user_id = str(user.get("id") or "")
        lease = context.get("offline_lease")
        public_key = context.get("offline_lease_public_key")
        if not user_id or not isinstance(lease, dict) or not isinstance(public_key, str):
            _secure_write(LICENSE_CACHE_PATH, {"active": False, "reason": "no_signed_lease"})
            return
        try:
            from core.secure_store import verify_offline_lease
            now_ms = int(time.time() * 1000)
            verify_offline_lease(
                lease,
                expected_user_id=user_id,
                expected_device_hash=_installation_device_hash(),
                expected_app_id="ses-merkezi",
                expected_platform="windows",
                public_key_pem=public_key,
                now_ms=now_ms,
            )
        except (ValueError, TypeError, RuntimeError, OverflowError):
            _secure_write(LICENSE_CACHE_PATH, {"active": False, "reason": "signed_lease_invalid"})
            return
        _secure_write(LICENSE_CACHE_PATH, {
            "user_id": user_id,
            "offline_lease": lease,
            "offline_lease_public_key": public_key,
            "last_seen_at_ms": now_ms,
        })


    def education_api(self, action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        allowed = {"published_documents", "document_open", "published_exams", "exam_begin", "exam_submit"}
        if action not in allowed:
            raise ValueError("Öğrenci eğitim API işlemi izin listesinde değil.")
        return self._edge_call(action, payload, function_slug="sesm-education-admin")

    def open_pdf_url(self, url: str) -> dict[str, Any]:
        from urllib.parse import urlparse
        parsed = urlparse(str(url))
        if parsed.scheme != "https" or parsed.hostname != "itasctyjzyewcykozuex.supabase.co" or not parsed.path.startswith("/storage/v1/object/sign/sesm-education-pdfs/"):
            raise ValueError("Eğitim PDF bağlantısı güvenli değil.")
        opened = webbrowser.open(str(url), new=2)
        if not opened:
            raise RuntimeError("PDF bağlantısı tarayıcıda açılamadı.")
        return {"ok": True}

    def auth_context(self) -> dict[str, Any]:
        context = self._edge_call("context", {"device_hash": _installation_device_hash()})
        self._account_context = context
        return context

    def auth_logout(self) -> dict[str, Any]:
        session = self._session
        if session and session.get("access_token"):
            try:
                self._edge_call("session_event", {"event_type": "logout", "platform": "windows"})
            except Exception:
                pass
        if session and session.get("access_token"):
            request = Request(
                SUPABASE_URL + "/auth/v1/logout",
                headers={"Accept": "application/json", "apikey": SUPABASE_PUBLISHABLE_KEY,
                         "Authorization": "Bearer " + str(session["access_token"])},
                method="POST",
            )
            try:
                with urlopen(request, timeout=8):
                    pass
            except Exception:
                pass
        self._clear_auth_session()
        _secure_write(LICENSE_CACHE_PATH, {"active": False, "verified_at": time.time(), "reason": "signed_out"})
        return {"ok": True}

    def license_activate(self, key: str) -> dict[str, Any]:
        result = self._edge_call("license_activate", {"key": str(key).strip(), "device_hash": _installation_device_hash()})
        context = self._edge_call("context", {"device_hash": _installation_device_hash()})
        self._cache_server_license(context)
        return {"ok": True, "activation": result, "context": context}

    def store_get(self) -> dict[str, Any]:
        return self._edge_call("store_get")

    def store_update(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._edge_call("store_update", payload)

    def purchase_submit(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._edge_call("purchase_submit", payload)

    def purchase_list(self) -> dict[str, Any]:
        return self._edge_call("purchase_list")

    def purchase_review(self, purchase_id: str, decision: str, admin_note: str = "") -> dict[str, Any]:
        return self._edge_call("purchase_review", {"purchase_id": purchase_id, "decision": decision, "admin_note": admin_note})

    def admin_dashboard(self) -> dict[str, Any]:
        """Return the owner-only central administration dashboard."""
        return self._edge_call("admin_dashboard", {"platform": "windows"})

    def license_list(self) -> dict[str, Any]:
        """Return license metadata for the server-authorized owner only."""
        return self._edge_call("license_list")

    def license_create(
        self, label: str, plan_code: str, max_activations: int, expires_days: int,
        customer_name: str = "", customer_email: str = "", payment_method: str = "cash",
        payment_status: str = "unpaid", amount: Any = 0, currency: str = "TRY",
        payment_reference: str = "", bundle_code: str = "start",
    ) -> dict[str, Any]:
        """Create a manually sold license; payment metadata is validated again server-side."""
        return self._edge_call("license_create", {
            "label": label, "plan_code": plan_code, "max_activations": max_activations,
            "expires_days": expires_days, "customer_name": customer_name,
            "customer_email": customer_email, "payment_method": payment_method,
            "payment_status": payment_status, "amount": amount, "currency": currency,
            "payment_reference": payment_reference, "bundle_code": bundle_code,
        })

    def license_payment_update(self, license_id: str, payment_status: str) -> dict[str, Any]:
        return self._edge_call("license_payment_update", {"license_id": license_id, "payment_status": payment_status})

    def license_revoke(self, license_id: str) -> dict[str, Any]:
        return self._edge_call("license_revoke", {"license_id": license_id})

    def teacher_students(self) -> dict[str, Any]:
        return self._edge_call("teacher_students")

    def student_progress(self, student_user_id: str = "") -> dict[str, Any]:
        payload = {"student_user_id": student_user_id} if student_user_id else {}
        return self._edge_call("progress_get", payload)

    def teacher_mark_progress(self, student_user_id: str, module_id: str, completed: bool, teacher_note: str = "") -> dict[str, Any]:
        return self._edge_call("progress_mark", {"student_user_id": student_user_id, "module_id": module_id, "completed": bool(completed), "teacher_note": teacher_note})

    def check_updates(self) -> dict[str, Any]:
        request = Request(UPDATE_MANIFEST_URL, headers={"Accept": "application/json", "User-Agent": f"StagepulseSesMerkezi/{APP_VERSION}"})
        # Manifest kontrolü geçici ağ/HTTP hatalarında sınırlı geri çekilmeyle yinelenir.
        raw = None
        for attempt in range(3):
            try:
                with urlopen(request, timeout=12) as response:
                    raw = response.read(256_001)
                break
            except HTTPError as exc:
                if exc.code == 404:
                    return {"ok": True, "available": False, "published": False, "message": "Güncelleme servisi henüz stagepulse.com.tr üzerinde yayınlanmamış."}
                if exc.code not in (408, 425, 429, 500, 502, 503, 504) or attempt == 2:
                    raise RuntimeError(f"Güncelleme servisi HTTP {exc.code} döndürdü.") from exc
            except (URLError, TimeoutError, OSError):
                if attempt == 2:
                    return {"ok": False, "available": False, "offline": True, "message": "Güncelleme servisine ulaşılamadı. Yerel araçlar kullanılabilir."}
            if attempt < 2:
                time.sleep(attempt + 1)
        if raw is None:
            return {"ok": False, "available": False, "offline": True, "message": "Güncelleme servisine ulaşılamadı. Yerel araçlar kullanılabilir."}
        if len(raw) > 256_000:
            raise RuntimeError("Güncelleme bildirimi beklenenden büyük.")
        try:
            manifest = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise RuntimeError("Güncelleme bildirimi geçerli JSON değil.") from exc
        if manifest.get("published") is not True:
            return {"ok": True, "available": False, "published": False,
                    "channel": str(manifest.get("channel", UPDATE_CHANNEL)),
                    "current_version": APP_VERSION,
                    "message": str(manifest.get("message", "Bu kanalda yeni sürüm yok."))[:500]}
        version = str(manifest.get("version", ""))
        url = str(manifest.get("url", ""))
        digest = str(manifest.get("sha256", "")).lower()
        import re
        if (manifest.get("ok") is not True or
                manifest.get("channel") != UPDATE_CHANNEL or
                manifest.get("prerelease") is not False):
            raise RuntimeError("Yalnızca yayımlanmış kararlı güncellemeler kabul edilir.")
        if (not re.fullmatch(r"\d+\.\d+\.\d+", version) or
                not re.fullmatch(r"[0-9a-f]{64}", digest)):
            raise RuntimeError("Güncelleme bildiriminin sürüm veya SHA-256 alanı geçersiz.")
        filename = f"Stagepulse-Ses-Merkezi-Windows-{version}.exe"
        expected_path = f"/ibrahimFOH/Stagepulse-Releases/releases/download/v{version}/{filename}"
        parsed = urlparse(url)
        if (parsed.scheme != "https" or parsed.hostname != "github.com" or
                parsed.path != expected_path or parsed.username or parsed.password or
                parsed.query or parsed.fragment or parsed.port or
                manifest.get("filename") != filename):
            raise RuntimeError("Güncelleme adresi beklenen Stagepulse kararlı yayın dosyası değil.")
        available = _version_tuple(version) > _version_tuple(APP_VERSION)
        return {"ok": True, "published": True, "available": available, "current_version": APP_VERSION, "version": version,
                "url": url, "sha256": digest, "channel": str(manifest.get("channel", UPDATE_CHANNEL)), "notes": str(manifest.get("notes", ""))[:2000],
                "message": "Yeni sürüm mevcut." if available else "Uygulama güncel."}

    def install_update(self, manifest_json: str) -> dict[str, Any]:
        try:
            manifest = json.loads(str(manifest_json))
        except json.JSONDecodeError as exc:
            raise ValueError("Güncelleme bildirimi geçersiz.") from exc
        checked = self.check_updates()
        if not checked.get("published") or not checked.get("available"):
            return {"ok": False, "message": checked.get("message", "Yeni güncelleme yok.")}
        if str(manifest.get("sha256", "")).lower() != checked.get("sha256") or str(manifest.get("url", "")) != checked.get("url"):
            raise ValueError("Güncelleme bilgisi doğrulanan bildirime uymuyor.")
        import secrets
        installer_path = Path(tempfile.gettempdir()) / f"StagepulseSesMerkeziUpdate_{secrets.token_hex(8)}.exe"
        request = Request(checked["url"], headers={"User-Agent": f"StagepulseSesMerkezi/{APP_VERSION}"})
        partial_path = installer_path.with_suffix(installer_path.suffix + ".part")
        try:
            for attempt in range(1, 4):
                partial_path.unlink(missing_ok=True)
                h = hashlib.sha256()
                total = 0
                try:
                    with urlopen(request, timeout=300) as response:
                        final_host = (urlparse(response.geturl()).hostname or "").lower()
                        if final_host not in {"github.com", "release-assets.githubusercontent.com"}:
                            raise RuntimeError("Güncelleme indirme yönlendirmesi güvenilir bir GitHub sunucusuna gitmiyor.")
                        with partial_path.open("wb") as out:
                            while True:
                                chunk = response.read(1024 * 1024)
                                if not chunk:
                                    break
                                total += len(chunk)
                                if total > 2 * 1024 * 1024 * 1024:
                                    raise RuntimeError("Güncelleme paketi 2 GB sınırını aşıyor.")
                                h.update(chunk)
                                out.write(chunk)
                            out.flush()
                            os.fsync(out.fileno())
                    if total < 1024 * 1024 or h.hexdigest().lower() != checked["sha256"]:
                        raise RuntimeError("İndirilen kurulum dosyasının boyutu veya SHA-256 özeti doğrulanmadı.")
                    partial_path.replace(installer_path)
                    break
                except Exception:
                    partial_path.unlink(missing_ok=True)
                    if attempt == 3:
                        raise
                    time.sleep(attempt * 2)
            if os.name != "nt":
                raise RuntimeError("Güncelleme kurucusu yalnızca Windows'ta çalıştırılabilir.")
            helper = Path(tempfile.gettempdir()) / f"stagepulse_update_{secrets.token_hex(8)}.ps1"
            log_path = DATA_ROOT / "guncelleme-kurulum.log"
            quote = lambda value: "'" + str(value).replace("'", "''") + "'"
            script = "\n".join([
                "$ErrorActionPreference='Stop'",
                "$log=" + quote(log_path),
                "try {",
                f"  Wait-Process -Id {os.getpid()} -ErrorAction Stop",
                f"  $installer={quote(installer_path)}",
                "  $p=Start-Process -FilePath $installer -ArgumentList '/S' -Wait -PassThru",
                "  if ($p.ExitCode -ne 0) { throw ('Kurucu çıkış kodu: ' + $p.ExitCode) }",
                "  $key='HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\StagepulseSesMerkezi'",
                "  $installed=(Get-ItemProperty -LiteralPath $key -ErrorAction Stop).DisplayVersion",
                "  if ($installed -ne " + quote(checked["version"]) + ") { throw ('Kurulu sürüm doğrulanamadı. Beklenen: " + checked["version"] + "; bulunan: ' + $installed) }",
                "  Set-Content -LiteralPath $log -Value ('OK|' + $installed) -Encoding UTF8",
                "} catch { Set-Content -LiteralPath $log -Value ('ERROR|' + $_.Exception.Message) -Encoding UTF8 }",
                f"Remove-Item -LiteralPath {quote(installer_path)} -Force -ErrorAction SilentlyContinue",
                f"Remove-Item -LiteralPath {quote(helper)} -Force -ErrorAction SilentlyContinue",
            ]) + "\n"
            helper.write_text(script, encoding="utf-8-sig")
            subprocess.Popen(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", str(helper)], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), close_fds=True)
            if self.window is not None:
                self.window.destroy()
            return {"ok": True, "message": "Güncelleme indirildi ve doğrulandı. Kurulum sonucu uygulama yeniden açıldığında denetlenecek."}
        except Exception:
            try:
                installer_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise

    def open_website(self, page: str = "home") -> dict[str, Any]:
        target = {"home": WEBSITE_URL, "support": WEBSITE_URL + "/iletisim.html", "privacy": WEBSITE_URL + "/gizlilik.html"}.get(str(page), WEBSITE_URL)
        webbrowser.open(target)
        return {"ok": True, "url": target}

    def open_whatsapp(self) -> dict[str, Any]:
        target = "https://wa.me/905320683012?text=Merhaba%20Stagepulse%2C%20uygulama%20deste%C4%9Fi%20almak%20istiyorum."
        webbrowser.open(target)
        return {"ok": True, "url": target}

    def export_json_dialog(self, suggested_name: str, json_text: str) -> dict[str, Any]:
        import webview
        path = _dialog_path(self.window.create_file_dialog(
            webview.SAVE_DIALOG, save_filename=Path(suggested_name).name,
            file_types=("JSON (*.json)",)
        ))
        if not path:
            return {"cancelled": True}
        if not path.lower().endswith(".json"):
            path += ".json"
        try:
            parsed = json.loads(json_text)
        except json.JSONDecodeError as exc:
            raise ValueError("Dışa aktarılacak içerik geçerli JSON değil.") from exc
        _atomic_json_write(Path(path), parsed)
        return {"ok": True, "path": path}

    def export_text_dialog(self, suggested_name: str, text: str) -> dict[str, Any]:
        import webview
        path = _dialog_path(self.window.create_file_dialog(
            webview.SAVE_DIALOG, save_filename=Path(suggested_name).name,
            file_types=("Metin / CSV (*.txt;*.csv)",)
        ))
        if not path:
            return {"cancelled": True}
        Path(path).write_text(str(text), encoding="utf-8-sig")
        return {"ok": True, "path": path}


class LocalHandler(SimpleHTTPRequestHandler):
    """Yalnızca loopback'e bağlanan paket içi statik dosya sunucusu."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(RESOURCE_ROOT), **kwargs)

    def log_message(self, fmt: str, *args: Any) -> None:
        # Kullanıcının ekranında veya konsolda gereksiz HTTP günlüğü gösterme.
        return

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Permissions-Policy", "camera=(), geolocation=(), payment=()")
        self.send_header("Content-Security-Policy", "default-src 'self' data: blob:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; media-src 'self' blob: data:; font-src 'self' data:; connect-src 'self' blob:; frame-src 'self' blob:; object-src 'self'; base-uri 'self'; form-action 'self'")
        super().end_headers()

    def _allowed_resource(self, request_path: str) -> bool:
        """HTTP yüzeyi yalnızca ön yüz, araç, ders belgeleri ve eğitim PDF'sini sunar."""
        decoded = unquote(urlsplit(request_path).path)
        if decoded == "/":
            decoded = "/ui/index.html"
        target = (RESOURCE_ROOT / decoded.lstrip("/")).resolve()
        allowed_roots = (UI_ROOT.resolve(), TOOLS_ROOT.resolve())
        allowed_doc_paths = {
            (DOCS_ROOT / filename).resolve()
            for filename, _title in EDUCATIONAL_DOCS
        }
        allowed_doc_paths.add((DOCS_ROOT / "EGITIM_DALLARI_USTA_YOLU_VE_FIYATLANDIRMA_TR.md").resolve())
        allowed_doc_paths.add((EDUCATIONAL_PDF_ROOT / "stagepulse_egitim_katalogu_v1.json").resolve())
        allowed_pdf_paths = {
            (EDUCATIONAL_PDF_ROOT / item["file"]).resolve()
            for item in STUDENT_PDFS
        }
        return target.is_file() and (
            any(root == target or root in target.parents for root in allowed_roots)
            or target in allowed_doc_paths
            or target in allowed_pdf_paths
        )

    def do_GET(self) -> None:
        request_path = urlsplit(self.path).path
        if request_path == "/":
            self.path = "/ui/index.html"
        if not self._allowed_resource(self.path):
            # HTTP/1.0 status-line reason phrase latin-1 ile kodlanır; Türkçe karakter
            # kullanmak bazı Python/Windows kombinasyonlarında handler'ı düşürebilir.
            body = "Kaynak bulunamadı.".encode("utf-8")
            self.send_response(404, "Not Found")
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass
            return
        super().do_GET()


def webview2_installed() -> bool:
    if os.name != "nt":
        return True
    try:
        import winreg
        guid = r"{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
        keys = [
            (winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\WOW6432Node\\Microsoft\\EdgeUpdate\\Clients\\" + guid),
            (winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\EdgeUpdate\\Clients\\" + guid),
            (winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\EdgeUpdate\\Clients\\" + guid),
        ]
        for hive, key in keys:
            try:
                with winreg.OpenKey(hive, key) as handle:
                    version, _ = winreg.QueryValueEx(handle, "pv")
                if version and version != "0.0.0.0":
                    return True
            except OSError:
                pass
    except ImportError:
        pass
    return False

def ensure_webview2_runtime() -> bool:
    """Install the bundled Microsoft WebView2 bootstrapper when an MSIX device lacks the runtime."""
    if webview2_installed():
        return True
    if os.name != "nt":
        return True
    installer = APP_HOME / "Runtime" / "MicrosoftEdgeWebView2RuntimeInstallerX64.exe"
    if not installer.is_file():
        return False
    try:
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        result = subprocess.run(
            [str(installer), "/silent", "/install"],
            check=False,
            timeout=240,
            creationflags=flags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return result.returncode in (0, 3010) and webview2_installed()
    except (OSError, subprocess.TimeoutExpired):
        return False


def show_native_error(title: str, message: str) -> None:
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, message, title, 0x10)
            return
        except Exception:
            pass
    print(f"{title}: {message}", file=sys.stderr)


def initial_window_size(screen_width: int | None = None, screen_height: int | None = None) -> tuple[int, int, tuple[int, int]]:
    """Choose a readable initial window that fits common laptop and desktop screens."""
    if screen_width is None or screen_height is None:
        if os.name == "nt":
            try:
                import ctypes
                user32 = ctypes.windll.user32
                screen_width = int(user32.GetSystemMetrics(0))
                screen_height = int(user32.GetSystemMetrics(1))
            except Exception:
                screen_width, screen_height = 1440, 900
        else:
            screen_width, screen_height = 1440, 900
    sw, sh = max(640, int(screen_width)), max(480, int(screen_height))
    width = min(1500, int(sw * 0.94), sw - 24)
    height = min(980, int(sh * 0.90), sh - 48)
    width = max(min(940, sw - 24), width)
    height = max(min(600, sh - 48), height)
    return width, height, (min(940, width), min(600, height))


def main() -> int:
    if not UI_ROOT.joinpath("index.html").is_file():
        show_native_error(APP_NAME, "Paket kaynakları bulunamadı. Temiz derleme paketi eksik.")
        return 2
    missing_student_pdfs = [item["file"] for item in STUDENT_PDFS if not (EDUCATIONAL_PDF_ROOT / item["file"]).is_file()]
    if missing_student_pdfs:
        show_native_error(APP_NAME, "Öğrenci eğitim PDF'leri eksik:\n" + "\n".join(missing_student_pdfs))
        return 2
    if not ensure_webview2_runtime():
        show_native_error(
            APP_NAME,
            "Microsoft WebView2 Runtime bulunamadı. Uygulama, Stagepulse_Kurulum.exe ile kurulmalıdır. "
            "Kurulum dosyası bu bileşeni gerekiyorsa sessizce yükler. "
            "MSIX paketinde Microsoft'un çevrimdışı yükleyicisi bulunur ve eksikse ilk açılışta çalıştırılır.\n\n"
            "Kurulumdan sonra Windows'u yeniden başlatıp uygulamayı tekrar açın.\n"
            "Destek: https://stagepulse.com.tr/"
        )
        return 3

    try:
        import webview
    except ImportError:
        show_native_error(APP_NAME, "Uygulama içi web motoru eksik. EXE derleme paketini yeniden üretin.")
        return 4

    server = ThreadingHTTPServer(("127.0.0.1", 0), LocalHandler)
    server.daemon_threads = True
    port = int(server.server_address[1])
    server_thread = threading.Thread(target=server.serve_forever, name="KSM-local-http", daemon=True)
    server_thread.start()

    api = AppApi()
    user_data = DATA_ROOT / "webview"
    user_data.mkdir(parents=True, exist_ok=True)
    win_width, win_height, min_window_size = initial_window_size()
    window = webview.create_window(
        f"{APP_NAME} · v{APP_VERSION}",
        url=f"http://127.0.0.1:{port}/ui/index.html",
        js_api=api,
        width=win_width, height=win_height, min_size=min_window_size,
        text_select=True, confirm_close=True, background_color="#0d1015",
    )
    api.window = window
    try:
        def on_window_closed() -> None:
            try:
                api.stop_rta()
            finally:
                threading.Thread(target=server.shutdown, daemon=True).start()
        window.events.closed += on_window_closed
        webview.start(gui="edgechromium", debug=False, private_mode=False, storage_path=str(user_data))
    except Exception as exc:
        traceback.print_exc()
        show_native_error(APP_NAME, f"Ana uygulama penceresi açılamadı.\n\n{exc}")
        return 5
    finally:
        try:
            server.shutdown()
            server.server_close()
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
