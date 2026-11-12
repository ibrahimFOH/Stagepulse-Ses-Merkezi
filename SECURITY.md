# Güvenlik Politikası

## Desteklenen sürüm

| Sürüm | Güvenlik güncellemesi |
|---|---|
| 4.0.x | Destekleniyor |
| 4.0 öncesi | Desteklenmiyor |

Güvenlik düzeltmeleri öncelikle desteklenen kararlı sürüme uygulanır. Eski sürümlerdeki bir açığın etkilenip etkilenmediği ayrıca değerlendirilir.

## Güvenlik açığı bildirme

Güvenlik açığı bildirimlerini herkese açık issue, tartışma veya pull request olarak yayımlamayın. İstismar edilebilir ayrıntıları özel tutun. Bildirim için [Stagepulse bakım sorumlusu GitHub profili](https://github.com/ibrahimFOH) üzerinden özel iletişim kurun.

Lütfen bildiriminize etkilenen sürümü, işletim sistemini, etkiyi, yeniden üretim adımlarını ve mümkünse güvenli bir doğrulama örneğini ekleyin. Gerçek kullanıcı verilerini, erişim anahtarlarını veya lisans bilgilerini göndermeyin.

## Müdahale ve açıklama takvimi

- Bildirim alındıktan sonra 3 iş günü içinde alındı teyidi hedeflenir.
- İlk etki ve kapsam değerlendirmesi 10 iş günü içinde yapılır.
- Düzeltme ve koordineli açıklama takvimi, riskin ciddiyetine göre bildirim sahibiyle kararlaştırılır.
- Kullanıcıları korumak için düzeltme yayımlanmadan önce istismar ayrıntıları kamuya açıklanmaz.

## Güvenli geliştirme

Bağımlılıklar OSV-Scanner ve Trivy ile taranır. GitHub Actions iş akışları zizmor ile denetlenir. Kod değişiklikleri Python/JavaScript regresyon testleri, Android birim testleri ve Windows paketleme kontrollerinden geçirilir.
