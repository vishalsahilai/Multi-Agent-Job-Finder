import re
import time
import random
import logging
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 15
DELAY_MIN = 1.0
DELAY_MAX = 2.5

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

#  Board-Specific Scrapers 

def _scrape_indeed(soup: BeautifulSoup) -> dict:
    return {
        "title":           _text(soup, ["h1.jobsearch-JobInfoHeader-title", "h1[data-testid='jobsearch-JobInfoHeader-title']"]),
        "company":         _text(soup, ["div[data-testid='inlineHeader-companyName'] a", "div.icl-u-lg-mr--sm a"]),
        "location":        _text(soup, ["div[data-testid='job-location']", "div.icl-u-xs-mt--xs"]),
        "date_posted":     _text(soup, ["span[data-testid='myJobsStateDate']", "p.jobsearch-HiringInsights-entry--bullet"]),
        "employment_type": _text(soup, ["span[data-testid='attribute_snippet_testid']"]),
        "description":     _text(soup, ["div#jobDescriptionText", "div.jobsearch-jobDescriptionText"]),
    }


def _scrape_linkedin(soup: BeautifulSoup) -> dict:
    return {
        "title":           _text(soup, ["h1.top-card-layout__title", "h1.t-24"]),
        "company":         _text(soup, ["a.topcard__org-name-link", "span.topcard__flavor a"]),
        "location":        _text(soup, ["span.topcard__flavor--bullet", "span.topcard__flavor:nth-of-type(2)"]),
        "date_posted":     _text(soup, ["span.posted-time-ago__text", "time"]),
        "employment_type": _text(soup, ["span.description__job-criteria-text:nth-of-type(1)"]),
        "description":     _text(soup, ["div.description__text", "div.show-more-less-html__markup"]),
    }


def _scrape_rozee(soup: BeautifulSoup) -> dict:
    return {
        "title":           _text(soup, ["h1.job-title", "h1.title", "h1"]),
        "company":         _text(soup, ["div.company-name a", "span.company-name", "a.comp-name"]),
        "location":        _text(soup, ["span.location", "div.job-location", "li.location"]),
        "date_posted":     _text(soup, ["span.date", "div.posted-date", "li.posted"]),
        "employment_type": _text(soup, ["span.job-type", "li.job-type"]),
        "description":     _text(soup, ["div.job-description", "div#job-description", "div.desc"]),
    }


def _scrape_mustakbil(soup: BeautifulSoup) -> dict:
    return {
        "title":           _text(soup, ["h1.job-title", "h1", "h2.job-title"]),
        "company":         _text(soup, ["span.company", "a.company-name", "div.company"]),
        "location":        _text(soup, ["span.location", "div.location"]),
        "date_posted":     _text(soup, ["span.date-posted", "div.date", "span.posted"]),
        "employment_type": _text(soup, ["span.job-type", "div.job-type"]),
        "description":     _text(soup, ["div.job-description", "div.description"]),
    }


def _scrape_glassdoor(soup: BeautifulSoup) -> dict:
    return {
        "title":           _text(soup, ["div[data-test='jobTitle']", "h1.job-title"]),
        "company":         _text(soup, ["div[data-test='employerName']", "span.employer-name"]),
        "location":        _text(soup, ["div[data-test='location']", "span.location"]),
        "date_posted":     _text(soup, ["div[data-test='job-age']", "span.date"]),
        "employment_type": _text(soup, ["span[data-test='job-type']"]),
        "description":     _text(soup, ["div[class*='JobDetails_jobDescription']", "div.desc"]),
    }


def _scrape_generic(soup: BeautifulSoup) -> dict:
    """Fallback scraper using common patterns across job boards."""
    return {
        "title":           _text(soup, ["h1", "h1.job-title", "h1.title", "[class*='job-title']", "[class*='jobTitle']"]),
        "company":         _text(soup, ["[class*='company']", "[class*='employer']", "[class*='org-name']"]),
        "location":        _text(soup, ["[class*='location']", "[class*='city']", "[class*='place']"]),
        "date_posted":     _text(soup, ["[class*='date']", "[class*='posted']", "time", "[datetime]"]),
        "employment_type": _text(soup, ["[class*='job-type']", "[class*='employment']", "[class*='work-type']"]),
        "description":     _text(soup, ["[class*='description']", "[class*='job-desc']", "[class*='details']", "article"]),
    }


#  Board Router 

BOARD_SCRAPERS = {
    "indeed.com":    _scrape_indeed,
    "linkedin.com":  _scrape_linkedin,
    "rozee.pk":      _scrape_rozee,
    "mustakbil.com": _scrape_mustakbil,
    "glassdoor.com": _scrape_glassdoor,
}


