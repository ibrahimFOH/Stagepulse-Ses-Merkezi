# Stagepulse SPL / RTA Ar-Ge ve saha doğrulama planı

## Amaç ve kabul ilkesi

Stagepulse ölçüm altyapısını profesyonel ses sistemi analizi için geliştirmek. Bir grafiğin çizilmesi veya kalibrasyon değerinin girilmesi tek başına ölçüm doğruluğu kanıtı değildir. Her metrik için algoritma testi, ses zinciri testi, referans cihaz karşılaştırması ve saha kaydı ayrı tutulur.

Smaart Suite'in yayımlanmış özellikleri işlevsel referans alınır; arayüzü veya özel algoritmaları kopyalanmaz. Hedeflenen ana başlıklar RTA/spektrogram, çift kanallı Transfer Function, magnitude/faz/coherence, delay, impulse response ve SPL kayıt/raporlamadır.

## SMAART ve EBU/ITU referans doğrulama protokolü

Bu bölüm Stagepulse sonuçlarının bağımsız referans araçlarıyla karşılaştırılması içindir. Karşılaştırma tamamlanmadan "SMAART ile aynı", "EBU/ITU uyumlu" veya "sertifikalı" ifadesi kullanılmaz.

### SMAART ile RTA / Transfer Function karşılaştırması
1. Aynı ses kartı, aynı örnekleme hızı, aynı giriş kazancı ve aynı fiziksel mikrofon kullanılmalıdır.
2. Transfer Function için CH0 referans, CH1 ölçüm mikrofonu olacak şekilde aynı sinyal yolu kurulmalıdır; iki kanal aynı saat kaynağından alınmalıdır.
3. Önce dijital loopback ile unity magnitude, bilinen sample delay ve polarity inversion senaryoları doğrulanmalıdır.
4. Ardından hoparlör-mikrofon ölçümünde aynı konum, pencereleme, FFT boyutu, averaging, smoothing ve delay ayarları iki yazılımda eşlenmelidir.
5. Magnitude, phase, coherence, delay, impulse response/ETC ve 1/3 oktav RTA sonuçları aynı grafik aralığında dışa aktarılmalıdır.
6. Her testte Stagepulse/SMAART farkı frekans bazında, gecikme örnek/ms bazında ve coherence farkı ayrı raporlanmalıdır.
7. Düşük coherence, clipping, saat uyumsuzluğu veya farklı smoothing ayarı bulunan karşılaştırma kabul testi sayılmaz.

### EBU / ITU loudness doğrulaması
- Referans kapsamı: ITU-R BS.1770 ailesi ve EBU R128 iş akışı; ölçüm ve raporlama testleri için EBU Tech 3341/3342 dokümanları ve EBU Loudness Test Set kullanılmalıdır.
- Kısa ton, sessizlik, kanal yerleşimi, surround ağırlıkları, gating, K-weighting, integrated loudness, loudness range ve true-peak testleri ayrı ayrı yürütülmelidir.
- Test dosyalarının beklenen sonuçları referans test setinden alınmalı; örnek dosyalar ve beklenen sonuçlar uygulama testlerine sabit fixture olarak eklenmelidir.
- LUFS normalizasyonu ile loudness ölçümü ayrı işlevlerdir. Bir dosyanın hedef LUFS seviyesine yaklaştırılması, BS.1770 ölçüm uygunluğunu veya true-peak sınırını tek başına kanıtlamaz.
- Android ve Windows aynı referans dosyalarını kullanmalı; platform farkı, sample rate, kanal sırası ve decoder davranışı rapora yazılmalıdır.
- EBU Loudness Test Set tam geçişi ve referans cihaz/uygulama karşılaştırması kaydedilmeden EBU/ITU uygunluğu iddia edilmez.

### Kabul kaydı
Her test için test kimliği, uygulama sürümü, platform, ham dosya SHA-256, referans yazılım/sürüm, donanım, ayarlar, beklenen değer, Stagepulse değeri, fark, kabul toleransı ve sonuç saklanmalıdır. Başarısız testler silinmez; hata kaydı ve düzeltme commit'iyle ilişkilendirilir.

## 3.9.8 sürümünde entegre edilenler

