"""
Reusable Plotly chart builders.
All functions return a plotly Figure — Streamlit renders via st.plotly_chart().
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

PALETTE = px.colors.qualitative.Plotly

_LAYOUT = dict(
    paper_bgcolor="#0E1117",
    plot_bgcolor="#0E1117",
    font_color="#FAFAFA",
    margin=dict(l=20, r=20, t=40, b=20),
)


def rainfall_timeseries(df: pd.DataFrame, station_id: str | None = None) -> go.Figure:
    """Daily rainfall bar chart, optionally filtered by station."""
    data = df.copy()
    if station_id:
        data = data[data["station_id"] == station_id]

    if data.empty:
        return _empty_fig("No data for selected filters")

    daily = data.groupby("date")["RR"].mean().reset_index()
    fig = px.bar(
        daily, x="date", y="RR",
        labels={"RR": "Rainfall (mm)", "date": ""},
        title="Daily Average Rainfall",
        color="RR",
        color_continuous_scale="Blues",
    )
    fig.update_layout(**_LAYOUT)
    return fig


def temperature_trend(df: pd.DataFrame) -> go.Figure:
    """Min / avg / max temperature band over time."""
    if df.empty:
        return _empty_fig("No data")

    monthly = df.groupby(df["date"].dt.to_period("M")).agg(
        Tn=("Tn", "mean"),
        Tavg=("Tavg", "mean"),
        Tx=("Tx", "mean"),
    ).reset_index()
    monthly["date"] = monthly["date"].dt.to_timestamp()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly["date"], y=monthly["Tx"],
        name="Tx (max)", line=dict(color="#FF5722", width=1.5),
    ))
    fig.add_trace(go.Scatter(
        x=monthly["date"], y=monthly["Tavg"],
        name="Tavg (avg)", line=dict(color="#4A90D9", width=2),
        fill="tonexty", fillcolor="rgba(74,144,217,0.1)",
    ))
    fig.add_trace(go.Scatter(
        x=monthly["date"], y=monthly["Tn"],
        name="Tn (min)", line=dict(color="#26C6DA", width=1.5),
        fill="tonexty", fillcolor="rgba(38,198,218,0.08)",
    ))
    fig.update_layout(title="Monthly Temperature Range (°C)", **_LAYOUT)
    return fig


def humidity_scatter(df: pd.DataFrame) -> go.Figure:
    """Scatter: humidity vs rainfall, coloured by month."""
    if df.empty:
        return _empty_fig("No data")

    sample = df.dropna(subset=["RH_avg", "RR"]).sample(min(2000, len(df)), random_state=42)
    fig = px.scatter(
        sample, x="RH_avg", y="RR",
        color="month",
        labels={"RH_avg": "Humidity (%)", "RR": "Rainfall (mm)", "month": "Month"},
        title="Humidity vs Rainfall",
        opacity=0.6,
        color_continuous_scale="Viridis",
    )
    fig.update_layout(**_LAYOUT)
    return fig


def monthly_rain_heatmap(df: pd.DataFrame) -> go.Figure:
    """Year × Month heatmap of average rainfall."""
    if df.empty:
        return _empty_fig("No data")

    df = df.copy()
    df["year"] = df["date"].dt.year
    pivot = df.pivot_table(values="RR", index="year", columns="month", aggfunc="mean")

    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=[
                "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
            ],
            y=pivot.index.tolist(),
            colorscale="Blues",
            showscale=True,
        )
    )
    fig.update_layout(title="Average Rainfall by Year & Month (mm)", **_LAYOUT)
    return fig


def wind_rose(df: pd.DataFrame) -> go.Figure:
    """Polar bar chart for wind direction frequency."""
    if "ddd_x" not in df.columns or df["ddd_x"].dropna().empty:
        return _empty_fig("No wind direction data")

    bins = range(0, 361, 45)
    labels = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    df = df.dropna(subset=["ddd_x"])
    df = df.copy()
    df["dir_bin"] = pd.cut(df["ddd_x"], bins=list(bins) + [360], labels=labels + ["N"], right=False)
    counts = df["dir_bin"].value_counts().reindex(labels, fill_value=0)

    fig = go.Figure(
        go.Barpolar(
            r=counts.values,
            theta=labels,
            marker_color="#4A90D9",
            opacity=0.8,
        )
    )
    fig.update_layout(title="Wind Direction Distribution", **_LAYOUT)
    return fig


def _empty_fig(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=message, xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=16, color="#AAAAAA"),
    )
    fig.update_layout(**_LAYOUT)
    return fig