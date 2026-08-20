import time
import random
import logging
from typing import Optional
from urllib.parse import urljoin, urlparse
 
import requests
from bs4 import BeautifulSoup
 
logger = logging.getLogger(__name__)

#  HTTP Config
 
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
 
REQUEST_TIMEOUT = 15       # seconds
DELAY_MIN = 1.5            # min delay between requests
DELAY_MAX = 3.5            # max delay between requests

#Board-Specific Job Link Extractors
 
def _extract_indeed(soup: BeautifulSoup, base_url: str) -> list:
    links = []
    for a in soup.select("a[href*='/rc/clk'], a[href*='viewjob'], a[data-jk]"):
        href = a.get("href", "")
        if href:
            full = urljoin("https://www.indeed.com", href)
            links.append(full)
    return links
 
 
def _extract_linkedin(soup: BeautifulSoup, base_url: str) -> list:
    links = []
    for a in soup.select("a.base-card__full-link, a[href*='/jobs/view/']"):
        href = a.get("href", "")
        if href and "/jobs/view/" in href:
            # Strip tracking params
            clean = href.split("?")[0]
            links.append(clean)
    return links
 
 
def _extract_rozee(soup: BeautifulSoup, base_url: str) -> list:
    links = []
    for a in soup.select("a[href*='/job/'], a.job-title-link, h3 a, h2 a"):
        href = a.get("href", "")
        if href and "/job/" in href:
            full = urljoin("https://www.rozee.pk", href)
            links.append(full)
    return links
 
 
def _extract_mustakbil(soup: BeautifulSoup, base_url: str) -> list:
    links = []
    for a in soup.select("a[href*='/job-detail/'], a[href*='/jobs/']"):
        href = a.get("href", "")
        if href:
            full = urljoin("https://mustakbil.com", href)
            links.append(full)
    return links
 
 
def _extract_glassdoor(soup: BeautifulSoup, base_url: str) -> list:
    links = []
    for a in soup.select("a[href*='job-listing'], a[data-test='job-link']"):
        href = a.get("href", "")
        if href:
            full = urljoin("https://www.glassdoor.com", href)
            links.append(full)
    return links
 
 
def _extract_google_jobs(soup: BeautifulSoup, base_url: str) -> list:
    """
    Google Jobs embeds listings — extract job title + company links.
    These link out to the actual job board pages.
    """
    links = []
    for a in soup.select("a[href*='//']"):
        href = a.get("href", "")
        # Google wraps with /url?q= redirect
        if "/url?q=" in href:
            actual = href.split("/url?q=")[1].split("&")[0]
            links.append(actual)
        elif href.startswith("http") and "google.com" not in href:
            links.append(href)
    return links


# ── Board Router ──────────────────────────────────────────────────────────────
 
BOARD_EXTRACTORS = {
    "indeed.com":     _extract_indeed,
    "linkedin.com":   _extract_linkedin,
    "rozee.pk":       _extract_rozee,
    "mustakbil.com":  _extract_mustakbil,
    "glassdoor.com":  _extract_glassdoor,
    "google.com":     _extract_google_jobs,
}
 
 
def _get_extractor(url: str):
    domain = urlparse(url).netloc.replace("www.", "")
    for key, fn in BOARD_EXTRACTORS.items():
        if key in domain:
            return fn
    return None
 