"""Test 14 — Suspicious keywords in descriptions/narrations."""

import re
from .base import LedgerTest, TestResult


class SuspiciousWordsTest(LedgerTest):
    test_id = "T14"
    title = "Suspicious keywords in descriptions"
    objective = "Identify entries whose narrations contain words suggesting adjustments, corrections, or concealment."
    method = "Case-insensitive search for a configurable list of keywords across the description field."
    requires = ["description"]

    def _run(self, df, cols, ctx):
        desc_col = cols["description"]
        words = ctx.get("suspicious_words", [])
        if not words:
            return self._skip("Suspicious word list is empty.")

        pattern = r"\b(" + "|".join(re.escape(w) for w in words) + r")\b"
        desc_str = df[desc_col].astype(str)
        matches = desc_str.str.extract(pattern, expand=False, flags=re.IGNORECASE)
        mask = matches.notna()
        flagged = df[mask].copy()
        if not flagged.empty:
            flagged["Matched_Keyword"] = matches[mask].str.lower().values
        return TestResult(self.test_id, self.title, self.objective, self.method, flagged=flagged)
