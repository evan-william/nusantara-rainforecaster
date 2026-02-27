"""Tests for utils/charts.py — just confirm figures are generated without errors."""

import pandas as pd
import pytest

from utils.charts import (
    _empty_fig,
    humidity_scatter,
    monthly_rain_heatmap,
    rainfall_timeseries,
    temperature_trend,
    wind_rose,
)


@pytest.fixture
def sample():
    """Minimal dataframe for chart testing."""
    import numpy as np
    n = 100
    return pd.DataFrame({
        "date": pd.date_range("2020-01-01", periods=n, freq="D"),
        "station_id": "S1",
        "RR": np.where(range(n), 5.0, 0.0),
        "Tn": [20.0] * n,
        "Tx": [32.0] * n,
        "Tavg": [27.0] * n,
        "RH_avg": [85.0] * n,
        "ss": [4.0] * n,
        "month": pd.date_range("2020-01-01", periods=n, freq="D").month,
        "ddd_x": [90.0] * n,
    })


def test_rainfall_timeseries_returns_figure(sample):
    fig = rainfall_timeseries(sample)
    assert fig is not None


def test_rainfall_timeseries_with_station(sample):
    fig = rainfall_timeseries(sample, station_id="S1")
    assert fig is not None


def test_temperature_trend(sample):
    fig = temperature_trend(sample)
    assert fig is not None


def test_humidity_scatter(sample):
    fig = humidity_scatter(sample)
    assert fig is not None


def test_monthly_rain_heatmap(sample):
    fig = monthly_rain_heatmap(sample)
    assert fig is not None


def test_wind_rose(sample):
    fig = wind_rose(sample)
    assert fig is not None


def test_empty_fig_annotation():
    fig = _empty_fig("nothing here")
    assert any(a.text == "nothing here" for a in fig.layout.annotations)


def test_charts_empty_df_no_crash():
    empty = pd.DataFrame()
    # Should return a figure with empty annotation, not raise
    fig = rainfall_timeseries(empty)
    assert fig is not None
    fig = temperature_trend(empty)
    assert fig is not None