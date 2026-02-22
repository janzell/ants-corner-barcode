#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_URL="http://127.0.0.1:5173/"
LOG_DIR="$SCRIPT_DIR/.runtime"
LOG_FILE="$LOG_DIR/netlify-dev.log"
PID_FILE="$LOG_DIR/netlify-dev.pid"

mkdir -p "$LOG_DIR"

is_running() {
  curl -sSf "$APP_URL" >/dev/null 2>&1
}

ensure_dependencies() {
  if [ ! -d "$SCRIPT_DIR/node_modules" ]; then
    cd "$SCRIPT_DIR"
    npm install
  fi
}

start_server() {
  cd "$SCRIPT_DIR"
  nohup npm run dev >"$LOG_FILE" 2>&1 &
  echo $! > "$PID_FILE"
}

if ! is_running; then
  ensure_dependencies
  start_server

  for _ in {1..45}; do
    if is_running; then
      break
    fi
    sleep 1
  done
fi

open "$APP_URL"
