import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

#  Blocked Domains (never job postings) 

BLOCKED_DOMAINS = {
    # Dev/tech content
    "github.com", "gitlab.com", "bitbucket.org",
    "stackoverflow.com", "stackexchange.com",
    "medium.com", "dev.to", "hashnode.dev", "substack.com",
    "geeksforgeeks.org", "tutorialspoint.com", "w3schools.com",
    "freecodecamp.org", "codecademy.com", "coursera.org",
    "udemy.com", "pluralsight.com", "edx.org", "khanacademy.org",
    # Docs & reference
    "docs.python.org", "readthedocs.io", "pypi.org",
    "npmjs.com", "developer.mozilla.org", "developer.android.com",
    "developer.apple.com", "learn.microsoft.com", "cloud.google.com",
    "docs.aws.amazon.com", "kubernetes.io", "docker.com",
    # News & blogs
    "techcrunch.com", "wired.com", "theverge.com", "arstechnica.com",
    "thenextweb.com", "zdnet.com", "venturebeat.com", "forbes.com",
    "bloomberg.com", "reuters.com", "bbc.com", "cnn.com",
    # Video
    "youtube.com", "youtu.be", "vimeo.com", "twitch.tv",
    # Social (non-job)
    "twitter.com", "x.com", "facebook.com", "instagram.com",
    "reddit.com", "quora.com", "pinterest.com",
    # Wiki / encyclopedia
    "wikipedia.org", "wikimedia.org",
    # Other
    "pastebin.com", "gist.github.com", "notion.so", "slack.com",
}

#  Allowed Job Board Domains (whitelist) 
ALLOWED_JOB_DOMAINS = {
    "linkedin.com",
    "indeed.com",
    "rozee.pk",
    "mustakbil.com",
    "glassdoor.com",
    "naukri.com",
    "monster.com",
    "ziprecruiter.com",
    "simplyhired.com",
    "careerbuilder.com",
    "jobs.google.com",
    "workcircle.com",
    "bayt.com",           # Middle East + Pakistan
    "gulftalent.com",
    "bestjobs.pk",
    "jobsinpakistan.com",
    "paperpk.com",
    "pk.mustakbil.com",
    "theladders.com",
    "wellfound.com",      # Startup jobs (formerly AngelList)
    "remoteok.com",
    "weworkremotely.com",
    "himalayas.app",
    "flexjobs.com",
}

#  Blocked URL Path Patterns 

BLOCKED_PATH_PATTERNS = [
    "/blog/", "/blogs/", "/news/", "/article/", "/articles/",
    "/tutorial/", "/tutorials/", "/guide/", "/guides/",
    "/learn/", "/course/", "/courses/", "/training/",
    "/docs/", "/documentation/", "/wiki/", "/faq/",
    "/forum/", "/community/", "/discussion/",
    "/pricing/", "/about/", "/contact/", "/login/", "/signup/",
    "/tag/", "/tags/", "/category/", "/categories/",
    "/search?", "/topic/",
]

#  Required Path Patterns (URL must contain one of these for job boards) 

JOB_PATH_SIGNALS = [
    "/job", "/jobs", "/career", "/careers", "/vacancy", "/vacancies",
    "/position", "/opening", "/work-with-us", "/join-us",
    "/employment", "/recruit", "/hiring", "/apply",
    "viewjob", "jobdetail", "job-detail", "job_detail",
    "/rc/clk",       # Indeed tracking
    "jk=",           # Indeed job key
    "/jobs/view/",   # LinkedIn
]


#  Filter Functions 

def _get_domain(url: str) -> str:
    try:
        parsed = urlparse(url)
        return parsed.netloc.replace("www.", "").lower()
    except Exception:
        return ""


def _is_blocked_domain(domain: str) -> bool:
    # Exact match or subdomain match
    for blocked in BLOCKED_DOMAINS:
        if domain == blocked or domain.endswith(f".{blocked}"):
            return True
    return False


def _is_allowed_job_domain(domain: str) -> bool:
    for allowed in ALLOWED_JOB_DOMAINS:
        if domain == allowed or domain.endswith(f".{allowed}"):
            return True
    return False


def _has_blocked_path(url: str) -> bool:
    url_lower = url.lower()
    return any(pattern in url_lower for pattern in BLOCKED_PATH_PATTERNS)


def _has_job_signal(url: str) -> bool:
    url_lower = url.lower()
    return any(signal in url_lower for signal in JOB_PATH_SIGNALS)


def _is_valid_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def filter_url(url: str) -> tuple:
    """
    Evaluate a single URL.

    Returns:
        (keep: bool, reason: str)
    """
    if not url or not _is_valid_url(url):
        return False, "invalid URL"

    domain = _get_domain(url)

    if _is_blocked_domain(domain):
        return False, f"blocked domain: {domain}"

    if _has_blocked_path(url):
        return False, "blocked path pattern"

    # If it's a known job board, trust it
    if _is_allowed_job_domain(domain):
        return True, "known job board"

    # Unknown domain — require a job signal in the path
    if _has_job_signal(url):
        return True, "job signal in URL"

    return False, f"no job signal, unknown domain: {domain}"


#  Main Entry Point 

def filter_urls(job_items: list) -> list:
    """
    Filter a list of job URL dicts from Stage 5.

    Args:
        job_items: List of dicts with keys: job_url, board, query

    Returns:
        Filtered list — only real job posting URLs kept.
    """
    kept = []
    removed = 0

    for item in job_items:
        url = item.get("job_url", "")
        keep, reason = filter_url(url)

        if keep:
            kept.append(item)
        else:
            removed += 1
            logger.debug(f"Removed [{reason}]: {url}")

    logger.info(f"URL filter: {len(kept)} kept, {removed} removed from {len(job_items)} total")
    return kept