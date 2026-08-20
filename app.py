import os
import logging
from datetime import date, timedelta

import streamlit as st
from dotenv import load_dotenv

from src.resume_job_matcher.pipeline import run_pipeline

#  Config 

load_dotenv()
logging.basicConfig(level=logging.INFO)

st.set_page_config(
    page_title="AI Job Finder",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

#  Styles 

st.markdown("""
<style>
    .match-high   { color: #22c55e; font-weight: bold; }
    .match-mid    { color: #f59e0b; font-weight: bold; }
    .match-low    { color: #ef4444; font-weight: bold; }
    .job-card     { background: #1e1e2e; border-radius: 10px; padding: 16px; margin-bottom: 12px; border: 1px solid #2d2d44; }
    .badge        { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 12px; margin-right: 6px; }
    .badge-board  { background: #3b3b5c; color: #a5b4fc; }
    .badge-type   { background: #1e3a2f; color: #6ee7b7; }
    .stat-box     { background: #1e1e2e; border-radius: 8px; padding: 12px; text-align: center; border: 1px solid #2d2d44; }
</style>
""", unsafe_allow_html=True)


#  Sidebar 

with st.sidebar:
    st.title("💼 AI Job Finder")
    st.caption("Upload your resume — we find the best matches.")
    st.divider()

    # API Key
    api_key = st.text_input(
        "Gemini API Key",
        value=st.secrets.get("GEMINI_API_KEY", ""),
        type="password",
        help="Get your key at https://aistudio.google.com/app/apikey",
    )

    st.divider()
    st.subheader("🔧 Search Filters")

    # Location
    location = st.text_input("Location", placeholder="e.g. Karachi, Remote")

    # Employment Type
    employment_type = st.selectbox(
        "Employment Type",
        options=["Any", "Full-time", "Remote", "Hybrid", "On-site", "Contract"],
    )
    employment_type = None if employment_type == "Any" else employment_type

    # Date Range
    col1, col2 = st.columns(2)
    with col1:
        from_date = st.date_input("From Date", value=date.today() - timedelta(days=30))
    with col2:
        to_date = st.date_input("To Date", value=date.today())

    # Max Results
    max_results = st.slider("Max Job Results", min_value=10, max_value=100, value=50, step=10)

    st.divider()
    st.caption("Built with LangChain + Gemini + BeautifulSoup")


#  Main Area 

st.header("📄 Upload Your Resume")

uploaded_file = st.file_uploader(
    "Drag and drop or click to upload",
    type=["pdf", "docx"],
    help="PDF or DOCX only",
)

if uploaded_file:
    st.success(f"✅ Uploaded: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")

st.divider()

run_btn = st.button("🚀 Find Jobs", type="primary", use_container_width=True, disabled=not uploaded_file)

#  Pipeline Runner 

if run_btn:
    if not api_key:
        st.error("❌ Please enter your Gemini API key in the sidebar.")
        st.stop()

    if not uploaded_file:
        st.error("❌ Please upload a resume first.")
        st.stop()

    # Progress UI
    st.divider()
    st.subheader("⚙️ Pipeline Progress")

    STEP_LABELS = [
        "Reading resume",
        "Extracting skills & keywords",
        "Analyzing resume (AI — 1 call)",
        "Building search URLs",
        "Searching job boards",
        "Filtering junk URLs",
        "Scraping job details",
        "Filtering by date range",
        "Removing duplicates",
        "Scoring & ranking jobs",
    ]

    progress_bar = st.progress(0)
    step_cols = st.columns(5)
    step_status = {}

    # Render step placeholders
    placeholders = []
    rows = [st.columns(5), st.columns(5)]
    for i, label in enumerate(STEP_LABELS):
        row = rows[i // 5]
        col = row[i % 5]
        ph = col.empty()
        ph.markdown(f"⬜ **Step {i+1}**  \n{label}")
        placeholders.append(ph)

    status_ph = st.empty()

    def progress_callback(step: int, total: int, message: str):
        pct = int((step / total) * 100)
        progress_bar.progress(pct)
        status_ph.info(f"**Step {step}/{total}:** {message}")
        # Mark previous steps done
        for i in range(step - 1):
            placeholders[i].markdown(f"✅ **Step {i+1}**  \n{STEP_LABELS[i]}")
        # Mark current step active
        placeholders[step - 1].markdown(f"🔄 **Step {step}**  \n{STEP_LABELS[step-1]}")

    # Run pipeline
    with st.spinner("Running pipeline..."):
        result = run_pipeline(
            file=uploaded_file.getvalue(),
            filename=uploaded_file.name,
            gemini_api_key=api_key,
            location=location,
            employment_type=employment_type,
            from_date=from_date,
            to_date=to_date,
            max_results=max_results,
            progress_callback=progress_callback,
        )

    # Mark all done
    progress_bar.progress(100)
    status_ph.success("✅ Pipeline complete!")
    for i, ph in enumerate(placeholders):
        ph.markdown(f"✅ **Step {i+1}**  \n{STEP_LABELS[i]}")

    #  Error Handling 

    if result["status"] == "error":
        st.error(f"❌ Pipeline error: {result['error']}")
        st.stop()

    #  Candidate Profile 

    st.divider()
    st.subheader("👤 Candidate Profile")

    c = result["candidate"]
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Name",        c.get("name") or "—")
    p2.metric("Role",        c.get("candidate_role") or "—")
    p3.metric("Seniority",   c.get("seniority") or "—")
    p4.metric("Experience",  f"{c['years_exp']} yrs" if c.get("years_exp") else "—")

    if c.get("top_skills"):
        st.markdown("**Top Skills:** " + "  ".join([f"`{s}`" for s in c["top_skills"]]))

    if c.get("summary"):
        with st.expander("AI Summary"):
            st.write(c["summary"])

    #  Stats 

    st.divider()
    st.subheader("📊 Pipeline Stats")
    s = result["stats"]

    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("URLs Found",    s.get("raw_urls_found", 0))
    s2.metric("After Filter",  s.get("urls_after_filter", 0))
    s3.metric("Scraped",       s.get("jobs_scraped", 0))
    s4.metric("Unique Jobs",   s.get("jobs_after_dedup", 0))
    s5.metric("Final Results", s.get("final_job_count", 0))

    #  Results Table 

    jobs = result["jobs"]
    no_date_jobs = result["no_date_jobs"]

    st.divider()
    st.subheader(f"🎯 Matched Jobs ({len(jobs)})")

    if not jobs and not no_date_jobs:
        st.warning("No jobs found. Try adjusting the date range, location, or employment type.")
        st.stop()

    def render_jobs(job_list: list):
        for job in job_list:
            pct = job.get("match_percent", 0)
            if pct >= 70:
                pct_html = f'<span class="match-high">{pct}%</span>'
            elif pct >= 40:
                pct_html = f'<span class="match-mid">{pct}%</span>'
            else:
                pct_html = f'<span class="match-low">{pct}%</span>'

            board_badge = f'<span class="badge badge-board">{job.get("board", "")}</span>'
            type_badge  = f'<span class="badge badge-type">{job.get("employment_type", "")}</span>' if job.get("employment_type") else ""

            st.markdown(f"""
<div class="job-card">
  <div style="display:flex; justify-content:space-between; align-items:start;">
    <div>
      <strong style="font-size:16px;">{job.get("title", "Unknown Title")}</strong><br>
      <span style="color:#94a3b8;">{job.get("company", "Unknown Company")} &nbsp;·&nbsp; {job.get("location", "—")}</span><br>
      <small style="color:#64748b;">📅 {job.get("date_display", "Date Unknown")}</small>
    </div>
    <div style="text-align:right;">
      <span style="font-size:22px;">{pct_html}</span><br>
      <small>match</small>
    </div>
  </div>
  <div style="margin-top:8px;">{board_badge}{type_badge}</div>
  <div style="margin-top:10px;">
    <a href="{job.get('job_url', '#')}" target="_blank">
      <button style="background:#4f46e5;color:white;border:none;padding:6px 16px;border-radius:6px;cursor:pointer;">
        View Job →
      </button>
    </a>
    </div>
</div>
""", unsafe_allow_html=True)

            with st.expander("Score breakdown"):
                bd = job.get("score_breakdown", {})
                bc1, bc2, bc3 = st.columns(3)
                bc1.metric("Title Match",    f"{bd.get('title_match', 0)} pts")
                bc1.metric("Skill Match",    f"{bd.get('skill_match', 0)} pts")
                bc2.metric("Keyword Match",  f"{bd.get('keyword_match', 0)} pts")
                bc2.metric("Location Match", f"{bd.get('location_match', 0)} pts")
                bc3.metric("Seniority",      f"{bd.get('seniority_match', 0)} pts")
                bc3.metric("Emp. Type",      f"{bd.get('employment_type', 0)} pts")

    render_jobs(jobs)

    #  No-Date Jobs Section 
    if no_date_jobs:
        st.divider()
        with st.expander(f"📋 Jobs with Unknown Date ({len(no_date_jobs)}) — shown separately"):
            render_jobs(no_date_jobs)

    #  Download CSV 

    st.divider()
    if jobs or no_date_jobs:
        import csv
        import io

        all_jobs = jobs + no_date_jobs
        csv_buf = io.StringIO()
        writer = csv.DictWriter(csv_buf, fieldnames=[
            "title", "company", "location", "date_display",
            "employment_type", "match_percent", "board", "job_url"
        ])
        writer.writeheader()
        for j in all_jobs:
            writer.writerow({
                "title":           j.get("title", ""),
                "company":         j.get("company", ""),
                "location":        j.get("location", ""),
                "date_display":    j.get("date_display", ""),
                "employment_type": j.get("employment_type", ""),
                "match_percent":   j.get("match_percent", ""),
                "board":           j.get("board", ""),
                "job_url":         j.get("job_url", ""),
            })

        st.download_button(
            label="⬇️ Download Results as CSV",
            data=csv_buf.getvalue(),
            file_name="job_results.csv",
            mime="text/csv",
            use_container_width=True,
        )