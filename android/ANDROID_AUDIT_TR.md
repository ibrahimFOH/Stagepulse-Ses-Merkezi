# Android kaynak ve paket denetim raporu

**Kaynak sürümü:** 3.7.4  
**Sürüm kodu:** 30704  
**Son kaynak incelemesi:** 4 Kasım 2026

## Doğrulanan kaynak yapısı

- WebView, `WebViewAssetLoader` ile `https://appassets.androidplatform.net/assets/ui/index.html` adresinden yerel paket içeriğini açar.
- WebView dosya erişimi kapalıdır; düz HTTP karışık içerik kabul edilmez.
- Arayüz HTML/CSS/JavaScript ve gerekli görseller Android assets içine paketlenir.
- Telefon görünümü mobil menü ve tek sütun akışına; tablet görünümü sürekli gezinme rayı ve kullanılabilir yatay alana göre düzenlenir. 601–800 piksel aralığında telefon/tablet medya sorgularının çakışması giderilmiştir.
- 13 öğrenci PDF'i ve 12 uygulama içi ders kılavuzu paket kaynaklarında mevcuttur.
- Android Kotlin köprüsünde öğrenci PDF listesi, paketlenen PDF listesiyle eşleşecek şekilde doğrulanır.
- WebAudio RTA göreli dBFS görünümü sağlar; kalibre edilmiş SPL, faz veya transfer-function ölçümü değildir.
- Android dosya seçicisi ve WAV peak/RMS analiz akışı bulunur.
- Yaklaşık loudness düzeyleme ve stereo 16-bit PCM WAV dışa aktarma bulunur; sertifikalı LUFS/true-peak uygunluk ölçümü veya limiter iddiası yoktur.
- Supabase Auth, oturum yenileme, cihaz kimliği, lisans ve öğretmen/öğrenci uçları Kotlin köprüsünden çağrılır.
- Oturum belirteçleri Android Keystore AES-GCM anahtarıyla şifrelenir. Servis rolü anahtarı Android paketine eklenmez.
- Güncelleme indirme öncesinde sürüm/URL denetimi, indirme boyutu sınırı ve SHA-256 kontrolü yapılır.

## Sağlayıcı ve platform ayrımı

- Android AI sağlayıcısı yalnızca GroqCloud'dur. İstek için açık kullanıcı onayı ve etkin lisans veya doğrulanmış sahip rolü gerekir.
- Android tarafında Ollama reddedilir. Ollama yalnızca Windows uygulamasında yerel servis olarak çalışır.
- Gemini, OpenAI, Grok ve özel OpenAI uyumlu endpoint'ler Android uygulamasında etkin sağlayıcı değildir.
- Windows uygulaması yerel Ollama ve isteğe bağlı Groq yedeği kullanır.

## Ekran uyumluluğu

- Telefon: tek sütun sayfa, açılır yan menü, büyük dokunma hedefleri, dikey kaydırma.
- Tablet: sürekli yan gezinme, dar tabletlerde kompakt gezinme ve uygun olduğunda tek sütun içerik.
- CSS medya sorguları statik olarak kontrol edildi; açma/kapama süslü parantezleri dengeli.
- Gerçek cihazlarda görünüm, ekran döndürme, klavye açılması, sistem çubukları ve farklı yoğunluklar ayrıca test edilmelidir.

## Kaynak denetimi

`android/scripts/verify_assets.py` aşağıdakileri doğrular:

- Zorunlu Android arayüz ve Kotlin dosyaları.
- HTML ve CSS yerel dosya referansları.
- Eğitim kataloğundaki 12 belge dosyası.
- Öğrenci paketindeki 13 PDF ve dosya boyutları.
- Kotlin PDF izin listesi ile paket PDF listesinin aynı olması.
- Android `versionName` ve `versionCode` tutarlılığı.
- Android HTTPS yerel varlık kaynağı ve mobil/tablet kesme noktaları.

Node.js `--check` tüm Android JavaScript dosyalarını, Gradle iş akışı da Android kaynak derlemesini denetler. `verify_assets.py` ders kataloğu yollarının paket dışına taşmasını da reddeder.

## Henüz yeşil olarak doğrulanmamış işler

GitHub Actions geçmişindeki son Android işi runner atanmadan tamamlanmıştır: `runner_id=0`, `runner_name=""`, `steps=[]`. Bu nedenle kaynak testi veya Gradle derlemesi çalışmış sayılmaz. Android kalite, imzalı test ve CodeQL iş akışları runner sorunu nedeniyle manuel başlatmaya alınmıştır. Tekrarlanan APK derleme iş akışı kaldırılmıştır.

Bu denetim kaynak ağacındaki dosya ve referans kontrollerini kapsar; başarılı APK derlemesi, APK imza doğrulaması, cihaz kurulumu veya gerçek mikrofon/AI/lisans testinin yerine geçmez.

## Yayın öncesi zorunlu adımlar

1. GitHub Actions runner tahsis sorunu giderilmeli.
2. `android-quality.yml` gerçek runner üzerinde yeşil tamamlanmalı. Yinelenen `build-android-apk.yml` iş akışı kaldırıldı.
3. Kalıcı Stagepulse Android keystore ile Release APK üretilmeli; geçici CI anahtarı dağıtımda kullanılmamalı.
4. APK sertifikası ve SHA-256 doğrulanmalı.
5. Android telefonda ve tablette kabul listesi uygulanmalı.
6. Ortak yayın öncesinde Windows, kurucu ve Android sürümleri eşleştirilmeli. Şu an Windows 3.7.1, Android 3.7.4 olduğu için ortak yayın kontrolü geçmez.
