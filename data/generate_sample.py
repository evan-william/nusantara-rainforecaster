"""
Generate a synthetic sample dataset matching the BMKG column schema.
Run once: python data/generate_sample.py 

(DO NOT ACTUALLY NEED THIS, ALREADY HAVE A REAL DATASET FROM KAGGLE)
"""

import random
from pathlib import Path

import numpy as np
import pandas as pd

OUTPUT_PATH = Path(__file__).parent / "sample_weather.csv"

STATIONS = {
    "96001": ("Manado", "N"),
    "96749": ("Surabaya", "SE"),
    "97180": ("Jakarta", "W"),
    "97372": ("Makassar", "SE"),
    "97502": ("Denpasar", "SE"),
}

np.random.seed(42)
random.seed(42)


def _rain_prob(month: int) -> float:
    """Simple sinusoidal wet/dry season model for equatorial Indonesia."""
    return 0.55 + 0.35 * np.sin(2 * np.pi * (month - 1) / 12)


def generate(start="2010-01-01", end="2023-12-31") -> pd.DataFrame:
    dates = pd.date_range(start, end, freq="D")
    rows = []

    for station_id, (_, wind_dir) in STATIONS.items():
        for d in dates:
            month = d.month
            p_rain = _rain_prob(month)
            rained = np.random.rand() < p_rain
            rr = np.random.exponential(15) if rained else 0.0

            tavg = 26 + 2 * np.sin(2 * np.pi * (month - 4) / 12) + np.random.normal(0, 0.8)
            tn = tavg - np.random.uniform(3, 6)
            tx = tavg + np.random.uniform(2, 5)
            rh = 80 + 10 * (rr / 50) + np.random.normal(0, 3)
            rh = np.clip(rh, 50, 100)
            ss = max(0, 12 - rr / 5 + np.random.normal(0, 1))
            ff_avg = np.random.uniform(2, 8)
            ff_x = ff_avg + np.random.uniform(1, 5)
            ddd_x = np.random.choice([90, 180, 225, 270, 315])

            rows.append(
                {
                    "date": d.strftime("%-d/%-m/%Y"),
                    "Tn": round(tn, 1),
                    "Tx": round(tx, 1),
                    "Tavg": round(tavg, 1),
                    "RH_avg": round(rh, 0),
                    "RR": round(rr, 1),
                    "ss": round(ss, 1),
                    "ff_x": round(ff_x, 1),
                    "ddd_x": ddd_x,
                    "ff_avg": round(ff_avg, 1),
                    "ddd_car": wind_dir,
                    "station_id": station_id,
                }
            )

    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate()
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved {len(df)} rows to {OUTPUT_PATH}")