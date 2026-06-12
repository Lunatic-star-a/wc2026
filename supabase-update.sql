-- ============================================================
-- FIFA World Cup 2026 — 增量更新（已有数据库，不删除数据）
-- ============================================================
-- 复制到 Supabase SQL Editor → 全选 → Run
-- 可重复运行，不会报错

-- 1. 添加比赛实时追踪字段
alter table public.matches add column if not exists match_minute integer;
alter table public.matches add column if not exists injury_time integer;

-- 2. 更新排行榜视图：分数优先，同分按用户名字母排序
create or replace view public.leaderboard as
select
  row_number() over (order by total_points desc, username asc) as rank,
  id as user_id,
  username,
  total_points as points,
  predictions_count
from public.profiles
order by total_points desc, username asc;

-- 3. 确保所有表启用 realtime 实时推送
do $$ begin
  alter publication supabase_realtime add table public.matches;
exception when duplicate_object then null; end $$;

do $$ begin
  alter publication supabase_realtime add table public.profiles;
exception when duplicate_object then null; end $$;

do $$ begin
  alter publication supabase_realtime add table public.predictions;
exception when duplicate_object then null; end $$;

do $$ begin
  alter publication supabase_realtime add table public.chat_messages;
exception when duplicate_object then null; end $$;
