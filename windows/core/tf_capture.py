# -*- coding: utf-8 -*-
"""Eşzamanlı stereo girişten Welch H1 transfer-function ölçümü.

CH0 referans, CH1 ölçüm mikrofonudur. Sonuçlar göreli dB, faz ve coherence
değerleridir; dB SPL kalibrasyonu veya gecikme telafisi içermez.
"""
from __future__ import annotations

import math
import threading
import time
from typing import Any

import numpy as np

from .rta_capture import SUPPORTED_FFT_SIZES, band_ratio, supported_centers


def _load_sd():
    try:
        import sounddevice as sd
        return sd
    except Exception as exc:
        raise RuntimeError(f"PortAudio yüklenemedi: {exc}") from exc


class TFCapture:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._event = threading.Event()
        self._worker = None
        self._stream = None
        self._running = False
        self._fft_size = 16384
        self._sample_rate = 0
        self._device_index = None
        self._device_name = ""
        self._num_avg = 8
        self._window = None
        self._window_energy = 1.0
        self._sxx = None
        self._syy = None
        self._syx = None
        self._avg_count = 0
        self._ref_buf = None
        self._mic_buf = None
        self._write_pos = 0
        self._filled = 0
        self._frames_since = 0
        self._peak_ref = -120.0
        self._peak_mic = -120.0
        self._last_error = ""
        self._callback_status = ""
        self._started = 0.0
        self._last_callback = 0.0

    @property
    def running(self) -> bool:
        with self._lock:
            return self._running

    def start(self, device_index: Any = None, fft_size: int = 16384,
              num_averages: int = 8) -> dict[str, Any]:
        try:
            fft_size = int(fft_size)
            num_averages = max(1, min(64, int(num_averages)))
        except (TypeError, ValueError) as exc:
            raise ValueError("FFT ve ortalama değerleri sayısal olmalı.") from exc
        if fft_size not in SUPPORTED_FFT_SIZES:
            raise ValueError("FFT boyutu 8192, 16384 veya 32768 olmalı.")
        self.stop()
        sd = _load_sd()
        devices = sd.query_devices()
        default_rate = 48000.0
        chosen = None if device_index in (None, "", "default") else int(device_index)
        if chosen is not None:
            if chosen < 0 or chosen >= len(devices):
                raise ValueError("Stereo giriş aygıt numarası geçersiz.")
            device = devices[chosen]
            if int(device.get("max_input_channels", 0) or 0) < 2:
                raise RuntimeError("TF ölçümü için aynı aygıtta en az iki giriş kanalı gerekir.")
            name = str(device.get("name", f"Giriş {chosen}"))
            default_rate = float(device.get("default_samplerate", 48000) or 48000)
        else:
            default_pair = sd.default.device
            default_index = int(default_pair[0]) if default_pair is not None else -1
            candidates = ([default_index] if 0 <= default_index < len(devices) else []) + list(range(len(devices)))
            for idx in candidates:
                dev = devices[idx]
                if int(dev.get("max_input_channels", 0) or 0) >= 2:
                    chosen = idx
                    device = dev
                    name = str(dev.get("name", f"Giriş {idx}"))
                    default_rate = float(dev.get("default_samplerate", 48000) or 48000)
                    break
            else:
                raise RuntimeError("Stereo girişli aygıt bulunamadı. Referans ve mikrofon aynı ses kartına bağlanmalı.")
        rates = []
        for rate in (48000, int(round(default_rate)), 44100, 96000, 32000):
            if rate > 0 and rate not in rates:
                rates.append(rate)
        valid = []
        for rate in rates:
            try:
                sd.check_input_settings(device=chosen, channels=2, samplerate=rate, dtype="float32")
                valid.append(rate)
            except Exception:
                continue
        if not valid:
            raise RuntimeError("Seçilen aygıtta desteklenen stereo örnekleme hızı bulunamadı.")
        sr = valid[0]
        window = np.hanning(fft_size)
        with self._lock:
            self._fft_size = fft_size
            self._sample_rate = sr
            self._device_index = chosen
            self._device_name = name
            self._num_avg = num_averages
            self._window = window
            self._window_energy = float(np.sum(window * window))
            bins = fft_size // 2 + 1
            self._sxx = np.zeros(bins, dtype=np.float64)
            self._syy = np.zeros(bins, dtype=np.float64)
            self._syx = np.zeros(bins, dtype=np.complex128)
            self._avg_count = 0
            self._ref_buf = np.zeros(fft_size, dtype=np.float32)
            self._mic_buf = np.zeros(fft_size, dtype=np.float32)
            self._write_pos = 0
            self._filled = 0
            self._frames_since = 0
            self._peak_ref = self._peak_mic = -120.0
            self._last_error = self._callback_status = ""
            self._started = time.monotonic()
            self._last_callback = 0.0
            self._running = True
            self._event.clear()
        try:
            stream = sd.InputStream(
                device=chosen, channels=2, samplerate=sr, dtype="float32",
                blocksize=max(512, fft_size // 4), latency="high",
                callback=self._cb,
            )
            with self._lock:
                self._stream = stream
            stream.start()
            worker = threading.Thread(target=self._loop, name="Stagepulse-TF-FFT", daemon=True)
            with self._lock:
                self._worker = worker
            worker.start()
        except Exception as exc:
            self.stop()
            raise RuntimeError(f"Stereo TF akışı başlatılamadı: {exc}") from exc
        return {
            "ok": True, "running": True, "device_index": chosen,
            "device": name, "sample_rate": sr, "fft_size": fft_size,
            "averages_target": num_averages,
            "message": "Stereo TF başladı. CH0 referans, CH1 ölçüm mikrofonu. Pembe gürültü kullan.",
        }

    def _cb(self, indata, frames, time_info, status) -> None:
        arr = np.asarray(indata, dtype=np.float32)
        if arr.ndim != 2 or arr.shape[1] < 2 or not arr.size:
            return
        ref = np.nan_to_num(arr[:, 0], nan=0.0, posinf=0.0, neginf=0.0)
        mic = np.nan_to_num(arr[:, 1], nan=0.0, posinf=0.0, neginf=0.0)
        with self._lock:
            if not self._running:
                return
            self._peak_ref = 20.0 * math.log10(max(float(np.max(np.abs(ref))), 1e-6))
            self._peak_mic = 20.0 * math.log10(max(float(np.max(np.abs(mic))), 1e-6))
            if status:
                self._callback_status = str(status)
            n = ref.size
            size = self._fft_size
            pos = self._write_pos
            if n >= size:
                self._ref_buf[:] = ref[-size:]
                self._mic_buf[:] = mic[-size:]
                self._write_pos = 0
                self._filled = size
            else:
                first = min(n, size - pos)
                self._ref_buf[pos:pos + first] = ref[:first]
                self._mic_buf[pos:pos + first] = mic[:first]
                if n > first:
                    self._ref_buf[:n - first] = ref[first:]
                    self._mic_buf[:n - first] = mic[first:]
                self._write_pos = (pos + n) % size
                self._filled = min(size, self._filled + n)
            self._frames_since += n
            self._last_callback = time.monotonic()
        self._event.set()

    def _loop(self) -> None:
        while True:
            self._event.wait(0.05)
            self._event.clear()
            with self._lock:
                if not self._running:
                    return
                if self._filled < self._fft_size or self._frames_since < max(1, self._sample_rate // 25):
                    continue
                pos = self._write_pos
                if pos == 0:
                    ref = self._ref_buf.copy()
                    mic = self._mic_buf.copy()
                else:
                    ref = np.concatenate((self._ref_buf[pos:], self._ref_buf[:pos]))
                    mic = np.concatenate((self._mic_buf[pos:], self._mic_buf[:pos]))
                self._frames_since = 0
                window = self._window
                energy = self._window_energy
            try:
                x = np.fft.rfft(ref.astype(np.float64) * window)
                y = np.fft.rfft(mic.astype(np.float64) * window)
                pxx = np.abs(x) ** 2 / energy
                pyy = np.abs(y) ** 2 / energy
                pyx = np.conj(x) * y / energy
                with self._lock:
                    if self._avg_count < self._num_avg:
                        self._sxx += pxx
                        self._syy += pyy
                        self._syx += pyx
                        self._avg_count += 1
                    else:
                        # Sabit N uzunluklu kayan üstel ortalama; sayaç büyümez.
                        n = float(self._num_avg)
                        self._sxx += (pxx - self._sxx / n)
                        self._syy += (pyy - self._syy / n)
                        self._syx += (pyx - self._syx / n)
            except Exception as exc:
                with self._lock:
                    self._last_error = str(exc)

    def snapshot(self, mode: str = "third", min_hz: float = 20,
                 max_hz: float = 20000) -> dict[str, Any]:
        with self._lock:
            if not self._running:
                return {"ok": False, "running": False, "error": "TF çalışmıyor."}
            if self._last_error:
                return {"ok": False, "running": True, "error": self._last_error}
            sr, fft, count = self._sample_rate, self._fft_size, self._avg_count
            sxx, syy, syx = self._sxx.copy(), self._syy.copy(), self._syx.copy()
            peak_ref, peak_mic = self._peak_ref, self._peak_mic
            started, last_cb, device = self._started, self._last_callback, self._device_name
            callback_status = self._callback_status
        centers = supported_centers(sr, mode, min_hz, max_hz)
        if count == 0:
            return {
                "ok": True, "running": True, "ready": False, "device": device,
                "sample_rate": sr, "fft_size": fft, "centers": centers,
                "mag_db": [-60.0] * len(centers), "phase_deg": [0.0] * len(centers),
                "coherence": [0.0] * len(centers), "averages": 0,
                "peak_ref_dbfs": peak_ref, "peak_mic_dbfs": peak_mic,
                "seconds_since_last_callback": max(0.0, time.monotonic() - (last_cb or started)),
                "callback_status": callback_status, "message": "TF ortalaması hazırlanıyor.",
            }
        if count < self._num_avg:
            sxx /= count
            syy /= count
            syx /= count
        else:
            sxx /= float(self._num_avg)
            syy /= float(self._num_avg)
            syx /= float(self._num_avg)
        h = np.zeros_like(syx)
        valid = sxx > 1e-24
        h[valid] = syx[valid] / sxx[valid]
        denom = sxx * syy
        coherence = np.zeros_like(sxx)
        good = denom > 1e-24
        coherence[good] = np.clip(np.abs(syx[good]) ** 2 / denom[good], 0.0, 1.0)
        freqs = np.fft.rfftfreq(fft, d=1.0 / float(sr))
        ratio = band_ratio(mode)
        magnitude, phase, coh_band = [], [], []
        for center in centers:
            low, high = center / ratio, center * ratio
            idx = np.flatnonzero((freqs >= low) & (freqs <= high))
            if idx.size == 0:
                magnitude.append(-60.0)
                phase.append(0.0)
                coh_band.append(0.0)
                continue
            weights = np.maximum(sxx[idx], 1e-24)
            h_band = np.sum(h[idx] * weights) / np.sum(weights)
            magnitude.append(float(np.clip(20.0 * math.log10(max(abs(h_band), 1e-6)), -60.0, 30.0)))
            phase.append(float(np.degrees(np.angle(h_band))))
            coh_band.append(float(np.average(coherence[idx], weights=weights)))
        return {
            "ok": True, "running": True, "ready": count >= self._num_avg,
            "device": device, "sample_rate": sr, "fft_size": fft,
            "centers": centers, "mag_db": magnitude, "phase_deg": phase,
            "coherence": coh_band, "averages": count,
            "peak_ref_dbfs": peak_ref, "peak_mic_dbfs": peak_mic,
            "seconds_since_last_callback": max(0.0, time.monotonic() - (last_cb or started)),
            "callback_status": callback_status, "message": "TF güncel.",
        }

    def stop(self) -> dict[str, Any]:
        with self._lock:
            stream, worker = self._stream, self._worker
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
            worker.join(timeout=3.0)
            if worker.is_alive():
                error = error or "TF analiz iş parçacığı zamanında kapanmadı."
        return {"ok": error is None, "running": False, "error": error}
