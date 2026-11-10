# Stagepulse Ses Merkezi

Stagepulse Ses Merkezi; Windows masaüstü uygulaması ve Android uygulamasından oluşan Türkçe ses mühendisliği platformudur. Yönetici hesabı ve yetkileri ana uygulama içindeki giriş/oturum akışıyla yönetilir. Son kullanıcı paketleri ayrı Stagepulse-Releases deposunda üretilir.

## 3.9.8 SPL/RTA ölçüm ve mikrofon entegrasyonları

- Windows ve Android canlı RTA ekranlarında 1/1, 1/3, 1/6, 1/12, 1/24 ve 1/48 oktav bant çözünürlükleri.
- Android mikrofon akışında PCM tabanlı FFT; bant güçleri dBFS RMS olarak hesaplanır.
- Ölçüm mikrofonu frekans düzeltmesi CSV profiliyle RTA spektrumuna uygulanabilir.
- Windows stereo WAV analizine A/C/Z ağırlıklı Leq, Fast/Slow maksimum, Peak ve L10/L50/L90 istatistikleri eklendi.
- Mevcut yönetici panelinden gelişmiş RTA ve mikrofon correction özellikleri merkezi olarak açılıp kapatılabilir; ayarlar Supabase üzerinde tutulur.
- Yönetici panelinde mikrofon/kalibratör bilgileri ve saha kontrol kaydı bulunur. Operatör saha kaydı IEC uygunluk sertifikası değildir.

## 3.9.7 önceki entegrasyonlar

- Windows ve Android'e OSC/UDP gönderimi eklendi; M32/X32 için varsayılan UDP portu 10023.
- İki platformda standart MIDI Type 0 dosyası oluşturulabilir.
- Arşivdeki SPL/FFT, elektrik/kablo ve RF araçları mevcut daha gelişmiş Stagepulse araçlarıyla çakıştığı veya güvenilir ölçüm üretmediği için tekrar eklenmedi.

## 3.9.7 son düzeltmeler

- Android Compressor ve Gate kulak eğitimi A/B dinleme, rastgele sınav ve stilleriyle doğrulandı.
- SPL 2D/3D kaynak seçimi ve sürükleme koordinatları düzeltildi.
- Android kalite denetimi Compressor/Gate arayüz bileşenlerini ve sürüm eşleşmesini kontrol eder.

## 3.9.5 arayüz ve SPL iyileştirmeleri

- Öğrenci ekranında görünür FULL PAKET satın alma/lisans kısayolu.
- Destek ve iletişim düğmeleri doğrudan Stagepulse WhatsApp hattını açar.
- SPL 2D/3D haritası seçilen PA, sub ve monitör kaynaklarının konum/seviye/yön bilgisiyle canlı güncellenir.
- SPL ekipmanları kategoriye göre listelenir; eklenebilir, seçilebilir, düzenlenebilir ve 2D haritada sürüklenebilir.
- Compressor ve Gate kulak eğitimi A/B dinleme ve rastgele sınavları korunmuştur.

## Platform sürümleri

| Bileşen | Kaynak sürümü | Sürümün yönetildiği yer |
|---|---:|---|
| Windows Ses Merkezi | 3.9.8 | windows/Merkez.py ve windows/EXE_OLUSTUR.ps1 |
| Android Ses Merkezi | 3.9.8 (30908) | android/app/build.gradle |
| Yönetici girişi | Ana uygulama içinde | Ana uygulamanın kimlik doğrulama ve yetki kontrolü |

3.9.8 kaynak sürümüdür. Windows EXE ve imzalı Android APK, Windows/Android kalite kontrolleri yeşil olduktan sonra `Stagepulse-Releases` deposunda kararlı sürüm olarak yayımlanır. Android APK kalıcı Stagepulse keystore ile imzalanmıştır. Windows EXE şu an Authenticode kod imzası taşımamaktadır; Windows SmartScreen uyarısı görülebilir. Yönetici hesabı girişi ana uygulamanın içindedir; ayrı yönetici EXE/APK derlenmez veya yayımlanmaz.

## Depo düzeni

- windows/: Windows uygulaması, Python ses motorları, eğitim belgeleri, testler ve kurucu.
- android/: Kotlin ana uygulaması, WebView arayüzü, çevrimdışı eğitim içeriği, Android köprüsü ve Android kalite denetimleri.
- admin-app/: Önceki ayrı yönetim istemcisi kaynakları; kararlı yayın iş akışına dahil değildir.
- shared/: Platformlar arası ortak çalışma notları.

Stagepulse ana web sitesi içeriği bu çalışma kapsamında değiştirilmedi.

## Ölçüm araçlarının güncel kapsamı

