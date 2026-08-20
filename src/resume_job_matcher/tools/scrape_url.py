from resume_job_matcher.agents.job_scraper_agent import scrape_job
import requests


def scrape_url(url: str, board: str = "unknown", query: str = "") -> dict:
    """Scrape a single job URL. Delegates to job_scraper_agent."""
    session = requests.Session()
    return scrape_job(url, board, query, session)