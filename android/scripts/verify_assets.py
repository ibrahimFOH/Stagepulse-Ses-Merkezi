#!/usr/bin/env python3
"""Android paketindeki arayüz kaynaklarını ve çevrimdışı eğitim içeriğini doğrular."""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

# GitHub Windows runner varsayılan CP1252 kodlamasında Türkçe tanı mesajlarını yazamaz.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "android" / "app" / "src" / "main" / "assets"
UI = ASSETS / "ui"
HTML = UI / "index.html"
DOC_LIST = UI / "docs-list.json"
MAIN = ROOT / "android" / "app" / "src" / "main" / "java" / "com" / "stagepulse" / "sesmerkezi" / "MainActivity.kt"
MANIFEST = ROOT / "android" / "app" / "src" / "main" / "AndroidManifest.xml"
errors = []

for p in (HTML, UI / "app.js", UI / "style.css", UI / "rta_math.js", UI / "acoustic_math.js", UI / "first_party_tools.js", MAIN, MANIFEST, DOC_LIST):
    if not p.is_file():
        errors.append("Zorunlu dosya eksik: " + str(p.relative_to(ROOT)))

if HTML.is_file():
    source = HTML.read_text(encoding="utf-8")
    refs = re.findall(r"""(?i)\b(?:href|src)\s*=\s*["']([^"']+)["']""", source)
    for ref in refs:
        value = ref.strip()
        if not value or value.startswith(("#", "about:", "data:", "blob:", "http://", "https://", "mailto:", "tel:")):
            continue
        if value.startswith("/assets/"):
            target = ASSETS / value[len("/assets/"):]
        elif value.startswith("/"):
            errors.append("Android yerel varlık kaynağını kullanmayan mutlak yol: " + value)
            continue
        else:
            clean = value.split("?", 1)[0].split("#", 1)[0]
            target = (UI / clean).resolve()
        try:
            target.relative_to(ASSETS.resolve())
        except ValueError:
            errors.append("Kaynak APK varlık dizininin dışına çıkıyor: " + value)
            continue
        if not target.is_file():
            errors.append("HTML kaynağı APK içinde bulunamadı: " + value + " -> " + str(target.relative_to(ASSETS)))

ENGINEERING_PAGES = ("systemplan", "patch", "rf", "distribution", "roommap", "speaker", "wavelab")
if HTML.is_file():
    page_source = HTML.read_text(encoding="utf-8")
    page_names = re.findall(r"""data-page\s*=\s*["']([^"']+)["']""", page_source)
    nav_names = re.findall(r"""data-route\s*=\s*["']([^"']+)["']""", page_source)
    if len(page_names) != len(set(page_names)):
        errors.append("Android arayüzünde aynı data-page birden fazla kez tanımlanmış.")
    for route in ENGINEERING_PAGES:
        if route not in page_names:
            errors.append("Android mühendislik sayfası eksik: " + route)
        if route not in nav_names:
            errors.append("Android menüsünde mühendislik aracı eksik: " + route)
    first_party_position = page_source.find("first_party_tools.js")
    app_position = page_source.find("/assets/ui/app.js")
    if first_party_position < 0 or app_position < 0 or first_party_position > app_position:
        errors.append("Ortak mühendislik motoru ana uygulama JS dosyasından önce yüklenmiyor.")

shared_tools = UI / "first_party_tools.js"
desktop_tools = ROOT / "windows" / "ui" / "first_party_tools.js"
if shared_tools.is_file() and desktop_tools.is_file():
    if shared_tools.read_text(encoding="utf-8") != desktop_tools.read_text(encoding="utf-8"):
        errors.append("Android mühendislik motoru Windows sürümüyle eşleşmiyor.")
else:
    errors.append("Ortak mühendislik motoru Windows ve Android paketlerinde bulunmalı.")

