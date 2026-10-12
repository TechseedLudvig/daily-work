#!/usr/bin/env python3
"""Export logged content for analysis: one JSON line per content task id, with its runs in the
order they arrived and its outcome.

export_content.py [--out content.jsonl]             read the Supabase "content" table: URL from
                                                    telemetry.json, service (secret) key from
                                                    the environment variable SUPABASE_SERVICE_KEY
export_content.py --input rows.jsonl [--out ...]    read rows from a file instead

Each line: {"content_id", "outcome": {"outcome", "rating", "grill_completed", "ts"} or null,
            "runs": [{"skill", "ts", "plugin_version", "turns", "files"}]}
The output holds task content. Keep it out of every repo.
"""
import argparse
import json
from pathlib import Path

import metrics


def group(rows):
    """Tasks in order of first appearance. A task recorded twice keeps its latest outcome."""
    tasks = {}
    for row in sorted(rows, key=lambda r: r.get("id", 0)):
        task = tasks.setdefault(row["content_id"], {"content_id": row["content_id"], "outcome": None, "runs": []})
        if row["kind"] == "run":
            task["runs"].append({k: row[k] for k in ("skill", "ts", "plugin_version", "turns", "files")})
        else:
            task["outcome"] = {"outcome": row["outcome"], "rating": row.get("rating"),
                               "grill_completed": row["grill_completed"], "ts": row["ts"]}
    return list(tasks.values())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export daily-work content rows grouped by task.")
    parser.add_argument("--input", help="JSON lines file of content rows, instead of Supabase")
    parser.add_argument("--out", default="content.jsonl")
    args = parser.parse_args()
    if args.input:
        loaded = [json.loads(line) for line in Path(args.input).read_text().splitlines() if line.strip()]
    else:
        loaded = metrics.load_supabase("content")
    tasks = group(loaded)
    Path(args.out).write_text("".join(json.dumps(t, ensure_ascii=False) + "\n" for t in tasks))
    print(f"{len(loaded)} rows; wrote {len(tasks)} tasks to {args.out}")
