---
name: record
description: >-
  /daily-work:record [task-name]. Record a finished task: write
  ## Result and ## Caveats in its task file from the project's outputs/ and the conversation,
  add missing sources to the project's sources.md, mark the project README line done, commit,
  and list the Done lines a person still has to check. Shows the draft and asks once before
  writing anything. With no argument, record the only open
  task, or list the open tasks.
  Only when the person asks for it by name; never on your own.
argument-hint: "[task-name]"
---

# Record

Arguments: `$ARGUMENTS`
If that line does not show the person's text, use what they wrote after the skill name.

`<plugin>` in the commands below is the daily-work plugin folder, the one that holds `scripts/`
and `skills/`; this file is `<plugin>/skills/record/SKILL.md`. Write it as an absolute path.
Run this skill only when the person's own message asks for it by name. Never start it yourself,
not even when the work looks finished; ask the person instead.

Ask the person one question only: the "Record this?" in step 3. Nothing is written before
the answer.

Never open or print .env. Never create CONTEXT.md or GLOSSARY.md. Never edit `## Ask` or `## Spec`.

## No argument

Run `bash "<plugin>/scripts/record.sh" list`. If it prints exactly one line and
that line is a path under `tasks/`, that is the task: continue below with it. Otherwise print
its output and stop.

## With a task

The task is a task name (`pitch-deck`) or a task file (`hackathon/tasks/pitch-deck.md`); pass
it to the script as given. `begin` prints the task file on its `task:` line.

1. Run `bash "<plugin>/scripts/record.sh" begin <task>`. On a line
   starting "refused:", print it and stop. Otherwise it names the task file, sources.md and
   the files in the project's outputs/ changed since the last commit.
2. Read the task file, the project's sources.md, and every file listed under outputs. The
   project's outputs/ is shared by all its tasks: the listed files are the ones this task
   made or changed. If none are listed, take the files from the conversation. Use the
   conversation for what was done and why.
3. Draft, without writing anything yet, the Result and Caveats bodies (below), the sources
   from step 4 and the one line from step 5. Print them under the headings `Result`,
   `Caveats`, `New sources` and `Line`, then ask: "Record this? (yes/no)". Wait for the
   answer. On yes or go ahead, continue with the draft. On a change, redo the draft with it
   and ask again. On no, or anything else, write nothing and stop.
   Then edit the task file, replacing only the body under `## Result` and under `## Caveats`:
   - Result: what was produced or changed and where (paths under outputs/; for a file that
     already existed, what changed in it), and the answer itself: the numbers, findings or
     recommendation, each tied to its source, slide or line.
   - Caveats: what was assumed, what could not be checked, which figures do not reconcile,
     which sources were missing or stale. Write "None." only if that is true.
   Only state what outputs/ or the conversation shows.
4. For each source the task used (a file, system, report or person) that is not already in
   sources.md, add one bullet in its format: `- <source>: <what it is, where it lives, what it
   is authoritative for>.` Change no existing bullet.
5. Run, with one line (under 80 characters) saying what the task produced:
   ```
   bash "<plugin>/scripts/record.sh" finish <task> <<'DAILY_WORK_LINE'
   <one line>
   DAILY_WORK_LINE
   ```
   It refuses if `## Ask` or `## Spec` changed or a placeholder remains; fix your edit and
   rerun finish. Otherwise it marks the README line done, commits "daily-work: record
   <task-name>", and prints the Done lines.
6. End on the script's output: the Done lines left for a person to check. If they still read
   `<a check a person can confirm in under a minute>`, say the Spec has no Done lines yet.
