# Stagepulse Ses Mühendisliği Merkezi — Dallanmış Eğitim ve Lisans Kataloğu

**Kaynak sürümü:** 4.0.0 · **Denetim tarihi:** 2026-11-11 · **Durum:** eğitim kapsamı ve yeterlilik tasarımı. Bu belge tek başına uygulama içi her görevin, öğretmen onayının veya fiziksel eğitimin çalıştığını kanıtlamaz.

## Eğitim modeli

Öğrenci tek bir düz çizgide ilerlemek zorunda değildir. Önce ortak temel modüller tamamlanır; ardından canlı ses, RF, PA/sistem tasarımı, stüdyo, SPL/akustik, dijital konsol, konuşma/yayın ve bakım dallarından biri veya birkaçı seçilir. Her dalın kuramsal bölümü, uygulama görevi, kanıt dosyası, sınavı ve eğitmen onay kapısı bulunur. Uygulama içi hesaplayıcılar simülasyon/ön çalışma içindir; gerçek donanımda ölçüm ve güvenlik adımlarının yerine geçmez.

## Seviye basamakları

### L0 · Başlangıç
- Geçiş ölçütü: %70 bilgi sınavı; güvenlik modülü zorunlu
- Yeterlilik: Temel kavramlar ve ekipman tanıma

### L1 · Temel uygulayıcı
- Geçiş ölçütü: Kontrol listesinin %80'i ve kritik hata yok
- Yeterlilik: Tek başına güvenli hazırlık ve kablo/patch kontrolü

### L2 · Saha uygulayıcısı
- Geçiş ölçütü: Uygulama rubriği en az 80/100
- Yeterlilik: Gerçek senaryoda kurulum, test, raporlama

### L3 · İleri uygulayıcı
- Geçiş ölçütü: En az 3 arıza senaryosu ve proje dosyası
- Yeterlilik: Sistem optimizasyonu, koordinasyon ve bağımsız teşhis

### L4 · Usta adayı
- Geçiş ölçütü: İki farklı senaryoda başarılı uygulama ve sözlü savunma
- Yeterlilik: Baştan sona iş planı, risk analizi, teslim ve ekip iletişimi

### L5 · Usta / eğitmen onayı
- Geçiş ölçütü: Eğitmen imzası, %85 sınav ve sıfır kritik güvenlik hatası
- Yeterlilik: Gerçek donanımda bağımsız yeterlilik; öğrenci kendisi onaylayamaz

## Eğitim dalları

### Canlı Ses / FOH / Monitör
**Hedef kitle:** Konser, festival, tiyatro, otel ve etkinlik ses ekipleri
**Modüller:**
- Sinyal akışı, dB, gain staging ve headroom
- Mikrofon seçimi, polarite, DI ve stage patch
- Midas M32 Live üzerinde input, bus, DCA, FX ve scene
- FOH denge, monitör miksleri, IEM ve soundcheck
- PA yerleşimi, sub hizalama, delay ve SPL güvenliği
- Rider, stageplot, input list, arıza teşhisi ve show dosyası
**Uygulama ve sınav görevleri:**
- 32 kanallı sanal/kağıt patch planını hazırla ve eğitmenle doğrula
- M32 üzerinde line-check, gain ve 4 monitör mix'i kur
- Soundcheck senaryosunda 5 arızayı ölçülebilir sırayla teşhis et
- Etkinlik sonrası show dosyası ve teknik rapor teslim et
**Usta onay kapısı:** Eğitmen gözetiminde eksiksiz kurulum, güvenli soundcheck ve arıza senaryosu; 85/100 teorik sınav ve tüm kritik güvenlik maddeleri geçer.

