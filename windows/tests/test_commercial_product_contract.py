from pathlib import Path
import ast
import re

ROOT = Path(__file__).resolve().parents[1]


def test_ai_catalog_allows_only_ollama_and_groq_without_persisting_keys():
    source = (ROOT / 'core' / 'ai_providers.py').read_text('utf-8')
    ui = (ROOT / 'ui' / 'index.html').read_text('utf-8')
    app = (ROOT / 'ui' / 'app.js').read_text('utf-8')
    module = ast.parse(source)
    providers_node = next(
        node.value for node in module.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == 'PROVIDERS' for target in node.targets)
    )
    providers = ast.literal_eval(providers_node)
    assert set(providers) == {'ollama', 'groq'}
    for provider in ('ollama', 'groq'):
        assert f'value="{provider}"' in ui
    for retired in ('openai', 'gemini', 'grok', 'openai_compatible'):
        assert f'value="{retired}"' not in ui
    assert 'api_key' in source
    assert 'Anahtar kaydedilmez' in ui
    assert "finally{\n  $('aiKey').value='';" in app
    assert 'storeSecret("api_key"' not in app


def test_commercial_license_backend_is_server_only_and_teacher_progress_guarded():
    migration = (ROOT / 'supabase/migrations/20261029000000_ses_merkezi_commercial_licensing.sql').read_text('utf-8').lower()
    edge = (ROOT / 'supabase/functions/ses-merkezi-desktop/index.ts').read_text('utf-8')
    for table in ('sesm_license_keys', 'sesm_activations', 'sesm_students', 'sesm_progress', 'sesm_audit_events'):
        assert f'create table if not exists public.{table}' in migration
        assert f'alter table public.{table} enable row level security' in migration
    assert 'revoke all on table public.sesm_license_keys' in migration
    assert 'p_max' in migration or 'max_activations' in migration
    assert 'async function requireOwner(userId: string)' in edge
    assert 'if (action === "license_create") {\n      await requireOwner(user.id);' in edge
    assert 'if (action === "progress_mark") {\n      await requireOwner(user.id);' in edge
    assert 'sesm_audit_events' in edge
    assert 'SUPABASE_SERVICE_ROLE_KEY' in edge  # server environment only; never put the secret in UI/EXE
    assert 'SUPABASE_SERVICE_ROLE_KEY' not in (ROOT / 'ui/app.js').read_text('utf-8')


def test_single_installer_publication_is_honest_until_site_manifest_exists():
    readme = (ROOT / 'README_TR.md').read_text('utf-8')
    script = (ROOT / 'EXE_OLUSTUR.ps1').read_text('utf-8')
    nsi = (ROOT / 'setup/StagepulseSesMerkezi.nsi').read_text('utf-8')
    assert 'latest.json' in readme and 'yayımlanmadı' in readme
    assert 'dist klasöründe tam olarak bir EXE' in script
    assert 'CreateShortcut "$DESKTOP\\Stagepulse Ses Merkezi.lnk"' in nsi
    assert 'CreateShortcut "$SMPROGRAMS\\Stagepulse\\Stagepulse Ses Merkezi.lnk"' in nsi
    assert 'CreateShortcut' in nsi
    assert 'StagepulseSesMerkezi-Kurulum-$version.exe' in script


def test_window_sizing_and_student_pdf_fallback_are_complete():
    app = (ROOT / 'ui/app.js').read_text('utf-8')
    assert '09_SPL_dB_3D_Gorsel_Atlasi.pdf' in app
    assert 'def initial_window_size(' in (ROOT / 'Merkez.py').read_text('utf-8')
    assert 'height=win_height' in (ROOT / 'Merkez.py').read_text('utf-8')


def test_owner_license_inventory_and_revoke_controls_are_connected():
    html = (ROOT / 'ui/index.html').read_text('utf-8')
    app = (ROOT / 'ui/app.js').read_text('utf-8')
    core = (ROOT / 'Merkez.py').read_text('utf-8')
    edge = (ROOT / 'supabase/functions/ses-merkezi-desktop/index.ts').read_text('utf-8')
    assert 'id="refreshLicenseList"' in html and 'id="licenseList"' in html
    assert 'async function refreshLicenseList()' in app
    assert 'data-revoke-license' in app
    assert 'def license_list(self)' in core
    assert 'if (action === "license_list")' in edge
    assert 'if (action === "license_revoke")' in edge


