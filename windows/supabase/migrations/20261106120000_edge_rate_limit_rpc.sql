-- Atomik Edge Function rate-limit RPC. Anahtarlar ham IP/kullanıcı değeri olarak saklanmaz.
create schema if not exists extensions;
create extension if not exists pgcrypto with schema extensions;
create table if not exists private.edge_rate_limits (
  key_hash text primary key check (key_hash ~ '^[0-9a-f]{64}$'),
  window_started_at timestamptz not null,
  request_count integer not null check (request_count >= 0),
  updated_at timestamptz not null default now()
);
revoke all on private.edge_rate_limits from public, anon, authenticated;
grant all on private.edge_rate_limits to service_role;

create or replace function public.check_login_rate_limit(p_key text, p_max integer default 60)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_hash text;
  v_now timestamptz := clock_timestamp();
  v_count integer;
begin
  if p_key is null or length(p_key) < 1 or length(p_key) > 512
     or p_max is null or p_max < 1 or p_max > 10000 then
    return false;
  end if;

  v_hash := encode(extensions.digest(convert_to(p_key, 'UTF8'), 'sha256'), 'hex');

  perform pg_advisory_xact_lock(hashtextextended(v_hash, 0));

  insert into private.edge_rate_limits(key_hash, window_started_at, request_count, updated_at)
  values (v_hash, v_now, 1, v_now)
  on conflict (key_hash) do update
    set window_started_at = case
          when private.edge_rate_limits.window_started_at <= v_now - interval '1 minute' then v_now
          else private.edge_rate_limits.window_started_at end,
        request_count = case
          when private.edge_rate_limits.window_started_at <= v_now - interval '1 minute' then 1
          else private.edge_rate_limits.request_count + 1 end,
        updated_at = v_now
  returning request_count into v_count;

  if random() < 0.01 then
    delete from private.edge_rate_limits
    where updated_at < v_now - interval '1 day';
  end if;

  return v_count <= p_max;
end;
$$;

revoke all on function public.check_login_rate_limit(text, integer) from public, anon, authenticated;
grant execute on function public.check_login_rate_limit(text, integer) to service_role;
