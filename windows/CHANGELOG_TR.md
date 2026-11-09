# Stagepulse Ses Merkezi 3.9.5

- RTA ölçüm adayları için doğrulama ve müdahale adımları eklendi.
- SPL saha ölçüm sihirbazı, nokta kaydı ve CSV raporu eklendi.
- Tek/üç faz akım ve gerilim düşümü ön hesaplayıcısı eklendi.
- El mikrofonu ve IEM için birleşik RF ön koordinasyon aracı eklendi.
- Dört kanallı sanal mikser, gain staging, EQ ve compressor pratiği eklendi.
- AI video ders senaryoları, storyboard ve video oynatıcı kütüphanesi eklendi.
- Asistan, Operatör ve Mühendis öğrenme yolu ile PDF katılım belgesi eklendi.
- Katılım belgesinin resmî yeterlilik veya akreditasyon sağlamadığı açıkça belirtildi.

# Değişiklik günlüğü

## 3.9.4
- Ayarlar ekranında çevrimdışı lisans süresi, önbellek ve benzeri dahili tanılama alanları gizlendi; yalnızca kullanıcıya dönük sürüm/platform/bağlantı durumu gösterilir.
- Windows ve Android uygulamaları açılışta kararlı güncelleme servisini otomatik denetler; yeni sürüm varsa bildirim ve mevcut güvenli indirme/kurulum akışı sunulur.
- Çevrimdışı durumda otomatik denetim sessiz kalır; güncelleme altyapısı ve lisans doğrulama alanları korunur.
- Windows ve Android sürümleri 3.9.4 / Android versionCode 30904 olarak eşitlendi.

## 3.9.2
- 11 çalışma dalındaki işlevler tek Windows/Android ürün akışında doğrulandı: çevrimiçi oturum, Türk GSM numarasıyla öğrenci girişi/kaydı, çevrimdışı imzalı lisans, cihaz aktarımı, FULL PAKET havale bildirimi ve yönetici onayı.
- Canlı Supabase `ses-merkezi-desktop` fonksiyonu güncel kaynakla eşitlendi; açık anahtar dağıtımı ve sunucu tarafı telefon kaydı etkinleştirildi.
- Çevrimdışı lisans doğrulaması için RS256 imza, kullanıcı/cihaz/platform bağlama, saat geri alma, lisans süresi ve 14 günlük ücretli / 7 günlük deneme sınırı regresyon testleri eklendi.
- Windows ve Android sürümleri 3.9.2 / Android versionCode 30902 olarak eşitlendi.
- Windows/Android paketleri ve kararlı yayın, tüm kalite kontrolleri yeşil olmadan yayımlanmış sayılmaz.


## 3.9.0
- Windows ve Android uygulama sürümleri 3.9.0 / Android versionCode 30900 olarak eşitlendi.
- Windows canlı RTA, iki saniyeyi aşan ses akışı kesintisini güncel olmayan veri olarak işaretler.
- Windows RTA'ya fiziksel 1 kHz / 94 veya 114 dB SPL ses kalibratörüyle oturumluk Z-ağırlıksız referans kalibrasyonu eklendi. Mikrofon frekans cevabı düzeltmesi veya IEC sınıf 1/2 uygunluğu iddia edilmez.
- Windows Acoustic Engine ekranına aynı ses kartının iki girişinden canlı H1 Transfer Function magnitude, phase ve coherence yakalama eklendi. CH0 referans, CH1 ölçüm mikrofonudur.
- Canlı RTA, SPL kalibrasyonu ve canlı TF için regresyon ve ürün sözleşmesi testleri eklendi.
- Ticari satış dokümantasyonu tek FULL PAKET ve yönetici onaylı havale/EFT modeline hizalandı.
- Yayın kararı Windows/Android CI, imza, SHA-256 ve fiziksel cihaz kabulü yeşil olmadan verilmez.



