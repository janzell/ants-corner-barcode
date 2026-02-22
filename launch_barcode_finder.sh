#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_URL="http://127.0.0.1:5000/"
LOG_DIR="$SCRIPT_DIR/.runtime"
LOG_FILE="$LOG_DIR/server.log"
PID_FILE="$LOG_DIR/server.pid"

mkdir -p "$LOG_DIR"

is_running() {
  curl -sSf "$APP_URL" >/dev/null 2>&1
}

start_server() {
  cd "$SCRIPT_DIR"
  nohup "$SCRIPT_DIR/run_webapp.sh" >"$LOG_FILE" 2>&1 &
  echo $! > "$PID_FILE"
}

if ! is_running; then
  start_server

  for _ in {1..30}; do
    if is_running; then
      break
    fi
    sleep 1
  done
fi

open "$APP_URL"