android_app_js = UI / "app.js"
if android_app_js.is_file():
    app_source = android_app_js.read_text(encoding="utf-8")
    if "StagepulseFirstPartyTools?.initAll()" not in app_source:
        errors.append("Android açılışında ortak mühendislik araçları başlatılmıyor.")
    rta_start = app_source.split("async function startBrowserRta()", 1)[-1].split("async function stopRta(", 1)[0]
    if ("navigator.mediaDevices.getUserMedia({audio:reqAudio})" not in rta_start or
            "navigator.mediaDevices.getUserMedia({audio:true})" not in rta_start or
            "reqAudio.deviceId={ideal:deviceId}" not in rta_start or
            "await requestAndroidMicrophonePermission" in rta_start):
        errors.append("Android RTA WebView mikrofon akışı ideal cihaz seçimi ve otomatik yedek denemeyi içermiyor.")
    first_capture = rta_start.find("navigator.mediaDevices.getUserMedia(")
    if first_capture < 0 or "await stopBrowserRta()" in rta_start[:first_capture]:
        errors.append("Android mikrofon isteği öncesinde bekleyen AudioContext kapanışı bulunuyor.")
    if "const snapshot=api()?await api().get_rta_snapshot" not in app_source or ":browserRtaSnapshot();" not in app_source:
        errors.append("Android RTA, WebAudio spektrum verisini yerel RTA akışından ayıramıyor.")
    if "rtaTraceHistory.slice(-4)" not in app_source or "function updateRtaMeters(" not in app_source:
        errors.append("RTA çoklu spektrum izi veya canlı giriş metreleri eksik.")
    if "function calibrateAndroidSpl()" not in app_source or "function clearAndroidSplCalibration()" not in app_source:
        errors.append("Android oturumluk SPL kalibrasyon akışı eksik.")
    for element_id in ("rtaCalibratorLevel", "rtaCalibrate", "rtaClearCalibration", "rtaCalibrationStatus"):
        if f'id="{element_id}"' not in page_source:
            errors.append("Android SPL kalibrasyon kontrolü eksik: " + element_id)
    required_tf_functions = (
        "function androidTfFft(",
        "function androidTfSnapshot(",
        "function drawAndroidTfChart(",
        "function refreshAndroidTfDevices(",
        "function startAndroidTf(",
        "function stopAndroidTf(",
        "function initAndroidTfControls(",
        "channelCount:{exact:2}",
        "input.numberOfChannels<2",
        "androidTfChannelVerified",
    )
    for token in required_tf_functions:
        if token not in app_source:
            errors.append("Android canlı stereo TF uygulaması eksik: " + token)
    for element_id in (
        "androidTfPanel", "androidTfDevice", "androidTfFft", "androidTfAverages",
        "androidTfRefresh", "androidTfStart", "androidTfStop",
        "androidTfMagnitude", "androidTfPhase", "androidTfCoherence", "androidTfStatus",
    ):
        if f'id="{element_id}"' not in page_source:
            errors.append("Android canlı TF arayüz bileşeni eksik: " + element_id)
    for element_id in ("rtaPeakMeterFill", "rtaRmsMeterFill", "rtaPeakMeterValue", "rtaRmsMeterValue"):
        if f'id="{element_id}"' not in page_source:
            errors.append("RTA seviye göstergesi eksik: " + element_id)
    kotlin_source = MAIN.read_text(encoding="utf-8") if MAIN.is_file() else ""
    if "override fun onPermissionRequest(request: PermissionRequest)" not in kotlin_source or "requestedResources.toTypedArray()" not in kotlin_source or "Manifest.permission.RECORD_AUDIO" not in kotlin_source:
        errors.append("Android WebView mikrofon izin isteği çalışma zamanı iznine bağlanmamış.")
    tool_source = shared_tools.read_text(encoding="utf-8") if shared_tools.is_file() else ""
    if "window.StagepulseAndroid.saveBase64File" not in tool_source or "readAsDataURL" not in tool_source:
        errors.append("Android mühendislik araçları dışa aktarımı yerel dosya köprüsünü kullanmıyor.")
    if "function initWaveLab()" not in tool_source or "pascalsToDbSpl" not in tool_source:
        errors.append("Dalga / faz / gecikme laboratuvarının ortak motoru eksik.")
    for required in ('data-wave-tab="live"', "waveMicStart", "waveMicStop", "waveMicDelaySlider", "waveMicMonitor", "function startMicDelay()", "function stopMicDelay()", "N = round(Δt × fₛ)", "varsayılan olarak kamera veya mikrofon açmaz"):
        if required not in page_source and required not in tool_source:
            errors.append("Canlı mikrofon gecikme laboratuvarı bileşeni eksik: " + required)

