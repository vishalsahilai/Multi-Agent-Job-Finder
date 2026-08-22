import re
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a professional cover letter writer.
Write a concise, personalized cover letter for a job application.
Return ONLY the cover letter text — no subject line, no "Dear Hiring Manager" prefix instructions, no extra commentary.
Keep it to 3 paragraphs maximum. Professional but human tone."""


def _build_prompt(job: dict, profile: dict, candidate: dict) -> str:
    return f"""Write a cover letter for this job application:

JOB:
- Title: {job.get('title', '')}
- Company: {job.get('company', '')}
- Location: {job.get('location', '')}
- Description (first 800 chars): {(job.get('description') or '')[:800]}

APPLICANT:
- Name: {profile.get('full_name', '')}
- Years of experience: {profile.get('years_exp', candidate.get('years_exp', ''))}
- Top skills: {', '.join(candidate.get('top_skills', []))}
- Current/target role: {candidate.get('candidate_role', '')}
- Extra info: {profile.get('extra_info', '')}

Write a 3-paragraph cover letter. Start directly with "Dear Hiring Team," """


def generate_cover_letter(
    job: dict,
    profile: dict,
    candidate: dict,
    api_key: str,
) -> str:
    """
    Generate a personalized cover letter for one job.

    Args:
        job:       Job dict from Phase 1 results.
        profile:   User profile from UI form (name, email, phone, etc.)
        candidate: Candidate dict from Phase 1 pipeline.
        api_key:   Gemini API key.

    Returns:
        Cover letter as plain text string.
        Falls back to a generic template if LLM fails.
    """
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-3.6-flash",
            google_api_key=api_key,
            max_tokens=600,
        )
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=_build_prompt(job, profile, candidate)),
        ]
        response = llm.invoke(messages)
        raw = response.content if isinstance(response.content, str) else response.content[0].text
        return raw.strip()

    except Exception as e:
        logger.warning(f"Cover letter LLM failed: {e}. Using fallback.")
        return _fallback_cover_letter(job, profile, candidate)


def _fallback_cover_letter(job: dict, profile: dict, candidate: dict) -> str:
    name    = profile.get("full_name", "Applicant")
    title   = job.get("title", "this position")
    company = job.get("company", "your company")
    skills  = ", ".join(candidate.get("top_skills", [])[:5])
    years   = profile.get("years_exp") or candidate.get("years_exp") or "several"

    return f"""Dear Hiring Team,

I am writing to express my strong interest in the {title} role at {company}. With {years} years of experience and expertise in {skills}, I am confident in my ability to contribute meaningfully to your team.

Throughout my career, I have developed strong technical skills and a proven ability to deliver results. I am particularly drawn to {company} because of its reputation and the exciting challenges this role presents.

I would welcome the opportunity to discuss how my background aligns with your needs. Thank you for considering my application.

Sincerely,
{name}"""