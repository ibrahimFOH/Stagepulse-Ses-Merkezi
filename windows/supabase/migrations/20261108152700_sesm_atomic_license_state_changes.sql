create or replace function public.sesm_set_license_payment_status(
  p_license_id uuid,
  p_owner_user_id uuid,
  p_payment_status text
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_license public.sesm_license_keys%rowtype;
begin
  if p_payment_status not in ('paid', 'unpaid', 'refunded') then
    raise exception using errcode = '22023', message = 'INVALID_PAYMENT_STATUS';
  end if;

  select * into v_license
  from public.sesm_license_keys
  where id = p_license_id and created_by = p_owner_user_id
  for update;

  if not found then
    raise exception using errcode = 'P0002', message = 'LICENSE_NOT_FOUND';
  end if;

  update public.sesm_license_keys
  set payment_status = p_payment_status
  where id = p_license_id;

  if p_payment_status <> 'paid' then
    update public.sesm_activations
    set is_active = false
    where license_id = p_license_id and is_active = true;

    update public.sesm_students
    set is_active = false, updated_at = now()
    where license_id = p_license_id
      and teacher_user_id = p_owner_user_id
      and is_active = true;
  end if;

  return jsonb_build_object(
    'id', v_license.id,
    'payment_status', p_payment_status,
    'customer_name', v_license.customer_name
  );
end;
$$;

create or replace function public.sesm_revoke_license_atomic(
  p_license_id uuid,
  p_owner_user_id uuid
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_license public.sesm_license_keys%rowtype;
begin
  select * into v_license
  from public.sesm_license_keys
  where id = p_license_id and created_by = p_owner_user_id
  for update;

  if not found then
    raise exception using errcode = 'P0002', message = 'LICENSE_NOT_FOUND';
  end if;

  update public.sesm_license_keys
  set is_active = false
  where id = p_license_id;

  update public.sesm_activations
  set is_active = false
  where license_id = p_license_id and is_active = true;

  update public.sesm_students
  set is_active = false, updated_at = now()
  where license_id = p_license_id
    and teacher_user_id = p_owner_user_id
    and is_active = true;

  return jsonb_build_object('id', v_license.id, 'is_active', false);
end;
$$;

revoke all on function public.sesm_set_license_payment_status(uuid, uuid, text) from public, anon, authenticated;
revoke all on function public.sesm_revoke_license_atomic(uuid, uuid) from public, anon, authenticated;
grant execute on function public.sesm_set_license_payment_status(uuid, uuid, text) to service_role;
grant execute on function public.sesm_revoke_license_atomic(uuid, uuid) to service_role;