if DOC_LIST.is_file():
    try:
        items = json.loads(DOC_LIST.read_text(encoding="utf-8"))
        if not isinstance(items, list) or not items:
            errors.append("docs-list.json boş olmayan bir liste olmalı")
        else:
            for item in items:
                if not isinstance(item, dict) or not item.get("file") or not item.get("title"):
                    errors.append("Geçersiz ders kataloğu kaydı: " + repr(item))
                    continue
                relative = Path(str(item["file"]))
                if relative.is_absolute() or ".." in relative.parts:
                    errors.append("Ders belgesi yolu geçersiz: " + str(item["file"]))
                    continue
                p = (ASSETS / "docs" / relative).resolve()
                try:
                    p.relative_to((ASSETS / "docs").resolve())
                except ValueError:
                    errors.append("Ders belgesi yolu paket dışına çıkıyor: " + str(item["file"]))
                    continue
                if not p.is_file():
                    errors.append("Ders belgesi APK içinde bulunamadı: " + str(item["file"]))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append("docs-list.json geçersiz: " + str(exc))

expected_pdfs = [
    "00_Uygulama_Kullanimi_Ogrenci.pdf",
    "01_Ses_Muhendisligi_Ogrenci_Ders_Kitabi.pdf",
    "02_Canli_Ses_Live_Sound_Ogrenci_Dersleri.pdf",
    "03_Studio_Ses_Muhendisligi_Ogrenci_Dersleri.pdf",
    "04_Dijital_Ses_Mikseri_Ogrenci_Calisma_Kitabi.pdf",
    "05_Canli_Ses_Mikseri_Hizli_Basvuru.pdf",
    "06_Ogrenci_Uygulama_Formlari.pdf",
    "07_Saha_Olcumu_SPL_Raporlama_Egitimi.pdf",
    "08_SPL_Alan_RTA_Teknik_Uygulama_Eki.pdf",
    "09_SPL_dB_3D_Gorsel_Atlasi.pdf",
    "10_Midas_M32_Live_Uygulamali_Egitim.pdf",
    "11_Yamaha_CL5_Uygulamali_Egitim.pdf",
    "12_Allen_Heath_Avantis_Uygulamali_Egitim.pdf",
]
for name in expected_pdfs:
    p = ASSETS / "egitim_paketleri" / name
    if not p.is_file() or p.stat().st_size < 1024:
        errors.append("Öğrenci PDF dosyası eksik veya çok küçük: " + name)

frequency = UI / "araclar" / "Frekans_Bulucu"
for name in ("index.html", "freq-finder.css", "freq-finder.js"):
    if not (frequency / name).is_file():
        errors.append("Frekans Bulucu dosyası eksik: " + name)