- Windows canlı RTA yakalama motoru 1/1, 1/3, 1/6, 1/12, 1/24 ve 1/48 oktav çözünürlüklerini destekler.
- Android canlı mikrofon akışı WebView getUserMedia üzerinden alınır; zaman alanı PCM örnekleri Hann pencereli FFT ile aynı fractional-octave bantlarına dönüştürülür.
- Windows ve Android RTA matematiği ortak rta_math.js varlığıyla eşitlenmiştir.
- Ölçüm mikrofonu CSV correction profili frekans ekseninde logaritmik interpolasyonla RTA bantlarına uygulanır. Profil cihazda saklanır ve yalnızca RTA spektrumunu düzeltir; SPL kalibrasyonu değildir.
- Windows stereo WAV analiz ekranı A/C/Z ağırlıklı Leq, Fast/Slow maksimum, Peak ve 1 saniyelik L10/L50/L90 sonuçlarını gösterir. Kalibrasyon offset'i yoksa dBFS olarak etiketlenir. A/C ağırlıklandırması için 32 kHz altındaki dosyalarda yalnızca Z hesaplanır.
- Android canlı RTA'da fiziksel 1 kHz kalibratörle oturumluk Z/ağırlıksız RMS kalibrasyonu bulunur. Bu, A/C ağırlıklı yasal SPL ölçümü değildir.
- Mevcut yönetici paneline gelişmiş RTA ve mikrofon correction özellik bayrakları eklendi. Ayarlar Supabase `sesm_store_settings.measurement_settings` JSON alanında tutulur; güncelleme yalnızca owner yetkili Edge Function üzerinden yapılır.
- Yönetici panelindeki saha kayıt alanı mikrofon/kalibratör metaverisini ve operatör kontrol listesini dışa aktarır. Bu saha notları cihazda tutulur; otomatik ölçüm doğrulaması değildir.
- windows/core/acoustic_engine.py ve windows/core/rta_capture.py sentetik sinyal, bant çözünürlüğü, ağırlıklandırma ve kalibrasyon testlerini içerir.

## Ölçüm modülleri ve tamamlanma ölçütleri

### RTA
1. FFT boyutu ve örnekleme hızı kayıt metaverisine yazılır.
2. 1/1–1/48 oktav çözünürlük seçenekleri desteklenir.
3. Bant gücü dBFS RMS olarak raporlanır.
4. Peak hold, ortalama alma, hedef eğri ve spektrogram ayrı kabul maddeleridir.
5. Bant filtrelerinin IEC 61260 sınıf uygunluğu ayrıca ölçülmeden iddia edilmez.

### SPL
1. Z (ağırlıksız), A ve C frekans ağırlıklandırması.
2. Fast 125 ms ve Slow 1 s zaman ağırlıklandırması.
3. Leq, Fast/Slow maksimum, peak ve 1 saniyelik L10/L50/L90.
4. Fiziksel kalibratör referansından gelen offset, cihaz/giriş/örnekleme profiline bağlı olmalıdır.
5. Mikrofon düzeltme eğrisi, preamp kazancı, ADC headroom ve frekans tepkisi ayrıca izlenmelidir.
6. IEC 61672 Class 1/2 uygunluğu, yazılım testiyle değil ölçüm zincirinin uygun testleriyle doğrulanır.

### Transfer Function / sistem hizalama
1. Referans ve ölçüm kanalı aynı ses kartından eşzamanlı alınır.
2. H1, magnitude, faz ve magnitude-squared coherence ayrı test edilir.
3. Gecikme bulucu bilinen sample delay ve polarity inversion testleriyle doğrulanır.
4. Impulse Response / ETC ve pencereleme testleri eklenir.
5. Düşük coherence ve clipping durumunda sonuç güvenilmez olarak işaretlenir.
6. Canlı otomatik delay takibi ve çoklu ölçüm motoru, temel doğrulama tamamlanmadan açılmaz.

## Saha test düzeneği

### Gerekli donanım
- Aynı anda en az iki giriş alabilen, kararlı sürücülü ses kartı.
- Phantom power sağlayan mikrofon preamp.
- Üretici kalibrasyon dosyası bulunan ölçüm mikrofonu.
- Uygun seviyeli akustik kalibratör (tercihen 94 dB / 1 kHz).
- Bağımsız referans SPL ölçüm cihazı.
- Bilinen test sinyali üretimi için çıkış kanalı ve loopback bağlantısı.
- Saha konumlarını tekrarlanabilir biçimde kaydetmek için tripod ve ölçüm notu.

### Test sırası
1. Ses kartı sürücüsü, örnekleme hızı, kanal eşlemesi ve giriş kazancı sabitlenir.
2. 1 kHz kalibratör ile her ölçüm oturumu öncesi/sonrası referans kaydı alınır.
3. 100 Hz, 1 kHz ve 10 kHz sabit tonlarla RTA frekans ve seviye karşılaştırması yapılır.
4. Pembe gürültü ile 1/3, 1/6 ve 1/12 oktav bant eğrileri referans analizörle karşılaştırılır.
5. A/C/Z ağırlıklı seviyeler, Fast/Slow zaman ağırlıkları ve Leq sonuçları referans cihazla kıyaslanır.
6. Transfer Function için loopback ve hoparlör-mikrofon testi ayrı ayrı yapılır.
7. Bilinen gecikme, polarite tersliği, clipping, düşük seviye ve kesilen ses akışı senaryoları kaydedilir.
8. PA sol/sağ, sub, crossover ve uzak saha noktalarında tekrar ölçüm alınır.
9. Ham WAV, ölçüm JSON'u, donanım metaverisi, kalibrasyon bilgisi ve referans cihaz ekran çıktısı aynı oturum kimliğiyle saklanır.

