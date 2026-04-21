"""Ledger Scanner — production Streamlit app.
Run:  streamlit run app.py
"""

from datetime import date, datetime
import pandas as pd
import streamlit as st

from config import (
    COUNTRIES, WEEKEND_PRESETS, DEFAULT_SUSPICIOUS_WORDS,
    get_holidays, holiday_names, HOLIDAYS_AVAILABLE,
)
from data_loader import list_sheets, load_sheet, preview_rows
from preprocessors import clean_amount, merge_debit_credit, parse_dates, parse_times
from column_mapper import auto_map, has_amount_signal, PATTERNS

from tests.round_entries import RoundEntriesTest
from tests.weekend_holiday import WeekendHolidayTest
from tests.odd_hours import OddHoursTest
from tests.monthly_totals import MonthlyTotalsTest
from tests.reversed_entries import ReversedEntriesTest
from tests.journal_gaps import JournalGapsTest
from tests.revenue_debits import RevenueDebitsTest
from tests.cross_account import PrepaymentVsBankTest, AccrualVsBankTest, BankVsPnlTest
from tests.postings_by_user import PostingsByUserTest
from tests.user_key_accounts import UserKeyAccountsTest
from tests.duplicates import DuplicatesTest
from tests.suspicious_words import SuspiciousWordsTest
from report_builder import build_report


ALL_TESTS = [
    RoundEntriesTest(), WeekendHolidayTest(), OddHoursTest(), MonthlyTotalsTest(),
    ReversedEntriesTest(), JournalGapsTest(), RevenueDebitsTest(),
    PrepaymentVsBankTest(), AccrualVsBankTest(), BankVsPnlTest(),
    PostingsByUserTest(), UserKeyAccountsTest(), DuplicatesTest(), SuspiciousWordsTest(),
]


st.set_page_config(page_title="Ledger Scanner", page_icon="🔎", layout="wide")
st.title("🔎 Ledger Scanner")
st.caption("Forensic journal entry testing. Upload a general ledger, get a findings report.")

if not HOLIDAYS_AVAILABLE:
    st.warning("The `holidays` Python package is not installed. Run `pip install holidays` to enable automatic holiday detection.")


# ============================================================
# SIDEBAR — engagement context
# ============================================================
with st.sidebar:
    st.header("1. Engagement details")
    client_name = st.text_input("Client name", value="Client Ltd.")
    period_from = st.date_input("Period from", value=date(date.today().year - 1, 1, 1))
    period_to = st.date_input("Period to", value=date(date.today().year - 1, 12, 31))
    client_period = f"{period_from.strftime('%d %b %Y')} – {period_to.strftime('%d %b %Y')}"

    st.divider()
    st.header("2. Jurisdiction")

    country_code = st.selectbox(
        "Country",
        options=list(COUNTRIES.keys()),
        format_func=lambda c: f"{COUNTRIES[c]} ({c})",
        index=0,
    )
    years_needed = list(range(period_from.year, period_to.year + 1))
    auto_hols = get_holidays(country_code, years_needed)
    auto_hol_names = holiday_names(country_code, years_needed)

    weekend_label = st.selectbox("Weekend days", options=list(WEEKEND_PRESETS.keys()), index=0)
    weekend_days = WEEKEND_PRESETS[weekend_label]

    with st.expander(f"Public holidays detected ({len(auto_hols)})"):
        if auto_hols:
            hol_df = pd.DataFrame([
                {"Date": d.strftime("%Y-%m-%d"), "Day": d.strftime("%A"), "Holiday": auto_hol_names.get(d, "")}
                for d in sorted(auto_hols)
            ])
            st.dataframe(hol_df, hide_index=True, use_container_width=True)
        else:
            st.info("No holidays loaded. Install `holidays` or add custom dates below.")

    custom_holidays_text = st.text_area(
        "Custom holidays (one date per line, YYYY-MM-DD)",
        value="",
        help="Client-specific non-working days. E.g. internal shutdowns, religious days not in the default list.",
        height=100,
    )
    custom_holidays = set()
    for line in custom_holidays_text.strip().split("\n"):
        line = line.strip()
        if line:
            try:
                custom_holidays.add(datetime.strptime(line, "%Y-%m-%d").date())
            except ValueError:
                st.warning(f"Could not parse holiday date: {line}")

    all_holidays = auto_hols | custom_holidays

    st.divider()
    st.header("3. Test configuration")
    odd_start = st.slider("Odd-hours window START", 0, 23, 19, help="Hour of day when 'after hours' begins")
    odd_end = st.slider("Odd-hours window END", 0, 23, 8, help="Hour of day when business hours resume")

    with st.expander("Suspicious keywords (edit list)"):
        sus_text = st.text_area(
            "One word per line",
            value="\n".join(DEFAULT_SUSPICIOUS_WORDS),
            height=200,
        )
        suspicious_words = [w.strip() for w in sus_text.split("\n") if w.strip()]


