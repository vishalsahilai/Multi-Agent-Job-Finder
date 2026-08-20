# 🔍 Multi-Agent Job Finder

> A production-ready AI-powered job discovery system built with Python, Streamlit, Google Gemini, BeautifulSoup, Playwright, and custom Python algorithms — handling everything from resume parsing to date-filtered, relevance-scored job results with minimum LLM usage.

---

## 🖥️ Live Preview

> Upload your resume → Get recent, relevant, date-filtered jobs in seconds.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Features](#features)
4. [How It Works](#how-it-works)
5. [File Structure](#file-structure)
6. [Prerequisites](#prerequisites)
7. [Setup & Installation](#setup--installation)
8. [Environment Variables](#environment-variables)
9. [Streamlit UI Guide](#streamlit-ui-guide)
10. [Search Configuration](#search-configuration)
11. [Date Filtering Algorithm](#date-filtering-algorithm)
12. [Relevance Scoring Algorithm](#relevance-scoring-algorithm)
13. [Duplicate Removal](#duplicate-removal)
14. [Job Scraping](#job-scraping)
15. [Technologies](#technologies)
16. [API Requirements](#api-requirements)
17. [Limitations](#limitations)
18. [Future Improvements](#future-improvements)
19. [Author](#author)

---

## Overview

**Multi-Agent Job Finder** is a full-stack AI job discovery system that takes a candidate's resume, analyzes it intelligently, searches real job boards, scrapes actual job postings, filters by date range, removes duplicates, scores by relevance, and presents clean results in a Streamlit interface.

The system is built around three core innovations:

- **Minimum LLM Usage** — Gemini is called exactly once per run. All other processing (filtering, scoring, deduplication, date parsing, keyword extraction) is done in Python.
- **Date-Range Filtering** — Handles 5+ real-world date formats (absolute, relative, ISO) to return only jobs posted within a user-specified date range.
- **Python-First Architecture** — Resume keyword extraction, URL filtering, relevance scoring, duplicate removal, and job sorting are all pure Python algorithms — no API cost.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Streamlit UI                               │
│   Resume Upload │ Date Picker │ Location │ Filters │ Job Table  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Pipeline                                  │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Resume Reader│  │ Keyword      │  │  Single LLM Call     │  │
│  │ PDF / DOCX   │  │ Extractor    │  │  Google Gemini       │  │
│  │ Python only  │  │ Python only  │  │  (Analyzer — once)   │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Query        │  │  Job Search  │  │   URL Filter         │  │
│  │ Optimizer    │  │  Requests +  │  │   Python only        │  │
│  │ Python only  │  │  Python      │  │   (removes junk)     │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Job Scraper  │  │ Date Filter  │  │  Duplicate Remover   │  │
│  │ BeautifulSoup│  │ Python only  │  │  Python only         │  │
│  │ + Playwright │  │ (From→To)    │  │  URL + Fuzzy match   │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           Relevance Scorer — Python only                 │   │
│  │    Title Match │ Tech Match │ Skills │ Location │ Type   │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
                    Final Job Table
            (sorted by relevance + date)
```

---

## Features

- **Resume Upload** — PDF and DOCX formats supported
- **Python Resume Keyword Extraction** — skills, years of experience, location, job title extracted without LLM
- **Single LLM Call** — Gemini called once to generate optimized search queries and candidate profile
- **Optimized Search Queries** — weak queries upgraded automatically (e.g. "Python jobs" → "Junior Python Backend Developer Django FastAPI Karachi")
- **Multi-Platform Job Search** — searches Rozee.pk, Indeed, LinkedIn public pages, and Google Jobs
- **Smart URL Filtering** — removes GitHub repos, tutorials, Medium articles, documentation, YouTube before scraping
- **Python-Based Scraping** — BeautifulSoup for static pages, Playwright for dynamic pages — no LLM used during scraping
- **5-Format Date Parsing** — handles absolute dates, relative dates, ISO dates, and "Posted X days ago" formats
- **Date Range Filtering** — From Date → To Date filter removes all out-of-range jobs
- **Duplicate Job Removal** — URL normalization + fuzzy title+company matching eliminates duplicates
- **Relevance Scoring Algorithm** — scores each job on 5 signals and ranks by percentage match
- **Configurable Job Count** — Max Jobs slider dynamically adjustable via UI
- **Location Filter** — filter results by city or country
- **Employment Type Filter** — Full-time, Remote, Hybrid, On-site
- **Live Progress Tracker** — 10-step status updates during pipeline execution
- **Clean Job Cards** — Job Title, Company, Date, Location, Match %, Link in one organized view
- **No Fake Dates** — if posting date is unavailable, shows "Date Not Available" — never fabricates
- **CSV Download** — export all results with one click

---

## How It Works

### Full Pipeline Flow

```
User uploads Resume (PDF / DOCX)
         ↓
Resume Reader extracts raw text (Python — pypdf / python-docx)
         ↓
Keyword Extractor runs on text (Python — regex + skill dictionary)
  → Extracts: skills, years of experience, location, job title keywords
         ↓
Single Gemini Call (1 API call total per run)
  → Input: resume text + Python-extracted keywords
  → Output: candidate role, 3 search queries, top skills list (JSON)
         ↓
Query Optimizer enhances queries (Python)
  → "Python Developer" → "Junior Python Backend Developer Django FastAPI Karachi"
  → Builds URLs for 6 job boards per query
         ↓
Job Search runs (Python — requests + BeautifulSoup)
  → Searches Rozee.pk, Indeed, LinkedIn, Google Jobs, Glassdoor, Mustakbil
  → Collects raw job posting URLs
         ↓
URL Filter removes junk (Python — string matching)
  → Removes: github.com, medium.com, dev.to, youtube.com, geeksforgeeks, docs
  → Keeps: linkedin.com/jobs, indeed.com/viewjob, rozee.pk/job, company career pages
         ↓
Job Scraper extracts job data (Python — BeautifulSoup / Playwright)
  → Title, Company, Location, Employment Type, Description, Date Posted, URL
         ↓
Date Normalizer converts all date formats (Python — dateparser)
  → "August 10, 2026" | "3 days ago" | "2026-08-10" | "yesterday" → datetime
         ↓
Date Filter applies From Date → To Date range (Python)
  → Jobs outside range removed
  → Date unavailable jobs kept separately with "Date Not Available" label
         ↓
Duplicate Remover cleans results (Python)
  → URL normalization (strips utm params, trailing slashes, http/https)
  → Fuzzy title + company match for cross-platform duplicates
         ↓
Relevance Scorer ranks all jobs (Python)
  → Score calculated per job → converted to percentage → sorted descending
         ↓
Streamlit UI displays Final Job Cards
  → Job Title | Company | Date | Location | Match % | Link | Score Breakdown
```

### LLM Usage (Exactly 1 Call Per Run)

```
What Gemini does:
  Input → resume text (first 3000 chars) + Python-extracted keywords
  Output → {
    "candidate_role": "Junior Python Backend Developer",
    "seniority": "Junior",
    "search_queries": [
      "Junior Python Backend Developer Django FastAPI Karachi",
      "Python Developer FastAPI PostgreSQL remote Pakistan",
      "Backend Engineer Django REST Framework entry level"
    ],
    "top_skills": ["Python", "Django", "FastAPI", "PostgreSQL", "REST API"],
    "summary": "..."
  }

What Python handles (no LLM):
  ✅ Resume text extraction
  ✅ Skill keyword detection (100+ skills across 8 categories)
  ✅ Experience year parsing
  ✅ Query optimization / enhancement
  ✅ Job board URL building (6 boards × 3 queries = 18 URLs)
  ✅ URL filtering (junk removal)
  ✅ Job page scraping
  ✅ Date parsing and normalization
  ✅ Date range filtering
  ✅ Duplicate detection and removal
  ✅ Relevance scoring
  ✅ Result sorting
  ✅ Location filtering
  ✅ Employment type filtering
```

---

## File Structure

```
Multi-Agent-Job-Finder/
│
├── app.py                              ← Streamlit UI entry point
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── data/
│   └── sample_resumes/                 ← Sample PDF/DOCX resumes for testing
│
├── src/
│   └── resume_job_matcher/
│       │
│       ├── __init__.py
│       ├── config.py                   ← Pydantic settings + .env loader
│       ├── pipeline.py                 ← Full pipeline orchestrator
│       │
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── resume_reader.py        ← PDF/DOCX text extractor (pypdf + python-docx)
│       │   └── scrape_url.py           ← Python scraper (BeautifulSoup + Playwright)
│       │
│       ├── chains/
│       │   ├── __init__.py
│       │   └── analyzer.py             ← Single Gemini call → candidate profile + queries
│       │
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── job_search_agent.py     ← Python-based multi-platform job search
│       │   └── job_scraper_agent.py    ← BeautifulSoup / Playwright scraper
│       │
│       └── processors/
│           ├── __init__.py
│           ├── keyword_extractor.py    ← Python resume keyword + skill parser
│           ├── query_optimizer.py      ← Search query + job board URL builder (Python)
│           ├── url_filter.py           ← Junk URL removal (Python)
│           ├── date_normalizer.py      ← Multi-format date parser + range filter (Python)
│           ├── date_filter.py          ← From Date → To Date range filter (Python)
│           ├── duplicate_remover.py    ← URL normalization + fuzzy dedup (Python)
│           └── relevance_scorer.py     ← 5-signal job relevance scorer (Python)
│
└── tests/
    ├── __init__.py
    ├── test_resume_reader.py
    ├── test_date_normalizer.py
    ├── test_duplicate_remover.py
    └── test_relevance_scorer.py
```

---

## Prerequisites

| Tool | Version / Notes |
|---|---|
| Python | **≥ 3.10** |
| pip | Latest |
| Git | Latest |
| Google Gemini API Key | Free — [aistudio.google.com](https://aistudio.google.com) |
| Playwright (optional) | For dynamic job pages — `playwright install chromium` |

> ⚠️ Playwright is optional but recommended. Static scraping (BeautifulSoup) works without it. Install Playwright only if job pages fail to load with requests alone.

---

## Setup & Installation

```bash
# 1. Clone the repository
git clone https://github.com/vishalsahilai/Multi-Agent-Job-Finder.git
cd Multi-Agent-Job-Finder

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Playwright browser (optional — for dynamic scraping)
playwright install chromium

# 5. Set up environment variables
cp .env.example .env
# Open .env and add your GEMINI_API_KEY

# 6. Run the Streamlit app
streamlit run app.py
```

App opens at `http://localhost:8501`

---

## Environment Variables

Only **one** variable is required:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Get your free key at [aistudio.google.com](https://aistudio.google.com/app/apikey)

> ⚠️ **Never commit `.env` to GitHub.** The `.env.example` file is safe to commit — it contains no real values.

---

## Streamlit UI Guide

### Sidebar — Search Configuration

| Control | Type | Purpose |
|---|---|---|
| Gemini API Key | Password Input | Auto-loaded from `.env` — override anytime |
| Location | Text Input | City or country filter (e.g. "Karachi", "Remote") |
| Employment Type | Dropdown | Any / Full-time / Remote / Hybrid / On-site / Contract |
| From Date | Date Picker | Start of job posting date range |
| To Date | Date Picker | End of job posting date range |
| Max Job Results | Slider | Maximum jobs to collect (10–100) |

### Progress Tracker

```
✅ Step 1  — Reading resume
✅ Step 2  — Extracting skills & keywords
✅ Step 3  — Analyzing resume (AI — 1 call)
✅ Step 4  — Building search URLs
✅ Step 5  — Searching job boards
✅ Step 6  — Filtering junk URLs
✅ Step 7  — Scraping job details
✅ Step 8  — Filtering by date range
✅ Step 9  — Removing duplicates
✅ Step 10 — Scoring & ranking jobs
```

### Final Job Cards

Each job displays:
- **Title** and **Company**
- **Date Posted** and **Location**
- **Match %** — color coded (🟢 70%+ / 🟡 40%+ / 🔴 below 40%)
- **Source board** badge (Rozee.pk, LinkedIn, Indeed, etc.)
- **View Job** button — opens original posting
- **Score Breakdown** expander — shows points per signal

---

## Search Configuration

### How Search Queries Are Built

| Stage | Example |
|---|---|
| Raw resume skills | Python, Django, FastAPI, PostgreSQL |
| LLM-generated query | "Python Developer" |
| Python-optimized query | "Junior Python Backend Developer Django FastAPI Karachi" |
| Job board URLs built | 6 boards × 3 queries = 18 search URLs |

### Platforms Searched

| Platform | Method | Notes |
|---|---|---|
| Rozee.pk | requests + BeautifulSoup | Major Pakistan job board |
| Mustakbil.com | requests + BeautifulSoup | Pakistan job board |
| Indeed | requests + BeautifulSoup | Global job board |
| LinkedIn | requests (public pages) | Public job listings only |
| Glassdoor | requests + BeautifulSoup | Global job board |
| Google Jobs | requests + parsing | Aggregates multiple boards |

### URL Filter Rules

Removed automatically (junk):
- `github.com` — repositories, not jobs
- `medium.com`, `dev.to` — tutorials and articles
- `geeksforgeeks.org`, `w3schools.com` — documentation
- `youtube.com` — video content
- `stackoverflow.com` — Q&A, not jobs
- `reddit.com` — discussion forums

Kept (actual job postings):
- `linkedin.com/jobs/`
- `indeed.com/viewjob`
- `rozee.pk/job/`
- `mustakbil.com/job-detail/`
- Company career pages (`/careers/`, `/jobs/`, `careers.`)

---

## Date Filtering Algorithm

### Supported Formats

| Format Example | Parsed As |
|---|---|
| `August 10, 2026` | Absolute date |
| `10 Aug 2026` | Absolute date |
| `2026-08-10` | ISO 8601 date |
| `Posted 3 days ago` | Today minus 3 days |
| `Posted yesterday` | Today minus 1 day |
| `Just now` | Today |
| No date found | `None` → "Date Not Available" |

### Filter Logic

```
For each scraped job:
  1. Extract raw date string from HTML
  2. Try relative pattern match → datetime
  3. Try absolute strptime (13 formats) → datetime
  4. Fallback to dateparser library → datetime
  5. Compare: job_date >= From Date AND job_date <= To Date → Keep
  6. Outside range → Remove
  7. Date is None → Keep separately, label "Date Not Available"

Rules:
  ✅ Never fabricate a date
  ✅ "Date Not Available" is honest output — not an error
  ✅ Jobs with unavailable dates shown last, after dated jobs
```

---

## Relevance Scoring Algorithm

### Scoring Table

| Signal | Max Points | How Checked |
|---|---|---|
| Job Title Match | 30 | Candidate role keywords vs job title (partial scoring) |
| Skill Match | 60 | Top skills from analyzer in job description (20pts each, cap 3) |
| Keyword Match | 30 | Resume skills in job description (10pts each, cap 3) |
| Location Match | 10 | Job location vs candidate location (remote always matches) |
| Seniority Match | 10 | Junior/Mid/Senior signal words in job text |
| Employment Type | 5 | Remote/Full-time/Hybrid match |

**Maximum possible: 145 points → normalized to 100%**

Sorted by match % descending, then date (newest first) as tiebreaker.

---

## Duplicate Removal

### Pass 1 — URL Normalization

```
https://www.linkedin.com/jobs/view/123?utm_source=google&trk=abc
http://linkedin.com/jobs/view/123/
→ Both normalize to: linkedin.com/jobs/view/123
→ Second is dropped
```

### Pass 2 — Fuzzy Title + Company Match

```
Job A: "Python Developer" at "ABC Technologies Pvt Ltd"
Job B: "Python Developer" at "ABC Technologies"
→ token_sort_ratio = 89 (above threshold 85)
→ Job B is a duplicate → removed
```

---

## Job Scraping

### Static Scraping (BeautifulSoup + requests)

```
GET job_url (with realistic User-Agent headers)
         ↓
BeautifulSoup parses HTML
         ↓
Board-specific CSS selectors extract:
  - Job title     → h1.job-title, [data-testid="jobTitle"]
  - Company       → .company-name, [data-testid="company"]
  - Location      → .job-location, [data-testid="location"]
  - Date posted   → time[datetime], .posted-date, .job-age
  - Description   → .job-description, #job-details
         ↓
Generic fallback selectors for unknown boards
         ↓
Structured job dict returned
```

### Dynamic Scraping (Playwright — optional)

Used automatically when static fetch returns no title and no description:

```
Playwright launches headless Chromium
         ↓
Navigates to job URL (20s timeout)
         ↓
Waits 2s for JS render
         ↓
page.content() → full rendered HTML
         ↓
BeautifulSoup parses → same extraction logic
         ↓
Browser closed
```

---

## Technologies

| Layer | Technology | Purpose |
|---|---|---|
| UI | Streamlit | Web interface — upload, filters, results |
| LLM | Google Gemini (gemini-3.6-flash) | Resume analysis — 1 call per run |
| PDF Parsing | pypdf | Extract text from PDF resumes |
| DOCX Parsing | python-docx | Extract text from Word resumes |
| Static Scraping | requests + BeautifulSoup | Job page HTML extraction |
| Dynamic Scraping | Playwright | JavaScript-rendered job pages |
| Date Parsing | dateparser + python-dateutil | Multi-format date normalization |
| Fuzzy Matching | rapidfuzz | Duplicate detection + title matching |
| Config | python-dotenv + pydantic-settings | Environment variable management |
| LLM Framework | langchain + langchain-google-genai | Gemini integration |

---

## API Requirements

| API / Service | Required | Cost | Purpose |
|---|---|---|---|
| Google Gemini API | ✅ Yes | Free tier available | Resume analysis (1 call/run) |
| Tavily Search API | ❌ Removed | Was paid | Replaced with Python search |
| LinkedIn API | ❌ Not needed | — | Public pages scraped directly |
| Indeed API | ❌ Not needed | — | Public pages scraped directly |

> Only **one** API key is needed — Google Gemini. Everything else is Python.

---

## Limitations

- **LinkedIn / Indeed rate limits** — These platforms detect and throttle scrapers. The system uses random request delays and realistic User-Agent headers, but heavy usage may trigger blocks. Use responsibly.
- **Dynamic pages** — Some job boards load content via JavaScript. Playwright handles this automatically but requires a Chromium installation.
- **Date availability** — Not all job postings include a posting date in their HTML. These are shown as "Date Not Available" — never fabricated.
- **Pakistan-focused search** — Query optimization is tuned for the Pakistan job market (Rozee.pk, Mustakbil, Karachi, Lahore). Adjust `query_optimizer.py` for other regions.
- **No authentication** — Only publicly accessible job pages are scraped. LinkedIn full API and Indeed official API are not used.
- **Single LLM provider** — Currently only Google Gemini is supported. OpenAI or other providers would require changes to `analyzer.py`.

---

## Future Improvements

- [ ] Add support for OpenAI and Anthropic as LLM providers
- [ ] Add Rozee.pk official API integration when available
- [ ] Email alerts — notify user when new matching jobs are posted
- [ ] Resume comparison mode — compare two resumes against same job results
- [ ] Job tracking dashboard — mark jobs as Applied / Saved / Rejected
- [ ] Salary range filter — filter jobs by mentioned salary
- [ ] Multi-language resume support
- [ ] Docker deployment
- [ ] CI/CD pipeline with GitHub Actions

---

## Author

**Vishal Sahil** — AI Developer

- 🐙 [github.com/vishalsahilai](https://github.com/vishalsahilai)

---

MIT License — Free to use, modify, and distribute.

> Built with ❤️ · Powered by Python + Google Gemini · Minimum API, Maximum Intelligence