## Ölçüm kayıt şablonu

Her saha oturumunda en az şu alanlar bulunur:
- Oturum kimliği, tarih/saat ve operatör.
- Uygulama sürümü ve ölçüm motoru sürümü.
- Bilgisayar/telefon, işletim sistemi ve ses kartı sürücüsü.
- Mikrofon marka/model/seri numarası ve kalibrasyon dosyası sürümü.
- Preamp kazancı, phantom power ve kanal yönlendirmesi.
- Örnekleme hızı, FFT boyutu, pencere, bant çözünürlüğü ve ortalama ayarları.
- Kalibratör seviyesi, ölçüm öncesi/sonrası farkı ve offset.
- Referans cihaz marka/model/seri numarası ve kalibrasyon geçerliliği.
- Ölçüm konumu, mikrofon yüksekliği, hoparlör yönü ve ortam koşulları.
- Stagepulse sonucu, referans sonucu, mutlak fark ve kabul/red kararı.
- Ham kayıt ve rapor dosyalarının SHA-256 özeti.

## İlk kabul hedefleri

Bunlar doğrulanacak proje hedefleridir; şu an sağlandığı iddia edilmez:
- 1 kHz referans tonunda RTA band seviyesi: ±1 dB yazılım testi.
- Transfer Function unity loopback magnitude: ±0.5 dB.
- Bilinen dijital gecikme: ±0.1 sample sentetik test.
- Coherence: unity loopback'te 0.99 üzeri.
- SPL Leq karşılaştırması: referans cihaza göre hedef ±1 dB; saha koşulu ve cihaz sınıfına göre ayrıca raporlanır.
- A/C ağırlıklandırma eğrisi: IEC referans tablosuna karşı frekans noktası bazında hata raporu.

## Yönetici kontrol merkezi

Yönetici ayrı bir uygulama veya sayfa değildir; ana Stagepulse uygulamasında owner oturumu açılınca görünür. 3.9.8 kapsamında merkezi ölçüm bayrakları mevcut FULL PAKET mağaza ayarları kaydı içinde saklanır:
- `advanced_rta_enabled`: 1/6, 1/12, 1/24 ve 1/48 oktav seçeneklerini açar/kapatır.
- `microphone_correction_enabled`: RTA CSV mikrofon düzeltmesini açar/kapatır.
- Edge Function `store_get` ayarları okur; `store_update` yalnızca owner tarafından değiştirilebilir ve değerleri boolean olarak doğrular.
- İstemci ayarları çevrimdışı açılış için önbelleğe alır; sunucudan gelen yeni ayarlar önbelleği günceller.
- Saha cihazı ve kalibratör metaverisi JSON olarak dışa aktarılır; bu operatör kaydı merkezi bir ölçüm sertifikası değildir.

Gelecek genişletmeler (platform bazlı stable/beta/experimental kanalları, minimum sürüm, eğitim kataloğu, duyuru ve bakım bildirimi) ayrı gereksinim ve yetki tasarımıyla ele alınmalıdır. Kritik lisans ve güvenlik kararları özellik bayrağına bırakılmaz.

## Fiziksel kabul öncesinde kalan işler

- Gerçek Android telefon, USB ses kartı ve ölçüm mikrofonuyla izin/akış/FFT kararlılığı saha ortamında doğrulanmalı.
- Windows ve Android sonuçları aynı 1 kHz ton, pembe gürültü ve aynı kalibratörle karşılaştırılmalı.
- Mikrofon CSV correction dosyasının üretici kaynağı, cihaz seri numarası ve geçerliliği doğrulanmalı; bilinen referans mikrofonla fark raporlanmalı.
- SPL A/C/Z, Fast/Slow ve Leq sonuçları izlenebilir referans cihazla karşılaştırılmalı.
- IEC 61672 / IEC 61260 uygunluğu bağımsız laboratuvar/uygun test ekipmanı ile ölçülmeli. Yazılım veya sentetik testler Class 1/2 uygunluk kanıtı değildir.
- Transfer Function için canlı otomatik delay tracking, gelişmiş averaging ve multi-engine henüz kapsam dışıdır.

Kod testleri sentetik sinyallerin matematiksel davranışını doğrular; gerçek mikrofon, preamp, ADC, kalibratör, çevresel koşullar ve IEC sınıfını doğrulamaz.