css = UI / "style.css"
if css.is_file():
    css_source = css.read_text(encoding="utf-8")
    css_refs = re.findall(r"""url\(\s*["']?([^"')]+)["']?\s*\)""", css_source, re.I)
    for ref in css_refs:
        value = ref.strip()
        if not value or value.startswith(("#", "data:", "http://", "https://")):
            continue
        target = (UI / value.split("?", 1)[0].split("#", 1)[0]).resolve()
        try:
            target.relative_to(ASSETS.resolve())
        except ValueError:
            errors.append("CSS kaynağı APK varlık dizininin dışına çıkıyor: " + value)
            continue
        if not target.is_file():
            errors.append("CSS kaynağı bulunamadı: " + value)
    if css_source.count("{") != css_source.count("}"):
        errors.append("Android CSS süslü parantezleri dengeli değil.")
    if re.search(r"@media\s*\([^)]*min-width\s*:\s*(?:601|761)px", css_source):
        errors.append("Eski telefon/tablet ekran kesme noktaları çakışıyor.")
    if "@media(max-width:800px)" not in css_source or "min-width:801px" not in css_source:
        errors.append("Telefon/tablet uyumlu ekran kesme noktaları eksik.")
    if "@media(max-width:1024px)" not in css_source or "overflow-y:auto" not in css_source:
        errors.append("Telefon/tablet ana sayfa kaydırma düzeltmesi eksik.")
    if ".main-area>section.page.active{display:block}" not in css_source:
        errors.append("Mobil/tablet etkin sayfanın tam içerikle gösterilmesi doğrulanamadı.")
    if "html,body{" not in css_source or "height:auto" not in css_source:
        errors.append("Mobil/tablet kök sayfa yüksekliği doğal içerik akışına bırakılmamış.")
    if "body.mobile-menu-open .sidebar{display:flex!important}" not in css_source:
        errors.append("Android telefon menüsü açılma kuralı eksik.")
    if not re.search(r"@media\(max-width:800px\)[\s\S]*?\.sidebar\{[^}]*display:none", css_source):
        errors.append("Android telefon menüsü kapalı başlangıç kuralı eksik.")

if HTML.is_file():
    topbar = re.search(r'<header class="topbar">(.*?)</header>', source, re.S)
    if not topbar:
        errors.append("Mobil başlık alanı bulunamadı.")
    else:
        header_source = topbar.group(1)
        menu_pos = header_source.find('id="mobileMenuToggle"')
        title_pos = header_source.find('class="topbar-title"')
        if menu_pos < 0 or title_pos < 0 or menu_pos > title_pos:
            errors.append("Mobil menü düğmesi sayfa başlığının solunda değil.")

WINDOWS_HTML_CHECK = ROOT / "windows" / "ui" / "index.html"
WINDOWS_CSS_CHECK = ROOT / "windows" / "ui" / "style.css"
if WINDOWS_HTML_CHECK.is_file():
    windows_html = WINDOWS_HTML_CHECK.read_text(encoding="utf-8")
    windows_topbar = re.search(r'<header class="topbar">(.*?)</header>', windows_html, re.S)
    if not windows_topbar:
        errors.append("Windows mobil başlık alanı bulunamadı.")
    else:
        header = windows_topbar.group(1)
        menu_pos = header.find('id="mobileMenuToggle"')
        title_pos = header.find('class="topbar-title"')
        if menu_pos < 0 or title_pos < 0 or menu_pos > title_pos:
            errors.append("Windows mobil menü düğmesi sayfa başlığının solunda değil.")
if WINDOWS_CSS_CHECK.is_file():
    windows_css = WINDOWS_CSS_CHECK.read_text(encoding="utf-8")
    if "@media(max-width:1024px)" not in windows_css or "overflow-y:auto" not in windows_css:
        errors.append("Windows telefon/tablet dikey sayfa kaydırma kuralları eksik.")
    if "body.mobile-menu-open .sidebar{display:flex!important}" not in windows_css:
        errors.append("Windows telefon menüsü açılma kuralı eksik.")
else:
    errors.append("Windows arayüz CSS dosyası bulunamadı.")

