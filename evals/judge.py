"""Turns a run record into metrics per step: file checks from scoring.py plus an LLM judge that
scores each rubric criterion from 1 to 5 with a short reason.
"""
import json
import subprocess
import tempfile
from pathlib import Path

import flow
import scoring

PROMPT = """You are grading one step of a workflow in which an AI assistant helps a person with a task
at work. Grade only what the materials show. Be strict: 5 means nothing to fix.

Criteria, each scored 1 to 5:
{criteria}
{extra}
Materials:

{materials}

Reply with one JSON object and nothing else, in this shape:
{shape}
"""

FACTS = """
Also, for each hidden fact below, say how the task file carries it: "stated" if the task file
gives it as something the person said or as a plain requirement, "assumed" if it appears only
as an assumption or a choice of the assistant, "absent" if it is not there.
{facts}

Also list every question the assistant put to the person in the conversation, one entry per
question, and for each whether the documents already answer it (docs_answer).
"""


def block(title, text):
    return f"=== {title} ===\n{text.strip() if text else '(nothing)'}\n"


def talk(transcript):
    return "\n\n".join(f"{'PERSON' if t['role'] == 'user' else 'ASSISTANT'}: {t['text']}" for t in transcript)


def outputs(files):
    return "\n".join(block(f"output file {p}", t) for p, t in (files.get("outputs") or {}).items()) or block("output files", "")


def worked(files):
    """The work step left something to grade: a file in outputs/, or an answer written into the task file."""
    return bool(files.get("outputs")) or files.get("task_after_work", files.get("task_after_grill")) != files.get("task_after_grill")


def task_after_work(files):
    changed = files.get("task_after_work") not in (None, files.get("task_after_grill"))
    return block("task file as the work left it", files["task_after_work"]) if changed else ""


def materials(step, scenario, record):
    f, t = record["files"], record["transcripts"]
    card = "\n".join(f"- {x['fact']}" for x in scenario["card"]["facts"])
    docs = "\n".join(block(f"document {n}", d) for n, d in scenario["docs"].items())
    if step == "brief":
        return block("the person's request", scenario["request"]) + block("conversation", talk(t["brief"])) + block("brief written", f.get("brief"))
    if step == "grill":
        return (block("brief", f.get("brief")) + docs + block("conversation", talk(t["grill"]))
                + block("task file written", f.get("task_after_grill")))
    if step == "work":
        return (block("task file", f.get("task_after_grill")) + block("expected", scenario["expected"]) + outputs(f)
                + task_after_work(f))
    if step == "record":
        return (block("task file after record", f.get("task_final")) + outputs(f)
                + block("conversation while working", talk(t.get("work", []))))
    return (block("the person's request", scenario["request"]) + block("what the person really wanted (hidden facts)", card)
            + block("expected", scenario["expected"]) + block("task file", f.get("task_final") or f.get("task_after_grill")) + outputs(f))


def ask(step, scenario, record, cfg, out):
    """One judge call for a step. Returns (parsed reply, cost in USD at API prices, tokens by kind)."""
    rubric = cfg["rubrics"][step]
    shape = {"scores": {c: {"score": 3, "reason": "one sentence"} for c in rubric}}
    extra = ""
    if step == "grill":
        facts = scenario["card"]["facts"]
        extra = FACTS.format(facts="\n".join(f"- {x['id']}: {x['fact']}" for x in facts))
        shape["facts"] = {x["id"]: "stated | assumed | absent" for x in facts}
        shape["questions"] = [{"question": "the question, shortened", "docs_answer": False}]
    prompt = PROMPT.format(criteria="\n".join(f"- {c}: {text}" for c, text in rubric.items()), extra=extra,
                           materials=materials(step, scenario, record), shape=json.dumps(shape, indent=2))
    cost, tokens = 0.0, {k: 0 for k in flow.TOKENS}
    with tempfile.TemporaryDirectory(prefix="daily-work-eval-judge-") as empty:
        for attempt in (1, 2):
            try:
                call = flow.claude(prompt, empty, cfg["models"]["judge"], cfg, Path(out) / "logs" / f"judge-{step}-{attempt}.jsonl")
                cost += call["cost_usd"]
                tokens = {k: tokens[k] + call[k] for k in flow.TOKENS}
                parsed = scoring.parse_judge(call["text"])
                scoring.judge_scores(parsed, rubric)
                return parsed, cost, tokens
            except (ValueError, RuntimeError, subprocess.TimeoutExpired):
                continue
    return None, cost, tokens