def test_ollama_default_groq_fallback_and_full_package_sales_contract():
    ai = (ROOT / 'core' / 'ai_providers.py').read_text('utf-8')
    ui = (ROOT / 'ui' / 'app.js').read_text('utf-8')
    assert 'http://127.0.0.1:11434/api/chat' in ai
    assert 'https://api.groq.com/openai/v1/chat/completions' in ai
    assert '"model": "openai/gpt-oss-120b"' in ai
    assert "auto:{endpoint:'http://127.0.0.1:11434/api/chat',model:'auto'}" in ui
    assert "groq:{endpoint:'https://api.groq.com/openai/v1/chat/completions',model:'openai/gpt-oss-120b'}" in ui
    html = (ROOT / 'ui' / 'index.html').read_text('utf-8')
    edge = (ROOT / 'supabase' / 'functions' / 'ses-merkezi-desktop' / 'index.ts').read_text('utf-8')
    assert 'id="fullPackagePurchasePanel"' in html
    assert 'id="fullPackageAdminPanel"' in html
    assert 'licensePlan' not in html and 'licenseBundle' not in html
    assert 'function commerceApi()' in ui and 'purchase_submit' in ui and 'purchase_review' in ui
    assert 'store_update' in ui and 'await refreshLicenseList();' in ui
    assert 'price > 2500' in edge and 'sesm_review_full_package_purchase' in edge
    assert 'purchase_submit' in edge and 'purchase_review' in edge



def test_windows_and_android_clients_use_the_current_stagepulse_core_project():
    current_url = 'https://itasctyjzyewcykozuex.supabase.co'
    current_key = 'sb_publishable_tP3CMhVAjv6FNtrkYfVEOA_dbF9m8Jb'
    retired_url = 'https://mtjcqqrogjqaxkagwkti.supabase.co'
    retired_key = 'sb_publishable_yR_HlWlFbYYq22tQmiB9LA_acq6bQi6'

    windows = (ROOT / 'Merkez.py').read_text('utf-8')
    android = (
        ROOT.parent / 'android' / 'app' / 'src' / 'main' / 'java'
        / 'com' / 'stagepulse' / 'sesmerkezi' / 'MainActivity.kt'
    ).read_text('utf-8')

    for source in (windows, android):
        assert current_url in source
        assert current_key in source
        assert retired_url not in source
        assert retired_key not in source
    assert 'SUPABASE_SERVICE_ROLE_KEY' not in windows
    assert 'SUPABASE_SERVICE_ROLE_KEY' not in android

def test_all_windows_owner_logins_use_shared_supabase_auth():
    source = (ROOT / 'Merkez.py').read_text('utf-8')
    assert 'LICENSE_ADMIN_EMAILS' not in source
    assert '_admin_auth_request' not in source
    assert 'if not identity or "@" not in identity or not password' in source
    assert 'self._auth_request("/auth/v1/token?grant_type=password"' in source


def test_repository_readme_versions_match_windows_and_android_builds():
    readme = (ROOT.parent / 'README.md').read_text('utf-8')
    windows = (ROOT / 'Merkez.py').read_text('utf-8')
    android = (ROOT.parent / 'android/app/build.gradle').read_text('utf-8')
    windows_version = re.search(r'^APP_VERSION\s*=\s*"([^"]+)"', windows, re.MULTILINE)
    android_name = re.search(r"versionName\s+'([^']+)'", android)
    android_code = re.search(r'versionCode\s+(\d+)', android)
    assert windows_version and android_name and android_code
    assert f"| Windows Ses Merkezi | {windows_version.group(1)} |" in readme
    assert f"| Android Ses Merkezi | {android_name.group(1)} ({android_code.group(1)}) |" in readme


def test_private_source_actions_are_scoped_and_manually_runnable():
    windows = (ROOT.parent / '.github/workflows/build-windows-exe.yml').read_text('utf-8')
    release = (ROOT.parent / '.github/workflows/trigger-ses-merkezi-release.yml').read_text('utf-8')

    assert 'workflow_dispatch:' in windows and 'pull_request:' in windows
    assert 'branches: [main]' in windows
    assert 'push:' in windows
    assert not (ROOT.parent / '.github/workflows/build-admin-apps.yml').exists()
    assert 'push:' in release and 'workflow_dispatch:' in release

