#!/usr/bin/env python3
"""Opt-in feedback for daily-work: one task's file and a comment, sent only after the person
has seen the exact payload and said yes. Stored apart from telemetry events.

feedback.py preview <task>          task name or file; comment on stdin; prints the exact payload and saves it
feedback.py send                    POSTs the saved payload, unchanged, and deletes it
"""
import json
import sys
from pathlib import Path

import telemetry

MAX_CONTENT = 30000
MAX_COMMENT = 2000


def refuse(why):
    print(f"refused: {why}")
    sys.exit(1)


def pending():
    return telemetry.HOME / "feedback-pending.json"


def preview(task, comment):
    if telemetry.opted_out():
        refuse("DAILY_WORK_TELEMETRY=0 is set; nothing is sent")
    if not telemetry.config():
        refuse("no url and anon_key in telemetry.json; nothing can be sent")
    if not comment:
        refuse("usage: /daily-work:feedback <task name> <comment>")
    # A bare task name stands for its task file or, before grilling, its brief.
    found = [Path(task)] if "/" in task else sorted(Path().glob(f"*/tasks/{task}.md")) + sorted(Path().glob(f"*/briefs/{task}.md"))
    if len(found) > 1:
        refuse(f"'{task}' is a task in several projects; name one of: {' '.join(map(str, found))}")
    f = found[0] if found else Path(task)
    if not (f.is_file() and f.suffix == ".md" and f.parent.name in ("tasks", "briefs")):
        refuse(f"{task} is not a task name, a task file or a brief")
    payload = {
        **telemetry.common(f.parent.parent / "tasks" / f.name),
        "comment": comment[:MAX_COMMENT],
        "content": f.read_text()[:MAX_CONTENT],
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    telemetry.HOME.mkdir(parents=True, exist_ok=True)
    pending().write_text(text)
    print(f"This is exactly what will be sent to {telemetry.config()[0]} (table: feedback):")
    print(text)


def send():
    if telemetry.opted_out():
        refuse("DAILY_WORK_TELEMETRY=0 is set; nothing is sent")
    if not telemetry.config():
        refuse("no url and anon_key in telemetry.json; nothing can be sent")
    if not pending().is_file():
        refuse("nothing to send; run preview first")
    try:
        telemetry.post("feedback", pending().read_bytes(), timeout=10)
    except Exception as error:
        refuse(f"not sent ({error})")
    pending().unlink()
    print("sent")


if __name__ == "__main__":
    if sys.argv[1:2] == ["preview"] and len(sys.argv) == 3:
        preview(sys.argv[2], sys.stdin.read().strip())
    elif sys.argv[1:] == ["send"]:
        send()
    else:
        refuse("usage: feedback.py preview <task> | send")
