import json
from pathlib import Path

import pytest
import Merkez


def test_student_profiles_are_separate_and_atomic(tmp_path, monkeypatch):
    monkeypatch.setattr(Merkez, 'PROFILE_PATH', tmp_path / 'profiles.dat')
    # Isolate legacy migration from any developer's real AppData profile.
    monkeypatch.setattr(Merkez, 'LEGACY_PROFILE_PATH', tmp_path / 'legacy-profiles.json')
    api = Merkez.AppApi()
    api.save_profile('Öğrenci A', json.dumps({'completedModules': ['rta']}))
    api.save_profile('Öğrenci B', json.dumps({'completedModules': ['wav']}))
    loaded = api.load_profiles()['profiles']
    assert set(loaded) == {'Öğrenci A', 'Öğrenci B'}
    assert loaded['Öğrenci A']['completedModules'] == ['rta']
    assert loaded['Öğrenci B']['completedModules'] == ['wav']
    api.delete_profile('Öğrenci A')
    assert list(api.load_profiles()['profiles']) == ['Öğrenci B']
    assert not list(tmp_path.glob('*.tmp'))


def test_profile_name_required(tmp_path, monkeypatch):
    monkeypatch.setattr(Merkez, 'PROFILE_PATH', tmp_path / 'profiles.dat')
    monkeypatch.setattr(Merkez, 'LEGACY_PROFILE_PATH', tmp_path / 'legacy-profiles.json')
    with pytest.raises(ValueError, match='Öğrenci adı'):
        Merkez.AppApi().save_profile(' ', '{}')


def test_ai_endpoint_rejects_cleartext_to_remote_host():
    with pytest.raises(ValueError, match='HTTPS'):
        Merkez.AppApi().ai_chat('groq', 'model', 'secret', 'test', 'http://example.com/v1/chat/completions')


def test_ai_endpoint_rejects_invalid_scheme():
    with pytest.raises(ValueError, match='Endpoint geçerli'):
        Merkez.AppApi().ai_chat('groq', 'model', '', 'test', 'file:///etc/passwd')


def test_whitelisted_doc_and_traversal_guard():
    api = Merkez.AppApi()
    names = {item['file'] for item in api.list_docs()}
    assert '00_BASLANGIC_TR.md' in names
    with pytest.raises(ValueError, match='izin verilen listede'):
        api.read_doc('../../Merkez.py')


def test_student_pdf_catalog_only_lists_existing_student_materials():
    api = Merkez.AppApi()
    items = api.list_student_pdfs()
    assert len(items) == 13
    assert items[0]['file'] == '00_Uygulama_Kullanimi_Ogrenci.pdf'
    assert items[-1]['file'] == '12_Allen_Heath_Avantis_Uygulamali_Egitim.pdf'
    assert {x['file'] for x in items[-3:]} == {'10_Midas_M32_Live_Uygulamali_Egitim.pdf','11_Yamaha_CL5_Uygulamali_Egitim.pdf','12_Allen_Heath_Avantis_Uygulamali_Egitim.pdf'}
    assert all((Merkez.EDUCATIONAL_PDF_ROOT / item['file']).is_file() for item in items)
    assert all(item['url'].startswith('/egitim_paketleri/') for item in items)
    assert not any('Egitmen' in item['file'] or 'Fiyat' in item['file'] for item in items)


def test_student_pdf_download_only_allows_catalogued_pdf(tmp_path, monkeypatch):
    import sys
    import types

    target = tmp_path / 'exports' / 'student-guide.pdf'
    class FakeWindow:
        def create_file_dialog(self, *args, **kwargs):
            return str(target)
    fake_webview = types.SimpleNamespace(SAVE_DIALOG='save')
    monkeypatch.setitem(sys.modules, 'webview', fake_webview)
    api = Merkez.AppApi()
    api.window = FakeWindow()
    item = Merkez.STUDENT_PDFS[1]
    result = api.save_student_pdf_dialog(item['file'])
    assert result['ok'] is True
    assert target.read_bytes().startswith(b'%PDF-')
    with pytest.raises(ValueError, match='kataloğunda bulunmuyor'):
        api.save_student_pdf_dialog('../../Merkez.py')

