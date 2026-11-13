# Stagepulse Ses Mühendisliği Merkezi 4.0.6

Paylaşılan arayüz/araç modülleri Android ve Windows tarafında aynı 4.0.6 sürümünde tutulur.

**Tek Windows kurulum dosyası · tek pencere uygulama · lisanssız yerel demo · çevrimiçi lisans, satış ve öğretmen kontrolü**

## 4.0.3 ve önceki sürümden gelen araçlar

- OSC/UDP mesaj gönderimi: IPv4 hedef, UDP portu ve float/integer/string parametreleri.
- MIDI Type 0 dosyası üretimi: tempo, kanal, program, nota, velocity ve süre.
- OSC gönderimi tek yönlüdür; mikserden durum/yanıt okuma veya otomatik geri bildirim içermez.

### Önceki sürümlerde eklenen araçlar

- RTA ölçüm adayları için çoklu konum doğrulaması ve adım adım müdahale önerileri.
- SPL saha ölçüm sihirbazı, ölçüm noktası kaydı ve CSV özeti.
- Tek/üç faz güç, akım ve kablo gerilim düşümü ön hesaplayıcısı.
- El mikrofonu ve IEM kanallarını birlikte ele alan RF ön koordinasyon aracı.
- Dört kanallı sanal mikser laboratuvarı: gain, HPF, EQ, compressor, mute/solo ve ses dosyası oynatma.
- Sekiz AI video ders senaryosu, storyboard ve video oynatıcı altyapısı.
- Asistan, Operatör ve Mühendis öğrenme yolu ile PDF katılım belgesi.

Katılım belgesi yalnızca Stagepulse eğitimine katılımı gösterir; resmî yeterlilik, akreditasyon veya mesleki yetki sağlamaz.

### Yerel araçlar

- **Kulak eğitimi:** Frekans ve EQ çalışmalarına kompresör ve gürültü kapısı (Noise Gate) A/B dinleme alıştırmaları eklendi.
- **70,7 / 100 V hoparlör hattı hesabı:** Hoparlör tap yükleri, yükselteç güç payı ve bakır kablo gerilim düşümü.
- **Mikser kanal bağlantı raporu:** M32/X32 `.scn` dosyasının yerel ve salt okunur çözümlemesi; CSV dışa aktarımı.
- **Kablosuz frekans planı:** Kullanıcının doğruladığı frekans aralığında kanal yerleşimi ve yüklenen tarama CSV verisinde girişim noktalarının dışlanması.
- **Oda ses basınç seviyesi haritası:** Ölçüm CSV verilerinden enterpolasyonlu ısı haritası.
- **Hoparlör ve sayısal sinyal işleme eğitimi:** Kapalı kutu Thiele–Small ön hesabı ve Butterworth geçiş eğrisi.
- **Sahne ve ses-görüntü planı:** Ölçekli 2B yerleşim, ekipman listesi, JSON/CSV dışa aktarımı.
- **Akustik sistem analizi:** Stereo WAV üzerinden H1 Transfer Function, Magnitude, Phase, Coherence, Delay Finder ve Impulse Response/ETC. Windows masaüstü sürümünde aynı ses kartının iki girişinden canlı H1 magnitude/faz/coherence yakalama da bulunur; CH0 referans, CH1 ölçüm mikrofonudur. Canlı akış aynı saat kaynağındaki iki kanalı gerektirir.

Yeni araçların hesaplama kodu Stagepulse içinde bağımsızdır. Kaynak ZIP arşivleri uygulamaya kopyalanmaz. Araçlar dış CDN veya çevrimiçi hesaplama servisi kullanmaz. RF planı yasal tahsis belgesi değildir; kullanıcı izinli bandı kendisi doğrular. M32/X32 sahne okuyucusu yalnızca temel verileri çözümler ve sahne dosyasını değiştirmez.

## Öğrenci / müşteri kurulumu

