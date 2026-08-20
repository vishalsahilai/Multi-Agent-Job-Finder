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
 