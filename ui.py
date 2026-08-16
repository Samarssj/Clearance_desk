"""Custom visual system for the Clearance Desk Streamlit app.

The scoring and extraction modules remain intentionally separate from this file.
Every helper returns small, escaped HTML fragments so the Streamlit surface can
feel like a product UI instead of a collection of default widgets.
"""

import html
import math


def _safe(value) -> str:
    """Escape values before placing them in unsafe_allow_html fragments."""
    if value is None or value == "":
        return "—"
    return html.escape(str(value))


# ---------------------------------------------------------------------------
# Shared score vocabulary
# ---------------------------------------------------------------------------


def verdict_tier(score: float):
    if score >= 75:
        return "CLEARED", "var(--mint)", "Strong alignment"
    if score >= 50:
        return "CONDITIONAL", "var(--amber)", "Review required"
    return "REJECTED", "var(--rose)", "Low alignment"


# ---------------------------------------------------------------------------
# Signature result components
# ---------------------------------------------------------------------------


def render_stamp(score: float) -> str:
    label, color, sublabel = verdict_tier(score)
    return (
        f'<div class="verdict-stamp" style="--stamp-color:{color};">'
        f'<span class="stamp-kicker">DECISION STATUS</span>'
        f'<span class="stamp-label">{label}</span>'
        f'<span class="stamp-sub">{sublabel} · {score:.1f} / 100</span>'
        "</div>"
    )


def _polar_point(cx, cy, r, angle_deg):
    rad = math.radians(angle_deg)
    return cx + r * math.cos(rad), cy - r * math.sin(rad)


def render_gauge(score: float) -> str:
    """Render an SVG half-dial with an accessible text readout."""
    label, color, _ = verdict_tier(score)
    cx, cy, r = 120, 112, 88
    clamped = max(0.0, min(100.0, float(score)))
    start_angle = 180
    end_angle = 180 - (clamped / 100.0) * 180
    x0, y0 = _polar_point(cx, cy, r, start_angle)
    x1, y1 = _polar_point(cx, cy, r, end_angle)
    needle_x, needle_y = _polar_point(cx, cy, r - 16, end_angle)

    return (
        '<div class="gauge-card">'
        '<div class="gauge-caption"><span>FIT READING</span><span>0 — 100</span></div>'
        '<div class="gauge-wrap">'
        '<svg viewBox="0 0 240 150" class="gauge-svg" role="img" '
        f'aria-label="Fit score {clamped:.1f} out of 100">'
        f'<path d="M {x0:.1f} {y0:.1f} A {r} {r} 0 0 1 {2 * cx - x0:.1f} {y0:.1f}" '
        'fill="none" stroke="var(--track)" stroke-width="16" stroke-linecap="round"/>'
        f'<path d="M {x0:.1f} {y0:.1f} A {r} {r} 0 {1 if clamped > 50 else 0} 1 {x1:.1f} {y1:.1f}" '
        f'fill="none" stroke="{color}" stroke-width="16" stroke-linecap="round"/>'
        f'<line x1="{cx}" y1="{cy}" x2="{needle_x:.1f}" y2="{needle_y:.1f}" '
        'stroke="var(--paper)" stroke-width="3" stroke-linecap="round"/>'
        f'<circle cx="{cx}" cy="{cy}" r="6" fill="{color}" stroke="var(--paper)" stroke-width="3"/>'
        "</svg>"
        '<div class="gauge-readout">'
        f'<span class="gauge-score" style="color:{color};">{clamped:.1f}</span>'
        '<span class="gauge-max">/ 100</span>'
        "</div></div>"
        f'<div class="gauge-tier" style="color:{color};">{label} signal</div>'
        "</div>"
    )


def render_metric_card(label: str, value: str, detail: str, accent: str = "mint") -> str:
    return (
        f'<div class="metric-card metric-{accent}">'
        f'<div class="metric-label">{_safe(label)}</div>'
        f'<div class="metric-value">{_safe(value)}</div>'
        f'<div class="metric-detail">{_safe(detail)}</div>'
        "</div>"
    )


