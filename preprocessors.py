"""Normalize raw ledger data into analysis-ready form.
Handles amount formatting variants, date format variants, debit/credit merging."""

import pandas as pd
import numpy as np
import re


def clean_amount(series: pd.Series) -> pd.Series:
    """Normalize an amount column to float.
    Handles: currency symbols, thousand separators, parentheses negatives,
    European decimal format, leading/trailing whitespace."""
    s = series.astype(str).str.strip()

    # Remove currency symbols and codes
    s = s.str.replace(r"[$£€¥₨]", "", regex=True)
    s = s.str.replace(r"\b(AED|USD|GBP|EUR|PKR|INR|SAR|QAR|KWD|BHD|OMR|CAD|AUD|NZD)\b",
                      "", regex=True, flags=re.IGNORECASE)

    # Parentheses → negative: "(1,234.56)" → "-1,234.56"
    paren = s.str.match(r"^\s*\(.*\)\s*$")
    s = s.where(~paren, "-" + s.str.replace(r"[()]", "", regex=True))

    # Detect European format (comma as decimal separator): "1.234,56"
    # Heuristic: if there are both dots and commas, and the LAST separator is a comma,
    # it's European. Otherwise assume US format.
def _normalize(val: str) -> str:
    if not val or val.lower() in ("nan", "none", ""):
        return ""
        has_dot = "." in val
        has_comma = "," in val
        if has_dot and has_comma:
            if val.rfind(",") > val.rfind("."):
                # European: 1.234,56 → 1234.56
                return val.replace(".", "").replace(",", ".")
            else:
                # US: 1,234.56 → 1234.56
                return val.replace(",", "")
        elif has_comma and not has_dot:
            # Ambiguous: could be "1,234" (US thousands) or "1,56" (European decimal).
            # Only treat as decimal if exactly one comma with 1-3 digits after.
            parts = val.split(",")
            if len(parts) == 2 and 1 <= len(parts[1]) <= 2:
                return val.replace(",", ".")
            return val.replace(",", "")
        return val

    s = s.apply(_normalize)
    s = s.replace({"": np.nan, "nan": np.nan, "None": np.nan})
    return pd.to_numeric(s, errors="coerce")


def merge_debit_credit(df: pd.DataFrame, debit_col: str, credit_col: str,
                       new_col: str = "_amount") -> pd.DataFrame:
    """Combine separate Debit/Credit columns into a single signed amount.
    Convention: Debit = positive, Credit = negative."""
    out = df.copy()
    dr = clean_amount(out[debit_col]).fillna(0)
    cr = clean_amount(out[credit_col]).fillna(0)
    out[new_col] = dr - cr
    return out


def parse_dates(series: pd.Series, user_format: str = "auto") -> pd.Series:
    """Parse a date column robustly.
    user_format can be 'auto', 'DMY', 'MDY', 'YMD', or an explicit strftime pattern."""
    if user_format == "auto":
        # Try pandas auto-parser; fall back to dayfirst
        parsed = pd.to_datetime(series, errors="coerce", format="mixed", dayfirst=False)
        if parsed.isna().mean() > 0.3:
            parsed = pd.to_datetime(series, errors="coerce", format="mixed", dayfirst=True)
        return parsed
    if user_format == "DMY":
        return pd.to_datetime(series, errors="coerce", dayfirst=True, format="mixed")
    if user_format == "MDY":
        return pd.to_datetime(series, errors="coerce", dayfirst=False, format="mixed")
    if user_format == "YMD":
        return pd.to_datetime(series, errors="coerce", format="mixed")
    # Explicit strftime pattern
    return pd.to_datetime(series, errors="coerce", format=user_format)


def parse_times(series: pd.Series) -> pd.Series:
    """Parse a time-only or datetime column to extract hour component."""
    parsed = pd.to_datetime(series, errors="coerce", format="mixed")
    return parsed


def detect_subtotal_rows(df: pd.DataFrame) -> pd.Series:
    """Return boolean mask: True where the row looks like a subtotal/footer.
    Heuristic: most columns empty, one column contains 'total' or 'subtotal'."""
    non_null_counts = df.notna().sum(axis=1)
    has_total_keyword = df.astype(str).apply(
        lambda r: r.str.contains(r"\b(sub)?total\b|\bgrand\b", case=False, na=False).any(),
        axis=1,
    )
    too_few_values = non_null_counts <= max(2, len(df.columns) // 3)
    return has_total_keyword & too_few_values
