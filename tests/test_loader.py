"""Tests for data/loader.py"""

import io
import textwrap

import numpy as np
import pandas as pd
import pytest

from data.loader import (
    _validate_and_clean,
    engineer_features,
    filter_data,
    load_csv,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_CSV = textwrap.dedent(
    """\
    date,Tn,Tx,Tavg,RH_avg,RR,ss,ff_x,ddd_x,ff_avg,ddd_car,station_id
    1/1/2010,21.4,30.2,27.1,82,9,0.5,7,90,5,E,96001
    2/1/2010,21.0,29.6,25.7,95,24,0.2,6,90,4,E,96001
    3/1/2010,20.2,26.8,24.5,98,0,0.0,5,90,4,E,96001
    4/1/2010,21.0,29.2,25.8,90,0,0.1,4,225,3,SW,96001
    """
)


@pytest.fixture
def raw_df() -> pd.DataFrame:
    return pd.read_csv(io.StringIO(VALID_CSV))


@pytest.fixture
def clean_df() -> pd.DataFrame:
    return load_csv(io.StringIO(VALID_CSV))


@pytest.fixture
def featured_df(clean_df) -> pd.DataFrame:
    return engineer_features(clean_df)


# ---------------------------------------------------------------------------
# load_csv / _validate_and_clean
# ---------------------------------------------------------------------------


def test_load_csv_from_file_like(clean_df):
    assert not clean_df.empty
    assert "date" in clean_df.columns
    assert str(clean_df["date"].dtype).startswith("datetime64")


def test_load_csv_from_string_path(tmp_path):
    p = tmp_path / "weather.csv"
    p.write_text(VALID_CSV)
    df = load_csv(str(p))
    assert len(df) == 4


def test_missing_required_column_raises():
    bad_csv = "date,Tn,Tx\n1/1/2010,21.4,30.2\n"
    with pytest.raises(ValueError, match="missing required columns"):
        load_csv(io.StringIO(bad_csv))


def test_invalid_source_type_raises():
    with pytest.raises(ValueError):
        load_csv(12345)


def test_invalid_dates_dropped():
    csv = VALID_CSV + "baddate,21,30,27,80,5,1,5,90,4,E,96001\n"
    df = load_csv(io.StringIO(csv))
    assert len(df) == 4  # bad row dropped


def test_out_of_range_values_become_nan():
    csv = VALID_CSV.replace("27.1", "999")  # Tavg = 999 is out of range
    df = load_csv(io.StringIO(csv))
    assert df["Tavg"].isna().any()


def test_numeric_coercion_non_numeric_becomes_nan():
    csv = VALID_CSV.replace("9,0.5", "abc,0.5")
    df = load_csv(io.StringIO(csv))
    assert df["RR"].isna().any()


def test_station_id_sanitised():
    csv = VALID_CSV.replace("96001", "96001; DROP TABLE")
    df = load_csv(io.StringIO(csv))
    # Semicolons and spaces stripped
    assert all(s.replace("-", "").replace("_", "").isalnum() for s in df["station_id"])


def test_sorted_by_date(clean_df):
    assert clean_df["date"].is_monotonic_increasing


# ---------------------------------------------------------------------------
# engineer_features
# ---------------------------------------------------------------------------


def test_cyclical_month_features(featured_df):
    assert "month_sin" in featured_df.columns
    assert "month_cos" in featured_df.columns
    # sin² + cos² should be ≈ 1
    total = featured_df["month_sin"] ** 2 + featured_df["month_cos"] ** 2
    np.testing.assert_allclose(total.values, 1.0, atol=1e-9)


def test_is_rainy_binary(featured_df):
    assert set(featured_df["is_rainy"].unique()).issubset({0, 1})


def test_roll7_column_created(featured_df):
    assert "RR_roll7" in featured_df.columns


# ---------------------------------------------------------------------------
# filter_data
# ---------------------------------------------------------------------------


def test_filter_by_station(featured_df):
    result = filter_data(featured_df, station_ids=["96001"])
    assert all(result["station_id"] == "96001")


def test_filter_invalid_station_returns_empty(featured_df):
    result = filter_data(featured_df, station_ids=["INVALID; DROP"])
    assert result.empty


def test_filter_by_date_range(featured_df):
    result = filter_data(featured_df, date_start="2010-01-01", date_end="2010-01-02")
    assert all(result["date"] <= pd.Timestamp("2010-01-02"))


def test_filter_rain_only(featured_df):
    result = filter_data(featured_df, rain_only=True)
    assert all(result["RR"] > 0.5)


def test_filter_no_args_returns_all(featured_df):
    result = filter_data(featured_df)
    assert len(result) == len(featured_df)