"""
scoring.py
ATS-style scoring: compares a ParsedResume against a job description using
(1) fuzzy keyword/skill overlap, (2) semantic embedding similarity, and
(3) an LLM-generated gap analysis.
"""

import re
import json
import numpy as np
from dataclasses import dataclass, field
from typing import Optional

from rapidfuzz import fuzz

from extraction import ParsedResume, SKILL_KEYWORDS


@dataclass
class ScoreResult:
    overall_score: float = 0.0
    keyword_score: float = 0.0
    semantic_score: float = 0.0
    experience_score: float = 0.0
    matched_skills: list = field(default_factory=list)
    missing_skills: list = field(default_factory=list)
    gap_summary: Optional[str] = None


# ---------------------------------------------------------------------------
# JD skill extraction (reuses the same seed skill list + fuzzy match to
# catch skills not in the seed list but present in the JD text)
# ---------------------------------------------------------------------------

def extract_jd_skills(jd_text: str) -> list:
    jd_lower = jd_text.lower()
    found = [kw for kw in SKILL_KEYWORDS if kw in jd_lower]

    # Also pull out capitalized multi-word phrases near "experience with/in"
    extra = re.findall(
        r"(?:experience (?:with|in)|proficiency in|knowledge of)\s+([A-Za-z0-9,\s./+-]{3,40})",
        jd_text, flags=re.IGNORECASE
    )
    for chunk in extra:
        for token in re.split(r",| and ", chunk):
            token = token.strip().lower()
            if 2 < len(token) < 30 and token not in found:
                found.append(token)
    return list(dict.fromkeys(found))  # dedupe, preserve order


# ---------------------------------------------------------------------------
# Keyword / fuzzy overlap score
# ---------------------------------------------------------------------------

def keyword_overlap_score(resume_skills: list, jd_skills: list, threshold: int = 80):
    if not jd_skills:
        return 100.0, [], []

    matched, missing = [], []
    resume_skills_lower = [s.lower() for s in resume_skills]

    for jd_skill in jd_skills:
        best = max(
            (fuzz.token_sort_ratio(jd_skill, rs) for rs in resume_skills_lower),
            default=0,
        )
        if best >= threshold:
            matched.append(jd_skill)
        else:
            missing.append(jd_skill)

    score = 100.0 * len(matched) / len(jd_skills)
    return score, matched, missing


# ---------------------------------------------------------------------------
# Semantic similarity score (via Gemini embeddings, with graceful fallback)
# ---------------------------------------------------------------------------

def semantic_similarity_score(resume_text: str, jd_text: str, embed_fn=None) -> float:
    """
    embed_fn: a function(text) -> np.array embedding. If None, falls back to
    a crude word-overlap Jaccard score so the app still works without an API key.
    """
    if embed_fn is not None:
        try:
            r_vec = np.array(embed_fn(resume_text))
            j_vec = np.array(embed_fn(jd_text))
            cos_sim = float(
                np.dot(r_vec, j_vec) / (np.linalg.norm(r_vec) * np.linalg.norm(j_vec) + 1e-8)
            )
            return max(0.0, min(1.0, cos_sim)) * 100
        except Exception:
            pass

    # Fallback: Jaccard similarity over lowercase word sets
    r_words = set(re.findall(r"[a-z]{3,}", resume_text.lower()))
    j_words = set(re.findall(r"[a-z]{3,}", jd_text.lower()))
    if not r_words or not j_words:
        return 0.0
    jaccard = len(r_words & j_words) / len(r_words | j_words)
    return jaccard * 100


# ---------------------------------------------------------------------------
# Experience score (very simple heuristic; extend as needed)
# ---------------------------------------------------------------------------

def experience_score(resume_years: Optional[float], jd_text: str) -> float:
    jd_years_match = re.search(r"(\d+)\+?\s*years?", jd_text.lower())
    required_years = float(jd_years_match.group(1)) if jd_years_match else 0.0

    if required_years == 0:
        return 100.0
    if resume_years is None:
        return 40.0  # unknown, partial credit
    if resume_years >= required_years:
        return 100.0
    return max(0.0, 100.0 * resume_years / required_years)


# ---------------------------------------------------------------------------
# LLM gap analysis
# ---------------------------------------------------------------------------

GAP_PROMPT = """You are an ATS/recruiter assistant. Given the resume summary
and job description below, write a concise 3-4 sentence analysis of the
candidate's fit: what stands out as strong, and what's the biggest gap or
missing qualification. Be direct and specific, no fluff.

Resume skills: {skills}
Resume experience: {experience}

Job description:
---
{jd_text}
---
"""


def generate_gap_summary(model, resume: ParsedResume, jd_text: str) -> Optional[str]:
    if model is None:
        return None
    try:
        prompt = GAP_PROMPT.format(
            skills=", ".join(resume.skills) or "none listed",
            experience="; ".join(resume.experience) or "not extracted",
            jd_text=jd_text[:4000],
        )
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Main scoring entry point
# ---------------------------------------------------------------------------

WEIGHTS = {"keyword": 0.45, "semantic": 0.35, "experience": 0.20}


def score_resume(resume: ParsedResume, jd_text: str, gemini_model=None,
                  embed_fn=None) -> ScoreResult:
    jd_skills = extract_jd_skills(jd_text)
    kw_score, matched, missing = keyword_overlap_score(resume.skills, jd_skills)
    sem_score = semantic_similarity_score(resume.raw_text, jd_text, embed_fn=embed_fn)
    exp_score = experience_score(resume.years_experience, jd_text)

    overall = (
        WEIGHTS["keyword"] * kw_score
        + WEIGHTS["semantic"] * sem_score
        + WEIGHTS["experience"] * exp_score
    )

    gap_summary = generate_gap_summary(gemini_model, resume, jd_text)

    return ScoreResult(
        overall_score=round(overall, 1),
        keyword_score=round(kw_score, 1),
        semantic_score=round(sem_score, 1),
        experience_score=round(exp_score, 1),
        matched_skills=matched,
        missing_skills=missing,
        gap_summary=gap_summary,
    )