### RF / Kablosuz Mikrofon ve IEM
**Hedef kitle:** Kablosuz el/yaka mikrofonu, IEM ve RF koordinasyonu yapanlar
**Modüller:**
- RF temel kavramları, bantlar ve ülke mevzuatını doğrulama
- Tarama, intermodülasyon ve frekans koordinasyonu
- Anten çeşitleri, yön, dağıtım, kablo kaybı ve yerleşim
- Shure ULX-D/PSM ve benzeri sistemlerde koordinasyon iş akışı
- Pil yönetimi, yedek planı, drop-out ve parazit teşhisi
**Uygulama ve sınav görevleri:**
- Gerçek cihaz modeli/bölgesi için üretici aralığını doğrula
- RF tarama raporu ve kanal koordinasyon tablosu oluştur
- Mikrofon + IEM kanallarını birlikte test edip kesilme günlüğü tut
- Yedek frekans ve arıza kurtarma planını canlı test et
**Usta onay kapısı:** Bant uygunluğu doğrulanmadan yayın açmama, çakışmasız planı kanıtla ve en az 3 arıza senaryosunu çöz.

### PA Sistem Tasarımı / DSP / Array
**Hedef kitle:** Sistem teknisyeni, sistem mühendisi ve PA sorumluları
**Modüller:**
- Hoparlör verisi, polarite, empedans ve bağlantı güvenliği
- Aktif/pasif sistemler, crossover, gain structure ve limiter
- Sub dizilimi, polarite, zaman hizalama ve ölçüm mantığı
- Kapsama, SPL tahmini, mekan geometrisi ve çevresel etki
- Üretici yazılımı, preset ve güvenli rigging sınırları
**Uygulama ve sınav görevleri:**
- Mekan ölçülerinden kapsama ve dinleme noktaları planı çıkar
- Üretici verileriyle SPL tahmin tablosu oluştur ve belirsizlikleri yaz
- Sub/ana sistem hizalamasını ölçüm mikrofonu ile doğrula
- Önce/sonra ölçüm ve limiter/clip güvenlik kontrolü raporla
**Usta onay kapısı:** Üretici verisi, ölçüm ve model varsayımları açıkça ayrılmış sistem raporu; gerçek saha doğrulaması ve güvenlik kontrolü.

### Stüdyo / Kayıt / Düzenleme / Miks
**Hedef kitle:** Stüdyo, podcast, içerik ve müzik prodüksiyonu
**Modüller:**
- Akustik oda, mikrofon tekniği ve kayıt seviyesi
- DAW oturumu, routing, editing, comping ve dosya yönetimi
- EQ, kompresör, gate, de-esser, reverb ve otomasyon
- Faz/polarite, mono uyumu, gürültü ve artefakt kontrolü
- Loudness, peak/true-peak sınırları ve teslim formatları
**Uygulama ve sınav görevleri:**
- Kuru kaynakları düzenle, dosya isimlendirme ve oturum arşivi kur
- Konuşma kaydını temizle; artefakt öncesi/sonrası A/B kanıtı al
- Miks ve alternatif teslimleri doğru örnekleme/bit derinliğiyle dışa aktar
- Dosyayı yeniden açıp QC formunu doldur
**Usta onay kapısı:** Oturum dosyası, ham kaynak, miks, teslim formatı ve kalite kontrol raporu eksiksiz; kör A/B dinleme sınavı.

### Miks ve Mastering Uzmanlığı
**Hedef kitle:** Müzik prodüktörü, miks mühendisi ve mastering hazırlığı yapanlar
**Modüller:**
- Oturum hazırlığı, gain staging, dosya düzeni ve referans parça yönetimi
- Statik denge, panorama, faz/polarite ve mono uyumluluğu
- EQ, kompresyon, paralel işlem, saturation ve efekt derinliği
- Otomasyon, bus routing, headroom ve miks revizyonu
- LUFS-I, loudness range, sample peak, true peak ve teslim formatları
**Uygulama ve sınav görevleri:**
- Çok kanallı bir oturumu temizle, isimlendir ve yeniden açılabilir şekilde arşivle
- Referans parçayla seviye eşlenmiş A/B miks karşılaştırması yap
- Mono, faz, korelasyon ve düşük frekans kontrol raporu üret
- Streaming ve yüksek çözünürlüklü teslim için ayrı master çıktıları ve QC formu hazırla
**Usta onay kapısı:** Ham oturum, miks sürümleri, ölçüm raporu, teknik teslim dosyaları ve seviye eşlenmiş kör dinleme değerlendirmesi.

