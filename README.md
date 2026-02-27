<div align="center">

<img src="assets/rainfore-logo.jpg" alt="Nusantara RainForecaster" width="600"/>

# Nusantara RainForecaster

**AI-powered Indonesia rainfall prediction — built with Streamlit & scikit-learn**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.6.0-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

[Features](#features) · [Live Demo](#-try-it-live) · [Quick Start](#quick-start) · [Architecture](#architecture) · [Contributing](#contributing)

</div>

---

## 🌧️ Try It Live

> **[nusantara-rainforecaster.streamlit.app](https://nusantara-rainforecaster.streamlit.app/)**
> No install needed, runs fully in your browser.

---

## What is this?

Nusantara RainForecaster is a gamified weather web app that analyzes historical Indonesian weather data (BMKG format) and predicts rainfall probability using a **Gradient Boosting classifier** and **Random Forest regressor**. It features three modes:

- **Smart Mode** — pick any of the next 7 days and get an instant AI prediction using historical median values for that month, automatically inferred from your data.
- **Manual Mode** — enter today's exact conditions (temperature, humidity, sunshine, wind) for a fully custom prediction.
- **Dashboard** — explore historical trends across stations and date ranges.

Rain timing estimates use **real BMKG climatology logic** based on sunshine duration (`ss`), humidity (`RH_avg`), total rainfall (`RR`), and seasonal patterns — not random guesses.

---

## Features

### Smart Mode (7-Day Forecast Strip)
- Visual 7-day tile strip showing rain probability and estimated mm for each day
- Click any day tile or pick a custom date — prediction updates instantly
- Features inferred from historical monthly medians with realistic daily variation
- Rain timing derived from `ss` + `RH_avg` + BMKG seasonal patterns

### Manual Mode
- Enter all conditions manually: `Tavg`, `Tn`, `Tx`, `RH_avg`, `ss`, wind speeds, and 7-day rolling averages
- Same ML model, full user control over inputs

### Dashboard
- KPI metrics: total records, rainy days, avg rainfall, avg temperature
- Charts: daily rainfall bar, temperature band (min/avg/max), humidity vs rainfall scatter, monthly heatmap, rain probability by month — all interactive via Plotly

### AI Model
- **Classifier**: GradientBoostingClassifier — predicts probability of rain (`RR > 0.5 mm`)
- **Regressor**: RandomForestRegressor — estimates rainfall volume (mm) on rainy days
- Auto-trains on startup from `data/weather_data.csv` with joblib caching
- Model identified by MD5 checksum; retrain anytime from the Data tab

### Rain Timing Estimation (BMKG-based)
| Condition | Rain Type |
|---|---|
| `ss = 0` jam | Sepanjang hari, mulai 06:00 |
| `ss < 2` jam atau `RH ≥ 90%` | Pagi orografik, ~07:00–09:00 |
| `ss 2–4` jam + musim hujan | Siang, ~11:00–14:00 |
| `RH ≥ 90%` + musim hujan | Siang-sore, ~12:00–15:00 |
| `ss 4–10` jam (default) | **Konvektif sore (paling umum)**, ~13:00–15:00 |

Durasi dihitung dari `RR` (mm) ÷ intensitas BMKG per kategori (ringan/sedang/lebat/sangat lebat/ekstrem).

### Security
- Uploaded files validated for size (50 MB cap) and schema before parsing
- Station IDs sanitised against a whitelist
- Numeric columns range-clamped to physical bounds; corrupt values → NaN
- Model files written with `chmod 0600`
- XSRF protection enabled in `.streamlit/config.toml`
- No user data persisted between sessions

---

## Quick Start

### 1. Clone & install

```bash
git clone https://github.com/your-username/nusantara-rainforecaster.git
cd nusantara-rainforecaster

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Add your data

Place your BMKG-format CSV at `data/weather_data.csv`. The app will auto-train the model on first launch.

Or use the helper to generate synthetic sample data:

```bash
python data/generate_sample.py
```

### 3. Run

```bash
streamlit run app.py
```

Or use the helper script:

```bash
chmod +x run.sh
./run.sh all    # install → generate data → tests → launch app
```

The model trains automatically on first run and caches to `models/cache/`. Subsequent launches load the cache instantly.

---

## Using Your Own Data

CSV must include these columns at minimum:

| Column | Description |
|--------|-------------|
| `date` | `DD-MM-YYYY` or `YYYY-MM-DD` |
| `Tn` | Min temperature (°C) |
| `Tx` | Max temperature (°C) |
| `Tavg` | Avg temperature (°C) |
| `RH_avg` | Avg humidity (%) |
| `RR` | Rainfall (mm) |
| `station_id` | Station identifier |

Optional but recommended (improve model accuracy and rain timing estimates):

| Column | Description |
|--------|-------------|
| `ss` | Sunshine duration (hours/day) — used for rain timing |
| `ff_x` | Max wind speed (m/s) |
| `ff_avg` | Avg wind speed (m/s) |
| `ddd_x` | Wind direction at max speed (°) |

---

## Retraining the Model

After updating `data/weather_data.csv`, retrain from the **Data tab → Retrain Model**, or via CLI:

```bash
python -c "
from data.loader import load_csv, engineer_features
from models.trainer import train
df = engineer_features(load_csv('data/weather_data.csv'))
m = train(df)
print('Done:', m)
"
```

Then commit the updated cache:

```bash
git add models/cache/rain_classifier.joblib models/cache/rain_regressor.joblib
git commit -m "retrain model"
git push
```

> **Note:** Pin your scikit-learn version in `requirements.txt` (e.g. `scikit-learn==1.6.0`) to ensure the cached `.joblib` is compatible across environments.

---

## Running Tests

```bash
pytest                                          # all tests
pytest tests/test_loader.py                    # single file
pytest --cov=. --cov-report=term-missing       # with coverage
```

---

## Architecture

```
nusantara-rainforecaster/
├── app.py                      # Entry point, page routing, Smart/Manual mode
├── run.sh                      # Dev helper (setup / test / launch)
├── requirements.txt
├── pytest.ini
│
├── .streamlit/
│   └── config.toml             # Theme, XSRF, upload limits
│
├── data/
│   ├── loader.py               # CSV parsing, validation, feature engineering
│   ├── weather_data.csv        # Your BMKG data goes here
│   └── generate_sample.py      # Synthetic dataset generator
│
├── models/
│   ├── trainer.py              # Pipeline builders, train(), predict(),
│   │                           # estimate_rain_hours() (BMKG logic)
│   └── cache/
│       ├── rain_classifier.joblib
│       └── rain_regressor.joblib
│
├── utils/
│   ├── charts.py               # Plotly figure builders
│   └── style.py                # CSS injection, UI components
│
├── tests/
│   ├── test_loader.py
│   ├── test_trainer.py
│   └── test_charts.py
│
└── assets/
    └── rainfore-logo.jpg
```

---

## Tech Stack

| Layer | Library |
|-------|---------|
| Web UI | Streamlit 1.32+ |
| ML — Classification | GradientBoostingClassifier (scikit-learn 1.6.0) |
| ML — Regression | RandomForestRegressor (scikit-learn 1.6.0) |
| Data Processing | Pandas, NumPy |
| Visualisation | Plotly |
| Model Persistence | joblib |
| Testing | pytest, pytest-cov |

---

## Roadmap

- [ ] BMKG API integration for live feature pulling
- [ ] Multi-step ahead forecasting (3-day outlook)
- [ ] API endpoint (FastAPI) for headless predictions
- [ ] Model versioning and comparison UI
- [ ] Dockerised deployment

---

## Contributing

1. Fork the repository.
2. Create a branch: `git checkout -b feature/your-feature`.
3. Make changes and add tests.
4. Run `pytest` — all tests must pass.
5. Open a pull request with a clear description.

---

## License

MIT — see [LICENSE](LICENSE).