def render_chips(items: list, kind: str) -> str:
    if not items:
        empty_copy = "No gaps flagged in the current brief." if kind == "missing" else "No direct matches detected."
        return f'<p class="chip-empty">{empty_copy}</p>'
    css_class = "chip-matched" if kind == "matched" else "chip-missing"
    chips = "".join(f'<span class="chip {css_class}">{_safe(item)}</span>' for item in items)
    return f'<div class="chip-row">{chips}</div>'


def render_bars(rows: list) -> str:
    """rows: list of (label, value, color, weight) tuples."""
    bars = ""
    for row in rows:
        label, value, color = row[:3]
        weight = row[3] if len(row) > 3 else ""
        safe_value = max(0.0, min(100.0, float(value)))
        bars += (
            '<div class="bar-row">'
            f'<div class="bar-label"><span>{_safe(label)}'
            f'<small>{_safe(weight)}</small></span><strong>{safe_value:.0f}</strong></div>'
            '<div class="bar-track">'
            f'<div class="bar-fill" style="width:{safe_value:.1f}%; background:{color};"></div>'
            "</div></div>"
        )
    return f'<div class="bar-group">{bars}</div>'


def render_candidate_card(resume, filename: str = "") -> str:
    name = _safe(resume.name or "Candidate file")
    file_label = _safe(filename or "Resume intake")
    links = []
    if resume.linkedin:
        links.append(f'<a href="{_safe(resume.linkedin)}" target="_blank">LinkedIn</a>')
    if resume.github:
        links.append(f'<a href="{_safe(resume.github)}" target="_blank">GitHub</a>')
    link_line = " · ".join(links) if links else "No public links detected"
    return (
        '<div class="candidate-card">'
        '<div class="candidate-card-top">'
        '<div class="avatar-mark">'
        f'{(str(resume.name or "C")[:1]).upper()}'
        "</div>"
        '<div><div class="card-kicker">CANDIDATE FILE</div>'
        f'<div class="candidate-name">{name}</div>'
        f'<div class="candidate-file">{file_label}</div></div>'
        "</div>"
        '<div class="candidate-fields">'
        f'<div><span>EMAIL</span><strong>{_safe(resume.email)}</strong></div>'
        f'<div><span>PHONE</span><strong>{_safe(resume.phone)}</strong></div>'
        f'<div><span>EXPERIENCE</span><strong>{_safe(resume.years_experience)} yrs detected</strong></div>'
        f'<div><span>LINKS</span><strong>{link_line}</strong></div>'
        "</div></div>"
    )


def render_signal_panel(title: str, kicker: str, body: str, tone: str = "amber") -> str:
    return (
        f'<div class="signal-panel signal-{tone}">'
        f'<div class="panel-kicker">{_safe(kicker)}</div>'
        f'<div class="panel-title">{_safe(title)}</div>'
        f'<div class="panel-body">{body}</div>'
        "</div>"
    )


# ---------------------------------------------------------------------------
# Global CSS
# ---------------------------------------------------------------------------

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Mono:wght@400;500&family=Manrope:wght@600;700;800&display=swap');

:root {
  --ink: #0c1118;
  --ink-soft: #111925;
  --ink-raised: #172231;
  --ink-lift: #1d2b3c;
  --paper: #f4f7fb;
  --paper-dim: #99a9bb;
  --paper-faint: #66768a;
  --track: #2a3b50;
  --mint: #65e5ba;
  --mint-deep: #22b889;
  --amber: #f2b766;
  --rose: #f27d9a;
  --blue: #7eb8ff;
  --violet: #a995ff;
}

.stApp {
  background:
    radial-gradient(circle at 82% -10%, rgba(126,184,255,.12), transparent 32rem),
    radial-gradient(circle at 10% 15%, rgba(101,229,186,.06), transparent 26rem),
    var(--ink) !important;
  color: var(--paper) !important;
}

