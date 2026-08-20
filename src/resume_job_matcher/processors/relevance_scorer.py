import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

#  Score Weights 

WEIGHTS = {
    "title_match":      30,   # Job title matches candidate role
    "skill_match":      20,   # Each required/key skill found in description
    "skill_cap":        60,   # Max points from skill matches (3 skills × 20)
    "keyword_match":    10,   # Each resume skill keyword found in description
    "keyword_cap":      30,   # Max points from keyword matches (3 × 10)
    "location_match":   10,   # Location matches
    "seniority_match":  10,   # Seniority level matches
    "employment_type":   5,   # Employment type matches
}

MAX_SCORE = (
    WEIGHTS["title_match"]
    + WEIGHTS["skill_cap"]
    + WEIGHTS["keyword_cap"]
    + WEIGHTS["location_match"]
    + WEIGHTS["seniority_match"]
    + WEIGHTS["employment_type"]
)  # = 145 points total → normalized to 100%

#  Seniority Signal Words 

SENIORITY_SIGNALS = {
    "Intern":    ["intern", "internship", "trainee", "graduate trainee"],
    "Junior":    ["junior", "jr.", "entry level", "entry-level", "associate", "fresher"],
    "Mid-Level": ["mid", "mid-level", "intermediate", "2+ years", "3+ years"],
    "Senior":    ["senior", "sr.", "5+ years", "6+ years", "7+ years"],
    "Lead":      ["lead", "staff", "principal", "architect", "head of", "tech lead"],
}

#  Employment Type Signal Words 

EMPLOYMENT_SIGNALS = {
    "Full-time": ["full-time", "full time", "permanent", "regular"],
    "Remote":    ["remote", "work from home", "wfh", "distributed", "anywhere"],
    "Hybrid":    ["hybrid", "flexible", "partially remote"],
    "On-site":   ["on-site", "onsite", "in-office", "in office", "on site"],
    "Contract":  ["contract", "freelance", "part-time", "part time"],
}


#  Helpers 

def _normalize(text: Optional[str]) -> str:
    if not text:
        return ""
    return text.lower().strip()


def _contains(haystack: str, needle: str) -> bool:
    """Word-boundary safe contains check."""
    return bool(re.search(r"\b" + re.escape(needle.lower()) + r"\b", haystack))


def _combined_text(job: dict) -> str:
    """Combine title + description + location for searching."""
    parts = [
        job.get("title", ""),
        job.get("description", ""),
        job.get("location", ""),
        job.get("employment_type", ""),
    ]
    return " ".join(p for p in parts if p).lower()


# ── Scoring Signals ───────────────────────────────────────────────────────────

def _score_title(job_title: str, candidate_role: str) -> int:
    """
    Check if candidate role keywords appear in the job title.
    Partial match also scores (e.g. 'Python' in 'Senior Python Developer').
    """
    if not job_title or not candidate_role:
        return 0

    job_t = _normalize(job_title)
    role_words = _normalize(candidate_role).split()

    # Full role match
    if _normalize(candidate_role) in job_t:
        return WEIGHTS["title_match"]

    # Partial — count matching words
    matched = sum(1 for w in role_words if len(w) > 2 and w in job_t)
    ratio = matched / max(len(role_words), 1)

    if ratio >= 0.75:
        return WEIGHTS["title_match"]
    elif ratio >= 0.5:
        return int(WEIGHTS["title_match"] * 0.6)
    elif ratio >= 0.25:
        return int(WEIGHTS["title_match"] * 0.3)
    return 0


def _score_skills(job_text: str, top_skills: list) -> int:
    """Score based on top skills from analyzer appearing in job text."""
    if not top_skills:
        return 0

    points = 0
    for skill in top_skills:
        if _contains(job_text, skill):
            points += WEIGHTS["skill_match"]
            if points >= WEIGHTS["skill_cap"]:
                break

    return min(points, WEIGHTS["skill_cap"])


def _score_keywords(job_text: str, all_skills: list) -> int:
    """Score based on any resume skill keywords appearing in job text."""
    if not all_skills:
        return 0

    points = 0
    for skill in all_skills:
        if _contains(job_text, skill):
            points += WEIGHTS["keyword_match"]
            if points >= WEIGHTS["keyword_cap"]:
                break

    return min(points, WEIGHTS["keyword_cap"])


def _score_location(job: dict, candidate_location: str) -> int:
    if not candidate_location:
        return 0

    job_loc = _normalize(job.get("location", ""))
    cand_loc = _normalize(candidate_location)

    # Remote jobs match any location
    if "remote" in job_loc:
        return WEIGHTS["location_match"]

    if cand_loc and cand_loc in job_loc:
        return WEIGHTS["location_match"]

    # Partial — city name in location
    cand_words = cand_loc.split()
    if any(w in job_loc for w in cand_words if len(w) > 3):
        return int(WEIGHTS["location_match"] * 0.5)

    return 0


def _score_seniority(job_text: str, seniority: str) -> int:
    if not seniority:
        return 0

    signals = SENIORITY_SIGNALS.get(seniority, [])
    for signal in signals:
        if signal in job_text:
            return WEIGHTS["seniority_match"]
    return 0


def _score_employment_type(job: dict, preferred_type: Optional[str]) -> int:
    if not preferred_type:
        return WEIGHTS["employment_type"]   # no preference = always matches

    job_text = _normalize(job.get("employment_type", "") + " " + job.get("description", "")[:500])
    signals = EMPLOYMENT_SIGNALS.get(preferred_type, [])

    for signal in signals:
        if signal in job_text:
            return WEIGHTS["employment_type"]
    return 0


#  Main Entry Point 

def score_jobs(
    jobs: list,
    candidate_role: str,
    top_skills: list,
    all_skills: list,
    candidate_location: str,
    seniority: str,
    employment_type: Optional[str] = None,
) -> list:
    scored = []

    for job in jobs:
        job_text = _combined_text(job)
        job_title = _normalize(job.get("title", ""))

        title_pts      = _score_title(job_title, candidate_role)
        skill_pts      = _score_skills(job_text, top_skills)
        keyword_pts    = _score_keywords(job_text, all_skills)
        location_pts   = _score_location(job, candidate_location)
        seniority_pts  = _score_seniority(job_text, seniority)
        emp_type_pts   = _score_employment_type(job, employment_type)

        total = title_pts + skill_pts + keyword_pts + location_pts + seniority_pts + emp_type_pts
        percent = round(min((total / MAX_SCORE) * 100, 100), 1)

        job["match_score"]   = total
        job["match_percent"] = percent
        job["score_breakdown"] = {
            "title_match":      title_pts,
            "skill_match":      skill_pts,
            "keyword_match":    keyword_pts,
            "location_match":   location_pts,
            "seniority_match":  seniority_pts,
            "employment_type":  emp_type_pts,
        }

        scored.append(job)

    # Sort by match_percent descending, then by date (newest first) as tiebreaker
    scored.sort(
        key=lambda j: (
            -j["match_percent"],
            -(j["date_posted"].timestamp() if j.get("date_posted") else 0),
        )
    )

    logger.info(f"Scored {len(scored)} jobs | Top match: {scored[0]['match_percent']}% — '{scored[0].get('title')}'" if scored else "No jobs to score")
    return scored