"""Smart column detection with dual-column (Debit/Credit) support."""

import re

# Logical field → list of regex patterns (tried in order)
PATTERNS = {
    "amount": [
        r"\b(net[\s_]*amount|amount|amt|value|total|balance|lc[\s_]*amount|local[\s_]*amount)\b",
    ],
    "debit": [
        r"\b(dr|debit|debits|debit[\s_]*amt|debit[\s_]*amount)\b",
    ],
    "credit": [
        r"\b(cr|credit|credits|credit[\s_]*amt|credit[\s_]*amount)\b",
    ],
    "date": [
        r"\b(posting[\s_]*date|doc[\s_\.]*date|document[\s_]*date|trans(action)?[\s_]*date|entry[\s_]*date|booking[\s_]*date|value[\s_]*date|date)\b",
    ],
    "account": [
        r"\b(account|acc|coa|nominal|gl)[\s_\.]*(code|no|number|id)?\b",
        r"\b(account[\s_]*code|acc[\s_]*code|nominal[\s_]*code|gl[\s_]*code)\b",
    ],
    "doc_no": [
        r"\b(doc[\s_\.]*no|doc[\s_]*number|document[\s_]*no|document[\s_]*number|ref(erence)?[\s_]*no|voucher|je[\s_]*no|journal[\s_]*no|seq(uence)?)\b",
    ],
    "description": [
        r"\b(description|narration|narrative|memo|particular|detail|desc|note|remark|text)s?\b",
        r"\bref(erence)?[\s_]*(ii|2|name|desc)\b",
    ],
    "user": [
        r"\b(posted[\s_]*by|post[\s_]*by|created[\s_]*by|entered[\s_]*by|user[\s_]*id|user|operator|employee|preparer)\b",
    ],
    "time": [
        r"\b(posting[\s_]*time|time[\s_]*of[\s_]*posting|posted[\s_]*at|timestamp|time)\b",
    ],
    "account_desc": [
        r"\b(account[\s_]*name|account[\s_]*desc|acc[\s_]*name|acc[\s_]*desc|nominal[\s_]*name|gl[\s_]*name)\b",
    ],
}


def auto_map(columns):
    """Returns {logical_name: column_name or None}.
    Each column is assigned to at most one logical field."""
    mapping = {}
    used = set()
    for logical, patterns in PATTERNS.items():
        match = None
        for col in columns:
            if col in used:
                continue
            col_norm = str(col).lower().strip()
            if any(re.search(p, col_norm, re.IGNORECASE) for p in patterns):
                match = col
                break
        mapping[logical] = match
        if match:
            used.add(match)
    return mapping


def has_amount_signal(mapping):
    """True if we have either a single amount column OR both debit+credit."""
    return bool(mapping.get("amount")) or (bool(mapping.get("debit")) and bool(mapping.get("credit")))
