-- Stagepulse Ses Mühendisliği Merkezi: lisans, cihaz aktivasyonu ve öğretmen onaylı öğrenci ilerlemesi.
-- Mevcut Stagepulse tablolarını değiştirmez. Tüm yazma/okuma işlemleri Edge Function üzerinden yapılır.
create table if not exists public.sesm_license_keys (
  id uuid primary key default gen_random_uuid(),
  key_hash text not null unique check (key_hash ~ '^[0-9a-f]{64}$'),
  label text not null default 'Öğrenci lisansı' check (char_length(label) between 1 and 120),
  plan_code text not null default 'student' check (plan_code in ('student','classroom','lifetime')),
  max_activations integer not null default 1 check (max_activations between 1 and 100),
  expires_at timestamptz,
  is_active boolean not null default true,
  created_by uuid not null references auth.users(id),
  created_at timestamptz not null default now(),
  notes text not null default '' check (char_length(notes) <= 500)
);

create table if not exists public.sesm_activations (
  id uuid primary key default gen_random_uuid(),
  license_id uuid not null references public.sesm_license_keys(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  device_hash text not null check (device_hash ~ '^[0-9a-f]{64}$'),
  activated_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  is_active boolean not null default true,
  unique (license_id, device_hash)
);
create index if not exists sesm_activations_user_idx on public.sesm_activations(user_id, is_active);

create table if not exists public.sesm_students (
  user_id uuid primary key references auth.users(id) on delete cascade,
  teacher_user_id uuid not null references auth.users(id),
  license_id uuid not null references public.sesm_license_keys(id),
  email text not null default '' check (char_length(email) <= 320),
  display_name text not null default '' check (char_length(display_name) <= 120),
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists sesm_students_teacher_idx on public.sesm_students(teacher_user_id, is_active, created_at desc);

create table if not exists public.sesm_progress (
  student_user_id uuid not null references public.sesm_students(user_id) on delete cascade,
  module_id text not null check (module_id in ('frequency','ear','calculators','acoustics','rta','mixer','wav','lufs','cues','checklists','docs')),
  completed boolean not null default false,
  marked_by uuid references auth.users(id),
  marked_at timestamptz,
  teacher_note text not null default '' check (char_length(teacher_note) <= 1000),
  updated_at timestamptz not null default now(),
  primary key (student_user_id, module_id),
  check ((completed = false and marked_at is null) or (completed = true and marked_at is not null and marked_by is not null))
);

create table if not exists public.sesm_audit_events (
  id uuid primary key default gen_random_uuid(),
  actor_user_id uuid references auth.users(id) on delete set null,
  action text not null check (char_length(action) between 1 and 80),
  subject_user_id uuid references auth.users(id) on delete set null,
  license_id uuid references public.sesm_license_keys(id) on delete set null,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists sesm_audit_created_idx on public.sesm_audit_events(created_at desc);

-- License activation is a single transaction and locks the license row to prevent concurrent seat overflow.
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

alter table public.sesm_license_keys enable row level security;
alter table public.sesm_activations enable row level security;
alter table public.sesm_students enable row level security;
alter table public.sesm_progress enable row level security;
alter table public.sesm_audit_events enable row level security;

revoke all on table public.sesm_license_keys, public.sesm_activations, public.sesm_students, public.sesm_progress, public.sesm_audit_events from anon, authenticated;
grant all on table public.sesm_license_keys, public.sesm_activations, public.sesm_students, public.sesm_progress, public.sesm_audit_events to service_role;
revoke all on function public.sesm_activate_license(text,uuid,text,text,text) from public, anon, authenticated;
grant execute on function public.sesm_activate_license(text,uuid,text,text,text) to service_role;