4.0.6 kaynak sürümüdür. Windows EXE ve kalıcı Stagepulse keystore ile imzalı Android APK, Windows/Android kalite kontrolleri yeşil olduktan sonra `Stagepulse-Releases` deposunda kararlı sürüm olarak yayımlanır. Windows EXE şu an Authenticode kod imzası taşımamaktadır; Windows SmartScreen uyarısı görülebilir. Güvenilir yayıncı doğrulaması için gelecekteki sürümden önce geçerli bir Windows Code Signing sertifikası ve release secret'ları yapılandırılmalıdır. Bu kurucu uygulamayı `%LOCALAPPDATA%\Programs\Stagepulse\SesMerkezi` altına yerleştirir, masaüstüne ve Başlat menüsüne kısayol ekler ve Windows uygulama kaldırma kaydı oluşturur. Son kullanıcıya Python, CMD, BAT veya ayrı araç EXE'leri verilmez. Güncelleme aynı kurucunun sessiz yükseltme modunu kullanır; öğrenci profilleri kurulum güncellemesinde silinmez.

Bu depo kaynak koddur. Windows kurulum EXE'si, Windows x64 ortamındaki `EXE_OLUSTUR.bat` veya `EXE_OLUSTUR.ps1` ile üretilir. 4.0.6 kaynak sürümüdür; Windows x64 EXE, kalıcı anahtarla imzalı Android APK, SHA-256 ve GitHub Release doğrulamaları yayın hattında yapılır. Derleme bilgisayarında Python 3.11/3.12/3.13/3.14 x64 gerekir; son kullanıcıda gerekmez. Node.js derleme ortamında isteğe bağlıdır; kuruluysa JavaScript sözdizimi ve yerel araç çalışma zamanı testleri çalıştırılır. Kurulu değilse bu iki Node testi atlanır, Python kaynak testleri yine yürütülür. Betik önce testleri çalıştırır, Microsoft WebView2 yükleyicisinin dijital imzasını ve NSIS paketinin SHA-256 değerini doğrular; derleme sonunda geçici araçları siler ve `dist` klasöründe yalnızca tek kurulum EXE'si bırakır.

## Windows MSIX derleme ve kurulum

MSIX, mevcut PyInstaller payload'ından üretilir; uygulama kaynakları veya EXE derleme sistemi ayrı bir kopyaya bölünmez. MSIX manifesti Windows masaüstü, internet ve mikrofon erişimini tanımlar. Paket x64'tür.

### Yerel derleme

1. Windows 10/11 x64 bilgisayara Python 3.11–3.14 x64, Windows 10/11 SDK (MakeAppx ve SignTool) ve mevcut EXE derlemesinin gerektirdiği araçları kur.
2. Depoyu Windows bilgisayarına indir; `windows` klasörüne gir.
3. İlk kurulumda sertifika oluşturulup Windows güvenilir kişiler deposuna ekleneceği için `MSIX_OLUSTUR.bat` dosyasını **Yönetici olarak çalıştır**.
4. İlk çalıştırmada en az 12 karakterli PFX parolası belirle. `windows/msix/cert/` altındaki PFX özel anahtarını depoya veya dağıtım ZIP'ine ekleme.
5. Derleme tamamlandığında `windows/dist/` altında sürüm numaralı `.msix`, `.msix.sha256` ve `Stagepulse-MSIX-Signing.cer` oluşur.

İlk kurulumda Windows, yerel geliştirme sertifikasına güvenmediği için imzalı MSIX'i yüklemeyi reddedebilir. Betik sertifikayı yerel bilgisayarda güvenilir kişiler deposuna ekler. Başka bir bilgisayara test paketi taşınırsa CER sertifikasını o bilgisayarda güvenilir kişiler deposuna yönetici olarak eklemek gerekir. Bu kendinden imzalı sertifika yalnızca geliştirme/test içindir; genel dağıtımda Stagepulse adına güvenilir bir kod imzalama sertifikası kullanılmalıdır.

### GitHub Actions otomasyonu