def test_stagepulse_release_version_is_consistent_across_platforms():
    root = ROOT.parent
    windows = (ROOT / 'Merkez.py').read_text('utf-8')
    installer = (ROOT / 'EXE_OLUSTUR.ps1').read_text('utf-8')
    nsi = (ROOT / 'setup/StagepulseSesMerkezi.nsi').read_text('utf-8')
    windows_html = (ROOT / 'ui/index.html').read_text('utf-8')
    windows_js = (ROOT / 'ui/app.js').read_text('utf-8')
    android_gradle = (root / 'android/app/build.gradle').read_text('utf-8')
    android_html = (root / 'android/app/src/main/assets/ui/index.html').read_text('utf-8')
    android_js = (root / 'android/app/src/main/assets/ui/app.js').read_text('utf-8')
    readme = (root / 'README.md').read_text('utf-8')

    windows_version = re.search(r'^APP_VERSION\s*=\s*"([^"]+)"', windows, re.MULTILINE)
    assert windows_version, "Windows APP_VERSION tanımlı olmalı"
    version = windows_version.group(1)
    parts = tuple(int(part) for part in version.split('.'))
    assert len(parts) == 3 and all(part >= 0 for part in parts)
    expected_code = parts[0] * 10000 + parts[1] * 100 + parts[2]

    assert f"$version = '{version}'" in installer
    assert f'!define VERSION "{version}"' in nsi
    android_version = re.search(r"versionName\s+'([^']+)'", android_gradle)
    android_code = re.search(r"versionCode\s+(\d+)", android_gradle)
    assert android_version and re.fullmatch(r"\d+\.\d+\.\d+", android_version.group(1))
    android_parts = tuple(int(part) for part in android_version.group(1).split("."))
    android_expected_code = android_parts[0] * 10000 + android_parts[1] * 100 + android_parts[2]
    assert android_code and int(android_code.group(1)) == android_expected_code
    assert version in windows_html and version in windows_js
    assert android_version.group(1) in android_html and android_version.group(1) in android_js
    assert f"| Windows Ses Merkezi | {version} |" in readme
    assert f"| Android Ses Merkezi | {android_version.group(1)} ({android_expected_code}) |" in readme
    assert f"version:'{version}'" in windows_js



def test_ses_merkezi_requires_paid_license_or_authenticated_trial():
    edge = (ROOT / 'supabase/functions/ses-merkezi-desktop/index.ts').read_text('utf-8')
    desktop = (ROOT / 'Merkez.py').read_text('utf-8')
    windows_ui = (ROOT / 'ui/app.js').read_text('utf-8')
    android_ui = (
        ROOT.parent / 'android/app/src/main/assets/ui/app.js'
    ).read_text('utf-8')
    android_native = (
        ROOT.parent / 'android/app/src/main/java/com/stagepulse/sesmerkezi/MainActivity.kt'
    ).read_text('utf-8')

    assert 'DEMO_FEATURES' not in edge
    assert 'trialContext(' in edge
    assert 'const allowed = entitlement.paid || entitlement.trial.active === true;' in edge
    assert 'demo: entitlement.trial.active === true' in edge
    assert 'trial.active===true' in windows_ui and 'trial.active===true' in android_ui
    assert 'trial_active = bool(trial_info.get("active")) and not licensed' in desktop
    assert 'val trial = context.optJSONObject("trial")?.optBoolean("active", false) == true' in android_native
    assert '"demo_mode": False' in desktop
    assert '"license_required_for_local_tools": True' in desktop
    assert 'Yerel demo açık' not in windows_ui
    assert 'Yerel demo açık' not in android_ui
    assert '7L * 24L * 60L * 60L * 1000L' in android_native

def test_ses_merkezi_uses_one_license_scope_without_bundle_picker():
    html = (ROOT / 'ui/index.html').read_text('utf-8')
    ui = (ROOT / 'ui/app.js').read_text('utf-8')
    edge = (ROOT / 'supabase/functions/ses-merkezi-desktop/index.ts').read_text('utf-8')
    migration = (ROOT / 'supabase/migrations/20261107143000_sesm_full_package_bank_transfer.sql').read_text('utf-8')

    assert 'licenseBundle' not in html
    assert 'licenseBundle' not in ui
    assert 'paket ${' not in ui
    assert 'sesm_review_full_package_purchase' in edge
    assert "'full_master'" in migration
    assert 'allowedBundles' not in edge

