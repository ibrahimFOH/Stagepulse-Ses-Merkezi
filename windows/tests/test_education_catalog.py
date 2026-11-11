import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_education_catalog_has_all_requested_branches_and_master_gate():
    catalog = json.loads((ROOT / "egitim_paketleri/stagepulse_egitim_katalogu_v1.json").read_text("utf-8"))
    ids = {x["id"] for x in catalog["tracks"]}
    assert {"live_sound", "rf_wireless", "pa_system", "studio_post", "mix_mastering", "spl_acoustics", "digital_console", "speech_broadcast", "maintenance"} <= ids
    assert [x["id"] for x in catalog["levels"]] == ["L0", "L1", "L2", "L3", "L4", "L5"]
    assert all(x["practicals"] and x["master_gate"] for x in catalog["tracks"])
    assert catalog["evaluation_policy"]["student_can_mark_mastery"] is False
    assert len(catalog["packages"]) >= 8

def test_curriculum_ui_has_practice_test_and_single_license_scope():
    html = (ROOT / "ui/index.html").read_text("utf-8")
    js = (ROOT / "ui/app.js").read_text("utf-8")
    core = (ROOT / "Merkez.py").read_text("utf-8")
    edge = (ROOT / "supabase/functions/ses-merkezi-desktop/index.ts").read_text("utf-8")
    migration = (ROOT / "supabase/migrations/20261029190000_ses_merkezi_education_bundles.sql").read_text("utf-8")
    sales_migration = (ROOT / "supabase/migrations/20261107143000_sesm_full_package_bank_transfer.sql").read_text("utf-8")
    assert 'data-page="curriculum"' in html and 'id="curriculumQuizButton"' in html
    assert 'function renderCurriculumQuiz()' in js and 'id="licenseBundle"' not in html
    assert 'sesm_review_full_package_purchase' in edge
    assert 'bundle_code' in core
    assert "'full_master'" in sales_migration
    assert 'bundle_code: valid ? (lic!.bundle_code ?? \"start\") : null' in edge
    assert 'bundle_code text not null' in migration


def test_mix_mastering_branch_has_complete_turkish_training_content():
    catalog = json.loads((ROOT / "egitim_paketleri/stagepulse_egitim_katalogu_v1.json").read_text("utf-8"))
    track = next(x for x in catalog["tracks"] if x["id"] == "mix_mastering")
    assert len(track["workflow"]) == 12
    assert len(track["cards"]) == 72
    assert len(track["problems"]) == 40
    assert all(x["title"] and x["principle"] and x["practice"] and x["verification"] for x in track["cards"])
    assert all(x["symptom"] and x["possible_causes"] and x["diagnosis"] and x["first_action"] for x in track["problems"])
    for path in (ROOT / "ui/index.html", ROOT / "ui/app.js"):
        assert "mix_mastering" in path.read_text("utf-8")


def test_mix_mastering_is_fully_wired_on_windows_and_android():
    repo = ROOT.parent
    android = repo / "android/app/src/main/assets"
    windows_html = (ROOT / "ui/index.html").read_text("utf-8")
    android_html = (android / "ui/index.html").read_text("utf-8")
    windows_js = (ROOT / "ui/app.js").read_text("utf-8")
    android_js = (android / "ui/app.js").read_text("utf-8")
    windows_core = (ROOT / "Merkez.py").read_text("utf-8")
    windows_doc = ROOT / "docs/MIKS_MASTERING_KAYNAK_REHBERI_TR.md"
    android_doc = android / "docs/MIKS_MASTERING_KAYNAK_REHBERI_TR.md"
    android_docs_list = json.loads((android / "ui/docs-list.json").read_text("utf-8"))
    windows_catalog = ROOT / "egitim_paketleri/stagepulse_egitim_katalogu_v1.json"
    android_catalog = android / "egitim_paketleri/stagepulse_egitim_katalogu_v1.json"

    assert "MIKS_MASTERING_KAYNAK_REHBERI_TR.md" in windows_core
    assert windows_doc.is_file() and android_doc.is_file()
    assert any(item["file"] == "MIKS_MASTERING_KAYNAK_REHBERI_TR.md" for item in android_docs_list)
    assert windows_doc.read_bytes() == android_doc.read_bytes()
    assert windows_catalog.read_bytes() == android_catalog.read_bytes()
    for html in (windows_html, android_html):
        assert 'data-select-track="mix_mastering"' in html
        assert 'value="mix_mastering"' in html
    for js in (windows_js, android_js):
        assert "data-select-track" in js
        assert "curriculumQuizBank.mix_mastering" in js
        assert "chooseBrowserLufs(target,tp);return;" in js
    assert "normalize_lufs_dialog(target,tp)" in windows_js
    assert "normalize_lufs_dialog(target,tp)" not in android_js
    marker = "// --- Multitrack mix lab ---"
    win_engine = windows_js[windows_js.index("async function normalizeLoudnessBrowser"):windows_js.index(marker)]
    android_engine = android_js[android_js.index("async function normalizeLoudnessBrowser"):android_js.index(marker)]
    assert win_engine == android_engine
