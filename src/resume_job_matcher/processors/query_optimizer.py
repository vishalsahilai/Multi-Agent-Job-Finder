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

#  Query Enhancer 
 
def _enhance_query(
    base_query: str,
    top_skills: list,
    location: str,
    seniority: str,
) -> str:
    """
    Append location and key skills to base query to make it more targeted.
    Example: 'Python Developer' → 'Python Developer Django FastAPI Karachi'
    """
    parts = [base_query.strip()]
 
    # Add up to 2 top skills not already in query
    query_lower = base_query.lower()
    added_skills = 0
    for skill in top_skills:
        if skill.lower() not in query_lower and added_skills < 2:
            parts.append(skill)
            added_skills += 1
 
    # Add location if not already present
    if location and location.lower() not in query_lower:
        parts.append(location)
 
    return " ".join(parts)

#  Seniority Filter Map 
 
SENIORITY_TERMS = {
    "Intern":     ["intern", "internship", "trainee"],
    "Junior":     ["junior", "entry level", "associate", "jr"],
    "Mid-Level":  [],   # no modifier — keep query clean
    "Senior":     ["senior", "sr"],
    "Lead":       ["lead", "staff", "principal"],
}
 
 
def _add_seniority(query: str, seniority: str) -> str:
    terms = SENIORITY_TERMS.get(seniority, [])
    if not terms:
        return query
    term = terms[0]
    # Only prepend if not already in query
    if term.lower() not in query.lower():
        return f"{term} {query}"
    return query

 
#  Main Entry Point
 
def optimize_queries(
    search_queries: list,
    top_skills: list,
    location: str,
    seniority: str,
    employment_type: Optional[str] = None,
) -> list:
    results = []
    seen_urls = set()
 
    for raw_query in search_queries:
        # Step 1: Enhance with skills + location
        enhanced = _enhance_query(raw_query, top_skills, location, seniority)
 
        # Step 2: Add seniority prefix
        enhanced = _add_seniority(enhanced, seniority)
 
        # Step 3: Add employment type if specified
        if employment_type and employment_type.lower() == "remote":
            if "remote" not in enhanced.lower():
                enhanced = f"{enhanced} remote"
 
        # Step 4: Build URLs for each job board
        board_urls = [
            ("Google Jobs",  _google_jobs_url(enhanced, location)),
            ("Indeed",       _indeed_url(enhanced, location)),
            ("LinkedIn",     _linkedin_url(enhanced, location)),
            ("Rozee.pk",     _rozee_url(enhanced, location)),
            ("Mustakbil",    _mustakbil_url(enhanced)),
            ("Glassdoor",    _glassdoor_url(enhanced, location)),
        ]
 
        for board, url in board_urls:
            if url not in seen_urls:
                seen_urls.add(url)
                results.append({
                    "query": enhanced,
                    "board": board,
                    "url":   url,
                })
 
    return results