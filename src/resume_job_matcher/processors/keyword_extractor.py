import re
from typing import Optional


"""
Stage 2: Python Resume Keyword Extractor
Extracts skills, experience years, location, job title, email, phone from resume text.
No LLM calls — pure Python regex + dictionary matching.
"""
 
import re
from typing import Optional
 
 
#  Skill Dictionaries
 
SKILLS = {
    "languages": [
        "python", "javascript", "typescript", "java", "c++", "c#", "c",
        "go", "golang", "rust", "ruby", "php", "swift", "kotlin", "scala",
        "r", "matlab", "perl", "bash", "shell", "powershell", "dart", "lua",
        "haskell", "elixir", "clojure", "groovy", "cobol", "fortran",
    ],
    "web_frameworks": [
        "django", "flask", "fastapi", "express", "nestjs", "nextjs", "nuxtjs",
        "react", "angular", "vue", "svelte", "spring", "spring boot", "laravel",
        "rails", "ruby on rails", "asp.net", "blazor", "gatsby", "remix",
        "fiber", "gin", "echo", "tornado", "aiohttp", "starlette", "hapi",
    ],
    "databases": [
        "postgresql", "postgres", "mysql", "sqlite", "mongodb", "redis",
        "elasticsearch", "cassandra", "dynamodb", "firebase", "supabase",
        "oracle", "sql server", "mssql", "mariadb", "cockroachdb", "neo4j",
        "influxdb", "clickhouse", "snowflake", "bigquery", "redshift",
    ],
    "cloud": [
        "aws", "azure", "gcp", "google cloud", "heroku", "digitalocean",
        "vercel", "netlify", "cloudflare", "linode", "vultr", "railway",
        "ec2", "s3", "lambda", "rds", "ecs", "eks", "cloud run", "app engine",
    ],
    "devops": [
        "docker", "kubernetes", "k8s", "jenkins", "github actions", "gitlab ci",
        "circleci", "travis ci", "ansible", "terraform", "helm", "prometheus",
        "grafana", "nginx", "apache", "linux", "ubuntu", "centos", "debian",
        "ci/cd", "devops", "sre", "gitops", "argocd",
    ],
    "data_ml": [
        "pandas", "numpy", "scikit-learn", "sklearn", "tensorflow", "keras",
        "pytorch", "xgboost", "lightgbm", "spark", "hadoop", "airflow",
        "dbt", "mlflow", "huggingface", "langchain", "openai", "gemini",
        "machine learning", "deep learning", "nlp", "computer vision",
        "data science", "data engineering", "etl", "data pipeline",
        "tableau", "power bi", "looker", "matplotlib", "seaborn", "plotly",
    ],
    "mobile": [
        "react native", "flutter", "android", "ios", "swift", "kotlin",
        "xamarin", "ionic", "capacitor", "expo",
    ],
    "tools": [
        "git", "github", "gitlab", "bitbucket", "jira", "confluence",
        "figma", "postman", "swagger", "graphql", "rest", "rest api",
        "grpc", "websocket", "kafka", "rabbitmq", "celery", "redis",
        "webpack", "vite", "babel", "eslint", "pytest", "jest", "selenium",
        "playwright", "cypress", "linux", "vim", "vs code", "intellij",
    ],
    "concepts": [
        "agile", "scrum", "kanban", "tdd", "bdd", "microservices",
        "monolith", "serverless", "event-driven", "oop", "functional programming",
        "design patterns", "system design", "api design", "data structures",
        "algorithms", "distributed systems", "cloud native", "devsecops",
    ],
}
 
# Flatten for fast lookup
ALL_SKILLS_FLAT = {skill for category in SKILLS.values() for skill in category}

#  Job Title Patterns
 
TITLE_KEYWORDS = [
    "software engineer", "software developer", "web developer", "backend developer",
    "frontend developer", "full stack developer", "fullstack developer",
    "mobile developer", "android developer", "ios developer",
    "data scientist", "data engineer", "data analyst", "ml engineer",
    "machine learning engineer", "ai engineer", "nlp engineer",
    "devops engineer", "cloud engineer", "sre", "site reliability engineer",
    "security engineer", "cybersecurity", "network engineer",
    "product manager", "project manager", "scrum master",
    "ui/ux designer", "ux designer", "ui designer",
    "qa engineer", "test engineer", "automation engineer",
    "tech lead", "technical lead", "engineering manager",
    "solutions architect", "cloud architect", "system architect",
    "python developer", "java developer", "javascript developer",
    "node.js developer", "react developer", "django developer",
    "intern", "junior developer", "senior developer",
    "associate engineer", "graduate trainee",
]

# Location Keywords 
 
