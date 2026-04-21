"""Test 7 — Debit entries in revenue accounts.
Revenue accounts normally hold credit balances. Debits (other than genuine refunds/
adjustments) are unusual and worth reviewing."""

from .base import LedgerTest, TestResult


class RevenueDebitsTest(LedgerTest):
    test_id = "T07"
    title = "Debit postings to revenue accounts"
    objective = "Identify debit entries in revenue codes — unusual except for genuine refunds or reversals."
    method = "Flag entries where account is classified as Revenue and amount is positive (debit)."
    requires = ["amount"]

    def _run(self, df, cols, ctx):
        revenue_codes = set(ctx.get("revenue_codes", []))
        acc_col = cols.get("account")

        if not revenue_codes:
            return self._skip("No revenue account codes classified. Use 'Account classification' panel in sidebar.")
        if not acc_col:
            return self._skip("Account column not mapped.")

        work = df.copy()
        is_revenue = work[acc_col].astype(str).isin({str(c) for c in revenue_codes})
        is_debit = work["_amount"] > 0
        flagged = work[is_revenue & is_debit].copy()
        return TestResult(self.test_id, self.title, self.objective, self.method, flagged=flagged)
