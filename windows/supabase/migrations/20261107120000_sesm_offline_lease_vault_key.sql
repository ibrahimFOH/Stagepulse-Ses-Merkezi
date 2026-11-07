create or replace function public.sesm_offline_lease_private_key()
returns text
language sql
security definer
set search_path = ''
as $$
  select decrypted_secret
  from vault.decrypted_secrets
  where name = 'sesm_offline_lease_private_key_v1'
  limit 1;
$$;

revoke all on function public.sesm_offline_lease_private_key() from public, anon, authenticated;
grant execute on function public.sesm_offline_lease_private_key() to service_role;