## 3.8.4
- Android sürümü 3.8.4 / versionCode 30804 olarak güncellendi.
- Windows uygulaması, kurulum betiği ve NSIS kurucu sürümü 3.8.4 ile eşitlendi.
- Windows ve Android arayüz sürüm etiketleri 3.8.4 olarak eşitlendi.
- Android WebView mikrofon/kamera izinleri ve RTA kapanış düzeltmeleri bu sürümün kaynak paketinde korunur.
- Kararlı dağıtım, mevcut Android imza anahtarı, Windows/Android paket testleri, SHA-256 ve latest.json doğrulaması tamamlanmadan yayımlanmış sayılmaz.

## 3.8.1
- Android WebView için mikrofon ve kamera izinleri ayrı ayrı ve birlikte yönetilir; yalnızca güvenilen uygulama kaynağından gelen medya istekleri kabul edilir.
- Mikrofon izni sonrasında giriş aygıtı adları ve listeleri yenilenir.
- Windows ve Android sürüm numaraları 3.8.1 olarak, Android versionCode 30801 ile eşitlendi.
- Kararlı güncelleme servisi, Windows EXE ve Android APK adresi ile SHA-256 değerlerini doğrulanmış latest.json manifestinden alır.


## 3.7.7
- Windows ve Android kaynak sürümleri 3.7.7 olarak eşitlendi; Android versionCode 30707.
- Kurucu, arayüz, proje dışa aktarımları ve sürüm doğrulama testleri 3.7.7 ile eşitlendi.
- Yayın paketleri, kalıcı imza ve kararlı güncelleme manifesti CI ve kabul testleri tamamlanana kadar değiştirilmez.

## 3.7.5
- Oda SPL haritası, oda sınırları dışındaki CSV ölçüm noktalarını enterpolasyona almadan reddeder; sınır testi regresyon paketine eklendi.
- Windows ve Android ortak araç motorları yeniden eşitlendi.
- Android sürümü `3.7.5` / `versionCode 30705`; Windows uygulaması ve kurulum paketi `3.7.5` olarak eşitlendi.
- Özel kaynak deposundaki runner atanmayan otomatik iş akışı tetiklemeleri kaldırıldı; derleme ve paket doğrulaması Stagepulse-Releases CI hattında yapılır.

## 3.7.4
- Windows uygulaması, kurulum paketi ve Android APK aynı 3.7.4 sürüm numarasına eşitlendi.
- Canlı mikrofon gecikme deneyinde bekleyen mikrofon izni sayfa gizlenince veya laboratuvardan çıkılınca iptal edilir; geç dönen mikrofon akışı ve AudioContext kapatılır.
- Dalga laboratuvarı mikrofon izin açıklaması ve örnek gecikmesi yuvarlama formülü düzeltildi.
- Android telefon ve tablet dokunmatik yerleşimleri, ortak Windows/Android motor eşitliği ve sürüm eşitliği kalite kontrollerine alındı.

## 3.7.1
- Windows EXE, Supabase yenileme belirtecini Windows DPAPI ile şifrelenmiş yerel oturum dosyasında saklar; uygulama açılışında belirteci yenileyip kullanıcı rolü ve lisansı sunucudan yeniden doğrular.
- Android APK, Android Keystore ile şifrelenmiş oturumu açılışta geri yükler; süresi dolan erişim belirtecini yeniler ve güncel hesap/lisans bağlamını alır.
- Kullanıcı çıkış yaptığında sunucu oturumu iptal edilir ve yerel oturum belirteçleri temizlenir. Geçici ağ hataları saklanan oturumu silmez.
- Windows ve Android için oturum kalıcılığı ve yenileme regresyon kontrolleri eklendi.

