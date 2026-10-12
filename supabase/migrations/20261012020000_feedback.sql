-- daily-work feedback: the table from 20261012000000_telemetry.sql, for a database where
-- public.events was created and public.feedback was not. Safe to run on a database that
-- already has it: nothing here changes an existing table or its rows.
-- The public (anon / publishable) key can insert and do nothing else. Only the service key reads.

create table if not exists public.feedback (
  id             bigint generated always as identity primary key,
  received_at    timestamptz not null default now(),
  ts             timestamptz not null,
  plugin_version text        not null check (plugin_version ~ '^\d+\.\d+\.\d+$'),
  install_id     uuid        not null,
  task_id        uuid,
  comment        text        not null check (char_length(comment) between 1 and 2000),
  content        text        not null check (char_length(content) between 1 and 30000)
);

alter table public.feedback enable row level security;

revoke all on public.feedback from anon, authenticated;

grant insert (ts, plugin_version, install_id, task_id, comment, content)
  on public.feedback to anon;

drop policy if exists "anon can insert feedback" on public.feedback;
create policy "anon can insert feedback" on public.feedback for insert to anon with check (true);

-- PGRST205 is the API's schema cache not knowing the table. Reload it.
notify pgrst, 'reload schema';