[data-testid="stSidebar"] {
  background: rgba(17,25,37,.96) !important;
  border-right: 1px solid rgba(126,184,255,.13);
}
[data-testid="stSidebar"] > div:first-child { padding-top: 2rem; }
[data-testid="stSidebar"] .block-container { padding: 1.8rem 1.25rem; }

#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }

h1, h2, h3, h4, .hero-title, .candidate-name, .metric-value, .panel-title {
  font-family: 'Manrope', sans-serif !important;
}
body, p, span, div, label, button, textarea { font-family: 'DM Sans', sans-serif; }

.block-container { max-width: 1440px; padding: 2.1rem 4rem 4rem; }

.app-topbar { display:flex; justify-content:space-between; align-items:center; margin-bottom: 3.4rem; }
.brand-lockup { display:flex; align-items:center; gap:.8rem; }
.brand-mark { width:2.3rem; height:2.3rem; display:grid; place-items:center; border:1px solid rgba(101,229,186,.55); border-radius:10px; color:var(--mint); font-family:'DM Mono', monospace; font-size:1.2rem; box-shadow:0 0 30px rgba(101,229,186,.12); }
.brand-name { font-size:.88rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; }
.brand-sub { color:var(--paper-faint); font-family:'DM Mono', monospace; font-size:.67rem; letter-spacing:.05em; margin-top:.18rem; }
.topbar-status { border:1px solid rgba(101,229,186,.25); background:rgba(101,229,186,.06); color:var(--mint); border-radius:999px; padding:.48rem .82rem; font:500 .68rem 'DM Mono', monospace; letter-spacing:.07em; text-transform:uppercase; }

.hero-grid { display:grid; grid-template-columns: minmax(0,1.55fr) minmax(280px,.8fr); gap:3rem; align-items:end; margin-bottom:3.5rem; }
.hero-kicker, .section-kicker, .panel-kicker, .metric-label, .card-kicker, .eyebrow { font:500 .68rem 'DM Mono', monospace; color:var(--mint); letter-spacing:.13em; text-transform:uppercase; }
.hero-title { font-size: clamp(2.6rem, 5vw, 5.3rem); line-height: .98; letter-spacing:-.065em; max-width: 760px; margin:.85rem 0 1.2rem; }
.hero-title em { color:var(--blue); font-style:normal; }
.hero-copy { color:var(--paper-dim); font-size:1.05rem; line-height:1.65; max-width:660px; margin:0; }
.hero-aside { border-left:1px solid var(--track); padding-left:1.4rem; }
.hero-aside-title { color:var(--paper); font:700 .88rem 'Manrope', sans-serif; margin:.65rem 0 1rem; }
.hero-aside-row { display:flex; gap:.7rem; align-items:flex-start; margin:.72rem 0; color:var(--paper-dim); font-size:.84rem; line-height:1.45; }
.hero-aside-row b { color:var(--blue); font:500 .72rem 'DM Mono', monospace; }

.section-heading { display:flex; justify-content:space-between; align-items:end; gap:1rem; margin:0 0 1rem; }
.section-title { font:700 1.25rem 'Manrope', sans-serif; margin:.4rem 0 0; }
.section-note { color:var(--paper-faint); font-size:.8rem; }

[data-testid="column"] { min-width:0; }
.intake-card, .result-surface { background:linear-gradient(145deg, rgba(29,43,60,.82), rgba(17,25,37,.88)); border:1px solid rgba(126,184,255,.13); border-radius:22px; box-shadow:0 18px 60px rgba(0,0,0,.16); }
.intake-card { padding:1.25rem 1.3rem .9rem; min-height:100%; }
.input-label { color:var(--paper); font:700 .95rem 'Manrope', sans-serif; margin:.45rem 0 .2rem; }
.input-help { color:var(--paper-faint); font-size:.78rem; margin-bottom:.85rem; }

