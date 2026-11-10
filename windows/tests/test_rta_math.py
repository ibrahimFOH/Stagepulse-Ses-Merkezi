from __future__ import annotations
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which('node')
pytestmark = pytest.mark.skipif(NODE is None, reason='RTA JavaScript birim testleri için Node.js gerekir; EXE çalışma zamanı gereksinimi değildir.')


def run_js(expression: str):
    module = (ROOT / 'ui' / 'rta_math.js').as_posix()
    code = f"const m=require({json.dumps(module)}); const result=({expression}); console.log(JSON.stringify(result));"
    result = subprocess.run([NODE, '-e', code], cwd=ROOT, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def test_44100_hz_excludes_incomplete_20khz_third_octave_band():
    centers = run_js("m.supportedCenters(44100, 'third', 20, 20000)")
    assert centers[-1] == 16000
    assert 20000 not in centers


def test_48000_hz_can_include_full_20khz_third_octave_band():
    centers = run_js("m.supportedCenters(48000, 'third', 20, 20000)")
    assert centers[-1] == 20000


def test_octave_and_third_octave_are_distinct_center_sets():
    value = run_js("({third:m.supportedCenters(48000,'third',20,20000),octave:m.supportedCenters(48000,'octave',20,20000)})")
    assert len(value['third']) > len(value['octave']) * 2
    assert value['third'][-1] == 20000
    assert value['octave'][-1] == 16000


def test_smoothing_time_constant_responds_monotonically():
    values = run_js("({fast:m.smooth([0],[10],0.5,0.12)[0],slow:m.smooth([0],[10],0.5,1.5)[0]})")
    assert values['fast'] > values['slow'] > 0


def test_selected_frequency_range_is_clamped_to_highest_complete_band():
    assert run_js("m.clampRangeToSupported(44100,'third',20,20000)") == [20,16000]
    assert run_js("m.clampRangeToSupported(48000,'third',20,20000)") == [20,20000]
    assert run_js("m.clampRangeToSupported(16000,'third',125,8000)") == [125,6300]


def test_clamped_range_uses_separate_octave_resolution():
    assert run_js("m.clampRangeToSupported(16000,'octave',20,20000)") == [20,4000]


def test_python_and_javascript_supported_bands_match():
    from core.rta_capture import supported_centers as py_supported
    for sr in (16000, 22050, 32000, 44100, 48000, 96000):
        for mode in ('third', 'octave'):
            js = run_js(f"m.supportedCenters({sr}, {json.dumps(mode)}, 20, 20000)")
            assert js == py_supported(sr, mode, 20, 20000)

def test_fractional_octave_centers_support_1_over_6_to_1_over_48():
    for bands in (6, 12, 24, 48):
        centers = run_js(f"m.fractionalCenters(48000, {bands}, 20, 20000)")
        assert 1000 in centers
        assert centers == sorted(centers)
        assert len(centers) > len(run_js("m.fractionalCenters(48000, 3, 20, 20000)"))


def test_fractional_octave_centers_respect_nyquist_and_range():
    centers = run_js("m.fractionalCenters(44100, 48, 100, 20000)")
    assert all(100 <= value <= 20000 for value in centers)
    assert all(value * (2 ** (1 / 96)) <= 44100 / 2 * 0.999 for value in centers)


def test_fractional_octave_centers_reject_unsupported_resolution():
    with pytest.raises(subprocess.CalledProcessError):
        run_js("m.fractionalCenters(48000, 5, 20, 20000)")

def test_live_rta_math_supports_all_fractional_octave_resolutions():
    for bands in (1, 3, 6, 12, 24, 48):
        centers = run_js(f"m.supportedCenters(48000, {json.dumps(str(bands))}, 20, 20000)")
        assert centers == sorted(centers)
        assert 1000 in centers
    assert len(run_js("m.centers('6')")) > len(run_js("m.centers('3')"))
    assert len(run_js("m.centers('12')")) > len(run_js("m.centers('6')"))
