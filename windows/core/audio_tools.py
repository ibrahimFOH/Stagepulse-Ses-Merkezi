# -*- coding: utf-8 -*-
"""Yerel ses dosyası analizi ve loudness normalizasyonu."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


def analyze_wav(path: str | Path) -> dict[str, Any]:
    """PCM WAV dosyasını toplam ve kanal bazında sample-peak/RMS/DC analiz eder."""
    import wave
    import numpy as np

    p = Path(path).expanduser().resolve()
    if not p.is_file():
        raise FileNotFoundError(f"Dosya bulunamadı: {p}")
    try:
        with wave.open(str(p), "rb") as wf:
            channels = wf.getnchannels()
            sample_rate = wf.getframerate()
            width = wf.getsampwidth()
            frames = wf.getnframes()
            if wf.getcomptype() != "NONE":
                raise ValueError("Yalnızca sıkıştırılmamış PCM WAV destekleniyor.")
            if width not in (1, 2, 3, 4):
                raise ValueError(f"Desteklenmeyen PCM bit derinliği: {width * 8}")
            if sample_rate <= 0 or channels <= 0 or frames <= 0:
                raise ValueError("WAV başlığı eksik veya geçersiz.")

            full_scale = float(1 << (8 * width - 1))
            peak = np.zeros(channels, dtype=np.float64)
            squares = np.zeros(channels, dtype=np.float64)
            dc_sum = np.zeros(channels, dtype=np.float64)
            near_full = np.zeros(channels, dtype=np.int64)
            counts = np.zeros(channels, dtype=np.int64)
            chunk_frames = max(1, min(32768, sample_rate // 2 or 1))

            while True:
                raw = wf.readframes(chunk_frames)
                if not raw:
                    break
                if width == 1:
                    values = np.frombuffer(raw, dtype=np.uint8).astype(np.int32) - 128
                elif width == 2:
                    values = np.frombuffer(raw, dtype="<i2").astype(np.int32)
                elif width == 3:
                    packed = np.frombuffer(raw[:len(raw) - len(raw) % 3], dtype=np.uint8).reshape(-1, 3)
                    unsigned = packed[:, 0].astype(np.int32) | (packed[:, 1].astype(np.int32) << 8) | (packed[:, 2].astype(np.int32) << 16)
                    values = (unsigned ^ 0x800000) - 0x800000
                else:
                    values = np.frombuffer(raw[:len(raw) - len(raw) % 4], dtype="<i4").astype(np.int64)

                usable = values.size - values.size % channels
                if usable == 0:
                    continue
                matrix = values[:usable].reshape(-1, channels).astype(np.float64) / full_scale
                abs_matrix = np.abs(matrix)
                peak = np.maximum(peak, abs_matrix.max(axis=0))
                squares += np.square(matrix).sum(axis=0, dtype=np.float64)
                dc_sum += matrix.sum(axis=0, dtype=np.float64)
                near_full += np.count_nonzero(abs_matrix >= (1.0 - 1.0 / full_scale), axis=0)
                counts += matrix.shape[0]
    except (wave.Error, EOFError) as exc:
        raise ValueError(f"WAV okunamadı: {exc}") from exc

    if not np.all(counts > 0):
        raise ValueError("Dosyada PCM örneği bulunamadı.")
    rms = np.sqrt(squares / counts)
    peak_db = np.where(peak > 0, 20.0 * np.log10(np.maximum(peak, 1e-300)), np.nan)
    rms_db = np.where(rms > 0, 20.0 * np.log10(np.maximum(rms, 1e-300)), np.nan)
    crest = peak_db - rms_db
    channel_reports = []
    for index in range(channels):
        channel_reports.append({
            "channel": index + 1,
            "sample_peak_dbfs": None if not np.isfinite(peak_db[index]) else float(peak_db[index]),
            "rms_dbfs": None if not np.isfinite(rms_db[index]) else float(rms_db[index]),
            "crest_factor_db": None if not np.isfinite(crest[index]) else float(crest[index]),
            "dc_offset_percent": float(100.0 * dc_sum[index] / counts[index]),
            "near_full_sample_count": int(near_full[index]),
            "near_full_sample_percent": float(100.0 * near_full[index] / counts[index]),
            "sample_values": int(counts[index]),
        })
    total_count = int(counts.sum())
    total_peak = float(peak.max())
    total_rms = math.sqrt(float(squares.sum()) / total_count)
    total_peak_db = 20 * math.log10(total_peak) if total_peak > 0 else None
    total_rms_db = 20 * math.log10(total_rms) if total_rms > 0 else None
    return {
        "file": p.name, "path": str(p), "channels": channels,
        "sample_rate_hz": sample_rate, "bits_per_sample": width * 8,
        "frames": frames, "duration_seconds": frames / sample_rate,
        "sample_values": total_count,
        "sample_peak_dbfs": total_peak_db, "rms_dbfs": total_rms_db,
        "crest_factor_db": total_peak_db - total_rms_db if total_peak_db is not None and total_rms_db is not None else None,
        "near_full_sample_count": int(near_full.sum()),
        "near_full_sample_percent": float(100.0 * near_full.sum() / total_count),
        "dc_offset_percent": float(100.0 * dc_sum.sum() / total_count),
        "channel_analysis": channel_reports,
        "scope_note": "Bu rapor PCM sample-peak/RMS/DC ölçer. LUFS, oversampled true-peak veya kalibreli dB SPL ölçümü değildir."
    }

def normalize_lufs(source: str | Path, output: str | Path, target_lufs: float = -14.0,
                   target_true_peak_db: float = -1.0) -> dict[str, Any]:
    """K-weighted BS.1770 loudness hedefi ve tahmini 4x true-peak tavanıyla WAV üretir.

    Kaynak dosya değiştirilmez. True-peak sınırı hedef LUFS'e erişmeyi engellerse
    sınır önceliklidir; bu araç limiter uygulamaz ve sonucu açıkça raporlar.
    """
    import numpy as np
    import soundfile as sf
    import pyloudnorm as pyln
    from scipy.signal import resample_poly

    src = Path(source).expanduser().resolve()
    out = Path(output).expanduser().resolve()
    if not src.is_file():
        raise FileNotFoundError(f"Kaynak dosya bulunamadı: {src}")
    if src == out:
        raise ValueError("Kaynak ve çıktı aynı dosya olamaz.")
    if not -70.0 <= float(target_lufs) <= 0.0:
        raise ValueError("Hedef LUFS -70 ile 0 arasında olmalıdır.")
    if not -20.0 <= float(target_true_peak_db) <= 0.0:
        raise ValueError("True-peak tavanı -20 ile 0 dBTP arasında olmalıdır.")

    audio, rate = sf.read(str(src), dtype="float32", always_2d=True)
    if audio.size == 0 or rate < 8000:
        raise ValueError("Ses dosyası boş veya örnekleme frekansı geçersiz.")
    if not np.isfinite(audio).all():
        raise ValueError("Ses dosyasında NaN veya sonsuz örnek var.")
    if len(audio) < int(rate * 0.5):
        raise ValueError("Loudness ölçümü için ses en az 0,5 saniye olmalıdır.")

    meter = pyln.Meter(int(rate), filter_class="DeMan")
    measured = float(meter.integrated_loudness(audio))
    try:
        input_lra = float(meter.loudness_range(audio))
    except (ValueError, RuntimeError):
        input_lra = float("nan")
    if not math.isfinite(input_lra):
        input_lra = None
    if not math.isfinite(measured):
        raise ValueError("LUFS ölçümü alınamadı. Dosya sessiz veya ölçüm için uygun olmayabilir.")

    # 4x oversampling true-peak tahmini; uzun kayıtları düşük RAM ile işlemek için bloklar.
    peak_linear = 0.0
    frame_count = len(audio)
    chunk = max(65536, int(rate * 8))
    overlap = 256
    for start in range(0, frame_count, chunk):
        lo = max(0, start - overlap)
        hi = min(frame_count, start + chunk + overlap)
        seg = audio[lo:hi]
        over = resample_poly(seg, 4, 1, axis=0)
        peak_linear = max(peak_linear, float(np.max(np.abs(over))) if over.size else 0.0)
    input_tp = 20 * math.log10(peak_linear) if peak_linear > 0 else -120.0
    requested_gain = float(target_lufs) - measured
    peak_limited_gain = float(target_true_peak_db) - input_tp
    applied_gain = min(requested_gain, peak_limited_gain)
    factor = 10 ** (applied_gain / 20.0)
    output_audio = audio * factor
    output_audio = np.clip(output_audio, -1.0, 1.0)
    import os
    import tempfile

    out.parent.mkdir(parents=True, exist_ok=True)
    temp_handle = tempfile.NamedTemporaryFile(delete=False, suffix=".wav", dir=str(out.parent))
    temp_path = Path(temp_handle.name)
    temp_handle.close()
    try:
        sf.write(str(temp_path), output_audio, int(rate), format="WAV", subtype="PCM_24")
        verified_audio, verified_rate = sf.read(str(temp_path), dtype="float32", always_2d=True)
        if verified_rate != int(rate) or verified_audio.shape != output_audio.shape:
            raise RuntimeError("Çıktı WAV doğrulaması başarısız: kanal veya örnekleme bilgisi değişti.")
        verified_meter = pyln.Meter(int(verified_rate), filter_class="DeMan")
        verified_lufs = float(verified_meter.integrated_loudness(verified_audio))
        try:
            output_lra = float(verified_meter.loudness_range(verified_audio))
        except (ValueError, RuntimeError):
            output_lra = float("nan")
        if not math.isfinite(output_lra):
            output_lra = None
        if not math.isfinite(verified_lufs):
            raise RuntimeError("Yazılan dosyanın LUFS ölçümü doğrulanamadı.")
        verified_peak = 0.0
        for start in range(0, len(verified_audio), chunk):
            lo = max(0, start - overlap)
            hi = min(len(verified_audio), start + chunk + overlap)
            oversampled = resample_poly(verified_audio[lo:hi], 4, 1, axis=0)
            if oversampled.size:
                verified_peak = max(verified_peak, float(np.max(np.abs(oversampled))))
        verified_tp = 20 * math.log10(verified_peak) if verified_peak > 0 else -120.0
        if verified_tp > float(target_true_peak_db) + 0.15:
            raise RuntimeError("Yazılan dosya true-peak tavanını aşıyor; çıktı yayımlanmadı.")
        os.replace(str(temp_path), str(out))
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass

    actual_peak = float(np.max(np.abs(verified_audio))) if verified_audio.size else 0.0
    actual_sample_peak = 20 * math.log10(actual_peak) if actual_peak > 0 else -120.0
    achieved = verified_lufs
    return {
        "source": str(src), "output": str(out), "sample_rate_hz": int(rate),
        "channels": int(audio.shape[1]), "input_lufs_i": measured,
        "input_lra_lu": input_lra, "output_lra_lu": output_lra,
        "target_lufs_i": float(target_lufs), "achieved_lufs_i": achieved,
        "achieved_lufs_i_estimate": achieved,
        "input_true_peak_estimate_dbtp": input_tp,
        "target_true_peak_dbtp": float(target_true_peak_db),
        "applied_gain_db": applied_gain,
        "target_lufs_limited_by_peak": applied_gain < requested_gain - 1e-6,
        "output_sample_peak_dbfs": actual_sample_peak,
        "output_true_peak_dbtp_verified": verified_tp,
        "output_subtype": "PCM_24",
        "notes": [
            "LUFS integrated ve LRA ölçümleri pyloudnorm DeMan K-weighting filtresiyle hesaplandı.",
            "True-peak değeri 4x oversampling ile tahmin edilmiştir; sertifikalı teslim ölçer yerine geçmez.",
            "Limiter uygulanmaz; true-peak tavanı hedef loudness'e erişimi kısıtlayabilir.",
            "Çıktıyı tekrar ölçüp kritik bölümleri dinleyin. Kaynak dosya değiştirilmez."
        ]
    }

