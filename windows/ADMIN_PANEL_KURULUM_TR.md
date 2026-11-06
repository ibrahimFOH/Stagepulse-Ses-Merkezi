# Stagepulse Lisans Yönetimi: kullanım ve güvenlik

## Yönetici adresi

`https://stagepulse.com.tr/ses-merkezi-lisans/`

Bu sayfa tek yönetici girişini masaüstü ve mobil tarayıcıya sunar. Kaynak repo içinde `website_release/ses-merkezi-lisans/` altında panelin kopyası bulunur. Site reposu `ibrahimFOH/Stagepulse.hatay` içinde aynı yol yayınlanır.

## Giriş

1. Stagepulse sahibi hesabının Supabase Auth e-posta adresi ve şifresiyle giriş yap.
2. Sunucu `context` işlemiyle rolü tekrar kontrol eder; `owner` olmayan hesap oturumu yönetim ekranına taşıyamaz.
3. Halka açık kayıt oluşturma yoktur. Şifreyi kodlara, CSV'ye veya satış notlarına yazma.

## Elden satış akışı

1. `Lisans oluştur` bölümünde müşteri adını, lisans türünü ve süresini gir. İsteğe bağlı e-posta, satış notu ve iç notu ekle.
2. Ödeme yöntemi `Elden nakit`, `Banka havalesi / EFT`, `Kart / POS` veya `Diğer` olabilir. Tutar TL bazındadır.
3. Tahsilat tamamlanmadıysa `Ödeme bekleniyor` bırak. Gerçekten tahsilat yaptıysan `Ödeme alındı / ödendi` seç. Ödeme bekleyen lisans aktivasyon alamaz.
4. `Lisans anahtarı üret` düğmesine bas. Anahtar bir kez görüntülenir; hemen kopyalayıp öğrenciye güvenli şekilde ilet. Anahtarı ekranı kapattıktan sonra panel tekrar göstermez.
5. Sonraki satış/işlem için `Lisans listesi` bölümünden arama/filtreleme yap. Ödeme onayla/iade kaydı oluştur, lisansı iptal et, süreli lisansı 30 veya 365 gün uzat, cihazları görüntüle/kaldır veya CSV dışa aktar.

## Lisans türleri ve cihaz sınırı

- `Bireysel öğrenci`: normal süreli lisans.
- `Sınıf / kurum`: sınıf/kurum etiketiyle lisans.
- `Süresiz kullanım`: bitiş tarihi yoktur; süre uzatma işlemi uygulanmaz.
- Cihaz limiti anahtar oluşturulurken belirlenir. Cihaz kaldırıldığında ilgili aktivasyon pasiflenir; öğrenci tekrar aktivasyon denemesini uygulama içinden yapmak zorundadır.

## Güvenlik modeli

- Tarayıcı tarafında sadece Supabase publishable (anon) anahtarı kullanılır. `service_role` veya özel sunucu anahtarları kesinlikle sayfaya eklenmez.
- Lisans anahtarının düz metni veritabanına yazılmaz; sunucu SHA-256 özetini saklar. Düz anahtar yalnızca oluşturma yanıtında bir kere döner.
- Yeni `license_activations`, `activation_revoke`, `license_extend` ve `audit_list` işlemleri sunucuda `requireOwner(user.id)` denetimi yapar. Aktivasyon araması/iptali lisansın mevcut yöneticiye ait olmasıyla sınırlandırılır. Süre uzatma 1 ile 3650 gün arasında olmalı; kapalı, ücretsiz-ödenmemiş veya süresiz lisans uzatılamaz.
- Edge Function JWT doğrulaması etkin olmalıdır. Yönetim paneli HTTPS dışından açılmamalı.
- `audit_list` son yönetici olaylarını gösterir. CSV satış raporunu kolay dışarı aktarır; Excel/CSV dosyasını yalnızca korunan yönetici ortamında sakla.

## Sınırlamalar

- Bu panel elden nakit, havale ve POS için iç satış/tahsilat kaydı oluşturur. Bankaya para çekmez, çevrimiçi ödeme almaz ve fatura/e-Arşiv/fiş yerine geçmez.
- Panel internet olmadan lisans oluşturamaz ve işlem verilerini offline sıraya almaz.
- Tarayıcıdaki oturum güvenli yönetici hesabına bağlıdır. Telefon veya bilgisayar ortak kullanılıyorsa işlem bitince `Güvenli çıkış` yap.

## Dağıtım sonrası test listesi

- [ ] Masaüstü Chrome/Edge'de URL açılıyor.
- [ ] Telefonda aynı URL açılıyor ve form alanları ekran dışına taşmıyor.
- [ ] Yanlış/rolsüz hesap reddediliyor.
- [ ] Sahip hesabı giriş yapıp lisans listesini görebiliyor.
- [ ] Test anahtarı oluşturulabiliyor ve yalnızca bir kez görüntüleniyor.
- [ ] Ödeme bekleyen test lisansı aktive edilemiyor.
- [ ] Test lisansı `paid` olduğunda lisans doğrulama akışı çalışıyor.
- [ ] İade, iptal, süre uzatma ve cihaz kaldırma sonucu listede/aktivasyonda görülüyor.
- [ ] CSV Türkçe karakterleri koruyor.
- [ ] Test lisansları gerçek öğrenci kayıtlarıyla karıştırılmadan iptal ediliyor.
