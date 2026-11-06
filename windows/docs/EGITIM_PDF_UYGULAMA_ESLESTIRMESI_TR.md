# Öğrenci PDF'leri ↔ Uygulama eşleştirme denetimi — 3.5.2

Bu dosya geliştirme/kalite notudur; öğrenci PDF kitaplığında gösterilmez. Öğrenci dağıtımında yalnızca `egitim_paketleri/` altında kataloglanan on öğrenci PDF’si bulunur. EXE’ye ayrıca öğrenci arayüzünde açıkça listelenen 11 eğitim Markdown rehberi eklenir; `TEST_RAPORU_TR.md`, bu eşleştirme dosyası ve birleştirme matrisi EXE’ye eklenmez ve yerel HTTP üzerinden sunulmaz.

## Bire bir eşleştirme

| PDF | PDF'deki öğrenme hedefi | Uygulamadaki karşılık | Denetim sonucu / sınır |
|---|---|---|---|
| `00_Uygulama_Kullanimi_Ogrenci.pdf` | Uygulama akışı, güvenli çalışma, RTA ve PDF kullanımı | Tek pencere, araç menüleri, öğrenci profili, PDF kitaplığı | 3.5.2 için yeniden oluşturuldu. Tek dosya Windows EXE ve fiziksel PC mikrofonu testi bu çalışma ortamında doğrulanamadı. |
| `01_Ses_Muhendisligi_Ogrenci_Ders_Kitabi.pdf` | Dalga/periyot, dB oranları, dalga boyu, oda modları, Sabine T60 | dBu↔Vrms, enerji dB toplamı, gecikme, dalga boyu/λ/4/λ/2, oda eksenel modları, yeni Sabine T60 hesaplayıcısı | Formül eşleştirmesi eklendi. Sabine girdisi eşdeğer soğurma alanı A olmalı; toplam duvar alanı ile aynı değildir. Yeni yüzey hesaplayıcısı A=Σ(αᵢ×Sᵢ) katkılarını oda yüzeyleri üzerinden hesaplar ve seçilen 125 Hz–8 kHz bandına ait α katsayıları ister; başlangıç katsayıları yalnızca örnektir. |
| `02_Canli_Ses_Live_Sound_Ogrenci_Dersleri.pdf` | FOH iş akışı, gain, PA, delay, DSP, ölçüm sınırları | Teknik hesaplayıcılar, SPL mesafe kestirimi, alan geometrisi, RTA ve eğitim PDF'leri | Konsol simülatörü değildir; gerçek Midas/Yamaha/A&H mikseri uygulama tarafından kontrol edilmez. |
| `03_Studio_Ses_Muhendisligi_Ogrenci_Dersleri.pdf` | Kayıt, düzenleme, miks, dijital ses, peak/RMS/LUFS ve teslim | Yerel WAV analiz, LUFS normalizasyon, çok katmanlı ön miks | Ses katmanı kompresör/gate/EQ işlemleri eğitim amaçlı yaklaşık DSP'dir; profesyonel DAW/limiter yerine geçmez. |
| `04_Dijital_Ses_Mikseri_Ogrenci_Calisma_Kitabi.pdf` | Gerçek mikser üzerinde kontrollü görevler, sinyal akışı, gözlenebilir kanıt | Öğrenci ilerlemesi, kontrol listeleri, ders rehberleri | Bu bir donanım emülatörü değildir. Fader/phantom/bus işlemleri gerçek konsolda eğitmen gözetiminde yapılır. |
| `05_Canli_Ses_Mikseri_Hizli_Basvuru.pdf` | Gain, phantom, HPF, mute, bus ve sahne öncesi kontroller | PDF kitaplığı ve kontrol listeleri | Bilgi referansıdır; uygulama fiziksel konsola komut göndermez. |
| `06_Ogrenci_Uygulama_Formlari.pdf` | Uygulama sonuçları, ölçüm notları, öz değerlendirme | Öğrenci profili/ilerleme ve PDF dışa aktarma | PDF formları eğitim kaydı olarak kalır; tüm form alanlarını uygulama içinde otomatik doldurma mevcut kapsamda yoktur. |
| `07_Saha_Olcumu_SPL_Raporlama_Egitimi.pdf` | dB SPL, p0=20 µPa, LAeq/LAFmax/LASmax/LCpeak, A/C/Z, kalibrasyon ve mesafe kaybı | Pa↔dB SPL, dB enerji toplamı, referans seviye/mesafe kestirimi, yüzey soğurma alanı/Sabine ve birikimli NIOSH maruziyet kestirimi, RTA | Gerçek kalibreli SPL metre veya LAeq ölçer yoktur. PC mikrofonunun dBFS çıktısı dBA/dB SPL olarak kullanılamaz. |
| `08_SPL_Alan_RTA_Teknik_Uygulama_Eki.pdf` | Çözümlü SPL, mesafe, alan, Sabine, maruziyet ve RTA sınırları | SPL/alan sayfası, Sabine T60, NIOSH maruziyet, RTA aday kesim paneli | Yeni ek güncellendi ve PDF kitaplığına eklendi; yüzey soğurması/Sabine örneği ve güvenlik sınırları eğitim anlatımına bağlandı. Çıktı gerçek saha ölçümünü taklit ettiğini iddia etmez. |

