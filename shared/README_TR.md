# Stagepulse Ses Merkezi · Ortak kaynaklar

Bu klasör, Stagepulse Ses Merkezi'nin Android ve Windows istemcilerinin gerçekten ortak kullandığı, gizli bilgi içermeyen kaynaklar için ayrılmıştır.

## Kaynak düzeni

- Ortak arayüz ve ses aracı kaynaklarının güncel kopyaları Android ve Windows uygulama varlıklarında tutulur.
- `android/app/src/main/assets/ui/first_party_tools.js` ile `windows/ui/first_party_tools.js` aynı içerikte olmalıdır.
- Ortak kaynak değişiklikleri iki istemciye birlikte uygulanmalı ve `windows/tests/test_first_party_tools.js` içindeki eşitlik denetimi geçmelidir.

**Geçerli uygulama sürümü:** 4.0.0
