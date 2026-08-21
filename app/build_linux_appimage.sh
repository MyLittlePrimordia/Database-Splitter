#!/usr/bin/env bash
# Builds the standalone Linux binary with PyInstaller and packages it into
# an .AppImage using appimagetool. Run from the repo root or the app/ folder.
set -euo pipefail

APP_NAME="split-database"
DISPLAY_NAME="JSON Chunk Splitter"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> Building ${DISPLAY_NAME} binary with PyInstaller"
python3 -m pip install --break-system-packages pyinstaller

pyinstaller --noconfirm --onefile \
  --name "$APP_NAME" \
  --icon "assets/icon.png" \
  --add-data "assets:assets" \
  main.py

APPDIR="dist/${APP_NAME}.AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
cp "dist/${APP_NAME}" "$APPDIR/usr/bin/${APP_NAME}"
cp "assets/icon.png" "$APPDIR/${APP_NAME}.png"

cat > "$APPDIR/${APP_NAME}.desktop" << DESKTOP
[Desktop Entry]
Type=Application
Name=${DISPLAY_NAME}
Exec=${APP_NAME}
Icon=${APP_NAME}
Categories=Utility;
DESKTOP

cat > "$APPDIR/AppRun" << APPRUN
#!/bin/sh
HERE="\$(dirname "\$(readlink -f "\${0}")")"
exec "\${HERE}/usr/bin/split-database" "\$@"
APPRUN
chmod +x "$APPDIR/AppRun"

if [ ! -f appimagetool ]; then
  curl -L -o appimagetool \
    "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
  chmod +x appimagetool
fi

./appimagetool "$APPDIR" "dist/${DISPLAY_NAME// /_}.AppImage"

echo "==> Done: dist/${DISPLAY_NAME// /_}.AppImage"