### SPL / Akustik / Gürültü Ölçümü
**Hedef kitle:** Saha ölçümü, raporlama, mekan ve çevresel gürültü işi
**Modüller:**
- dB SPL, dBA/dBC/dBZ, LAeq ve zaman ağırlıkları
- Kalibrasyon, cihaz sınıfı ve ölçüm belirsizliği
- Mesafe, yansıma, oda modları, RT60 ve soğurma
- Ölçüm noktası, süre, arka plan ve tekrar ölçümü
- Saha raporu, sınırlamalar ve resmi mevzuat doğrulama
**Uygulama ve sınav görevleri:**
- Kalibratör ve ölçer bilgilerini ölçüm formuna kaydet
- En az 5 noktada ölçüm yap; konum ve koşulları belgeleyip haritala
- Arka plan ölçümü ve tekrar ölçümünü karşılaştır
- Varsayım ve ölçülmüş veriyi ayıran teknik rapor teslim et
**Usta onay kapısı:** Kalibrasyon ve ölçüm koşulları belgeli rapor; dBFS/RTA verisini dB SPL diye sunmama; ölçüm belirsizliği ve sınırlar doğru yazılmalı.

### Dijital Konsol Uzmanlığı
**Hedef kitle:** Midas M32 Live, Yamaha CL5, Allen & Heath Avantis ve benzerleri
**Modüller:**
- Input patch, preamp, phantom, HPF ve kanal dinamiği
- Bus, subgroup, matrix, DCA, mute group ve FX routing
- Scene/safe/recall scope, show dosyası ve yedekleme
- FOH/monitör/IEM iş akışı ve konsol arızaları
- Dante/ağ sesinin temelleri ve saat/örnekleme mantığı
**Uygulama ve sınav görevleri:**
- M32 üzerinde sıfırdan show dosyası kur
- FOH + 6 monitor + 2 IEM bus planı oluştur
- Scene recall sırasında güvenli parametreleri test et
- Konsol yedeğini dışa aktar ve geri yükle
**Usta onay kapısı:** Gerçek konsolda görev kontrol listesi, doğru routing, güvenli recall ve bağımsız arıza çözümü.

### Konuşma / Podcast / Yayın Sesi
**Hedef kitle:** Sunucu, konferans, podcast ve canlı yayın ses zinciri
**Modüller:**
- Konuşma mikrofonlama, mesafe ve oda tonu
- Anlaşılabilirlik, EQ, de-esser, kompresyon ve gate
- Hibrit/uzaktan bağlantı, mix-minus ve geri besleme önleme
- Yayın loudness ve kayıt teslim standartları
- Konuşma QC, telaffuz ve edit notları
**Uygulama ve sınav görevleri:**
- 60 saniyelik konuşma kaydı ve oda tonu al
- İşlenmiş/işlenmemiş A/B örneği üret
- Mix-minus sinyal akış şeması çiz ve test et
- Teslim loudness/QC raporu oluştur
**Usta onay kapısı:** Kesintisiz konuşma zinciri, anlaşılabilirlik değerlendirmesi ve teknik teslim standardı.

### Kablolama / Bakım / Arıza Teşhisi
**Hedef kitle:** Saha teknisyeni ve sistem bakım personeli
**Modüller:**
- Balanced/unbalanced, XLR/TRS/SpeakON ve pinout
- Kablo test, lehimleme, süreklilik ve kısa devre
- Güç, topraklama ve elektrik güvenliği sınırları
- Hum/buzz, RF, dijital clock ve network arızaları
- Bakım kaydı, etiketleme, yedek ve envanter
**Uygulama ve sınav görevleri:**
- XLR 3 pin kabloyu şemaya göre test et
- Arızalı kabloda sorunu bul ve onarım sonrası yeniden test et
- Hum/buzz için güvenli teşhis ağacı uygula
- Envanter ve bakım formu oluştur
**Usta onay kapısı:** Kablo test cihazı sonuçları, güvenli arıza teşhisi ve bakım kayıtları; elektrik panosu/şebeke müdahalesi yalnız yetkili personelde.

