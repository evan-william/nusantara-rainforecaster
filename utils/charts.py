"""Plotly chart builders — all return go.Figure."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

_BG   = "#060B14"
_GRID = "#0D1626"
_TEXT = "#E8EEF4"
_ACC  = "#38BDF8"

_BASE = dict(
    paper_bgcolor=_BG,
    plot_bgcolor=_BG,
    font=dict(color=_TEXT, family="'DM Sans', sans-serif", size=12),
    margin=dict(l=12, r=12, t=36, b=12),
    xaxis=dict(gridcolor=_GRID, showline=False, zeroline=False),
    yaxis=dict(gridcolor=_GRID, showline=False, zeroline=False),
)


def rainfall_bar(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("No data")
    daily = df.groupby("date")["RR"].mean().reset_index()
    fig = go.Figure(go.Bar(
        x=daily["date"], y=daily["RR"],
        marker=dict(
            color=daily["RR"],
            colorscale=[[0, "#0D1626"], [0.3, "#0EA5E9"], [1, "#38BDF8"]],
            showscale=False,
        ),
        hovertemplate="%{x|%d %b %Y}<br>%{y:.1f} mm<extra></extra>",
    ))
    fig.update_layout(title="Daily Rainfall (mm)", **_BASE)
    return fig


def temp_band(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("No data")
    m = df.groupby(df["date"].dt.to_period("M")).agg(
        Tn=("Tn", "mean"), Tavg=("Tavg", "mean"), Tx=("Tx", "mean")
    ).reset_index()
    m["date"] = m["date"].dt.to_timestamp()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=m["date"], y=m["Tx"],
        name="Max", line=dict(color="#F97316", width=1.5)))
    fig.add_trace(go.Scatter(x=m["date"], y=m["Tavg"],
        name="Avg", line=dict(color=_ACC, width=2.5),
        fill="tonexty", fillcolor="rgba(56,189,248,0.08)"))
    fig.add_trace(go.Scatter(x=m["date"], y=m["Tn"],
        name="Min", line=dict(color="#818CF8", width=1.5),
        fill="tonexty", fillcolor="rgba(129,140,248,0.06)"))
    fig.update_layout(
        title="Monthly Temperature Range (°C)",
        legend=dict(orientation="h", y=-0.15),
        **_BASE
    )
    return fig


def heatmap_monthly(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("No data")
    df = df.copy()
    df["year"]  = df["date"].dt.year
    df["month"] = df["date"].dt.month
    pivot = df.pivot_table(values="RR", index="year", columns="month", aggfunc="mean")
    month_labels = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[month_labels[i-1] for i in pivot.columns],
        y=pivot.index.astype(str).tolist(),
        colorscale=[[0,"#060B14"],[0.3,"#0369A1"],[0.7,"#0EA5E9"],[1,"#38BDF8"]],
        showscale=True,
        hovertemplate="%{y} %{x}<br>%{z:.1f} mm<extra></extra>",
    ))
    fig.update_layout(title="Avg Rainfall by Year & Month (mm)", **_BASE)
    return fig


def humidity_vs_rain(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("No data")
    s = df.dropna(subset=["RH_avg","RR"]).sample(min(3000, len(df)), random_state=42)
    fig = go.Figure(go.Scatter(
        x=s["RH_avg"], y=s["RR"],
        mode="markers",
        marker=dict(
            color=s["RR"], colorscale="Blues",
            size=5, opacity=0.55, showscale=False,
        ),
        hovertemplate="Humidity: %{x:.0f}%<br>Rain: %{y:.1f} mm<extra></extra>",
    ))
    fig.update_layout(
        title="Humidity vs Rainfall",
        xaxis_title="Humidity (%)", yaxis_title="Rainfall (mm)",
        **_BASE
    )
    return fig


def rain_probability_by_month(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("No data")
    df = df.copy()
    df["month"] = df["date"].dt.month
    prob = df.groupby("month").apply(lambda x: (x["RR"] > 0.5).mean() * 100).reset_index()
    prob.columns = ["month", "pct"]
    labels = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    prob["label"] = prob["month"].apply(lambda m: labels[m-1])

    fig = go.Figure(go.Bar(
        x=prob["label"], y=prob["pct"],
        marker=dict(
            color=prob["pct"],
            colorscale=[[0,"#0D1626"],[0.5,"#0284C7"],[1,"#38BDF8"]],
            showscale=False,
        ),
        hovertemplate="%{x}: %{y:.1f}%<extra></extra>",
    ))
    fig.update_layout(title="Rain Probability by Month (%)", yaxis_range=[0,100], **_BASE)
    return fig


def _empty(msg: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=msg, xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#4B5563"))
    fig.update_layout(**_BASE)
    return fig