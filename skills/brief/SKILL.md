---
name: brief
description: >-
  /daily-work:brief [project] <describe the task>. Rewrite a person's description of a task into
  a clear brief, show it for the person to verify, then write it to
  <project>/briefs/<task-name>.md, ready for /mattpocock-skills:grill-with-docs, creating the project if new.
disable-model-invocation: true
argument-hint: "[project] <describe the task>"
---

# Brief

The user typed: `$ARGUMENTS`
If that line does not show the person's text, use what they wrote after the skill name.

`<plugin>` in the commands below is the daily-work plugin folder: the folder two levels above
the one this SKILL.md is in. Write it as an absolute path. Run this skill only when the person
asks for it by name.

1. **Project.** The projects are the folders at the repo root that hold a `tasks/` folder;
   list them. If the first word of the text is one of them, that is the project and the rest
   is the description. Otherwise ask the user which project, listing the existing ones and,
   when the first word is a valid name (`a-z`, `0-9`, `-`), offering it as a new project.
   Wait for the answer. Projects are lowercase, `a-z`, `0-9` and `-` only. If the description
   is empty, print `usage: /daily-work:brief [project] <describe the task>` and stop.
2. **Rewrite.** Turn the description into a brief that someone else could read cold:
   - one short paragraph: what is wanted, for whom, and why;
   - then, only for what the description says: `Input:`, `Output:`, `Constraints:` lines;
   - fix spelling and grammar, remove repetition, keep the person's terms (e.g. "UNS");
   - add nothing the description does not say, and do not settle anything it leaves open.
     Open points stay open; grilling settles them.
   If the description is about changing something the project already produced, list the
   project's `outputs/` and write the line `Output: update outputs/<file>` naming the
   existing file. If more than one file could be meant, write `Output: update an existing
   output (which one is open)` and list the candidates. Such a brief is a new task on an
   existing output; it never asks for a copy or a new file.
   Also write a **title** (a short heading, 3 to 8 words, sentence case) and a **task name** (2 to
   4 lowercase words joined by hyphens, only `a-z`, `0-9`, `-`, e.g. `uns-mockup`) that no
   file in the project's `briefs/` or `tasks/` already has.
3. **Verify.** Show the project, the title, the task name and the rewritten brief, and ask: "Write
   this brief, or what should change?" Wait for the answer. Revise and show it again until
   the person approves. Write nothing before that.
4. On approval, run this one command from the repo root. Put the title on the first
   heredoc line and the approved brief, unchanged, on the lines after it:

   ```
   bash "<plugin>/scripts/brief.sh" <project> <task-name> <<'DAILY_WORK_ARGS'
   <title>
   <approved brief>
   DAILY_WORK_ARGS
   ```
5. Print its output exactly as printed and end the turn on its last line. A refusal is one
   line starting "refused:"; print it and stop.

Edit nothing yourself and do not start the task. Do not create CONTEXT.md or GLOSSARY.md. Never open or
print .env.
