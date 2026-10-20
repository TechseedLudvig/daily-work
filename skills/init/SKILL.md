---
name: init
description: >-
  /daily-work:init [dir]. Set up a daily-work repo: AGENTS.md, README.md, .gitignore, .env.example,
  pyproject.toml, .claude/settings.json, tools/, and git init if needed. Never overwrites; an existing
  AGENTS.md gets only missing ## sections, an existing .gitignore only missing lines, an existing
  CLAUDE.md only the @AGENTS.md line.
  The session runs one script and edits nothing.
  Only when the person asks for it by name; never on your own.
argument-hint: "[dir]"
---

# Init

`<plugin>` in the commands below is the daily-work plugin folder, the one that holds `scripts/`
and `skills/`; this file is `<plugin>/skills/init/SKILL.md`. Write it as an absolute path.
Run this skill only when the person's own message asks for it by name. Never start it yourself,
not even when the work looks finished; ask the person instead.

Run this one command from the repo root, with the arguments the person gave (usually none):

```
bash "<plugin>/scripts/init.sh" $ARGUMENTS
```

Print its output exactly as printed, one line per file, and end the turn on its last line.
Edit nothing yourself. Do not create CONTEXT.md or GLOSSARY.md. Never open or print .env.