# ============================================================
# MAIN AREA — step-by-step flow
# ============================================================
st.header("Step 1 — Upload the general ledger")
uploaded = st.file_uploader("", type=["xlsx", "xls", "xlsm", "csv", "tsv"])

if uploaded is None:
    st.info("Accepts xlsx, xls, xlsm, csv, tsv. A sample CSV `sample_ledger.csv` is included in the project folder.")
    st.stop()

# Sheet selection for Excel files
st.header("Step 2 — Choose sheet and header row")
sheets = list_sheets(uploaded)
sheet_col, header_col = st.columns(2)
with sheet_col:
    sheet_choice = st.selectbox("Sheet", sheets)
with header_col:
    header_row = st.number_input("Header row (0 = first row contains column names)", min_value=0, max_value=20, value=0, step=1)

with st.expander("Preview first 10 rows (raw, no header applied)"):
    st.dataframe(preview_rows(uploaded, sheet_name=sheet_choice if sheet_choice != "(single sheet)" else None),
                 use_container_width=True)

# Load the actual data
try:
    df_raw = load_sheet(uploaded, sheet_name=sheet_choice if sheet_choice != "(single sheet)" else None,
                        header_row=int(header_row))
except Exception as e:
    st.error(f"Could not load file: {e}")
    st.stop()

st.success(f"Loaded {len(df_raw):,} rows × {len(df_raw.columns)} columns")
with st.expander("Preview loaded data (first 10 rows)"):
    st.dataframe(df_raw.head(10), use_container_width=True)


# ============================================================
st.header("Step 3 — Map columns")
auto = auto_map(df_raw.columns)
col_choices = ["— not in this ledger —"] + list(df_raw.columns)


def _col_picker(field_name, label, help_text=None):
    default = auto.get(field_name)
    idx = col_choices.index(default) if default in col_choices else 0
    sel = st.selectbox(label, col_choices, index=idx, key=f"map_{field_name}", help=help_text)
    return None if sel == "— not in this ledger —" else sel


st.caption("Auto-detected where possible. Override any dropdown if incorrect.")

amount_mode = st.radio(
    "Amount structure",
    ["Single signed amount column", "Separate Debit and Credit columns"],
    horizontal=True,
    index=0 if auto.get("amount") and not (auto.get("debit") and auto.get("credit")) else 1
    if (auto.get("debit") and auto.get("credit")) else 0,
)

cols_ui_top = st.columns(3)
with cols_ui_top[0]:
    if amount_mode == "Single signed amount column":
        amount_col = _col_picker("amount", "Amount")
        debit_col = credit_col = None
    else:
        amount_col = None
        debit_col = _col_picker("debit", "Debit")
        credit_col = _col_picker("credit", "Credit")
with cols_ui_top[1]:
    date_col = _col_picker("date", "Date of posting")
    date_format = st.selectbox(
        "Date format",
        ["auto", "DMY (31/12/2024)", "MDY (12/31/2024)", "YMD (2024-12-31)"],
        index=0,
    )
    date_fmt_map = {"auto": "auto", "DMY (31/12/2024)": "DMY",
                    "MDY (12/31/2024)": "MDY", "YMD (2024-12-31)": "YMD"}
with cols_ui_top[2]:
    doc_col = _col_picker("doc_no", "Document / JE number")

cols_ui_bot = st.columns(4)
with cols_ui_bot[0]:
    desc_col = _col_picker("description", "Description / narration")
with cols_ui_bot[1]:
    user_col = _col_picker("user", "Posted by (user)")
with cols_ui_bot[2]:
    time_col = _col_picker("time", "Time of posting")
with cols_ui_bot[3]:
    acc_col = _col_picker("account", "Account code")

cols_map = {
    "amount": amount_col, "debit": debit_col, "credit": credit_col,
    "date": date_col, "doc_no": doc_col, "description": desc_col,
    "user": user_col, "time": time_col, "account": acc_col,
}


# ============================================================
# Preprocess the dataframe (amount, date, time normalization)
# ============================================================
df = df_raw.copy()

# Normalize amount
if amount_mode == "Single signed amount column" and amount_col:
    df["_amount"] = clean_amount(df[amount_col])
elif debit_col and credit_col:
    df = merge_debit_credit(df, debit_col, credit_col, new_col="_amount")
    df["_amount"] = clean_amount(df["_amount"].astype(str))

# Normalize date
if date_col:
    df["_date"] = parse_dates(df[date_col], user_format=date_fmt_map.get(date_format, "auto"))

# Normalize time
if time_col:
    parsed_time = parse_times(df[time_col])
    df["_time_hour"] = parsed_time.dt.hour

