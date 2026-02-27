"""Global CSS — gamified weather app, immersive dark atmosphere."""

import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background: #030711 !important;
    color: #E2E8F0;
    font-family: 'Outfit', sans-serif;
}

/* ── Kill sidebar & default nav ── */
[data-testid="collapsedControl"],
section[data-testid="stSidebar"],
[data-testid="stToolbar"] { display: none !important; }

/* ── Main layout ── */
.main .block-container {
    max-width: 1100px;
    padding: 0 1.5rem 4rem;
    margin: 0 auto;
}

/* ── Animated sky background ── */
[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed;
    inset: 0;
    background:
        radial-gradient(ellipse 80% 50% at 20% -10%, rgba(14,165,233,0.12) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 110%, rgba(99,102,241,0.08) 0%, transparent 60%),
        #030711;
    pointer-events: none;
    z-index: 0;
}

/* ── Top header bar ── */
.rf-topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.25rem 0 1rem;
    margin-bottom: 0.5rem;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    position: relative;
    z-index: 10;
}
.rf-brand {
    display: flex;
    align-items: center;
    gap: 10px;
}
.rf-brand-icon {
    font-size: 1.4rem;
    filter: drop-shadow(0 0 8px rgba(56,189,248,0.6));
    animation: float 3s ease-in-out infinite;
}
@keyframes float {
    0%,100% { transform: translateY(0px); }
    50%      { transform: translateY(-4px); }
}
.rf-brand-name {
    font-size: 1rem;
    font-weight: 700;
    letter-spacing: -0.01em;
    color: #F1F5F9;
}
.rf-brand-sub {
    font-size: 0.7rem;
    color: #475569;
    font-weight: 400;
    margin-left: 2px;
}
.rf-status {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.7rem;
    color: #475569;
}
.rf-status-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #22C55E;
    box-shadow: 0 0 6px #22C55E;
    animation: blink 2s infinite;
}
@keyframes blink {
    0%,100% { opacity: 1; }
    50%      { opacity: 0.4; }
}