`.github/workflows/build-windows-exe.yml` ana dalındaki Windows derleme hattı; kaynak testleri, EXE üretimi, SHA-256 kontrolü, geçici CI imza sertifikasıyla MSIX üretimi/imzası ve Windows üzerinde MSIX kur-kaldır testini çalıştırır. `main` dalına ilgili Windows kaynakları gönderildiğinde otomatik başlar; GitHub Actions > **Stagepulse Windows EXE kalite ve derleme** > **Run workflow** ile elle de başlatılabilir. Başarılı derleme çıktıları aynı sürüm numaralı workflow artifact'inde EXE, MSIX, SHA-256 ve CI test sertifikası olarak saklanır. CI sertifikası her çalıştırmada geçicidir; kullanıcıya dağıtılacak kalıcı imza anahtarı değildir.

## Eğitim yolları ve yeterlilik

Uygulamaya **Eğitim dalları / usta yolu** ekranı eklendi. Dokuz öğrenme alanı, L0–L5 yeterlilik basamakları, uygulama görevleri ve dal bazlı kısa bilgi testleri `docs/EGITIM_DALLARI_USTA_YOLU_VE_FIYATLANDIRMA_TR.md` içinde ayrıntılıdır. Makine tarafından okunabilir katalog `egitim_paketleri/stagepulse_egitim_katalogu_v1.json` dosyasıdır. Eğitim dalları içerik ve yeterlilik sınıflandırmasıdır; ayrı satılan modüller değildir. Ticari satış yalnızca FULL PAKET üzerinden yapılır.

Lisans kaydındaki teknik kapsam alanı veritabanı uyumluluğu için korunur; güncel ticari ürün tek FULL PAKET'tir. Eğitim dalları ayrı ürün veya ayrı lisans kapsamı değildir. Ücretli erişim ve cihaz yetkisi sunucu tarafında doğrulanır.

## Uygulama bölümleri

- `Merkez.py`: uygulama girişi, WebView2 penceresi, yerel ve sunucu API köprüsü.
- `ui/`: tek pencerenin Türkçe sayfaları ve erişilebilir/ölçeklenebilir stiller.
- `core/`: güvenli profil deposu, yerel ses işleme, RTA yakalama ve AI sağlayıcı adaptörleri.
- `araclar/`: yerel Frekans Bulucu.
- `egitim_paketleri/`: öğrenciye verilecek izinli PDF dersleri.
- `supabase/`: ticari lisans ve ilerleme verisinin şemasıyla Edge Function.
- `setup/`: tek kurulum EXE'sinin NSIS tanımı.
- `website_release/`: Windows derlemesinden sonra web sitesine yayımlanacak güncelleme manifesti ve yayın kontrol dosyası.

## Lisans, öğrenci ve öğretmen yetkileri

- Lisans anahtarı sunucuda düz metin tutulmaz; SHA-256 özeti saklanır. Anahtar oluşturulduğunda kullanıcıya yalnızca bir defa gösterilir.
- Lisans, hesap ve cihaz kimliğiyle doğrulanır; aktivasyon sınırı, son kullanım tarihi ve iptal kontrolü sunucudadır.
- Öğrenci ilerlemesi sunucuda tutulur ve öğrenci yalnızca görüntüler. Aşama işaretleme işlemi Edge Function'da yalnızca sabit Stagepulse sahibi UUID'si ve `owner` üyeliğiyle yetkilendirilir; düğmeyi gizlemek tek başına güvenlik sınırı değildir.
- Profil dosyaları Windows'ta DPAPI ile mevcut Windows kullanıcısına bağlanarak şifrelenir. Bu dosyalar başka bir Windows hesabında doğrudan açılamaz. Eski düz JSON profil dosyası bulunursa bir defalık şifreli depoya geçiş yapılır.
- Yönetici/öğretmen yetkisi çevrimdışı lisans önbelleğinden geri yüklenmez. Öğrenci araçları yerelde çalışabilir; lisans ve öğretmen kontrolü için internet gerekir.
- Mobil ve masaüstü lisans yönetimi: `https://stagepulse.com.tr/ses-merkezi-lisans/`. Yönetici oturumu ve sunucu tarafı sahip yetkisi doğrulanır. Müşteri yalnızca FULL PAKET için banka havalesi/EFT bildirimi gönderir; fiyat yönetici mağaza ayarından belirlenir ve 2.500 TL'yi aşamaz. Yönetici banka hareketini kontrol edip onaylar veya reddeder. Onayda lisans anahtarı sunucuda üretilir. Nakit, POS veya çevrimiçi kart tahsilatı bu satış akışında kullanılmaz. Paneldeki işlem kaydı muhasebe belgesi veya fatura yerine geçmez.

