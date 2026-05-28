-- ============================================================
-- FIFA World Cup 2026 - Prediction Platform
-- Supabase Database Migration
-- ============================================================
-- Run this in Supabase SQL Editor:
-- https://app.supabase.com → Your Project → SQL Editor → New Query
-- Paste and run.

-- ── Extensions ──
create extension if not exists "pgcrypto";

-- ── Profiles (extends auth.users) ──
create table if not exists public.profiles (
  id          uuid primary key references auth.users(id) on delete cascade,
  username    text not null unique,
  display_name text,
  total_points integer default 0 not null,
  predictions_count integer default 0 not null,
  created_at  timestamptz default now() not null,
  updated_at  timestamptz default now() not null
);

-- ── Matches ──
create table if not exists public.matches (
  id          bigint primary key generated always as identity,
  match_date  date not null,
  match_time  text not null,               -- e.g. '16:00'
  home_team   text not null,
  away_team   text not null,
  stage       text not null,               -- 'group','r32','r16','qf','sf','3rd','final'
  group_name  text,                        -- 'A'..'L' for group stage
  venue       text not null,
  home_score  integer,                     -- null until match is played
  away_score  integer,                     -- null until match is played
  status      text default 'upcoming' not null, -- 'upcoming','live','finished'
  created_at  timestamptz default now() not null,
  updated_at  timestamptz default now() not null
);

-- ── Predictions ──
create table if not exists public.predictions (
  id          bigint primary key generated always as identity,
  user_id     uuid not null references public.profiles(id) on delete cascade,
  match_id    bigint not null references public.matches(id) on delete cascade,
  home_score  integer not null,
  away_score  integer not null,
  points      integer default 0 not null,  -- calculated after match
  created_at  timestamptz default now() not null,
  unique(user_id, match_id)               -- one prediction per user per match
);

-- ── Indexes ──
create index if not exists idx_predictions_user    on public.predictions(user_id);
create index if not exists idx_predictions_match   on public.predictions(match_id);
create index if not exists idx_predictions_points  on public.predictions(points desc);
create index if not exists idx_matches_status      on public.matches(status);
create index if not exists idx_matches_date        on public.matches(match_date);
create index if not exists idx_profiles_points     on public.profiles(total_points desc);

-- ── Auto-update updated_at ──
create or replace function public.update_timestamp()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql security definer;

create trigger trg_profiles_updated
  before update on public.profiles
  for each row execute function public.update_timestamp();

create trigger trg_matches_updated
  before update on public.matches
  for each row execute function public.update_timestamp();

-- ── Score Calculation Function ──
-- Called when match scores are updated. Calculates points for all predictions.
create or replace function public.calculate_prediction_points(match_id bigint)
returns void as $$
declare
  m public.matches;
  pred record;
  earned integer;
begin
  select * into m from public.matches where id = match_id;
  if m is null or m.home_score is null or m.away_score is null then
    return;
  end if;

  for pred in
    select * from public.predictions where match_id = match_id
  loop
    earned := 0;

    -- Exact score: 3 points
    if pred.home_score = m.home_score and pred.away_score = m.away_score then
      earned := 3;
    -- Correct result (win/draw/loss): 1 point
    elsif sign(pred.home_score - pred.away_score) = sign(m.home_score - m.away_score) then
      earned := 1;
    -- Both scoreless draw
    elsif pred.home_score = pred.away_score and m.home_score = m.away_score then
      earned := 1;
    end if;

    update public.predictions set points = earned where id = pred.id;

    -- Update user total
    update public.profiles
    set total_points = (
      select coalesce(sum(points), 0) from public.predictions where user_id = pred.user_id
    ),
    predictions_count = (
      select count(*) from public.predictions where user_id = pred.user_id
    )
    where id = pred.user_id;
  end loop;
end;
$$ language plpgsql security definer;

-- ── Leaderboard View ──
create or replace view public.leaderboard as
select
  row_number() over (order by total_points desc, predictions_count desc) as rank,
  id as user_id,
  username,
  total_points as points,
  predictions_count
from public.profiles
where total_points > 0 or predictions_count > 0
order by total_points desc, predictions_count desc;

-- ── Row Level Security (RLS) ──
alter table public.profiles enable row level security;
alter table public.matches enable row level security;
alter table public.predictions enable row level security;

-- Profiles: users can read all, only update their own
create policy "Profiles are viewable by everyone"
  on public.profiles for select using (true);

create policy "Users can update own profile"
  on public.profiles for update using (auth.uid() = id);

create policy "Users can insert own profile"
  on public.profiles for insert with check (auth.uid() = id);

-- Matches: everyone can read, only service_role can modify
create policy "Matches are viewable by everyone"
  on public.matches for select using (true);

create policy "Only service_role can insert matches"
  on public.matches for insert with check (true);

create policy "Only service_role can update matches"
  on public.matches for update using (true);

-- Predictions: users can CRUD their own
create policy "Users can view own predictions"
  on public.predictions for select using (auth.uid() = user_id);

create policy "Users can insert own predictions"
  on public.predictions for insert with check (auth.uid() = user_id);

create policy "Users can update own predictions"
  on public.predictions for update using (auth.uid() = user_id);

create policy "Users can delete own predictions"
  on public.predictions for delete using (auth.uid() = user_id);

-- ── Insert trigger for profiles (auto-create on signup) ──
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, username, display_name)
  values (
    new.id,
    coalesce(new.raw_user_meta_data ->> 'username', 'user_' || substring(new.id::text, 1, 8)),
    coalesce(new.raw_user_meta_data ->> 'username', 'user_' || substring(new.id::text, 1, 8))
  );
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