## Formül/doğru değer denetimi

### Düzeltildi/eklendi

- Ses basınç seviyesi: `Lp = 20 log10(pRMS / 20 µPa)`; ters dönüşüm `pRMS = 20 µPa × 10^(Lp/20)`.
- dB enerji toplamı: `10 log10(Σ 10^(Li/10))`; örneğin 90 dB + 90 dB = 93,01 dB. Koherent/ faz ilişkili kaynaklar için bu toplam dizinin gerçek cevabını tek başına vermez.
- Serbest alan noktasal kaynak kestirimi: `L2 = L1 - 20 log10(r2/r1)`. Yaklaşık −6,02 dB/mesafe iki katı yalnızca belirtilen koşullarda geçerlidir; line array, oda ve çevresel yayılımın genel kuralı değildir.
- Sabine ilk kestirimi: `T60 ≈ 0,161 V/A`; V m³, A m² sabin eşdeğer soğurma alanıdır. Bu sonuç oda ölçümü veya düşük frekans modeli değildir.
- Dikdörtgen alan: `A = W×D`, `V≈W×D×H`; uzak köşe `sqrt(D²+(W/2)²)`. Yatay açıdan çıkarılan genişlik yalnızca geometri izdüşümüdür.
- Eksenel mod: `fn=n×c/(2L)`; bu tam oda cevabı değildir.
- Mesleki maruziyet örneği, NIOSH'un 85 dBA/8 saat, 3 dB değişim oranı referansına göre etiketlendi. Bu bir Türkiye mevzuatı, genel halk veya konser ses sınırı değildir.
- RTA bantlarının üst kenar şartı Python ve JavaScript'te aynı taban-10 nominal bant oranıyla hesaplanır. 44,1 kHz akışta 20 kHz üçüncü oktav bandı tam değildir; 48 kHz akışta bant geometrik olarak sığabilir ama mikrofonun 20 kHz yanıtını kanıtlamaz.

### Bilinçli olarak eklenmeyen iddialar

- Kalibre edilmiş dB SPL, LAeq, LAFmax/LCpeak, doz uygunluk raporu: kalibrasyonlu ölçüm donanımı/uygun prosedür olmadan iddia edilmez.
- Faz/transfer function, impulse response, IEC sınıf 1/2 ölçüm uyumluluğu: uygulama bunları ölçmüyor ve sertifikalı cihaz gibi sunmuyor.
- Gerçek PA/array sayısı, SPL hedefi veya güvenli kapasiteyi yalnızca alan m²'sinden belirleme: üretici kutup verisi, yükseklik/eğim, kaynak, DSP, limiter, konum ızgarası ve saha doğrulaması gerekir.
- RTA EQ önerisini otomatik miksere uygulama veya müzik/konuşma spektrumundan oda düzeltmesi çıkarma: kapalıdır. Öneri için kullanıcı pembe gürültü/kararlı bantlı test sinyali kullanımını onaylamalı; sonuçlar en fazla −3 dB kesim adayıdır ve donanıma yazılmaz.

## Kaynaklar

- NIOSH mesleki gürültü maruziyeti: https://www.cdc.gov/niosh/bulletin/2016/noise.html
- OSHA Technical Manual, noise: https://www.osha.gov/otm/section-3-health-hazards/chapter-5
- ANSI/ASA S1.11 / IEC 61260-1 (R2023): https://webstore.ansi.org/standards/asa/ASAANSIS111PartIEC612602014
- IEC 61672-1 ses seviyesi ölçer: https://webstore.iec.ch/en/publication/5708
- ISO 9613-2:2024 dış ortam yayılım modeli: https://www.iso.org/standard/74047.html

## Kapsam ve çalışma sınırı

Kaynak PDF'lerindeki ilgili bölümler ve örnekler metin olarak taranmış; temel formüller uygulama kodunda saf fonksiyon testleriyle karşılaştırılmıştır. Otomatik testler gerçek Windows EXE açılışı, gerçek mikrofon frekans cevabı veya sahadaki akustik kalibrasyonu kanıtlamaz. Bunlar teslim öncesinde gerçek donanımda ayrıca yapılmalıdır.

| `09_SPL_dB_3D_Gorsel_Atlasi.pdf` | SPL 2D/3D harita, dB basınç/güç oranları ve kavramsal salon görseli | Dinamik SPL plan haritası, aynı modelin 3D yüzeyi, dB oran kartları, Stagepulse uygulama içi logo/wordmark | 3.5.2 görsel paketi; hesap modelinin basitleştirilmiş noktasal kaynak olduğu açıkça yazılır.
