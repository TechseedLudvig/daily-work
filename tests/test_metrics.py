import csv
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "metrics"))
import metrics

W2, W3, W6 = "2026-01-05", "2026-01-12", "2026-02-02"  # Mondays of ISO weeks 2, 3 and 6


def ev(event, day, hour, user, task, version="1.0.0", **more):
    return {"event": event, "ts": f"{day}T{hour:02d}:00:00Z", "plugin_version": version,
            "install_id": user, "task_id": task, **more}


# Week 2, version 1.0.0: four briefs at 00:00. Three are recorded after 10, 20 and 30 hours,
# two are grilled, two of the three records carry a rating (5 and 4). Installs: u1 and u2.
# Week 3, version 1.1.0: u3 starts one task and never closes it.
# Week 6 (week 2 + 4), version 1.1.0: u1 is back and closes a task in 2 hours, unrated.
EVENTS = [
    ev("brief", W2, 0, "u1", "t1"), ev("brief", W2, 0, "u1", "t2"),
    ev("brief", W2, 0, "u2", "t3"), ev("brief", W2, 0, "u2", "t4"),
    ev("grill", W2, 1, "u1", "t1", outcome="completed"),
    ev("grill", W2, 1, "u1", "t2", outcome="completed"),
    ev("record", W2, 10, "u1", "t1", rating=5),
    ev("record", W2, 20, "u1", "t2", rating=4),
    ev("record", "2026-01-06", 6, "u2", "t3"),
    ev("brief", W3, 9, "u3", "t5", "1.1.0"),
    ev("brief", W6, 9, "u1", "t6", "1.1.0"),
    ev("record", W6, 11, "u1", "t6", "1.1.0"),
]


class Metrics(unittest.TestCase):
    def setUp(self):
        self.m = {name: rows for name, _, _, rows in metrics.compute(EVENTS)}

    def test_percentile_interpolates(self):
        self.assertEqual(metrics.percentile([10, 20, 30], 0.75), 25)
        self.assertEqual(metrics.percentile([30, 10, 20, 40], 0.5), 25)
        self.assertEqual(metrics.percentile([7], 0.75), 7)

    def test_weeks_are_iso_weeks(self):
        self.assertEqual(metrics.label(metrics.week(ev("brief", "2026-01-11", 23, "u", "t"))), "2026-W02")
        self.assertEqual(metrics.label(metrics.week(ev("brief", "2026-01-12", 0, "u", "t"))), "2026-W03")

    def test_tasks_started_and_closed(self):
        self.assertEqual(self.m["tasks"], [
            ["2026-W02", "1.0.0", 4, 3],
            ["2026-W03", "1.1.0", 1, 0],
            ["2026-W06", "1.1.0", 1, 1],
        ])

    def test_cycle_time_median_and_p75(self):
        self.assertEqual(self.m["cycle_time"], [
            ["2026-W02", "1.0.0", 3, 20.0, 25.0],
            ["2026-W03", "1.1.0", 0, "", ""],
            ["2026-W06", "1.1.0", 1, 2.0, 2.0],
        ])

    def test_completion_rate(self):
        self.assertEqual(self.m["completion"], [
            ["2026-W02", "1.0.0", 4, 3, 0.75],
            ["2026-W03", "1.1.0", 1, 0, 0.0],
            ["2026-W06", "1.1.0", 1, 1, 1.0],
        ])

    def test_grill_share_skipped_or_aborted(self):
        self.assertEqual(self.m["grill"], [
            ["2026-W02", "1.0.0", 4, 2, 0.5],
            ["2026-W03", "1.1.0", 1, 0, 1.0],
            ["2026-W06", "1.1.0", 1, 0, 1.0],
        ])

    def test_rating_average_and_share(self):
        self.assertEqual(self.m["rating"], [
            ["2026-W02", "1.0.0", 3, 2, 0.67, 4.5],
            ["2026-W06", "1.1.0", 1, 0, 0.0, ""],
        ])

    def test_active_installs_and_4_week_retention(self):
        self.assertEqual(self.m["installs"], [
            ["2026-W02", "1.0.0", 2, 1, 0.5],   # u1 of u1, u2 is active in week 6
            ["2026-W03", "1.1.0", 1, "", ""],   # week 7 is not in the data yet
            ["2026-W06", "1.1.0", 1, "", ""],
        ])

    def test_a_repeated_event_for_one_task_counts_once(self):
        again = EVENTS + [ev("brief", W2, 5, "u1", "t1"), ev("record", W2, 23, "u1", "t1", rating=1)]
        m = {name: rows for name, _, _, rows in metrics.compute(again)}
        self.assertEqual(m["tasks"][0], ["2026-W02", "1.0.0", 4, 3])
        self.assertEqual(m["rating"][0], ["2026-W02", "1.0.0", 3, 2, 0.67, 4.5])

    def test_events_without_a_task_id_count_for_installs_only(self):
        old = [ev("record", W2, 12, "u9", None, rating=1), ev("grill", W2, 12, "u9", None, outcome="completed")]
        m = {name: rows for name, _, _, rows in metrics.compute(EVENTS + old)}
        self.assertEqual(m["tasks"][0], ["2026-W02", "1.0.0", 4, 3])
        self.assertEqual(m["rating"][0], ["2026-W02", "1.0.0", 3, 2, 0.67, 4.5])
        self.assertEqual(m["installs"][0], ["2026-W02", "1.0.0", 3, 1, 0.33])

    def test_reads_timestamps_as_supabase_returns_them(self):
        rows = [dict(e, ts=e["ts"].replace("Z", "+00:00"), id=i, received_at=e["ts"],
                     outcome=e.get("outcome"), rating=e.get("rating")) for i, e in enumerate(EVENTS)]
        self.assertEqual(metrics.compute(rows), metrics.compute(EVENTS))

    def test_service_key_comes_from_the_environment_only(self):
        with mock.patch.dict(os.environ, clear=True), self.assertRaises(KeyError):
            metrics.load_supabase()

    def test_no_events(self):
        self.assertTrue(all(rows == [] for _, _, _, rows in metrics.compute([])))

    def test_writes_summary_and_one_csv_per_metric(self):
        with tempfile.TemporaryDirectory() as d:
            metrics.write(metrics.compute(EVENTS), Path(d))
            names = sorted(p.name for p in Path(d).iterdir())
            self.assertEqual(names, ["completion.csv", "cycle_time.csv", "grill.csv", "installs.csv", "rating.csv", "summary.md",
                                     "tasks.csv"])
            with open(Path(d) / "completion.csv", newline="") as f:
                rows = list(csv.reader(f))
            self.assertEqual(rows[0], ["week", "plugin_version", "briefs", "recorded", "completion_rate"])
            self.assertEqual(rows[1], ["2026-W02", "1.0.0", "4", "3", "0.75"])
            self.assertIn("| 2026-W02 | 1.0.0 | 4 | 3 | 0.75 |", (Path(d) / "summary.md").read_text())


if __name__ == "__main__":
    unittest.main()
