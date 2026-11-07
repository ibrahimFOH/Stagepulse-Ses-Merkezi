# -*- coding: utf-8 -*-
"""Native microphone capture and relative FFT-band analysis for Stagepulse.

The reported levels are digital full-scale RMS band powers, not calibrated dB SPL.
Band aggregation overlaps FFT bins fractionally so narrow low-frequency bands do not
silently become empty when the FFT bin spacing is wider than the nominal band.
"""
from __future__ import annotations

import math
import threading
import time
from typing import Any

import numpy as np

THIRD_CENTERS = (20, 25, 31.5, 40, 50, 63, 80, 100, 125, 160, 200, 250,
                 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500,
                 3150, 4000, 5000, 6300, 8000, 10000, 12500, 16000, 20000)
OCTAVE_CENTERS = (31.5, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000)
SUPPORTED_FFT_SIZES = (8192, 16384, 32768)
FLOOR_POWER = 1e-30  # Numerical floor; displayed band level is clamped to -120 dBFS


def band_ratio(mode: str) -> float:
    if mode == "third":
        return 10 ** (1 / 20)
    if mode == "octave":
        return 10 ** (3 / 20)
    raise ValueError("Bant modu 'third' veya 'octave' olmalı.")


def supported_centers(sample_rate: float, mode: str, min_hz: float = 20,
                      max_hz: float = 20000) -> list[float]:
    """Return nominal band centers whose complete upper edge fits below Nyquist."""
    if not math.isfinite(float(sample_rate)) or float(sample_rate) <= 0:
        return []
    ratio = band_ratio(mode)
    nyquist = float(sample_rate) / 2
    centers = THIRD_CENTERS if mode == "third" else OCTAVE_CENTERS
    return [float(f) for f in centers
            if float(min_hz) <= f <= float(max_hz) and f * ratio <= nyquist * 0.999]


def spectrum_power_db(samples: np.ndarray, sample_rate: float) -> tuple[np.ndarray, np.ndarray]:
    """Compute one-sided integrated power per FFT bin, expressed as dBFS RMS.

    A Hann window is power-normalized using Parseval's relation. Power, rather than
    magnitude, is summed into each band. A full-scale peak sine therefore reads near
    -3 dBFS RMS across its containing band, as expected.
    """
    x = np.asarray(samples, dtype=np.float64).reshape(-1)
    n = x.size
    if n not in SUPPORTED_FFT_SIZES:
        raise ValueError(f"FFT boyutu desteklenmiyor: {n}")
    if not math.isfinite(float(sample_rate)) or sample_rate <= 0:
        raise ValueError("Örnekleme frekansı pozitif olmalı.")
    if not np.all(np.isfinite(x)):
        x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
    window = np.hanning(n)
    window_energy = float(np.sum(window * window))
    if window_energy <= 0:
        raise ValueError("FFT penceresi hesaplanamadı.")
    bins = np.fft.rfft(x * window)
    power = (np.abs(bins) ** 2) / (n * window_energy)
    if n % 2 == 0:
        if power.size > 2:
            power[1:-1] *= 2.0
    elif power.size > 1:
        power[1:] *= 2.0
    power = np.maximum(power, FLOOR_POWER)
    power_db = 10.0 * np.log10(power)
    frequencies = np.fft.rfftfreq(n, d=1.0 / float(sample_rate))
    return frequencies, power_db


