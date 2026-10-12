-- daily-work telemetry: usage events and opt-in feedback, in two separate tables.
-- The plugin inserts with the public (anon / publishable) key. That key can insert rows and
-- do nothing else: no select, update or delete. Only the service (secret) key reads.

create table public.events (
  id             bigint generated always as identity primary key,
  received_at    timestamptz not null default now(),
  event          text        not null check (event in ('brief', 'grill', 'record')),
  ts             timestamptz not null,
  plugin_version text        not null check (plugin_version ~ '^\d+\.\d+\.\d+$'),
  install_id     uuid        not null,
  task_id        uuid,
  outcome        text        check (outcome in ('completed', 'skipped', 'aborted')),
  rating         smallint    check (rating between 1 and 5),
  constraint outcome_on_grill_only check ((event = 'grill') = (outcome is not null)),
  constraint rating_on_record_only check (rating is null or event = 'record'),
  constraint brief_has_task_id     check (event <> 'brief' or task_id is not null)
);

create table public.feedback (
  id             bigint generated always as identity primary key,
  received_at    timestamptz not null default now(),
  ts             timestamptz not null,
  plugin_version text        not null check (plugin_version ~ '^\d+\.\d+\.\d+$'),
  install_id     uuid        not null,
  task_id        uuid,
  comment        text        not null check (char_length(comment) between 1 and 2000),
  content        text        not null check (char_length(content) between 1 and 30000)
);

create index events_ts on public.events (ts);

alter table public.events   enable row level security;
alter table public.feedback enable row level security;

-- Supabase grants anon and authenticated everything on new public tables. Take it all back,
-- then allow insert only, and only into the columns the plugin sends.
revoke all on public.events, public.feedback from anon, authenticated;

grant insert (event, ts, plugin_version, install_id, task_id, outcome, rating)
  on public.events to anon;
grant insert (ts, plugin_version, install_id, task_id, comment, content)
  on public.feedback to anon;

create policy "anon can insert events"   on public.events   for insert to anon with check (true);
create policy "anon can insert feedback" on public.feedback for insert to anon with check (true);
