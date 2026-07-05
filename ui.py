"""
ui.py
Hand-rolled visual components for the Resume-JD Matcher's "clearance desk"
aesthetic — no default Plotly widgets. Everything here returns raw HTML/SVG
strings meant to be rendered via st.markdown(..., unsafe_allow_html=True).
"""

import math

# ---------------------------------------------------------------------------
# Tier logic (shared by the stamp + gauge coloring)
# ---------------------------------------------------------------------------

def verdict_tier(score: float):
    if score >= 75:
        return "CLEARED", "var(--mint)"
    if score >= 50:
        return "CONDITIONAL", "var(--amber)"
    return "REJECTED", "var(--rose)"


# ---------------------------------------------------------------------------
# Verdict stamp — the signature element
# ---------------------------------------------------------------------------

def render_stamp(score: float) -> str:
    label, color = verdict_tier(score)
    return (
        f'<div class="stamp" style="border-color:{color}; color:{color};">'
        f'<span class="stamp-label">{label}</span>'
        f'<span class="stamp-sub">FILE SCORE {score:.1f}</span></div>'
    )


# ---------------------------------------------------------------------------
# Radar gauge — custom semicircle arc + needle (replaces Plotly indicator)
# ---------------------------------------------------------------------------

def _polar_point(cx, cy, r, angle_deg):
    rad = math.radians(angle_deg)
    return cx + r * math.cos(rad), cy - r * math.sin(rad)


def render_gauge(score: float) -> str:
    label, color = verdict_tier(score)
    cx, cy, r = 100, 100, 80

    start_angle = 180
    end_angle = 180 - (max(0, min(100, score)) / 100) * 180
    swept = start_angle - end_angle
    large_arc = 1 if swept > 180 else 0

    x0, y0 = _polar_point(cx, cy, r, start_angle)
    x1, y1 = _polar_point(cx, cy, r, end_angle)
    track_x1, track_y1 = _polar_point(cx, cy, r, 0)

    needle_x, needle_y = _polar_point(cx, cy, r - 12, end_angle)

    return (
        f'<div class="gauge-wrap"><svg viewBox="0 0 200 120" class="gauge-svg">'
        f'<path d="M {x0:.1f} {y0:.1f} A {r} {r} 0 1 1 {track_x1:.1f} {track_y1:.1f}" '
        f'fill="none" stroke="var(--track)" stroke-width="14" stroke-linecap="round"/>'
        f'<path d="M {x0:.1f} {y0:.1f} A {r} {r} 0 {large_arc} 1 {x1:.1f} {y1:.1f}" '
        f'fill="none" stroke="{color}" stroke-width="14" stroke-linecap="round"/>'
        f'<line x1="{cx}" y1="{cy}" x2="{needle_x:.1f}" y2="{needle_y:.1f}" '
        f'stroke="var(--paper)" stroke-width="3" stroke-linecap="round"/>'
        f'<circle cx="{cx}" cy="{cy}" r="5" fill="var(--paper)"/></svg>'
        f'<div class="gauge-readout">'
        f'<span class="gauge-score" style="color:{color};">{score:.1f}</span>'
        f'<span class="gauge-max">/ 100</span></div></div>'
    )


# ---------------------------------------------------------------------------
# Skill chips
# ---------------------------------------------------------------------------

def render_chips(items: list, kind: str) -> str:
    if not items:
        empty_copy = "No gaps flagged." if kind == "missing" else "None matched."
        return f'<p class="chip-empty">{empty_copy}</p>'
    css_class = "chip-matched" if kind == "matched" else "chip-missing"
    chips = "".join(f'<span class="chip {css_class}">{item}</span>' for item in items)
    return f'<div class="chip-row">{chips}</div>'


# ---------------------------------------------------------------------------
# Sub-score bars
# ---------------------------------------------------------------------------

def render_bars(rows: list) -> str:
    """rows: list of (label, value, color) tuples."""
    bars = ""
    for label, value, color in rows:
        bars += (
            f'<div class="bar-row">'
            f'<div class="bar-label"><span>{label}</span>'
            f'<span class="bar-value">{value:.0f}</span></div>'
            f'<div class="bar-track">'
            f'<div class="bar-fill" style="width:{value:.1f}%; background:{color};"></div>'
            f'</div></div>'
        )
    return f'<div class="bar-group">{bars}</div>'


# ---------------------------------------------------------------------------
# Global CSS
# ---------------------------------------------------------------------------

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500&display=swap');

:root {
  --ink: #10231F;
  --ink-raised: #16302A;
  --paper: #EDEFE4;
  --paper-dim: #9FB0A8;
  --track: #24443C;
  --amber: #E7A33E;
  --rose: #D9636A;
  --mint: #7FC8A9;
}