def aggregate_band_db(frequencies: np.ndarray, bin_power_db: np.ndarray,
                      sample_rate: float, center_hz: float, mode: str) -> float:
    """Integrate bin power in an octave/fractional-octave band with edge overlap.

    Each FFT bin contributes according to the fraction of its width inside the band.
    This avoids gaps at low frequencies for modest FFT sizes while refusing incomplete
    bands that extend beyond Nyquist. Returns -120 dBFS if no valid power exists.
    """
    freqs = np.asarray(frequencies, dtype=np.float64)
    db = np.asarray(bin_power_db, dtype=np.float64)
    if not len(freqs) or len(freqs) != len(db) or sample_rate <= 0 or center_hz <= 0:
        return -120.0
    ratio = band_ratio(mode)
    low, high = center_hz / ratio, center_hz * ratio
    nyquist = float(sample_rate) / 2
    if high > nyquist * 0.999:
        return -120.0
    if len(freqs) < 2:
        return -120.0
    bin_width = float(freqs[1] - freqs[0])
    if bin_width <= 0:
        return -120.0
    first = max(1, int(math.floor(low / bin_width)) - 1)
    last = min(len(freqs) - 1, int(math.ceil(high / bin_width)) + 1)
    total_power = 0.0
    used = 0
    for idx in range(first, last + 1):
        left = max(0.0, float(freqs[idx]) - bin_width / 2.0)
        right = min(nyquist, float(freqs[idx]) + bin_width / 2.0)
        width = right - left
        if width <= 0:
            continue
        overlap = min(high, right) - max(low, left)
        if overlap <= 0 or not math.isfinite(float(db[idx])):
            continue
        fraction = min(1.0, overlap / width)
        total_power += (10.0 ** (float(db[idx]) / 10.0)) * fraction
        used += 1
    if not used or total_power <= 0 or not math.isfinite(total_power):
        return -120.0
    return max(-120.0, min(6.0, 10.0 * math.log10(total_power)))


def _load_sounddevice():
    try:
        import sounddevice as sd
        return sd
    except Exception as exc:
        raise RuntimeError(
            "Yerel mikrofon sürücüsü yüklenemedi. Tek EXE paketinde sounddevice/PortAudio bulunmalı."
        ) from exc


def list_input_devices() -> list[dict[str, Any]]:
    """List PortAudio input devices, marking the OS default input."""
    sd = _load_sounddevice()
    try:
        all_devices = sd.query_devices()
        host_apis = sd.query_hostapis()
        default_pair = sd.default.device
        default_index = int(default_pair[0]) if default_pair is not None else -1
        result = []
        for index, device in enumerate(all_devices):
            channels = int(device.get("max_input_channels", 0) or 0)
            if channels < 1:
                continue
            host_id = int(device.get("hostapi", -1))
            host_name = str(host_apis[host_id].get("name", "")) if 0 <= host_id < len(host_apis) else ""
            result.append({
                "index": index,
                "name": str(device.get("name", f"Ses girişi {index}")),
                "host_api": host_name,
                "max_input_channels": channels,
                "default_sample_rate": int(round(float(device.get("default_samplerate", 0) or 0))),
                "is_default": index == default_index,
            })
        return result
    except Exception as exc:
        raise RuntimeError(f"Windows/PortAudio giriş aygıtları listelenemedi: {exc}") from exc


