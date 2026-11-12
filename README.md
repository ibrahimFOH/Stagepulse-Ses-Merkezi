# Stagepulse Ses Merkezi

Stagepulse Ses Merkezi; Windows masaüstü uygulaması ve Android uygulamasından oluşan Türkçe ses mühendisliği platformudur. Yönetici hesabı ve yetkileri ana uygulama içindeki giriş/oturum akışıyla yönetilir. Son kullanıcı paketleri ayrı Stagepulse-Releases deposunda üretilir.

## 4.0.3 Sistem tasarım araçları ve mühendislik güncellemeleri

- Line Array Designer: kabin sayısı, splay, aiming ve askı yüksekliği için geometrik yan görünüş.
- SPL Coverage: iki eşit noktasal kaynağa dayalı, serbest alan varsayımlı yaklaşık 2D seviye haritası.
- Sub-Top Alignment: referans noktasına göre geometrik yol farkı, gecikme hedefi ve crossover faz kestirimi.
- Sistem taslağı JSON dışa aktarımı; Android ve Windows ortak arayüz/hesaplama kodu.
- Model sınırları arayüzde açıklanır; polar/GLL verisi, oda yansımaları ve saha ölçümü yerine geçmez.

## Önceki sürümden gelen SPL/RTA ölçüm ve mikrofon entegrasyonları

- Windows ve Android canlı RTA ekranlarında 1/1, 1/3, 1/6, 1/12, 1/24 ve 1/48 oktav bant çözünürlükleri.
- Android mikrofon akışında PCM tabanlı FFT; bant güçleri dBFS RMS olarak hesaplanır.
- Ölçüm mikrofonu frekans düzeltmesi CSV profiliyle RTA spektrumuna uygulanabilir.
- Windows stereo WAV analizine A/C/Z ağırlıklı Leq, Fast/Slow maksimum, Peak ve L10/L50/L90 istatistikleri eklendi.
- Mevcut yönetici panelinden gelişmiş RTA ve mikrofon correction özellikleri merkezi olarak açılıp kapatılabilir; ayarlar Supabase üzerinde tutulur.
- Yönetici panelinde mikrofon/kalibratör bilgileri ve saha kontrol kaydı bulunur. Operatör saha kaydı IEC uygunluk sertifikası değildir.

## Önceki sürümden gelen entegrasyonlar

- Windows ve Android'e OSC/UDP gönderimi eklendi; M32/X32 için varsayılan UDP portu 10023.
- İki platformda standart MIDI Type 0 dosyası oluşturulabilir.
- Arşivdeki SPL/FFT, elektrik/kablo ve RF araçları mevcut daha gelişmiş Stagepulse araçlarıyla çakıştığı veya güvenilir ölçüm üretmediği için tekrar eklenmedi.

## Önceki sürümden gelen son düzeltmeler

- Android Compressor ve Gate kulak eğitimi A/B dinleme, rastgele sınav ve stilleriyle doğrulandı.
- SPL 2D/3D kaynak seçimi ve sürükleme koordinatları düzeltildi.
- Android kalite denetimi Compressor/Gate arayüz bileşenlerini ve sürüm eşleşmesini kontrol eder.

## Önceki sürümden gelen arayüz ve SPL iyileştirmeleri

- Öğrenci ekranında görünür FULL PAKET satın alma/lisans kısayolu.
- Destek ve iletişim düğmeleri doğrudan Stagepulse WhatsApp hattını açar.
- SPL 2D/3D haritası seçilen PA, sub ve monitör kaynaklarının konum/seviye/yön bilgisiyle canlı güncellenir.
- SPL ekipmanları kategoriye göre listelenir; eklenebilir, seçilebilir, düzenlenebilir ve 2D haritada sürüklenebilir.
- Compressor ve Gate kulak eğitimi A/B dinleme ve rastgele sınavları korunmuştur.

## Platform sürümleri

Kaynak sürümü 4.0.4'tür. Aşağıdaki sürüm bilgileri kaynak ağacını tanımlar; tek başına Release deposunda imzalı kurulumların yayımlandığını veya fiziksel cihaz kabul testlerinin tamamlandığını göstermez.

| Bileşen | Kaynak sürümü | Sürümün yönetildiği yer |
|---|---:|---|
| Windows Ses Merkezi | 4.0.4 | windows/Merkez.py ve windows/EXE_OLUSTUR.ps1 |
| Android Ses Merkezi | 4.0.4 (40004) | android/app/build.gradle |
| Yönetici girişi | Ana uygulama içinde | Ana uygulamanın kimlik doğrulama ve yetki kontrolü |

