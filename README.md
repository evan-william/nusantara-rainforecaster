<div align="center">

<img src="assets/rainfore-logo.jpg" alt="Nusantara RainForecaster" width="600" />

# Nusantara RainForecaster

An explainable rainfall-estimation prototype for Indonesian weather data, built with Streamlit and scikit-learn.

[Live demo](https://nusantara-rainforecaster.streamlit.app/) · [Quick start](#quick-start) · [Model design](#model-design) · [Data contract](#data-contract)

</div>

## Why this project exists

Nusantara RainForecaster turns BMKG-format historical observations into an interactive ML workflow. It lets users explore station-level weather patterns, compare rainy and dry periods, and test rainfall scenarios without working directly in notebooks.

The product has three workspaces:

- **Forecast** — compare a seven-day historical-pattern scenario or enter weather conditions manually.
- **Dashboard** — filter stations and dates, then inspect rainfall, temperature, humidity, and seasonal patterns.
- **Data** — preview validated records, retrain the models, inspect the active model checksum, and export filtered data.

> Smart Mode is a scenario estimate based on historical monthly conditions and deterministic daily variation. It does not ingest live weather observations and should not be treated as an operational weather forecast or safety alert.

## Product highlights

- Responsive Indonesian-language interface with accessible focus states and reduced-motion support.
- Deterministic seven-day scenarios: the same target date produces the same inferred conditions.
- Manual prediction workflow for temperature, humidity, sunshine, wind, and rolling weather features.
- Interactive Plotly views for daily rainfall, temperature range, monthly rainfall, humidity, and wind direction.
- CSV schema validation, physical-range checks, station-ID sanitisation, and a 50 MB upload limit.
- Cached model artifacts with checksum-based visibility in the UI.
- Compatibility layer for the original multi-page interface and the current single-page product.
- Automated coverage for loading, feature engineering, filtering, model training, inference, and chart generation.

## Model design

The application uses two scikit-learn pipelines:

| Task | Model | Output |
|---|---|---|
| Rain classification | Gradient Boosting classifier | Probability that rainfall exceeds 0.5 mm |
| Rainfall regression | Random Forest regressor | Estimated rainfall volume for likely rainy conditions |

Both pipelines include median imputation and feature scaling. Evaluation uses a chronological 80/20 holdout so later observations are tested against earlier training data. After metrics are calculated, the deployable models are fit again on the complete validated dataset.

Features include temperature, humidity, sunshine duration, wind speed, cyclical month/day encodings, and shifted seven-day rolling weather statistics. Shifted rolling features prevent the target day from leaking into its own historical context.

The rain-window estimate is a deterministic heuristic informed by probability, estimated rainfall, sunshine duration, humidity, and wet/dry-season context. It is presented separately from the learned model output.

## Quick start

```bash
git clone https://github.com/evan-william/nusantara-rainforecaster.git
cd nusantara-rainforecaster

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

The repository includes `data/weather_data.csv`. If model artifacts are absent, the application trains them during startup and stores them under `models/cache/`.

## Data contract

Required CSV columns:

| Column | Meaning |
|---|---|
| `date` | Observation date (`DD-MM-YYYY`, `DD/MM/YYYY`, or `YYYY-MM-DD`) |
| `Tn` | Minimum temperature (°C) |
| `Tx` | Maximum temperature (°C) |
| `Tavg` | Average temperature (°C) |
| `RH_avg` | Average relative humidity (%) |
| `RR` | Rainfall (mm) |
| `station_id` | Weather-station identifier |

Optional columns improve scenario detail: `ss` (sunshine duration), `ff_x` (maximum wind speed), `ff_avg` (average wind speed), and `ddd_x` (wind direction).

Invalid dates are dropped, non-numeric values are coerced to missing values, and measurements outside configured physical bounds are excluded from model inputs. Validation decisions are logged rather than silently hidden.

## Project structure

```text
.
├── app.py                 # Current Streamlit product and navigation
├── data/
│   ├── loader.py          # Validation, cleaning, and feature engineering
│   └── weather_data.csv   # Bundled BMKG-format dataset
├── models/
│   ├── trainer.py         # Training, evaluation, persistence, and inference
│   └── cache/             # Serialized model artifacts
├── pages/                 # Compatibility views from the original interface
├── utils/
│   ├── charts.py          # Plotly figure builders
│   └── style.py           # Product components and responsive styling
└── tests/                 # Loader, model, and visualization tests
```

## Verification

```bash
pytest -q
python -m compileall -q app.py data models pages utils
```

Current local verification: **32 tests passing**, plus a Streamlit `AppTest` smoke run with no application exceptions.

## Known limitations

- No live BMKG API or nowcasting feed is connected.
- Predictions are station-agnostic unless station context is reflected in the supplied features.
- Model quality depends on the coverage and cleanliness of the bundled dataset.
- Rain-window timing is heuristic, not a separately trained temporal model.
- This prototype is not intended for disaster response, aviation, or other safety-critical decisions.

## Roadmap

- Connect a live, documented weather-data source.
- Add station-aware encoding and spatial validation.
- Track experiments and model versions outside serialized joblib files.
- Add calibration and drift monitoring.
- Expose a versioned inference API.

## License

MIT — see [LICENSE](LICENSE).
