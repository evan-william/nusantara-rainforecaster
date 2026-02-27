"""
Data loading and preprocessing.
Handles the real BMKG format: DD-MM-YYYY dates, sparse wind columns, null RR.
"""

import io
import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {"date", "Tn", "Tx", "Tavg", "RH_avg", "RR", "station_id"}
NUMERIC_COLUMNS = ["Tn", "Tx", "Tavg", "RH_avg", "RR", "ss", "ff_x", "ddd_x", "ff_avg"]

VALID_RANGES = {
    "Tn":     (-5,  45),
    "Tx":     (-5,  55),
    "Tavg":   (-5,  50),
    "RH_avg": (0,   100),
    "RR":     (0,   900),
    "ss":     (0,   24),
    "ff_x":   (0,   80),
    "ff_avg": (0,   60),
    "ddd_x":  (0,   360),
}

MAX_UPLOAD_BYTES = 200 * 1024 * 1024


def load_csv(source) -> pd.DataFrame:
    """Load from file path, Path, or file-like. Raises ValueError on bad structure."""
    try:
        if isinstance(source, (str, Path)):
            raw = pd.read_csv(source, low_memory=False)
        elif hasattr(source, "read"):
            content = source.read()
            if isinstance(content, bytes):
                content = content.decode("utf-8", errors="replace")
            raw = pd.read_csv(io.StringIO(content), low_memory=False)
        else:
            raise ValueError("source must be a file path or file-like object")
    except Exception as exc:
        raise ValueError(f"Cannot read CSV: {exc}") from exc

    return _clean(raw)


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.str.strip()

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Try multiple date formats — BMKG uses DD-MM-YYYY
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
        parsed = pd.to_datetime(df["date"], format=fmt, errors="coerce")
        if parsed.notna().sum() > len(df) * 0.8:
            df["date"] = parsed
            break
    else:
        df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")

    dropped = df["date"].isna().sum()
    if dropped:
        logger.warning("Dropped %d rows with unparseable dates", dropped)
    df = df.dropna(subset=["date"])

    # Coerce numerics
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Clamp out-of-range values to NaN
    for col, (lo, hi) in VALID_RANGES.items():
        if col in df.columns:
            mask = (df[col] < lo) | (df[col] > hi)
            if mask.any():
                logger.warning("Clamped %d out-of-range in '%s'", mask.sum(), col)
            df.loc[mask, col] = np.nan

    # Sanitise station_id
    df["station_id"] = (
        df["station_id"].astype(str).str.strip()
        .str.replace(r"[^\w\-]", "", regex=True)
    )

    if "ddd_car" in df.columns:
        df["ddd_car"] = df["ddd_car"].astype(str).str.strip().str.upper()

    return df.sort_values("date").reset_index(drop=True)


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["year"]       = df["date"].dt.year
    df["month"]      = df["date"].dt.month
    df["day_of_year"]= df["date"].dt.dayofyear

    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    df["doy_sin"]   = np.sin(2 * np.pi * df["day_of_year"] / 365)
    df["doy_cos"]   = np.cos(2 * np.pi * df["day_of_year"] / 365)

    for col in ["RR", "Tavg", "RH_avg"]:
        if col in df.columns:
            df[f"{col}_roll7"] = (
                df.groupby("station_id")[col]
                .transform(lambda s: s.shift(1).rolling(7, min_periods=1).mean())
            )

    df["is_rainy"] = (df["RR"] > 0.5).astype(int)
    return df


def filter_data(
    df: pd.DataFrame,
    station_ids: Optional[list] = None,
    date_start=None,
    date_end=None,
    rain_only: bool = False,
) -> pd.DataFrame:
    out = df.copy()
    if station_ids:
        valid = set(df["station_id"].unique())
        safe  = [s for s in station_ids if s in valid]
        out   = out[out["station_id"].isin(safe)]
    if date_start:
        out = out[out["date"] >= pd.Timestamp(date_start)]
    if date_end:
        out = out[out["date"] <= pd.Timestamp(date_end)]
    if rain_only:
        out = out[out["RR"] > 0.5]
    return out.reset_index(drop=True)


def get_stations(df: pd.DataFrame) -> list[str]:
    return sorted(df["station_id"].unique().tolist())