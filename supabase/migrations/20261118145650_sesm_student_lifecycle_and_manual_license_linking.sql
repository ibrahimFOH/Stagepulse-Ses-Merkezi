alter table public.sesm_students
  add column if not exists phone text,
  add column if not exists email_verified_at timestamptz,
  add column if not exists application_status text not null default 'pending',
  add column if not exists application_note text not null default '',
  add column if not exists reviewed_at timestamptz,
  add column if not exists reviewed_by uuid;

do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conrelid='public.sesm_students'::regclass
      and conname='sesm_students_application_status_check'
  ) then
    alter table public.sesm_students
      add constraint sesm_students_application_status_check
      check (application_status in ('pending','approved','rejected','legacy'));
  end if;
  if not exists (
    select 1 from pg_constraint
    where conrelid='public.sesm_students'::regclass
      and conname='sesm_students_phone_format_check'
  ) then
    alter table public.sesm_students
      add constraint sesm_students_phone_format_check
      check (phone is null or phone ~ '^\+905[0-9]{9}$');
  end if;
  if not exists (
    select 1 from pg_constraint
    where conrelid='public.sesm_students'::regclass
      and conname='sesm_students_reviewed_by_fkey'
  ) then
    alter table public.sesm_students
      add constraint sesm_students_reviewed_by_fkey
      foreign key (reviewed_by) references auth.users(id) on delete set null;
  end if;
end $$;

create unique index if not exists sesm_students_email_lower_unique
  on public.sesm_students (lower(email))
  where coalesce(email,'') <> '';

create unique index if not exists sesm_students_phone_unique
  on public.sesm_students (phone)
  where phone is not null;

update public.sesm_students s
set
  phone = coalesce(
    nullif(btrim(u.raw_user_meta_data->>'phone'),''),
    nullif(btrim(u.phone),'')
  ),
  email_verified_at = u.email_confirmed_at,
  application_status = case
    when s.is_active = true and exists (
      select 1
      from public.sesm_license_keys l
      where l.id=s.license_id
        and l.is_active=true
        and l.payment_status='paid'
        and (l.expires_at is null or l.expires_at > now())
    ) then 'approved'
    else 'legacy'
  end,
  updated_at = now()
from auth.users u
where u.id=s.user_id
  and s.application_status='pending';

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
  v_match_count integer;
  v_license_id uuid;
  v_payment_status text;
begin
  select teacher_user_id,email,license_id,application_status
    into v_teacher_user_id,v_email,v_current_license_id,v_application_status
  from public.sesm_students
  where user_id=p_student_user_id
  for update;

  if not found
     or v_current_license_id is not null
     or coalesce(btrim(v_email),'')=''
     or v_application_status='rejected' then
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
        when v_payment_status='paid' and application_status in ('pending','legacy')
          then 'approved'
        else application_status
      end,
      updated_at=now()
  where user_id=p_student_user_id
    and license_id is null
    and application_status<>'rejected';

  return v_license_id;
end;
$$;

revoke all on function public.sesm_try_link_manual_license(uuid) from public,anon,authenticated;

create or replace function public.sesm_handle_auth_student_signup()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_owner_ids uuid[];
  v_teacher_user_id uuid;
  v_display_name text;
  v_phone text;
begin
  if new.email is null
     or lower(new.email) like '%@students.stagepulse.invalid'
     or coalesce(new.raw_app_meta_data->>'provider','') <> 'email'
     or lower(coalesce(new.raw_user_meta_data->>'account_type','')) in ('admin','owner','staff')
     or (
       not (coalesce(new.raw_user_meta_data,'{}'::jsonb) ? 'display_name')
       and lower(coalesce(new.raw_user_meta_data->>'account_type','')) <> 'student'
     )
     or exists (
       select 1 from public.admin_profiles ap
       where ap.user_id=new.id and ap.active=true
     ) then
    return new;
  end if;

  select array_agg(distinct m.user_id)
    into v_owner_ids
  from public.org_memberships m
  join public.org_roles r on r.id=m.role_id
  where m.active=true
    and r.code='owner'
    and r.is_admin_role=true
    and r.active=true;

  if coalesce(cardinality(v_owner_ids),0) <> 1 then
    raise exception 'STUDENT_ENROLLMENT_UNAVAILABLE';
  end if;
  v_teacher_user_id := v_owner_ids[1];

  v_display_name := left(
    coalesce(
      nullif(btrim(new.raw_user_meta_data->>'display_name'),''),
      nullif(btrim(new.raw_user_meta_data->>'full_name'),''),
      split_part(new.email,'@',1)
    ),
    120
  );

  v_phone := nullif(btrim(new.raw_user_meta_data->>'phone'),'');
  if v_phone is not null and v_phone !~ '^\+905[0-9]{9}$' then
    v_phone := null;
  end if;

  insert into public.sesm_students (
    user_id,teacher_user_id,license_id,email,phone,display_name,is_active,
    email_verified_at,application_status,application_note
  ) values (
    new.id,v_teacher_user_id,null,lower(new.email),v_phone,v_display_name,true,
    new.email_confirmed_at,'pending',''
  )
  on conflict (user_id) do nothing;

  perform public.sesm_try_link_manual_license(new.id);

  insert into public.sesm_audit_events(actor_user_id,action,subject_user_id,details)
  values (
    v_teacher_user_id,'student_registered',new.id,
    jsonb_build_object(
      'source','email_signup',
      'profile_status',(select application_status from public.sesm_students where user_id=new.id),
      'email_verified',new.email_confirmed_at is not null
    )
  );

  return new;
end;
$$;

revoke all on function public.sesm_handle_auth_student_signup() from public,anon,authenticated;
grant execute on function public.sesm_handle_auth_student_signup() to supabase_auth_admin;

