"""
Data loading, validation, and preprocessing for weather CSV files.
"""

import io
import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Expected columns and their dtypes after parsing
REQUIRED_COLUMNS = {"date", "Tn", "Tx", "Tavg", "RH_avg", "RR", "station_id"}
NUMERIC_COLUMNS = ["Tn", "Tx", "Tavg", "RH_avg", "RR", "ss", "ff_x", "ddd_x", "ff_avg"]

# Hard limits to catch obviously corrupt data
VALID_RANGES = {
    "Tn": (-10, 50),
    "Tx": (-10, 60),
    "Tavg": (-10, 55),
    "RH_avg": (0, 100),
    "RR": (0, 1000),
    "ss": (0, 24),
    "ff_x": (0, 100),
    "ff_avg": (0, 100),
    "ddd_x": (0, 360),
}

SAMPLE_DATA_PATH = Path(__file__).parent.parent / "data" / "sample_weather.csv"


def load_csv(source) -> pd.DataFrame:
    """Load weather CSV from a file path, Path object, or file-like object.

    Raises ValueError if the data is structurally invalid.
    """
    try:
        if isinstance(source, (str, Path)):
            raw = pd.read_csv(source, low_memory=False)
        elif hasattr(source, "read"):
            content = source.read()
            # Decode bytes safely
            if isinstance(content, bytes):
                content = content.decode("utf-8", errors="replace")
            raw = pd.read_csv(io.StringIO(content), low_memory=False)
        else:
            raise ValueError("source must be a path or file-like object")
    except Exception as exc:
        raise ValueError(f"Failed to read CSV: {exc}") from exc

    return _validate_and_clean(raw)


def load_sample_data() -> pd.DataFrame:
    """Load the bundled sample dataset."""
    if not SAMPLE_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Sample data not found at {SAMPLE_DATA_PATH}. "
            "Run `python data/generate_sample.py` first."
        )
    return load_csv(SAMPLE_DATA_PATH)


def _validate_and_clean(df: pd.DataFrame) -> pd.DataFrame:
    """Validate structure, parse types, and clamp outliers."""
    df.columns = df.columns.str.strip()

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Dataset missing required columns: {missing}")

    # Parse dates — accepts both d/m/Y and Y-m-d
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    invalid_dates = df["date"].isna().sum()
    if invalid_dates > 0:
        logger.warning("Dropped %d rows with unparseable dates.", invalid_dates)
    df = df.dropna(subset=["date"])

    # Coerce numeric columns; non-numeric become NaN (don't crash)
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Replace values outside physical bounds with NaN
    for col, (lo, hi) in VALID_RANGES.items():
        if col in df.columns:
            mask = (df[col] < lo) | (df[col] > hi)
            if mask.any():
                logger.warning(
                    "Clamped %d out-of-range values in column '%s'.", mask.sum(), col
                )
            df.loc[mask, col] = np.nan

    # Sanitise station_id — keep only alphanumeric + underscore + dash
    df["station_id"] = (
        df["station_id"]
        .astype(str)
        .str.strip()
        .str.replace(r"[^\w\-]", "", regex=True)
    )

    # Normalize wind direction text if present
    if "ddd_car" in df.columns:
        df["ddd_car"] = df["ddd_car"].astype(str).str.strip().str.upper()

    df = df.sort_values("date").reset_index(drop=True)
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add time-based and lag features used by the ML model."""
    df = df.copy()
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["day_of_year"] = df["date"].dt.dayofyear
    df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)

    # Cyclical encoding so the model sees continuity across year boundary
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    df["doy_sin"] = np.sin(2 * np.pi * df["day_of_year"] / 365)
    df["doy_cos"] = np.cos(2 * np.pi * df["day_of_year"] / 365)

    # 7-day rolling features per station
    for col in ["RR", "Tavg", "RH_avg"]:
        if col in df.columns:
            df[f"{col}_roll7"] = (
                df.groupby("station_id")[col]
                .transform(lambda s: s.shift(1).rolling(7, min_periods=1).mean())
            )

    # Binary rain indicator
    df["is_rainy"] = (df["RR"] > 0.5).astype(int)

    return df


def get_station_list(df: pd.DataFrame) -> list[str]:
    return sorted(df["station_id"].unique().tolist())


def filter_data(
    df: pd.DataFrame,
    station_ids: Optional[list] = None,
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    rain_only: bool = False,
) -> pd.DataFrame:
    """Apply sidebar filters to the dataframe safely."""
    filtered = df.copy()

    if station_ids:
        # Validate station IDs against actual data to prevent injection-style abuse
        valid = set(df["station_id"].unique())
        safe_ids = [s for s in station_ids if s in valid]
        filtered = filtered[filtered["station_id"].isin(safe_ids)]

    if date_start:
        filtered = filtered[filtered["date"] >= pd.to_datetime(date_start)]

    if date_end:
        filtered = filtered[filtered["date"] <= pd.to_datetime(date_end)]

    if rain_only:
        filtered = filtered[filtered["RR"] > 0.5]

    return filtered.reset_index(drop=True)