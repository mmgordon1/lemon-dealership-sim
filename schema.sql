-- Run in Supabase SQL Editor. Do not put any service-role keys in GitHub.
create table if not exists public.sim_settings (
  id integer primary key default 1 check (id = 1),
  stage integer not null default 1 check (stage between 1 and 9),
  mode text not null default 'instructor' check (mode in ('instructor','self-paced')),
  updated_at timestamptz not null default now()
);
insert into public.sim_settings (id) values (1) on conflict (id) do nothing;
create table if not exists public.teams (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  pin_hash text not null,
  created_at timestamptz not null default now()
);
create table if not exists public.decisions (
  id bigint generated always as identity primary key,
  team_id uuid not null references public.teams(id) on delete cascade,
  round integer not null check (round between 1 and 7),
  reliable integer not null check (reliable >= 0),
  disclosed integer not null check (disclosed >= 0),
  undisclosed integer not null check (undisclosed >= 0),
  customers integer not null,
  cost integer not null,
  operating_profit integer not null,
  inspected boolean,
  fine integer not null default 0,
  created_at timestamptz not null default now(),
  unique (team_id, round)
);
create table if not exists public.relocations (
  team_id uuid primary key references public.teams(id) on delete cascade,
  relocate boolean not null,
  created_at timestamptz not null default now()
);
-- No direct browser database access. Only the server uses the service-role key.
alter table public.sim_settings enable row level security;
alter table public.teams enable row level security;
alter table public.decisions enable row level security;
alter table public.relocations enable row level security;