## Lisans yönetim paneli (PC ve telefon)

- Panel: `https://stagepulse.com.tr/ses-merkezi-lisans/`
- Yalnızca mevcut Stagepulse sahibi yönetici hesabı ile giriş yapılabilir; herkese açık kayıt ekranı yoktur. Supabase Auth oturumu ve Edge Function içindeki sahip/rol denetimi birlikte kullanılır.
- Müşteri FULL PAKET satın alma bildirimi gönderirken banka transfer referansını girer. Yönetici banka hesabındaki hareketi kontrol edip onaylar veya reddeder. Onay verilmeden lisans anahtarı oluşturulmaz ve lisans etkinleştirilmez.
- Eski doğrudan yönetici lisans üretme API yolları Ses Merkezi için kapalıdır. Yeni lisans yalnızca havale/EFT satın alma kaydının yönetici onayıyla üretilir; mevcut lisansların aktivasyonu ve yönetimi korunur.
- Canlı satışa başlamadan önce yönetici mağaza ayarlarından banka adı, hesap sahibi, IBAN ve ödeme açıklamasını tanımlamalıdır. Banka bilgileri eksikse satın alma bildirimi `BANK_DETAILS_NOT_CONFIGURED` ile reddedilir; lisans üretilmez.
- Yeni lisans anahtarı oluşturulduğunda yalnızca o anda gösterilir. Kopyalayıp müşteriye güvenli şekilde teslim et. Sunucuda anahtarın kendisi yerine SHA-256 özeti saklanır. Anahtarı kaybedersen yeniden göstermeye çalışmak yerine yeni anahtar oluşturman ve eski lisansı iptal etmen gerekir.
- Yönetim paneli HTTPS ve internet bağlantısı ister; kayıtlar çevrimdışı oluşturulmaz. Mobil tarayıcı ve masaüstü tarayıcı aynı paneli kullanır.
- Tahsilat/CSV kayıtları iç yönetim kaydıdır; fatura, e-Arşiv veya yasal muhasebe belgesi değildir. Online ödeme altyapısı bu sürüme dahil değildir.
- Yönetici erişimi çalışmazsa Supabase Auth hesabının doğru e-postasını/şifresini ve Stagepulse `owner` üyeliğini kontrol et. Yönetici parolasını uygulama dosyalarına yazma.

Kurulum ve denetim ayrıntıları: `website_release/ADMIN_PANEL_KURULUM_TR.md`.

Denetim özeti ve doğrulanmış testler: `DENETIM_RAPORU_TR.md` (119 otomatik test geçti; canlı web ve Windows EXE uçtan uca testi bu ortamda yapılamadı).

## Yapay zekâ bağlantıları

Arayüz yerel Ollama ve isteğe bağlı GroqCloud yedeğini destekler. Ollama görev türüne göre bu bilgisayara kurulu modeller arasında otomatik yönlendirilir; Groq yalnızca kullanıcı açıkça seçip onay verdiğinde kullanılır. Groq API anahtarı oturum alanına girilir; kalıcı profile kaydedilmez ve günlük dosyasına yazılmaz. Bulut sağlayıcısı kullanılırken istem/veri doğrudan seçilen sağlayıcıya gönderilir; kullanıcı arayüzündeki açık onay şarttır. Ollama yerel olarak kurulmuş ve model indirilmişse internet olmadan çalışabilir. Bu kurucu tüm büyük yerel dil modellerini içine almaz; bu, kurulum boyutunu yüzlerce GB'ye kadar büyütebilir.