/* Streamlit widget overrides */
.stTextArea textarea, [data-testid="stFileUploaderDropzone"] { background:rgba(12,17,24,.55) !important; border:1px solid var(--track) !important; color:var(--paper) !important; border-radius:14px !important; }
.stTextArea textarea { min-height:220px !important; padding:1rem !important; font-size:.92rem !important; line-height:1.55 !important; }
[data-testid="stFileUploaderDropzone"] { border-style:dashed !important; min-height:180px; }
[data-testid="stFileUploaderDropzone"]:hover { border-color:var(--mint) !important; background:rgba(101,229,186,.04) !important; }
[data-testid="stFileUploaderDropzone"] small, [data-testid="stFileUploaderDropzone"] span { color:var(--paper-dim) !important; }
.stButton { margin-top:1.25rem; }
.stButton > button { background:linear-gradient(135deg, var(--mint), #8deecb) !important; color:var(--ink) !important; font:700 .78rem 'DM Mono', monospace !important; letter-spacing:.08em !important; text-transform:uppercase; border:0 !important; border-radius:12px !important; padding:.82rem 1.1rem !important; box-shadow:0 8px 22px rgba(101,229,186,.16); transition:transform .15s ease, box-shadow .15s ease; }
.stButton > button:hover { transform:translateY(-2px); box-shadow:0 12px 28px rgba(101,229,186,.25); }
.stButton > button:focus { box-shadow:0 0 0 2px var(--ink), 0 0 0 4px var(--mint) !important; }
.stAlert { border-radius:14px !important; background:rgba(242,183,102,.08) !important; border:1px solid rgba(242,183,102,.3) !important; }

.divider { height:1px; border:0; background:linear-gradient(90deg, var(--track), transparent); margin:3.6rem 0 2.2rem; }
.result-header { display:flex; justify-content:space-between; align-items:end; gap:1.5rem; margin-bottom:1.3rem; }
.result-header .section-title { font-size:1.55rem; }
.processing-note { color:var(--paper-faint); font:500 .7rem 'DM Mono', monospace; letter-spacing:.04em; }

.metric-grid { display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:.75rem; margin:1.2rem 0 1.1rem; }
.metric-card { padding:1rem 1.05rem; min-height:120px; background:rgba(29,43,60,.55); border:1px solid rgba(126,184,255,.12); border-radius:16px; position:relative; overflow:hidden; }
.metric-card::after { content:""; position:absolute; width:80px; height:80px; border-radius:50%; right:-28px; bottom:-36px; background:var(--metric-glow); filter:blur(2px); opacity:.1; }
.metric-mint { --metric-glow:var(--mint); }
.metric-blue { --metric-glow:var(--blue); }
.metric-amber { --metric-glow:var(--amber); }
.metric-rose { --metric-glow:var(--rose); }
.metric-label { color:var(--paper-faint); font-size:.62rem; }
.metric-value { font-size:1.8rem; margin:.55rem 0 .15rem; letter-spacing:-.04em; }
.metric-detail { color:var(--paper-dim); font-size:.74rem; }

.result-grid { display:grid; grid-template-columns: minmax(250px,.9fr) minmax(300px,1.1fr) minmax(280px,1fr); gap:1rem; align-items:stretch; }
.verdict-panel, .gauge-card, .candidate-card, .signal-panel { background:rgba(29,43,60,.52); border:1px solid rgba(126,184,255,.12); border-radius:18px; }
.verdict-panel { padding:1.2rem; display:flex; flex-direction:column; justify-content:space-between; min-height:300px; }
.verdict-panel-top { display:flex; justify-content:space-between; align-items:start; gap:1rem; }
.verdict-panel-title { font:700 1rem 'Manrope', sans-serif; margin-top:.38rem; }
.status-dot { width:9px; height:9px; border-radius:50%; background:var(--mint); box-shadow:0 0 0 5px rgba(101,229,186,.1); margin-top:.3rem; }
.verdict-stamp { border:1px solid var(--stamp-color); color:var(--stamp-color); padding:1.4rem 1.1rem 1.1rem; border-radius:14px; display:inline-flex; flex-direction:column; gap:.34rem; width:max-content; margin-top:2.5rem; transform:rotate(-2deg); box-shadow:inset 0 0 0 4px rgba(255,255,255,.025); }
.stamp-kicker, .stamp-sub { font:500 .62rem 'DM Mono', monospace; letter-spacing:.1em; opacity:.82; }
.stamp-label { font:800 1.95rem 'Manrope', sans-serif; letter-spacing:.02em; }
.verdict-foot { color:var(--paper-faint); font-size:.75rem; line-height:1.5; max-width:220px; }

.gauge-card { min-height:300px; padding:1rem 1.1rem; display:flex; flex-direction:column; justify-content:center; }
.gauge-caption { display:flex; justify-content:space-between; color:var(--paper-faint); font:500 .63rem 'DM Mono', monospace; letter-spacing:.1em; }
.gauge-wrap { position:relative; margin:1.05rem auto 0; width:min(100%, 330px); }
.gauge-svg { width:100%; display:block; }
.gauge-readout { position:absolute; bottom:7px; left:0; right:0; text-align:center; }
.gauge-score { font:800 2.55rem 'Manrope', sans-serif; letter-spacing:-.06em; }
.gauge-max { color:var(--paper-faint); font:500 .77rem 'DM Mono', monospace; }
.gauge-tier { text-align:center; font:500 .68rem 'DM Mono', monospace; letter-spacing:.1em; text-transform:uppercase; margin-top:-.3rem; }

.candidate-card { padding:1.15rem; min-height:300px; }
.candidate-card-top { display:flex; align-items:center; gap:.8rem; padding-bottom:1rem; border-bottom:1px solid var(--track); }
.avatar-mark { width:2.65rem; height:2.65rem; display:grid; place-items:center; border-radius:12px; color:var(--ink); background:linear-gradient(135deg,var(--blue),var(--violet)); font:800 1.1rem 'Manrope', sans-serif; }
.card-kicker { color:var(--paper-faint); font-size:.62rem; }
.candidate-name { font-size:1.12rem; margin:.18rem 0 .12rem; }
.candidate-file { color:var(--paper-faint); font:500 .68rem 'DM Mono', monospace; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:220px; }
.candidate-fields { display:grid; gap:.85rem; padding-top:1rem; }
.candidate-fields div { display:flex; flex-direction:column; gap:.18rem; }
.candidate-fields span { color:var(--paper-faint); font:500 .61rem 'DM Mono', monospace; letter-spacing:.08em; }
.candidate-fields strong { color:var(--paper-dim); font-size:.78rem; font-weight:500; overflow-wrap:anywhere; }
.candidate-fields a { color:var(--blue); text-decoration:none; }

.detail-grid { display:grid; grid-template-columns:1.1fr .9fr; gap:1rem; margin-top:1rem; }
.detail-card { background:rgba(29,43,60,.38); border:1px solid rgba(126,184,255,.1); border-radius:18px; padding:1.2rem; }
.detail-card-header { display:flex; justify-content:space-between; gap:1rem; align-items:end; margin-bottom:1.1rem; }
.detail-card-title { font:700 1rem 'Manrope', sans-serif; margin-top:.35rem; }
.detail-card-note { color:var(--paper-faint); font:500 .66rem 'DM Mono', monospace; }

.bar-group { display:flex; flex-direction:column; gap:1.25rem; }
.bar-label { display:flex; justify-content:space-between; align-items:baseline; color:var(--paper); font-size:.8rem; margin-bottom:.45rem; }
.bar-label span { display:flex; gap:.55rem; align-items:baseline; }
.bar-label small { color:var(--paper-faint); font:500 .65rem 'DM Mono', monospace; }
.bar-label strong { font:500 .78rem 'DM Mono', monospace; }
.bar-track { height:9px; background:var(--track); border-radius:999px; overflow:hidden; }
.bar-fill { height:100%; border-radius:999px; animation:grow .65s ease-out; }
@keyframes grow { from { width:0%; } }

.signal-panel { padding:1.2rem; min-height:100%; }
.signal-amber { border-color:rgba(242,183,102,.2); }
.signal-blue { border-color:rgba(126,184,255,.2); }
.signal-title, .panel-title { font:700 1rem 'Manrope', sans-serif; margin:.42rem 0 .8rem; }
.panel-body { color:var(--paper-dim); font-size:.85rem; line-height:1.65; }

.chip-row { display:flex; flex-wrap:wrap; gap:.5rem; }
.chip { font:500 .69rem 'DM Mono', monospace; padding:.42rem .65rem; border-radius:999px; border:1px solid; }
.chip-matched { color:var(--mint); border-color:rgba(101,229,186,.36); background:rgba(101,229,186,.07); }
.chip-missing { color:var(--rose); border-color:rgba(242,125,154,.36); background:rgba(242,125,154,.07); }
.chip-empty { color:var(--paper-faint); font-size:.78rem; margin:0; }

.note-card { border-left:2px solid var(--amber); padding:1rem 1.1rem; background:rgba(242,183,102,.06); border-radius:0 14px 14px 0; color:var(--paper-dim); font-size:.9rem; line-height:1.7; }
.fallback-note { color:var(--paper-faint); font-size:.73rem; line-height:1.45; margin-top:1rem; }
.stExpander { border:1px solid rgba(126,184,255,.12) !important; border-radius:14px !important; background:rgba(17,25,37,.45) !important; }

.sidebar-brand { margin-bottom:2.2rem; }
.sidebar-kicker { color:var(--mint); font:500 .67rem 'DM Mono', monospace; letter-spacing:.12em; text-transform:uppercase; }
.sidebar-title { font:800 1.4rem 'Manrope', sans-serif; letter-spacing:-.04em; margin:.5rem 0 .3rem; }
.sidebar-copy { color:var(--paper-faint); font-size:.75rem; line-height:1.55; }
.sidebar-section { border-top:1px solid var(--track); padding-top:1.15rem; margin-top:1.45rem; }
.sidebar-section-title { color:var(--paper); font:700 .76rem 'Manrope', sans-serif; margin-bottom:.8rem; }
.weight-row { display:flex; justify-content:space-between; align-items:center; color:var(--paper-dim); font-size:.74rem; padding:.42rem 0; }
.weight-row b { color:var(--paper); font:500 .7rem 'DM Mono', monospace; }
.verdict-key { display:grid; gap:.55rem; }
.key-row { display:flex; align-items:center; gap:.5rem; color:var(--paper-dim); font-size:.73rem; }
.key-dot { width:7px; height:7px; border-radius:50%; }
.system-status { display:flex; gap:.45rem; align-items:center; color:var(--mint); font:500 .67rem 'DM Mono', monospace; }
.system-status::before { content:""; width:6px; height:6px; border-radius:50%; background:var(--mint); box-shadow:0 0 0 4px rgba(101,229,186,.09); }
[data-testid="stSidebar"] .stCaption { color:var(--paper-faint) !important; font-size:.68rem; }

@media (max-width: 950px) {
  .block-container { padding:1.4rem 1.2rem 3rem; }
  .hero-grid, .result-grid, .detail-grid { grid-template-columns:1fr; gap:1rem; }
  .hero-grid { margin-bottom:2.2rem; }
  .hero-aside { border-left:0; border-top:1px solid var(--track); padding:1rem 0 0; }
  .metric-grid { grid-template-columns:repeat(2, minmax(0,1fr)); }
  .app-topbar { margin-bottom:2rem; }
}
@media (max-width: 560px) {
  .metric-grid { grid-template-columns:1fr 1fr; gap:.55rem; }
  .metric-card { min-height:105px; padding:.8rem; }
  .metric-value { font-size:1.45rem; }
  .hero-title { font-size:2.6rem; }
}
</style>
"""
