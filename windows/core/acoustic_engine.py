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

def fractional_octave_spectrum(samples: Any, sample_rate: Any, bands_per_octave: int = 3,
                                fft_size: int | None = None, min_hz: float = 20.0,
                                max_hz: float = 20000.0) -> dict[str, Any]:
    """Fractional-octave FFT band powers in dBFS RMS; not an IEC filter-class claim."""
    x = _audio_vector(samples, "Ölçüm")
    rate = _validate_rate(sample_rate)
    try:
        bands, low_limit, high_limit = int(bands_per_octave), float(min_hz), float(max_hz)
    except (TypeError, ValueError) as exc:
        raise ValueError("Bant çözünürlüğü ve frekans sınırları sayısal olmalı.") from exc
    if bands not in (1, 3, 6, 12, 24, 48):
        raise ValueError("Bant çözünürlüğü 1, 3, 6, 12, 24 veya 48 olmalı.")
    if not math.isfinite(low_limit) or not math.isfinite(high_limit) or low_limit <= 0 or high_limit <= low_limit:
        raise ValueError("Frekans aralığı pozitif ve artan olmalı.")
    if fft_size is None:
        fft_size = 1 << (min(x.size, 65536).bit_length() - 1)
    try:
        size = int(fft_size)
    except (TypeError, ValueError) as exc:
        raise ValueError("FFT boyutu tam sayı olmalı.") from exc
    if size < 256 or size & (size - 1) or size > x.size or size > 262144:
        raise ValueError("FFT boyutu 256–262144 aralığında, ikinin kuvveti ve kayıt uzunluğundan küçük olmalı.")
    frame = x[-size:]
    window = np.hanning(size)
    window_energy = float(np.sum(window * window))
    if window_energy <= 0:
        raise ValueError("FFT penceresi oluşturulamadı.")
    spectrum = np.fft.rfft(frame * window)
    power = (np.abs(spectrum) ** 2) / (size * window_energy)
    if size % 2 == 0:
        if power.size > 2:
            power[1:-1] *= 2.0
    elif power.size > 1:
        power[1:] *= 2.0
    frequencies = np.fft.rfftfreq(size, d=1.0 / rate)
    nyquist, bin_width = rate / 2.0, rate / size
    half_band_ratio = 2.0 ** (1.0 / (2.0 * bands))
    first = math.ceil(bands * math.log2(low_limit / 1000.0) - 1e-12)
    last = math.floor(bands * math.log2(high_limit / 1000.0) + 1e-12)
    centers, levels = [], []
    for band_index in range(first, last + 1):
        center = 1000.0 * (2.0 ** (band_index / bands))
        lower, upper = center / half_band_ratio, center * half_band_ratio
        if center < low_limit or center > high_limit or upper > nyquist * 0.999:
            continue
        total, used = 0.0, 0
        for bin_index, frequency in enumerate(frequencies):
            left = 0.0 if bin_index == 0 else max(0.0, float(frequency) - bin_width / 2.0)
            right = min(nyquist, float(frequency) + bin_width / 2.0)
            width = right - left
            if width <= 0:
                continue
            overlap = min(upper, right) - max(lower, left)
            if overlap > 0:
                total += float(power[bin_index]) * min(1.0, overlap / width)
                used += 1
        level = 10.0 * math.log10(total) if used and total > 0 else -120.0
        centers.append(center)
        levels.append(max(-120.0, min(6.0, level)))
    return {"ok": True, "method": "Hann FFT / fractional-bin power integration",
            "sample_rate": rate, "fft_size": size, "bands_per_octave": bands,
            "centers_hz": centers, "levels_dbfs": levels, "units": "dBFS RMS",
            "band_definition": "base-2 exact geometric centers anchored at 1 kHz",
            "standard_compliance": False}