## 3.7.0
- Stagepulse Acoustic Engine eklendi: stereo WAV üzerinden Welch H1 Transfer Function, Magnitude, Phase, Coherence, Delay Finder ve Impulse Response/ETC hesapları.
- Analiz dosyası WebView üzerinden büyük JSON ses dizilerine dönüştürülmeden yerel Python/soundfile katmanında okunur; 2.000.000 örnek sınırı bellek kullanımını korur.
- Akustik analiz ekranı mevcut Canlı RTA sayfasına eklendi. Canlı iki kanallı ses kartı yakalama bu aşamada kapsam dışıdır; dB SPL kalibrasyonu veya Smaart uyumluluğu iddia edilmez.
- DSP testleri; unity gain, -6 dB kazanç, coherence, gecikme, polarite, impulse response, stereo WAV ve mono dosya reddini kapsar.
- Kulak eğitimine özgün kompresör ve gürültü kapısı (Noise Gate) dinleme alıştırmaları eklendi. Eşik, oran, diz, atak, bırakma, çıkış kazancı, bekletme ve kısma aralığı ayarlanabilir. A/B örnekleri çevrimdışı üretilir; ses motoru yalnızca kullanıcı oynatmayı başlattığında açılır.
- 70,7/100 V sabit gerilim hoparlör hattı hesaplayıcısı eklendi: tap yükleri, yedek güç payı, yükselteç anma gücü, hat akımı, bakır kablo direnci ve gerilim düşümü.
- Midas M32 / Behringer X32 .scn dosyaları için salt okunur kanal bağlantı raporu eklendi. Temel giriş blokları, kanal adları, fiziksel kaynaklar, preamp kazancı, gate, dinamik işlemci, EQ durumu ve bus gönderimleri CSV olarak dışa aktarılabilir. Dosya konsola geri yazılmaz.
- kablosuz frekans planlama aracı eklendi. Kullanıcı tarafından girilen frekans bandı, minimum kanal aralığı ve yerel tarama CSV verisiyle kanal önerisi üretir; temel üçüncü derece intermodülasyon çakışmalarını denetler. Hazır Türkiye frekans listesi veya yasal uygunluk iddiası içermez.
- Ölçüm CSV verisinden oda SPL ısı haritası eklendi. Ölçüm noktaları ters uzaklık ağırlıklı enterpolasyonla görselleştirilir; kalibrasyonsuz verinin mutlak SPL doğrulaması olmadığı belirtilir.
- Hoparlör eğitimi için Thiele–Small kapalı kutu ön hesabı ve Butterworth geçiş filtresi genlik hesabı eklendi. Sonuçlar gerçek kabin, FIR/IIR DSP dosyası veya FEM/BEM simülasyonu olarak sunulmaz.
- Ölçekli 2B sahne/ses-görüntü yerleşim aracı eklendi. Ekipman sürükleme, örnek sahne, oda/sahne ölçüsü, yaklaşık kablo uzunluğu, JSON plan ve CSV envanter dışa aktarımı bulunur.
- Yeni araçlar Stagepulse kaynak kodunda bağımsız olarak yazıldı. Harici ZIP arşivleri, CDN, çevrimiçi hesaplama servisi veya üçüncü taraf JavaScript çalışma zamanı bağımlılığı eklenmedi.
- Windows kurulum sürümü 3.7.0 olarak yükseltildi; derleme sırasında ana arayüz ve yeni araç dosyası ayrı ayrı JavaScript sözdizim kontrolünden geçirilir.


## 3.6.2
- Kulak eğitimi Web Audio motoru ve test gürültüsü artık uygulama açılışında oluşturulmaz; yalnızca kullanıcı ses çalma düğmesine bastığında başlatılır. Ses cihazı/izin hatası ana pencerenin diğer işlevlerini durdurmaz.
- Açılış modülleri bağımsız hata korumasına alındı. Bir modül başlatılamasa bile kalan araçların olay bağlantıları kurulmaya devam eder.
- Yakalanan JavaScript ve asenkron hatalar alt durum satırında görünür; hata ayrıntısı geliştirici konsoluna yazılır.
- Windows kurulum sürümü 3.6.2 olarak yükseltildi.