4.0.4 kaynak sürümüdür. Windows EXE ve imzalı Android APK, Windows/Android kalite kontrolleri yeşil olduktan sonra `Stagepulse-Releases` deposunda kararlı sürüm olarak yayımlanır; indirme manifesti ve SHA-256 dosyaları da aynı sürümle üretilir. Android APK kalıcı Stagepulse keystore ile imzalanmıştır. Windows EXE şu an Authenticode kod imzası taşımamaktadır; Windows SmartScreen uyarısı görülebilir. Yönetici hesabı girişi ana uygulamanın içindedir; ayrı yönetici EXE/APK derlenmez veya yayımlanmaz.

## Uygulama ekranları ve araç envanteri (4.0.3)\n\nArayüzün tüm sayfalarında ve öğrenci PDF kitaplığındaki 13 kitapta teknik terimler Türkçe ad + İngilizce karşılık biçiminde gösterilir; PDF'lerde ortak terim sözlüğü de bulunur.

Windows ve Android arayüzlerinde aynı 28 çalışma ekranı bulunur. Ekran adlarının ortak olması, donanıma bağlı işlevlerin iki platformda birebir aynı olduğu anlamına gelmez; platform farkları aşağıda ayrıca belirtilmiştir.

| Alan | Ekranlar ve kapsam |
|---|---|
| Temel ses ve eğitim | Ana sayfa, Frekans Bulucu, Kulak Eğitimi, Teknik Hesaplayıcılar, Ses Katmanı Atölyesi, Sanal Mikser Laboratuvarı |
| Ölçüm ve analiz | SPL/Alan Planı, Canlı RTA, WAV Kalite Analizi, LUFS Normalizasyonu, Oda SPL Haritası, Dalga/Faz/Gecikme Laboratuvarı |
| Sistem ve saha | Sahne/AV Planı, Mikser Patch Raporu, RF Frekans Planı, 70,7/100 V Dağıtım Hesabı, Hoparlör/DSP Tasarım Eğitimi, OSC/MIDI Araçları |
| Operasyon ve içerik | Cue/Video Notları, Kontrol Listeleri, Türkçe Kılavuzlar, Öğrenci PDF Kitaplığı, Video Ders Kütüphanesi |
| Öğrenme ve hesap | Eğitim Müfredatı, Öğrenci İlerlemesi, AI Asistanı, Hesap/Lisans/Güncelleme, Ayarlar/Gizlilik |

### Platforma göre doğrulanmış kapsam sınırları

- Windows: yerel ses girişinden RTA; oturumluk 1 kHz kalibratör referansıyla Z gösterimi; stereo WAV analizinde A/C/Z Leq, Fast/Slow maksimum, Peak ve L10/L50/L90; aynı ses kartının iki girişinden canlı H1 Transfer Function; DeMan K-weighting ile BS.1770 tabanlı LUFS/LRA normalizasyonu ve 48 kHz için BS.1770-5 Annex 2 4-faz FIR true-peak ölçümü; EBU Loudness Test Set klasörünü ve operatörün referans CSV'sini kullanarak toplu karşılaştırma; yerel Ollama ve isteğe bağlı Groq.
- Android: WebAudio mikrofon akışından RTA; 1 kHz kalibratörle oturumluk Z/RMS düzeltmesi; aynı USB ses kartının iki girişinden stereo H1 Transfer Function; WAV analizinde desteklenen biçimlerde peak/RMS; tarayıcı tabanlı yaklaşık LUFS/LRA ve 4x true-peak tahmini; EBU Loudness Test Set toplu doğrulaması Windows masaüstüne özeldir; Groq sağlayıcısı.
- Her iki platform: sahne/AV planlama, patch raporu, RF ön koordinasyon, 70/100 V hesabı, oda SPL haritası, hoparlör/DSP ön hesabı, dalga/faz laboratuvarı, OSC gönderimi ve MIDI Type 0 üretimi.
- OSC/UDP gönderimi tek yönlüdür; mikserden durum/yanıt veya komutun uygulandığına dair teyit sağlamaz.
- RF aracı koordinasyon ön çalışmasıdır; spektrum analizörü veya yasal frekans tahsis belgesi değildir. PA/SPL haritaları üretici polar/GLL verisi ve gerçek saha ölçümünün yerine geçmez.
- RTA/FFT ve oturumluk kalibrasyon IEC 61672 veya IEC 61260 sınıf uygunluğu sağlamaz. Transfer Function sonuçları da tek başına sistemin doğru hizalandığını kanıtlamaz.
- Eğitim/video kütüphanesindeki içerik ve ekranların bulunması, bütün videoların yayımlandığı veya her eğitim görevinin gerçek donanımda tamamlandığı anlamına gelmez.

### Eğitim PDF güncellemesi

