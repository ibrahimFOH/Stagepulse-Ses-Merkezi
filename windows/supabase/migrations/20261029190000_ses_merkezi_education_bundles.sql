-- Stagepulse Ses Merkezi 3.6.0: eğitim paketi kapsamı lisans kaydına eklenir.
alter table public.sesm_license_keys
  add column if not exists bundle_code text not null default 'start';

alter table public.sesm_license_keys
  drop constraint if exists sesm_license_keys_bundle_code_check;

alter table public.sesm_license_keys
  add constraint sesm_license_keys_bundle_code_check
  check (bundle_code in ('start','live_sound','rf_wireless','pa_system','studio_post','spl_acoustics','digital_console','full_master','institution'));

comment on column public.sesm_license_keys.bundle_code is
  'Stagepulse eğitim kapsamı. Özellik yetkilendirmesi Edge Function tarafında ayrıca uygulanmalıdır.';
