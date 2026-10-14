"""Scoring for the offline eval: checks on the files a run produced, the arithmetic on what
the judge returned, aggregation over runs, and comparison against a baseline. No model calls
and no file access here; everything takes text or plain data and returns plain data.
"""
import json
import math
import re
import statistics

STEPS = ["brief", "grill", "work", "record", "end_to_end"]
PLACEHOLDER = "<written by /daily-work:record>"
DONE_PLACEHOLDER = "- <a check a person can confirm in under a minute>"
# Everything else is better when higher.
LOWER_IS_BETTER = {"questions", "questions_docs_answer", "rounds", "turns", "tokens", "tokens_input",
                   "tokens_cached", "tokens_output", "cost_usd", "seconds"}
SHARES = {"layout_share", "essential_share", "facts_share", "stated_share", "checks_share", "completed"}


def kind(metric):
    """score: a 1 to 5 judge criterion. share: 0 to 1. count: anything counted or measured."""
    if metric in SHARES:
        return "share"
    return "count" if metric in LOWER_IS_BETTER else "score"


def clean(text):
    lines = [line.rstrip() for line in text.strip().splitlines()]
    return "\n".join(lines)


def sections(text):
    """The body under each '## ' heading, in order of appearance."""
    out, name = {}, None
    for line in text.splitlines():
        if line.startswith("## "):
            name = line[3:].strip()
            out[name] = []
        elif name is not None:
            out[name].append(line)
    return {k: clean("\n".join(v)) for k, v in out.items()}


def header(text, key):
    for line in text.splitlines():
        if line.startswith("## "):
            break
        if line.startswith(f"{key}: "):
            return line[len(key) + 2:].strip()
    return None


def brief_body(brief):
    """The description in a brief: what follows its heading and its Project, Written and Id lines."""
    lines = brief.splitlines()
    last = max((i for i, line in enumerate(lines) if line.startswith(("# ", "Project: ", "Written: ", "Id: "))),
               default=-1)
    return clean("\n".join(lines[last + 1:]))


def share(checks):
    return sum(1 for v in checks.values() if v) / len(checks) if checks else 0.0


def brief_layout(brief):
    return {
        "heading": brief.startswith("# ") and len(brief.splitlines()[0]) > 2,
        "project_line": bool(header(brief, "Project")),
        "written_line": bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", header(brief, "Written") or "")),
        "id_line": bool(header(brief, "Id")),
        "has_description": bool(brief_body(brief)),
    }


def task_layout(task, brief, brief_deleted):
    """The layout the generated AGENTS.md asks a grilling session to leave behind."""
    s = sections(task)
    spec = s.get("Spec", "")
    done = re.search(r"^Done looks like:\n((?:- .*\n?)+)", spec, re.M)
    done_lines = [line for line in (done.group(1).splitlines() if done else []) if line != DONE_PLACEHOLDER]
    purpose = re.search(r"^Purpose: (.+)$", spec, re.M)
    return {
        "heading": task.startswith("# "),
        "project_line": bool(header(task, "Project")),
        "created_line": bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", header(task, "Created") or "")),
        "id_copied": bool(header(task, "Id")) and header(task, "Id") == header(brief, "Id"),
        "sections_in_order": list(s) == ["Ask", "Spec", "Result", "Caveats"],
        "ask_is_brief": clean(s.get("Ask", "")) == brief_body(brief) != "",
        "spec_purpose": bool(purpose) and not purpose.group(1).startswith("<"),
        "spec_done_lines": bool(done_lines),
        "spec_decided": bool(re.search(r"^Decided:$", spec, re.M)),
        "spec_out_of_scope": bool(re.search(r"^Out of scope:$", spec, re.M)),
        "result_left": s.get("Result") == PLACEHOLDER,
        "caveats_left": s.get("Caveats") == PLACEHOLDER,
        "brief_deleted": bool(brief_deleted),
    }


def ask_and_spec(task):
    s = sections(task)
    return s.get("Ask"), s.get("Spec")


def record_checks(task_before, task_after, project_readme, task_name, commit_subjects):
    """What record must leave behind, whatever it wrote: the parts record.sh also enforces."""
    after = sections(task_after)
    written = lambda body: bool(body) and PLACEHOLDER not in body
    return {
        "ask_spec_unchanged": ask_and_spec(task_before) == ask_and_spec(task_after) != (None, None),
        "result_written": written(after.get("Result")),
        "caveats_written": written(after.get("Caveats")),
        "readme_done": bool(re.search(rf"^- \d{{4}}-\d{{2}}-\d{{2}} {re.escape(task_name)}: done, \S", project_readme, re.M)),
        "committed": f"daily-work: record {task_name}" in commit_subjects,
    }


def parse_judge(text):
    """The JSON object in a judge reply, which may come wrapped in prose or a code fence."""
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("no JSON object in the judge reply")
    return json.loads(text[start:end + 1])


def judge_scores(parsed, criteria):
    """{criterion: score} for exactly the criteria asked for; refuses anything outside 1 to 5."""
    out = {}
    for c in criteria:
        entry = (parsed.get("scores") or {}).get(c)
        score = entry.get("score") if isinstance(entry, dict) else entry
        if not isinstance(score, int) or isinstance(score, bool) or not 1 <= score <= 5:
            raise ValueError(f"judge gave no score from 1 to 5 for '{c}'")
        out[c] = score
    return out