4.0.3 öğrenci kitaplığındaki canlı ses PDF'si RF tarama, intermodülasyon, anten ve IEM koordinasyonu; stüdyo PDF'si miks/mastering, LUFS, true peak ve dither konularını kapsar. PDF üretim hattı bu kitapları Windows ve Android varlıklarına aynı dosya içeriğiyle yazar ve doğrular.

### Eğitim kataloğu

Eğitim sistemi dokuz dal içerir: Canlı Ses/FOH/Monitör, RF/Kablosuz Mikrofon ve IEM, PA Sistem Tasarımı/DSP/Array, Stüdyo/Kayıt/Düzenleme/Miks, SPL/Akustik/Gürültü Ölçümü, Dijital Konsol, Konuşma/Podcast/Yayın, Kablolama/Bakım/Arıza Teşhisi ve Miks/Mastering. Yeterlilik basamakları L0–L5'tir. Öğrenci kitaplığında 13 özgün PDF bulunur; uygulama içindeki 12 konu kılavuzu bunlardan ayrı dokümanlardır. Katalog dosyası Windows ve Android varlıklarında byte düzeyinde aynı tutulur.

## Depo düzeni

- windows/: Windows uygulaması, Python ses motorları, eğitim belgeleri, testler ve kurucu.
- android/: Kotlin ana uygulaması, WebView arayüzü, çevrimdışı eğitim içeriği, Android köprüsü ve Android kalite denetimleri.
- admin-app/: Önceki ayrı yönetim istemcisi kaynakları; kararlı yayın iş akışına dahil değildir.
- shared/: Platformlar arası ortak çalışma notları.

Stagepulse ana web sitesi içeriği bu çalışma kapsamında değiştirilmedi.

## Ölçüm araçlarının güncel kapsamı

Windows masaüstü sürümünde canlı RTA, oturumluk 1 kHz ses kalibratörü referansıyla dB SPL Z gösterimi ve aynı ses kartının iki giriş kanalından canlı H1 Transfer Function bulunur. Stereo TF'de CH0 referans, CH1 ölçüm mikrofonudur. Kalibrasyon mikrofon frekans düzeltmesi veya IEC sınıfı ölçüm uygunluğu sağlamaz. Gerçek ses kartı, mikrofon ve saha kabul testleri otomatik kaynak testlerinden ayrı doğrulanmalıdır.

Ticari satış modeli yalnızca FULL PAKET'tir. Eğitim dalları ayrı satış ürünü değil, FULL PAKET içindeki dokuz öğrenme/yeterlilik yoludur. Katalog JSON'unda kalan eski paket kodları veritabanı/geriye dönük uyumluluk içindir; aktif ayrı satış ürünleri değildir. Eğitim kataloğu ve açık doğrulama kapıları `windows/docs/EGITIM_DALLARI_USTA_YOLU_VE_FIYATLANDIRMA_TR.md` içinde tutulur.

## Android geliştirme ve doğrulama

Gerekli araçlar: JDK 17, Android SDK Platform 35, Android Build Tools 35.0.0, Gradle 8.13 (wrapper ve CI ile eşleşir), Android Gradle Plugin 8.13.2, Node.js 22 ve Python 3.12.

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

## SPL/RTA ölçüm motoru: mevcut kapsam ve sınırlar

Windows canlı RTA motoru ve Android WebAudio PCM yakalama zinciri 1/1, 1/3, 1/6, 1/12, 1/24 ve 1/48 oktav çözünürlüklerini destekler. Android tarafında PCM örnekleri Hann pencereli FFT ile analiz edilir; bant seviyeleri dBFS RMS olarak gösterilir. Ölçüm mikrofonu CSV düzeltmesi RTA bant grafiğine uygulanabilir.

Windows stereo WAV analiz ekranı A/C/Z ağırlıklı Leq, Fast/Slow maksimum, Peak ve 1 saniyelik L10/L50/L90 sonuçlarını gösterir. Kalibrasyon offset'i olmadan değerler dBFS olarak etiketlenir. Yönetici panelinden gelişmiş RTA ve mikrofon düzeltme özellikleri Supabase üzerinde merkezi olarak yönetilir. Mikrofon, kalibratör ve saha kontrol bilgileri yerel saha kaydı olarak dışa aktarılabilir.

Gerçek mikrofon/ses kartı saha testi, izlenebilir kalibrasyon, ölçüm mikrofonu üretici correction dosyasının doğrulanması ve IEC 61672 / IEC 61260 uygunluk testleri laboratuvar veya yetkin saha ekipmanıyla ayrıca yapılmalıdır. Uygulama bu standartlara uygunluk sertifikası iddia etmez.


## EBU Tech 3341 doğrulaması ve bağımsız OAA karşılaştırması