## Ticari paket ve lisans kapsamı

**Güncel ticari ürün yalnızca FULL PAKET'tir.** Eğitim dalları ayrı satılan ürünler veya bağımsız lisanslar değildir; FULL PAKET içindeki öğrenme yollarıdır. Bu nedenle bu belgede eski ayrı dal fiyatları satış fiyatı olarak kullanılmamalıdır.

Katalog JSON'unda ve eski veritabanı şemasında bulunan `start`, `live_sound`, `rf_wireless`, `pa_system`, `studio_post`, `spl_acoustics`, `digital_console`, `full_master` ve `institution` kodları geriye dönük veri/şema uyumluluğu içindir. Bu kodların bulunması, ayrı paketlerin bugün satışta olduğu anlamına gelmez. Güncel satış akışı, yönetici onaylı FULL PAKET banka havalesi/EFT bildirimiyle sınırlıdır; online kart tahsilatı ve otomatik fatura/e-Arşiv bu akışın parçası değildir.

Fiyat, vergi, banka bilgileri ve satışa açılma durumu yönetici mağaza ayarları ile canlı sistemde doğrulanmalıdır. Bu doküman veya JSON içindeki eski öneri tutarları canlı fiyat kaynağı kabul edilmemelidir.

## Lisans paketlerinin işleyişi

Lisans yetkisi içeriğe erişimi belirler; yeterlilik veya mesleki yetki vermez. Öğrenci kendi usta statüsünü onaylayamaz. Usta/öğretmen onayı için gerçek uygulama kanıtı, kritik güvenlik maddelerinin geçilmesi ve yetkili eğitmen kararı gerekir. Lisans kodlarının veritabanında bulunması, ilgili ayrı satış paketinin aktif olduğu anlamına gelmez.

## Usta seviyesine kadar ölçülebilir öğrenme akışı

1. Ön değerlendirme ve hedef dal seçimi.
2. Konu modülü ve örnek vaka.
3. Rehberli uygulama: adım adım görev, beklenen çıktı ve durdurma koşulu.
4. Bağımsız uygulama: aynı beceriyi farklı senaryoda tekrar et.
5. Kanıt: dosya, ölçüm, fotoğraf, routing şeması veya rapor.
6. Otomatik bilgi sınavı ve uygulama rubriği.
7. Eğitmen gözlemi ve düzeltme döngüsü.
8. Başarısız maddelerde yeniden çalışma ve tekrar sınavı.
9. Portföy ve sözlü savunma.
10. Usta onayı yalnızca yetkili eğitmen tarafından verilir.

## Stagepulse.com.tr iş akışlarıyla eşleştirme

| İş / hizmet alanı | Uygulamadaki eğitim çıktısı |
|---|---|
| Ses sistemi kiralama ve etkinlik operasyonu | Talep formu, rider inceleme, ekipman/teknik ekip listesi, kurulum-söküm ve etkinlik raporu |
| Ses sistemi tasarımı ve teklif | İhtiyaç analizi, sistem seçenekleri, varsayımlar, ekipman/personel/lojistik maliyeti, kapsam ve riskler |
| SPL ölçümü ve raporlama | Ölçüm planı, cihaz/kalibrasyon kaydı, ölçüm noktaları, grafik ve sınırlamalar |
| Ses mühendisliği eğitimi | Dallara ayrılmış ders, uygulama, sınav, kanıt ve öğretmen onayı |
| Stüdyo/kayıt/post-prodüksiyon | Kayıt planı, düzenleme, miks QC, loudness ve teslim paketi |
| Teknik dokümantasyon ve danışmanlık | Teknik rapor, arıza ağacı, bakım listesi, 3D sahne/yerleşim teslimi ve teslim dosyaları |
| Dante / Network Audio | Ağ topolojisi, IP/clock planı, routing testi, senkronizasyon ve arıza kurtarma |
| Ses + ışık + LED prodüksiyon koordinasyonu | Ortak etkinlik planı, güç/kablo/kurulum koordinasyonu; ışık/LED uzmanlık uygulaması ayrı sorumluluk olarak tanımlanır |