## 3.6.1
- Windows uygulama paketi PyInstaller `onedir` biçimine geçirildi. Tek dosyalı kurulum EXE'si korunurken uygulama bağımlılıkları kurulum sırasında `_internal` klasörüne açılır; uygulama her başlatıldığında büyük paketin geçici dizine yeniden çıkarılması önlenir.
- Kaldırıcı, uygulama EXE'si ve `_internal` bağımlılık klasörü dahil tüm kurulum dizinini kaldırır. `%APPDATA%` altındaki kullanıcı profilleri ve lisans önbelleği korunur.
- Kurulum ve paket bütünlüğü testleri yeni `onedir` yapısını doğrulayacak şekilde güncellendi.

## 3.6.0
- Profil boşken oluşan sonsuz asenkron profil yükleme döngüsü giderildi.
- İlk açılış lisans ekranına zorunlu yönlendirmesi kaldırıldı; yerel demo araçları erişilebilir.
- Başlangıçtaki sessiz güncelleme denetimi kapatıldı; ağ isteği yalnızca kullanıcı güncelleme düğmesine bastığında yapılır.
- NSIS script UTF-8 BOM ile kaydedilerek Türkçe kaldırma/kurulum metinlerindeki mojibake sorunu hedeflendi.
- Stagepulse ikonunun EXE ve masaüstü kısayolunda görünmesi için ikon varlığı ve PyInstaller parametresi eklendi.
- Manuel satış/ödeme takibi canlı Supabase veritabanı ve Edge Function sürüm 5 ile eşleştirildi; ödeme onayı sunucuda doğrulanıyor, ödemesi onaylanmamış anahtar etkinleştirilemiyor.
- Yönetici panelinde ödeme onaylama/geri alma ve lisans iptal akışı sunucu tarafına bağlandı.
- Yerel Ollama demo modunda çalışabilir; uzak/bulut AI çağrıları istemci arayüzü ve Python API katmanında lisans kontrolünden geçer.
- Üç konsol için Türkçe eğitim PDF'leri eklendi: Midas M32 Live, Yamaha CL5, Allen & Heath Avantis.

# Değişiklik günlüğü — Stagepulse Ses Mühendisliği Merkezi

## 3.5.3 — Tek kurulum ve öğrenciye dağıtım ZIP'i

- Tek `Setup.exe` tüm uygulama, Python bağımlılıkları, eğitim PDF'leri ve öğrenci araçlarını taşır. Son kullanıcıya Python/CMD/NSIS/PowerShell gerekmez.
- WebView2 çevrimdışı yükleyicisi artık uygulama EXE'sinin içine gömülmez; tek kurulum EXE'sinin içine alınır ve yalnızca gerekiyorsa kurulum sırasında geçici dizinden sessizce çalıştırılır.
- Kurulum klasöründe yalnızca `StagepulseSesMerkezi.exe` ve `Uninstall.exe` bırakılır. Masaüstü ve Başlat menüsü kısayolları ile Windows Program Kaldır kaydı oluşturulur.
- Başarılı derleme, öğrenciye gönderilmeye hazır ve içinde yalnızca `Stagepulse_Kurulum.exe` bulunan `ogrenciye_gonder/Stagepulse_Ogrenci_Kurulum_3.5.3.zip` paketini üretir.
- Testler, eksik WebView2 Runtime'ın kurulum sırasında ele alındığını ve runtime yükleyicisinin kurulu uygulama klasöründe bırakılmadığını kontrol eder.


- Profil testleri hem şifreli depo hem eski JSON geçiş yolunu geçici test klasörüne yönlendirir; geliştirici bilgisayarındaki gerçek profiller test sonucunu etkilemez.
- SHA-256 ile doğrulanmış NSIS ZIP'i çıkarılıp gerekli derleyici kopyalandıktan hemen sonra kaldırılır; paket bütünlüğü testi başlamadan kaynak ağacında ZIP kalmaz.
- Derleme/kurucu sürümü 3.5.2 olarak güncellendi. Öğrenci PDF’leri içerik açısından değişmediği için kendi belge sürümünde bırakıldı.