def _weighting_filter(samples: np.ndarray, sample_rate: float, weighting: str) -> np.ndarray:
    """A/C frequency weighting with bilinear prewarping; Z is unweighted."""
    mode = str(weighting).upper()
    if mode == "Z":
        return samples.copy()
    if mode not in ("A", "C"):
        raise ValueError("Frekans ağırlıklandırması A, C veya Z olmalı.")
    if sample_rate < 32000:
        raise ValueError("A/C ağırlıklandırması için örnekleme hızı en az 32 kHz olmalı.")
    from scipy.signal import bilinear, lfilter, zpk2tf
    f1, f2, f3, f4 = 20.598997, 107.65265, 737.86223, 12194.217
    def prewarp(frequency: float) -> float:
        return 2.0 * sample_rate * math.tan(math.pi * frequency / sample_rate)
    w1, w2, w3, w4 = (prewarp(v) for v in (f1, f2, f3, f4))
    if mode == "A":
        zeros = [0j] * 4
        poles = [-w1 + 0j] * 2 + [-w2 + 0j, -w3 + 0j] + [-w4 + 0j] * 2
    else:
        zeros = [0j] * 2
        poles = [-w1 + 0j] * 2 + [-w4 + 0j] * 2
    numerator, denominator = zpk2tf(zeros, poles, 1.0)
    ref = prewarp(1000.0)
    gain = abs(np.polyval(numerator, 1j * ref) / np.polyval(denominator, 1j * ref))
    if not math.isfinite(float(gain)) or gain <= 0:
        raise RuntimeError("A/C ağırlıklandırma filtresi normalize edilemedi.")
    digital_b, digital_a = bilinear(numerator / gain, denominator, fs=sample_rate)
    return lfilter(digital_b, digital_a, samples)


def measure_spl(samples: Any, sample_rate: Any,
                calibration_offset_db: float | None = None) -> dict[str, Any]:
    """A/C/Z Leq, Fast/Slow maxima, peak and 1-second L10/L50/L90.

    Without a physical calibrator offset, levels remain explicitly labelled dBFS.
    """
    x = _audio_vector(samples, "Ölçüm")
    rate = _validate_rate(sample_rate)
    offset = None if calibration_offset_db is None else float(calibration_offset_db)
    if offset is not None and not math.isfinite(offset):
        raise ValueError("Kalibrasyon düzeltmesi sonlu bir sayı olmalı.")
    from scipy.signal import lfilter
    block_size = max(1, int(round(rate)))
    results: dict[str, Any] = {}
    for weighting in ("A", "C", "Z"):
        weighted = _weighting_filter(x, rate, weighting)
        squared = weighted * weighted
        fast_alpha = 1.0 - math.exp(-1.0 / (rate * 0.125))
        slow_alpha = 1.0 - math.exp(-1.0 / rate)
        fast_power = lfilter([fast_alpha], [1.0, -(1.0 - fast_alpha)], squared)
        slow_power = lfilter([slow_alpha], [1.0, -(1.0 - slow_alpha)], squared)
        correction = offset if offset is not None else 0.0
        def power_db(value: float) -> float:
            return 10.0 * math.log10(max(float(value), 1e-20)) + correction
        blocks = []
        for start in range(0, squared.size, block_size):
            block = squared[start:start + block_size]
            if block.size:
                blocks.append(power_db(float(np.mean(block))))
        results[weighting] = {
            "leq_db": power_db(float(np.mean(squared))),
            "lmax_fast_db": power_db(float(np.max(fast_power))),
            "lmax_slow_db": power_db(float(np.max(slow_power))),
            "lpeak_db": 20.0 * math.log10(max(float(np.max(np.abs(weighted))), 1e-10)) + correction,
            "percentiles_1s_db": {
                "L10": float(np.percentile(blocks, 90)),
                "L50": float(np.percentile(blocks, 50)),
                "L90": float(np.percentile(blocks, 10)),
            },
        }
    return {
        "ok": True, "sample_rate": rate, "frames": int(x.size),
        "duration_seconds": float(x.size / rate),
        "calibrated_spl": offset is not None,
        "units": "dB SPL" if offset is not None else "dBFS",
        "calibration_offset_db": offset,
        "peak_dbfs": 20.0 * math.log10(max(float(np.max(np.abs(x))), 1e-10)),
        "clipping_percent": float(np.mean(np.abs(x) >= 0.999) * 100.0),
        "percentile_window_seconds": 1.0, "weightings": results,
    }
