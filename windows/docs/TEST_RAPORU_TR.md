# Tarihsel test raporu · Stagepulse 3.7.1 ve önceki sürümler

> Bu dosyadaki 117/117 test sonucu ve 3.7.1/3.6.2 açıklamaları tarihsel kayıttır; 4.0.0 için güncel CI sonucu olarak yorumlanmamalıdır. Güncel doğrulama, `main` dalındaki `.github/workflows/android-quality.yml`, `.github/workflows/build-windows-exe.yml` ve güvenlik iş akışlarının ilgili commit için verdiği sonuçlardan okunmalıdır.

## 4.0.0 için ayrı doğrulama kapsamı

- 13 özgün eğitim PDF'sinin açılabilirliği, metin kapsamı, sayfa içeriği ve Android/Windows byte eşitliği.
- Dokuz eğitim dalının katalogda bulunması; katalog JSON'unun iki platformda byte eşitliği.
- Windows ve Android arayüzlerinde 28 birincil ekranın aynı olması.
- Android Gradle Wrapper sürümünün kalite CI sürümüyle eşleşmesi.
- RF koordinasyonu ve miks/mastering anahtar konularının ilgili öğrenci PDF'lerinde bulunması.

Bu maddelerin başarılı olduğu ancak ilgili 4.0.0 commit'inin GitHub Actions koşuları tamamlandığında söylenebilir.


## 3.7.1 doğrulama kapsamı

- Yeni ön yüz dosyasının paket bütünlüğü ve HTML içindeki tüm doğrudan öğe kimlikleri denetlenir.
- Yeni araç kodlarının dış ağ, CDN veya çalışma anında kütüphane indirme bağımlılığı taşımadığı kontrol edilir.
- M32/X32 sahne okuyucusu için AES50-A/B kaynak eşlemesi, kanal adı, preamp, gate, kompresör ve bus gönderimi örnek verilerle sınanır.
- Kompresör ve gürültü kapısı işlemcilerinin çıktı uzunluğu ve sonlu sayısal değer üretmesi sınanır.
- Windows derleme betiği Node.js mevcutsa iki ana JavaScript dosyasını ve yerel araç çalışma zamanı testini yürütür.
- Windows kurulum dosyasının üretimi ve SHA-256 doğrulaması GitHub Actions derlemesinde yapılır.


## 3.6.2 başlangıç yanıt verebilirliği düzeltmesi
- Kulak eğitimi Web Audio motoru ve gürültü tamponu başlangıçtan kaldırıldı; ses motoru yalnızca kullanıcı etkileşiminde oluşturulur.
- Her başlangıç modülü bağımsız hata korumasıyla çalıştırılır; tek modül hatası kalan düğme bağlantılarını engellemez.
- JavaScript ve yakalanmamış asenkron hatalar uygulama durum satırına yansıtılır.
- Bu sürümün Casper üzerindeki gerçek sonuçları kurulumdan sonra kullanıcı bilgisayarında doğrulanmalıdır.

Bu rapor 3.6.2 kaynak düzeltmelerinin test kapsamını ve önceki sürümlere ait tarihsel bulguları kaydeder.

## 3.6.2 açılış paketi doğrulaması
- PyInstaller komutu `--onedir` ve `_internal` içerik dizinini kullanır; `--onefile` kullanılmaz.
- NSIS tek kurulum EXE'si, uygulama EXE'si ile `_internal` bağımlılık klasörünün tamamını kurulum dizinine kopyalar.
- Kaldırıcı tüm kurulum dizinini kaldırırken kullanıcı verilerinin bulunduğu `%APPDATA%\Stagepulse\SesMerkezi` klasörüne dokunmaz.
- Gerçek Windows açılış süresi ve 4 GB RAM'li hedef bilgisayardaki performans, yeni kurulum test edilmeden ölçülmüş sayılmaz.

**Son doğrulama: 117/117 otomatik test geçti.** Ayrıca `node --check ui/app.js`, `python -m py_compile Merkez.py core/*.py scripts/*.py` ve 13 öğrenci PDF’sinin açılabilirliği/metin bütünlüğü kontrol edildi. Bu kontroller fiziksel mikrofonu veya gerçek Windows kurulumunu çalıştırmayı ikame etmez.