def test_device_revoke_is_atomic_and_inactive_bindings_can_transfer():
    migration = (
        ROOT / 'supabase/migrations/20261107120000_sesm_device_transfer_after_revoke.sql'
    ).read_text('utf-8')
    edge = (ROOT / 'supabase/functions/ses-merkezi-desktop/index.ts').read_text('utf-8')

    assert 'create or replace function public.sesm_revoke_activation' in migration
    assert 'grant execute on function public.sesm_revoke_activation(uuid,uuid) to service_role' in migration
    assert 'is_active=true and user_id is not null and user_id<>p_user_id' in migration
    assert 'admin.rpc("sesm_revoke_activation"' in edge


def test_live_measurement_controls_are_exposed_with_explicit_limits():
    html = (ROOT / 'ui' / 'index.html').read_text('utf-8')
    app = (ROOT / 'ui' / 'app.js').read_text('utf-8')
    core = (ROOT / 'core' / 'rta_capture.py').read_text('utf-8')
    tf = (ROOT / 'core' / 'tf_capture.py').read_text('utf-8')
    bridge = (ROOT / 'Merkez.py').read_text('utf-8')

    assert 'id="startLiveTf"' in html and 'id="liveTfDevice"' in html
    assert 'list_tf_devices' in bridge and 'start_tf' in bridge and 'get_tf_snapshot' in bridge
    assert 'function initLiveTfControls()' in app
    assert 'calibrate_spl' in core and 'id="rtaCalibrate"' in html
    assert 'stream_stale' in core and 'stream_stale' in tf
    assert "if(snapshot.stream_stale){rtaSmoothed=null;rtaTraceHistory=[];drawRta([]);}" in app
    assert "if(snapshot.stream_stale){" in app and "const blank=Array(snapshot.centers.length).fill(Number.NaN);" in app
    assert 'SPL kalibrasyonu' in app
    assert 'IEC sınıfı' in app or 'IEC' in html


def test_full_package_bank_transfer_requires_owner_approval_and_server_license_creation():
    migration = (ROOT / 'supabase/migrations/20261107143000_sesm_full_package_bank_transfer.sql').read_text('utf-8')
    edge = (ROOT / 'supabase/functions/ses-merkezi-desktop/index.ts').read_text('utf-8')

    assert "product_code text not null default 'full_package' check (product_code = 'full_package')" in migration
    assert "payment_method in ('cash','bank_transfer','legacy')" in migration
    assert 'revoke all on public.sesm_purchase_requests from anon, authenticated' in migration
    assert 'sesm_purchase_requests_one_open_or_approved_per_user_idx' in migration
    assert 'if (action === "purchase_submit")' in edge
    assert 'if (action === "purchase_review")' in edge
    assert 'await requireOwner(user.id)' in edge
    assert 'admin.rpc("sesm_review_full_package_purchase"' in edge
    assert "'bank_transfer','paid'" in migration
    assert 'purchase_reference' not in edge


def test_full_package_sales_cannot_bypass_bank_transfer_owner_approval():
    desktop_edge = (ROOT / 'supabase/functions/ses-merkezi-desktop/index.ts').read_text('utf-8')
    core_edge = (ROOT / 'supabase/functions/license-core/index.ts').read_text('utf-8')

    direct_create = desktop_edge[desktop_edge.index('if (action === "license_create")'):]
    direct_create = direct_create[:direct_create.index('if (action === "license_payment_update")')]
    assert 'BANK_TRANSFER_APPROVAL_REQUIRED' in direct_create
    assert 'sesm_review_full_package_purchase' in desktop_edge
    assert 'purchase_review' in desktop_edge
    admin_create = core_edge[core_edge.index('async function adminCreate'):core_edge.index('Deno.serve')]
    assert 'appId === "ses-merkezi"' in admin_create
    assert 'appId === "ses-merkezi-android"' in admin_create
    assert 'BANK_TRANSFER_APPROVAL_REQUIRED' in admin_create
