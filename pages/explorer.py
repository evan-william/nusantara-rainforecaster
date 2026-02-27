"""
Data Explorer page — upload a CSV, preview data, download filtered subset.
"""

import io

import streamlit as st

from data.loader import (
    engineer_features,
    filter_data,
    get_station_list,
    load_csv,
    load_sample_data,
)
from utils.charts import rainfall_timeseries

_MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB


def render_explorer() -> None:
    st.title("Data Explorer")
    st.caption("Upload your own BMKG-format CSV or work with the sample dataset.")

    source = st.radio("Data source", ["Use sample dataset", "Upload my CSV"], horizontal=True)

    df = None

    if source == "Upload my CSV":
        uploaded = st.file_uploader(
            "Upload weather CSV",
            type=["csv"],
            help="Must include: date, Tn, Tx, Tavg, RH_avg, RR, station_id columns.",
        )
        if uploaded is not None:
            # Size guard before reading
            if uploaded.size > _MAX_UPLOAD_BYTES:
                st.error(f"File too large ({uploaded.size / 1e6:.1f} MB). Limit is 50 MB.")
                return

            with st.spinner("Parsing and validating…"):
                try:
                    df = engineer_features(load_csv(uploaded))
                    st.success(f"Loaded {len(df):,} rows successfully.")
                except ValueError as exc:
                    st.error(f"Invalid file: {exc}")
                    return
    else:
        try:
            df = engineer_features(load_sample_data())
        except FileNotFoundError:
            st.error(
                "Sample data not found. Run `python data/generate_sample.py` first."
            )
            return

    if df is None:
        st.info("Upload a file or select the sample dataset to begin.")
        return

    # --- Filters ---
    with st.expander("Filters", expanded=True):
        stations = get_station_list(df)
        selected = st.multiselect("Stations", stations, default=stations)

        col1, col2 = st.columns(2)
        date_min = df["date"].min().date()
        date_max = df["date"].max().date()
        start = col1.date_input("From", value=date_min, min_value=date_min, max_value=date_max)
        end = col2.date_input("To", value=date_max, min_value=date_min, max_value=date_max)

        rain_only = st.checkbox("Rainy days only")

    filtered = filter_data(
        df,
        station_ids=selected or None,
        date_start=str(start),
        date_end=str(end),
        rain_only=rain_only,
    )

    st.markdown(f"**{len(filtered):,} records** match filters.")

    if filtered.empty:
        st.warning("No records match selected filters.")
        return

    # --- Preview ---
    display_cols = ["date", "station_id", "Tn", "Tx", "Tavg", "RH_avg", "RR", "ss"]
    st.dataframe(
        filtered[[c for c in display_cols if c in filtered.columns]]
        .head(500)
        .reset_index(drop=True),
        use_container_width=True,
    )

    st.plotly_chart(rainfall_timeseries(filtered), use_container_width=True)

    # --- Download ---
    csv_bytes = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download filtered CSV",
        data=csv_bytes,
        file_name="filtered_weather.csv",
        mime="text/csv",
    )