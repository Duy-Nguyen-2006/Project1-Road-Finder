-- Road Finder: per-user saved scenarios and shipper presets
-- Requires 001_profiles.sql applied first

create table if not exists public.saved_scenarios (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  name text not null,
  payload jsonb not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint saved_scenarios_name_len check (char_length(name) between 1 and 120)
);

create index if not exists saved_scenarios_user_id_idx
  on public.saved_scenarios (user_id, updated_at desc);

create table if not exists public.shipper_presets (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  name text not null,
  latitude double precision not null,
  longitude double precision not null,
  created_at timestamptz not null default now(),
  constraint shipper_presets_name_len check (char_length(name) between 1 and 80),
  constraint shipper_presets_lat check (latitude between -90 and 90),
  constraint shipper_presets_lng check (longitude between -180 and 180)
);

create index if not exists shipper_presets_user_id_idx
  on public.shipper_presets (user_id, created_at desc);

alter table public.saved_scenarios enable row level security;
alter table public.shipper_presets enable row level security;

create policy "saved_scenarios_select_own"
  on public.saved_scenarios for select
  using (auth.uid() = user_id);

create policy "saved_scenarios_insert_own"
  on public.saved_scenarios for insert
  with check (auth.uid() = user_id);

create policy "saved_scenarios_update_own"
  on public.saved_scenarios for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy "saved_scenarios_delete_own"
  on public.saved_scenarios for delete
  using (auth.uid() = user_id);

create policy "shipper_presets_select_own"
  on public.shipper_presets for select
  using (auth.uid() = user_id);

create policy "shipper_presets_insert_own"
  on public.shipper_presets for insert
  with check (auth.uid() = user_id);

create policy "shipper_presets_update_own"
  on public.shipper_presets for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy "shipper_presets_delete_own"
  on public.shipper_presets for delete
  using (auth.uid() = user_id);