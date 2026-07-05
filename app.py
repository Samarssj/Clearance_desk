"""
app.py
Streamlit UI for the Resume-JD Matcher — styled as a "clearance desk":
a candidate file gets scanned against a role brief and comes back stamped.
"""

import os
import tempfile

import streamlit as st
from dotenv import load_dotenv

from extraction import parse_resume, configure_gemini
from scoring import score_resume
from ui import CUSTOM_CSS, render_stamp, render_gauge, render_chips, render_bars

load_dotenv()

st.set_page_config(page_title="Clearance Desk · Resume Matcher", page_icon="🗂️", layout="wide")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Masthead
# ---------------------------------------------------------------------------

st.markdown(
    """
    <span class="eyebrow">Clearance Desk</span>
    <h1 class="masthead-title">Resume ↔ Role Matcher</h1>
    <p class="masthead-sub">Every file gets scanned, scored, and stamped against the role brief.</p>
    """,
    unsafe_allow_html=True,
)
st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown('<span class="eyebrow">Scoring Weights</span>', unsafe_allow_html=True)
    st.markdown(
        "- **45%** Skill overlap (fuzzy matched)\n"
        "- **35%** Semantic similarity\n"
        "- **20%** Experience match"
    )
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<span class="eyebrow">Verdict Key</span>', unsafe_allow_html=True)
    st.markdown(
        "- 🟢 **CLEARED** — 75+\n"
        "- 🟡 **CONDITIONAL** — 50–74\n"
        "- 🔴 **REJECTED** — below 50"
    )

_gemini_key = os.getenv("GEMINI_API_KEY", "")
gemini_model = configure_gemini(_gemini_key) if _gemini_key else None
if not gemini_model:
    st.sidebar.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.sidebar.caption("LLM fallback disabled — running on rules only.")

# ---------------------------------------------------------------------------
# Intake
# ---------------------------------------------------------------------------

col1, col2 = st.columns(2)

with col1:
    st.markdown('<span class="eyebrow">Intake — Candidate File</span>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("PDF or DOCX", type=["pdf", "docx", "txt"], label_visibility="collapsed")

with col2:
    st.markdown('<span class="eyebrow">Target Role Brief</span>', unsafe_allow_html=True)
    jd_text = st.text_area(
        "Job description", height=260, label_visibility="collapsed",
        placeholder="Paste the role's required skills, experience, and qualifications here…",
    )

run = st.button("Run Clearance Scan", use_container_width=True)

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

if run:
    if not uploaded_file:
        st.warning("No file in the intake tray — upload a resume to begin the scan.")
    elif not jd_text.strip():
        st.warning("The role brief is empty — paste a job description to score against.")
    else:
        with st.spinner("Reading the file…"):
            suffix = "." + uploaded_file.name.split(".")[-1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name
            resume = parse_resume(tmp_path, gemini_model=gemini_model)
            os.unlink(tmp_path)

        with st.spinner("Scoring against the brief…"):
            result = score_resume(resume, jd_text, gemini_model=gemini_model)

        st.markdown('<hr class="divider">', unsafe_allow_html=True)

        verdict_col, gauge_col, file_col = st.columns([1, 1.2, 1.4])

        with verdict_col:
            st.markdown('<span class="eyebrow">Verdict</span>', unsafe_allow_html=True)
            st.markdown(render_stamp(result.overall_score), unsafe_allow_html=True)
            if resume.used_llm_fallback:
                st.caption("LLM fallback engaged — layout was ambiguous for rules alone.")

        with gauge_col:
            st.markdown('<span class="eyebrow">Fit Reading</span>', unsafe_allow_html=True)
            st.markdown(render_gauge(result.overall_score), unsafe_allow_html=True)

        with file_col:
            st.markdown('<span class="eyebrow">Candidate File</span>', unsafe_allow_html=True)
            file_card_html = (
                '<div class="file-card">'
                f'<div><span class="field-label">NAME</span>{resume.name or "—"}</div>'
                f'<div><span class="field-label">EMAIL</span>{resume.email or "—"}</div>'
                f'<div><span class="field-label">PHONE</span>{resume.phone or "—"}</div>'
                f'<div><span class="field-label">EXPERIENCE</span>{resume.years_experience or "N/A"} yrs (detected)</div>'
                '</div>'
            )
            st.markdown(file_card_html, unsafe_allow_html=True)

        st.markdown('<hr class="divider">', unsafe_allow_html=True)

        st.markdown('<span class="eyebrow">Score Breakdown</span>', unsafe_allow_html=True)
        st.markdown(
            render_bars([
                ("Skill Overlap", result.keyword_score, "var(--amber)"),
                ("Semantic Similarity", result.semantic_score, "var(--mint)"),
                ("Experience Match", result.experience_score, "var(--rose)"),
            ]),
            unsafe_allow_html=True,
        )

        st.markdown('<hr class="divider">', unsafe_allow_html=True)

        chip_col1, chip_col2 = st.columns(2)
        with chip_col1:
            st.markdown('<span class="eyebrow">Matched Skills</span>', unsafe_allow_html=True)
            st.markdown(render_chips(result.matched_skills, "matched"), unsafe_allow_html=True)
        with chip_col2:
            st.markdown('<span class="eyebrow">Flagged Gaps</span>', unsafe_allow_html=True)
            st.markdown(render_chips(result.missing_skills, "missing"), unsafe_allow_html=True)

        st.markdown('<hr class="divider">', unsafe_allow_html=True)

        st.markdown('<span class="eyebrow">Field Notes</span>', unsafe_allow_html=True)
        if result.gap_summary:
            st.markdown(f'<div class="field-note">{result.gap_summary}</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="field-note">No AI notes on file — connect a Gemini key server-side '
                'to generate a written fit summary.</div>',
                unsafe_allow_html=True,
            )

        with st.expander("Raw extracted resume data"):
            st.json({
                "name": resume.name,
                "email": resume.email,
                "phone": resume.phone,
                "linkedin": resume.linkedin,
                "github": resume.github,
                "skills": resume.skills,
                "education": resume.education,
                "experience": resume.experience,
                "years_experience": resume.years_experience,
            })