## Otomatik kontroller

Son yerel çalıştırmada **117 otomatik test geçti**. Sentetik sinyal, formül ve taklit aygıt testleri dahildir; fiziksel PC mikrofonu ölçümü değildir.

- Python sözdizimi: `Merkez.py`, `core/`, `scripts/`.
- JavaScript sözdizimi: `ui/app.js`, `ui/rta_math.js`, `ui/acoustic_math.js`.
- RTA bant merkezleri, standart taban-10 bant kenar oranı, Python/JavaScript liste tutarlılığı, Nyquist üst bant sınırı, özel aralık kırpma, Hann pencereli FFT güç normalizasyonu, kesirli FFT-bin sınır ağırlığı, 20 Hz alt bantları, 18 kHz tiz sinyali ve callback gözetimi.
- SPL basınç↔seviye formülleri, enerji dB toplamı, noktasal kaynak mesafe kestirimi, geometrik alan/hacim, Sabine T60, yüzeylerden eşdeğer soğurma alanı A, eksenel oda modları ve 1–3 blok birikimli NIOSH referans dozu.
- RTA tavsiyesinin kesimle sınırlı olması, 8 kararlı örnek beklemesi ve pembe gürültü/kararlı test sinyali onayı olmadan üretim yapmaması.
- HTML DOM id eşleşmesi, dış CDN bağımlılığı kontrolü, PDF kitaplığı kataloğu, PDF dosyalarının gerçek PDF başlığı ile bütünlük kontrolü, yalnızca öğrenci belgelerinin EXE içine gömülmesi ve denetim raporlarının yerel HTTP üzerinden sunulmaması.
- Öğrenci profil ayrımı, kayıt güvenliği, dosya seçici sınırı, loopback sunucusunun ana ekran ve PDF sunması, Python kaynak kodunu sunmaması.

## Öğrenci materyalleri

Öğrenci PDF kataloğu: 13 dosya. Eğitmen kitapları, fiyat teklifleri ve iç denetim PDF'leri öğrenci kitaplığına alınmaz. Midas M32 Live, Yamaha CL5 ve Allen & Heath Avantis için eklenen üç ayrı 19 sayfalık uygulamalı eğitim PDF’si render edilip kontrol edildi. PDF ↔ uygulama karşılaştırması `docs/EGITIM_PDF_UYGULAMA_ESLESTIRMESI_TR.md` içindedir.

## Donanımda ayrıca doğrulanması gerekenler

- Windows x64 üzerinde `StagepulseSesMerkezi-Kurulum-3.6.0.exe` kurulumu ve `StagepulseSesMerkezi.exe` açılışı, PortAudio/Windows sürücüsü ve WebView2 ilk kurulum akışı. Bu Linux ortamında gerçek Windows EXE derlemesi yapılmamıştır.
- Dahili PC mikrofonu, USB ses kartı ve ölçüm mikrofonuyla gerçek RTA yanıtı; test tonu/ölçüm mikrofonu ve fiziksel frekans cevabı.
- Bilinen mikrofonla üst frekans karşılaştırması. 48 kHz akışın 20 kHz bandını matematiksel olarak kapsaması mikrofonun 20 kHz'de doğru ölçtüğünü kanıtlamaz.
- Düşük RAM'li Windows bilgisayarda uzun dosyalar için performans ve gerçek miks çıktısının dinlenerek incelenmesi.

## Ölçüm sınırları

RTA, yerel PortAudio mikrofon akışından FFT ile göreli dBFS RMS oktav/1/3 oktav bant gücü hesaplar. IEC 61260-1 veya IEC 61672 sınıf 1/2 uyumluluğu, kalibre edilmiş dB SPL, faz/transfer-function ya da mikrofon frekans cevabı garantisi vermez. SPL mesafe aracı sadece serbest alan noktasal kaynak yaklaşımıdır; alan hesaplayıcısı gerçek polar/akustik simülasyonu değildir. NIOSH doz hesabı mesleki referans eğitimidir, mevzuat uygunluk sonucu değildir.