## 3.5.2 - Derleme test izolasyonu ve geçici arşiv temizliği

- Öğrenci profil testleri geliştirici bilgisayarındaki AppData dosyalarından ayrıldı; eski JSON geçişi yalnızca geçici test klasöründe çalışır.
- SHA-256 ile doğrulanan NSIS ZIP'i çıkarıldıktan hemen sonra, pytest başlamadan önce silinir.
- Tek kurulum EXE hedefi ve SHA-256 doğrulaması korunur.

# Değişiklik günlüğü

## 3.9.2
- 11 çalışma dalındaki işlevler tek Windows/Android ürün akışında doğrulandı: çevrimiçi oturum, Türk GSM numarasıyla öğrenci girişi/kaydı, çevrimdışı imzalı lisans, cihaz aktarımı, FULL PAKET havale bildirimi ve yönetici onayı.
- Canlı Supabase `ses-merkezi-desktop` fonksiyonu güncel kaynakla eşitlendi; açık anahtar dağıtımı ve sunucu tarafı telefon kaydı etkinleştirildi.
- Çevrimdışı lisans doğrulaması için RS256 imza, kullanıcı/cihaz/platform bağlama, saat geri alma, lisans süresi ve 14 günlük ücretli / 7 günlük deneme sınırı regresyon testleri eklendi.
- Windows ve Android sürümleri 3.9.2 / Android versionCode 30902 olarak eşitlendi.
- Windows/Android paketleri ve kararlı yayın, tüm kalite kontrolleri yeşil olmadan yayımlanmış sayılmaz.


## 3.5.1 - 29 Ekim 2026

- NSIS indirme hatası düzeltildi: ZIP indirme adresleri alternatif resmî SourceForge aynaları üzerinden yeniden denenir.
- İndirilen içerik ZIP başlığı, dosya boyutu ve yayımlanmış SHA-256 ile doğrulanır; hiçbir durumda hash kontrolü atlanmaz.
- Arşiv aynaları uyumsuz içerik döndürürse aynı NSIS 3.13 sürümünün kurulum dosyası sabit SHA-256 değeriyle doğrulanıp yalnızca geliştirici makinesine sessizce kurulur.
- Başarılı derleme sonunda geçici NSIS kurulum dosyası da temizlenir.
- Sürüm numarası kaynak kodu, kurucu ve öğrenci belgelerinde 3.5.1 ile eşleştirildi.

## 3.5.0 - 29 Ekim 2026

- Tek kurulum EXE’si üretimi: NSIS kurucusu uygulama EXE’sini içine alır, masaüstü ve Başlat menüsü kısayolu oluşturur.
- WebView2 Evergreen çevrimdışı yükleyicisi uygulama paketine eklenir; eksikse ilk açılışta kullanıcı bağlamında kurulur.
- `stagepulse.com.tr` üzerinden sürüm manifesti kontrolü; indirilen kurulum dosyası SHA-256 ile doğrulanır. Gerçek kurulum EXE’si ve `latest.json` siteye yüklenmeden otomatik güncelleme yayına alınmış sayılmaz.
- Supabase üzerinde lisans anahtarı hash’i, cihaz aktivasyonu, geçerlilik tarihi, iptal ve denetim kaydı.
- Öğrenci aşamaları yalnızca tanımlı Stagepulse sahibi hesabından sunucu tarafında işaretlenebilir.
- Yerel profiller Windows DPAPI ile kullanıcı hesabına bağlı şifrelenir.
- OpenAI, Gemini, Grok (xAI), GroqCloud, Ollama ve özel HTTPS sağlayıcısı için ayrı adaptörler; API anahtarı kalıcı profile yazılmaz.
- Başlangıç pencere boyutu ekran çözünürlüğüne göre seçilir, öğrenci PDF yedek kataloğu 10 belgeyi kapsar.

