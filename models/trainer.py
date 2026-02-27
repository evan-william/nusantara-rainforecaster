"""
ML pipeline with joblib persistence for fast startup.
Pre-trains on data/weather_data.csv and caches model to models/cache/.
"""

import hashlib
import logging
import os
from pathlib import Path
from typing import Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, mean_absolute_error, r2_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

MODEL_DIR  = Path(__file__).parent / "cache"
MODEL_DIR.mkdir(exist_ok=True)

CLF_PATH   = MODEL_DIR / "rain_classifier.joblib"
REG_PATH   = MODEL_DIR / "rain_regressor.joblib"
DATA_PATH  = Path(__file__).parent.parent / "data" / "weather_data.csv"

FEATURE_COLS = [
    "Tn", "Tx", "Tavg", "RH_avg", "ss", "ff_x", "ff_avg",
    "month_sin", "month_cos", "doy_sin", "doy_cos",
    "RR_roll7", "Tavg_roll7", "RH_avg_roll7",
]


def _clf_pipe() -> Pipeline:
    return Pipeline([
        ("imp",   SimpleImputer(strategy="median")),
        ("scl",   StandardScaler()),
        ("model", GradientBoostingClassifier(
            n_estimators=200, max_depth=4,
            learning_rate=0.05, subsample=0.8, random_state=42,
        )),
    ])


def _reg_pipe() -> Pipeline:
    return Pipeline([
        ("imp",   SimpleImputer(strategy="median")),
        ("scl",   StandardScaler()),
        ("model", RandomForestRegressor(
            n_estimators=200, max_depth=8,
            min_samples_leaf=5, random_state=42, n_jobs=-1,
        )),
    ])


def train(df: pd.DataFrame) -> dict:
    avail = [c for c in FEATURE_COLS if c in df.columns]
    if len(avail) < 6:
        raise ValueError(f"Not enough feature columns. Found: {avail}")

    X   = df[avail]
    y_c = (df["RR"] > 0.5).astype(int)

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y_c, test_size=0.2, random_state=42, stratify=y_c
    )

    clf = _clf_pipe()
    clf.fit(X_tr, y_tr)
    acc = accuracy_score(y_te, clf.predict(X_te))
    auc = roc_auc_score(y_te, clf.predict_proba(X_te)[:, 1])

    metrics = {"accuracy": float(acc), "roc_auc": float(auc), "features": avail, "rows": len(df)}

    rain_mask = df["RR"] > 0.5
    if rain_mask.sum() > 50:
        X_r = X[rain_mask]
        y_r = df.loc[rain_mask, "RR"]
        X_rtr, X_rte, y_rtr, y_rte = train_test_split(X_r, y_r, test_size=0.2, random_state=42)
        reg = _reg_pipe()
        reg.fit(X_rtr, y_rtr)
        metrics["mae"] = float(mean_absolute_error(y_rte, reg.predict(X_rte)))
        metrics["r2"]  = float(r2_score(y_rte, reg.predict(X_rte)))
        joblib.dump(reg, REG_PATH, compress=3)
    else:
        metrics["mae"] = None
        metrics["r2"]  = None

    joblib.dump(clf, CLF_PATH, compress=3)
    # Restrict permissions where possible (won't error on read-only FS)
    try:
        CLF_PATH.chmod(0o600)
        REG_PATH.chmod(0o600)
    except Exception:
        pass

    logger.info("Training complete: acc=%.3f auc=%.3f", acc, auc)
    return metrics


def _load(path: Path):
    if not path.exists():
        return None
    return joblib.load(path)


def predict(row: pd.DataFrame) -> Tuple[float, Optional[float]]:
    clf = _load(CLF_PATH)
    if clf is None:
        raise RuntimeError("Model not trained yet.")

    avail = [c for c in FEATURE_COLS if c in row.columns]
    X     = row[avail]
    prob  = float(clf.predict_proba(X)[:, 1][0])

    mm = None
    if prob > 0.5:
        reg = _load(REG_PATH)
        if reg is not None:
            mm = max(0.0, float(reg.predict(X)[0]))

    return prob, mm


def auto_train_if_needed() -> Optional[dict]:
    """Called at app startup. Trains from data/weather_data.csv if no model cached."""
    if CLF_PATH.exists():
        return None  # already cached
    if not DATA_PATH.exists():
        logger.warning("weather_data.csv not found at %s", DATA_PATH)
        return None
    try:
        from data.loader import load_csv, engineer_features
        df = engineer_features(load_csv(DATA_PATH))
        return train(df)
    except Exception as exc:
        logger.error("Auto-train failed: %s", exc)
        return None


def is_trained() -> bool:
    return CLF_PATH.exists()


def checksum() -> Optional[str]:
    if not CLF_PATH.exists():
        return None
    h = hashlib.md5()
    with open(CLF_PATH, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def get_monthly_stats(df: pd.DataFrame) -> dict:
    """
    Pre-compute per-month median weather stats used by Smart Mode.
    Returns dict keyed by month (1-12).
    """
    stats = {}
    for month in range(1, 13):
        m = df[df["date"].dt.month == month]
        if len(m) < 5:
            m = df
        def med(col):
            return float(m[col].median()) if col in m.columns and m[col].notna().any() else 0.0
        stats[month] = {
            "Tn": med("Tn"), "Tx": med("Tx"), "Tavg": med("Tavg"),
            "RH_avg": med("RH_avg"), "ss": med("ss"),
            "ff_x": med("ff_x"), "ff_avg": med("ff_avg"),
            "RR_roll7": med("RR_roll7") if "RR_roll7" in m.columns else med("RR"),
            "Tavg_roll7": med("Tavg_roll7") if "Tavg_roll7" in m.columns else med("Tavg"),
            "RH_avg_roll7": med("RH_avg_roll7") if "RH_avg_roll7" in m.columns else med("RH_avg"),
            "rain_prob": float((m["RR"] > 0.5).mean()) if "RR" in m.columns else 0.5,
            "avg_rain_mm": float(m.loc[m["RR"] > 0.5, "RR"].mean()) if "RR" in m.columns else 5.0,
        }
    return stats


def estimate_rain_hours(prob: float, mm: Optional[float], month: int) -> dict:
    """
    Estimate likely rain start/end times based on Indonesia tropical patterns.
    Afternoon convective rain is most common (13:00-17:00).
    Morning rain more common Nov-Mar (wet season).
    """
    if prob < 0.3:
        return {"start": None, "end": None, "peak": None, "description": "Tidak ada hujan"}

    # Wet season Nov-Apr: more morning rain; Dry season May-Oct: afternoon convective
    wet_season = month in [11, 12, 1, 2, 3, 4]

    if mm and mm > 40:
        # Heavy rain — longer duration, likely starts earlier
        start_h = 12 if wet_season else 13
        end_h   = 19 if wet_season else 18
        peak_h  = 14
    elif mm and mm > 15:
        start_h = 13
        end_h   = 17
        peak_h  = 15
    else:
        # Light — short afternoon shower
        start_h = 14
        end_h   = 16
        peak_h  = 15

    if wet_season and prob > 0.7:
        start_h = max(9, start_h - 2)  # wet season: can start earlier

    return {
        "start": f"{start_h:02d}:00",
        "end":   f"{end_h:02d}:00",
        "peak":  f"{peak_h:02d}:00",
        "description": f"Hujan diperkirakan ~{start_h:02d}:00–{end_h:02d}:00 WIB",
    }