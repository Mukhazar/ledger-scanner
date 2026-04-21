"""Test 3 — Postings made during unusual hours."""

from .base import LedgerTest, TestResult


class OddHoursTest(LedgerTest):
    test_id = "T03"
    title = "Postings during odd hours"
    objective = "Identify entries posted outside normal business hours."
    method = "Flag entries posted in the configured 'after-hours' window (default: 7 PM – 8 AM)."
    requires = ["time"]

    def _run(self, df, cols, ctx):
        after_hours_start = ctx.get("odd_hours_start", 19)  # 7 PM
        after_hours_end = ctx.get("odd_hours_end", 8)        # 8 AM

        work = df.copy().dropna(subset=["_time_hour"])
        hour = work["_time_hour"].astype(int)

        if after_hours_start > after_hours_end:
            # Wraps midnight: 19..23 or 0..8
            mask = (hour >= after_hours_start) | (hour < after_hours_end)
        else:
            mask = (hour >= after_hours_start) & (hour < after_hours_end)

        flagged = work[mask].copy()
        if not flagged.empty:
            flagged["Hour"] = hour[mask].astype(str) + ":00"

        return TestResult(self.test_id, self.title, self.objective, self.method, flagged=flagged)
