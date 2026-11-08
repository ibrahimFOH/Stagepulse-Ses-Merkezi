# Stagepulse Ses Merkezi yayın kontrolü

## Windows ve Android kaynak sürümü 3.9.0

1. Windows x64 geliştirme bilgisayarında `EXE_OLUSTUR.bat` tamamlanıp tüm testler yeşil olmadan uygulamayı dağıtma.
2. `dist/StagepulseSesMerkezi-Kurulum-3.9.0.exe` dosyasını `/downloads/ses-merkezi/StagepulseSesMerkezi-Kurulum-3.9.0.exe` hedefine yükle.
3. Derlemenin oluşturduğu `website_release/latest.json` dosyasını `/downloads/ses-merkezi/latest.json` adresine yükle. İçindeki `sha256` aynı kurulum EXE'sinin SHA-256 özeti olmalı.
4. Tarayıcıda manifestin JSON döndürdüğünü ve kurucunun indirildiğini doğrula. Güncelleme kontrolünü uygulamanın Hesap/Güncelleme ekranından test et.
5. Ücretli genel dağıtımdan önce Stagepulse adına Windows Authenticode kod-imzalama sertifikası kullan. Bu depoda özel kod-imzalama anahtarı tutulmaz. HTTPS ve SHA-256, kod imzasının yerine geçmez.

## Web lisans yönetimi (yönetici)

- Adres: `https://stagepulse.com.tr/ses-merkezi-lisans/`
- Bilgisayar ve mobil tarayıcıdan aynı URL kullanılır. Giriş yalnızca mevcut Stagepulse sahibi/yönetici hesabıyla yapılır; genel kayıt kapalıdır.
- Panel `ses-merkezi-desktop` Supabase Edge Function üzerinden çağrı yapar. Yayınlanan Edge Function sürümü 6 ve JWT doğrulaması etkindir. Yönetici işlemleri ayrıca sunucu tarafında owner rolüyle sınırlandırılır.
- Panelin web dosyaları `ses-merkezi-lisans/index.html`, `admin.css`, `admin.js` içindedir. `/ses-merkezi-lisans/*` yanıtları için `noindex` ve cache kontrol header'ları `_headers` dosyasında; yolun ağdan önce kontrol edilmesi `sw.js` içinde ayarlanır.
- Ticari satış yalnızca FULL PAKET içindir. Müşteri havale/EFT bildirimi gönderir; yönetici gerçek banka hareketini doğrulayıp onaylamadan lisans üretilmez. Bu akış iyzico/Stripe veya kart tahsilatı yapmaz; panel kaydı fatura/fiş üretmez.
- Yayından sonra hem telefon hem masaüstü tarayıcıda giriş ekranını, yetkisiz hesabın reddedildiğini, lisans listeleme/yeni lisans/ödeme durumu/iptal/süre uzatma/cihaz kaldırma/CSV işlemlerini kontrol et. Gerçek üretim lisansı oluşturmadan önce bu işlemleri mevcut test hesaplarıyla uçtan uca doğrula.

## Doğrulama notu

Bu çalışma paketindeki Python testleri ve JavaScript sözdizimi kontrolleri yerel kaynak üzerinde yürütülür. Windows kurulum EXE'si Linux geliştirme ortamında derlenmiş veya test edilmiş sayılmaz. Web yayını CDN/Cloudflare önbelleği nedeniyle gecikirse `https://stagepulse.com.tr/ses-merkezi-lisans/` ve altındaki iki varlığın güncel içerik döndürdüğünü ayrıca doğrula.

## Öğrenciye teslim

Windows derleme bilgisayarında `EXE_OLUSTUR.bat` çalıştır. Öğrenciye yalnızca kurulum EXE'sini ya da içeriğinde tek kurulum EXE'si olan `ogrenciye_gonder/Stagepulse_Ogrenci_Kurulum_3.9.0.zip` dosyasını ver. Kaynak depo, Python, NSIS veya ara uygulama EXE'lerini gönderme.


## Android yayın imzası (kalıcı)

Android APK güncellemelerinde uygulama verilerinin korunması için tüm sürümler aynı özel imza anahtarıyla imzalanmalıdır. GitHub Actions, aşağıdaki depo sırları tanımlandığında ayrıca kalıcı imzalı Release APK üretir:

- `ANDROID_KEYSTORE_BASE64`
- `ANDROID_KEYSTORE_PASSWORD`
- `ANDROID_KEY_ALIAS`
- `ANDROID_KEY_PASSWORD`

Anahtar dosyasını ve parolaları depoya veya kaynak ZIP'ine ekleme. GitHub deposunda **Settings → Secrets and variables → Actions** bölümüne ekle. Anahtar kaybolursa aynı paket kimliği için güncelleme imzası üretilemez.
