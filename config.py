"""Configuration — country list, weekend presets, holiday fetcher.

Uses the `holidays` library (https://pypi.org/project/holidays/) which
covers 100+ countries and automatically handles moving religious dates
(Eid, Easter, Diwali, Chinese New Year, etc.).
"""

from datetime import date
from typing import List, Set

try:
    import holidays as _holidays_lib
    HOLIDAYS_AVAILABLE = True
except ImportError:
    HOLIDAYS_AVAILABLE = False


# ISO code → display name. Ordered for the UI dropdown.
# Full list available at https://python-holidays.readthedocs.io
COUNTRIES = {
    "GB": "United Kingdom",
    "US": "United States",
    "AE": "United Arab Emirates",
    "PK": "Pakistan",
    "IN": "India",
    "SA": "Saudi Arabia",
    "QA": "Qatar",
    "KW": "Kuwait",
    "BH": "Bahrain",
    "OM": "Oman",
    "CA": "Canada",
    "AU": "Australia",
    "NZ": "New Zealand",
    "IE": "Ireland",
    "ZA": "South Africa",
    "NG": "Nigeria",
    "KE": "Kenya",
    "EG": "Egypt",
    "SG": "Singapore",
    "MY": "Malaysia",
    "PH": "Philippines",
    "BD": "Bangladesh",
    "LK": "Sri Lanka",
    "ID": "Indonesia",
    "HK": "Hong Kong",
    "CN": "China",
    "JP": "Japan",
    "DE": "Germany",
    "FR": "France",
    "NL": "Netherlands",
    "ES": "Spain",
    "IT": "Italy",
    "CH": "Switzerland",
    "SE": "Sweden",
    "BR": "Brazil",
    "MX": "Mexico",
    "TR": "Turkey",
}

# Weekend presets: Monday=0, Tuesday=1, ..., Sunday=6
WEEKEND_PRESETS = {
    "Saturday + Sunday (UK, US, Europe, most of Asia)": [5, 6],
    "Friday + Saturday (UAE, Saudi pre-2022, most Gulf)": [4, 5],
    "Friday + Sunday (Brunei)": [4, 6],
    "Friday only (Iran)": [4],
    "Saturday only (Nepal, Israel)": [5],
    "Sunday only": [6],
    "No weekend (7-day operation)": [],
}


def get_holidays(country_code: str, years: List[int]) -> Set[date]:
    """Fetch holidays for a country across given years.
    Returns a set of date objects. Returns empty set if library not installed
    or country not supported."""
    if not HOLIDAYS_AVAILABLE:
        return set()
    try:
        hols = _holidays_lib.country_holidays(country_code, years=years)
        return set(hols.keys())
    except (KeyError, NotImplementedError, AttributeError):
        return set()


def holiday_names(country_code: str, years: List[int]) -> dict:
    """Returns {date: holiday_name} for display in the UI."""
    if not HOLIDAYS_AVAILABLE:
        return {}
    try:
        return dict(_holidays_lib.country_holidays(country_code, years=years))
    except (KeyError, NotImplementedError, AttributeError):
        return {}


# Suspicious keywords for the text-analysis test. User-editable in UI.
DEFAULT_SUSPICIOUS_WORDS = [
    "fraud", "error", "adjustment", "misstatement", "manipulation",
    "irregularity", "discrepancy", "override", "misreport", "conceal",
    "falsify", "alter", "misclassify", "corruption", "omission", "abuse",
    "deficiency", "understate", "overstate", "anomaly", "misconduct",
    "illegal", "unauthorized", "noncompliance", "wrong", "correct",
    "reversal", "void", "cancel", "delete", "fix", "restate", "backdated",
]
