# Stagepulse Miks ve Mastering Kaynak Rehberi

Bu rehber, ücretsiz ve lisansı incelenmiş açık kaynak projelerin Stagepulse içindeki yerini açıklar. Eğitim kartları ve teşhis metinleri Stagepulse için özgün Türkçe içeriktir; üçüncü taraf ürünlerin metinleri veya arayüzleri kopyalanmamıştır.

## Entegrasyon kararı

| Kaynak | Lisans | Karar |
|---|---|---|
| [NULL JSFX](https://github.com/koulaxizis/null-jsfx) | MIT | Reaper kullanıcıları için dış eklenti referansı. Eklentiler ayrı indirilir; Stagepulse APK/EXE içine gömülmez. |
| [LoudScan](https://github.com/Blaztekk/LoudScan) | MIT | Toplu loudness raporu üretir. Stagepulse'ta WAV analizi ve LUFS normalizasyonu zaten bulunduğundan aynı işlev ikinci kez taşınmaz. |
| [pyloudnorm](https://github.com/csteinmetz1/pyloudnorm) | MIT | Windows tarafında mevcut bağımlılık ve ölçüm motorudur. Yeniden eklenmez. |
| [libebur128](https://github.com/jiixyj/libebur128) | MIT | Alternatif C ölçüm motorudur. Şu anki Python motoruyla aynı görevi yaptığı için gereksiz yerel derleme yükü oluşturmaz. |

## NULL JSFX Reaper rehberi

NULL JSFX, Reaper içinde çalışan JSFX eklentileri sunar. Kullanıcı eklentileri yalnızca resmi depo ve resmi sürüm sayfasından edinmelidir. Stagepulse bu eklentilerin ikili dosyalarını dağıtmaz ve üçüncü taraf eklentilerin çalışmasını garanti etmez.

Öğrenme sırası:
1. Ekolayzer: filtre türü, merkez frekansı, Q ve kazanç.
2. Compressor: threshold, ratio, attack, release, knee ve gain reduction.
3. Gate/expander: threshold, hold, range ve release.
4. Reverb/delay: send-return, predelay, decay, feedback ve senkron.
5. Stereo: mono uyumu, faz ve genişlik.
6. Metering: peak, RMS ve loudness değerlerinin farklı anlamları.

## Ölçüm ve mastering notları

- Sample Peak, True Peak ve Integrated Loudness birbirinin yerine kullanılamaz.
- LUFS hedefi teslim şartına göre seçilir; tüm müzik türleri ve platformlar için tek evrensel hedef yoktur.
- True Peak ölçümü oversampling ve kullanılan standardın ayarlarına bağlıdır.
- Normalizasyon, limiter değildir. Hedef LUFS ile tepe tavanı çelişirse sonuç açıkça raporlanmalıdır.
- Ölçüm sonucu dinleme kontrolünün yerini almaz.
- Stagepulse'un mevcut Windows normalizasyonu `pyloudnorm` kullanır. Android tarafındaki tarayıcı ölçümü yaklaşık olarak etiketlenmeye devam eder; Windows ölçümüyle aynı doğrulukta olduğu iddia edilmez.

## Ticari kullanım ve atıf

Bu rehberde listelenen dört projenin depo metadata'sında MIT lisansı görülmektedir. Kod veya ikili dosya kopyalanırsa ilgili sürümün lisans metni, telif bildirimi ve üçüncü taraf bağımlılıkları ayrıca korunmalıdır. Bu entegrasyonda NULL JSFX ve LoudScan kodu kopyalanmamıştır; yalnızca bağlantı ve kullanım açıklaması verilmiştir. pyloudnorm zaten bağımlılık olarak kullanıldığından mevcut lisans bildirimi korunmalıdır.

## Stagepulse içeriği

Uygulamadaki Miks ve Mastering Uzmanlığı dalı şunları içerir:
- 12 aşamalı Mix-to-Master iş akışı
- 72 Türkçe uygulama kartı
- 40 belirti, olası neden, teşhis ve ilk müdahale kaydı
- Uygulama görevleri ve bilgi sınavı
- Öğretmen onayına bağlı yeterlilik kapısı

Bu içerikler eğitim amaçlıdır. Belirli bir parçaya ait ayar reçetesi veya profesyonel mastering garantisi değildir.
