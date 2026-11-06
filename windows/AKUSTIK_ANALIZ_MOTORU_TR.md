# Stagepulse Acoustic Engine

Stagepulse Ses Merkezi için bağımsız geliştirilen, NumPy tabanlı akustik ölçüm DSP çekirdeği.

## İlk sürüm kapsamı
- İki kanallı Welch H1 Transfer Function
- Magnitude (dB), Phase (derece), Magnitude-Squared Coherence
- Normalize çapraz korelasyonla Delay Finder
- H1 üzerinden Impulse Response ve ETC

## Kullanım
```python
from core.acoustic_engine import transfer_function, delay_finder, impulse_response

tf = transfer_function(reference_samples, measurement_samples, 48000)
delay = delay_finder(reference_samples, measurement_samples, 48000)
ir = impulse_response(reference_samples, measurement_samples, 48000)
```

## Ölçüm şartları ve sınırlar
- Referans giriş, ölçüm çıkışıdır. H1 = S_yx / S_xx.
- İki kanal eşzamanlı ve aynı örnekleme hızında yakalanmalıdır.
- Referans ve ölçüm sinyalleri aynı saat kaynağına bağlı olmalıdır.
- Coherence, ölçümün frekans başına güvenilirliğine dair göstergedir; tek başına doğruluk sertifikası değildir.
- Bu modül dB SPL üretmez. dB SPL için ölçüm mikrofonu/ses kartı kalibrasyonu ve ayrı A/C/Z ağırlıklandırma ile zaman ağırlıklandırma katmanı gerekir.
- Bu ilk sürüm saha cihazı üzerinde doğrulanmış bir ürün olarak sunulamaz; testler sentetik sinyal doğrulamasıdır.
- Kaynak kodu Stagepulse tarafından bağımsız yazılmıştır. SoundDocs/AcoustIQ kaynak kodu veya arayüzü bu modüle aktarılmamıştır.

## Test
Windows klasöründe:
```powershell
python -m pytest tests/test_acoustic_engine.py -q
```
