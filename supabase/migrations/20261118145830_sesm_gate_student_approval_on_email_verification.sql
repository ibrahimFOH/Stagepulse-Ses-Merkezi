create or replace function public.sesm_try_link_manual_license(p_student_user_id uuid)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_teacher_user_id uuid;
  v_email text;
  v_current_license_id uuid;
  v_application_status text;
  v_email_verified_at timestamptz;
  v_match_count integer;
  v_license_id uuid;
  v_payment_status text;
begin
  select teacher_user_id,email,license_id,application_status,email_verified_at
    into v_teacher_user_id,v_email,v_current_license_id,v_application_status,v_email_verified_at
  from public.sesm_students
  where user_id=p_student_user_id
  for update;

  if not found or v_current_license_id is not null
     or coalesce(btrim(v_email),'')='' or v_application_status='rejected' then
    return null;
  end if;

  select count(*) into v_match_count
  from public.sesm_license_keys l
  where l.created_by=v_teacher_user_id
    and lower(btrim(l.customer_email))=lower(btrim(v_email))
    and l.customer_email<>''
    and l.is_active=true
    and l.payment_method in ('cash','bank_transfer')
    and coalesce(l.license_kind,'unclassified')<>'test'
    and l.payment_status in ('paid','unpaid')
    and (l.expires_at is null or l.expires_at>now());

  if v_match_count<>1 then return null; end if;

  select l.id,l.payment_status into v_license_id,v_payment_status
  from public.sesm_license_keys l
  where l.created_by=v_teacher_user_id
    and lower(btrim(l.customer_email))=lower(btrim(v_email))
    and l.customer_email<>''
    and l.is_active=true
    and l.payment_method in ('cash','bank_transfer')
    and coalesce(l.license_kind,'unclassified')<>'test'
    and l.payment_status in ('paid','unpaid')
    and (l.expires_at is null or l.expires_at>now())
  limit 1;

  update public.sesm_students
  set license_id=v_license_id,
      application_status=case
        when v_payment_status='paid' and v_email_verified_at is not null
          and application_status in ('pending','legacy') then 'approved'
        else application_status
      end,
      updated_at=now()
  where user_id=p_student_user_id and license_id is null
    and application_status<>'rejected';
  return v_license_id;
end;
$$;

create or replace function public.sesm_sync_student_email_verification()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  if new.email_confirmed_at is distinct from old.email_confirmed_at then
    update public.sesm_students s
    set email_verified_at=new.email_confirmed_at,
        application_status=case
          when new.email_confirmed_at is not null
            and exists (
              select 1 from public.sesm_license_keys l
              where l.id=s.license_id and l.is_active=true
                and l.payment_status='paid'
                and l.payment_method in ('cash','bank_transfer')
                and coalesce(l.license_kind,'unclassified')<>'test'
                and (l.expires_at is null or l.expires_at>now())
            )
            and s.application_status in ('pending','legacy')
          then 'approved' else s.application_status end,
        updated_at=now()
    where s.user_id=new.id;
  end if;
  return new;
end;
$$;

revoke all on function public.sesm_try_link_manual_license(uuid) from public,anon,authenticated;
revoke all on function public.sesm_sync_student_email_verification() from public,anon,authenticated;
grant execute on function public.sesm_sync_student_email_verification() to supabase_auth_admin;
