# daily-work

A Claude Code plugin that gives a repo a structure for ad-hoc white-collar work: reading decks,
evaluating documents, pulling and checking numbers, writing memos. Work is grouped in areas (a
client, a system, a recurring responsibility). A person describes a task in a brief; Matt Pocock's
`grill-with-docs` skill grills the brief into a task Claude can work on; the plugin records
what was done. Nothing here builds software.

Local filesystem and git, plus one kind of network call: usage telemetry to the plugin author.
When `brief`, a grilling or `record` completes, the plugin sends the event name, a UTC
timestamp, the plugin version, a random install id, a random task id, the grill outcome, and
your 1 to 5 rating if you give one. No personal or machine identifiers are sent. It is on by
default; set `DAILY_WORK_TELEMETRY=0` to send nothing. The telemetry code never reads
transcripts or task content. See [Telemetry](#telemetry). The plugin never opens `.env`.

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
`CONTEXT.md` to `GLOSSARY.md`; it will arrive without warning, so the generated `CLAUDE.md`
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

## The per-task loop

1. **Brief.** Describe the task in your own words:
   `/daily-work:brief techseed I want to help my colleague visualise different options of a UNS structure …`
   Claude rewrites it into a clear brief (no additions, open points left open), with a
   heading and a file name, and asks for the area if you did not name an existing one. You
   approve or correct it; only then is the task folder `areas/techseed/tasks/uns-mockup/`
   created, holding `brief.md`, `inputs/` and `outputs/`.
2. **Grill.** `/mattpocock-skills:grill-with-docs areas/techseed/tasks/uns-mockup/brief.md` (Matt Pocock's
   skill). It interviews you until the task is clear, and records terms in `CONTEXT.md` and
   decisions in `docs/adr/`. When it ends, the generated CLAUDE.md has Claude replace
   `brief.md` with `task.md` in the same folder: the brief as the Ask, what was settled as
   the Spec.
3. **Work.** Tell Claude to work on the task folder. Client files go in `inputs/`; what the
   task produces, code included, goes in `outputs/`.
4. **Record.** `/daily-work:record areas/techseed/tasks/uns-mockup` writes Result and
   Caveats, marks the task done in the area README, commits, and lists the Done lines a
   person still has to check.

A repo set up by this plugin:

```
CLAUDE.md                     how Claude works here
README.md                     ## Areas: one line per area
areas/
  techseed/
    README.md                 ## Tasks: one line per task, open or done
    sources.md                where facts come from, and which source wins
    tasks/
      uns-mockup/             not grilled yet
        brief.md              the verified description
        .task-id              a random id for usage telemetry
        inputs/  outputs/
      q3-numbers/             grilled
        task.md               heading, Ask, Spec, Result, Caveats
        inputs/               client files (not committed)
        outputs/              what was produced, code included (committed)
tools/                        code used by two or more tasks
```

## Skills

All four are user-invoked only.

- **`/daily-work:init [dir]`** — creates `CLAUDE.md`, `README.md`, `.gitignore`,
  `.env.example`, `pyproject.toml`, `areas/` and `tools/`, and runs `git init` if the
  directory is not in a repo. Prints `copied` or `skipped` per file. Never overwrites: an
  existing `CLAUDE.md` gets only the template's missing `##` sections, an existing
  `.gitignore` only its missing lines. Safe to re-run.
- **`/daily-work:brief [area] <describe the task>`** — rewrites the description into a brief,
  shows it for you to verify, and on approval creates `areas/<area>/tasks/<task-name>/` with
  `brief.md`, `inputs/` and `outputs/`, adds `- <date> <task-name>: open` under `## Tasks` in the
  area README, and creates the area (`README.md`, `sources.md`, its line under `## Areas`) if
  new.
- **`/daily-work:record [task folder]`** — fills `## Result` and `## Caveats` from `outputs/`
  and the conversation, adds any missing source to the area's `sources.md`, changes the README
  line to `- <date> <task-name>: done, <one line>`, commits `daily-work: record <task-name>`, and prints
  the Done lines left to check. It refuses to commit if `## Ask` or `## Spec` changed. With no
  argument it lists open tasks. With telemetry on, it first asks "Was this useful?" (1 to 5,
  anything else skips).
- **`/daily-work:feedback <task folder> <comment>`** — sends the plugin author that task's
  `task.md` (or `brief.md`) and your comment. It prints exactly what will be sent and sends
  only after you answer yes. See [Telemetry](#telemetry).

`inputs/` is gitignored so client files never enter git history; only its `.gitkeep` is
tracked. `pyproject.toml` lists pandas, openpyxl, python-pptx,
python-docx, pypdf and python-dotenv for `uv`; edit it to suit.

## What daily-work does and does not do with grill-with-docs

- It never calls, wraps or edits Matt Pocock's skills, and its own skills work without them.
- The generated `CLAUDE.md` is what makes a grilling session end by turning `brief.md` into
  `task.md`.
- It never creates or edits `CONTEXT.md`, `GLOSSARY.md`, `CONTEXT-MAP.md` or `docs/adr/`;
  those belong to `grill-with-docs`.

## Telemetry

The plugin author uses this to see whether the brief, grill, record loop gets used and where
it stalls. It is metadata only, it is opt-out, and no personal or machine identifiers are
sent.

**When.** One event when `/daily-work:brief` creates a task folder, one when a grilling
writes `task.md` next to a `brief.md`, and one when `/daily-work:record` commits.

**Sent in every event:**

| Field | What it is |
| --- | --- |
| `event` | `brief`, `grill` or `record` |
| `ts` | UTC time, to the second |
| `plugin_version` | from `plugin.json` |
| `install_id` | a random UUID, see below |
| `task_id` | a random UUID, see below; left out for tasks that have none |

Grill events add `outcome` (`completed`). Record events add `rating`, 1 to 5, only if you
gave one. Nothing else is sent.

**Never sent:** your name, email, git identity, user name, host name or any other personal
or machine identifier, in clear text or hashed; prompts; file names; paths; area or task
names; task content (briefs, task.md, inputs, outputs); transcripts; the repo name or
remote; environment variables; `.env`. The telemetry code does not read transcripts or task
content at all. The server sees your IP address, as any server does; the plugin does not
send it as a field and it is not stored with the events.

**The install id** is a random number (a version 4 UUID) made the first time an event is
sent. It is not derived from you, your account or your machine, and has no link to the
person; it only lets the author count installs and see whether they come back. It is stored
in `~/.config/daily-work/install-id`. To reset it, delete that file: the next event gets a
new random id with no tie to the old one.

**The task id** is another random UUID, written to `.task-id` in the task folder when
`/daily-work:brief` creates it, and committed with the task. It ties a task's brief, grill
and record events together and says nothing about the task. A task folder without the file
(made before version 0.6.0) sends its events without a task id.

**First run.** The first command that would send an event prints a notice instead and sends
nothing. Events start with the run after that.

**Opt out.** Set `DAILY_WORK_TELEMETRY=0` in your environment, for example in
`~/.claude/settings.json`:

```json
{ "env": { "DAILY_WORK_TELEMETRY": "0" } }
```

Nothing is sent, no notice is shown, no install id is made, and `/daily-work:record` does
not ask for a rating.

**Feedback is separate and opt-in.** `/daily-work:feedback <task folder> <comment>` sends
that one task's `task.md` (or `brief.md` if it is not grilled yet), your comment, and the
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