## Önceki sürüm 3.3.1 görsel/SPL denetimi (tarihsel kayıt)

- Uygulama içindeki SP metin simgesi, siyah-altın-beyaz vektör Stagepulse wordmark ve dalga işaretiyle değiştirildi.
- SPL/alan ekranına hesaplanan 2D noktasal-kaynak haritası ve aynı formülün 3D yüzeyi eklendi.
- Fiziksel dB basınç/genlik ve yoğunluk/güç ilişkisi görseli eklendi.
- Fotogerçekçi salon görseli sayı etiketi taşımayan kavramsal illüstrasyon olarak işaretlendi; sayısal tahmin yerine kullanılmıyor.
- Öğrenci kataloğuna 09_SPL_dB_3D_Gorsel_Atlasi.pdf eklendi.

- Yeni `tests/test_visual_assets.py` kontrolleriyle marka varlığı, 2D/3D harita formülü, dB oranları, PDF render edilebilirliği ve öğrenci kataloğu doğrulanır. Son test: `pytest -q` → 79 geçti.
- Chromium headless tarayıcı testi bu yürütme ortamında yerel `127.0.0.1` adresini kurum politikasının engellemesi nedeniyle tamamlanamadı; gerçek Windows WebView2/EXE ve mikrofon testi ayrıca gerekir.


## Önceki sürüm 3.3.1 derleme düzeltmesi (tarihsel kayıt)

Windows derleme testi `tests/test_visual_assets.py` dosyasında `fitz` modülü bulunamadığı için başlamadan duruyordu. `fitz`, PyMuPDF paketinin Python modülüdür. `PyMuPDF` ve `Pillow` artık açık bağımlılık olarak `requirements.txt` içinde tanımlıdır; testler çalıştırılmadan EXE derlemesine geçilmez.


## 3.5.2 ürün ve ticari özellik denetimi

- Tek kurulum EXE’si için NSIS betiği, masaüstü ve Başlat menüsü kısayolu, kaldırma kaydı ve kullanıcı profilini koruyan yükseltme akışı kontrol edildi.
- Lisans tablolarında RLS etkin, istemci rollerine doğrudan tablo erişimi verilmemiştir. Edge Function sürüm 5; manuel satış/ödeme durumu, lisans oluşturma/listeleme/iptal, cihaz aktivasyonu ve öğretmen onayını sunucu tarafında yetkilendirir. Ödemesi `paid` olmayan anahtarın aktivasyonu veritabanı fonksiyonunda reddedilir.
- Öğretmen panelindeki lisans listesi anahtarın kendisini veya hash’i göstermez; yalnızca lisans metaverisi ve etkin cihaz sayısını gösterir. İptal işlemi sunucuda doğrulanır.
- Windows Setup EXE bu Linux ortamında derlenmedi. Gerçek indirme EXE’si ve `latest.json` henüz Stagepulse sitesine yüklenmediği sürece müşterilerde otomatik güncelleme canlı kabul edilmez.
- Ödeme kuruluşu entegrasyonu (Stripe/iyzico), Authenticode kod imzası ve gerçek Windows mikrofon/EXE uçtan uca denemesi ayrıca gereklidir.


## 3.6.0 tek kurulum ek kontrolü

- WebView2 Standalone Installer artık yalnızca NSIS kurulum paketine eklenir ve gerekiyorsa `$PLUGINSDIR` içinden `/silent /install` ile çalıştırılır.
- PyInstaller uygulama EXE'sine Runtime Installer ikinci kez gömülmez.
- Öğrenci ZIP'i derleme sonunda oluşturulur ve yalnızca `Stagepulse_Kurulum.exe` dosyası içerdiği doğrulanır.
- Kurulu uygulama klasöründe `StagepulseSesMerkezi.exe`, `_internal` bağımlılık klasörü ve `Uninstall.exe` bulunması beklenir. Gerçek Windows kurulumunda bu dosya düzeni ayrıca doğrulanmalıdır.


## 3.6.0 kaynak doğrulaması

