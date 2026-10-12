# <repo name>

## Purpose
<One paragraph, written by the owner: what this repo is for, who works in it, what kinds of
tasks land here.>

## Reading order
Before any task: the glossary if it exists (CONTEXT.md, or GLOSSARY.md), then the project's
README.md, sources.md and glossary if it has one, then the task file.

## Where things go
Work belongs to a project: <project>/ at the repo root, an engagement, a system or a
recurring responsibility. A project holds briefs/, tasks/, inputs/ and outputs/, side by
side. A task starts as briefs/<task-name>.md, a person's description of it; grilling turns it
into tasks/<task-name>.md. Client files go in the project's inputs/ and are never committed.
What the tasks produce, code included, goes in the project's outputs/ and is committed.

outputs/ belongs to the project, not to one task. A task that changes something already in
outputs/ edits that file in place: no copy, no new file beside it, no folder per task. Its
task file names the file it changes.

A method used twice becomes a skill in .claude/skills/. A script used once stays in the
project's outputs/; used twice, it moves to tools/.

## Naming a task
A task is named by its task name alone, e.g. "pitch-deck": that means
<project>/briefs/pitch-deck.md if it exists, otherwise <project>/tasks/pitch-deck.md, in
whichever project holds it. Find the file; never ask the person for a path. If two projects
hold the name, ask which project.

## Before answering
State in one line: which sources you will use, what each term in the ask means (the glossary
or "undefined"), the scope, and the form of the output. An undefined term or a missing source is
the question to ask; nothing else is.

## When to grill
Run /mattpocock-skills:grill-with-docs when the clarify line shows an undefined term or a missing source, or
when the ask is larger than one sitting. Otherwise the clarify line is enough.

## After a grilling session on a brief
Before ending, turn the brief <project>/briefs/<task-name>.md into a task:
1. Write <project>/tasks/<task-name>.md, same file name as the brief, in exactly this layout:

   # <the brief's heading>

   Project: <project>
   Created: <today>
   Id: <the brief's Id line, copied unchanged>

   ## Ask
   <the brief's text, unchanged, without its heading, Project, Written and Id lines>

   ## Spec
   Purpose: <one line: who this is for and what they do with it>
   Done looks like:
   - <a check a person can confirm in under a minute>
   Decided:
   - stated: <what the asker said>
   - assumed: <what Claude chose, and why>
   Out of scope:
   - <what this task does not do>

   ## Result
   <written by /daily-work:record>

   ## Caveats
   <written by /daily-work:record>

2. Fill ## Spec with what was settled. Leave ## Result and ## Caveats as shown.
3. Delete the brief.
4. Show the path of the task file.

## After a grilling session on a task
Write what was settled into that task's file under Spec: Done lines, Decided as stated or
assumed, Out of scope. Nothing settled in the session stays only in the session.

## Done
A Done line is something a person can confirm in under a minute. A number reconciles to a
named figure. A memo answers the questions in the Ask. A review points at the slide or line
for every finding.

## Finishing
Run /daily-work:record <task-name>. It writes Result and Caveats, updates the project
index, and names the Done lines left for a person to check.
