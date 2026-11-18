alter table public.sesm_license_keys
  add column if not exists customer_phone text not null default '';

do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conrelid='public.sesm_license_keys'::regclass
      and conname='sesm_license_keys_customer_phone_check'
  ) then
    alter table public.sesm_license_keys
      add constraint sesm_license_keys_customer_phone_check
      check (customer_phone='' or customer_phone ~ '^\+905[0-9]{9}$');
  end if;
end $$;

create index if not exists sesm_license_keys_customer_phone_idx
  on public.sesm_license_keys(customer_phone)
  where customer_phone<>'';

create or replace function public.sesm_try_link_manual_license(p_student_user_id uuid)
returns uuid language plpgsql security definer set search_path=''
as $$
declare
  v_teacher_user_id uuid;
  v_email text;
  v_phone text;
  v_current_license_id uuid;
  v_application_status text;
  v_email_verified_at timestamptz;
  v_match_count integer;
  v_license_id uuid;
  v_payment_status text;
begin
  select teacher_user_id,email,phone,license_id,application_status,email_verified_at
    into v_teacher_user_id,v_email,v_phone,v_current_license_id,v_application_status,v_email_verified_at
  from public.sesm_students where user_id=p_student_user_id for update;

  if not found or v_current_license_id is not null
     or (coalesce(btrim(v_email),'')='' and v_phone is null)
     or v_application_status='rejected' then return null; end if;

  select count(*) into v_match_count
  from public.sesm_license_keys l
  where l.created_by=v_teacher_user_id and l.is_active=true
    and l.payment_method in ('cash','bank_transfer')
    and coalesce(l.license_kind,'unclassified')<>'test'
    and l.payment_status in ('paid','unpaid')
    and (l.expires_at is null or l.expires_at>now())
    and (
      (coalesce(btrim(v_email),'')<>'' and l.customer_email<>'' and lower(btrim(l.customer_email))=lower(btrim(v_email)))
      or (v_phone is not null and l.customer_phone=v_phone)
    );

  if v_match_count<>1 then return null; end if;

  select l.id,l.payment_status into v_license_id,v_payment_status
  from public.sesm_license_keys l
  where l.created_by=v_teacher_user_id and l.is_active=true
    and l.payment_method in ('cash','bank_transfer')
    and coalesce(l.license_kind,'unclassified')<>'test'
    and l.payment_status in ('paid','unpaid')
    and (l.expires_at is null or l.expires_at>now())
    and (
      (coalesce(btrim(v_email),'')<>'' and l.customer_email<>'' and lower(btrim(l.customer_email))=lower(btrim(v_email)))
      or (v_phone is not null and l.customer_phone=v_phone)
    )
  limit 1;

  update public.sesm_students
  set license_id=v_license_id,
      application_status=case
        when v_payment_status='paid' and (v_phone is not null or v_email_verified_at is not null)
          and application_status in ('pending','legacy') then 'approved'
        else application_status end,
      updated_at=now()
  where user_id=p_student_user_id and license_id is null and application_status<>'rejected';
  return v_license_id;
end;
$$;

create or replace function public.sesm_attach_manual_license_to_student()
returns trigger language plpgsql security definer set search_path=''
as $$
declare
  v_student_user_id uuid;
  v_student_count integer;
begin
  if coalesce(btrim(new.customer_email),'')=''
     and coalesce(btrim(new.customer_phone),'')='' then return new; end if;
  if not new.is_active or new.payment_method not in ('cash','bank_transfer')
     or coalesce(new.license_kind,'unclassified')='test' then return new; end if;

  select count(distinct s.user_id) into v_student_count
  from public.sesm_students s
  where s.teacher_user_id=new.created_by and s.license_id is null
    and s.application_status<>'rejected'
    and (
      (coalesce(btrim(new.customer_email),'')<>'' and s.email<>'' and lower(btrim(s.email))=lower(btrim(new.customer_email)))
      or (coalesce(btrim(new.customer_phone),'')<>'' and s.phone=new.customer_phone)
    );

  if v_student_count<>1 then return new; end if;

  select s.user_id into v_student_user_id
  from public.sesm_students s
  where s.teacher_user_id=new.created_by and s.license_id is null
    and s.application_status<>'rejected'
    and (
      (coalesce(btrim(new.customer_email),'')<>'' and s.email<>'' and lower(btrim(s.email))=lower(btrim(new.customer_email)))
      or (coalesce(btrim(new.customer_phone),'')<>'' and s.phone=new.customer_phone)
    )
  limit 1;

  if v_student_user_id is not null then perform public.sesm_try_link_manual_license(v_student_user_id); end if;
  return new;
