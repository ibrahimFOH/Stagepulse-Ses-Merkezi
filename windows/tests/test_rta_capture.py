from __future__ import annotations
import numpy as np
import pytest
from core.rta_capture import (
    SUPPORTED_FFT_SIZES, aggregate_band_db, spectrum_power_db, supported_centers,
)


def sine(freq: float, sample_rate: int, size: int, amplitude: float = 0.5) -> np.ndarray:
    t = np.arange(size, dtype=np.float64) / sample_rate
    return amplitude * np.sin(2 * np.pi * freq * t)


def test_supported_bands_obey_nyquist_upper_band_edge():
    assert supported_centers(44100, 'third', 20, 20000)[-1] == 16000
    assert 20000 not in supported_centers(44100, 'third', 20, 20000)
    assert supported_centers(48000, 'third', 20, 20000)[-1] == 20000
    assert supported_centers(16000, 'octave', 20, 20000)[-1] == 4000

@pytest.mark.parametrize("bands", [1, 3, 6, 12, 24, 48])
def test_fractional_octave_live_centers_are_ordered_and_respect_nyquist(bands):
    centers = supported_centers(48000, str(bands), 20, 20000)
    assert centers == sorted(centers)
    assert 1000.0 in centers
    ratio = 10 ** (3 / 20) if bands == 1 else 10 ** (1 / 20) if bands == 3 else 2 ** (1 / (2 * bands))
    assert all(center * ratio <= 24000 * 0.999 for center in centers)


def test_fractional_octave_live_bands_resolve_more_detail_than_third_octave():
    third = supported_centers(48000, "3", 20, 20000)
    sixth = supported_centers(48000, "6", 20, 20000)
    twelfth = supported_centers(48000, "12", 20, 20000)
    assert len(sixth) > len(third)
    assert len(twelfth) > len(sixth)

@pytest.mark.parametrize("bands", ["1", "3", "6", "12", "24", "48"])
def test_live_fractional_band_aggregator_returns_valid_power(bands):
    sr, size = 48000, 32768
    frequencies, spectrum_db = spectrum_power_db(sine(1000, sr, size), sr)
    level = aggregate_band_db(frequencies, spectrum_db, sr, 1000, bands)
    assert -20 < level < 0


def test_invalid_live_fractional_octave_resolution_is_rejected():
    with pytest.raises(ValueError, match="Bant çözünürlüğü"):
        supported_centers(48000, "5", 20, 20000)


@pytest.mark.parametrize('fft_size', SUPPORTED_FFT_SIZES)
def test_low_frequency_band_uses_fractional_edge_bins_instead_of_becoming_empty(fft_size):
    sr = 48000
    freq = 20.0
    frequencies, spectrum_db = spectrum_power_db(sine(freq, sr, fft_size), sr)
    level = aggregate_band_db(frequencies, spectrum_db, sr, 20, 'third')
    assert level > -30, (fft_size, level)
    assert level < -3


def test_high_tone_is_in_expected_treble_band_and_44k_does_not_fake_20k_support():
    sr, size = 48000, 32768
    frequencies, spectrum_db = spectrum_power_db(sine(18000, sr, size), sr)
    level_20k = aggregate_band_db(frequencies, spectrum_db, sr, 20000, 'third')
    level_16k = aggregate_band_db(frequencies, spectrum_db, sr, 16000, 'third')
    assert level_20k > level_16k + 15
    assert aggregate_band_db(frequencies, spectrum_db, 44100, 20000, 'third') == -120


def test_band_power_is_near_expected_rms_for_bin_centred_sine():
    sr, size, freq, amplitude = 48000, 16384, 1000, 0.5
    frequencies, spectrum_db = spectrum_power_db(sine(freq, sr, size, amplitude), sr)
    value = aggregate_band_db(frequencies, spectrum_db, sr, 1000, 'third')
    expected_rms_dbfs = 20 * np.log10(amplitude / np.sqrt(2))
    assert value == pytest.approx(expected_rms_dbfs, abs=1.5)


def test_spectrum_rejects_invalid_fft_size():
    with pytest.raises(ValueError, match='FFT boyutu'):
        spectrum_power_db(np.zeros(1024), 48000)


