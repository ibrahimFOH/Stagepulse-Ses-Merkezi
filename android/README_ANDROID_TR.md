# Stagepulse Ses Mühendisliği Merkezi 3.9.0 · Android

**Uygulama kimliği:** `com.stagepulse.sesmerkezi`  
**Sürüm kodu:** `30900`  
**Minimum Android:** API 26  
**Hedef Android:** API 35  
**Derleme:** JDK 17 · Gradle 8.13 · Android Gradle Plugin 8.13.2 · Android SDK 35

## Proje yapısı

- `app/src/main/java/com/stagepulse/sesmerkezi/MainActivity.kt`: WebView, Android-JavaScript köprüsü, hesap/lisans oturumu, Groq bağlantısı, dosya dışa aktarma ve uygulama güncelleme doğrulaması.
- `app/src/main/assets/ui/`: Türkçe arayüz, CSS, JavaScript araçları ve mobil/tablet düzeni.
- `app/src/main/assets/docs/`: Uygulama içi 12 ders kılavuzu.
- `app/src/main/assets/egitim_paketleri/`: Öğrenciye sunulan 13 PDF.
- `scripts/verify_assets.py`: HTML/CSS kaynakları, PDF kataloğu, Kotlin izin listesi ve sürüm eşleşmesi denetimi.

## Android'de bulunan özellikler

- WebView içinde yerel paketlenmiş arayüz; çevrimdışı eğitim belgeleri ve araçlar.
- Telefon ve tablet boyutlarına göre uyarlanan gezinme ve çalışma alanı.
- WebAudio tabanlı RTA; giriş aygıtı seçimi, FFT ve 1/3 oktav/oktav analizi.
- 94/114 dB SPL, 1 kHz fiziksel akustik kalibratörle oturumluk RMS SPL düzeltmesi. Mikrofon frekans cevabı düzeltmesi veya IEC 61260 sınıf 1/2 uygunluğu iddia edilmez.
- Canlı stereo H1 Transfer Function: aynı USB ses kartının CH0 referans ve CH1 ölçüm kanallarından magnitude, phase ve coherence. Mono girişler reddedilir; iki bağımsız kanal gerekir.
- Telefon/tablet arayüzünde FFT 8192/16384/32768, ortalama 4/8/16/32, giriş aygıtı seçimi ve akış kesilmesi uyarıları.
- Android dosya seçicisi üzerinden ses dosyası alma ve desteklenen WAV biçimleri için peak/RMS analizi.
- Saha ve sistem mühendisliği araçları: ölçekli sahne/AV planı, Midas M32/Behringer X32 .scn patch raporu, kablosuz kanal planı, 70/100 V hat hesabı, oda SPL haritası ve hoparlör/DSP ön hesabı.
- Dalga/Faz/Gecikme Laboratuvarı: frekans, dalga boyu, periyot, iki kaynak girişimi, faz ve dB SPL formülleri; isteğe bağlı canlı mikrofon gecikme deneyi 0–5.000 ms. Mikrofon izlemesi varsayılan olarak sessizdir ve kamera açılmaz.
- Yaklaşık loudness düzeyleme ve stereo PCM WAV dışa aktarma. EBU/ITU sertifikalı ölçüm veya profesyonel limiter değildir.
- Supabase Auth oturum açma/kayıt, lisans etkinleştirme, sahip lisans yönetimi ve öğretmen/öğrenci ilerleme uçları.
- Oturum belirteçleri Android Keystore AES-GCM ile şifrelenmiş uygulama depolamasında tutulur.
- Android AI bağlantısı yalnızca Groq kullanır. İstem göndermek için kullanıcı onayı, etkin lisans veya sunucu tarafından doğrulanmış sahip rolü gerekir. API anahtarı oturum belleği dışında saklanmaz.
- Güncelleme bildirimi, sürüm kodu, güvenilir indirme adresi ve APK SHA-256 kontrolü yapar. İndirilen paket kontrol başarısızsa kurulmaz.

## AI sağlayıcısı sınırı

Android uygulamasının etkin sağlayıcısı GroqCloud'dur. Ollama yalnızca Windows bilgisayarındaki yerel servis üzerinden çalışır; telefondaki `127.0.0.1` Windows bilgisayarını göstermez. Gemini, OpenAI, Grok veya özel endpoint'ler Android arayüzünde kullanılabilir sağlayıcı olarak sunulmaz.

## Derleme ve test

Depo kökünden kaynak denetimi:

```bash
python android/scripts/verify_assets.py
```

JavaScript sözdizimi:

```bash
find android/app/src/main/assets/ui -type f -name '*.js' -print0 | while IFS= read -r -d '' file; do node --check "$file" || exit 1; done
```

Birim testleri ve debug APK:

```bash
gradle -p android --no-daemon clean testDebugUnitTest assembleDebug
```

APK yolu:

`android/app/build/outputs/apk/debug/app-debug.apk`

Debug APK geliştirme/test paketidir. 3.9.0 yayın manifestinde kalıcı Stagepulse keystore ile imzalanmış APK ve SHA-256 bilgileri bulunur. Bu kaynak doküman, yeni değişikliklerin release APK olarak derlendiğini veya fiziksel cihaz kabul testlerinin tamamlandığını tek başına kanıtlamaz.

## Gerçek cihaz kabul listesi

1. Android 8.0 ve üzeri telefonda (API 26+) temiz kurulum ve yükseltme.
2. Ekran döndürme, sistem çubuğu güvenli alanları, telefon ve tablet görünümü.
3. Mikrofon izni, RTA akışı ve ses girişini durdurma.
4. WAV dosyası seçme, geçersiz biçim reddi ve analiz sonucu.
5. On üç PDF'nin harici görüntüleyicide açılması.
6. Supabase giriş, çıkış, oturum geri yükleme, lisans etkinleştirme ve rol denetimi.
7. Groq bağlantı testi, yanlış anahtar/yanlış model ve onay verilmemiş istek reddi.
8. Güncelleme bildirimi, SHA-256 hatası ve imza uyumsuzluğu senaryoları.

Otomatik derleme veya statik denetim, fiziksel cihaz kabul testinin yerine geçmez.
