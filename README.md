<div align="center">

<img src="assets/logo.png" alt="Nusantara RainForecaster" width="600"/>

# Nusantara RainForecaster

**AI-powered Indonesia weather prediction built with Streamlit and scikit-learn**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4+-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)](https://scikit-learn.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

[Features](#features) · [Quick Start](#quick-start) · [Architecture](#architecture) · [Contributing](#contributing)

</div>

---

## What is this?

Nusantara RainForecaster is a web application that analyzes historical Indonesian weather data (BMKG format) and predicts rainfall using a Gradient Boosting classifier and Random Forest regressor. You can explore historical trends, filter by station or date, and enter today's conditions to get a probability-based forecast for the next day.

---

## Features

**Dashboard** — KPI metrics, rainfall time series, temperature bands, humidity scatter, wind rose, and a year × month heatmap. All charts are interactive (Plotly).

**Data Explorer** — Upload your own BMKG-format CSV or work with the bundled sample dataset. Filter by station, date range, and rain condition. Download filtered results.

**AI Forecaster** — Train two models (classifier + regressor) directly from the UI. Enter current conditions via a form, then receive a rain probability, estimated millimetres, and severity advisory. Each trained model is identified by its MD5 checksum.

**Security defaults:**
- Uploaded files are validated for size (50 MB cap) and structural schema before parsing.
- Station IDs are sanitised against a whitelist before being used as filters.
- Numeric columns are range-clamped to physical bounds; corrupt values become NaN.
- Trained model files are written with mode `0600`.
- XSRF protection and CORS disabled are set in `.streamlit/config.toml`.
- No user data is persisted between sessions.

---

## Quick Start

### 1. Clone & install

```bash
git clone https://github.com/your-username/nusantara-rainforecaster.git
cd nusantara-rainforecaster

python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Generate sample data

```bash
python data/generate_sample.py
```

### 3. Run the app

```bash
streamlit run app.py
```

Or use the helper script:

```bash
chmod +x run.sh
./run.sh all    # install → generate data → tests → launch app
```

---

## Using Your Own Data

The CSV must contain at minimum these columns:

| Column | Description |
|--------|-------------|
| `date` | `d/m/Y` or `Y-m-d` format |
| `Tn` | Min temperature (°C) |
| `Tx` | Max temperature (°C) |
| `Tavg` | Avg temperature (°C) |
| `RH_avg` | Avg humidity (%) |
| `RR` | Rainfall (mm) |
| `station_id` | Numeric or alphanumeric station identifier |

Optional columns (`ss`, `ff_x`, `ddd_x`, `ff_avg`, `ddd_car`) improve chart richness and model accuracy when present.

---

## Running Tests

```bash
pytest                          # all tests
pytest tests/test_loader.py     # single file
pytest --cov=. --cov-report=term-missing   # with coverage
```

---

## Architecture

```
nusantara-rainforecaster/
├── app.py                      # Entry point, page routing
├── run.sh                      # Dev helper (setup / test / launch)
├── requirements.txt
├── pytest.ini
│
├── .streamlit/
│   └── config.toml             # Theme, XSRF, upload limits
│
├── pages/
│   ├── dashboard.py            # Historical overview page
│   ├── explorer.py             # CSV upload + filter + download
│   └── forecast.py             # Train model + predict page
│
├── data/
│   ├── loader.py               # CSV parsing, validation, feature engineering
│   └── generate_sample.py      # Synthetic dataset generator
│
├── models/
│   └── trainer.py              # Pipeline builders, train(), predict()
│
├── utils/
│   ├── charts.py               # Plotly figure builders
│   └── style.py                # Custom CSS injection
│
├── tests/
│   ├── test_loader.py
│   ├── test_trainer.py
│   └── test_charts.py
│
└── assets/
    └── logo.png
```

---

## Tech Stack

| Layer | Library |
|-------|---------|
| Web UI | Streamlit 1.32+ |
| ML — Classification | GradientBoostingClassifier (scikit-learn) |
| ML — Regression | RandomForestRegressor (scikit-learn) |
| Data Processing | Pandas, NumPy |
| Visualisation | Plotly |
| Testing | pytest, pytest-cov |

---

## Roadmap

- [ ] API endpoint (FastAPI) for headless predictions
- [ ] Multi-step ahead forecasting (3-day outlook)
- [ ] BMKG API integration for live feature pulling
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