-- Schema complet ClipAI pour Supabase (PostgreSQL)
-- A executer dans Supabase > SQL Editor

create extension if not exists pgcrypto;

create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  email varchar(255) unique not null,
  password_hash varchar(255) not null,
  full_name varchar(255),
  avatar_url text,
  plan text not null default 'free' check (plan in ('free', 'pro', 'business')),
  videos_used_this_month integer not null default 0,
  stripe_customer_id varchar(255),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists videos (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  youtube_url text not null,
  youtube_id varchar(50),
  title varchar(500),
  duration_seconds integer,
  thumbnail_url text,
  status text not null default 'pending' check (status in ('pending','downloading','transcribing','detecting','cutting','formatting','uploading','done','error')),
  error_message text,
  progress_percent integer not null default 0,
  clips_count integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists clips (
  id uuid primary key default gen_random_uuid(),
  video_id uuid not null references videos(id) on delete cascade,
  user_id uuid not null references users(id) on delete cascade,
  title varchar(500),
  description text,
  start_time double precision not null,
  end_time double precision not null,
  duration_seconds double precision,
  file_url text,
  thumbnail_url text,
  file_size_bytes bigint,
  resolution varchar(20) not null default '1080x1920',
  format varchar(10) not null default 'mp4',
  download_count integer not null default 0,
  created_at timestamptz not null default now()
);

create table if not exists subscriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  stripe_subscription_id varchar(255) unique,
  stripe_price_id varchar(255),
  plan text check (plan in ('pro','business')),
  status text check (status in ('active','canceled','past_due','trialing','incomplete','unpaid')),
  current_period_start timestamptz,
  current_period_end timestamptz,
  cancel_at_period_end boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists usage_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  video_id uuid references videos(id) on delete set null,
  action_type text not null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_users_email on users(email);
create index if not exists idx_videos_user_id on videos(user_id);
create index if not exists idx_videos_status on videos(status);
create index if not exists idx_videos_created_at on videos(created_at desc);
create index if not exists idx_clips_video_id on clips(video_id);
create index if not exists idx_clips_user_id on clips(user_id);
create index if not exists idx_subscriptions_user_id on subscriptions(user_id);
create index if not exists idx_usage_logs_user_id on usage_logs(user_id);
create index if not exists idx_usage_logs_created_at on usage_logs(created_at desc);

create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_users_updated_at on users;
create trigger trg_users_updated_at
before update on users
for each row execute function set_updated_at();

drop trigger if exists trg_videos_updated_at on videos;
create trigger trg_videos_updated_at
before update on videos
for each row execute function set_updated_at();

drop trigger if exists trg_subscriptions_updated_at on subscriptions;
create trigger trg_subscriptions_updated_at
before update on subscriptions
for each row execute function set_updated_at();
