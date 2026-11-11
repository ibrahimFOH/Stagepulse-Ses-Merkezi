from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]


def test_ui_has_no_external_script_or_stylesheet_dependencies():
    for name in ('ui/index.html', 'araclar/Frekans_Bulucu/index.html'):
        html = (ROOT / name).read_text(encoding='utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        external_scripts = [t.get('src') for t in soup.find_all('script') if str(t.get('src', '')).startswith(('http://', 'https://'))]
        external_styles = [t.get('href') for t in soup.find_all('link') if str(t.get('href', '')).startswith(('http://', 'https://'))]
        assert not external_scripts, f'{name}: external JS {external_scripts}'
        assert not external_styles, f'{name}: external CSS {external_styles}'


def test_ebu_reference_table_is_bundled_and_no_manual_csv_upload_remains():
    html = (ROOT / "ui/index.html").read_text(encoding="utf-8")
    app = (ROOT / "ui/app.js").read_text(encoding="utf-8")
    assert (ROOT / "references/ebu_tech3341_reference.csv").is_file()
    assert 'id="ebuReferenceCsv"' not in html
    assert "ebuReferenceCsvText" not in app
    assert "run_ebu_loudness_validation(tolerance)" in app
    assert "referans tablosu uygulamaya gömülüdür" in html


def test_packaged_paths_exist():
    required = ['Merkez.py', 'ui/index.html', 'ui/app.js', 'ui/rta_math.js', 'ui/acoustic_math.js', 'ui/style.css', 'ui/first_party_tools.js', 'ui/advanced_modules.js', 'tests/test_first_party_tools.js',
                'araclar/Frekans_Bulucu/index.html', 'egitim_paketleri/00_Uygulama_Kullanimi_Ogrenci.pdf',
                'egitim_paketleri/01_Ses_Muhendisligi_Ogrenci_Ders_Kitabi.pdf',
                'egitim_paketleri/09_SPL_dB_3D_Gorsel_Atlasi.pdf',
                'core/rta_capture.py', 'core/acoustic_engine.py', 'core/acoustic_api.py', 'ui/assets/stagepulse-logo.svg', 'ui/assets/stagepulse.ico', 'ui/assets/stagepulse-icon.png', 'ui/assets/spl-3d-konsept.png']
    for item in required:
        assert (ROOT / item).is_file(), item


def test_archives_are_not_embedded_in_student_app():
    assert not (ROOT / 'kaynak_arsivleri').exists()
    assert not list(ROOT.rglob('*.zip'))


def test_literal_javascript_dom_ids_exist_and_html_ids_are_unique():
    import re
    soup = BeautifulSoup((ROOT / 'ui/index.html').read_text(encoding='utf-8'), 'html.parser')
    ids = [node.get('id') for node in soup.find_all(id=True)]
    assert len(ids) == len(set(ids)), 'Duplicate HTML id'
    app_js = (ROOT / 'ui/app.js').read_text(encoding='utf-8')
    referenced = set(re.findall(r"\$\(['\"]([A-Za-z][A-Za-z0-9_-]*)['\"]\)", app_js))
    # SPL equipment editor builds these controls only after an item is selected.
    dynamic_ids = {'splEditAngle', 'splEditApply', 'splEditBeam', 'splEditLevel',
                   'splEditName', 'splEditRemove', 'splEditX', 'splEditY'}
    missing = sorted(referenced - set(ids) - dynamic_ids)
    assert not missing, f'JavaScript refers to missing DOM ids: {missing}'
    for dynamic_id in dynamic_ids:
        assert f'id="{dynamic_id}"' in app_js, f'Dynamic SPL control is not rendered: {dynamic_id}'


def test_pdf_save_does_not_navigate_out_of_the_single_app_window():
    app_js = (ROOT / 'ui/app.js').read_text(encoding='utf-8')
    assert 'save_student_pdf_dialog(item.file)' in app_js
    assert "window.open(r.url,'_self')" not in app_js
    assert "window.open('/KULLANIM_VE_DENETIM_REHBERI_TR.pdf','_self')" not in app_js
    assert 'loadStudentPdfs()' in app_js
    assert 'data-page="pdf"' in (ROOT / 'ui/index.html').read_text(encoding='utf-8')


def test_rta_controls_and_correct_band_math_are_wired():
    app_js = (ROOT / 'ui/app.js').read_text(encoding='utf-8')
    html = (ROOT / 'ui/index.html').read_text(encoding='utf-8')
    math_js = (ROOT / 'ui/rta_math.js').read_text(encoding='utf-8')
    assert 'rtaRefreshDevices' in html and 'rtaFftSize' in html and 'rtaRange' in html
    assert 'rtaCustomMin' in html and 'rtaCustomMax' in html
    assert 'Özel frekans aralığı' in html
    assert "value==='custom'" in app_js
    assert 'api().list_rta_devices()' in app_js
    assert 'api().start_rta(selected,fftSize)' in app_js
    assert 'api().get_rta_snapshot' in app_js
    assert 'sounddevice' in (ROOT / 'requirements.txt').read_text(encoding='utf-8')
    assert 'f*br <= nyquist*.999' in math_js


def test_webview2_runtime_is_embedded_in_setup_not_inside_app_payload():
    source = (ROOT / 'Merkez.py').read_text(encoding='utf-8')
    ps = (ROOT / 'EXE_OLUSTUR.ps1').read_text(encoding='utf-8-sig')
    nsi = (ROOT / 'setup' / 'StagepulseSesMerkezi.nsi').read_text(encoding='utf-8')
    asset = 'MicrosoftEdgeWebView2RuntimeInstallerX64.exe'
    assert asset in ps and asset in nsi
    assert not any('--add-data' in line and asset in line for line in ps.splitlines())
    assert 'File /oname=${WEBVIEW2_FILE} "${WEBVIEW2_INSTALLER}"' in nsi
    assert 'SetOutPath "$PLUGINSDIR"' in nsi
    assert '/silent /install' in nsi
    assert 'Kurulum dosyası bu bileşeni gerekiyorsa sessizce yükler.' in source


def test_build_uses_onedir_with_a_stable_internal_contents_directory():
    name = 'EXE_OLUSTUR.ps1'
    text = (ROOT / name).read_text(encoding='utf-8-sig')
    assert '--onedir' in text, name
    assert '--onefile' not in text, name
    assert "'--contents-directory','_internal'" in text, name


def test_windows_build_script_defines_data_separator_and_uses_single_output_name():
    ps = (ROOT / 'EXE_OLUSTUR.ps1').read_text(encoding='utf-8')
    assert '$sep = [IO.Path]::PathSeparator' in ps
    assert "'--add-data',\"ui${sep}ui\"" in ps
    assert "'--name','StagepulseSesMerkezi'" in ps
    assert "egitim_paketleri${sep}egitim_paketleri" in ps
    assert "Python 3.11, 3.12, 3.13 veya 3.14 x64" in ps
    assert "StagepulseSesMerkezi-Kurulum-$version.exe" in ps
    assert "APP_PAYLOAD" in ps and "makensis" in ps


def test_student_docs_have_no_old_v21_startup_instructions():
    start = (ROOT / 'docs/00_BASLANGIC_TR.md').read_text(encoding='utf-8')
    all_docs = '\n'.join(p.read_text(encoding='utf-8') for p in (ROOT / 'docs').glob('*.md'))
    assert 'Merkezi 2.1' not in start
    assert 'BASLAT.bat' not in start
    assert 'kaynak_arsivleri klasöründe değiştirilmeden tutulur' not in all_docs


def test_multitrack_memory_guards_are_enabled_for_low_ram_devices():
    app_js = (ROOT / 'ui/app.js').read_text(encoding='utf-8')
    assert 'MAX_DECODED_AUDIO_BYTES = 512 * 1024 * 1024' in app_js
    assert 'MAX_RENDER_AUDIO_BYTES = 320 * 1024 * 1024' in app_js
    assert 'MAX_AUDIO_WORK_BYTES = 1024 * 1024 * 1024' in app_js
    assert 'RAM koruması' in app_js


def test_all_student_pdf_materials_are_real_pdf_files_and_catalogued():
    import Merkez
    items = Merkez.STUDENT_PDFS
    assert len(items) == 13
    for item in items:
        path = ROOT / 'egitim_paketleri' / item['file']
        assert path.is_file(), item['file']
        assert path.read_bytes()[:5] == b'%PDF-'
    packaged_pdfs = {path.name for path in (ROOT / 'egitim_paketleri').glob('*.pdf')}
    catalogued_pdfs = {item['file'] for item in items}
    assert packaged_pdfs == catalogued_pdfs, 'Katalog dışında PDF veya eksik öğrenci PDF var.'
    assert not any('Egitmen' in item['file'] or 'Fiyat' in item['file'] or 'Denetim' in item['file'] for item in items)


def test_rta_math_module_is_loaded_before_application_logic():
    html = (ROOT / 'ui/index.html').read_text(encoding='utf-8')
    assert html.index('/ui/rta_math.js') < html.index('/ui/acoustic_math.js') < html.index('/ui/app.js')


def test_rta_prefers_native_microphone_and_clamps_to_full_bands():
    app_js = (ROOT / 'ui/app.js').read_text(encoding='utf-8')
    math_js = (ROOT / 'ui/rta_math.js').read_text(encoding='utf-8')
    capture = (ROOT / 'core/rta_capture.py').read_text(encoding='utf-8')
    assert 'getUserMedia' not in app_js
    assert 'clampRangeToSupported' in app_js and 'clampRangeToSupported' in math_js
    assert 'seconds_since_last_callback' in app_js and 'samples_received' in capture
    assert 'rtaCommandQueue' in app_js and 'enqueueRtaCommand' in app_js


def test_acoustic_dsp_engine_is_imported_only_when_analysis_is_requested():
    api = (ROOT / 'core/acoustic_api.py').read_text(encoding='utf-8')
    assert 'from core.acoustic_engine import transfer_function, delay_finder, impulse_response' not in api.split('class AcousticAnalysisApi:', 1)[0]
    assert 'from core.acoustic_engine import transfer_function, delay_finder, impulse_response' in api
    assert 'from core.acoustic_engine import transfer_function' in api
    assert 'from core.acoustic_engine import delay_finder' in api
    assert 'from core.acoustic_engine import impulse_response' in api


def test_audio_engine_is_lazy_and_does_not_block_startup():
    app_js = (ROOT / 'ui/app.js').read_text(encoding='utf-8')
    ear_init = app_js.split('function initEarTraining()', 1)[1].split('function newEqQuestion()', 1)[0]
    assert 'getAudioContext()' not in ear_init
    assert 'createBuffer(' not in ear_init
    assert "if(ctx.state!=='running')await ctx.resume()" in app_js
    assert 'async function playTone(' in app_js
    assert 'async function playNoise(' in app_js


def test_startup_initializers_fail_independently():
    app_js = (ROOT / 'ui/app.js').read_text(encoding='utf-8')
    assert 'function runInitStep(name, initialize, errors)' in app_js
    assert 'const runNext=(index)=>' in app_js
    assert 'window.setTimeout(()=>runNext(index+1),12)' in app_js
    assert 'requestAnimationFrame(()=>window.setTimeout(()=>runNext(0),0))' in app_js
    for initializer in ('initCalculators','initAcoustics','initEarTraining','initMixer','initRtaControls','initWav','initLufs','initCues','initChecklists','initStudent','initDocs','initAssistant','initAccount','initSettings'):
        assert initializer in app_js


def test_release_version_is_consistent():
    import re

    version_source = (ROOT / "Merkez.py").read_text(encoding="utf-8")
    match = re.search(r'APP_VERSION\s*=\s*"([^"]+)"', version_source)
    assert match, "Merkez.py APP_VERSION tanımlı olmalı"
    version = match.group(1)
    assert re.fullmatch(r"\d+\.\d+\.\d+", version), version
    major, minor, patch = (int(part) for part in version.split("."))
    expected_code = major * 10000 + minor * 100 + patch

    checks = {
        "EXE_OLUSTUR.ps1": (r"\$version\s*=\s*'([^']+)'", "utf-8-sig"),
        "setup/StagepulseSesMerkezi.nsi": (r'!define\s+VERSION\s+"([^"]+)"', "utf-8"),
        "ui/app.js": (r"Stagepulse UI release (\d+\.\d+\.\d+)", "utf-8"),
        "ui/first_party_tools.js": (r"sürüm (\d+\.\d+\.\d+)", "utf-8"),
        "README_TR.md": (r"^# Stagepulse Ses Mühendisliği Merkezi (\d+\.\d+\.\d+)$", "utf-8"),
    }
    for name, (pattern, encoding) in checks.items():
        content = (ROOT / name).read_text(encoding=encoding)
        found = re.search(pattern, content, re.M)
        assert found and found.group(1) == version, f"{name}: beklenen {version}"

    gradle = (ROOT.parent / "android" / "app" / "build.gradle").read_text(encoding="utf-8")
    android_name = re.search(r"versionName\s+'([^']+)'", gradle)
    android_code = re.search(r"versionCode\s+(\d+)", gradle)
    assert android_name and re.fullmatch(r"\d+\.\d+\.\d+", android_name.group(1)), "Android versionName geçersiz"
    android_parts = tuple(int(part) for part in android_name.group(1).split("."))
    android_expected_code = android_parts[0] * 10000 + android_parts[1] * 100 + android_parts[2]
    assert android_code and int(android_code.group(1)) == android_expected_code, "Android versionCode uyuşmuyor"

    android_tools = ROOT.parent / "android" / "app" / "src" / "main" / "assets" / "ui" / "first_party_tools.js"
    desktop_tools = ROOT / "ui" / "first_party_tools.js"
    assert desktop_tools.read_bytes() == android_tools.read_bytes(), "Windows ve Android ortak mühendislik motorları birebir eşleşmeli"


def test_acoustic_calculators_are_wired_and_have_explicit_limits():
    html = (ROOT / 'ui/index.html').read_text(encoding='utf-8')
    app = (ROOT / 'ui/app.js').read_text(encoding='utf-8')
    math = (ROOT / 'ui/acoustic_math.js').read_text(encoding='utf-8')
    assert 'data-page="acoustics"' in html and 'id="calcRt60"' in html
    for node_id in ('calcSplDistance','calcAudienceArea','calcPressureSpl','calcSplPressure','calcExposure','calcRt60','useFarDistance','useAudienceVolume','calcAbsorption','useAbsorptionResult','absWidth','absDepth','absHeight','absFrequency','absFloorAlpha','absCeilingAlpha','absLongWallAlpha','absShortWallAlpha'):
        assert f'id="{node_id}"' in html and node_id in app
    for node_id in ('exposureLevel2','exposureMinutes2','exposureLevel3','exposureMinutes3'):
        assert f'id="{node_id}"' in html
    assert "'exposureLevel'+(i===1?'':i)" in app and "'exposureMinutes'+(i===1?'':i)" in app
    for function in ('distanceSpl','areaPlan','pressureToSpl','splToPressure','sabineRt60','equivalentAbsorption','nioshExposure','nioshDose','recommendCuts'):
        assert f'function {function}' in math
    assert 'donanıma otomatik uygulanmaz' in app or 'otomatik uygulanmaz' in math


def test_rta_optimizer_is_advisory_only_and_smoothing_is_ordered():
    html = (ROOT / 'ui/index.html').read_text(encoding='utf-8')
    app = (ROOT / 'ui/app.js').read_text(encoding='utf-8')
    math = (ROOT / 'ui/acoustic_math.js').read_text(encoding='utf-8')
    assert 'rtaOptimizerHistory.length<8' in app
    assert 'rtaOptimizerTestSignalConfirm' in html and 'rtaOptimizerTestSignalConfirm' in app
    assert 'no auto' not in app.lower()
    assert 'Math.min(3' in math
    assert 'fast:.12,medium:.18,slow:.5' in app
    assert 'otomatik uygulanmaz' in app


def test_latest_student_pdf_has_correct_catalog_and_educational_only_scope():
    import Merkez
    items=Merkez.STUDENT_PDFS
    assert len(items)==13
    assert items[-1]['file']=='12_Allen_Heath_Avantis_Uygulamali_Egitim.pdf'
    assert (ROOT/'egitim_paketleri'/'08_SPL_Alan_RTA_Teknik_Uygulama_Eki.pdf').is_file()
    assert not any(('Egitmen' in x['file'] or 'Fiyat' in x['file'] or 'Denetim' in x['file']) for x in items)


def test_exposure_dose_ui_sums_multiple_blocks_and_warns_at_full_dose():
    html = (ROOT / 'ui/index.html').read_text(encoding='utf-8')
    app = (ROOT / 'ui/app.js').read_text(encoding='utf-8')
    math = (ROOT / 'ui/acoustic_math.js').read_text(encoding='utf-8')
    assert 'Blok 2 · LAeq' in html and 'Blok 3 · LAeq' in html
    assert 'AcousticMath.nioshDose(segments)' in app
    assert 'referenceDoseReached:dosePercent>=100' in math
    assert 'Birikimli NIOSH mesleki referans dozu' in app


def test_sabine_surface_absorption_estimator_is_connected_and_labeled_as_example():
    html = (ROOT / 'ui/index.html').read_text(encoding='utf-8')
    app = (ROOT / 'ui/app.js').read_text(encoding='utf-8')
    assert 'A = Σ(αᵢ × Sᵢ)' in html
    assert 'AcousticMath.equivalentAbsorption' in app and "val('absFrequency')" in app
    assert 'lastEquivalentAbsorption.equivalentAbsorptionM2' in app
    assert 'varsayılanlar yalnızca 500 Hz örneğidir' in html


def test_exposure_dose_ui_sums_multiple_blocks_and_warns_at_full_dose():
    html = (ROOT / 'ui/index.html').read_text(encoding='utf-8')
    app = (ROOT / 'ui/app.js').read_text(encoding='utf-8')
    math = (ROOT / 'ui/acoustic_math.js').read_text(encoding='utf-8')
    assert 'Blok 2 · LAeq' in html and 'Blok 3 · LAeq' in html
    assert 'AcousticMath.nioshDose(segments)' in app
    assert 'referenceDoseReached:dosePercent>=100' in math
    assert 'Birikimli NIOSH mesleki referans dozu' in app


def test_student_exe_bundles_only_student_docs_not_qa_reports():
    ps = (ROOT / 'EXE_OLUSTUR.ps1').read_text(encoding='utf-8')
    source = (ROOT / 'Merkez.py').read_text(encoding='utf-8')
    assert not any("--add-data" in line and "docs${sep}docs" in line for line in ps.splitlines())
    assert 'EGITIM_PDF_UYGULAMA_ESLESTIRMESI_TR.md' not in ps
    assert 'allowed_doc_paths' in source
    import Merkez
    handler = object.__new__(Merkez.LocalHandler)
    assert handler._allowed_resource('/docs/00_BASLANGIC_TR.md')
    assert not handler._allowed_resource('/docs/TEST_RAPORU_TR.md')
    assert not handler._allowed_resource('/docs/EGITIM_PDF_UYGULAMA_ESLESTIRMESI_TR.md')
    assert handler._allowed_resource('/egitim_paketleri/08_SPL_Alan_RTA_Teknik_Uygulama_Eki.pdf')
    assert not handler._allowed_resource('/egitim_paketleri/KULLANIM_VE_DENETIM_REHBERI_TR.pdf')


def test_student_pdf_fallback_catalog_matches_packaged_pdf_catalog():
    import re
    app = (ROOT / 'ui/app.js').read_text('utf-8')
    files = set(re.findall(r"file:'([^']+\.pdf)'", app[app.index('const fallbackStudentPdfs'):app.index('let studentPdfs=')]))
    packaged = {p.name for p in (ROOT / 'egitim_paketleri').glob('*.pdf')}
    assert files == packaged, f'Fallback PDF kataloğu uyuşmuyor: eksik={packaged-files}, fazla={files-packaged}'


def test_verified_nsis_archive_is_removed_before_application_tests():
    ps = (ROOT / 'EXE_OLUSTUR.ps1').read_text(encoding='utf-8-sig')
    zip_removed = ps.index("Remove-Item -LiteralPath $zip -Force -ErrorAction SilentlyContinue", ps.index("if ($zipVerified)"))
    tests_start = ps.index("python -m pytest -q")
    assert zip_removed < tests_start, 'Verified NSIS ZIP must be removed before bundle integrity tests.'
    assert "Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $expand" in ps


def test_console_training_manuals_are_real_turkish_19_page_pdfs():
    import fitz
    names = [
        '10_Midas_M32_Live_Uygulamali_Egitim.pdf',
        '11_Yamaha_CL5_Uygulamali_Egitim.pdf',
        '12_Allen_Heath_Avantis_Uygulamali_Egitim.pdf',
    ]
    for name in names:
        path = ROOT / 'egitim_paketleri' / name
        assert path.is_file() and path.stat().st_size > 40000
        doc = fitz.open(path)
        assert len(doc) >= 18
        text = '\n'.join(page.get_text() for page in doc)
        assert 'STAGEPULSE' in text and 'Uygulamalı' in text
        assert 'Sahada sık görülen hata' in text
        assert 'Kaynaklar ve doküman kontrolü' in text
        doc.close()


def test_application_brand_assets_are_valid_and_wired_to_desktop_build():
    from PIL import Image
    ico = ROOT / 'ui/assets/stagepulse.ico'
    png = ROOT / 'ui/assets/stagepulse-icon.png'
    with Image.open(ico) as im:
        assert im.format == 'ICO'
        assert im.size[0] >= 256
    with Image.open(png) as im:
        assert im.format == 'PNG' and im.size == (256, 256)
    ps = (ROOT / 'EXE_OLUSTUR.ps1').read_text(encoding='utf-8-sig')
    nsi = (ROOT / 'setup/StagepulseSesMerkezi.nsi').read_text(encoding='utf-8-sig')
    html = (ROOT / 'ui/index.html').read_text(encoding='utf-8')
    assert "'--icon','ui\\assets\\stagepulse.ico'" in ps
    assert '!pragma codepage 65001' in nsi
    assert 'DisplayIcon' in nsi and 'CreateShortcut "$DESKTOP\\Stagepulse Ses Merkezi.lnk"' in nsi
    assert 'href="/ui/assets/stagepulse-icon.png"' in html
    assert 'src="/ui/assets/stagepulse-logo-full.png"' in html
    assert (ROOT / 'ui/assets/stagepulse-logo-full.png').is_file()


def test_empty_profile_loading_is_cached_and_not_recursively_reloaded():
    app = (ROOT / 'ui/app.js').read_text(encoding='utf-8')
    assert 'let profilesLoaded = false;' in app
    assert 'if(profilesLoaded)return profiles;' in app
    assert 'if(profilesLoadPromise)return profilesLoadPromise;' in app
    assert 'profilesLoadPromise=(async()=>{' in app
    # Rendering a profile list must not itself start another native read.
    body = app.split('function refreshProfiles(){', 1)[1].split('function loadStudentData(', 1)[0]
    assert 'api().load_profiles()' not in body


def test_manual_sales_license_payment_is_checked_on_server_and_activation_rpc():
    edge = (ROOT / 'supabase/functions/ses-merkezi-desktop/index.ts').read_text(encoding='utf-8')
    migration = (ROOT / 'supabase/migrations/20261029150800_ses_merkezi_manual_sales.sql').read_text(encoding='utf-8')
    core = (ROOT / 'Merkez.py').read_text(encoding='utf-8')
    assert 'if (action === "license_payment_update")' in edge
    assert 'payment_status: paymentStatus' in edge
    assert 'lic.payment_status === "paid"' in edge
    assert "raise exception 'LICENSE_PAYMENT_REQUIRED'" in migration
    assert 'payment_method' in migration and 'payment_reference' in migration
    assert 'def license_payment_update' in core


def test_first_party_tools_are_local_and_every_direct_dom_reference_exists():
    import re
    html = (ROOT / 'ui/index.html').read_text(encoding='utf-8')
    tools = (ROOT / 'ui/first_party_tools.js').read_text(encoding='utf-8')
    soup = BeautifulSoup(html, 'html.parser')
    ids = {node.get('id') for node in soup.find_all(id=True)}
    referenced = set(re.findall(r"byId\(['\"]([A-Za-z][A-Za-z0-9_-]*)['\"]\)", tools))
    # System Designer is injected by the shared local UI module, so validate its
    # generated IDs alongside the IDs that are present in static HTML.
    dynamic_ids = set(re.findall(r"id\s*=\s*['\"]([A-Za-z][A-Za-z0-9_-]*)['\"]", tools))
    missing = sorted(referenced - ids - dynamic_ids)
    assert not missing, f'Yeni araçlarda HTML veya dinamik arayüz öğesi eksik: {missing}'
    assert re.search(r'<script src="/ui/first_party_tools.js" defer></script>', html)
    assert html.index('first_party_tools.js') < html.index('/ui/app.js')
    assert not re.search(r"https?://|\bfetch\s*\(|XMLHttpRequest|WebSocket|import\s*\(", tools)
    assert 'parseM32Scene' in tools and 'processCompressor' in tools and 'processGate' in tools
    assert 'calculatePowerLine' in tools and 'rfIntermodCollision' in tools
    assert 'roomHeatColor' in tools and 'drawStagePlan' in tools
    for route in ('systemplan', 'patch', 'rf', 'distribution', 'roommap', 'speaker'):
        assert f'data-page="{route}"' in html
        assert f'data-route="{route}"' in html


def test_release_version_and_local_tool_syntax_check_are_consistent():
    import re
    source = (ROOT / 'Merkez.py').read_text(encoding='utf-8')
    build = (ROOT / 'EXE_OLUSTUR.ps1').read_text(encoding='utf-8-sig')
    readme = (ROOT / 'README_TR.md').read_text(encoding='utf-8')
    match = re.search(r'APP_VERSION\s*=\s*"([^"]+)"', source)
    assert match, "APP_VERSION tanımlı olmalı"
    version = match.group(1)
    assert re.search(r"\$version\s*=\s*'" + re.escape(version) + r"'", build)
    assert f'# Stagepulse Ses Mühendisliği Merkezi {version}' in readme
    assert 'node --check ui\\first_party_tools.js' in build


def test_new_release_text_has_no_replacement_characters_or_old_exercise_typo():
    paths = [
        ROOT / 'ui/index.html',
        ROOT / 'ui/app.js',
        ROOT / 'ui/first_party_tools.js',
        ROOT / 'ui/style.css',
        ROOT / 'README_TR.md',
        ROOT / 'CHANGELOG_TR.md',
        ROOT / 'docs/REPO_BIRLESTIRME_MATRISI_TR.md',
    ]
    for path in paths:
        content = path.read_text(encoding='utf-8')
        assert chr(0xFFFD) not in content, f'Bozuk UTF-8 karakteri: {path.name}'
    html = (ROOT / 'ui/index.html').read_text(encoding='utf-8')
    assert 'ALISTIRMA' not in html
    assert 'ALIŞTIRMA' in html


def test_dynamics_quizzes_are_present_and_connected_to_local_audio_logic():
    html = (ROOT / 'ui/index.html').read_text(encoding='utf-8')
    tools = (ROOT / 'ui/first_party_tools.js').read_text(encoding='utf-8')
    for prefix in ('comp', 'gate'):
        for control in ('QuizNew', 'QuizPlayA', 'QuizPlayB', 'QuizAnswerA', 'QuizAnswerB', 'QuizFeedback'):
            assert f'id="{prefix}{control}"' in html
            assert f"'{prefix}{control}'" in tools
    assert 'Math.random() < 0.5' in tools
    assert 'answerQuiz' in tools and 'playQuizSample' in tools


def test_acoustic_analysis_is_visible_and_connected_to_native_api():
    html = (ROOT / 'ui/index.html').read_text(encoding='utf-8')
    app = (ROOT / 'ui/app.js').read_text(encoding='utf-8')
    api = (ROOT / 'Merkez.py').read_text(encoding='utf-8')
    assert 'id="acousticAnalyze"' in html
    assert 'id="acousticMagnitudeChart"' in html
    assert 'id="acousticPhaseChart"' in html
    assert 'id="acousticCoherenceChart"' in html
    assert "['Akustik sistem analizi',initAcousticAnalyzer]" in app
    assert 'api().analyze_stereo_wav(path,size,overlap)' in app
    assert 'class AppApi(AcousticAnalysisApi):' in api
    assert 'dB SPL kalibrasyonu' in html


def test_windows_saved_auth_session_is_restored_during_native_startup():
    app_js = (ROOT / 'ui/app.js').read_text(encoding='utf-8')
    merkez = (ROOT / 'Merkez.py').read_text(encoding='utf-8')
    assert 'const authPromise = api().auth_restore()' in app_js
    assert 'Promise.race([authPromise,new Promise(resolve=>setTimeout(()=>resolve(null),3000))])' in app_js
    assert 'SESSION_PATH = DATA_ROOT / "hesap_oturumu.dat"' in merkez
    assert 'def auth_restore(self)' in merkez
    assert '_persist_auth_session()' in merkez


def test_spl_equipment_editor_and_live_source_map_are_wired():
    html = (ROOT / 'ui/index.html').read_text(encoding='utf-8')
    app = (ROOT / 'ui/app.js').read_text(encoding='utf-8')
    assert 'id="splEquipmentEditor"' in html
    for control in ('splEquipmentCategory', 'splEquipmentAdd', 'splEquipmentList',
                    'splEquipmentProperties', 'splEquipmentReset'):
        assert f'id="{control}"' in html
    assert 'function initSplEquipmentEditor()' in app
    assert 'function renderSplEquipment()' in app
    assert 'function splMapLevel(x,y,p)' in app
    assert 'energy+=Math.pow(10,level/10)' in app
    assert 'splEquipment.forEach(e=>' in app
    assert 'pointermove' in app and 'pointerdown' in app
    assert 'çoklu noktasal kaynak enerji toplamı' in html.lower() or 'çoklu noktasal kaynakların enerji toplamı' in html.lower()


def test_student_purchase_and_whatsapp_support_are_visible():
    html = (ROOT / 'ui/index.html').read_text(encoding='utf-8')
    app = (ROOT / 'ui/app.js').read_text(encoding='utf-8')
    assert 'id="studentPurchaseCta"' in html
    assert 'id="studentWhatsAppCta"' in html
    assert 'WhatsApp destek / iletişim' in html
    assert 'https://wa.me/905320683012' in app
    assert 'open_whatsapp' in app


def test_compressor_and_gate_ear_training_are_not_removed():
    html = (ROOT / 'ui/index.html').read_text(encoding='utf-8')
    tools = (ROOT / 'ui/first_party_tools.js').read_text(encoding='utf-8')
    for item in ('compThreshold', 'compRatio', 'compPlayA', 'compPlayB',
                 'gateThreshold', 'gateRange', 'gatePlayA', 'gatePlayB'):
        assert f'id="{item}"' in html
    assert 'processCompressor' in tools and 'processGate' in tools
    assert 'initDynamicsEarTraining' in tools
