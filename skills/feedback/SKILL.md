---
name: feedback
description: >-
  /daily-work:feedback <task-name> <comment>. Send the plugin author one
  task file (or brief) with a comment. Shows exactly what will be sent and sends only
  after the person confirms. Nothing is ever sent without this command.
disable-model-invocation: true
argument-hint: "<task-name> <comment>"
---

# Feedback

Arguments: `$ARGUMENTS`

The first word is the task name (or the path of the task file or brief), the rest is the comment.
Run the script from the repo root. Never open or print .env.

1. Run, with the comment unchanged on the heredoc line:
   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/feedback.py" preview <task> <<'DAILY_WORK_COMMENT'
   <comment>
   DAILY_WORK_COMMENT
   ```
   On a line starting "refused:", print it and stop.
2. Print the script's output exactly as printed, in full, then ask: "Send this? (yes/no)".
   Wait for the answer. Change nothing in what is shown.
3. Only on a clear yes, run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/feedback.py" send` and
   print its output. On anything else, say "Nothing sent." and stop.