## Stagepulse web sitesi ve güncellemeler

Uygulama güncellemeleri Supabase `ses-merkezi-updates` Edge Function üzerinden alınır. İşlev yalnızca `stable` kanalını okur; kaynak manifest `Stagepulse-Releases` deposundaki `latest.json` dosyasıdır. Yayın hattı Windows EXE ve imzalı Android APK'nın SHA-256 özetlerini üretir, Release varlıklarını yayımlar ve manifesti otomatik olarak günceller. Windows ve Android istemcileri yeni sürümü bu manifestten kontrol eder; APK imzası ve paket özeti kurulmadan önce doğrulanır. Manifest henüz yayımlanmamışsa uygulama bunu açıkça `yayımlanmadı` olarak gösterir; eski veya test kanalı kullanılmaz. Ücretli geniş dağıtım öncesinde Stagepulse adına bir Windows Authenticode kod-imzalama sertifikası kullanılması gerekir; bu depo içinde imzalama sertifikası/özel anahtar yoktur ve SmartScreen uyarısı görülebilir. HTTPS ve SHA-256 doğrulaması kod imzasının yerine geçmez.

## LUFS / EBU Loudness Test Set

Windows masaüstünde yerel ses işleme motoru DeMan K-weighting ile integrated LUFS ve Loudness Range (LRA) hesaplar; 48 kHz için ITU-R BS.1770-5 Annex 2 4-faz FIR true-peak ölçümü uygular ve PCM 24-bit WAV dışa aktarımını yeniden okuyup kontrol eder. True-peak tavanı hedef LUFS'e erişimi sınırlayabilir; limiter uygulanmaz.

EBU doğrulama aracı çıkarılmış EBU Loudness Test Set WAV klasörünü tarar. Referans CSV şu alanları destekler: `filename`, `integrated_lufs`, `lra_lu`, `momentary_max_lufs`, `short_term_max_lufs`, `true_peak_dbtp`. Referans değeri bulunmayan dosya PASS sayılmaz. EBU klasörü ve beklenen referans CSV kullanıcı tarafından sağlanmalıdır; resmi test seti uygulama paketine gömülü değildir. Bu araç raporu sertifika veya EBU onayı değildir.

Android sürümünde tarayıcı tabanlı yaklaşık LUFS/LRA normalizasyonu bulunur; Windows yerel ölçüm motoru ve EBU test klasörü karşılaştırma aracı Android'de yoktur. Android sonuçları aynı referans uygunluğu olarak sunulmamalıdır.

## RTA ve teknik sınırlar

RTA, bilgisayarın yerel ses girişinden FFT ve göreli dBFS bant seviyeleri alır. Windows masaüstünde 94/114 dB SPL, 1 kHz fiziksel ses kalibratörüyle oturumluk referans kalibrasyonu yapılabilir; uygulama yeniden başlatıldığında kalibrasyon sıfırlanır. Bu işlem mikrofon frekans cevabı düzeltmesi, A/C ağırlıklandırması veya IEC sınıfı 1/2 uygunluğu sağlamaz. Kalibrasyon yapılmadan mutlak dB SPL iddiasında bulunulmaz. Canlı stereo TF magnitude/faz/coherence verir; bu, mikrofon kalibrasyonu veya üreticiye özel line-array tahmini değildir. Otomatik optimizasyon sadece öneridir ve EQ'yu miksere kendiliğinden uygulamaz. RTA ve ses kayıtları için Windows mikrofon izni/cihaz seçimi gerekir.

## Test ve geliştirici komutları

Geliştirici makinesinde:

```powershell
python -m pip install -r requirements.txt
(İsteğe bağlı) node --check ui/app.js; node --check ui/first_party_tools.js; node tests/test_first_party_tools.js  # Node.js kuruluysa
python -m py_compile Merkez.py core/*.py
python -m pytest -q
.\EXE_OLUSTUR.bat
```

`EXE_OLUSTUR.bat` yalnızca geliştirici/build makinesi içindir; öğrencinin bunu çalıştırması gerekmemelidir.