create or replace function public.sesm_attach_manual_license_to_student()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_student_user_id uuid;
begin
  if coalesce(btrim(new.customer_email),'')='' or not new.is_active
     or new.payment_method not in ('cash','bank_transfer')
     or coalesce(new.license_kind,'unclassified')='test' then
    return new;
  end if;

  select s.user_id into v_student_user_id
  from public.sesm_students s
  where s.teacher_user_id=new.created_by
    and lower(btrim(s.email))=lower(btrim(new.customer_email))
    and s.license_id is null
    and s.application_status<>'rejected'
  limit 1;

  if v_student_user_id is not null then
    perform public.sesm_try_link_manual_license(v_student_user_id);
  end if;

  return new;
end;
$$;

revoke all on function public.sesm_attach_manual_license_to_student() from public,anon,authenticated;

drop trigger if exists sesm_manual_license_student_link on public.sesm_license_keys;
create trigger sesm_manual_license_student_link
after insert or update of payment_status,is_active,customer_email,created_by
on public.sesm_license_keys
for each row
execute function public.sesm_attach_manual_license_to_student();

with owner_choice as (
  select
    (array_agg(distinct m.user_id))[1] as owner_user_id,
    count(distinct m.user_id) as owner_count
  from public.org_memberships m
  join public.org_roles r on r.id=m.role_id
  where m.active=true and r.code='owner' and r.is_admin_role=true and r.active=true
),
orphan_candidates as (
  select
    u.id,o.owner_user_id,lower(u.email) as email,
    nullif(btrim(u.raw_user_meta_data->>'phone'),'') as phone,
    left(coalesce(
      nullif(btrim(u.raw_user_meta_data->>'display_name'),''),
      nullif(btrim(u.raw_user_meta_data->>'full_name'),''),
      split_part(u.email,'@',1)
    ),120) as display_name,
    u.email_confirmed_at
  from auth.users u
  cross join owner_choice o
  left join public.sesm_students s on s.user_id=u.id
  left join public.admin_profiles ap on ap.user_id=u.id and ap.active=true
  where o.owner_count=1
    and s.user_id is null and ap.user_id is null
    and u.email is not null
    and lower(u.email) not like '%@students.stagepulse.invalid'
    and coalesce(u.raw_app_meta_data->>'provider','')='email'
    and lower(coalesce(u.raw_user_meta_data->>'account_type','')) not in ('admin','owner','staff')
    and (
      coalesce(u.raw_user_meta_data->>'account_type','')='student'
      or coalesce(u.raw_user_meta_data,'{}'::jsonb) ? 'display_name'
    )
)
insert into public.sesm_students (
  user_id,teacher_user_id,license_id,email,phone,display_name,is_active,
  email_verified_at,application_status,application_note
)
select
  id,owner_user_id,null,email,
  case when phone ~ '^\+905[0-9]{9}$' then phone else null end,
  display_name,true,email_confirmed_at,'pending',''
from orphan_candidates
on conflict (user_id) do nothing;

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
)
returns jsonb
language plpgsql
set search_path = ''
as $function$
declare
  v_license public.sesm_license_keys%rowtype;
  v_core_id uuid;
begin
  if p_owner_user_id is null
     or p_key_hash is null
     or p_key_hash !~ '^[0-9a-f]{64}$'
     or char_length(trim(coalesce(p_customer_name,''))) not between 2 and 120
     or char_length(coalesce(p_customer_email,'')) > 320
     or char_length(coalesce(p_payment_reference,'')) > 120
     or char_length(coalesce(p_admin_note,'')) > 500
     or p_payment_method not in ('cash','bank_transfer')
     or p_payment_status not in ('paid','unpaid')
     or p_amount is null or p_amount<0 or p_amount>2500
     or p_max_devices not in (1,2,3,5)
  then
    raise exception using errcode='22023',message='MANUAL_LICENSE_INPUT_INVALID';
  end if;

  if not exists (
    select 1 from public.org_memberships m
    join public.org_roles r on r.id=m.role_id
    where m.user_id=p_owner_user_id and m.active=true
      and r.code='owner' and r.is_admin_role=true and r.active=true
  ) then
    raise exception using errcode='42501',message='FORBIDDEN_OWNER_ONLY';
  end if;

  if p_payment_status='paid' and p_payment_method='bank_transfer'
     and char_length(trim(coalesce(p_payment_reference,'')))<3
  then
    raise exception using errcode='22023',message='PAYMENT_REFERENCE_REQUIRED';
  end if;

  insert into public.sesm_license_keys (
    key_hash,label,plan_code,bundle_code,max_activations,expires_at,
    created_by,notes,customer_name,customer_email,payment_method,
    payment_status,amount,currency,payment_reference,license_kind
  ) values (
    p_key_hash,'FULL PAKET','student','full_master',p_max_devices,null,
    p_owner_user_id,left(coalesce(p_admin_note,''),500),
    trim(p_customer_name),lower(trim(coalesce(p_customer_email,''))),
    p_payment_method,p_payment_status,p_amount,'TRY',
    case when p_payment_method='cash' then '' else trim(coalesce(p_payment_reference,'')) end,
    'sale'
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
      'payment_method',p_payment_method,'amount',p_amount,'max_devices',p_max_devices));

  insert into public.license_core_audit(license_id,actor_user_id,action,app_id,details)
  values(v_core_id,p_owner_user_id,'license_created','ses-merkezi',
    jsonb_build_object('source','owner_manual_issue','payment_status',p_payment_status));

  return jsonb_build_object('license_id',v_license.id,'license_core_id',v_core_id,
    'max_activations',v_license.max_activations,'payment_status',v_license.payment_status,
    'expires_at',v_license.expires_at);
end;
$function$;