def fact_metrics(card_facts, judged):
    """card_facts: [{id, essential}]. judged: {id: 'stated' | 'assumed' | 'absent'} for the task file.
    essential_share: essential hidden facts found in the task file. stated_share: of the facts
    found, those written as stated by the asker and not as an assumption of the agent."""
    found = [f for f in card_facts if judged.get(f["id"]) in ("stated", "assumed")]
    essential = [f for f in card_facts if f["essential"]]
    return {
        "essential_share": sum(1 for f in essential if f in found) / len(essential) if essential else 1.0,
        "facts_share": len(found) / len(card_facts) if card_facts else 1.0,
        "stated_share": sum(1 for f in found if judged[f["id"]] == "stated") / len(found) if found else 0.0,
    }


def question_metrics(judged_questions, rounds):
    """judged_questions: [{question, docs_answer: bool}], every question the grill put to the user."""
    return {
        "questions": len(judged_questions),
        "questions_docs_answer": sum(1 for q in judged_questions if q.get("docs_answer")),
        "rounds": rounds,
    }


def aggregate(runs):
    """runs: [{scenario, run, metrics: {step: {metric: number}}}].
    Returns one row per scenario, step and metric, plus rows for scenario 'ALL': the mean of
    the scenario means, with min and max over scenarios."""
    values = {}
    for r in runs:
        for step, metrics in r["metrics"].items():
            for metric, v in metrics.items():
                if v is not None:
                    values.setdefault((r["scenario"], step, metric), []).append(float(v))
    rows = [row(scenario, step, metric, vs) for (scenario, step, metric), vs in values.items()]
    overall = {}
    for r in rows:
        overall.setdefault((r["step"], r["metric"]), []).append(r["mean"])
    rows += [row("ALL", step, metric, means) for (step, metric), means in overall.items()]
    order = {s: i for i, s in enumerate(STEPS)}
    return sorted(rows, key=lambda r: (r["scenario"] == "ALL", r["scenario"], order.get(r["step"], 99), r["metric"]))


def row(scenario, step, metric, vs):
    return {"scenario": scenario, "step": step, "metric": metric, "n": len(vs),
            "mean": round(statistics.fmean(vs), 3), "min": min(vs), "max": max(vs),
            "sd": round(statistics.stdev(vs), 3) if len(vs) > 1 else 0.0}


def noise(rows_a, rows_b, leave_out=()):
    """How far each metric moves between two full runs of the same code: the standard deviation,
    over scenarios, of the difference in the scenario mean. Keyed "step/metric"."""
    a = {(r["scenario"], r["step"], r["metric"]): r["mean"] for r in rows_a
         if r["scenario"] != "ALL" and r["scenario"] not in leave_out}
    diffs = {}
    for r in rows_b:
        key = (r["scenario"], r["step"], r["metric"])
        if key in a:
            diffs.setdefault(f"{r['step']}/{r['metric']}", []).append(r["mean"] - a[key])
    return {k: {"sd": round(statistics.stdev(d), 4), "scenarios": len(d)} for k, d in diffs.items() if len(d) > 1}


def limit(row, base_mean, thresholds, noise):
    """The largest drop that is still noise. The config threshold is the floor; with a noise
    calibration, a drop must also be past noise_multiplier standard deviations, which for the
    overall row (a mean over scenarios) shrink by the square root of the scenario count."""
    k = kind(row["metric"])
    if k == "count":
        # A count that goes from 0 to anything has no relative size; one whole unit counts.
        floor = thresholds["count_relative"] * abs(base_mean) if base_mean else 0.99
    else:
        floor = thresholds[k]
    n = (noise or {}).get(f"{row['step']}/{row['metric']}")
    if not n:
        return floor
    spread = thresholds.get("noise_multiplier", 3) * n["sd"]
    if row["scenario"] == "ALL":
        spread /= math.sqrt(n["scenarios"])
    return max(floor, spread)


def compare(rows, baseline, thresholds, noise=None):
    """One entry per row that the baseline also has. delta is signed so that negative is worse.
    beyond: the drop is past the limit for that row. Only an overall row is a regression; a
    scenario row past its limit is marked for a look, because three runs of one scenario vary
    too much for one drop to mean anything on its own."""
    base = {(b["scenario"], b["step"], b["metric"]): b for b in baseline}
    out = []
    for r in rows:
        b = base.get((r["scenario"], r["step"], r["metric"]))
        if b is None:
            continue
        delta = r["mean"] - b["mean"]
        if r["metric"] in LOWER_IS_BETTER:
            delta = -delta
        lim = limit(r, b["mean"], thresholds, noise)
        beyond = -delta > lim
        out.append({"scenario": r["scenario"], "step": r["step"], "metric": r["metric"], "kind": kind(r["metric"]),
                    "baseline": b["mean"], "now": r["mean"], "delta": round(delta, 3), "limit": round(lim, 3),
                    "beyond": beyond, "regression": beyond and r["scenario"] == "ALL"})
    return out


# Running longer or costing more is reported, not counted as the flow getting worse.
INFORMATIONAL = {"turns", "tokens", "tokens_input", "tokens_cached", "tokens_output", "cost_usd", "seconds"}


def regressions(comparison):
    return [c for c in comparison if c["regression"] and c["metric"] not in INFORMATIONAL]


def looks(comparison, scenario=None, step=None, metric=None):
    """Scenario rows whose drop is past their limit: where to look, not regressions."""
    return [c for c in comparison if c["beyond"] and c["scenario"] != "ALL" and c["metric"] not in INFORMATIONAL
            and scenario in (None, c["scenario"]) and step in (None, c["step"]) and metric in (None, c["metric"])]


def first_drop(comparison):
    """The earliest step in the flow with a regression, or None."""
    hit = {c["step"] for c in regressions(comparison)}
    return next((s for s in STEPS if s in hit), None)
