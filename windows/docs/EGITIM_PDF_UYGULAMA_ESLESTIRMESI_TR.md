# Stagepulse eğitim PDF denetimi ve uygulama eşleştirmesi — v4.0.0

Bu belge öğrenci PDF kitaplığının kaynak, kapsam, teknik sınır ve dağıtım kontrol kaydıdır. Tekil PDF'ler `windows/egitim_paketleri/` ve Android paketinde `android/app/src/main/assets/egitim_paketleri/` altında tutulur. İki platformun PDF dosyaları üretim hattında aynı Windows çıktısından kopyalanır.

## Kitap envanteri ve kapsam

| PDF | İçerik kapsamı | v4.0.0 geliştirmesi / kontrol ölçütü |
|---|---|---|
| 00 Uygulama Kullanımı | Uygulama akışı, araçlar, SPL/RTA, güvenlik ve öğrenci kitaplığı | RTA'nın dBFS spektrumu olduğu, kalibre SPL/IEC analizörü olmadığı açık; Nyquist ve mikrofon sınırları açıklanır. |
| 01 Ses Mühendisliği | Dalga, dB referansları, faz/polarite, elektrik, mikrofon, akustik, işitme güvenliği | 8 ders, formül ve bitirme görevi; dBFS/dBu/dBV/dB SPL ayrımı ve raporlama disiplini. |
| 02 Canlı Ses | Rider, patch, gain, FOH, monitor/IEM, PA, sub hizalama, show operasyonu | 8 saha dersi; 4 wedge + 2 IEM iş akışı, ölçüm ve arıza teşhisi. |
| 03 Stüdyo | Kayıt, mikrofonlama, DAW, edit, EQ/dinamik, stereo, loudness ve QC | 8 ders; LUFS/sample peak/true peak ayrımı, mono kontrolü ve yeniden açılan proje teslimi. |
| 04 Dijital Mikser | Sinyal yolu, preamp, kanal işleme, bus/subgroup/matrix, DCA, scene, FX, ağ ve yedek | 8 uygulamalı ders; DCA'nın audio bus olmadığı ve üreticiye özgü routing farkları vurgulanır. |
| 05 Canlı Mikser Hızlı Başvuru | Açılış/kapanış, gain, işlemci, monitor/IEM ve arıza kartları | Sahada hızlı kontrol listeleri; phantom, IEM ve güç sırası uyarıları. |
| 06 Öğrenci Formları | Ders günlüğü, patch, mikrofon/RF, SPL, stüdyo QC, olay raporu ve rubrik | Kanıt temelli değerlendirme; kritik güvenlik hatası başarısızlık sebebi. |
| 07 Saha SPL Raporlama | LAeq, LAFmax/LASmax, LCpeak, kalibrasyon, A/C/Z, ölçüm ızgarası, belirsizlik | 8 ders; dB aritmetik ortalaması yerine enerji ortalaması, kalibrasyon ve rapor sınırları. |
| 08 SPL / Alan / RTA Teknik Eki | SPL, enerji toplamı, mesafe, alan geometrisi, Sabine, NIOSH ve RTA | Formüller, çözümlü örnekler ve RTA/Nyquist sınırları; NIOSH mesleki referans olarak etiketlenir. |
| 09 SPL dB 3D Atlas | 2D/3D SPL model haritaları, dB oranları ve kavramsal PA görseli | Tek ideal noktasal kaynak/serbest alan varsayımı ve gerçek simülasyon/ölçüm olmadığı açıkça belirtilir. |
| 10 Midas M32 Live | Input/preamp, gain, kanal işleme, bus/DCA, monitor, AES50, FX, scene, kayıt ve show | 12 konsol dersi; gerçek konsol/firmware üzerinde doğrulama şartı korunur. |
| 11 Yamaha CL5 | HA/patch, kanal işleme, Mix/Matrix, Centralogic, Dante, monitor, FX, scene ve show | 12 konsol dersi; Dante ağı ve cihaz/firmware farkları üretici belgesiyle doğrulanır. |
| 12 Allen & Heath Avantis | I/O patch, preamp, kanal işleme, Mix bus, FX, DCA, monitor, scene ve ağ | 12 konsol dersi; model/firmware seçenekleri gerçek cihazda doğrulanır. |

## Teknik doğruluk ilkeleri

- Ses basınç seviyesi: `Lp = 20 log10(pRMS / 20 µPa)`.
- Bağımsız enerji katkıları: `Lsum = 10 log10(Σ 10^(Li/10))`. Faz ilişkili kaynakların dizi davranışını tek başına modellemez.
- Serbest alan noktasal kaynak kestirimi: `L2 = L1 - 20 log10(r2/r1)`. Line array, oda veya çoklu kaynak için genel kural değildir.
- Sabine ilk kestirimi: `T60 ≈ 0,161 V/A`; `A = Σ(αi × Si)`. Katsayılar frekansa ve malzemeye bağlıdır.
- LAeq enerji ortalamasıdır; dB değerlerinin aritmetik ortalaması değildir.
- Sample peak, true peak ve LUFS farklı ölçütlerdir. Birbirlerinin yerine kullanılmaz.
- RTA/FFT grafiği, mikrofon ve giriş zinciri kalibre değilse dB SPL ölçümü değildir.
- RF frekans planı cihaz bandı, ülke/bölge düzenlemesi ve üretici koordinasyon aracıyla doğrulanır.
- PA kapsama ve SPL tasarımı üretici polar verisi, yükseklik/eğim, DSP, ölçüm ızgarası ve saha doğrulaması ister.
- Eğitim PDF'leri üretici kılavuzu, akredite rapor veya mevzuat uygunluk belgesi değildir.

## Üretim ve otomatik kalite kapısı

Tek kaynak üretim sırası:

1. `windows/scripts/generate_core_curriculum_pdfs.py` → 01–07.
2. `windows/scripts/generate_student_guide.py` → 00.
3. `windows/scripts/generate_acoustic_appendix.py` → 08.
4. `windows/scripts/generate_spl_visual_atlas.py` → 09.
5. `windows/scripts/generate_console_training_pdfs.py` → 10–12.
6. Üretilen PDF'ler Android varlık dizinine kopyalanır.
7. `windows/scripts/verify_education_pdfs.py` PDF açılabilirliğini, metin kapsamını, sayfa içeriğini ve Android/Windows birebir eşitliğini denetler.
8. `android/scripts/verify_assets.py` uygulama paketindeki PDF izin listesini ve ortak varlıkları denetler.

GitHub Actions bu üretimi main üzerinde çalıştırır; PDF'lerde fark varsa iki platformun PDF'lerini tek commit ile main'e yazar. Üretim veya test başarısızsa commit adımı çalışmaz.

## Kalan gerçek donanım doğrulamaları

- M32, CL5 ve Avantis kitaplarındaki menü/işlev adları, kullanılan firmware sürümünde fiziksel konsolda teyit edilmeli.
- RF taraması, intermodülasyon ve anten dağıtımı gerçek cihaz/anten düzeniyle uygulamalı yapılmalı.
- PA hizalama, transfer function ve impulse response uygun ölçüm mikrofonu, referans ve loopback ile doğrulanmalı.
- SPL raporlaması kalibratörlü uygun sınıf cihaz ve geçerli saha prosedürü gerektirir.
- Stüdyo teslimleri gerçek DAW oturumu ve ses dosyalarıyla dinleme/QC testinden geçmeli.

Bu kontroller eğitim materyalinin teknik kapsamını tarif eder; otomatik PDF testi fiziksel donanım yeterliliğini kanıtlamaz.
