-- Nabeh SafeLink custom authentication schema.
-- Run this once in Supabase SQL Editor before deploying the custom-auth code.
-- Supabase remains the database provider; Supabase Auth is not used.

create extension if not exists pgcrypto;

create table if not exists public.custom_users (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  display_name text not null,
  password_hash text not null,
  email_verified boolean not null default false,
  preferred_language text not null default 'ar',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.custom_auth_otps (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  email text not null,
  purpose text not null check (purpose in ('signup', 'recovery')),
  code_hash text not null,
  attempts integer not null default 0 check (attempts >= 0),
  expires_at timestamptz not null,
  consumed_at timestamptz null,
  created_at timestamptz not null default now()
);

create index if not exists custom_users_email_idx on public.custom_users (lower(email));
create index if not exists custom_auth_otps_lookup_idx
  on public.custom_auth_otps (user_id, purpose, created_at desc)
  where consumed_at is null;

-- The backend uses the service key and enforces ownership from its JWT.
-- Existing projects may have foreign keys from these tables to auth.users.
-- Remove those Auth-only constraints because custom_users owns identity now.
do $$
declare
  constraint_row record;
begin
  for constraint_row in
    select conrelid::regclass as table_name, conname
    from pg_constraint
    where contype = 'f'
      and confrelid = 'auth.users'::regclass
      and conrelid in ('public.user_profiles'::regclass, 'public.scans'::regclass)
  loop
    execute format('alter table %s drop constraint if exists %I', constraint_row.table_name, constraint_row.conname);
  end loop;
end $$;

-- Existing rows created with Supabase Auth are intentionally not auto-mapped:
-- passwords cannot be extracted from auth.users. Users must register again or
-- use an administrator-led migration process outside this application.