Windows masaüstü sürümünde canlı RTA, oturumluk 1 kHz ses kalibratörü referansıyla dB SPL Z gösterimi ve aynı ses kartının iki giriş kanalından canlı H1 Transfer Function bulunur. Stereo TF'de CH0 referans, CH1 ölçüm mikrofonudur. Kalibrasyon mikrofon frekans düzeltmesi veya IEC sınıfı ölçüm uygunluğu sağlamaz. Gerçek ses kartı, mikrofon ve saha kabul testleri otomatik kaynak testlerinden ayrı doğrulanmalıdır.

Ticari satış modeli yalnızca FULL PAKET'tir. Eğitim dalları ayrı satış ürünü değil, Full Paket içindeki öğrenme/yeterlilik yapısıdır.

## Android geliştirme ve doğrulama

Gerekli araçlar: JDK 17, Android SDK Platform 35, Android Build Tools 35.0.0, Gradle 8.9, Node.js 22 ve Python 3.12.

Depo kök dizininden:

```bash
python android/scripts/verify_assets.py
```

Android JavaScript dosyalarını denetlemek için:

```bash
find android/app/src/main/assets/ui -type f -name '*.js' -print0 | while IFS= read -r -d '' file; do node --check "$file" || exit 1; done
```

Android birim testleri ve yerel debug APK:

```bash
gradle -p android --no-daemon clean testDebugUnitTest assembleDebug
```

APK çıktısı:

android/app/build/outputs/apk/debug/app-debug.apk

Debug APK, üretim imzalı yayın paketi değildir. Gerçek telefonda mikrofon, dosya seçici, PDF açma, hesap/lisans, ekran yönü ve güncelleme kabul testleri ayrıca yapılmalıdır. Ayrıntı: android/README_ANDROID_TR.md ve android/ANDROID_AUDIT_TR.md.

## Windows geliştirme

Windows EXE üretim adımları windows/README_TR.md ve windows/EXE_OLUSTUR.ps1 içindedir. Paketleme; Windows x64 ortamında Python kaynak testlerini, JavaScript kontrollerini, PyInstaller uygulama paketini ve NSIS tek kurulum EXE'sini üretir. Son kullanıcıya Python, CMD veya ayrı derleme araçları gerekmez.

## Yapay zekâ sağlayıcıları

- Windows: yerel Ollama ve isteğe bağlı Groq yedeği.
- Android: yalnızca Groq. Android cihazının kendi 127.0.0.1 adresi bilgisayardaki Ollama servisi değildir.
- Bulut istekleri için açık veri gönderme onayı ve sunucu tarafındaki lisans denetimi uygulanır. API anahtarları kalıcı uygulama depolarına yazılmaz.

## CI ve yayın süreci

Android kalite iş akışı `main` dalına gelen Android kaynak değişikliklerinde ve pull request'lerde varlık, JavaScript sözdizimi, sürüm eşleşmesi ve Gradle birim testlerini çalıştırır. Windows kaynak doğrulaması ve dağıtılabilir paket üretimi ayrı iş akışlarıyla yönetilir. Bir CI koşusu runner tahsis edilmeden başlarsa bu, testlerin başarılı veya başarısız olduğu anlamına gelmez.

Kararlı Windows EXE ve imzalı Android APK, `Stagepulse-Releases` deposunun yayın hattından üretilir. Kaynak depoya push yapılması tek başına GitHub Release etiketi, indirme manifesti veya Stagepulse web sitesini güncellemez.

## 3.9.8 SPL/RTA ölçüm motoru

Windows canlı RTA motoru ve Android WebAudio PCM yakalama zinciri 1/1, 1/3, 1/6, 1/12, 1/24 ve 1/48 oktav çözünürlüklerini destekler. Android tarafında PCM örnekleri Hann pencereli FFT ile analiz edilir; bant seviyeleri dBFS RMS olarak gösterilir. Ölçüm mikrofonu CSV düzeltmesi RTA bant grafiğine uygulanabilir.

Windows stereo WAV analiz ekranı A/C/Z ağırlıklı Leq, Fast/Slow maksimum, Peak ve 1 saniyelik L10/L50/L90 sonuçlarını gösterir. Kalibrasyon offset'i olmadan değerler dBFS olarak etiketlenir. Yönetici panelinden gelişmiş RTA ve mikrofon düzeltme özellikleri Supabase üzerinde merkezi olarak yönetilir. Mikrofon, kalibratör ve saha kontrol bilgileri yerel saha kaydı olarak dışa aktarılabilir.

Gerçek mikrofon/ses kartı saha testi, izlenebilir kalibrasyon, ölçüm mikrofonu üretici correction dosyasının doğrulanması ve IEC 61672 / IEC 61260 uygunluk testleri laboratuvar veya yetkin saha ekipmanıyla ayrıca yapılmalıdır. Uygulama bu standartlara uygunluk sertifikası iddia etmez.