CITIES = [
    # Original list
    "karachi", "lahore", "islamabad", "rawalpindi", "faisalabad", "multan",
    "peshawar", "quetta", "hyderabad", "sialkot",
    "new york", "san francisco", "seattle", "austin", "boston", "chicago",
    "london", "toronto", "dubai", "singapore", "berlin", "amsterdam",
    "remote", "on-site", "hybrid", "work from home", "wfh",
    
    # United Kingdom & Ireland
    "manchester", "birmingham", "edinburgh", "glasgow", "leeds", "bristol", "dublin", "cork",
    
    # North America (US & Canada Expansion)
    "los angeles", "denver", "washington dc", "atlanta", "miami", "dallas", "houston", 
    "vancouver", "montreal", "calgary", "ottawa",
    
    # Australia & New Zealand
    "sydney", "melbourne", "brisbane", "perth", "auckland", "wellington",
    
    # European Tech Hubs (English Speaking Business)
    "frankfurt", "munich", "paris", "zurich", "stockholm", "copenhagen", "oslo", "tallinn",
    
    # Middle East, Africa & Asia-Pacific Business Hubs
    "abu dhabi", "riyadh", "cape town", "johannesburg", "hong kong", "manila", "kuala lumpur",
    "bangalore", "mumbai", "pune", "chennai", "delhi",
    
    # Additional Remote/Flex Keywords
    "anywhere", "worldwide", "global remote", "flexible"
]

#  Extractor Functions
 
def extract_email(text: str) -> Optional[str]:
    pattern = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    match = re.search(pattern, text)
    return match.group(0) if match else None
 
 
def extract_phone(text: str) -> Optional[str]:
    # Matches common formats: +92-300-1234567, (021) 1234567, 03001234567, etc.
    pattern = r"(\+?\d{1,3}[\s\-]?)?(\(?\d{2,4}\)?[\s\-]?)(\d{3,4}[\s\-]?\d{3,4})"
    match = re.search(pattern, text)
    return match.group(0).strip() if match else None
 
 
def extract_years_of_experience(text: str) -> Optional[int]:
    """
    Detects patterns like:
    - '5 years of experience'
    - '3+ years'
    - 'experience: 2 years'
    - Date ranges like '2019 - 2024' → 5 years
    """
    # Explicit mention
    pattern = r"(\d+)\+?\s*years?\s*(of\s*)?(experience|exp)"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return int(match.group(1))
 
    # Infer from date ranges (e.g., Jan 2019 – Dec 2023)
    year_pattern = r"\b(20\d{2}|19\d{2})\b"
    years_found = [int(y) for y in re.findall(year_pattern, text)]
    if len(years_found) >= 2:
        min_year = min(years_found)
        max_year = max(years_found)
        if 1990 <= min_year <= 2026 and max_year >= min_year:
            return max_year - min_year
 
    return None
 
 
def extract_skills(text: str) -> dict:
    """
    Returns matched skills grouped by category.
    Also returns a flat list of all matched skills.
    """
    text_lower = text.lower()
    matched = {}
    all_matched = []
 
    for category, skills in SKILLS.items():
        found = []
        for skill in skills:
            # Word boundary match to avoid partial matches (e.g., 'c' in 'science')
            if re.search(r"\b" + re.escape(skill) + r"\b", text_lower):
                found.append(skill)
        if found:
            matched[category] = found
            all_matched.extend(found)
 
    return {
        "by_category": matched,
        "all": list(dict.fromkeys(all_matched)),  # preserve order, remove dupes
    }
 
 
def extract_job_title(text: str) -> Optional[str]:
    """
    Finds the most likely current/target job title from resume text.
    Prioritizes titles found near the top (first 500 chars) of the resume.
    """
    text_lower = text.lower()
    top_section = text_lower[:500]
 
    # Try top section first
    for title in TITLE_KEYWORDS:
        if re.search(r"\b" + re.escape(title) + r"\b", top_section):
            return title.title()
 
    # Fallback: search full text
    for title in TITLE_KEYWORDS:
        if re.search(r"\b" + re.escape(title) + r"\b", text_lower):
            return title.title()
 
    return None
 
 
def extract_location(text: str) -> Optional[str]:
    text_lower = text.lower()
    for city in CITIES:
        if re.search(r"\b" + re.escape(city) + r"\b", text_lower):
            return city.title()
    return None
 
 
def extract_name(text: str) -> Optional[str]:
    """
    Best-effort name extraction: assumes first non-empty line is the candidate name
    if it looks like a name (2-4 words, no digits, no special chars).
    """
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        words = line.split()
        if 2 <= len(words) <= 4 and all(w.replace(".", "").isalpha() for w in words):
            return line
        break  # Only check the very first non-empty line
    return None
 
 
def extract_education(text: str) -> list:
    """Extract degree keywords found in resume."""
    degrees = [
        "bachelor", "b.s.", "b.sc", "b.e.", "b.tech", "bsc", "be",
        "master", "m.s.", "m.sc", "m.e.", "m.tech", "msc", "mba",
        "phd", "ph.d", "doctorate",
        "associate", "diploma", "certification", "certified",
        "computer science", "information technology", "software engineering",
        "data science", "electrical engineering", "mathematics",
    ]
    text_lower = text.lower()
    found = []
    for deg in degrees:
        if re.search(r"\b" + re.escape(deg) + r"\b", text_lower):
            found.append(deg)
    return found

#  Main Entry Point 
 
def extract_keywords(resume_text: str) -> dict:

    return {
        "name":      extract_name(resume_text),
        "email":     extract_email(resume_text),
        "phone":     extract_phone(resume_text),
        "location":  extract_location(resume_text),
        "job_title": extract_job_title(resume_text),
        "years_exp": extract_years_of_experience(resume_text),
        "skills":    extract_skills(resume_text),
        "education": extract_education(resume_text),
    }