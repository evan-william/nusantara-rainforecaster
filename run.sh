#!/usr/bin/env bash
# run.sh — helper script for local development
set -euo pipefail

PYTHON="${PYTHON:-python3}"

usage() {
  echo "Usage: $0 [setup|data|test|app|all]"
  echo ""
  echo "  setup  Install Python dependencies"
  echo "  data   Generate sample dataset"
  echo "  test   Run pytest suite"
  echo "  app    Launch Streamlit app"
  echo "  all    setup + data + test + app"
}

setup() {
  echo "==> Installing dependencies"
  "$PYTHON" -m pip install --upgrade pip
  "$PYTHON" -m pip install -r requirements.txt
}

generate_data() {
  echo "==> Generating sample dataset"
  "$PYTHON" data/generate_sample.py
}

run_tests() {
  echo "==> Running tests"
  "$PYTHON" -m pytest "$@"
}

run_app() {
  echo "==> Starting Streamlit"
  streamlit run app.py
}

CMD="${1:-}"

case "$CMD" in
  setup)  setup ;;
  data)   generate_data ;;
  test)   shift; run_tests "$@" ;;
  app)    run_app ;;
  all)
    setup
    generate_data
    run_tests
    run_app
    ;;
  ""|help|-h|--help)
    usage
    ;;
  *)
    echo "Unknown command: $CMD"
    usage
    exit 1
    ;;
esac