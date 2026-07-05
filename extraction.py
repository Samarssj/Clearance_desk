"""
extraction.py
Hybrid resume parser: fast regex/spaCy rules for structured fields,
Gemini LLM fallback for messy/ambiguous sections and semantic normalization.
"""

import re
import json
import os
from dataclasses import dataclass, field
from typing import Optional

import pdfplumber
from docx import Document
import google.generativeai as genai


def configure_gemini(api_key: Optional[str] = None):
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        return None
    genai.configure(api_key=key)
    return genai.GenerativeModel("gemini-2.0-flash")


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class ParsedResume:
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    skills: list = field(default_factory=list)
    education: list = field(default_factory=list)
    experience: list = field(default_factory=list)
    years_experience: Optional[float] = None
    raw_text: str = ""
    used_llm_fallback: bool = False


# ---------------------------------------------------------------------------
# File loading
# ---------------------------------------------------------------------------

def load_text(file_path: str) -> str:
    if file_path.lower().endswith(".pdf"):
        text = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text.append(page.extract_text() or "")
        return "\n".join(text)
    elif file_path.lower().endswith(".docx"):
        doc = Document(file_path)
        return "\n".join(p.text for p in doc.paragraphs)
    else:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()


# ---------------------------------------------------------------------------
# Rule-based extraction (fast, deterministic, free)
# ---------------------------------------------------------------------------

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}")
LINKEDIN_RE = re.compile(r"(https?://)?(www\.)?linkedin\.com/in/[A-Za-z0-9\-_/]+")
GITHUB_RE = re.compile(r"(https?://)?(www\.)?github\.com/[A-Za-z0-9\-_/]+")

SECTION_HEADERS = ["experience", "work experience", "education", "skills",
                   "projects", "certifications", "summary", "objective"]

# A reasonably broad seed skill list; extend as needed
SKILL_KEYWORDS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "sql", "r",
    "react", "node.js", "django", "flask", "streamlit", "fastapi",
    "aws", "gcp", "azure", "docker", "kubernetes", "terraform",
    "machine learning", "deep learning", "nlp", "computer vision",
    "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    "mongodb", "postgresql", "mysql", "redis", "git", "ci/cd",
    "rest api", "graphql", "microservices", "agile", "scrum",
]


def rule_based_extract(text: str) -> ParsedResume:
    resume = ParsedResume(raw_text=text)

    email_match = EMAIL_RE.search(text)
    resume.email = email_match.group(0) if email_match else None

    phone_match = PHONE_RE.search(text)
    resume.phone = phone_match.group(0).strip() if phone_match else None

    li_match = LINKEDIN_RE.search(text)
    resume.linkedin = li_match.group(0) if li_match else None

    gh_match = GITHUB_RE.search(text)
    resume.github = gh_match.group(0) if gh_match else None

    # Name: heuristic - first non-empty line that isn't an email/phone/header
    for line in text.strip().split("\n")[:5]:
        line = line.strip()
        if line and not EMAIL_RE.search(line) and not PHONE_RE.search(line) \
                and len(line.split()) <= 5:
            resume.name = line
            break

    # Skills: keyword match against seed list (case-insensitive)
    text_lower = text.lower()
    resume.skills = [kw for kw in SKILL_KEYWORDS if kw in text_lower]

    # Years of experience: look for patterns like "5 years", "3+ years"
    years_match = re.search(r"(\d+)\+?\s*years?", text_lower)
    if years_match:
        resume.years_experience = float(years_match.group(1))

    return resume


def rule_confidence_ok(resume: ParsedResume) -> bool:
    """Decide if rule-based extraction is 'good enough' or needs LLM fallback."""
    missing = sum([
        resume.name is None,
        resume.email is None,
        len(resume.skills) == 0,
    ])
    return missing == 0


# ---------------------------------------------------------------------------
# LLM fallback (Gemini) - used only when rules are low-confidence
# ---------------------------------------------------------------------------

LLM_EXTRACT_PROMPT = """You are a resume parsing engine. Extract structured
information from the resume text below. Return ONLY valid JSON, no markdown
fences, no commentary, matching this exact schema:

{{
  "name": string or null,
  "email": string or null,
  "phone": string or null,
  "skills": [string],
  "education": [string],
  "experience": [string],
  "years_experience": number or null
}}

Normalize skill names to common industry terms (e.g. "ML" -> "Machine Learning").

Resume text:
---
{resume_text}
---
"""


def llm_extract(model, text: str) -> Optional[dict]:
    if model is None:
        return None
    try:
        response = model.generate_content(
            LLM_EXTRACT_PROMPT.format(resume_text=text[:8000])
        )
        cleaned = response.text.strip().strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        return json.loads(cleaned)
    except Exception:
        return None


def merge_llm_result(resume: ParsedResume, llm_data: dict) -> ParsedResume:
    """Fill only the gaps left by rule-based extraction; don't overwrite good data."""
    resume.name = resume.name or llm_data.get("name")
    resume.email = resume.email or llm_data.get("email")
    resume.phone = resume.phone or llm_data.get("phone")
    if not resume.skills and llm_data.get("skills"):
        resume.skills = llm_data["skills"]
    elif llm_data.get("skills"):
        # merge + dedupe, case-insensitive
        seen = {s.lower() for s in resume.skills}
        for s in llm_data["skills"]:
            if s.lower() not in seen:
                resume.skills.append(s)
                seen.add(s.lower())
    resume.education = llm_data.get("education") or resume.education
    resume.experience = llm_data.get("experience") or resume.experience
    resume.years_experience = resume.years_experience or llm_data.get("years_experience")
    resume.used_llm_fallback = True
    return resume


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def parse_resume(file_path: str, gemini_model=None) -> ParsedResume:
    text = load_text(file_path)
    resume = rule_based_extract(text)

    if not rule_confidence_ok(resume) and gemini_model is not None:
        llm_data = llm_extract(gemini_model, text)
        if llm_data:
            resume = merge_llm_result(resume, llm_data)

    return resume
