#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DESKTOP_DIR="$HOME/Desktop"
SHORTCUT_PATH="$DESKTOP_DIR/Ants Corner Barcode Finder.command"

cat > "$SHORTCUT_PATH" <<EOF
#!/bin/zsh
"$SCRIPT_DIR/launch_barcode_finder.sh"
EOF

chmod +x "$SHORTCUT_PATH"
chmod +x "$SCRIPT_DIR/launch_barcode_finder.sh"
chmod +x "$SCRIPT_DIR/run_webapp.sh"

echo "Shortcut created: $SHORTCUT_PATH"
echo "Double-click it to open Ants Corner Barcode Finder."
