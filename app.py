"""
Nusantara RainForecaster
Auto-loads data/weather_data.csv, pre-trains on startup with joblib cache.
No CSV upload needed. No sidebar. Gamified weather UI.
"""

import datetime
import numpy as np
import pandas as pd
import streamlit as st

from data.loader import engineer_features, filter_data, get_stations, load_csv
from models.trainer import (
    auto_train_if_needed, checksum, estimate_rain_hours,
    get_monthly_stats, is_trained, predict, train, DATA_PATH,
)
from utils.charts import (
    heatmap_monthly, humidity_vs_rain,
    rain_probability_by_month, rainfall_bar, temp_band,
)
from utils.style import (
    alert_banner, inject_css, kpi_grid, nav_pills,
    topbar, weather_hero, week_strip,
)

st.set_page_config(
    page_title="RainForecaster",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()

# ── Session defaults ────────────────────────────────────────────────────────
_DEFAULTS = {
    "tab":          "Forecast",
    "sel_day_idx":  0,
    "df_feat":      None,
    "month_stats":  None,
    "trained_msg":  None,
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Auto-load data & train on first run ─────────────────────────────────────
@st.cache_resource(show_spinner=False)
def _startup():
    """Runs once per process. Loads CSV and trains model if not cached."""
    df = None
    feat = None
    stats = None
    train_result = None

    if DATA_PATH.exists():
        try:
            df   = load_csv(DATA_PATH)
            feat = engineer_features(df)
            stats = get_monthly_stats(feat)
        except Exception as e:
            st.error(f"Gagal load data: {e}")

    if not is_trained() and feat is not None:
        try:
            train_result = train(feat)
        except Exception as e:
            st.error(f"Auto-train gagal: {e}")
    elif not is_trained():
        # Try auto_train (will find data itself)
        train_result = auto_train_if_needed()

    return df, feat, stats, train_result


df_raw, df_feat, month_stats, _train_info = _startup()

# Populate session state from startup
if st.session_state.df_feat is None and df_feat is not None:
    st.session_state.df_feat   = df_feat
    st.session_state.month_stats = month_stats


# ── Helpers ─────────────────────────────────────────────────────────────────

def _build_row(target_date: datetime.date, feats: dict) -> pd.DataFrame:
    dt = pd.Timestamp(target_date)
    return pd.DataFrame([{
        **feats,
        "month_sin": np.sin(2 * np.pi * dt.month / 12),
        "month_cos": np.cos(2 * np.pi * dt.month / 12),
        "doy_sin":   np.sin(2 * np.pi * dt.dayofyear / 365),
        "doy_cos":   np.cos(2 * np.pi * dt.dayofyear / 365),
    }])


def _infer(target_date: datetime.date) -> dict:
    """
    Get features for target_date using historical monthly median as base,
    then apply deterministic daily variation so each date looks different.
    Uses date as seed → same date always gives same result (stable on rerun).
    """
    stats = st.session_state.month_stats
    if stats:
        base = dict(stats.get(target_date.month, list(stats.values())[0]))
    else:
        base = {
            "Tn": 22.0, "Tx": 32.0, "Tavg": 27.0, "RH_avg": 82.0,
            "ss": 5.0, "ff_x": 6.0, "ff_avg": 4.0,
            "RR_roll7": 5.0, "Tavg_roll7": 27.0, "RH_avg_roll7": 82.0,
        }

    # Seeded RNG from date → deterministic, berbeda tiap hari
    seed = target_date.year * 10000 + target_date.month * 100 + target_date.day
    rng  = np.random.default_rng(seed)

    def jitter(val, scale, lo=None, hi=None):
        """Gaussian noise dengan clamp."""
        v = val + rng.normal(0, scale)
        if lo is not None: v = max(lo, v)
        if hi is not None: v = min(hi, v)
        return round(float(v), 1)

    base["Tavg"]   = jitter(base["Tavg"],   1.2, -5,  50)
    base["Tn"]     = jitter(base["Tn"],     1.0, -5,  base["Tavg"])
    base["Tx"]     = jitter(base["Tx"],     1.5, base["Tavg"], 55)
    base["RH_avg"] = jitter(base["RH_avg"], 4.0,  30, 100)
    base["ss"]     = jitter(base["ss"],     1.5,  0,  12)
    base["ff_x"]   = jitter(base["ff_x"],   1.0,  0,  30)
    base["ff_avg"] = jitter(base["ff_avg"], 0.8,  0,  base["ff_x"])

    # Roll7: variasi lebih kecil (rolling average sudah lebih smooth)
    base["RR_roll7"]    = jitter(base.get("RR_roll7", 5.0),    1.5, 0)
    base["Tavg_roll7"]  = jitter(base.get("Tavg_roll7", 27.0), 0.8, -5, 50)
    base["RH_avg_roll7"]= jitter(base.get("RH_avg_roll7", 82.0), 2.5, 30, 100)

    return base


def _verdict(prob: float, mm: float | None):
    if prob >= 0.75:
        return "Hujan Lebat", "#F87171", "⛈️", "alert-heavy", "Kemungkinan besar hujan lebat. Hindari bepergian."
    if prob >= 0.5:
        return "Akan Hujan", "#38BDF8", "🌧️", "alert-rain", "Siapkan payung sebelum keluar."
    if prob >= 0.3:
        return "Mungkin Hujan", "#FDE047", "🌦️", "alert-maybe", "Ada kemungkinan hujan ringan."
    return "Cerah", "#4ADE80", "☀️", "alert-clear", "Cuaca cerah. Nikmati harimu!"


def _intensity(mm: float | None, prob: float) -> str:
    if mm and mm > 50: return "Sangat Lebat"
    if mm and mm > 20: return "Lebat"
    if mm and mm > 5:  return "Sedang"
    if prob > 0.5:     return "Ringan"
    return "Tidak ada"


def _run_forecast(target_date: datetime.date):
    feats    = _infer(target_date)
    row      = _build_row(target_date, feats)
    prob, mm = predict(row)
    hours    = estimate_rain_hours(
        prob, mm, target_date.month,
        ss=feats.get("ss",     6.0),
        rh=feats.get("RH_avg", 80.0),
    )
    return prob, mm, hours, feats


# ── Header & Nav ────────────────────────────────────────────────────────────
topbar(is_trained())

nav_pills(st.session_state.tab)

# Real buttons hidden via CSS — overlaid on top of the pill strip
st.markdown('<div class="nav-btn-overlay">', unsafe_allow_html=True)
_nc1, _nc2, _nc3, _ = st.columns([1, 1, 1, 6])
with _nc1:
    if st.button("Dashboard", key="nav_d", use_container_width=True):
        st.session_state.tab = "Dashboard"; st.rerun()
with _nc2:
    if st.button("Forecast", key="nav_f", use_container_width=True):
        st.session_state.tab = "Forecast"; st.rerun()
with _nc3:
    if st.button("Data", key="nav_data", use_container_width=True):
        st.session_state.tab = "Data"; st.rerun()
st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# FORECAST TAB  (default landing page)
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.tab == "Forecast":

    if not is_trained():
        st.markdown("""
        <div class="train-banner">
            <div class="train-banner-title"><span class="radar-icon">📡</span> Melatih Model AI...</div>
            <div class="train-banner-sub">Taruh file <code>weather_data.csv</code> di folder <code>data/</code> lalu restart app.</div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    today  = datetime.date.today()
    # ── Mode selector ──────────────────────────────────────────────────────
    st.markdown('<div class="sec-label">Mode Prediksi</div>', unsafe_allow_html=True)
    mode = st.radio(
        "mode", ["🔮  Smart Mode", "🛠  Manual Mode"],
        horizontal=True, label_visibility="collapsed"
    )

    smart = "Smart" in mode

    if smart:
        # ── 7-day strip ──────────────────────────────────────────────────
        st.markdown('<div class="sec-label">Pilih Tanggal</div>', unsafe_allow_html=True)

        week_days = []
        for i in range(7):
            d = today + datetime.timedelta(days=i)
            try:
                p, m, _, _ = _run_forecast(d)
                week_days.append({"date": d, "prob": p, "mm": m})
            except Exception:
                week_days.append({"date": d, "prob": 0.0, "mm": None})

        # Render HTML strip (visual only)
        week_strip(week_days, st.session_state.sel_day_idx)

        # Clickable day selectors below strip
        day_cols = st.columns(7)
        for i, (col, d) in enumerate(zip(day_cols, week_days)):
            with col:
                lbl = d["date"].strftime("%d/%m")
                if st.button(lbl, key=f"day_{i}", use_container_width=True):
                    st.session_state.sel_day_idx = i
                    st.rerun()

        # Also allow arbitrary date
        st.markdown('<div class="sec-label" style="margin-top:1rem">Atau Pilih Tanggal Lain</div>', unsafe_allow_html=True)
        custom_col, _ = st.columns([1.5, 5])
        with custom_col:
            custom_date = st.date_input("Tanggal", value=today + datetime.timedelta(days=1),
                label_visibility="collapsed")

        # Determine active date: custom if changed, else selected day
        sel_idx    = st.session_state.sel_day_idx
        if sel_idx < len(week_days):
            active_date = week_days[sel_idx]["date"]
        else:
            active_date = custom_date

        # Use custom_date if user changed it away from "tomorrow"
        if custom_date != today + datetime.timedelta(days=1):
            active_date = custom_date

        # ── Run prediction ────────────────────────────────────────────────
        try:
            prob, mm, hours, feats = _run_forecast(active_date)
        except Exception as e:
            st.error(f"Prediksi gagal: {e}"); st.stop()

        verdict, color, icon, alert_cls, advice = _verdict(prob, mm)
        intensity = _intensity(mm, prob)

        # Hero card
        weather_hero(
            date_str=active_date.strftime("%A, %d %B %Y"),
            verdict=verdict, sub=f"Berdasarkan pola historis bulan {active_date.strftime('%B')}",
            prob=prob, mm=mm, intensity=intensity,
            color=color, icon=icon, rain_window=hours,
        )

        alert_banner(alert_cls, icon, advice)

        # Inferred values detail
        with st.expander("Detail nilai yang diestimasi dari data historis"):
            ec = st.columns(4)
            items = [
                ("Suhu Avg", f"{feats['Tavg']:.1f} °C"),
                ("Suhu Min", f"{feats['Tn']:.1f} °C"),
                ("Suhu Max", f"{feats['Tx']:.1f} °C"),
                ("Kelembapan", f"{feats['RH_avg']:.0f} %"),
                ("Matahari", f"{feats['ss']:.1f} jam"),
                ("Angin Maks", f"{feats['ff_x']:.1f} m/s"),
                ("Angin Avg", f"{feats['ff_avg']:.1f} m/s"),
                ("RR 7 hari", f"{feats['RR_roll7']:.1f} mm"),
            ]
            for i, (lbl, val) in enumerate(items):
                ec[i % 4].metric(lbl, val)

    else:
        # ── MANUAL MODE ───────────────────────────────────────────────────
        # FIX 1: Removed st.form wrapper — forms cannot contain st.stop() after
        # submit and cause "Missing Submit Button" warnings in certain Streamlit
        # versions. Using individual keys on every widget instead.
        st.markdown('<div class="sec-label">Kondisi Cuaca</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        target_date = c1.date_input("Tanggal",               value=today + datetime.timedelta(days=1), key="m_date")
        tavg = c2.number_input("Suhu Rata-rata (°C)",        value=27.0, min_value=-5.0, max_value=50.0, key="m_tavg")
        tn   = c2.number_input("Suhu Min (°C)",              value=22.0, min_value=-5.0, max_value=45.0, key="m_tn")
        tx   = c3.number_input("Suhu Max (°C)",              value=32.0, min_value=-5.0, max_value=55.0, key="m_tx")
        rh   = c3.number_input("Kelembapan (%)",             value=82.0, min_value=0.0,  max_value=100.0, key="m_rh")

        c4, c5, c6 = st.columns(3)
        ss     = c4.number_input("Durasi Matahari (h)",      value=5.0,  key="m_ss")
        ff_x   = c5.number_input("Angin Maks (m/s)",         value=6.0,  key="m_ffx")
        ff_avg = c6.number_input("Angin Rata-rata (m/s)",    value=4.0,  key="m_ffavg")

        st.markdown('<div class="sec-label">Rata-rata 7 Hari Terakhir</div>', unsafe_allow_html=True)
        r1, r2, r3 = st.columns(3)
        rr_r   = r1.number_input("Curah Hujan (mm)",         value=5.0,  min_value=0.0,               key="m_rrr")
        tavg_r = r2.number_input("Suhu 7 Hari (°C)",         value=27.0, min_value=-5.0, max_value=50.0, key="m_tavgr")
        # FIX 2: Renamed label "Kelembapan 7 Hari (%)" to avoid duplicate element ID
        # with the "Kelembapan (%)" widget above (same label = same auto-generated ID)
        rh_r   = r3.number_input("Kelembapan 7 Hari (%)",   value=82.0, min_value=0.0,  max_value=100.0, key="m_rhr")

        go = st.button("Prediksi Sekarang →", type="primary", use_container_width=True, key="m_go")

        if not go:
            st.stop()

        feats = {"Tn": tn, "Tx": tx, "Tavg": tavg, "RH_avg": rh,
                 "ss": ss, "ff_x": ff_x, "ff_avg": ff_avg,
                 "RR_roll7": rr_r, "Tavg_roll7": tavg_r, "RH_avg_roll7": rh_r}
        row = _build_row(target_date, feats)
        try:
            prob, mm = predict(row)
        except Exception as e:
            st.error(f"Prediksi gagal: {e}"); st.stop()

        hours = estimate_rain_hours(
            prob, mm, target_date.month,
            ss=ss,
            rh=rh,
        )
        verdict, color, icon, alert_cls, advice = _verdict(prob, mm)
        intensity = _intensity(mm, prob)

        weather_hero(
            date_str=target_date.strftime("%A, %d %B %Y"),
            verdict=verdict, sub="Berdasarkan input kondisi manual",
            prob=prob, mm=mm, intensity=intensity,
            color=color, icon=icon, rain_window=hours,
        )
        alert_banner(alert_cls, icon, advice)


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD TAB
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.tab == "Dashboard":
    feat = st.session_state.df_feat

    if feat is None:
        st.markdown("""
        <div style="text-align:center;padding:4rem 0;color:#334155">
            <div style="font-size:3rem;margin-bottom:12px">📊</div>
            <div style="font-size:1rem;color:#475569">Tidak ada data. Taruh <code>weather_data.csv</code> di folder <code>data/</code>.</div>
        </div>""", unsafe_allow_html=True)
        st.stop()

    stations = get_stations(feat)

    # ── Inline filters ────────────────────────────────────────────────────
    st.markdown('<div class="sec-label">Filter</div>', unsafe_allow_html=True)
    fc1, fc2, fc3, fc4 = st.columns([2, 1.5, 1.5, 1])
    with fc1:
        sel_st = st.multiselect("Stasiun", stations, default=stations,
            label_visibility="collapsed", placeholder="Semua stasiun")
    dmin, dmax = feat["date"].min().date(), feat["date"].max().date()
    with fc2:
        ds = st.date_input("Dari",   value=dmin, min_value=dmin, max_value=dmax, label_visibility="collapsed")
    with fc3:
        de = st.date_input("Sampai", value=dmax, min_value=dmin, max_value=dmax, label_visibility="collapsed")
    with fc4:
        rain_only = st.checkbox("Hujan saja")

    filtered = filter_data(feat, station_ids=sel_st or None,
        date_start=str(ds), date_end=str(de), rain_only=rain_only)

    if filtered.empty:
        st.warning("Tidak ada data untuk filter ini."); st.stop()

    kpi_grid(
        records=len(filtered),
        rainy=int((filtered["RR"] > 0.5).sum()),
        avg_rain=filtered["RR"].mean(),
        avg_temp=filtered["Tavg"].mean(),
    )

    r1l, r1r = st.columns(2)
    with r1l:
        st.plotly_chart(rainfall_bar(filtered), use_container_width=True, config={"displayModeBar": False})
    with r1r:
        st.plotly_chart(rain_probability_by_month(filtered), use_container_width=True, config={"displayModeBar": False})

    st.plotly_chart(temp_band(filtered), use_container_width=True, config={"displayModeBar": False})

    r2l, r2r = st.columns(2)
    with r2l:
        st.plotly_chart(humidity_vs_rain(filtered), use_container_width=True, config={"displayModeBar": False})
    with r2r:
        st.plotly_chart(heatmap_monthly(filtered), use_container_width=True, config={"displayModeBar": False})


# ══════════════════════════════════════════════════════════════════════════════
# DATA TAB
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.tab == "Data":
    feat = st.session_state.df_feat

    # ── Data status ───────────────────────────────────────────────────────
    if feat is not None:
        st.success(
            f"**{len(feat):,} baris** · **{feat['station_id'].nunique()} stasiun** · "
            f"{feat['date'].min().strftime('%d %b %Y')} → {feat['date'].max().strftime('%d %b %Y')}"
        )
    else:
        st.warning(f"File `weather_data.csv` tidak ditemukan di `{DATA_PATH}`. "
                   "Upload manual di bawah atau taruh file di path tersebut lalu restart.")
        uploaded = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")
        if uploaded:
            try:
                df   = load_csv(uploaded)
                feat = engineer_features(df)
                st.session_state.df_feat    = feat
                st.session_state.month_stats = get_monthly_stats(feat)
                st.success(f"Loaded {len(feat):,} rows.")
                st.rerun()
            except ValueError as e:
                st.error(f"File tidak valid: {e}")
        st.stop()

    # ── Model training ────────────────────────────────────────────────────
    with st.expander("🤖  Model AI", expanded=not is_trained()):
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Training rows", f"{len(feat):,}")
        mc2.metric("Stasiun", feat["station_id"].nunique())
        mc3.metric("Hari hujan", f"{(feat['RR'] > 0.5).sum():,}")

        if is_trained():
            st.caption(f"Model aktif · MD5: `{checksum()}`")
            if st.button("Retrain Model"):
                with st.spinner("Training…"):
                    try:
                        m = train(feat)
                        st.success(f"Selesai — Acc: {m['accuracy']:.2%}  AUC: {m['roc_auc']:.3f}")
                    except Exception as e:
                        st.error(str(e))
        else:
            if st.button("Train Model Sekarang", type="primary"):
                with st.spinner("Training Gradient Boosting + Random Forest…"):
                    try:
                        m = train(feat)
                        st.success(f"Training selesai! Acc: {m['accuracy']:.2%}  AUC: {m['roc_auc']:.3f}")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    # ── Data preview ──────────────────────────────────────────────────────
    st.markdown('<div class="sec-label">Preview Data</div>', unsafe_allow_html=True)
    stations = get_stations(feat)
    pc1, pc2, pc3 = st.columns([2, 1.5, 1.5])
    with pc1:
        psel = st.multiselect("Stasiun", stations, default=stations, placeholder="Semua")
    dmin, dmax = feat["date"].min().date(), feat["date"].max().date()
    with pc2:
        ps = st.date_input("Dari",   value=dmin, min_value=dmin, max_value=dmax, key="p_s")
    with pc3:
        pe = st.date_input("Sampai", value=dmax, min_value=dmin, max_value=dmax, key="p_e")

    pf = filter_data(feat, station_ids=psel or None, date_start=str(ps), date_end=str(pe))
    pcols = [c for c in ["date","station_id","Tn","Tx","Tavg","RH_avg","RR","ss"] if c in pf.columns]
    st.dataframe(pf[pcols].head(1000), use_container_width=True, hide_index=True)
    st.download_button("Download CSV", pf.to_csv(index=False).encode(), "filtered.csv", "text/csv")