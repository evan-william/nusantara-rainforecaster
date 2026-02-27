"""
Dashboard page — historical overview KPIs and charts.
"""

import streamlit as st

from data.loader import (
    engineer_features,
    filter_data,
    get_station_list,
    load_sample_data,
)
from utils.charts import (
    humidity_scatter,
    monthly_rain_heatmap,
    rainfall_timeseries,
    temperature_trend,
    wind_rose,
)


def _load_data():
    """Cache data loading so it doesn't re-run on every widget interaction."""
    try:
        df = load_sample_data()
        return engineer_features(df)
    except FileNotFoundError:
        return None


@st.cache_data(show_spinner=False)
def _cached_load():
    return _load_data()


def render_dashboard() -> None:
    st.title("Weather Dashboard")
    st.caption("Historical overview for Indonesia weather stations")

    with st.spinner("Loading data…"):
        df = _cached_load()

    if df is None:
        st.error(
            "Sample data not found. Run `python data/generate_sample.py` to generate it, "
            "or upload your own CSV via the Data Explorer page."
        )
        return

    # --- Sidebar filters ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filters")

    stations = get_station_list(df)
    selected_stations = st.sidebar.multiselect(
        "Station ID", stations, default=stations[:2]
    )

    date_min = df["date"].min().date()
    date_max = df["date"].max().date()
    date_range = st.sidebar.date_input(
        "Date range",
        value=(date_min, date_max),
        min_value=date_min,
        max_value=date_max,
    )
    rain_only = st.sidebar.checkbox("Show rainy days only")

    # Unpack safely — user might select only one date
    start = str(date_range[0]) if len(date_range) > 0 else None
    end = str(date_range[1]) if len(date_range) > 1 else None

    filtered = filter_data(
        df,
        station_ids=selected_stations or None,
        date_start=start,
        date_end=end,
        rain_only=rain_only,
    )

    if filtered.empty:
        st.warning("No records match the current filters.")
        return

    # --- KPI row ---
    total_days = len(filtered)
    rainy_days = int((filtered["RR"] > 0.5).sum())
    avg_rain = filtered["RR"].mean()
    avg_temp = filtered["Tavg"].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Records", f"{total_days:,}")
    c2.metric("Rainy Days", f"{rainy_days:,}")
    c3.metric("Avg Rainfall", f"{avg_rain:.1f} mm")
    c4.metric("Avg Temperature", f"{avg_temp:.1f} °C")

    st.markdown("---")

    # --- Charts ---
    col_l, col_r = st.columns(2)
    with col_l:
        station_for_ts = selected_stations[0] if selected_stations else None
        st.plotly_chart(
            rainfall_timeseries(filtered, station_id=station_for_ts),
            use_container_width=True,
        )
        st.plotly_chart(temperature_trend(filtered), use_container_width=True)

    with col_r:
        st.plotly_chart(humidity_scatter(filtered), use_container_width=True)
        st.plotly_chart(wind_rose(filtered), use_container_width=True)

    st.plotly_chart(monthly_rain_heatmap(filtered), use_container_width=True)