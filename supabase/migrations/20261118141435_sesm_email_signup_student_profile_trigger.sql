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
begin
  -- Phone-based accounts use the existing student_signup flow and internal alias.
  -- Non-student service accounts are deliberately excluded.
  if new.email is null
     or lower(new.email) like '%@students.stagepulse.invalid'
     or coalesce(new.raw_app_meta_data->>'provider', '') <> 'email'
     or lower(coalesce(new.raw_user_meta_data->>'account_type', '')) in ('admin','owner','staff')
     or not (coalesce(new.raw_user_meta_data, '{}'::jsonb) ? 'display_name') then
    return new;
  end if;

  select array_agg(distinct m.user_id)
    into v_owner_ids
  from public.org_memberships m
  join public.org_roles r on r.id = m.role_id
  where m.active = true
    and r.code = 'owner'
    and r.is_admin_role = true
    and r.active = true;

  if coalesce(cardinality(v_owner_ids), 0) <> 1 then
    raise exception 'STUDENT_ENROLLMENT_UNAVAILABLE';
  end if;
  v_teacher_user_id := v_owner_ids[1];

  v_display_name := left(
    coalesce(
      nullif(btrim(new.raw_user_meta_data->>'display_name'), ''),
      nullif(btrim(new.raw_user_meta_data->>'full_name'), ''),
      split_part(new.email, '@', 1)
    ),
    120
  );

  insert into public.sesm_students (
    user_id, teacher_user_id, license_id, email, display_name, is_active
  ) values (
    new.id, v_teacher_user_id, null, lower(new.email), v_display_name, true
  )
  on conflict (user_id) do nothing;

  return new;
end;
$$;

revoke all on function public.sesm_handle_auth_student_signup() from public, anon, authenticated;
grant execute on function public.sesm_handle_auth_student_signup() to supabase_auth_admin;

drop trigger if exists sesm_auth_student_profile_after_insert on auth.users;
create trigger sesm_auth_student_profile_after_insert
after insert on auth.users
for each row
execute function public.sesm_handle_auth_student_signup();