if MAIN.is_file():
    content = MAIN.read_text(encoding="utf-8")
    if "WebViewAssetLoader" not in content or "https://appassets.androidplatform.net/assets/ui/index.html" not in content:
        errors.append("MainActivity paketlenmiş HTTPS varlık kaynağını kullanmıyor")
    allowed_match = re.search(r"private val allowedStudentPdfs\s*=\s*setOf\((.*?)\n\s*\)", content, re.S)
    if not allowed_match:
        errors.append("MainActivity öğrenci PDF izin listesi bulunamadı.")
    else:
        allowed_pdfs = re.findall(r'"([^"]+\.pdf)"', allowed_match.group(1))
        if len(allowed_pdfs) != len(set(allowed_pdfs)):
            errors.append("MainActivity öğrenci PDF izin listesinde tekrar eden kayıt var.")
        if set(allowed_pdfs) != set(expected_pdfs):
            missing = sorted(set(expected_pdfs) - set(allowed_pdfs))
            extra = sorted(set(allowed_pdfs) - set(expected_pdfs))
            errors.append("Öğrenci PDF izin listesi uyuşmuyor: eksik=" + repr(missing) + "; extra=" + repr(extra))
    if 'provider != "groq"' not in content or "api.groq.com" not in content:
        errors.append("Android AI köprüsü yalnızca Groq sağlayıcısıyla sınırlandırılmamış.")
    if "StagepulseSesMerkezi/3.6.2" in content:
        errors.append("Android AI User-Agent eski 3.6.2 sürümünü içeriyor.")
    for required in (
        "PermissionRequest.RESOURCE_AUDIO_CAPTURE",
        "Manifest.permission.RECORD_AUDIO",
        "REQUEST_MEDIA_PERMISSION",
        "pendingMediaPermission",
        "appassets.androidplatform.net",
    ):
        if required not in content:
            errors.append("Android WebView medya izin akışı eksik: " + required)

if MANIFEST.is_file():
    import xml.etree.ElementTree as ET
    try:
        manifest_root = ET.parse(MANIFEST).getroot()
        android_ns = "{http://schemas.android.com/apk/res/android}"
        declared_permissions = {
            node.attrib.get(android_ns + "name")
            for node in manifest_root.findall("uses-permission")
        }
        required_permissions = {
            "android.permission.RECORD_AUDIO",
        }
        missing_permissions = sorted(required_permissions - declared_permissions)
        if missing_permissions:
            errors.append("AndroidManifest medya izinleri eksik: " + ", ".join(missing_permissions))
        declared_features = {
            (node.attrib.get(android_ns + "name"), node.attrib.get(android_ns + "required"))
            for node in manifest_root.findall("uses-feature")
        }
        if ("android.hardware.microphone", "false") not in declared_features:
            errors.append("Android mikrofon donanımı opsiyonel işaretlenmeli.")
        if "android.permission.CAMERA" in declared_permissions:
            errors.append("AndroidManifest kamera izni içermemeli.")
        if any(name == "android.hardware.camera.any" for name, _required in declared_features):
            errors.append("AndroidManifest kamera donanımı özelliği içermemeli.")
    except ET.ParseError as exc:
        errors.append("AndroidManifest XML geçersiz: " + str(exc))

gradle_file = ROOT / "android" / "app" / "build.gradle"
if gradle_file.is_file():
    gradle = gradle_file.read_text(encoding="utf-8")
    version_name = re.search(r"\bversionName\s+'([^']+)'", gradle)
    version_code = re.search(r"\bversionCode\s+(\d+)", gradle)
    if not version_name or not version_code:
        errors.append("Android versionName/versionCode bulunamadı.")
    else:
        parts = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", version_name.group(1))
        if not parts:
            errors.append("Android versionName X.Y.Z biçiminde değil.")
        else:
            expected_code = int(parts.group(1)) * 10000 + int(parts.group(2)) * 100 + int(parts.group(3))
            if int(version_code.group(1)) != expected_code:
                errors.append("Android versionCode uyuşmuyor: " + version_code.group(1) + " != " + str(expected_code))

