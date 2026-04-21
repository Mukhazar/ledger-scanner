"""Test 11 — Postings by user (summary)."""

import pandas as pd
from .base import LedgerTest, TestResult


class PostingsByUserTest(LedgerTest):
    test_id = "T11"
    title = "Postings by user"
    objective = "Summarize posting volume and value per user to identify unusual concentration."
    method = "Group all entries by the user/posted-by column."
    requires = ["user"]

    def _run(self, df, cols, ctx):
        user_col = cols["user"]
        work = df.copy()
        summary = work.groupby(user_col).agg(
            Entries=(user_col, "size"),
            Total_Debits=("_amount", lambda s: s[s > 0].sum() if not s.isna().all() else 0),
            Total_Credits=("_amount", lambda s: s[s < 0].sum() if not s.isna().all() else 0),
        ).reset_index().rename(columns={user_col: "User"})

        summary = summary.sort_values("Entries", ascending=False)
        return TestResult(
            self.test_id, self.title, self.objective, self.method,
            flagged=summary,
            notes="Summary output — review users with unusually high volume or value concentration."
        )
