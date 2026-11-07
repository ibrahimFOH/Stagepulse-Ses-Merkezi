# Stagepulse Android kaynak ve kabul denetimi

**Kaynak sürümü:** 3.9.0  
**Sürüm kodu:** 30900  
**Denetim kapsamı:** Android kaynak ağacı ve paketleme sözleşmeleri

## Mevcut mimari

- Kotlin ana uygulaması, yerel WebViewAssetLoader üzerinden paketlenmiş Türkçe HTML/CSS/JavaScript arayüzünü açar.
- WebView dosya erişimi kapalıdır; yerel varlıklar HTTPS uygulama şeması üzerinden sunulur.
- Öğrenci kitaplığı 13 PDF, uygulama içi kılavuz kataloğu 12 belge içerir.
- WebAudio RTA mikrofon girişini tarayıcı ses zinciri üzerinden işler. Sonuçlar göreli dijital seviyelerdir; kalibre edilmiş dB SPL veya IEC 61260 sınıf 1/2 ölçümü değildir.
- Android sürümünde canlı iki kanallı H1 Transfer Function yakalama ve fiziksel ses kalibratörü akışı bulunmaz. Canlı stereo TF ve 1 kHz kalibratörle oturumluk SPL kalibrasyonu Windows masaüstü kapsamındadır.
- WAV dosya seçimi ve desteklenen dosyalarda peak/RMS analizi bulunur.
- Yaklaşık loudness düzeyleme ve stereo PCM WAV dışa aktarma, sertifikalı LUFS/true-peak uygunluk ölçümü veya profesyonel limiter değildir.
- Supabase Auth, oturum yenileme, cihaz kimliği, lisans ve öğretmen/öğrenci uçları Kotlin köprüsünden çağrılır.
- Oturum belirteçleri Android Keystore AES-GCM anahtarıyla şifrelenir; servis rolü anahtarı APK içine eklenmez.
- Güncelleme akışı sürüm, URL, dosya boyutu ve SHA-256 kontrolleri yapar.

## Yetkilendirme ve gizlilik

- Android istemcisi GroqCloud sağlayıcısını kullanır; bulut isteği için açık kullanıcı onayı ve geçerli yetki gerekir.
- Ollama yalnızca Windows bilgisayarındaki yerel servis içindir; Android cihazındaki 127.0.0.1 Windows makinesini göstermez.
- API anahtarları kalıcı uygulama depolarına yazılmaz.
- Lisans ve rol kararları istemci arayüzünün görünürlüğüne bırakılmaz; sunucu tarafında doğrulanır.

## Kaynak doğrulamaları

Depo kök dizininden çalıştırılacak kontroller:

```bash
python android/scripts/verify_assets.py
find android/app/src/main/assets/ui -type f -name '*.js' -print0 | while IFS= read -r -d '' file; do node --check "$file" || exit 1; done
gradle -p android --no-daemon clean testDebugUnitTest assembleDebug
```

Kaynak doğrulaması PDF kataloğu, dosya referansları, izin listesi, sürüm kodu ve JavaScript sözdizimini denetler. Bu kontroller imzalı Release APK, mikrofon donanımı veya fiziksel cihaz kabul testinin yerine geçmez.

## Fiziksel cihaz kabulü

Aşağıdaki adımlar gerçek Android telefon/tablet üzerinde ayrıca doğrulanmalıdır:

1. Temiz kurulum, mevcut sürümden yükseltme ve uygulama kaldırma.
2. Mikrofon izni verme, reddetme ve sonradan ayarlardan açma.
3. RTA başlatma/durdurma, başka uygulamanın mikrofonu kullanması ve ses girişinin kesilmesi.
4. WAV dosyası seçme, bozuk/uyumsuz dosya reddi ve analiz.
5. 13 PDF'nin harici görüntüleyicide açılması.
6. Supabase giriş/çıkış, oturum geri yükleme, lisans aktivasyonu ve cihaz sınırı.
7. Groq açık onayı, yanlış anahtar/model ve bağlantı kesilmesi senaryoları.
8. Güncelleme SHA-256 hatası ve imza uyuşmazlığında kurulumun reddedilmesi.
9. Telefon/tablet ekran boyutları, döndürme, klavye açılması ve sistem çubuğu güvenli alanları.

**Durum:** Kaynakta tanımlanan statik denetimler ve CI çalışmaları fiziksel cihaz kabulünü otomatik olarak kanıtlamaz. Bu rapor gerçek cihaz testlerinin tamamlandığını iddia etmez.
