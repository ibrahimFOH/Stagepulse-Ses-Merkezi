-- Ortak Edge Function rate limit RPC. Supabase migration 20261105211714.
-- Service-role only; anahtar veritabanında düz metin tutulmaz.
grant usage on schema private to service_role;
grant select, insert, delete on table private.rate_limits to service_role;

create or replace function public.check_login_rate_limit(p_key text, p_max integer default 60)
returns boolean
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_key text;
  v_limit integer;
  v_count integer;
  v_now timestamptz := clock_timestamp();
begin
  if p_key is null or length(trim(p_key)) = 0 or length(p_key) > 512 then
    return false;
  end if;
  v_key := md5(p_key);
  v_limit := greatest(1, least(coalesce(p_max, 60), 1000));
  perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(v_key, 0));
  select count(*)::integer into v_count from private.rate_limits
   where key = v_key and request_at >= v_now - interval '1 minute';
  if v_count >= v_limit then return false; end if;
  insert into private.rate_limits(key, request_at) values (v_key, v_now);
  return true;
end;
$$;
revoke all on function public.check_login_rate_limit(text, integer) from public, anon, authenticated;
grant execute on function public.check_login_rate_limit(text, integer) to service_role;
