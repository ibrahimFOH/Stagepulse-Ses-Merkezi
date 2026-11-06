# -*- coding: utf-8 -*-
"""pywebview köprüsü için sınırlı ve doğrulamalı akustik analiz API'si."""
from __future__ import annotations

import json
from typing import Any


class AcousticAnalysisApi:
    @staticmethod
    def _parse_audio_json(raw: Any, label: str) -> list[float]:
        if not isinstance(raw, str) or len(raw.encode("utf-8")) > 32 * 1024 * 1024:
            raise ValueError(f"{label}: JSON metni geçersiz veya 32 MB sınırını aşıyor.")
        try:
            values = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{label}: geçerli JSON ses örnek dizisi gerekli.") from exc
        if not isinstance(values, list) or len(values) < 32 or len(values) > 2_000_000:
            raise ValueError(f"{label}: 32–2.000.000 arası örnek içeren dizi gerekli.")
        return values

    def analyze_stereo_wav(
        self, file_path: Any, segment_size: Any = 8192, overlap: Any = 0.5,
    ) -> dict[str, Any]:
        """Analyze a user-selected stereo WAV without serializing audio through WebView."""
        from pathlib import Path
        import soundfile as sf

        selected = getattr(self, "_selected_wav_path", None)
        self._selected_wav_path = None
        if not selected:
            raise ValueError("WAV dosyasını uygulamanın dosya seçicisiyle seçmelisin.")
        path = Path(str(file_path)).expanduser().resolve()
        if path != Path(str(selected)).resolve():
            raise ValueError("Yalnızca uygulamanın seçtiği WAV dosyası analiz edilebilir.")
        if path.suffix.lower() != ".wav" or not path.is_file():
            raise ValueError("Geçerli bir WAV dosyası seçilmelidir.")
        info = sf.info(str(path))
        if info.channels != 2:
            raise ValueError("Stereo WAV gerekli: sol kanal referans, sağ kanal ölçüm olmalı.")
        if info.samplerate < 8000 or info.samplerate > 384000:
            raise ValueError("Örnekleme hızı 8.000–384.000 Hz aralığında olmalı.")
        if info.frames < 256 or info.frames > 2_000_000:
            raise ValueError("Kayıt 256–2.000.000 örnek aralığında olmalı (RAM koruması).")
        audio, sample_rate = sf.read(str(path), dtype="float64", always_2d=True)
        if audio.shape[1] != 2:
            raise ValueError("Stereo kanal verisi okunamadı.")
        reference, measurement = audio[:, 0], audio[:, 1]
        size = int(segment_size)
        ov = float(overlap)
        from core.acoustic_engine import transfer_function, delay_finder, impulse_response
        tf = transfer_function(reference, measurement, sample_rate, size, ov)
        delay = delay_finder(reference, measurement, sample_rate, 500.0)
        ir = impulse_response(reference, measurement, sample_rate, size, ov)
        return {
            "ok": True,
            "file_name": path.name,
            "sample_rate": sample_rate,
            "duration_seconds": len(reference) / sample_rate,
            "channels": 2,
            "transfer_function": tf,
            "delay": delay,
            "impulse_response": ir,
            "calibrated_spl": False,
        }

    def analyze_transfer_function_json(
        self, reference_json: str, measurement_json: str,
        sample_rate: Any, segment_size: Any = 8192, overlap: Any = 0.5,
    ) -> dict[str, Any]:
        reference = self._parse_audio_json(reference_json, "Referans")
        measurement = self._parse_audio_json(measurement_json, "Ölçüm")
        from core.acoustic_engine import transfer_function
        result = transfer_function(reference, measurement, sample_rate, int(segment_size), float(overlap))
        return result

    def analyze_delay_json(
        self, reference_json: str, measurement_json: str,
        sample_rate: Any, max_delay_ms: Any = 500.0,
    ) -> dict[str, Any]:
        reference = self._parse_audio_json(reference_json, "Referans")
        measurement = self._parse_audio_json(measurement_json, "Ölçüm")
        from core.acoustic_engine import delay_finder
        return delay_finder(reference, measurement, sample_rate, float(max_delay_ms))

    def analyze_impulse_response_json(
        self, reference_json: str, measurement_json: str,
        sample_rate: Any, segment_size: Any = 8192, overlap: Any = 0.5,
    ) -> dict[str, Any]:
        reference = self._parse_audio_json(reference_json, "Referans")
        measurement = self._parse_audio_json(measurement_json, "Ölçüm")
        from core.acoustic_engine import impulse_response
        return impulse_response(reference, measurement, sample_rate, int(segment_size), float(overlap))
