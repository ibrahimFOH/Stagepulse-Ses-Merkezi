# Stagepulse Ses Mühendisliği Merkezi 3.6.0 — Lisans Yönetimi Denetim Raporu

Denetim tarihi: 29 Ekim 2026

## Yapılan işler

- Masaüstü ve mobil tarayıcıya uyumlu Türkçe lisans yönetim paneli eklendi: `website_release/ses-merkezi-lisans/`.
- Panelde yönetici girişinden sonra sunucuda ayrıca `owner` rolü doğrulanır. Genel kullanıcı kaydı açılmaz.
- Manuel nakit, havale/EFT, kart/POS ödeme yöntemi, tutar, ödeme durumu, müşteri bilgileri ve satış notu kaydı eklendi.
- Benzersiz lisans anahtarı bir kez gösterilir; veritabanında düz anahtar değil SHA-256 özeti saklanır.
- Lisans listeleme/arama/filtreleme, ödeme onayı, iade durumu, lisans iptali, süre uzatma, cihaz aktivasyonlarını görüntüleme/kaldırma, işlem geçmişi ve CSV dışa aktarma arayüzleri eklendi.
- `ses-merkezi-desktop` Supabase Edge Function sürüm 6 olarak dağıtıldı. JWT doğrulaması etkin. Yeni cihaz ve süre işlemleri sunucuda owner yetkisi ve lisans sahipliği kontrolü yapar.
- Web yayın deposuna `ses-merkezi-lisans/` varlıkları, `_headers` noindex/cache başlıkları ve `sw.js` güncellemesi gönderildi.
- Ücretli lisans yaratırken “Ödendi” seçimi ek bir onay ister.

## Gerçekleştirilen otomatik doğrulama

- `node --check website_release/ses-merkezi-lisans/admin.js`: başarılı.
- `python -m py_compile Merkez.py core/*.py`: başarılı.
- `pytest -q`: **119 passed**.
- HTML'deki tüm `el('...')` referanslarının karşılık gelen `id` öğeleri olduğu kontrol edildi; eksik ID bulunmadı.
- Canlı Edge Function tekrar okunarak `license_activations`, `activation_revoke`, `license_extend`, `audit_list` işlemlerinin yayımlanmış olduğu ve her birinin `requireOwner(user.id)` kullandığı doğrulandı.
- Tarayıcı istemcisinde `service_role` / sunucu gizli anahtarı kullanılmıyor.

## Dış ortamda tamamlanması gereken uçtan uca test

Bu çalışma ortamından `stagepulse.com.tr` adresine DNS/HTTPS isteği gönderilemediği için, Cloudflare önbelleği boşaltıldıktan sonra canlı web sayfasının gerçek telefonda ve bilgisayarda açıldığı bağımsız olarak doğrulanamadı. GitHub deposu güncellendi ve Edge Function aktif durumda, fakat bu tek başına canlı sitedeki her adımın uçtan uca test edildiği anlamına gelmez.

Yayın sonrası test: `website_release/ADMIN_PANEL_KURULUM_TR.md` içindeki kontrol listesini uygula. Üretim müşterisi için ilk ücretli lisans oluşturmadan önce, test hesabı ile yeni lisans oluşturma, ödeme bekleyen anahtarın reddedilmesi, ödeme onayı, iptal, süre uzatma ve cihaz kaldırma adımlarını doğrula.

## Windows uygulama EXE'si hakkında

Bu paket kaynak kod ve web panel dosyalarını içerir. Windows kurulum EXE'si burada derlenmedi; Linux ortamında Windows yükleyicisini çalıştırıp gerçek Casper/Windows kurulumunu test etmek mümkün değil. Windows bilgisayarda `EXE_OLUSTUR.bat` çalıştırıp oluşan kurulum EXE'sini aynı makinede açılış/profil/lisans testlerinden geçirmek gerekir. Bu rapor bir Windows EXE test raporu değildir.

## Sınırlar

- Panel manuel satış/tahsilat kaydı tutar; bankadan ödeme çekmez, çevrimiçi kart tahsilatı yapmaz ve e-Fatura/e-Arşiv/fiş oluşturmaz.
- Yönetim paneli lisans işlemleri için internet ister.
- Windows uygulamasının her eski sürümünün lisans kontrolünü her işlemde sunucudan yenilediği ayrıca Windows'ta doğrulanmalıdır.


## 3.6.0 eğitim kataloğu ve dağıtım sınırları

- Sekiz uzmanlık dalı, L0–L5 seviyeleri, uygulama görevleri, üç soruluk dal bazlı ön testler ve önerilen fiyat taslağı uygulama kaynağına eklendi.
- Lisans kaydına `bundle_code` alanı ekleyen migration eklendi. Bu migration Supabase'e uygulanmadan yeni yönetim paneli paket alanı veritabanına kaydedilemez.
- Bu kaynak pakette özel kullanıcı adı/şifre panelinin HTML/JS/CSS dosyaları bulunur; `license-admin` Edge Function kaynak kodu bu ZIP içinde bulunmadığından sunucu tarafı fonksiyonun varlığı ve sürümü ayrıca doğrulanmalıdır. Mevcut dağıtılmış fonksiyonun çalıştığı varsayılmamalıdır.
- `bundle_code` lisans kaydında tutulur. Özellik bazlı güvenli kilitleme için `licensedContext` yanıtında bundle kapsamının taşınması ve her korunan Edge Function işleminde kapsam kontrolü tamamlanmalıdır. Bu sürüm bu sunucu tarafı entitlement işini tamamlanmış olarak iddia etmez.
- Önerilen fiyatlar canlı satış fiyatı değildir. Vergi, eğitmen saati, ekipman, saha erişimi ve işletme giderleri hesaplandıktan sonra yönetim onayı gerekir.
