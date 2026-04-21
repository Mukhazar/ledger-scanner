"""Test 12 — Users posting to key/sensitive accounts.
Flags entries where a user has posted to accounts classified as 'key' or 'sensitive'
(e.g., suspense accounts, inter-company, loss accounts, related-party)."""

from .base import LedgerTest, TestResult


class UserKeyAccountsTest(LedgerTest):
    test_id = "T12"
    title = "User postings to key/sensitive accounts"
    objective = "Identify which users are posting to sensitive accounts that warrant closer review."
    method = "Flag all entries where the account is classified as 'key account' by the auditor."
    requires = ["user"]

    def _run(self, df, cols, ctx):
        key_codes = set(ctx.get("key_account_codes", []))
        acc_col = cols.get("account")

        if not key_codes:
            return self._skip("No 'key account' codes classified. Use the Account Classification panel.")
        if not acc_col:
            return self._skip("Account column not mapped.")

        work = df.copy()
        flagged = work[work[acc_col].astype(str).isin({str(c) for c in key_codes})].copy()
        return TestResult(self.test_id, self.title, self.objective, self.method, flagged=flagged)
