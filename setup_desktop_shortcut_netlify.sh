#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DESKTOP_DIR="$HOME/Desktop"
SHORTCUT_PATH="$DESKTOP_DIR/Ants Corner Barcode Finder (Netlify).command"

cat > "$SHORTCUT_PATH" <<EOF
#!/bin/zsh
"$SCRIPT_DIR/launch_netlify_barcode_finder.sh"
EOF

chmod +x "$SHORTCUT_PATH"
chmod +x "$SCRIPT_DIR/launch_netlify_barcode_finder.sh"

echo "Shortcut created: $SHORTCUT_PATH"
echo "Double-click it to launch Ants Corner Barcode Finder (Netlify)."
