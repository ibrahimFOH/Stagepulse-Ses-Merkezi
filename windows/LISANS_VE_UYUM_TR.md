# Lisans ve yeniden dağıtım notu

Bu tek uygulama deposu, önceki arşivdeki 53 kaynağın karar tablosunu saklar; 53 ZIP'in tamamını veya içlerindeki çalıştırılabilir dosyaları yeniden dağıtmaz.

- Frekans Bulucu: kendi kaynak LICENSE dosyasında CC0 1.0 beyanı bulunur ve bu lisans bildirimi modül içinde korunur.
- Kullanıcının önceki çalışma alanındaki bazı HTML projelerinde ve modellerde açık LICENSE bulunmuyordu. Bu kodlar doğrudan yeni öğrenci paketine kopyalanmamıştır; uyumlu iş akışları arayüzde bağımsız biçimde yeniden oluşturulmuştur.
- MacOS'a özgü uygulamalar, belirli mikser/USB donanımına bağlı prototipler, büyük ML modelleri, ayrı genel amaçlı asistanlar, portföy siteleri ve kişisel kart projeleri Windows ses mühendisliği EXE'sine dahil edilmemiştir. Karar gerekçeleri `docs/REPO_BIRLESTIRME_MATRISI_TR.md` dosyasındadır.
- Frekans Bulucu haricindeki bu yeni uygulama modüllerinin kaynak kodu öğrenci/kurum için özel dağıtım amacıyla hazırlanmıştır. Kurum dışına kaynak kodu veya marka/üçüncü taraf materyali dağıtmadan önce fikri mülkiyet denetimi yapın.
- Microsoft WebView2 Runtime yalnızca resmi Microsoft adresinden indirilir; imza doğrulanmadan derlemeye konulmaz. Microsoft'un çevrimdışı dağıtım rehberi: https://learn.microsoft.com/microsoft-edge/webview2/concepts/distribution


## Ortak lisans ve kimlik çekirdeği

Stagepulse, Ses Merkezi ve JARVIS aynı Supabase Auth kimliğini kullanır. Lisans kayıtları ortak `license_core` siciline eşitlenir; Ses Merkezi öğrenci ve eğitim ilerleme kayıtları ürün modülünde kalır.

- Ortak API: `license-core` Edge Function (JWT doğrulaması zorunlu).
- Lisans anahtarları yalnızca SHA-256 özetiyle saklanır.
- Cihaz sınırı ortak lisans sicilinde uygulanır.
- Eski `sesm_license_keys` ve `sesm_activations` kayıtları tetikleyicilerle ortak sicile eşitlenir.
- Eski lisans kayıtları silinmez; yönetim ve aktivasyon uyumluluğu korunur.
- Yönetici yetkisi Supabase Auth kullanıcısının aktif `owner` rolüyle doğrulanır.
