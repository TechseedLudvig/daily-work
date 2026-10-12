#!/usr/bin/env python3
"""Weekly daily-work usage metrics, broken down by plugin version.

metrics.py --supabase [--out metrics-out]            read the Supabase "events" table: URL from
                                                     telemetry.json, service (secret) key from
                                                     the environment variable SUPABASE_SERVICE_KEY
metrics.py --input events.jsonl [--out metrics-out]  one JSON event per line

Writes summary.md and one CSV per metric. A week is an ISO week, Monday to Sunday, UTC.
Task metrics (cycle time, completion, grill) belong to the week and version of the brief.
Events without a task id (tasks older than the task id) count for installs only.
"""
import argparse
import csv
import json
import os
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from statistics import median


def when(event):
    return datetime.fromisoformat(event["ts"].replace("Z", "+00:00"))


def week(event):
    day = when(event).date()
    return day - timedelta(days=day.weekday())


def label(monday):
    year, number, _ = monday.isocalendar()
    return f"{year}-W{number:02d}"


def percentile(values, p):
    """Linear interpolation between the two nearest ranks."""
    v = sorted(values)
    k = (len(v) - 1) * p
    lo = int(k)
    hi = min(lo + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (k - lo)


def num(x):
    return "" if x is None else round(x, 2)


def share(part, whole):
    return part / whole if whole else None


def compute(events):
    """Return [(name, title, header, rows)], rows sorted by week then version."""
    events = sorted(events, key=when)
    first = {}  # the earliest event of each kind per task
    for e in events:
        if e.get("task_id") and (e["event"] != "grill" or e.get("outcome") == "completed"):
            first.setdefault((e["event"], e["task_id"]), e)
    briefs = [e for (kind, _), e in first.items() if kind == "brief"]
    records = [e for (kind, _), e in first.items() if kind == "record"]

    def group(items):
        out = {}
        for e in items:
            out.setdefault((week(e), e["plugin_version"]), []).append(e)
        return out

    def closed(brief):
        record = first.get(("record", brief["task_id"]))
        return record if record and when(record) >= when(brief) else None

    by_brief, by_record, by_any = group(briefs), group(records), group(events)
    installs_in_week = {}
    for e in events:
        installs_in_week.setdefault(week(e), set()).add(e["install_id"])
    last_week = max(installs_in_week, default=None)

    tasks, cycle, completion, grill, rating, installs = [], [], [], [], [], []
    for key in sorted(by_any):
        wk, version = key
        head = [label(wk), version]
        b, r = by_brief.get(key, []), by_record.get(key, [])
        tasks.append(head + [len(b), len(r)])
        if b:
            hours = [(when(closed(e)) - when(e)).total_seconds() / 3600 for e in b if closed(e)]
            cycle.append(head + [len(hours), num(median(hours) if hours else None),
                                 num(percentile(hours, 0.75) if hours else None)])
            completion.append(head + [len(b), len(hours), num(share(len(hours), len(b)))])
            grilled = sum(("grill", e["task_id"]) in first for e in b)
            grill.append(head + [len(b), grilled, num(share(len(b) - grilled, len(b)))])
        if r:
            rated = [e["rating"] for e in r if e.get("rating") is not None]
            rating.append(head + [len(r), len(rated), num(share(len(rated), len(r))),
                                  num(sum(rated) / len(rated) if rated else None)])
        active = {e["install_id"] for e in by_any[key]}
        later = wk + timedelta(weeks=4)
        if later <= last_week:
            kept = len(active & installs_in_week.get(later, set()))
            installs.append(head + [len(active), kept, num(share(kept, len(active)))])
        else:
            installs.append(head + [len(active), "", ""])

    w = ["week", "plugin_version"]
    return [
        ("tasks", "Tasks started and closed", w + ["tasks_started", "tasks_closed"], tasks),
        ("cycle_time", "Cycle time, brief to record", w + ["tasks", "median_hours", "p75_hours"], cycle),
        ("completion", "Completion rate", w + ["briefs", "recorded", "completion_rate"], completion),
        ("grill", "Grill", w + ["briefs", "grilled", "share_skipped_or_aborted"], grill),
        ("rating", "Rating", w + ["records", "rated", "share_rated", "average_rating"], rating),
        ("installs", "Active installs and 4-week retention",
         w + ["active_installs", "retained_4w", "retention_4w"], installs),
    ]


def write(metrics, out):
    out.mkdir(parents=True, exist_ok=True)
    lines = ["# daily-work usage", ""]
    for name, title, header, rows in metrics:
        with open(out / f"{name}.csv", "w", newline="") as f:
            csv.writer(f).writerows([header] + rows)
        lines += [f"## {title}", "", "| " + " | ".join(header) + " |", "|" + " --- |" * len(header)]
        lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
        lines.append("")
    (out / "summary.md").write_text("\n".join(lines))


def load_supabase(table="events", page=1000):
    """Every row of a table. The service key comes from the environment only."""
    root = Path(__file__).resolve().parent.parent
    url = json.loads((root / "telemetry.json").read_text())["url"].rstrip("/")
    key = os.environ["SUPABASE_SERVICE_KEY"]
    rows = []
    while True:
        request = urllib.request.Request(
            f"{url}/rest/v1/{table}?select=*&order=id&limit={page}&offset={len(rows)}",
            headers={"apikey": key})
        with urllib.request.urlopen(request, timeout=30) as response:
            batch = json.load(response)
        rows += batch
        if len(batch) < page:
            return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Weekly daily-work usage metrics.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", help="JSON lines file, one event per line")
    source.add_argument("--supabase", action="store_true", help='read the Supabase "events" table')
    parser.add_argument("--out", default="metrics-out")
    args = parser.parse_args()
    if args.supabase:
        loaded = load_supabase()
    else:
        loaded = [json.loads(line) for line in Path(args.input).read_text().splitlines() if line.strip()]
    write(compute(loaded), Path(args.out))
    print(f"{len(loaded)} events; wrote {args.out}/summary.md and one CSV per metric")