def test_static_server_only_exposes_application_resources():
    handler = Merkez.LocalHandler
    assert handler._allowed_resource(handler.__new__(handler), '/') is True
    assert handler._allowed_resource(handler.__new__(handler), '/ui/app.js') is True
    assert handler._allowed_resource(handler.__new__(handler), '/araclar/Frekans_Bulucu/index.html') is True
    assert handler._allowed_resource(handler.__new__(handler), '/docs/00_BASLANGIC_TR.md') is True
    assert handler._allowed_resource(handler.__new__(handler), '/egitim_paketleri/01_Ses_Muhendisligi_Ogrenci_Ders_Kitabi.pdf') is True
    assert handler._allowed_resource(handler.__new__(handler), '/egitim_paketleri/../../Merkez.py') is False
    assert handler._allowed_resource(handler.__new__(handler), '/Merkez.py') is False
    assert handler._allowed_resource(handler.__new__(handler), '/core/audio_tools.py') is False
    assert handler._allowed_resource(handler.__new__(handler), '/../Merkez.py') is False


def test_native_rta_api_validates_ranges_and_calls_capture(monkeypatch):
    class FakeRta:
        def __init__(self): self.started = None
        def start(self, device_index, fft_size):
            self.started = (device_index, fft_size)
            return {'ok': True, 'sample_rate': 48000, 'fft_size': fft_size}
        def snapshot(self, mode, low, high):
            return {'ok': True, 'mode': mode, 'low': low, 'high': high}
        def stop(self): return {'ok': True, 'running': False}
    api = Merkez.AppApi()
    fake = FakeRta()
    api._rta_capture = fake
    assert api.start_rta('', 16384)['sample_rate'] == 48000
    assert fake.started == (None, 16384)
    assert api.get_rta_snapshot('third', 20, 20000)['high'] == 20000
    with pytest.raises(ValueError, match='Bant modu'):
        api.get_rta_snapshot('unvalid', 20, 20000)
    with pytest.raises(ValueError, match='Frekans aralığı'):
        api.get_rta_snapshot('third', 20000, 20)
    assert api.stop_rta()['running'] is False


