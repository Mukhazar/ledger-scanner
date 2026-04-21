"""File loading — xlsx, xls, csv, tsv.
Handles: multi-sheet Excel, encoding detection, header row detection, messy data."""

import pandas as pd
from io import BytesIO
from typing import Optional, List


def list_sheets(uploaded_file) -> List[str]:
    """For xlsx/xls, return sheet names. For csv/tsv, return ['(single sheet)']."""
    name = uploaded_file.name.lower()
    if name.endswith((".xlsx", ".xls", ".xlsm")):
        uploaded_file.seek(0)
        xl = pd.ExcelFile(uploaded_file)
        return xl.sheet_names
    return ["(single sheet)"]


def load_sheet(uploaded_file, sheet_name: Optional[str] = None, header_row: int = 0) -> pd.DataFrame:
    """Load a specific sheet/file into a DataFrame.
    header_row is 0-indexed (0 = first row is headers)."""
    uploaded_file.seek(0)
    name = uploaded_file.name.lower()

    if name.endswith((".xlsx", ".xls", ".xlsm")):
        df = pd.read_excel(uploaded_file, sheet_name=sheet_name or 0, header=header_row, dtype=str)
    elif name.endswith(".tsv"):
        df = _read_text(uploaded_file, sep="\t", header_row=header_row)
    else:  # .csv or anything else — try CSV
        df = _read_text(uploaded_file, sep=",", header_row=header_row)

    # Drop fully empty rows and columns
    df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
    # Strip column names
    df.columns = [str(c).strip() for c in df.columns]
    # Reset index
    df = df.reset_index(drop=True)
    return df


def _read_text(uploaded_file, sep: str, header_row: int) -> pd.DataFrame:
    """Read CSV/TSV with encoding fallback."""
    raw = uploaded_file.read()
    if isinstance(raw, str):
        raw = raw.encode("utf-8")

    for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            return pd.read_csv(BytesIO(raw), sep=sep, header=header_row, dtype=str, encoding=encoding)
        except (UnicodeDecodeError, pd.errors.ParserError):
            continue
    # Last resort — ignore errors
    return pd.read_csv(BytesIO(raw), sep=sep, header=header_row, dtype=str,
                       encoding="utf-8", encoding_errors="ignore")


def preview_rows(uploaded_file, sheet_name: Optional[str] = None, n: int = 10) -> pd.DataFrame:
    """First N rows with NO header assumption — for header-row detection UI."""
    uploaded_file.seek(0)
    name = uploaded_file.name.lower()
    if name.endswith((".xlsx", ".xls", ".xlsm")):
        return pd.read_excel(uploaded_file, sheet_name=sheet_name or 0, header=None, nrows=n, dtype=str)
    return _read_text(uploaded_file, sep=("\t" if name.endswith(".tsv") else ","), header_row=None).head(n)