def _get_scraper(url: str):
    domain = urlparse(url).netloc.replace("www.", "").lower()
    for key, fn in BOARD_SCRAPERS.items():
        if key in domain:
            return fn
    return _scrape_generic


#  Helpers 

def _text(soup: BeautifulSoup, selectors: list) -> Optional[str]:
    """Try each selector in order, return first non-empty text found."""
    for sel in selectors:
        try:
            el = soup.select_one(sel)
            if el:
                text = el.get_text(separator=" ", strip=True)
                if text:
                    return text[:2000]  # cap description length
        except Exception:
            continue
    return None


def _clean_date(raw: Optional[str]) -> Optional[str]:
    """Light cleanup of raw date strings before Stage 8 normalizer."""
    if not raw:
        return None
    # Strip noise like "Posted", "Active", bullet chars
    cleaned = re.sub(r"^(posted|active|updated|listed)[:\s]*", "", raw, flags=re.IGNORECASE)
    return cleaned.strip() or None


def _clean_description(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    # Collapse whitespace
    cleaned = re.sub(r"\s+", " ", raw).strip()
    return cleaned[:3000]  # cap at 3000 chars for downstream processing


#  Static Fetcher (requests) 

def _fetch_static(url: str, session: requests.Session) -> Optional[BeautifulSoup]:
    try:
        r = session.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return BeautifulSoup(r.text, "lxml")
    except Exception as e:
        logger.debug(f"Static fetch failed for {url}: {e}")
        return None


#  Dynamic Fetcher (Playwright) 

def _fetch_dynamic(url: str) -> Optional[BeautifulSoup]:
    """
    Use Playwright headless browser for JS-rendered pages.
    Only called when static fetch returns no useful content.
    """
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers(HEADERS)
            page.goto(url, timeout=20000, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)   # wait for JS render
            html = page.content()
            browser.close()
            return BeautifulSoup(html, "lxml")
    except Exception as e:
        logger.debug(f"Playwright fetch failed for {url}: {e}")
        return None


def _needs_dynamic(soup: Optional[BeautifulSoup], scraper_fn) -> bool:
    """Check if static fetch returned useful content."""
    if not soup:
        return True
    result = scraper_fn(soup)
    # If we got no title and no description, page is likely JS-rendered
    return not result.get("title") and not result.get("description")


#  Single Job Scraper 

def scrape_job(url: str, board: str, query: str, session: requests.Session) -> dict:
    """Scrape a single job posting URL and return structured data."""
    base = {
        "job_url":         url,
        "board":           board,
        "query":           query,
        "title":           None,
        "company":         None,
        "location":        None,
        "date_posted_raw": None,
        "employment_type": None,
        "description":     None,
        "scrape_status":   "ok",
    }

    scraper_fn = _get_scraper(url)

    # Try static first
    soup = _fetch_static(url, session)

    # Fall back to Playwright if needed
    if _needs_dynamic(soup, scraper_fn):
        logger.debug(f"Static insufficient, trying Playwright: {url}")
        soup = _fetch_dynamic(url)

    if not soup:
        base["scrape_status"] = "failed"
        return base

    extracted = scraper_fn(soup)

    base.update({
        "title":           extracted.get("title"),
        "company":         extracted.get("company"),
        "location":        extracted.get("location"),
        "date_posted_raw": _clean_date(extracted.get("date_posted")),
        "employment_type": extracted.get("employment_type"),
        "description":     _clean_description(extracted.get("description")),
    })

    return base


#  Main Entry Point 

def scrape_jobs(filtered_urls: list) -> list:
    """
    Scrape all job posting URLs from Stage 6.

    Args:
        filtered_urls: List of dicts with keys: job_url, board, query

    Returns:
        List of scraped job dicts, skipping failed scrapes.
    """
    results = []
    session = requests.Session()
    total = len(filtered_urls)

    for i, item in enumerate(filtered_urls, 1):
        url   = item["job_url"]
        board = item["board"]
        query = item["query"]

        logger.info(f"[{i}/{total}] Scraping [{board}]: {url}")

        job = scrape_job(url, board, query, session)

        if job["scrape_status"] == "failed":
            logger.warning(f"  → Scrape failed, skipping")
        elif not job.get("title"):
            logger.warning(f"  → No title extracted, skipping")
        else:
            logger.info(f"  → '{job['title']}' at '{job['company']}'")
            results.append(job)

        time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

    logger.info(f"Scraper done: {len(results)} jobs extracted from {total} URLs")
    return results