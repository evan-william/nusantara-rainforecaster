"""Tests for models/trainer.py"""

import io
import textwrap

import numpy as np
import pytest

from data.loader import engineer_features, load_csv
from models.trainer import (
    CLASSIFIER_PATH,
    REGRESSOR_PATH,
    _build_classifier,
    _build_regressor,
    models_exist,
    predict,
    train,
)


# ---------------------------------------------------------------------------
# Helper — generate a small synthetic dataframe for fast tests
# ---------------------------------------------------------------------------


def _make_df(n: int = 300):
    """Minimal synthetic dataset compatible with engineer_features output."""
    np.random.seed(0)
    dates = list(range(n))
    import pandas as pd

    df = pd.DataFrame(
        {
            "date": pd.date_range("2015-01-01", periods=n, freq="D"),
            "Tn": np.random.uniform(18, 24, n),
            "Tx": np.random.uniform(28, 35, n),
            "Tavg": np.random.uniform(24, 30, n),
            "RH_avg": np.random.uniform(70, 98, n),
            "RR": np.where(np.random.rand(n) > 0.4, np.random.exponential(10, n), 0),
            "ss": np.random.uniform(0, 10, n),
            "ff_x": np.random.uniform(2, 10, n),
            "ff_avg": np.random.uniform(1, 7, n),
            "station_id": "TEST01",
        }
    )
    return engineer_features(df)


# ---------------------------------------------------------------------------
# Pipeline builders
# ---------------------------------------------------------------------------


def test_build_classifier_has_steps():
    pipe = _build_classifier()
    assert hasattr(pipe, "steps")
    step_names = [s[0] for s in pipe.steps]
    assert "imputer" in step_names
    assert "model" in step_names


def test_build_regressor_has_steps():
    pipe = _build_regressor()
    step_names = [s[0] for s in pipe.steps]
    assert "scaler" in step_names


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------


def test_train_returns_metrics(tmp_path, monkeypatch):
    # Redirect model save path to tmp_path
    monkeypatch.setattr("models.trainer.CLASSIFIER_PATH", tmp_path / "clf.pkl")
    monkeypatch.setattr("models.trainer.REGRESSOR_PATH", tmp_path / "reg.pkl")

    df = _make_df()
    metrics = train(df)

    assert "classifier_accuracy" in metrics
    assert "classifier_roc_auc" in metrics
    assert 0.0 <= metrics["classifier_accuracy"] <= 1.0
    assert 0.0 <= metrics["classifier_roc_auc"] <= 1.0


def test_train_saves_model_file(tmp_path, monkeypatch):
    clf_path = tmp_path / "clf.pkl"
    monkeypatch.setattr("models.trainer.CLASSIFIER_PATH", clf_path)
    monkeypatch.setattr("models.trainer.REGRESSOR_PATH", tmp_path / "reg.pkl")

    train(_make_df())
    assert clf_path.exists()


def test_train_raises_with_insufficient_features():
    import pandas as pd

    bad_df = pd.DataFrame({"date": ["2020-01-01"], "station_id": ["A"]})
    with pytest.raises(ValueError, match="Not enough feature columns"):
        train(bad_df)


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------


def test_predict_after_train(tmp_path, monkeypatch):
    clf_path = tmp_path / "clf.pkl"
    reg_path = tmp_path / "reg.pkl"
    monkeypatch.setattr("models.trainer.CLASSIFIER_PATH", clf_path)
    monkeypatch.setattr("models.trainer.REGRESSOR_PATH", reg_path)

    train(_make_df())

    import pandas as pd

    row = pd.DataFrame(
        [
            {
                "Tn": 21.0,
                "Tx": 31.0,
                "Tavg": 27.0,
                "RH_avg": 85.0,
                "ss": 4.0,
                "ff_x": 6.0,
                "ff_avg": 4.0,
                "month_sin": 0.5,
                "month_cos": 0.87,
                "doy_sin": 0.5,
                "doy_cos": 0.87,
                "RR_roll7": 8.0,
                "Tavg_roll7": 27.0,
                "RH_avg_roll7": 85.0,
            }
        ]
    )

    rain_prob, est_mm = predict(row)
    assert 0.0 <= rain_prob <= 1.0
    if est_mm is not None:
        assert est_mm >= 0.0


def test_predict_raises_when_no_model(tmp_path, monkeypatch):
    monkeypatch.setattr("models.trainer.CLASSIFIER_PATH", tmp_path / "missing.pkl")

    import pandas as pd

    row = pd.DataFrame([{"Tn": 21.0}])
    with pytest.raises(RuntimeError, match="not trained"):
        predict(row)