def why(parsed, rubric):
    return {c: (parsed["scores"][c].get("reason", "") if isinstance(parsed["scores"][c], dict) else "") for c in rubric}


def score_run(record, scenario, cfg, out, steps):
    """Metrics per step for one run. A step that did not complete scores 1 on every criterion
    and 0 on every share: there is nothing to grade, and leaving it out would hide the failure."""
    f, metrics, reasons, checks, judge_cost = record["files"], {}, {}, {}, 0.0
    split = {k: sum(s[k] for s in record["steps"].values()) for k in flow.TOKENS}
    judge_tokens = 0
    for step in steps:
        s = record["steps"][step]
        m = metrics[step] = {"completed": float(s["completed"]), "turns": s["turns"], "tokens": s["tokens"],
                             "cost_usd": s["cost_usd"], "seconds": s["seconds"]}
        produced = worked(f) if step == "work" else f.get({"brief": "brief", "grill": "task_after_grill", "record": "task_final"}[step])
        rubric = cfg["rubrics"][step]
        if not produced:
            m.update({c: 1 for c in rubric})
            m.update({"brief": {"layout_share": 0.0}, "grill": {"layout_share": 0.0, "essential_share": 0.0},
                      "record": {"checks_share": 0.0}}.get(step, {}))
            continue
        if step == "brief":
            checks[step] = scoring.brief_layout(f["brief"])
            m["layout_share"] = scoring.share(checks[step])
        elif step == "grill":
            checks[step] = scoring.task_layout(f["task_after_grill"], f.get("brief", ""), f.get("brief_deleted"))
            m["layout_share"] = scoring.share(checks[step])
        elif step == "record":
            checks[step] = scoring.record_checks(f["task_after_grill"], f["task_final"], f["project_readme"],
                                                 f["task_name"], f["commits"])
            m["checks_share"] = scoring.share(checks[step])
        parsed, cost, tokens = ask(step, scenario, record, cfg, out)
        judge_cost += cost
        judge_tokens += tokens["tokens"]
        split = {k: split[k] + tokens[k] for k in flow.TOKENS}
        if parsed is None:
            reasons[step] = {"error": "the judge gave no usable reply in two tries"}
            continue
        m.update(scoring.judge_scores(parsed, rubric))
        reasons[step] = why(parsed, rubric)
        if step == "grill":
            m.update(scoring.fact_metrics(scenario["card"]["facts"], parsed.get("facts") or {}))
            rounds = sum(1 for t in record["transcripts"]["grill"] if t["role"] == "assistant")
            m.update(scoring.question_metrics(parsed.get("questions") or [], rounds))
            reasons[step]["questions"] = parsed.get("questions") or []
            reasons[step]["facts"] = parsed.get("facts") or {}
    if set(steps) == set(flow.FLOW):
        done = all(record["steps"][s]["completed"] for s in flow.FLOW)
        m = metrics["end_to_end"] = {"completed": float(done)}
        for k in ("turns", "cost_usd", "seconds", *flow.TOKENS):
            m[k] = round(sum(record["steps"][s][k] for s in flow.FLOW), 4)
        rubric = cfg["rubrics"]["end_to_end"]
        if worked(f):
            parsed, cost, tokens = ask("end_to_end", scenario, record, cfg, out)
            judge_cost += cost
            judge_tokens += tokens["tokens"]
            split = {k: split[k] + tokens[k] for k in flow.TOKENS}
            if parsed:
                m.update(scoring.judge_scores(parsed, rubric))
                reasons["end_to_end"] = why(parsed, rubric)
        else:
            m.update({c: 1 for c in rubric})
    scored = {"scenario": record["scenario"], "grill": record["grill"], "metrics": metrics, "checks": checks,
              "reasons": reasons, "judge_cost_usd": round(judge_cost, 4), "judge_tokens": judge_tokens, "tokens_split": split, "error": record["error"]}
    (Path(out) / "scores.json").write_text(json.dumps(scored, indent=2, ensure_ascii=False))
    return scored
