"""
AI Forecaster page — train models and run predictions.
"""

import datetime

import numpy as np
import pandas as pd
import streamlit as st

from data.loader import engineer_features, load_sample_data
from models.trainer import get_model_checksum, models_exist, predict, train


@st.cache_data(show_spinner=False)
def _get_training_data():
    try:
        df = load_sample_data()
        return engineer_features(df)
    except FileNotFoundError:
        return None


def _confidence_label(prob: float) -> str:
    if prob >= 0.75:
        return f'<span class="confidence-high">{prob*100:.0f}%</span>'
    if prob >= 0.5:
        return f'<span class="confidence-med">{prob*100:.0f}%</span>'
    return f'<span class="confidence-low">{prob*100:.0f}%</span>'


def render_forecast() -> None:
    st.title("AI Micro-Forecaster")
    st.caption(
        "Provide today's conditions and get an estimated rain probability "
        "for the next 24 hours."
    )

    # --- Train section ---
    with st.expander("Model Training", expanded=not models_exist()):
        st.markdown(
            "Train the model on the sample dataset before making predictions. "
            "This takes ~30 seconds."
        )
        if st.button("Train Model", type="primary"):
            df = _get_training_data()
            if df is None:
                st.error("Sample data not found. Run `python data/generate_sample.py`.")
            else:
                with st.spinner("Training… this may take a moment"):
                    try:
                        metrics = train(df)
                        st.success("Training complete!")
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Accuracy", f"{metrics['classifier_accuracy']:.2%}")
                        col2.metric("ROC-AUC", f"{metrics['classifier_roc_auc']:.3f}")
                        mae = metrics.get("regressor_mae")
                        col3.metric(
                            "Rainfall MAE",
                            f"{mae:.1f} mm" if mae is not None else "N/A",
                        )
                    except Exception as exc:
                        st.error(f"Training failed: {exc}")

    if not models_exist():
        st.info("Train the model first to enable predictions.")
        return

    checksum = get_model_checksum()
    st.caption(f"Model checksum (MD5): `{checksum}`")

    st.markdown("---")
    st.subheader("Enter Current Conditions")

    # --- Input form ---
    with st.form("forecast_form"):
        col1, col2, col3 = st.columns(3)

        target_date = col1.date_input(
            "Target date",
            value=datetime.date.today() + datetime.timedelta(days=1),
        )
        tavg = col2.number_input("Avg Temperature (°C)", value=27.0, min_value=-10.0, max_value=55.0)
        tn = col2.number_input("Min Temperature (°C)", value=23.0, min_value=-10.0, max_value=50.0)
        tx = col2.number_input("Max Temperature (°C)", value=32.0, min_value=-10.0, max_value=60.0)
        rh = col3.number_input("Avg Humidity (%)", value=82.0, min_value=0.0, max_value=100.0)
        ss = col3.number_input("Sunshine Duration (h)", value=5.0, min_value=0.0, max_value=24.0)
        ff_x = col1.number_input("Max Wind Speed (m/s)", value=6.0, min_value=0.0, max_value=100.0)
        ff_avg = col1.number_input("Avg Wind Speed (m/s)", value=4.0, min_value=0.0, max_value=100.0)

        st.markdown("**7-day Averages (optional — improves accuracy)**")
        r1, r2, r3 = st.columns(3)
        rr_roll = r1.number_input("Avg RR past 7 days (mm)", value=5.0, min_value=0.0)
        tavg_roll = r2.number_input("Avg Tavg past 7 days (°C)", value=27.0, min_value=-10.0, max_value=55.0)
        rh_roll = r3.number_input("Avg RH past 7 days (%)", value=82.0, min_value=0.0, max_value=100.0)

        submitted = st.form_submit_button("Predict", type="primary")

    if not submitted:
        return

    # Build feature row
    dt = pd.Timestamp(target_date)
    month = dt.month
    doy = dt.dayofyear
    row = pd.DataFrame(
        [
            {
                "Tn": tn,
                "Tx": tx,
                "Tavg": tavg,
                "RH_avg": rh,
                "ss": ss,
                "ff_x": ff_x,
                "ff_avg": ff_avg,
                "month_sin": np.sin(2 * np.pi * month / 12),
                "month_cos": np.cos(2 * np.pi * month / 12),
                "doy_sin": np.sin(2 * np.pi * doy / 365),
                "doy_cos": np.cos(2 * np.pi * doy / 365),
                "RR_roll7": rr_roll,
                "Tavg_roll7": tavg_roll,
                "RH_avg_roll7": rh_roll,
            }
        ]
    )

    with st.spinner("Running inference…"):
        try:
            rain_prob, est_mm = predict(row)
        except Exception as exc:
            st.error(f"Prediction error: {exc}")
            return

    st.markdown("---")
    st.subheader("Prediction Result")

    verdict = "Rain expected" if rain_prob > 0.5 else "No rain expected"
    st.markdown(f"### {verdict} on {target_date.strftime('%A, %d %B %Y')}")

    m1, m2, m3 = st.columns(3)
    m1.metric("Rain Probability", f"{rain_prob:.0%}")
    if est_mm is not None:
        m2.metric("Estimated Rainfall", f"{est_mm:.1f} mm")
    else:
        m2.metric("Estimated Rainfall", "—")

    intensity = (
        "Heavy rain" if est_mm and est_mm > 50
        else "Moderate rain" if est_mm and est_mm > 10
        else "Light rain / drizzle" if rain_prob > 0.5
        else "Dry / Clear"
    )
    m3.metric("Intensity", intensity)

    # Probability bar
    st.progress(int(rain_prob * 100))
    st.markdown(
        f"Confidence: {_confidence_label(rain_prob)}",
        unsafe_allow_html=True,
    )

    # Advisory
    if rain_prob > 0.75:
        st.warning("High probability of rain. Carry an umbrella and check for flood alerts.")
    elif rain_prob > 0.5:
        st.info("Moderate rain probability. Prepare for possible showers.")
    else:
        st.success("Low rain probability. Enjoy the weather!")