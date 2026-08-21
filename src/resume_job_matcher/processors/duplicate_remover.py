"""
Stage 9: Duplicate Remover
Removes duplicate job postings using two methods:
1. URL normalization — same job posted on same board
2. Fuzzy title + company matching — same job posted on multiple boards
No LLM — Python set operations + rapidfuzz.
"""

import re
import logging
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from rapidfuzz import fuzz

logger = logging.getLogger(__name__)

# Similarity threshold — above this = considered duplicate (0-100)
FUZZY_THRESHOLD = 85


# ── URL Normalizer ────────────────────────────────────────────────────────────

# UTM and tracking params to strip
STRIP_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "ref", "referer", "referrer", "source", "src",
    "trk", "trackingId", "tracking",          # LinkedIn
    "from", "fromjk", "advn", "adid",          # Indeed
    "salchk", "spon", "tk",
    "cmp", "cmpid",
    "fbclid", "gclid", "msclkid",
    "hl", "gl",
}


def _normalize_url(url: str) -> str:
    """
    Strip tracking params, normalize scheme/case, remove trailing slash.
    Returns a canonical URL string for deduplication.
    """
    try:
        parsed = urlparse(url.strip().lower())

        # Normalize scheme to https
        scheme = "https"

        # Strip www.
        netloc = parsed.netloc.replace("www.", "")

        # Clean query params
        raw_params = parse_qs(parsed.query, keep_blank_values=False)
        clean_params = {
            k: v for k, v in raw_params.items()
            if k.lower() not in STRIP_PARAMS
        }
        clean_query = urlencode(sorted(clean_params.items()), doseq=True)

        # Remove trailing slash from path
        path = parsed.path.rstrip("/")

        # Remove fragment (#)
        canonical = urlunparse((scheme, netloc, path, "", clean_query, ""))
        return canonical

    except Exception:
        return url.strip().lower()


# ── Text Normalizer (for fuzzy matching) ─────────────────────────────────────

def _normalize_text(text: str) -> str:
    """Lowercase, remove punctuation, collapse whitespace."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _make_fingerprint(title: str, company: str) -> str:
    """Build a combined string for fuzzy comparison."""
    t = _normalize_text(title or "")
    c = _normalize_text(company or "")
    return f"{t} {c}".strip()


# ── Dedup Logic ───────────────────────────────────────────────────────────────

def _is_fuzzy_duplicate(fingerprint: str, seen_fingerprints: list) -> bool:
    """
    Check if fingerprint is too similar to any already-seen fingerprint.
    Uses token_sort_ratio to handle word order differences.
    e.g. "python developer django" vs "django python developer" → match
    """
    for seen in seen_fingerprints:
        score = fuzz.token_sort_ratio(fingerprint, seen)
        if score >= FUZZY_THRESHOLD:
            return True
    return False


# ── Main Entry Point ──────────────────────────────────────────────────────────

def remove_duplicates(jobs: list) -> list:
    """
    Remove duplicate job postings from the combined list.

    Pass 1 — URL dedup: exact match after normalization.
    Pass 2 — Fuzzy dedup: title + company similarity across boards.

    Args:
        jobs: Combined list of job dicts (in_range + no_date from Stage 8).

    Returns:
        Deduplicated list, preserving first occurrence.
    """
    # ── Pass 1: URL dedup ─────────────────────────────────────────────────────
    seen_urls = set()
    after_url_dedup = []

    for job in jobs:
        norm = _normalize_url(job.get("job_url", ""))
        if norm and norm not in seen_urls:
            seen_urls.add(norm)
            after_url_dedup.append(job)
        else:
            logger.debug(f"URL duplicate removed: {job.get('job_url')}")

    url_removed = len(jobs) - len(after_url_dedup)
    logger.info(f"Pass 1 (URL dedup): removed {url_removed}, kept {len(after_url_dedup)}")

    # ── Pass 2: Fuzzy title + company dedup ──────────────────────────────────
    seen_fingerprints = []
    after_fuzzy_dedup = []

    for job in after_url_dedup:
        fp = _make_fingerprint(job.get("title", ""), job.get("company", ""))

        if not fp.strip():
            # No title or company — can't fingerprint, keep it
            after_fuzzy_dedup.append(job)
            continue

        if _is_fuzzy_duplicate(fp, seen_fingerprints):
            logger.debug(f"Fuzzy duplicate removed: '{job.get('title')}' @ '{job.get('company')}'")
        else:
            seen_fingerprints.append(fp)
            after_fuzzy_dedup.append(job)

    fuzzy_removed = len(after_url_dedup) - len(after_fuzzy_dedup)
    logger.info(f"Pass 2 (fuzzy dedup): removed {fuzzy_removed}, kept {len(after_fuzzy_dedup)}")
    logger.info(f"Total removed: {len(jobs) - len(after_fuzzy_dedup)} | Final count: {len(after_fuzzy_dedup)}")

    return after_fuzzy_dedup