# Görsel, SPL ve dB denetimi — Stagepulse 3.5.2

## Önceki sürümde gözlenen eksikler

1. **Marka işareti:** Yan menüdeki `SP` metin simgesi gerçek bir varlık dosyası değildi. Artık `ui/assets/stagepulse-logo.svg` vektör kilidi kullanılıyor. Bu dosya Stagepulse için siyah-altın-beyaz paletle hazırlanmış yeni bir uygulama içi kilittir; resmî web sitesiyle bire bir logo dosyası eşleşmesi olduğu iddia edilmez.
2. **SPL haritası:** Önceki arayüz yalnızca sayısal SPL/mesafe ve alan geometrisi sonuçlarını gösteriyordu. Dinamik, 2D ve 3D hesaplanmış alan görselleştirmeleri yoktu.
3. **dB öğretim grafiği:** dB farkı, ses basıncı genliği oranı ve yoğunluk/güç oranı görsel olarak karşılaştırılmıyordu.
4. **Gerçekçi 3D anlatım:** PA ve dinleyici alanını gösterecek fotogerçekçi görsel ve öğrenciye yönelik görsel atlası yoktu.
5. **Test çalıştırma:** `pytest -q` kök dizinden çalıştırıldığında Python paket kökü bulunamayabiliyordu. `pytest.ini` içine `pythonpath = .` eklendi.

## 3.5.2 ile eklenenler

- `ui/assets/stagepulse-logo.svg`: siyah zemin, altın dalga işareti ve beyaz Stagepulse wordmark.
- `ui/assets/spl-3d-konsept.png`: yüksek çözünürlüklü, sayı/metin içermeyen fotogerçekçi salon/PA konsept görseli. İlgili ekran ve PDF üzerinde bunun bir **kavramsal illüstrasyon** olduğu yazılıdır; render içindeki renk ve rakamlar ölçüm kanıtı değildir.
- `SPL / alan planı` sayfasında kullanıcı alan genişliği, derinliği, referans dB SPL ve referans mesafesini değiştirince güncellenen 2D renk haritası ve aynı modelden üretilen izometrik 3D yüzey.
- Harita renk skalası her hesapta gerçek model minimum/maksimumuna göre ölçeklenir; lejant ve sayısal aralık eşleşir.
- dB görselinde +3, +6 ve +10 dB farklarının basınç genliği ile yoğunluk/güç oranlarına etkisi.
- `egitim_paketleri/09_SPL_dB_3D_Gorsel_Atlasi.pdf`: 4 sayfalık öğrenci PDF'si. İçinde kavramsal PA görseli, hesaplanabilir serbest-alan modeli için 2D harita, 3D model yüzeyi, mesafe profili, dB ilişki grafiği ve saha ölçüm raporu kontrol listesi bulunur.
- Başlangıç rehberinde atlas listelenir ve uygulama PDF kataloğuna eklenir. Eğitmen kitapları, fiyat teklifleri veya iç denetim raporları öğrenci kitaplığına eklenmez.

## SPL haritasının açık sınırı

Hesaplanan harita şu tek kaynak eğitim varsayımını kullanır:

`Lp(r) = Lp(r0) - 20 log10(r/r0)`

Kaynak, sahne ön merkezindeki ideal noktasal kaynak kabul edilir; mesafe `r0`'dan küçükse serbest-alan uzak-alan formülüyle fazladan artış yapılmaz. Harita gerçek çizgi dizi/array modeli değildir; kabin açısı, üretici polar eğrisi, yükseklik/eğim, frekans bandı, birden çok kaynak arasındaki faz etkileşimi, sub yerleşimi, zemin/duvar yansımaları, havadaki soğurma, kalabalık veya DSP limiter modeli içermez. Bu nedenle harita sistem tasarımı, halk maruziyeti veya yasal uygunluk raporu olarak kullanılmamalıdır.

Gerçek bir array tahmini için güvenilir üretici polar verisi ve sistem/ortam geometrisi gerekir. AES56, hoparlör polar radyasyon ölçüm verisinin nasıl alınacağını ve belgelenmesi gerektiğini ele alır: <https://aes.org/publications/standards-store/?id=72>.

## dB görselindeki oranlar

Aynı ortamda seviye farkı ΔL için basınç genliği oranı `10^(ΔL/20)`, yoğunluk/güç oranı `10^(ΔL/10)` olarak gösterilir. Bu fiziksel oranlar öznel algı veya tüm PA sistemlerinde duyulan sonuç için garanti değildir.

## Kaynak / ölçüm sınırlamaları

- IEC 61672-1 ses seviye ölçerlerin performans özellikleri ile sınıf 1/2 kategorilerini tanımlar: <https://webstore.iec.ch/en/publication/5708>.
- NIOSH ses seviyesi haritası için cihazın ağırlıklandırma/tepki ayarlarını ve ölçüm koşullarını kaydetmeyi önerir; NIOSH REL mesleki maruziyet bağlamındadır, konser/genel halk mevzuatı değildir: <https://www.cdc.gov/niosh/noise/prevent/understand.html>.
- PC mikrofonunun donanımsal frekans cevabı bilinmeden 20 kHz'deki düşük göstergeyi yazılımla gerçekçi biçimde düzeltmek mümkün değildir.
- Gerçek Windows EXE ve fiziksel mikrofon testi, bu Linux ortamında yürütülemez. Kaynak testi, UI statik testi ve PDF render kontrolü fiziksel cihaz testinin yerine geçmez.
