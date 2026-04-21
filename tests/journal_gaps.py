"""Test 6 — Gaps or out-of-sequence journal numbers."""

import re
import pandas as pd
from .base import LedgerTest, TestResult


class JournalGapsTest(LedgerTest):
    test_id = "T06"
    title = "Gaps or jumps in journal entry numbers"
    objective = "Identify missing sequence numbers, which may indicate deleted or hidden entries."
    method = "Extract numeric portion of doc numbers, sort, and identify non-sequential gaps."
    requires = ["doc_no"]

    def _run(self, df, cols, ctx):
        doc_col = cols["doc_no"]
        work = df.copy()
        work["_docnum"] = work[doc_col].astype(str).str.extract(r"(\d+)", expand=False)
        work = work.dropna(subset=["_docnum"])
        if work.empty:
            return self._skip("No numeric portion found in document numbers.")
        work["_docnum"] = work["_docnum"].astype(int)

        # Check if there's a prefix grouping (e.g., JE001 vs INV001)
        work["_prefix"] = work[doc_col].astype(str).str.extract(r"^([A-Za-z\-/]+)", expand=False).fillna("")

        gaps_list = []
        for prefix, g in work.groupby("_prefix"):
            nums = sorted(g["_docnum"].unique())
            if len(nums) < 2:
                continue
            expected = set(range(nums[0], nums[-1] + 1))
            actual = set(nums)
            missing = sorted(expected - actual)
            for m in missing:
                gaps_list.append({
                    "Prefix": prefix or "(none)",
                    "Missing Number": m,
                    "Before": max([n for n in nums if n < m]),
                    "After": min([n for n in nums if n > m]),
                })

        gaps_df = pd.DataFrame(gaps_list)
        notes = None
        if not gaps_df.empty:
            notes = f"Found {len(gaps_df)} missing sequence number(s) across {gaps_df['Prefix'].nunique()} prefix group(s)."
        return TestResult(self.test_id, self.title, self.objective, self.method,
                          flagged=gaps_df, notes=notes)
