---
name: init
description: >-
  /daily-work:init [dir]. Set up a daily-work repo: AGENTS.md, CLAUDE.md, README.md, .gitignore,
  .env.example, pyproject.toml, .claude/settings.json, tools/, and git init if needed. Never overwrites; an
  existing AGENTS.md gets only missing ## sections, an existing .gitignore or CLAUDE.md only missing lines.
  The session runs one script and edits nothing.
disable-model-invocation: true
argument-hint: "[dir]"
---

# Init

`<plugin>` in the commands below is the daily-work plugin folder: the folder two levels above
the one this SKILL.md is in. Write it as an absolute path. Run this skill only when the person
asks for it by name.

Run this one command from the repo root, with the arguments the person gave (usually none):

```
bash "<plugin>/scripts/init.sh" $ARGUMENTS
```

Print its output exactly as printed, one line per file, and end the turn on its last line.
Edit nothing yourself. Do not create CONTEXT.md or GLOSSARY.md. Never open or print .env.
