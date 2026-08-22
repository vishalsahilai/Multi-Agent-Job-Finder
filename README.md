# 🔍 Multi-Agent Job Finder

> A production-ready AI-powered job discovery and auto-apply system built with Python, Streamlit, Google Gemini, BeautifulSoup, and Playwright — handling everything from resume parsing to date-filtered, relevance-scored job results, and automatic job applications.

---

## 🖥️ Local Usage

```bash
streamlit run app.py
# Opens at http://localhost:8501
```

Upload your resume → jobs scraped and ranked in minutes. No hosting. Runs fully on your machine.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Phase 1 — Job Finder](#phase-1--job-finder)
3. [Phase 2 — Auto Apply](#phase-2--auto-apply)
4. [System Architecture](#system-architecture)
5. [File Structure](#file-structure)
6. [Prerequisites](#prerequisites)
7. [Setup & Installation](#setup--installation)
8. [Environment Variables](#environment-variables)
9. [How It Works — Phase 1](#how-it-works--phase-1)
10. [How It Works — Phase 2](#how-it-works--phase-2)
11. [Relevance Scoring Algorithm](#relevance-scoring-algorithm)
12. [Date Filtering Algorithm](#date-filtering-algorithm)
13. [Duplicate Removal](#duplicate-removal)
14. [Technologies](#technologies)
15. [API Requirements](#api-requirements)
16. [Limitations](#limitations)
17. [Future Improvements](#future-improvements)
18. [Author](#author)

---

## Overview

**Multi-Agent Job Finder** is a two-phase AI job discovery and auto-apply system.

**Phase 1 (Complete):** Upload resume → scrape real jobs from LinkedIn, Rozee.pk, Indeed, Glassdoor, Mustakbil → filter by date → remove duplicates → score by relevance → show ranked results.

**Phase 2 (In Development):** Select jobs from Phase 1 results → system automatically fills and submits applications on LinkedIn Easy Apply, Indeed, and Rozee.pk using your profile data.

### Core Principles

- **Minimum LLM Usage** — Gemini is called exactly once per run. All filtering, scoring, deduplication, date parsing, and keyword extraction is pure Python.
- **No Data Storage** — Resume bytes stay in memory only. Nothing saved to disk. No database.
- **Local First** — Runs entirely on your machine. No hosting required.
- **Python-First Architecture** — 10-stage pipeline where only 1 stage uses an LLM.

---

## Phase 1 — Job Finder

**Status: ✅ Complete and Working**

| What it does | How |
|---|---|
| Read resume (PDF / DOCX) | pypdf + python-docx |
| Extract skills, title, location, experience | Python regex + 100+ skill dictionary |
| Analyze resume and generate search queries | 1 Gemini API call |
| Build job board search URLs | Python — 6 boards × 3 queries = 18 URLs |
| Search and collect job posting URLs | requests + BeautifulSoup |
| Filter junk URLs (GitHub, Medium, YouTube) | Python string matching |
| Scrape job details from each posting | BeautifulSoup + Playwright |
| Parse all date formats | Python + dateparser |
| Filter jobs by From Date → To Date | Python |
| Remove duplicate jobs | URL normalization + fuzzy matching |
| Score and rank by relevance | 5-signal Python scorer |
| Show results in Streamlit UI | Job cards + match % + CSV download |

---

## Phase 2 — Auto Apply

**Status: 🚧 In Development**

After Phase 1 shows ranked jobs, Phase 2 lets the system automatically apply to selected jobs.

| What it does | How |
|---|---|
| User selects jobs to apply to | Checkboxes in Streamlit UI |
| User fills applicant profile once | Name, email, phone, experience, cover letter template |
| System opens each job application | Playwright browser automation |
| Fills application form fields automatically | CSS selectors + form detection |
| Attaches resume PDF automatically | File input automation |
| Generates custom cover letter per job | 1 Gemini call per application |
| Submits application | Playwright click + form submit |
| Logs result (Applied / Failed / Manual needed) | Python dict → shown in UI |

### Phase 2 Supported Platforms

| Platform | Method | Status |
|---|---|---|
| LinkedIn Easy Apply | Playwright form fill | 🚧 In Development |
| Indeed Apply | Playwright form fill | 🚧 In Development |
| Rozee.pk Apply | Playwright form fill | 🚧 In Development |
| Company career pages | Generic form detection | 🚧 Planned |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Streamlit UI                                 │
│  Resume Upload │ Filters │ Job Cards │ Apply Selector │ Apply Log   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PHASE 1 — Job Finder Pipeline                    │
│                                                                     │
│  Stage 1   Resume Reader        (pypdf / python-docx)              │
│  Stage 2   Keyword Extractor    (Python regex + skill dict)        │
│  Stage 3   Analyzer             (1 Gemini call)                    │
│  Stage 4   Query Optimizer      (Python — 18 URLs built)           │
│  Stage 5   Job Search Agent     (requests + BeautifulSoup)         │
│  Stage 6   URL Filter           (Python string matching)           │
│  Stage 7   Job Scraper Agent    (BeautifulSoup + Playwright)       │
│  Stage 8   Date Normalizer      (Python + dateparser)              │
│  Stage 9   Duplicate Remover    (URL norm + rapidfuzz)             │
│  Stage 10  Relevance Scorer     (Python 5-signal scorer)           │
│                                                                     │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
              Ranked Job Cards shown in UI
                             │
                    User selects jobs
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PHASE 2 — Auto Apply Pipeline                    │
│                                                                     │
│  Stage 1   Profile Loader       (user form in UI)                  │
│  Stage 2   Cover Letter Gen     (1 Gemini call per job)            │
│  Stage 3   Application Agent    (Playwright browser automation)    │
│  Stage 4   Form Filler          (CSS selectors + field detection)  │
│  Stage 5   Resume Attacher      (file input automation)            │
│  Stage 6   Submitter            (click + submit)                   │
│  Stage 7   Result Logger        (Applied / Failed / Manual)        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
              Application Log shown in UI
```

---

## File Structure

```
Multi-Agent-Job-Finder/
│
├── app.py                                  ← Streamlit UI (Phase 1 + Phase 2 tabs)
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── data/
│   └── sample_resumes/                     ← Sample PDF/DOCX resumes for testing
│
├── src/
│   └── resume_job_matcher/
│       │
│       ├── __init__.py
│       ├── config.py                       ← Pydantic settings + .env loader
│       ├── pipeline.py                     ← Phase 1 pipeline orchestrator
│       │
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── resume_reader.py            ← PDF/DOCX text extractor
│       │   └── scrape_url.py               ← Single URL scraper wrapper
│       │
│       ├── chains/
│       │   ├── __init__.py
│       │   ├── analyzer.py                 ← Single Gemini call → profile + queries
│       │   └── cover_letter_generator.py   ← Phase 2: Gemini cover letter per job
│       │
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── job_search_agent.py         ← Multi-board job URL collector
│       │   ├── job_scraper_agent.py        ← BeautifulSoup + Playwright scraper
│       │   └── apply_agent.py             ← Phase 2: Playwright auto-apply agent
│       │
│       └── processors/
│           ├── __init__.py
│           ├── keyword_extractor.py        ← Python resume keyword parser
│           ├── query_optimizer.py          ← Search query + URL builder
│           ├── url_filter.py               ← Junk URL removal
│           ├── date_normalizer.py          ← Multi-format date parser + range filter
│           ├── date_filter.py              ← Date filter wrapper
│           ├── duplicate_remover.py        ← URL norm + fuzzy dedup
│           ├── relevance_scorer.py         ← 5-signal relevance scorer
│           └── application_logger.py       ← Phase 2: log apply results
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
| Playwright | Required for dynamic scraping + Phase 2 auto-apply |

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

# 4. Install Playwright browser (required for Phase 2, recommended for Phase 1)
playwright install chromium

# 5. Set up environment variables
cp .env.example .env
# Open .env and add your GEMINI_API_KEY

# 6. Run the app
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

> Never commit `.env` to GitHub. `.env.example` is safe to commit.

---

## How It Works — Phase 1

```
User uploads Resume (PDF / DOCX)
         ↓
Stage 1: Resume Reader — pypdf / python-docx → clean text
         ↓
Stage 2: Keyword Extractor — regex + 100+ skill dict
         → skills, years of experience, location, job title
         ↓
Stage 3: Single Gemini Call (only LLM call in Phase 1)
         → candidate role, seniority, 3 search queries, top skills
         ↓
Stage 4: Query Optimizer — Python
         → enhances queries, builds 18 job board URLs
         ↓
Stage 5: Job Search Agent — requests + BeautifulSoup
         → LinkedIn, Rozee.pk, Indeed, Glassdoor, Mustakbil, Google Jobs
         ↓
Stage 6: URL Filter — Python
         → removes GitHub, Medium, YouTube, tutorials, docs
         ↓
Stage 7: Job Scraper — BeautifulSoup + Playwright
         → title, company, location, date, description, employment type
         ↓
Stage 8: Date Normalizer + Filter — Python + dateparser
         → all formats → datetime → From/To date range filter
         ↓
Stage 9: Duplicate Remover — Python + rapidfuzz
         → URL normalization + fuzzy title+company match (85% threshold)
         ↓
Stage 10: Relevance Scorer — Python
         → 5 signals → percentage → sorted descending
         ↓
Streamlit shows ranked job cards with match %, source, date, apply link
```

---

## How It Works — Phase 2

```
User reviews Phase 1 results
         ↓
User selects jobs to apply to (checkboxes)
         ↓
User fills applicant profile once in UI:
  → Full name, email, phone, LinkedIn URL
  → Years of experience, notice period, expected salary
         ↓
For each selected job:
         ↓
  Cover Letter Generator — 1 Gemini call
  → Personalizes cover letter for that job + company
         ↓
  Apply Agent — Playwright
  → Opens job application in headless browser
  → Detects platform (LinkedIn Easy Apply / Indeed / Rozee.pk)
  → Fills all form fields automatically
  → Attaches resume PDF
  → Pastes cover letter
  → Clicks submit
         ↓
  Result Logger:
  → "Applied"         — confirmation detected
  → "Failed"          — error or captcha
  → "Manual Required" — complex multi-step form
         ↓
Application log shown in UI + CSV export
```

---

## Relevance Scoring Algorithm

| Signal | Max Points | How |
|---|---|---|
| Job Title Match | 30 | Candidate role keywords in job title (partial scoring) |
| Skill Match | 60 | Top skills from analyzer in description (20pts × 3 max) |
| Keyword Match | 30 | Resume skills in description (10pts × 3 max) |
| Location Match | 10 | City match — remote always matches |
| Seniority Match | 10 | Junior/Mid/Senior signal words |
| Employment Type | 5 | Remote/Full-time/Hybrid match |
| **Total** | **145 → 100%** | Sorted descending, date as tiebreaker |

---

## Date Filtering Algorithm

| Format | Example | Method |
|---|---|---|
| Relative | `3 days ago`, `yesterday`, `just now` | Regex → today minus N days |
| Long form | `August 10, 2026`, `10 Aug 2026` | strptime (13 formats) |
| ISO | `2026-08-10` | strptime |
| Fuzzy | anything else | dateparser library |
| Not found | — | None → "Date Not Available" |

Jobs with no date shown separately — never fabricated.

---

## Duplicate Removal

**Pass 1 — URL normalization:**
Strips `utm_*`, `trk`, `fbclid`, `www.`, trailing slashes. Same URL from two queries → second dropped.

**Pass 2 — Fuzzy title + company:**
`token_sort_ratio` from rapidfuzz. Threshold: 85/100. Handles word order differences across boards.

---

## Technologies

| Layer | Technology | Purpose |
|---|---|---|
| UI | Streamlit | Local web interface |
| LLM | Google Gemini (gemini-3.6-flash) | Resume analysis + cover letters |
| PDF | pypdf | Resume text extraction |
| DOCX | python-docx | Resume text extraction |
| Static scraping | requests + BeautifulSoup | Job page extraction |
| Dynamic scraping + apply | Playwright | JS pages + Phase 2 automation |
| Date parsing | dateparser + python-dateutil | Multi-format normalization |
| Fuzzy matching | rapidfuzz | Dedup + title similarity |
| Config | python-dotenv + pydantic-settings | .env loader |
| LLM framework | langchain-google-genai | Gemini integration |

---

## API Requirements

| Service | Required | Cost | Purpose |
|---|---|---|---|
| Google Gemini API | ✅ Yes | Free tier available | Phase 1: 1 call/run · Phase 2: 1 call/job |
| LinkedIn API | ❌ No | — | Public pages only |
| Indeed API | ❌ No | — | Public pages only |
| Tavily | ❌ Removed | Was paid | Replaced with Python |

---

## Limitations

- **LinkedIn / Indeed rate limiting** — Heavy usage may trigger blocks. System uses random delays and realistic headers.
- **Captcha on apply** — Phase 2 will hit captcha on some platforms. Logged as "Manual Required".
- **LinkedIn Easy Apply only** — Phase 2 supports Easy Apply. External application pages need manual apply.
- **Date availability** — Not all postings include dates. Shown as "Date Not Available" — never fabricated.
- **Local only** — Runs on your machine. No cloud deployment.
- **Single LLM provider** — Only Gemini supported currently.

---

## Future Improvements

- [ ] Phase 2: LinkedIn Easy Apply automation (in progress)
- [ ] Phase 2: Indeed Apply automation (in progress)
- [ ] Phase 2: Rozee.pk Apply automation (in progress)
- [ ] Application tracking dashboard (Applied / Saved / Rejected)
- [ ] Email notification when new matching jobs posted
- [ ] Salary range filter
- [ ] Multi-language resume support
- [ ] OpenAI / Anthropic as alternative LLM providers

---

## Author

**Vishal Sahil** — AI Developer

- 🐙 [github.com/vishalsahilai](https://github.com/vishalsahilai)

---

MIT License — Free to use, modify, and distribute.

> Built with ❤️ · Powered by Python + Google Gemini · Minimum API, Maximum Intelligence