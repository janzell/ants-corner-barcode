#!/bin/zsh
# Script to run the Flask app from this repository
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if command -v pipenv >/dev/null 2>&1; then
	pipenv run python app.py
elif [ -x "$SCRIPT_DIR/install/bin/python" ]; then
	"$SCRIPT_DIR/install/bin/python" app.py
else
	python3 app.py
fi
