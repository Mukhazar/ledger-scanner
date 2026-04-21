"""Base classes for all forensic tests.

Each test is a subclass of LedgerTest. Tests receive:
    - df: normalized DataFrame with '_amount' and '_date' columns already parsed
    - cols: dict mapping logical names ('amount', 'date', ...) to actual column names
    - ctx: dict of engagement context (country, holidays, weekend_days, etc.)
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import pandas as pd


@dataclass
class TestResult:
    test_id: str
    title: str
    objective: str
    method: str
    flagged: pd.DataFrame = field(default_factory=pd.DataFrame)
    notes: Optional[str] = None
    skipped: bool = False

    @property
    def count(self) -> int:
        return 0 if self.flagged is None else len(self.flagged)

    @property
    def conclusion(self) -> str:
        if self.skipped:
            return f"Test skipped — {self.notes or 'required data not available'}"
        n = self.count
        if n == 0:
            return "No exceptions found."
        return f"{n} potentially suspicious entr{'y' if n == 1 else 'ies'} flagged for review."


class LedgerTest:
    test_id: str = ""
    title: str = ""
    objective: str = ""
    method: str = ""

    # Logical column fields this test needs. Used to skip gracefully.
    requires: list = []

    def _skip(self, message: str) -> TestResult:
        return TestResult(self.test_id, self.title, self.objective, self.method,
                          notes=message, skipped=True)

    def _check_requirements(self, df: pd.DataFrame, cols: Dict[str, str]) -> Optional[str]:
        """Return error message if required columns missing, else None."""
        missing = []
        for req in self.requires:
            if req == "amount":
                if "_amount" not in df.columns:
                    missing.append("Amount")
            elif req == "date":
                if "_date" not in df.columns or df["_date"].isna().all():
                    missing.append("Date")
            elif req == "time":
                if "_time_hour" not in df.columns or df["_time_hour"].isna().all():
                    missing.append("Time of posting")
            else:
                if not cols.get(req):
                    missing.append(req.replace("_", " ").title())
        if missing:
            return f"Required columns not mapped: {', '.join(missing)}"
        return None

    def run(self, df: pd.DataFrame, cols: Dict[str, str], ctx: Dict[str, Any]) -> TestResult:
        err = self._check_requirements(df, cols)
        if err:
            return self._skip(err)
        return self._run(df, cols, ctx)

    def _run(self, df: pd.DataFrame, cols: Dict[str, str], ctx: Dict[str, Any]) -> TestResult:
        raise NotImplementedError
