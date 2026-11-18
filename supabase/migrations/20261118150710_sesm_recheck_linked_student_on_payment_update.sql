
create or replace function public.sesm_attach_manual_license_to_student()
returns trigger language plpgsql security definer set search_path=''
as $$
declare
  v_student_user_id uuid;
  v_student_count integer;
begin
  if coalesce(btrim(new.customer_email),'')=''
     and coalesce(btrim(new.customer_phone),'')='' then return new; end if;
  if not new.is_active
     or new.payment_method not in ('cash','bank_transfer')
     or coalesce(new.license_kind,'unclassified')='test' then return new; end if;

  select count(distinct s.user_id) into v_student_count
  from public.sesm_students s
  where s.teacher_user_id=new.created_by
    and (s.license_id is null or s.license_id=new.id)
    and s.application_status<>'rejected'
    and (
      (coalesce(btrim(new.customer_email),'')<>'' and s.email<>'' and lower(btrim(s.email))=lower(btrim(new.customer_email)))
      or (coalesce(btrim(new.customer_phone),'')<>'' and s.phone=new.customer_phone)
    );

  if v_student_count<>1 then return new; end if;

  select s.user_id into v_student_user_id
  from public.sesm_students s
  where s.teacher_user_id=new.created_by
    and (s.license_id is null or s.license_id=new.id)
    and s.application_status<>'rejected'
    and (
      (coalesce(btrim(new.customer_email),'')<>'' and s.email<>'' and lower(btrim(s.email))=lower(btrim(new.customer_email)))
      or (coalesce(btrim(new.customer_phone),'')<>'' and s.phone=new.customer_phone)
    )
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
after insert or update of payment_status,is_active,customer_email,customer_phone,created_by
on public.sesm_license_keys
for each row
execute function public.sesm_attach_manual_license_to_student();