def test_loopback_server_serves_ui_and_student_pdf_but_not_python_source():
    from http.server import ThreadingHTTPServer
    from threading import Thread
    from urllib.error import HTTPError
    from urllib.request import urlopen

    server = ThreadingHTTPServer(('127.0.0.1', 0), Merkez.LocalHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{server.server_address[1]}'
    try:
        with urlopen(base + '/', timeout=3) as response:
            html = response.read()
            assert response.status == 200
            assert b'Canl' in html
        with urlopen(base + '/egitim_paketleri/01_Ses_Muhendisligi_Ogrenci_Ders_Kitabi.pdf', timeout=3) as response:
            assert response.status == 200
            pdf_bytes = response.read()
            assert pdf_bytes.startswith(b'%PDF-')
        try:
            urlopen(base + '/Merkez.py', timeout=3)
            assert False, 'Python kaynak kodu HTTP üzerinden sunulmamalı.'
        except HTTPError as exc:
            assert exc.code == 404
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_initial_window_size_adapts_to_laptop_and_desktop_screens():
    width, height, minimum = Merkez.initial_window_size(1366, 768)
    assert width <= 1366 and height <= 768
    assert width >= 940 and height >= 600
    assert minimum == (940, 600)
    small_width, small_height, small_min = Merkez.initial_window_size(800, 600)
    assert small_width <= 800 and small_height <= 600
    assert small_min[0] <= small_width and small_min[1] <= small_height
    large_width, large_height, _ = Merkez.initial_window_size(2560, 1440)
    assert large_width > width and large_height > height


def test_all_ai_providers_require_a_paid_license(tmp_path, monkeypatch):
    import core.ai_providers

    monkeypatch.setattr(Merkez, "LICENSE_CACHE_PATH", tmp_path / "no-license.dat")
    api = Merkez.AppApi()
    with pytest.raises(RuntimeError, match="ödemesi onaylı lisans gerekir"):
        api.ai_chat("groq", "openai/gpt-oss-120b", "dummy-key", "hello", "https://api.groq.com/openai/v1/chat/completions")
    with pytest.raises(RuntimeError, match="ödemesi onaylı lisans gerekir"):
        api.ai_chat("ollama", "llama3.2", "", "hello", "http://127.0.0.1:11434/api/chat")

    monkeypatch.setattr(api, "_cached_license_status", lambda: {"active": True})
    monkeypatch.setattr(core.ai_providers, "chat", lambda *args, **kwargs: {"ok": True, "provider": "ollama", "content": "yerel"})
    result = api.ai_chat("ollama", "llama3.2", "", "hello", "http://127.0.0.1:11434/api/chat")
    assert result["provider"] == "ollama"
    assert result["content"] == "yerel"


def test_auth_restore_keeps_paid_license_available_during_network_outage(monkeypatch, tmp_path):
    monkeypatch.setattr(Merkez, "SESSION_PATH", tmp_path / "session.dat")
    stored = {
        "access_token": "last-access-token",
        "refresh_token": "last-refresh-token",
        "user": {"id": "student-user"},
    }
    monkeypatch.setattr(Merkez, "_secure_read", lambda path, fallback: stored if path == Merkez.SESSION_PATH else fallback)
    api = Merkez.AppApi()
    monkeypatch.setattr(api, "_auth_user_request", lambda access: (_ for _ in ()).throw(RuntimeError("Stagepulse hesabına ulaşılamadı. İnternet bağlantısını kontrol et.")))
    monkeypatch.setattr(api, "_cached_license_status", lambda: {
        "active": True, "user_id": "student-user", "reason": "offline_grace",
    })

    result = api.auth_restore()

    assert result["ok"] is True
    assert result["authenticated"] is False
    assert result["offline"] is True
    assert result["license"]["active"] is True
    assert api._session is stored



def test_owner_login_uses_central_supabase_auth(monkeypatch, tmp_path):
    monkeypatch.setattr(Merkez, "LICENSE_CACHE_PATH", tmp_path / "license-cache.dat")
    monkeypatch.setattr(Merkez, "SESSION_PATH", tmp_path / "session.dat")
    api = Merkez.AppApi()
    captured = {}

    def fake_auth_request(path, body):
        captured["path"] = path
        captured["body"] = body
        return {"access_token": "shared-supabase-jwt", "refresh_token": "shared-refresh-token", "user": {"id": "owner-id", "email": body["email"]}}

    context = {"role": "owner", "user": {"id": "owner-id", "email": "owner@example.com"}, "licensed": {"active": True}}
    monkeypatch.setattr(api, "_auth_request", fake_auth_request)
    monkeypatch.setattr(api, "_edge_call", lambda action, payload=None: context)
    monkeypatch.setattr(api, "_cache_server_license", lambda value: None)

    result = api.auth_login("OWNER@EXAMPLE.COM", "shared-password")

    assert captured["path"] == "/auth/v1/token?grant_type=password"
    assert captured["body"] == {"email": "owner@example.com", "password": "shared-password"}
    assert api._session["access_token"] == "shared-supabase-jwt"
    assert (tmp_path / "session.dat").is_file()
    assert result["context"]["role"] == "owner"


def test_username_only_login_is_rejected():
    with pytest.raises(ValueError, match="Ortak Stagepulse hesabının e-posta adresi"):
        Merkez.AppApi().auth_login("stagepulseadmin", "password12345")


def test_student_login_keeps_email_auth_flow(monkeypatch, tmp_path):
    monkeypatch.setattr(Merkez, "LICENSE_CACHE_PATH", tmp_path / "license-cache.dat")
    monkeypatch.setattr(Merkez, "SESSION_PATH", tmp_path / "session.dat")
    api = Merkez.AppApi()
    captured = {}
    def fake_auth_request(path, body):
        captured["path"] = path
        captured["body"] = body
        return {"access_token": "student-access-token", "refresh_token": "student-refresh-token", "user": {"email": "student@example.com"}}
    expected_context = {"role": "student", "user": {"email": "student@example.com"}, "licensed": {"active": True}}
    monkeypatch.setattr(api, "_auth_request", fake_auth_request)
    monkeypatch.setattr(api, "_edge_call", lambda action, payload=None: expected_context)
    monkeypatch.setattr(api, "_cache_server_license", lambda context: None)

    result = api.auth_login("STUDENT@example.com", "student-password")

    assert captured["path"] == "/auth/v1/token?grant_type=password"
    assert captured["body"]["email"] == "student@example.com"
    assert (tmp_path / "session.dat").is_file()
    assert result["context"]["role"] == "student"


def test_android_ai_bridge_only_supports_groq_and_does_not_persist_keys():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    kotlin = (root / "android" / "app" / "src" / "main" / "java" / "com" / "stagepulse" / "sesmerkezi" / "MainActivity.kt").read_text(encoding="utf-8")
    android_js = (root / "android" / "app" / "src" / "main" / "assets" / "ui" / "app.js").read_text(encoding="utf-8")
    assert '"ai_chat" -> return requestMobileAi(payload)' in kotlin
    assert 'private fun requestMobileAi(payload: JSONObject)' in kotlin
    assert 'if (provider != "groq")' in kotlin
    assert 'if (provider == "ollama")' in kotlin
    assert 'https://api.groq.com/openai/v1/chat/completions' in kotlin
    assert 'uri.host?.lowercase() != "api.groq.com"' in kotlin
    assert 'uri.scheme != "https"' in kotlin
    assert 'instanceFollowRedirects = false' in kotlin
    assert "ai_chat: (provider, model, api_key, prompt, endpoint) => call('ai_chat'" in android_js
    assert "consent: $('aiConsent').checked" in android_js
    assert 'payload.optBoolean("consent", false)' in kotlin
    assert 'if(window.StagepulseAndroid)' in android_js
    assert 'option[value="ollama"]' in android_js
    assert "window.StagepulseAndroid&&$('aiProvider').value==='ollama'" in android_js
    assert 'storeSecret("api_key"' not in kotlin and 'storeSecret("api_key"' not in android_js
    assert "finally{$('aiKey').value='';" in android_js


def test_windows_edge_requests_use_shared_license_product_identity(monkeypatch):
    import io

    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self, limit=-1):
            return b'{"ok":true,"role":"guest","licensed":{"active":false}}'

    def fake_urlopen(request, timeout=20):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(Merkez, "urlopen", fake_urlopen)
    api = Merkez.AppApi()
    api._session = {"access_token": "test-user-jwt"}
    api._cache_server_license = lambda context: None

    result = api._edge_call("context", {"app_id": "attacker-app", "platform": "android", "device_hash": "a" * 64})

    assert result["ok"] is True
    assert captured["url"].endswith("/functions/v1/ses-merkezi-desktop")
    assert captured["body"]["app_id"] == "ses-merkezi"
    assert captured["body"]["platform"] == "windows"
    assert captured["body"]["device_hash"] == "a" * 64
    assert captured["headers"]["Authorization"] == "Bearer test-user-jwt"


