"""Global CSS — premium dark weather app aesthetic."""

import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

/* ── Reset & base ── */
*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    background: #060B14 !important;
    color: #E8EEF4;
    font-family: 'DM Sans', sans-serif;
}

/* Hide sidebar toggle & default sidebar */
[data-testid="collapsedControl"],
section[data-testid="stSidebar"] { display: none !important; }

/* Main container width */
.main .block-container {
    max-width: 1180px;
    padding: 2rem 2rem 4rem;
    margin: 0 auto;
}

/* ── Header ── */
.rf-header {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 2.5rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid #0D1626;
}
.rf-header-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    background: #38BDF8;
    box-shadow: 0 0 12px #38BDF8;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%,100% { box-shadow: 0 0 8px #38BDF8; }
    50%      { box-shadow: 0 0 20px #38BDF8, 0 0 40px rgba(56,189,248,0.3); }
}
.rf-header h1 {
    font-size: 1.25rem;
    font-weight: 600;
    letter-spacing: -0.02em;
    color: #E8EEF4;
    margin: 0;
}
.rf-header span {
    font-size: 0.8rem;
    color: #4B6A8A;
    font-weight: 400;
    margin-left: 4px;
}

/* ── Nav tabs ── */
.rf-nav {
    display: flex;
    gap: 4px;
    margin-bottom: 2rem;
    background: #0D1626;
    padding: 4px;
    border-radius: 10px;
    width: fit-content;
}
.rf-nav-btn {
    padding: 7px 20px;
    border-radius: 7px;
    border: none;
    background: transparent;
    color: #4B6A8A;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s ease;
}
.rf-nav-btn:hover   { color: #94A3B8; background: #131F32; }
.rf-nav-btn.active  { background: #0EA5E9; color: #fff; }

/* ── Stat cards ── */
.stat-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 2rem;
}
.stat-card {
    background: #0D1626;
    border: 1px solid #111D2E;
    border-radius: 12px;
    padding: 18px 20px;
    transition: border-color 0.2s;
}
.stat-card:hover { border-color: #1E3A5F; }
.stat-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #4B6A8A;
    margin-bottom: 6px;
}
.stat-value {
    font-size: 1.6rem;
    font-weight: 600;
    color: #E8EEF4;
    line-height: 1;
    font-family: 'DM Mono', monospace;
}
.stat-sub {
    font-size: 0.75rem;
    color: #38BDF8;
    margin-top: 4px;
}

/* ── Filter bar ── */
.filter-bar {
    background: #0D1626;
    border: 1px solid #111D2E;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}
.filter-label {
    font-size: 0.75rem;
    color: #4B6A8A;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    white-space: nowrap;
}

/* ── Chart cards ── */
.chart-card {
    background: #0D1626;
    border: 1px solid #111D2E;
    border-radius: 12px;
    padding: 4px;
    margin-bottom: 16px;
}

/* ── Upload zone ── */
[data-testid="stFileUploader"] {
    background: #0D1626 !important;
    border: 1px dashed #1E3A5F !important;
    border-radius: 12px !important;
}

/* ── Streamlit widget overrides ── */
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div {
    background: #0D1626 !important;
    border-color: #1E3A5F !important;
    border-radius: 8px !important;
}
[data-testid="stDateInput"] input {
    background: #0D1626 !important;
    border-color: #1E3A5F !important;
}
.stButton > button {
    background: #0EA5E9 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    padding: 0.5rem 1.5rem !important;
    transition: background 0.15s !important;
}
.stButton > button:hover { background: #38BDF8 !important; }

/* Secondary button */
.stButton.secondary > button {
    background: transparent !important;
    border: 1px solid #1E3A5F !important;
    color: #94A3B8 !important;
}

/* ── Prediction result ── */
.pred-card {
    background: linear-gradient(135deg, #0D1626 0%, #0A1628 100%);
    border: 1px solid #1E3A5F;
    border-radius: 16px;
    padding: 28px 32px;
    margin-top: 1.5rem;
}
.pred-verdict {
    font-size: 1.75rem;
    font-weight: 600;
    letter-spacing: -0.03em;
    margin-bottom: 4px;
}
.pred-date { font-size: 0.875rem; color: #4B6A8A; margin-bottom: 20px; }
.pred-stats { display: flex; gap: 32px; margin-top: 16px; }
.pred-stat-label { font-size: 0.7rem; text-transform: uppercase;
    letter-spacing: 0.08em; color: #4B6A8A; }
.pred-stat-value { font-size: 1.3rem; font-weight: 600;
    font-family: 'DM Mono', monospace; color: #E8EEF4; }

/* Progress bar */
.prob-bar-wrap { margin: 16px 0 8px; }
.prob-bar-bg {
    height: 6px; background: #111D2E; border-radius: 99px; overflow: hidden;
}
.prob-bar-fill {
    height: 100%; border-radius: 99px;
    background: linear-gradient(90deg, #0284C7, #38BDF8);
    transition: width 0.5s ease;
}

/* ── Alert badges ── */
.badge { display: inline-flex; align-items: center; gap: 6px;
    padding: 6px 12px; border-radius: 8px; font-size: 0.8rem; font-weight: 500; }
.badge-warn { background: rgba(234,179,8,0.12); color: #EAB308;
    border: 1px solid rgba(234,179,8,0.25); }
.badge-info { background: rgba(56,189,248,0.10); color: #38BDF8;
    border: 1px solid rgba(56,189,248,0.25); }
.badge-ok   { background: rgba(34,197,94,0.10); color: #22C55E;
    border: 1px solid rgba(34,197,94,0.25); }

/* ── Metrics ── */
[data-testid="metric-container"] {
    background: #0D1626 !important;
    border: 1px solid #111D2E !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
}

/* ── Section title ── */
.section-title {
    font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em;
    color: #4B6A8A; margin-bottom: 12px; margin-top: 8px;
}

/* ── Mode description ── */
.mode-desc {
    background: #0D1626;
    border: 1px solid #111D2E;
    border-left: 3px solid #38BDF8;
    border-radius: 0 8px 8px 0;
    padding: 10px 16px;
    font-size: 0.875rem;
    color: #94A3B8;
    margin-bottom: 1.5rem;
}
.mode-desc strong { color: #E8EEF4; }

/* ── 7-day forecast strip ── */
.day-card {
    background: #0D1626;
    border: 1px solid #111D2E;
    border-radius: 12px;
    padding: 14px 8px;
    text-align: center;
    transition: border-color 0.2s, transform 0.15s;
}
.day-card:hover {
    border-color: #1E3A5F;
    transform: translateY(-2px);
}
.day-name {
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #4B6A8A;
    margin-bottom: 2px;
}
.day-date {
    font-size: 0.8rem;
    color: #94A3B8;
    margin-bottom: 8px;
    font-family: 'DM Mono', monospace;
}
.day-icon { font-size: 1.6rem; margin-bottom: 8px; }
.day-prob {
    font-size: 1rem;
    font-weight: 600;
    font-family: 'DM Mono', monospace;
    margin-bottom: 2px;
}
.day-mm {
    font-size: 0.72rem;
    color: #4B6A8A;
}

/* Hide Streamlit footer */
footer, #MainMenu { visibility: hidden; }
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def header() -> None:
    st.markdown("""
    <div class="rf-header">
        <div class="rf-header-dot"></div>
        <h1>Nusantara RainForecaster <span>Indonesia Weather Intelligence</span></h1>
    </div>
    """, unsafe_allow_html=True)


def stat_cards(records: int, rainy: int, avg_rain: float, avg_temp: float) -> None:
    rain_pct = rainy / records * 100 if records else 0
    st.markdown(f"""
    <div class="stat-grid">
        <div class="stat-card">
            <div class="stat-label">Total Records</div>
            <div class="stat-value">{records:,}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Rainy Days</div>
            <div class="stat-value">{rainy:,}</div>
            <div class="stat-sub">{rain_pct:.1f}% of days</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Avg Rainfall</div>
            <div class="stat-value">{avg_rain:.1f}</div>
            <div class="stat-sub">mm / day</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Avg Temperature</div>
            <div class="stat-value">{avg_temp:.1f}</div>
            <div class="stat-sub">°C</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def prediction_card(
    date_str: str, prob: float, mm: float | None, intensity: str, verdict: str, color: str
) -> None:
    bar_w = int(prob * 100)
    mm_str = f"{mm:.1f} mm" if mm is not None else "—"
    st.markdown(f"""
    <div class="pred-card">
        <div class="pred-verdict" style="color:{color}">{verdict}</div>
        <div class="pred-date">{date_str}</div>
        <div class="prob-bar-wrap">
            <div class="prob-bar-bg">
                <div class="prob-bar-fill" style="width:{bar_w}%;
                     background:linear-gradient(90deg,{color}88,{color});"></div>
            </div>
        </div>
        <div style="font-size:.75rem;color:#4B6A8A;margin-bottom:4px;">
            Rain probability: {prob:.0%}
        </div>
        <div class="pred-stats">
            <div>
                <div class="pred-stat-label">Estimated Rainfall</div>
                <div class="pred-stat-value">{mm_str}</div>
            </div>
            <div>
                <div class="pred-stat-label">Intensity</div>
                <div class="pred-stat-value" style="font-size:1rem">{intensity}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)