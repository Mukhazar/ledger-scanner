"""Test 13 — Possible duplicate journal entries."""

import pandas as pd
from .base import LedgerTest, TestResult


class DuplicatesTest(LedgerTest):
    test_id = "T13"
    title = "Possible duplicate journal entries"
    objective = "Identify entries that appear duplicated across amount, date, account, and description."
    method = "Flag groups of 2+ rows sharing the same amount + date + account (+ description if available)."
    requires = ["amount", "date"]

    def _run(self, df, cols, ctx):
        acc_col = cols.get("account")
        desc_col = cols.get("description")

        work = df.dropna(subset=["_amount", "_date"]).copy()
        work["_date_only"] = work["_date"].dt.date

        group_cols = ["_amount", "_date_only"]
        if acc_col and acc_col in work.columns:
            group_cols.append(acc_col)
        if desc_col and desc_col in work.columns:
            group_cols.append(desc_col)

        dup_mask = work.duplicated(subset=group_cols, keep=False)
        flagged = work[dup_mask].copy()
        if not flagged.empty:
            # Assign a group id so auditor can pair duplicates
            flagged["DupGroup"] = flagged.groupby(group_cols, dropna=False).ngroup() + 1
            flagged = flagged.sort_values("DupGroup")
        flagged = flagged.drop(columns=["_date_only"], errors="ignore")
        return TestResult(self.test_id, self.title, self.objective, self.method, flagged=flagged)
