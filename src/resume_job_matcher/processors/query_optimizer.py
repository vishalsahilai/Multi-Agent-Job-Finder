from typing import Optional
from urllib.parse import urlencode, quote_plus

 # Job Board URL Builders 
 
def _google_jobs_url(query: str, location: str = "") -> str:
    q = f"{query} {location} jobs".strip()
    params = {"q": q, "ibp": "htl;jobs"}
    return f"https://www.google.com/search?{urlencode(params)}"
 
 
def _indeed_url(query: str, location: str = "") -> str:
    params = {"q": query, "l": location, "sort": "date", "fromage": "30"}
    # Remove empty params
    params = {k: v for k, v in params.items() if v}
    return f"https://www.indeed.com/jobs?{urlencode(params)}"
 
 
def _rozee_url(query: str, location: str = "") -> str:
    # Rozee.pk — Pakistan's top job board
    slug = query.lower().replace(" ", "-")
    if location:
        loc_slug = location.lower().replace(" ", "-")
        return f"https://www.rozee.pk/job/jsearch/q/{quote_plus(query)}/fc/1/fpv/{loc_slug}"
    return f"https://www.rozee.pk/job/jsearch/q/{quote_plus(query)}"
 
 
def _linkedin_url(query: str, location: str = "") -> str:
    params = {
        "keywords": query,
        "location": location,
        "f_TPR": "r2592000",   # last 30 days
        "sortBy": "DD",        # sort by date
    }
    params = {k: v for k, v in params.items() if v}
    return f"https://www.linkedin.com/jobs/search/?{urlencode(params)}"
 
 
def _glassdoor_url(query: str, location: str = "") -> str:
    params = {"sc.keyword": query, "locT": "C", "locName": location}
    params = {k: v for k, v in params.items() if v}
    return f"https://www.glassdoor.com/Job/jobs.htm?{urlencode(params)}"
 
 
def _mustakbil_url(query: str) -> str:
    # Mustakbil.com — another major Pakistan job board
    return f"https://mustakbil.com/jobs/?search={quote_plus(query)}"
 