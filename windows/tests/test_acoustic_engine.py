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
