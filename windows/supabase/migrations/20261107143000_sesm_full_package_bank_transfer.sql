create table if not exists public.sesm_store_settings (
  id boolean primary key default true check (id = true),
  product_code text not null default 'full_package' check (product_code = 'full_package'),
  product_name text not null default 'FULL PAKET' check (product_name = 'FULL PAKET'),
  price numeric(10,2) not null default 2500.00 check (price >= 0 and price <= 2500.00),
  currency text not null default 'TRY' check (currency = 'TRY'),
  bank_name text not null default '',
  account_holder text not null default '',
  iban text not null default '',
  payment_instructions text not null default '',
  contact_phone text not null default '',
  updated_at timestamptz not null default now(),
  updated_by uuid references auth.users(id) on delete set null
);

insert into public.sesm_store_settings (id) values (true) on conflict (id) do nothing;

alter table public.sesm_license_keys
  drop constraint if exists sesm_license_keys_plan_code_check;
alter table public.sesm_license_keys
  add constraint sesm_license_keys_plan_code_check check (plan_code = 'student');
alter table public.sesm_license_keys
  drop constraint if exists sesm_license_keys_bundle_code_check;
alter table public.sesm_license_keys
  add constraint sesm_license_keys_bundle_code_check check (bundle_code = 'full_master');

alter table public.sesm_license_keys
  drop constraint if exists sesm_license_keys_payment_method_check;
alter table public.sesm_license_keys
  add constraint sesm_license_keys_payment_method_check
  check (payment_method in ('cash','bank_transfer','legacy'));
alter table public.sesm_license_keys
  drop constraint if exists sesm_license_keys_amount_check;
alter table public.sesm_license_keys
  add constraint sesm_license_keys_amount_check check (amount >= 0 and amount <= 2500);
alter table public.sesm_license_keys
  drop constraint if exists sesm_license_keys_currency_check;
alter table public.sesm_license_keys
  add constraint sesm_license_keys_currency_check check (currency = 'TRY');

create table if not exists public.sesm_purchase_requests (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete restrict,
  product_code text not null default 'full_package' check (product_code = 'full_package'),
  product_name text not null default 'FULL PAKET' check (product_name = 'FULL PAKET'),
  amount numeric(10,2) not null check (amount >= 0 and amount <= 2500.00),
  currency text not null default 'TRY' check (currency = 'TRY'),
  customer_name text not null check (length(trim(customer_name)) between 2 and 120),
  customer_email text not null check (length(trim(customer_email)) between 5 and 320),
  customer_phone text not null default '',
  transfer_reference text not null check (length(trim(transfer_reference)) between 3 and 120),
  customer_note text not null default '',
  status text not null default 'pending' check (status in ('pending','approved','rejected')),
  admin_note text not null default '',
  reviewed_by uuid references auth.users(id) on delete set null,
  reviewed_at timestamptz,
  license_id uuid references public.sesm_license_keys(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint sesm_purchase_review_consistency check (
    (status = 'pending' and reviewed_at is null)
    or (status in ('approved','rejected') and reviewed_at is not null)
  )
);

create index if not exists sesm_purchase_requests_user_created_idx
  on public.sesm_purchase_requests (user_id, created_at desc);
create index if not exists sesm_purchase_requests_status_created_idx
  on public.sesm_purchase_requests (status, created_at desc);
create unique index if not exists sesm_purchase_requests_one_pending_per_user_idx
  on public.sesm_purchase_requests (user_id) where status = 'pending';

alter table public.sesm_store_settings enable row level security;
alter table public.sesm_purchase_requests enable row level security;
revoke all on public.sesm_store_settings from anon, authenticated;
revoke all on public.sesm_purchase_requests from anon, authenticated;

create or replace function public.sesm_review_full_package_purchase(
  p_purchase_id uuid, p_owner_user_id uuid, p_key_hash text
) returns jsonb
language plpgsql security definer set search_path = ''
as $$
declare
  v_request public.sesm_purchase_requests%rowtype;
  v_license public.sesm_license_keys%rowtype;
  v_core_id uuid;
begin
  if p_purchase_id is null or p_owner_user_id is null or p_key_hash is null or p_key_hash !~ '^[0-9a-f]{64}$' then
    raise exception using errcode='22023', message='PURCHASE_REVIEW_INPUT_INVALID';
  end if;
  select * into v_request from public.sesm_purchase_requests where id=p_purchase_id for update;
  if not found then raise exception using errcode='P0002', message='PURCHASE_NOT_FOUND'; end if;
  if v_request.status <> 'pending' then raise exception using errcode='P0001', message='PURCHASE_ALREADY_REVIEWED'; end if;
  insert into public.sesm_license_keys (
    key_hash,label,plan_code,bundle_code,max_activations,expires_at,created_by,notes,
    customer_name,customer_email,payment_method,payment_status,amount,currency,payment_reference
  ) values (
    p_key_hash,'FULL PAKET','student','full_master',3,null,p_owner_user_id,
    'Havale/EFT ile satın alındı; yönetici onaylı.',v_request.customer_name,
    v_request.customer_email,'bank_transfer','paid',v_request.amount,'TRY',v_request.transfer_reference
  ) returning * into v_license;
  insert into public.license_core (
    product_code,key_hash,key_normalization,legacy_system,legacy_license_id,owner_user_id,
    customer_name,status,plan_code,bundle_code,max_devices,expires_at,payment_status,metadata
  ) values (
    'ses-merkezi',p_key_hash,'alnum_upper','ses-merkezi',v_license.id,p_owner_user_id,
    v_request.customer_name,'active','full_package','full_master',3,null,'paid',
    jsonb_build_object('purchase_request_id',v_request.id,'payment_method','bank_transfer','amount',v_request.amount,'currency','TRY')
  ) returning id into v_core_id;
  update public.sesm_purchase_requests set status='approved',reviewed_by=p_owner_user_id,
    reviewed_at=pg_catalog.now(),license_id=v_license.id,updated_at=pg_catalog.now() where id=v_request.id;
  insert into public.sesm_audit_events(actor_user_id,action,subject_user_id,license_id,details)
  values (p_owner_user_id,'full_package_purchase_approved',v_request.user_id,v_license.id,
    jsonb_build_object('purchase_request_id',v_request.id,'amount',v_request.amount,'currency','TRY'));
  return jsonb_build_object('purchase_id',v_request.id,'license_id',v_license.id,'license_core_id',v_core_id);
end;
$$;

revoke all on function public.sesm_review_full_package_purchase(uuid,uuid,text) from public, anon, authenticated;
grant execute on function public.sesm_review_full_package_purchase(uuid,uuid,text) to service_role;
