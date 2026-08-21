#!/usr/bin/env bash
# Builds the macOS .app bundle with PyInstaller and packages it into a .dmg
# with create-dmg (with automatic hdiutil fallback). Run from repo root or app/.
set -euo pipefail

APP_NAME="JSON Chunk Splitter"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> Checking icons..."
# If icon.icns doesn't exist, auto-generate it from icon.png or icon.ico using macOS native tools
if [ ! -f "assets/icon.icns" ]; then
  if [ -f "assets/icon.png" ]; then
    echo "==> Converting assets/icon.png -> assets/icon.icns"
    mkdir -p icon.iconset
    sips -z 16 16     assets/icon.png --out icon.iconset/icon_16x16.png >/dev/null 2>&1 || true
    sips -z 32 32     assets/icon.png --out icon.iconset/icon_16x16@2x.png >/dev/null 2>&1 || true
    sips -z 32 32     assets/icon.png --out icon.iconset/icon_32x32.png >/dev/null 2>&1 || true
    sips -z 64 64     assets/icon.png --out icon.iconset/icon_32x32@2x.png >/dev/null 2>&1 || true
    sips -z 128 128   assets/icon.png --out icon.iconset/icon_128x128.png >/dev/null 2>&1 || true
    sips -z 256 256   assets/icon.png --out icon.iconset/icon_128x128@2x.png >/dev/null 2>&1 || true
    sips -z 256 256   assets/icon.png --out icon.iconset/icon_256x256.png >/dev/null 2>&1 || true
    sips -z 512 512   assets/icon.png --out icon.iconset/icon_256x256@2x.png >/dev/null 2>&1 || true
    sips -z 512 512   assets/icon.png --out icon.iconset/icon_512x512.png >/dev/null 2>&1 || true
    sips -z 1024 1024 assets/icon.png --out icon.iconset/icon_512x512@2x.png >/dev/null 2>&1 || true
    iconutil -c icns icon.iconset -o assets/icon.icns || true
    rm -rf icon.iconset
  elif [ -f "assets/icon.ico" ]; then
    echo "==> Converting assets/icon.ico -> assets/icon.icns"
    sips -s format png assets/icon.ico --out assets/temp_icon.png >/dev/null 2>&1 || true
    if [ -f "assets/temp_icon.png" ]; then
      mkdir -p icon.iconset
      sips -z 128 128 assets/temp_icon.png --out icon.iconset/icon_128x128.png >/dev/null 2>&1 || true
      sips -z 256 256 assets/temp_icon.png --out icon.iconset/icon_256x256.png >/dev/null 2>&1 || true
      sips -z 512 512 assets/temp_icon.png --out icon.iconset/icon_512x512.png >/dev/null 2>&1 || true
      iconutil -c icns icon.iconset -o assets/icon.icns || true
      rm -rf icon.iconset assets/temp_icon.png
    fi
  fi
fi

# Build PyInstaller argument list dynamically
ICON_ARGS=()
if [ -f "assets/icon.icns" ]; then
  ICON_ARGS=(--icon "assets/icon.icns")
fi

DATA_ARGS=()
if [ -d "assets" ]; then
  DATA_ARGS=(--add-data "assets:assets")
fi

echo "==> Building ${APP_NAME}.app with PyInstaller"
python3 -m pip install --break-system-packages pyinstaller

pyinstaller --noconfirm --windowed --onedir \
  --name "$APP_NAME" \
  "${ICON_ARGS[@]}" \
  "${DATA_ARGS[@]}" \
  main.py

DIST_APP="dist/${APP_NAME}.app"
if [ ! -d "$DIST_APP" ]; then
  echo "Build failed: $DIST_APP not found" >&2
  exit 1
fi

echo "==> Packaging .dmg"
rm -f "dist/${APP_NAME}.dmg"

# Try create-dmg first
if command -v create-dmg >/dev/null 2>&1; then
  create-dmg \
    --volname "$APP_NAME" \
    --window-size 540 380 \
    --icon-size 100 \
    --app-drop-link 420 180 \
    --overwrite \
    "dist/${APP_NAME}.dmg" \
    "$DIST_APP" || true
fi

# Fallback to macOS native hdiutil if create-dmg was missing or failed in headless CI
if [ ! -f "dist/${APP_NAME}.dmg" ]; then
  echo "==> create-dmg unavailable or failed; generating DMG with native hdiutil..."
  hdiutil create -volname "$APP_NAME" -srcfolder "$DIST_APP" -ov -format UDZO "dist/${APP_NAME}.dmg"
fi

echo "==> Done: dist/${APP_NAME}.dmg"