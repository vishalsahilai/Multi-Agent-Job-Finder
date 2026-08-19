import json
import re
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

 
#  Prompt
 
SYSTEM_PROMPT = """You are a resume analyzer. Your job is to read a resume and return structured JSON only.
Do not include markdown, code blocks, or any explanation — raw JSON only.
 
Return exactly this structure:
{
  "candidate_role": "string — the most accurate job title for this candidate (e.g. 'Backend Python Developer')",
  "seniority": "string — one of: Intern, Junior, Mid-Level, Senior, Lead",
  "top_skills": ["list of 5-8 most relevant technical skills from the resume"],
  "search_queries": [
    "query 1 — specific job search query string",
    "query 2 — alternate query with different keywords",
    "query 3 — broader fallback query"
  ],
  "summary": "2-3 sentence professional summary of the candidate"
}
 
Rules:
- search_queries must be ready to use in a job board search bar (no quotes, no operators)
- Each search query should be different — vary the keywords and phrasing
- top_skills must be actual technologies/tools, not soft skills
- Keep all values concise"""
 
 
def _build_user_prompt(resume_text: str, extracted: dict) -> str:
    """Build a compact prompt using resume text + already-extracted Python keywords."""
 
    # Truncate resume to 3000 chars to keep token usage low
    truncated = resume_text[:3000] if len(resume_text) > 3000 else resume_text
 
    skills_flat = extracted.get("skills", {}).get("all", [])
    skills_str = ", ".join(skills_flat[:20]) if skills_flat else "not detected"
 
    location = extracted.get("location") or "not detected"
    years_exp = extracted.get("years_exp")
    exp_str = f"{years_exp} years" if years_exp else "not detected"
    title_hint = extracted.get("job_title") or "not detected"
 
    return f"""RESUME TEXT (first 3000 chars):
{truncated}
 
PRE-EXTRACTED DATA (Python):
- Detected title: {title_hint}
- Detected skills: {skills_str}
- Detected location: {location}
- Detected experience: {exp_str}
 
Using the resume text and pre-extracted data above, return the JSON structure."""

# LLM Client 
 
def _get_llm(api_key: str) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model="gemini-3-flash",
        google_api_key=api_key,
        temperature=0.1,        # low temp = consistent structured output
        max_tokens=600,         # enough for the JSON, no fluff
    )

#  Response Parser 
 
def _parse_response(raw: str) -> dict:
    """
    Safely parse JSON from LLM response.
    Strips markdown fences if present.
    Falls back to empty structure on failure.
    """
    # Strip ```json ... ``` or ``` ... ``` wrappers
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
 
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to find JSON object inside the text
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
 
    return {}
 
 