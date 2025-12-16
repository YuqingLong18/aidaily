#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="/www/wwwroot/aidaily"
API_DIR="$APP_ROOT/apps/api"
LOG_DIR="$APP_ROOT/logs"
TS="$(date +%F_%H%M%S)"

mkdir -p "$LOG_DIR"
cd "$API_DIR"
# Load env if present (OpenRouter key etc.)
if [ -f "$APP_ROOT/.env" ]; then
  set -a
  . "$APP_ROOT/.env"
  set +a
fi
# Ensure venv exists
if [ ! -x "$API_DIR/.venv/bin/python" ]; then
  echo "Missing venv at $API_DIR/.venv. Create it first." >&2
  exit 1
fi

source "$API_DIR/.venv/bin/activate"

echo "== Nexus daily run: $(date -Is) =="

# Run "today" edition label (Beijing local date), which summarizes previous UTC day
python -m app.ingest --mode live --date "$(date +%F)" --print-window --curate \
  | tee -a "$LOG_DIR/ingest_${TS}.log"

echo "== Done: $(date -Is) =="
