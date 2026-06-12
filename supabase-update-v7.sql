-- ============================================================
-- FIFA World Cup 2026 — v7 增量更新
-- 修复: 预测提交后 predictions_count 自动更新
-- 在 Supabase SQL Editor 中全选运行
-- ============================================================

-- 1. 当 predictions 表发生变化时，自动更新 profiles.predictions_count
create or replace function public.update_predictions_count()
returns trigger as $$
begin
  if TG_OP = 'INSERT' or TG_OP = 'UPDATE' then
    update public.profiles
    set predictions_count = (select count(*) from public.predictions where user_id = new.user_id)
    where id = new.user_id;
    return new;
  elsif TG_OP = 'DELETE' then
    update public.profiles
    set predictions_count = (select count(*) from public.predictions where user_id = old.user_id)
    where id = old.user_id;
    return old;
  end if;
  return null;
end;
$$ language plpgsql security definer;

-- 2. 创建触发器
drop trigger if exists trg_predictions_count on public.predictions;
create trigger trg_predictions_count
  after insert or update or delete on public.predictions
  for each row execute function public.update_predictions_count();

-- 3. 一次性修复: 同步所有现有用户的 predictions_count
update public.profiles p
set predictions_count = (select count(*) from public.predictions where user_id = p.id)
where predictions_count != (select count(*) from public.predictions where user_id = p.id);