def test_android_ses_client_identifies_its_shared_license_product():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    kotlin = (root / "android" / "app" / "src" / "main" / "java" / "com" / "stagepulse" / "sesmerkezi" / "MainActivity.kt").read_text(encoding="utf-8")
    assert '.put("app_id", "ses-merkezi-android")' in kotlin
    assert '.put("platform", "android")' in kotlin


def test_ses_edge_uses_only_shared_supabase_auth_and_license_core():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    source = (root / "supabase" / "functions" / "ses-merkezi-desktop" / "index.ts").read_text(encoding="utf-8")
    assert "admin.auth.getUser(token)" in source
    assert "verifyLicenseAdminToken" not in source
    assert "stagepulse_license_admin_config" not in source
    assert "/functions/v1/license-core" in source


def test_auth_restore_rotates_and_persists_refresh_token(monkeypatch, tmp_path):
    monkeypatch.setattr(Merkez, "SESSION_PATH", tmp_path / "session.dat")
    monkeypatch.setattr(Merkez, "LICENSE_CACHE_PATH", tmp_path / "license-cache.dat")
    stored = {"refresh_token": "old-refresh-token"}
    writes = {}
    monkeypatch.setattr(Merkez, "_secure_read", lambda path, fallback: stored if path == Merkez.SESSION_PATH else fallback)
    monkeypatch.setattr(Merkez, "_secure_write", lambda path, value: writes.update({str(path): value}))
    api = Merkez.AppApi()
    calls = []
    def fake_auth_request(path, body):
        calls.append((path, body))
        return {"access_token": "rotated-access", "refresh_token": "rotated-refresh", "user": {"id": "owner-id"}}
    context = {"role": "owner", "user": {"id": "owner-id"}, "licensed": {"active": True}}
    monkeypatch.setattr(api, "_auth_user_request", lambda access: None)
    monkeypatch.setattr(api, "_auth_request", fake_auth_request)
    monkeypatch.setattr(api, "_edge_call", lambda action, payload=None: context)
    result = api.auth_restore()
    assert calls == [("/auth/v1/token?grant_type=refresh_token", {"refresh_token": "old-refresh-token"})]
    assert result["authenticated"] is True
    assert result["context"]["role"] == "owner"
    assert writes[str(Merkez.SESSION_PATH)]["refresh_token"] == "rotated-refresh"


