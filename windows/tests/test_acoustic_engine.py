from __future__ import annotations

import numpy as np
import pytest

from core.acoustic_engine import transfer_function, delay_finder, impulse_response


def tone(freq, rate, size, amplitude=0.4):
    t = np.arange(size, dtype=np.float64) / rate
    return amplitude * np.sin(2 * np.pi * freq * t)


def test_transfer_function_unity_gain_and_high_coherence():
    rate, size = 48000, 32768
    x = tone(1000, rate, size)
    result = transfer_function(x, x, rate, segment_size=4096)
    idx = int(np.argmin(np.abs(np.asarray(result["frequency_hz"]) - 1000)))
    assert result["magnitude_db"][idx] == pytest.approx(0.0, abs=0.2)
    assert result["coherence"][idx] > 0.999


def test_transfer_function_gain_and_phase_for_delayed_signal():
    rate, size, delay = 48000, 32768, 48
    x = tone(1000, rate, size)
    y = np.concatenate([np.zeros(delay), x[:-delay]]) * 0.5
    result = transfer_function(x, y, rate, segment_size=4096)
    idx = int(np.argmin(np.abs(np.asarray(result["frequency_hz"]) - 1000)))
    assert result["magnitude_db"][idx] == pytest.approx(-6.0206, abs=0.5)
    assert result["coherence"][idx] > 0.98


def test_delay_finder_positive_delay():
    rate, size, delay = 48000, 12000, 137
    rng = np.random.default_rng(7)
    x = rng.normal(0, 0.2, size)
    y = np.concatenate([np.zeros(delay), x[:-delay]])
    result = delay_finder(x, y, rate)
    assert result["delay_samples"] == pytest.approx(delay, abs=0.1)
    assert result["delay_ms"] == pytest.approx(delay * 1000 / rate, abs=0.003)


def test_delay_finder_detects_polarity_inversion():
    rate, size = 48000, 4096
    rng = np.random.default_rng(11)
    x = rng.normal(0, 0.2, size)
    result = delay_finder(x, -x, rate)
    assert result["delay_samples"] == pytest.approx(0, abs=0.1)
    assert result["polarity_inverted"] is True


def test_delay_finder_rejects_silence():
    with pytest.raises(ValueError, match="Sessiz"):
        delay_finder(np.zeros(1024), np.zeros(1024), 48000)


def test_transfer_function_rejects_mismatched_channels():
    with pytest.raises(ValueError, match="örnek sayısı"):
        transfer_function(np.zeros(2048), np.zeros(1024), 48000, 256)


def test_impulse_response_has_expected_length_and_finite_values():
    rate, size = 48000, 16384
    rng = np.random.default_rng(13)
    x = rng.normal(0, 0.2, size)
    y = np.concatenate([np.zeros(32), x[:-32]])
    result = impulse_response(x, y, rate, segment_size=2048)
    assert len(result["impulse_response"]) == 2048
    assert np.all(np.isfinite(result["etc_db"]))


def test_stereo_wav_api_reads_local_file_and_returns_analysis(tmp_path):
    import soundfile as sf
    from core.acoustic_api import AcousticAnalysisApi

    rate, size = 48000, 8192
    reference = tone(1000, rate, size)
    measurement = reference * 0.5
    path = tmp_path / "stereo_test.wav"
    sf.write(path, np.column_stack((reference, measurement)), rate, subtype="FLOAT")

    api = AcousticAnalysisApi()
    api._selected_wav_path = str(path)
    result = api.analyze_stereo_wav(str(path), 2048, 0.5)
    assert result["ok"] is True
    assert result["channels"] == 2
    assert result["sample_rate"] == rate
    assert result["file_name"] == path.name
    assert result["calibrated_spl"] is False
    assert len(result["transfer_function"]["frequency_hz"]) == 1025
    assert len(result["impulse_response"]["impulse_response"]) == 2048


def test_stereo_wav_api_rejects_mono_file(tmp_path):
    import soundfile as sf
    from core.acoustic_api import AcousticAnalysisApi

    path = tmp_path / "mono.wav"
    sf.write(path, np.zeros(4096), 48000)
    api = AcousticAnalysisApi()
    api._selected_wav_path = str(path)
    with pytest.raises(ValueError, match="Stereo WAV"):
        api.analyze_stereo_wav(str(path), 2048, 0.5)

