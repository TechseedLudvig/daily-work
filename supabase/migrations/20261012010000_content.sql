-- daily-work content logging: prompts and replies from brief, grill and record runs, from
-- people who have not set DAILY_WORK_CONTENT=0. A table of its own with ids of its own: no install id,
-- no telemetry task id, and times only to the hour, so rows cannot be matched to public.events.
-- The public (anon / publishable) key can insert and do nothing else. Rows live 30 days.

create table public.content (
  id              bigint generated always as identity primary key,
  received_at     timestamptz not null default date_trunc('hour', now()),
  kind            text        not null check (kind in ('run', 'outcome')),
  ts              timestamptz not null
                    check (date_trunc('hour', ts at time zone 'UTC') = ts at time zone 'UTC'),
  plugin_version  text        not null check (plugin_version ~ '^\d+\.\d+\.\d+$'),
  content_id      uuid        not null,
  -- kind = 'run': one skill run, every turn of it, and the paths written in the project folder
  skill           text        check (skill in ('brief', 'grill', 'record')),
  turns           jsonb       check (jsonb_typeof(turns) = 'array' and jsonb_array_length(turns) <= 200
                                     and octet_length(turns::text) <= 12000000),
  files           jsonb       check (jsonb_typeof(files) = 'array' and jsonb_array_length(files) <= 200
                                     and octet_length(files::text) <= 100000),
  -- kind = 'outcome': one row when record finishes
  outcome         text        check (outcome = 'completed'),
  rating          smallint    check (rating between 1 and 5),
  grill_completed boolean,
  constraint run_fields     check ((kind = 'run') = (skill is not null and turns is not null and files is not null)),
  constraint run_only       check (kind = 'run' or (skill is null and turns is null and files is null)),
  constraint outcome_fields check ((kind = 'outcome') = (outcome is not null and grill_completed is not null)),
  constraint outcome_only   check (kind = 'outcome' or (outcome is null and grill_completed is null and rating is null))
);

create index content_content_id  on public.content (content_id);
create index content_received_at on public.content (received_at);

alter table public.content enable row level security;

revoke all on public.content from anon, authenticated;

grant insert (kind, ts, plugin_version, content_id, skill, turns, files, outcome, rating, grill_completed)
  on public.content to anon;

create policy "anon can insert content" on public.content for insert to anon with check (true);

-- Delete rows older than 30 days, every night at 03:17 UTC.
create extension if not exists pg_cron;

select cron.schedule(
  'daily-work-content-30-days',
  '17 3 * * *',
  $$delete from public.content where received_at < now() - interval '30 days'$$
);
