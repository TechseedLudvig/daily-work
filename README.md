# daily-work

A plugin for coding agents (Claude Code, GitHub Copilot CLI, OpenAI Codex) that gives a repo a
structure for ad-hoc white-collar work: reading decks,
evaluating documents, pulling and checking numbers, writing memos. Work is grouped in projects (an
engagement, a system, a recurring responsibility). A person describes a task in a brief; Matt Pocock's
`grill-with-docs` skill grills the brief into a task the agent can work on; the plugin records
what was done. Nothing here builds software.

It is built and tested in Claude Code, and this README uses Claude Code's commands. For the
other agents see [Other coding agents](#other-coding-agents).

Local filesystem and git, plus two kinds of network call to the plugin author: usage
telemetry and content logging. Both are on by default and each has its own off switch.
When `brief`, a grilling or `record` completes, the plugin sends the event name, a UTC
timestamp, the plugin version, a random install id, a random task id, and the grill outcome.
No personal or machine identifiers are sent. It is on by
default; set `DAILY_WORK_TELEMETRY=0` to send nothing. The telemetry code never reads
transcripts or task content. See [Telemetry](#telemetry). The plugin never opens `.env`.

Separately, the plugin sends the author what was typed and answered during brief, grill and
record runs. That is task content. It is on by default; set `DAILY_WORK_CONTENT=0` to send
none of it. See [Content logging](#content-logging).

## Setup

New to Claude Code, or on a computer without it? Start with
[GETTING-STARTED.md](GETTING-STARTED.md).

Everything below happens in your **work repo**, the repo where you do daily work, not in this
plugin's repo.

**1. Install the plugins** (once per machine, inside Claude Code):

```
/plugin marketplace add ludvignion/daily-work
/plugin install daily-work@daily-work
/plugin install mattpocock-skills
```

`mattpocock-skills` is Matt Pocock's skill set from
[mattpocock/skills](https://github.com/mattpocock/skills), in Claude Code's official
marketplace. daily-work uses its `grill-with-docs` skill (which calls his `grilling` and
`domain-modeling`) for the grilling step, as `/mattpocock-skills:grill-with-docs`. daily-work
does not ship or call it.

Both plugins update automatically. A planned change in Matt Pocock's skills renames
`CONTEXT.md` to `GLOSSARY.md`; it will arrive without warning, so the generated `AGENTS.md`
reads whichever of the two exists.

To update daily-work by hand: `/plugin marketplace update daily-work`, then restart Claude
Code. From a terminal, the same commands start with `claude plugin` instead of `/plugin`.

**2. Create the work repo and set it up** (once per work repo):

```
mkdir ~/workspace/<work repo> && cd ~/workspace/<work repo>
claude
/daily-work:init
```

To try a local checkout of daily-work instead of installing it:
`claude --plugin-dir /path/to/daily-work`.

## Other coding agents

The same repo installs in GitHub Copilot CLI and OpenAI Codex. Neither has been run by the
author yet; the install lines follow each tool's documentation.

| Agent | Install |
| --- | --- |
| Claude Code | `/plugin marketplace add ludvignion/daily-work`, then `/plugin install daily-work@daily-work` |
| GitHub Copilot CLI | `copilot plugin marketplace add ludvignion/daily-work`, then `copilot plugin install daily-work@daily-work` |
| OpenAI Codex | `codex plugin marketplace add ludvignion/daily-work`, then install daily-work from the Plugins Directory |

Matt Pocock's skills, needed for the grilling step, install in any agent with
`npx skills add mattpocock/skills`.

What differs outside Claude Code:

| | Claude Code | Copilot CLI, Codex |
| --- | --- | --- |
| The four skills (init, brief, record, feedback) | yes, as `/daily-work:<skill>` | yes, under the tool's own way of naming a skill |
| `AGENTS.md` in the work repo | read through `CLAUDE.md` | read directly |
| Telemetry events for brief and record | yes | yes |
| Telemetry event for a finished grilling | yes | no |
| Content logging of prompts and replies | yes | no; only the outcome row when record finishes |
| Switches in `.claude/settings.json` | yes | no; set `DAILY_WORK_TELEMETRY=0` or `DAILY_WORK_CONTENT=0` in your shell |

The last three rows depend on Claude Code's hooks (`claude-code/hooks.json`), which the other
agents do not load.

Not supported: installing the skills alone with `npx skills add ludvignion/daily-work`. That
copies each skill's folder without the plugin's `scripts/` and `templates/`, which the skills
need.

## The per-task loop

1. **Brief.** Describe the task in your own words:
   `/daily-work:brief hackathon I want to help my colleague visualise different options of a UNS structure …`
   Claude rewrites it into a clear brief (no additions, open points left open), with a
   heading and a file name, and asks for the project if you did not name an existing one.
   You approve or correct it; only then is `hackathon/briefs/uns-mockup.md` written, and the
   project folder with it if the project is new.
2. **Grill.** `/mattpocock-skills:grill-with-docs hackathon/briefs/uns-mockup.md` (Matt Pocock's
   skill). It interviews you until the task is clear, and records terms in `CONTEXT.md` and
   decisions in `docs/adr/`. When it ends, the generated AGENTS.md has Claude write
   `hackathon/tasks/uns-mockup.md` and delete the brief: the brief as the Ask, what was
   settled as the Spec.
3. **Work.** Tell Claude "work on uns-mockup". Client files go in the project's
   `inputs/`; what the task produces, code included, goes in the project's `outputs/`.
4. **Record.** `/daily-work:record uns-mockup` writes Result and
   Caveats, marks the task done in the project README, commits, and lists the Done lines a
   person still has to check.

You never have to type a path. `brief` prints the grill line to paste; after that the task
name is enough (`/mattpocock-skills:grill-with-docs uns-mockup` works too), and
`/daily-work:record` with no argument records the task if only one is open. Full paths are
accepted everywhere a name is.

**Changing an existing output** is a task like any other: brief it
(`/daily-work:brief hackathon update the prices in the pitch deck`), grill it, work, record.
`outputs/` belongs to the project, not to a task, so the new task edits
`hackathon/outputs/pitch-deck.pptx` in place; its brief names the file, and nothing is copied
or created beside it.

A repo set up by this plugin (the repo here is called `techseed`):

```
techseed/
  AGENTS.md                   how a coding agent works here
  CLAUDE.md                   one line, @AGENTS.md, so Claude Code reads the same file
  README.md                   ## Projects: one line per project
  tools/                      code used by two or more tasks
  hackathon/                  a project
    README.md                 ## Tasks: one line per task, open or done
    sources.md                where facts come from, and which source wins
    briefs/
      uns-mockup.md           not grilled yet: the verified description
    tasks/
      pitch-deck.md           grilled: heading, Ask, Spec, Result, Caveats
      pitch-deck-prices.md    a later task that changes the same deck
    inputs/                   client files, shared by the project's tasks (not committed)
    outputs/                  what the tasks produced, code included (committed)
      pitch-deck.pptx
```

A project is any folder at the repo root that holds a `tasks/` folder.

## Skills

All four are user-invoked only.

- **`/daily-work:init [dir]`** — creates `AGENTS.md`, `CLAUDE.md`, `README.md`, `.gitignore`,
  `.env.example`, `pyproject.toml`, `.claude/settings.json` and `tools/`, and runs `git init` if the
  directory is not in a repo. Prints `copied` or `skipped` per file. Never overwrites: an
  existing `AGENTS.md` gets only the template's missing `##` sections, an existing `CLAUDE.md`
  only the `@AGENTS.md` line if it lacks it, an existing `.gitignore` only its missing lines.
  Safe to re-run.
- **`/daily-work:brief [project] <describe the task>`** — rewrites the description into a brief,
  shows it for you to verify, and on approval writes `<project>/briefs/<task-name>.md`, adds
  `- <date> <task-name>: open` under `## Tasks` in the project README, and creates the project
  (`README.md`, `sources.md`, `tasks/`, `inputs/`, `outputs/`, its line under `## Projects`)
  if new. It refuses a project name that is already a folder of another kind, such as `tools`.
- **`/daily-work:record [task-name]`** — fills `## Result` and `## Caveats` from the
  project's `outputs/` and the conversation, adds any missing source to the project's
  `sources.md`, changes the README line to `- <date> <task-name>: done, <one line>`, commits
  `daily-work: record <task-name>`, and prints the Done lines left to check. The commit takes
  the task file, the project's `outputs/`, `README.md` and `sources.md`, the repo `README.md`
  and `tools/`. It refuses to commit if `## Ask` or `## Spec` changed. With no argument it
  records the only open task, or lists the open tasks if there are several. It asks you
  nothing.
- **`/daily-work:feedback <task-name> <comment>`** — sends the plugin author that task file
  (or its brief) and your comment. It prints exactly what will be sent and sends only after
  you answer yes. See [Telemetry](#telemetry).

A project's `inputs/` is gitignored so client files never enter git history; only its `.gitkeep` is
tracked. `pyproject.toml` lists pandas, openpyxl, python-pptx,
python-docx, pypdf and python-dotenv for `uv`; edit it to suit.

## What daily-work does and does not do with grill-with-docs

- It never calls, wraps or edits Matt Pocock's skills, and its own skills work without them.
- The generated `AGENTS.md` is what makes a grilling session end by turning the brief in
  `briefs/` into the task file in `tasks/`.
- It never creates or edits `CONTEXT.md`, `GLOSSARY.md`, `CONTEXT-MAP.md` or `docs/adr/`;
  those belong to `grill-with-docs`.

## Where the switches live

`/daily-work:init` creates `.claude/settings.json` in the work repo with both switches on:

```json
{
  "env": {
    "DAILY_WORK_TELEMETRY": "1",
    "DAILY_WORK_CONTENT": "1"
  }
}
```

Change a `"1"` to `"0"` to turn that one off, then restart Claude Code. Only `0` turns a
switch off; a missing line means on.

| File | Applies to |
| --- | --- |
| `<work repo>/.claude/settings.json` | everyone using this repo; committed |
| `<work repo>/.claude/settings.local.json` | you, in this repo only; not committed; wins over the file above |
| `~/.claude/settings.json` | you, in every repo |

If the repo already had a `.claude/settings.json`, init leaves it alone: add the `env` lines
yourself.

## Telemetry

The plugin author uses this to see whether the brief, grill, record loop gets used and where
it stalls. It is metadata only, it is opt-out, and no personal or machine identifiers are
sent.

**When.** One event when `/daily-work:brief` writes a brief, one when a grilling writes the
task file of a brief, and one when `/daily-work:record` commits.

**Sent in every event:**

| Field | What it is |
| --- | --- |
| `event` | `brief`, `grill` or `record` |
| `ts` | UTC time, to the second |
| `plugin_version` | from `plugin.json` |
| `install_id` | a random UUID, see below |
| `task_id` | a random UUID, see below; left out for tasks that have none |

Grill events add `outcome` (`completed`). Nothing else is sent.

**Never sent by telemetry:** your name, email, git identity, user name, host name or any other personal
or machine identifier, in clear text or hashed; prompts; file names; paths; project or task
names; task content (briefs, task files, inputs, outputs); transcripts; the repo name or
remote; environment variables; `.env`. The telemetry code does not read transcripts or task
content at all. The server sees your IP address, as any server does; the plugin does not
send it as a field and it is not stored with the events.

**The install id** is a random number (a version 4 UUID) made the first time an event is
sent. It is not derived from you, your account or your machine, and has no link to the
person; it only lets the author count installs and see whether they come back. It is stored
in `~/.config/daily-work/install-id`. To reset it, delete that file: the next event gets a
new random id with no tie to the old one.

**The task id** is another random UUID, written as the `Id:` line of the brief when
`/daily-work:brief` creates it, carried over to the task file by the grilling, and committed
with the task. It ties a task's brief, grill and record events together and says nothing
about the task. A task file without the line sends its events without a task id.

**First run.** The first command that would send an event prints a notice instead and sends
nothing. Events start with the run after that.

**Opt out.** In the work repo's `.claude/settings.json`, which `/daily-work:init` creates,
change `"DAILY_WORK_TELEMETRY": "1"` to `"0"` and restart Claude Code. See
[Where the switches live](#where-the-switches-live).

Nothing is sent, no notice is shown and no install id is made.

**Feedback is separate and opt-in.** `/daily-work:feedback <task-name> <comment>` sends
that one task file (or the brief if it is not grilled yet), your comment, and the
same `ts`, `plugin_version`, `install_id` and `task_id` as above. It prints the exact
payload first and sends only on a yes. It is stored in a table of its own, apart from the
events. Nothing is ever sent this way unless you run the command. With
`DAILY_WORK_TELEMETRY=0` it refuses.

**Where it goes.** A Supabase database in the EU. The plugin holds a public key that can
only add rows; it cannot read, change or delete anything.

**For the author.** `supabase/migrations/` creates the two tables and their insert-only
rules. `telemetry.json` holds the project URL and the anon (publishable) key; while either
is empty, nothing is sent. `SUPABASE_SERVICE_KEY=... python3 metrics/metrics.py --supabase`
turns stored events into weekly numbers; the service key is read from the environment and
never belongs in this repo. Tests: `python3 -m unittest discover tests`.

## Content logging

On by default. It sends the plugin author what you typed and what Claude answered during
skill runs, so that changes to the plugin can be tested against real runs. That is task
content, possibly client content: turn it off wherever you are not allowed to share it.

**Turn it off:** in the work repo's `.claude/settings.json`, change
`"DAILY_WORK_CONTENT": "1"` to `"0"` and restart Claude Code. See
[Where the switches live](#where-the-switches-live).

Only the value `0` turns it off. Nothing is sent, nothing is kept on disk, and no notice is
shown.

**First run.** The first `/daily-work:brief` or `/daily-work:record` prints a notice and
sends nothing; logging starts with the run after it, so you can turn it off in between.

**A run** is one `/daily-work:brief` (from the command until the brief is written),
one grilling of a brief (from `/mattpocock-skills:grill-with-docs <brief or task name>` until
its task file exists), or one `/daily-work:record` (from the command until the
commit). A command typed inside a sentence starts a run too. Work done between runs is not
logged. A run that never ends is never sent.

**Sent per run:**

| Field | What it is |
| --- | --- |
| `kind` | `run` |
| `skill` | `brief`, `grill` or `record` |
| `ts` | UTC time, rounded down to the hour |
| `plugin_version` | from `plugin.json` |
| `content_id` | a random UUID for the task, see below |
| `turns` | everything you typed and every final answer of Claude during the run, in order, starting with the command line; any single one over 50 KB is cut there and marked `truncated` |
| `files` | the files changed in the project folder during the run, as paths inside that folder (`outputs/report.xlsx`); never their contents, never the project name. The task's own file is listed as `task.md` or `brief.md` and other tasks' files are left out, so no task name is in the list |

What you type is sent as typed. A `/daily-work:record q3-numbers` line
therefore carries that task name, and Claude's answers may name files and quote task content.

**Sent once when record finishes:** `kind` `outcome`, `ts`, `plugin_version`, `content_id`,
`outcome` (`completed`), and `grill_completed`: whether a grill
run of this task was logged.

**Never sent:** file contents, the transcript, tool calls and their output, Claude's
intermediate messages within a turn, anything from outside a run, the install id, the
telemetry task id.

**The content id** is a random UUID in `tasks/.<task-name>.content-id` in the project folder,
made the first time a run of that task is logged. It is a different number from the task's
`Id:` line.

**Not linked to telemetry.** Content rows go to a table of their own. They carry no install
id and no telemetry task id, and their times are rounded to the hour, so a content row
cannot be matched to a telemetry event. The two switches are independent:
`DAILY_WORK_TELEMETRY=0` does not turn content logging off, and `DAILY_WORK_CONTENT=0` does
not turn telemetry off. To send nothing at all, set both.

**Where and how long.** The author's Supabase database in the EU, through the same
insert-only public key as telemetry. Rows are deleted 30 days after they arrive.

**On your machine.** While a run is open, its turns wait in
`~/.config/daily-work/content-runs/`; the file is deleted when the run is sent, when you
type another slash command, or after 12 hours. With content logging off, the hooks stop
before reading anything.

**For the author.** `supabase/migrations/20261012010000_content.sql` creates the table, its
insert-only rules and the nightly 30-day delete. `SUPABASE_SERVICE_KEY=... python3
metrics/export_content.py` writes `content.jsonl`, one line per content id with its runs and
outcome. That file holds task content; keep it out of every repo.
