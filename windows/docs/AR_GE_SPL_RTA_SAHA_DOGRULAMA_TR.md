# Stagepulse SPL / RTA Ar-Ge ve saha doğrulama planı

## Amaç ve kabul ilkesi

Stagepulse ölçüm altyapısını profesyonel ses sistemi analizi için geliştirmek. Bir grafiğin çizilmesi veya kalibrasyon değerinin girilmesi tek başına ölçüm doğruluğu kanıtı değildir. Her metrik için algoritma testi, ses zinciri testi, referans cihaz karşılaştırması ve saha kaydı ayrı tutulur.

Smaart Suite'in yayımlanmış özellikleri işlevsel referans alınır; arayüzü veya özel algoritmaları kopyalanmaz. Hedeflenen ana başlıklar RTA/spektrogram, çift kanallı Transfer Function, magnitude/faz/coherence, delay, impulse response ve SPL kayıt/raporlamadır.

## Mevcut koda eklenen temel

- windows/core/acoustic_engine.py: 1/1, 1/3, 1/6, 1/12, 1/24 ve 1/48 oktav bant analizi; A/C/Z ağırlıklı SPL metrikleri.
- windows/core/acoustic_api.py: WebView üzerinden RTA ve SPL örnek analizi çağrıları.
- windows/ui/rta_math.js ve Android varlığı: aynı base-2 bant merkezlerinin UI tarafında hesaplanması.
- windows/tests/test_acoustic_engine.py: sentetik sinyal, çözünürlük, ağırlıklandırma, kalibrasyon ve API testleri.
- Ölçüm seviyeleri, fiziksel kalibrasyon düzeltmesi yoksa dBFS olarak işaretlenir.

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

## Yönetici kontrol merkezi için hedef mimari

Mevcut ticari ürün tek FULL PAKET olarak kalır. Yönetici paneline daha sonra şu yapı eklenmelidir:
- Modül görünürlüğü: Windows ve Android için ayrı ayrı etkin/pasif.
- Özellik bayrakları: kararlı, beta, deneysel ve kapalı durumları.
- Eğitim kataloğu: dal, seviye, ders, içerik ve yayımlanma durumu.
- Uygulama içeriği: duyuru, yardım, sürüm notu ve bakım bildirimi.
- Lisans ve satış: mevcut FULL PAKET/lisans akışını koruyarak fiyat ve kampanya yönetimi.
- Değişiklik günlüğü: kim, neyi, hangi tarihte değiştirdi.
- Sunucu tarafı yetki: UI'da düğme gizlemek yetkilendirme değildir; her yönetici yazma işlemi Edge Function/RLS/RPC tarafında doğrulanmalıdır.
- Platform sürümü ve minimum sürüm: uyumsuz istemcide riskli özellik kapatılabilmelidir.

Özellik bayrakları için önerilen kayıt anahtarı feature_key + platform + channel; platform değerleri windows, android, both; kanal değerleri stable, beta, experimental olmalıdır. Kullanıcı/cihaz yanıtına yalnızca izin verilen, imzalı/HTTPS üzerinden alınan yapılandırma döndürülmelidir. Kritik güvenlik ve lisans kontrolleri özellik bayrağına bırakılmamalıdır.

## Şimdilik yapılmayanlar

- Android gerçek zamanlı PCM yakalama zincirine yeni SPL algoritmasının bağlanması.
- UI'da 1/6–1/48 oktav seçicilerinin ve SPL metrik ekranlarının açılması.
- TF otomatik delay tracking, gelişmiş averaging ve multi-engine.
- Ölçüm mikrofonu frekans düzeltme dosyası yönetimi.
- Saha cihazı karşılaştırması ve IEC uygunluk testi.
- Yönetici feature-flag veritabanı, Edge Function yönetim eylemi ve ekran kontrolleri.

Bu maddeler kodun mevcut durumuyla karıştırılmamalı; ayrı geliştirme ve kabul işleri olarak izlenmelidir.