.stApp {
  background: var(--ink) !important;
  color: var(--paper) !important;
}

[data-testid="stSidebar"] {
  background: var(--ink-raised) !important;
  border-right: 1px solid var(--track);
}

h1, h2, h3, .stamp-label {
  font-family: 'Space Grotesk', sans-serif !important;
}

body, p, span, div, label {
  font-family: 'IBM Plex Sans', sans-serif;
}

.eyebrow {
  font-family: 'IBM Plex Mono', monospace;
  letter-spacing: 0.12em;
  font-size: 0.75rem;
  color: var(--amber);
  text-transform: uppercase;
  margin-bottom: 0.35rem;
  display: block;
}

.masthead-title {
  font-family: 'Space Grotesk', sans-serif;
  font-weight: 700;
  font-size: 2.4rem;
  margin: 0;
  letter-spacing: -0.01em;
}

.masthead-sub {
  font-family: 'IBM Plex Mono', monospace;
  color: var(--paper-dim);
  font-size: 0.9rem;
  margin-top: 0.3rem;
}

hr.divider {
  border: none;
  border-top: 1px dashed var(--track);
  margin: 1.6rem 0;
}

/* Streamlit widget overrides */
.stTextArea textarea, [data-testid="stFileUploaderDropzone"] {
  background: var(--ink-raised) !important;
  border: 1px solid var(--track) !important;
  color: var(--paper) !important;
  border-radius: 4px !important;
}

[data-testid="stFileUploaderDropzone"] {
  border-style: dashed !important;
}

.stButton > button {
  background: var(--amber) !important;
  color: var(--ink) !important;
  font-family: 'IBM Plex Mono', monospace !important;
  font-weight: 600 !important;
  letter-spacing: 0.05em !important;
  text-transform: uppercase;
  border: none !important;
  border-radius: 3px !important;
  padding: 0.7rem 1rem !important;
}

.stButton > button:hover {
  background: #f2b459 !important;
}

/* Verdict stamp */
.stamp {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  border: 3px double;
  padding: 0.9rem 1.6rem;
  transform: rotate(-4deg);
  font-family: 'IBM Plex Mono', monospace;
  border-radius: 4px;
}
.stamp-label {
  font-size: 1.6rem;
  font-weight: 700;
  letter-spacing: 0.08em;
}
.stamp-sub {
  font-size: 0.7rem;
  letter-spacing: 0.1em;
  opacity: 0.85;
  margin-top: 0.2rem;
}

/* Gauge */
.gauge-wrap {
  position: relative;
  max-width: 260px;
  margin: 0 auto;
}
.gauge-svg {
  width: 100%;
  display: block;
}
.gauge-readout {
  position: absolute;
  bottom: 6px;
  left: 0;
  right: 0;
  text-align: center;
}
.gauge-score {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 2rem;
  font-weight: 700;
}
.gauge-max {
  font-family: 'IBM Plex Mono', monospace;
  color: var(--paper-dim);
  font-size: 0.85rem;
}

/* Chips */
.chip-row { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.chip {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.8rem;
  padding: 0.3rem 0.7rem;
  border-radius: 999px;
  border: 1px solid;
}
.chip-matched { border-color: var(--mint); color: var(--mint); }
.chip-missing { border-color: var(--rose); color: var(--rose); }
.chip-empty { color: var(--paper-dim); font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem; }

/* Bars */
.bar-group { display: flex; flex-direction: column; gap: 0.9rem; }
.bar-label {
  display: flex;
  justify-content: space-between;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.82rem;
  color: var(--paper-dim);
  margin-bottom: 0.25rem;
}
.bar-value { color: var(--paper); }
.bar-track {
  height: 8px;
  background: var(--track);
  border-radius: 4px;
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  border-radius: 4px;
  animation: grow 0.7s ease-out;
}
@keyframes grow {
  from { width: 0%; }
}

/* Candidate file card */
.file-card {
  background: var(--ink-raised);
  border: 1px solid var(--track);
  border-radius: 6px;
  padding: 1.1rem 1.3rem;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.9rem;
  line-height: 1.7;
}
.file-card .field-label { color: var(--paper-dim); margin-right: 0.4rem; }
.file-card a { color: var(--mint); }

/* Field notes (gap analysis) */
.field-note {
  border-left: 3px solid var(--amber);
  padding: 0.9rem 1.2rem;
  background: var(--ink-raised);
  font-family: 'IBM Plex Sans', sans-serif;
  font-size: 0.95rem;
  line-height: 1.6;
  border-radius: 0 4px 4px 0;
}
</style>
"""
