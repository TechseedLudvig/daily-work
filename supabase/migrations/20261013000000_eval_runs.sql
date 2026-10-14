-- daily-work offline eval: one summary row per run, scenario and step (evals/README.md).
-- Simulated data only, kept apart from events, content and feedback. Written and read with
-- the service (secret) key; the public (anon / publishable) key can do nothing here.
-- Safe to run more than once.

create table if not exists public.eval_runs (
  id             bigint generated always as identity primary key,
  received_at    timestamptz not null default now(),
  run_id         text        not null,
  run_date       date        not null,
  plugin_version text        not null check (plugin_version ~ '^\d+\.\d+\.\d+$'),
  grill          text        not null,
  model          text        not null,
  scenario       text        not null,
  step           text        not null check (step in ('brief', 'grill', 'work', 'record', 'end_to_end')),
  -- {metric: {mean, min, max, sd, n}} over the runs of that scenario; scenario 'ALL' is the mean over scenarios
  metrics        jsonb       not null check (jsonb_typeof(metrics) = 'object'),
  unique (run_id, grill, scenario, step)
);

create index if not exists eval_runs_run_date on public.eval_runs (run_date);

alter table public.eval_runs enable row level security;

revoke all on public.eval_runs from anon, authenticated;
-- A run pushed again replaces its rows, which takes insert and update.
grant select, insert, update, delete on public.eval_runs to service_role;

notify pgrst, 'reload schema';