def test_auth_restore_does_not_clear_session_on_network_failure(monkeypatch):
    stored = {"refresh_token": "keep-this-token"}
    monkeypatch.setattr(Merkez, "_secure_read", lambda path, fallback: stored)
    api = Merkez.AppApi()
    monkeypatch.setattr(api, "_auth_user_request", lambda access: None)
    monkeypatch.setattr(api, "_auth_request", lambda *args: (_ for _ in ()).throw(RuntimeError("Stagepulse hesabına ulaşılamadı.")))
    with pytest.raises(RuntimeError, match="ulaşılamadı"):
        api.auth_restore()
    assert api._session is None


def test_auth_restore_clears_revoked_refresh_token(monkeypatch, tmp_path):
    monkeypatch.setattr(Merkez, "SESSION_PATH", tmp_path / "session.dat")
    monkeypatch.setattr(Merkez, "LICENSE_CACHE_PATH", tmp_path / "license-cache.dat")
    cleared = []
    monkeypatch.setattr(Merkez, "_secure_read", lambda path, fallback: {"refresh_token": "revoked"})
    monkeypatch.setattr(Merkez, "_secure_write", lambda path, value: cleared.append(value))
    api = Merkez.AppApi()
    monkeypatch.setattr(api, "_auth_user_request", lambda access: None)
    monkeypatch.setattr(api, "_auth_request", lambda *args: (_ for _ in ()).throw(RuntimeError("Kimlik servisi HTTP 400 döndürdü.")))
    result = api.auth_restore()
    assert result["authenticated"] is False
    assert api._session is None
    assert cleared


def test_android_session_is_restored_on_app_start():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    kotlin = (root / "android" / "app" / "src" / "main" / "java" / "com" / "stagepulse" / "sesmerkezi" / "MainActivity.kt").read_text(encoding="utf-8")
    android_js = (root / "android" / "app" / "src" / "main" / "assets" / "ui" / "app.js").read_text(encoding="utf-8")
    assert '"auth_restore" -> return restoreMobileAuthSession()' in kotlin
    assert 'auth_restore: () => call(\'auth_restore\')' in android_js
    assert 'const restored = await nativeApi.auth_restore()' in android_js
    assert 'requireMobileAccessToken()' in kotlin
    assert 'fetchMobileContext()' in kotlin


def test_auth_restore_keeps_valid_access_token_without_rotating_refresh(monkeypatch):
    stored = {"access_token": "still-valid", "refresh_token": "keep-refresh"}
    monkeypatch.setattr(Merkez, "_secure_read", lambda path, fallback: stored)
    api = Merkez.AppApi()
    context = {"role": "owner", "user": {"id": "owner-id"}, "licensed": {"active": True}}
    monkeypatch.setattr(api, "_auth_user_request", lambda access: {"id": "owner-id"} if access == "still-valid" else None)
    monkeypatch.setattr(api, "_edge_call", lambda action, payload=None: context)
    monkeypatch.setattr(api, "_cache_server_license", lambda value: None)
    monkeypatch.setattr(Merkez, "_secure_write", lambda path, value: None)
    monkeypatch.setattr(api, "_auth_request", lambda *args: (_ for _ in ()).throw(AssertionError("Geçerli oturum gereksiz yere yenilendi.")))
    result = api.auth_restore()
    assert result["authenticated"] is True
    assert api._session["refresh_token"] == "keep-refresh"


