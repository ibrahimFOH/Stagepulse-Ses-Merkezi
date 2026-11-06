from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "website_release" / "ses-merkezi-lisans"


def test_mobile_web_panel_has_secure_login_and_core_actions():
    html = (PANEL / "index.html").read_text("utf-8")
    js = (PANEL / "admin.js").read_text("utf-8")
    css = (PANEL / "admin.css").read_text("utf-8")
    assert '<html lang="tr">' in html
    assert 'meta name="robots" content="noindex,nofollow,noarchive"' in html
    assert 'id="loginForm"' in html and 'id="licenseForm"' in html
    assert 'id="licenseList"' in html and 'id="auditList"' in html
    assert 'stagepulse_sesm_admin_token' in js
    assert 'loginWithCustomCredentials' in js
    assert 'ADMIN_LOGIN_URL' in js and '/functions/v1/license-admin' in js
    assert 'signInWithPassword' not in js
    assert "context" in js and ("context.role !== 'owner'" in js or "c.role!=='owner'" in js)
    for action in ('license_list', 'license_create', 'license_payment_update', 'license_revoke', 'license_activations', 'activation_revoke', 'license_extend', 'audit_list'):
        assert f"invoke('{action}'" in js or f"invoke(\"{action}\"" in js
    assert 'SUPABASE_SERVICE_ROLE_KEY' not in js
    assert 'service_role' not in html.lower()
    assert '@media(max-width:640px)' in css
    assert 'navigator.clipboard.writeText' in js
    assert 'Tahsilatı gerçekten aldığını onaylıyor musun?' in js
    assert 'sb_secret_' not in js and 'service_role' not in js.lower()
    assert ('escapeHtml' in js or 'const esc =' in js)


def test_new_admin_actions_are_owner_guarded_and_license_scoped():
    edge = (ROOT / "supabase" / "functions" / "ses-merkezi-desktop" / "index.ts").read_text("utf-8")
    for action in ('license_activations', 'activation_revoke', 'license_extend', 'audit_list'):
        action_block = edge.split(f'if (action === "{action}") {{', 1)[1].split('\n    if (action === ', 1)[0]
        assert 'await requireOwner(user.id);' in action_block
    assert '.eq("created_by", user.id)' in edge
    assert 'device_hint:' in edge
    assert 'license_extended' in edge
    assert 'activation_revoked' in edge
