-- Stagepulse 3.5.4: manuel satış ve ödeme kaydı.
-- Mevcut lisansların erişimi geriye dönük kapatılmaz; yeni lisans oluşturulurken uygulama
-- ödeme durumunu açıkça gönderir. Aktivasyon RPC'si ödeme onayını ayrıca zorunlu tutar.
alter table public.sesm_license_keys
  add column if not exists customer_name text not null default '' check (char_length(customer_name) <= 120),
  add column if not exists customer_email text not null default '' check (char_length(customer_email) <= 320),
  add column if not exists payment_method text not null default 'legacy' check (payment_method in ('cash','bank_transfer','card','other','legacy')),
  add column if not exists payment_status text not null default 'paid' check (payment_status in ('paid','unpaid','refunded')),
  add column if not exists amount numeric(12,2) not null default 0 check (amount >= 0 and amount <= 999999999),
  add column if not exists currency text not null default 'TRY' check (currency ~ '^[A-Z]{3}$'),
  add column if not exists payment_reference text not null default '' check (char_length(payment_reference) <= 120);

create or replace function public.sesm_activate_license(
  p_key_hash text, p_user_id uuid, p_device_hash text, p_email text, p_display_name text
) returns jsonb
language plpgsql security definer set search_path = public, pg_temp
as $$
declare lic public.sesm_license_keys%rowtype; existing public.sesm_students%rowtype; used_seats integer;
begin
  if p_key_hash !~ '^[0-9a-f]{64}$' or p_device_hash !~ '^[0-9a-f]{64}$' then
    raise exception 'INVALID_ACTIVATION_DATA' using errcode='22023';
  end if;
  select * into lic from public.sesm_license_keys where key_hash=p_key_hash for update;
  if not found or not lic.is_active or (lic.expires_at is not null and lic.expires_at <= now()) then
    raise exception 'LICENSE_INVALID_OR_EXPIRED' using errcode='P0001';
  end if;
  if lic.payment_status is distinct from 'paid' then
    raise exception 'LICENSE_PAYMENT_REQUIRED' using errcode='P0001';
  end if;
  select * into existing from public.sesm_students where user_id=p_user_id for update;
  if found and existing.teacher_user_id <> lic.created_by then
    raise exception 'STUDENT_ALREADY_LINKED' using errcode='P0001';
  end if;
  if exists(select 1 from public.sesm_activations where license_id=lic.id and device_hash=p_device_hash and is_active=true and user_id<>p_user_id) then
    raise exception 'DEVICE_BOUND_TO_OTHER_USER' using errcode='P0001';
  end if;
  select count(distinct device_hash)::integer into used_seats from public.sesm_activations where license_id=lic.id and is_active=true;
  if not exists(select 1 from public.sesm_activations where license_id=lic.id and device_hash=p_device_hash and is_active=true)
     and used_seats >= lic.max_activations then
    raise exception 'LICENSE_ACTIVATION_LIMIT' using errcode='P0001';
  end if;
  insert into public.sesm_activations(license_id,user_id,device_hash,activated_at,last_seen_at,is_active)
  values(lic.id,p_user_id,p_device_hash,now(),now(),true)
  on conflict(license_id,device_hash) do update set user_id=excluded.user_id,last_seen_at=now(),is_active=true;
  insert into public.sesm_students(user_id,teacher_user_id,license_id,email,display_name,is_active,updated_at)
  values(p_user_id,lic.created_by,lic.id,left(coalesce(p_email,''),320),left(coalesce(p_display_name,''),120),true,now())
  on conflict(user_id) do update set license_id=excluded.license_id,email=excluded.email,
    display_name=case when excluded.display_name='' then public.sesm_students.display_name else excluded.display_name end,
    is_active=true,updated_at=now();
  insert into public.sesm_audit_events(actor_user_id,action,subject_user_id,license_id,details)
    values(p_user_id,'license_activated',p_user_id,lic.id,jsonb_build_object('device_hash_prefix',left(p_device_hash,8)));
  return jsonb_build_object('ok',true,'license_id',lic.id,'expires_at',lic.expires_at,'plan_code',lic.plan_code);
end;
$$;


-- Service-role only, matching the existing license data access model.
revoke all on function public.sesm_activate_license(text,uuid,text,text,text) from public, anon, authenticated;
grant execute on function public.sesm_activate_license(text,uuid,text,text,text) to service_role;