## Yayın öncesi kalan harici adımlar

1. `EXE_OLUSTUR.bat` Windows x64 ortamında çalıştırılıp gerçek `dist/StagepulseSesMerkezi-Kurulum-3.5.1.exe` üretilmeli.
2. EXE ve `website_release/latest.json`, Stagepulse indirme dizinine yüklenmeli.
3. Ücretli dağıtım öncesinde Stagepulse adına Authenticode kod imzalama sertifikası yapılandırılmalı. Stripe/iyzico gibi otomatik ödeme entegrasyonu bu sürümde yoktur; lisans anahtarları sahip panelinden elle oluşturulur.
4. Windows mikrofonu, WebView2 ilk kurulum ve sessiz güncelleme gerçek Windows cihazında uçtan uca test edilmeli.


## 3.5.1 Derleme betiği düzeltmesi

- Windows PowerShell 5.1'in akıllı tırnakları komut ayıracı olarak yorumlamasına yol açan metinler güvenli düz yazıyla değiştirildi.
- NSIS sessiz kurulum parametresinde boşluk içeren kurulum yolları doğru tırnaklanıyor.
- SHA-256 kontrolleri korunuyor; doğrulama başarısızlığında kurulum duruyor.


## 3.6.0 — Eğitim dalları ve lisans kapsamı

- Ortak temel eğitimden sonra 8 uzmanlık dalı: canlı ses, RF/IEM, PA/DSP, stüdyo, SPL/akustik, dijital konsol, konuşma/yayın ve kablolama/bakım.
- L0–L5 başlangıçtan usta/eğitmen onayına ölçütler ve güvenlik geçiş kapıları eklendi.
- Uygulama içinde uzmanlık seçimi, uygulama görevleri, yerel profil notu ve dal başına kısa bilgi testi eklendi. Bu tikler resmî öğretmen onayı değildir.
- Önerilen eğitim fiyatları ve makine tarafından okunabilir eğitim kataloğu eklendi. Fiyatlar yayın öncesi işletme maliyetiyle onaylanmalıdır.
- Lisans kaydına `bundle_code` kapsamı eklendi; yeni Supabase migration uygulanmalıdır. Paket kodu veritabanında saklanır, ancak her özellik için sunucu tarafı yetkilendirme ayrıca tamamlanmalıdır.
- Yeni sürüm kaynak testleriyle doğrulanır; Windows kurulum EXE'si, gerçek cihaz uygulamaları ve canlı Supabase deployment bu ortamda otomatik olarak yayımlanmış sayılmaz.


## 3.9.0 · Ölçüm güvenilirliği ve ticari akış temizliği

- Canlı stereo Transfer Function arayüzü Windows masaüstünde etkinleştirildi. Aynı ses kartında CH0 referans, CH1 ölçüm mikrofonu olarak kullanılır.
- RTA ve canlı TF, iki saniyeden uzun süren ses akışı kesintisini algılar; son spektrumu canlı veri olarak işaretlemez.
- Windows RTA'ya 1 kHz fiziksel ses kalibratörüyle 94/114 dB SPL oturumluk Z-ağırlıksız referans kalibrasyonu eklendi. Uygulama yeniden başlatıldığında kalibrasyon sıfırlanır.
- Kalibrasyonun mikrofon frekans cevabı düzeltmesi veya IEC sınıf 1/2 uygunluğu olmadığı arayüzde ve belgelerde açıklandı.
- Android belgeleri 3.9.0 ile hizalandı; Android'de canlı stereo TF ve fiziksel kalibratör entegrasyonu bulunmadığı belirtildi.
- Satış dokümantasyonu yalnızca FULL PAKET banka havalesi/EFT ve yönetici onayı modeline göre temizlendi.
- RTA/TF akış sağlığı ve SPL kalibrasyonu için regresyon testleri eklendi.
