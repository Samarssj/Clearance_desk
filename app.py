"""Clearance Desk — a focused resume-to-role fit review surface."""

import os
import tempfile

import streamlit as st
from dotenv import load_dotenv

from extraction import configure_gemini, parse_resume
from scoring import score_resume
from ui import (
    CUSTOM_CSS,
    render_bars,
    render_candidate_card,
    render_chips,
    render_gauge,
    render_metric_card,
    render_signal_panel,
    render_stamp,
)

load_dotenv()

st.set_page_config(
    page_title="Clearance Desk · Fit Review",
    page_icon="▣",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar: quiet product context instead of a generic control rail
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown(
        '<div class="sidebar-brand">'
        '<div class="sidebar-kicker">Private review console</div>'
        '<div class="sidebar-title">Clearance Desk</div>'
        '<div class="sidebar-copy">A compact screening workspace for reading candidate files against a live role brief.</div>'
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="system-status">RULE ENGINE ONLINE</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section-title">Scoring model</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="weight-row"><span>Skill overlap</span><b>45%</b></div>'
        '<div class="weight-row"><span>Semantic similarity</span><b>35%</b></div>'
        '<div class="weight-row"><span>Experience match</span><b>20%</b></div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section-title">Decision key</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="verdict-key">'
        '<div class="key-row"><span class="key-dot" style="background:var(--mint)"></span><span><b>CLEARED</b> · 75 and up</span></div>'
        '<div class="key-row"><span class="key-dot" style="background:var(--amber)"></span><span><b>CONDITIONAL</b> · 50–74</span></div>'
        '<div class="key-row"><span class="key-dot" style="background:var(--rose)"></span><span><b>REJECTED</b> · below 50</span></div>'
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

_gemini_key = os.getenv("GEMINI_API_KEY", "")
gemini_model = configure_gemini(_gemini_key) if _gemini_key else None
if not gemini_model:
    st.sidebar.markdown(
        '<div class="sidebar-section"><div class="sidebar-section-title">Mode note</div>'
        '<div class="sidebar-copy">No Gemini key detected. Clearance Desk will use deterministic extraction and word-overlap similarity for this session.</div></div>',
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Header and intake
# ---------------------------------------------------------------------------

st.markdown(
    '<div class="app-topbar">'
    '<div class="brand-lockup"><div class="brand-mark">⌁</div><div>'
    '<div class="brand-name">Clearance Desk</div>'
    '<div class="brand-sub">Resume intelligence / 01</div>'
    '</div></div>'
    '<div class="topbar-status">Local workspace</div>'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="hero-grid">'
    '<div><div class="hero-kicker">Candidate fit review</div>'
    '<h1 class="hero-title">Turn a resume into a <em>clear signal.</em></h1>'
    '<p class="hero-copy">Drop in a candidate file, add the target role, and get a transparent fit readout built for the moment before the interview slate.</p>'
    '</div>'
    '<div class="hero-aside"><div class="hero-kicker">How it works</div>'
    '<div class="hero-aside-title">A fast, explainable first pass.</div>'
    '<div class="hero-aside-row"><b>01</b><span>Extract contact details, skills, and experience from the candidate file.</span></div>'
    '<div class="hero-aside-row"><b>02</b><span>Compare the profile against the language and requirements in the role brief.</span></div>'
    '<div class="hero-aside-row"><b>03</b><span>Review the score, the evidence, and the gaps before making a call.</span></div>'
    '</div></div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-heading"><div><div class="section-kicker">01 / Intake</div>'
    '<div class="section-title">Set up a clearance scan</div></div>'
    '<div class="section-note">PDF, DOCX, or TXT · no files leave this workspace</div></div>',
    unsafe_allow_html=True,
)

intake_left, intake_right = st.columns([0.95, 1.25], gap="large")
with intake_left:
    st.markdown(
        '<div class="intake-card"><div class="input-label">Candidate file</div>'
        '<div class="input-help">Upload the resume you want to review.</div>',
        unsafe_allow_html=True,
    )
    uploaded_file = st.file_uploader(
        "Candidate resume",
        type=["pdf", "docx", "txt"],
        label_visibility="collapsed",
        help="Supported formats: PDF, DOCX, TXT",
    )
    st.markdown('</div>', unsafe_allow_html=True)

with intake_right:
    st.markdown(
        '<div class="intake-card"><div class="input-label">Target role brief</div>'
        '<div class="input-help">Paste the job description or the requirements that matter most.</div>',
        unsafe_allow_html=True,
    )
    jd_text = st.text_area(
        "Job description",
        height=220,
        label_visibility="collapsed",
        placeholder="Paste the role's mission, required skills, experience level, and qualifications here…",
    )
    st.markdown('</div>', unsafe_allow_html=True)

run = st.button("Run clearance scan  →", use_container_width=True)

# ---------------------------------------------------------------------------
# Scan + results
# ---------------------------------------------------------------------------

if run:
    if not uploaded_file:
        st.warning("Add a candidate file to the intake tray before running the scan.")
    elif not jd_text.strip():
        st.warning("Paste a target role brief so the candidate can be scored against something concrete.")
    else:
        with st.spinner("Reading the candidate file…"):
            suffix = "." + uploaded_file.name.split(".")[-1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            try:
                resume = parse_resume(tmp_path, gemini_model=gemini_model)
            finally:
                os.unlink(tmp_path)

        with st.spinner("Comparing the profile with the role brief…"):
            result = score_resume(resume, jd_text, gemini_model=gemini_model)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="result-header"><div><div class="section-kicker">02 / Clearance readout</div>'
            '<div class="section-title">The signal is in</div></div>'
            '<div class="processing-note">PROFILE × ROLE BRIEF · COMPLETE</div></div>',
            unsafe_allow_html=True,
        )

        matched_count = len(result.matched_skills)
        missing_count = len(result.missing_skills)
        experience_text = f"{resume.years_experience:g} yrs" if resume.years_experience is not None else "Not detected"
        st.markdown(
            '<div class="metric-grid">'
            + render_metric_card("Overall fit", f"{result.overall_score:.1f}", "weighted signal", "mint")
            + render_metric_card("Matched skills", str(matched_count), "from the role brief", "blue")
            + render_metric_card("Flagged gaps", str(missing_count), "to investigate", "rose")
            + render_metric_card("Experience", experience_text, "detected in resume", "amber")
            + '</div>',
            unsafe_allow_html=True,
        )

        verdict_col, gauge_col, candidate_col = st.columns([0.95, 1.15, 1.05], gap="medium")
        with verdict_col:
            label = "Ready for shortlist" if result.overall_score >= 75 else "Needs human review"
            st.markdown(
                '<div class="verdict-panel"><div class="verdict-panel-top">'
                '<div><div class="panel-kicker">Decision layer</div>'
                f'<div class="verdict-panel-title">{label}</div></div>'
                '<div class="status-dot"></div></div>'
                + render_stamp(result.overall_score)
                + '<div class="verdict-foot">A weighted reading, not a final hiring decision. Use the evidence below to guide the next conversation.</div></div>',
                unsafe_allow_html=True,
            )
            if resume.used_llm_fallback:
                st.caption("Ambiguous layout detected; LLM fallback helped complete the extraction.")

        with gauge_col:
            st.markdown(render_gauge(result.overall_score), unsafe_allow_html=True)

        with candidate_col:
            st.markdown(render_candidate_card(resume, uploaded_file.name), unsafe_allow_html=True)

        st.markdown('<div class="detail-grid">', unsafe_allow_html=True)
        breakdown_col, evidence_col = st.columns([1.05, 0.95], gap="medium")
        with breakdown_col:
            st.markdown(
                '<div class="detail-card"><div class="detail-card-header">'
                '<div><div class="panel-kicker">Signal composition</div><div class="detail-card-title">What shaped the score</div></div>'
                '<div class="detail-card-note">WEIGHTED</div></div>'
                + render_bars([
                    ("Skill overlap", result.keyword_score, "var(--blue)", "45% weight"),
                    ("Semantic similarity", result.semantic_score, "var(--mint)", "35% weight"),
                    ("Experience match", result.experience_score, "var(--amber)", "20% weight"),
                ])
                + '</div>',
                unsafe_allow_html=True,
            )
        with evidence_col:
            gap_copy = result.gap_summary or "No AI field note was generated in this session. Use the matched and missing skill evidence as the review starting point."
            st.markdown(render_signal_panel("Field note", "Recruiter lens", gap_copy, "amber"), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="detail-grid">', unsafe_allow_html=True)
        matched_col, missing_col = st.columns(2, gap="medium")
        with matched_col:
            st.markdown(
                '<div class="detail-card"><div class="detail-card-header">'
                '<div><div class="panel-kicker">Evidence / aligned</div><div class="detail-card-title">Matched skills</div></div>'
                f'<div class="detail-card-note">{matched_count} SIGNALS</div></div>'
                + render_chips(result.matched_skills, "matched")
                + '</div>',
                unsafe_allow_html=True,
            )
        with missing_col:
            st.markdown(
                '<div class="detail-card"><div class="detail-card-header">'
                '<div><div class="panel-kicker">Evidence / investigate</div><div class="detail-card-title">Flagged gaps</div></div>'
                f'<div class="detail-card-note">{missing_count} SIGNALS</div></div>'
                + render_chips(result.missing_skills, "missing")
                + '</div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-kicker">03 / Source record</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title" style="margin:.4rem 0 1rem;">Extracted candidate data</div>', unsafe_allow_html=True)
        with st.expander("Open the raw extraction record"):
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
