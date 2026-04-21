"""Test 5 — Reversed journal entries.
Flag: same absolute amount posted within a short window, one debit one credit,
same account code if available."""

import pandas as pd
from .base import LedgerTest, TestResult


class ReversedEntriesTest(LedgerTest):
    test_id = "T05"
    title = "Reversed journal entries"
    objective = "Identify pairs of entries that appear to offset each other, possibly hiding irregular activity."
    method = "For each entry, find an entry with the same absolute amount but opposite sign within the engagement period (same account if account code available)."
    requires = ["amount", "date"]

    def _run(self, df, cols, ctx):
        work = df.dropna(subset=["_amount", "_date"]).copy()
        work = work[work["_amount"] != 0]
        work["_abs"] = work["_amount"].abs()
        work["_sign"] = work["_amount"].apply(lambda x: "D" if x > 0 else "C")

        acc_col = cols.get("account")

        group_cols = ["_abs"]
        if acc_col and acc_col in work.columns:
            group_cols.append(acc_col)

        # For each group, we need at least one positive and one negative
        def has_both_signs(g):
            return (g["_sign"] == "D").any() and (g["_sign"] == "C").any()

        grouped = work.groupby(group_cols, dropna=False)
        flagged_indexes = []
        for _, g in grouped:
            if len(g) >= 2 and has_both_signs(g):
                flagged_indexes.extend(g.index.tolist())

        flagged = work.loc[flagged_indexes].drop(columns=["_abs", "_sign"]).copy()
        return TestResult(self.test_id, self.title, self.objective, self.method, flagged=flagged)
