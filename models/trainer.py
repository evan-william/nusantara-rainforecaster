"""
Model training, persistence, and prediction logic.

Two models:
  - RainfallClassifier: Binary (rain / no rain)
  - RainfallRegressor:  Rainfall amount in mm (only when rain predicted)
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
from sklearn.metrics import (
    accuracy_score,
    mean_absolute_error,
    r2_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).parent.parent / "models"
MODEL_DIR.mkdir(exist_ok=True)

CLASSIFIER_PATH = MODEL_DIR / "rain_classifier.pkl"
REGRESSOR_PATH = MODEL_DIR / "rain_regressor.pkl"

# Features used for training — derived from engineer_features() in loader.py
FEATURE_COLS = [
    "Tn", "Tx", "Tavg", "RH_avg", "ss", "ff_x", "ff_avg",
    "month_sin", "month_cos", "doy_sin", "doy_cos",
    "RR_roll7", "Tavg_roll7", "RH_avg_roll7",
]


def _build_classifier() -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "model",
                GradientBoostingClassifier(
                    n_estimators=200,
                    max_depth=4,
                    learning_rate=0.05,
                    subsample=0.8,
                    random_state=42,
                ),
            ),
        ]
    )


def _build_regressor() -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=200,
                    max_depth=8,
                    min_samples_leaf=5,
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )


def train(df: pd.DataFrame) -> dict:
    """Train both models on the provided dataframe, persist to disk.

    Returns a dict of evaluation metrics.
    """
    available = [c for c in FEATURE_COLS if c in df.columns]
    if len(available) < 6:
        raise ValueError(
            f"Not enough feature columns. Got {available}, need at least 6."
        )

    X = df[available].copy()
    y_cls = (df["RR"] > 0.5).astype(int)
    y_reg = df.loc[df["RR"] > 0.5, "RR"].copy()

    X_train, X_test, y_cls_train, y_cls_test = train_test_split(
        X, y_cls, test_size=0.2, random_state=42, stratify=y_cls
    )

    # Classification
    clf = _build_classifier()
    clf.fit(X_train, y_cls_train)
    y_pred_cls = clf.predict(X_test)
    y_prob_cls = clf.predict_proba(X_test)[:, 1]

    metrics = {
        "classifier_accuracy": float(accuracy_score(y_cls_test, y_pred_cls)),
        "classifier_roc_auc": float(roc_auc_score(y_cls_test, y_prob_cls)),
        "features_used": available,
        "training_rows": len(df),
    }

    # Regression (rain rows only)
    X_rain = X.loc[df["RR"] > 0.5]
    if len(X_rain) > 50:
        X_r_train, X_r_test, y_r_train, y_r_test = train_test_split(
            X_rain, y_reg, test_size=0.2, random_state=42
        )
        reg = _build_regressor()
        reg.fit(X_r_train, y_r_train)
        y_pred_reg = reg.predict(X_r_test)
        metrics["regressor_mae"] = float(mean_absolute_error(y_r_test, y_pred_reg))
        metrics["regressor_r2"] = float(r2_score(y_r_test, y_pred_reg))
    else:
        reg = None
        metrics["regressor_mae"] = None
        metrics["regressor_r2"] = None

    # Save securely with restricted permissions
    _save_model(clf, CLASSIFIER_PATH)
    if reg is not None:
        _save_model(reg, REGRESSOR_PATH)

    logger.info("Training complete. Metrics: %s", metrics)
    return metrics


def _save_model(model, path: Path) -> None:
    with open(path, "wb") as f:
        pickle.dump(model, f)
    path.chmod(0o600)


def _load_model(path: Path):
    if not path.exists():
        return None
    with open(path, "rb") as f:
        return pickle.load(f)


def predict(
    df_row: pd.DataFrame,
) -> Tuple[float, Optional[float]]:
    """Return (rain_probability, estimated_mm).

    df_row must have the same feature columns used during training.
    """
    clf = _load_model(CLASSIFIER_PATH)
    if clf is None:
        raise RuntimeError("Model not trained yet. Train first via the AI Forecaster page.")

    available = [c for c in FEATURE_COLS if c in df_row.columns]
    X = df_row[available]

    rain_prob = float(clf.predict_proba(X)[:, 1][0])

    estimated_mm = None
    if rain_prob > 0.5:
        reg = _load_model(REGRESSOR_PATH)
        if reg is not None:
            raw = float(reg.predict(X)[0])
            estimated_mm = max(0.0, raw)

    return rain_prob, estimated_mm


def models_exist() -> bool:
    return CLASSIFIER_PATH.exists()


def get_model_checksum() -> Optional[str]:
    """Return MD5 checksum of the classifier file for integrity display."""
    if not CLASSIFIER_PATH.exists():
        return None
    h = hashlib.md5()
    with open(CLASSIFIER_PATH, "rb") as f:
        h.update(f.read())
    return h.hexdigest()