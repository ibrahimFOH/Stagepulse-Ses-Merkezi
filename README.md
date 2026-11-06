# Stagepulse Ses Merkezi

Stagepulse Ses Merkezi; Windows masaüstü uygulaması ve Android uygulamasından oluşan Türkçe ses mühendisliği platformudur. Yönetici hesabı ve yetkileri ana uygulama içindeki giriş/oturum akışıyla yönetilir. Son kullanıcı paketleri ayrı Stagepulse-Releases deposunda üretilir.

## Platform sürümleri

| Bileşen | Kaynak sürümü | Sürümün yönetildiği yer |
|---|---:|---|
| Windows Ses Merkezi | 3.8.9 | windows/Merkez.py ve windows/EXE_OLUSTUR.ps1 |
| Android Ses Merkezi | 3.8.9 (30809) | android/app/build.gradle |
| Yönetici girişi | Ana uygulama içinde | Ana uygulamanın kimlik doğrulama ve yetki kontrolü |

Windows EXE ve Android APK aynı kararlı sürümde doğrulanır ve yayımlanır. Yönetici hesabı girişi ana uygulamanın içindedir; ayrı yönetici EXE/APK derlenmez veya yayımlanmaz. Android APK kalıcı Android imza anahtarıyla imzalanır.

## Depo düzeni

- windows/: Windows uygulaması, Python ses motorları, eğitim belgeleri, testler ve kurucu.
- android/: Kotlin ana uygulaması, WebView arayüzü, çevrimdışı eğitim içeriği, Android köprüsü ve Android kalite denetimleri.
- admin-app/: Önceki ayrı yönetim istemcisi kaynakları; kararlı yayın iş akışına dahil değildir.
- shared/: Platformlar arası ortak çalışma notları.

Stagepulse ana web sitesi içeriği bu çalışma kapsamında değiştirilmedi.

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

## GitHub Actions ve CI sorumluluğu

Özel kaynak deposundaki GitHub-hosted runner koşuları bazı commitlerde runner tahsis edilmeden sona eriyordu: ilgili job kayıtlarında runner_id=0, boş runner adı ve hiç başlamamış adımlar görülüyordu. Bu sonuçlar kaynak kodunun test edilip başarısız olduğu anlamına gelmez.

Bu nedenle kaynak deposundaki üç platform iş akışı workflow_dispatch ile kontrollü başlatılır; PR başına runner alamayan kırmızı iş üretmez. Tam Windows ve Android doğrulamasının yetkili hattı, ibrahimFOH/Stagepulse-Releases deposundaki Stagepulse Ses Merkezi sürüm yayın iş akışıdır. Bu hat özel kaynak deposunu salt okunur token ile alır ve sürüm eşitliğini, Python güvenlik denetimini, Windows pytest/Node testlerini, Windows kurulum EXE derlemesini, Android varlık ve JavaScript testlerini, Gradle birim testini ve kalıcı imzalı APK üretimini çalıştırır.

Bir koşuda runner_id=0 ve steps=[] varsa bu koşu CI başarısı veya kaynak test hatası olarak yorumlanmamalıdır. Özel repo için GitHub Settings > Actions > General ve hesap Billing & licensing > Actions ayarlarında Actions erişimi ile kullanılabilir hosted-runner kotası/yetkisi ayrıca kontrol edilmelidir. Bu hesap ayarları depo kodundan değiştirilemez.

Stagepulse-Releases iş akışının push kaynak CI koşusu paket artifact'larını üretir; publish işi push olayında çalışmaz. GitHub Release etiketi, indirme manifesti veya Stagepulse web sitesi ancak açık yayın akışı ile güncellenir.
