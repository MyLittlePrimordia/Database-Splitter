#!/usr/bin/env bash
# Builds the macOS .app bundle with PyInstaller and packages it into a .dmg
# with create-dmg. Run from the repo root or the app/ folder.
set -euo pipefail

APP_NAME="JSON Chunk Splitter"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> Building ${APP_NAME}.app with PyInstaller"
python3 -m pip install --break-system-packages pyinstaller

pyinstaller --noconfirm --windowed --onedir \
  --name "$APP_NAME" \
  --icon "assets/icon.icns" \
  --add-data "assets:assets" \
  main.py

DIST_APP="dist/${APP_NAME}.app"
if [ ! -d "$DIST_APP" ]; then
  echo "Build failed: $DIST_APP not found" >&2
  exit 1
fi

echo "==> Packaging .dmg with create-dmg"
if ! command -v create-dmg >/dev/null 2>&1; then
  brew install create-dmg
fi

mkdir -p dist/dmg
create-dmg \
  --volname "$APP_NAME" \
  --window-size 540 380 \
  --icon-size 100 \
  --app-drop-link 420 180 \
  "dist/${APP_NAME}.dmg" \
  "$DIST_APP" || true

echo "==> Done: dist/${APP_NAME}.dmg"