def test_native_device_listing_filters_to_inputs_and_marks_default(monkeypatch):
    import sys
    from types import SimpleNamespace
    from core.rta_capture import list_input_devices

    devices = [
        {'name': 'Dahili Mikrofon', 'max_input_channels': 1, 'max_output_channels': 0,
         'default_samplerate': 44100.0, 'hostapi': 0},
        {'name': 'Hoparlör', 'max_input_channels': 0, 'max_output_channels': 2,
         'default_samplerate': 48000.0, 'hostapi': 0},
    ]
    fake = SimpleNamespace(query_devices=lambda: devices,
                           query_hostapis=lambda: ({'name': 'Windows WASAPI'},),
                           default=SimpleNamespace(device=(0, 1)))
    monkeypatch.setitem(sys.modules, 'sounddevice', fake)
    got = list_input_devices()
    assert len(got) == 1
    assert got[0]['name'] == 'Dahili Mikrofon'
    assert got[0]['is_default'] is True
    assert got[0]['default_sample_rate'] == 44100


def test_native_capture_prefers_48khz_when_the_device_supports_it(monkeypatch):
    import sys
    from types import SimpleNamespace
    from core.rta_capture import RTACapture

    devices = [{'name': 'PC Mikrofonu', 'max_input_channels': 1, 'max_output_channels': 0,
                'default_samplerate': 44100.0, 'hostapi': 0}]
    class FakeStream:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
        def start(self):
            pass
        def stop(self):
            pass
        def close(self):
            pass
    class FakeSoundDevice:
        default = SimpleNamespace(device=(0, -1))
        InputStream = FakeStream
        @staticmethod
        def query_devices(device=None, kind=None):
            if kind == 'input': return devices[0]
            if device is None: return devices
            return devices[device]
        @staticmethod
        def query_hostapis(): return ({'name': 'Windows WASAPI'},)
        @staticmethod
        def check_input_settings(device=None, channels=None, samplerate=None, dtype=None):
            if samplerate not in (44100, 48000): raise ValueError('unsupported sample rate')
    monkeypatch.setitem(sys.modules, 'sounddevice', FakeSoundDevice)
    capture = RTACapture()
    result = capture.start(None, 8192)
    assert result['sample_rate'] == 48000
    assert result['device'] == 'PC Mikrofonu'
    capture.stop()


def test_snapshot_reports_if_driver_opens_but_no_microphone_frames_arrive(monkeypatch):
    import sys
    from types import SimpleNamespace
    from core.rta_capture import RTACapture

    devices = [{'name': 'Sessiz/erişimsiz mikrofon', 'max_input_channels': 1, 'max_output_channels': 0,
                'default_samplerate': 48000.0, 'hostapi': 0}]
    class FakeStream:
        def __init__(self, **kwargs): pass
        def start(self): pass
        def stop(self): pass
        def close(self): pass
    class FakeSoundDevice:
        default = SimpleNamespace(device=(0, -1))
        InputStream = FakeStream
        @staticmethod
        def query_devices(device=None, kind=None):
            if kind == 'input': return devices[0]
            if device is None: return devices
            return devices[device]
        @staticmethod
        def query_hostapis(): return ({'name': 'Windows WASAPI'},)
        @staticmethod
        def check_input_settings(device=None, channels=None, samplerate=None, dtype=None):
            if samplerate != 48000: raise ValueError('unsupported')
    monkeypatch.setitem(sys.modules, 'sounddevice', FakeSoundDevice)
    capture = RTACapture()
    capture.start(None, 8192)
    snapshot = capture.snapshot('third', 20, 20000)
    assert snapshot['samples_received'] == 0
    assert snapshot['seconds_since_last_callback'] >= 0
    capture.stop()


def test_audio_callback_updates_input_meter_and_sample_watchdog():
    from core.rta_capture import RTACapture
    capture = RTACapture()
    capture._running = True
    capture._started_monotonic = __import__('time').monotonic()
    samples = sine(1000, 48000, 480, amplitude=0.25).astype(np.float32).reshape(-1, 1)
    capture._audio_callback(samples, len(samples), None, None)
    assert capture._samples_received == len(samples)
    assert capture._peak_dbfs == pytest.approx(20 * np.log10(0.25), abs=0.2)
    assert capture._rms_dbfs == pytest.approx(20 * np.log10(0.25 / np.sqrt(2)), abs=0.3)
    assert capture._last_callback_monotonic > 0


