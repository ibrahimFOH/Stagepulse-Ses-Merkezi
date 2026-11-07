-- pg_net extension kaydını public şemasından extensions şemasına taşı.
-- Kuyruk ve yanıt tabloları önceden kontrol edildi: ikisi de boş.
-- Database Webhook, pg_cron çağrısı veya trigger bağımlılığı bulunmadı.
-- DROP CASCADE kullanılmaz; beklenmeyen bir bağımlılık varsa işlem güvenle durur.
begin;

create schema if not exists extensions;
drop extension pg_net;
create extension pg_net with schema extensions;

commit;
