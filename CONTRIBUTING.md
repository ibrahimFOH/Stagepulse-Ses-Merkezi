# Katkı ve Kod İnceleme Süreci

Stagepulse Ses Merkezi özel mülkiyetli bir projedir. Depoya erişim, katkı yapma veya kodu kullanma lisansı vermez. Harici katkılar yalnızca Stagepulse bakım sorumlusunun önceden verdiği yazılı izinle kabul edilir.

## Değişiklik önerme

1. Hata veya geliştirme önerisini GitHub Issues üzerinden açıklayın. Güvenlik açıklarını herkese açık issue yerine [SECURITY.md](SECURITY.md) süreciyle bildirin.
2. Yazılı yetki verilmiş katkıcılar değişikliklerini ayrı bir Pull Request (PR) olarak sunar. Doğrudan `main` dalına yazma, inceleme sürecinin yerine geçmez.
3. PR açıklamasında amaç, etkilenen platformlar (Windows/Android), kullanıcı etkisi, geriye dönük uyumluluk ve riskler belirtilmelidir.
4. Büyük özellikler için otomatik test veya doğrulama eklenmelidir. Hata düzeltmelerine mümkün olduğunda regresyon testi eklenir.
5. Bağımlılık, izin, kimlik doğrulama, ağ erişimi, dosya işleme ve kullanıcı verisi değişiklikleri özellikle işaretlenmelidir.

## Bağımsız inceleme şartı

- Değişikliğin yazarı kendi PR'ını onaylayamaz.
- Yayınlanacak her güvenlik açısından önemli değişiklik ve her sürüm adayı, yazardan farklı bir kişi tarafından incelenmelidir.
- İnceleyici; doğruluğu, güvenlik sınırlarını, hata durumlarını, veri doğrulamayı, gizli bilgi sızıntısını, bağımlılık etkisini, test kapsamını ve kullanıcı dokümantasyonunu kontrol eder.
- İnceleme sonucu GitHub PR incelemesi olarak kaydedilir: **Approved**, **Request changes** veya gerekçeli **Commented**.
- Açık kritik/yüksek önem bulgusu, başarısız zorunlu test veya çözümlenmemiş inceleme yorumu varken değişiklik kararlı sürüme alınmaz.
- İnceleyici bulunmuyorsa bağımsız inceleme yapılmış gibi işaretlenmez; değişiklik yayın adayı olarak bekletilir.

## Yerel doğrulama

Windows Python testleri:

```powershell
cd windows
python -m pip install -r requirements.txt
python -m pytest tests -q
```

JavaScript regresyon testleri:

```powershell
node --check windows/ui/bilingual_terms.js
node --check windows/ui/app.js
node --check windows/ui/first_party_tools.js
node windows/tests/test_first_party_tools.js
```

Android kalite kontrolleri ve paket doğrulaması GitHub Actions üzerinden yürütülür. WAV ayrıştırıcısı için fuzz testleri `.github/workflows/fuzz.yml` ile çalıştırılır. Tüm zorunlu CI işleri yeşil olmadan değişiklik hazır kabul edilmez.

## Kodlama ve teslim

- Mevcut mimariyi ve Türkçe arayüz terminolojisini koruyun; teknik terimleri gerektiğinde İngilizce karşılığıyla verin.
- Sürüm numaralarını tek tek elle değiştirmek yerine mevcut sürüm doğrulama akışını kullanın.
- Gizli anahtar, token, kişisel veri, lisans dosyası veya imzalama sertifikası commit etmeyin.
- Kaynak kodu, PDF, APK, EXE ve MSIX gibi üretilen dosyaların sürüm/kimlik tutarlılığını doğrulayın.
- Her PR küçük ve tek amaçlı olmalıdır.