Bu eşleştirme Stagepulse.com.tr ana sayfası, Hizmetler ve Teknik Mühendislik sayfalarında listelenen ses sistemi kiralama, FOH/monitör/IEM, Dante/network audio, kurulum-operasyon, Stage Plot, 3D sahne çizimi, SPL, teknik rider ve entegre prodüksiyon hizmetlerine göre genişletilmiştir. Kaynaklar: https://stagepulse.com.tr/ ; https://stagepulse.com.tr/hizmetler.html ; https://stagepulse.com.tr/muhendislik.html . Bu eşleştirme site hizmetleri için uygulama içi iş akışı önerisidir. Web sitesindeki canlı formlar, ödeme, müşteri kayıtları veya teklif gönderimi bu katalog dosyasıyla kendiliğinden entegre olmuş sayılmaz; her bağlantı ayrıca API/iş akışı testi ister.

## Ölçme ve güvenlik politikası

- Teorik sınav tek başına ustalık kanıtı değildir.
- Kritik güvenlik hatası varsa toplam puan yüksek olsa bile uygulama başarısız sayılır.
- Öğrenci kendi resmî ilerlemesini/usta statüsünü onaylayamaz.
- RF bantları, güç güvenliği, rigging ve işitme maruziyeti için cihaz/ülke/mevzuat bilgisi sahada doğrulanır.
- Uygulama dBFS ölçümünü kalibre edilmiş dB SPL olarak göstermez; gerçek SPL raporu için uygun ölçüm donanımı ve yöntem gerekir.
- Her eğitim modülünde hedef, ön koşul, araç, adım adım uygulama, beklenen çıktı, yaygın hata, güvenlik durdurma koşulu ve değerlendirme rubriği bulunmalıdır.

## Açık doğrulama ve tamamlanma kapıları

- Fiyatları işletme maliyeti ve vergiyle onaylamak.
- Paket kodlarını veritabanı, lisans üretimi, aktivasyon ve özellik yetkileri boyunca uçtan uca test etmek.
- Usta onayını yalnızca yetkili öğretmen rolüne bağlamak ve denetim günlüğüne yazmak.
- Her dal için uygulama videoları/örnek dosyalar ve gerçek cihaz oturumları hazırlamak.
- Windows EXE ve Android APK dağıtımını ayrı paket/cihaz testlerinden geçirmek.
- Siteye ödeme altyapısı eklenmediyse uygulamada online ödeme varmış gibi göstermemek.


## Site hizmetleri için teklif hesaplama yaklaşımı

Stagepulse.com.tr hizmet sayfaları sabit genel fiyat yerine proje bazlı teklif tarif ediyor. Bu nedenle uygulama, müşteri girdileri olmadan sahte kesin fiyat üretmemelidir. Teklif şablonu en az şu kalemleri içermelidir: ekipman modeli/adedi/süre, teknik ekip sayısı ve saatleri, kurulum-prova-söküm, nakliye/şehir dışı ulaşım/konaklama, keşif-çizim-SPL raporu mühendislik emeği, ek tedarik, vergi ve açık iptal/hava riski koşulları.

**Teklif formülü:** ekipman + personel/saat + kurulum/söküm + lojistik + mühendislik/dokümantasyon + ek tedarik + vergi + açık risk/iptal koşulları. Fiyatı onaylayan kişi her maliyet kalemini doğrulamalıdır.
