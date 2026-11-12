# Stagepulse Ses Merkezi değişiklik geçmişi

## 4.0.5 · Ortak Yönetim Merkezi ve oturum güvenliği

- Windows ve Android uygulamalarına yalnızca sahip rolünün erişebildiği ortak Yönetim Merkezi eklendi.
- Lisans, öğrenci, satın alma, oturum ve yönetici işlem kayıtları tek yönetim ekranında toplandı.
- Oturum doğrulama olayları istemciden kabul edilmez; sunucu tarafından kontrollü biçimde kaydedilir.
- Çıkış olayları yalnızca yakın zamanda doğrulanmış oturumlar için kaydedilir.
- Windows ve Android yönetim ekranları kendi yerel köprüleri üzerinden aynı yetkili sunucu uç noktasını kullanır.
- Windows/Android sürümleri 4.0.5 olarak eşitlendi; Android versionCode 40005 olarak artırıldı.

## 4.0.0 · Kaynak sürümü

- Windows ve Android kaynak sürümleri 4.0.0 olarak eşitlendi.
- Sistem tasarım araçları; Line Array Designer, SPL Coverage ve Sub-Top Alignment açıklamalarıyla belgelendi. Bu araçlar yaklaşık/geometrik ön çalışma üretir; üretici polar/GLL verisi ve saha ölçümü yerine geçmez.
- Eğitim kataloğu dokuz uzmanlık dalı ve L0–L5 yeterlilik basamaklarıyla eşitlendi. Güncel ticari ürün yalnızca FULL PAKET olarak tanımlandı; eski paket kodları geriye dönük uyumluluk olarak işaretlendi.
- Canlı ses öğrenci PDF'sine RF tarama, intermodülasyon, anten ve IEM koordinasyonu dersi eklendi.
- Stüdyo öğrenci PDF'sine miks/mastering, LUFS, true peak, dither ve teslim QC dersi eklendi.
- PDF kalite kapısı yeni RF/mastering anahtar içeriklerini de doğrular.
- Windows/Android katalog kopyaları ve 28 birincil ekran için otomatik eşitlik testleri eklendi.
- Android Gradle Wrapper, Android kalite CI iş akışıyla Gradle 8.13 üzerinde eşitlendi.
- PDF üretim iş akışında main dalına yazmadan önce uzak dalı fetch/rebase ederek eşzamanlı commit yarışına karşı koruma eklendi.

## Önceki sürüm geçmişi (3.9.7 ve öncesi)

- Windows ve Android'e ortak OSC/UDP mesaj gönderimi eklendi. IPv4, UDP portu, OSC adresi ve float/integer/string veri türü doğrulanır; gönderim cihaz yanıtı olarak raporlanmaz.
- Windows ve Android'de tempo, kanal, program, nota, velocity ve süre ayarlı standart MIDI Type 0 dosyası oluşturulabilir.
- MIDI dosyası Android'de İndirilenler/Stagepulse klasörüne, Windows'ta indirme akışına kaydedilir.
- Arşivdeki SPL/FFT, sabit 230 V kablo hesabı ve gerçek tarama yapmayan RF sezgiseli mevcut daha gelişmiş Stagepulse araçlarıyla çakıştığı veya güvenilir ölçüm üretmediği için taşınmadı.


- Android Compressor ve Gate kulak eğitimi; A/B dinleme, rastgele sınav ve arayüz stilleriyle yeniden doğrulandı.
- SPL 2D/3D görünümünde kaynak seçme ve sürükleme davranışı, tuvalin gerçek mantıksal koordinatlarına göre düzeltildi.
- Android varlık denetimi Compressor/Gate kontrollerini ve stillerini zorunlu doğrulamaya aldı.

## 3.9.5

- RTA ölçüm adayları için doğrulama ve müdahale adımları eklendi.
- SPL saha ölçüm sihirbazı, ölçüm noktası kaydı ve CSV özeti eklendi.
- Tek/üç faz güç, akım ve kablo gerilim düşümü ön hesaplayıcısı eklendi.
- El mikrofonu ve IEM kanallarını birlikte ele alan RF ön koordinasyon aracı eklendi.
- Dört kanallı sanal mikser, gain staging, EQ ve compressor pratiği eklendi.
- AI video ders senaryoları, storyboard ve video oynatıcı kütüphanesi eklendi.
- Asistan, Operatör ve Mühendis öğrenme yolu ile PDF katılım belgesi eklendi.
- SPL 2D/3D haritası kategori bazlı PA/Sub/Monitör yerleşimi, seçme, düzenleme ve sürükleme ile canlı güncellenecek şekilde geliştirildi.
- Öğrenci ekranına görünür FULL PAKET satın alma/lisans kısayolu eklendi.
- Destek ve iletişim düğmeleri doğrudan WhatsApp hattına yönlendirildi.
- Compressor ve Gate A/B dinleme ve rastgele sınav alıştırmaları korundu.
- Katılım belgesinin resmî yeterlilik veya akreditasyon sağlamadığı açıkça belirtildi.

