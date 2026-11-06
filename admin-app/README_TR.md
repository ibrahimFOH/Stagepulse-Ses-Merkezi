# Stagepulse Usta Öğretmen Yönetim Uygulaması

Bu ayrı uygulama Stagepulse Ses Mühendisliği Merkezi'nin sahibi/usta öğretmeni için tasarlanmıştır. Öğrenci uygulamasından ayrıdır.

## Gerçek sunucu bağlantıları
- Yönetici girişi: `license-admin` özel yönetici oturum token'ı.
- Yönetim verileri: `ses-merkezi-desktop` Edge Function.
- Yetki: sunucu tarafında sabit Stagepulse owner kimliği ve `org_memberships` içindeki aktif owner rolü tekrar doğrulanır.
- Lisanslar: `sesm_license_keys`, `sesm_activations`.
- Öğrenciler: `sesm_students`.
- Öğrenci modül ilerlemesi: `sesm_progress`.
- Denetim kaydı: `sesm_audit_events`.

## Uygulamadaki gerçek işlevler
- Genel Bakış: lisans ve öğrenci özetleri.
- Öğrenciler: lisansını etkinleştirmiş öğrencilerin listesi.
- Öğrenci ilerlemesi: 11 modül için tamamlandı/tamamlanmadı işaretleme ve öğretmen notu kaydetme.
- Lisanslar: lisans oluşturma, paket seçme, cihaz sınırı, süre, ödeme bilgisi, ödeme onayı, uzatma, iptal.
- Raporlar: lisans CSV dışa aktarma ve yönetici işlem geçmişi.
- Ayarlar: yönetici şifresi değiştirme.
- Eğitim Kataloğu: öğrenci uygulamasındaki eğitim paketleri.

## Henüz olmayan özellikler
- Ayrı öğrenci hesabı oluşturma/silme ve parola sıfırlama yönetimi için yönetici API'si henüz yok.
- Sınav/soru bankası/otomatik notlandırma için tablo ve API henüz yok.
- Eğitim PDF'lerini panelden düzenleme/yükleme/yayınlama akışı henüz yok.
Bu özellikler varmış gibi gösterilmez.

## Derleme
GitHub Actions `Stagepulse Yönetim Paneli EXE + APK` workflow'u Windows EXE ve Android debug APK üretir. Android debug APK test içindir. Dağıtım için release keystore ile ayrıca imzalanmalıdır.