class RTACapture:
    """Thread-safe native PortAudio capture with a rolling sample window."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._event = threading.Event()
        self._worker: threading.Thread | None = None
        self._stream = None
        self._running = False
        self._buffer = np.zeros(16384, dtype=np.float32)
        self._write_pos = 0
        self._filled = 0
        self._frames_since_analysis = 0
        self._fft_size = 16384
        self._sample_rate = 0
        self._device_index: int | None = None
        self._device_name = ""
        self._frequencies: np.ndarray | None = None
        self._power_db: np.ndarray | None = None
        self._peak_dbfs = -120.0
        self._rms_dbfs = -120.0
        self._callback_status = ""
        self._last_error = ""
        self._samples_received = 0
        self._started_monotonic = 0.0
        self._last_callback_monotonic = 0.0

    @property
    def running(self) -> bool:
        with self._lock:
            return self._running

    def start(self, device_index: int | None = None, fft_size: int = 16384) -> dict[str, Any]:
        if fft_size not in SUPPORTED_FFT_SIZES:
            raise ValueError("FFT boyutu 8192, 16384 veya 32768 olmalı.")
        self.stop()
        sd = _load_sounddevice()
        chosen_index = None if device_index is None else int(device_index)
        try:
            devices = sd.query_devices()
            host_apis = sd.query_hostapis()
            if chosen_index is not None:
                if chosen_index < 0 or chosen_index >= len(devices):
                    raise ValueError("Seçilen mikrofon aygıt numarası geçersiz. Girişleri yenile.")
                device = devices[chosen_index]
                if int(device.get("max_input_channels", 0) or 0) < 1:
                    raise ValueError("Seçilen aygıtta ses girişi yok.")
                device_name = str(device.get("name", f"Ses girişi {chosen_index}"))
                default_rate = float(device.get("default_samplerate", 48000) or 48000)
                host_id = int(device.get("hostapi", -1))
            else:
                default_pair = sd.default.device
                default_index = int(default_pair[0]) if default_pair is not None else -1
                if default_index >= 0 and default_index < len(devices):
                    device = devices[default_index]
                    device_name = str(device.get("name", "Varsayılan giriş"))
                    default_rate = float(device.get("default_samplerate", 48000) or 48000)
                    host_id = int(device.get("hostapi", -1))
                    chosen_index = default_index
                else:
                    device = sd.query_devices(kind="input")
                    device_name = str(device.get("name", "Varsayılan giriş"))
                    default_rate = float(device.get("default_samplerate", 48000) or 48000)
                    host_id = int(device.get("hostapi", -1))
            host_name = str(host_apis[host_id].get("name", "")) if 0 <= host_id < len(host_apis) else ""
            candidates = []
            for candidate in (48000, int(round(default_rate)), 44100, 96000, 32000, 22050, 16000):
                if candidate > 0 and candidate not in candidates:
                    candidates.append(candidate)
            valid_rates = []
            for rate in candidates:
                try:
                    sd.check_input_settings(device=chosen_index, channels=1, samplerate=rate, dtype="float32")
                    valid_rates.append(rate)
                except Exception:
                    continue
            if not valid_rates:
                raise RuntimeError("Aygıt için desteklenen mono örnekleme hızı bulunamadı. Windows Ses > Giriş bölümünde varsayılan biçimi kontrol et.")
            sample_rate = valid_rates[0]
            with self._lock:
                self._fft_size = fft_size
                self._buffer = np.zeros(fft_size, dtype=np.float32)
                self._write_pos = 0
                self._filled = 0
                self._frames_since_analysis = 0
                self._sample_rate = sample_rate
                self._device_index = chosen_index
                self._device_name = device_name
                self._frequencies = None
                self._power_db = None
                self._peak_dbfs = -120.0
                self._rms_dbfs = -120.0
                self._callback_status = ""
                self._last_error = ""
                self._samples_received = 0
                self._started_monotonic = time.monotonic()
                self._last_callback_monotonic = 0.0
                self._running = True
                self._event.clear()
            stream = sd.InputStream(
                device=chosen_index, channels=1, samplerate=sample_rate,
                dtype="float32", blocksize=max(512, fft_size // 4),
                latency="high", callback=self._audio_callback,
            )
            with self._lock:
                self._stream = stream
            stream.start()
            self._worker = threading.Thread(target=self._analysis_loop, name="Stagepulse-RTA-FFT", daemon=True)
            self._worker.start()
            return {
                "ok": True, "running": True, "device_index": chosen_index,
                "device": device_name, "host_api": host_name,
                "sample_rate": sample_rate, "fft_size": fft_size,
                "frequency_limit_hz": sample_rate / 2,
                "message": "Yerel mikrofon yakalama başladı. Örnekleme, açılan PortAudio akışının hızıdır; mikrofonun kalibre edilmiş frekans cevabı değildir.",
            }
        except Exception as exc:
            self.stop()
            if isinstance(exc, (ValueError, RuntimeError)):
                raise
            raise RuntimeError(
                f"Mikrofon açılamadı ({type(exc).__name__}): {exc}. Windows Mikrofon iznini, aygıtı ve başka uygulamaların kullanımını kontrol et."
            ) from exc

    def _audio_callback(self, indata, frames, time_info, status) -> None:
        data = np.asarray(indata[:, 0], dtype=np.float32)
        with self._lock:
            if status:
                self._callback_status = str(status)
            peak = float(np.max(np.abs(data))) if data.size else 0.0
            rms = float(np.sqrt(np.mean(data.astype(np.float64) ** 2))) if data.size else 0.0
            self._peak_dbfs = 20 * math.log10(max(peak, 1e-6))
            self._rms_dbfs = 20 * math.log10(max(rms, 1e-6))
            n = data.size
            size = self._buffer.size
            if n >= size:
                self._buffer[:] = data[-size:]
                self._write_pos = 0
                self._filled = size
            elif n:
                first = min(n, size - self._write_pos)
                self._buffer[self._write_pos:self._write_pos + first] = data[:first]
                if n > first:
                    self._buffer[:n - first] = data[first:]
                self._write_pos = (self._write_pos + n) % size
                self._filled = min(size, self._filled + n)
            self._frames_since_analysis += n
            self._samples_received += n
            self._last_callback_monotonic = time.monotonic()
        self._event.set()

    def _analysis_loop(self) -> None:
        while True:
            self._event.wait(0.05)
            self._event.clear()
            with self._lock:
                if not self._running:
                    return
                if self._filled < self._fft_size or self._frames_since_analysis < max(1, self._sample_rate // 40):
                    continue
                pos = self._write_pos
                if pos == 0:
                    samples = self._buffer.copy()
                else:
                    samples = np.concatenate((self._buffer[pos:], self._buffer[:pos])).astype(np.float32, copy=False)
                sample_rate = self._sample_rate
                self._frames_since_analysis = 0
            try:
                frequencies, power_db = spectrum_power_db(samples, sample_rate)
                with self._lock:
                    self._frequencies = frequencies
                    self._power_db = power_db
            except Exception as exc:
                with self._lock:
                    self._last_error = str(exc)

    def snapshot(self, mode: str = "third", min_hz: float = 20,
                 max_hz: float = 20000) -> dict[str, Any]:
        with self._lock:
            running = self._running
            sample_rate = self._sample_rate
            fft_size = self._fft_size
            device = self._device_name
            frequencies = None if self._frequencies is None else self._frequencies.copy()
            power_db = None if self._power_db is None else self._power_db.copy()
            peak = self._peak_dbfs
            rms = self._rms_dbfs
            status = self._callback_status
            error = self._last_error
            samples_received = self._samples_received
            started_monotonic = self._started_monotonic
            last_callback_monotonic = self._last_callback_monotonic
        if not running:
            return {"ok": False, "running": False, "error": "Mikrofon çalışmıyor."}
        if error:
            return {"ok": False, "running": True, "error": error}
        now = time.monotonic()
        reference_time = last_callback_monotonic or started_monotonic
        seconds_since_last_callback = max(0.0, now - reference_time) if reference_time else 0.0
        # A stream that stops after producing valid frames must not keep presenting
        # its last spectrum as live data. Use the same two-second threshold as the UI.
        stream_stale = seconds_since_last_callback > 2.0
        centers = supported_centers(sample_rate, mode, min_hz, max_hz)
        if frequencies is None or power_db is None:
            values = [-120.0] * len(centers)
            ready = False
        else:
            values = [aggregate_band_db(frequencies, power_db, sample_rate, center, mode) for center in centers]
            ready = True
        if stream_stale:
            ready = False
        return {
            "ok": True, "running": True, "ready": ready,
            "device": device, "sample_rate": sample_rate, "fft_size": fft_size,
            "frequency_limit_hz": sample_rate / 2,
            "centers": centers, "band_dbfs": values,
            "peak_dbfs": peak, "rms_dbfs": rms,
            "stream_status": status,
            "samples_received": samples_received,
            "seconds_since_last_callback": seconds_since_last_callback,
            "stream_stale": stream_stale,
            "stream_healthy": not stream_stale,
            "message": (
                "Ses akışı durdu; giriş aygıtını ve sürücüyü kontrol et."
                if stream_stale else
                "FFT verisi hazırlanıyor…" if not ready else "FFT göreli güç spektrumu güncel."
            ),
        }

    def stop(self) -> dict[str, Any]:
        with self._lock:
            stream = self._stream
            worker = self._worker
            self._stream = None
            self._worker = None
            self._running = False
            self._event.set()
        error = None
        if stream is not None:
            try:
                stream.stop()
            except Exception as exc:
                error = str(exc)
            try:
                stream.close()
            except Exception as exc:
                error = error or str(exc)
        if worker is not None and worker is not threading.current_thread():
            worker.join(timeout=2.0)
        with self._lock:
            self._frequencies = None
            self._power_db = None
            self._filled = 0
            self._frames_since_analysis = 0
        return {"ok": error is None, "running": False, "error": error}
