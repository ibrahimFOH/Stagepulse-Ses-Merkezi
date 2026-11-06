# -*- coding: utf-8 -*-
"""Stagepulse Acoustic Engine: bağımsız iki kanallı ölçüm DSP çekirdeği.

Bu modül mevcut Stagepulse kodundan bağımsız, NumPy tabanlı yeni uygulamadır.
Girişler float örnek dizileridir. Sonuçlar dBFS/bağıl ölçümdür; dB SPL değildir.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np


def _audio_vector(values: Any, name: str) -> np.ndarray:
    data = np.asarray(values, dtype=np.float64)
    if data.ndim == 2:
        if data.shape[1] == 1:
            data = data[:, 0]
        else:
            raise ValueError(f"{name}: tek kanallı örnek dizisi gerekli.")
    if data.ndim != 1 or data.size < 32:
        raise ValueError(f"{name}: en az 32 ses örneği gerekli.")
    if not np.all(np.isfinite(data)):
        raise ValueError(f"{name}: NaN veya sonsuz örnek içeriyor.")
    return data


def _validate_rate(sample_rate: Any) -> float:
    rate = float(sample_rate)
    if not math.isfinite(rate) or rate < 8000 or rate > 384000:
        raise ValueError("Örnekleme hızı 8.000–384.000 Hz aralığında olmalı.")
    return rate


def _segments(data: np.ndarray, size: int, overlap: float):
    if size < 32 or size > data.size:
        raise ValueError("Segment boyutu sinyal uzunluğundan küçük ve en az 32 olmalı.")
    if not 0 <= overlap < 1:
        raise ValueError("Örtüşme oranı 0 ile 1 arasında olmalı.")
    step = max(1, int(round(size * (1.0 - overlap))))
    window = np.hanning(size)
    for start in range(0, data.size - size + 1, step):
        yield data[start:start + size] * window
    return


def transfer_function(
    reference: Any,
    measurement: Any,
    sample_rate: Any,
    segment_size: int = 8192,
    overlap: float = 0.5,
    coherence_floor: float = 1e-24,
    _include_welch: bool = False,
) -> dict[str, Any]:
    """Welch H1 transfer function, magnitude, phase and magnitude-squared coherence.

    Konvansiyon: reference giriş, measurement çıkıştır. H1 = S_yx / S_xx.
    """
    x = _audio_vector(reference, "Referans")
    y = _audio_vector(measurement, "Ölçüm")
    rate = _validate_rate(sample_rate)
    if x.size != y.size:
        raise ValueError("Referans ve ölçüm kanallarının örnek sayısı eşit olmalı.")
    n = int(segment_size)
    if n & (n - 1) or n < 256 or n > 65536:
        raise ValueError("Segment boyutu 256–65536 aralığında ikinin kuvveti olmalı.")
    if x.size < n:
        raise ValueError("İki kanalda da en az bir tam analiz segmenti bulunmalı.")
    step = max(1, int(round(n * (1.0 - float(overlap)))))
    if not 0 <= float(overlap) < 1:
        raise ValueError("Örtüşme oranı 0 ile 1 arasında olmalı.")
    window = np.hanning(n)
    scale = float(np.sum(window * window))
    if scale <= 0:
        raise ValueError("Analiz penceresi oluşturulamadı.")

    sxx = np.zeros(n // 2 + 1, dtype=np.float64)
    syy = np.zeros_like(sxx)
    syx = np.zeros(sxx.shape, dtype=np.complex128)
    count = 0
    for start in range(0, x.size - n + 1, step):
        X = np.fft.rfft(x[start:start+n] * window)
        Y = np.fft.rfft(y[start:start+n] * window)
        sxx += (np.abs(X) ** 2) / scale
        syy += (np.abs(Y) ** 2) / scale
        syx += (np.conj(X) * Y) / scale
        count += 1
    if count == 0:
        raise ValueError("Analiz için yeterli ses verisi yok.")
    sxx /= count
    syy /= count
    syx /= count

    valid = (sxx > float(coherence_floor)) & (syy > float(coherence_floor))
    h1 = np.zeros_like(syx)
    h1[valid] = syx[valid] / sxx[valid]
    denominator = sxx * syy
    coherence = np.zeros_like(sxx)
    good = valid & (denominator > float(coherence_floor))
    coherence[good] = np.clip(np.abs(syx[good]) ** 2 / denominator[good], 0.0, 1.0)
    magnitude_db = np.full(sxx.shape, 0.0, dtype=np.float64)
    phase_deg = np.full(sxx.shape, 0.0, dtype=np.float64)
    magnitude_db[valid] = 20.0 * np.log10(np.maximum(np.abs(h1[valid]), 1e-15))
    phase_deg[valid] = np.rad2deg(np.angle(h1[valid]))
    frequencies = np.fft.rfftfreq(n, 1.0 / rate)

    result = {
        "ok": True,
        "engine": "Stagepulse Acoustic Engine",
        "method": "Welch H1",
        "sample_rate": rate,
        "segment_size": n,
        "overlap": float(overlap),
        "averages": count,
        "frequency_hz": frequencies.tolist(),
        "magnitude_db": [float(v) if is_valid else None for v, is_valid in zip(magnitude_db, valid)],
        "phase_deg": [float(v) if is_valid else None for v, is_valid in zip(phase_deg, valid)],
        "coherence": [float(v) if is_valid else None for v, is_valid in zip(coherence, valid)],
        "valid_mask": valid.tolist(),
        "units": {"magnitude": "dB", "phase": "degree", "coherence": "ratio"},
        "calibrated_spl": False,
    }
    if _include_welch:
        result["_welch"] = {"sxx": sxx, "syx": syx, "averages": count}
    return result


def delay_finder(reference: Any, measurement: Any, sample_rate: Any,
                 max_delay_ms: float = 500.0) -> dict[str, Any]:
    """Find relative delay by normalized cross-correlation.

    Pozitif gecikme, ölçüm kanalının referanstan sonra geldiğini belirtir.
    """
    x = _audio_vector(reference, "Referans")
    y = _audio_vector(measurement, "Ölçüm")
    rate = _validate_rate(sample_rate)
    if x.size != y.size:
        raise ValueError("Referans ve ölçüm kanallarının örnek sayısı eşit olmalı.")
    limit_ms = float(max_delay_ms)
    if not math.isfinite(limit_ms) or not 0 < limit_ms <= 2000:
        raise ValueError("Azami gecikme 0–2000 ms aralığında olmalı.")
    max_lag = min(x.size - 1, int(round(rate * limit_ms / 1000.0)))
    x = x - np.mean(x)
    y = y - np.mean(y)
    nx = float(np.linalg.norm(x))
    ny = float(np.linalg.norm(y))
    if nx <= 1e-15 or ny <= 1e-15:
        raise ValueError("Sessiz kanalda gecikme hesaplanamaz.")
    # FFT correlation avoids NumPy's O(N²) direct correlate on long field recordings.
    fft_size = 1 << (2 * x.size - 1).bit_length()
    if fft_size > (1 << 20):
        raise ValueError("Kayıt çok uzun; gecikme analizi için FFT boyutu 1.048.576 örnek sınırını aşıyor.")
    spectrum_y = np.fft.rfft(y, n=fft_size)
    spectrum_x = np.fft.rfft(x, n=fft_size)
    circular = np.fft.irfft(spectrum_y * np.conj(spectrum_x), n=fft_size)
    if max_lag:
        corr = np.concatenate((circular[-max_lag:], circular[:max_lag + 1]))
    else:
        corr = circular[:1]
    lags = np.arange(-max_lag, max_lag + 1, dtype=np.int64)
    corr = corr / (nx * ny)
    peak_index = int(np.argmax(np.abs(corr)))
    lag = float(lags[peak_index])
    peak = float(corr[peak_index])
    if 0 < peak_index < len(corr) - 1:
        a, b, c = (abs(float(v)) for v in corr[peak_index-1:peak_index+2])
        denom = a - 2.0 * b + c
        if abs(denom) > 1e-15:
            lag += float(np.clip(0.5 * (a - c) / denom, -1.0, 1.0))
    delay_ms = lag * 1000.0 / rate
    return {
        "ok": True,
        "method": "normalized cross-correlation",
        "delay_samples": lag,
        "delay_ms": delay_ms,
        "polarity_inverted": peak < 0,
        "correlation_peak": abs(peak),
        "sample_rate": rate,
        "calibrated_spl": False,
    }


def impulse_response(reference: Any, measurement: Any, sample_rate: Any,
                     segment_size: int = 8192, overlap: float = 0.5,
                     tf_result: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return H1-derived impulse response and normalized ETC envelope."""
    result = tf_result if tf_result is not None else transfer_function(
        reference, measurement, sample_rate, segment_size, overlap, _include_welch=True
    )
    welch = result.get("_welch")
    if not isinstance(welch, dict) or "sxx" not in welch or "syx" not in welch:
        result = transfer_function(
            reference, measurement, sample_rate, segment_size, overlap, _include_welch=True
        )
        welch = result["_welch"]
    sxx = np.asarray(welch["sxx"], dtype=np.float64)
    syx = np.asarray(welch["syx"], dtype=np.complex128)
    n = int(segment_size)
    h1 = syx / np.maximum(sxx, 1e-24)
    ir = np.fft.irfft(h1, n=n)
    peak = float(np.max(np.abs(ir)))
    normalized = ir / peak if peak > 0 else ir
    etc = 20.0 * np.log10(np.maximum(np.abs(normalized), 1e-12))
    times_ms = (np.arange(n, dtype=np.float64) * 1000.0 / float(sample_rate))
    result.pop("_welch", None)
    result.update({
        "impulse_time_ms": times_ms.tolist(),
        "impulse_response": ir.tolist(),
        "etc_db": etc.tolist(),
        "impulse_peak": peak,
    })
    return result
