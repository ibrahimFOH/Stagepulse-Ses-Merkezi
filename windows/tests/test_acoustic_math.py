from __future__ import annotations
import json
import shutil
import subprocess
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which('node')
pytestmark = pytest.mark.skipif(NODE is None, reason='Akustik JavaScript birim testleri için Node.js gerekir.')


def run_js(expression: str):
    module = (ROOT / 'ui' / 'acoustic_math.js').as_posix()
    code = f"const m=require({json.dumps(module)}); const result=({expression}); console.log(JSON.stringify(result));"
    result = subprocess.run([NODE, '-e', code], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', check=True)
    return json.loads(result.stdout)


def test_independent_equal_db_sources_sum_by_energy_not_arithmetic():
    assert run_js('m.dbSum([90,90])') == pytest.approx(93.0102999566, abs=1e-8)
    assert run_js('m.dbSum([90,87])') == pytest.approx(91.7643486, abs=1e-5)


def test_pressure_spl_forward_and_reverse_examples():
    assert run_js('m.pressureToSpl(0.1)') == pytest.approx(73.9794000867, abs=1e-8)
    assert run_js('m.splToPressure(94)') == pytest.approx(1.002374467, rel=1e-7)
    assert run_js('m.pressureToSpl(m.splToPressure(94))') == pytest.approx(94, abs=1e-10)


def test_distance_spl_formula_and_multiple_source_assumption_are_explicit():
    result = run_js('m.distanceSpl(100,1,10,2)')
    assert result['singleSourceDbSpl'] == pytest.approx(80, abs=1e-10)
    assert result['combinedEnergyEstimateDbSpl'] == pytest.approx(83.0102999566, abs=1e-8)
    assert result['distanceCorrectionDb'] == pytest.approx(-20, abs=1e-10)
    assert any('faz' in x.lower() for x in result['assumptions'])


def test_area_geometry_and_width_coverage_example():
    result = run_js('m.areaPlan(20,30,6,90)')
    assert result['areaM2'] == pytest.approx(600)
    assert result['volumeM3'] == pytest.approx(3600)
    assert result['farthestCornerDistanceM'] == pytest.approx(31.6227766)
    assert result['idealWidthAtRearM'] == pytest.approx(60)
    assert result['idealWidthCoveragePercent'] == 100
    assert any('kutup' in x.lower() or 'gerçek' in x.lower() for x in result['assumptions'])


def test_wavelength_is_not_mistaken_for_delay_preset():
    result = run_js('m.wavelength(100)')
    assert result['wavelengthM'] == pytest.approx(3.43)
    assert result['quarterWaveM'] == pytest.approx(0.8575)
    assert result['halfWaveM'] == pytest.approx(1.715)
    assert result['periodMs'] == pytest.approx(10)
    assert 'delay' in result['note'].lower()


def test_axial_room_mode_first_order_matches_known_example():
    modes = run_js('m.axialModes(5,4,2.5,343,1)')
    values = {(x['axis'],x['order']):x['frequencyHz'] for x in modes}
    assert values[('Uzunluk',1)] == pytest.approx(34.3)
    assert values[('Genişlik',1)] == pytest.approx(42.875)
    assert values[('Yükseklik',1)] == pytest.approx(68.6)


def test_niosh_reference_uses_three_db_exchange_rate_and_dose():
    a = run_js('m.nioshExposure(85,480)')
    b = run_js('m.nioshExposure(88,240)')
    c = run_js('m.nioshExposure(91,120)')
    assert a['nioshReferenceMinutes'] == pytest.approx(480)
    assert a['dosePercent'] == pytest.approx(100)
    assert b['dosePercent'] == pytest.approx(100)
    assert c['dosePercent'] == pytest.approx(100)
    assert 'genel halk' in a['note'].lower()


def test_rta_peak_helper_only_suggests_cuts_and_never_boosts():
    centers = [50 * (2 ** (i/3)) for i in range(15)]
    values = [-50.0] * 15
    values[7] = -38.0
    result = run_js(f'm.recommendCuts({json.dumps(centers)},{json.dumps(values)},6)')
    assert result
    assert all(x['suggestedCutDb'] < 0 for x in result)
    assert all(abs(x['suggestedCutDb']) <= 3 for x in result)
    assert all('uygulanmaz' in x['action'].lower() for x in result)


@pytest.mark.parametrize('expression', [
    'm.pressureToSpl(0)',
    'm.distanceSpl(100,0,10,1)',
    'm.distanceSpl(100,1,10,1.5)',
    'm.areaPlan(20,30,6,180)',
    'm.wavelength(0)',
    'm.axialModes(-1,4,2.5)',
    'm.nioshExposure(200,480)',
    'm.recommendCuts([100,200],[1],6)',
])
def test_invalid_acoustic_inputs_are_rejected(expression):
    module = (ROOT / 'ui' / 'acoustic_math.js').as_posix()
    code = f"const m=require({json.dumps(module)}); try{{ {expression}; process.exit(7); }}catch(e){{ console.log('rejected'); }}"
    result = subprocess.run([NODE, '-e', code], cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
    assert result.returncode == 0 and 'rejected' in result.stdout


def test_sabine_rt60_reference_example_and_limits():
    result = run_js('m.sabineRt60(360,20)')
    assert result['rt60Seconds'] == pytest.approx(2.898)
    assert 'difüz alan' in result['note'].lower()
    module = (ROOT / 'ui' / 'acoustic_math.js').as_posix()
    code = f"const m=require({json.dumps(module)}); try{{m.sabineRt60(100,0);process.exit(7)}}catch(e){{console.log('rejected')}}"
    run = subprocess.run([NODE, '-e', code], cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
    assert run.returncode == 0 and 'rejected' in run.stdout


def test_standard_nominal_band_edges_use_base_ten_ratio():
    module = (ROOT / 'ui' / 'rta_math.js').as_posix()
    code = f"const m=require({json.dumps(module)}); console.log(JSON.stringify([m.ratio('third'),m.ratio('octave')]));"
    result = subprocess.run([NODE, '-e', code], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', check=True)
    third, octave = json.loads(result.stdout)
    assert third == pytest.approx(10 ** (1/20))
    assert octave == pytest.approx(10 ** (3/20))


def test_niosh_multiple_exposure_blocks_are_added_by_dose_not_averaged_db():
    result = run_js('m.nioshDose([{levelDba:85,durationMinutes:240},{levelDba:88,durationMinutes:120}])')
    assert result['totalDurationMinutes'] == pytest.approx(360)
    assert result['dosePercent'] == pytest.approx(100)
    assert result['referenceDoseReached'] is True
    assert len(result['segments']) == 2
    assert result['segments'][0]['dosePercent'] == pytest.approx(50)
    assert result['segments'][1]['dosePercent'] == pytest.approx(50)


def test_niosh_dose_rejects_empty_or_invalid_blocks():
    module = (ROOT / 'ui' / 'acoustic_math.js').as_posix()
    for expression in ("m.nioshDose([])", "m.nioshDose([{levelDba:85,durationMinutes:0}])", "m.nioshDose([{levelDba:141,durationMinutes:5}])"):
        code = f"const m=require({json.dumps(module)}); try{{ {expression}; process.exit(7); }}catch(e){{ console.log('rejected'); }}"
        result = subprocess.run([NODE, '-e', code], cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
        assert result.returncode == 0 and 'rejected' in result.stdout
