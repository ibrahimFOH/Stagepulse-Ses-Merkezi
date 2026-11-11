import math
import wave
from pathlib import Path

import numpy as np
import soundfile as sf

from core.audio_tools import analyze_wav, normalize_lufs


def make_pcm16(path: Path, amplitude: float = 0.2, seconds: float = 2.0, rate: int = 48000):
    t = np.arange(int(seconds * rate), dtype=np.float64) / rate
    samples = np.round(np.sin(2 * np.pi * 1000 * t) * amplitude * 32767).astype('<i2')
    with wave.open(str(path), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(samples.tobytes())
    return samples


def test_analyze_wav_reports_pcm_scope_and_metrics(tmp_path):
    path = tmp_path / 'tone.wav'
    samples = make_pcm16(path, amplitude=0.5, seconds=1)
    report = analyze_wav(path)
    assert report['channels'] == 1
    assert len(report['channel_analysis']) == 1
    assert report['channel_analysis'][0]['channel'] == 1
    assert report['channel_analysis'][0]['sample_peak_dbfs'] == report['sample_peak_dbfs']
    assert report['sample_rate_hz'] == 48000
    assert report['bits_per_sample'] == 16
    assert report['frames'] == 48000
    assert 0.99 < report['duration_seconds'] < 1.01
    assert -7.0 < report['sample_peak_dbfs'] < -5.5
    assert -12.0 < report['rms_dbfs'] < -8.0
    assert 'dB SPL' in report['scope_note']
    assert len(samples) == report['frames']


def test_normalize_writes_new_pcm24_file_and_does_not_touch_source(tmp_path):
    source = tmp_path / 'source.wav'
    output = tmp_path / 'out' / 'normalized.wav'
    make_pcm16(source, amplitude=0.2, seconds=3)
    before = source.read_bytes()
    report = normalize_lufs(source, output, -14.0, -1.0)
    assert output.is_file()
    assert source.read_bytes() == before
    info = sf.info(str(output))
    assert info.subtype == 'PCM_24'
    assert info.samplerate == 48000 and info.channels == 1
    assert math.isfinite(report['input_lufs_i'])
    assert math.isfinite(report['achieved_lufs_i_estimate'])
    assert report['target_true_peak_dbtp'] == -1.0
    assert report['output'].endswith('normalized.wav')


def test_loud_material_is_limited_by_peak_not_clipped_to_target(tmp_path):
    source, output = tmp_path / 'loud.wav', tmp_path / 'safe.wav'
    samples = make_pcm16(source, amplitude=0.01, seconds=3)
    # Seyrek yüksek tepe, düşük entegre loudness: loudness hedefi piki aşmadan karşılanamaz.
    samples[24001] = 31000
    with wave.open(str(source), 'wb') as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(48000); wf.writeframes(samples.tobytes())
    report = normalize_lufs(source, output, -14.0, -1.0)
    assert report['target_lufs_limited_by_peak'] is True
    assert report['applied_gain_db'] < 0
    assert report['output_sample_peak_dbfs'] <= -0.85


def test_invalid_target_rejected(tmp_path):
    source = tmp_path / 'tone.wav'
    make_pcm16(source)
    try:
        normalize_lufs(source, tmp_path / 'bad.wav', 1, -1)
    except ValueError as exc:
        assert 'Hedef LUFS' in str(exc)
    else:
        raise AssertionError('Geçersiz LUFS hedefi reddedilmedi.')


def test_source_and_destination_must_differ(tmp_path):
    source = tmp_path / 'tone.wav'
    make_pcm16(source)
    try:
        normalize_lufs(source, source)
    except ValueError as exc:
        assert 'aynı dosya' in str(exc)
    else:
        raise AssertionError('Kaynak dosyanın üzerine yazmaya izin verildi.')


def test_analyze_wav_reports_independent_stereo_channel_metrics(tmp_path):
    path = tmp_path / "stereo.wav"
    rate = 48000
    t = np.arange(rate, dtype=np.float64) / rate
    left = np.round(np.sin(2 * np.pi * 1000 * t) * 0.5 * 32767).astype("<i2")
    right = np.round(np.sin(2 * np.pi * 500 * t) * 0.1 * 32767 + 0.05 * 32767).astype("<i2")
    interleaved = np.column_stack((left, right)).astype("<i2")
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(interleaved.tobytes())
    report = analyze_wav(path)
    assert len(report["channel_analysis"]) == 2
    left_report, right_report = report["channel_analysis"]
    assert left_report["channel"] == 1 and right_report["channel"] == 2
    assert left_report["sample_peak_dbfs"] > right_report["sample_peak_dbfs"]
    assert abs(right_report["dc_offset_percent"] - 5.0) < 0.1
    assert report["sample_values"] == rate * 2



def test_normalizer_reports_de_man_lra_metrics(tmp_path):
    source = tmp_path / "program.wav"
    output = tmp_path / "program_out.wav"
    make_pcm16(source, amplitude=0.15, seconds=5)
    report = normalize_lufs(source, output, -23.0, -1.0)
    assert report["input_lra_lu"] is not None
    assert math.isfinite(report["input_lra_lu"])
    assert report["output_lra_lu"] is not None
    assert math.isfinite(report["output_lra_lu"])
    assert report["output_true_peak_dbtp_verified"] <= -0.85


def test_itu_true_peak_uses_published_bs1770_fir_at_48khz():
    from core.audio_tools import _true_peak_linear

    rate = 48000
    t = np.arange(rate, dtype=np.float64) / rate
    signal = 0.5 * np.sin(2 * np.pi * 1000 * t)
    peak, method = _true_peak_linear(signal, rate)
    assert 0.47 <= peak <= 0.52
    assert "48-tap FIR" in method


def test_ebu_test_set_never_marks_files_pass_without_reference_csv(tmp_path):
    from core.audio_tools import validate_ebu_test_set

    rate = 48000
    t = np.arange(rate, dtype=np.float64) / rate
    path = tmp_path / "EBU_Test_01.wav"
    sf.write(path, 0.2 * np.sin(2 * np.pi * 1000 * t), rate, subtype="PCM_24")
    report = validate_ebu_test_set(tmp_path)
    assert report["files_total"] == 1
    assert report["counts"]["REFERENCE_REQUIRED"] == 1
    assert report["results"][0]["status"] == "REFERENCE_REQUIRED"
    assert report["results"][0]["momentary_max_lufs"] is not None
    assert report["results"][0]["short_term_max_lufs"] is None


def test_ebu_reference_pass_is_limited_to_declared_metrics(tmp_path):
    from core.audio_tools import validate_ebu_test_set

    rate = 48000
    t = np.arange(rate, dtype=np.float64) / rate
    path = tmp_path / "EBU_Reference_Test.wav"
    sf.write(path, 0.2 * np.sin(2 * np.pi * 1000 * t), rate, subtype="PCM_24")
    measured = validate_ebu_test_set(tmp_path)
    integrated = measured["results"][0]["integrated_lufs"]
    reference = "filename,integrated_lufs\\nEBU_Reference_Test.wav," + str(integrated) + "\\n"
    report = validate_ebu_test_set(tmp_path, reference)
    result = report["results"][0]
    assert report["counts"]["PASS"] == 1
    assert result["status"] == "PASS"
    assert result["reference_metrics"] == ["integrated_lufs"]
    assert "yalnızca CSV'de" in report["scope_note"]


def test_ebu_true_peak_uses_asymmetric_tech3341_tolerance(tmp_path):
    from core.audio_tools import validate_ebu_test_set

    rate = 48000
    t = np.arange(rate, dtype=np.float64) / rate
    path = tmp_path / "EBU_TP_Test.wav"
    sf.write(path, 0.2 * np.sin(2 * np.pi * 1000 * t), rate, subtype="PCM_24")
    measured = validate_ebu_test_set(tmp_path)
    peak = measured["results"][0]["true_peak_dbtp"]
    reference = (
        "filename,true_peak_dbtp,true_peak_tolerance_high_db,true_peak_tolerance_low_db\\n"
        f"{path.name},{peak - 0.35},0.2,0.4\\n"
    )
    report = validate_ebu_test_set(tmp_path, reference)
    assert report["counts"]["FAIL"] == 1
    comparison = report["results"][0]["comparisons"][0]
    assert comparison["tolerance_high_db"] == 0.2
    assert comparison["tolerance_low_db"] == 0.4


def test_ebu_reference_csv_can_produce_pass_only_when_all_available_metrics_match(tmp_path):
    from core.audio_tools import validate_ebu_test_set

    rate = 48000
    t = np.arange(rate * 5, dtype=np.float64) / rate
    path = tmp_path / "EBU_Full_Reference.wav"
    sf.write(path, 0.18 * np.sin(2 * np.pi * 997 * t), rate, subtype="PCM_24")
    measured = validate_ebu_test_set(tmp_path)
    row = measured["results"][0]
    reference = (
        "filename,integrated_lufs,lra_lu,momentary_max_lufs,short_term_max_lufs,true_peak_dbtp\n"
        + path.name + ","
        + ",".join(str(row[key]) for key in (
            "integrated_lufs", "lra_lu", "momentary_max_lufs",
            "short_term_max_lufs", "true_peak_dbtp"
        ))
        + "\n"
    )
    result = validate_ebu_test_set(tmp_path, reference, tolerance_lu=0.01)
    assert result["counts"]["PASS"] == 1
    assert result["results"][0]["status"] == "PASS"
    assert len(result["results"][0]["comparisons"]) == 5
