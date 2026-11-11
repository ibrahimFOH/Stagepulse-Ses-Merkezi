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


def _true_peak_linear(audio: Any, sample_rate: int) -> tuple[float, str]:
    """ITU-R BS.1770-5 Annex 2 oversampled inter-sample peak estimate."""
    import numpy as np
    from scipy.signal import resample_poly, upfirdn

    x = np.asarray(audio, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    if x.size == 0 or not np.all(np.isfinite(x)):
        raise ValueError("True Peak girdisi boş veya geçersiz.")
    rate = int(sample_rate)
    if rate <= 0:
        raise ValueError("True Peak örnekleme hızı geçersiz.")

    if rate == 48000:
        # ITU-R BS.1770-5 Annex 2, Table: 48-tap / four-phase FIR interpolator.
        phases = (
            (0.0017089843750, 0.0109863281250, -0.0196533203125, 0.0332031250,
             -0.0594482421875, 0.1373291015625, 0.9721679687500, -0.1022949218750,
             0.0476074218750, -0.0266113281250, 0.0148925781250, -0.0083007812500),
            (-0.0291748046875, 0.0292968750, -0.0517578125, 0.0891113281250,
             -0.16650390625, 0.4650878906250, 0.7797851562500, -0.2003173828125,
             0.1015625000, -0.0582275390625, 0.0330810546875, -0.0189208984375),
            (-0.0189208984375, 0.0330810546875, -0.0582275390625, 0.1015625000,
             -0.2003173828125, 0.7797851562500, 0.4650878906250, -0.16650390625,
             0.0891113281250, -0.0517578125, 0.0292968750, -0.0291748046875),
            (-0.0083007812500, 0.0148925781250, -0.0266113281250, 0.0476074218750,
             -0.1022949218750, 0.9721679687500, 0.1373291015625, -0.0594482421875,
             0.0332031250, -0.0196533203125, 0.0109863281250, 0.0017089843750),
        )
        taps = np.asarray([phases[p][i] for i in range(12) for p in range(4)], dtype=np.float64)
        oversampled = upfirdn(taps, x, up=4, axis=0)
        method = "ITU-R BS.1770-5 Annex 2 · 48 kHz · 4-phase 48-tap FIR"
    else:
        # Retain at least 192 kHz analysis rate; a high-quality Kaiser FIR is used
        # where the Recommendation's published 48 kHz coefficient set does not apply.
        factor = max(1, int(math.ceil(192000.0 / rate)))
        if factor == 1:
            oversampled = x
            method = f"BS.1770-5 Annex 2 yaklaşımı · {rate} Hz native-rate"
        else:
            oversampled = resample_poly(x, factor, 1, axis=0, window=("kaiser", 8.6))
            method = f"BS.1770-5 Annex 2 yaklaşımı · Kaiser FIR {factor}x"
    interpolated_peak = float(np.max(np.abs(oversampled))) if oversampled.size else 0.0
    # Interpolation must never report a peak below an actual input sample.
    sample_peak = float(np.max(np.abs(x))) if x.size else 0.0
    return max(interpolated_peak, sample_peak), method


def _measure_true_peak(audio: Any, sample_rate: int, chunk_seconds: float = 8.0) -> tuple[float, str]:
    """Measure a long file in overlapping chunks without losing inter-sample peaks."""
    import numpy as np

    x = np.asarray(audio, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    chunk = max(1, int(round(int(sample_rate) * float(chunk_seconds))))
    overlap = 64
    peak = 0.0
    method = ""
    for start in range(0, len(x), chunk):
        lo = max(0, start - overlap)
        hi = min(len(x), start + chunk + overlap)
        value, method = _true_peak_linear(x[lo:hi], int(sample_rate))
        peak = max(peak, value)
    return peak, method


def _loudness_window_maxima(audio: Any, sample_rate: int, meter: Any) -> tuple[float | None, float | None]:
    """Return ungated 400 ms Momentary and 3 s Short-term maxima."""
    import numpy as np

    x = np.asarray(audio, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    filtered = x.copy()
    filters = getattr(meter, "_filters", None)
    if not filters:
        return None, None
    # pyloudnorm 0.2 stores its two K-weighting stages in a dict.
    filter_stages = list(filters.values()) if isinstance(filters, dict) else list(filters)
    for filt in filter_stages:
        for channel in range(filtered.shape[1]):
            filtered[:, channel] = filt.apply_filter(filtered[:, channel])
    # BS.1770-5 Annex 1 channel order: L, R, C, Ls, Rs. No LFE channel.
    channel_gains = np.asarray((1.0, 1.0, 1.0, 1.41, 1.41), dtype=np.float64)
    weights = channel_gains[:filtered.shape[1]]
    weighted_power = np.sum(np.square(filtered) * weights[None, :], axis=1)
    step = max(1, int(round(sample_rate * 0.1)))

    def maximum(window_seconds: float) -> float | None:
        width = int(round(sample_rate * window_seconds))
        if width <= 0 or len(weighted_power) < width:
            return None
        values = []
        for start in range(0, len(weighted_power) - width + 1, step):
            power = float(np.mean(weighted_power[start:start + width]))
            if power > 0 and math.isfinite(power):
                values.append(-0.691 + 10.0 * math.log10(power))
        return max(values) if values else None

    return maximum(0.4), maximum(3.0)


def validate_ebu_test_set(folder: str | Path, reference_csv_text: str = "",
                          tolerance_lu: float = 0.2) -> dict[str, Any]:
    """Measure extracted EBU WAV sequences and compare optional operator-supplied references.

    CSV columns: filename, integrated_lufs, lra_lu, momentary_max_lufs,
    short_term_max_lufs, true_peak_dbtp. Missing references are never marked PASS.
    """
    import csv
    import io
    import numpy as np
    import soundfile as sf
    import pyloudnorm as pyln

    root = Path(folder).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError("EBU test klasörü bulunamadı.")
    files = sorted(p for p in root.rglob("*.wav") if p.is_file())
    if not files:
        raise ValueError("Seçilen klasörde WAV test dosyası bulunamadı.")
    if len(files) > 500:
        raise ValueError("Tek çalıştırmada en fazla 500 WAV test dosyası işlenebilir.")
    tolerance = float(tolerance_lu)
    if not math.isfinite(tolerance) or not 0.01 <= tolerance <= 2.0:
        raise ValueError("LU toleransı 0.01 ile 2.0 arasında olmalı.")

    references: dict[str, dict[str, str]] = {}
    if reference_csv_text.strip():
        reader = csv.DictReader(io.StringIO(reference_csv_text.lstrip("\ufeff")))
        required = {"filename"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise ValueError("Referans CSV başlığı en az filename içermeli.")
        for row in reader:
            key = Path(str(row.get("filename", "")).strip()).name.casefold()
            if key:
                references[key] = row

    rows = []
    for path in files:
        audio, rate = sf.read(str(path), dtype="float64", always_2d=True)
        if audio.size == 0 or not np.all(np.isfinite(audio)):
            rows.append({"filename": path.name, "status": "FAIL", "error": "Boş veya geçersiz ses verisi"})
            continue
        if audio.shape[1] > 5:
            rows.append({"filename": path.name, "status": "UNSUPPORTED", "error": "BS.1770-5 Annex 1 için en fazla 5 ana kanal (L/R/C/Ls/Rs), LFE ayrı desteklenmez"})
            continue
        meter = pyln.Meter(int(rate), filter_class="DeMan")
        try:
            integrated = float(meter.integrated_loudness(audio))
            if not math.isfinite(integrated):
                raise ValueError("Integrated loudness sonucu sonlu değil.")
        except Exception as exc:
            rows.append({"filename": path.name, "status": "FAIL", "error": str(exc)})
            continue
        try:
            lra = float(meter.loudness_range(audio))
            if not math.isfinite(lra):
                lra = None
        except (ValueError, RuntimeError):
            # Very short EBU sequences may not contain enough valid 3 s blocks for LRA.
            lra = None
        momentary, short_term = _loudness_window_maxima(audio, int(rate), meter)
        peak_linear, peak_method = _measure_true_peak(audio, int(rate))
        true_peak = 20.0 * math.log10(peak_linear) if peak_linear > 0 else -120.0
        measured = {
            "integrated_lufs": integrated, "lra_lu": lra,
            "momentary_max_lufs": momentary, "short_term_max_lufs": short_term,
            "true_peak_dbtp": true_peak,
        }
        ref = references.get(path.name.casefold())
        comparisons = []
        if ref:
            for key, value in measured.items():
                raw = str(ref.get(key, "") or "").strip()
                if not raw or value is None:
                    continue
                try:
                    expected = float(raw)
                except ValueError:
                    continue
                allowed = max(tolerance, 0.3) if key == "true_peak_dbtp" else tolerance
                delta = float(value) - expected
                comparisons.append({"metric": key, "reference": expected, "measured": float(value),
                                    "difference": delta, "tolerance": allowed,
                                    "pass": abs(delta) <= allowed})
        expected_metrics = {key for key, value in measured.items() if value is not None}
        compared_metrics = {item["metric"] for item in comparisons}
        if comparisons and not all(item["pass"] for item in comparisons):
            status = "FAIL"
        elif comparisons and compared_metrics >= expected_metrics:
            status = "PASS"
        elif comparisons:
            status = "PARTIAL_REFERENCE"
        else:
            status = "REFERENCE_REQUIRED"
        rows.append({
            "filename": path.name, "sample_rate_hz": int(rate), "channels": int(audio.shape[1]),
            "duration_seconds": len(audio) / int(rate), **measured,
            "true_peak_method": peak_method, "comparisons": comparisons, "status": status,
        })
    counts = {key: sum(1 for row in rows if row["status"] == key)
              for key in ("PASS", "FAIL", "PARTIAL_REFERENCE", "REFERENCE_REQUIRED", "UNSUPPORTED")}
    return {
        "ok": True, "standard_basis": "ITU-R BS.1770-5 / EBU Tech 3341 / EBU Tech 3342",
        "folder": root.name, "files_total": len(rows), "counts": counts, "tolerance_lu": tolerance,
        "reference_csv_loaded": bool(references), "results": rows,
        "scope_note": "EBU Loudness Test Set WAV dosyalarını ölçer. Referans CSV verilmeden hiçbir dosya PASS sayılmaz. Bu otomatik rapor resmî sertifika veya EBU onayı değildir.",
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

    # BS.1770-5 Annex 2 true-peak ölçümü; 48 kHz için yayımlanmış 4-fazlı FIR katsayıları.
    peak_linear, true_peak_method = _measure_true_peak(audio, int(rate))
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
        verified_peak, verified_tp_method = _measure_true_peak(verified_audio, int(verified_rate))
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
        "true_peak_method": true_peak_method,
        "output_subtype": "PCM_24",
        "notes": [
            "LUFS integrated ve LRA ölçümleri pyloudnorm DeMan K-weighting filtresiyle hesaplandı.",
            f"True Peak yöntemi: {true_peak_method}; referans testleri tamamlanmadan sertifikalı ölçüm iddiası değildir.",
            "Limiter uygulanmaz; true-peak tavanı hedef loudness'e erişimi kısıtlayabilir.",
            "Çıktıyı tekrar ölçüp kritik bölümleri dinleyin. Kaynak dosya değiştirilmez."
        ]
    }

