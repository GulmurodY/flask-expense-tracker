#!/usr/bin/env bash
# Run the expense tracker and always free the port on exit.
# Stop with Ctrl+C (or Ctrl+Z) — the port will be released either way.

set -uo pipefail

PORT="${PORT:-8001}"
CONDA_ENV="${CONDA_ENV:-expense_tracker}"

free_port() {
  local pids
  pids=$(lsof -ti "tcp:${PORT}" 2>/dev/null || true)
  if [ -n "$pids" ]; then
    echo "Freeing port ${PORT} (pids: ${pids})..."
    kill $pids 2>/dev/null || true
    sleep 1
    pids=$(lsof -ti "tcp:${PORT}" 2>/dev/null || true)
    [ -n "$pids" ] && kill -9 $pids 2>/dev/null || true
  fi
}

cleanup() {
  echo
  echo "Shutting down..."
  [ -n "${APP_PID:-}" ] && kill -9 "$APP_PID" 2>/dev/null || true
  free_port
  exit 0
}

# Catch Ctrl+C (INT), kill/term, and Ctrl+Z (TSTP) — all trigger cleanup.
trap cleanup INT TERM TSTP

# Free the port first in case a previous run left it occupied.
free_port

# Activate the conda environment.
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$CONDA_ENV"

echo "Starting expense tracker on http://localhost:${PORT} (Ctrl+C to stop)"
PORT="$PORT" python main.py &
APP_PID=$!

# Wait on the app; if it exits or a signal arrives, clean up.
wait "$APP_PID"
cleanup