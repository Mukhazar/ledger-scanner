"""Test 2 — Weekend and holiday postings."""

from .base import LedgerTest, TestResult


class WeekendHolidayTest(LedgerTest):
    test_id = "T02"
    title = "Postings on weekends and holidays"
    objective = "Identify entries posted on non-working days, which may indicate unusual activity."
    method = "Flag entries where posting date is a weekend (as configured) or public holiday."
    requires = ["date"]

    def _run(self, df, cols, ctx):
        weekend_days = ctx.get("weekend_days", [5, 6])
        all_holidays = ctx.get("holidays", set())  # set of date objects

        work = df.copy()
        work = work.dropna(subset=["_date"])

        wd = work["_date"].dt.weekday
        is_weekend = wd.isin(weekend_days)
        date_only = work["_date"].dt.date
        is_holiday = date_only.isin(all_holidays)

        flagged = work[is_weekend | is_holiday].copy()
        if not flagged.empty:
            flag_map = []
            for wknd, hol in zip(is_weekend[is_weekend | is_holiday],
                                  is_holiday[is_weekend | is_holiday]):
                if wknd and hol:
                    flag_map.append("Weekend + Holiday")
                elif wknd:
                    flag_map.append("Weekend")
                else:
                    flag_map.append("Holiday")
            flagged["Flag"] = flag_map

        return TestResult(self.test_id, self.title, self.objective, self.method, flagged=flagged)
