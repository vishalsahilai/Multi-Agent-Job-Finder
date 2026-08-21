import logging
from datetime import date
from typing import Optional, Callable

from src.resume_job_matcher.tools.resume_reader import read_resume
from src.resume_job_matcher.processors.keyword_extractor import extract_keywords
from src.resume_job_matcher.chains.analyzer import analyze_resume
from src.resume_job_matcher.processors.query_optimizer import optimize_queries
from src.resume_job_matcher.agents.job_search_agent import search_jobs
from src.resume_job_matcher.processors.url_filter import filter_urls
from src.resume_job_matcher.agents.job_scraper_agent import scrape_jobs
from src.resume_job_matcher.processors.date_normalizer import filter_by_date
from src.resume_job_matcher.processors.duplicate_remover import remove_duplicates
from src.resume_job_matcher.processors.relevance_scorer import score_jobs

logger = logging.getLogger(__name__)


#  Progress Reporter 

def _noop(step: int, total: int, message: str):
    """Default no-op progress callback."""
    logger.info(f"[{step}/{total}] {message}")


#  Pipeline 

TOTAL_STEPS = 10


def run_pipeline(
    file: bytes,
    filename: str,
    gemini_api_key: str,
    location: str = "",
    employment_type: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    max_results: int = 50,
    progress_callback: Optional[Callable] = None,
) -> dict:
    cb = progress_callback or _noop
    stats = {}

    #  Stage 1: Read Resume 
    cb(1, TOTAL_STEPS, "Reading resume...")
    resume = read_resume(file, filename)

    if resume["error"]:
        return {"status": "error", "error": resume["error"], "candidate": {}, "jobs": [], "no_date_jobs": [], "stats": {}}

    stats["resume_chars"] = resume["char_count"]
    stats["resume_words"] = resume["word_count"]
    stats["resume_format"] = resume["format"]
    logger.info(f"Stage 1 done: {resume['word_count']} words, format={resume['format']}")

    #  Stage 2: Extract Keywords 
    cb(2, TOTAL_STEPS, "Extracting skills and keywords...")
    extracted = extract_keywords(resume["text"])
    stats["skills_found"] = len(extracted["skills"]["all"])
    logger.info(f"Stage 2 done: {stats['skills_found']} skills, title={extracted['job_title']}")

    #  Stage 3: Single LLM Call 
    cb(3, TOTAL_STEPS, "Analyzing resume (AI)...")
    analysis = analyze_resume(resume["text"], extracted, gemini_api_key)
    stats["llm_fallback"] = analysis.get("_fallback", False)
    logger.info(f"Stage 3 done: role={analysis['candidate_role']}, seniority={analysis.get('seniority')}")

    # Merge location: prefer user input, fallback to resume-detected
    effective_location = location.strip() or extracted.get("location") or ""

    candidate = {
        "name":           extracted.get("name"),
        "email":          extracted.get("email"),
        "phone":          extracted.get("phone"),
        "location":       effective_location,
        "job_title":      extracted.get("job_title"),
        "years_exp":      extracted.get("years_exp"),
        "education":      extracted.get("education"),
        "candidate_role": analysis["candidate_role"],
        "seniority":      analysis.get("seniority", "Mid-Level"),
        "top_skills":     analysis.get("top_skills", []),
        "all_skills":     extracted["skills"]["all"],
        "summary":        analysis.get("summary", ""),
        "search_queries": analysis.get("search_queries", []),
    }

    #  Stage 4: Optimize Queries 
    cb(4, TOTAL_STEPS, "Building job board search URLs...")
    optimized = optimize_queries(
        search_queries=candidate["search_queries"],
        top_skills=candidate["top_skills"],
        location=effective_location,
        seniority=candidate["seniority"],
        employment_type=employment_type,
    )
    stats["search_urls_built"] = len(optimized)
    logger.info(f"Stage 4 done: {len(optimized)} URLs built across job boards")

    #  Stage 5: Search Jobs 
    cb(5, TOTAL_STEPS, "Searching job boards...")
    raw_job_urls = search_jobs(optimized, max_results=max_results)
    stats["raw_urls_found"] = len(raw_job_urls)
    logger.info(f"Stage 5 done: {len(raw_job_urls)} job URLs found")

    if not raw_job_urls:
        return {
            "status": "ok",
            "error": None,
            "candidate": candidate,
            "jobs": [],
            "no_date_jobs": [],
            "stats": stats,
        }

    #  Stage 6: Filter URLs 
    cb(6, TOTAL_STEPS, "Filtering junk URLs...")
    clean_urls = filter_urls(raw_job_urls)
    stats["urls_after_filter"] = len(clean_urls)
    logger.info(f"Stage 6 done: {len(clean_urls)} URLs after filter")

    #  Stage 7: Scrape Jobs 
    cb(7, TOTAL_STEPS, "Scraping job details...")
    scraped = scrape_jobs(clean_urls)
    stats["jobs_scraped"] = len(scraped)
    logger.info(f"Stage 7 done: {len(scraped)} jobs scraped")

    if not scraped:
        return {
            "status": "ok",
            "error": None,
            "candidate": candidate,
            "jobs": [],
            "no_date_jobs": [],
            "stats": stats,
        }

    #  Stage 8: Normalize Dates + Filter 
    cb(8, TOTAL_STEPS, "Filtering by date range...")
    in_range, no_date = filter_by_date(scraped, from_date=from_date, to_date=to_date)
    stats["jobs_in_date_range"] = len(in_range)
    stats["jobs_no_date"] = len(no_date)
    logger.info(f"Stage 8 done: {len(in_range)} in range, {len(no_date)} no date")

    #  Stage 9: Remove Duplicates 
    cb(9, TOTAL_STEPS, "Removing duplicates...")
    combined = in_range + no_date
    unique = remove_duplicates(combined)
    stats["jobs_after_dedup"] = len(unique)
    logger.info(f"Stage 9 done: {len(unique)} unique jobs")

    # Re-split into in_range and no_date after dedup
    unique_in_range = [j for j in unique if j.get("date_posted") is not None]
    unique_no_date  = [j for j in unique if j.get("date_posted") is None]

    #  Stage 10: Score + Sort 
    cb(10, TOTAL_STEPS, "Scoring and ranking jobs...")
    scored_in_range = score_jobs(
        jobs=unique_in_range,
        candidate_role=candidate["candidate_role"],
        top_skills=candidate["top_skills"],
        all_skills=candidate["all_skills"],
        candidate_location=effective_location,
        seniority=candidate["seniority"],
        employment_type=employment_type,
    )
    scored_no_date = score_jobs(
        jobs=unique_no_date,
        candidate_role=candidate["candidate_role"],
        top_skills=candidate["top_skills"],
        all_skills=candidate["all_skills"],
        candidate_location=effective_location,
        seniority=candidate["seniority"],
        employment_type=employment_type,
    )
    stats["final_job_count"] = len(scored_in_range)
    logger.info(f"Stage 10 done: {len(scored_in_range)} scored jobs")

    return {
        "status":       "ok",
        "error":        None,
        "candidate":    candidate,
        "jobs":         scored_in_range,
        "no_date_jobs": scored_no_date,
        "stats":        stats,
    }