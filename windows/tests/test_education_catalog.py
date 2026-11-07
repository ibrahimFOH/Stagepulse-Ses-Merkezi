import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_education_catalog_has_all_requested_branches_and_master_gate():
    catalog = json.loads((ROOT / "egitim_paketleri/stagepulse_egitim_katalogu_v1.json").read_text("utf-8"))
    ids = {x["id"] for x in catalog["tracks"]}
    assert {"live_sound", "rf_wireless", "pa_system", "studio_post", "spl_acoustics", "digital_console", "speech_broadcast", "maintenance"} <= ids
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
    assert 'data-page="curriculum"' in html and 'id="curriculumQuizButton"' in html
    assert 'function renderCurriculumQuiz()' in js and 'id="licenseBundle"' not in html
    assert 'const bundle = "full_master";' in edge
    assert 'bundle_code' in core and 'bundle_code: bundle' in edge
    assert 'bundle_code: valid ? (lic!.bundle_code ?? \"start\") : null' in edge
    assert 'bundle_code text not null' in migration
