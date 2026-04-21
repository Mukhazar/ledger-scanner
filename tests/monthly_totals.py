"""Test 4 — Monthly transaction totals summary.
Not strictly a 'flag' test — provides a summary for auditor review."""

import pandas as pd
from .base import LedgerTest, TestResult


class MonthlyTotalsTest(LedgerTest):
    test_id = "T04"
    title = "Monthly transaction totals"
    objective = "Summarize total debits, credits, and net movement by month for trend review."
    method = "Group all entries by posting month."
    requires = ["amount", "date"]

    def _run(self, df, cols, ctx):
        work = df.dropna(subset=["_date", "_amount"]).copy()
        work["_month"] = work["_date"].dt.to_period("M").astype(str)

        summary = work.groupby("_month").agg(
            Entries=("_amount", "size"),
            Total_Debits=("_amount", lambda s: s[s > 0].sum()),
            Total_Credits=("_amount", lambda s: s[s < 0].sum()),
            Net=("_amount", "sum"),
        ).reset_index().rename(columns={"_month": "Month"})

        return TestResult(
            self.test_id, self.title, self.objective, self.method,
            flagged=summary,
            notes="Summary output — review for unusual spikes or drops.",
        )