# Drop rows where date is outside the engagement period (optional, with warning)
if "_date" in df.columns:
    in_period = df["_date"].between(pd.Timestamp(period_from), pd.Timestamp(period_to), inclusive="both")
    out_count = int((~in_period & df["_date"].notna()).sum())
    if out_count > 0:
        st.info(f"{out_count} row(s) have dates outside the engagement period {period_from} to {period_to}. They will still be analysed but appear in flags.")


# ============================================================
st.header("Step 4 — Account classification (optional, required for some tests)")
st.caption("Select which account codes fall into each category. Tests 7–10 and 12 require this. Use the search/multi-select. You can skip — those tests will be marked 'skipped' in the report.")

if acc_col:
    unique_accounts = sorted(df_raw[acc_col].dropna().astype(str).unique().tolist())
    unique_descs = []
    if "account_desc" in cols_map and cols_map.get("account_desc"):
        unique_descs = df_raw[[acc_col, cols_map["account_desc"]]].dropna().drop_duplicates().values.tolist()

    with st.expander(f"{len(unique_accounts)} unique account codes found — click to classify", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            bank_codes = st.multiselect("Bank accounts", unique_accounts, key="bank")
            prepayment_codes = st.multiselect("Prepayment accounts", unique_accounts, key="prep")
        with c2:
            accrual_codes = st.multiselect("Accrual accounts", unique_accounts, key="accr")
            revenue_codes = st.multiselect("Revenue accounts", unique_accounts, key="rev")
        with c3:
            pnl_codes = st.multiselect("P&L accounts (all)", unique_accounts, key="pnl")
            key_account_codes = st.multiselect("Key / sensitive accounts (suspense, intercompany, etc.)", unique_accounts, key="keyacc")
else:
    bank_codes = prepayment_codes = accrual_codes = revenue_codes = pnl_codes = key_account_codes = []
    st.info("Map an Account column above to enable classification.")


# ============================================================
st.header("Step 5 — Select which tests to run")
with st.expander("All 14 tests (default: all enabled)", expanded=False):
    test_enable = {}
    cols_tests = st.columns(2)
    for i, t in enumerate(ALL_TESTS):
        with cols_tests[i % 2]:
            test_enable[t.test_id] = st.checkbox(f"{t.test_id} — {t.title}", value=True, key=f"enable_{t.test_id}")


# ============================================================
st.header("Step 6 — Run")
if st.button("Run forensic tests", type="primary", use_container_width=True):

    ctx = {
        "country_name": COUNTRIES.get(country_code, country_code),
        "country_code": country_code,
        "years": years_needed,
        "weekend_days": weekend_days,
        "weekend_label": weekend_label,
        "holidays": all_holidays,
        "custom_holidays": custom_holidays,
        "odd_hours_start": odd_start,
        "odd_hours_end": odd_end,
        "bank_codes": bank_codes,
        "prepayment_codes": prepayment_codes,
        "accrual_codes": accrual_codes,
        "revenue_codes": revenue_codes,
        "pnl_codes": pnl_codes,
        "key_account_codes": key_account_codes,
        "suspicious_words": suspicious_words,
    }

    results = []
    progress = st.progress(0.0, text="Running tests...")
    selected = [t for t in ALL_TESTS if test_enable.get(t.test_id, True)]

    for i, test in enumerate(selected):
        try:
            result = test.run(df, cols_map, ctx)
        except Exception as e:
            from tests.base import TestResult
            result = TestResult(test.test_id, test.title, test.objective, test.method,
                                notes=f"Error: {type(e).__name__}: {e}", skipped=True)
        results.append(result)
        progress.progress((i + 1) / len(selected), text=f"Completed: {test.title}")

    progress.empty()

    # ---- Summary ----
    st.subheader("Findings summary")
    summary_rows = []
    for r in results:
        summary_rows.append({
            "Test ID": r.test_id,
            "Test": r.title,
            "Status": "Skipped" if r.skipped else "Run",
            "Exceptions": "—" if r.skipped else r.count,
            "Note": r.notes or "",
        })
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

    # ---- Build and offer report ----
    st.subheader("Download")
    report_bytes = build_report(client_name, client_period, results, ctx=ctx, cols=cols_map)
    safe_name = "".join(c for c in client_name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
    st.download_button(
        "⬇ Download full Excel report",
        data=report_bytes,
        file_name=f"{safe_name}_JE_Testing_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True,
    )

    # ---- Preview each test ----
    with st.expander("Preview findings by test"):
        for r in results:
            st.markdown(f"### {r.test_id} — {r.title}")
            st.write(r.conclusion)
            if not r.skipped and r.flagged is not None and not r.flagged.empty:
                st.dataframe(r.flagged.head(50), use_container_width=True)
            st.divider()