Stagepulse Windows loudness test aracı, EBU Tech 3341 V4.0 (Kasım 2023) Tablo 1'de açıkça tanımlanan ölçütleri uygulama paketine gömülü referans CSV'sinden otomatik okuyarak karşılaştırır. Kullanıcının referans CSV yüklemesi gerekmez; yalnızca resmî EBU WAV test setini indirip çıkarması ve klasörü seçmesi gerekir. Referans CSV'de 59 dosya/kriter eşlemesi bulunur: test 1-10, 12-13 ve 15-23. Test 11 ve 14 canlı ölçerde art arda 20 değer üretmeyi gerektirir; mevcut dosya-temelli toplu ölçüm yalnızca maksimum değer çıkardığı için bu iki test PASS sayılmaz. Test 6 için 5.0 kanal dosyası kullanılır; sessiz LFE kanalı eklenmiş 6 kanallı WAVEEX varyantı mevcut ölçüm kapsamına dahil değildir.

- Referans dosyası: `windows/references/ebu_tech3341_reference.csv`; Windows EXE içine `references/` olarak paketlenir ve uygulama tarafından otomatik yüklenir.
- Test motoru: `windows/core/audio_tools.py` içindeki `validate_ebu_test_set()`
- Loudness toleransı: Tech 3341 Tablo 1'de belirtilen ±0.1 LU.
- True Peak toleransı: +0.2 / −0.4 dBTP; kod bu toleransı asimetrik uygular.
- PASS, yalnızca CSV'de doldurulmuş referans metriklerinin geçtiğini belirtir. Boş metrikler test edilmemiştir; bu sonuç EBU/ITU sertifikası veya tam uygunluk beyanı değildir.
- LRA testleri EBU Tech 3342 kapsamındadır; bu CSV'de LRA için doğrulanmış beklenen değer bulunmadığından LRA sütunu boş bırakılmıştır.

### EBU test sinyallerinin kullanım kısıtları

EBU test seti Git deposuna, GitHub Actions artifact'lerine veya Stagepulse dağıtım paketlerine kopyalanmaz. EBU kullanım koşulları test sinyallerini yalnızca kurum içi Ar-Ge kapsamında ses ekipmanı/sistem performansını değerlendirmek için sınırlar; ticari, iş veya kâr amaçlı kullanım ile kopyalama, değiştirme, yayımlama ve dağıtım yasaktır. Stagepulse ticari ürün geliştirme/satış doğrulaması için bu sinyallerin kullanımı, EBU'dan ayrıca yazılı izin alınmadan yapılmamalıdır.

- Resmî test seti: https://tech.ebu.ch/publications/ebu_loudness_test_set
- EBU ses test dizileri kullanım koşulları: https://tech.ebu.ch/files/live/sites/tech/files/shared/testmaterial/use%20of%20EBU%20AUDIO%20test%20sequences.pdf
- EBU Tech 3341 V4.0: https://tech.ebu.ch/publications/tech3341

Test 15-23 sinyalleri yüksek seviyelidir; EBU uyarısı gereği normal dinleme seviyesinde dinlenmemelidir. Testler yalnızca dosya analiziyle yürütülmelidir.

### OAA CLI ile çapraz kontrol

Yüklenen Windows CLI arşivinin SHA-256 değeri resmî Open Audio Analyzer v0.16.0 Windows release varlığıyla eşleşir: `e93544a6dbde956bba2c2f7a74575b82b19eb95750d91eae159d076836bdfa9c`. Bu araç Stagepulse'a gömülmez ve ikili dosyası depoya kopyalanmaz; resmî kaynaktan ayrı indirilir.

1. Resmî sürüm: https://github.com/JonasGrunau/open_audio_analyzer/releases/tag/v0.16.0
2. Arşivi açın; `bin/oaa.exe` ile `lib/oaa_engine.dll` dosyalarının göreli konumunu koruyun.
3. Bir WAV dosyasını metin raporuyla analiz edin: `bin/oaa.exe "dosya.wav"`
4. JSON raporu alın: `bin/oaa.exe --format json "dosya.wav"`
5. Stagepulse ile OAA sonuçlarını aynı kaynak WAV, aynı kanal düzeni ve aynı örnekleme hızı üzerinden karşılaştırın. Farkları otomatik olarak hata saymayın; algoritma sürümü, K-weighting, gating, kanal haritası ve true-peak filtreleri aynı olmalıdır.

OAA bağımsız bir karşılaştırma aracıdır; EBU tarafından sertifikalandırılmış referans cihaz olarak sunulmaz. OAA motorunun GPL-3.0-or-later lisansı vardır. İkili dosyanın dağıtılması halinde ilgili lisans ve karşılık gelen kaynak kod yükümlülükleri ayrıca yerine getirilmelidir. Kaynak: https://github.com/JonasGrunau/open_audio_analyzer
