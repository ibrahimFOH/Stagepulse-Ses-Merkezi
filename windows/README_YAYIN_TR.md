# Stagepulse Ses Merkezi yayın ve kabul kontrolü

## Güncel kararlı sürüm

- Kaynak sürümü: **4.0.4**
- Android sürümü: **4.0.4 (versionCode 40004)**
- Windows sürümü: **4.0.4**
- Kararlı yayın: [Stagepulse Ses Merkezi 4.0.4](https://github.com/ibrahimFOH/Stagepulse-Releases/releases/tag/v4.0.4)
- Yayın deposu: `ibrahimFOH/Stagepulse-Releases`
- Güncelleme manifesti: `Stagepulse-Releases/main/latest.json`

Bu dosya yayın sürecinin güncel açıklamasıdır. Sürüm numarasını yeni sürümlerde buradaki sabit metinden değil, Android Gradle ve Windows kaynak sürüm alanlarından doğrula.

## Otomatik yayın akışı

1. Uygulama kaynak değişiklikleri yalnızca `Stagepulse-Ses-Merkezi/main` dalına gönderilir.
2. `.github/workflows/trigger-ses-merkezi-release.yml` Android, Windows ve NSIS sürümlerinin eşleşmesini ve Android `versionCode` değerini doğrular.
3. Kaynak depo, doğrulanan commit için `ses-merkezi-vX.Y.Z` etiketi oluşturur ve `Stagepulse-Releases` deposunu tetikler.
4. Yayın deposu Android APK'yı kalıcı keystore ile imzalar; Windows x64 kurulum EXE'sini oluşturur.
5. Yayın hattı iki paketin sürümünü ve SHA-256 özetlerini doğrular, GitHub Release varlıklarını yayımlar ve `latest.json` dosyasını günceller.
6. Supabase `ses-merkezi-updates` Edge Function, Android ve Windows istemcilerine aynı kararlı manifestten platforma uygun indirme bilgilerini sunar.

**Elle APK/EXE yükleme veya web sunucusuna manifest kopyalama yapma.** Yayın hattı bu işlemleri otomatik yürütür. Yeni yayın tamamlanmadan `latest.json` dosyasını elle değiştirme.

## 4.0.4 yayın varlıkları

- `Stagepulse-Ses-Merkezi-Android-4.0.4.apk`
- `Stagepulse-Ses-Merkezi-Android-4.0.4.apk.sha256`
- `Stagepulse-Ses-Merkezi-Windows-4.0.4.exe`
- `Stagepulse-Ses-Merkezi-Windows-4.0.4.exe.sha256`
- `latest.json`

Yayın hattı bu dosyaları GitHub Release'e ekler. İndirme adresleri ve SHA-256 değerleri manifestte tutulur.

## Yayın öncesi otomatik kontroller

- Android JavaScript sözdizimi, ortak araç regresyonları, Gradle testleri ve APK imza/sürüm/hizalama kontrolleri.
- Windows Python kaynak, bağımlılık güvenlik, sözdizimi ve regresyon testleri.
- Windows EXE paketleme ve SHA-256 üretimi.
- Android ve Windows sürüm eşitliği.
- Her iki paketin SHA-256 değerlerinin yeniden hesaplanması.
- Manifest şeması, indirme adresleri, kanal ve canlı manifest doğrulaması.

Yayın kabulü için kaynak depo Android kalite, Windows EXE ve güvenlik iş akışlarının; yayın deposu ise üç yayın işinin tamamının başarılı olması gerekir.

## Manuel gerçek cihaz kabul testi

CI, gerçek Android telefon veya Windows bilgisayar üzerinde fiziksel donanım testinin yerine geçmez. Her kararlı yayından sonra:

1. Android'de mevcut kurulum üzerine APK güncellemesini dene; uygulama verilerinin ve lisans oturumunun korunduğunu doğrula.
2. Android mikrofon izni, RTA, ses girişi, dosya seçici, PDF ve güncelleme bildirimi akışlarını dene.
3. Windows'ta kurulum EXE'sini temiz bir Windows x64 sisteminde kur; açılış, profil, lisans, ses cihazı seçimi, mikrofon izni ve RTA'yı dene.
4. Windows ve Android uygulamalarında güncelleme kontrolü yap; yeni sürüm bildiriminin doğru sürümü göstermesini doğrula.
5. İndirilen APK/EXE dosyalarının SHA-256 değerlerini manifestle karşılaştır.
6. Güncelleme sonrası uygulamayı yeniden başlat ve temel işlevleri tekrar kontrol et.

Gerçek cihaz testleri yapılmadıysa bunları yapılmış gibi raporlama.

## İmzalama ve dağıtım sınırları

### Android

Android APK kalıcı Stagepulse keystore ile imzalanır. Yayın iş akışı imza doğrulaması yapar. Aşağıdaki GitHub Actions secrets değerleri kaynak depoda tutulmamalı, yalnızca depo sırları olarak saklanmalıdır:

- `ANDROID_KEYSTORE_BASE64`
- `ANDROID_KEYSTORE_PASSWORD`
- `ANDROID_KEY_ALIAS`
- `ANDROID_KEY_PASSWORD`

Keystore ve parolaları depoya, ZIP dosyasına veya loglara ekleme. Keystore kaybolursa aynı uygulama kimliği için güncelleme imzası üretilemeyebilir.

### Windows

Mevcut Windows EXE Authenticode kod imzası taşımamaktadır; Windows SmartScreen uyarısı gösterebilir. HTTPS ve SHA-256 bütünlük kontrolü, kod imzasının yerine geçmez. Güvenilir yayıncı doğrulaması için Stagepulse adına geçerli Code Signing sertifikası ve `WINDOWS_SIGNING_CERT_PFX_BASE64` ile `WINDOWS_SIGNING_CERT_PASSWORD` secrets değerleri gerekir.

## Lisans yönetimi

- Yönetim paneli: [Stagepulse Ses Merkezi Lisans Yönetimi](https://stagepulse.com.tr/ses-merkezi-lisans/)
- Yönetici işlemleri Supabase Edge Function üzerinden ve sunucu tarafı yetki denetimiyle yürütülür.
- Ticari satış akışı FULL PAKET için banka havalesi/EFT bildirimi ve yönetici onayına dayanır. Bu akış çevrimiçi kart tahsilatı veya otomatik banka doğrulaması yapmaz.
- Panel kayıtları fatura, e-Arşiv veya yasal muhasebe belgesi değildir.
- Üretim müşterisi için işlem yapmadan önce test hesabıyla giriş, yetki reddi, ödeme bildirimi, onay/red, lisans iptali, süre uzatma ve cihaz kaldırma adımlarını doğrula.

## Dağıtım kararı

Aşağıdaki koşulların tamamı sağlanmadan yeni sürümü kararlı olarak duyurma:

- [ ] Kaynak sürüm alanları Android, Windows ve NSIS'te eşleşiyor.
- [ ] Android kalite ve Windows EXE CI kontrolleri yeşil.
- [ ] Android APK kalıcı anahtarla imzalı ve imza doğrulaması başarılı.
- [ ] Windows EXE üretildi ve SHA-256 oluşturuldu.
- [ ] Yayın deposundaki Android/Windows varlıkları ve manifest aynı sürümü gösteriyor.
- [ ] Yayın deposu workflow'larının tamamı yeşil.
- [ ] Android gerçek cihaz kabul testi tamamlandı.
- [ ] Windows gerçek cihaz kabul testi tamamlandı.
- [ ] Güncelleme bildirimi ve kurulum sonrası temel işlevler doğrulandı.