@pytest.mark.parametrize("bands", [1, 3, 6, 12, 24, 48])
def test_fractional_octave_spectrum_includes_reference_tone_and_reports_dBFS(bands):
    from core.acoustic_engine import fractional_octave_spectrum
    rate, size = 48000, 16384
    result = fractional_octave_spectrum(tone(1000, rate, size, 0.5), rate, bands, size)
    index = int(np.argmin(np.abs(np.asarray(result["centers_hz"]) - 1000.0)))
    assert result["centers_hz"][index] == pytest.approx(1000.0)
    assert result["levels_dbfs"][index] == pytest.approx(-9.0309, abs=1.0)
    assert result["units"] == "dBFS RMS"
    assert result["standard_compliance"] is False


def test_fractional_octave_resolution_increases_band_count():
    from core.acoustic_engine import fractional_octave_spectrum
    x = tone(1000, 48000, 32768)
    counts = [len(fractional_octave_spectrum(x, 48000, bands, 32768)["centers_hz"])
              for bands in (3, 6, 12, 24, 48)]
    assert counts == sorted(counts)
    assert counts[-1] > counts[0] * 10


def test_fractional_octave_rejects_unsupported_resolution_and_fft():
    from core.acoustic_engine import fractional_octave_spectrum
    x = tone(1000, 48000, 8192)
    with pytest.raises(ValueError, match="Bant çözünürlüğü"):
        fractional_octave_spectrum(x, 48000, 5)
    with pytest.raises(ValueError, match="FFT boyutu"):
        fractional_octave_spectrum(x, 48000, 3, 3000)


def test_spl_metrics_are_explicitly_uncalibrated_without_reference_offset():
    from core.acoustic_engine import measure_spl
    rate, size = 48000, 96000
    result = measure_spl(tone(1000, rate, size, 0.1), rate)
    assert result["calibrated_spl"] is False
    assert result["units"] == "dBFS"
    assert result["weightings"]["Z"]["leq_db"] == pytest.approx(-23.0103, abs=0.2)
    assert result["weightings"]["A"]["leq_db"] == pytest.approx(result["weightings"]["Z"]["leq_db"], abs=0.5)
    assert result["weightings"]["C"]["leq_db"] == pytest.approx(result["weightings"]["Z"]["leq_db"], abs=0.5)


def test_spl_metrics_apply_calibration_offset_and_return_fast_slow_peak_percentiles():
    from core.acoustic_engine import measure_spl
    rate, size = 48000, 96000
    result = measure_spl(tone(1000, rate, size, 0.1), rate, calibration_offset_db=114.0)
    assert result["calibrated_spl"] is True
    assert result["units"] == "dB SPL"
    assert result["weightings"]["Z"]["leq_db"] == pytest.approx(90.9897, abs=0.2)
    assert result["weightings"]["A"]["lmax_fast_db"] > 80
    assert result["weightings"]["A"]["lmax_slow_db"] > 80
    assert set(result["weightings"]["A"]["percentiles_1s_db"]) == {"L10", "L50", "L90"}


def test_a_weighting_attenuates_100hz_more_than_c_weighting():
    from core.acoustic_engine import measure_spl
    rate, size = 48000, 96000
    result = measure_spl(tone(100, rate, size, 0.1), rate, calibration_offset_db=114.0)
    assert result["weightings"]["C"]["leq_db"] - result["weightings"]["A"]["leq_db"] > 15.0


def test_spl_metrics_reject_non_finite_calibration_offset():
    from core.acoustic_engine import measure_spl
    with pytest.raises(ValueError, match="Kalibrasyon"):
        measure_spl(tone(1000, 48000, 8192), 48000, float("nan"))


def test_acoustic_api_exposes_fractional_rta_and_spl_analysis():
    import json
    from core.acoustic_api import AcousticAnalysisApi
    api = AcousticAnalysisApi()
    x = tone(1000, 48000, 8192).tolist()
    rta = api.analyze_rta_samples_json(json.dumps(x), 48000, 12, 8192)
    spl = api.analyze_spl_samples_json(json.dumps(x), 48000)
    assert rta["bands_per_octave"] == 12
    assert spl["calibrated_spl"] is False
    assert spl["units"] == "dBFS"