def test_android_release_ci_uses_persistent_keystore_and_stable_channel():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    gradle = (root / "android" / "app" / "build.gradle").read_text(encoding="utf-8")
    assert "ANDROID_KEYSTORE_PATH" in gradle
    assert "signingConfig signingConfigs.ciRelease" in gradle
    assert "def updateChannel = 'stable'" in gradle
    assert "'test'" not in gradle


def _signed_offline_lease(claims):
    import base64
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, rsa

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_pem = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    payload = json.dumps(claims, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    signature = key.sign(payload, padding.PKCS1v15(), hashes.SHA256())
    enc = lambda value: base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")
    return {"envelope": {"v": 1, "alg": "RS256", "payload": enc(payload), "signature": enc(signature)}, "public_key": public_pem}


def _offline_claims(now_ms, entitlement="paid", duration_ms=14 * 24 * 60 * 60 * 1000):
    trial = entitlement == "trial"
    return {
        "v": 1,
        "uid": "test-user",
        "app_id": "ses-merkezi",
        "platform": "windows",
        "device_hash": "a" * 64,
        "entitlement": entitlement,
        "paid": not trial,
        "plan_code": "trial" if trial else "student",
        "bundle_code": "trial" if trial else "full_master",
        "license_expires_at_ms": now_ms + 30 * 24 * 60 * 60 * 1000 if not trial else None,
        "trial_expires_at_ms": now_ms + duration_ms if trial else None,
        "issued_at_ms": now_ms,
        "expires_at_ms": now_ms + duration_ms,
    }


def test_offline_lease_accepts_valid_paid_14_day_entitlement():
    from core.secure_store import verify_offline_lease

    now = 1_800_000_000_000
    signed = _signed_offline_lease(_offline_claims(now))
    result = verify_offline_lease(
        signed["envelope"],
        expected_user_id="test-user",
        expected_device_hash="a" * 64,
        expected_app_id="ses-merkezi",
        expected_platform="windows",
        now_ms=now + 60_000,
        public_key_pem=signed["public_key"],
    )
    assert result["paid"] is True
    assert result["entitlement"] == "paid"


def test_offline_lease_rejects_wrong_device_and_tampered_signature():
    from core.secure_store import verify_offline_lease

    now = 1_800_000_000_000
    signed = _signed_offline_lease(_offline_claims(now))
    args = dict(
        expected_user_id="test-user",
        expected_device_hash="b" * 64,
        expected_app_id="ses-merkezi",
        expected_platform="windows",
        now_ms=now + 60_000,
        public_key_pem=signed["public_key"],
    )
    with pytest.raises(ValueError, match="farklı kullanıcıya veya cihaza"):
        verify_offline_lease(signed["envelope"], **args)

    broken = dict(signed["envelope"])
    broken["signature"] = "A" * 342
    args["expected_device_hash"] = "a" * 64
    with pytest.raises(ValueError, match="imzası doğrulanamadı"):
        verify_offline_lease(broken, **args)


def test_offline_lease_rejects_clock_rollback_expiry_and_overlong_trial():
    from core.secure_store import verify_offline_lease

    now = 1_800_000_000_000
    signed = _signed_offline_lease(_offline_claims(now))
    common = dict(
        expected_user_id="test-user",
        expected_device_hash="a" * 64,
        expected_app_id="ses-merkezi",
        expected_platform="windows",
        public_key_pem=signed["public_key"],
    )
    with pytest.raises(ValueError, match="Sistem saati geri alınmış"):
        verify_offline_lease(signed["envelope"], now_ms=now, last_seen_ms=now + 60 * 60 * 1000, **common)
    with pytest.raises(ValueError, match="süresi dolmuş"):
        verify_offline_lease(signed["envelope"], now_ms=now + 15 * 24 * 60 * 60 * 1000, **common)

    trial = _signed_offline_lease(_offline_claims(now, "trial", 8 * 24 * 60 * 60 * 1000))
    with pytest.raises(ValueError, match="Deneme offline lisans sınırı"):
        verify_offline_lease(trial["envelope"], now_ms=now + 60_000, **{**common, "public_key_pem": trial["public_key"]})