### Eski 3.6.0 derleme düzeltmesi (tarihsel)

Windows PowerShell 5.1 ile uyumluluk için derleme betiğindeki akıllı tırnaklar düz metinle değiştirildi. NSIS kurulum parametresinin boşluk içeren dizinlere güvenli aktarımı düzeltildi.


## Eski 3.6.0 düzeltmesi (tarihsel)

- Profil testleri gerçek geliştirici profil dosyasını okumaz.
- NSIS ZIP arşivi doğrulanıp çıkarıldıktan sonra testlerden önce silinir; geçici kurulum arşivi öğrenci uygulaması kaynak ağacında kalmaz.
- Testleri `python -m pytest -q` ile çalıştırın. Windows kurulum EXE'si Windows derleme makinesinde üretilmelidir.


## Öğrenciye nasıl gönderilir?

Windows x64 derleme bilgisayarında `EXE_OLUSTUR.bat` çalıştır. Testler başarılı olursa `dist` içinde yalnızca güncel sürüm numarasını taşıyan Stagepulse kurulum EXE'si bulunur. Aynı işlem `ogrenciye_gonder/` altındaki güncel sürüm ZIP'i dosyasını üretir; bu ZIP'in içinde yalnızca `Stagepulse_Kurulum.exe` vardır. Öğrenciye kaynak depo, Python, NSIS, PowerShell veya ara uygulama EXE'si gönderilmez.

Kurulum sırasında WebView2 Runtime yoksa tek kurulum sihirbazı bunu sessizce yükler. Kurulum dizininde `StagepulseSesMerkezi.exe`, PyInstaller bağımlılıklarını taşıyan `_internal` klasörü ve `Uninstall.exe` bulunur. Bu yapı, her uygulama açılışında tek dosyalı paketin yeniden çıkarılmasını önler. Kaldırıcı Windows'un Program Kaldır bölümüne kayıtlıdır ve öğrenci profillerini korur.


## Eski 3.6.0 düzeltmeleri (tarihsel)

- Boş öğrenci profili deposunda tekrarlanan `load_profiles()` çağrısı kaldırıldı; profil listesi yalnızca bir kez yüklenir.
- Lisans yokken ana sayfaya erişim engellenmez. Çevrimdışı araçlar, yerel profiller ve PDF kitaplığı demo modunda kullanılabilir; ücretli bulut/öğretmen özellikleri korunur.
- Başlangıçtaki otomatik güncelleme ağ isteği kaldırıldı; güncelleme kullanıcı isteğiyle denetlenir.
- NSIS kaynağı UTF-8 BOM ile yazılır; Türkçe kurulum ve kaldırma metinleri Unicode olarak derlenir.
- Windows EXE ve masaüstü kısayolu için Stagepulse altın/siyah marka simgesi eklenir.
- FULL PAKET banka transferi bildirimi: müşteri ve transfer referansı kaydedilir; ödeme onayı yalnızca yönetici tarafından gerçek banka hareketi kontrol edildikten sonra verilir.
- Öğrenci kitaplığına Midas M32 Live, Yamaha CL5 ve Allen & Heath Avantis uygulamalı eğitimleri eklendi.

## Windows yeniden derleme

Kaynak ZIP'i Windows üzerinde açıp `EXE_OLUSTUR.bat` çalıştır. Bu ortamda Windows kurulum EXE'si çalıştırılıp imzalanamaz; `dist` içindeki çıktı Windows derleme makinesinde üretilecektir.


## Lisans yönetimi ve yetki sınırı

Lisans yönetimi yalnızca Supabase Auth oturumu ve sunucu tarafı `owner` yetkisiyle çalışır. Masaüstü Edge Function özel yönetici token'ı kabul etmez. Ortak lisans çekirdeğindeki yönetim listeleme ve iptal sorguları `owner_user_id` ile oturum sahibine sınırlandırılır. Bu depodaki lisans şemasında ayrı bir `tenant_id` alanı bulunmadığından mevcut tenant sınırı lisans sahibi kullanıcı kimliğidir.
