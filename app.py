"""
Nusantara RainForecaster — main entry point.
No sidebar. Tabs: Dashboard · Data · Forecast
Forecast has two modes:
  - Smart Mode: pick any date → ML auto-infers features from historical patterns
  - Manual Mode: user inputs all weather params manually
"""

import datetime

import numpy as np
import pandas as pd
import streamlit as st

from data.loader import (
    MAX_UPLOAD_BYTES,
    engineer_features,
    filter_data,
    get_stations,
    load_csv,
)
from models.trainer import checksum, is_trained, predict, train
from utils.charts import (
    heatmap_monthly,
    humidity_vs_rain,
    rain_probability_by_month,
    rainfall_bar,
    temp_band,
)
from utils.style import (
    header,
    inject_css,
    prediction_card,
    stat_cards,
)

st.set_page_config(
    page_title="Nusantara RainForecaster",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()

# ── Session state ──────────────────────────────────────────────────────────
for key, default in [("df_raw", None), ("tab", "Dashboard"), ("forecast_mode", "smart")]:
    if key not in st.session_state:
        st.session_state[key] = default


def _df() -> pd.DataFrame | None:
    return st.session_state.df_raw


def _featured() -> pd.DataFrame | None:
    df = _df()
    return engineer_features(df) if df is not None else None


def _infer_features_from_history(df: pd.DataFrame, target_date: datetime.date) -> dict:
    """
    Smart Mode: estimate weather features for a given date by averaging
    historical values for the same month across all years in the dataset.
    Falls back to overall medians when the month has no data.
    """
    df = df.copy()
    month = target_date.month
    same_month = df[df["date"].dt.month == month]
    src = same_month if len(same_month) >= 10 else df

    def med(col): return float(src[col].median()) if col in src.columns and src[col].notna().any() else 0.0

    # 7-day rolling: use same-month average of RR_roll7 if available,
    # else just use same-month median RR as proxy
    rr_roll   = med("RR_roll7")   if "RR_roll7"   in src.columns else med("RR")
    tavg_roll = med("Tavg_roll7") if "Tavg_roll7" in src.columns else med("Tavg")
    rh_roll   = med("RH_avg_roll7") if "RH_avg_roll7" in src.columns else med("RH_avg")

    return {
        "Tn": med("Tn"), "Tx": med("Tx"), "Tavg": med("Tavg"),
        "RH_avg": med("RH_avg"), "ss": med("ss"),
        "ff_x": med("ff_x"), "ff_avg": med("ff_avg"),
        "RR_roll7": rr_roll,
        "Tavg_roll7": tavg_roll,
        "RH_avg_roll7": rh_roll,
    }


def _build_feature_row(target_date: datetime.date, feats: dict) -> pd.DataFrame:
    dt    = pd.Timestamp(target_date)
    month = dt.month
    doy   = dt.dayofyear
    return pd.DataFrame([{
        **feats,
        "month_sin": np.sin(2 * np.pi * month / 12),
        "month_cos": np.cos(2 * np.pi * month / 12),
        "doy_sin":   np.sin(2 * np.pi * doy / 365),
        "doy_cos":   np.cos(2 * np.pi * doy / 365),
    }])


def _render_result(target_date: datetime.date, prob: float, mm: float | None, inferred: dict | None = None) -> None:
    if prob >= 0.75:
        verdict, color, badge_cls = "Hujan Lebat", "#38BDF8", "badge-warn"
        advice = "Kemungkinan besar hujan lebat. Pertimbangkan untuk tidak keluar."
    elif prob >= 0.5:
        verdict, color, badge_cls = "Kemungkinan Hujan", "#60A5FA", "badge-info"
        advice = "Ada kemungkinan hujan. Bawa payung."
    elif prob >= 0.3:
        verdict, color, badge_cls = "Gerimis Mungkin", "#94A3B8", "badge-info"
        advice = "Kemungkinan kecil hujan. Cuaca kemungkinan baik-baik saja."
    else:
        verdict, color, badge_cls = "Cerah & Kering", "#22C55E", "badge-ok"
        advice = "Probabilitas hujan rendah. Nikmati harimu!"

    intensity = (
        "Lebat"   if mm and mm > 50 else
        "Sedang"  if mm and mm > 10 else
        "Ringan"  if prob > 0.5     else
        "Tidak ada"
    )

    prediction_card(
        date_str=target_date.strftime("%A, %d %B %Y"),
        prob=prob, mm=mm, intensity=intensity,
        verdict=verdict, color=color,
    )
    st.markdown(
        f'<div class="badge {badge_cls}" style="margin-top:12px">{advice}</div>',
        unsafe_allow_html=True,
    )

    # If Smart Mode, show the inferred values in a collapsed expander
    if inferred:
        with st.expander("Nilai yang diestimasi dari data historis"):
            cols = st.columns(4)
            labels = [
                ("Avg Temp", f"{inferred['Tavg']:.1f} °C"),
                ("Min Temp", f"{inferred['Tn']:.1f} °C"),
                ("Max Temp", f"{inferred['Tx']:.1f} °C"),
                ("Humidity", f"{inferred['RH_avg']:.0f} %"),
                ("Sunshine", f"{inferred['ss']:.1f} h"),
                ("Wind Max", f"{inferred['ff_x']:.1f} m/s"),
                ("Wind Avg", f"{inferred['ff_avg']:.1f} m/s"),
                ("RR 7d avg", f"{inferred['RR_roll7']:.1f} mm"),
            ]
            for i, (lbl, val) in enumerate(labels):
                cols[i % 4].metric(lbl, val)


def _no_data_banner() -> None:
    st.markdown("""
    <div style="text-align:center;padding:4rem 0;">
        <div style="font-size:2.5rem;margin-bottom:12px">⛅</div>
        <div style="font-size:1rem;font-weight:500;color:#94A3B8;margin-bottom:6px">
            Belum ada data
        </div>
        <div style="font-size:.85rem;color:#4B6A8A">
            Buka tab <strong style="color:#38BDF8">Data</strong> untuk upload CSV kamu.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Header & Navigation ────────────────────────────────────────────────────

header()

TABS = ["Dashboard", "Data", "Forecast"]

nav_html = '<div class="rf-nav">'
for t in TABS:
    active = "active" if st.session_state.tab == t else ""
    nav_html += f'<button class="rf-nav-btn {active}" disabled>{t}</button>'
nav_html += "</div>"
st.markdown(nav_html, unsafe_allow_html=True)

nc1, nc2, nc3, _ = st.columns([1, 1, 1, 6])
for col, tab_name in zip([nc1, nc2, nc3], TABS):
    with col:
        if st.button(tab_name, use_container_width=True, key=f"nav_{tab_name}"):
            st.session_state.tab = tab_name
            st.rerun()

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════
if st.session_state.tab == "Dashboard":
    df = _df()
    if df is None:
        _no_data_banner()
        st.stop()

    feat = engineer_features(df)
    stations = get_stations(feat)

    fc1, fc2, fc3, fc4 = st.columns([2, 1.5, 1.5, 1])
    with fc1:
        sel_stations = st.multiselect("Station", stations, default=stations,
            label_visibility="collapsed", placeholder="All stations")
    date_min, date_max = feat["date"].min().date(), feat["date"].max().date()
    with fc2:
        d_start = st.date_input("From", value=date_min, min_value=date_min,
            max_value=date_max, label_visibility="collapsed")
    with fc3:
        d_end = st.date_input("To", value=date_max, min_value=date_min,
            max_value=date_max, label_visibility="collapsed")
    with fc4:
        rain_only = st.checkbox("Hujan saja")

    filtered = filter_data(feat, station_ids=sel_stations or None,
        date_start=str(d_start), date_end=str(d_end), rain_only=rain_only)

    if filtered.empty:
        st.warning("Tidak ada data yang cocok dengan filter ini.")
        st.stop()

    stat_cards(
        records=len(filtered),
        rainy=int((filtered["RR"] > 0.5).sum()),
        avg_rain=filtered["RR"].mean(),
        avg_temp=filtered["Tavg"].mean(),
    )

    row1l, row1r = st.columns(2)
    with row1l:
        st.plotly_chart(rainfall_bar(filtered), use_container_width=True, config={"displayModeBar": False})
    with row1r:
        st.plotly_chart(rain_probability_by_month(filtered), use_container_width=True, config={"displayModeBar": False})

    st.plotly_chart(temp_band(filtered), use_container_width=True, config={"displayModeBar": False})

    row2l, row2r = st.columns(2)
    with row2l:
        st.plotly_chart(humidity_vs_rain(filtered), use_container_width=True, config={"displayModeBar": False})
    with row2r:
        st.plotly_chart(heatmap_monthly(filtered), use_container_width=True, config={"displayModeBar": False})


# ══════════════════════════════════════════════════════════════════════════
# DATA (was Explorer)
# ══════════════════════════════════════════════════════════════════════════
elif st.session_state.tab == "Data":
    st.markdown('<div class="section-title">Upload Data CSV</div>', unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Drop your BMKG weather CSV here",
        type=["csv"],
        help="Kolom wajib: date (DD-MM-YYYY), Tn, Tx, Tavg, RH_avg, RR, station_id",
        label_visibility="collapsed",
    )

    if uploaded is not None:
        if uploaded.size > MAX_UPLOAD_BYTES:
            st.error(f"File terlalu besar ({uploaded.size/1e6:.0f} MB). Maks 200 MB.")
            st.stop()
        with st.spinner("Memproses dan memvalidasi…"):
            try:
                df = load_csv(uploaded)
                st.session_state.df_raw = df
            except ValueError as e:
                st.error(f"File tidak valid: {e}")
                st.stop()

    df = _df()
    if df is None:
        st.info("Upload CSV untuk mulai. Kolom wajib: `date`, `Tn`, `Tx`, `Tavg`, `RH_avg`, `RR`, `station_id`")
        st.stop()

    st.success(
        f"**{len(df):,} baris** · **{df['station_id'].nunique()} stasiun** · "
        f"{df['date'].min().strftime('%d %b %Y')} → {df['date'].max().strftime('%d %b %Y')}"
    )

    # Train model straight from this tab
    with st.expander("Train Model AI", expanded=not is_trained()):
        feat = engineer_features(df)
        tc1, tc2, tc3 = st.columns(3)
        tc1.metric("Baris training", f"{len(feat):,}")
        tc2.metric("Stasiun", feat["station_id"].nunique())
        tc3.metric("Hari hujan", f"{(feat['RR'] > 0.5).sum():,}")

        if st.button("Mulai Training", type="primary"):
            with st.spinner("Training Gradient Boosting + Random Forest…"):
                try:
                    m = train(feat)
                    st.success("Training selesai!")
                    mc1, mc2, mc3 = st.columns(3)
                    mc1.metric("Accuracy", f"{m['accuracy']:.2%}")
                    mc2.metric("ROC-AUC",  f"{m['roc_auc']:.3f}")
                    mc3.metric("Rain MAE", f"{m['mae']:.1f} mm" if m["mae"] else "N/A")
                except Exception as e:
                    st.error(f"Training gagal: {e}")

    if is_trained():
        st.caption(f"Model checksum (MD5): `{checksum()}`")

    st.markdown('<div class="section-title">Filter & Preview</div>', unsafe_allow_html=True)
    ec1, ec2, ec3 = st.columns([2, 1.5, 1.5])
    stations = get_stations(df)
    with ec1:
        sel = st.multiselect("Stasiun", stations, default=stations, placeholder="Semua stasiun")
    date_min, date_max = df["date"].min().date(), df["date"].max().date()
    with ec2:
        es = st.date_input("Dari", value=date_min, min_value=date_min, max_value=date_max, key="exp_s")
    with ec3:
        ee = st.date_input("Sampai", value=date_max, min_value=date_min, max_value=date_max, key="exp_e")

    filt = filter_data(df, station_ids=sel or None, date_start=str(es), date_end=str(ee))
    st.markdown(f"**{len(filt):,} records** cocok.")

    preview_cols = [c for c in ["date","station_id","Tn","Tx","Tavg","RH_avg","RR","ss"] if c in filt.columns]
    st.dataframe(filt[preview_cols].head(1000), use_container_width=True, hide_index=True)
    st.download_button("Download CSV", filt.to_csv(index=False).encode(), "filtered_weather.csv", "text/csv")


# ══════════════════════════════════════════════════════════════════════════
# FORECAST — Smart Mode + Manual Mode
# ══════════════════════════════════════════════════════════════════════════
elif st.session_state.tab == "Forecast":

    if not is_trained():
        st.markdown("""
        <div style="text-align:center;padding:3rem 0;">
            <div style="font-size:1.8rem;margin-bottom:8px">🤖</div>
            <div style="font-size:1rem;color:#94A3B8;font-weight:500">Model belum ditraining</div>
            <div style="font-size:.85rem;color:#4B6A8A;margin-top:4px">
                Upload data dan train model di tab <strong style="color:#38BDF8">Data</strong> dulu.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # ── Mode switcher ──
    st.markdown('<div class="section-title">Mode Prediksi</div>', unsafe_allow_html=True)
    mode_col, _ = st.columns([2, 5])
    with mode_col:
        mode = st.radio(
            "mode",
            ["Smart Mode", "Manual Mode"],
            horizontal=True,
            label_visibility="collapsed",
            key="forecast_mode_radio",
        )

    # Mode description
    if mode == "Smart Mode":
        st.markdown("""
        <div class="mode-desc">
            <strong>Smart Mode</strong> — Pilih tanggal, AI otomatis memperkirakan kondisi cuaca
            berdasarkan pola historis bulan tersebut. Tidak perlu input apapun.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="mode-desc">
            <strong>Manual Mode</strong> — Masukkan kondisi cuaca aktual secara manual
            untuk prediksi yang lebih presisi.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")

    # ══════════════════
    # SMART MODE
    # ══════════════════
    if mode == "Smart Mode":
        df = _df()
        if df is None:
            st.warning("Upload data historis di tab Data agar Smart Mode bisa bekerja.")
            st.stop()

        feat = engineer_features(df)

        # Date picker — allow any date, past or future
        today = datetime.date.today()
        sc1, sc2, _ = st.columns([1.5, 1.5, 4])
        with sc1:
            target_date = st.date_input(
                "Pilih tanggal",
                value=today + datetime.timedelta(days=1),
                key="smart_date",
            )
        with sc2:
            # Quick-pick buttons
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("Besok", key="btn_tomorrow"):
                target_date = today + datetime.timedelta(days=1)
            
        # Show quick range forecast (next 7 days)
        show_range = st.checkbox("Lihat 7 hari ke depan sekaligus", value=False)

        if show_range:
            st.markdown('<div class="section-title">Prakiraan 7 Hari</div>', unsafe_allow_html=True)
            days_data = []
            for i in range(7):
                d = today + datetime.timedelta(days=i)
                feats = _infer_features_from_history(feat, d)
                row = _build_feature_row(d, feats)
                try:
                    p, m = predict(row)
                    days_data.append({"date": d, "prob": p, "mm": m})
                except Exception:
                    pass

            if days_data:
                # Render 7-day strip
                day_cols = st.columns(7)
                day_names = ["Sen","Sel","Rab","Kam","Jum","Sab","Min"]
                for i, (col, d) in enumerate(zip(day_cols, days_data)):
                    p = d["prob"]
                    m = d["mm"]
                    icon = "🌧️" if p >= 0.5 else ("🌦️" if p >= 0.3 else "☀️")
                    color = "#38BDF8" if p >= 0.75 else ("#60A5FA" if p >= 0.5 else ("#94A3B8" if p >= 0.3 else "#22C55E"))
                    mm_str = f"{m:.0f}mm" if m else "—"
                    col.markdown(f"""
                    <div class="day-card">
                        <div class="day-name">{day_names[d['date'].weekday()]}</div>
                        <div class="day-date">{d['date'].strftime('%d/%m')}</div>
                        <div class="day-icon">{icon}</div>
                        <div class="day-prob" style="color:{color}">{p:.0%}</div>
                        <div class="day-mm">{mm_str}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            # Single date prediction
            feats = _infer_features_from_history(feat, target_date)
            row   = _build_feature_row(target_date, feats)

            with st.spinner("Menganalisis pola historis…"):
                try:
                    prob, mm = predict(row)
                except Exception as e:
                    st.error(f"Prediksi gagal: {e}")
                    st.stop()

            _render_result(target_date, prob, mm, inferred=feats)

    # ══════════════════
    # MANUAL MODE
    # ══════════════════
    else:
        with st.form("manual_form"):
            st.markdown('<div class="section-title">Kondisi Cuaca Saat Ini</div>', unsafe_allow_html=True)

            r1c1, r1c2, r1c3 = st.columns(3)
            target_date = r1c1.date_input(
                "Tanggal prediksi",
                value=datetime.date.today() + datetime.timedelta(days=1),
            )
            tavg = r1c2.number_input("Suhu Rata-rata (°C)", value=27.0, min_value=-5.0, max_value=50.0)
            tn   = r1c2.number_input("Suhu Min (°C)",        value=22.0, min_value=-5.0, max_value=45.0)
            tx   = r1c3.number_input("Suhu Max (°C)",        value=32.0, min_value=-5.0, max_value=55.0)
            rh   = r1c3.number_input("Kelembapan (%)",       value=82.0, min_value=0.0,  max_value=100.0)

            r2c1, r2c2, r2c3 = st.columns(3)
            ss     = r2c1.number_input("Durasi Matahari (h)",   value=5.0, min_value=0.0, max_value=24.0)
            ff_x   = r2c2.number_input("Kec. Angin Maks (m/s)", value=6.0, min_value=0.0, max_value=80.0)
            ff_avg = r2c3.number_input("Kec. Angin Rata2 (m/s)",value=4.0, min_value=0.0, max_value=60.0)

            st.markdown('<div class="section-title" style="margin-top:12px">Rata-rata 7 Hari Terakhir</div>', unsafe_allow_html=True)
            r3c1, r3c2, r3c3 = st.columns(3)
            rr_roll   = r3c1.number_input("Curah Hujan 7h (mm)",  value=5.0,  min_value=0.0)
            tavg_roll = r3c2.number_input("Suhu Rata2 7h (°C)",   value=27.0, min_value=-5.0, max_value=50.0)
            rh_roll   = r3c3.number_input("Kelembapan 7h (%)",    value=82.0, min_value=0.0,  max_value=100.0)

            submitted = st.form_submit_button("Prediksi Sekarang", type="primary", use_container_width=True)

        if not submitted:
            st.stop()

        feats = {
            "Tn": tn, "Tx": tx, "Tavg": tavg, "RH_avg": rh,
            "ss": ss, "ff_x": ff_x, "ff_avg": ff_avg,
            "RR_roll7": rr_roll, "Tavg_roll7": tavg_roll, "RH_avg_roll7": rh_roll,
        }
        row = _build_feature_row(target_date, feats)

        with st.spinner("Menjalankan inferensi…"):
            try:
                prob, mm = predict(row)
            except Exception as e:
                st.error(f"Prediksi gagal: {e}")
                st.stop()

        _render_result(target_date, prob, mm)