def test_rta_snapshot_marks_stopped_stream_stale_instead_of_live():
    import time
    from core.rta_capture import RTACapture

    capture = RTACapture()
    capture._running = True
    capture._sample_rate = 48000
    capture._fft_size = 8192
    capture._device_name = "Test giriş"
    capture._started_monotonic = time.monotonic() - 5
    capture._last_callback_monotonic = time.monotonic() - 3
    capture._frequencies = np.fft.rfftfreq(8192, 1 / 48000)
    capture._power_db = np.full(4097, -60.0)

    result = capture.snapshot()
    assert result["stream_stale"] is True
    assert result["stream_healthy"] is False
    assert result["ready"] is False
    assert result["seconds_since_last_callback"] >= 3


def test_live_tf_snapshot_marks_stopped_stream_stale():
    import time
    from core.tf_capture import TFCapture

    capture = TFCapture()
    capture._running = True
    capture._sample_rate = 48000
    capture._fft_size = 8192
    capture._num_avg = 4
    capture._device_name = "Test stereo giriş"
    capture._started = time.monotonic() - 5
    capture._last_callback = time.monotonic() - 3
    bins = 8192 // 2 + 1
    capture._sxx = np.ones(bins, dtype=np.float64)
    capture._syy = np.ones(bins, dtype=np.float64)
    capture._syx = np.ones(bins, dtype=np.complex128)
    capture._avg_count = 4

    result = capture.snapshot()
    assert result["stream_stale"] is True
    assert result["stream_healthy"] is False
    assert result["ready"] is False
    assert result["averages_target"] == 4


def test_spl_calibration_uses_reference_calibrator_and_reports_z_weighted_level():
    import time
    from core.rta_capture import RTACapture

    capture = RTACapture()
    capture._running = True
    capture._started_monotonic = time.monotonic() - 1
    capture._last_callback_monotonic = time.monotonic()
    capture._samples_received = 4096
    capture._rms_dbfs = -20.0

    calibrated = capture.calibrate_spl(94.0)
    assert calibrated["ok"] is True
    assert calibrated["offset_db"] == pytest.approx(114.0)
    result = capture.snapshot()
    assert result["calibrated_spl"] is True
    assert result["spl_db"] == pytest.approx(94.0)
    assert result["spl_weighting"] == "Z/unweighted"


def test_spl_calibration_rejects_stale_or_missing_microphone_signal():
    import time
    from core.rta_capture import RTACapture

    capture = RTACapture()
    capture._running = True
    capture._started_monotonic = time.monotonic() - 5
    capture._last_callback_monotonic = time.monotonic() - 4
    capture._samples_received = 4096
    capture._rms_dbfs = -20.0
    with pytest.raises(RuntimeError, match="Kararlı mikrofon verisi"):
        capture.calibrate_spl(94.0)


def test_snapshot_includes_weighted_spl_metrics_when_fft_window_is_ready():
    import time
    from core.rta_capture import RTACapture
    capture = RTACapture()
    capture._running = True
    capture._sample_rate = 48000
    capture._fft_size = 16384
    capture._device_name = "Test giriş"
    capture._started_monotonic = time.monotonic()
    capture._last_callback_monotonic = time.monotonic()
    capture._buffer = sine(1000, 48000, 16384, amplitude=0.1).astype(np.float32)
    capture._filled = 16384
    capture._write_pos = 0
    capture._frequencies = np.fft.rfftfreq(16384, 1 / 48000)
    capture._power_db = np.full(8193, -60.0)
    result = capture.snapshot()
    assert result["spl_measurement"]["ok"] is True
    assert set(result["spl_measurement"]["weightings"]) == {"A", "C", "Z"}
    assert result["spl_measurement"]["window_seconds"] == pytest.approx(16384 / 48000)
    assert result["spl_measurement"]["calibrated_spl"] is False


def test_spl_filter_self_test_matches_iec_nominal_a_c_z_curves():
    from core.acoustic_engine import run_spl_filter_self_test

    report = run_spl_filter_self_test()
    assert report["tests_total"] == 33
    assert report["tests_failed"] == 0, report["results"]
    assert report["tests_passed"] == 33
