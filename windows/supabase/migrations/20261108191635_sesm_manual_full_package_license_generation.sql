create or replace function public.sesm_create_manual_full_package_license(
  p_owner_user_id uuid,
  p_key_hash text,
  p_customer_name text,
  p_customer_email text,
  p_payment_method text,
  p_payment_status text,
  p_amount numeric,
  p_payment_reference text,
  p_admin_note text,
  p_max_devices integer
) returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_license public.sesm_license_keys%rowtype;
  v_core_id uuid;
begin
  if p_owner_user_id is null
     or p_key_hash is null
     or p_key_hash !~ '^[0-9a-f]{64}$'
     or char_length(trim(coalesce(p_customer_name, ''))) not between 2 and 120
     or char_length(coalesce(p_customer_email, '')) > 320
     or char_length(coalesce(p_payment_reference, '')) > 120
     or char_length(coalesce(p_admin_note, '')) > 500
     or p_payment_method not in ('cash', 'bank_transfer')
     or p_payment_status not in ('paid', 'unpaid')
     or p_amount is null
     or p_amount < 0
     or p_amount > 2500
     or p_max_devices not in (1, 2, 3, 5)
  then
    raise exception using errcode = '22023', message = 'MANUAL_LICENSE_INPUT_INVALID';
  end if;

  if not exists (
    select 1 from public.org_memberships m
    join public.org_roles r on r.id = m.role_id
    where m.user_id = p_owner_user_id and m.active = true
      and r.code = 'owner' and r.is_admin_role = true and r.active = true
  ) then
    raise exception using errcode = '42501', message = 'FORBIDDEN_OWNER_ONLY';
  end if;

  if p_payment_status = 'paid' and p_payment_method = 'bank_transfer'
     and char_length(trim(coalesce(p_payment_reference, ''))) < 3
  then
    raise exception using errcode = '22023', message = 'PAYMENT_REFERENCE_REQUIRED';
  end if;

  insert into public.sesm_license_keys (
    key_hash, label, plan_code, bundle_code, max_activations, expires_at,
    created_by, notes, customer_name, customer_email, payment_method,
    payment_status, amount, currency, payment_reference
  ) values (
    p_key_hash, 'FULL PAKET', 'student', 'full_master', p_max_devices, null,
    p_owner_user_id, left(coalesce(p_admin_note, ''), 500),
    trim(p_customer_name), lower(trim(coalesce(p_customer_email, ''))),
    p_payment_method, p_payment_status, p_amount, 'TRY',
    trim(coalesce(p_payment_reference, ''))
  ) returning * into v_license;

  insert into public.license_core (
    product_code, key_hash, key_normalization, legacy_system, legacy_license_id,
    owner_user_id, customer_name, status, plan_code, bundle_code, max_devices,
    expires_at, payment_status, metadata
  ) values (
    'ses-merkezi', p_key_hash, 'alnum_upper', 'ses-merkezi', v_license.id,
    p_owner_user_id, trim(p_customer_name), 'active', 'full_package',
    'full_master', p_max_devices, null, p_payment_status,
    jsonb_build_object('source', 'owner_manual_issue', 'payment_method', p_payment_method,
      'amount', p_amount, 'currency', 'TRY',
      'payment_reference', trim(coalesce(p_payment_reference, '')))
    )
  ) returning id into v_core_id;

  insert into public.license_entitlements (license_id, app_id, capability, enabled, limits)
  select v_core_id, e.app_id, e.capability, e.enabled, e.limits
  from public.license_product_entitlements e
  where e.app_id in ('ses-merkezi', 'ses-merkezi-android')
  on conflict (license_id, app_id, capability) do nothing;

  insert into public.sesm_audit_events (actor_user_id, action, license_id, details)
  values (p_owner_user_id, 'license_created', v_license.id,
    jsonb_build_object('source', 'owner_manual_issue', 'payment_status', p_payment_status,
      'payment_method', p_payment_method, 'amount', p_amount, 'max_devices', p_max_devices)
  );

  insert into public.license_core_audit (license_id, actor_user_id, action, app_id, details)
  values (v_core_id, p_owner_user_id, 'license_created', 'ses-merkezi',
    jsonb_build_object('source', 'owner_manual_issue', 'payment_status', p_payment_status)
  );

  return jsonb_build_object('license_id', v_license.id, 'license_core_id', v_core_id,
    'max_activations', v_license.max_activations, 'payment_status', v_license.payment_status,
    'expires_at', v_license.expires_at);
end;
$$;

revoke all on function public.sesm_create_manual_full_package_license(
  uuid, text, text, text, text, text, numeric, text, text, integer
) from public, anon, authenticated;

grant execute on function public.sesm_create_manual_full_package_license(
  uuid, text, text, text, text, text, numeric, text, text, integer
) to service_role;
