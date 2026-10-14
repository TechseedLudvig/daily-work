-- daily-work offline eval: let the public (anon / publishable) key insert into eval_runs, as it
-- can into events, content and feedback, so a run stores itself without the secret key.
-- The public key can insert and do nothing else; it cannot read, change or delete a row, so a
-- run that is already stored is refused (the unique key), not replaced. Only the service key reads.
-- Safe to run more than once.

-- Bounds on what an insert may carry, since anyone with the public key can send one.
alter table public.eval_runs drop constraint if exists eval_runs_sizes;
alter table public.eval_runs add constraint eval_runs_sizes check (
  char_length(run_id) <= 64 and char_length(grill) <= 64 and char_length(model) <= 64
  and char_length(scenario) <= 100 and pg_column_size(metrics) <= 20000
);

grant insert (run_id, run_date, plugin_version, grill, model, scenario, step, metrics)
  on public.eval_runs to anon;

drop policy if exists "anon can insert eval_runs" on public.eval_runs;
create policy "anon can insert eval_runs" on public.eval_runs for insert to anon with check (true);

notify pgrst, 'reload schema';
