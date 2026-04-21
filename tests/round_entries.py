"""Test 1 — Round entries flag."""

from .base import LedgerTest, TestResult


class RoundEntriesTest(LedgerTest):
    test_id = "T01"
    title = "Round entries (ending in 000 or 999)"
    objective = "Identify unusually round journal amounts that may indicate fabricated entries or threshold avoidance."
    method = "Flag whole-number amounts where absolute value ends in 000 or 999."
    requires = ["amount"]

    def _run(self, df, cols, ctx):
        amt_abs = df["_amount"].abs()
        is_whole = (amt_abs % 1) == 0
        ends_000 = is_whole & (amt_abs >= 1000) & ((amt_abs % 1000) == 0)
        ends_999 = is_whole & (amt_abs >= 999) & ((amt_abs % 1000) == 999)

        flagged = df[ends_000 | ends_999].copy()
        if not flagged.empty:
            flagged["Flag"] = flagged["_amount"].abs().apply(
                lambda x: "Ends 000" if x % 1000 == 0 else "Ends 999"
            )
        return TestResult(self.test_id, self.title, self.objective, self.method, flagged=flagged)