end;
$$;

drop trigger if exists sesm_manual_license_student_link on public.sesm_license_keys;
create trigger sesm_manual_license_student_link
after insert or update of payment_status,is_active,customer_email,customer_phone,created_by
on public.sesm_license_keys
for each row execute function public.sesm_attach_manual_license_to_student();

create or replace function public.sesm_create_manual_full_package_license(
  p_owner_user_id uuid,p_key_hash text,p_customer_name text,p_customer_email text,
  p_payment_method text,p_payment_status text,p_amount numeric,p_payment_reference text,
  p_admin_note text,p_max_devices integer,p_customer_phone text
)
returns jsonb language plpgsql set search_path=''
as $function$
declare
  v_license public.sesm_license_keys%rowtype;
  v_core_id uuid;
begin
  if p_owner_user_id is null or p_key_hash is null or p_key_hash !~ '^[0-9a-f]{64}$'
     or char_length(trim(coalesce(p_customer_name,''))) not between 2 and 120
     or char_length(coalesce(p_customer_email,''))>320
     or char_length(coalesce(p_payment_reference,''))>120
     or char_length(coalesce(p_admin_note,''))>500
     or (coalesce(btrim(p_customer_phone),'')<>'' and btrim(p_customer_phone) !~ '^\+905[0-9]{9}$')
     or p_payment_method not in ('cash','bank_transfer')
     or p_payment_status not in ('paid','unpaid')
     or p_amount is null or p_amount<0 or p_amount>2500
     or p_max_devices not in (1,2,3,5)
  then raise exception using errcode='22023',message='MANUAL_LICENSE_INPUT_INVALID'; end if;

  if not exists (
    select 1 from public.org_memberships m join public.org_roles r on r.id=m.role_id
    where m.user_id=p_owner_user_id and m.active=true
      and r.code='owner' and r.is_admin_role=true and r.active=true
  ) then raise exception using errcode='42501',message='FORBIDDEN_OWNER_ONLY'; end if;

  if p_payment_status='paid' and p_payment_method='bank_transfer'
     and char_length(trim(coalesce(p_payment_reference,'')))<3
  then raise exception using errcode='22023',message='PAYMENT_REFERENCE_REQUIRED'; end if;

  insert into public.sesm_license_keys (
    key_hash,label,plan_code,bundle_code,max_activations,expires_at,created_by,notes,
    customer_name,customer_email,customer_phone,payment_method,payment_status,amount,
    currency,payment_reference,license_kind
  ) values (
    p_key_hash,'FULL PAKET','student','full_master',p_max_devices,null,p_owner_user_id,
    left(coalesce(p_admin_note,''),500),trim(p_customer_name),lower(trim(coalesce(p_customer_email,''))),
    trim(coalesce(p_customer_phone,'')),p_payment_method,p_payment_status,p_amount,'TRY',
    case when p_payment_method='cash' then '' else trim(coalesce(p_payment_reference,'')) end,'sale'
  ) returning * into v_license;

  select id into v_core_id from public.license_core
  where legacy_system='ses-merkezi' and legacy_license_id=v_license.id;
  if v_core_id is null then raise exception using errcode='P0001',message='LICENSE_CORE_SYNC_FAILED'; end if;

  insert into public.license_entitlements(license_id,app_id,capability,enabled,limits)
  select v_core_id,e.app_id,e.capability,e.enabled,e.limits
  from public.license_product_entitlements e
  where e.app_id in ('ses-merkezi','ses-merkezi-android')
  on conflict(license_id,app_id,capability) do nothing;

  insert into public.sesm_audit_events(actor_user_id,action,license_id,details)
  values(p_owner_user_id,'license_created',v_license.id,
    jsonb_build_object('source','owner_manual_issue','payment_status',p_payment_status,
      'payment_method',p_payment_method,'amount',p_amount,'max_devices',p_max_devices,
      'customer_phone',case when v_license.customer_phone='' then null else v_license.customer_phone end));

  insert into public.license_core_audit(license_id,actor_user_id,action,app_id,details)
  values(v_core_id,p_owner_user_id,'license_created','ses-merkezi',
    jsonb_build_object('source','owner_manual_issue','payment_status',p_payment_status));

  return jsonb_build_object('license_id',v_license.id,'license_core_id',v_core_id,
    'max_activations',v_license.max_activations,'payment_status',v_license.payment_status,
    'expires_at',v_license.expires_at);
end;
$function$;

drop function if exists public.sesm_create_manual_full_package_license(uuid,text,text,text,text,text,numeric,text,text,integer);