/* ── Navigation pills ── */
.rf-nav-wrap {
    display: flex;
    gap: 2px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 3px;
    width: fit-content;
    margin-bottom: 2rem;
    position: relative;
    z-index: 10;
}
.rf-nav-pill {
    padding: 7px 18px;
    border-radius: 9px;
    font-size: 0.8rem;
    font-weight: 500;
    color: #475569;
    cursor: default;
    letter-spacing: 0.01em;
    transition: color 0.2s;
}
.rf-nav-pill.active {
    background: linear-gradient(135deg, #0EA5E9, #6366F1);
    color: #fff;
    box-shadow: 0 2px 12px rgba(14,165,233,0.3);
}

/* ── Hide real nav buttons (use only as click triggers) ── */
.nav-btn-row { margin-bottom: 2rem; }
.nav-btn-row .stButton > button {
    background: transparent !important;
    border: none !important;
    color: transparent !important;
    height: 0 !important;
    padding: 0 !important;
    min-height: 0 !important;
    overflow: hidden !important;
    position: absolute !important;
    pointer-events: none !important;
}

/* ── Hero weather card ── */
.weather-hero {
    background: linear-gradient(135deg,
        rgba(14,165,233,0.12) 0%,
        rgba(99,102,241,0.08) 50%,
        rgba(3,7,17,0) 100%);
    border: 1px solid rgba(14,165,233,0.15);
    border-radius: 20px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.weather-hero::before {
    content: '';
    position: absolute;
    top: -50%; right: -20%;
    width: 400px; height: 400px;
    background: radial-gradient(circle, rgba(14,165,233,0.06) 0%, transparent 70%);
    pointer-events: none;
}
.hero-date {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #475569;
    margin-bottom: 8px;
}
.hero-verdict {
    font-size: 2.8rem;
    font-weight: 800;
    letter-spacing: -0.04em;
    line-height: 1;
    margin-bottom: 6px;
}
.hero-sub {
    font-size: 0.9rem;
    color: #64748B;
    margin-bottom: 1.5rem;
}
.hero-stats {
    display: flex;
    gap: 2rem;
    flex-wrap: wrap;
}
.hero-stat {
    display: flex;
    flex-direction: column;
    gap: 2px;
}
.hero-stat-label {
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #334155;
}
.hero-stat-val {
    font-size: 1.1rem;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
    color: #E2E8F0;
}
.hero-icon {
    position: absolute;
    right: 2.5rem;
    top: 50%;
    transform: translateY(-50%);
    font-size: 5rem;
    opacity: 0.15;
    animation: float 4s ease-in-out infinite;
    pointer-events: none;
}

/* ── Probability ring ── */
.prob-ring-wrap {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 16px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
}
.prob-ring-text { flex: 1; }
.prob-ring-title {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #475569;
    margin-bottom: 4px;
}
.prob-big {
    font-size: 2.2rem;
    font-weight: 800;
    font-family: 'JetBrains Mono', monospace;
}
.prob-label { font-size: 0.8rem; color: #64748B; margin-top: 2px; }

/* ── Timeline (hourly forecast) ── */
.timeline-wrap {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 16px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
}
.timeline-title {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #475569;
    margin-bottom: 1rem;
}
.timeline-bar {
    display: flex;
    gap: 3px;
    align-items: flex-end;
    height: 48px;
    margin-bottom: 6px;
}
.timeline-hour {
    flex: 1;
    border-radius: 3px 3px 0 0;
    transition: opacity 0.2s;
    min-height: 3px;
}
.timeline-labels {
    display: flex;
    justify-content: space-between;
    font-size: 0.6rem;
    color: #334155;
    font-family: 'JetBrains Mono', monospace;
}
.timeline-rain-window {
    font-size: 0.8rem;
    color: #38BDF8;
    margin-top: 8px;
    font-weight: 500;
}

/* ── 7-day strip ── */
.week-strip {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 8px;
    margin-bottom: 1.5rem;
}
.day-tile {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 14px;
    padding: 12px 6px;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
    position: relative;
    overflow: hidden;
}
.day-tile.selected {
    border-color: rgba(14,165,233,0.5);
    background: rgba(14,165,233,0.08);
    box-shadow: 0 0 20px rgba(14,165,233,0.1);
}
.day-tile:hover { border-color: rgba(255,255,255,0.12); transform: translateY(-2px); }
.day-tile-name {
    font-size: 0.6rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #475569;
    margin-bottom: 2px;
}
.day-tile-date {
    font-size: 0.75rem;
    font-family: 'JetBrains Mono', monospace;
    color: #94A3B8;
    margin-bottom: 6px;
}
.day-tile-icon { font-size: 1.4rem; margin-bottom: 4px; }
.day-tile-prob {
    font-size: 0.85rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
}
.day-tile-mm { font-size: 0.6rem; color: #475569; margin-top: 1px; }

/* ── KPI grid ── */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-bottom: 1.5rem;
}
.kpi-card {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 14px;
    padding: 16px 18px;
    transition: border-color 0.2s;
}
.kpi-card:hover { border-color: rgba(14,165,233,0.2); }
.kpi-label {
    font-size: 0.62rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #334155;
    margin-bottom: 6px;
}
.kpi-val {
    font-size: 1.5rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    color: #F1F5F9;
    line-height: 1;
}
.kpi-sub { font-size: 0.65rem; color: #38BDF8; margin-top: 3px; }

/* ── Section label ── */
.sec-label {
    font-size: 0.62rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #334155;
    margin: 1.5rem 0 0.75rem;
}

/* ── Alert banner ── */
.alert-banner {
    border-radius: 12px;
    padding: 12px 16px;
    font-size: 0.82rem;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 1rem;
}
.alert-rain  { background: rgba(14,165,233,0.08); border: 1px solid rgba(14,165,233,0.2); color: #38BDF8; }
.alert-heavy { background: rgba(239,68,68,0.08);  border: 1px solid rgba(239,68,68,0.2);  color: #F87171; }
.alert-clear { background: rgba(34,197,94,0.08);  border: 1px solid rgba(34,197,94,0.2);  color: #4ADE80; }
.alert-maybe { background: rgba(234,179,8,0.08);  border: 1px solid rgba(234,179,8,0.2);  color: #FDE047; }

/* ── Form inputs ── */
[data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
    color: #E2E8F0 !important;
    font-family: 'JetBrains Mono', monospace !important;
}
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #0EA5E9, #6366F1) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 15px rgba(14,165,233,0.2) !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(14,165,233,0.35) !important;
}

/* ── Streamlit metric overrides ── */
[data-testid="metric-container"] {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    border-radius: 12px !important;
    padding: 12px 16px !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.02) !important;
    border: 1px dashed rgba(14,165,233,0.3) !important;
    border-radius: 12px !important;
}

/* ── Train progress ── */
.train-banner {
    background: linear-gradient(135deg, rgba(14,165,233,0.08), rgba(99,102,241,0.08));
    border: 1px solid rgba(14,165,233,0.2);
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.5rem;
    text-align: center;
}
.train-banner-title { font-size: 1.1rem; font-weight: 700; color: #38BDF8; margin-bottom: 4px; }
.train-banner-sub   { font-size: 0.8rem; color: #475569; }

/* ── Radar animation (decorative) ── */
@keyframes radarSpin {
    from { transform: rotate(0deg); }
    to   { transform: rotate(360deg); }
}
.radar-icon { animation: radarSpin 4s linear infinite; display: inline-block; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden;
}

/* ── Hide streamlit chrome ── */
footer, #MainMenu, [data-testid="stDecoration"] { display: none !important; }

/* ── Radio buttons (mode switcher) ── */
[data-testid="stRadio"] label {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 8px 16px !important;
    font-size: 0.82rem !important;
    transition: all 0.15s;
    cursor: pointer;
}
[data-testid="stRadio"] label:has(input:checked) {
    background: rgba(14,165,233,0.1);
    border-color: rgba(14,165,233,0.3);
    color: #38BDF8;
}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def topbar(model_ready: bool) -> None:
    status_dot = '<div class="rf-status-dot"></div>' if model_ready else '<div class="rf-status-dot" style="background:#EF4444;box-shadow:0 0 6px #EF4444"></div>'
    status_txt = "Model siap" if model_ready else "Model belum ditraining"
    st.markdown(f"""
    <div class="rf-topbar">
        <div class="rf-brand">
            <div class="rf-brand-icon">💧</div>
            <div>
                <div class="rf-brand-name">RainForecaster <span class="rf-brand-sub">Nusantara</span></div>
            </div>
        </div>
        <div class="rf-status">
            {status_dot}
            <span>{status_txt}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def nav_pills(active: str) -> None:
    tabs = ["Dashboard", "Forecast", "Data"]
    pills = ""
    for t in tabs:
        cls = "rf-nav-pill active" if t == active else "rf-nav-pill"
        pills += f'<div class="{cls}">{t}</div>'
    st.markdown(f'<div class="rf-nav-wrap">{pills}</div>', unsafe_allow_html=True)


def kpi_grid(records: int, rainy: int, avg_rain: float, avg_temp: float) -> None:
    rain_pct = rainy / records * 100 if records else 0
    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-label">Total Data</div>
            <div class="kpi-val">{records:,}</div>
            <div class="kpi-sub">records</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Hari Hujan</div>
            <div class="kpi-val">{rainy:,}</div>
            <div class="kpi-sub">{rain_pct:.1f}% dari total</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Rata-rata Hujan</div>
            <div class="kpi-val">{avg_rain:.1f}</div>
            <div class="kpi-sub">mm / hari</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Rata-rata Suhu</div>
            <div class="kpi-val">{avg_temp:.1f}</div>
            <div class="kpi-sub">°C</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def weather_hero(
    date_str: str, verdict: str, sub: str, prob: float,
    mm: float | None, intensity: str, color: str, icon: str,
    rain_window: dict
) -> None:
    bar_pct = int(prob * 100)
    mm_str  = f"{mm:.1f} mm" if mm else "— mm"

    # Build hourly timeline (24 bars)
    bars_html = ""
    rain_start = int(rain_window.get("start", "99:00")[:2]) if rain_window.get("start") else 99
    rain_end   = int(rain_window.get("end", "00:00")[:2])   if rain_window.get("end")   else 0
    rain_peak  = int(rain_window.get("peak", "00:00")[:2])  if rain_window.get("peak")  else 0

    for h in range(24):
        in_rain = rain_start <= h < rain_end
        is_peak = h == rain_peak
        if is_peak:
            height = 100
            bg = color
        elif in_rain:
            frac = 1 - abs(h - rain_peak) / max(1, (rain_end - rain_start))
            height = max(20, int(frac * 85))
            bg = f"rgba(56,189,248,{0.3 + frac*0.4:.2f})"
        else:
            height = 5
            bg = "rgba(255,255,255,0.04)"
        bars_html += f'<div class="timeline-hour" style="height:{height}%;background:{bg}"></div>'

    window_text = rain_window.get("description", "Tidak ada estimasi")

    st.markdown(f"""
    <div class="weather-hero">
        <div class="hero-icon">{icon}</div>
        <div class="hero-date">{date_str}</div>
        <div class="hero-verdict" style="color:{color}">{verdict}</div>
        <div class="hero-sub">{sub}</div>
        <div class="hero-stats">
            <div class="hero-stat">
                <div class="hero-stat-label">Probabilitas</div>
                <div class="hero-stat-val">{bar_pct}%</div>
            </div>
            <div class="hero-stat">
                <div class="hero-stat-label">Estimasi Volume</div>
                <div class="hero-stat-val">{mm_str}</div>
            </div>
            <div class="hero-stat">
                <div class="hero-stat-label">Intensitas</div>
                <div class="hero-stat-val">{intensity}</div>
            </div>
        </div>
    </div>
    <div class="timeline-wrap">
        <div class="timeline-title">Estimasi Waktu Hujan (24 Jam)</div>
        <div class="timeline-bar">{bars_html}</div>
        <div class="timeline-labels">
            <span>00:00</span><span>06:00</span><span>12:00</span><span>18:00</span><span>23:00</span>
        </div>
        <div class="timeline-rain-window">⏱ {window_text}</div>
    </div>
    """, unsafe_allow_html=True)


def week_strip(days: list, selected_idx: int) -> None:
    day_names = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
    tiles = ""
    for i, d in enumerate(days):
        p    = d["prob"]
        m    = d["mm"]
        icon = "🌧️" if p >= 0.65 else ("⛈️" if p >= 0.8 else ("🌦️" if p >= 0.35 else "☀️"))
        col  = "#38BDF8" if p >= 0.65 else ("#FDE047" if p >= 0.35 else "#4ADE80")
        mm_s = f"{m:.0f}mm" if m else "—"
        sel  = "selected" if i == selected_idx else ""
        tiles += f"""
        <div class="day-tile {sel}">
            <div class="day-tile-name">{day_names[d['date'].weekday()]}</div>
            <div class="day-tile-date">{d['date'].strftime('%d/%m')}</div>
            <div class="day-tile-icon">{icon}</div>
            <div class="day-tile-prob" style="color:{col}">{p:.0%}</div>
            <div class="day-tile-mm">{mm_s}</div>
        </div>"""
    st.markdown(f'<div class="week-strip">{tiles}</div>', unsafe_allow_html=True)


def alert_banner(cls: str, icon: str, text: str) -> None:
    st.markdown(
        f'<div class="alert-banner {cls}"><span>{icon}</span><span>{text}</span></div>',
        unsafe_allow_html=True
    )