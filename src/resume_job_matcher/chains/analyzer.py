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
        model="gemini-3.6-flash",
        google_api_key=api_key,       
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

#  Fallback (if LLM fails)
 
def _build_fallback(extracted: dict) -> dict:
    """
    Build a basic response from Python-extracted data alone.
    Used when LLM call fails or returns unparseable output.
    """
    title = extracted.get("job_title") or "Software Developer"
    skills = extracted.get("skills", {}).get("all", [])
    top_skills = skills[:8] if skills else ["Python", "Software Development"]
    location = extracted.get("location") or ""
 
    loc_suffix = f" {location}" if location else ""
 
    queries = [
        f"{title}{loc_suffix}",
        f"{' '.join(top_skills[:3])} developer{loc_suffix}",
        f"{title} jobs",
    ]
 
    return {
        "candidate_role": title,
        "seniority": "Mid-Level",
        "top_skills": top_skills,
        "search_queries": queries,
        "summary": f"Candidate with skills in {', '.join(top_skills[:5])}.",
        "_fallback": True,
    }
 
# Main Entry Point
 
def analyze_resume(
    resume_text: str,
    extracted_keywords: dict,
    api_key: str,
) -> dict:
    """
    Single LLM call to analyze resume and generate search queries.
 
    Args:
        resume_text:        Cleaned text from Stage 1.
        extracted_keywords: Dict from Stage 2 keyword_extractor.
        api_key:            Gemini API key.
 
    Returns:
        {
            "candidate_role":  str,
            "seniority":       str,
            "top_skills":      list[str],
            "search_queries":  list[str],   ← used directly in Stage 4
            "summary":         str,
            "_fallback":       bool          ← True only if LLM failed
        }
    """
    try:
        llm = _get_llm(api_key)
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=_build_user_prompt(resume_text, extracted_keywords)),
        ]
        response = llm.invoke(messages)
        raw_text = response.content
 
        parsed = _parse_response(raw_text)
 
        # Validate required keys exist
        required = {"candidate_role", "top_skills", "search_queries"}
        if not required.issubset(parsed.keys()):
            raise ValueError(f"Missing keys in LLM response: {required - parsed.keys()}")
 
        # Ensure search_queries is a list of 3
        queries = parsed.get("search_queries", [])
        if not isinstance(queries, list) or len(queries) == 0:
            raise ValueError("search_queries missing or empty")
 
        parsed["_fallback"] = False
        return parsed
 
    except Exception as e:
        print(f"[Analyzer] LLM call failed: {e}. Using Python fallback.")
        return _build_fallback(extracted_keywords)
 