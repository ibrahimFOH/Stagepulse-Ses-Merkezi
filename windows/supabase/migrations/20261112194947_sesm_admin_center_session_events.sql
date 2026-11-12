create table if not exists public.sesm_session_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  event_type text not null check (event_type in ('session_verified','logout')),
  app_id text not null default 'ses-merkezi',
  platform text not null default 'unknown' check (platform in ('windows','android','web','unknown')),
  user_agent text,
  created_at timestamptz not null default now()
);
create index if not exists sesm_session_events_created_at_idx on public.sesm_session_events (created_at desc);
create index if not exists sesm_session_events_user_created_idx on public.sesm_session_events (user_id, created_at desc);
alter table public.sesm_session_events enable row level security;
revoke all on public.sesm_session_events from anon, authenticated;
grant all on public.sesm_session_events to service_role;
