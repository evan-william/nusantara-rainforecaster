"""
ML pipeline: Gradient Boosting classifier (rain/no-rain) +
Random Forest regressor (how much mm).
"""

import hashlib
import logging
import pickle
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, mean_absolute_error, r2_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).parent
MODEL_DIR.mkdir(exist_ok=True)

CLF_PATH = MODEL_DIR / "rain_classifier.pkl"
REG_PATH = MODEL_DIR / "rain_regressor.pkl"

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

    X    = df[avail]
    y_c  = (df["RR"] > 0.5).astype(int)

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y_c, test_size=0.2, random_state=42, stratify=y_c
    )

    clf = _clf_pipe()
    clf.fit(X_tr, y_tr)
    acc = accuracy_score(y_te, clf.predict(X_te))
    auc = roc_auc_score(y_te, clf.predict_proba(X_te)[:, 1])

    metrics = {
        "accuracy": float(acc),
        "roc_auc":  float(auc),
        "features": avail,
        "rows":     len(df),
    }

    # Regressor on rainy rows only
    rain_mask = df["RR"] > 0.5
    if rain_mask.sum() > 50:
        X_r = X[rain_mask]
        y_r = df.loc[rain_mask, "RR"]
        X_rtr, X_rte, y_rtr, y_rte = train_test_split(X_r, y_r, test_size=0.2, random_state=42)
        reg = _reg_pipe()
        reg.fit(X_rtr, y_rtr)
        metrics["mae"] = float(mean_absolute_error(y_rte, reg.predict(X_rte)))
        metrics["r2"]  = float(r2_score(y_rte, reg.predict(X_rte)))
        _save(reg, REG_PATH)
    else:
        metrics["mae"] = None
        metrics["r2"]  = None

    _save(clf, CLF_PATH)
    return metrics


def _save(obj, path: Path) -> None:
    with open(path, "wb") as f:
        pickle.dump(obj, f)
    path.chmod(0o600)


def _load(path: Path):
    if not path.exists():
        return None
    with open(path, "rb") as f:
        return pickle.load(f)


def predict(row: pd.DataFrame) -> Tuple[float, Optional[float]]:
    clf = _load(CLF_PATH)
    if clf is None:
        raise RuntimeError("Model not trained yet.")

    avail = [c for c in FEATURE_COLS if c in row.columns]
    X = row[avail]

    prob = float(clf.predict_proba(X)[:, 1][0])
    mm   = None
    if prob > 0.5:
        reg = _load(REG_PATH)
        if reg is not None:
            mm = max(0.0, float(reg.predict(X)[0]))

    return prob, mm


def is_trained() -> bool:
    return CLF_PATH.exists()


def checksum() -> Optional[str]:
    if not CLF_PATH.exists():
        return None
    h = hashlib.md5()
    with open(CLF_PATH, "rb") as f:
        h.update(f.read())
    return h.hexdigest()