WINDOWS_APP = ROOT / "windows" / "Merkez.py"
WINDOWS_INSTALLER = ROOT / "windows" / "EXE_OLUSTUR.ps1"
WINDOWS_NSI = ROOT / "windows" / "setup" / "StagepulseSesMerkezi.nsi"
WINDOWS_UI_JS = ROOT / "windows" / "ui" / "app.js"
ANDROID_UI_JS = UI / "app.js"
if all(p.is_file() for p in (WINDOWS_APP, WINDOWS_INSTALLER, WINDOWS_NSI, WINDOWS_HTML_CHECK, WINDOWS_UI_JS, ANDROID_UI_JS, gradle_file)):
    windows_app_text = WINDOWS_APP.read_text(encoding="utf-8")
    installer_text = WINDOWS_INSTALLER.read_text(encoding="utf-8")
    nsi_text = WINDOWS_NSI.read_text(encoding="utf-8-sig")
    windows_html_text = WINDOWS_HTML_CHECK.read_text(encoding="utf-8")
    windows_js_text = WINDOWS_UI_JS.read_text(encoding="utf-8")
    android_js_text = ANDROID_UI_JS.read_text(encoding="utf-8")
    android_html_text = HTML.read_text(encoding="utf-8")
    desktop_version = re.search(r'APP_VERSION\s*=\s*"([^"]+)"', windows_app_text)
    installer_version = re.search(r"\$version\s*=\s*'([^']+)'", installer_text)
    nsi_version = re.search(r'!define\s+VERSION\s+"([^"]+)"', nsi_text)
    android_version = re.search(r"\bversionName\s+'([^']+)'", gradle)
    desktop_ui_version = re.search(r"release\s+(\d+\.\d+\.\d+)", windows_js_text)
    android_ui_version = re.search(r"release\s+(\d+\.\d+\.\d+)", android_js_text)
    desktop_html_version = re.search(r"v(\d+\.\d+\.\d+)\s*·\s*Stagepulse", windows_html_text)
    android_html_version = re.search(r"v(\d+\.\d+\.\d+)\s*·\s*Stagepulse", android_html_text)
    desktop_versions = (desktop_version, installer_version, nsi_version, desktop_ui_version, desktop_html_version)
    android_versions = (android_version, android_ui_version, android_html_version)
    if not all(desktop_versions):
        errors.append("Windows uygulama/kurucu sürümlerinden biri tanımlı değil.")
    elif len({match.group(1) for match in desktop_versions}) != 1:
        errors.append("Windows uygulama ve kurucu sürümleri kendi içinde eşleşmiyor: " + ", ".join(sorted({match.group(1) for match in desktop_versions})))
    if not all(android_versions):
        errors.append("Android uygulama sürümlerinden biri tanımlı değil.")
    elif len({match.group(1) for match in android_versions}) != 1:
        errors.append("Android Gradle, arayüz ve HTML sürümleri kendi içinde eşleşmiyor: " + ", ".join(sorted({match.group(1) for match in android_versions})))
else:
    errors.append("Windows/Android sürüm eşitliği denetimi için gerekli dosyalar eksik.")

# Android WebView RTA: analiz düğümü sessiz sink üzerinden render grafiğine bağlı olmalı.
if ANDROID_UI_JS.is_file():
    rta_source = ANDROID_UI_JS.read_text(encoding="utf-8")
    required_rta_chain = (
        "createMediaStreamSource(browserRtaStream)",
        "createAnalyser()",
        "createGain()",
        "browserRtaAnalyser.connect(browserRtaSilentSink)",
        "browserRtaSilentSink.connect(browserRtaContext.destination)",
    )
    for token in required_rta_chain:
        if token not in rta_source:
            errors.append("Android RTA ses analiz zinciri eksik: " + token)

if errors:
    print("ANDROID VARLIK DENETİMİ BAŞARISIZ")
    for error in errors:
        print(" - " + error)
    sys.exit(1)

docs = json.loads(DOC_LIST.read_text(encoding="utf-8"))
print("Android varlık denetimi geçti: " + str(len(expected_pdfs)) + " PDF, " + str(len(docs)) + " ders belgesi, altı ortak mühendislik aracı ve dalga laboratuvarı, HTML/CSS referansları, Kotlin izin listesi, sürüm bilgileri ve ekran kesme noktaları doğrulandı.")