- `pytest -q --disable-warnings --maxfail=1`: 117 geçti.
- Python modülleri için `py_compile`; `ui/app.js`, `ui/acoustic_math.js`, `ui/rta_math.js` için Node sözdizimi kontrolü başarılı.
- Öğrenci kütüphanesindeki 13 PDF açıldı; metin çıkarımı ve sayfa sayısı kontrol edildi. Midas M32, Yamaha CL5 ve Avantis kitapları 19’ar sayfadır.
- Stagepulse ikon dosyası ICO/PNG olarak doğrulandı ve PyInstaller/NSIS kaynaklarına bağlandı.
- Supabase canlı veritabanında ödeme sütunları eklendi; Edge Function `ses-merkezi-desktop` sürüm 5 ve `verify_jwt=true` olarak etkin.
- Gerçek Windows Setup EXE’si bu Linux ortamında derlenmedi. Windows x64 bilgisayarda `EXE_OLUSTUR.bat` çalıştırılmalı; sonra kurulum, masaüstü simgesi, ilk açılış hızı ve mikrofon testi gerçek bilgisayarda kontrol edilmelidir.


## EBU Tech 3341 V4.0 ve OAA çapraz kontrol notu

Kaynak: EBU Tech 3341 V4.0, Kasım 2023, Tablo 1 (özellikle PDF sayfa 8-9). Referans eşlemeleri `windows/references/ebu_tech3341_reference.csv` dosyasındadır. Bu CSV, ZIP içindeki WAV dosya adları ile standartta açıkça verilen beklenen değerleri eşler; test sinyallerinin kendisini içermez. CSV, Windows EXE paketine `references/` dizini olarak dahil edilir ve `validate_ebu_test_set()` tarafından otomatik yüklenir. Kullanıcının CSV dosyası seçmesi/yüklemesi gerekmez; yalnızca EBU WAV test klasörü seçilir.

- Dosya-temelli referans eşlemesi: test 1-10, 12-13 ve 15-23.
- Test 11 ve 14: canlı ölçer için art arda 20 Short-term/Momentary değer gerektirir. Mevcut toplu dosya ölçümü bu zaman dizisini doğrulamadığından bu testler kapsam dışıdır.
- Test 6: 5.0 kanal PCM dosyası kullanılır. 6 kanallı sessiz LFE varyantı bu ölçüm yolunda desteklenmez.
- Test 15-23: true-peak toleransı asimetriktir (+0.2/−0.4 dBTP); referans karşılaştırması bunu ayrı üst/alt toleranslarla uygular.
- CSV'de yalnızca EBU Tablo 1'in beklenen değer verdiği metrikler doldurulur. PASS yalnızca doldurulmuş kriterleri kapsar; boş alanlar doğrulanmış sayılmaz.
- EBU Tech 3342 LRA testleri ayrı bir standart/test kapsamıdır. Bu raporda LRA için beklenen referans değerleri uydurulmamıştır.

**Kullanım ve telif sınırı:** EBU test dizileri yalnızca iç Ar-Ge amaçlı performans değerlendirmesi için sağlanır; ticari/iş/kâr amaçlı kullanım ve test dizilerini kopyalama, değiştirme, yayımlama veya dağıtma yasaktır. Bu nedenle WAV arşivi, EBU PDF'si ve bunlardan oluşan test artifact'leri Stagepulse deposuna veya dağıtım paketlerine eklenmez. Stagepulse ticari ürün doğrulaması için kullanım öncesinde EBU'dan yazılı izin alınmalıdır. Resmî kaynaklar: https://tech.ebu.ch/publications/ebu_loudness_test_set ve EBU kullanım koşulları: https://tech.ebu.ch/files/live/sites/tech/files/shared/testmaterial/use%20of%20EBU%20AUDIO%20test%20sequences.pdf.

**OAA CLI:** Yüklenen `oaa-cli-Windows.zip`, resmî Open Audio Analyzer v0.16.0 Windows release SHA-256 değeriyle eşleşir. CLI Stagepulse'a gömülmez; resmî sürümden ayrı edinilip aynı WAV dosyalarında bağımsız karşılaştırma için çalıştırılır. OAA çıktısı EBU sertifikası veya mutlak referans cihaz sonucu değildir. Resmî release: https://github.com/JonasGrunau/open_audio_analyzer/releases/tag/v0.16.0.
