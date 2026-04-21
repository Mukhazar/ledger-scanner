"""Tests 8, 9, 10 — Cross-account consistency checks.
Prepayment/Accrual entries should typically hit Bank.
Bank entries should typically hit P&L or another Bank/Balance-Sheet contra.
These tests flag entries where the expected offsetting account is missing."""

import pandas as pd
from .base import LedgerTest, TestResult


def _collect_by_doc(df, doc_col, classification_col_name="_classification"):
    """Groups entries by doc_no and lists all classifications present per doc."""
    return df.groupby(doc_col)[classification_col_name].apply(set).to_dict()


class _CrossAccountBase(LedgerTest):
    """Shared logic: for each doc_no, flag if source-classified lines exist but
    expected offset classification is not also present in the same doc."""
    requires = ["doc_no"]
    source_key = ""       # 'prepayment' / 'accrual' / 'bank'
    expected_key = ""     # 'bank' / 'pnl'
    source_label = ""
    expected_label = ""

    def _run(self, df, cols, ctx):
        source_codes = set(ctx.get(f"{self.source_key}_codes", []))
        expected_codes = set(ctx.get(f"{self.expected_key}_codes", []))
        acc_col = cols.get("account")
        doc_col = cols.get("doc_no")

        if not source_codes:
            return self._skip(f"No {self.source_label} accounts classified.")
        if not expected_codes:
            return self._skip(f"No {self.expected_label} accounts classified.")
        if not acc_col:
            return self._skip("Account column not mapped.")

        work = df.copy()
        work["_classification"] = "other"
        work.loc[work[acc_col].astype(str).isin({str(c) for c in source_codes}), "_classification"] = "source"
        work.loc[work[acc_col].astype(str).isin({str(c) for c in expected_codes}), "_classification"] = "expected"

        by_doc = _collect_by_doc(work, doc_col)

        def is_problem(doc_id):
            classes = by_doc.get(doc_id, set())
            return "source" in classes and "expected" not in classes

        flagged_docs = [d for d, cl in by_doc.items() if is_problem(d)]
        flagged = work[work[doc_col].isin(flagged_docs) & (work["_classification"] == "source")].copy()
        flagged = flagged.drop(columns=["_classification"])

        return TestResult(self.test_id, self.title, self.objective, self.method, flagged=flagged)


class PrepaymentVsBankTest(_CrossAccountBase):
    test_id = "T08"
    title = "Prepayments without corresponding Bank entry"
    objective = "Identify prepayment postings that do not have an offsetting bank entry in the same journal — possible misclassification."
    method = "For each doc number, flag prepayment-account lines where the same doc has no bank-account line."
    source_key = "prepayment"
    expected_key = "bank"
    source_label = "prepayment"
    expected_label = "bank"


class AccrualVsBankTest(_CrossAccountBase):
    test_id = "T09"
    title = "Accruals without corresponding Bank entry"
    objective = "Identify accrual postings that do not have an offsetting bank entry — possible misclassification or manual adjustment."
    method = "For each doc number, flag accrual-account lines where the same doc has no bank-account line."
    source_key = "accrual"
    expected_key = "bank"
    source_label = "accrual"
    expected_label = "bank"


class BankVsPnlTest(_CrossAccountBase):
    test_id = "T10"
    title = "Bank entries without corresponding P&L entry"
    objective = "Identify bank postings that do not touch P&L — may indicate balance-sheet-only transfers or incomplete postings worth review."
    method = "For each doc number, flag bank-account lines where the same doc has no P&L-account line."
    source_key = "bank"
    expected_key = "pnl"
    source_label = "bank"
    expected_label = "P&L"
