# PA, Array ve Sub Hizalama: Güvenli Çalışma Notu

## İşe başlamadan

- Hoparlörlerin tam modelini, üretici yazılımını, presetini ve sistem işlemcisini doğrula.
- Üreticinin tahminleme yazılımında sahne ve seyirci alanı geometrisini gerçek ölçülerle çiz.
- Hedef kapsama alanı, maksimum kullanım seviyesi, komşu alanlar ve zaman kısıtlarını yaz.
- Rigging tablolarını, yükleri, bağlantı elemanlarını ve rüzgâr/zemin şartlarını yetkili kişiyle doğrula.

## Zaman ve mesafe

Sesin havadaki hızı yaklaşık olarak sıcaklığa bağlıdır:

`c ≈ 331,3 + 0,606 × sıcaklık(°C)` metre/saniye

Mesafe farkına karşılık gelen teorik gecikme:

`gecikme (ms) = mesafe (m) / c × 1000`

20 °C'de c yaklaşık 343,4 m/s'dir; her 1 metre için yaklaşık 2,91 ms elde edilir. Bu değer ilk tahmindir. Doğru hizalama için gerçek akustik merkez, polarite, crossover, filtreler ve ölçüm sonuçları da önemlidir.

## Sub dizilimi ve geçiş bölgesi

- Yerleşim (tek/çift sıra, merkez kümesi, kardioid/end-fire vb.) hedef kapsama, sahne arkası, komşu alanlar ve mevcut sistemin imkanlarıyla seçilir.
- Her yöntemin yerleşim, kablolama, gecikme, polarite ve seviye koşulları vardır. Sadece gecikme ekleyerek kardioid veya end-fire sonucu elde edildiği varsayılmaz.
- Polarite tersleme tek başına çözüm değildir; ilgili modelin üretici dokümanı ve ölçüm doğrulaması gerekir.
- Ana hoparlörle sub arasındaki crossover çevresinde genlik, faz ve zaman örtüşmesini ölç. Farklı konumlarda birden fazla ölçüm al.
- Tek noktada mükemmel görünen sonucu tüm seyirci alanı için doğru kabul etme.

## Saha doğrulaması

1. Ölçüm mikrofonu, arayüz, kalibrasyon dosyası ve ölçüm yazılımının doğru olduğunu kontrol et.
2. Başlangıç seviyesini düşük tut; test sinyalini yavaşça yükselt.
3. Sol/sağ sistemleri, subları ve fill gruplarını ayrı ayrı kontrol et.
4. Polarite, gecikme, filtre ve yönlendirme ayarlarını sırayla doğrula.
5. Bir değişiklikten sonra aynı noktalar ve aynı ölçüm koşullarıyla yeniden ölç.
6. Ayarları ve mikrofon konumlarını dosyaya kaydet.

**Sınır:** Bu not bir üretici rigging kılavuzu, ArrayCalc/Soundvision tahminlemesi veya kalibreli ölçüm sistemi değildir. Donanım güvenliği ve nihai parametreler üretici belgeleri ve yetkin personelle doğrulanır.
