"""
Stage 8: Date Normalizer + Date Range Filter
Converts raw date strings from Stage 7 into datetime objects.
Then filters jobs by user-specified From Date / To Date.
No LLM — pure Python using dateparser + regex.
"""

import re
import logging
from datetime import datetime, timedelta, date
from typing import Optional

logger = logging.getLogger(__name__)

# ── Relative Date Patterns ────────────────────────────────────────────────────
# Handles: "3 days ago", "posted yesterday", "2 hours ago", "just now", "1 week ago"

RELATIVE_PATTERNS = [
    (r"just\s*now|moments?\s*ago",                          lambda _: 0),
    (r"(\d+)\s*hours?\s*ago",                               lambda m: 0),       # same day
    (r"yesterday",                                          lambda _: 1),
    (r"(\d+)\s*days?\s*ago",                                lambda m: int(m.group(1))),
    (r"(\d+)\s*weeks?\s*ago",                               lambda m: int(m.group(1)) * 7),
    (r"(\d+)\s*months?\s*ago",                              lambda m: int(m.group(1)) * 30),
    (r"a\s*day\s*ago",                                      lambda _: 1),
    (r"a\s*week\s*ago",                                     lambda _: 7),
    (r"a\s*month\s*ago",                                    lambda _: 30),
    (r"(\d+)\+\s*days?\s*ago",                              lambda m: int(m.group(1))),  # "30+ days ago"
]


def _parse_relative(text: str) -> Optional[datetime]:
    text_lower = text.lower().strip()
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    for pattern, delta_fn in RELATIVE_PATTERNS:
        m = re.search(pattern, text_lower)
        if m:
            try:
                days_back = delta_fn(m)
                return today - timedelta(days=days_back)
            except Exception:
                continue
    return None


# ── Absolute Date Formats ─────────────────────────────────────────────────────

ABSOLUTE_FORMATS = [
    "%Y-%m-%d",          # 2026-08-10
    "%d-%m-%Y",          # 10-08-2026
    "%d/%m/%Y",          # 10/08/2026
    "%m/%d/%Y",          # 08/10/2026
    "%B %d, %Y",         # August 10, 2026
    "%b %d, %Y",         # Aug 10, 2026
    "%d %B %Y",          # 10 August 2026
    "%d %b %Y",          # 10 Aug 2026
    "%B %d %Y",          # August 10 2026
    "%b %d %Y",          # Aug 10 2026
    "%Y/%m/%d",          # 2026/08/10
    "%d.%m.%Y",          # 10.08.2026
    "%Y.%m.%d",          # 2026.08.10
]


def _parse_absolute(text: str) -> Optional[datetime]:
    text = text.strip()
    # Try to extract just the date portion if there's extra text
    date_pattern = re.search(
        r"\d{1,4}[-/.\s]\w+[-/.\s]\d{2,4}|\w+\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+\w+\s+\d{4}",
        text
    )
    candidates = [text]
    if date_pattern:
        candidates.insert(0, date_pattern.group(0).strip())

    for candidate in candidates:
        for fmt in ABSOLUTE_FORMATS:
            try:
                return datetime.strptime(candidate, fmt)
            except ValueError:
                continue
    return None


# ── Dateparser Fallback ───────────────────────────────────────────────────────

def _parse_with_dateparser(text: str) -> Optional[datetime]:
    try:
        import dateparser
        result = dateparser.parse(
            text,
            settings={
                "PREFER_DAY_OF_MONTH": "first",
                "RETURN_AS_TIMEZONE_AWARE": False,
                "PREFER_LOCALE_DATE_ORDER": False,
                "TO_TIMEZONE": "UTC",
            }
        )
        return result
    except Exception:
        return None


# ── Main Normalizer ───────────────────────────────────────────────────────────

def normalize_date(raw: Optional[str]) -> Optional[datetime]:
    """
    Convert any raw date string to a datetime object.

    Priority:
    1. Relative patterns (fastest, most common on job boards)
    2. Absolute format strptime (exact match)
    3. dateparser library (fuzzy fallback)

    Returns None if all methods fail.
    """
    if not raw or not isinstance(raw, str):
        return None

    raw = raw.strip()
    if not raw:
        return None

    # 1. Relative
    result = _parse_relative(raw)
    if result:
        return result

    # 2. Absolute
    result = _parse_absolute(raw)
    if result:
        return result

    # 3. dateparser fallback
    result = _parse_with_dateparser(raw)
    if result:
        # Sanity check — reject dates far in the future or ancient past
        now = datetime.now()
        if datetime(2000, 1, 1) <= result <= now + timedelta(days=1):
            return result

    return None


# ── Date Filter 

def filter_by_date(
    jobs: list,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> tuple:
    """
    Filter scraped jobs by date range.

    Args:
        jobs:      List of job dicts from Stage 7 (with date_posted_raw).
        from_date: Start date (inclusive). None = no lower bound.
        to_date:   End date (inclusive). None = no upper bound (defaults to today).

    Returns:
        (in_range: list, no_date: list)
        - in_range: Jobs with date within the specified range
        - no_date:  Jobs where date could not be parsed (shown separately in UI)
    """
    if to_date is None:
        to_date = datetime.now().date()

    in_range = []
    no_date = []

    for job in jobs:
        raw = job.get("date_posted_raw")
        parsed = normalize_date(raw)

        if parsed is None:
            # Can't determine date — keep separately
            job["date_posted"] = None
            job["date_display"] = "Date Not Available"
            no_date.append(job)
            continue

        job_date = parsed.date()
        job["date_posted"] = parsed
        job["date_display"] = parsed.strftime("%d %b %Y")   # e.g. "10 Aug 2026"

        # Apply filters
        if from_date and job_date < from_date:
            logger.debug(f"Date filter: removed (too old) — {job_date} | {job.get('title')}")
            continue

        if job_date > to_date:
            logger.debug(f"Date filter: removed (future date) — {job_date} | {job.get('title')}")
            continue

        in_range.append(job)

    logger.info(
        f"Date filter: {len(in_range)} in range, "
        f"{len(no_date)} no date, "
        f"{len(jobs) - len(in_range) - len(no_date)} removed"
    )

    return in_range, no_date