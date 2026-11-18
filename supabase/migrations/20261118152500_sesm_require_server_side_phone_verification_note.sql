
create or replace function public.sesm_review_student_application(
  p_student_user_id uuid,
  p_owner_user_id uuid,
  p_application_status text,
  p_application_note text default ''
)
returns jsonb
language plpgsql
security definer
set search_path=''
as $$
declare
  v_student public.sesm_students%rowtype;
  v_license_id uuid;
  v_note text:=left(btrim(coalesce(p_application_note,'')),1000);
begin
  if p_application_status not in ('pending','approved','rejected')
     or p_student_user_id is null or p_owner_user_id is null then
    raise exception using errcode='22023',message='STUDENT_APPLICATION_DATA_INVALID';
  end if;

  if not exists (
    select 1 from public.org_memberships m
    join public.org_roles r on r.id=m.role_id
    where m.user_id=p_owner_user_id and m.active=true
      and r.code='owner' and r.is_admin_role=true and r.active=true
  ) then
    raise exception using errcode='42501',message='FORBIDDEN_OWNER_ONLY';
  end if;

  select * into v_student
  from public.sesm_students
  where user_id=p_student_user_id and teacher_user_id=p_owner_user_id
  for update;

  if not found then
    raise exception using errcode='P0002',message='STUDENT_NOT_FOUND';
  end if;

  if p_application_status='approved'
     and coalesce(btrim(v_student.email),'')<>''
     and v_student.email_verified_at is null then
    raise exception using errcode='P0001',message='STUDENT_EMAIL_NOT_VERIFIED';
  end if;

  if p_application_status='approved'
     and coalesce(btrim(v_student.email),'')=''
     and v_student.phone is not null
     and (
       position('Telefon doğrulaması:' in v_note)<>1
       or length(btrim(substr(v_note,length('Telefon doğrulaması:')+1)))<3
     ) then
    raise exception using errcode='P0001',message='STUDENT_PHONE_VERIFICATION_NOTE_REQUIRED';
  end if;

  if p_application_status in ('pending','rejected')
     and v_student.license_id is not null then
    raise exception using errcode='P0001',message='STUDENT_HAS_LINKED_LICENSE';
  end if;

  update public.sesm_students
  set application_status=p_application_status,
      application_note=v_note,
      reviewed_at=case when p_application_status='pending' then null else now() end,
      reviewed_by=case when p_application_status='pending' then null else p_owner_user_id end,
      is_active=(p_application_status<>'rejected'),
      updated_at=now()
  where user_id=p_student_user_id;

  if p_application_status='approved' then
    v_license_id:=public.sesm_try_link_manual_license(p_student_user_id);
  else
    v_license_id:=v_student.license_id;
  end if;

  select * into v_student
  from public.sesm_students
  where user_id=p_student_user_id;

  insert into public.sesm_audit_events(actor_user_id,action,subject_user_id,license_id,details)
  values(
    p_owner_user_id,
    'student_application_'||p_application_status,
    p_student_user_id,
    coalesce(v_student.license_id,v_license_id),
    jsonb_build_object(
      'application_note',v_note,
      'email_verified',v_student.email_verified_at is not null,
      'license_linked',v_student.license_id is not null
    )
  );

  return jsonb_build_object(
    'user_id',v_student.user_id,
    'email',v_student.email,
    'phone',v_student.phone,
    'display_name',v_student.display_name,
    'is_active',v_student.is_active,
    'license_id',v_student.license_id,
    'application_status',v_student.application_status,
    'application_note',v_student.application_note,
    'email_verified_at',v_student.email_verified_at,
    'reviewed_at',v_student.reviewed_at
  );
end;
$$;

revoke all on function public.sesm_review_student_application(uuid,uuid,text,text) from public,anon,authenticated;
grant execute on function public.sesm_review_student_application(uuid,uuid,text,text) to service_role;

