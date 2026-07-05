# Clearance Desk (Hybrid ATS Scorer)

A hybrid resume parser and ATS-style scoring tool that compares a candidate's
resume against a job description and returns a fit score with a breakdown.

## Why "hybrid"?

Most resumes have deterministic fields (email, phone, LinkedIn/GitHub) that
regex handles perfectly well — no need to pay for an LLM call every time.
This project uses **rule-based extraction first** (spaCy + regex) and only
**falls back to Gemini** when the rules can't confidently extract a field
(e.g., unusual resume layout, missing name detection, sparse skills list).
This keeps the tool fast and cheap for well-formatted resumes while staying
robust for messy ones.

## Features

- **Extraction:** name, email, phone, LinkedIn, GitHub, skills, education,
  experience, years of experience.
- **Scoring:** weighted combination of
  - Fuzzy keyword/skill overlap (`rapidfuzz`)
  - Semantic similarity (Gemini embeddings, with a Jaccard fallback if no API
    key is provided — the app degrades gracefully rather than breaking)
  - Years-of-experience match against the JD's stated requirement
- **Gap analysis:** LLM-generated summary of the candidate's strengths and
  weakest area relative to the JD.
- **UI:** Streamlit app with score gauge, breakdown bar chart, and
  matched/missing skill lists.

## Setup

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp .env.example .env   # then add your Gemini API key
streamlit run app.py
```

The app also works **without** a Gemini API key — it falls back to
rule-based-only extraction and a word-overlap similarity score. This means
the app never hard-fails just because a key is missing, which is useful for
demoing without exposing your key.

## Project structure

```
resume-jd-matcher/
├── app.py            # Streamlit UI
├── extraction.py      # Hybrid resume parsing (rules + LLM fallback)
├── scoring.py          # ATS scoring: keyword, semantic, experience
├── requirements.txt
└── .env.example
```

## Possible extensions (good for a v2 / follow-up commit)

- Batch mode: score many resumes against one JD, rank candidates
- Resume rewrite suggestions targeting the missing keywords
- Support for more file types (RTF, image-based PDFs via OCR)
- Swap the seed skill list for a taxonomy (e.g., ESCO or O*NET) for broader coverage
- Cache LLM calls to avoid re-parsing the same resume on every rerun

## Deployment

Tested for deployment on **Streamlit Community Cloud** or **Render** (same
pattern as other projects in this portfolio). Remember to set `GEMINI_API_KEY`
as a secret/environment variable on the platform rather than committing `.env`.

<img width="1440" height="900" alt="Screenshot 2026-07-05 at 20 12 38" src="https://github.com/user-attachments/assets/4f8be5a4-01e6-4d71-9706-dbb518e81d2c" />

